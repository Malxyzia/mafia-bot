import random
import asyncio
import discord
from discord import *
from discord.ext import commands
from discord.ext.commands import Bot
import time
import copy

### Bot initialisation
# Bot token removed for privacy reasons 
TOKEN = ""

parties = []
bot = commands.Bot(command_prefix='~')
bot.remove_command("help")
game = False
cooldowns = False

class Player:

    def __init__(self, userID, sendID, userNum, role):
        self.role = role
        self.playerRef = userID
        self.refNum = userNum
        self.name = userID.name
        self.sendRef = sendID

class Party:

    def __init__(self, player, guild, ctx):
        self.owner = player
        self.members = [player]
        self.players = []
        self.guild = guild
        self.ctx = ctx
        self.counter = 0
        self.register = {}
        self.told = []
        self.roles = {}
        self.mafiaresponse = ''
        self.doctorresponse = ''
        self.detectiveresponse = ''
        self.dead = []
        self.mafia = []
        self.night = 'off'
        self.mafiavoteno = 0
        self.mafiavote = {}
        self.mafiaaccusations = {}
        self.mafiadead = 0
        self.mafiano = 0
        self.lynchvoter = {}
        self.lynchvoted = {}
        self.doctor = ''
        self.detective = ''
        self.civilians = []
        self.potInt = []
        self.commence = False
        self.theme = random.randint(1,2)
        self.death = None
        self.cooldowns = False
        self.playerNumRef = {}
        self.last = None

    def declare(self, res, tempPlayers):
        if res == 'R':
            res = random.choice(tempPlayers)
            self.last = res
            tempPlayers.remove(res)
            return [tempPlayers, res]
        elif res == 'D':
            res = self.death
            return [tempPlayers, res]
        elif res == 'A':
            res = len(self.players) - 1
            return [tempPlayers, res]
        elif res == 'S':
            res = self.last
            return [tempPlayers, res]


    async def introduction(self):
        self.cooldownIN = True
        playerNum = len(self.members)
        mafiaNum = len(self.mafia)
        playerName = [i.name for i in self.members]
        for line in open('storylines.txt', encoding='utf8'):
            line = line.strip()
            if line == 'Deaths:':
                self.commence = False
            if self.commence:
                self.potInt.append(line)
            if line == str(self.theme):
                self.commence = True
        introduction = random.choice(self.potInt)
        try:
            introduction = introduction.format(str(playerNum), str(mafiaNum))
        except:
            introduction = introduction.format(str(playerNum), random.choice(self.members), str(mafiaNum))
        for item in introduction.split('|'):
            await discord.utils.get(self.guild.channels, name='deliberation-room').send(f"```\n{item}\n```")
            await asyncio.sleep(random.choice([4, 5, 6]))
        await discord.utils.get(self.guild.channels, name='deliberation-room').send("Good Luck!")
        self.cooldownIN = False

    async def deathline(self, player):
        self.cooldownIN = True
        deaths = []
        self.death = player.title()
        for line in open('storylines.txt', encoding='utf8'):
            line = line.strip()
            if line in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20']:
                commence1 = False
                commence2 = False
            if commence1 and commence2:
                deaths.append(line)
            if line == str(self.theme):
                commence1 = True
            if commence1 and line == 'Deaths:':
                commence2 = True
        format, scenario = random.choice(deaths).split('$')
        while format.count('R') > len(self.players):
            format, scenario = random.choice(deaths).split('$')
        tempPlayers = [i.name.title() for i in self.players if i not in self.dead or i.name.title() != self.death]
        rand = []
        for item in format:
            tempPlayers, item = self.declare(item, tempPlayers)
            rand.append(item)
        scenario = scenario.format(*rand)
        for item in scenario.split('|'):
            await discord.utils.get(self.guild.channels, name='deliberation-room').send(f'```\n{item}\n```')
            await asyncio.sleep(random.choice([1,2,3, 4, 5, 6,7,8]))
        self.cooldownIN = False

    async def createMessage(self):
        embed = discord.Embed(title="Party Lobby: Mafia", color=discord.Color.from_rgb(66, 244, 78),
        description='Currently there are {} people in the party.'.format(len(self.members)))
        embed.add_field(name="Members:", value='\n'.join(i.name for i in self.members)) 
        return await self.ctx.send(embed=embed)
    
    async def addMember(self, user):
        self.members.append(user)
        embed = discord.Embed(title="Party Lobby: Mafia", color=discord.Color.from_rgb(66, 244, 78),
        description='Currently there are {} people in the party.'.format(len(self.members)))
        embed.add_field(name="Members:", value='\n'.join(i.name for i in self.members)) 
        logs = await self.ctx.channel.history(limit=20).flatten()
        for msg in logs:
            if msg.author.name == "The Mafia":
                await msg.edit(embed=embed)
                break
        count = 1
        mgs = []
        log = await self.ctx.channel.history(limit=count).flatten()
        for x in log:
            mgs.append(x)
        await self.ctx.channel.delete_messages(mgs)
    
    async def removeMember(self, user):
        self.members.remove(user)
        embed = discord.Embed(title="Party Lobby: Mafia", color=discord.Color.from_rgb(66, 244, 78),
        description='Currently there are {} people in the party.'.format(len(self.members)))
        embed.add_field(name="Members:", value='\n'.join(i.name for i in self.members)) 
        logs = await self.ctx.channel.history(limit=20).flatten()
        for msg in logs:
            if msg.author.name == "The Mafia":
                await msg.edit(embed=embed)
                break
        count = 1
        mgs = []
        log = await self.ctx.channel.history(limit=count).flatten()
        for x in log:
            mgs.append(x)
        await self.ctx.channel.delete_messages(mgs)
        await self.ctx.send(f"You have successfully left the party.")

    async def murder(self, ctx, user, target):
        # Making sure the global variables are able to be accessed and altered in the function. This was causing errors.
        killed = target
        if self.mafiavoteno != self.mafiano - self.mafiadead:
            # Checking whether the player being murder is both playing and alive.
            if self.playerNumRef[killed] in self.players and self.playerNumRef[killed] not in self.dead:
                # Checking whether the mafia has already accused another player.
                if user in self.mafiaaccusations:
                    # Subtracting a vote from the mafia's previous accusations.
                    self.mafiavote[self.mafiaaccusations[user]] -= 1
                # Changing the mafia's accusation in the mafiaaccusation dictionary.
                self.mafiaaccusations[user] = killed
                # Checking whether the accused has previously been accused.
                if killed in self.mafiavote:
                    # Adding a vote to the mafia's new accusation.
                    self.mafiavote[killed] += 1
                # Otherwise if they haven't already been accused.
                else:
                    # Set the new accusation's vote to 1.
                    self.mafiavote[killed] = 1
                # Checking whether there are now more accusers for the most recently accused person than the previously most accused.
                if self.mafiavote[killed] > self.mafiavoteno:
                    # Changing mafiavoteno to represent the greatest amount of votes for a player.
                    self.mafiavoteno = self.mafiavote[killed]
                    # Checking whether the amount of votes for the new user is made by all living mafia.
                    if self.mafiavoteno == self.mafiano - self.mafiadead:
                        # Setting the mafia's murder victim to mafiaresponse.
                        self.mafiaresponse = self.playerNumRef[killed]
                        # Checking whether the mafia are killing themselves.
                        if self.playerNumRef[killed].role == 'mafia':
                            # Roasting the mafia for killing themselves.
                            await ctx.send("Is that you, Hayton? Are you trying to break my game? Why would you do this??? Oh well. Goodbye.")
                        else:
                            # Outputting that the action was successful.
                            await ctx.send('It shall be done. By the morning, ' + self.playerNumRef[killed].name + ' shall cease to exist.')
                            # Below: explaining the success of the action and why it got up to the stage it did instead of killing someone.
                    else:
                        await ctx.send(user + ' wants to kill ' + self.playerNumRef[killed].name)
                else:
                    await ctx.send(user + ' wants to kill ' + self.playerNumRef[killed].name)
            else:
                await ctx.send("That user is already killed. Either that or they aren’t playing, but I’ll give your intelligence the benefit of the doubt.")
        else:
            await ctx.send("If we kill too many of them at once they will become suspicious...")
        await self.roundend()

    async def save(self, ctx, user, saved):
        if self.doctorresponse == '':
            # Checking whether the user being saved is both playing and alive.
            if self.playerNumRef[saved] in self.players and self.playerNumRef[saved] not in self.dead:
                # Setting the doctorresponse to the user being saved.
                self.doctorresponse = self.playerNumRef[saved]
                # Checking whether the doctor saved themselve.
                if self.playerNumRef[saved].name.lower() == user:
                    # Roasting the doctor for saving themself.
                    await ctx.send("Hey. Hey! I see you, you greedy thing. Someone's gonna die tonight, you know. Is all you can think about yourself? I am very unimpressed.")
                else:
                    # Outputting the success of the function.
                    await ctx.send(self.playerNumRef[saved].name + " is safe. For tonight at least...")
            # Below: Explaining why the function may not have worked.
            else:
                await ctx.send("You look around for " + self.playerNumRef[saved].name + " but you can’t find him. Because he’s not playing, or he’s dead. Try again.")
        else:
            await ctx.send("Don't be greedy")
        await self.roundend()

    async def detect(self, ctx, user, target):
        detected = target
        # Checking whether a game is in progress.
        if self.detectiveresponse == '':
            # Checking whether the person being detected is alive and playing.
            if self.playerNumRef[detected] in self.players and self.playerNumRef[detected] not in self.dead:
                # Checking whether the person being detected is a mafia or not.
                if self.playerNumRef[detected].role == 'mafia':
                    # Outputting the result.
                    await ctx.send("```css\nMafia beware... tonight, one of you is exposed...\n```")
                # Checking whether the detective is investigating themselves.
                elif self.playerNumRef[detected].name.lower() == user:
                    # Roasting the detective for investigating themself.
                    await ctx.send("Yeah, he's a mafia. The worst of the worst. (Hayton, is that you?)")
                else:
                    # Outputting that the user being detected is innocent.
                    await ctx.send("```diff\n- A wasted night. They're completely innocent.\n```")
                # Setting the detectiveresponse to the user detected.
                self.detectiveresponse = self.playerNumRef[detected]
                # Below: Explaining why the function was not successful.
            else:
                await ctx.send("No, " + self.playerNumRef[detected].name + " is not an alive Mafia. He is also either not playing, or dead. Try again.")
        else:
            await ctx.send("Don't be greedy...")
        await self.roundend()

    async def lynch(self, ctx, user, lynched):
        if self.playerNumRef[lynched] in self.players:
            # Checking whether the person being lynched is dead.
            if self.playerNumRef[lynched] not in self.dead:
                # Checking whether the lyncher has previously put in a vote for a separate user.
                if user in self.lynchvoter:
                    # Removing the lyncher's previous vote.
                    self.lynchvoted[self.playerNumRef[self.lynchvoter[user]]] -= 1
                # Resetting the lyncher's vote.
                self.lynchvoter[user] = lynched
                # Checking whether the person being lynched has been lynched by anyone else.
                if self.playerNumRef[lynched] in self.lynchvoted:
                    # Adding a vote to the total lynches against them.
                    self.lynchvoted[self.playerNumRef[lynched]] += 1
                    # Checking whether the majority of players now support the lynching.
                    if self.lynchvoted[self.playerNumRef[lynched]] > (len(self.players)-len(self.dead)) / 2:
                        # Appending the lynch victim to the dead.
                        self.dead.append(self.playerNumRef[lynched])
                        # Checking whether the killed user was a mafia.
                        if self.playerNumRef[lynched].role == 'mafia':
                            # Adding 1 to the count of dead mafia.
                            self.mafiadead += 1
                        # Initiating the night phase.
                        await ctx.send(f"```diff\n- {self.playerNumRef[lynched].name}, your fellow peers have decided. You are now dead, executed for your alleged crimes. Everyone go to sleep.\n```")
                        self.night = 'on'
                        # Resetting everybody's lynching votes.
                        self.lynchvoted = {}
                        self.lynchvoter = {}
                        ### Mute the Discord lynchinggrounds server.
                        common_channel = discord.utils.get(self.guild.channels, name="deliberation-room")
                        _playing = discord.utils.get(self.guild.roles, name="Players")
                        await common_channel.set_permissions(_playing, read_messages=True, send_messages=False)
                        mafia_channel = discord.utils.get(self.guild.channels, name="mafia")
                        for viewable in mafia_channel.members:
                            await mafia_channel.set_permissions(viewable, read_messages=True, send_messages=True)
                    # Otherwise if they are not killed.
                    else:
                        # Iterate through everyone who has been voted for lynching that round.
                        for i in self.lynchvoted:
                            # Await ctx.send the amount of votes everyone who has been voted for now has.
                            await ctx.send(i.name + " has " + str(self.lynchvoted[i]) + " votes.")
                        # Explain how many votes are required for someone to die.
                        await ctx.send("Minimum required votes is over " + str((len(self.players)-len(self.dead)) / 2))
                # Otherwise if the person being lynched has not been voted for before.
                else:
                    # Set their amount of votes to 1.
                    self.lynchvoted[self.playerNumRef[lynched]] = 1
                    # Iterate through everyone who has been voted for lynching that round.
                    for i in self.lynchvoted:
                        # Await ctx.send the amount of votes everyone who has been voted for now has.
                        await ctx.send(i.name + " has " + str(self.lynchvoted[i]) + " votes.")
                    # Explain how many votes are required for someone to die.
                    await ctx.send("Minimum required votes is over " + str((len(self.players)-len(self.dead)) / 2))
            # Below: Explain why the attempted lynching did not work.
            else:
                await ctx.send("Do not murder the dead, " + user.title() + ". Murder the living.")
        else:
            await ctx.send("This user is not recognised. Please unleash your violence on the existing.")
        await self.roundend()

    async def begin(self):
        tempList = []
        for mem in self.members:
            tempList.append(mem.name)
        await self.ctx.send(", ".join(tempList)+ ", you are now playing Mafia. Please check your individual chats with me. Now, go to sleep." )
        self.invite = await discord.utils.get(self.guild.channels, name="deliberation-room").create_invite(max_uses=len(self.members))
        for mem in self.members:
            await mem.send(self.invite)
        # The setting of the amount of mafia, doctors and civilians depending on the amount of players.
        if len(self.members) < 6:
            self.mafiano = 1
        elif len(self.members) < 10:
            self.mafiano = 2
        else:
            self.mafiano = 3
        self.detectiveno = 1
        self.doctorno = 1
        # Initialisation of the game.
        global game
        game = True
        length = len(self.members)
        check1 = 0
        randlist = []
        userNums = []
        """ The following uses a series of specific Discord functions.
        This involves the creation of specific chats with and between users,
        the muting of chats and the outputting to each user of their identity."""
        ###mute the main chat
        await asyncio.sleep(10)
        while len(self.guild.members) < len(self.players):
            if (len(self.guild.members) > len(self.players)+2 and len([i for i in self.players if i.name.lower() == 'supernovae']) == 0)  or (len(guild.members) > len(self.players)+1 and len([i for i in self.players if i.name.lower() == 'supernovae']) == 1):
                break
        await self.invite.delete()
        self.guildMembers = [i for i in self.guild.members if i.name != 'The Mafia']
        while check1 < length:
            iterationcheck = random.randint(0, (length-1))
            userNum = random.randint(1, 1000)
            if iterationcheck not in randlist and userNum not in userNums:
                if check1 < self.mafiano:
                    player = Player(self.guildMembers[iterationcheck], self.members[iterationcheck], userNum, "mafia")
                    self.players.append(player)
                    # Appending the user to the list of mafia.
                    # Adding one to the amount of users who have been allocated a role.
                    check1 += 1
                    # Appending the random number to randlist.
                    userNums.append(userNum)
                    randlist.append(iterationcheck)
                    self.mafia.append(player)
                    self.playerNumRef[userNum] = player
                # Checking whether all required mafia and doctors have been created.
                elif check1 < (self.mafiano + self.doctorno):
                    # Storing the role of the player as doctor in the roles dictionary.
                    player = Player(self.guildMembers[iterationcheck], self.members[iterationcheck], userNum, "doctor")
                    self.players.append(player)
                    # Adding one to the amount of users who have been allocated a role.
                    check1 += 1
                    # Appending the random number to randlist.
                    randlist.append(iterationcheck)
                    # Setting the variable doctor to the user.
                    self.doctor = player
                    self.playerNumRef[userNum] = player
                # Checking whether all required mafia, doctors and detectives have been created.
                elif check1 < (self.mafiano + self.doctorno + self.detectiveno):
                    # Storing the role of the player as detective in the roles dictionary.
                    player = Player(self.guildMembers[iterationcheck], self.members[iterationcheck], userNum, "detective")                    
                    # Adding one to the amount of users who have been allocated a role.
                    check1 += 1
                    # Appending the random number to randlist.
                    randlist.append(iterationcheck)
                    self.players.append(player)
                    # Setting the variable detective to the user.
                    self.detective = player
                    self.playerNumRef[userNum] = player
                # Checking whether all special roles have been allocated.
                else:
                    # Storing the role of the player as civilian in the roles dictionary.
                    player = Player(self.guildMembers[iterationcheck], self.members[iterationcheck], userNum, "civilian")     
                    # Adding one to the amount of users who have been allocated a role.
                    check1 += 1
                    # Appending the random number to randlist.
                    self.players.append(player)
                    randlist.append(iterationcheck)
                    self.civilians.append(player)
                    self.playerNumRef[userNum] = player
        _playing = discord.utils.get(self.guild.roles, name='Players')
        for mem in self.guild.members:
            await mem.add_roles(_playing)
        play_chat = discord.utils.get(self.guild.channels, name="deliberation-room")
        await play_chat.set_permissions(_playing, read_messages=True, send_messages=False)
        await self.introduction()
        while self.cooldownIN:
            pass
        # Output to the specific roles their identities and gameplay actions.
        for mafiapeeps in self.mafia:
            await mafiapeeps.sendRef.send(f"You are the mafia. Your player reference number is {mafiapeeps.refNum}.")
            mafia_channel = discord.utils.get(self.guild.channels, name="mafia")
            await mafia_channel.set_permissions(mafiapeeps.playerRef, read_messages=True, send_messages=True)
            self.told.append(mafiapeeps)
        await self.doctor.sendRef.send(f"You are the doctor. Your player reference number is {self.doctor.refNum}.")
        doctor_channel = discord.utils.get(self.guild.channels, name="doctor")
        await doctor_channel.set_permissions(self.doctor.playerRef, read_messages=True, send_messages=True)
        self.told.append(self.doctor)
        await self.detective.sendRef.send(f"You are the detective. Your player reference number is {self.detective.refNum}.")
        detective_channel = discord.utils.get(self.guild.channels, name="detective")
        await detective_channel.set_permissions(self.detective.playerRef, read_messages=True, send_messages=True)
        self.told.append(self.detectiveno)
        for civilian in self.civilians:
            await civilian.sendRef.send(f"You are a civilian. Your player reference number is {civilian.refNum}.")
        self.night = 'on'
        await play_chat.set_permissions(_playing, read_messages=True, send_messages=False)           
        # All lines below in the function explain why the begin function didn't work.
        await self.roundend()

    async def roundend(self):
        # Below: Checking whether the mafia, detective or doctor is dead.
        # Checking whether the mafia is dead.
        if self.mafiano - self.mafiadead == 0 and self.mafiano != 0:
            # Setting the mafiaresponse to an obscure status indicative variable.
            # This is done because mafiaresponse must be completed for the night phase to end.
            self.mafiaresponse = 'deadmafia'
        # Checking whether the doctor is dead.
        if self.doctor in self.dead:
            # Setting the doctorresponse to an obscure status indicative variable.
            # This is done because doctorresponse must be completed for the night phase to end.
            self.doctorresponse = 'deaddoctor'
        # Checking whether the detective is dead.
        if self.detective in self.dead:
            # Setting the detectiveresponse to an obscure status indicative variable.
            # This is done because detectiveresponse must be completed for the night phase to end.
            self.detectiveresponse = 'deaddetective'
        # Below: nightend phase.
        # Checking whether all special roles have completed their nightly duties.
        if self.mafiaresponse != '' and self.doctorresponse != '' and self.detectiveresponse != '':
            # Checking whether the doctor saved the same person the mafia killed.
            if self.mafiaresponse == self.doctorresponse:
                # Outputting what happened during the night.
                await discord.utils.get(self.guild.channels, name='deliberation-room').send(self.doctorresponse.name + ", you're a lucky person. You were killed, and saved, by the doctor. Day, commence.")
            # Checking whether the doctor did not save the murdered.
            else:
                # Checking whether the mafia are all dead or not.
                if self.mafiaresponse != 'deadmafia':
                    # Outputting the response from the mafia.
                    await self.deathline(self.mafiaresponse.name)
                    while self.cooldownIN:
                        pass
                    deadRole = discord.utils.get(self.guild.roles, name='Dead')
                    print(deadRole.id, deadRole.guild)
                    print(self.mafiaresponse.playerRef.guild)
                    await self.mafiaresponse.playerRef.add_roles(deadRole)
                    # Checking whether the dead person was a mafia member.
                    if self.mafiaresponse.role == 'mafia':
                        # Adding one to the count of dead mafia.
                        self.mafiadead += 1
                    # Appending the dead user to the list of dead.
                    self.dead.append(self.mafiaresponse)
            # Resetting all the variables specific to the nightphase.
            self.night = 'off'
            self.mafiaresponse = ''
            self.doctorresponse = ''
            self.detectiveresponse = ''
            self.mafiavoteno = 0
            self.mafiavote = {}
            self.mafiaaccusations = {}
            for deadpeeps in self.dead:
                _playing = discord.utils.get(self.guild.roles, name='Players')
                deadRole = discord.utils.get(self.guild.roles, name='Dead')
                await deadpeeps.playerRef.add_roles(deadRole)
                await deadpeeps.playerRef.remove_roles(_playing)
            common_channel = discord.utils.get(self.guild.channels, name="deliberation-room")
            _playing = discord.utils.get(self.guild.roles, name="Players")
            await common_channel.set_permissions(_playing, read_messages=True, send_messages=True)    
            # Muting night-specific chat spaces.
            mafia_channel = discord.utils.get(self.guild.channels, name="mafia")
            for viewable in mafia_channel.members:
                await mafia_channel.set_permissions(viewable, read_messages=True, send_messages=False)
            # Below: gameend phase.
        if game:
            # Checking whether there is only one player left and not all the mafia are dead.
            if len(self.players) - len(self.dead) == len(self.mafia) and self.mafiano - self.mafiadead > 0:
                # Printing that the mafia all win and who they all are.
                tempList = []
                for i in self.mafia:
                    tempList.append(i.name)
                await discord.utils.get(self.guild.channels, name='deliberation-room').send(f"```css\nMafia win! Congratulations {', '.join(tempList)}\n```")
                await self.endGame()
                return
            # Checking whether the only users still alive are a mafia and a doctor.
            elif len(self.players) - len(self.dead) == 2 and self.mafiano - self.mafiadead > 0 and self.doctor not in self.dead:
                # Outputting that there is a stalemate and explaining why.
                tempList = []
                for i in self.mafia:
                    tempList.append(i.name)
                await discord.utils.get(self.guild.channels, name='deliberation-room').send(f"```css\nThe only survivors are {self.doctor.name}, who can never die as the doctor, and a surviving mafia member! This means tha mafia win. The mafia were {', '.join(tempList)}\n```")
                await self.endGame()
                return
            # Checking whether the mafia are all dead.
            elif self.mafiano == self.mafiadead:
                # Outputting that the civilians win and who the mafia were.
                tempList = []
                for i in self.mafia:
                    tempList.append(i.name)
                await discord.utils.get(self.guild.channels, name='deliberation-room').send(f"```css\nCivilians win! Take that, {', '.join(tempList)}\n```")
                await self.endGame()
                return
                # Ending the game loop.
            # Below: ensuring that there is not a stalemate reached when only two people are left alive.
            if self.night == 'off' and len(self.players) - len(self.dead) == 2:
                await discord.utils.get(self.guild.channels, name='deliberation-room').send("```diff\n- The two surviving users fought long and hard to lynch one another, but seeing as neither gained the majority, they collapsed into a restless sleep.\n```")
                self.night = 'on'

    async def endGame(self):
        global game
        await asyncio.sleep(10)
        for mem in self.guild.members:
            try:
                if mem.id == bot.user.id:
                    continue
                await mem.kick()
                await mem.send("The game is over! See you next time!")
            except:
                pass
        global cooldowns
        game = False
        cooldowns = True
        for channel in self.guild.channels:
            try:
                async for msg in channel.history().flatten():
                    await msg.delete()
            except:
                pass
        parties.remove(parties[0])
        cooldowns = False

