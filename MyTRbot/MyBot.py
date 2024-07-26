import sys # 시스템 관련 기능 사용
from PyQt5.QtWidgets import * # PyQt5의 모든 위젯 클래스를 import
from PyQt5 import uic # UI파일을 로드하는 기능 제공
from PyQt5.QAxContainer import *

form_class = uic.loadUiType('main_window.ui')[0] # Qt Designer로 디자인한 UI 파일을 로드하여 클래스 형태로 반환

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
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login()

        #kiwoom event
        self.kiwoom.OnEventConnect.connect(self.event_connect)

    def setUI(self):
        self.setupUi(self) # Qt Designer로 디자인한 UI를 현재 인스턴스에 설정

    def login(self):
        self.kiwoom.dynamicCall("CommConnect()") # dynamicCall은 COM 객체의 메서드를 호출하는데 사용

    def event_connect(self, nErrCode):
        if nErrCode == 0:
            print("로그인 성공")
            self.statusbar.showMessage("로그인 성공")
        elif nErrCode == -100:
            print("사용자 정보교환 실패")
        elif nErrCode == -101:
            print("서버접속 실패")
        elif nErrCode == -102:
            print("버전처리 실패")


if __name__ == '__main__':
    app = QApplication(sys.argv) # QApplication 객체 생성
    myApp = MyBot() # MyBot 클래스의 인스턴스 생성
    myApp.show() # 메인 윈도우를 화면에 표시
    app.exec() # 애플리케이션의 이벤트 루프 시작