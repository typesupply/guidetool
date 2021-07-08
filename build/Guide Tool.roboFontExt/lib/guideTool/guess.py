from lib.tools.bezierTools import calculateAngle

def guessPositionAndAngleFromSelectedPoints(glyph):
    font = glyph.font
    position = None
    angle = None
    selectedBPoints = []
    for contourIndex, contour in enumerate(glyph):
        for bPointIndex, bPoint in enumerate(contour.bPoints):
            if bPoint.selected:
                selectedBPoints.append((contourIndex, bPointIndex, bPoint))
    if len(selectedBPoints) not in (1, 2):
        return None
    elif len(selectedBPoints) == 1:
        contourIndex, bPointIndex, bPoint = selectedBPoints[0]
        anchor = bPoint.anchor
        bcpIn = bPoint.bcpIn
        bcpOut = bPoint.bcpOut
        # two off curves
        if bcpIn != (0, 0) and bcpOut != (0, 0):
            # vertical
            if (bcpIn[0], bcpOut[0]) == (0, 0):
                position = (anchor[0], 0)
                angle = 90
            # horizontal
            elif (bcpIn[1], bcpOut[1]) == (0, 0):
                position = (0, anchor[1])
                angle = 0
        # one off curve
        elif bcpIn != (0, 0) or bcpOut != (0, 0):
            for point in (bcpIn, bcpOut):
                if point == (0, 0):
                    continue
                # vertical
                if point[0] == 0:
                    position = (anchor[0], 0)
                    angle = 90
                # horizontal
                elif point[1] == 0:
                    position = (0, anchor[1])
                    angle = 0
        # no usable off curves
        if angle is None:
            # not likely to put a guide on a vertical metric
            verticalMetrics = [font.info.descender, 0, font.info.xHeight, font.info.capHeight, font.info.ascender]
            if anchor[1] in verticalMetrics:
                position = (anchor[0], 0)
                angle = 90
            # test neighbors
            bPoints = glyph[contourIndex].bPoints
            previousBPoint = bPoints[bPointIndex - 1]
            nextBPoint = bPoints[(bPointIndex + 1) % len(bPoints)]
            angles = [
                calculateAngle(previousBPoint.anchor, bPoint.anchor),
                calculateAngle(nextBPoint.anchor, bPoint.anchor)
            ]
            # defer to horizontal
            if 0 in angles:
                position = (0, anchor[1])
                angle = 0
            # vertical
            elif 90 in angles:
                position = (anchor[0], 0)
                angle = 90
    else:
        bPoints = [p[-1] for p in selectedBPoints]
        x = set([bPoint.anchor[0] for bPoint in bPoints])
        y = set([bPoint.anchor[1] for bPoint in bPoints])
        if len(y) == 1:
            position = (0, y.pop())
            angle = 0
        elif len(x) == 1:
            position = (x.pop(), 0)
            angle = 90
        else:
            bPoint1 = selectedBPoints[0][-1]
            bPoint2 = selectedBPoints[1][-1]
            angle = calculateAngle(bPoint1.anchor, bPoint2.anchor)
            position = bPoint1.anchor
    if angle is None:
        position = (0, 0)
        angle = 0
    return dict(position=position, angle=angle)

if __name__ == "__main__":
    glyph = CurrentGlyph()
    d = guessPositionAndAngleFromSelectedPoints(glyph)
    print(d)