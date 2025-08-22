from storage.database import Database

playerTournamentsStructure = {
    "entrantId" : (None, int),
    "tournamentId" : (None, int),
    "placement" : (None, int)
}

playerStructure = {
    "name" : (None, str),
    "discriminator" : (None, str),
    "link" : (None, str),
    "tournaments" : (list, dict),
    "setOfEntrantIds" : (set, int),
    "userId" : (None, int)
}

allPlayersStructure = {
    "players" : (list, dict),
    "playerDiscriminators" : (set, str)
}

playerDatabaseName = "AllPlayers"

class AllPlayers(Database):
    def __init__(self):
        super().__init__(playerDatabaseName, allPlayersStructure)

    def _updatePlayer(self, newPlayer):
        tournamentInfo = {
            "entrantId" : newPlayer["entrantId"],
            "tournamentId" : newPlayer["tournamentId"],
            "placement" : newPlayer["placement"] 
        }
        self._appendToItemKey("players", "discriminator", newPlayer["discriminator"], ["tournaments"], tournamentInfo)
        self._appendToItemKey("players", "discriminator", newPlayer["discriminator"], ["setOfEntrantIds"], tournamentInfo["entrantId"])

    def getPlayers(self):
        return self.activeDatabase["players"]

    def getPlayerFromDiscriminator(self, discriminator):
        #Get player from startgg discriminator
        if self.playerStored(discriminator):
            for player in self.getPlayers():
                if player["discriminator"] == discriminator:
                    return True, player
        return False, None

    def addPlayer(self, newPlayer):
        """
        Add player to database, return status:\n
            1   : Player added
            0   : Player updated
            -1  : Error
        """
        status = self._addPlayer(newPlayer)
        if status == 0:
            self._updatePlayer(newPlayer)
        return status

    def _addPlayer(self, newPlayer):
        setOfDiscriminators = self._getItems("playerDiscriminators")
        try:
            if newPlayer["discriminator"] in setOfDiscriminators:
                return 0
            tournamentInfo = {
                "entrantId" : newPlayer["entrantId"],
                "tournamentId" : newPlayer["tournamentId"],
                "placement" : newPlayer["placement"] 
            }
            newPlayerFiltered = {
                "name" : newPlayer["name"],
                "userId" : newPlayer["userId"],
                "discriminator" : ["discriminator"],
                "link" : newPlayer["link"],
                "tournaments" : [tournamentInfo],
                "setOfEntrantIds" : {tournamentInfo["entrantId"]}
            }
            self._add("players", newPlayerFiltered)
            return 1
        except:
            return -1
        
    def removePlayer(self, startggDiscriminator):
        setOfDiscriminators = self._getItems("playerDiscriminators")
        if startggDiscriminator in setOfDiscriminators:
            self._removeDict("players", "discriminator", startggDiscriminator)
        
    def getSetCheck(self):
        return self._getItems("playerDiscriminators")
    
    def playerStored(self, discriminator):
        savedPlayers = self._getItems("playerDiscriminators")
        if discriminator in savedPlayers:
            return True
        return False

    def loadPlayers(self):
        self._load_db()

    def savePlayers(self):
        self._save_db()

