import threading as t
from startggModules.startggInterface import startggInterface
import webbrowser
from UI import UI
from time import sleep

class App:
    def __init__(self):
        self._setupLocks()
        self._setupInfopoints()
        self.UI = UI(self)
        self.startgg = startggInterface(self)

    def start(self):
        self.UI.start()

    def _setupLocks(self):
        self.startggLock = t.Lock()
        self.systemLock = t.Lock()
        self.databaseLock = t.Lock()

    def exit(self):
        self.startgg.save()

    def _setupInfopoints(self):
        self.tournamentsInfo = []

    def updateTournamentTier(self, newTier, tournamentId):
        self.startgg.events.updateTournamentTier(newTier, tournamentId)

    def _updateTournaments(self):
        self.UI.createTournaments()

    def openLink(self,link):
        webbrowser.open(link,2,True)

    def updateCounting(self, id, counting):

        self.startgg.updateCounting(id, counting==1)

    def getTournaments(self, s, e):
        t.Thread(target=lambda: self.startgg.getTournaments(s,e), daemon=False).start()

    def trackPlayer(self, discriminator):
        return self.startgg.enterPlayer(discriminator)
    