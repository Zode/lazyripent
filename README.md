# lazyripent
tool for mass ripenting

This python script allows you to mass edit bsp files with ripent, comes with a basic syntax to set up conditions ("selectors") and actions ("modifiers"). Code produced in one night so its messy at best ;)
Requires Python3, Steam, and Sven Co-op SDK. Automatically selects 64-bit or 32-bit ripent.

usage: `python lazyripent.py "C:\path\to\bsps" myrules`

```
#cheatsheet
{ 
MATCH "key" "value"
NOTMATCH "key" "value"
HAVE "key"
NOTHAVE "key"
ADD "key" "value"
REMOVE "key"
REPLACE "key" "value",
REPLACE "key" "value?" "parse"
NEWENT "key:value:key:$key"
}
```

See example_rules.txt for further info on how to use the syntax.