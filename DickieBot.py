# -*- coding: utf-8 -*-
'''
    DickieBot v 1.0 : The Dickening
    Created by Dickie 6/9/2011  (heh...6/9)
    
    By using this bot you agree to the following:
        - Licorice is fucking gross.
        - mog like dudes.
'''

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from time import localtime, strftime
from datetime import datetime as dt

import re, time, getpass, string, random, sys, types
import commands, factoids
import wikiscrape_datastructure as wiki

# Global constants for configuration and initialization
# Channel names are CASE SENSITIVE
G_CHANNELS = ['##gen','#hsvguns','##boobs','#MidsouthMakers']
#G_CHANNELS = ['##boobs'] # used for testing
G_DATABASE = 'DickieBot.db'
G_BOTNAME,G_HOST,G_PORT = 'DickieBot','chat.freenode.net', 6667

G_MESS_LIMIT = 434

# int percentage, denoting chance of triggering random factoid on a non-command PRIvmsg or action
G_RANDOMFREQUENCY = 2

# List of users we choose to prevent from using some commands
G_NONOLIST = ['GirBot','ackis2','fedaykin','lambdabot','botparts','Cskiboy','NOTMAKERSLOCAL','WareWulf','RfidBot','blombast','BitcoinTip']

# Logs IRC chatter
class IRCLogger():
    files = {}    #Dictionary of file objects

    def __init__(self):
        # Opens a file to log each channel separately, storing the objects
        for channel in G_CHANNELS:
            self.files[channel] = open('./logs/%s.txt' % (channel.replace('#','')), 'a')
                
        # Opens a file to log non-channel chatter
        self.files[G_BOTNAME] = open('./logs/%s.txt' % G_BOTNAME, 'a')
            
    # Logs a line to a particular file
    def log(self,channel,msg):
        # Determine where we are sending this logged message
        if channel in G_CHANNELS: target = channel
        else: target = G_BOTNAME
               
        timestamp = '[%s]' % (strftime("%x %X",localtime()))

	if self.files[target].closed:
	    self.files[target] = open('./logs/%s.txt' % (channel.replace('#','')),'a')

        self.files[target].write('%s %s\n' % (timestamp, msg))
        self.files[target].flush()

    # Closes all files
    def close(self):
        timestamp = '[%s]' % (strftime("%x %X",localtime()))

        for channel in G_CHANNELS:
            self.files[channel].write('%s: File %s closed.\n' % (timestamp,channel))
            self.files[channel].flush()
            self.files[channel].close()
        self.files[G_BOTNAME].write('%s: File %s closed.\n' % (timestamp,channel))
        self.files[G_BOTNAME].flush()
        self.files[G_BOTNAME].close()

