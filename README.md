# Log repair Tool

## Problem description

This is example of typical DevOps or Administration case.

Logging software output log file containing JSONs but for mistake JSON was pretty formatted with new-lines and in such way was saved to log file.
Log should contains entries like:

```
Datetime Message JSON-data-inline
```

__Example:__

```
2022-05-13 Some text description {"detail_1": "value 1", "detail_2": "value 2", "detail_3": ["value_3-1", "value_3-2", "value_3-3"]}
```

But instead contains:

```
Datetime Message JSON
data
in
multple
lines
```

__Example:__

```
2022-05-13 Some text description {
"detail_1": "value 1",
"detail_2": "value 2",
"detail_3": [
"value_3-1",
"value_3-2",
"value_3-3"]
}
```

## Users need and complication

Users need logs containg JSON data inline.
But not only possibility to convert downloaded logs but also have tool that do this online as some messages from logs are input to other system doing some atomated actions based on messages and JSON data.
Bugfix would be prepared but team is heavy loaded so we have to write as tools doing conversion for historical logs as tool doing conversion online.


## Solution

In repository there are 3 directories with the following tools:
1. generator

  1. Python script simulating program generating such broken logs

    Script generate broken logs and proper logs to use during testing repair tool

2. offline-repair

  1. Python script doing conversion of historical logs

  2. Python script comparing repaired logs with generated for testing

3. online-repair

  1.Go program doing conversion online

