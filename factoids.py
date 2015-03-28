# -*- coding: utf-8 -*-
import sqlite3 as sql
import re
from time import localtime
from time import strftime

# I use this for string timestamps. My server is in the CST zone.
# Change this for yours if you are elsewhere, or figure this whole
# Python-timezone business out for yourself.
G_TIMEZONE = 'CST'

# Website containing list of factoids
G_PAGE = 'http://dtown.noip.me'

# This class handles all manipulation or access of the sqlite 
# database holding our factoid table
class factoidHandler():

    # Initialize the factoid handler, connecting to the database file given
    # and ensuring factoid table is present.
    def __init__(self,dbName):
        
        self.connection = sql.connect(dbName)
        self.cursor = self.connection.cursor()
        
        # Table consists of:
        #   idNumber     - Unique numeric key for each record
        #   factType     - 0: canned response to a triggering phrase
        #                  1: randomly triggered responses 
        #                  2: response to a user being kicked from the channel
        #   trig         - Triggering phrase for factoids of factType 0
        #   response     - message to be displayed in the channel
        #   responseType - 0: PRIVMSG
        #                  1: ACTION
        #   addedDate    - date record was added to the table (text)
        #   addedBy      - nick of user who added record
        #   lastCalled   - date record was last triggered (text)
        #   callCount    - number of times record has been triggered
        self.cursor.execute(\
            '''
            create table if not exists 
            facts ( idNumber integer primary key,
                    factType integer,
                    trig varchar(500),
                    response varchar(500),
                    responseType integer,
                    addedDate varchar(25),
                    addedBy varchar(50),
                    lastCalled varchar(25),
                    callCount integer )
            ''')

    # Returns website containing list of factoids
    def getList(self):
	return G_PAGE    

    # Function to return the first free id number in the factoids table, starting at 1
    def firstFreeID(self):
        firstFree = 0
        counter = 1
        
        # While we haven't found a free ID, loop
        while not firstFree:
            # Query table for record with ID == counter
            self.cursor.execute('''
                select * 
                from facts 
                where idNumber = ?
            ''', [counter])
        
            # If no record exists for ID == counter, use counter as free ID
            if self.cursor.fetchone() == None:
                firstFree = counter
            # Otherwise increment
            else:
                counter += 1
            
        return firstFree
        
    # After factoid is triggered, increment count and update last triggered date    
    def afterTriggered(self,id,count): 
        newCount = count + 1
        timestamp = strftime("%x %X",localtime()) + " %s" % (G_TIMEZONE)
        
        self.cursor.execute('''
            update facts
            set callCount = ?,
                lastCalled = ?
            where idNumber = ?
        ''',[newCount,timestamp,id])
        self.connection.commit()
        
    # Search table for given id
    def findFact(self,id):
        if re.match(r'^[0-9]+$',id,re.I):
            self.cursor.execute('''
                select * 
                from facts 
                where idNumber = ?
            ''', [id]) 
                
            result = self.cursor.fetchone()
            if result != None:
                # save column values, split up for readability
                idNumber,factType, trigger, response, responseType = result[:5]
                addedDate, addedBy, lastCalled, callCount = result[5:]
                
                # If response is PRIVMSG
                if responseType == 0:
                    responseText = '/msg'
                # If response is ACTION
                else: 
                    responseText = '/me'
                
                # If on trigger, send the following format
                if factType == 0:
                    response = 'ID %s: "%s" is "%s %s" Added [%s] by %s. Count: %s  Last: [%s]' %\
                        (id,trigger,responseText,response,addedDate,addedBy,callCount,lastCalled)
                # If randomly triggered, send the following format
                elif factType == 1:
                    response = 'ID %s: (random) "%s %s" Added [%s] by %s. Count: %s  Last: [%s]' %\
                        (id,responseText,response,addedDate,addedBy,callCount,lastCalled)
                # If triggered by a kick, send the following format
                else:
                    response = 'ID %s: (onKick) "%s %s" Added [%s] by %s. Count: %s  Last: [%s]' %\
                        (id,responseText,response,addedDate,addedBy,callCount,lastCalled)
            else:
                response = '¯\(°_o)/¯'
        else:
            response = '¯\(°_o)/¯'

	return response
        
    # Called to determine if factoid is known  
    def known(self,*args):
        found = False
    
        # Searching by id
        if len(args) == 1:
            self.cursor.execute('''
                select * 
                from facts 
                where idNumber = ?
            ''',args)
            if self.cursor.fetchone() == None:
                found = False
            else:
                found = True
        #searching by trigger and response
        else:
            self.cursor.execute('''
                select * 
                from facts 
                where trim(lower(trig)) = trim(lower(?)) 
                and   trim(lower(response)) = trim(lower(?))
            ''',args)
            if self.cursor.fetchone() == None:
                found = False
            else:
                found = True
        
        return found
    
    # Adds a record to the factoid table
    def addFact(self,factType,response,responseType,addedBy,trigger=''):
        newID = self.firstFreeID()
        timestamp = strftime("%x %X",localtime()) + " %s" % (G_TIMEZONE)
        acknowledgement = ''
        
        # Row to add to table, fields in table column order, count 0 and last trigger time blank
        insertList = [newID,factType,trigger,response,responseType,timestamp,addedBy,'',0]
        
        # Check if the factoid is already known
	if len(response)>512 or len(trigger)>512:
	    acknowledgement = 'As your mother said last night, "That''s too long."'
        elif not self.known(trigger,response):
            self.cursor.execute('''
                insert into facts
                values(?,?,?,?,?,?,?,?,?)
            ''',insertList)
            self.connection.commit()
            
            # If response is PRIVMSG
            if responseType == 0:
                responseText = '/msg'
            # If response is ACTION
            else: 
                responseText = '/me'
            
            # If on trigger, send the following acknowledgement
            if factType == 0:
                acknowledgement = 'Ok, %s: %s is "%s %s". ID:%d' % (addedBy,trigger,responseText,response,newID)
            # If randomly triggered, send the following acknowledgement
            elif factType == 1:
                acknowledgement = 'Ok, %s: I\'ll randomly "%s %s". ID:%d' % (addedBy,responseText,response,newID)
            # If triggered by a kick, send the following acknowledgement
            else:
                acknowledgement = 'Ok, %s: On a kick, I\'ll "%s %s". ID:%d' % (addedBy,responseText,response,newID)
        else:
            acknowledgement = 'Oh, I already know that.'
            
        return acknowledgement
    
    # Delete a record from the factoid table
    def delFact(self,id,user):
        acknowledgement = ''
    
        if self.known(id) and re.match(r'^[0-9]+$',id,re.I):
            # Fetch row to delete for acknowledgement
            self.cursor.execute('''
                select * 
                from facts
                where idNumber = ?
            ''',[id])
            result = self.cursor.fetchone()
            if result == None:
                return('I don\'t know that one.')
            
            # Delete row
            self.cursor.execute('''
                delete 
                from facts
                where idNumber = ?
            ''',[id])
            self.connection.commit()
            
            # save old values, split up for readability
            idNumber,factType, trigger, response, responseType = result[:5]
            addedDate, addedBy, lastCalled, callCount = result[5:]
            
            # If response is PRIVMSG
            if responseType == 0:
                responseText = '/msg'
            # If response is ACTION
            else: 
                responseText = '/me'
            
            # If deleting fact on trigger, send the following acknowledgement
            if factType == 0:
                acknowledgement = '%s deleted ID %s: "%s" is "%s %s" Created: [%s] by %s. Count: %s' % \
                (user,idNumber,trigger,responseText,response,addedDate,addedBy,callCount)
            # If deleting randomly triggered fact, send the following acknowledgement
            elif factType == 1:
                acknowledgement = '%s deleted ID %s: (random) "%s %s" Created: [%s] by %s. Count: %s' % \
                (user,idNumber,responseText,response,addedDate,addedBy,callCount)
            # If deleting fact triggered by a kick, send the following acknowledgement
            else:
                acknowledgement = '%s deleted ID %s: (onKick) "%s %s" Created: [%s] by %s. Count: %s' % \
                (user,idNumber,responseText,response,addedDate,addedBy,callCount)
            
        else:
            acknowledgement = '¯\(°_o)/¯'
            
        return acknowledgement
            
    # Function to react to a trigger, be it phrase (0), random chance(1), or a kick(2)
    def react(self,*args):
        factType = args[0]
	if len(args) > 1:
            trigger = args[1].strip('\x01')
        
        idNumber = callCount = 0 
        responseType = response = ''
        
        # If triggered on phrase, include trigger in query
        if factType == 0:
            self.cursor.execute('''
                select idNumber,callCount,responseType,response
                from facts
                where factType = ? 
                and trim(lower(trig)) = trim(lower(?))
                order by random()
                limit 1
            ''',[factType,trigger])
        # If triggered on kick or random, merely query by factType
        else:
            self.cursor.execute('''
                select idNumber,callCount,responseType,response
                from facts
                where factType = ? 
                order by random()
                limit 1
            ''',[factType])
            
        result = self.cursor.fetchone()
        if result != None:
            idNumber,callCount,responseType,response = result
       
        self.afterTriggered(idNumber,callCount)
        
        return (idNumber,responseType,response)

    # Modify existing factoids
    def modfact(self,id,p,r,user):
	timestamp = strftime("%x %X",localtime()) + " %s" % (G_TIMEZONE)
	self.cursor.execute('''
	select response
	from facts
	where idNumber = ?
	''',[id])
	result = self.cursor.fetchone()
	    
	if result != None:
	    old = result[0]

	    if re.search(r'%s'%p,old,re.I) == None:
		acknowledgement = 'No match found on that regex.'
	    else:
	    	new = re.sub(ur'%s'%p,ur'%s'%r,old,0,re.I|re.U)
	
		if new.startswith('!') or len(new)>=512:
		    acknowledgement = 'NOPE'
		else:	
	    	    self.cursor.execute('''
	    	    update facts
	    	    set response = trim(?),
	    	    addedBy = trim(?),
	    	    addedDate = ? 
	    	    where idNumber = ?
	    	    ''',[new,user,timestamp,id])
	
	    	    self.connection.commit()

	    	    acknowledgement = 'Successfully changed [%s] "%s" to "%s"' % (id,old,new)	
	else: 
	    acknowledgement = '¯\(°_o)/¯'		    	

	return(acknowledgement)
