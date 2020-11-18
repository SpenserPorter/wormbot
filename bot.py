import asyncio
import datetime
import logging
from pathlib import Path
import os
import discord
import lotto_dao as db
from discord.ext import commands

client = discord.Client()

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

    @client.event
    async def on_member_join(member):
        db.add_user(member.id)
        await member.dm_channel.send(
            f'Hi {member.name}, welcome to the server! Type !help to see a list of all commands.'
        )

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
            await channel.send("It's not rigged")
        await self.process_commands(message)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
