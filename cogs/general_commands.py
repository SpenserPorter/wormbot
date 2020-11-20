import discord
import lotto_dao as db
import asyncio
import re
from discord.ext import commands

def get_cock_power(cock_status):
    return (50 + cock_status) / 100

def build_embed(embed_input_dict):

    embed = discord.Embed(title=None,
                      description=None,
                      colour=embed_input_dict['colour'])

    embed.set_author(name=embed_input_dict['author_name'])

    for key, field in embed_input_dict['fields'].items():
        embed.add_field(name=field['name'], value=field['value'])
    return embed

class GeneralCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=["lb"])
    async def leaderboard(self,ctx):
        '''Displays worm balance leaderboard'''

        user_list = db.get_user()
        balances = []

        for user_id in user_list:
            user = await self.bot.fetch_user(user_id[0])

            if not user.bot:
                balance = db.get_user_balance(user.id)
                cock_status = db.get_cock_status(user.id)
                balances.append((user.name, cock_status, balance))

        sorted_balances = sorted(balances, key=lambda balances: balances[2], reverse=True)
        rank = 1
        output = []

        for user_name, cock_status, user_balance in sorted_balances:
            cock_power = "{:.1f}% <:Worm:752975370231218178>".format((get_cock_power(cock_status) * 100)) if cock_status is not -1 else ":x:"
            output.append("{}: **{}** - {:,} - {}".format(rank, user_name, round(user_balance), cock_power))
            rank += 1

        embed_dict = {'colour':discord.Colour(0x034cc1), 'author_name':"Worm Hall of Fame",
                    'fields': {1:{'name': "Leaderboard", 'value': "\n".join(output[0:10])}}}

        await ctx.send(embed = build_embed(embed_dict))

    @commands.group(invoke_without_command=True, hidden=True)
    async def worms_please(self, ctx, amount: int):
        '''Adds worms to all non bot users balances'''

        if ctx.author.id != 154415714411741185: #My user.id
            await ctx.send("You're not my real dad!")
            return

        user_id_list = db.get_user() #Returns a list of all users

        for user_id in user_id_list:
            user = await self.bot.fetch_user(user_id[0])
            if not user.bot:
                new_balance = db.modify_user_balance(user_id[0], amount)
                await ctx.send('Added {:,} worms to {}\'s account. New balance is {:,}'.format(amount, user.name, new_balance))

    @commands.group(invoke_without_command=True, aliases=["bal","balance","worm"])
    async def worms(self,ctx):
        '''Shows your worm balance and number of tickets in next lottery'''

        balance = db.get_user_balance(ctx.author.id)
        lottory_id = db.get_current_lottory()
        ticket_list = db.get_user_tickets(ctx.author.id,lottory_id)
        await ctx.send("{} has {:,} worms and {} tickets for the next lottery".format(ctx.author.name, round(balance,2), len(ticket_list)))

def setup(bot):
    bot.add_cog(GeneralCommands(bot))
