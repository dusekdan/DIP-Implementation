# Module Loading Strategy

I would like to make my tool as extensible and reusable as possible and therefore I am planning on supporting basic dependencies between modules.

Method `get_deps()` or `get_dependencies()` (undecided yet) will return either `dependency dictionary` or `dependency object` of the structure similar to the following one:

```json
{
    "depends_on": "module_name",
    "dependency_type": "output|processor|presenter", // Should tell the module runner when the dependent module can be run and on what data.
    "is_essential": "True|False", // If dependency is essential and can not be satisfied the module can not be run.
}
```

At the moment, the basic idea of how the tool will run is the following: 

1. `run.py` is started and the module discovery takes place (searches `modules` folder for modules there)
2. Based on values returned from `get_dependencies()` method, modules are classified to `independent`, `satisfiably_dependent` and `nonsatisfiably_dependent`.
3. `independent` modules are run and their results and state are stored (e.g. _module X, run finished, module results object_)
4. `satisfiably_dependent` modules are checked for modules that can be run (e.g. their `get_dependencies()` can be satisfied from the results of modules that were run already)
5. // Dependent modules should be able to specify what kind of information they want from the results object provided (or maybe the whole object will be passed automagically)
6. Dependent modules that can be run are run and the process from _(4)_ is repeated. If no modules can be run for 5 rounds, terminate execution and report it as a problem.