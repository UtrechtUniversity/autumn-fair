"""Commandline tool to check and validate csv files."""

import argparse
import toml
import sys
import pandas as pd
import pprint

from pathlib import Path

from validation_utils import *

# Location of this file
PATH = Path.absolute(Path(__file__))

# Files to validate
CSV_FILE_NAMES = ['environment_events.csv', 'environment.csv', 'host_events.csv', 'hosts.csv']

# Max number of results printed to screen
MAX_NUM_RES = 25


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

    parser.add_argument(
            "-v",
            "--verbose",
            help="Get more output in the single steps of the pipeline to debug.",
            action='store_true'
            )

    args, _ = parser.parse_known_args() 
   
    # For tab separated files
    if args.sep == "tab":
        args.sep = "\t"

    # read in toml file
    validation = read_toml(args.configfile)
    if args.verbose == True:
        print(f"DEBUG: validation.toml.")
        pprint.pprint(validation)
    # read in data
    data = read_csv_files(args.data, args.sep)
    if args.verbose == True:
        for df_name in data:
            print(f"DEBUG:shape of {df_name}: {data[df_name].shape}")
    print("Read in csv files done.")

    # check if all columns exist
    result = check_column_exists(data, validation)
    counter = 0
    for fname, col in result:
        print(f"{FAIL}Missing column {col} in {fname}.{ENDC}")
        counter+=1
        if counter == MAX_NUM_RES-1:
            print(f"First {MAX_NUM_RES} results out of {len(result)}")
            break
    print("Check if all columns are present in the csv completed.")

    # check column types
    result = check_column_types(data, validation)
    counter = 0
    for fname, col, fount_type, exp_type in result:
        print(f"{FAIL}TYPE in {fname} column {col}; expected {exp_type}, found {fount_type}.{ENDC}")
        counter+=1
        if counter == MAX_NUM_RES-1:
            print(f"First {MAX_NUM_RES} results out of {len(result)}")
            break
    print("Check column types completed.")

    # checks on identifier columns
    ids = ["host_id", "environment_id"]
    if identifier_checks(data, ids):
        print("Identifier columns checked successfully.")
    else:
        print("Errors found in identifer columns. Please correct them.")
        return(-1)

    # check dependencies between columns
    for data_name in data:
        if set(validation["column_dependencies"]["event"]).issubset(data[data_name].columns):
            measure = set(validation["column_dependencies"]["measurement"]).issubset(
                        data[data_name].columns)
            inoc = set(validation["column_dependencies"]["inoculation"]).issubset(
                        data[data_name].columns)
            treat = set(validation["column_dependencies"]["treatment"]).issubset(
                        data[data_name].columns)
            if not (measure or inoc or treat):
                print(f"{data_name}: Need also information on either of measurement,")
                print("inoculation or treatment.")

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
