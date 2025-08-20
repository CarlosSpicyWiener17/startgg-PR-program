from storage.database import Database

trackedPlayersStructure = {
    "players" : (list, dict),
    "playerDiscriminators" : (set, str)
}

class TrackedPlayers(Database):
    def __init__(self):
        super().__init__("TrackedPlayers", trackedPlayersStructure)

    def getTracklist(self):
        return self._getItems("players")
    
    def addTrackedPlayer(self, newPlayer):
        setOfDiscriminators = self._getItems("playerDiscriminators")
        if newPlayer["discriminator"] in setOfDiscriminators:
            for i, player in enumerate(self.activeDatabase["players"]):
                try:
                    if newPlayer["discriminator"] == player["discriminator"]:
                        self.activeDatabase["players"][i] = newPlayer
                        return 0
                except:
                    return -1
        try:
            self._add("players", newPlayer)
            return 1
        except:
            return -1
        
    def removeTrackedPlayer(self, startggDiscriminator):
        setOfDiscriminators = self._getItems("playerDiscriminators")
        if startggDiscriminator in setOfDiscriminators:
            self._removeDict("players", "discriminator", startggDiscriminator)
        
    def getSetCheck(self):
        return self._getItems("playerDiscriminators")
    
    def loadTracklist(self):
        self._load_db()

    def saveTracklist(self):
        self._save_db()

