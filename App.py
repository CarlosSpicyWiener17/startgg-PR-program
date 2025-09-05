import threading as t
from startggModules.startggInterface import startggInterface
from excel import Exporter
import webbrowser
from UI import UI
from time import sleep
import logging
from platformdirs import user_data_dir, user_documents_dir
import os
import queue

appName = "WienerPR"
appAuthor = "CarlosSpicyWiener"


global logger

logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)

error_handler = logging.FileHandler(os.path.join(os.path.join(user_documents_dir(), "Wiener Exports"),"error.log"))
error_handler.setLevel(logging.ERROR)
error_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
error_handler.setFormatter(error_format)

info_handler = logging.FileHandler(os.path.join(os.path.join(user_documents_dir(), "Wiener Exports"),"info.log"))
info_handler.setLevel(logging.INFO)
info_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
info_handler.setFormatter(info_format)

logger.addHandler(error_handler)
logger.addHandler(info_handler)

class App:
    def __init__(self):
        self.logger = logger
        self.queue = queue.Queue()
        self.docuDir = os.path.join(user_documents_dir(), "Wiener Exports")
        os.makedirs(self.docuDir, exist_ok=True)
        self._setupLocks()
        self._setupInfopoints()
        self.startgg = startggInterface(self, self.docuDir)
        self.UI = UI(self)
        self.writer = Exporter(self, self.docuDir)
        tracklist = self.startgg.trackedPlayers.getTracklist()
        """
        for disc in tracklist:
            self.startgg.enterPlayerForce(disc)"""
        self.tracklistInfo = self.startgg.playerList.getPlayers(tracklist)
        playersNow = self.startgg.playerList.getPlayers()
        print("How many players: ", len(playersNow))
        self.tournamentsInfo = self.startgg.events.getEvents()
        self.UI.createTracklist()
        self.UI.createTournaments()
        self.UI.window.after(100, self.checkQueue)

    def processQueue(self):
        try:
            while True:
                msg, data = self.queue.get_nowait()
                try:
                    if msg == "addSingleEvent":
                        self.UI._getTournaments()
                        self._updateTournaments()
                    elif msg == "removedEvent":
                        self.UI._getTournaments()
                        self._updateTournaments()
                    elif msg == "removeTracked":
                        self.startgg.getTrackedPlayers()  
                        self.updateTracklist()
                    elif msg == "getTournaments":
                        self.tournamentsInfo = data
                        self._updateTournaments()
                    elif msg == "status":
                        self.st(data)
                    elif msg == "error":
                        self.logger.error(data)
                except:
                    pass
                self.queue.task_done()
        except queue.Empty:
            pass

    def checkQueue(self):
        self.processQueue()
        self.UI.window.after(100, self.checkQueue)

    def getPlayer(self, disc):
        return self.startgg.playerList.getPlayer(disc)

    def getCompetitors(self):
        tracklist = self.startgg.trackedPlayers.getTracklist()
        for player in self.startgg.playerList.activeDatabase["players"]:
            if player["discriminator"] in tracklist:
                yield player

    def reRank(self):
        t.Thread(target=self.startgg.reRankTournaments).start()

    def updateTopCut(self, discriminator, yOn):
        t.Thread(target= lambda: self.startgg.toggleTopCut(discriminator, yOn == 1)).start()

    def addEvent(self, entryfield):
        self.st("Adding single event...")
        slug = None
        try:
            link : str = entryfield.get()
            slugStart = link.find("tournament/")
            if slugStart != -1:
                nameEnd = link.find("/",slugStart+11)
                eventEnd = link.find("/event/")
                slugEnd = link.find("/", eventEnd+7)
                if slugEnd == -1:
                    slug=link[slugStart:]
                else:
                    slug=link[slugStart:slugEnd]
            
        except:
            self.st(f"Error with processing link: {entryfield.get()}")
            return
    
        t.Thread(target = lambda: self.startgg.addEvent(slug), daemon=True).start()
        
        

    def start(self):
        logger.info("Starting UI")
        self.UI.start()

    def exit(self):
        self.startgg.save()

    def getTracklist(self):
        print("hey")
        tlist = self.startgg.trackedPlayers.getTracklist()
        print("tlist is ", tlist)
        return tlist

    def getValidTournaments(self):
        tracklist = self.startgg.trackedPlayers.getTracklist()
        allCounting = [tournament for tournament in self.tournamentsInfo if tournament["counting"]]

        self.startgg.fillEventSets(allCounting, tracklist)
        return allCounting

    def trackPlayer(self, discriminator):
        with self.databaseLock:
            self.UI.status.set("Tracking player...")

            status = self.startgg.enterPlayer(discriminator)
            if status == -1:
                self.st(f"Error, couldnt track discriminator")
            elif status == 0:
                self.st(f"Already tracked")
            elif status == 1:
                self.st(f"Successfully tracked new player")
            self.startgg.getTrackedPlayers()    
            self.updateTracklist()
            self.UI.status.set("Player tracked")
        return status

    def untrackPlayer(self, discriminator):
        self.st("Untracking player")
        t.Thread(target=lambda: self.startgg.removeTrackedPlayer(discriminator)).start()

    def updateCounting(self, id, countingVar):
        #Turn counting integer into bool
        t.Thread(target= lambda: self.startgg.toggleTournamentCounts(id, countingVar.get()==1)).start()

    def st(self, msg):
        self.UI.status.set(msg)

    def updateTournamentTier(self, newTier, tournamentId):
        self.st("Updating tournament tier")
        t.Thread(target= lambda: self.startgg.updateTournamentTier(newTier, tournamentId)).start()

    def openLink(self,link):
        webbrowser.open(link,2,True)

    def getTournaments(self, s, e):
        self.queue.put(("status","Getting Tournaments"))

        t.Thread(target=lambda: self.startgg.getTournaments(s,e), daemon=False).start()

    def export(self, entryField):
        self.UI.status.set("Exporting...")
        t.Thread(target= lambda:self.writer.export(entryField.get())).start()
        
    def deleteTournament(self, tourneyId):
        t.Thread(target= lambda: self.startgg.removeEvent(tourneyId)).start()

    def getTracklist(self):
        self.startgg.getTrackedPlayers()

    def getTrackedDiscriminators(self):
        return self.startgg.trackedPlayers.getTracklist()

    def updateTracklist(self):
        
        self.UI.createTracklist()
        

    
    def _setupLocks(self):
        self.startggLock = t.Lock()
        self.systemLock = t.Lock()
        self.databaseLock = t.Lock()
        self.writerLock = t.Lock()
    
    def _updateTournaments(self):
        self.UI.createTournaments()
        self.UI.status.set("Tournaments ready for export")

    def _setupInfopoints(self):
        self.tournamentsInfo = []
        self.tracklistInfo = []