@bot.command(pass_context=True)
async def help(ctx):
    # Outputting possible functions for the user.
    messages = {
        "User commands:" : "- ~lynch {player} - Vote for a player to be lynched\n- ~view {player} - View the progress of the game\n- ~alive - Check who is alive\n- ~rules - Read the basic Mafia rules\n- ~viewID - Check every player's corresponding player ID.",
        "Mafia commands:" : "- ~murder {player} - Nominate a player to be killed",
        "Doctor commands:" : "- ~save {player} - Nominate a player to be saved",
        "Detective commands:" : "- ~detect {player} - Discover whether a player is mafia",
        "General commands:" : "- ~party - Create a new party if one doesn't already exist\n- ~join - Join an existing party\n- ~begin - Only the party owner can use this to begin a game of Mafia\n- ~disband - Disband the current party (only usable if party owner)\n- ~leave - Leave the current party."
    }
    embed = discord.Embed(title="Help Menu", color=discord.Color.from_rgb(100, 149, 237),
    description=f'These are the commands that this bot currently has:')
    for cmd in messages:
        embed.add_field(name=cmd, value=messages[cmd], inline=False)
    embed.set_footer(text="Bot Design by Omen#5109, modified/revamped with permission by SuperNovae#6180. Storylines created by Nodoby#5120 and implemented SuperNovae#6180")
    await ctx.send(embed=embed) 

