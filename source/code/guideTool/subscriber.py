from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber
from mojo.extensions import getExtensionDefault
from .defaults import extensionIdentifier
from .smart import parseRules, matchGlyphRules

class GuideToolSubscriber(Subscriber):

    debug = False

    def build(self):
        self.loadDefaults()

    def loadDefaults(self):
        self.macros = getExtensionDefault(extensionIdentifier + ".smartMacros")
        self.toggleGuidelines()

    def roboFontDidChangePreferences(self, info):
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
            if hasattr(guideline, "naked"):
                guideline = guideline.naked()
            rules = guideline.lib.get(extensionIdentifier + ".rules")
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