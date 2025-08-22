from storage.database import Database

trackedPlayersStructure = {
    "playerDiscriminators" : (set, str)
}

trackedPlayersName = "TrackedPlayers"

class TrackedPlayers(Database):
    def __init__(self):
        super().__init__(trackedPlayersName, trackedPlayersStructure)

    def getTracklist(self):
        return self._getItems("playerDiscriminators")
    
    def isTracked(self, discriminator):
        #Checks if this discriminator is stored
        trackedPlayers = self.getTracklist()
        if discriminator in trackedPlayers:
            return True
        return False

    def addTrackedPlayer(self, newPlayer):
        setOfDiscriminators = self._getItems("playerDiscriminators")
        try:
            if newPlayer["discriminator"] in setOfDiscriminators:
                return 0
            self._add("playerDiscriminators", newPlayer["discriminator"])
            return 1
        except:
            return -1
        
    def removeTrackedPlayer(self, startggDiscriminator):
        setOfDiscriminators = self._getItems("playerDiscriminators")
        if startggDiscriminator in setOfDiscriminators:
            self._remove("playerDiscriminators", startggDiscriminator)
        
    def getSetCheck(self):
        return self._getItems("playerDiscriminators")
    
    def loadTracklist(self):
        self._load_db()

    def saveTracklist(self):
        self._save_db()

