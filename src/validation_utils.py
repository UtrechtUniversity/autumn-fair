import pandas as pd

# Colors
INFO = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

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
    List of tuples [(data_name, column_name, found_type, expected_type)]

    """
    output = []
    
    for data_name in data:
        if data_name == "host_events.csv":
            section = "events"
        else:
            section = data_name.split(".")[0]
        for var_name in validation[section]:
            if var_name in data[data_name].columns:
                if isinstance(validation[section][var_name]["type"], list):
                    res = [type_is_equal(str(data[data_name][var_name].dtype), t) 
                                for t in validation[section][var_name]["type"]]
                    if not any(res):
                        output.append((data_name, var_name,
                                       str(data[data_name][var_name].dtype),
                                       validation[section][var_name]['type']
                                       ))
                elif not type_is_equal(str(data[data_name][var_name].dtype),
                                     validation[section][var_name]["type"]):
                    output.append((data_name, var_name,
                                   str(data[data_name][var_name].dtype),
                                   validation[section][var_name]['type']
                                   ))
    return output

def check_column_exists(data: dict, validation: dict) -> list:
    """Iterate over all csv files and check if all columns are present.

    Parameters
    ----------
    data:
        Dictionary mapping from filename to Pandas.DataFrame
    validation:
        Dictionary rendered from the validation toml.

    Returns                                                                                                -------                                                                                                List of tuples [(data_name, missing_column_name)]

    """
    missing = []
    for data_name in data:
        if data_name == "host_events.csv":
            section = "events"
        else:
            section = data_name.split(".")[0]
        for var_name in validation[section]:
            if not var_name in data[data_name].columns:
                missing.append((data_name, var_name))
    return missing

def check_column_clusters(cols: dict, data_frame: pd.DataFrame):
    """Check if rows of cluster columns are defined, return row and col names if not.

    cols: dict
        Mapping from cluster name to column names. E.g. cols["event"] = ["event_day", "event_time", "event_type"]
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
    """Check if all values in the column are unique."""
    return df[col_name].nunique() == len(df[col_name])

def find_none_values(df: pd.DataFrame, col_name: str):
    """Check if all values in the column contains None."""
    return(df[df[col_name].isnull()].index.tolist())

def identifier_checks(data: dict, id_col_names: list) -> bool:
    """Check identifier columns."""

    # check if id columns contain None values
    for col_name in id_col_names:
        for data_name in [d for d in data if col_name in data[d]]:
            res = find_none_values(data[data_name], col_name)
            if len(res) > 0:
                print(f"{FAIL}{data_name} column {col_name} empty cells found in rows\n{res}{ENDC}")
                print("Check no empty cells in ID columns completed.")
                return False

    # check if ids in host.csv and environment.csv are unique 
    if not unique_values(data["hosts.csv"], "host_id"):
        print(f"{FAIL}hosts.csv: Column host_id contains duplicates.{ENDC}")
        return False
    if not unique_values(data["environment.csv"], "environment_id"):
        print(f"{FAIL}environment.csv: Column environment_id contains duplicates.{ENDC}")
        return False
    
    #TODO: generalise the tuple (file, id_col)
    ids = {}
    ids["host_id"] = data["hosts.csv"]["host_id"].unique()
    ids["environment_id"] = data["environment.csv"]["environment_id"].unique()
    
    for col_name in id_col_names:
        for data_name in [d for d in data if col_name in data[d]]:
            if not set(data[data_name][col_name]).issubset(ids[col_name]):
                print(f"{FAIL}File {data_name} contains undefined ids in column {col_name}:")
                print(set(data[data_name][col_name]).difference(ids[col_name]))
                print(ENDC)
                #return False

    return True
