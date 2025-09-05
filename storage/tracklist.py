from pickle import load, dump
import gzip
import os
trackedPlayersStructure = {
    "playerDiscriminators" : (set, str)
}

trackedPlayersName = "TrackedPlayers"

class TrackedPlayers:
    def __init__(self, logger, userDir):
        self.name = trackedPlayersName
        self.file_path = os.path.join(userDir, self.name+".pkl")
        self.logger = logger
        
    def getTracklist(self) -> set:
        return self.activeDatabase["playerDiscriminators"]
    
    def isTracked(self, discriminator):
        #Checks if this discriminator is stored
        if discriminator in self.activeDatabase["playerDiscriminators"]:
            return True
        return False

    def addTrackedPlayer(self, newPlayer):

        try:
            if newPlayer["discriminator"] in self.activeDatabase["playerDiscriminators"]:
                return 0
            self.activeDatabase["playerDiscriminators"].add(newPlayer["discriminator"])
            return 1
        except:
            return -1
        
    def removeTrackedPlayer(self, startggDiscriminator):
        if startggDiscriminator in self.activeDatabase["playerDiscriminators"]:
            self.activeDatabase["playerDiscriminators"].remove(startggDiscriminator)
    
    def loadTracklist(self):
        try:
            if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                with gzip.open(self.file_path, "rb") as databaseFile:
                    self.activeDatabase = load(databaseFile)   
                    databaseFile.close()
            else:
                self.activeDatabase = {
                    "playerDiscriminators" : set()
                }
        except:
            self.activeDatabase = {
                    "playerDiscriminators" : set()
                }
            self.logger.error(f"Some error with saving in {self.name} database", exc_info=True)

    def saveTracklist(self):
        """
        Saves the database to file
        """
        try:
            with gzip.open(self.file_path, "wb") as databaseFile:
                dump(self.activeDatabase,databaseFile)   
                databaseFile.close()
        except:
            self.logger.error(f"Some error with saving in {self.name} database", exc_info=True)

