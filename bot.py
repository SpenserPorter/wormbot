import asyncio
import datetime
import logging
from pathlib import Path
import os
import ast
import discord
import lotto_dao as db
from discord.ext import commands

worms = db.get_config("worm_emojis_list")
worm_emoji_amount = int(db.get_config("worm_emoji_amount"))
worm_roles_dict = ast.literal_eval(db.get_config("worm_roles_dict"))

#worm_roles_dict={0:"Dead Worm (0 Worms)", 500: "Flat Worm (1-500) Worms", 1000: "Silly Worm™ (501-1000)", 2000:"Magic Wigglee™ (1001-2000)", 3000: "Wiggle Worm™ (2001-3000) Worms",4000:"Wacky Worm™ (3001-4000) Worms", 5000:"Tricky Worm™ (4001-5000)",9999999999999:"Magic Worm™ (5000+)"}
#worm_roles_dict={0:"test1",100:"test2",999999999999999:"test3"}

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
        while True:
            user_list = db.get_user()
            balances = []
            for user_id in user_list:
                user = await self.fetch_user(user_id[0])

                if not user.bot:
                    balance = db.get_user_balance(user.id)
                    options=[]
                    for key in worm_roles_dict:
                        if balance < key:
                            options.append(key)
                    min_key = min(options)
                    role_name = worm_roles_dict[min_key]
                    guild = self.get_guild(459332259321741323)
                    member = guild.get_member(user.id)
                    current_roles = member.roles
                    role_to_assign = discord.utils.get(member.guild.roles, name=role_name)
                    if role_to_assign not in member.roles:
                        for role in current_roles:
                            if role.name in worm_roles_dict.values():
                                await member.remove_roles(role)
                                print("Removing {} from {}".format(role.name, member.name))
                        print("Assigning {} to {}".format(role_to_assign.name, user.name))
                        await member.add_roles(role_to_assign)

            await asyncio.sleep(10)

    async def on_member_join(self, member):
        db.add_user(member.id)
        channel = await member.create_dm()
        await channel.send('Hi {}, welcome to the server! Type !help to see a list of all commands.'.format(member.name))

    async def on_raw_reaction_add(self, payload):
        key = await self.http.get_message(payload.channel_id, payload.message_id)
        if (payload.emoji.name in worms):  # and payload.user_id != int(key["author"]["id"]) and 749486563691593740 != int(key["author"]["id"]):
            db.modify_user_balance(payload.user_id, worm_emoji_amount)

    async def on_raw_reaction_remove(self, payload):
        key = await self.http.get_message(payload.channel_id, payload.message_id)
        if (payload.emoji.name in worms) and payload.user_id != int(key["author"]["id"]):
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
