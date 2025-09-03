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
    "id" : (None, int),
    "topCut" : (None, bool)
}

allPlayersStructure = {
    "players" : (list, playerStructure),
    "playerDiscriminators" : (set, str)
}

playerDatabaseName = "AllPlayers"


class AllPlayers(Database):
    def __init__(self, logger, userDir):
        super().__init__(playerDatabaseName, allPlayersStructure, logger, userDir)

    def getPlayers(self, discriminators = None):
        if discriminators is None:
            return self.get("players")
        else:
            print("Getting players")
            return self.get("players", lambda player: player["discriminator"] in discriminators)

    def toggleTopCut(self, playerDiscriminator, isTopCut):
        players = self.get("players")
        newPlayer = None
        for i, player in enumerate(players):
            if player["discriminator"] == playerDiscriminator:
                newPlayer = player
                newPlayer["topCut"] = isTopCut
                print("Player:\n", player, "\nNewplayer:\n", newPlayer)
                break
        if not newPlayer is None:
            players.pop(i)
            players.append(newPlayer)
            print("new playerlist")
        self.activeDatabase["players"] = players

    def getPlayerFromEntrant(self, entrantId):
        players = self.get("players", lambda player: entrantId in player["setOfEntrantIds"])
        if players != []:
            return players[0]

    def getPlayer(self, discriminator):
        try:

            players = self.get("players", lambda player: player["discriminator"] == discriminator)

            if len(players) > 0:
                return players[0]
            else:
                return None
        except:
            print("unknown error pls")

    def addPlayer(self, newPlayer):
        """
        Add player to database, return status:\n
            1   : Player added
            0   : Player updated
            -1  : Error
        """
        self.add("players", newPlayer)

    def addPlayers(self, newPlayers):
        """
        Add player to database, return status:\n
            1   : Player added
            0   : Player updated
            -1  : Error
        """

        for player in newPlayers:
            oldPlayer = self.getPlayer(player["discriminator"])
            if not oldPlayer is None:
                for tournament in player["tournaments"]:
                    if not tournament in oldPlayer["tournaments"]:
                        oldPlayer["tournaments"].append(tournament)
                oldPlayer["setOfEntrantIds"].update(player["setOfEntrantIds"])
            else:
                self.addPlayer(player)
        print("Added all yay")



    def removePlayer(self, startggDiscriminator):
        setOfDiscriminators = self.get("playerDiscriminators")
        if startggDiscriminator in setOfDiscriminators:
            players = self.get("players")
            for player in players:
                if player["discriminator"] == startggDiscriminator:
                    self.remove("players", player)
                    self.remove("playerDiscriminators", startggDiscriminator)
                    break
        
    def getSetCheck(self):
        return self.get("playerDiscriminators")
    
    def playerStored(self, discriminator):
        savedPlayers = self.get("playerDiscriminators")
        if discriminator in savedPlayers:
            return True
        return False

    def loadPlayers(self):
        self._load_db()

    def savePlayers(self):
        self._save_db()

