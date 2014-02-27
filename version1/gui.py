'''
Created on 13.2.2014

@author: suonto
'''
import sys
import os
from PyQt4 import QtGui
from client import Client
import time
import threading
import warnings
from PyQt4.QtCore import QRegExp
warnings.filterwarnings("ignore")
import pyperclip
warnings.resetwarnings()

import message as m

class Fields(object):

    def __init__(self):
        self.id = None
        self.pwd = None
        self.row = None

class Buttons(object):

    def __init__(self):
        self.copy = None
        self.remove = None
        self.row = None

class Data(object):

    def __init__(self):
        self.id = None
        self.pwd = None
        self.row = None

class Row(object):
    
    def __init__(self, fields, buttons, data):
        self.fields = fields 
        self.data = data
        self.buttons = buttons

        self.fields.row = self 
        self.data.row = self
        self.buttons.row = self

class Refresher(threading.Thread):
    
    def __init__(self, refresh_function, wait_time=290):
        threading.Thread.__init__(self)
        self.daemon = True
        self.__rf = refresh_function
        self.__wt = wait_time
    
    def run(self):
        '''
        Pings the server every wait time period (5 min) to signal that the session is still alive.
        '''
        while True:
            time.sleep(self.__wt)
            response = self.__rf()

class Gui(QtGui.QWidget):
    '''
    This is the user interface of the suonto.com password manager.
    Enjoy!
    '''
    def __init__(self):
        super(Gui, self).__init__()
        
        self.title = 'suonto.com password manager' 
        self.rows = []
        self.outer_grid = QtGui.QGridLayout()
        self.client = Client(None, None)

    def login_screen(self):

        self.login_widgets = []
        username_label = QtGui.QLabel("Username: ")
        self.outer_grid.addWidget(username_label, 0, 0)
        self.login_widgets.append(username_label)
        
        password_label = QtGui.QLabel("Password: ")
        self.outer_grid.addWidget(password_label, 1, 0)
        self.login_widgets.append(password_label)

        username_edit = QtGui.QLineEdit(self)
        username_edit.setFixedWidth(150)
        username_edit.setInputMask("Nnnnnnnnnnnnnnn")
        self.outer_grid.addWidget(username_edit, 0, 1)
        self.login_widgets.append(username_edit)
        
        note = QtGui.QLabel('')
        # Params: widget to add, row, column, row_span, column span
        self.outer_grid.addWidget(note, 2, 0, 4, 3)
        self.login_widgets.append(note)

        password_edit = QtGui.QLineEdit(self)
        password_edit.setFixedWidth(150)
        password_edit.setEchoMode(QtGui.QLineEdit.Password)
        password_edit.returnPressed.connect(self.login(username_edit, password_edit, note))
        self.outer_grid.addWidget(password_edit, 1, 1)   
        self.login_widgets.append(password_edit)
        
        
        new_button = QtGui.QPushButton('New user')
        new_button.clicked.connect(self.register_screen)
        self.outer_grid.addWidget(new_button, 0, 2)
        self.login_widgets.append(new_button)

        login_button = QtGui.QPushButton('Login')
        login_button.clicked.connect(password_edit.returnPressed)
        self.outer_grid.addWidget(login_button, 1, 2)
        self.login_widgets.append(login_button)

        self.setLayout(self.outer_grid)
        self.move(500, 200)
        self.setWindowTitle(self.title)
        self.show()

    def register_screen(self):
        self.hide()
        self.swipe_screen(self.login_widgets)
        self.registration_widgets = []
        username_label = QtGui.QLabel("Username: ")
        self.outer_grid.addWidget(username_label, 0, 0)
        self.registration_widgets.append(username_label)
        
        password_label = QtGui.QLabel("Password: ")
        self.outer_grid.addWidget(password_label, 1, 0)
        self.registration_widgets.append(password_label)

        password_label2 = QtGui.QLabel("Re-type: ")
        self.outer_grid.addWidget(password_label2, 2, 0)
        self.registration_widgets.append(password_label2)

        reg_token = QtGui.QLabel("Reg. token: ")
        self.outer_grid.addWidget(reg_token, 3, 0)
        self.registration_widgets.append(reg_token)

        username_edit = QtGui.QLineEdit(self)
        username_edit.setFixedWidth(150)
        username_edit.setInputMask("Nnnnnnnnnnnnnnn")
        self.outer_grid.addWidget(username_edit, 0, 1)
        self.registration_widgets.append(username_edit)

        pass_edit = QtGui.QLineEdit(self)
        pass_edit.setFixedWidth(150)
        pass_edit.setEchoMode(QtGui.QLineEdit.Password)
        self.outer_grid.addWidget(pass_edit, 1, 1)
        self.registration_widgets.append(pass_edit)

        pass_edit2 = QtGui.QLineEdit(self)
        pass_edit2.setFixedWidth(150)
        pass_edit2.setEchoMode(QtGui.QLineEdit.Password)
        self.outer_grid.addWidget(pass_edit2, 2, 1)
        self.registration_widgets.append(pass_edit2)

        token_edit = QtGui.QLineEdit(self)
        token_edit.setFixedWidth(150)
        self.outer_grid.addWidget(token_edit, 3, 1)
        self.registration_widgets.append(token_edit)
     
        note = QtGui.QLabel('You can try the password manager with a demo\naccount by clicking the "Demo" button.\nFor a registration token, contact Markus Suonto.')
        # Params: widget to add, row, column, row_span, column span
        self.outer_grid.addWidget(note, 4, 0, 4, 3)
        self.registration_widgets.append(note)

        demo_button = QtGui.QPushButton('Demo')
        demo_button.clicked.connect(self.demo(note))
        self.outer_grid.addWidget(demo_button, 2, 2)
        self.registration_widgets.append(demo_button)

        reg_button = QtGui.QPushButton('Register')
        reg_button.clicked.connect(self.register(username_edit, pass_edit, pass_edit2, token_edit, note))
        self.outer_grid.addWidget(reg_button, 3, 2)
        self.registration_widgets.append(reg_button)

        self.show()

    def demo(self, note):
        def demo():
            response = self.client.demo()
            if response.type == m.T_RESPONSE:
                un = response.args[m.K_USER]
                pp = response.args[m.K_DEMO_PASS]
                self.hide()
                self.swipe_screen(self.registration_widgets)
                self.client.set_credentials(un, pp)
                self.client.demo_settings(response.args[m.K_SID])
                self.launch_client(demo=True)
            else:
                note.setText(response.pay)
        return demo

    def register(self, uname, pwd, pwd2, reg_token, note):
        def register():    
            un = str(uname.text())
            pp = str(pwd.text())
            pp2 = str(pwd2.text())
            rt = str(reg_token.text())
            un_valid = self.__is_valid_id(un)
            pwd_valid = self.__is_valid_password(pp)
            if un_valid and pwd_valid and pp==pp2 and len(pp) > 9:
                response = self.client.register(un, pp, rt)
                if response.type == m.T_ACK:
                    self.hide()
                    self.swipe_screen(self.registration_widgets)
                    self.client.set_credentials(un, pp)
                    self.launch_client()  
                else:  
                    note.setText(response.pay)  
            elif not un_valid:
                note.setText("Invalid username. It has to be 4-15 normal\nenglish characters or numbers.")  
            elif not pwd_valid or len(pp) < 10:
                note.setText("Invalid password. Password has to be 10-50\ncharacters long.")
            elif pp != pp2:
                note.setText("Passwords don't match.")
        return register

    def login(self, uname, pwd, note):
        def login():
            un = str(uname.text())
            pp = str(pwd.text())
            response = self.client.try_login(un, pp)
            if response.type == m.T_RESPONSE:
                self.hide()
                self.swipe_screen(self.login_widgets)
                self.client.set_credentials(un, pp)
                self.launch_client()
            else:
                note.setText('Access denied.')
                pwd.setText('')
        return login

    def swipe_screen(self, widgets):
        for widget in widgets:
            self.outer_grid.removeWidget(widget)
            widget.deleteLater()

    def launch_client(self, demo=False):
        Refresher(self.client.stay_logged).start()
        if not demo:
            self.client.login()
        self.grid = QtGui.QGridLayout()    
        self.passwords = self.fetch_passwords()
        if self.passwords != None:
            self.continue_launch()
        else:
            label = QtGui.QLabel("Permission to passwords denied.\nEither the account has been registered elsewhere,\nor you have deleted your username.pem file.\nIn the latter case, contact Markus Suonto for advice.")
            self.outer_grid.addWidget(label, 0, 0)
            self.show()

    def continue_launch(self):
        # adding the scroll area for the passwords
        scrollingWidget = QtGui.QWidget()
        scrollingWidget.setLayout(self.grid)

        self.ScrollArea = QtGui.QScrollArea()
        self.ScrollArea.setWidgetResizable(True)
        self.ScrollArea.setEnabled(True)
        self.ScrollArea.setFixedSize(400, 60) 

        self.ScrollArea.setWidget(scrollingWidget)
        self.outer_grid.addWidget(self.ScrollArea, 2, 0, 1, 2)
        
        self.rows = self.__build_rows()
        self.__rows_to_window()
        
        # adding identifier and password labels 
        id_label = QtGui.QLabel("Identifier: ")
        self.outer_grid.addWidget(id_label, 0, 0)
        
        password_label = QtGui.QLabel("password: ")
        self.outer_grid.addWidget(password_label, 0, 1)
        
        # adding input text field for password id and value.
        self.id_edit = QtGui.QLineEdit(self)
        self.id_edit.setFixedWidth(100)
        self.id_edit.returnPressed.connect(self.add_password())
        self.outer_grid.addWidget(self.id_edit, 1, 0)
        
        self.pass_edit = QtGui.QLineEdit(self)
        self.pass_edit.setFixedWidth(150)
        self.pass_edit.returnPressed.connect(self.add_password())
        self.outer_grid.addWidget(self.pass_edit, 1, 1)   
        
        # "Add password"-button to the first row
        add_password_button = QtGui.QPushButton('Add Password')
        self.outer_grid.addWidget(add_password_button, 1, 3)
        add_password_button.clicked.connect(self.add_password())
        
        # adding note field in the bottom
        self.note_label = QtGui.QLabel('Welcome '+self.client.get_username()+".")
        self.outer_grid.addWidget(self.note_label, 4, 0, 2, 3)
        
        self.show()

    def closeEvent(self, event):
        uname = self.client.get_username() 
        if uname:
            if uname.startswith('demo_'):
                try:
                    os.remove(uname)
                except:
                    pass
            try:
                self.client.logout()
            except:
                pass

    def fetch_passwords(self):
        response = self.client.get_passwords()
        if response.type == m.T_RESPONSE:
            passwords = response.args
        else:
            return None
        pwds = {}
        try:
            for id in passwords.keys():
                pwds[id] = self.client.decrypt_rsa(passwords[id])
        except Exception as e:
            #print e
            return None
        return pwds
        
    def add_password(self):
        def add_password():
            id = self.read_id_edit()
            pwd = self.read_pass_edit()
            id_valid = self.__is_valid_id(id)
            pwd_valid = self.__is_valid_password(pwd)
            if id_valid and pwd_valid:
                if not id in self.passwords.keys():
                    response = self.client.store_password(id, pwd)
                    if response.type == m.T_ACK:
                        self.update_id_edit('')
                        self.update_pass_edit('')
                        self.passwords[id] = pwd
                        self.rebuild_rows()                       
                    self.update_note_field(response.pay)
                    return
                else:
                    self.update_note_field('Adding duplicate id is not allowed.')

            elif not id_valid:
                self.update_note_field('Invalid id. Id must be 4-15 characters long and it may\nonly contain standard english characters and numbers.')
            elif not pwd_valid:
                self.update_note_field('Invalid password. Password must be 1-50 characters long\nand may not contain whitespaces or country-special characters.')
                
        return add_password
    

    def remove_password(self, id):
        def remove_password():
            for row in self.rows:
                if row.data.id == id:
                    response = self.client.remove_password(id)
                    if response.type == m.T_ACK:
                        del self.passwords[id]
                        self.rebuild_rows()
                    self.update_note_field(response.pay)
                    return
            raise Exception("Remove password failure: row not found.")
        return remove_password
     
    def rebuild_rows(self):
        for row in self.__rows():
            self.__remove_row(row)        
        self.rows = self.__build_rows()
        self.__rows_to_window()

    
    def read_id_edit(self):
        return str(self.id_edit.text())
    
    def read_pass_edit(self):
        return str(self.pass_edit.text())
    
    def update_id_edit(self, text):
        self.id_edit.setText(text)

    def update_pass_edit(self, text):
        self.pass_edit.setText(text)
        
    def update_note_field(self, text):
        self.note_label.setText(text)

    def __build_rows(self):
        rows = []
        for id in self.passwords.keys():
            pwd = self.passwords[id]
            row  = Row(fields=Fields(), buttons=Buttons(), data=Data())
            row.data.id = id
            row.data.pwd = pwd
            id_label = QtGui.QLabel(id)
            id_label.setFixedWidth(100)
            row.fields.id = id_label
            pwd_field = QtGui.QLabel(len(pwd)*'*')
            pwd_field.setFixedWidth(100)
            row.fields.pwd = pwd_field
            copy_button = QtGui.QPushButton('Copy', self)
            copy_button.setFixedWidth(80)
            copy_button.clicked.connect(self.copy(row))
            row.buttons.copy = copy_button
            remove_button = QtGui.QPushButton('Remove', self)
            remove_button.setFixedWidth(80)
            remove_button.clicked.connect(self.remove_password(id))
            row.buttons.remove = remove_button
            rows.append(row)
        if len(rows) < 4:
            self.ScrollArea.setFixedSize(400, 50*len(rows))
        else:
            self.ScrollArea.setFixedSize(420, 200) 
        return sorted(rows, key=lambda row : row.data.id.lower())

    def __rows_to_window(self):
        for i in range(len(self.rows)):
            self.grid.addWidget(self.rows[i].fields.id, i, 0)
            self.grid.addWidget(self.rows[i].fields.pwd, i, 1)
            self.grid.addWidget(self.rows[i].buttons.copy, i, 2)
            self.grid.addWidget(self.rows[i].buttons.remove, i, 3)
        self.adjustSize()
    
    def __remove_row(self, row):
        widgets = []
        widgets.append(row.fields.id)
        widgets.append(row.fields.pwd)
        widgets.append(row.buttons.copy)
        widgets.append(row.buttons.remove)
        for widget in widgets:
            self.grid.removeWidget(widget)
            widget.deleteLater()
        self.rows.remove(row) 
   
    def __is_valid_id(self, id):
        normal = False
        for letter in id:
            if not (64 < ord(str(letter)) < 91 or 96 < ord(str(letter)) < 123 or 47 < ord(str(letter)) < 58):
                return False
        if 3 < len(id) < 16:
            return True
        else:
            return False 

    def __is_valid_password(self, pwd):
        for letter in pwd:
            if ord(str(letter)) < 33 or ord(str(letter)) > 125:
                return False
        if 0 < len(pwd) < 51:
            return True
        else:
            return False 
    
    def copy(self, row):
        def copy():
            pyperclip.copy(row.data.pwd)
            self.note_label.setText("Copied  "+row.data.id+" password into clipboard.\nYou can paste it by pressing ctrl+v.")
        return copy
    
    def __rows(self):
        '''
        Returns the content of self.rows.
        We use this to avoid using self.rows in situations where
        it is modified in the middle of process.
        '''
        rows = []
        for row in self.rows:
            rows.append(row)
        return rows
    
def main():
    app = QtGui.QApplication(sys.argv)
    gui = Gui()
    gui.login_screen()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()
    
    
