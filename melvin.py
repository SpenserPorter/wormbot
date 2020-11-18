import discord
import random
import datetime
import asyncio
from discord.ext import commands

#TOKEN = "NzQ5NDg2NTYzNjkxNTkzNzQw.X0srwQ.XfT6_2qU-cBhQHxYfxqvGtg8Zdc"
TOKEN = "Nzc4Mzg2MTEzNDU0MTQ1NTQ3.X7ROjw.6jwTylzC29i8reFdb7z4WIMg9Qw"
client = commands.Bot(command_prefix = "!")


# @client.event
# async def status(ctx, user: discord.Member):
#     if user.activity:
#         await ctx.send(f'{user.name} is {user.activity.type.name}')
#     else:
#         await ctx.send(f'{user.name}: no activity')


# @bot.command(hidden=True)
# async def mystatus(ctx):
#     user = ctx.message.author
#     await ctx.send(user.activity.type.name) if user.activity else await ctx.send('No activity')
#     user_id = str(after.id)
#     if str(after.status) == "offline":
#         print("{} has gone {}.".format(after.name,after.status))
#     if str(after.status) == "online":
#         print("{} has gone {}.".format(after.name,after.status))
def update_number(entries, i, count, file):
    user = entries.pop(i).split("%")

    user[1] = str(count)

    entries.append("%".join(user))
    file.seek(0)
    file.truncate()
    file.write("_".join(entries))
    file.close()
    return "%".join(user)


def create_new_entry(id, file, count):
    file.write("_" + id + "%" + str(count))
    file.close()
    return


def check_for_client_Location(id, count=0, react=0):
    id = str(id)
    User_Data = open(list(temp_list_data[int(id[0])])[0], "r+")
    for each in User_Data:
        Whole_Data = each
    entries = Whole_Data.split("_")
    found = False
    i = 0
    for each in entries:
        if id in each:
            found = True
            break
        i += 1
    if not found:
        if react == 1:
            create_new_entry(id, User_Data, 1)
        elif react == 42069:  # if react is 42069 and user isnt in it creates new entrie of 0
            if count != 0:
                create_new_entry(id, User_Data, count)
                return
            return False
        else:
            create_new_entry(id, User_Data, 0)
        User_Data.close()
        return id + "%" + str(count)
    else:
        if react == 0 and count == 0:  # Checking for stats
            User_Data.close()
            return entries[i]
        if react == 1337:
            update_number(entries, i, count, User_Data)
            return
        elif count == 0 and not react == 42069:
            num = update_number(entries, i, (int(entries[i].split("%")[1]) + react), User_Data)
            User_Data.close()
            return num  # return string ie 1234271893%73
        elif react == 42069:
            return entries[i]
        update_number(entries, i, count, User_Data)
        return


def clearing_time(test,type):
    if type == "daily":
        today.clear()  # clear list
        today.append("-".join(test))
        temp_file = open("today", "w")  # reset file save
        temp_file.write("-".join(test) + "_")
        temp_file.close()
    elif type == "steal":
        pass


def time(which):
    after = datetime.date.today().strftime("%Y-%m-%d").split("-")
    if which == "daily":
        try:
            before = today[0].split("-")
            if len(before) != 3:
                clearing_time(after)
        except:
            clearing_time(after,"daily")
            return
        finally:
            if int(after[0]) > int(before[0]):
                clearing_time(after)
            elif int(after[1]) > int(before[1]):
                clearing_time(after)
            elif int(after[2]) > int(before[2]):
                clearing_time(after)
    elif which == "steal":
        pass



