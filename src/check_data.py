import toml
import pandas as pd
from pathlib import Path


def read_toml(path: Path) -> dict:
    return toml.load(path)

def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(Path)

def flatten_list_of_dicts(key: str, val: str, data: list) -> dict:
    return {item[key]: item[val] for item in data}

def verify_col_by_section(section: str, df: pd.DataFrame, validation: dict):
    if not section in validation:
        print(f"{section} not present in validation toml file")
        return

    name_to_type = flatten_lists_of_dicts('name', 'type', validation[section]['columns'])

    undefined = []

    for name in name_to_type:
        if name not in df.columns:
            undefined.append((name, None, None))
        else:
            if str(df[name].dtype) != name_to_type[name]:
                undefined.append((name, str(df[name].dtype), name_to_type[name]))

    return undefined

df = pd.read_csv("data/dataE.csv")
validation = toml.load("data/metadata_test/_validation_schema.toml")

for section in validation:
    undefined = verify_col_by_section(section, df, validation)
    print(f"Result for section {section}")
    for col, act_type, exp_type in undefined:
        if act_type is None:
            print(f"Undefined column: {col}")
        else:
            print(f"{col} expected type {exp_type} but found {act_type}.")

