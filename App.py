import threading as t
from startggModules.startggInterface import startggInterface
from excel import Exporter
import webbrowser
from UI import UI
from time import sleep

class App:
    def __init__(self):
        self._setupLocks()
        self._setupInfopoints()
        self.UI = UI(self)
        self.startgg = startggInterface(self)
        self.writer = Exporter(self)
        tracklist = self.startgg.trackedPlayers.getTracklist()
        print(tracklist)
        self.tracklistInfo = self.startgg.playerList.getPlayers(tracklist)
        print(self.tracklistInfo)
        self.tournamentsInfo = self.startgg.events.getEvents()
        self.UI.createTracklist()

    def start(self):
        self.UI.start()

    def exit(self):
        self.startgg.save()

    def trackPlayer(self, discriminator):
        status = self.startgg.enterPlayer(discriminator)
        self.startgg.getTrackedPlayers()    
        self.updateTracklist()
        return status

    def untrackPlayer(self, discriminator):
        self.startgg.trackedPlayers.removeTrackedPlayer(discriminator)
        self.startgg.getTrackedPlayers()
        self.updateTracklist()

    def updateCounting(self, id, counting):
        #Turn counting integer into bool
        self.startgg.events.updateCounting(id, counting==1)

    def updateTournamentTier(self, newTier, tournamentId):
        self.startgg.events.updateTournamentTier(newTier, tournamentId)

    def openLink(self,link):
        webbrowser.open(link,2,True)

    def getTournaments(self, s, e):
        t.Thread(target=lambda: self.startgg.getTournaments(s,e), daemon=False).start()

    def export(self, entryField):
        self.writer.export(entryField.get())

    def getTracklist(self):
        self.startgg.getTrackedPlayers()

    def updateTracklist(self):
        self.UI.createTracklist()

    
    def _setupLocks(self):
        self.startggLock = t.Lock()
        self.systemLock = t.Lock()
        self.databaseLock = t.Lock()
    
    def _updateTournaments(self):
        self.UI.createTournaments()

    def _setupInfopoints(self):
        self.tournamentsInfo = []
        self.tracklistInfo = []