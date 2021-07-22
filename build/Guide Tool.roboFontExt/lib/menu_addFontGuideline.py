import AppKit
from fontParts.world import CurrentGlyph
from mojo.UI import getDefault, CurrentGlyphWindow
from guideTool.guess import guessPositionAndAngleFromSelectedPoints
from guideTool.editor import GuidelineEditorController

def run():
    glyph = CurrentGlyph()
    if glyph is None:
        return
    font = glyph.font
    editor = CurrentGlyphWindow()
    data = guessPositionAndAngleFromSelectedPoints(glyph)
    if data is None:
        AppKit.NSBeep()
        return
    with font.undo("Add Guide"):
        guideline = font.appendGuideline(**data)
    GuidelineEditorController(guideline, glyph, editor.getGlyphView())

if __name__ == "__main__":
    run()
