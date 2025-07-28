#!/usr/bin/env python3

import argparse
import os
from converter.csv_log import CsvLog
from converter.ld_log import LdLog

DESCRIPTION = (
    """Generates MoTeC .ld files using csv logs from an AiM data logger"""
)

EPILOG = """UTFR Firmware Team"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG)
    parser.add_argument("log", type=str, help="Path to logfile")
    parser.add_argument(
        "--frequency",
        type=int,
        help="Sample rate for messages collected by the data logger",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Name of output file, defaults to the same filename as 'log'",
    )
    args = parser.parse_args()

    if args.log:
        args.log = os.path.expanduser(args.log)
    if args.output:
        args.output = os.path.expanduser(args.output)

    # Make sure our input files are valid
    if not os.path.isfile(args.log):
        print("ERROR: log file %s does not exist" % args.log)
        exit(1)

    print("Parsing CSV...")
    data_log: CsvLog = CsvLog.parse(args.log)
    if args.frequency:
        data_log.set_frequency(args.frequency)
    data_log.create_channels()

    if len(data_log.channels) == 0:
        print("ERROR: Failed to find any channels in log data")
        exit(1)

    print("Converting to MoTeC log...")
    motec_log = LdLog.initialize(data_log)
    motec_log.add_all_channels(data_log)

    print("Saving MoTeC log...")
    if args.output:
        ld_filename = os.path.splitext(args.output)[0] + ".ld"
    else:
        # Copy the path and name from the source file, but change the extension
        dir, filename = os.path.split(args.log)
        filename = os.path.splitext(filename)[0]
        ld_filename = os.path.join(dir, filename + ".ld")

    output_dir = os.path.dirname(ld_filename)
    if output_dir and not os.path.isdir(output_dir):
        print("Directory '%s' does not exist, will create it" % output_dir)
        os.makedirs(output_dir)

    motec_log.write(ld_filename)
    print("Done!")
