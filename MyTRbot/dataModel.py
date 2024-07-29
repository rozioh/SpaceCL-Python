class DataModel:
    def __init__(self):
        self.itemList = []

    class ItemInfo:
        def __init__(self, itemCode, itemName):
            self.itemCode = itemCode #종목코드
            self.itemName = itemName #종목명