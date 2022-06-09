import pprint
import AppKit
import ezui
from mojo.UI import getDefault, CurrentGlyphWindow
from fontParts.fontshell import RGuideline
from lib.fontObjects.fontPartsWrappers import RGuideline
from mojo.extensions import getExtensionDefault
from mojo.events import postEvent
from .defaults import extensionIdentifier
from .smart import parseRules
from .compatibility import getGuidelineLibValue, setGuidelineLibValue

numberTextFieldWidth = 50
noColor = (1.0, 1.0, 1.0, 1.0)

class GuidelineEditorController(ezui.WindowController):

    def build(self, guideline, glyph, glyphEditor):
        self.guideline = guideline
        self.glyph = glyph
        self.editor = glyphEditor

        self.defaultColors = getExtensionDefault(extensionIdentifier + ".swatchColors")

        positionValueType = "number"
        roundTo = getDefault("glyphViewRoundValues", defaultClass=int)
        if roundTo >= 1:
            positionValueType = "integer"

        colorSwatchItems = [
            dict(
                identifier="default",
                text="Default",
                callback="colorSwatchesPullDownButtonCallback"
            )
        ]
        for i, color in enumerate(self.defaultColors):
            w = 50
            h = 5
            image = AppKit.NSImage.alloc().initWithSize_((w, h))
            image.lockFocus()
            AppKit.NSColor.whiteColor().set()
            AppKit.NSRectFill(((0, 0), (w, h)))
            AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(*color).set()
            AppKit.NSRectFillUsingOperation(
                ((0, 0), (w, h)),
                AppKit.NSCompositeSourceOver
            )
            image.unlockFocus()
            colorSwatchItems.append(
                dict(
                    identifier=f"color_{i}",
                    image=image,
                    callback="colorSwatchesPullDownButtonCallback"
                )
            )

        content = """
        = GuideToolGuidelineEditor
        """
        descriptionData = dict()

        self.w = ezui.EZPopUp(
            content=content,
            descriptionData=descriptionData,
            controller=self,
            parent=glyphEditor
        )

    def started(self):
        editor = self.w.getItem("content")
        editor.setObjects(
            self.glyph.font,
            self.glyph,
            self.guideline
        )
        self.w.open()

    def windowWillClose(self, sender):
        editor = self.w.getItem("content")
        editor.closeUndoState()


if __name__ == "__main__":
    editor = CurrentGlyphWindow()
    glyph = CurrentGlyph()
    font = glyph.font
    guideline = font.guidelines[0]
    GuidelineEditorController(guideline, glyph, editor.getGlyphView())