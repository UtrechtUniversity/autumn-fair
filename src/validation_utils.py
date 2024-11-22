"""Functionality for the validatuion pipeline."""

import pandas as pd

# Colors
INFO = "\033[93m"
FAIL = "\033[91m"
ENDC = "\033[0m"


def print_output(text: str, type_out: str):
    """Print text as info or error."""
    if type_out == "info":
        print(f"{INFO}INFO {text}{ENDC}")
    elif type_out == "fail":
        print(f"{FAIL}ERROR {text}{ENDC}")


def type_is_equal(col_type: str, val_type: str) -> bool:
    """Compare column types to types in the validation.toml."""
    # string
    if col_type == "object" and val_type == "string":
        return True
    # float
    if col_type.startswith("float") and val_type == "float":
        return True
    # integer
    if col_type.startswith("int") and val_type.startswith("int"):
        return True
    return False


def check_column_types(data: dict, validation: dict) -> list:
    """Iterate over all csv files and check whether columns are well formatted.

    Parameters
    ----------
    data:
        Dictionary mapping from filename to Pandas.DataFrame
    validation:
        Dictionary rendered from the validation toml.

    Returns
    -------
    Columns that did not pass the test, in which csv file they are located,
    their actual type and the expected type.
        List of tuples [(data_name, column_name, found_type, expected_type)]

    """
    output = []

    for data_name, df in data.items():
        if data_name == "host_events.csv":
            section = "events"
        else:
            section = data_name.split(".")[0]
        for var_name in validation[section]:
            if var_name in df.columns:
                # The type of the var_name (column) can be a list of allowed types
                type_is_list = isinstance(validation[section][var_name]["type"], list)
                if type_is_list:
                    type_list = validation[section][var_name]["type"]
                    # compare the actual type to each of the types in the list
                    res = [type_is_equal(str(df[var_name].dtype), t) for t in type_list]
                    if not any(res):
                        output.append(
                            (
                                data_name,
                                var_name,
                                str(df[var_name].dtype),
                                validation[section][var_name]["type"],
                            )
                        )
                else:
                    if not type_is_equal(
                        str(df[var_name].dtype), validation[section][var_name]["type"]
                    ):
                        output.append(
                            (
                                data_name,
                                var_name,
                                str(data[data_name][var_name].dtype),
                                validation[section][var_name]["type"],
                            )
                        )
    return output


def check_column_exists(data: dict, validation: dict) -> list:
    """Iterate over all csv files and check if all columns are present.

    Parameters
    ----------
    data:
        Dictionary mapping from filename to Pandas.DataFrame
    validation:
        Dictionary rendered from the validation toml.

    Returns
    -------
    List of tuples [(data_name, missing_column_name)]

    """
    missing = []
    for data_name, df in data.items():
        if data_name == "host_events.csv":
            section = "events"
        else:
            section = data_name.split(".")[0]
        for var_name in validation[section]:
            if var_name not in df.columns:
                missing.append((data_name, var_name))
    return missing


def find_empty_columns(data: dict) -> list:
    """Iterate over all csv files and find columns which are empty.

    Parameters
    ----------
    data:
        Dictionary mapping from filename to Pandas.DataFrame
    validation:
        Dictionary rendered from the validation toml.

    Returns
    -------
    List of tuples [(data_name, empty_column_name)]

    """
    empty = []
    for data_name, df in data.items():
        empty_cols = [col for col in df.columns if df[col].isnull().all()]
        empty.extend(list(zip([data_name] * len(empty_cols), empty_cols)))
    return empty


def check_categorical_values(col: pd.core.series.Series, cat_values: list) -> list:
    """Return list of values in a column which do not match any categorical values."""
    return set(col.unique()).difference(cat_values)


def check_column_values(data: dict, validation: dict) -> list:
    """Find all columns with categorical values and check them.

    Parameters
    ----------
    data:
        Dictionary mapping from filename to Pandas.DataFrame
    validation:
        Dictionary rendered from the validation toml.

    Returns
    -------
        List of tuples [(data_name, column_name, list of values that do not match)]
    """
    unexpected_values = []
    for data_name, df in data.items():
        if data_name == "host_events.csv":
            section = "events"
        else:
            section = data_name.split(".")[0]
        for var_name in validation[section]:
            if var_name in df.columns and "values" in validation[section][var_name]:
                cat_values = validation[section][var_name]["values"]
                col = data[data_name][var_name]
                if len(col) == 0:
                    unexpected_values.append(
                        (data_name, var_name, "no data in column")
                    )
                else:
                    unexpected_values.append(
                        (data_name, var_name, check_categorical_values(col, cat_values))
                    )
    # remove empty sets
    res = [vals for vals in unexpected_values if len(vals[2]) > 0]
    return res


def check_column_clusters(cols: dict, data_frame: pd.DataFrame) -> list:
    """Check if row contains values in all columns of the cluster.

    Return row and col names if not.

    cols: dict
        Mapping from cluster name to column names.
        E.g. cols["event"] = ["event_day", "event_time", "event_type"]
    """
    result = []
    for items in cols.values():
        if set(items).issubset(data_frame.columns):
            df = data_frame[items]
            df_na = df[df.isna().any(axis=1)]
            for index, row in df_na.iterrows():
                if not pd.isna(row).all():
                    result.append((index, items))
    return result


def unique_values(df: pd.DataFrame, col_name: str):
    """Check if all values in the column are unique and not None."""
    return df[col_name].nunique() == len(df[col_name])


def find_none_values(df: pd.DataFrame, col_name: str):
    """Check if all values in the column contains None."""
    return df[df[col_name].isnull()].index.tolist()


def identifier_checks(data: dict, id_col_names: list) -> bool:
    """Check identifier columns."""

    # check if id columns contain None values
    for col_name in id_col_names:
        for data_name in [d for d in data if col_name in data[d]]:
            res = find_none_values(data[data_name], col_name)
            if len(res) > 0:
                msg = f"{data_name} column {col_name} empty cells found in rows\n{res}"
                print_output(msg, "fail")
                print("Completed check for empty cells in ID columns.")
                return False

    # check if ids in host.csv and environment.csv are unique
    if not unique_values(data["hosts.csv"], "host_id"):
        print_output("hosts.csv: Column host_id contains duplicates.", "fail")
        return False
    if not unique_values(data["environment.csv"], "environment_id"):
        print_output(
            "environment.csv: Column environment_id contains duplicates.", "fail"
        )
        return False

    # TODO: generalise the tuple (file, id_col)
    ids = {}
    ids["host_id"] = data["hosts.csv"]["host_id"].unique()
    ids["environment_id"] = data["environment.csv"]["environment_id"].unique()

    for col_name in id_col_names:
        for data_name in [d for d in data if col_name in data[d]]:
            if not set(data[data_name][col_name]).issubset(ids[col_name]):
                msg = (
                    f"File {data_name} contains undefined ids in column {col_name}:\n"
                    f"{set(data[data_name][col_name]).difference(ids[col_name])}"
                )
                print_output(msg, "fail")
                return False

    return True
