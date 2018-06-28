# Task file converter

Converts edat or psychopy csv files to tsv used in bids

Requires a context.LogConfig object in the Project info of the file it is being run on
Schema is as follows:

```
"context" : {
	"LogConfig": {
		"Task_1_Name" : {
			"initialScannerEvent": {
				"type": "string",
				"description": "The name of the event that begins a run"
			},
			"events": {
				"type": "array",
				"description": "A list of event names that should be parsed into the tsv"
			},
			"response_time": {
				"type": "boolean",
				"description": "Wether or not to include the response time",
				"default": False
			},
			"trial_type": {
				"type": "string",
				"description": "The column header that should be used to determine the trial type"
			},
			"stimuli": {
				"type": "string",
				"description": "The column header to use for the stim file"
			},
			"skip-rows": {
				"type": "number",
				"description": "Number of rows for the csv that should be skipped before the log starts",
				"default": 0
			},
			"accuracy": {
				"type": "string",
				"description": "Column to use for accuracy",
				"defualt": "{event}.ACC"
			},
			"onset": {
				"type": "string",
				"description": "Column to use for event onset",
				"default": "{event}.OnsetTime"
			},
			"next_onset": {
				"type": "string",
				"description": "In case there is no dedicated column for duration, column that marks end of current event"
			},
			"csv_null_values": {
				"type": "array",
				"description": "List of values to use as null for csv's",
				"default": ["", "NULL"]
			},
			"null_output": {
				"type": "string",
				"description": "What value to write out when no value is present",
				"default": "n/a"
			},
			"start_run": {
				"type": "number",
				"description": "Number to start counting run numbers from",
				"default": 0
			}
		},
		"Task_2":{...}
	}
}
```

The file's name will be matched against one of the event names. If the file's name is Something_Event_1.csv, it will match to the object associated with "Event_1" in the LogConfig.

The outputs of the gear will default to the name of the input file (with a different extension as the output will be a tsv). If there are multiple runs present in the file, the gear will output a separate file for each run in the form `{input_file_name}_run-#.tsv`.
There is an option in the gear configuration to manually set the file name of the output, the run number will still be appended and the extension will still be .tsv.
