#!/usr/bin/env python3
"""Merge binary files to stdout.

Differences are resolved by using the bytes which are found in most of the files.
"""

import argparse
import sys

from contextlib import ExitStack
from importlib.metadata import version


RESULT_STRING = (
    "{handled:d} bytes handled, "
    + "{equal:d} equal, "
    + "{differences:d} differences, "
    + "{ambiguous:d} ambiguous, "
    + "{worst:d} matches at worst."
)


def positive(numeric_type):
    def require_positive(value):
        number = numeric_type(value)
        if number <= 0:
            raise argparse.ArgumentTypeError(f"Number {value} must be positive.")
        return number

    return require_positive


def merge_files(files, minimum=0):
    if minimum > len(files):
        print("Minimum must be less than or equal to the number of files to merge.")
        sys.exit("minimum_too_high")

    file_count = len(files)
    position = 0
    differences = 0
    ambiguous = 0
    worst = file_count

    try:
        with ExitStack() as stack:
            # Open files
            files = [stack.enter_context(open(filename, "rb")) for filename in files]
            block_size = 4096

            # Iterate over data
            while files:
                data = [file.read(block_size) for file in files]
                data_length = [len(d) for d in data]
                max_length = max(data_length)
                output_buffer = bytearray(max_length)

                for i in range(max_length):
                    values = [x[i] for x in data if len(x) > i]
                    bins = {}
                    for value in values:
                        if value not in bins:
                            bins[value] = 0
                        bins[value] += 1

                    sorted_bins = sorted(bins.items(), key=lambda x: x[1], reverse=True)

                    if sorted_bins[0][1] < worst:
                        worst = sorted_bins[0][1]
                        print(
                            f"{position + i:#x}: worst byte so far (matches: {worst})",
                            file=sys.stderr,
                        )

                    if sorted_bins[0][1] < file_count:
                        differences += 1

                    if len(sorted_bins) > 1 and sorted_bins[0][1] == sorted_bins[1][1]:
                        ambiguous += 1
                        print(f"{position + i:#x}: no clear winner", file=sys.stderr)

                    if sorted_bins[0][1] < minimum:
                        print(
                            f"{position + i:#x}: only {sorted_bins[0][1]} "
                            + f"(required: {minimum}) matches, aborting",
                            file=sys.stderr,
                        )
                        sys.exit("minimum_not_met")

                    output_buffer[i] = sorted_bins[0][0]

                # Write winning byte
                sys.stdout.buffer.write(output_buffer)

                position += max_length

                # Remove files which did not deliver a full block
                files = [
                    file
                    for (file, length) in zip(files, data_length)
                    if length == block_size
                ]

    finally:
        print(
            RESULT_STRING.format(
                handled=position,
                equal=position - differences,
                differences=differences,
                ambiguous=ambiguous,
                worst=worst,
            ),
            file=sys.stderr,
        )


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Files to merge")
    parser.add_argument(
        "-m",
        "--minimum",
        dest="minimum",
        type=positive(int),
        default=1,
        help="minimum number of matches required for a valid byte (default: 1)",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {version('re_helpers')}"
    )
    args = parser.parse_args(args)
    merge_files(args.files, args.minimum)


if __name__ == "__main__":
    main()
