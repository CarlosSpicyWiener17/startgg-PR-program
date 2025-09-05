from storage.errors import *
import gzip
from pickle import load, dump
import os 
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

class Event_db:
    """
    Tournament database
    """
    def __init__(self, logger, userDir):
        self.name = eventDatabaseName
        self.file_path = os.path.join(userDir, self.name+".pkl")
        self.logger = logger

    def loadEvents(self):
        try:
            if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                with gzip.open(self.file_path, "rb") as databaseFile:
                    self.activeDatabase = load(databaseFile)   
                    databaseFile.close()
            else:
                self.activeDatabase = {
                    "events" : [],
                    "eventIds" : set(),
                    "checkedDates" : []
                }
        except:
            self.activeDatabase = {
                    "events" : [],
                    "eventIds" : set(),
                    "checkedDates" : []
                }
            self.logger.error(f"Some error with saving in {self.name} database", exc_info=True)

    def updateTournamentTier(self, newTier : str, tournamentId):
        """
        Changes eventTier of tournament to new tier
        """
        for event in self.activeDatabase["events"]:
            if event["id"] == tournamentId:
                event["eventTier"] = newTier
                break

    def getCounting(self):
        """
        Gives all tournaments which count for PR rankings
        """
        return [event for event in self.activeDatabase["events"] if event["counting"]]

    def toggleTournamentCounts(self, tournamentId, isCounting,):
        """
        Changes counting key of tournament to isCounting of type bool
        """
        for event in self.activeDatabase["events"]:
            if event["id"] == tournamentId:
                event["counting"] = isCounting
                break


    def getEvent(self, eventId):
        try:

            for event in self.activeDatabase["events"]:
                if event["id"] == eventId:
                    return event
            return None
        except:
            print("unknown error pls")

    def addEvents(self, newEvents):
        """
        Add several tournaments to event database
        """

        for event in newEvents:
            try:
                self.activeDatabase["eventIds"].add(event["id"])
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
        for event in self.activeDatabase["events"]:
            if event["id"] == eventId:
                self.activeDatabase["events"].remove(event)
                break


    def getEvents(self, ids=None):
        if ids is None:
            return self.activeDatabase["events"]
        else:
            return [event for event in self.activeDatabase["events"] if event["id"] in ids]
    
    def addTime(self, start, end):
        if start > end:
            start, end = end, start
        merged = []
        placed = False
        for s, e in self.activeDatabase["checkedDates"]:
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
        self.activeDatabase["checkedDates"] = merged

    def getSpecificEvent(self, id):
        """
        Gets specific event from tournament id
        """
        return self.getEvents({id})
    
    def getProcessedEventIds(self, after, before):
        """
        Gets all, already processed, tournaments, within given timeframe
        """

        return {event["id"] for event in self.activeDatabase["events"] if after <= event["startAt"] and event["startAt"] <= before}
    
    def isWithinTime(self, after, before):
        for start, end in self.activeDatabase["checkedDates"]:
            if start <= after and before <= end:
                return True
        return False

    def saveEvents(self):
        """
        Saves the database to file
        """
        try:
            with gzip.open(self.file_path, "wb") as databaseFile:
                dump(self.activeDatabase,databaseFile)   
                databaseFile.close()
        except:
            self.logger.error(f"Some error with saving in {self.name} database", exc_info=True)
