import fnmatch
import defcon

# ------
# Syntax
# ------
#
# # comment
#
# match: any | all (only allowed once, any is the default)
# name: fnmatch pattern
# script: unicode tag
# category: unicode tag
# group: fnmatch pattern
# macro: name

def parseRules(rules, macros=None):
    """

    # match

    >>> r = parseRules(
    ...     "match: any"
    ... )
    >>> _dump(r)
    matchType: any

    >>> r = parseRules(
    ...     "match: all"
    ... )
    >>> _dump(r)
    matchType: all

    >>> r = parseRules(
    ...     "match: xxx"
    ... )
    >>> _dump(r)
    Unknown match type: xxx

    # name

    >>> r = parseRules(
    ...     "name: ABC*"
    ... )
    >>> _dump(r)
    names: ABC*

    >>> r = parseRules(
    ...     '''
    ...     name: ABC*
    ...     name: XYZ?
    ...     '''
    ... )
    >>> _dump(r)
    names: ABC* | XYZ?

    # script

    >>> r = parseRules(
    ...     "script: ABC"
    ... )
    >>> _dump(r)
    scripts: ABC

    >>> r = parseRules(
    ...     '''
    ...     script: ABC
    ...     script: XYZ
    ...     '''
    ... )
    >>> _dump(r)
    scripts: ABC | XYZ

    # category

    >>> r = parseRules(
    ...     "category: ABC"
    ... )
    >>> _dump(r)
    categories: ABC

    >>> r = parseRules(
    ...     '''
    ...     category: ABC
    ...     category: XYZ
    ...     '''
    ... )
    >>> _dump(r)
    categories: ABC | XYZ

    # group

    >>> r = parseRules(
    ...     "group: ABC*"
    ... )
    >>> _dump(r)
    groups: ABC*

    >>> r = parseRules(
    ...     '''
    ...     group: ABC*
    ...     group: XYZ?
    ...     '''
    ... )
    >>> _dump(r)
    groups: ABC* | XYZ?

    # macro
    >>> macros = dict(
    ...     macro1=parseRules(
    ...         '''
    ...         name: name1
    ...         name: name2
    ...         script: script1
    ...         script: script2
    ...         category: category1
    ...         category: category2
    ...         group: group1
    ...         group: group2
    ...         '''
    ...     ),
    ...     macro2=parseRules(
    ...         '''
    ...         name: xxx
    ...         script: xxx
    ...         category: xxx
    ...         group: xxx
    ...         '''
    ...     )
    ... )

    >>> r = parseRules(
    ...     '''
    ...     macro: macro1
    ...     ''',
    ...     macros
    ... )
    >>> _dump(r)
    categories: category1 | category2
    groups: group1 | group2
    names: name1 | name2
    scripts: script1 | script2

    >>> r = parseRules(
    ...     '''
    ...     name: aName
    ...     script: aScript
    ...     category: aCategory
    ...     group: aGroup
    ...     macro: macro1
    ...     ''',
    ...     macros
    ... )
    >>> _dump(r)
    categories: aCategory | category1 | category2
    groups: aGroup | group1 | group2
    names: aName | name1 | name2
    scripts: aScript | script1 | script2
    """
    allowMacros = macros is not None
    matchType = None
    names = set()
    scripts = set()
    categories = set()
    groups = set()
    for line in rules.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        tag, content = line.split(":", 1)
        tag = tag.strip()
        content = content.strip()
        if tag == "match":
            if content not in ("any", "all"):
                return f"Unknown match type: {content}"
            matchType = content
        elif tag == "name":
            names.add(content)
        elif tag == "script":
            scripts.add(content)
        elif tag == "category":
            categories.add(content)
        elif tag == "group":
            groups.add(content)
        elif tag == "macro":
            if not allowMacros:
                return "Macros are not allowed."
            macro = macros.get(content, {})
            names |= macro.get("names", set())
            scripts |= macro.get("scripts", set())
            categories |= macro.get("categories", set())
            groups |= macro.get("groups", set())
        else:
            return f"Unknown tag: {tag}."
    rules = dict(
        matchType=matchType,
        names=names,
        scripts=scripts,
        categories=categories,
        groups=groups
    )
    return rules

