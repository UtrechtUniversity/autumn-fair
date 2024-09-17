import pandas as pd

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

def check_column_types(data, validation):
    """Iterate over all csv files and check whether columns are well formatted."""
    for data_name in data:
        if data_name == "host_events.csv":
            section = "events"
        else:
            section = data_name.split(".")[0]
        print(f"Checking {data_name} against {section}:")
        for var_name in validation[section]:
            if var_name in data[data_name].columns:
                if not type_is_equal(str(data[data_name][var_name].dtype), validation[section][var_name]["type"]):
                    print(f"{var_name} should be {validation[section][var_name]["type"]}")
                    print(f"\t Found: {str(data[data_name][var_name].dtype)}")
    print("----")

def check_column_exists(data, validation):
    """Iterate over all csv files and check if all columns are present."""
    for data_name in data:
        if data_name == "host_events.csv":
            section = "events"
        else:
            section = data_name.split(".")[0]
        for var_name in validation[section]:
            if not var_name in data[data_name].columns:
                print(f"{data_name}; Column not found: {var_name}")
    print("----")

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