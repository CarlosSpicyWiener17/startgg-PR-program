from storage.database import Database

trackedPlayersStructure = {
    "playerDiscriminators" : (set, str)
}

trackedPlayersName = "TrackedPlayers"

class TrackedPlayers(Database):
    def __init__(self, logger, userDir):
        super().__init__(trackedPlayersName, trackedPlayersStructure, logger, userDir)

    def getTracklist(self):
        return self.get("playerDiscriminators")
    
    def isTracked(self, discriminator):
        #Checks if this discriminator is stored
        setOfDiscriminators = self.get("playerDiscriminators")
        if discriminator in setOfDiscriminators:
            return True
        return False

    def addTrackedPlayer(self, newPlayer):
        setOfDiscriminators = self.get("playerDiscriminators")
        try:
            if newPlayer["discriminator"] in setOfDiscriminators:
                return 0
            self.add("playerDiscriminators", newPlayer["discriminator"])
            return 1
        except:
            return -1
        
    def removeTrackedPlayer(self, startggDiscriminator):
        setOfDiscriminators = self.get("playerDiscriminators")
        if startggDiscriminator in setOfDiscriminators:
            self.activeDatabase["playerDiscriminators"].remove(startggDiscriminator)
    
    def loadTracklist(self):
        self._load_db()
        print(self.activeDatabase)

    def saveTracklist(self):
        self._save_db()

