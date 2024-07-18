import toml
import pandas as pd
from pathlib import Path


def read_toml(path: Path) -> dict:
    return toml.load(path)

def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(Path)

def flatten_list_of_dicts(key: str, val: str, data: list) -> dict:
    """Combines the values of two different dictionary keys into a new dictionary.

    Given a list of dictionaries, retrieve the values behind key in one dictionary and
    behind value in another dictionary and return them as new dictionary.
    Example:
    
    data = [{'name': 'host_id',
             'type': ['string', 'int64'],
             'format': 'AA0_00000',
             'unique': True},
            {'name': 'host_groupNumber', 'type': 'integer'},
            {'name': 'host_sex', 'type': 'string', 'format': 'A', 'values': ['M', 'F']},
            {'name': 'host_age', 'type': 'integer'},
            {'name': 'host_death', 'type': 'integer'},
            {'name': 'host_species', 'type': 'string'},
            {'name': 'host_breed', 'type': 'string'}]

    key = "name"
    val = "type"

    Result:
    
    {'host_id': ['string', 'int64'],
     'host_groupNumber': 'integer',
     'host_sex': 'string',
     'host_age': 'integer',
     'host_death': 'integer',
     'host_species': 'string',
     'host_breed': 'string'}
    """

    return {item[key]: item[val] for item in data if key in item and val in item}

def verify_col_by_section(section: str, df: pd.DataFrame, validation: dict):
    if not section in validation:
        print(f"{section} not present in validation toml file")
        return

    name_to_type = flatten_list_of_dicts('name', 'type', validation[section]['columns'])

    undefined = []

    for name in name_to_type:
        if name not in df.columns:
            undefined.append((name, None, None))
        else:
            if  not str(df[name].dtype) in list(name_to_type[name]):
                undefined.append((name, str(df[name].dtype), name_to_type[name]))

    return undefined

def duplicates(column_name: str, df: pd.DataFrame) -> pd.DataFrame:
    return df[df[[column_name]].duplicated()][column_name]

def read_data_from_loc(folder: Path) -> list:
    """
    The data validation expects three csv files in folder:
    ├── data
    │ ├── environment.csv
    │ ├── events.csv
    │ └──hosts.csv

    The function checks of the three files are there and returns each as a
    pandas dataframe.
    
    """
    if not folder.is_dir():
        print(f"{folder} does not exist.")
        return 
    files = [x for x in folder.glob('**/*') if x.is_file()]
    data_parts = []
    for data_file in ["environment.csv", "events.csv", "hosts.csv"]:
        try:
            data_parts.append(pd.read_csv(folder.joinpath(data_file)))
        except FileNotFoundError:
            print(f"{folder.joinpath(data_file)} does not exist.")
            return



# TODO: Goes into a commandline client
# Step 1: Read in the validation.toml
val_path = Path("data/metadata_test/_validation_schema.toml") # param for client
validation = toml.load(val_path)

# Step 2: read in the data folder and assert that all three csv files are there.
data_path = Path("data") # param for client
data_frames = read_data_from_loc(data_path)

# Test functionality
df = pd.read_csv("data/dataE.csv")
# check if all columns are in the dataframe(s) and if their type is correct
for section in validation:
    undefined = verify_col_by_section(section, df, validation)
    print(f"Result for section {section}")
    for col, act_type, exp_type in undefined:
        if act_type is None:
            print(f"Missing column: {col}")
        else:
            print(f"{col} expected type {exp_type} but found {act_type}.")


# check if all values in columns labeled with unique=true
name_to_unique = {}
for section in validation:
    name_to_unique.update(flatten_list_of_dicts('name', 'unique', validation[section]['columns']))

for col in df.columns:
    if col in name_to_unique and name_to_unique[col] == True:
        dupes = duplicates(col, df)
        if len(dupes) > 0:
            print(f"{col} contains {len(dupes)} duplicate entries.")
