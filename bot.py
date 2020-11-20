import asyncio
import datetime
import logging
from pathlib import Path
import os
import ast
import discord
import lotto_dao as db
from discord.ext import commands

worm_emojis_list = db.get_config("worm_emojis_list")
worm_emoji_amount = int(db.get_config("worm_emoji_amount"))
worm_roles_dict = ast.literal_eval(db.get_config("worm_roles_dict"))
guild_id = int(db.get_config("guild_id"))
worm_god_id = int(db.get_config("worm_god_id"))
default_channel = int(db.get_config("default_channel"))

#worm_roles_dict={0:"Dead Worm (0 Worms)", 500: "Flat Worm (1-500) Worms", 1000: "Silly Worm™ (501-1000)", 2000:"Magic Wigglee™ (1001-2000)", 3000: "Wiggle Worm™ (2001-3000) Worms",4000:"Wacky Worm™ (3001-4000) Worms", 5000:"Tricky Worm™ (4001-5000)",9999999999999:"Magic Worm™ (5000+)"}
#################{0:"Dead Worm (0 Worms)", 500: "Flat Worm (1-500) Worms", 1000: "Silly Worm™ (501-1000)", 2000:"Magic Wigglee™ (1001-2000)", 3000: "Wiggle Worm™ (2001-3000) Worms",4000:"Wacky Worm™ (3001-4000) Worms", 5000:"Tricky Worm™ (4001-5000)",99999999999999:"Magic Worm™ (5000+)"}
#worm_roles_dict={0:"test1",100:"test2","max":"god"}


