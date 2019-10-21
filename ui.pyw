import threading
import bulbabot
import iomanage
import asyncio

import time

from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QLabel, QListWidget, QListWidgetItem, QLineEdit, QCheckBox, QComboBox

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


class PokeFarmTab(QWidget):
    def _switched(self):
        self.SetupServC()
        self.SetupChanC(0)

    def __init__(self, p):
        super().__init__()

        self.p = p
        self.catchchange = False

        RootLayout = QVBoxLayout()
        self.setLayout(RootLayout)

        ## Modes ##

        ModeW = QWidget()
        RootLayout.addWidget(ModeW)

        ModeL = QHBoxLayout()
        ModeW.setLayout(ModeL)

        ModeLabel = QLabel("Pokefarmer Mode")
        ModeL.addWidget(ModeLabel)

        ModeC = QComboBox()
        ModeL.addWidget(ModeC)

        ModeC.addItem("Off")
        ModeC.addItem("Slow (30s - 50s between messages)")
        ModeC.addItem("Medium (8s - 15s between messages)")
        ModeC.addItem("Fast (1s - 6s between messages)")
        ModeC.addItem("Bot (1s - 2s between messages)")

        ModeC.setCurrentIndex(p.io.Read()["Pokefarm"]["Mode"])
        ModeC.currentIndexChanged.connect(self.ChangedMode)

        ## Channel ##

        CW = QWidget()
        RootLayout.addWidget(CW)

        CL = QHBoxLayout()
        CW.setLayout(CL)

        ServLabel = QLabel("Server")
        CL.addWidget(ServLabel)

        self.ServC = QComboBox()
        CL.addWidget(self.ServC)
        self.SetupServC()

        ChanLabel = QLabel("Channel")
        CL.addWidget(ChanLabel)

        self.ChanC = QComboBox()
        CL.addWidget(self.ChanC)
        self.SetupChanC(self.ServC.currentIndex())

        self.ServC.currentIndexChanged.connect(self.SetupChanC)
        self.ChanC.currentTextChanged.connect(self.ChangedChannel)

        self.hide()

    def SetupServC(self):
        if self.p.bot == None or self.p.botthread == None:
            self.ServC.clear()
            self.ServC.addItem("Bot needs to be on to change this option.")
        elif not self.p.bot.is_ready():
            self.ServC.clear()
            self.ServC.addItem("Please wait for bot to start before changing this option.")
        else:
            self.ServC.clear()

            servs = self.p.bot.guilds
            servnames = []

            self.ServC.addItem(" ")

            for guild in servs:
                #servnames.append(guild.name)
                self.ServC.addItem(guild.name + " (" + str(guild.id) + ")")

            self.SetupChanC(0)

            #self.ServC.addItems(*servnames)

    def SetupChanC(self, i):
        self.catchchange = True

        if self.p.bot == None or self.p.botthread == None:
            self.ChanC.clear()
        elif not self.p.bot.is_ready():
            self.ChanC.clear()
        elif i == 0:
            self.ChanC.clear()
        else:
            self.ChanC.clear()
            self.catchchange = True
            n = self.ServC.currentText()

            for guild in self.p.bot.guilds:
                if n == guild.name + " (" + str(guild.id) + ")": break

            self.ChanC.addItem(" ")

            for chan in guild.channels:
                if chan.type == bulbabot.discord.ChannelType.text:
                    self.ChanC.addItem(chan.name + " (" + str(chan.id) + ")")

    def ChangedChannel(self, t):
        if self.catchchange:
            self.catchchange = False
            return

        try:
            if t == " ":
                d = self.p.io.Read()
                d["Pokefarm"]["Channel"] = None
                self.p.io.Write(d)
                return

            self.p.dbprint(t)
            id = int(t.split("(")[-1].split(")")[0])

            d = self.p.io.Read()
            d["Pokefarm"]["Channel"] = id
            self.p.io.Write(d)

            asyncio.ensure_future(self.p.bot.Farm(), loop=self.p.bot.loop)
        except Exception as e:
            self.p.dbprint(e)
            print("[UI] Tried to set farming channel, but failed!")

    def ChangedMode(self, i):
        d = self.p.io.Read()
        d["Pokefarm"]["Mode"] = i
        self.p.io.Write(d)


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
        self.print_wrap.emit(str(s))

    def ChangeTab(self, tab):
        if not self.active == None:
            self.active.hide()

        try:
            tab._switched()
        except:
            pass

        self.active = tab
        tab.show()

    def stop_bot(self):
        try:
            self.StartButton.setEnabled(False)
            self.StopButton.setEnabled(False)
            asyncio.ensure_future(self.bot.close(), loop = self.bot.loop)

            while self.botthread.is_alive():
                time.sleep(.1)

            print("[UI] Stopped bot.")
            self.botthread = None
            self.bot = None
        except:
            print("[UI] Tried to stop bot, but bot wasn't running!")

        self.StartButton.setEnabled(True)
        self.StopButton.setEnabled(True)

    def start_bot(self):
        if self.botthread == None or not self.botthread.is_alive():
            self.StartButton.setEnabled(False)
            self.StopButton.setEnabled(False)
            print("[UI] Starting bot...")

            asyncio.set_event_loop(asyncio.new_event_loop())

            self.bot = bulbabot.bot(self.io)
            self.botthread = threading.Thread(target = self.bot.run, args=["MAIN"],\
                kwargs={"ror": [[self.StopButton.setEnabled, True], [self.StartButton.setEnabled, True], [self.SetupServ], [self.SetupChan, 0]]})
            self.botthread.daemon = True
            self.botthread.start()
            #self.StartButton.setEnabled(True)
        else:
            print("[UI] Tried to start bot, but bot was already running!")

    def __init__(self):
        global print

        super().__init__()
        self.dbprint = print
        print = self.print

        self.io = iomanage.IOManager("configs.json")

        d = self.io.Read()
        if d == {}:
            self.io.Write(Default_Settings)
            d = Default_Settings

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

        SSW = QWidget()
        TabBarLayout.addWidget(SSW)

        SSWL = QHBoxLayout()
        SSW.setLayout(SSWL)

        self.StartButton = QPushButton("Start Bot")
        self.StartButton.clicked.connect(self.start_bot)
        self.StopButton = QPushButton("Stop Bot")
        self.StopButton.clicked.connect(self.stop_bot)

        SSWL.addWidget(self.StartButton)
        SSWL.addWidget(self.StopButton)

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

        PKTab = PokeFarmTab(self)
        TabSectL.addWidget(PKTab)

        self.SetupServ = PKTab.SetupServC
        self.SetupChan = PKTab.SetupChanC

        ## Sig Connects ##

        TerminalButton.clicked.connect(lambda: self.ChangeTab(TermTab))
        PokeFarmerButton.clicked.connect(lambda: self.ChangeTab(PKTab))
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
