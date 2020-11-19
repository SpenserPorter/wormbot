import discord
import numpy as np
import lotto_dao as db
import asyncio
import re
from discord.ext import commands

ticket_cost = int(db.get_config("lottery_ticket_cost"))

#{Megaball:{num_matches:payout}}
payout_table = {True:{0:0*ticket_cost, 1:3*ticket_cost, 2:10*ticket_cost, 3:150*ticket_cost, 4:15000*ticket_cost},
                False:{0:0*ticket_cost, 1:0*ticket_cost, 2:2*ticket_cost, 3:15*ticket_cost, 4:1250*ticket_cost}}

numbers = [x for x in range(1,24)]

def build_embed(embed_input_dict):

    embed = discord.Embed(title=None,
                      description=None,
                      colour=embed_input_dict['colour']
                      )

    embed.set_author(name=embed_input_dict['author_name'])

    try:
        for key, field in embed_input_dict['fields'].items():
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'] if 'inline' in field else False)
    except:
        pass
    return embed

def format_winning_tickets(ticket_result_list):
    outstring=""
    for ticket_result in ticket_result_list:
        outstring+="Ticket {} won you {} worms! ".format(Ticket(ticket_result[0]), ticket_result[1])
    return outstring


class Ticket(object):
    __slots__ = ('numbers')

    def __init__(self, numbers):
        self.numbers = numbers

    def __repr__(self):
        return "{}-{}-{}-{}-M{}".format(*[n for n in self.numbers])

def quickpick(number_of_tickets=1):
    '''Returns a number of QuickPick tickets'''
    ticket_list = []
    numlist = [x for x in range(1,24)]
    for unused in range(number_of_tickets):
        np.random.shuffle(numlist)
        numbers = numlist[:4]
        megaball = np.random.randint(1,12)
        numbers.append(megaball)
        ticket_list.append(numbers)
    return ticket_list

def parse_ticket(winner, ticket):
    match = [x for x in ticket[:4] if x in winner[:4]]
    mega = winner[4] == ticket[4]
    return mega, len(match)

def add_ticket_to_dict(result_dict, user_id, ticket_value, payout):
    if user_id not in result_dict:
        result_dict[user_id] = [[ticket_value, payout]]
    else:
        result_dict[user_id].append([ticket_value, payout])
    return result_dict

def determine_payout(mega, match):
    return payout_table[mega][match]