# Protocol the bot will follow
class MyIRCBot(irc.IRCClient):
    # Meta meta meta meta meta meta meta meta meta meta meta meta
    # Mushroom mushroom
    nickname = G_BOTNAME
    realnick = G_BOTNAME
    userinfo = "I'm using the Internet!"
    versionName = 'The Dickening'
    versionEnv = 'Python 2.6'
    username = G_BOTNAME
    realname = G_BOTNAME
    sourceURL = 'Not yet.'
    versionNum = '1.0'
        
    # Dictionary containing shut up flag, shut up start time, and shut up duration
    shutUp = {}
 
    # Will log our IRC sessions
    logger = IRCLogger()
    
    # Factoid handler. Factoids are shared over multiple channels.
    factoids = factoids.factoidHandler(G_DATABASE)
    
    # Dictionary of the last factoid triggered per channel, or per PM
    lastFact = {}

    # Dict of command handlers. One for each channel. This separates inventory
    # and roulette guns
    commands = {} 
    
    # Will store nick list for each channel
    nickList = {}
    
    # List of channels in which we are ops
    opChans = []

    # Keep track of lines since last random factoid.
    lineCount = {}

    # Called when connection is made
    def connectionMade(self):
        # IRCClient implementation called to preserve important features
        # like registering with the network and providing a nick
        irc.IRCClient.connectionMade(self)

        # Log connection time
        naow = time.asctime(time.localtime(time.time()))
        for channel in G_CHANNELS:
            self.logger.log(channel,'[connected at %s]' % naow)
            self.nickList[channel] = []
            self.commands[channel] = commands.commandHandler()
	    self.shutUp[channel] = [False,dt.now(),0]
	    self.lastFact[channel] = 0
	    self.lineCount[channel] = 0
        self.logger.log(G_BOTNAME,'[connected at %s]' % naow)

        self.msg('nickserv','ghost %s %s' % (G_BOTNAME,NICKPASS))
        
    # Called when the connection is lost
    def connectionLost(self, reason):
        # IRCClient implementation called to preserve functionality we
        # don't want to override
        irc.IRCClient.connectionLost(self, reason)

        # Log disconnect time
        naow = time.asctime(time.localtime(time.time()))
        for channel in G_CHANNELS:
            self.logger.log(channel,'[disconnected at %s]' % naow)
        self.logger.log(G_BOTNAME,'[disconnected at %s]' % naow)

        # Close the files
        self.logger.close()

    # Called when bot has registered with a server
    def signedOn(self):
	# Go ahead and try to ghost and change nick just in case
	self.msg('nickserv','ghost %s %s' % (G_BOTNAME,NICKPASS))
        self.setNick(G_BOTNAME)

        # Identify with services
        self.msg('nickServ','identify %s' % NICKPASS)
        
        # Join them thar channels, initialize nickList for each
        for channel in G_CHANNELS:
            self.join(channel)

    # Called when bot attempts to send a line, overwritten for unicode handling
    def sendLine(self,line):
	if isinstance(line,types.UnicodeType):
	    irc.IRCClient.sendLine(self,line.encode(sys.stdin.encoding))
	else:
	    irc.IRCClient.sendLine(self, line)
	
	print line

    # Called when my nick has changed
    def nickChanged(self,nick):
        # Log the change
        self.logger.log(G_BOTNAME,'[My nick changed to %s]' % nick)
        
        # Try to regain nick
        #if nick != G_BOTNAME:
        #    self.msg('nickserv','ghost %s %s' % (G_BOTNAME,NICKPASS))
        #    self.setNick(G_BOTNAME)
        #    self.msg('nickserv','identify %s' % NICKPASS)

    # Called when bot joins a channel
    def joined(self, channel):
        # Log the join
        self.logger.log(channel,'[I have joined %s]' % channel)
        
        # Make an entrance
        self.msg(channel,"I'm back, baby.")

    # Called when bot is kicked from a channel
    def kickedFrom(self,channel,kicker,message):
        # 1. Complain
        self.msg(kicker,'Meanie.')
        # 2. Come back (if able)
        self.join(channel)
	# 3. Try to kick back (if able)
	time.sleep(3)
	self.kick(channel,kicker,'Take that, slut!')

    # Called when I receive a private message
    def privmsg(self, user, channel, msg):
        # Log the message
        self.logger.log(channel,'%s: %s - %s' % (channel,user,msg))
        
        # Strip the nick from the nick@host string
        user = user.split('!', 1)[0]
        
        # Determine where replies to this message should go
        if channel in G_CHANNELS: 
	    target = channel
	    self.lineCount[channel] += 1
        else:
	    target = user

	print 'Target - msg - %s' % (target)
            
        command,sep,args = '','',''

        # Checking for command, first make sure nick is not ignored
        if user not in G_NONOLIST:
            # Check for command in direct address to bot
            # Examples: "BotName: wiki toothpaste", "BotName, !spin"
            if re.match(r'^%s[\,\:\-]?\s+' % (G_BOTNAME),msg,re.I) != None:
                # Split string into botname and message section
                breakout = re.split(r'^%s[\,\:\-]?\s+' % (G_BOTNAME),msg,re.I)
                # Command and command arguments will be in the second half of the list
                command,sep,args = breakout[1].lstrip('!').partition(' ')
                
            # Check for general command line starting with exclamation point
            elif msg.startswith('!'):
                command,spc,args = msg.lstrip('!').partition(' ')
                command = command.lower()
                
            # Check for command syntax, then handle command    
            if command != '':
                # Is command pull? This is to "pull the trigger" on the channel's roulette gun.
                # Usage: !pull
                if command == 'pull':
                    # We don't play roulette alone.
                    if target != user:
                        # If I don't have ops, then there's no point
                        if target not in self.opChans:
                            self.msg(target,'This channel does not respect my second amendment right to bear arms.')
                            return
                        type,response = self.commands[channel].pull()
                        
                        # If return type is 1, gun fires, kicked from channel
                        if type == 1:
                            self.kick(target,user,response)
                            #self.describe(target,'reloads and spins the cylinder.')
                        # Otherwise, gun goes "click" and user exhales in relief
                        else:
                            self.msg(target,response)
                    else:
                        self.msg(user,"Playing Russian roulette alone? We can help: www.sprc.org")
                        
                # Is command spin? This is to "spin the cylinder" of the channel's roulette gun.
                # Usage: !spin
                elif command == 'spin':
                    # We don't play roulette alone.
                    if target != user:
                        # If I don't have ops, then there's no point
                        if target not in self.opChans:
                            self.msg(target,'This channel does not acknowledge my second amendment rights to carry a firearm.')
                        else:
                            self.commands[channel].spin()
                            self.describe(target,'spins the cylinder of the revolver.')
                    else:
                        self.describe(target,'twirls around in circles.')
                        
                # Is command inventory? This is to display the current channel's inventory.
                # Usage: !inventory
                elif command == 'inventory':
                    # Inventory is a group activity!
                    if target != user:
                        contents = self.commands[channel].getInventory()
                        if contents == '':
                            self.msg(target,'Inventory is empty')
                        else:
                            self.msg(target,'Current inventory is: [%s]' % contents )
                    else:
                        self.msg(target,'I haz a flavor.')
                
                # Is command to learn a factoid?
                # Usage: !<on|add>[rand|kick] [trigger] </msg|/me> <response>
                # trigger is mandatory when [rand|kick] omitted
                elif re.match(r'^(on|add)(rand|kick)?\s*$',command,re.I):
                    # Split up command parameters, then sanitize the trigger by removing 
                    # punctuation and trailing/leading spaces
                    var = re.split(r'(\/me|\/msg)',args,re.I)
                    var[0] = var[0].translate(string.maketrans("",""),string.punctuation).strip()
                    for i in range(len(var)): var[i] = var[i].strip()
                    
		    usage = 'It\'s !<on|add>[kick|rand] [trigger] </msg|/me> <response>. Try again. Don\'t screw it up.'

		    # If no message type provided, yell at them
		    if len(var) < 2:
			acknowledgement = usage
			self.msg(target,acknowledgement)
			return

                    # Save type of response to be used in function call, return if invalid
                    if var[1] == '/msg': 
                        respType = 0 
                    elif var[1] == '/me': 
                        respType = 1
                    else:
                        acknowledgement = usage
                        self.msg(target,acknowledgement)
                        return                        
                        
                    # First, we want to make sure we're not being tricked into remembering common bot commands
                    if re.match(r'^[\!\@\.][A-Za-z0-9]',var[2],re.I) != None:
                        acknowledgement = 'I\'m not remembering potential bot commands.'
                    # If the response is clean, proceed
                    elif var[2] != '':
                        response = var[2].decode(sys.stdin.encoding)
                        trigger = var[0].decode(sys.stdin.encoding)
                    
                        # Attempt to remember a response to a kick
                        if 'kick' in command.lower():
                                acknowledgement = self.factoids.addFact(2,response,respType,user)   
                        # Attempt to remember a random 
                        elif 'rand' in command.lower():
                                acknowledgement = self.factoids.addFact(1,response,respType,user)   
                        # If kick and rand are not part of the command, let's first make sure the command 
                        # is 'on' or 'add', and that there is a valid response.
                        elif command.lower() not in ('on','add'):
                            acknowledgement = usage
                        # Attempt to remember a response to a triggering phrase
                        else:
                            # Forgot the trigger
                            '''if trigger == '':
                                acknowledgement = 'You forgot your trigger: !<on|add> <trigger> </msg|/me> '\
                                                  '<response>. Try again. Don\'t screw it up.'
			    elif len(trigger) < 6:
				acknowledgement = 'Your trigger is too short, but I\'m sure you hear that a lot. '\
						  '(Trigger must be >= 6 alphanumeric characters)'
                            else:'''
			    if trigger <> '' and len(trigger)>=6:
                                # Replaces bot's name with '$self' variable, so the bot's name does not effect the triggering
                                trigger = re.sub(G_BOTNAME,'$self',trigger,re.I)
                                acknowledgement = self.factoids.addFact(0,response,respType,user,trigger)  
                                # Change it back for acknowledgement, I'd rather it stay hidden to prevent inevitable confusion
                                acknowledgement = re.sub(r'$self',G_BOTNAME,acknowledgement,re.I)
                    else:
                        acknowledgement = usage
                    self.msg(target,acknowledgement)
                    
                # Is command forget? This removes a factoid from the database by ID number.
                # Usage: !<forget|baleet|delete> <id>
                elif command in ('forget','baleet','delete'):
                    # No secretly deleting factoids.
                    if target != channel:
                        self.msg('No.')
                    else:
                        acknowledgement = self.factoids.delFact(args,user)
                        self.msg(target,acknowledgement)

		#deal with this later
		elif command == 'forgetthat':
		    acknowledgement = self.factoids.delFact(str(self.lastFact[target]),user)
		    self.msg(target,acknowledgement)

                # Is command whatis? This looks up factoid detail by ID.
                # Usage: !whatis <id>
                elif command == 'whatis':
                    acknowledgement = self.factoids.findFact(args)
                    self.msg(target,acknowledgement)
                
                # Is command whatwasthat? This looks up the detail of the last triggered factoid
                # Usage: !<wtf|wth|whatwasthat>
                elif command in ('whatwasthat','wtf','wth'):
                    if target in self.lastFact and args == '':
                        acknowledgement = self.factoids.findFact(str(self.lastFact[target]))
                        self.msg(target,acknowledgement)

                # Is command help? This returns help info
                elif command in ('help','halp'):
                    if args == '':
                        self.msg(user,'Commands: wiki, wtf, whatis, forget, add, inventory, spin, pull, shutup, facts')
			self.msg(user,'Try !help <command> for more info.')
                    elif args == 'wiki':
                        self.msg(user,'!wiki [search term] : Returns the first paragraph of the wikipedia article for the '\
                                        'requested search term, if available. If search term omitted, returns a random '\
                                        'wikipedia article.')
                    elif args in ('whatwasthat','wtf','wth'):
                        self.msg(user,'!wtf : Returns details of the last factoid triggered.')
                    elif args in ('forget','baleet','delete'):
                        self.msg(user,'!forget <id> : Attempts to remove the factoid record denoted by its id number.')
		    elif args in ('modfact','modthat'):
			self.msg(user,'!modthat <s/pattern/repl> - mods last triggered response. !modfact <id> <s/pattern/repl> '\
				 	'- mods response by specified fact id')
		    elif args in ('shutup','shaddup','stfu'):
			self.msg(user,'!shutup [minutes] : Makes the bot shut up for however many minutes. Defaults to 5. '\
					'Max allowed is 20.')
                    elif args == 'inventory':
                        self.msg(user,'!inventory : Displays the inventory for the bot in a given channel.')
                    elif args in ('spin','pull'):
                        self.msg(user,'For the Russian Roulette game, !spin spins the cylinder, putting the bullet in a '\
                                        'random position. !pull pulls the trigger.')
		    elif args in ('facts','secrets'):
			self.msg(user,'!facts : Returns URL of factoid list')
                    elif args in ('on','onrand','onkick','add','addkick','addrand'):
                        self.msg(user,'To add a factoid triggered on a phrase: !on <trigger> </msg|/me> <response>. '\
					'Trigger must contain at least 6 alphanumeric characters.')
                        self.msg(user,'To add a randomly triggered factoid: !onrand </msg|/me> <response>')
                        self.msg(user,'To add a factoid triggered on someone being kicked: !onkick </msg|/me> <response>')
                        self.msg(user,'You may use the following variables in the response: $nick - the last user to speak '\
                                        'before the trigger, or triggering nick ; $rand - a random user from the channel '\
                                        'list ; $item - a random item from the bot\'s inventory (expends the inventory item).')

		# Is command to get list of factoids               
		elif command in ('secrets','facts'):
		    self.msg(target,self.factoids.getList())
	
		# Did someone think the bot was a little too chatty?
	 	elif command in ('shutup','shaddup','stfu') and not self.checkShutUp(target):
		    self.shutUp[channel][0] = True
		    self.shutUp[channel][1] = dt.now()
		    if re.match(r'^[0-9]+$',args,re.I):
			if int(args) <= 20:
			    self.shutUp[channel][2] = int(args)
			    acknowledgement = 'Ok, %s, I\'ll take a %s minute break.' % (user,args)
			else:
			    self.shutUp[channel][2] = 5
			    acknowledgement = 'I\'ll be quiet for 5 minutes instead'
			self.msg(target,acknowledgement)
		    elif args.strip() == '':
			self.shutUp[channel][2] = 5
			self.msg(target, 'Ok. I\'ll be back in a few minutes.')
	
		elif command in ('wiki','simple','mcwiki','ooo','trek','wookie','holocron'):
		    if args.strip() == '':
                        self.msg(target,wiki.wikiScrape(command,None,G_MESS_LIMIT))
                    else:
                        self.msg(target,wiki.wikiScrape(command,args,G_MESS_LIMIT))

		# Modify last triggered factoid
		# I'm sorry, but these modify commands are going to get weird.
		elif command == 'modthat':
		    errmsg = 'I\'m looking for "!modthat <s/pattern/replacement/>".'
		    cleanargs = re.sub(r'\\\/','<--F-->',args,0,re.I) # replace escaped forwardslashes so we can split
		    if cleanargs.strip().lower().startswith('s') and len(cleanargs.strip().split('/')) == 4:
			s,p,r,d = cleanargs.strip().split('/')

			# Put those slashes back in
			p = re.sub(r'\<\-\-F\-\-\>',r'\\/',p,0,re.I)
			r = re.sub(r'\<\-\-F\-\-\>',r'\\/',r,0,re.I)

			# They could have escaped a backslash! What do we do?
			# I'll tell you: replace \\ with <--B-->, then strip out all \, then replace <--B--> with \\
			r = re.sub(r'\\\\','<--B-->',r,0,re.I)
			r = re.sub(r'\\','',r,0,re.I)
			r = re.sub(r'\<\-\-B\-\-\>',r'\\\\',r,0,re.I) 

			self.msg(target,self.factoids.modfact(self.lastFact[target],p,r,user))
			
		    else:
			self.msg(target,errmsg)
		
		# Modify factoid by id
		elif command == 'modfact':
		    errmsg = 'I\'m looking for "!modfact <id> <s/pattern/replacement/>".'	
		    idnum,spc,args = args.strip().partition(' ')
		    cleanargs = re.sub(r'\\\/','<--F-->',args,0,re.I) # replace escaped forwardslashes so we can split
                    if cleanargs.strip().lower().startswith('s') and len(cleanargs.strip().split('/')) == 4 \
								 and idnum.strip() != '' \
								 and args.strip() != '':
                        s,p,r,d = cleanargs.strip().split('/')

                        # Put those slashes back in
                        p = re.sub(r'\<\-\-F\-\-\>',r'\\/',p,0,re.I)
                        r = re.sub(r'\<\-\-F\-\-\>',r'\\/',r,0,re.I)

                        # They could have escaped a backslash! What do we do?
                        # I'll tell you: replace \\ with <--B-->, then strip out all \, then replace <--B--> with \\
                        r = re.sub(r'\\\\','<--B-->',r,0,re.I)
                        r = re.sub(r'\\','',r,0,re.I)
                        r = re.sub(r'\<\-\-B\-\-\>',r'\\\\',r,0,re.I) 

                        self.msg(target,self.factoids.modfact(idnum,p,r,user))

                    else:
                        self.msg(target,errmsg)
		
                # Out of commands? Check for factoid trigger or roll the dice for a random factoid
                else:
                    self.triggerFactoids(user,target,0,msg)
            # Not a command? Check for factoid trigger or roll the dice for a random factoid
            else:
                self.triggerFactoids(user,target,0,msg)
    
    # Called to handle the possible triggering of factoids
    def triggerFactoids(self,user,target,factType,trigger=''):
        id = 0
    
	# You know what? No factoids in PM. So there. Also, see if we're to shut up.
	if target not in G_CHANNELS or self.checkShutUp(target):
	    return
        
	# Check for factoid triggered on a phrase
        if factType == 0 and not trigger.startswith('!'):
	    trigger = trigger.translate(string.maketrans("",""),string.punctuation)
	    trigger = re.sub(G_BOTNAME,'$self',trigger,re.I)
            id,responseType,response = self.factoids.react(factType,trigger.decode(sys.stdin.encoding))
        
	# If phrase did not trigger, or factoid expected is of different type
        if id == 0:
            # Check for on kick first, since it's the only other type which can be expected
            if factType == 2:
                id,responseType,response = self.factoids.react(factType)
            # Determine if random factoid will be triggered instead
            # Here, we get an lower bound by fetchin a random number between 1 and 100-G_RANDOMFREQUENCY
            # Then, we get a random number between 1 and 100 and see if it falls between lower bound 
            # and lower bound + G_RANDOMFREQUENCY. This preserves the % of liklihood while moving the 
            # target range, hopefully scattering distribution of random factoid triggerings
	    # This is overcomplicating things. I'll figure out something better later.
            else:
                lowerBound = random.randrange(100-G_RANDOMFREQUENCY)+1 
                upperBound = lowerBound + G_RANDOMFREQUENCY
                choice = random.randrange(100)+1
                if choice <= upperBound and choice >= lowerBound and self.lineCount[target] >= 5:
                    id,responseType,response = self.factoids.react(1)
	            self.lineCount[target] = 0
                    
        # If we have a factoid to response with
        if id != 0:
	    self.lastFact[target] = id

	    # Replace $rand, $nick, $item here 
	    for i in range(0,response.count('$rand')):
		randNick = self.nickList[target][random.randrange(len(self.nickList[target])-1)]
		response = response.replace('$rand',randNick,1)

	    response = response.replace('$nick',user)

	    for i in range(0,response.count('$item')):
	    	randItem = self.commands[target].getRandomItem()
		response = response.replace('$item',randItem.decode(sys.stdin.encoding),1)

	    response = response.replace('$self',G_BOTNAME)

            if responseType == 0:
                self.msg(target,response)
            else:
                self.describe(target,response)
     
    # Check shut up time
    def checkShutUp(self,channel):

	if channel not in self.shutUp:
	    return False
	if self.shutUp[channel][0]:
	    # Check if the time since being told to shut up exceeds duration
	    if ((dt.now()-self.shutUp[channel][1]).seconds)/60 >= self.shutUp[channel][2]:
		self.shutUp[channel][0] = False
		return False
	    else:
		return True
	return False
       
    # Called when any line is received
    def lineReceived(self, data):
        # Need IRCClient's implemented features
        irc.IRCClient.lineReceived(self, data)	
 
        # Readout on screen
        print data
 
        # Split up the line and see if it's the /NAMES response (353)
        # Example:
        # :barjavel.freenode.net 353 DickieTest @ #dtown2 :DickieTest Nick1 Nick2 Nick3 Nick4
        breakout = data.split(' ')
        code = breakout[1]
        if code == '353':
            channel = breakout[4]
	   
            # Partition data over ':BOTNAME ', since we don't want to be in nick list anyway
            leftSide, sep, nicks = data.partition(':'+G_BOTNAME+' ')
            
            # For each nick in the /names nick list, add it to the given channel's list,
            # stripping prefixes
            for nick in nicks.split(' '):
                self.nickList[channel].append(nick.lstrip('@').lstrip('+'))

	# Replacing the action function with the logic below because action treats the "\" character
	# as an escape key in raw text
	# Example:
	# :Dickie!~dickie@unaffiliated/dickie PRIVMSG #dtown :ACTION wiggles
	elif len(breakout) >= 5:
		if 'ACTION' in breakout[3]:
	    	    # Strips the message's pieces
		    user = breakout[0].split('!',1)[0].lstrip(':')
		    channel = breakout[2]
		    msg = ''
		    for x in breakout[4:]:
			msg = '%s%s ' % (msg,x)
		    msg = msg.strip()
 
	            # Check shut up time
	    	    self.checkShutUp(channel)
            
	            # Log the action
	            self.logger.log(channel,'%s: * %s %s' % (channel,user,msg))
	        
	            # Determine where replies to this message should go
	            if channel in G_CHANNELS: 	
			target = channel
			self.lineCount[channel] += 1
	            else: 
			target = user
	        
	            # Check for inventory command
		    pattern = re.compile(r'%s'%G_BOTNAME,re.I)
		    msg = re.sub(pattern,G_BOTNAME,msg,re.I).strip('\x01')
	            command,spc,args = msg.partition(' '+G_BOTNAME+' ')
	            command = command.lower()
		    theItem = args.rstrip('.').strip()
	        
	            if (command == 'gives' and
	                theItem != ''): 
	            
	                # Do not allow inventory by pm
	                if target == user or re.match(r'^[\!\@\.][A-Za-z0-9]',theItem,re.I) != None:
	                    response = 'throws %s back in %s\'s face.' % (theItem,user)
	                else:
	                    response = self.commands[channel].addToInventory(theItem)
	                self.describe(target,response)
       		        return
	            else:
	                self.triggerFactoids(user,target,0,msg)
 
    # Called when user is kicked from the channel    
    def userKicked(self, kickee, channel, kicker, message):
        # Log the kick
        self.logger.log(channel,'%s was kicked by %s: %s' % (kickee,kicker,message))
        
        # Remove the user from the channel list
        if kickee in self.nickList[channel]:
            self.nickList[channel].remove(kickee)
            
        self.triggerFactoids(kickee,channel,2,message)
    
    # Called when a user quits the server
    def userQuit(self,user,message):        
        # Since I don't know what channel the user was in, gotta loop
        for channel in G_CHANNELS:
            # Remove the user from the channel list
            if user in self.nickList[channel]:
                self.logger.log(channel,'%s has quit' % user)
                self.nickList[channel].remove(user)
    
    # Called when a user parts from a channel
    def userLeft(self,user,channel):
        # Log the part
        self.logger.log(channel,'%s left %s' % (user,channel))
        
        # Remove the user from the channel list
        if user in self.nickList[channel]:
            self.nickList[channel].remove(user)
    
    # Called when a user joins the channel
    def userJoined(self,user,channel):
        # Log the join
        self.logger.log(channel,'%s has joined %s' % (user,channel))
        
        # Add the user to the channel list
        if user not in self.nickList[channel]:
            self.nickList[channel].append(user)
           
    # Callen when a user changes nicks
    def userRenamed(self,oldname,newname):
	# No channel info, so loop through lists
	for channel in G_CHANNELS:
	    if oldname in self.nickList[channel]:
		self.nickList[channel].remove(oldname)
		self.nickList[channel].append(newname)
		self.logger.log(channel,'%s is not known as %s' % (oldname,newname)) 

    # Called when mode has changed on a user
    def modeChanged(self,user,channel,set,modes,args):
	if 'o' in modes:
            if set: self.opChans.append(channel)
            else: self.opChans.remove(channel)
        
    # Overwriting describe because it views the "\" key as an escape character in raw text
    def describe(self,channel,action):
        self.msg(channel, '\001ACTION %s\001' % action)

# Controls the creation and connectivity of our bot
class BotFactory(protocol.ClientFactory):
    protocol = MyIRCBot # Class of the IRC Protocol I will be using
    waitTime = 1        # Time to wait between reconnect attempts (sec)

    # If the connection drops, attempt to reconnect while resetting the wait time.
    def clientConnectionLost(self, connector, reason):
        self.waitTime = 1
        connector.connect()

    # If the connection fails, we will sleep for longer and longer until 
    # we get in or we give up. I just wanted to manage this myself.
    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason
        if self.waitTime > 1024:
            print 'Connection wait time exceeded. Shuttin\' \'er down, boss.'
            reactor.stop()
        else:
            self.waitTime = self.waitTime * 2
        time.sleep(self.waitTime)
        connector.connect()

if __name__ == '__main__':
    # Prompt for password in case bot is registered
    NICKPASS = getpass.getpass('Enter NickServ password for %s: ' % G_BOTNAME)

    # Create new factory
    factory = BotFactory()

    # Connect factory to the host and port
    reactor.connectTCP(G_HOST,G_PORT, factory)

    # Let's do this crazy thing!
    reactor.run()



