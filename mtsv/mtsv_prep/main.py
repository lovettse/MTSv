import subprocess
import sys
import argparse
import os
import datetime
import inspect
from ftplib import FTP
from time import sleep
import gzip
import tarfile
from multiprocessing import Pool, Queue, Process, Manager, RLock, freeze_support
from glob import iglob
from mtsv.commands import Command
from mtsv.parsing import make_sub_parser, get_global_config, ACTIONS, TYPES, add_default_arguments
from mtsv.mtsv_prep.MTSv_prune import *

from mtsv.utils import error, bin_path

from snakemake.workflow import Workflow, Rules, expand
import snakemake.workflow
from snakemake import shell

class Database(Command):
    config_section = ["DATABASE"]

    def __init__(self, params):
        print("running Database")
        super().__init__(params)
        print(self.params)


class CustomDB(Command):
    config_section = ["CUSTOM_DB"]

    def __init__(self, params):
        print("running custom database")
        super().__init__(params)
        print(self.params)

DEFAULT_DB_PATH = os.path.join(
    inspect.getfile(inspect.currentframe()),
    datetime.datetime.now().strftime("%b-%d-%Y"))

DEFAULT_PARTITIONS = ["2,2157", "10239,12884", "28384",
                      "2759-33090,4751,7742", "33090",
                      "4751", "7742-9443,9397,9913,9615",
                      "9443-9606", "9397", "9913", "9615", "9606"]

COMMANDS = {
    "database" : Database,
    "custom_db": CustomDB,
    }

FILE_LOCK = RLock()

def oneclickdl(args):
    print()
    print(args)
    return pull(
        path=args.path,
        thread_count=args.threads,
        databases=args.includedb)

def decompression(x, path):
    output = subprocess.PIPE
    if not os.path.isfile(x.strip(".gz")):
        subprocess.run(['gunzip',x], stderr=output, stdout=output)
        if output:
            with FILE_LOCK:
                with open(os.path.join(path, "artifacts/decompression.log"), "a") as out:
                    out.write("{0}\n".format(x))
    return x.strip(".gz")

def oneclickbuild(args):
    with open(os.path.join(args.path, "artifacts/decompression.log"), "w" ):
        pass
    pool = Pool(args.threads)
    pool.starmap(decompression, [(os.path.abspath(x),
                                  args.path) for x in iglob(os.path.join(args.path,"flat_files/*.gz"))])
    for fp in iglob(os.path.join(args.path,"artifacts/*_ff.txt")):
        db = list(os.path.split(fp))
        print(db)
        db[1] = db[1].strip().replace("_ff.txt",".fas")
        print(db)
        db = os.path.abspath("{0}{1}{2}".format(db[0],os.sep,db[1]))
        print(db)
        with open(os.path.abspath(fp), "r" ) as file:
            temp = file.readlines()

        with open(os.path.abspath(fp), "w") as file:
            for x in temp:
                if x.strip().rsplit(".",1)[1] == "gz":
                    x= x.strip().rsplit(".",1)[0]
                file.write("{0}\n".format(x))

        # with open(os.devnull, "w") as null:
        build_db(os.path.abspath(fp), db, os.devnull, os.devnull, args.threads, os.devnull)

    arguments = oneclickjson(args.path)

    pool.starmap(acc_serialization, [(argument['acc-to-taxid-paths'], argument['fasta-path'],
                                      argument['taxdump-path']) for argument in arguments ])
    # shutil.rmtree(os.path.join(args.path, "flat_files" ))
def mapper(x):
    return clip(*x)

def partition(args):
    partition_list = []
    for db in args.customdb:
        db = db.strip().replace(" ","_")
        arguments = parse_json(os.path.join(args.path, "artifacts/{0}.json".format(db)))
        for prt in args.partitions:
            try:
                if args.debug:
                    path = os.path.join(args.path, "indices", db, prt.replace(",", "_"))
                    temp = prt.split("-")

                else:
                    path = os.path.join(args.path, "indices", db, prt.replace(",", "_"))
                    os.makedirs(path, exist_ok=args.overwrite)
                    temp = prt.split("-")
                if len(temp) == 2:
                    inc = set(temp[0].split(","))
                    exc = set(temp[1].split(","))
                else:
                    inc = set(temp[0].split(","))
                    exc = set()
                partition_list.append( ( list(inc), args.rollup_rank, list(exc), os.path.join(path,
                                        "{0}.fas".format(prt.replace(",","_"))),arguments['minimum-length'],
                                         arguments['maximum-length'], arguments["fasta-path"],
                                         arguments["serialization-path"], args.debug  ) )
            except OSError:
                print("Partion folder {0} exists please use --overwrite to repartition".format(path))
            # except AttributeError as e:
            #     print(e)
            #     raise KeyboardInterrupt

    # ret_list = []
    # for i in partition_list:
    #     ret_list.append(clip(*i))
    p = Pool(args.threads)
    ret_list = p.starmap(clip, partition_list)
    # p.close()
    # p.join()

    print(ret_list)
    return ret_list

