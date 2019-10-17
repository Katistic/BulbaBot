import threading
import bulbabot
import iomanage

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



io = iomanage.IOManager("configs.json")

d = io.Read()
if d == {}: io.Write(Default_Settings)

bot = bulbabot.bot(io)

t = threading.Thread(target = bot.run())
t.daemon = False
t.start()

while t.is_alive():
    time.sleep(10)