@client.command()
async def give(ctx,who,value):
    "Share some love by giving it to others <3"
    message = ctx.message
    their_id = message.mentions[0].id
    value = int(value)
    if ctx.author.id == message.mentions[0].id:
        await ctx.send("You cant send worms to yourself dummy")
        return
    else:
        a = check_for_client_Location(message.author.id).split("%")
        if int(value) < 10:
            await ctx.send("You need to transfer a minimum of 10 worms.")
            return
        elif int(a[1]) < value:
            await ctx.send("You dont have " + str(value) + " worms. you only have " + a[1] + " worms")
            return  # not enough money
        else:
            b = check_for_client_Location(their_id, react=42069)
            if isinstance(b, bool):
                check = ctx.guild.get_member(their_id)
                if check == None:
                    await ctx.send("The person is not in this server")
                    return
                else:
                    check_for_client_Location(their_id, count=value, react=42069)
                    await ctx.send(file=discord.File(give_gif[random.randint(0, len(give_gif) - 1)]))
                    await ctx.send(message.author.mention + " has sent " + str(value) + " worms to " + message.mentions[0].mention)
                    return
            else:
                check_for_client_Location(their_id, count=int(b.split("%")[1]) + value)
                # print(int(a[1]) - value)
                check_for_client_Location(a[0], count=(int(a[1]) - value), react=1337)
                check_for_client_Location(their_id, count=value, react=42069)
                await ctx.send(file=discord.File(give_gif[random.randint(0, len(give_gif) - 1)]))
                await ctx.send(message.author.mention + " has sent " + str(value) + " worms to " + message.mentions[0].mention)
                return
#         elif message.content[1:6].lower() == "daily":  # remmeber to indent back
#             time("daily")
#

@client.command()
@commands.cooldown(1, 864000, commands.BucketType.user)
async def daily(ctx):
    "Does your daily check in - works every 24 hours"
    message = ctx.message
    a = check_for_client_Location(message.author.id).split("%")

    check_for_client_Location(a[0], count=int(a[1]) + 25)
    await ctx.send(file=discord.File(daily_gif[random.randint(0, len(daily_gif) - 1)]))
    await ctx.send("You collected 25 worms for today :D")


