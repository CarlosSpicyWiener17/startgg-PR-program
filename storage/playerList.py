import gzip
from pickle import load, dump
import os
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


class AllPlayers:
    def __init__(self, logger, userDir):
        self.name = playerDatabaseName
        self.logger = logger
        self.file_path = os.path.join(userDir, self.name+".pkl")

    def getPlayers(self, discriminators = None):
        if discriminators is None:
            return self.activeDatabase["players"]
        else:
            print("Getting players")
            return [player for player in self.activeDatabase["players"] if player["discriminator"] in discriminators]

    def toggleTopCut(self, playerDiscriminator, isTopCut):

        for player in self.activeDatabase["players"]:
            if player["discriminator"] == playerDiscriminator:
                player["topCut"] = isTopCut
                break

    def getPlayerFromEntrant(self, entrantId):
        fittingPlayers = [player for player in self.activeDatabase["players"] if entrantId in player["setOfEntrantIds"]]
        if len(fittingPlayers) > 0:
            return fittingPlayers[0]
        else:
            return None

    def getPlayer(self, discriminator):
        try:
            fittingPlayers = [player for player in self.activeDatabase["players"] if player["discriminator"] == discriminator]
            if len(fittingPlayers) > 0:
                return fittingPlayers[0]
            else:
                return None
        except:
            print("unknown error pls")

    def addPlayers(self, newPlayers):
        """
        Add several tournaments to player database
        """
        #pip install pysmashgg platformdirs customtkinter tkcalendar xlsxwriter pyinstaller
        #altgraph, xlsxwriter, urllib3, setuptools, pywin32-ctypes, platformdirs, pefile, packaging, idna, darkdetect, charset_normalizer, certifi, babel, tkcalendar, requests, pyinstaller-hooks-contrib, customtkinter, pysmashgg, pyinstaller
        for player in newPlayers:
            try:
                self.activeDatabase["playerDiscriminators"].add(player["discriminator"])
                oldPlayer = self.getPlayer(player["discriminator"])
                if not oldPlayer is None:
                    oldPlayer["name"] = player["name"]
                    for tournament in player["tournaments"]:
                        if not tournament["entrantId"] in oldPlayer["setOfEntrantIds"]:
                            oldPlayer["tournaments"].append(tournament)
                            oldPlayer["setOfEntrantIds"].add(tournament["entrantId"])
                    oldPlayer["topCut"] = player["topCut"] 
                else:
                    self.addPlayer(player)
            except:
                self.logger.error(f"Couldnt add or update player to database: {player["name"]}\nLink: {player["link"]}")

    def addPlayer(self, player):
        self.activeDatabase["players"].append(player)
        self.activeDatabase["playerDiscriminators"].add(player["discriminator"])



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
        try:
            if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                with gzip.open(self.file_path, "rb") as databaseFile:
                    self.activeDatabase = load(databaseFile)   
                    databaseFile.close()
            else:
                self.activeDatabase = {
                    "players" : [],
                    "playerDiscriminators" : set()
                }
        except:
            self.activeDatabase = {
                    "players" : [],
                    "playerDiscriminators" : set()
                }
            self.logger.error(f"Some error with saving in {self.name} database", exc_info=True)

    def savePlayers(self):
        """
        Saves the database to file
        """
        try:
            with gzip.open(self.file_path, "wb") as databaseFile:
                dump(self.activeDatabase,databaseFile)   
                databaseFile.close()
        except:
            self.logger.error(f"Some error with saving in {self.name} database", exc_info=True)

