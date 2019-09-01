import random
import re
import operator

from time import time
from collections import defaultdict
from sqlalchemy import Table, Column, String, Integer, PrimaryKeyConstraint, desc
from sqlalchemy.sql import select
from cloudbot import hook
from cloudbot.event import EventType
from cloudbot.util import botvars

fish = ["><(((º> ᴼᴹᴳ ᴬ FᴵSᴴ!", "><⁽⁽⁽⁽⁽◐> FᴵSᴴ!", "》((((◕> ᴹᵒᴬʳ FⁱSʰ!"]
fish_tail = ["～～～～～～～～～～～～", "¸.·´¯`·.¸¸.·´¯`·.¸¸.·´¯`·", "•*´¨`*•.¸¸.•*´¨`*•.¸¸.•*´¨`*•.¸¸.•"]
# fish = ["><((( FISH!)>", "><((TROUT!))>", "><((BASS!))>"]
# fish_tail = ["Something Smells Fishy!", "Bubbler!", "Got any 9's?"]


table = Table(
    'gofish',
    botvars.metadata,
    Column('network', String),
    Column('name', String),
    Column('caught', Integer),
    Column('feed', Integer),
    Column('chan', String),
    PrimaryKeyConstraint('name', 'chan','network')
    )

optout = Table(
    'nofish',
    botvars.metadata,
    Column('network', String),
    Column('chan', String),
    PrimaryKeyConstraint('chan','network')
    )



"""
game_status structure 
{ 
    'network':{
        '#chan1':{
            'fish_status':0|1|2, 
            'next_fish_time':'integer', 
            'game_started':0|1,
            'no_fish_kick': 0|1,
            'fish_time': 'float', 
            'catch_time': 'float'
        }
    }
}
"""

scripters = defaultdict(int)
game_status = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


@hook.on_start()
def load_optout(db):
    """load a list of channels gofish should be off in. Right now I am being lazy and not
    differentiating between networks this should be cleaned up later."""
    global opt_out
    opt_out = []
    chans = db.execute(select([optout.c.chan]))
    if chans:
        for row in chans:
            chan = row["chan"]
            opt_out.append(chan)

@hook.command("gofish", autohelp=False, permissions=["op"])
def go_fish(bot, chan, message, conn):
    """This command starts a gofish in your channel, to stop the game use .nofish"""
    global game_status
    if chan in opt_out:
        return
    elif not chan.startswith("#"):
        return "If you're wanting some 'me' time that's cool but there's no fishing by yourself."
    check = game_status[conn.name][chan]['game_on']
    if check:
        return "there is already a game running in {}.".format(chan)
    else:
        game_status[conn.name][chan]['game_on'] = 1
    set_fishtime(chan, conn)
    message("Fish are swimming about, to catch fish use .catch|reel|gaff, use .feeds|crackers to save them.", chan)

def set_fishtime(chan, conn):
    global game_status
#    game_status[conn.name][chan]['next_fish_time'] = random.randint(int(time()) + 1800, int(time()) + 3600)
    game_status[conn.name][chan]['next_fish_time'] = random.randint(int(time()) + 1800, int(time()) + 3600)
    game_status[conn.name][chan]['fish_status'] = 0
    return

@hook.command("nofish", autohelp=False, permissions=["op"])
def stop_hunt(chan, conn):
    """This command stops the gofish game in your channel. Scores will be preserved"""
    global game_status
    if chan in opt_out:
        return
    if game_status[conn.name][chan]['game_on']:
        game_status[conn.name][chan]['game_on'] = 0
        return "the game has been stopped."
    else:
        return "There is no game running in {}.".format(chan)

