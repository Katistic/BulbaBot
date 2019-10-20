import threading
import bulbabot
import iomanage
import asyncio

from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QLabel, QListWidget, QListWidgetItem, QLineEdit, QCheckBox

from PySide2.QtCore import Signal, Slot, QObject


Default_Settings = {
    "Blacklisted Servers": [], # [serv_id, serv_id, serv_id]
    "Pokefarm": {
        "Mode": 0, # 0 = Off, 1 = slow (30 - 50 seconds), 2 = Medium (8 - 15 seconds), 3 = Fast (1 - 6 seconds)
        "Channel": None # Channel ID
    },
    "Autocatcher": {
        "Mode": 0, # 0 = Off, 1 = Catch All, 2 = Legendary Only, 3 = Blacklist
        "Blacklist": [], # Blacklisted pokemon
        "Safe": True, # Try to look human
        "TimeMode": "w", # W = Whitelist, B = Blacklist
        "BlacklistMode": "w", # W = Whitelist, B = Blacklist
        "ToCatch": 1, # % Of spawned pokemon to catch, 1 = 100%
        "TimeSettings": {
            # Server_ID: {"24/7": True, "Day<Num,1-7>": [[Hour1, min1], [Hour2, min2], ..], ..}
        }
    },
    "ClientToken": None, # Token
    "RunOnStart": False
}

class SignalObject(QObject):
    sig = Signal(type)
    #    self.sig.connect(slot)

class TerminalTab(QWidget):
    def __init__(self, p):
        super().__init__()

        self.p = p

        RootLayout = QVBoxLayout(self)
        self.setLayout(RootLayout)

        self.List = QListWidget()
        RootLayout.addWidget(self.List)

        self.hide()

        #self.print_wrap.connect(self.print)

    @Slot(str)
    def print(self, string):
        item = QListWidgetItem()
        item.setText(string)

        self.List.addItem(item)
        self.List.scrollToBottom()

class ClientSettingTab(QWidget):
    def ChangeToken(self, qle):
        t = qle.text()

        id = self.p.io.GetId()
        d = self.p.io.Read(waitforwrite=True, id=id)
        d["ClientToken"] = t
        self.p.io.Write(d, id=id)

    def ROSChange(self, state):
        d = self.p.io.Read()

        if state != 0: state = True
        else: state = False

        d["RunOnStart"] = state
        self.p.io.Write(d)

    def __init__(self, p):
        super().__init__()
        self.p = p

        d = p.io.Read()
        t = d["ClientToken"]

        RootLayout = QVBoxLayout()
        self.setLayout(RootLayout)

        ## Token Input ##

        TokenInsert = QWidget()
        RootLayout.addWidget(TokenInsert)

        TokenInsertL = QHBoxLayout()
        TokenInsert.setLayout(TokenInsertL)

        Label = QLabel("Token")
        TokenInsertL.addWidget(Label)

        #Spacer = QWidget()
        #TokenInsertL.addWidget(Spacer)

        TokenEdit = QLineEdit()
        TokenEdit.setPlaceholderText("Enter user token here...")
        TokenEdit.returnPressed.connect(lambda: self.ChangeToken(TokenEdit))

        if t != None: TokenEdit.setText(t)

        TokenInsertL.addWidget(TokenEdit)

        SetButton = QPushButton("Set Token")
        TokenInsertL.addWidget(SetButton)
        SetButton.clicked.connect(lambda: self.ChangeToken(TokenEdit))

        ## Run-On-Start Toggle ##

        ROSW = QWidget()
        RootLayout.addWidget(ROSW)

        ROSWL = QHBoxLayout()
        ROSW.setLayout(ROSWL)

        #ROSLabel = QLabel("Run Bot On App Start")
        #ROSWL.addWidget(ROSLabel)

        ROSCB = QCheckBox()
        ROSWL.addWidget(ROSCB)

        ROSCB.setText("Run Bot on App Start")
        ROSCB.setChecked(d["RunOnStart"])
        ROSCB.stateChanged.connect(self.ROSChange)

        #########

        ESpacer = QWidget()
        RootLayout.addWidget(ESpacer)

        RootLayout.setStretchFactor(ESpacer, 30)

        self.hide()

