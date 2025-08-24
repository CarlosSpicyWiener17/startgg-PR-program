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


    def getPlayers(self, discriminators = None):
        if discriminators is None:
            return self.activeDatabase["players"]
        else:
            players = []
            for discriminator in discriminators:
                print(discriminator)
                success, gotPlayer = self.getPlayerFromDiscriminator(discriminator)
                if success:
                    print("suc")
                    players.append(gotPlayer)
        return players

    def getPlayerFromDiscriminator(self, discriminator):
        #Get player from startgg discriminator
        if self.playerStored(discriminator):
            print("1")
            for player in self.getPlayers():
                print("2")
                if player["discriminator"] == discriminator:
                    print("3")
                    return True, player
        print("NOT A SUCC")
        return False, None

    def addPlayer(self, newPlayer, entrant):
        """
        Add player to database, return status:\n
            1   : Player added
            0   : Player updated
            -1  : Error
        """
        status = self._addPlayer(newPlayer, entrant)
        if status == 0:
            if entrant:
                self._updatePlayer(newPlayer)
        return status

    def _addPlayer(self, newPlayer, entrant : bool):
        setOfDiscriminators = self._getItems("playerDiscriminators")
        try:
            if newPlayer["discriminator"] in setOfDiscriminators:
                return 0
            print("tourneyinfo")
            if entrant:
                tournamentInfo = {
                    "entrantId" : newPlayer["entrantId"],
                    "tournamentId" : newPlayer["tournamentId"],
                    "placement" : newPlayer["placement"] 
                }
                print("playfilter")
                newPlayerFiltered = {
                    "name" : newPlayer["name"],
                    "userId" : newPlayer["userId"],
                    "discriminator" : newPlayer["discriminator"],
                    "link" : newPlayer["link"],
                    "tournaments" : [tournamentInfo],
                    "setOfEntrantIds" : {tournamentInfo["entrantId"]}
                }
            else:
                newPlayerFiltered = {
                    "name" : newPlayer["name"],
                    "userId" : newPlayer["userId"],
                    "discriminator" : newPlayer["discriminator"],
                    "link" : newPlayer["link"],
                    "tournaments" : [],
                    "setOfEntrantIds" : set()
                }
            self._add("players", newPlayerFiltered)
            self._add("playerDiscriminators",newPlayer["discriminator"])
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

