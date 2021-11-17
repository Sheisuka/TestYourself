import sys
from PyQt5 import QtCore, QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QDialog, QStackedWidget, QMessageBox
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
        self.duration_cm = 60
        self.cm_going = False

        self.cm_opened = False

        self.ui.inputText.installEventFilter(self)
        
        self.current_user = (None, False, None)

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
        self.ui.dataBtn.clicked.connect(self.show_data)

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

        self.ui.endCmBtn.clicked.connect(self.end_cm)
        self.ui.againBtn.clicked.connect(self.again_cm)

        self.ui.goFromYourDataBtn.clicked.connect(self.show_menu)
        self.ui.changePassBtn.clicked.connect(self.show_change_pass)

        self.ui.confPassChangeBtn.clicked.connect(self.change_pass)
        self.ui.goFromPassChangeBtn.clicked.connect(self.show_menu)
    
    def show_data(self):
        if self.current_user[1] is True:
            user_data = self.cur.execute(f"""SELECT Login, Password, Nickname FROM Logins
                                             WHERE Login LIKE '{self.current_user[0]}'""").fetchall()
            self.ui.yourNickShow.setText(user_data[0][2])
            self.ui.yourLoginShow.setText(user_data[0][0])
            self.ui.WindowsStack.setCurrentWidget(self.ui.userData)
            try:
                best = (self.cur.execute(f"""SELECT Best FROM Scoreboard 
                                        WHERE nickname LIKE '{user_data[0][2]}'""").fetchall())[0][0]
                self.ui.yourBestCMShow.setText(f'{str(best)} с/м')
            except:
                self.ui.yourBestCMShow.setText('Пока что у нас нет вашего результата')
        else:
            self.show_go_sys(need='login')

    def show_change_pass(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.passChanging)

    
    def show_menu(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.Menu)

    def show(self):
        self.main_win.show()


    def show_modes(self):
        self.ui.descModeLabel_3.setText(self.ModesDescriptions[self.ui.modesBox.currentText()])
        self.ui.WindowsStack.setCurrentWidget(self.ui.Modes)
    
    def change_desc(self):
        self.ui.descModeLabel_3.setText(self.ui.ModesDescriptions[self.ui.modesBox.currentText()])
    
    def start_mode(self):
        mode = self.ui.modesBox.currentText()
        match mode:
            case 'Соревнование':
                self.ui.lcdTimer.display(self.duration_cm)
                self.index = 0
                self.ui.inputText.setPlaceholderText("Чтобы начать введите любой символ и нажмите пробел")
                self.inputlist.clear()
                shuffle(self.wordlist_cm)
                self.ui.lcdTimer.display(self.duration_cm)
                self.ui.inputText.clearFocus()
                self.ui.WindowsStack.setCurrentWidget(self.ui.CMMode)
                self.cm_opened = True
                if self.cm_opened is True:
                    self.cm_going = False
                    self.wordlist_cm = self.wordlist_cm[1:]
    
    def end_cm(self):
        self.ui.inputText.setPlaceholderText("Чтобы начать введите любой символ и нажмите пробел")
        self.inputlist.clear()
        self.ui.WindowsStack.setCurrentWidget(self.ui.Menu)
    
    def again_cm(self):
        self.refresh_cm()
        self.start_mode()
    
    def timer_start(self):
        self.time_left_int = self.duration_cm
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.timer_timeout)
        self.timer.start(1000)
        self.update_gui()

    def timer_timeout(self):
        self.time_left_int -= 1
        self.update_gui()
        self.timer.start(1000)
        if self.time_left_int == 0:
            self.stop_cm()

    def update_gui(self):
        self.ui.lcdTimer.display(self.time_left_int)
    
    def refresh_cm(self):
        try:
            self.index = 0
            self.cm_going = False
            self.ui.inputText.setText('')
            self.ui.inputText.setPlaceholderText("Чтобы начать введите любой символ и нажмите пробел")
            self.ui.outputText.setText('')
            self.timer.stop()
            self.time_left_int = self.duration_cm
            self.inputlist.clear()
            shuffle(self.wordlist_cm)
            self.ui.lcdTimer.display(self.duration_cm)
            self.ui.inputText.clearFocus()
        except:
            pass
    
    def stop_cm(self):
        self.show_results_cm(self.inputlist)
        self.timer.stop()

    def show_results_cm(self, lst):
        greatcount = 0
        try:
            if len(lst[0]) == 1:
                lst = lst[1:]
        except:
            pass
        count = len(lst)
        for i in range(len(lst)):
            if lst[i] == self.wordlist_cm[i]:
                greatcount += 1
        try:
            accuracy = f'Точность введенных слов равняется {round((greatcount / count) * 100)}%'
            count = f'Количество введеных слов за минуту равняется {count}'
        except:
            pass
            accuracy = f'Точность введенных слов равняется 0%'
            count = f'Количество введеных слов за минуту равняется {count}'
        self.ui.countLabel.setText(count)
        self.ui.accuracyLabel.setText(accuracy)
        self.ui.greatCountLabel.setText(f'Количество правильных слов за минуту - {greatcount}')
        self.ui.WindowsStack.setCurrentWidget(self.ui.CMResults)
        if self.current_user[2] not in (self.cur.execute("""SELECT nickname FROM Scoreboard""").fetchall())[0]\
            or greatcount > (self.cur.execute(f"""SELECT Best FROM Scoreboard
                                                WHERE nickname LIKE '{self.current_user[2]}'""").fetchall())[0][0]:
            self.cur.execute("""INSERT INTO Scoreboard(nickname, Best) 
                            VALUES (?,?);""", (self.current_user[2], greatcount))
            self.con.commit()

    def show_about(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.AboutApp)
    
    def show_go_sys(self, need='mode'):
        if self.current_user == (None, False, None) and need == 'login':
            self.ui.WindowsStack.setCurrentWidget(self.ui.goToSys)
        elif self.current_user != (None, False, None):
            self.show_modes()
        elif self.current_user == (None, False, None):
            self.ui.WindowsStack.setCurrentWidget(self.ui.goToSys)

    def show_sign_in(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.SignIn)

    def show_sign_up(self):
        self.ui.WindowsStack.setCurrentWidget(self.ui.SignUp)
    
    def show_rating(self):
        self.cur.execute(f"""SELECT nickname, Best from Scoreboard
                                    ORDER BY Best DESC""")
        top_ten = self.cur.fetchmany(10)
        place = 1
        for item in range(len(top_ten)):
            top_ten[item] = (top_ten[item][0], top_ten[item][1], place)
            place += 1
        for row in range(len(list(top_ten))):
            for item in range(len(top_ten[row])):
                self.ui.scoreTable.setItem(row, item, QtWidgets.QTableWidgetItem(str(top_ten[row][item])))
        self.ui.scoreTable.resizeColumnsToContents()
        self.ui.scoreTable.resizeRowsToContents()
        self.ui.WindowsStack.setCurrentWidget(self.ui.Rating)
    
    def change_pass(self):
        cur_pass = self.ui.confirmCurPassLine.text()
        new_pass = self.ui.newPassLine.text()
        new_pass_conf = self.ui.confirmNewPassLine.text()
        if self.check_password(new_pass, new_pass_conf) is True:
            self.cur.execute(f"""UPDATE Logins SET Password = '{new_pass}'
                                WHERE Login = '{self.current_user[0]}'""")
            self.show_menu()
            self.con.commit()
        else:
            self.ui.newPassLine.setStyleSheet("background-color: rgb(255, 96, 96);")
            self.ui.confirmNewPassLine.setStyleSheet("background-color: rgb(255, 96, 96);")
            self.ui.confirmCurPassLine.setStyleSheet("background-color: rgb(255, 96, 96);")

    
    def wrong_info_in(self):
        self.ui.LoginLine.setStyleSheet("background-color: rgb(255, 96, 96);")
        self.ui.PassLine.setStyleSheet("background-color: rgb(255, 96, 96);") 

    def wrong_format_up(self):
        self.ui.NameLine.setStyleSheet("background-color: rgb(255, 96, 96);")
        self.ui.PassLine1.setStyleSheet("background-color: rgb(255, 96, 96);") 
        self.ui.PassLine2.setStyleSheet("background-color: rgb(255, 96, 96);")
        self.ui.LoginLine_2.setStyleSheet("background-color: rgb(255, 96, 96);")

    def check_password(self, pass1=0, pass2=0):
        if len(pass1) >= 6 and pass1.isalnum() and pass1 == pass2:          
            return True
        else:
            return False

    def check_login(self, login='s'):
        if len(login) >= 4 and login not in self.login_data:                      
            return True
        else:
            return False
                                                                            
    def check_nick(self, nick='s'):
        if len(nick) >= 4 and nick not in self.nickname_data:                     
            return True
        else:
            return False

    def sign_in(self):
        login_try = self.ui.LoginLine.text()
        pass_try = self.ui.PassLine.text()
        if login_try in self.login_data:
            if pass_try == (self.cur.execute(f"""SELECT Login, Password FROM Logins                                      
                                                WHERE Login LIKE '{login_try}'""").fetchall())[0][1]:  # Сверяем пароль введенный с тем, что в базе
                nickname = (self.cur.execute(f"""SELECT Nickname from Logins
                                            WHERE Login LIKE '{login_try}'""").fetchall())[0]
                self.current_user = (login_try, True, nickname[0]) # Задаем значения данных текущей сессии
                self.show_menu()
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
            self.current_user = (login, True, nickname)
            self.show_menu()
        else:
            self.wrong_format_up()
            wrong_info = [("Логин", self.check_login(login)), ("Отображаемое имя", self.check_nick(nickname)), \
                          ("Пароль", self.check_password(passw, confpassw))]
            wrong_info = [check[0] for check in wrong_info if check[1] is False]
            errors = '\n'.join(wrong_info)
            up_error = QtWidgets.QMessageBox(self)
            up_error.setWindowTitle('Кажется вы что-то сделали не так')
            up_error.setText(f"""Вы ошиблись в полях: \n{errors}""")
            ok_btn = up_error.addButton("Понятно", QtWidgets.QMessageBox.AcceptRole)
            up_error.exec_()
            if up_error.clickedButton() is ok_btn:
                self.ui.LoginLine_2.setStyleSheet("color: rgb(112, 112, 112);\n"
                                                  "background-color: rgb(213, 213, 213);")
                self.ui.NameLine.setStyleSheet("color: rgb(112, 112, 112);\n"
                                               "background-color: rgb(213, 213, 213);")
                self.ui.PassLine1.setStyleSheet("color: rgb(112, 112, 112);\n"
                                                "background-color: rgb(213, 213, 213);")
                self.ui.PassLine2.setStyleSheet("color: rgb(112, 112, 112);\n"
                                                "background-color: rgb(213, 213, 213);")
                up_error.close()

    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and source is self.ui.inputText and event.key() == QtCore.Qt.Key_Space):
            if not all(i == ' ' for i in list(self.ui.inputText.toPlainText())):
                if self.cm_going is False:
                    self.timer_start()
                    self.cm_going = True
                self.inputlist.append((self.ui.inputText.toPlainText()).strip())
                self.ui.inputText.clear()
                self.ui.outputText.setText(self.wordlist_cm[self.index])
                self.index += 1

        return super().eventFilter(source, event)
   
    def close_app(self):
        exit = QtWidgets.QMessageBox(self)
        exit.setIcon(QtWidgets.QMessageBox.Question)
        exit.setWindowTitle('Подтвердите выход')
        exit.setText('Вы точно хотите выйти?..')
        yes_btn = exit.addButton('Да', QtWidgets.QMessageBox.AcceptRole)
        no_btn = exit.addButton('Нет', QtWidgets.QMessageBox.AcceptRole)
        exit.exec_()
        if exit.clickedButton() is yes_btn:
            sys.exit()
        elif exit.clickedButton() is no_btn:
            exit.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())