async def run():
    """
    Where the bot gets started. If you wanted to create an database connection pool or other session for the bot to use,
    it's recommended that you create it here and pass it to the bot as a kwarg.
    """
    bot = Bot(description='Get ya worms here!')
    token = os.getenv('WORM_BOT_TOKEN')
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        await bot.logout()

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix_,
            description=kwargs.pop('description')
        )
        self.start_time = None
        self.app_info = None

        self.loop.create_task(self.track_start())
        self.loop.create_task(self.load_all_extensions())

    async def track_start(self):
        """
        Waits for the bot to connect to discord and then records the time.
        Can be used to work out uptime.
        """
        await self.wait_until_ready()
        self.start_time = datetime.datetime.utcnow()

    async def get_prefix_(self, bot, message):
        """
        A coroutine that returns a prefix.

        I have made this a coroutine just to show that it can be done. If you needed async logic in here it can be done.
        A good example of async logic would be retrieving a prefix from a database.
        """
        prefix = ['!']
        return commands.when_mentioned_or(*prefix)(bot, message)

    async def load_all_extensions(self):
        """
        Attempts to load all .py files in /cogs/ as cog extensions
        """
        await self.wait_until_ready()
        await asyncio.sleep(1)  # ensure that on_ready has completed and finished printing
        cogs = [x.stem for x in Path('cogs').glob('*.py')]
        for extension in cogs:
            try:
                self.load_extension(f'cogs.{extension}')
                print(f'loaded {extension}')
            except Exception as e:
                error = f'{extension}\n {type(e).__name__} : {e}'
                print(f'failed to load extension {error}')
            print('-' * 10)
        self.loop.create_task(self.add_all_users())
        self.loop.create_task(self.update_worm_roles())

    async def on_ready(self):
        """
        This event is called every time the bot connects or resumes connection.
        """
        print('-' * 10)
        self.app_info = await self.application_info()
        print(f'Logged in as: {self.user.name}\n'
              f'Using discord.py version: {discord.__version__}\n'
              f'Owner: {self.app_info.owner}\n'
              f'Template Maker: SourSpoon / Spoon#7805')
        print('-' * 10)

    async def add_all_users(self):
        '''Dev function, runs DB migrations and adds all users to DB'''
        db.initialize_tables()
        for user in self.users:
            db.add_user(user.id)

    async def update_worm_roles(self):
        await asyncio.sleep(15)
        guild = self.get_guild(guild_id)
        role_object_dict={}
        worm_god = {"user": None, "score": 0}
        for key, role_name in worm_roles_dict.items():
            role_object = discord.utils.get(guild.roles, name=role_name)
            role_object_dict[key] = role_object
        while True:
            user_list = db.get_user()
            balances = []
            update_god = False
            users = db.get_user()

            for user_id_tuple in user_list:
                user_id = user_id_tuple[0]
                balance = db.get_user_balance(user_id)
                balances.append((user_id,balance))
                options=[]
                for threshold in role_object_dict:
                    if balance <= threshold:
                        options.append(threshold)
                min_threshold = min(options)
                role_to_assign = role_object_dict[min_threshold]
                member = guild.get_member(user_id)
                current_roles = member.roles
                if role_to_assign not in member.roles:
                    for role in current_roles:
                        if role in role_object_dict.values():
                            await member.remove_roles(role)
                            print("Removing {} from {}".format(role, member.name))
                    print("Assigning {} to {}".format(role_to_assign, member.name))
                    await member.add_roles(role_to_assign)

            god_role_object = discord.utils.get(guild.roles, id=worm_god_id)
            sorted_balances = sorted(balances, key=lambda balances: balances[1], reverse=True)
            new_worm_god_user_id = sorted_balances[0][0]
            new_worm_god_balance = sorted_balances[0][1]

            if new_worm_god_balance != worm_god["score"]:
                worm_god["score"] = new_worm_god_balance
                new_role_name = "Worm God ({} Worms)".format(worm_god["score"])
                await god_role_object.edit(name=new_role_name)

            if new_worm_god_user_id != worm_god["user"]:
                worm_god["user"] = new_worm_god_user_id
                current_god = god_role_object.members
                new_god = guild.get_member(worm_god["user"])
                if current_god is not None:
                    for god in current_god:
                        if god.id != worm_god["user"]:
                            await god.remove_roles(god_role_object)
                            message = "{} has been dethroned, All hail the new Worm God {} with {} worms!".format(god.mention, new_god.mention, worm_god["score"])
                            channel = guild.get_channel(default_channel)
                            await channel.send(message)
                await new_god.add_roles(god_role_object)


            await asyncio.sleep(60)

    async def on_member_join(self, member):
        db.add_user(member.id)
        channel = await member.create_dm()
        await channel.send('Hi {}, welcome to the server! Type !help to see a list of all commands.'.format(member.name))

    async def on_raw_reaction_add(self, payload):
        key = await self.http.get_message(payload.channel_id, payload.message_id)
        if (payload.emoji.name in worm_emojis_list):  # and payload.user_id != int(key["author"]["id"]) and 749486563691593740 != int(key["author"]["id"]):
            db.modify_user_balance(payload.user_id, worm_emoji_amount)

    async def on_raw_reaction_remove(self, payload):
        key = await self.http.get_message(payload.channel_id, payload.message_id)
        if (payload.emoji.name in worm_emojis_list) and payload.user_id != int(key["author"]["id"]):
            db.modify_user_balance(payload.user_id, worm_emoji_amount * -1)

    async def on_message_edit(self, before, after):
        '''Prevent rigged accusations with extreme predjustice'''
        if after.author.bot:
           return
        after_lw = after.content.lower()
        before_lw = before.content.lower()
        if after_lw.find("rigged") != -1 and before_lw.find("rigged") == -1:
           channel = after.channel
           await channel.send("I see what you did {}, it's not rigged!".format(after.author.nick))

    async def on_message(self, message):
        '''Prevent rigged accusations with extreme predjustice'''
        channel = message.channel
        print(message.author, message.author.id, message.content)
        if message.author.bot:
            return
        check_rigged = message.content.lower()
        if check_rigged.find("rigged") != -1:
            await channel.send("NANI???")
        await self.process_commands(message)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
