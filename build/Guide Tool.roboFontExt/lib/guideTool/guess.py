from fontParts.base.bPoint import absoluteBCPIn, absoluteBCPOut
from lib.tools.bezierTools import calculateAngle

def guessPositionAndAngleFromSelectedPoints(glyph):
    """
    Test case for one anchor selection:

    <?xml version='1.0' encoding='UTF-8'?>
    <glyph name="A" format="2">
      <advance width="900"/>
      <outline>
        <contour>
          <point x="200" y="200" type="line"/>
          <point x="700" y="100" type="line"/>
          <point x="600" y="600" type="line"/>
          <point x="200" y="600" type="line"/>
        </contour>
        <contour>
          <point x="400" y="300" type="curve" smooth="yes"/>
          <point x="455" y="290"/>
          <point x="490" y="344"/>
          <point x="500" y="400" type="curve"/>
          <point x="490" y="454"/>
          <point x="455" y="500"/>
          <point x="400" y="500" type="curve" smooth="yes"/>
          <point x="345" y="500"/>
          <point x="300" y="455"/>
          <point x="300" y="400" type="curve" smooth="yes"/>
          <point x="300" y="345"/>
          <point x="346" y="310"/>
        </contour>
        <contour>
          <point x="400" y="350" type="curve"/>
          <point x="400" y="350"/>
          <point x="445" y="372"/>
          <point x="450" y="400" type="curve"/>
          <point x="450" y="400"/>
          <point x="428" y="450"/>
          <point x="400" y="450" type="curve" smooth="yes"/>
          <point x="400" y="450"/>
          <point x="350" y="427"/>
          <point x="350" y="400" type="curve"/>
          <point x="350" y="400"/>
          <point x="373" y="355"/>
        </contour>
      </outline>
    </glyph>
    """
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
            # smooth
            elif bPoint.type == "curve":
                position = (anchor[0], anchor[1])
                angle = calculateAngle(bcpIn, bcpOut)
            # fallback (should only happen for corner)
            else:
                position = (anchor[0], anchor[1])
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
                # fallback
                else:
                    position = (anchor[0], anchor[1])
                    if point == bcpIn:
                        b = absoluteBCPIn(anchor, point)
                        angle = calculateAngle(b, anchor)
                    else:
                        b = absoluteBCPOut(anchor, point)
                        angle = calculateAngle(anchor, b)
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
            # fallback
            else:
                position = (anchor[0], anchor[1])
                angle = 0
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