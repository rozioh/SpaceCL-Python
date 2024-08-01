import sys # 시스템 관련 기능 사용
from PyQt5.QtWidgets import * # PyQt5의 모든 위젯 클래스를 import
from PyQt5 import uic # UI파일을 로드하는 기능 제공
from PyQt5.QAxContainer import *

form_class = uic.loadUiType('main_window.ui')[0] # Qt Designer로 디자인한 UI 파일을 로드하여 클래스 형태로 반환

import dataModel as dm

class MyBot(QMainWindow, form_class):
    """
    메인클래스
    작업일자 : 2024-07-26
    버전 : 1.0
    작업자 : Ahn
    """
    #생성자
    #클래스의 객체 초기화
    def __init__(self):
        super().__init__() # 부모 클래스(QMainWindow)의 생성자 호출
        self.setUI()
        self.myModel = dm.DataModel() #DataModel 초기화
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login() #로그인 > CommConnect() > 로그인창 출력 > OnEventConnect(event_connect) 발생

        #kiwoom event
        self.kiwoom.OnEventConnect.connect(self.event_connect)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trData)

        #Ui_Trigger
        self.searchItemButton.clicked.connect(self.searchItem) #종목 조회
        self.buyPushButton.clicked.connect(self.itemBuy) #매수 버튼
        self.sellPushButton.clicked.connect(self.itemSell) #매도 버튼

    def setUI(self):
        self.setupUi(self) # Qt Designer로 디자인한 UI를 현재 인스턴스에 설정

        column_head = [
            "00: 지정가",
            "03: 시장가",
            "05: 조건부지정가",
            "06: 최유리지정가",
            "07: 최우선지정가",
            "10: 지정가IOC",
            "13: 시장가IOC",
            "16: 최유리IOC",
            "20: 지정가FOK",
            "23: 시장가FOK",
            "26: 최유리FOK",
            "61: 장전시간외종가",
            "62: 시간외단일가매매",
            "81: 장후시간외종가"
        ]
        self.gubunComboBox.addItems(column_head) #거래구분(가격구분)

        column_head = [
            "매수",
            "매도",
            "매수취소",
            "매도취소",
            "매수정정",
            "매도정정"
        ]
        self.tradeGubunComboBox.addItems(column_head) #거래구분(주문유형)

    def login(self):
        self.kiwoom.dynamicCall("CommConnect()") # dynamicCall은 COM 객체의 메서드를 호출하는데 사용

    def event_connect(self, nErrCode):
        if nErrCode == 0:
            print("로그인 성공")
            self.statusbar.showMessage("로그인 성공")
            self.get_login_info() #로그인 정보 가져오기
            self.getItemList() #종목정보 호출
        elif nErrCode == -100:
            print("사용자 정보교환 실패")
        elif nErrCode == -101:
            print("서버접속 실패")
        elif nErrCode == -102:
            print("버전처리 실패")

    def get_login_info(self):
        # 로그인 정보
        accCnt = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT") #계좌개수
        accList = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCLIST") #보유계좌 목록
        accList = accList.split(";")  #accList = "계좌;계좌;" -> ['계좌', '계좌', '']
        accList.pop() #['계좌', '계좌']
        userId = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "USER_ID") #사용자 ID
        userName = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "USER_NAME") #사용자 이름
        serverGubun = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "GetServerGubun") #접속서버 구분 (1:모의투자, 나머지: 실거래 서버)

        if serverGubun == "1":
            serverGubun = "모의투자"
        else:
            serverGubun = "실거래 서버"

        self.statusbar.showMessage(serverGubun)
        self.accComboBox.addItems(accList) #ComboBox에 StringList를 넣음
        self.accComboBox.setCurrentIndex(1)
        self.getMyAccount() #계좌정보 가져오기
        self.getOutstandingRequest() #미체결요청 가져오기

    def getItemList(self):
        #종목코드 리스트 생성
        marketList = ["0", "10"] #시장구분값 = 0: 코스피, 10: 코스닥

        for market in marketList:
            codeList = self.kiwoom.dynamicCall("GetCodeListByMarket(QString)", market).split(";") #종목코드 리스트
            for code in codeList:
                name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)", code) #종목명

                item = dm.DataModel.ItemInfo(code, name)
                self.myModel.itemList.append(item) #dm을 만들어서 itemList에 저장

    def searchItem(self):
        #조회 버튼 클릭 시 호출
        #myModel에 저장된 itemList에서 itemName과 일치하는 것의 itemCode를 가져옴
        itemName = self.searchItemTextEdit.toPlainText()
        if itemName != "":
            for item in self.myModel.itemList:
                if item.itemName == itemName:
                    self.itemCodeTextEdit.setPlainText(item.itemCode)
                    self.volumeSpinBox.setValue(0)
                    self.getitemInfo(item.itemCode) #현재가 가져오기

        else:
            #종목명이 비었을 때 조회 시 종목코드와 가격 초기화
            self.itemCodeTextEdit.setPlainText("")
            self.priceSpinBox.setValue(0)
            QMessageBox.information(self, "Information", "종목명을 입력하세요.")

    def getitemInfo(self, code):
        #종목정보 TR Data
        #SetInputValue(사용자 호출) -> CommRqData(사용자 호출) -> OnReceiveTrData(이벤트 발생) -> GetCommData(수신 데이터 가져오기)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식기본정보요청", "OPT10001", 0, "5000")

    def receive_trData(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength, sErrorCode, sMessage, sSplmMsg):
        #Tr 이벤트 함수
        if sTrCode == "OPT10001":
            if sRQName == "주식기본정보요청":
                #현재가 priceSpinBox
                currentPrice = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "현재가")
                self.priceSpinBox.setValue(abs(int(currentPrice.lstrip())))
        elif sTrCode == "OPW00018":
            if sRQName == "계좌평가잔고내역":
                #테이블 세팅
                column_head = ["종목번호", "종목명", "보유수량", "매입가", "현재가", "평가손익", "수익률(%)"]
                colCount = len(column_head)
                rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName) #데이터 수신 시 멀티데이터의 개수 반환
                self.stockListTableWidget.setColumnCount(colCount) #열 설정
                self.stockListTableWidget.setRowCount(rowCount) #행 설정
                self.stockListTableWidget.setHorizontalHeaderLabels(column_head) #수평 헤더 레이블 설정

                for index in range(rowCount):
                    #멀티데이터 가져오기
                    itemCode = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "종목번호").strip(" ").strip("A")
                    itemName = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "종목명").strip(" ")
                    quantity = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "보유수량"))
                    buyingPrice = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "매입가"))
                    currentPrice = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "현재가"))
                    estimateProfit = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "평가손익"))
                    profitRate = float(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "수익률(%)"))

                    #StockBalance에 저장한 데이터 모델을 stockBalanceList에 저장
                    stockBalance = dm.DataModel.StockBalance(itemCode, itemName, quantity, buyingPrice, currentPrice, estimateProfit, profitRate)
                    self.myModel.stockBalanceList.append(stockBalance)

                    #테이블 셋
                    self.stockListTableWidget.setItem(index, 0, QTableWidgetItem(itemCode)) #setItem(row, column, QTableWidgetItem *item)
                    self.stockListTableWidget.setItem(index, 1, QTableWidgetItem(itemName))
                    self.stockListTableWidget.setItem(index, 2, QTableWidgetItem(str(quantity)))
                    self.stockListTableWidget.setItem(index, 3, QTableWidgetItem(str(buyingPrice)))
                    self.stockListTableWidget.setItem(index, 4, QTableWidgetItem(str(currentPrice)))
                    self.stockListTableWidget.setItem(index, 5, QTableWidgetItem(str(estimateProfit)))
                    self.stockListTableWidget.setItem(index, 6, QTableWidgetItem(f"{profitRate:.2f}")) #소수점 두자리까지 출력

                #싱글데이터 가져오기
                totalBuyingPrice = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총매입금액"))
                currentTotalPrice = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가금액"))
                balanceAsset = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "추정예탁자산"))
                totalEstimateProfit = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가손익금액"))

                #그리드 라벨 세팅. 소수점 고려하여 string으로 변환
                self.totalBuyingPriceLabel.setText(str(totalBuyingPrice))
                self.currentTotalPriceLabel.setText(str(currentTotalPrice))
                self.balanceAssetLabel.setText(str(balanceAsset))
                self.totalEstimateProfitLabel.setText(str(totalEstimateProfit))

        elif sTrCode == "OPT10075":
            if sRQName == "미체결요청":
                # 테이블 세팅
                column_head = ["종목코드", "종목명", "주문번호", "주문수량", "주문가격", "미체결수량", "주문구분", "시간", "현재가"]
                colCount = len(column_head)
                rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
                #outstandingTableWidget에 col, row, head 세팅
                self.outstandingTableWidget.setColumnCount(colCount)
                self.outstandingTableWidget.setRowCount(rowCount)
                self.outstandingTableWidget.setHorizontalHeaderLabels(column_head)

                for index in range(rowCount):
                    #데이터 가져오기
                    itemCode = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "종목코드").strip(" ").strip("A")
                    itemName = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "종목명").strip(" ")
                    orderNumber = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "주문번호").strip(" ")
                    orderQuantity = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "주문수량").strip(" ")
                    orderPrice = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "주문가격").strip(" ")
                    outstandingQuantity = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "미체결수량").strip(" ")
                    orderGubun = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "주문구분").strip(" ").strip("+").strip("-")
                    time = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "시간").strip(" ")
                    currentPrice = abs(int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index, "현재가").strip(" ")))

                    print("미체결요청: ",itemCode,", ", itemName,", ",orderNumber,", ",orderQuantity,", ",orderPrice,", ",outstandingQuantity,", ",orderGubun,", ",time,", ",currentPrice)

                    #데이터 모델 형태로 저장 후 outstandingBalanceList에 추가
                    outstandingBalance = dm.DataModel.OutstandingBalance(itemCode, itemName, orderNumber, orderQuantity, orderPrice, outstandingQuantity, orderGubun, time, currentPrice)
                    self.myModel.outstandingBalanceList.append(outstandingBalance)

                    #main_window UI의 미체결주문 탭에 테이블 셋
                    self.outstandingTableWidget.setItem(index, 0, QTableWidgetItem(str(itemCode)))
                    self.outstandingTableWidget.setItem(index, 1, QTableWidgetItem(str(itemName)))
                    self.outstandingTableWidget.setItem(index, 2, QTableWidgetItem(str(orderNumber)))
                    self.outstandingTableWidget.setItem(index, 3, QTableWidgetItem(str(orderQuantity)))
                    self.outstandingTableWidget.setItem(index, 4, QTableWidgetItem(str(orderPrice)))
                    self.outstandingTableWidget.setItem(index, 5, QTableWidgetItem(str(outstandingQuantity)))
                    self.outstandingTableWidget.setItem(index, 6, QTableWidgetItem(str(orderGubun)))
                    self.outstandingTableWidget.setItem(index, 7, QTableWidgetItem(str(time)))
                    self.outstandingTableWidget.setItem(index, 8, QTableWidgetItem(str(currentPrice)))
    def itemBuy(self):
        #매수 함수
        if self.searchItemTextEdit.toPlainText() == "":
            QMessageBox.information(self, "Information", "종목명을 입력하세요.")
        else:
            print("매수버튼 클릭")
            acc = self.accComboBox.currentText() #계좌정보
            code = self.itemCodeTextEdit.toPlainText() #종목코드
            amount = int(self.volumeSpinBox.value()) #수량
            price = int(self.priceSpinBox.value()) #가격
            hogaGb = self.gubunComboBox.currentText()[0:2] #가격구분(호가구분)
            if hogaGb == "03": #시장가(현재 거래되고 있는 가격)
                price = 0      #시장가(03)일 때, 주문가격 불필요 (0으로 입력)

            #서버에 주문을 전송하는 함수
            self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                    ["주식주문", "6000", acc, 1, code, amount, price, hogaGb, ""]) #1 = 신규매수

    def itemSell(self):
        #매도 함수
        if self.searchItemTextEdit.toPlainText() == "":
            QMessageBox.information(self, "Information", "종목명을 입력하세요.")
        else:
            print("매도버튼 클릭")
            acc = self.accComboBox.currentText()  # 계좌정보
            code = self.itemCodeTextEdit.toPlainText()  # 종목코드
            amount = int(self.volumeSpinBox.value())  # 수량
            price = int(self.priceSpinBox.value())  # 가격
            hogaGb = self.gubunComboBox.currentText()[0:2]  # 가격구분(호가구분)
            if hogaGb == "03": #시장가(현재 거래되고 있는 가격)
                price = 0      #시장가(03)일 때, 주문가격 불필요 (0으로 입력)

            #서버에 주문을 전송하는 함수
            self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                    ["주식주문", "6500", acc, 2, code, amount, price, hogaGb, ""]) #2 = 신규매도

    def getMyAccount(self):
        #계좌평가잔고내역요청 TR Data
        #SetInputValue(사용자 호출) -> CommRqData(사용자 호출) -> OnReceiveTrData(이벤트 발생) -> GetCommData(수신 데이터 가져오기)

        account = self.accComboBox.currentText() #계좌번호
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "") #사용안함 = 공백
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00") #00(공백불가)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2") #1:합산, 2:개별

        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역", "OPW00018", 0, "5100")

    def getOutstandingRequest(self):
        #미체결요청 TR Data
        # SetInputValue(사용자 호출) -> CommRqData(사용자 호출) -> OnReceiveTrData(이벤트 발생) -> GetCommData(수신 데이터 가져오기)
        account = self.accComboBox.currentText() #계좌번호
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0") #0:전체, 1:종목
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0") #0:전체, 1:매도, 2:매수
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", "") #공백허용: 전체종목구분=0으로 전체 종목 대상으로 조회됨
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1") #0:전체, 1:미체결, 2:체결

        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "미체결요청", "OPT10075", 0, "5200")


if __name__ == '__main__':
    app = QApplication(sys.argv) # QApplication 객체 생성
    myApp = MyBot() # MyBot 클래스의 인스턴스 생성
    myApp.show() # 메인 윈도우를 화면에 표시
    app.exec() # 애플리케이션의 이벤트 루프 시작