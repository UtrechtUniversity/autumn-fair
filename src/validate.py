"""Commandline tool to check and validate csv files."""

import argparse
import toml
import sys
import pandas as pd

from pathlib import Path

# Location of this file
PATH = Path.absolute(Path(__file__))

# Files to validate
CSV_FILE_NAMES = ['environment_events.csv', 'environment.csv', 'host_events.csv', 'hosts.csv']

# Colors
INFO = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def main() -> None:
    """CLI."""
    parser = argparse.ArgumentParser(
                prog="CSV file validation",
                description="Validates the formatting and typing of csv files."
             )
    
    parser.add_argument(
            "-d",
            "--data",
            help="The path to the data folder containing the csv files.",
            type=Path,
            required=True
            )

    parser.add_argument(
            "-c",
            "--configfile",
            help="The path to the validation.toml.",
            type=Path,
            default=PATH.parent.parent / "data" / "metadata_test" / "_validation_schema_v2.toml"
            )

    parser.add_argument(
            "-s",
            "--sep",
            help="Separator between columns in csv files. \n Tab separator: tab. Default: ;",
            type=str,
            default=";"
            )

    args, _ = parser.parse_known_args() 
   
    # For tab separated files
    if args.sep == "tab":
        args.sep = "\t"

    print(args)

    # read in toml file
    validation = read_toml(args.configfile)
    # read in data
    data = read_csv_files(args.data, args.sep)
    print(data[CSV_FILE_NAMES[0]])

def read_csv_files(path: Path, sep: str) -> dict:
    if not path.is_dir():
        raise FileNotFoundError(f"{FAIL}{path} does not exist.{ENDC}")
    files = [f.name for f in path.glob('**/*.csv') if f.is_file() and f.name in CSV_FILE_NAMES]
    if not set(files) == set(CSV_FILE_NAMES):
        msg = f"{FAIL}Missing files. Expected {CSV_FILE_NAMES}\nFound {files}{ENDC}"
        raise FileNotFoundError(msg)

    data = {}
    for f in files:
        try:
            data[f] = pd.read_csv(path.joinpath(f), sep=sep)
        except pd.errors.EmptyDataError as err:
            raise ValueError(f"{FAIL}{path.joinpath(f)} is empty.{ENDC}")
        except Exception as err:
            raise ValueError(f"{FAIL}Reading {path.joinpath(f)} failed.{ENDC} {repr(err)}")
    return data

    return


def read_toml(path: Path) -> dict:
    print(f"{INFO}INFO: reading validation file: {path}.{ENDC}")
    try:
        validation = toml.load(path)
    except FileNotFoundError as err:
        raise FileNotFoundError(f"{FAIL}Wrong path to validation file: {path}.{ENDC}") from err
    except toml.decoder.TomlDecodeError as err:
        _, ex_value, _ = sys.exc_info()
        raise ValueError(f"{FAIL}Wrong fromat of validation file: {ex_value}.{ENDC}") from err
    return validation

if __name__ == "__main__":
    main()