class Lottery(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def tickets(self, ctx, lottory_id=None):
        """
        DM all tickets for current lottery, or lottery id if given.
        """
        lottory = db.get_current_lottory() if lottory_id is None else lottory_id
        ticket_list = db.get_user_tickets(ctx.author.id,lottory)
        await ctx.send('{} has {} tickets in the curret drawing.'.format(ctx.author, len(ticket_list)))
        for n in range(0, len(ticket_list), 50):
            await ctx.author.send('{}'.format(ticket_list[n:n+50]))

    @commands.group(invoke_without_command=True, hidden=True)
    async def lottery(self, ctx, confirm):
        '''Advances to next lottery, this will abandon all tickets from previous if
            it was not drawn first!'''
        if ctx.author.id != 154415714411741185:
            await ctx.send("You're not my real dad!")
            return
        if confirm != "confirm":
            await ctx.send("Please confirm")
            return
        db.add_lottory(0)
        lottory_id = db.get_current_lottory()
        await ctx.send("Worm Lottery {} has begun, purchase tickets now!".format(lottory_id))

    @lottery.command(hidden=True)
    async def modify_prog(self, ctx, amount: int):
        if ctx.author.id != 154415714411741185:
            await ctx.send("You're not my real dad!")
            return
        lid = db.get_current_lottory()
        new_prog = db.modify_lottory_jackpot_prog(lid, amount)
        jackpot = new_prog + payout_table[True][4]
        await ctx.send("Lottory {} jackpot is now {}".format(lid, jackpot))

    @commands.group(invoke_without_command=True, aliases=['what'])
    async def info(self, ctx):
        '''Displays the paytable'''
        lid = db.get_current_lottory()
        progressive = db.get_lottory_jackpot_prog(lid)
        await ctx.send("4 Unordered Balls <1-23>, 1 MEGABALL <1-11> - Ticket cost {:,} \n Match 4+1 win {:,} + {:,} progressive!\nMatch 4     win {:,}\nMatch 3+1 win {:,}\nMatch 3     win {:,}\nMatch 2+1 win {:,}\nMatch 2+0 win {:,}\nMatch 1+1 win {:,}\nChance to win ANY prize 1:6".format(ticket_cost,
        payout_table[True][4], progressive, payout_table[False][4], payout_table[True][3], payout_table[False][3], payout_table[True][2], payout_table[False][2], payout_table[True][1]))

    @commands.group(invoke_without_command=True)
    async def status(self,ctx):
        '''Display the current lottery status'''
        lottory_id = db.get_current_lottory()
        tickets = db.get_lottory_tickets(lottory_id)
        num_tickets = len(tickets)
        progressive = db.get_lottory_jackpot_prog(lottory_id)
        jackpot = payout_table[True][4] + progressive
        await ctx.send("Lottery {} is in progress, currently {:,} tickets sold, current jackpot is {:,}".format(lottory_id,num_tickets,jackpot))

    @commands.group(invoke_without_command=True)
    async def draw(self,ctx):
        '''Start the next drawing'''

        lottory_id = db.get_current_lottory()
        progressive = db.get_lottory_jackpot_prog(lottory_id)
        total_jackpot = progressive + payout_table[True][4]
        ticket_list = db.get_lottory_tickets(lottory_id) #List of tuples (user_id, ticket_value)

        if len(ticket_list) < 1: #Verify there is at least 1 ticket sold before allowing drawing
            await ctx.send("There are no tickets sold for this drawing yet!")
            return

        db.add_lottory() #increment current when drawing starts
        winning_numbers = quickpick()[0] #Choose winning numbers
        balls = {0:'First', 1:'Second', 2:'Third', 3:'Fourth', 4:'MEGA'}
        embed_dict = {'colour':discord.Colour(0x006400), 'author_name':"Drawing for lottery {}! Jackpot is currently {:,}".format(lottory_id,total_jackpot),
                      'fields': {}
                      }
        lottory_message = await ctx.send(embed=build_embed(embed_dict))

        async with ctx.typing():
            winning_ticket_display = []
            for ball_number, ball_name in balls.items():
                await asyncio.sleep(3)
                winning_ticket_display.append(str(winning_numbers[ball_number]))
                embed_dict['fields'][1] = {'name': "{} Ball".format(ball_name), 'value': winning_numbers[ball_number], 'inline': True}
                winning_numbers_value = "-".join(winning_ticket_display) if len(winning_ticket_display) < 5 else Ticket(winning_numbers)
                embed_dict['fields'][2] = {'name': 'Winning Numbers' , 'value': winning_numbers_value, 'inline': True}
                await lottory_message.edit(embed=build_embed(embed_dict))

        num_tickets = len(ticket_list)
        progressive_split = []
        winner_dict = {}
        loser_dict = {}
        total_payout = 0

        async with ctx.typing():
            for ticket_tuple in ticket_list:
                ticket_value = eval(ticket_tuple[0]) #ticket value stored as a string, convert back to list
                user_id = ticket_tuple[1]
                mega, match = parse_ticket(winning_numbers, ticket_value)
                ticket_payout = determine_payout(mega, match)

                if ticket_payout != 0:
                    winner_dict = add_ticket_to_dict(winner_dict, user_id, ticket_value, ticket_payout)
                else:
                    loser_dict = add_ticket_to_dict(loser_dict, user_id, ticket_value, ticket_payout)

        results = {}
        async with ctx.typing():

            for user_id, list_of_winning_tickets in winner_dict.items():
                balance_modifier = 0

                for ticket_tuple in list_of_winning_tickets:
                    ticket_value = Ticket(ticket_tuple[0])
                    ticket_payout = ticket_tuple[1]

                    if ticket_payout == payout_table[True][4]:
                        progressive_split.append([user_id, ticket_value])
                    else:
                        balance_modifier += ticket_payout

                new_user_balance = db.modify_user_balance(user_id, balance_modifier)
                results[user_id] = [balance_modifier, new_user_balance, list_of_winning_tickets]
                total_payout += balance_modifier

            jackpot_results = {}

            if len(progressive_split) > 0:
                jackpot_progressive_share = round(progressive / len(progressive_split), 2)
                jackpot_payout = round(payout_table[True][4] + jackpot_progressive_share, 2)
                for ticket_tuple in progressive_split:
                    user_id = ticket_tuple[0]
                    ticket_value = ticket_tuple[1]
                    total_payout += jackpot_payout
                    new_user_balance = db.modify_user_balance(user_id, jackpot_payout)
                    if user_id not in jackpot_results:
                        jackpot_results[user_id] = [jackpot_payout, new_user_balance, [ticket_value], jackpot_progressive_share]
                    else:
                        jackpot_results[user_id][0] += jackpot_payout
                        jackpot_results[user_id][1] = new_user_balance
                        jackpot_results[user_id][2].append(ticket_value)
                        jackpot_results[user_id][3] += jackpot_progressive_share

                split_won = 'won' if len(jackpot_results) == 1 else 'split'
                await ctx.send("------------JACKPOT WINNAR!!!!!!-------------")
                for user_id, result in jackpot_results.items():
                    jackpot_payout = result[0]
                    new_user_balance = result[1]
                    ticket_values = result[2] if len(result[2]) <= 10 else len(result[2])
                    progressive_split = result[3]
                    user = await self.bot.fetch_user(user_id)
                    await ctx.send('{} {} the Jackpot! Payout {:,}, your share of the progressive is {:,}! with {} tickets!!'.format(user.name, split_won, round(jackpot_payout,2), round(progressive_split,2), ticket_values))
                    await user.send('You {} the Jackpot for lottory {} with ticket {}! {:,} has been deposited into your account. Your new balance is {}.'.format(split_won, lottory_id, ticket_value, round(jackpot_payout,2), new_user_balance))

            for user_id, result in results.items():
                jackpot_balance_modifier = jackpot_results[user_id][0] if user_id in jackpot_results else 0
                balance_modifier = result[0] + jackpot_balance_modifier
                new_user_balance = result[1]
                winning_tickets = result[2]
                user = await self.bot.fetch_user(user_id)
                embed_dict['fields'][user_id] = {'name': user.name, 'value': "Won a total of {:,} on {:,} winning tickers!".format(balance_modifier, len(winning_tickets)), 'inline': False}
                await user.send("Lottory {} Results: You won {:,} worms! Your new balance is {:,} worms.".format(lottory_id, balance_modifier, new_user_balance))
                if len(winning_tickets) < 100:
                    for n in range(0, len(winning_tickets), 50):
                        await user.send("Lottery {} winning numbers: {}. Your winning tickets: {}".format(lottory_id, winning_numbers, format_winning_tickets(winning_tickets[n:n+50])))
                await lottory_message.edit(embed=build_embed(embed_dict))

        income = ticket_cost * num_tickets
        payout_ratio = 100 * (total_payout - income) / income
        db.update_lottory_stats(lottory_id, income, total_payout)
        embed_dict['author_name'] = "Lottory {} ended!".format(lottory_id)
        embed_dict['fields'][0] = {"name": "{:,} tickets were sold for {:,}".format(num_tickets, income), 'value':"{:,} was paid out for a payout ratio of {}%".format(round(total_payout, 2), round(payout_ratio, 2))}
        await lottory_message.edit(embed=build_embed(embed_dict))

        if len(progressive_split) == 0:
            lottory_id = db.get_current_lottory() #Add progressive to next lottory
            db.modify_lottory_jackpot_prog(lottory_id, progressive)
        else:
            await ctx.send("Jackpot has been reseeded to {:,}".format(payout_table[True][4]))

    @lottery.command(invoke_without_command=True)
    async def stats(self, ctx, lottory_id=None):
        '''Returns lifetime lottory statistics, or stats of specific lottory_id if given'''
        stats_list = db.get_lottory_stats(lottory_id)
        total_income = 0
        total_outflow = 0
        lottory_id_total = '{}'.format(lottory_id) if lottory_id is not None else 'lifetime'
        for stats_tuple in stats_list:
            income = stats_tuple[0]
            outflow = stats_tuple[1]
            total_income += income
            total_outflow += outflow
        if total_income > 0:
            payout_ratio = 100 * (total_outflow - total_income) / total_income
            await ctx.send("Lottory {} stats: Total income: {:,} Total payout: {:,} Payout Ratio: {}%".format(lottory_id_total, total_income, total_outflow, round(payout_ratio,2)))
        else:
            await ctx.send("There are not stats yet!")

    @commands.group(invoke_without_command=True, aliases=['buy_tickets', 'bt'])
    async def buy_ticket(self, ctx, first: int, second: int, third: int, fourth: int, mega: int):
        """
        Purchase a lottory ticket, enter all 5 numbers seperated by spaces.
        Valid tickets must have first 4 numbes between 1-23, and last number between 1-11.
        Use !bt qp <number> to purchase a number of quickpick tickets. Good luck!
        """
        lottory_id = db.get_current_lottory()
        user_balance = db.get_user_balance(ctx.author.id)
        ticket = [first, second, third, fourth,mega]
        ticket_print = Ticket(ticket)

        if user_balance < ticket_cost:
            await ctx.send("That would cost {:,}, your balance is {:,}. Broke ass bitch".format(ticket_cost, user_balance))
            return

        #Validate ticket entry
        for number in ticket[:4]:
            if number not in numbers:
                await ctx.send("{} is not a valid ticket, first 4 numbers must be between {}-{}}".format(ticket, numbers[0], numbers[-1]))
                return
        if ticket[4] not in range(1,12):
            await ctx.send("{} is not a valid ticket, megaball must be between 1-11".format(ticket))
            return
        for i in range(3):
            if ticket[i] in ticket[:i]:
                await ctx.send("{} is not a valid ticket, first four numbers must be unique".format(ticket_print))
                return
            if ticket[i] in ticket[i+1:4]:
                await ctx.send("{} is not a valid ticket, first four numbers must be unique".format(ticket_print))
                return

        progressive_add = ticket_cost * .1
        db.add_ticket_to_user([ticket], lottory_id, ctx.author.id)
        new_balance = db.modify_user_balance(ctx.author.id, -1 * ticket_cost)
        db.modify_lottory_jackpot_prog(lottory_id, progressive_add)
        new_progressive = db.get_lottory_jackpot_prog(lottory_id) + payout_table[True][4]

        await ctx.send("{} purchased ticket {}, your balance is now {:,}. The progressive jackpot is now {:,}.".format(ctx.author.name, Ticket(ticket), new_balance, new_progressive))

    @buy_ticket.command(aliases=['quickpick'])
    async def qp(self, ctx, number_of_tickets=1):
        """
        Quickpick tickets, enter a number to choose how many you want!
        """
        lottory_id = db.get_current_lottory()
        user_balance = db.get_user_balance(ctx.author.id)
        total_cost = ticket_cost * number_of_tickets
        if user_balance < total_cost:
            await ctx.send("That would cost {:,}, your balance is {:,}.".format(total_cost, user_balance))
            return
        else:
            async with ctx.typing():

                ticket_list = quickpick(number_of_tickets)
                progressive_add = number_of_tickets * ticket_cost * .1
                db.add_ticket_to_user(ticket_list, lottory_id, ctx.author.id)
                new_balance = db.modify_user_balance(ctx.author.id, -1 * total_cost)
                db.modify_lottory_jackpot_prog(lottory_id, progressive_add)
                new_progressive = db.get_lottory_jackpot_prog(lottory_id)
                ticket_obj_list = list(map(lambda x: Ticket(x), ticket_list)) #Convert list of tickets to Ticket objects

                if len(ticket_list) <= 5:
                    output_line_list = []
                    for ticket in ticket_list:
                        output_line_list.append('Quickpick ticket {} purchased by {}, good luck!'.format(Ticket(ticket), ctx.author.name))
                    await ctx.send("\n".join(output_line_list))

                if number_of_tickets > 500:
                    await ctx.author.send("You bought {} tickets. I'm not going to send you all of them.".format(number_of_tickets))

                else:
                    for n in range(0, len(ticket_list), 50):
                        await ctx.author.send("Lottory {} Quickpick tickets {}".format(lottory_id, ticket_obj_list[n:n+50]))

                await ctx.send("{} spent {:,} on {:,} tickets, new balance is {:,}. The jackpot is now {:,}".format(ctx.author.name, total_cost, number_of_tickets, round(new_balance,2), payout_table[True][4]+new_progressive))

def setup(bot):
    bot.add_cog(Lottery(bot))
