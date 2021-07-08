import math
from collections import namedtuple
import AppKit
import defcon
from booleanOperations.booleanGlyph import BooleanGlyph
from lib.tools import bezierTools
from mojo.events import installTool, BaseEventTool, extractNSEvent
from mojo.UI import getDefault
from .editor import GuidelineEditorController
from .images import guideToolToolbarIcon, guideToolCursor
from .defaults import identifierStub


deleteKeys = [
    AppKit.NSBackspaceCharacter,
    AppKit.NSDeleteFunctionKey,
    AppKit.NSDeleteCharacter,
    chr(0x007F),
]

horizontalAngles = (0, 180)
verticalAngles = (90, 270)
rightAngles = horizontalAngles + verticalAngles


class GuidelineTool(BaseEventTool):

    selectedGuidelines = {}
    selectedGuidelineLayers = {}
    inRectSelection = False
    isDraggingGuidelines = False
    mouseDownPoint = None
    snappingToThesePoints = []
    snapToPointSymbolColor = None

    # prefs
    wantsItalicAngle = True
    wantsSnapToPoint = True
    wantsSnapToFuturePoints = True
    highlightAlphaScale = 0.15

    def setup(self):
        self.loadDefaults()
        container = self.extensionContainer(
            identifier=identifierStub + "background",
            location="background",
            clear=True
        )
        self.marqueeLayer = container.appendRectangleSublayer(
            name="marquee",
            fillColor=self.colorMarquee
        )
        self.selectionIndicatorLayer = container.appendBaseSublayer(
            name="selectionIndicator"
        )
        self.snapToPointsLayer = container.appendBaseSublayer(
            name="snapIndicator"
        )

    def loadDefaults(self):
        self.colorMarquee = getDefault("glyphViewSelectionMarqueColor")
        self.roundValuesTo = getDefault("glyphViewRoundValues", defaultClass=int)
        self.arrowIncrement = float(getDefault("glyphViewIncrement"))
        self.arrowShiftIncrement = float(getDefault("glyphViewShiftIncrement"))
        self.arrowCommandShiftIncrement = float(getDefault("glyphViewCommandShiftIncrement"))
        self.colorGlyphGuideline = getDefault("glyphViewLocalGuidesColor")
        self.colorFontGuideline = getDefault("glyphViewGlobalGuidesColor")
        self.highlightStrokeWidth = getDefault("glyphViewStrokeWidth") * 10
        self.snapToPointSymbolSize = getDefault("glyphViewStrokeWidth") * 40
        self.snapToPointSymbolSettings = dict(
            name="star",
            size=(self.snapToPointSymbolSize, self.snapToPointSymbolSize),
            pointCount=10,
            inner=0.2
        )

    def getToolbarIcon(self):
        return guideToolToolbarIcon

    def getDefaultCursor(self):
        return guideToolCursor

    def preferencesChanged(self):
        self.loadDefaults()
        self.marqueeLayer.setFillColor(self.colorMarquee)

    def currentGlyphChanged(self):
        self.deselectAll()

    def didUndo(self, notification):
        glyph = self.getGlyph()
        font = glyph.font
        glyphGuidelines = glyph.guidelines
        fontGuidelines = font.guidelines
        remove = []
        for guideline in self.selectedGuidelines.keys():
            if guideline in glyphGuidelines:
                continue
            if guideline in fontGuidelines:
                continue
            remove.append(guideline)
        for guideline in remove:
            del self.selectedGuidelines[guideline]
        self.displaySelectedGuidelines()

    def becomeActive(self):
        pass

    def becomeInactive(self):
        self.deselectAll()

    # Display

    def displaySnapToPoints(self):
        container = self.snapToPointsLayer
        if not self.snappingToThesePoints:
            container.clearSublayers()
        else:
            imageSettings = self.snapToPointSymbolSettings
            imageSettings["size"] = (self.snapToPointSymbolSize, self.snapToPointSymbolSize)
            imageSettings["fillColor"] = self.snapToPointSymbolColor
            needed = list(self.snappingToThesePoints)
            remove = []
            for symbol in container.getSublayers():
                point = symbol.getPosition()
                if point in needed:
                    needed.remove(point)
                else:
                    remove.append(symbol)
            if needed or remove:
                with container.sublayerGroup():
                    for point in needed:
                        container.appendSymbolSublayer(
                            position=point,
                            imageSettings=imageSettings
                        )
                    for symbol in remove:
                        container.removeSublayer(symbol)

    def displaySelectedGuidelines(self):
        container = self.selectionIndicatorLayer
        # clear all
        if not self.selectedGuidelines:
            container.clearSublayers()
            self.selectedGuidelineLayers = {}
            return
        # clear subset
        remove = [
            guideline
            for guideline in self.selectedGuidelineLayers.keys()
            if guideline not in self.selectedGuidelines
        ]
        if remove:
            with container.sublayerGroup():
                for guideline in remove:
                    layer = self.selectedGuidelineLayers.pop(guideline)
                    container.removeSublayer(layer)
        add = []
        for guideline in self.selectedGuidelines.keys():
            if guideline in self.selectedGuidelineLayers:
                layer = self.selectedGuidelineLayers[guideline]
                with layer.propertyGroup():
                    startPoint, endPoint = getGuidelinePathPoints(guideline)
                    color = getGuidelineHighlightColor(
                        guideline,
                        self.colorFontGuideline,
                        self.colorGlyphGuideline,
                        self.highlightAlphaScale
                    )
                    layer.setStartPoint(startPoint)
                    layer.setEndPoint(endPoint)
                    layer.setStrokeColor(color)
                    layer.setPosition((guideline.x, guideline.y))
            else:
                add.append(guideline)
        if add:
            with container.sublayerGroup():
                for guideline in add:
                    startPoint, endPoint = getGuidelinePathPoints(guideline)
                    color = getGuidelineHighlightColor(
                        guideline,
                        self.colorFontGuideline,
                        self.colorGlyphGuideline,
                        self.highlightAlphaScale
                    )
                    self.selectedGuidelineLayers[guideline] = container.appendLineSublayer(
                        position=(guideline.x, guideline.y),
                        startPoint=startPoint,
                        endPoint=endPoint,
                        strokeColor=color,
                        strokeWidth=self.highlightStrokeWidth
                    )

    def displayMarquee(self, point=None):
        skip = False
        if not self.inRectSelection:
            skip = True
        elif self.mouseDownPoint is None:
            skip = True
        elif point is None:
            skip = True
        if skip:
            self.marqueeLayer.setVisible(False)
            return
        x1, y1 = self.mouseDownPoint
        x2, y2 = point
        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))
        w = x2 - x1
        h = y2 - y1
        with self.marqueeLayer.propertyGroup():
            self.marqueeLayer.setVisible(True)
            self.marqueeLayer.setPosition((x1, y1))
            self.marqueeLayer.setSize((w, h))

    # Editor

    def openGuidelineEditor(self):
        if len(self.selectedGuidelines) != 1:
            return
        guideline = self.selectedGuideline
        glyph = self.getGlyph()
        glyphEditor = self.getNSView()
        GuidelineEditorController(guideline, glyph, glyphEditor)

    # Interaction

    def getVisibleRect(self):
        (vX, vY), (vW, vH) = self.getNSView().scaledVisibleRect()
        xO, yO = self.getNSView()._offset
        vX -= xO
        vY -= yO
        return ((vX, vY), (vW, vH))

    def mouseDown(self, point, clickCount):
        shouldIgnoreFollowingMouseEvents = False
        self.mouseDownPoint = point
        self.isDraggingGuidelines = False
        self.inRectSelection = False
        modifiers = self.getModifiers()
        shiftDown = modifiers["shiftDown"]
        capLockDown = modifiers["capLockDown"]
        commandDown = modifiers["commandDown"]
        optionDown = modifiers["optionDown"]
        controlDown = modifiers["controlDown"]
        hitGuideline = self.findGuidelineAtPoint(point)
        if hitGuideline:
            # open editor
            if clickCount == 2:
                self.selectedGuidelines = {
                    hitGuideline : getGuidelineState(hitGuideline)
                }
                self.openGuidelineEditor()
            # modifying selected guides
            elif shiftDown:
                # remove
                if hitGuideline in self.selectedGuidelines:
                    del self.selectedGuidelines[hitGuideline]
                # add
                else:
                    self.selectedGuidelines[hitGuideline] = getGuidelineState(hitGuideline)
                    self.isDraggingGuidelines = True
            # initiating drag
            elif hitGuideline in self.selectedGuidelines:
                self.isDraggingGuidelines = True
            # selecting new
            else:
                self.selectedGuidelines = {
                    hitGuideline : getGuidelineState(hitGuideline)
                }
                self.isDraggingGuidelines = True
        else:
            isInRuler, rulerData = self.isInRuler(point)
            # add new
            if clickCount == 2:
                x, y = point
                if optionDown:
                    angle = self.getVerticalAngle()
                    y = 0
                else:
                    angle = 0
                    x = 0
                x = bezierTools.roundValue(x, self.roundValuesTo)
                y = bezierTools.roundValue(y, self.roundValuesTo)
                dest = self.getGlyph()
                if commandDown:
                    dest = dest.font
                dest.prepareUndo("Add guideline")
                guideline = dest.appendGuideline(
                    position=(x, y),
                    angle=angle
                )
                dest.performUndo()
                self.selectedGuidelines = {
                    guideline : getGuidelineState(guideline)
                }
            # drag from ruler
            elif isInRuler:
                x, y = rulerData["point"]
                angle = rulerData["angle"]
                x = bezierTools.roundValue(x, self.roundValuesTo)
                y = bezierTools.roundValue(y, self.roundValuesTo)
                dest = self.getGlyph()
                if commandDown:
                    dest = dest.font
                dest.prepareUndo("Add guideline")
                guideline = dest.appendGuideline(
                    position=(x, y),
                    angle=angle
                )
                dest.performUndo()
                self.selectedGuidelines = {
                    guideline : getGuidelineState(guideline)
                }
                self.isDraggingGuidelines = True
            # deselect and start marquee
            else:
                self.selectedGuidelines = {}
                self.inRectSelection = True
        self.displaySelectedGuidelines()

    def isInRuler(self, point):
        ruler = 20
        scale = self.getNSView().inverseScale()
        ruler *= scale
        x, y = point
        (vX, vY), (vW, vH) = self.getVisibleRect()
        leftMin = vX
        leftMax = vX + ruler
        rightMax = vX + vW
        rightMin = rightMax - ruler
        topMax = vY + vH
        topMin = topMax - ruler
        bottomMin = vY
        bottomMax = vY + ruler
        angle = None
        # top
        if y >= topMin and y <= topMax:
            angle = 0
            x = 0
        # bottom
        elif y >= bottomMin and y <= bottomMax:
            angle = 0
            x = 0
        # left
        elif x >= leftMin and x <= leftMax:
            angle = self.getVerticalAngle()
            if angle == 90:
                y = 0
        # right
        elif x >= rightMin and x <= rightMax:
            angle = self.getVerticalAngle()
            if angle == 90:
                y = 0
        isInRuler = angle is not None
        data = dict(
            angle=angle,
            point=(x, y)
        )
        return isInRuler, data

    def mouseDragged(self, point, delta):
        modifiers = self.getModifiers()
        shiftDown = modifiers["shiftDown"]
        capLockDown = modifiers["capLockDown"]
        commandDown = modifiers["commandDown"]
        optionDown = modifiers["optionDown"]
        controlDown = modifiers["controlDown"]
        # marquee selection
        if self.inRectSelection:
            self.selectedGuidelines = self.findGuidelinesIntersectedBySelectionRect()
        # editing
        elif self.isDraggingGuidelines:
            # origin editing
            if commandDown and len(self.selectedGuidelines) == 1:
                guideline = self.selectedGuideline
                guideline.naked().prepareUndo("Move Guideline")
                x, y = point
                x = bezierTools.roundValue(x, self.roundValuesTo)
                y = bezierTools.roundValue(y, self.roundValuesTo)
                guideline.x = x
                guideline.y = y
            # angle editing
            elif optionDown and len(self.selectedGuidelines) == 1:
                x, y = point
                guideline = self.selectedGuideline
                if bezierTools.distanceFromPointToPoint((guideline.x, guideline.y), (x, y)) > 5:
                    guideline.naked().prepareUndo("Move Guideline")
                    guideline.angle = bezierTools.calculateAngle(
                        (guideline.x, guideline.y),
                        (x, y)
                    )
            # dragging
            else:
                # dragging 1
                if len(self.selectedGuidelines) == 1:
                    x, y = point
                    guideline = self.selectedGuideline
                    state = self.selectedGuidelines[guideline]
                    dx = x - state.x
                    dy = y - state.y
                # dragging > 1
                else:
                    sx, sy = self.mouseDownPoint
                    x, y = point
                    dx = x - sx
                    dy = y - sy
                self.snappingToThesePoints = set()
                snapTo = self.wantsSnapToPoint
                if snapTo:
                    snapTo = len(self.selectedGuidelines) == 1
                for guideline, state in self.selectedGuidelines.items():
                    guideline.naked().prepareUndo("Move Guideline")
                    x = state.x
                    y = state.y
                    angle = state.angle
                    if angle in horizontalAngles:
                        y += dy
                    elif angle in verticalAngles:
                        x += dx
                    else:
                        x += dx
                        y += dy
                    x = bezierTools.roundValue(x, self.roundValuesTo)
                    y = bezierTools.roundValue(y, self.roundValuesTo)
                    if snapTo:
                        self.snappingToThesePoints = self.findSnapToPoints((x, y), angle)
                        self.snapToPointSymbolColor = getGuidelineHighlightColor(
                            guideline,
                            self.colorFontGuideline,
                            self.colorGlyphGuideline,
                            self.highlightAlphaScale
                        )
                        if self.snappingToThesePoints:
                            snapTo = list(self.snappingToThesePoints)[0]
                            if angle in horizontalAngles:
                                y = snapTo[1]
                            elif angle in verticalAngles:
                                x = snapTo[0]
                            else:
                                x, y = snapTo
                    guideline.x = x
                    guideline.y = y
        self.displaySelectedGuidelines()
        self.displaySnapToPoints()
        self.displayMarquee(point)

    def mouseUp(self, point):
        # marquee selection
        if self.inRectSelection:
            self.selectedGuidelines = self.findGuidelinesIntersectedBySelectionRect()
        # dragging
        elif self.isDraggingGuidelines:
            for guideline, state in self.selectedGuidelines.items():
                if state != getGuidelineState(guideline):
                    guideline.naked().performUndo()
        self.inRectSelection = False
        self.isDraggingGuidelines = False
        self.mouseDownPoint = None
        self.snappingToThesePoints = []
        self.displaySnapToPoints()
        self.displaySelectedGuidelines()
        self.displayMarquee()

    def keyDown(self, nsEvent):
        didSomething = False
        if self.selectedGuidelines:
            event = extractNSEvent(nsEvent)
            key = event["keyDownWithoutModifiers"]
            if key == "\r" and self.selectedGuidelines:
                didSomething = True
                self.openGuidelineEditor()
            elif key in deleteKeys:
                didSomething = True
                glyph = self.getGlyph()
                font = glyph.font
                glyphGuidelines = []
                fontGuidelines = []
                for guideline, state in self.selectedGuidelines.items():
                    glyph = state.glyph
                    font = state.font
                    if glyph is not None:
                        glyphGuidelines.append(guideline)
                    else:
                        fontGuidelines.append(guideline)
                if glyphGuidelines:
                    glyph.prepareUndo("Delete Guidelines")
                    for guideline in glyphGuidelines:
                        glyph.removeGuideline(guideline)
                    glyph.performUndo()
                if fontGuidelines:
                    font.prepareUndo("Delete Guidelines")
                    for guideline in fontGuidelines:
                        font.removeGuideline(guideline)
                    font.performUndo()
                self.selectedGuidelines = {}
            else:
                arrowUp = event["up"]
                arrowDown = event["down"]
                arrowLeft = event["left"]
                arrowRight = event["right"]
                shiftDown = event["shiftDown"]
                commandDown = event["commandDown"]
                if True in (arrowUp, arrowDown, arrowLeft, arrowRight):
                    didSomething = True
                    dx = 0
                    dy = 0
                    if arrowUp:
                        dy = 1
                    elif arrowDown:
                        dy = -1
                    elif arrowLeft:
                        dx = -1
                    elif arrowRight:
                        dx = 1
                    multiplier = self.arrowIncrement
                    if shiftDown and commandDown:
                        multiplier = self.arrowCommandShiftIncrement
                    elif shiftDown:
                        multiplier = self.arrowShiftIncrement
                    dx *= multiplier
                    dy *= multiplier
                    dx = bezierTools.roundValue(dx, self.roundValuesTo)
                    dy = bezierTools.roundValue(dy, self.roundValuesTo)
                    for guideline in self.selectedGuidelines.keys():
                        guideline.naked().prepareUndo("Move Guideline")
                        guideline.x += dx
                        guideline.y += dy
                        guideline.naked().performUndo()
            self.displaySelectedGuidelines()
        if not didSomething:
            super().keyDown(nsEvent)

    def acceptMenuEditCallbacks(self, menuItem):
        return True

    def selectAll(self):
        glyph = self.getGlyph()
        font = glyph.font
        self.selectedGuidelines = {}
        for guideline in glyph.guidelines:
            self.selectedGuidelines[guideline] = getGuidelineState(guideline)
        for guideline in font.guidelines:
            self.selectedGuidelines[guideline] = getGuidelineState(guideline)
        self.displaySelectedGuidelines()

    def deselectAll(self):
        self.selectedGuidelines = {}
        self.displaySelectedGuidelines()

    # Contextual Menu

    def additionContextualMenuItems(self):
        glyph = self.getGlyph()
        font = glyph.font
        fontGuidelines = font.guidelines
        glyphGuidelines = glyph.guidelines
        selectedFontGuidelines = []
        selectedGlyphGuidelines = []
        for guideline in self.selectedGuidelines.keys():
            if guideline.glyph is not None:
                selectedGlyphGuidelines.append(guideline)
            else:
                selectedFontGuidelines.append(guideline)
        items = [
            dict(
                title="Clear All Guides",
                callback=self.menuClearAllCallback,
                enabled=bool(fontGuidelines + glyphGuidelines)
            ),
            dict(
                title="Clear Font Guides",
                callback=self.menuClearFontCallback,
                enabled=bool(fontGuidelines)
            ),
            dict(
                title="Clear Glyph Guides",
                callback=self.menuClearGlyphCallback,
                enabled=bool(glyphGuidelines)
            ),
            "----",
            dict(
                title="Convert to Font Guide",
                callback=self.menuConvertToFontCallback,
                enabled=bool(selectedFontGuidelines)
            ),
            dict(
                title="Convert to Glyph Guide",
                callback=self.menuConvertToGlyphCallback,
                enabled=bool(selectedGlyphGuidelines)
            )
        ]
        return items

    def menuClearAllCallback(self, sender):
        glyph = self.getGlyph()
        font = glyph.font
        font.clearGuidelines()
        glyph.clearGuidelines()

    def menuClearFontCallback(self, sender):
        glyph = self.getGlyph()
        font = glyph.font
        font.clearGuidelines()
        self.selectedGuidelines = {}
        self.displaySelectedGuidelines()

    def menuClearGlyphCallback(self, sender):
        glyph = self.getGlyph()
        glyph.clearGuidelines()
        self.selectedGuidelines = {}
        self.displaySelectedGuidelines()

    def menuConvertToFontCallback(self, sender):
        glyphGuidelines = []
        for guideline, state in self.selectedGuidelines.items():
            glyph = state.glyph
            if glyph is not None:
                glyphGuidelines.append(guideline)
        glyph = self.getGlyph()
        font = glyph.font
        for guideline in glyphGuidelines:
            del self.selectedGuidelines[guideline]
            glyph.removeGuideline(guideline)
            guideline = font.appendGuideline(
                guideline=guideline.copy()
            )
            self.selectedGuidelines[guideline] = getGuidelineState(guideline)
        self.displaySelectedGuidelines()

    def menuConvertToGlyphCallback(self, sender):
        fontGuidelines = []
        for guideline, state in self.selectedGuidelines.items():
            glyph = state.glyph
            if glyph is None:
                fontGuidelines.append(guideline)
        glyph = self.getGlyph()
        font = glyph.font
        for guideline in fontGuidelines:
            del self.selectedGuidelines[guideline]
            font.removeGuideline(guideline)
            guideline = glyph.appendGuideline(
                guideline=guideline.copy()
            )
            self.selectedGuidelines[guideline] = getGuidelineState(guideline)
        self.displaySelectedGuidelines()

    # Italic Support

    def getVerticalAngle(self):
        if not self.wantsItalicAngle:
            return 90
        glyph = self.getGlyph()
        font = glyph.font
        italicAngle = font.info.italicAngle
        if italicAngle is None:
            italicAngle = 0
        return 90 + italicAngle

    # Searching

    def _get_selectedGuideline(self):
        if len(self.selectedGuidelines) != 1:
            return None
        guideline = list(self.selectedGuidelines.keys())[0]
        return guideline

    selectedGuideline = property(_get_selectedGuideline)

    def findGuidelineAtPoint(self, point):
        glyph = self.getGlyph()
        font = glyph.font
        guidelines = font.guidelines + glyph.guidelines
        for guideline in guidelines:
            naked = guideline.naked()
            path = naked.getRepresentation("doodle.GuidelinePath")
            scale = self.getNSView().inverseScale()
            padding = scale * 2
            if path.isStrokeHitByPoint_padding_(point, padding):
                return guideline

    def findGuidelinesIntersectedBySelectionRect(self):
        (xMin, yMin), (w, h) = self.getMarqueRect()
        xMax = xMin + w
        yMax = yMin + h
        rectLines = [
            ((xMin, yMin), (xMin, yMax)),
            ((xMin, yMax), (xMax, yMax)),
            ((xMax, yMax), (xMax, yMin)),
            ((xMax, yMin), (xMin, yMin))
        ]
        glyph = self.getGlyph()
        font = glyph.font
        guidelines = glyph.guidelines
        guidelines += font.guidelines
        hits = {}
        for guideline in guidelines:
            beam = guideline.naked().getRepresentation("doodle.GuidelineBeam")
            for rectLine in rectLines:
                points = beam + rectLine
                if bezierTools.intersectLineLine(*points).points:
                    hits[guideline] = getGuidelineState(guideline)
                    break
        return hits

    def findSnapToPoints(self, point, angle):
        glyph = self.getGlyph()
        scale = self.getNSView().inverseScale()
        x, y = point
        padding = scale * 4
        xMin = x - padding
        xMax = x + padding
        yMin = y - padding
        yMax = y + padding
        hits = {}
        snapToPoints = glyph.getRepresentation(
            snapToPointsKey,
            removeOverlap=self.wantsSnapToFuturePoints
        )
        for point in snapToPoints:
            px, py = point
            distance = None
            if angle in horizontalAngles:
                if yMin <= py and py <= yMax:
                    distance = abs(y - py)
            elif angle in verticalAngles:
                if xMin <= px and px <= xMax:
                    distance = abs(x - px)
            else:
                distance = bezierTools.distanceFromPointToPoint((x, y), point)
                if distance > padding:
                    distance = None
            if distance is None:
                continue
            if distance not in hits:
                hits[distance] = set()
            hits[distance].add(point)
        if not hits:
            return set()
        closest = min(hits.keys())
        return hits[closest]