@hook.command("fishkick", permissions=["op"])
def no_fish_kick(text, chan, conn, notice):
    """If the bot has OP or half-op in the channel you can specify .fishkick enable|disable so that people are kicked for catching or feeding a non-existent fish. Default is off."""
    global game_status
    if chan in opt_out:
        return
    if text.lower() == 'enable':
        game_status[conn.name][chan]['no_fish_kick'] = 1
        return "users will now be kicked for catching or feeding non-existent fish. The bot needs to have appropriate flags to be able to kick users for this to work."
    elif text.lower() == 'disable':
        game_status[conn.name][chan]['no_fish_kick'] = 0
        return "kicking for non-existent fish has been disabled."
    else:
        notice(no_fish_kick.__doc__)
        return

def generate_fish():
    """Try and randomize the fish message so people can't highlight on it/script against it."""
    fbody = random.choice(fish)
    ftail = random.choice(fish_tail)
    return (fbody, ftail)


@hook.periodic(11, initial_interval=11)
def deploy_fish(message, bot):
    global game_status
    for network in game_status:
        if network not in bot.connections:
            continue
        conn = bot.connections[network]
        if not conn.ready:
            continue
        for chan in game_status[network]:
            active = game_status[network][chan]['game_on']
            fish_status = game_status[network][chan]['fish_status']
            next_fish = game_status[network][chan]['next_fish_time']
            if active == 1 and fish_status == 0 and next_fish <= time():
                #deploy a fish to channel
                game_status[network][chan]['fish_status'] = 1
                game_status[network][chan]['fish_time'] = time()
                fbody, ftail = generate_fish()
                conn.message(chan, "{}{}".format(fbody, ftail))
            continue
        continue


def hit_or_miss(deploy, catch):
    """This function calculates if the feed or catch will be successful."""
    if catch - deploy < 1:
        return .05
    elif 1 <= catch - deploy <= 7:
        out = random.uniform(.60, .75)
        return out
    else:
        return 1

def dbadd_entry(nick, chan, db, conn, catch, friend):
    """Takes care of adding a new row to the database."""
    query = table.insert().values(
        network = conn.name,
        chan = chan.lower(),
        name = nick.lower(),
        caught = catch,
        feed = friend)
    db.execute(query)
    db.commit()

def dbupdate(nick, chan, db, conn, catch, friend):
    """update a db row"""
    if catch and not friend:
        query = table.update() \
            .where(table.c.network == conn.name) \
            .where(table.c.chan == chan.lower()) \
            .where(table.c.name == nick.lower()) \
            .values(caught = catch)
        db.execute(query)
        db.commit()
    elif friend and not catch:
        query = table.update() \
            .where(table.c.network == conn.name) \
            .where(table.c.chan == chan.lower()) \
            .where(table.c.name == nick.lower()) \
            .values(feed = friend)
        db.execute(query)
        db.commit()

@hook.command("catch", "reel", "gaff", autohelp=False)
def catch(nick, chan, message, db, conn, notice):
    """when there are fish swimming about use this command to catch it."""
    global game_status, scripters
    if chan in opt_out:
        return
    network = conn.name
    score = ""
    out = ""
    miss = ["SWISH! The fish got away!", "Your bait fell off!", "Better luck next time.", "You need a bigger rod lol, maybe next time!", "Your line snapped, learn2knot and try again!", "Try some BACON, the fish got away!" ]
    if not game_status[network][chan]['game_on']:
        return "There is no game right now. Use .gofish to start a game."
    elif game_status[network][chan]['fish_status'] != 1:
        if game_status[network][chan]['no_fish_kick'] == 1:
            out = "KICK {} {} The last fish was already nabbed, try again with the next fish.".format(chan, nick)
            conn.send(out)
            return
        return "Heads up, the fish is already gone!"
    else: 
        game_status[network][chan]['catch_time'] = time()
        deploy = game_status[network][chan]['fish_time']
        catch = game_status[network][chan]['catch_time']
        if nick.lower() in scripters:
            if scripters[nick.lower()] > catch:
                notice("You are in a cool down period, you can try again in {} seconds.".format(str(scripters[nick.lower()] - catch)))
                return
        chance = hit_or_miss(deploy, catch)
        if not random.random() <= chance and chance > .05:
            out = random.choice(miss) + " You can try again in 7 seconds."
            scripters[nick.lower()] = catch + 7 
            return out
        if chance == .05:
            out += "You tried catching the fish in {} seconds, that's mighty fast. Are you running a script for this game? Take a 2 hour cool down.".format(str(catch - deploy))
            scripters[nick.lower()] = catch + 7200
            if not random.random() <= chance:
                return random.choice(miss) + " " + out
            else:
                message(out)
        game_status[network][chan]['fish_status'] = 2
        score = db.execute(select([table.c.caught]) \
            .where(table.c.network == conn.name) \
            .where(table.c.chan == chan.lower()) \
            .where(table.c.name == nick.lower())).fetchone()
        if score:
            score = score[0]
            score += 1
            dbupdate(nick, chan, db, conn, score, 0)
        else:
            score = 1
            dbadd_entry(nick, chan, db, conn, score, 0)
        timer = "{:.3f}".format(catch - deploy)
        fish = "fish" if score == 1 else "fishes"
        message("{} Perfect set, you hooked the fish in {} seconds! You have caught {} {} in {}.".format(nick, timer, score, fish, chan))
        set_fishtime(chan, conn)

