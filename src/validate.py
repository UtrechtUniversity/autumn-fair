"""Commandline tool to check and validate csv files."""

import argparse
import tomllib
import sys
import pandas as pd
import pprint

from pathlib import Path

from validation_utils import (check_column_types, check_column_exists,
                              check_column_clusters, identifier_checks,
                              print_output)

# Location of this file
PATH = Path.absolute(Path(__file__))

# Files to validate
CSV_FILE_NAMES = ['environment_events.csv', 'environment.csv', 'host_events.csv', 'hosts.csv']

# Max number of results printed to screen
MAX_NUM_RES = 25
COUNT = 0

def main() -> None:
    """CLI."""
    global COUNT
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
    print("Read in csv files: done.")

    # check if all columns exist
    result = check_column_exists(data, validation)
    for fname, col in result:
        print_output(f"Missing column {col} in {fname}.", "fail")
        COUNT+=1
        if COUNT == MAX_NUM_RES-1:
            print(f"First {MAX_NUM_RES} results out of {len(result)}")
            break
    COUNT = 0
    print("Check if all columns are present in the csv completed.")

    # check column types
    result = check_column_types(data, validation)
    for fname, col, found_type, exp_type in result:
        msg = f"TYPE in {fname} column {col}; expected {exp_type}, found {found_type}."
        print_output(msg, "fail")
        COUNT+=1
        if COUNT == MAX_NUM_RES-1:
            print(f"First {MAX_NUM_RES} results out of {len(result)}")
            break
    COUNT = 0
    print("Check column types completed.")


    # checks on identifier columns
    ids = ["host_id", "environment_id"]
    if identifier_checks(data, ids):
        print("Identifier columns checked successfully.")
    else:
        print("Errors found in identifier columns. Please correct them.")
        #sys.exit()

    # check dependencies between columns
    for data_name, df in data.items():
        if set(validation["column_dependencies"]["event"]).issubset(df.columns):
            measure = set(validation["column_dependencies"]["measurement"]).issubset(df.columns)
            inoc = set(validation["column_dependencies"]["inoculation"]).issubset(df.columns)
            treat = set(validation["column_dependencies"]["treatment"]).issubset(df.columns)
            if not (measure or inoc or treat):
                print(f"{data_name}: Need also information on either of measurement,")
                print("inoculation or treatment.")
    print("Check if column clusters are present completed.")

def read_csv_files(path: Path, sep: str) -> dict:
    if not path.is_dir():
        raise FileNotFoundError(f"{path} does not exist.")
    files = [f.name for f in path.glob('**/*.csv') if f.is_file() and f.name in CSV_FILE_NAMES]
    if not set(files) == set(CSV_FILE_NAMES):
        msg = f"{FAIL}Missing files. Expected {CSV_FILE_NAMES}\nFound {files}{ENDC}"
        raise FileNotFoundError(msg)

    data = {}
    for f in files:
        try:
            data[f] = pd.read_csv(path.joinpath(f), sep=sep)
        except pd.errors.EmptyDataError as err:
            raise ValueError(f"{path.joinpath(f)} is empty.")
        except Exception as err:
            raise ValueError(f"Reading {path.joinpath(f)} failed. {repr(err)}")
    return data

def read_toml(path: Path) -> dict:
    print_output(f"reading validation file: {path}.", "info")
    try:
        with open(path, "rb") as f:
            validation = tomllib.load(f)
        return validation
    except FileNotFoundError as err:
        raise FileNotFoundError(f"Wrong path to validation file: {path}.") from err
    except tomllib.TOMLDecodeError as err:
        _, ex_value, _ = sys.exc_info()
        raise ValueError(f"Wrong fromat of validation file: {ex_value}.") from err
    return validation

if __name__ == "__main__":
    main()