# Structure returned by module

When `get_results()` or similarly named method is called on the module, the retuned data should have the following structure:

```json
{
    "nonparsible" : [
        {"objectProp': 'propValue', 'otherProp': 4},
        {'objectProp': 'propValue', 'otherProp': 2},
    ],

    'parsible' : {
        'preferredProcessorName' => [
            {'objectX': 'Value', ...},
            {'objectX': 'Value', ...},
        ],
        'differentProcessorName' => [
            {'prop': 'xxx', 'prop2': 'xxxy'},
            {'prop': 'dxd', 'prop2': 'cxc'}
        ]
    }
}
```

This way, the entry point (`run.py`) will be able to call given modules' presenters to present nonparsible artifacts (contained withing the `nonparsible` collection).

The parsible artifacts (`parsible`) are stored within the property of `parsible` object, where the property name always says which processor should be used for further processing of these artifacts. It is expected that the processing will always go on for as long as either 1) only `nonparsible` artifacts are returned, or 2) processor name does not correspond to any available processor.

## RUN results recording

Results returned by each module that has been run need to be stored in memory (so the other modules can take advantage of these results) and if required, on disc too. **Scenario**: SiteCopier module crawles the page and stores request with headers + response with headers into file corresponding to the requested target location. It is not feasible for large targets to store this all in memory and expect other modules to just reach out for it. Instead, these requests should be stored into file on disc and other modules will know where to look for them and take advantage of them.

RUN-Result structure should look something like this.

```json
// Results = 
{ 
    "module_name": {
        "exit_flag": "OK|KO",
        "results": {RESULTS_OBJECT_DEFINED_ABOVE},
        "left_physical_artifcats': True|False
    }
}
```