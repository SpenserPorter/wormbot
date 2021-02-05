import discord
import lotto_dao as db
import asyncio
import re
import ast
import random
import math
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
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def steal(self, ctx, target, amount: int):
        '''Try to steal worms from another user,
            but be careful it may backfire! The more worms
            you attempt to steal, the less likely it is to succeed'''
        try:
            target = ctx.message.mentions[0]
        except:
            await ctx.send("No valid user found!")
            await ctx.command.reset_cooldown(ctx)
            return
        target_balance = db.get_user_balance(target.id)
        user_balance = db.get_user_balance(ctx.author.id)
        if amount < 10:
            await ctx.send("You have to steal at least 10 worms!")
            await ctx.command.reset_cooldown(ctx)
            return
        if target_balance < 100:
            await ctx.send("{} is too poor to steal from, find another target!".format(target.mention))
            await ctx.command.reset_cooldown(ctx)
            return
        if amount > target_balance:
            await ctx.send("{} only has {} worms, so I guess you're trying to steal all of them".format(target.mention, target_balance))
            amount = target_balance

        base_difficulty = 10
        ratio = round(amount / target_balance, 2)
        total_difficulty = math.ceil(base_difficulty + (10 * ratio))
        result = random.randint(1,20)
        await ctx.send("Attempting to steal {}% of {} worms, you'll need to roll {} or better!".format(ratio * 100, target.mention, total_difficulty))
        gif_message = await ctx.send('https://tenor.com/ba6fL.gif')
        await asyncio.sleep(5)
        if result >= total_difficulty:
            db.modify_user_balance(target.id, -1 * amount)
            db.modify_user_balance(ctx.author.id, amount)
            await ctx.send("{} rolled a {} and successfully stole {} worms from {}".format(ctx.author.mention, result, amount, target.mention))
            await gif_message.edit(content="https://tenor.com/bmxN5.gif")
            ctx.command.reset_cooldown(ctx)
        elif 1 < result < 6:
            backfire_percent = random.uniform(.1,.5)
            backfire_amount = round(user_balance * backfire_percent)
            await ctx.send("{} rolled a {}, got caught by the police and were forced to pay {} {} worms instead".format(ctx.author.mention, result, target.mention, backfire_amount))
            db.modify_user_balance(target.id, backfire_amount)
            db.modify_user_balance(ctx.author.id, -1 * backfire_amount)
            await gif_message.edit(content="https://tenor.com/bia0L.gif")
        elif result == 1:
            await ctx.send("{} rolled a {}, now all their worms are belong to {}".format(ctx.author.mention, result, target.mention))
            db.modify_user_balance(ctx.author.id, -1 * user_balance)
            db.modify_user_balance(target.id, user_balance)
            await gif_message.edit(content="https://tenor.com/btHVc.gif")
        else:
            await ctx.send("{} rolled a {}, nothing happened!".format(ctx.author.mention, result))
            await gif_message.edit(content="https://tenor.com/6ziX.gif")

    @steal.error
    async def steal_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            msg = "You need to wait at least {} hours and {} minutes since your last failed steal to try again!".format(error.retry_after//3600, error.retry_after % 3600 //60)
            await ctx.send(msg)
        else:
            raise error

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
