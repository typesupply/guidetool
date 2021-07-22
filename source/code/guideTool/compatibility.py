# -------------
# Guideline Lib
# -------------

def getIdentifier(guideline):
    if hasattr(guideline, "getIdentifier"):
        return guideline.getIdentifier()
    return guideline.generateIdentifier()

def getGuidelineLib(guideline):
    parent = None
    if hasattr(guideline, "glyph"):
        parent = guideline.glyph
    if parent is None:
        parent = guideline.font
    guidelineLibs = parent.lib.get("public.objectLibs", {})
    return guidelineLibs.get(getIdentifier(guideline), {})

def setGuidelineLib(guideline, value):
    parent = None
    if hasattr(guideline, "glyph"):
        parent = guideline.glyph
    if parent is None:
        parent = guideline.font
    guidelineLibs = parent.lib.get("public.objectLibs", {})
    guidelineLibs[getIdentifier(guideline)] = value
    parent.lib["public.objectLibs"] = guidelineLibs

def getGuidelineLibValue(guideline, key, fallback=None):
    lib = getGuidelineLib(guideline)
    return lib.get(key, fallback)

def setGuidelineLibValue(guideline, key, value):
    lib = getGuidelineLib(guideline)
    if value is None:
        if key in lib:
            lib.pop(key)
    else:
        lib[key] = value
    setGuidelineLib(guideline, lib)