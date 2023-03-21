import AppKit
import ezui
from fontTools import unicodedata
from mojo.extensions import getExtensionDefault
from mojo.UI import getDefault
from mojo.events import postEvent
from .defaults import extensionIdentifier
from .smart import parseRules, matchGlyphRules, parseMacros
from .compatibility import getGuidelineLibValue, setGuidelineLibValue

numberTextFieldWidth = 50
noColor = (1.0, 1.0, 1.0, 1.0)

def convertNumberType(number):
    if not isinstance(number, (int, float)):
        number = float(number)
    if not isinstance(number, int):
        asInt = int(number)
        if asInt == number:
            number = asInt
    return number

class GuideToolGuidelineEditor(ezui.TwoColumnForm):

    font = None
    glyph = None
    guideline = None

    def __init__(self,
            callback=None,
            identifier=None,
            container=None,
            controller=None,
            descriptionData={},
            onlyFontLevel=False,
            **kwargs
        ):
        callback = ezui.tools.callback.findCallback(
            callback,
            identifier=identifier,
            controller=controller
        )
        self.externalCallback = callback
        self.onlyFontLevel = onlyFontLevel
        self.defaultColors = getExtensionDefault(extensionIdentifier + ".swatchColors")

        titleColumnWidth = 75
        itemColumnWidth = 175

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

        levelContents = ""
        if not onlyFontLevel:
            levelContents = """
            : Level:
            ( ) Font @levelRadioButtons
            ( ) Glyph
            """

        contents = f"""
        {levelContents}

        : Name:
        [__] @nameTextField

        : Position:
        * HorizontalStack
        > [__] @xPositionTextField
        > [__] @yPositionTextField

        : Angle:
        * HorizontalStack
        > [__]° @angleTextField
        > (Italic Angle) @italicAnglePushButton

        : Color:
        * HorizontalStack
        > * ColorWell @colorColorWell
        > (...) @colorSwatchesPullDownButton

        : Magnetic:
        --X-- @magneticSlider

        :
        [ ] Show Measurements @measurementsCheckbox

        : Rules:
        * VerticalStack
        > [[__]] @rulesTextEditor
        > ((...)) @rulesPullDownButton
        """
        descriptionData = dict(
            levelRadioButtons=dict(),
            nameTextField=dict(),
            xPositionTextField=dict(
                width=numberTextFieldWidth,
                valueType=positionValueType
            ),
            yPositionTextField=dict(
                width=numberTextFieldWidth,
                valueType=positionValueType
            ),
            angleTextField=dict(
                width=numberTextFieldWidth,
                valueType="number"
            ),
            colorColorWell=dict(
                width=numberTextFieldWidth
            ),
            colorSwatchesPullDownButton=dict(
                itemDescriptions=colorSwatchItems
            ),
            magneticSlider=dict(
                minValue=2,
                maxValue=20
            ),
            measurementsCheckbox=dict(),
            rulesTextEditor=dict(
                height=100,
                width=itemColumnWidth
            ),
            rulesPullDownButton=dict(
                image=ezui.tools.makeImage(
                    symbolName="plus",
                    imageName=AppKit.NSImageNameAddTemplate,
                    template=True
                )
            )
        )
        contents = ezui.tools.normalizeContentDescriptions(
            contents,
            descriptionData
        )
        super().__init__(
            contents=contents,
            descriptionData=descriptionData,
            identifier=identifier,
            titleColumnWidth=titleColumnWidth,
            itemColumnWidth=itemColumnWidth,
            callback=self.internalCallback,
            container=container,
            controller=self
        )
        self.haveStartedUndo = False
        self.previousData = self.getItemValues()
        self.enableRulesEditor(startup=True)

    def internalCallback(self, sender):
        if self.guideline is None:
            return
        glyph = self.glyph
        font = self.font
        guideline = self.guideline
        isGlobal = guideline.naked().isGlobal
        data = self.getItemValues()
        if data == self.previousData:
            return
        self.previousData = data
        if not self.haveStartedUndo:
            guideline.naked().prepareUndo("Change Guideline")
            self.haveStartedUndo = True
        name = data["nameTextField"]
        if not name:
            name = None
        x = data["xPositionTextField"]
        if x is None:
            x = guideline.x
        x = convertNumberType(x)
        y = data["yPositionTextField"]
        if y is None:
            y = guideline.y
        y = convertNumberType(y)
        angle = data["angleTextField"]
        if angle is None:
            angle = guideline.angle
        angle = convertNumberType(angle)
        color = data["colorColorWell"]
        if color == noColor:
            color = None
        magnetic = data["magneticSlider"]
        measurements = data["measurementsCheckbox"]
        rules = data["rulesTextEditor"]
        wantsGlobal = True
        if not self.onlyFontLevel:
            wantsGlobal = not data["levelRadioButtons"]
            if isGlobal != wantsGlobal:
                if wantsGlobal:
                    glyph.removeGuideline(guideline)
                    guideline = font.appendGuideline(
                        guideline=guideline.copy()
                    )
                else:
                    font.removeGuideline(guideline)
                    guideline = glyph.appendGuideline(
                        guideline=guideline.copy()
                    )
                self.guideline = guideline
        guideline.name = name
        guideline.x = x
        guideline.y = y
        guideline.angle = angle
        guideline.color = color
        guideline.magnetic = magnetic
        guideline.showMeasurements = measurements
        if wantsGlobal:
            parsed = parseRules(rules, macros={})
            if isinstance(parsed, str):
                # XXX mark the text as invalid
                # parsed will be an error string
                pass
            else:
                setGuidelineLibValue(
                    guideline,
                    extensionIdentifier + ".rules",
                    rules
                )
        self.enableRulesEditor()
        postEvent(
            extensionIdentifier + ".guidelineEditedInEditor",
            guideline=self.guideline
        )
        if self.externalCallback is not None:
            self.externalCallback(self)

    def enableRulesEditor(self, startup=False):
        rulesEditor = self.getItem("rulesTextEditor")
        if self.guideline is None:
            rules = ""
            editable = False
        else:
            editable = self.guideline.glyph is None
            if not startup:
                if rulesEditor.getNSTextView().isEditable() == editable:
                    return
            if not editable:
                rules = ""
            else:
                rules = getGuidelineLibValue(
                    self.guideline,
                    extensionIdentifier + ".rules",
                    ""
                )
                self.buildRulesPullDownButtonItems()
        rulesEditor.set(rules)
        rulesEditor.getNSTextView().setEditable_(editable)

    def colorSwatchesPullDownButtonCallback(self, sender):
        button = self.getItem("colorSwatchesPullDownButton")
        identifier = button.getMenuItemIdentifier(sender)
        if identifier == "default":
            color = None
        else:
            i = int(identifier.split("_")[-1])
            color = self.defaultColors[i]
        colorWell = self.getItem("colorColorWell")
        # XXX
        if color is None:
            color = noColor
        colorWell.set(tuple(color))
        self.internalCallback(self)

    def italicAnglePushButtonCallback(self, sender):
        angleTextField = self.getItem("angleTextField")
        angle = self.font.info.italicAngle
        if angle is None:
            angle = 0
        angle += 90
        angleTextField.set(angle)
        self.internalCallback(self)

    def buildRulesPullDownButtonItems(self):
        # XXX
        # ezui doesn't allow setting a menu after
        # contruction. this needs to change. until
        # then, here's a hack.
        button = self.getItem("rulesPullDownButton")
        items = getRuleSuggestionMenuItems(
            self.font,
            self.glyph,
            self.rulesPullDownButtonItemCallback
        )
        nsButton = button.getNSPopUpButton()
        imageItem = nsButton.itemAtIndex_(0)
        nsButton.removeAllItems()
        menu = nsButton.menu()
        menu.addItem_(imageItem)
        ezui.tools.buildMenuItems(
            item=button,
            descriptions=items,
            menu=menu,
            controller=self
        )

    def rulesPullDownButtonItemCallback(self, sender):
        title = sender.title()
        rulesEditor = self.getItem("rulesTextEditor")
        text = rulesEditor.get().strip() + "\n" + title.split("#")[0].strip()
        text = text.strip()
        rulesEditor.set(text)
        self.internalCallback(self)

    def setObjects(self, font, glyph, guideline):
        self.font = font
        self.glyph = glyph
        self.guideline = guideline
        color = guideline.color
        if color is None:
            color = noColor
        isGlobal = guideline.naked().isGlobal
        data = dict(
            nameTextField=guideline.name,
            xPositionTextField=guideline.x,
            yPositionTextField=guideline.y,
            angleTextField=guideline.angle,
            colorColorWell=color,
            magneticSlider=guideline.magnetic,
            measurementsCheckbox=guideline.showMeasurements,
            # rulesTextEditor will be handled by enableRulesEditor
        )
        if not self.onlyFontLevel:
            data["levelRadioButtons"] = not isGlobal
        self.setItemValues(data)
        self.enableRulesEditor()

    def closeUndoState(self):
        if self.haveStartedUndo:
            self.guideline.naked().performUndo()


