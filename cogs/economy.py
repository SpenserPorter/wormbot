import discord
import lotto_dao as db
import asyncio
import re
import ast
import random
from discord.ext import commands

thumb_gif_list = ast.literal_eval(db.get_config("thumb_gifs"))
love_gif_list = ast.literal_eval(db.get_config("love_gifs"))

def build_embed(embed_input_dict):

    embed = discord.Embed(title=None,
                      description=None,
                      colour=embed_input_dict['colour'])

    embed.set_author(name=embed_input_dict['author_name'])

    for key, field in embed_input_dict['fields'].items():
        embed.add_field(name=field['name'], value=field['value'])
    return embed

class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        "Does your daily check in - works every 24 hours"
        db.modify_user_balance(ctx.author.id, int(db.get_config("daily_worms")))
        await ctx.send(thumb_gif_list[random.randint(0, len(thumb_gif_list) - 1)])
        await ctx.send("You collected {} worms for today :D".format(db.get_config("daily_worms")))


    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            msg = 'You already did your check in, please try again in %s Hours and %s Minute'%(error.retry_after//3600, error.retry_after % 3600 //60)
            await ctx.send(msg)
        else:
            raise error

    @commands.group(invoke_without_command=True)
    async def steal(self,ctx):
        await ctx.send("You haven't learned that skill yet!")

    @commands.group(invoke_without_command=True)
    async def give(self,ctx,who,value):
        "Share some love by giving it to others <3"
        message = ctx.message
        their_id = message.mentions[0].id
        value = int(value)
        if ctx.author.id == message.mentions[0].id:
            await ctx.send("You cant send worms to yourself dummy")
            return
        else:
            balance = db.get_user_balance(message.author.id)
            if int(value) < 10:
                await ctx.send("You need to transfer a minimum of 10 worms.")
                return
            elif balance < value:
                await ctx.send("You dont have {} worms, you only have {} worms").format(value, balance)
                return  # not enough money
            else:
                #give_gif
                db.modify_user_balance(ctx.author.id, value * -1)
                db.modify_user_balance(their_id, value)
                await ctx.send(love_gif_list[random.randint(0, len(love_gif_list) - 1)])
                await ctx.send("{} has sent {} worms to {}".format(message.author.mention, value, message.mentions[0].mention))
                return

def setup(bot):
    bot.add_cog(Economy(bot))
