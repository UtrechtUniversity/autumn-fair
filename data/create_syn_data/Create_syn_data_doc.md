# Create synthetic data to test the validation pipeline

To test the syntax of the pipeline you can create some synthetic data with `metasyn`.

## Installation

```
pip install metasyn
```

## Configuration and data generation

We provide configuration files to create the four csv files:

```
environment_config.toml
environment_events_config.toml
host_config.toml
host_events_config.toml

environment_events_gmf.json
environment_gmf.json
hosts_events_gmf.json
hosts_gmf.json
```

You can reconfigure the json files (first commands) or directly generate new data from the json-files (second commands)

- environment.csv

	```
	metasyn create-meta  --config environment_config.toml -o environment_gmf.json
	metasyn synthesize environment_gmf.json -o synthetic_data/environment.csv
	```

- environment_events.csv

	```
	metasyn create-meta --config environment_events_config.toml environment_events_gmf.json
	metasyn synthesize  environment_events_gmf.json -o synthetic_data/environment_events.csv
	```
	
- hosts.csv

	```
	metasyn create-meta --config host_config.toml hosts_gmf.json
	metasyn synthesize hosts_gmf.json -o synthetic_data/hosts.csv
	```
	
- host_events.csv

	```
	metasyn create-meta --config host_events_config.toml host_events_gmf.json
	metasyn synthesize host_events_gmf.json -o synthetic_data/host_events.csv
	```
	
### Run the jupyter notebook in /src