@bot.command(pass_context = True)
async def alive(ctx):
    party = parties[0]
    listing = [i.name for i in party.players if i not in party.dead]
    await ctx.send(f"{', '.join(listing)} are still alive.")

@bot.command(pass_context = True)
async def rules(ctx):
    ruleMsgs = {
        "Aim of the Game:" : "The aim of Mafia differs depending on the player's role. If the player is a mafia, their goal is to kill all other non-mafia players through lynching and 'murdering' at night. Otherwise, players who are not mafia have the aim of killing all the mafia. When either party succeeds in their goal, they win.",
        "Roles:" : "**- Mafia:**\nThe mafia are a select few individuals in a game of Mafia whose aim is to kill all other players except for themselves. They can freely converse with each other and each night, are able to vote on one player to which they will kill.\n**- Doctor:**\n The doctor is an individual who is able to save someone from death every night. However, they cannot save someone from being lynched.\n**- Detective:**\n The detective is an individual who can investigate a player once a night to see if they are mafia or not.\n**- Civilian:**\n A civilian has no particular roles. Their aim is to kill all players who are mafia via lynching.\n**- Dead:**\n These are players who have been killed either by the mafia or via lynching. The can communicate among themselves but cannot interact with other, alive players.",
        "Rules:" : "There are two phases in Mafia. Day and Night. During night, players with special roles (doctor, detective, mafia) can use their special abilities in their role chats. During this time, the general chat will be muted. After all roles have done their special duties, the day phase will approach. During this time, all role chats will be muted and the general chat unmuted. Day phase is when everyone discusses who should be lynched and votes on a player to lynch. A majority vote is needed to lynch someone.\n\nIn order to make this game pleasurable and fair, please do not private message (pm/dm) anyone relating to game details during a game, share screenshots in the chats, cheat, deliberately try to break the bot or deliberately stall from doing your special duties (should you have one). Furthermore, if you are dead, please do not communicate with players who are alive.",
        "General Commands:" : ">nominateMurder\n>save\n>detect\n>nominate\nPlease use >help to see the specifications of each command."
    }
    embed = discord.Embed(title="Mafia Rules:", color=discord.Color.from_rgb(255, 0, 255),
    description='These are the rules for playing Mafia')
    for msg in ruleMsgs:
            embed.add_field(name=msg, value=ruleMsgs[msg])
    embed.set_footer(text="Good luck and have fun!") 
    await ctx.send(embed=embed)

