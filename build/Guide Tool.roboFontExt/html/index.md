Tool:

* drag new guide from edges (command makes it font level)
* double click anywhere there isn't a guide to create a guide
  * command makes it font level
  * option makes it vertical
* marquee to select guides
* click guide to select
* drag to move selected guides
  * command moves the origin
  * option changes the angle
* arrows keys to move selected guides
* double click a guide to edit
* return brings up editor if one guide is selected
* control click to get some clear and convert options

Rule Syntax:

```
# comment
> macro title (only allowed in prefs window)
match: any | all (only allowed once, any is the default)
name: fnmatch pattern
script: unicode tag
category: unicode tag
group: fnmatch pattern
macro: name
```