@hook.command("feeds", "crackers", autohelp=False)
def feeds(nick, chan, message, db, conn, notice):
    """when there are fish swimming about use this command to feed them and make friends."""
    global game_status, scripters
    if chan in opt_out:
        return
    network = conn.name
    out = ""
    score = ""
    miss = ["How odd, the fish doesn't want to be your friend.", "The fish turned its nose up, try feeding it some crackers?", "You scared the fish away, try one of these? https://x0.no/099ia" ]
    if not game_status[network][chan]['game_on']:
        return "There is no game right now. Use .gofish to start a game."
    elif game_status[network][chan]['fish_status'] != 1:
        if game_status[network][chan]['no_fish_kick'] == 1:
            out = "KICK {} {} Pay attention, the fish is already gone!".format(chan, nick)
            conn.send(out)
            return
        return "Heads up, the fish is already gone!"
    else:
        game_status[network][chan]['catch_time'] = time()
        deploy = game_status[network][chan]['fish_time']
        catch = game_status[network][chan]['catch_time']
        if nick.lower() in scripters:
            if scripters[nick.lower()] > catch:
                notice("You are in a cool down period, you can try again in {} seconds.".format(str(scripters[nick.lower()] - catch)))
                return
        chance = hit_or_miss(deploy, catch)
        if not random.random() <= chance and chance > .05:
            out = random.choice(miss) + " You can try again in 7 seconds."
            scripters[nick.lower()] = catch + 7
            return out
        if chance == .05:
            out += "You tried saving that fish in {} seconds, that's mighty fast. Are you running a script for this game? Take a 2 hour cool down.".format(str(catch - deploy))
            scripters[nick.lower()] = catch + 7200
            if not random.random() <= chance:
                return random.choice(miss) + " " + out
            else:
                message(out)

        game_status[network][chan]['fish_status'] = 2
        score = db.execute(select([table.c.feed]) \
            .where(table.c.network == conn.name) \
            .where(table.c.chan == chan.lower()) \
            .where(table.c.name == nick.lower())).fetchone()
        if score:
            score = score[0]
            score += 1
            dbupdate(nick, chan, db, conn, 0, score)
        else:
            score = 1
            dbadd_entry(nick, chan, db, conn, 0, score)
        fish = "fish" if score == 1 else "fishes"
        timer = "{:.3f}".format(catch - deploy)
        message("{} You saved a fish in {} seconds! You have made friends with {} {} in {}.".format(nick, timer, score, fish, chan))
        set_fishtime(chan,conn)