ezui.registerClass("GuideToolGuidelineEditor", GuideToolGuidelineEditor)


# Rule Suggestions

categories = {
    "Cc" : "Control",
    "Cf" : "Format",
    "Co" : "Private Use",
    "Cs" : "Surrrogate",
    "Ll" : "Lowercase Letter",
    "Lm" : "Modifier Letter",
    "Lo" : "Other Letter",
    "Lt" : "Titlecase Letter",
    "Lu" : "Uppercase Letter",
    "Mc" : "Spacing Mark",
    "Me" : "Enclosing Mark",
    "Mn" : "Nonspacing Mark",
    "Nd" : "Decimal Number",
    "Nl" : "Letter Number",
    "No" : "Other Number",
    "Pc" : "Connector Punctuation",
    "Pd" : "Dash Punctuation",
    "Pe" : "Close Punctuation",
    "Pf" : "Final Punctuation",
    "Pi" : "Initial Punctuation",
    "Po" : "Other Punctuation",
    "Ps" : "Open Punctuation",
    "Sc" : "Currency Symbol",
    "Sk" : "Modifier Symbol",
    "Sm" : "Math Symbol",
    "So" : "Other Symbol",
    "Zl" : "Line Separator",
    "Zp" : "Paragraph Separator",
    "Zs" : "Space Separator"
}