@bot.command(pass_context = True)
async def begin(ctx):
    if game == True:
        return await ctx.send("There's a game on already, silly!")
    if len(parties[0].members) < 2:
        return await ctx.send("Not enough players.")
    if ctx.message.author.name.lower() != 'omen' and ctx.message.author.name.lower() != 'supernovae' and ctx.message.author != parties[0].owner:
        return await ctx.send("You != party owner. Be gone foul pretender!")
    await parties[0].begin()

@bot.command(pass_context = True)
async def party(ctx):
    user = ctx.message.author
    if len(parties) != 0:
        await ctx.send("Sorry, at the moment, only one party is supported at a time. Wait till they finish!")
        return
    elif game:
        await ctx.send("There's a game on, silly!")
    if cooldowns:
        await ctx.send("Sorry, I'm still cleaning up the mess you made in the deliberation room. You know, the blood, screaming and drama. Come back in fifteen seconds or so!")
        return
    party = Party(user, guild, ctx)
    parties.append(party)
    await party.createMessage()
    ###
    await party.roundend()

@bot.command(pass_context = True)
async def join(ctx):
    user = ctx.message.author
    if len(parties) == 0:
        await ctx.send("No parties exist yet. Go create one!")
        return
    party = parties[0]
    if user == party.owner:
        await ctx.send("You are the owner...")
        return
    elif user in party.members:
        await ctx.send("You're already in the party!")
        return
    elif game:
        await ctx.send("There's a game on, silly!")
    await party.addMember(user)
    ###
    await party.roundend()