# -----
# Tools
# -----

GuidelineState = namedtuple(
    "GuidelineState",
    [
        "font",
        "glyph",
        "x",
        "y",
        "angle"
    ]
)

def getGuidelineState(guideline):
    glyph = guideline.glyph
    font = guideline.font
    state = GuidelineState(
        font=font,
        glyph=glyph,
        x=guideline.x,
        y=guideline.y,
        angle=guideline.angle
    )
    return state

def getGuidelinePathPoints(guideline):
    bigNumber = 10000
    fx = math.cos(math.radians(guideline.angle))
    fy = math.sin(math.radians(guideline.angle))
    afx = math.cos(math.radians(guideline.angle + 90))
    afy = math.sin(math.radians(guideline.angle + 90))
    startPoint = (fx * bigNumber, fy * bigNumber)
    endPoint = (-fx * bigNumber, -fy * bigNumber)
    return (startPoint, endPoint)

def getGuidelineHighlightColor(guideline, fontColor, glyphColor, alphaScale):
    if guideline.color is not None:
        color = guideline.color
    elif guideline.glyph is not None:
        color = glyphColor
    else:
        color = fontColor
    color = scaleColorAlpha(color, alphaScale)
    return color

def scaleColorAlpha(color, scale):
    r, g, b, a = color
    a *= scale
    return (r, g, b, a)

# Factories

snapToPointsKey = identifierStub + "snapToPoints"

def getAllPointsFromGlyph(glyph):
    points = set()
    for contour in glyph:
        for point in contour:
            if point.segmentType is not None:
                points.add((point.x, point.y))
    return points

def snapToPointsRepresentationFactory(glyph, removeOverlap=False):
    points = getAllPointsFromGlyph(glyph)
    if removeOverlap:
        boolGlyph = BooleanGlyph(glyph)
        boolGlyph = boolGlyph.removeOverlap()
        result = defcon.Glyph()
        boolGlyph.drawPoints(result.getPointPen())
        points |= getAllPointsFromGlyph(result)
    return points

defcon.registerRepresentationFactory(
    defcon.Glyph,
    snapToPointsKey,
    snapToPointsRepresentationFactory,
    destructiveNotifications=(
        "Glyph.ContoursChanged",
        "Glyph.ComponentsChanged"
    )
)

# -------
# Install
# -------

def main():
    tool = GuidelineTool()
    installTool(tool)
    return tool


if __name__ == "__main__":
    main()
