import sys
from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QDialog, QStackedWidget
from PyQt5.QtCore import QObject, QSize, QEvent
from Windows import *
import sqlite3 as sql
from random import shuffle

class MainWindow(QtWidgets.QMainWindow, Ui_Main):
    def __init__(self):
        super().__init__()
        self.main_win = QMainWindow()
        self.ui = Ui_Main()
        self.ui.setupUi(self.main_win)

        self.ui.modesBox.addItems(['Соревнование', 'Тренировка'])

        self.ModesDescriptions = {'Соревнование': 
                                    """Соревнуйся с другими пользователями \n в скорости печати. Покажи всем \n на что способен! \n Одна попытка - 1 минута""",
                                    'Тренировка': 
                                    """Тренируй правильное 
                                    написание уже 
                                    подобранных слов или 
                                    загружай собственные!"""}
        
        self.inputlist = list()
        self.index = 0
        self.duration_cm = 5
        self.cm_going = False


        self.ui.inputText.installEventFilter(self)
        
        self.current_user = (None, False)

        self.wordlist_cm = list()
        with open('CM.txt', 'r', encoding='utf8') as file:      
            for line in file:                                   
                self.wordlist_cm.extend((line.rstrip()).split())       
        shuffle(self.wordlist_cm)

        self.con = sql.connect('Data.db')
        self.cur = self.con.cursor()

        self.login_data = [row[0] for row in self.cur.execute("""SELECT Login FROM Logins""").fetchall()]
        self.nickname_data = [row[0] for row in self.cur.execute("""SELECT Nickname FROM Logins""").fetchall()]

        self.ui.WindowsStack.setCurrentWidget(self.ui.Menu)
        self.ui.AboutBtn.clicked.connect(self.show_about)
        self.ui.ExitBtn.clicked.connect(self.close_app)
        self.ui.StartBtn.clicked.connect(self.show_go_sys)
        self.ui.ScoreBtn.clicked.connect(self.show_rating)

        self.ui.OkBtn.clicked.connect(self.show_menu)

        self.ui.goFromRatingBtn.clicked.connect(self.show_menu)

        self.ui.goFromSignInBtn.clicked.connect(self.show_menu)
        self.ui.SignInBtn.clicked.connect(self.sign_in)

        self.ui.goFromSignUpBtn.clicked.connect(self.show_menu)
        self.ui.SignUpBtn.clicked.connect(self.sign_up)

        self.ui.goMenuFromSysBtn.clicked.connect(self.show_menu)
        self.ui.chooseInBtn.clicked.connect(self.show_sign_in)
        self.ui.chooseUpBtn.clicked.connect(self.show_sign_up)

        self.ui.modesBox.activated.connect(self.change_desc)
        self.ui.goFromModesBtn.clicked.connect(self.show_menu)
        self.ui.startCurModeBtn.clicked.connect(self.start_mode)

        self.ui.goFromCMBtn.clicked.connect(self.show_menu)
        self.ui.refreshCMBtn.clicked.connect(self.refresh_cm)
        self.ui.inputText.textChanged.connect(self.go)
    
    def show_menu(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.Menu)

    def show(self):
        self.main_win.show()
    
    def show_modes(self):
        self.ui.descModeLabel.setText(self.ModesDescriptions[self.ui.modesBox.currentText()])
        self.ui.WindowsStack.setCurrentWidget(self.ui.Modes)
    
    def change_desc(self):
        self.ui.descModeLabel.setText(self.ui.ModesDescriptions[self.ui.modesBox.currentText()])
    
    def start_mode(self):
        mode = self.ui.modesBox.currentText()
        match mode:
            case 'Соревнование':
                self.ui.lcdTimer.display('60')
                self.ui.WindowsStack.setCurrentWidget(self.ui.CMMode)
    
    def timer_start(self):
        self.time_left_int = self.duration_cm
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.timer_timeout)
        self.timer.start(1000)

        self.update_gui()

    def timer_timeout(self):
        self.time_left_int -= 1

        if self.time_left_int == 0:
            self.stop_cm()

        self.update_gui()

    def update_gui(self):
        self.ui.lcdTimer.display(self.time_left_int)
    
    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and source is self.ui.inputText and event.key() == QtCore.Qt.Key_Space):
            if not all(i == ' ' for i in list(self.ui.inputText.toPlainText())):
                self.inputlist.append((self.ui.inputText.toPlainText()).strip())
                self.ui.inputText.clear()
                self.index += 1
                self.ui.outputText.setText(self.wordlist_cm[self.index])
                print(self.inputlist)
        return super().eventFilter(source, event)
    
    def refresh_cm(self):
        self.cm_going = False
                
    def go(self):
        if self.cm_going is False:
            self.timer_start()
            self.cm_going = True
    
    def stop_cm(self):
        self.timer.stop()
        self.show_results_cm(self.inputlist)

    def show_about(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.AboutApp)
    
    def show_go_sys(self):
        if self.current_user != (None, False):
            self.show_modes()
        else:
            self.ui.WindowsStack.setCurrentWidget(self.ui.goToSys)

    def show_sign_in(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.SignIn)

    def show_sign_up(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.SignUp)
    
    def show_rating(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.Rating)
    
    def wrong_info_in(self):
        self.ui.LoginLine.setStyleSheet("background-color: rgb(255, 96, 96);")
        self.ui.PassLine.setStyleSheet("background-color: rgb(255, 96, 96);") 

    def wrong_format_up(self):
        self.ui.NameLine.setStyleSheet("background-color: rgb(255, 96, 96);")
        self.ui.PassLine1.setStyleSheet("background-color: rgb(255, 96, 96);") 
        self.ui.PassLine2.setStyleSheet("background-color: rgb(255, 96, 96);")
        self.ui.LoginLine_2.setStyleSheet("background-color: rgb(255, 96, 96);")

    def check_password(self, pass1, pass2):                                       
        if len(pass1) >= 6 and pass1.isalnum() and pass1 == pass2:          
            return True                                                     
                                                                            
    def check_login(self, login):                                                 
        if len(login) >= 4 and login not in self.login_data:                      
            return True                                                     
                                                                            
    def check_nick(self, nick):                                                   
        if len(nick) >= 4 and nick not in self.nickname_data:                     
            return True  

    def sign_in(self):
        login_try = self.ui.LoginLine.text()
        pass_try = self.ui.PassLine.text()
        if login_try in self.login_data:
            if pass_try == (self.cur.execute(f"""SELECT Login, Password FROM Logins                                      
                                                WHERE Login LIKE '{login_try}'""").fetchall())[0][1]:  # Сверяем пароль введенный с тем, что в базе
                self.current_user = (login_try, True) # Задаем значения данных текущей сессии
                self.show_modes()
            else:
                self.wrong_info_in()
        else:
            self.wrong_info_in()


    
    def sign_up(self):
        nickname = self.ui.NameLine.text()
        login = self.ui.LoginLine_2.text()
        passw, confpassw = self.ui.PassLine1.text(), self.ui.PassLine2.text()
        if self.check_login(login) and self.check_nick(nickname) and self.check_password(passw, confpassw):
            self.cur.execute("""INSERT INTO Logins(Login, Password, Nickname) 
                                    VALUES (?,?,?);""", (login, passw, nickname))
            self.con.commit()
            self.current_user = (login, True)
            self.show_modes()
        else:
            self.wrong_format_up()
    
    def show_results_cm(self, lst):
        greatcount = 0
        lst = lst[1:]
        count = len(lst)
        for i in range(len(lst)):
            if lst[i] == self.wordlist_cm[i]:
                greatcount += 1
        try:
            accuracy, count = f'Точность введенных слов равняется {(round(greatcount / count) * 100)}%', f'Количество введеных слов за минуту равняется {count}'
        except:
            pass
            accuracy, count = f'Точность введенных слов равняется 0%', f'Количество введеных слов за минуту равняется {count}'
        greatcount = f'Количество правильно введеных слов за минуту равняется {greatcount}'
        self.ui.countLabel.setText(count)
        self.ui.accuracyLabel.setText(accuracy)
        self.ui.greatCountLabel.setText(greatcount)
        self.ui.WindowsStack.setCurrentWidget(self.ui.CMResults)

    
    
    def close_app(self):
        sys.exit()
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())