import threading
import bulbabot
import iomanage
import asyncio

from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QLabel, QListWidget, QListWidgetItem

from PySide2.QtCore import Signal, Slot, QObject


Default_Settings = {
    "Blacklisted Servers": [], # [serv_id, serv_id, serv_id]
    "Pokefarm": {
        "Mode": 0, # 0 = Off, 1 = slow (30 - 50 seconds), 2 = Medium (8 - 15 seconds), 3 = Fast (1 - 6 seconds)
        "Channel": None # Channel ID
    },
    "Autocatcher": {
        "Mode": 0, # 0 = Off, 1 = Catch All, 2 = Legendary Only
        "Backlist": [], # Blacklisted pokemon
        "Safe": True, # Try to look human
        "Mode": "w", # W = Whitelist, B = Blacklist
        "TimeSettings": {
            # Server_ID: {"24/7": True, "Day<Num,1-7>": [[Hour1, min1], [Hour2, min2], ..], ..}
        }
    },
    "ClientToken": None # Token
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

class MainWindow(QWidget):
    print_wrap = Signal(str)

    def print(self, s):
        self.print_wrap.emit(s)

    def __init__(self):
        super().__init__()

        self.io = iomanage.IOManager("configs.json")

        d = self.io.Read()
        if d == {}: self.io.Write(Default_Settings)

        bulbabot.print = self.print

        self.bot = bulbabot.bot(self.io)
        self.botthread = threading.Thread(target = self.bot.run)
        self.botthread.daemon = True
        self.botthread.start()

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

        ##### Tab Section ####

        TabSect = QWidget()
        RootLayout.addWidget(TabSect)

        TabSectL = QVBoxLayout()
        TabSect.setLayout(TabSectL)

        ## Tabs ##

        TermTab = TerminalTab(self)
        TabSectL.addWidget(TermTab)

        ##### Sizing #####

        TabBarLayout.setStretchFactor(Spacer, 2)
        TabBarLayout.setStretchFactor(Spacer1, 20)

        RootLayout.setStretchFactor(TabBar, 1)
        RootLayout.setStretchFactor(TabSect, 5)

        ##### SIG & SLOT ####

        #SigObj = SignalObject()
        #SigObj.sig.connect(TermTab.print)

        self.print_wrap.connect(TermTab.print)

        self.showNormal()
        TermTab.show()


app = QApplication([])

Window = MainWindow()
Window.setWindowTitle("BulbaBot")

app.exec_()

asyncio.ensure_future(Window.bot.close(), loop = Window.bot.loop)
Window.io.Stop()
