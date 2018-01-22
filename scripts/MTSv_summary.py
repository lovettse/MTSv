import argparse
from ete3 import NCBITaxa
import os.path as path
from  os import getcwd
from os.path import expanduser
from collections import defaultdict
import pandas as pd

div_map = {2:'Bacteria', 10239: 'Viruses (excluding environmental sample',
           2157: 'Archaea', 12884: 'Viroids', 28384: "Other and synthetic sequences",
           2759: "Eukaryotes", 33090: "Green Plants", 4751: "Fungi",
           7742: "Vertebrates (excluding Primates, Chiroptera, Bos taurus, Canis lupus familiaris)",
           9443: "Primates (excluding Homo sapiens)",
           9397: "Chiroptera", 9913: "Bos Taurus", 9615: "Canis lupus familiaris",
           9606: "Homo sapiens"}



def path_type(input_path):
    if not path.isdir(input_path):
        raise argparse.ArgumentTypeError(
            "Not a valid path: {}".format(input_path))
    return path.abspath(input_path)

def file_type(input_file):
    if not path.isfile(input_file):
        raise argparse.ArgumentTypeError(
            "Not a valid file path: {}".format(input_file))
    return path.abspath(input_file)

def tax2div(taxid):
    lineage = ncbi.get_lineage(taxid)
    for level in lineage[::-1]:
        if level in div_map:
            return div_map[level]
    return "Unknown"
        

if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(
        prog="MTSv Summary",
        description="Summarize number of hits for each taxa, "
                    "including signature hits.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    PARSER.add_argument(
        "project_name", metavar='PROJECT_NAME', type=str,
        help="Project name and output file prefix"
    )

    PARSER.add_argument(
        "all", metavar="COLLAPSE_FILE", type=file_type,
        help="Path to MTSv-collapse output file"
    )
    

    PARSER.add_argument(
        "-o", "--out_path", type=path_type, default="./",
        help="Output directory"
    )


    ARGS = PARSER.parse_args()

    ncbi = NCBITaxa()

    
    outfile = path.join(
        ARGS.out_path, "{0}_summary.xlsx".format(ARGS.project_name))

    data_dict = {}
    
    strip = str.strip
    with open(ARGS.all, "r") as infile:
        for line in infile:
            line = line.strip().rsplit(":", 1)
            taxa = [int(strip(tax)) for tax in line[1].split(",")]
            signature = True if len(taxa) == 1 else False
            counts = [int(c) for c in line[0].split("_")[1:]]
            for taxon in taxa:
                if taxon not in data_dict:
                    data_dict[taxon] = {i:[0,0,0] for i in range(len(counts))}
                for sample, count in enumerate(counts):
                    data_dict[taxon][sample][0] += count
                    data_dict[taxon][sample][1] += bool(count)
                    if signature:
                        data_dict[taxon][sample][2] += count

    taxid2name = ncbi.get_taxid_translator(data_dict.keys())      
    data_list = []
    for taxa, samples in data_dict.items():
        for sample, value in samples.items():
            row_list = [taxa, tax2div(taxa), taxid2name[taxa], sample, value[0], value[1], value[2]]
            data_list.append(row_list)

    data_frame = pd.DataFrame(
        data_list,
        columns=["TaxID","Division", "Sci. Name", "Sample",
        "Total Hits", "Unique Hits", "Signature Hits"])
      

    data_frame.to_excel(outfile, index=False) 