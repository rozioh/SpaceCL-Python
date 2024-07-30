class DataModel:
    def __init__(self):
        self.itemList = []
        self.stockBalanceList = []

    class ItemInfo:
        def __init__(self, itemCode, itemName):
            self.itemCode = itemCode #종목코드
            self.itemName = itemName #종목명

    class StockBalance:
        def __init__(self, itemCode, itemName, quantity, buyingPrice, currentPrice, estimateProfit, profitRate):
            self.itemCode = itemCode
            self.itemName = itemName
            self.quantity = quantity
            self.buyingPrice = buyingPrice
            self.currentPrice = currentPrice
            self.estimateProfit = estimateProfit
            self.profitRate = profitRate