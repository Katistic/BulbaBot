import discord
import asyncio
import iomanage

import time

import http.client

bv = "0.0.1"

class bot(discord.Client):
    def __init__(self, io):
        super().__init__()

        self.io = io

        self.bot_id = 365975655608745985
        self.pkfm_pause = False
        self.pcatch_messages = {}

        self.legendaries = [
            'Arceus', 'Articuno', 'Azelf', 'Celebi', 'Cobalion', 'Cosmoem', 'Cosmog', 'Cresselia',
            'Darkrai', 'Deoxys', 'Dialga', 'Diancie', 'Entei', 'Genesect', 'Giratina', 'Groudon',
            'Heatran', 'Ho-Oh', 'Hoopa', 'Jirachi', 'Keldeo', 'Kyogre', 'Kyurem', 'Landorus',
            'Latias', 'Latios', 'Lugia', 'Lunala', 'Magearna', 'Manaphy', 'Marshadow', 'Meloetta',
            'Mesprit', 'Mew', 'Mewtwo', 'Moltres', 'Necrozma', 'Palkia', 'Phione', 'Raikou',
            'Rayquaza', 'Regice', 'Regigigas', 'Regirock', 'Registeel', 'Reshiram', 'Shaymin', 'Silvally',
            'Solgaleo', 'Suicune', 'Tapu Bulu', 'Tapu Fini', 'Tapu Koko', 'Tapu Lele', 'Terrakion', 'Thundurus',
            'Tornadus', 'Type: Null', 'Uxie', 'Victini', 'Virizion', 'Volcanion', 'Xerneas', 'Yveltal',
            'Zapdos', 'Zekrom', 'Zeraora', 'Zygarde']

        #self.run()

    def run(self):
        d = self.io.Read()
        super().run(d["ClientToken"], bot=False)

    ## Checker Functions

    def TimeCheck(self, guild_id, d):
        if not str(guild_id) in d["Autocatcher"]["TimeSettings"]:
            return False if d["Autocatcher"]["Mode"] == "w" else True

        ts = d["Autocatcher"]["TimeSettings"][str(guild_id)]
        if ts["24/7"]: return True

        tReturn = False

        t = time.gmtime()

        if "Day"+str(t[6]+1) in ts:
            ds = ts["Day"+str(t[6]+1)]
            zones = len(ds) / 2

            for x in range(0, zones, 2):
                if t[3]+1 >= ds[x][0] and t[3]+1 <= ds[x+1][0]:
                    if t[3]+1 == ds[x][0]:
                        if t[4] >= ds[x][1]:
                            tReturn = True
                    elif t[3]+1 == ds[x+1][0]:
                        if t[4] <= ds[x][1]:
                            tReturn = True
                    else:
                        tReturn = True

        return rRetrun if d["Autocatcher"]["Mode"] == "w" else not rReturn

    ## Events

    async def on_ready(self):
        print("Logged on as " + self.user.name)

    async def on_message(self, msg):
        d = self.io.Read()
        if d["Autocatcher"]["Mode"] == 0:
            return

        if "catch " in msg.content and not msg.author.id == self.user.id:
            self.pcatch_messages[msg.content.lower()] = msg.guild.id
            await asyncio.sleep(10)
            if msg.content.lower() in self.pcatch_messages: del self.pcatch_messages[msg.content.lower()]

        elif self.user.mention in msg.content and msg.author.id == self.bot_id:
            pkmn = msg.content.split("level ")[1].split(" ")[1].split("!")[0]
            print("Caught " + pkmn + "!")

        else:
            if not msg.guild == None and not msg.guild.id in d["Blacklisted Servers"]:
                if self.TimeCheck(msg.guild.id, d):
                    if msg.author.id == self.bot_id:
                        self.pkfm_pause = True
                        if len(msg.embeds) > 0:
                            for x in msg.embeds:
                                if not x.image.url == discord.Embed.Empty:
                                    if x.title == "‌‌A wild pokémon has аppeаred!":
                                        st = time.time()

                                        if d["Autocatcher"]["Safe"]:
                                            s = await msg.guild.fetch_member(self.user.id)
                                            s = s.status

                                            if s != discord.Status.online and s != discord.Status.do_not_disturb:
                                                await self.change_presence(status = discord.Status.online)

                                            await msg.channel.trigger_typing()
                                        else: s = None

                                        print("\nPokemon appeared! Sending URL to server...")
                                        pf = x.description.split("nd type ")[1].split(" ")[0] ## Get command prefix
                                        pf = pf.replace("а", "a")

                                        conn = http.client.HTTPConnection("katddns.mooo.com", 80)
                                        conn.request("GET", "/bulbabot", headers={"URL": x.image.url, "User-Agent": "BulbaBot/"+bv})
                                        pkmn = str(conn.getresponse().read())
                                        pkmn = pkmn[2:len(pkmn)-1]

                                        if pkmn == "None":
                                            print("No match found.")
                                        else:
                                            print("Found match! Thinking " + pkmn)
                                            await asyncio.sleep(.5)

                                            catchcmd = pf + " " + pkmn
                                            if not catchcmd.lower() in self.pcatch_messages or not not self.pcatch_messages[catchcmd.lower()] == msg.guild.id:
                                                await msg.channel.send(catchcmd)
                                            else:
                                                print("Pokemon guessed, skipping.")

                                        print("Check took " + str(time.time() - st) + " seconds.")
                                        if s != discord.Status.online and s != discord.Status.do_not_disturb:
                                            await self.change_presence(status = s)
                        self.pkfm_pause = False

if __name__ == "__main__":
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
    bot.run()
