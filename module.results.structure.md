# Structure returned by module

When `get_results()` or similarly named method is called on the module, the retuned data should have the following structure:

```json
{
    "nonparsible" : [
        {"objectProp' : 'propValue', 'otherProp' : 4},
        {'objectProp' : 'propValue', 'otherProp' : 2},
    ],

    'parsible' : {
        'preferredProcessorName' => [
            {'objectX' : 'Value', ...},
            {'objectX' : 'Value', ...},
        ],
        'differentProcessorName' => [
            {'prop': 'xxx', 'prop2', 'xxxy'},
            {'prop': 'dxd', 'prop2', 'cxc'}
        ]
    }
}
```

This way, the entry point (`run.py`) will be able to call given modules' presenters to present nonparsible artifacts (contained withing the `nonparsible` collection).

The parsible artifacts (`parsible`) are stored within the property of `parsible` object, where the property name always says which processor should be used for further processing of these artifacts. It is expected that the processing will always go on for as long as either 1) only `nonparsible` artifacts are returned, or 2) processor name does not correspond to any available processor.