def matchGlyphRules(rules, glyph):
    """
    >>> font = _makeTestFont()

    # name: any
    >>> rules = dict(
    ...     matchType="any",
    ...     names={"name", "xxx"}
    ... )
    >>> matchGlyphRules(rules, font["name"])
    True

    # name: all
    >>> rules = dict(
    ...     matchType="all",
    ...     names={"name", "xxx"}
    ... )
    >>> matchGlyphRules(rules, font["name"])
    False

    # script: any
    >>> rules = dict(
    ...     matchType="any",
    ...     scripts={"Latin", "xxx"}
    ... )
    >>> matchGlyphRules(rules, font["script"])
    True

    # script: all
    >>> rules = dict(
    ...     matchType="all",
    ...     scripts={"Latin", "xxx"}
    ... )
    >>> matchGlyphRules(rules, font["script"])
    False

    # category: any
    >>> rules = dict(
    ...     matchType="any",
    ...     categories={"Lu", "xxx"}
    ... )
    >>> matchGlyphRules(rules, font["category"])
    True

    # category: all
    >>> rules = dict(
    ...     matchType="all",
    ...     categories={"Lu", "xxx"}
    ... )
    >>> matchGlyphRules(rules, font["category"])
    False

    # group: any
    >>> rules = dict(
    ...     matchType="any",
    ...     groups={"group1", "group2"}
    ... )
    >>> matchGlyphRules(rules, font["group"])
    True

    # group: all
    >>> rules = dict(
    ...     matchType="all",
    ...     groups={"group1", "group2"}
    ... )
    >>> matchGlyphRules(rules, font["group"])
    False
    """
    if not isinstance(glyph, defcon.Glyph):
        glyph = glyph.asDefcon()
    font = glyph.font
    unicodeData = font.unicodeData
    matchType = rules.get("matchType", "any")
    # Names
    for namePattern in rules.get("names", []):
        if matchPattern(glyph.name, namePattern):
            if matchType == "any":
                return True
        else:
            if matchType == "all":
                return False
    # Scripts
    script = unicodeData.scriptForGlyphName(glyph.name)
    if script in rules.get("scripts", []):
        if matchType == "any":
            return True
    else:
        if matchType == "all":
            return False
    # Categories
    category = unicodeData.categoryForGlyphName(glyph.name)
    if category in rules.get("categories", []):
        if matchType == "any":
            return True
    else:
        if matchType == "all":
            return False
    # Groups
    for groupPattern in rules.get("groups", []):
        for groupName, groupContent in font.groups.items():
            if matchPattern(groupName, groupPattern):
                if glyph.name in groupContent:
                    if matchType == "any":
                        return True
                else:
                    if matchType == "all":
                        return False
    # Nothing
    if matchType == "any":
        return False
    else:
        return True

def matchPattern(string, pattern):
    """
    > matchPattern("nameTest1", "nameTest")
    False
    > matchPattern("nameTest1", "nameTest*")
    True
    """
    return fnmatch.fnmatch(string, pattern)


# Test
# ----

def _makeTestFont():
    font = defcon.Font()
    font.newGlyph("name")
    glyph = font.newGlyph("script")
    glyph.unicode = ord("A")
    glyph = font.newGlyph("category")
    glyph.unicode = ord("B")
    font.newGlyph("group")
    font.groups["group1"] = ["group"]
    font.groups["group2"] = []
    return font

def _dump(d):
    if not isinstance(d, dict):
        print(d)
        return
    lines = []
    for key, value in sorted(d.items()):
        if not value:
            continue
        if isinstance(value, set):
            value = " | ".join(sorted(value))
        lines.append(f"{key}: {value}")
    print("\n".join(lines))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
