from guideTool.fontEditor import FontGuidelineTableController
from mojo.UI import CurrentGlyphWindow, CurrentFontWindow

font = CurrentFont()
fontOverview = CurrentFontWindow()
if fontOverview is not None:
    FontGuidelineTableController(font, fontOverview)
