import discord
import random
import lotto_dao as db
import asyncio
import fuzzywuzzy.process as fwp
from discord.ext import commands

time_to_accept_battle = 60
time_to_battle = 60

def convert_username(ctx, user_name):
    server = ctx.message.guild
    user = server.get_member_named(user_name)
    return user

def match_string_to_user(bot, ctx, string_to_match):
    member_list = bot.get_all_members()
    user_name, matching = fwp.extractOne(string_to_match, [(i.nick if i.nick else i.name) for i in member_list])
    if matching >= 50:
        user = convert_username(ctx, user_name)
        return user
    else:
        raise ValueError("No user found matching {}".format(string_to_match))

def get_cock_power(cock_status):
    return (50 + cock_status) / 100

def build_embed(embed_input_dict):

    embed = discord.Embed(title=None,
                      description=None,
                      colour=embed_input_dict['colour'])

    embed.set_author(name=embed_input_dict['author_name'])

    for key, field in embed_input_dict['fields'].items():
        embed.add_field(name=field['name'], value=field['value'], inline=field['inline'] if 'inline' in field else False)
    return embed

class CockBattle():

    def __init__(self, bot, ctx, challenger, challenged, purse):
        self.bot = bot
        self.ctx = ctx
        self.purse = purse
        self.wagers = {challenger: {}, challenged: {}}
        self.challenger = challenger
        self.challenger_cock_status = db.get_cock_status(challenger.id)
        self.challenged = challenged
        self.challenged_cock_status = db.get_cock_status(challenged.id)
        self.accepted = False
        self.odds = self.get_odds_for_challenger()

    def add_wager(self, user, bet_on, amount):
        if user in self.wagers[bet_on]:
            self.wagers[bet_on][user] += amount
        else:
            self.wagers[bet_on][user] = amount

    def resolve_battle(self):
        round = 0
        challenger = False
        challenged = False
        while challenger == challenged:
            challenger_result = random.random()
            challenged_result = random.random()
            challenger = challenger_result < get_cock_power(self.challenger_cock_status)
            challenged = challenged_result < get_cock_power(self.challenged_cock_status)
            round += 1
        if challenger:
            return round, self.challenger, self.challenged
        else:
            return round, self.challenged, self.challenger

    def get_odds_for_challenger(self):
        challenger_power = get_cock_power(self.challenger_cock_status)
        challenged_power = get_cock_power(self.challenged_cock_status)
        odds = (challenger_power * (1 - challenged_power)) / (challenged_power * (1 - challenger_power))
        return odds