def getRuleSuggestionMenuItems(font, glyph, callback):
    def makeItem(text):
        item = dict(
            text=text,
            callback=callback
        )
        return item

    items = []
    macros = getExtensionDefault(extensionIdentifier + ".smartMacros")
    macros = parseMacros(macros)
    # glyph suggestions
    if glyph is not None:
        unicodeData = font.asDefcon().unicodeData
        glyphName = glyph.name
        uni = unicodeData.pseudoUnicodeForGlyphName(glyphName)
        script = None
        if uni is not None:
            script = unicodedata.script(chr(uni))
        category = unicodeData.categoryForGlyphName(glyphName)
        matchedMacros = set()
        for name, rules in macros.items():
            if matchGlyphRules(rules, glyph):
                matchedMacros.add(name)
        # macros
        for macro in matchedMacros:
            item = makeItem(
                text=f"macro: {macro}"
            )
            items.append(item)
        # name patterns
        item = makeItem(
            text=f"name: {glyphName.split('.')[0]}.*"
        )
        items.append(item)
        if "." in glyphName and not glyphName.startswith("."):
            extension = glyphName.split(".", 1)[-1]
            item = makeItem(
                text=f"name: *.{extension}"
            )
            items.append(item)
        # script
        if script:
            item = makeItem(
                text=f"script: {script} # {unicodedata.script_name(script)}"
            )
            items.append(item)
        # category
        if category:
            item = makeItem(
                text=f"category: {category} # {categories.get(category)}"
            )
            items.append(item)
        # groups
        for groupName, contents in sorted(font.groups.items()):
            if glyphName in contents:
                item = makeItem(
                    text=f"group: {groupName}"
                )
                items.append(item)
        # divider
        items.append("---")
    # default suggestions
    # macros
    if macros:
        macroItems = dict(
            text="Macros",
            descriptions=[]
        )
        for macro in sorted(macros.keys()):
            item = makeItem(
                text=f"macro: {macro}"
            )
            macroItems["descriptions"].append(item)
        items.append(macroItems)
    # groups
    groups = [groupName for groupName in font.groups.keys() if not groupName.startswith("public.kern")]
    if groups:
        groupItems = dict(
            text="Groups",
            descriptions=[]
        )
        for groupName in sorted(groups):
            item = makeItem(
                text=f"group: {groupName}"
            )
            groupItems["descriptions"].append(item)
        items.append(groupItems)
    # scripts
    scriptItems = dict(
        text="Scripts",
        descriptions=[
            makeItem(text=f"script: {tag} \t# {name}")
            for tag, name in unicodedata.Scripts.NAMES.items()
        ]
    )
    items.append(scriptItems)
    # categories
    categoryItems = dict(
        text="Categories",
        descriptions=[
            makeItem(text=f"category: {tag} \t# {name}")
            for tag, name in categories.items()
        ]
    )
    items.append(categoryItems)
    return items