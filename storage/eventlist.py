from storage.errors import *
from storage.database import Database

# Configure logging once in your app


filename = "tournaments"

tournamentStructure = {
    "name" : (None, str),
    "id" : (None, int),
    "state" : (None, int),
    "Owner" : (None, dict),
    "mainEvent" : (None, dict),
    "link" : (None, str),
    "attendeeAmount" : (None, int),
    "attendeeBonus" : (None, int),
    "trackedScore" : (None, int),
    "totalScore" : (None, int),
    "eventTier" : (None, str),
    "startAt" : (None, int),
    "date" : (None, str),
}

databaseStructure = {
        "events" : (list, tournamentStructure),
        "eventIds" : (set, int),
        "checkedDates" : (list, tuple)
    }

databaseName = "Events"

class Event_db(Database):
    """
    Tournament database
    """
    def __init__(self):
        super().__init__(databaseName, databaseStructure)

    def loadEvents(self):
        self._load_db()

    def updateTournamentTier(self, newTier : str, tournamentId):
        """
        Changes eventTier of tournament to new tier
        """
        self._updateItemKey("events", "id", tournamentId, "eventTier", newTier)

    def addEvents(self, eventsToAdd):
        """
        Add several tournaments to event database
        """
        self._addMultiple("events", eventsToAdd)
        self._addMultiple("eventIds", set([event["id"] for event in eventsToAdd]))

    def removeEvent(self, eventId):
        self._removeDict("events", "id", eventId)

    def getEvents(self, ids):
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
        print(merged)
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
            print(start, end)
            if start <= after and before <= end:
                return True
        return False

    def saveEvents(self):
        self._save_db()
