from pysmashgg.api import run_query
from startggModules.queries import *
from startggModules.startggFilters import allEntrantsFilter, allTournamentsFilter
from startggModules.errors import *
from databases import *
import threading as t

import logging

logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)

error_handler = logging.FileHandler("error.log")
error_handler.setLevel(logging.ERROR)
error_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
error_handler.setFormatter(error_format)

info_handler = logging.FileHandler("info.log")
info_handler.setLevel(logging.INFO)
info_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
info_handler.setFormatter(info_format)

logger.addHandler(error_handler)
logger.addHandler(info_handler)

class startggInterface:
    """
    Structured interface between startgg api and system\n
    For easier development mainly
    """
    def __init__(self, system):
        """
            Initializes the interface.

        """
        self._getAuthorization()
        self.system = system
        #name is legacy. Actually contains Tournaments but filtered down to just 1 event
        self.events = Event_db()
        self.events.loadEvents()

        self.trackedPlayers = TrackedPlayers()
        self.trackedPlayers.loadTracklist()

        self.playerList = AllPlayers()
        self.playerList.loadPlayers()

    #def updateCounting(self, id, counting):

    def _getAuthorization(self):
        HEADER = "Bearer "
        with open("auth.txt", "r") as auth:
            HEADER += auth.readline().strip()
            auth.close()
        self.header = {"Authorization" : HEADER}

    def addEvents(self, eventsToAdd):
        print("Trying to add")
        with self.system.databaseLock:
            print("Got lock, adding tournaments")
            self.events.addEvents(eventsToAdd)
            print("Adding entrants")
            for i, tournament in enumerate(eventsToAdd):
                print(i+1, " tournament of ", len(eventsToAdd))
                for entrant in tournament["mainEvent"]["entrants"]:
                    self.playerList.addPlayer(entrant)

    def _getAllTournamentsQuery(self,after,before):
        """
        Gets all recent tournaments, within state, within selected timestamps, and returns them filtered
        """
        
        allTournaments = []

        #query startgg
        response = run_query(getAllTournamentsWA, variables= {"page" : 1, "ids" : [1386], "after" : int(after), "before" :int(before),}, header=self.header, auto_retry=True)
        
        #filter result
        filteredTournaments = allTournamentsFilter(response)
        allTournaments.extend(filteredTournaments)

        #repeat for remaining pages
        remainingPages = response["data"]["tournaments"]["pageInfo"]["totalPages"]-1

        for i in range(remainingPages):
            #query startgg
            response = run_query(getAllTournamentsWA, variables= {"page" : 2+i, "ids" : [1386], "after" : int(after), "before" : int(before)}, header=self.header, auto_retry=True)
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
        filteredEntrants, attendeeAmount = allEntrantsFilter(response, id)
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
            filteredEntrants, attendeeAmount = allEntrantsFilter(response, id)
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
            logger.error("Discriminator is wrong", exc_info=True)
            return None
        except:
            logger.error("Unknown error", exc_info=True)
            return None
    
    def enterPlayer(self, discriminator):
        """
        Adds new user to tracklist, if discriminator leads to a startgg user
        """
        try:
            if self.trackedPlayers.isTracked(discriminator):
                return 0

            playerExist, player = self.playerList.getPlayerFromDiscriminator(discriminator)
            if not playerExist:
                newUser = self._userQuery(discriminator)
                player = {
                    "name" : newUser["name"],
                    "discriminator" : newUser["discriminator"],
                    "userId" : newUser["id"],
                    "link" : "https://www.start.gg/user/"+newUser["discriminator"],
                    "tournaments" : [],
                    "setOfEntrantIds" : set(),
                }
            self.playerList.addPlayer(player)
            self.trackedPlayers.addTrackedPlayer(player)
            return 1
        except:
            return -1
    
    def updateTournamentTier(self, newTier, tournamentId):
        self.events.updateTournamentTier(newTier, tournamentId)

    def _fillEventEntrants(self, tournaments, predone):
        """
        Get all event entrants
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
        with self.system.startggLock:
            print("about to check these tourneys bro")
            self.system.tournamentsInfo = self._queryTournaments(start, end)

        if t.main_thread().is_alive():
            self.system._updateTournaments()
        else:
            self.save()

    def save(self):
        with self.system.databaseLock:
            print("Saving tournaments")
            self.events.saveEvents()
            print("Entrants")
            self.playerList.savePlayers()
            print("Tracked players")
            self.trackedPlayers.saveTracklist()
            print("All saved up")

    def _queryTournaments(self, after, before):
        """
        Function getting processed, and processing un-processed tournaments, and returns in correct format
        after, before are timestamps
        """
        print("Checking for tournaments")
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
        ranked=None
        allTournaments = predoneTournaments
        print("Length of tournaments with predones", len(allTournaments))
        if not tournamentsToProcess == []:
            print("Querying tournaments")
            filled = self._fillEventEntrants(tournamentsToProcess, predoneEventIds)
            ranked = rankTournamentTiers(filled, self.trackedPlayers.getSetCheck())
            allTournaments.extend(ranked)
        else:
            print("All tournaments are stored")
        if not ranked is None:
            print("adding events")
            ranked.sort(key=lambda x: x["startAt"], reverse=True)
            t.Thread(target=lambda: self.addEvents(ranked), daemon=False).start()
        allTournaments.sort(key=lambda x: x["startAt"])
        print("Got all the tournaments o7")
        return allTournaments
    
    def saveEvents(self):
        self.events.saveEvents()

def tournamentTier(tournament, trackSet):
    try:
        #legacy error checks to be safe and certain. im too scared to remove them
        if tournament["attendeeAmount"] < 12:
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
        if totalScore > 1:
            print("Has score enough")
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
        logger.error(f"Unknown error with {tournament["name"]}", exc_info=True)
        return False, None

def rankTournamentTiers(tournaments, trackSet):
    ranked= []
    for tournament in tournaments:
        success, rankedTournament = tournamentTier(tournament, trackSet)
        if success:
            ranked.append(rankedTournament)
    return ranked

