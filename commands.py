import random

class commandHandler(object):
    # Dictionary of lists for channel guns and trigger pull count
    rouletteGun = 0
    rouletteCount = 0
    
    # Dictionary of lists for channel inventories
    inventory = []
    
    def __init__(self):
        
        # initialize a loaded 6-chambered gun with one bullet
        # and an empty inventory. 
        # randrange(x) chooses a number between 0 and x-1.
        rouletteGun = random.randrange(6)+1
        rouletteCount = 0
        inventory =  []
     
    # Returns a list of inventory items
    def getInventory(self):
        response = ''
        
        # Create list of inventory items separated by commas
        if len(self.inventory) >= 1:
            for item in self.inventory:
                response = response + '%s, ' % (item.strip())
        else:
            response = ''
        
        return response.rstrip(', ')
     
    # Pops an inventory item out of the list and returns it
    def getRandomItem(self):
        item = ''
        invSize = len(self.inventory)
        
        if invSize >= 1:
            item = self.inventory.pop(random.randrange(invSize))
        else:
            item = 'nothing'
        
        return item
     
    # Adds a given item to the inventory
    # Responses are intended to be ACTIONs
    def addToInventory(self,item):
	item = item.strip()
        # No blank items, plz
        if item == '':
            return 'does nothing.'
   
	# Already have that
	if item in self.inventory:
	    return 'already has that.'
 
        # add item to inventory
        self.inventory.append(item)
        
        # DickieBot can only carry 10 things per channel, so if at capacity, drop the first item
        if len(self.inventory) >= 10:
            msg = 'drops %s and adds %s to his inventory.' % (self.inventory.pop(0),item)
        else:
            msg = 'adds %s to his inventory.' % (item)
        
        return(msg)
     
    # Pulls the trigger on the revolver
    def pull(self):
        self.rouletteCount += 1
        # If we match (or somehow go over) bullet location, blast them
        if self.rouletteCount >= self.rouletteGun:
            self.rouletteGun = random.randrange(6)+1
            self.rouletteCount = 0
            return(1,'BANG!')
        else:
            return(0,'*click*')
        
    # Spins the cylinder of the revolver, placing the bullet in a new
    # location and resetting the count
    def spin(self):
        self.rouletteGun = random.randrange(6)+1
        self.rouletteCount = 0