def chunk(file_list):
    dir_set = set()
    for fp in file_list:
        subprocess.run("{2} --input {0} --output {1}".format(fp, os.path.dirname(fp), bin_path('mtsv-chunk')).split() )
        dir_set.add(os.path.dirname(fp))
    return list(dir_set)

def snake(args):
    chunk_path = bin_path('mtsv-chunk')
    fm_build_path = bin_path('mtsv-build')
    print(chunk_path)
    print(fm_build_path)
    print(args)

    print(partition(args))
    # for i in args:
    #     print(i)
    workflow = Workflow(
        "__file__",
        overwrite_workdir=args.working_dir)
    if args.cluster_cfg is not None:
        workflow.cluster_cfg = args.cluster_cfg
    snakemake.workflow.rules = Rules()
    snakemake.workflow.config = dict()




    # @workflow.rule(name='chunking')
    # @workflow.docstring("""Fasta chunking""")
    # @workflow.input(os.path.join("test", "{}.index"))
    # @workflow.output(os.path.join(cmd.params['binning_outpath'], "{index}.bn"))
    # @workflow.params(call=chunk_path, args=args.chunk_size)
    # @workflow.message("Executing Fasta chunking on the follow files {input}.")
    # @workflow.log(os.path.join(args.path,"artifacts/logs/""{index}.log"))
    # @workflow.threads(1)
    # @workflow.shellcmd("{params.call} --input {input} --output{output} --gb {params.args} > {log} 2>&1")
    # @workflow.run
    # def __rule_chunking(input, output, params, wildcards,
    #                    threads, resources, log, version, rule,
    #                    conda_env, singularity_img, singularity_args,
    #                    use_singularity, bench_record, jobid, is_shell):
    #     shell(
    #         "{params.call} --input {input} --output{output} --gb {params.args} > {log} 2>&1"
    #     )
    #
    # workflow.check()
    # print("Dry run first ...")
    # workflow.execute(dryrun=True, updated_files=[])
    # return workflow

def fm_build(dir_list):
    fm_list = []
    for directory in dir_list:
        for fp in iglob(os.path.join(directory, "*.fasta")):
            out_file = os.path.join(directory, "{0}.fmi".format(os.path.basename(fp).split(".")[0]))
            subprocess.run("{2} --fasta {0} --index {1}.fmi".format(os.path.abspath(fp), out_file, bin_path('mtsv-build')).split() )
            fm_list.append(out_file)
    return fm_list

def oneclickfmbuild(args, is_default):
    to_link = fm_build(chunk(partition(args)))
    if is_default:
        path = os.path.join(args.path,"indices","default")
    else:
        path = os.path.join(args.path, "indices", "custom")
    os.makedirs(path, exist_ok=True)
    for fp in to_link:
        os.symlink(fp, os.path.join(path,os.path.basename(fp)))


def setup_and_run(parser):

    args = parser.parse_known_args()[0]

    # print(args)
    try:

        if args.cmd_class == Database:
            if args.download_only:
                # if not args.path:
                args.path = os.path.abspath(oneclickdl(args))
                # else:

            elif args.build_only:
                if os.path.isdir(args.path):
                    oneclickbuild(args)
                else:
                    print("A valid path was not specified")
            else:
                args.path = os.path.abspath(oneclickdl(args))
                oneclickbuild(args)

        elif args.cmd_class == CustomDB:
            # print("TODO Clipper")
            # snake(args)
            oneclickfmbuild(args, args.partitions == DEFAULT_PARTITIONS)

    except AttributeError:
        print("oneclick")
        sys.argv[1] = "database"
        args = parser.parse_known_args()[0]
        args.path = os.path.abspath(oneclickdl(args))
        oneclickbuild(args)
        path = args.path
        sys.argv[1] = "custom_db"
        args = parser.parse_known_args()[0]
        args.path = path
        oneclickfmbuild(args, args.partitions == DEFAULT_PARTITIONS)


        # args.path = os.path.abspath(oneclickdl(args))
        # oneclickbuild(args)
        # oneclickfmbuild(args, args.partitions == DEFAULT_PARTITIONS)

#   print(args.path)
    #     oneclickbuild(args)
    #     oneclickfmbuild(args, args.partitions == default_parts)
    # if args.do
    # elif args.oneclickdl:
    #     print(os.path.abspath(oneclickdl(args)))
    # elif args.oneclickbuild:
    #     if os.path.isdir(args.path):
    #         oneclickbuild(args)
    #     else:
    #         print("Path to parent of */flats_files/ needs to be specified or downloaded")
    # elif args.oneclickpartition:
    #     oneclickfmbuild(args, args.partitions == default_parts)