def smart_truncate(content, length=320, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return content[:length].rsplit(' ? ', 1)[0]+suffix


@hook.command("feeders", autohelp=False)
def feeders(text, chan, conn, db):
    """Prints a list of the top fish feeders in the channel, if 'global' is specified all channels in the database are included."""
    if chan in opt_out:
        return
    feeders = defaultdict(int)
    out = ""
    if text.lower() == 'global':
        out = "Fish friend scores across the network: "
        scores = db.execute(select([table.c.name, table.c.feed]) \
            .where(table.c.network == conn.name) \
            .order_by(desc(table.c.feed)))
        if scores:    
            for row in scores:
                if row[1] == 0:
                    continue
                feeders[row[0]] += row[1]
        else:
            return "it appears no one has fed any fish yet."
    else:
        out = "Fish friend scores in {}: ".format(chan)
        scores = db.execute(select([table.c.name, table.c.feed]) \
            .where(table.c.network == conn.name) \
            .where(table.c.chan == chan.lower()) \
            .order_by(desc(table.c.feed)))
        if scores:
            for row in scores:
                if row[1] == 0:
                    continue
                feeders[row[0]] += row[1]
        else:
            return "it appears no one has friended any fish yet."

    topfeeders = sorted(feeders.items(), key=operator.itemgetter(1), reverse = True)
    out += ' ? '.join(["{}: {}".format('\x02' + k[:1] + u'\u200b' + k[1:] + '\x02', str(v))  for k, v in topfeeders])
    out = smart_truncate(out)
    return out

@hook.command("caught", autohelp=False)
def caught(text, chan, conn, db):
    """Prints a list of the top fish catchers in the channel, if 'global' is specified all channels in the database are included."""
    if chan in opt_out:
        return
    catchers = defaultdict(int)
    out = ""
    if text.lower() == 'global':
        out = "Fish catchers scores across the network: "
        scores = db.execute(select([table.c.name, table.c.caught]) \
            .where(table.c.network == conn.name) \
            .order_by(desc(table.c.caught)))
        if scores:
            for row in scores:
                if row[1] == 0:
                    continue
                catchers[row[0]] += row[1]
        else:
            return "it appears no one has caught any fish yet."
    else:
        out = "Fish catchers scores in {}: ".format(chan)
        scores = db.execute(select([table.c.name, table.c.caught]) \
            .where(table.c.network == conn.name) \
            .where(table.c.chan == chan.lower()) \
            .order_by(desc(table.c.caught)))
        if scores:
            for row in scores:
                if row[1] == 0:
                    continue
                catchers[row[0]] += row[1]
        else:
            return "it appears no one has caught any fish yet."

    topcatchers = sorted(catchers.items(), key=operator.itemgetter(1), reverse = True)
    out += ' ? '.join(["{}: {}".format('\x02' + k[:1] + u'\u200b' + k[1:] + '\x02', str(v))  for k, v in topcatchers])
    out = smart_truncate(out)
    return out

@hook.command("fishforgive", permissions=["op", "ignore"])
def fishforgive(text):
    """Allows people to be removed from the mandatory cooldown period."""
    global scripters
    if text.lower() in scripters and scripters[text.lower()] > time():
        scripters[text.lower()] = 0
        return "{} has been removed from the mandatory cooldown period.".format(text)
    else:
        return "I couldn't find anyone banned from the game by that nick"

@hook.command("gofish_opt_out", permissions=["op", "ignore"], autohelp=False)
def gofish_opt_out(text, chan, db, conn):
    """Running this command without any arguments displays the status of the current channel. gofish_opt_out add #channel will disable all gofish commands in the specified channel. gofish_opt_out remove #channel will re-enable the game for the specified channel."""
    if not text:
        if chan in opt_out:
            return "Gofish is disabled in {}. To re-enable it run .gofish_opt_out remove #channel".format(chan)
        else:
            return "Gofish is enabled in {}. To disable it run .gofish_opt_out add #channel".format(chan)
    if text == "list":
        return ", ".join(opt_out)
    if len(text.split(' ')) < 2:
        return "please specify add or remove and a valid channel name"
    command = text.split()[0]
    channel = text.split()[1]
    if not channel.startswith('#'):
        return "Please specify a valid channel."
    if command.lower() == "add":
        if channel in opt_out:
            return "Gofish has already been disabled in {}.".format(channel)
        query = optout.insert().values(
            network = conn.name,
            chan = channel.lower())
        db.execute(query)
        db.commit()
        load_optout(db)
    if command.lower() == "remove":
        if not channel in opt_out:
            return "Gofish is already enabled in {}.".format(channel)
        delete = optout.delete(optout.c.chan == channel.lower())
        db.execute(delete)
        db.commit()
        load_optout(db)

@hook.command("fish", autohelp=False)
def fish_user(text, nick, chan, conn, db, message):
    """Prints a users gofish stats. If no nick is input it will check the calling username."""
    name = nick.lower()
    if text:
        name = text.split()[0].lower()
    fish = defaultdict(int)
    scores = db.execute(select([table.c.name, table.c.chan, table.c.caught, table.c.feed])
        .where(table.c.network == conn.name)
        .where(table.c.name == name)).fetchall()
    if scores:
        for row in scores:
            if row["chan"].lower() == chan.lower():
                fish["chancaught"] += row["caught"]
                fish["chanfeeders"] += row["feed"]
            fish["caught"] += row["caught"]
            fish["friend"] += row["feed"]
            fish["chans"] += 1
        if fish["chans"] == 1:
            message("{} has caught {} and saved {} fish in {}.".format(name, fish["chancaught"], fish["chanfeeders"], chan))
            return
        catch_average = int(fish["caught"] / fish["chans"])
        friend_average = int(fish["friend"] / fish["chans"])
        message("\x02{}'s\x02 gofish stats: \x02{}\x02 caught and \x02{}\x02 saved in {}. Across {} channels: \x02{}\x02 caught and \x02{}\x02 saved. Averaging \x02{}\x02 catches and \x02{}\x02 saves per channel.".format(name, fish["chancaught"], fish["chanfeeders"], chan, fish["chans"], fish["caught"], fish["friend"], catch_average, friend_average))
    else:
        return "It appears {} has not participated in the gofish game.".format(name)

@hook.command("fishstats", autohelp=False)
def fish_stats(chan, conn, db, message):
    """Prints gofish statistics for the entire channel and totals for the network."""
    fish = defaultdict(int)
    scores = db.execute(select([table.c.name, table.c.chan, table.c.caught, table.c.feed])
        .where(table.c.network == conn.name)).fetchall()
    if scores:
        fish["feedchan"] = defaultdict(int)
        fish["catchchan"] = defaultdict(int)
        for row in scores:
            fish["feedchan"][row["chan"]] += row["feed"]
            fish["catchchan"][row["chan"]] += row["caught"]
            #fish["chans"] += 1
            if row["chan"].lower() == chan.lower():
                fish["chancaught"] += row["caught"]
                fish["chanfeeders"] += row["feed"]
            fish["caught"] += row["caught"]
            fish["friend"] += row["feed"]
        fish["chans"] = int((len(fish["feedchan"]) + len(fish["catchchan"])) / 2)
        catchchan, catchscore = sorted(fish["catchchan"].items(), key=operator.itemgetter(1), reverse = True)[0]
        feedchan, feederscore = sorted(fish["feedchan"].items(), key=operator.itemgetter(1), reverse =True)[0]
        message("\x02Gofish Stats:\x02 {} caught and {} saved in \x02{}\x02. Across {} channels \x02{}\x02 fish have been caught and \x02{}\x02 saved. \x02Top Channels:\x02 \x02{}\x02 with {} catches and \x02{}\x02 with {} saves".format(fish["chancaught"], fish["chanfeeders"], chan, fish["chans"], fish["caught"], fish["friend"], catchchan, catchscore, feedchan, feederscore))
    else:
        return "It looks like there has been no gofish activity on this channel or network."
