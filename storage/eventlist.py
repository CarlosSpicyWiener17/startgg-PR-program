from storage.errors import *
from storage.database import Database

entrantStructure = {
            "name" : (None, str),
            "userId" : (None,int),
            "discriminator" : (None, str),
            "link" : (None, str),
            "entrantId" : (None,int),
            "tournamentId" : (None,int),
            "placement" : (None,int)
        }

ownerStructure = {
            "name" : (None, str),
            "discriminator" : (None, str),
            "link" : (None, str),
            "id" : (None, int)
        }

mainEventStructure = {
    "id" : (None, int),
    "name" : (None, str),
    "state" : (None, str),
    "entrants" : (list, dict)
}

tournamentStructure = {
    "name" : (None, str),
    "id" : (None, int),
    "state" : (None, int),
    "Owner" : (None, ownerStructure),
    "mainEvent" : (None, dict),
    "link" : (None, str),
    "attendeeAmount" : (None, int),
    "attendeeBonus" : (None, int),
    "trackedScore" : (None, int),
    "totalScore" : (None, int),
    "eventTier" : (None, str),
    "startAt" : (None, int),
    "date" : (None, str),
    "counting" : (None, bool)
}

eventDatabaseStructure = {
        "events" : (list, tournamentStructure),
        "eventIds" : (set, int),
        "checkedDates" : (list, tuple)
    }

eventDatabaseName = "Events"

class Event_db(Database):
    """
    Tournament database
    """
    def __init__(self):
        super().__init__(eventDatabaseName, eventDatabaseStructure)

    def loadEvents(self):
        self._load_db()

    def updateTournamentTier(self, newTier : str, tournamentId):
        """
        Changes eventTier of tournament to new tier
        """
        self._updateItemKey("events", "id", tournamentId, "eventTier", newTier)

    def toggleTournamentCounts(self, isCounting, tournamentId):
        """
        Changes counting key of tournament to isCounting of type bool
        """
        self._updateItemKey("events", "id", tournamentId, "counting", isCounting)

    def addEvents(self, eventsToAdd):
        """
        Add several tournaments to event database
        """
        print("Try addMultiple")
        self._updateMultipleDict("events", "id", eventsToAdd)
        self._addMultiple("eventIds", set([event["id"] for event in eventsToAdd]))

    def removeEvent(self, eventId):
        self._removeDict("events", "id", eventId)

    def getEvents(self, ids=None):
        if ids is None:
            return self._getItems("events")
        return self._conditionalGetDictItems("events", "id", lambda eventId: eventId in set(ids))
    
    def addTime(self, start, end):
        if start > end:
            start, end = end, start
        merged = []
        placed = False
        for s, e in self._getItems("checkedDates"):
            if e < start:  # current interval ends before new one starts
                merged.append((s, e))
            elif end < s:  # new one ends before current starts
                if not placed:
                    merged.append((start, end))
                    placed = True
                merged.append((s, e))
            else:  # overlap → merge
                start = min(start, s)
                end = max(end, e)
        if not placed:
            merged.append((start, end))
        self._overwrite("checkedDates", merged)

    def getSpecificEvent(self, id):
        """
        Gets specific event from tournament id
        """
        return self._getItemFromKeyValue("events", "id", id)
    
    def getProcessedEventIds(self, after, before):
        """
        Gets all, already processed, tournaments, within given timeframe
        """
        isWithinDates = self._conditionalGetDictItems("events", "startAt", lambda eventStartAt: after <= eventStartAt and eventStartAt <= before)
        
        return [event["id"] for event in isWithinDates]
    
    def isWithinTime(self, after, before):
        for start, end in self._getItems("checkedDates"):
            if start <= after and before <= end:
                return True
        return False

    def updateCounting(self, id, counting):
        self._updateItemKey("events", "id", id, "counting", counting)

    def saveEvents(self):
        self._save_db()