@bot.command(pass_context = True)
async def viewParty(ctx):
    await parties[0].createMessage()

@bot.command(pass_context = True)
async def leave(ctx):
    user = ctx.message.author
    if len(parties) == 0:
        await ctx.send("No parties exist at the moment.")
        return
    if user == parties[0].owner:
        await ctx.send('You are the owner. PLEASE USE ~disband and try not to break me. I have feelings you know.')
        return
    elif user not in parties[0].members:
        await ctx.send("You're not even in a party!")
        return
    await parties[0].removeMember(user)

@bot.command(pass_context = True)
async def disband(ctx): 
    user = ctx.message.author
    if user != parties[0].owner:
        await ctx.send("This partyeth owner thou is not.")
        return
    parties.remove(parties[0])
    await ctx.send("Party has been disbanded!")

@bot.command(pass_context = True)
async def murder(ctx, target):
    user = ctx.message.author.name.lower()
    if game:
        # Checking whether the comment is outputted in the mafia chat.
        if str(ctx.channel) == "mafia":
            # Checking whether the night is in progress.
            if parties[0].night == 'on':
                await parties[0].murder(ctx, user, int(target))
            else:
                await ctx.send("Hush, or the civilians will hear you. Let us wait for the night.")
        else:
            await ctx.send("You're very bad at hiding your identity.")
    else:
        await ctx.send('Everyone, I’d be very scared of ' + user.title() + '… he’s trying to kill people before the game’s even started.')

