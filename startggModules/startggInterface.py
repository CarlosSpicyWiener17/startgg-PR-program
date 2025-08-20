from pysmashgg.api import run_query
from startggModules.queries import *
from startggModules.startggFilters import allEntrantsFilter, allTournamentsFilter
from datetime import datetime
from startggModules.errors import *
from storage.eventlist import Event_db
from storage.tracklist import getSetCheck, addTrackedPlayer

import logging

# Configure logging once in your app
logging.basicConfig(
    filename="error.log",  # or just leave it blank to log to console
    level=logging.ERROR,   # Only log warnings/errors
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class startggInterface:
    """
    Structured interface between startgg api and system\n
    For easier development mainly
    """
    def __init__(self):
        """
            Initializes the interface.

        """
        self._getAuthorization()
        self.events = Event_db()
        self.events.loadEvents()

    def _getAuthorization(self):
        HEADER = "Bearer "
        with open("auth.txt", "r") as auth:
            HEADER += auth.readline().strip()
            auth.close()
        self.header = {"Authorization" : HEADER}

    def addEvents(self, events):
        self.events.addEvents(events)

    def _getAllTournamentsQuery(self,after,before):
        """
        Gets all recent tournaments, within state, within selected timestamps, and returns them filtered
        """
        
        allTournaments = []

        #query startgg
        response = run_query(getAllTournamentsWA, variables= {"page" : 1, "ids" : [1386], "after" : after, "before" :before,}, header=self.header, auto_retry=True)
        
        #filter result
        filteredTournaments = allTournamentsFilter(response)
        allTournaments.extend(filteredTournaments)

        #repeat for remaining pages
        remainingPages = response["data"]["tournaments"]["pageInfo"]["totalPages"]-1

        for i in range(remainingPages):
            #query startgg
            response = run_query(getAllTournamentsWA, variables= {"page" : 2+i, "ids" : [1386], "after" : after, "before" : before}, header=self.header, auto_retry=True)
            #filter result
            filteredTournaments = allTournamentsFilter(response)
            allTournaments.extend(filteredTournaments)

        return allTournaments
    
    def _tournamentEntrantsQuery(self,id):
        """
        Gets all entrants per event from startgg
        """
        allEntrants = []
        finalAttendeeAmount = 0
        #query startgg
        response = run_query(getAllEventEntrants, variables= {"page" : 1, "id" : id}, header=self.header, auto_retry=True)
        
        #filter result
        filteredEntrants, attendeeAmount = allEntrantsFilter(response)
        finalAttendeeAmount+=attendeeAmount
        allEntrants.extend(filteredEntrants)
        #repeat for remaining pages
        try:
            remainingPages = response["data"]["event"]["entrants"]["pageInfo"]["totalPages"]-1
        except:
            print(response)
            quit()

        for i in range(remainingPages):
            #query startgg
            response = run_query(getAllEventEntrants, variables= {"page" : 2+i, "id" : id}, header=self.header, auto_retry=True)
            
            #filter result
            filteredEntrants, attendeeAmount = allEntrantsFilter(response)
            finalAttendeeAmount+=attendeeAmount
            allEntrants.extend(filteredEntrants)
        
        return allEntrants, finalAttendeeAmount

    def _userQuery(self, discriminator) -> tuple[bool, dict | None]:
        """
        Try to get startgg user. Catch relevant errors

        Args:
            discriminator\t #startgg user discriminator
        Returns:
            bool: Success or not
            dict | None: user or None
        """
        try:
            slug = "user/" + discriminator
            response = run_query(query=getUserFromSlug, variables={"slug" : slug}, header=self.header, auto_retry=True)
            try:
                user = response["data"]
            except:
                raise DiscriminatorError(discriminator)
            user = response["data"]["user"]
            if user is None:
                raise DiscriminatorError(discriminator)
            return {
                "name" : user["player"]["gamerTag"],
                "discriminator" : user["discriminator"],
                "id" : user["id"]
            }
        except DiscriminatorError:
            logging.error("Discriminator is wrong", exc_info=True)
            return None
        except:
            logging.error("Unknown error", exc_info=True)
            return None
    
    def enterPlayer(self, discriminator):
        """
        Adds new user to tracklist, if discriminator leads to a startgg user
        """
        newUser = self._userQuery(discriminator)
        if newUser is not None:
            addTrackedPlayer(newUser)
    
    def updateTournamentTier(self, newTier, tournamentId):
        self.events.updateTournamentTier(newTier, tournamentId)

    def _fillEventEntrants(self, tournaments, predone):
        """
        Get all event entrants
        Edits tournaments in-place
        Avoids predone events
        """
        filledTournaments = []
        for tournament in tournaments:
            entrants, attendeeAmount = self._tournamentEntrantsQuery(tournament["mainEvent"]["id"])
            if attendeeAmount < 12:
                continue
            for entrant in entrants:
                try:
                    entrant["discriminator"]
                except:
                    raise DiscriminatorError(None)

            tournament["mainEvent"]["entrants"] = entrants
            
            tournament["attendeeAmount"] = attendeeAmount
            if attendeeAmount >= 55:
                attendeeBonus = 2
            elif attendeeAmount >= 40:
                attendeeBonus = 1
            else:
                attendeeBonus = 0
            tournament["attendeeBonus"] = attendeeBonus
            filledTournaments.append(tournament)
        return filledTournaments

    def getTournaments(self, start, end):
        return self._queryTournaments(start, end)

    def _queryTournaments(self, start, end):
        """
        Function getting processed, and processing un-processed tournaments, and returns in correct format
        Start, End are timestamps
        """
        #timestamps for tournament start times to search
        after, before = int(datetime.combine(start.get_date(), datetime.min.time()).timestamp()), int(datetime.combine(end.get_date(), datetime.min.time()).timestamp())
        
        #if there are gaps in previous searches, search all tournament ids within the specified timeframe
        tournamentsToProcess = []
        if not self.events.isWithinTime(after, before):
            tournamentsToProcess = self._getAllTournamentsQuery(after, before)
            #this time has now been checked
            self.events.addTime(after, before)
        

        #get previous events ids
        predoneEventIds = self.events.getProcessedEventIds(after, before)
        predoneTournaments = self.events.getEvents(predoneEventIds)

        allTournaments = []
        #if empty, means we only need to get tournaments
        if tournamentsToProcess == []:
            allTournaments = predoneTournaments
        else:
            filled = self._fillEventEntrants(tournamentsToProcess, predoneEventIds)
            ranked = rankTournamentTiers(filled, getSetCheck())
            allTournaments.extend(ranked)
        allTournaments.sort(key=lambda x: x["startAt"])

        return allTournaments
    
    def saveEvents(self):
        self.events.saveEvents()

def tournamentTier(tournament, trackSet):
    try:
        #legacy error checks to be safe and certain. im too scared to remove them
        if tournament["attendeeAmount"] < 12:
            tournament["eventTier"] = "None"
        try:
            tournament["eventTier"]
        except:
            tournament["eventTier"] = "None"

        #check tracked players. increase score by 1 per
        trackedPlayersPresent = 0
        for entrant in tournament["mainEvent"]["entrants"]:
            if entrant["discriminator"] in trackSet:
                trackedPlayersPresent+=1
                continue
        
        tournament["trackedScore"] = trackedPlayersPresent
        totalScore = trackedPlayersPresent + tournament["attendeeBonus"]
        tournament["totalScore"] = totalScore

        #Give tier based on totalscore. Note: Regional, Major, OOR Major are only set manually
        if totalScore >=18:
            eventTier = "18+"
        elif totalScore >=10:
            eventTier = "10-17"
        elif totalScore >=7:
            eventTier = "7-9"
        elif totalScore >=4:
            eventTier = "4-6"
        elif totalScore >= 2:
            eventTier = "2-3"
        else:
            eventTier = "None"
        tournament["eventTier"] = eventTier
        if eventTier == "None":
            tournament["counting"] = False
        return True, tournament
    except:
        logging.error(f"Unknown error with {tournament["name"]}", exc_info=True)
        return False, None

def rankTournamentTiers(tournaments, trackSet):
    ranked= []
    for tournament in tournaments:
        success, rankedTournament = tournamentTier(tournament, trackSet)
        if success:
            ranked.append(rankedTournament)
    return ranked

