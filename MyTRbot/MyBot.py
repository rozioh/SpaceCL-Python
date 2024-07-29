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

    def getItemList(self):
        #종목코드 리스트 생성
        marketList = ["0", "10"] #시장구분값 = 0: 코스피, 10: 코스닥

        for market in marketList:
            codeList = self.kiwoom.dynamicCall("GetCodeListByMarket(QString)", market).split(";") #종목코드 리스트
            for code in codeList:
                name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)", code) #종목명

                item = dm.DataModel.ItemInfo(code, name)
                self.myModel.itemList.append(item) #dm을 만들어서 itemList에 저장


if __name__ == '__main__':
    app = QApplication(sys.argv) # QApplication 객체 생성
    myApp = MyBot() # MyBot 클래스의 인스턴스 생성
    myApp.show() # 메인 윈도우를 화면에 표시
    app.exec() # 애플리케이션의 이벤트 루프 시작