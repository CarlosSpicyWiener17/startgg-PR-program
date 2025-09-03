from storage.errors import *
from storage.database import Database

entrantStructure = {
            "name" : (None, str),
            "id" : (None,int),
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

setStructure = {
    "winner" : (None, str),
    "loser" : (None, str)
}

mainEventStructure = {
    "id" : (None, int),
    "name" : (None, str),
    "state" : (None, str),
    "entrants" : (list, entrantStructure),
    "sets" : (list, setStructure)
}

tournamentStructure = {
    "name" : (None, str),
    "id" : (None, int),
    "state" : (None, int),
    "Owner" : (None, ownerStructure),
    "mainEvent" : (None, mainEventStructure),
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
    def __init__(self, logger, userDir):
        super().__init__(eventDatabaseName, eventDatabaseStructure, logger, userDir)
        self.logger = logger

    def loadEvents(self):
        self._load_db()

    def updateTournamentTier(self, newTier : str, tournamentId):
        """
        Changes eventTier of tournament to new tier
        """
        events = self.get("events")
        newTournament = None
        for i, event in enumerate(events):
            if event["id"] == tournamentId:
                newTournament = event
                newTournament["eventTier"] = newTier
                break
        if not newTournament is None:
            events.pop(i)
            events.append(newTournament)

    def getCounting(self):
        """
        Gives all tournaments which count for PR rankings
        """
        return self.get("events", lambda event: event["counting"])

    def toggleTournamentCounts(self, tournamentId, isCounting,):
        """
        Changes counting key of tournament to isCounting of type bool
        """
        events = self.get("events")
        newTournament = None
        for i, event in enumerate(events):
            if event["id"] == tournamentId:
                newTournament = event
                newTournament["counting"] = isCounting
                break
        if not newTournament is None:
            events.pop(i)
            events.append(newTournament)

    def getEvent(self, eventId):
        try:

            events = self.get("events", lambda event: event["id"] == eventId)

            if len(events) > 0:
                return events[0]
            else:
                return None
        except:
            print("unknown error pls")

    def addEvents(self, newEvents):
        """
        Add several tournaments to event database
        """

        for event in newEvents:
            try:
                oldEvent = self.getEvent(event["id"])
                if not oldEvent is None:
                    oldEvent["state"] = event["state"]
                    oldEvent["mainEvent"] = event["mainEvent"]
                    oldEvent["attendeeAmount"] = event["attendeeAmount"] 
                    oldEvent["attendeeBonus"] = event["attendeeBonus"] 
                    oldEvent["trackedScore"] = event["trackedScore"] 
                    oldEvent["totalScore"] = event["totalScore"] 
                    oldEvent["eventTier"] = event["eventTier"] 
                    oldEvent["counting"] = event["counting"]
                else:
                    self.addEvent(event)
            except:
                self.logger.error(f"Couldnt add or update event to database: {event["name"]}\nLink: {event["link"]}")

    def addEvent(self, event):
        self.activeDatabase["events"].append(event)

    def removeEvent(self, eventId):
        for i, event in enumerate(self.activeDatabase["events"]):
            if event["id"] == eventId:
                self.activeDatabase["events"].remove(event)
                break

    def getEvents(self, ids=None):
        if ids is None:
            return self.get("events")
        else:
            return self.get("events", lambda item: item["id"] in ids)
    
    def addTime(self, start, end):
        if start > end:
            start, end = end, start
        merged = []
        placed = False
        for s, e in self.get("checkedDates"):
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
        self.overWrite("checkedDates", merged)

    def getSpecificEvent(self, id):
        """
        Gets specific event from tournament id
        """
        return self.getEvents({id})
    
    def getProcessedEventIds(self, after, before):
        """
        Gets all, already processed, tournaments, within given timeframe
        """
        isWithinDates = self.get("events", lambda event: after <= event["startAt"] and event["startAt"] <= before)

        return [event["id"] for event in isWithinDates]
    
    def isWithinTime(self, after, before):
        for start, end in self.get("checkedDates"):
            if start <= after and before <= end:
                return True
        return False

    def saveEvents(self):
        self._save_db()
