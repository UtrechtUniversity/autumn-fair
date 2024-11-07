"""Commandline tool to check and validate csv files."""

import argparse
import tomllib
import sys
import pprint
from pathlib import Path
import pandas as pd

from validation_utils import (
    check_column_types,
    check_column_exists,
    find_empty_columns,
    check_column_values,
    check_column_clusters,
    identifier_checks,
    print_output,
)

# Location of this file
PATH = Path.absolute(Path(__file__))

# Files to validate
CSV_FILE_NAMES = [
    "environment_events.csv",
    "environment.csv",
    "host_events.csv",
    "hosts.csv",
]

# Max number of results printed to screen
MAX_NUM_RES = 10
COUNT = 0

def main() -> None:
    """CLI."""
    global COUNT

    parser = argparse.ArgumentParser(
        prog="CSV file validation",
        description="Validates the formatting and typing of csv files.",
    )

    parser.add_argument(
        "-d",
        "--data",
        help="The path to the data folder containing the csv files.",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "-c",
        "--configfile",
        help="The path to the validation.toml.",
        type=Path,
        default=PATH.parent.parent
        / "data"
        / "metadata_test"
        / "_validation_schema_v2.toml",
    )

    parser.add_argument(
        "-s",
        "--sep",
        help="Separator between columns in csv files. \n Tab separator: tab. Default: ;",
        type=str,
        default=";",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="Get more output in the single steps of the pipeline to debug.",
        action="store_true",
    )

    parser.add_argument(
        "-y",
        help="Run all validation steps.",
        action="store_true",
    )

    args, _ = parser.parse_known_args()

    # For tab separated files
    if args.sep == "tab":
        args.sep = "\t"

    # read in toml file
    validation = read_toml(args.configfile)
    if args.verbose is True:
        print("DEBUG: validation.toml.")
        pprint.pprint(validation)
    # read in data
    data = read_csv_files(args.data, args.sep)
    if args.verbose is True:
        for df_name, df in data:
            print(f"DEBUG:shape of {df_name}: {df.shape}")
    print("Read in csv files: done.")
    _continue_tests(args.y)

    # check if all columns exist
    result = check_column_exists(data, validation)
    for fname, col in result:
        print_output(f"Missing column {col} in {fname}.", "fail")
        if _stop_print(len(result)):
            break
    COUNT = 0
    print("Check if all columns are present: done")

    # find empty columns
    result = find_empty_columns(data)
    for fname, col in result:
        print_output(f"Empty column {col} in {fname}", "fail")
        if _stop_print(len(result)):
            break
    COUNT = 0
    print("Find empty columns: done")
    _continue_tests(args.y)

    # check column types
    result = check_column_types(data, validation)
    for fname, col, found_type, exp_type in result:
        msg = f"TYPE in {fname} column {col}; expected {exp_type}, found {found_type}."
        print_output(msg, "fail")
        if _stop_print(len(result)):
            break
    COUNT = 0
    print("Check column types completed.")
    _continue_tests(args.y)

    # check columns with categorical values e.g. event_type.values = ["M","I","T"]
    result = check_column_values(data, validation)
    for fname, col, unexpected_vals in result:
        if len(unexpected_vals) > 0:
            msg = (
                f"VALUES {fname} column {col} contains {unexpected_vals} --> not accepted."
            )
            print_output(msg, "fail")
        if _stop_print(len(result)):
            break
    print("Check categorical values completed.")
    _continue_tests(args.y)

    # checks on identifier columns
    ids = ["host_id", "environment_id"]
    if identifier_checks(data, ids):
        print("Identifier columns checked successfully.")
    else:
        print("Errors found in identifier columns. Please correct them.")
        _continue_tests(args.y)

    # check dependencies between columns
    for data_name, df in data.items():
        if set(validation["column_dependencies"]["event"]).issubset(df.columns):
            measure = set(validation["column_dependencies"]["measurement"]).issubset(
                df.columns
            )
            inoc = set(validation["column_dependencies"]["inoculation"]).issubset(
                df.columns
            )
            treat = set(validation["column_dependencies"]["treatment"]).issubset(
                df.columns
            )
            if not (measure or inoc or treat):
                print(f"{data_name}: Need also information on either of measurement,")
                print("inoculation or treatment.")
    print("Check if column clusters are present completed.")

    # check rows in each cluster of columns and return rows where single values are missing
    for data_name, df in data.items():
        result = check_column_clusters(validation["column_dependencies"], df)
        if len(result) > 0:
            print(f"{data_name}: found missing values")
            for index, cols in result:
                print(f"Row {index} in columns {cols}.")
                if _stop_print(len(result)):
                    break
            COUNT = 0


def read_csv_files(path: Path, sep: str) -> dict:
    """Read in csv files."""
    if not path.is_dir():
        raise FileNotFoundError(f"{path} does not exist.")
    files = [
        f.name
        for f in path.glob("**/*.csv")
        if f.is_file() and f.name in CSV_FILE_NAMES
    ]
    if not set(files) == set(CSV_FILE_NAMES):
        msg = f"Missing files. Expected {CSV_FILE_NAMES}\nFound {files}"
        raise FileNotFoundError(msg)

    data = {}
    for f in files:
        try:
            data[f] = pd.read_csv(path.joinpath(f), sep=sep)
        except pd.errors.EmptyDataError as err:
            raise ValueError(f"{path.joinpath(f)} is empty.") from err
        except Exception as err:
            raise ValueError(f"Reading {path.joinpath(f)} failed. {repr(err)}") from err
    return data


def read_toml(path: Path) -> dict:
    """Read in toml file."""
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


def _continue_tests(opt_y: bool):
    if opt_y is False:
        text = input("Continue tests? (ENTER/n)")
        if text in ["n", "N", "no", "No", "NO"]:
            sys.exit(0)

def _stop_print(total_num) -> bool:
    global COUNT
    COUNT += 1
    if COUNT == MAX_NUM_RES - 1:
        print(f"First {MAX_NUM_RES} results out of {total_num}.")
        return True
    return False



if __name__ == "__main__":
    main()