class MainWindow(QWidget):
    print_wrap = Signal(str)

    def print(self, s):
        self.print_wrap.emit(s)

    def ChangeTab(self, tab):
        if not self.active == None:
            self.active.hide()

        self.active = tab
        tab.show()

    def stop_bot(self):
        try:
            asyncio.ensure_future(self.bot.close(), loop = self.bot.loop)
        except:
            print("[UI] Tried to stop bot, but bot wasn't running!")

    def start_bot(self):
        if self.botthread == None or not self.botthread.is_alive():
            print("[UI] Starting bot...")

            self.bot = bulbabot.bot(self.io)
            self.botthread = threading.Thread(target = self.bot.run, args=["MAIN"])
            self.botthread.daemon = True
            self.botthread.start()
        else:
            print("[UI] Tried to start bot, but bot was already running!")

    def __init__(self):
        global print

        super().__init__()
        print = self.print

        self.io = iomanage.IOManager("configs.json")

        d = self.io.Read()
        if d == {}: self.io.Write(Default_Settings)

        bulbabot.print = self.print

        self.bot = None
        self.botthread = None
        #self.botthread = threading.Thread(target = self.bot.run)
        #self.botthread.daemon = True
        #self.botthread.start()

        RootLayout = QHBoxLayout()
        self.setLayout(RootLayout)

        ##### Tab Bar ####

        TabBar = QWidget()
        RootLayout.addWidget(TabBar)

        TabBarLayout = QVBoxLayout()
        TabBar.setLayout(TabBarLayout)

        Spacer = QWidget()
        TabBarLayout.addWidget(Spacer)

        TerminalButton = QPushButton("Terminal")
        TabBarLayout.addWidget(TerminalButton)

        AutoCatcherButton = QPushButton("Autocatcher")
        TabBarLayout.addWidget(AutoCatcherButton)

        PokeFarmerButton = QPushButton("Poke-Farmer")
        TabBarLayout.addWidget(PokeFarmerButton)

        Spacer1 = QWidget()
        TabBarLayout.addWidget(Spacer1)

        SettingsButton = QPushButton("Client Settings")
        TabBarLayout.addWidget(SettingsButton)

        Spacer2 = QWidget()
        TabBarLayout.addWidget(Spacer2)

        ##### Tab Section ####

        TabSect = QWidget()
        RootLayout.addWidget(TabSect)

        TabSectL = QVBoxLayout()
        TabSect.setLayout(TabSectL)

        ## Tabs ##

        TermTab = TerminalTab(self)
        TabSectL.addWidget(TermTab)

        CSTab = ClientSettingTab(self)
        TabSectL.addWidget(CSTab)

        ## Sig Connects ##

        TerminalButton.clicked.connect(lambda: self.ChangeTab(TermTab))
        SettingsButton.clicked.connect(lambda: self.ChangeTab(CSTab))

        ##### Sizing #####

        TabBarLayout.setStretchFactor(Spacer, 2)
        TabBarLayout.setStretchFactor(Spacer1, 2)
        TabBarLayout.setStretchFactor(Spacer2, 20)

        RootLayout.setStretchFactor(TabBar, 1)
        RootLayout.setStretchFactor(TabSect, 5)

        ##### SIG & SLOT ####

        #SigObj = SignalObject()
        #SigObj.sig.connect(TermTab.print)

        self.print_wrap.connect(TermTab.print)

        self.showNormal()
        TermTab.show()
        self.active = TermTab

        if d["RunOnStart"]: self.start_bot()


app = QApplication([])

Window = MainWindow()
Window.setWindowTitle("BulbaBot")

app.exec_()


Window.stop_bot()
Window.io.Stop()