@daily.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = 'You already did your check in, please try again in %s Hours and %s Minute'%(error.retry_after//36000,error.retry_after % 3600 //60)
        await ctx.send(msg)
    else:
        raise error


@client.command()
        # elif message.content[1:7].lower() == "double":
async def double(ctx,value):
    "Have a gambling addiction? Test your luck by potentially doubling your profits!! Or loose it all...."
    value = int(value)
    message = ctx.message
    def change(num,item):
        check_for_client_Location(item[0], count=str(num), react=1337)  # force change
    try:

                         # how much they initally bet
        saved = value  # how much they initally bet
        item = check_for_client_Location(message.author.id).split("%")
        if message.channel.id in temp_channel:
            await ctx.send("Someone else is playing, wait for them to finish :)")
            return
        else:
            temp_channel.append(message.channel.id)
        if value < 10:
            await ctx.send("you must bet at least 10 worms to play :D")
            temp_channel.remove(message.channel.id)
            return
        elif int(item[1]) < value:
            await ctx.send("You dont have " + str(value) + " worms, you have " + item[1] + " worms.")
            temp_channel.remove(message.channel.id)
            return

        def is_correct(m):
            return m.author == message.author

        while True:
            answer = random.randint(0, 1)
            if answer == 1:
                value = 2 * value
                await message.channel.send("You Won " + str(value) + " Worms!!")
                wrong = True
                i = 0
                while wrong:
                    # print("temp")
                    await ctx.send("Would you like to double " + str(value) + " Worms or risk losing it all? \n reply \"Double\" or \"Payout\"")
                    guess = await client.wait_for('message', check=is_correct, timeout=25.0)
                    # print("temps")

                    if guess.content.lower() == "double":
                        wrong = False
                    elif guess.content.lower() == "payout" or i == 3:
                        await message.channel.send(
                            'You recieved ' + str(value) + " Worms! You now have a total of " + str(int(item[1]) - saved + value) + " worms")
                        change(int(item[1]) - saved + value,item)
                        temp_channel.remove(message.channel.id)
                        return

                    else:
                        await message.channel.send("Please reply with \"Double\" or \"Payout\"")
                        i += 1
            else:
                await message.channel.send("You lost " + str(value) + " worms :<, and now you have a total of " + str(int(item[1]) - saved) + " worms")
                change(int(item[1]) - saved,item)
                temp_channel.remove(message.channel.id)
                return
#
    except asyncio.TimeoutError:
        await message.channel.send("Sorry you took too long to reply")
        await message.channel.send('You recieved ' + str(value) + " Worms and now you have a total of " + str(int(item[1]) - saved + value) + " worms")
        change(int(item[1]) - saved + value)
        temp_channel.remove(message.channel.id)
    except:
        await ctx.send("Do !double <amount you want to bet> to begin Double or Nothing!")
    finally:
        return
# @client.command()
# async def leaderboards():
#     pass

@client.event
async def on_member_update(before, after):
    # client.channels.get("<ID of the channel you want to send to>").send("<your message content here>")
    channel = client.get_channel(746544783459090433)
    if str(after.id) == "344916393294168064":
        if after.activity:
            await channel.send(str(after.activity.type) +"Did this work?")
        else:
            await channel.send(str(after.activity)+"Did this work?")
@client.command()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def steal(ctx,person,value):
    "Have someone you hate? Try to steal Worms from them, But be warned....it's not that easy to steal..."
    message = ctx.message
    # try:

    steal_value = int(value)
    their_id = message.mentions[0].id
    a = check_for_client_Location(message.author.id).split("%")
    b = check_for_client_Location(their_id, react=42069).split("%")
    data = {'author': message.author.mention, "value": steal_value,
            "target": message.mentions[0].mention, "author2": message.author.name,
            "target2": message.mentions[0].name}
    if message.author.id == message.mentions[0].id:
        await ctx.send("You cant steal worms form yourself dummy")
        return
    elif int(b[1]) < steal_value:
        await ctx.send("{target} don't even have that much worms to steal from".format(**data))
        return
    elif steal_value < 10:
        await ctx.send("Steal more worms coward")
        return
    elif int(a[1]) == 0:
        small = random.randint(0, 2)
        if small == 0:  # some one gave u money
            num = random.randint(20, 70)  # generous value
            data.update({"value": str(num)})
            check_for_client_Location(a[0], count=num + int(a[1]))
            await ctx.send(steal_zero[random.randint(0, len(steal_zero) - 1)].format(**data))
        elif small == 1:
            num = random.randint(1, 20)
            data.update({"value": str(num)})
            check_for_client_Location(a[0], count=num + int(a[1]))
            await message.channel.send(
                steal_one[random.randint(0, len(steal_one) - 1)].format(**data))
        else:  # stole thus same as teir 5
            ratio = random.randint(10, steal_value // 2) / steal_value
            num = int(round(ratio * steal_value, 0))
            data.update({"value": str(num)})
            check_for_client_Location(a[0], int(a[1]) + num)
            check_for_client_Location(b[0], int(b[1]) - num, react=1337)
            await ctx.send(steal_five[random.randint(0, len(steal_five) - 1)].format(**data))
        return
    chance = random.randint(2, 6)
    if chance == 2:  # looses more worms worms

        ratio = steal_value / int(b[1])
        number = min(int(round(ratio * int(a[1]), 0)), 10 * steal_value)
        num = random.randint(int(number // 2), int(number - 1))
        data.update({"value": str(num)})
        check_for_client_Location(a[0], int(a[1]) - num)
        await ctx.send(steal_two[random.randint(0, len(steal_two) - 1)].format(**data))
        return

    elif chance == 3:  # looses little worms
        ratio = steal_value / int(b[1])
        number = min(int(round(ratio * int(a[1]), 0)), 5 * steal_value)
        num = random.randint(1, int(number / 2 - 1))
        data.update({"value": str(num)})
        check_for_client_Location(a[0], int(a[1]) - num)
        await ctx.send(steal_three[random.randint(0, len(steal_three) - 1)].format(**data))
        return

    elif chance == 4:
        await ctx.send(steal_four[random.randint(0, len(steal_four) - 1)].format(**data))
        return

    elif chance == 5:  # gain little worm
        ratio = random.randint(10, steal_value // 2) / steal_value
        num = int(round(ratio * steal_value, 0))

        data.update({"value": str(num)})
        check_for_client_Location(a[0], int(a[1]) + num)
        check_for_client_Location(b[0], int(b[1]) - num, react=1337)
        await ctx.send(steal_five[random.randint(0, len(steal_five) - 1)].format(**data))

    elif chance == 6:  # gains lots worms
        ratio = random.randint(steal_value // 2, steal_value) / steal_value
        num = int(round(ratio * steal_value, 0))
        data.update({"value": str(num)})
        check_for_client_Location(a[0], int(a[1]) + num)
        check_for_client_Location(b[0], int(b[1]) - num, react=1337)
        await ctx.send(steal_six[random.randint(0, len(steal_six) - 1)].format(**data))


@steal.error
async def steal_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = 'You already did your check in, please try again in %s minutes and %s Seconds'%(int(error.retry_after//60),int(round(error.retry_after % 60,0)))
        await ctx.send(msg)
    else:
        raise error
@client.command()
async def worm(ctx,who = None):
    "Check the count of worms. Do !worm to check yourself or !worm <@mention> to check others. Remember, you can also earn worms by reacting with the worms emotes on OTHER users messages <3"
    message = ctx.message
    if who is None:
        ide = message.author
    else:
        ide = message.mentions[0]
    numm = check_for_client_Location(ide.id).split("%")[1]
    if numm == "0":
        await message.channel.send(ide.display_name + " has no worms :( React with some worms to other peoples posts to earn some :D!")
        return
    await message.channel.send(ide.display_name + " has " + numm + " worms!")
@client.listen()
async def on_message(message):
    if "thank you" in str(message.content.lower()):
        await message.channel.send("You're Welcome :D")
    if len(message.content) == 4 and message.content[0:4].lower() == "worm":  # user checks worms
        ide = message.author
        numm = check_for_client_Location(ide.id).split("%")[1]
        if numm == "0":
            await message.channel.send(
                ide.display_name + " has no worms :( React with some worms to other peoples posts to earn some :D!")
            return
        await message.channel.send(ide.display_name + " has " + numm + " worms!")

@client.event
async def on_raw_reaction_add(payload):
    key = await client.http.get_message(payload.channel_id, payload.message_id)
    if (
            payload.emoji.name in worms):  # and payload.user_id != int(key["author"]["id"]) and 749486563691593740 != int(key["author"]["id"]):
        check_for_client_Location(payload.user_id, react=1)


@client.event
async def on_raw_reaction_remove(payload):
    key = await client.http.get_message(payload.channel_id, payload.message_id)
    if (payload.emoji.name in worms) and payload.user_id != int(key["author"]["id"]) and 749486563691593740 != int(
            key["author"]["id"]):
        check_for_client_Location(payload.user_id, react=-1).split("%")


@client.event
async def on_ready():
    print("RUNNING")


f = "r+"
temp_list_data = [("User_Data_Zero", f), ('User_Data_One', f), ('User_Data_Two', f), ('User_Data_Three', f),
                  ('User_Data_Four', f), ('User_Data_Five', f), ('User_Data_Six', f), ('User_Data_Seven', f),
                  ('User_Data_Eight', f), ('User_Data_Nine', f)]
worms = ["WorM", "Worm"]
today = []
temp_channel = []
give_gif = []
daily_gif = []
# temp_file = open("give", "r")
# for each in temp_file:
#     give_gif.extend(each.split("_"))
#
# temp_file = open("daily", "r")
# for each in temp_file:
#     daily_gif.extend(each.split("_"))
# temp_file = open("today", "r")
# for each in temp_file:
#     today.extend(each.split("_"))
# steal_zero = []
# steal_one = []
# steal_two = []
# steal_three = []
# steal_four = []
# steal_five = []
# steal_six = []
# steal = [steal_zero, steal_one, steal_two, steal_three, steal_four, steal_five, steal_six]
# temp_file = open("steal", "r")
# i = -1
# for each in temp_file:
#     if "[][]" in each:
#         i += 1
#         continue
#     else:
#         steal[i].append(each.rstrip("\n"))

client.run(TOKEN)
