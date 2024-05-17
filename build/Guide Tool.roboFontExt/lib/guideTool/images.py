import os
import AppKit
from mojo.extensions import ExtensionBundle
from mojo.roboFont import CreateCursor

# ----
# Icon
# ----

guideToolToolbarIcon = AppKit.NSImage.alloc().initWithSize_((20, 20))
guideToolToolbarIcon.lockFocus()
path = AppKit.NSBezierPath.bezierPath()
path.setLineWidth_(2)
path.setLineCapStyle_(AppKit.NSLineCapStyleRound)
AppKit.NSColor.blackColor().set()
path.moveToPoint_((6, 3))
path.lineToPoint_((6, 17))
path.moveToPoint_((14, 3))
path.lineToPoint_((14, 17))
path.moveToPoint_((3, 6))
path.lineToPoint_((17, 6))
path.moveToPoint_((3, 14))
path.lineToPoint_((17, 14))
path.stroke()
guideToolToolbarIcon.unlockFocus()
guideToolToolbarIcon.setTemplate_(True)

# ------
# Cursor
# ------

bundle = ExtensionBundle("Guide Tool")
path = os.path.join(bundle.resourcesFolder, "guideToolCursor.pdf")
guideToolCursor = CreateCursor(
    path,
    (10, 10)
)
