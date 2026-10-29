"""Optional authenticated account browser; preserves existing native diagnostic UI.
Tokens/passwords stay in memory. Business mutation forms remain API workflows.
"""
import json
import requests
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLineEdit,QPushButton,QComboBox,QPlainTextEdit,QLabel
from shiboken6 import isValid

P='/api/v2/ecosystem'


class BusinessWorkspace(QDialog):
    def __init__(self,host,fixed_workspace=None):
        super().__init__(host);self.fixed_workspace=fixed_workspace;self.host=host;self.base_url=host.api.base_url.rstrip('/');self.token='';self.revision=0;self.pages=[]
        self.setWindowTitle('AI Car Scanner • '+(fixed_workspace or 'Account workspace'));self.resize(780,650)
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
        self.organization=QLineEdit();self.organization.setPlaceholderText('Business name')
        self.address=QLineEdit();self.address.setPlaceholderText('Business address')
        self.onboard=QPushButton('Register workshop' if fixed_workspace=='CUSTOMER' else 'Register shop')
        self.onboard.clicked.connect(self.create_organization)
        for field in (self.organization,self.address,self.onboard):
            layout.addWidget(field);field.setVisible(False)
        if fixed_workspace:self.workspace.hide()
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
        allowed=data['modes']+data['portals']
        self.workspace.clear()
        if self.fixed_workspace:
            if self.fixed_workspace in allowed:self.workspace.addItem(self.fixed_workspace)
            for field in (self.organization,self.address,self.onboard):field.setVisible(self.fixed_workspace not in allowed and self.fixed_workspace in ('CUSTOMER','MARKET'))
        else:self.workspace.addItems(allowed)
        self.workspace.setEnabled(bool(self.workspace.count()))
        if self.workspace.count():self.load_navigation()
        else:self.output.setPlainText('Create your business below to activate this application workspace.')

    def load_navigation(self):
        if not self.token or not self.workspace.count():return
        def ready(data):
            self.pages=data['pages'];self.page.clear();self.page.addItems([p['label'] for p in self.pages]);self.load_page()
        self.request(P+'/navigation?workspace='+self.workspace.currentText()+'&language='+self.language.currentText(),done=ready)

    def create_organization(self):
        if not self.token or self.fixed_workspace not in ('CUSTOMER','MARKET'):return
        body={'name':self.organization.text(),'address':self.address.text()}
        path='/service-centers' if self.fixed_workspace=='CUSTOMER' else '/merchants'
        self.request(P+path,'POST',body,lambda _:self.request(P+'/me',done=self.show_account))

    def load_page(self):
        index=self.page.currentIndex()
        if self.token and 0<=index<len(self.pages):self.request(self.pages[index]['path'])

    def logout(self):
        if self.token:self.request(P+'/auth/logout','POST')
        self.revision+=1;self.token='';self.workspace.clear();self.workspace.setEnabled(False);self.pages=[];self.page.clear();self.output.clear()
        for field in (self.organization,self.address,self.onboard):field.setVisible(False)

    def closeEvent(self,event):
        self.logout();super().closeEvent(event)