def main(argv=None):
    if argv is None:
        argv = sys.argv
    

    parser = argparse.ArgumentParser(
        prog="mtsv-setup",
        description="Download and build sequence databases and indices",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(
        title="commands", metavar="COMMAND",
        help="Setup Commands"
    )

    for command, cmd_class in COMMANDS.items():
        make_sub_parser(
            subparsers, command, cmd_class
        )

    p = subparsers.add_parser("oneclick")
    for command, cmd_class in COMMANDS.items():
        for arg, desc in get_global_config(cmd_class.config_section).items():
            if "_meta" in arg:
                continue
            if 'type' in desc:
                desc['type'] = TYPES[desc['type']]
            if 'default' in desc and 'help' in desc:
                desc['help'] += " (default: {})".format(desc['default'])
            if 'action' in desc and desc['action'] in ACTIONS:
                desc['action'] = getattr(
                    sys.modules[__name__], desc['action'])
            arg = "--{}".format(arg)
            if 'positional' in desc:
                del desc['positional']
            try:
                p.add_argument(
                    arg, **desc
                )
            except argparse.ArgumentError:
                continue
        try:
            add_default_arguments(p)
        except argparse.ArgumentError:
            pass
        # p.set_defaults(cmd_class=cmd_class)

        # print(command, get_global_config(cmd_class.config_section))


    # print(parser)
    # print(subparsers)
    if len(argv)==1:
        parser.print_help(sys.stdout)
        sys.exit(1)
    try:
        setup_and_run(parser)
    except KeyboardInterrupt:
        error("\n-- Stopped by user --", exception=False)



    # group = parser.add_mutually_exclusive_group(required=True)
    # group.add_argument("-oc", "--oneclick", "-oneclick",action='store_true')
    # group.add_argument("-ocdl", "--oneclickdl", "-oneclickdl",action='store_true')
    # group.add_argument("-ocbld", "--oneclickbuild", "-oneclickbuild",action='store_true')
    # group.add_argument("-ocprt", "--oneclickpartition", "-oneclickpartition", action='store_true')

    # group.add_argument("-c", "--custom", "-custom", action='store_true')


    # group = parser.add_argument_group()
    # group.add_argument("-p","--path","-path", default=datetime.datetime.now().strftime("%b-%d-%Y"),
    #                    help="Path to dated folder containing artifacts")

    # group.add_argument("-prt","--partitions","-partitions", nargs='*', default=default_parts,
    #                    help="Space seperated list of '-' delimited tuples of comma seperated TaxIDs for inclusion and exclusion\n" \
    #                         "ex. 1386-1392,1396 would create a FM-index of the genus Bacillus without B. anthracis and B. cereus\n" \
    #                         "if no exlusion desire no '-' is needed")
    # group.add_argument("-min","--minimum-length","-minimum-length", type=float,default=0,
    #                    help="Integer for minimum length of sequences to include")
    # group.add_argument("-max","--maximum-length","-maximum-length", type=float, default=float('inf'),
    #                    help="Integer for maximum length of sequences to include")
    # group.add_argument("-rur","--rollup-rank","-rollup-rank", default="species",
    #                    help="NCBI rank to set sequence headers i.e. None, genus, family et cetera\n (default: species)")

    # group.add_argument("-t", "--threads", "-threads", type=int, default=1,
    #                    help="Specify total threads to spawn default:1")
    # group.add_argument("-ow", "--overwrite", "-overwrite", help="Overwrite files if they exist",
    #                    action='store_true')

    # group.add_argument("-cdb", "--customdb", "-customdb", nargs='*', default=["genbank"],
    #                    help="Space delimited list of the following NCBI source: Chromosome, Scaffold, genbank.\n" \
    #                         "By default only genbank indices are built")

    # group.add_argument("-idb", "--includedb", "-includedb", nargs='*', default=["genbank","Chromosome","Scaffold"],
    #                    help=argparse.SUPPRESS)


    # if args.oneclick:
    #     args.path = os.path.abspath(oneclickdl(args))
    #     print(args.path)
    #     oneclickbuild(args)
    #     oneclickfmbuild(args, args.partitions == default_parts)

    # elif args.oneclickdl:
    #     print(os.path.abspath(oneclickdl(args)))
    # elif args.oneclickbuild:
    #     if os.path.isdir(args.path):
    #         oneclickbuild(args)
    #     else:
    #         print("Path to parent of */flats_files/ needs to be specified or downloaded")
    # elif args.oneclickpartition:
    #     oneclickfmbuild(args, args.partitions == default_parts)

if __name__ == "__main__":
    main()