@bot.command(pass_context = True)
async def save(ctx, saved):
    user = ctx.message.author.name.lower()
    # Checking whether a game is in progress.
    if game:
        # Checking whether the comment is outputted in the mafia chat.
        if str(ctx.channel) == "doctor":
            # Checking whether the night phase is in progress.
            if parties[0].night == 'on':
                await parties[0].save(ctx, user, int(saved))
            else:
                await ctx.send("For unknown reasons, you may not use this command until the night.")
        else:
            await ctx.send("You aren’t good at hiding your identity, are you?")
    else:
        await ctx.send("Your kindness is admired. Unfortunately, the game has not started.")

# A function allowing the Detective to detect a user.
@bot.command(pass_context = True)
async def detect(ctx, target):
    user = ctx.message.author.name.lower()
    if game:
        # Checking whether the comment is outputted in the detective chat.
        if str(ctx.channel) == "detective":
            # Checking whether the night is in progress.
            if parties[0].night == 'on':
                await parties[0].detect(ctx, user, int(target))
            else:
                await ctx.send("Careful, " + user.title() + "! Be private in your suspicions and wait until the night.")
        else:
            await ctx.send("Please do not detect people in this channel.")
    else:
        await ctx.send("Patience is a virtue, and one you don’t have.")

# A function allowing users to lynch other users (during the day).
@bot.command(pass_context = True)
async def lynch(ctx, lynched):
    user = ctx.message.author.name.lower()
    # Checking whether a game is in progress.
    if game:
        # Checking whether the command is outputted in the main chat.
        if str(ctx.channel) == "deliberation-room":
            if parties[0].night == 'off':
                await parties[0].lynch(ctx, user, int(lynched))
            else:
                await ctx.send("You’re impatient to kill people, aren’t you?")
        else:
            await ctx.send("You’re impatient to kill people, aren’t you?")
    else:
        await ctx.send(f"I'm really scared of {user.title()}, they're already trying to kill people!")

@bot.command(pass_context = True)
async def viewID(ctx):
    embed = discord.Embed(title="User IDs", color=discord.Color.from_rgb(100, 149, 237),
    description=f'These are the number IDs corresponding to each user:')
    random.shuffle(parties[0].players)
    for i in parties[0].players:
        embed.add_field(name=i.name, value=f"Their id is {i.refNum}.", inline=False)
    await ctx.send(embed=embed) 

@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("----------")
    status = discord.Activity(name='Type ~help for commands.', type=discord.ActivityType.playing)
    await bot.change_presence(status=type, activity=status)
    global guild
    for i in bot.guilds:
        if i.name == "Mafia Playground":
            guild = i
            break


bot.run(TOKEN)