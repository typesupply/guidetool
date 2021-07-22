from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber
from mojo.extensions import getExtensionDefault
from mojo.events import addObserver, removeObserver
from .defaults import extensionIdentifier
from .smart import parseRules, matchGlyphRules, parseMacros
from .compatibility import getGuidelineLibValue

class GuideToolSubscriber(Subscriber):

    debug = False

    def build(self):
        self.loadDefaults()
        addObserver(
            self,
            "extensionDefaultsChanged",
            extensionIdentifier + ".defaultsChanged"
        )

    def destroy(self):
        removeObserver(
            self,
            extensionIdentifier + ".defaultsChanged"
        )

    def loadDefaults(self):
        macros = getExtensionDefault(extensionIdentifier + ".smartMacros")
        self.macros = parseMacros(macros)
        self.toggleGuidelines()

    def roboFontDidChangePreferences(self, info):
        self.loadDefaults()

    def extensionDefaultsChanged(self, event):
        self.loadDefaults()

    def glyphEditorDidSetGlyph(self, info):
        self.toggleGuidelines()

    def toggleGuidelines(self):
        editor = self.getGlyphEditor()
        glyph = editor.getGlyph()
        if glyph is None:
            return
        font = glyph.font
        for guideline in font.guidelines:
            rules = getGuidelineLibValue(guideline, extensionIdentifier + ".rules")
            if not rules:
                continue
            rules = parseRules(
                rules,
                macros=self.macros
            )
            try:
                guideline.visible = matchGlyphRules(rules, glyph)
            except AttributeError:
                pass


def main():
    registerGlyphEditorSubscriber(GuideToolSubscriber)

if __name__ == "__main__":
    main()