# Guide Tool

This is a tool for creating, modifying guides and making them smart.

## Guide Editing Tool

The guide editing tool appears with the other editing tools in the glyph editor toolbar.

### To create a guide...

- Click and drag from the edges of the glyph editor. Starting at the top and bottom will create a horizontal guide. Starting at the left or right will create a vertical guide. If a "snap to" preference is active, nearby points will be used for to help determine the guide's position.
- Double click where you want a horizontal guide to be created.
- Hold the option key and double-click where you want a horizontal vertical to be created.
- Hold down the command key during a click + drag or a double-click to create a font-level guide.

### To select a guide...

- Click the guide you want to select.
- Mouse down and drag to create a selection rectangle. Any guide intersecting the rectangle will be selected.
- Use the shift key to add/subtract from the selection.

Selected guides will have a selection "glow" around them.

### To move a guide...

- Click and drag a guide. If a "snap to" preference is active, nearby points will be used for to help determine the guide's position.
- Drag a selected guide. If more than one guide is selected, all guides will be moved. If a "snap to" preference is active, nearby points will be used for to help determine the guide's position.
- Use the arrow keys to move the selected guides.

### To change the origin point of a guide...

- Click to select a guide and, while dragging, hold the command key.

### To change the angle of a guide....

- Click to select a guide and, while dragging, hold the option key.

### To delete a guide...

- Hit the delete key to remove the selected guides.

### To clear all guides...

- Hold control and click.
- Select the appropriate "Clear..." option.

### To convert a font-level guide to a glyph-level guide or vice-versa...

- Select the guides you want to convert.
- Hold the control and click.
- Choose the appropriate "Convert..." option.

### To open the guide editor pop up...

- Select the guide you want to edit.
- Hit the return key.

## Guide From Selected Points

With the standard RoboFont editing tool active:

- Use the control + option + G key combination to create a guide. If one point is selected, a horizontal guide will be created at the y position of the selected point. If two points are selected the guide will match the angle between the two points.
- Use the command + control + option + G key combination to create a font-level guide.

The guide editor pop up will appear and allow you to edit the details of the guide.

## Guide Editor Pop Up

The guide editor pop up will allow you to edit a guide's:

- Level (font or glyph)
- Name
- Position
- Angle
- Color
- Magnetism
- Measurement Display
- Smart Rules

## Smart Guides

**Note: This is experimental but also awesome.**

Guides can be set to only be visible when certain conditions are met by a glyph. For example, you can specify that a guide should only be shown in uppercase glyphs. This is managed by creating rules for a guide in the guide editor pop up. The rules are defined with a simple syntax:

```
# comment
> macro name (only allowed in preferences window)
match: any or all (only allowed once, any is the default)
name: [fnmatch pattern](https://docs.python.org/3/library/fnmatch.html) that will be tested against glyph names
script: unicode tag
category: unicode tag
group: [fnmatch pattern](https://docs.python.org/3/library/fnmatch.html) that will be tested against group names
macro: name
```

A macro is a shortcut defined in the Guide Tool preferences. If a macro name matches one defined in the preferences, the guide's rules will include the rules defined by the macro. This allows you to define your rules at the application level and use them for any number of guides.

## Preferences

In the Guide Tool Preferences you can edit:

- Selection Highlight: The opacity of the highlight used to show selected guides.
- Snap To: When dragging a guide, if any of the "snap to" options is active, the guide will be snapped to nearby points. "Point" will snap to points defined in the glyph. "Future Point" will snap to points that will exist if a "remove overlap" operation would be performed on the current state of the glyph.
- Vertical Angle: The angle to use when creating a vertical guide.
- Colors: The standard color swatches available to apply to guides.
- Macros: The macro definitions for smart guides. These use the same syntax as defined above.