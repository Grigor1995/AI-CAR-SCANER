"""Optional authenticated account browser; preserves existing native diagnostic UI.
Tokens/passwords stay in memory. Business mutation forms remain API workflows.
"""
import json
import requests
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLineEdit,QPushButton,QComboBox,QPlainTextEdit,QLabel
from shiboken6 import isValid

P='/api/v2/ecosystem'


class BusinessWorkspace(QDialog):
    def __init__(self,host):
        super().__init__(host);self.host=host;self.base_url=host.api.base_url.rstrip('/');self.token='';self.revision=0;self.pages=[]
        self.setWindowTitle('USER / CUSTOMER / ADMIN • MARKET');self.resize(780,650)
        layout=QVBoxLayout(self)
        layout.addWidget(QLabel('Account workspace • backend ecosystem mode and migrations required'))
        self.full_name=QLineEdit();self.full_name.setPlaceholderText("Full name")
        layout.addWidget(self.full_name)
        self.email=QLineEdit();self.email.setPlaceholderText('Email')
        self.password=QLineEdit();self.password.setPlaceholderText('Password');self.password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.email);layout.addWidget(self.password)
        row=QHBoxLayout();login=QPushButton('Sign in');logout=QPushButton('Sign out');row.addWidget(login);row.addWidget(logout);signup=QPushButton('Create account');row.addWidget(signup);layout.addLayout(row)
        signup.clicked.connect(self.register)
        self.workspace=QComboBox();self.workspace.setEnabled(False);layout.addWidget(self.workspace)
        self.language=QComboBox();self.language.addItems(['en','hy','ru','fr']);layout.addWidget(self.language)
        self.page=QComboBox();layout.addWidget(self.page);refresh=QPushButton('Open / Refresh');layout.addWidget(refresh)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);layout.addWidget(self.output)
        login.clicked.connect(self.login);logout.clicked.connect(self.logout)
        self.workspace.activated.connect(self.load_navigation);self.language.activated.connect(self.load_navigation)
        refresh.clicked.connect(self.load_page)

    def request(self,path,method='GET',body=None,done=None):
        base=self.base_url;token=self.token;ticket=self.revision
        def work():
            with requests.Session() as client:
                response=client.request(method,base+path,json=body,timeout=15,allow_redirects=False,headers={'Authorization':'Bearer '+token} if token else {})
                if response.status_code>=400:raise ValueError(f'HTTP {response.status_code}: '+response.json().get('detail','Request failed'))
                return response.json() if response.content else {}
        def result(data):
            if isValid(self) and ticket==self.revision:
                if done:done(data)
                else:self.output.setPlainText(json.dumps(data,ensure_ascii=False,indent=2))
        def failed(error):
            if isValid(self) and ticket==self.revision:self.output.setPlainText(str(error))
        self.host.run_worker(work,result,failed)

    def register(self):
        if self.token:
            self.output.setPlainText('Sign out before registering another account.')
            return
        data={'email':self.email.text(),'password':self.password.text(),'full_name':self.full_name.text()}
        self.password.clear()
        self.request(P+'/accounts','POST',data)

    def login(self):
        self.revision+=1
        data={'email':self.email.text(),'password':self.password.text()};self.password.clear()
        def logged(result):
            self.token=result['access_token'];self.request(P+'/me',done=self.show_account)
        self.request(P+'/auth/login','POST',data,logged)

    def show_account(self,data):
        self.workspace.clear();self.workspace.addItems(data['modes']+data['portals']);self.workspace.setEnabled(True);self.load_navigation()

    def load_navigation(self):
        if not self.token:return
        def ready(data):
            self.pages=data['pages'];self.page.clear();self.page.addItems([p['label'] for p in self.pages]);self.load_page()
        self.request(P+'/navigation?workspace='+self.workspace.currentText()+'&language='+self.language.currentText(),done=ready)

    def load_page(self):
        index=self.page.currentIndex()
        if self.token and 0<=index<len(self.pages):self.request(self.pages[index]['path'])

    def logout(self):
        if self.token:self.request(P+'/auth/logout','POST')
        self.revision+=1;self.token='';self.workspace.clear();self.workspace.setEnabled(False);self.pages=[];self.page.clear();self.output.clear()

    def closeEvent(self,event):
        self.logout();super().closeEvent(event)