class WormFight(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.cock_price = int(db.get_config("cock_price"))
        self.cock_battle = None

    @commands.group(invoke_without_command=True, aliases=["wf"])
    async def wormfight(self, ctx, amount:int):
        '''Test your worm in a fight to the death,
         each win increases your worms toughness and odds of winning!
         Buy a fightworm with !bw and then bet on the outcome of a fight
         with !wf <amount>'''

        user_id = ctx.author.id
        balance = db.get_user_balance(user_id)
        cock_status = db.get_cock_status(user_id)
        if self.cock_battle:
            if ctx.author == self.cock_battle.challenger or ctx.author == self.cock_battle.challenged:
                await ctx.send("You cannot participate in wormfights while your worm is preparing for battle")
                return

        if cock_status == -1:
            await ctx.send("Your worm is not ready for battle, prepare your worm with !prepare_worm first.")
            return

        if amount > balance:
            await ctx.send("That would cost {}, you only have {} :(".format(amount, balance))
            return

        else:
            new_balance = db.modify_user_balance(user_id, -1 * amount)
            result = random.random()
            cock_power = get_cock_power(cock_status)

            if result < cock_power:
                amount_won = amount * 2
                new_cock_status = cock_status + 1
                new_balance = db.modify_user_balance(user_id, amount_won)
                db.set_cock_status(user_id, new_cock_status)
                result_msg = "Your worm made you {:,} worms richer".format(amount)
                hardness_msg= "Now at {:.1f}% toughness".format(get_cock_power(new_cock_status) * 100)
                embed_dict = {'colour':discord.Colour(0x00e553), 'author_name':ctx.author.name,
                            'fields': {1:{'name': result_msg, 'value': hardness_msg}}}

                await ctx.send(embed=build_embed(embed_dict))
            else:
                db.set_cock_status(user_id, -1)
                result_msg = "Your worm got smoosh :("
                embed_dict = {'colour':discord.Colour(0xe10531), 'author_name':ctx.author.name,
                            'fields': {1:{'name': 'Ouch', 'value': result_msg}}}

                await ctx.send(embed=build_embed(embed_dict))

    @commands.group(invoke_without_commands=True, aliases=["cb"])
    async def wormbattle(self, ctx, user, purse=0):
        '''Challenge another users worm to a battle to the death, anyone can bet on the outcome'''

        if purse > db.get_user_balance(ctx.author.id):
            ctx.send("You don't have {} worms!".format(purse))

        if self.cock_battle is not None:
            await ctx.send("Only one worm battle at a time, wait for {} and {} to finish their battle!".format(self.cock_battle.challenger.name, self.cock_battle.challenged.name))
            return

        if db.get_cock_status(ctx.author.id) == -1:
            await ctx.send("You don't have a battleworm")
            return

        try:
            challenged_user = ctx.message.mentions[0]
        except:
            await ctx.send("You need to mention a user to challenge them!")

        if db.get_cock_status(challenged_user.id) == -1:
            await ctx.send("{} doesn't have a battleworm!".format(challenged_user.name))
            return

        if challenged_user == ctx.author:
            await ctx.send("Try punching yourself in the face instead?")
            return

        self.cock_battle = CockBattle(self.bot, ctx, ctx.author, challenged_user, purse=purse)

        embed_dict = {'colour':discord.Colour(0xffa500), 'author_name':"Worm Battle Challenge!",
                      'fields': {1:{'name': self.cock_battle.challenger.name, 'value': "{:.1f}% <:Worm:779117240087609404> @{:.2f}:1 odds".format(get_cock_power(self.cock_battle.challenger_cock_status)*100, 1/self.cock_battle.odds), 'inline': True},
                                 2:{'name': "VS", 'value': '-', 'inline': True},
                                 3:{'name': self.cock_battle.challenged.name, 'value': "{:.1f}% <:Worm:779117240087609404> @{:.2f}:1 odds".format(get_cock_power(self.cock_battle.challenged_cock_status)*100, self.cock_battle.odds), 'inline': True},
                                 4:{'name': "```{} has 60s to accept the challenge!```".format(self.cock_battle.challenged.name), 'value': 'Use <$challenge_accepted> to accept!', 'inline': False}
                                 }
                      }

        battle_message = await ctx.send(embed = build_embed(embed_dict))

        wait_cycles = 0
        while self.cock_battle.accepted == False and wait_cycles < 60:
            await asyncio.sleep(time_to_accept_battle//60)
            wait_cycles += 1
            if wait_cycles in [50, 30, 15]:
                embed_dict['fields'][4] = {'name': "```{} has {}s to accept the challenge!```".format(self.cock_battle.challenged.name, (time_to_accept_battle/60) * (60 - wait_cycles)), 'value': 'Use <$challenge_accepted> to accept!', 'inline': False}
                await battle_message.edit(embed=build_embed(embed_dict))

        if self.cock_battle.accepted:
            embed_dict['colour'] = discord.Colour(0x00e553)
            embed_dict['author_name'] = "Worm Battle Accepted!"
            embed_dict['fields'][4] = {'name': "```60s until the battle!```", 'value': 'Type !bb <amount> <user> to place your bets!', 'inline': False}
            await battle_message.edit(embed=build_embed(embed_dict))
            wait_cycles = 0
            while wait_cycles < 12:
                await asyncio.sleep(time_to_battle//12)
                wait_cycles += 1
                if wait_cycles in [10, 6, 3]:
                    embed_dict['fields'][4] = {'name': "```{}s until the battle!```".format((time_to_battle/12) * (12 - wait_cycles)), 'value': 'Type !bb <amount> <user> to place your bets!', 'inline': False}
                    await battle_message.edit(embed=build_embed(embed_dict))

            embed_dict['author_name'] = "Battle Results Below!"
            embed_dict['colour'] = discord.Colour(0xd3d3d3)
            embed_dict['fields'][4] = {'name': "```Battle!```", 'value': 'Results below!', 'inline': False}

            await battle_message.edit(embed=build_embed(embed_dict))

            rounds, winner, loser = self.cock_battle.resolve_battle()
            db.modify_user_balance(winner.id, self.cock_battle.purse)
            db.set_cock_status(loser.id, -1)

            if loser == self.cock_battle.challenger:
                donated_cock_power = ((self.cock_battle.challenger_cock_status) / 2) + 1
                embed_dict['fields'][3]['name'] = "{}:white_check_mark:".format(self.cock_battle.challenged.name)
                db.set_cock_status(winner.id, self.cock_battle.challenged_cock_status + donated_cock_power)
            else:
                donated_cock_power = ((self.cock_battle.challenged_cock_status) / 2) + 1
                embed_dict['fields'][1]['name'] = "{}:white_check_mark:".format(self.cock_battle.challenger.name)
                db.set_cock_status(winner.id, self.cock_battle.challenger_cock_status + donated_cock_power)

            results = []
            for user, amount_won in self.cock_battle.wagers[winner].items():
                new_user_balance = db.modify_user_balance(user.id, amount_won)
                results.append("{} won {:,} worms, new balance is {:,}".format(user, round(amount_won,2), round(new_user_balance,2)))

            embed_dict['author_name'] = "{}s battleworm won the battle!".format(winner.name)
            embed_dict['colour'] = discord.Colour(0x0077be)
            embed_dict['fields'][4] = {'name': "{} battleworm was victorious in round {} and wins {} from the purse!".format(winner.name, rounds, self.cock_battle.purse), 'value': "{}\% is added to his battleworms toughness".format(donated_cock_power), 'inline': False}

            await ctx.send(embed=build_embed(embed_dict))
            self.cock_battle = None
            await ctx.send("\n".join(results))

        else:
            embed_dict['author_name'] = "Worm Battle Aborted!"
            embed_dict['colour'] = discord.Colour(0xe10531)
            embed_dict['fields'][4] = {'name': "```{} did not accept, the battle is cancelled!```".format(self.cock_battle.challenged.name), 'value': 'Challenge someone awake next time!', 'inline': False}
            await battle_message.edit(embed=build_embed(embed_dict))
            self.cock_battle = None

    @commands.group(aliases=["ca"])
    async def challenge_accepted(self, ctx):
        '''Accept a wormbattle challenge'''
        if self.cock_battle is not None:
            if ctx.author == self.cock_battle.challenged:
                if self.cock_battle.accepted == True:
                    await ctx.send("The battle has already been accepted")
                else:
                    self.cock_battle.accepted = True
            else:
                await ctx.send("Only {} can accept the challenge".format(self.cock_battle.challenged.name))

    @commands.group(aliases=["bb"])
    async def battlebet(self, ctx, amount: int, user):
        '''Bet on the current wormbattle, !battlebet <amount> <user>'''

        if self.cock_battle is None:
            await ctx.send("There is no active worm battle")
            return
        if not self.cock_battle.accepted:
            await ctx.send("The battle has not been accepted by {} yet".format(self.cock_battle.challenged.name))
            return
        try:
            player_to_bet_on = ctx.message.mentions[0]
        except:
            try:
                player_to_bet_on = match_string_to_user(self.bot, ctx, user)
            except:
                await ctx.send("No user found matching {}".format(user_string))
                return
        if player_to_bet_on in [self.cock_battle.challenger, self.cock_battle.challenged]:
            user_id = ctx.author.id
            balance = db.get_user_balance(user_id)
            if amount > balance:
                await ctx.send("That would cost {}, you only have {} you chode".format(amount, balance))
                return
            else:
                new_balance = db.modify_user_balance(user_id, -1 * amount)
                if player_to_bet_on == self.cock_battle.challenger:
                    odds = 1/self.cock_battle.odds
                else:
                    odds = self.cock_battle.odds
                amount_to_win = (amount * odds) + amount
                self.cock_battle.add_wager(ctx.author, player_to_bet_on, amount_to_win)
                await ctx.send("{} bet {:,} to win {:,} on {}s battle worm, good luck!".format(ctx.author.name,
                amount, round(amount_to_win,2), player_to_bet_on))
        else:
            await ctx.send("{} is not participating in the current battle you mook".format(player_to_bet_on))
            return

    @commands.group(invoke_without_command=True, aliases=["pw","buy","buy_worm"])
    async def prepare_worm(self, ctx):
        '''Buy a fight worm'''
        user_id = ctx.author.id
        balance = db.get_user_balance(user_id)
        cock_status = db.get_cock_status(user_id)
        cock_power = get_cock_power(cock_status)
        if cock_status != -1:
            await ctx.send("Your battle worm is already prepared for battle, currently at {:.1f}% toughness".format(cock_power * 100))
            return
        if balance < self.cock_price:
            await ctx.send("You don't have any worms!")
            return
        else:
            db.modify_user_balance(user_id, -1 * self.cock_price)
            db.set_cock_status(user_id, 0)
            await ctx.send("You exchanged {} worms for a rookie battle worm! Win fights and battles to level him up!".format(self.cock_price))

def setup(bot):
    bot.add_cog(WormFight(bot))
