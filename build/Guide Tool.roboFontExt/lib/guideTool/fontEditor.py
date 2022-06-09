import ezui

def reprGuideline(guideline):
    name = guideline.name
    position = f"({guideline.x}, {guideline.y})"
    angle = f"{guideline.angle}°"
    data = [position, angle]
    if name:
        data.insert(0, name)
    return " ".join(data)

class FontGuidelineTableController(ezui.WindowController):

    def build(self, font, parentWindow):
        self.font = font
        guidelines = [
            self.makeTableItem(guideline)
            for guideline in font.guidelines
        ]
        content = """
        = HorizontalStack

        |-------------|             @guidelineTable
        | description |
        |-------------|
        > (+-)                      @guidelineTableAddRemoveButton

        * GuideToolGuidelineEditor  @guidelineEditor

        ==========================

        (Close)                     @closeButton
        """
        descriptionData = dict(
            guidelineTable=dict(
                items=guidelines,
                columnDescriptions=[
                    dict(
                        identifier="repr"
                    )
                ],
                allowsMultipleSelection=False,
                allowsEmptySelection=False,
                width=200
            ),
            guidelineEditor=dict(
                onlyFontLevel=True
            )
        )
        self.w = ezui.EZSheet(
            content=content,
            descriptionData=descriptionData,
            controller=self,
            parent=parentWindow.w
        )
        if guidelines:
            table = self.w.getItem("guidelineTable")
            table.setSelectedIndexes([0])
            self.guidelineTableSelectionCallback(table)

    def makeTableItem(self, guideline):
        item = dict(
            repr=reprGuideline(guideline),
            guideline=guideline
        )
        return item

    def started(self):
        self.w.open()

    def guidelineTableSelectionCallback(self, sender):
        if not hasattr(self, "w"):
            return
        items = sender.getSelectedItems()
        if not items:
            return
        item = items[0]
        guideline = item["guideline"]
        editor = self.w.getItem("guidelineEditor")
        editor.setObjects(self.font, None, guideline)

    def guidelineTableAddRemoveButtonAddCallback(self, sender):
        table = self.w.getItem("guidelineTable")
        items = table.get()
        guideline = self.font.appendGuideline(
            position=(0, 0),
            angle=0
        )
        item = self.makeTableItem(guideline)
        items.append(item)
        table.set(items)
        table.setSelectedIndexes([len(items) - 1])

    def guidelineTableAddRemoveButtonRemoveCallback(self, sender):
        table = self.w.getItem("guidelineTable")
        items = table.get()
        selection = table.getSelectedIndexes()
        if not selection:
            return
        remove = []
        keep = []
        for i, item in enumerate(items):
            if i in selection:
                remove.append(item)
            else:
                keep.append(item)
        table.set(keep)
        for item in remove:
            guideline = item["guideline"]
            self.font.removeGuideline(guideline)

    def guidelineEditorCallback(self, sender):
        table = self.w.getItem("guidelineTable")
        items = table.get()
        selection = table.getSelectedIndexes()
        if not selection:
            return
        item = items[selection[0]]
        guideline = item["guideline"]
        item["repr"] = reprGuideline(guideline)
        table.set(items)
        table.setSelectedIndexes(selection)

    def closeButtonCallback(self, sender):
        self.w.close()

