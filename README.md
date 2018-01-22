# MTSv

MTSv is a suite of metagenomic binning and analysis tools. It attempts to accurately identify which species are present in a given DNA sample. It assumes that read fragments in samples will be in a "shotgun" or short read format, typically ~50-200 bases in length.

All commands listed in this document assume they're being executed from the repository's root directory. Adjust accordingly if you've installed the tools elsewhere.

## Building

MTSv is built in Rust, with a little bit of Python. You'll need:

* `rustc` and `cargo` >= 1.8.0 ([rustup.rs](https://rustup.rs) is the easiest installation method)
* a C compiler (tested with GCC and clang)

### Tests

To run tests:

~~~
$ cargo test
~~~

To generate a code coverage report, make sure [kcov >= 26](https://simonkagstrom.github.io/kcov/) is installed on your `PATH`, then install `cargo-kcov`:

~~~
$ cargo install cargo-kcov
~~~

To run coverage:

~~~
$ cargo kcov -- --exclude-pattern="/.cargo,vendor/,tests/,bench/,include/,bin/,ssw/"
~~~

This will place a code coverage report under `target/kcov/index.html`.

### Building

To build the MTSv binaries:

~~~
$ cargo build --release
~~~

They'll be available under `target/release/MTSv-*`.

## Documentation

To generate the internal documentation:

~~~
$ cargo doc [--open]
~~~

(pass the `--open` flag if you want to immediately open the docs in your browser)

## Usage

MTSv builds several binaries:

* `MTSv-chunk`
* `MTSv-binner`
* `MTSv-build`
* `MTSv-collapse`
* `MTSv-inform`
* `MTSv-readprep`
* `MTSv-tree-build`

All of these accept the `--help` flag to print a help message on their usage. See below for specific use instructions.

### Snakemake

There's an (in-progress) Snakefile in the repository root. This manages a MTSv-based metagenomic workflow. See the [Snakemake website](https://bitbucket.org/snakemake/snakemake/wiki/Home) for installation and usage instructions.

(TODO: include instructions on configuring snakefile for particular file sets)

### Index construction

MTSv uses several pre-constructed indices for running its queries.

#### Reference file format & taxdump.tar.gz

To construct the indices, you'll need two files:

1. A FASTA file of all reference sequences, with headers in the format `ACCESSION-TAXONOMICID`. So if a sequence has accession # 12345, and belongs to the NCBI taxonomic ID 987, the header for that sequence should read `12345-987`.
2. The `taxdump.tar.gz` file from NCBI which corresponds to the sequences in your FASTA file.

#### Chunking reference database

MTSv uses A LOT of memory for its indices. About 20x the space compared to the FASTA file its given. As a result, it's generally preferable to split the database into small chunks that can be processed iteratively. These chunks should, as much as possible, have all or most of a taxonomic ID in each of them, as MTSv achieves speedups by skipping queries once it's found a successful match in a taxonomic node. MTSv includes a utility for doing so. To split your reference database into 1GB chunks (resulting in 15-20GB needed for running queries):

~~~
$ target/release/MTSv-chunk -i PATH_TO_FASTA -o PATH_TO_CHUNK_FOLDER -g NUM_GBS_PER_CHUNK
~~~

This will write a series of chunk files into the directory specified. See the help message for further information.

#### Metagenomic index

Now that you have N chunks of your FASTA database, they need to be processed into indices which MTSv can use for querying.

~~~
$ target/release/MTSv-build --fasta /path/to/chunkN.fasta --index /path/to/write/chunkN.index
~~~

Using default settings, indices will use ~15-20x as much RAM as the reference file used for their creation (at a sampling interval of 512 bytes). This can be overridden by passing the `--sample-interval <FM_SAMPLE_INTERVAL>` flag. Lower than 512 will increase the size of the index and can provide a reduction in query time. Increasing the flag will decrease the size of the index up to a point (the size of the suffix array can't be reduced, this setting only changes the FM index size) while accepting a slower query time.

See the help message for other options.

#### Taxonomic tree index

To determine which reads are informative for particular taxonomic IDs, you'll need to construct an index from the NCBI `taxdump.tar.gz` which corresponds to your FASTA database.

~~~
$ target/release/MTSv-tree-build --dump /path/to/taxdump.tar.gz --index /path/to/write/tree.index
~~~

See the help message for other options.

### readprep

MTSv assumes that unidentified read fragments/sequences (referred to as "query reads") come in FASTA format and are of uniform length within a given query file. Often one needs to run some quality-control processes and combine several files. If you have a variety of FASTQ files to combine and QC, run `MTSv-readprep`. For the full list of configurations, see the help message:

~~~
$ target/release/MTSv-readprep --help
~~~

This will write reads with headers in the format `R_COUNT1_COUNT2_COUNT3` and so on, where each count corresponds to the number of times that read was found in each FASTQ file, in the order they were passed as arguments.

### Binning queries

Now that you have the indices MTSv needs, and have prepared the query reads, run `MTSv-binner` on each index chunk. In this example, 3 SNPs are tolerated in matches, and 8 threads are used for processing:

~~~
$ target/release/MTSv-binner --edits 3 --threads 8 \
    --index /path/to/chunkN.index \
    --fasta /path/to/prepared_reads.fasta \
    --results /path/to/write/chunkN_results.txt
~~~

See the help message for other options.

#### Output

`MTSv-binner` writes results for a single read per line. For example, if a read with the header `R1_0_1` maps to taxon IDs `562`, `9062`, and `100`:

~~~
R1_0_1:562,9062,100
~~~

### Collapsing chunks

Since each results file from the binner will only represent some of the species matches for a given query read, combine all of the chunked results into a single results file for further analysis:

~~~
$ target/release/MTSv-collapse /path/to/chunk1_results.txt /path/to/chunk2_results.txt ... \
    --output /path/to/collapsed_results.txt
~~~

Make sure to include all of the chunk files. While the collapser could be run in multiple phases, it's generally much faster to do them all at once.

See the help message for other options.

### Finding informative reads

At this point, you should have a single file which records all of the taxonomic IDs (species, usually) which your query reads have mapped to (within the specified number of edits, that is).

To determine which reads are "informative" for which taxonomic nodes, you'll run the `MTSv-inform` tool. The simplest way to do so (spawning 8 threads):

~~~
$ target/release/MTSv-inform \
    --index /path/to/tree.index \
    --input /path/to/collapsed_results.txt \
    --threads 8
    --lca 0
    --output /path/to/write/informatives.txt
~~~

The sensitivity of the analysis can be adjusted either by changing the `--lca` flag, by by specifying one of the `[--genus|--family]` flags. Changing the LCA (least common ancestor) value will affect how many jumps "up" the taxonomic tree to consider. Specifying a "logical" LCA flag will search for a common genus or family (depending on the flag) which covers all of the results found earlier.

### Analyzing output

While MTSv is intended to house further analysis tools, they have not yet been built. An example of some analysis currently lives in the `name-summary.ipynb` Jupyter notebook. It takes a results file, and generates a CSV of some per-input-file breakdown.