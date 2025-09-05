from pysmashgg.api import run_query
from startggModules.queries import *
from startggModules.startggFilters import allEntrantsFilter, allTournamentsFilter, tournamentFilterNoMain
from startggModules.errors import *
from databases import *
import threading as t

import logging
global logger


class startggInterface:
    """
    Structured interface between startgg api and system\n
    For easier development mainly
    """
    def __init__(self, system, userDir):
        """
            Initializes the interface.

        """
        global logger
        self._getAuthorization()
        self.system = system
        logger = system.logger
        #name is legacy. Actually contains Tournaments but filtered down to just 1 event
        self.events = Event_db(logger, userDir)
        self.events.loadEvents()

        self.trackedPlayers = TrackedPlayers(logger, userDir)
        self.trackedPlayers.loadTracklist()

        self.playerList = AllPlayers(logger, userDir)
        self.playerList.loadPlayers()

    def _getAuthorization(self):
        HEADER = "Bearer "
        with open("auth.txt", "r") as auth:
            HEADER += auth.readline().strip()
            auth.close()
        self.header = {"Authorization" : HEADER}

    def entrantsToPlayers(self, entrants):
        players = []
        for entrant in entrants:
            tournamentInfo = {
                "entrantId" : entrant["entrantId"],
                "tournamentId" : entrant["tournamentId"],
                "placement" : entrant["placement"]
            }
            newPlayer = {
                "name" : entrant["name"],
                "discriminator" : entrant["discriminator"],
                "link" : entrant["link"],
                "tournaments" : [tournamentInfo],
                "setOfEntrantIds" : {entrant["entrantId"]},
                "id" : entrant["id"],
                "topCut" : False
            }
            players.append(newPlayer)
        return players

    def addEvents(self, eventsToAdd):
        logger.info("Adding events")

        self.events.addEvents(eventsToAdd)

        logger.info("Adding new entrants")
        for tournament in eventsToAdd:
            try:
                players = self.entrantsToPlayers(tournament["mainEvent"]["entrants"])
                len(players)
                self.playerList.addPlayers(players)
            except:
                logger.error(f"Error adding entrants to {tournament["link"]}", exc_info=True)


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
            logger.error("Error with startgg", response, exc_info=True)
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
    
    def getTrackedPlayers(self):
        tracklist = self.trackedPlayers.getTracklist()
        self.system.tracklistInfo = self.playerList.getPlayers(tracklist)

    def addEvent(self, slug):
        with self.system.startggLock:
            response = run_query(getTournamentEntrants, variables={"page" : 1, "slug" : slug}, header=self.header, auto_retry=True)

            event = response["data"]["event"]
            remainingPages = event["entrants"]["pageInfo"]["totalPages"]-1

            success, tournament = tournamentFilterNoMain(event["tournament"])

            event = {
                "id" : event["id"],
                "name" : event["name"],
                "state" : event["state"]
            }
            allEntrants = []
            totalAttendees = 0
            filteredEntrants, attendeeAmount = allEntrantsFilter(response, tournament["id"])
            totalAttendees+=attendeeAmount
            allEntrants.extend(filteredEntrants)

            for i in range(remainingPages):

                response = run_query(getTournamentEntrants, variables={"page" : 2+i, "slug" : slug}, header=self.header, auto_retry=True)
                filteredEntrants, attendeeAmount = allEntrantsFilter(response, tournament["id"])
                totalAttendees+=attendeeAmount
                allEntrants.extend(filteredEntrants)
        self.system.queue.put(("status", "Adding single event entrants"))
        allEntrants.sort(key=lambda x: x["placement"])
        event["entrants"] = allEntrants
        tournament["mainEvent"] = event
        tournament["attendeeAmount"] = totalAttendees
        if totalAttendees >= 55:
            attendeeBonus = 2
        elif totalAttendees >= 40:
            attendeeBonus = 1
        else:
            attendeeBonus = 0
        tournament["attendeeBonus"] = attendeeBonus
        self.system.queue.put(("status","Ranking single event"))
        success, rankedTournament = tournamentTier(tournament, self.trackedPlayers.getTracklist())

        with self.system.databaseLock:
            self.events.addEvents([rankedTournament])
        
        self.system.queue.put(("status","Single tournament added"))
        self.system.queue.put(("addSingleEvent", None))

    def reRankTournaments(self):
        """
        Ranks all tournaments anew based on current tracklist
        """
        with self.system.databaseLock:
            try:
                allTournaments = self.events.getEvents()
                trackList = self.trackedPlayers.getTracklist()
                self.rankTournamentTiers(allTournaments, trackList)
                self.system.queue.put(("reranked", None))
            except:
                pass

    def enterPlayer(self, discriminator):
        """
        Adds new user to tracklist, if discriminator leads to a startgg user
        """
        debugName = None
        try:
            if self.trackedPlayers.isTracked(discriminator):
                return 0
            print("not already tracked")
            player = self.playerList.getPlayer(discriminator)
            if player is None:
                print("player dont exist, so making new one")
                newUser = self._userQuery(discriminator)
                player = {
                    "name" : newUser["name"],
                    "discriminator" : newUser["discriminator"],
                    "id" : newUser["id"],
                    "link" : "https://www.start.gg/user/"+newUser["discriminator"],
                    "tournaments" : [],
                    "setOfEntrantIds" : set(),
                    "topCut" : False
                }
            else:
                self.trackedPlayers.addTrackedPlayer(player)
                return 1
            print("adding player")
            self.playerList.addPlayer(player)
            print("adding to track")
            self.trackedPlayers.addTrackedPlayer(player)

        except:
            if not debugName is None:
                logger.error(f"Error with player {debugName}", exc_info=True)
            else:
                logger.error(f"Error with player {discriminator}", exc_info=True)
            return -1
        

    def enterPlayerForce(self, discriminator):
        """
        Adds new user to tracklist, if discriminator leads to a startgg user
        """
        with self.system.databaseLock:
            try:
                print("not already tracked")
                player = self.playerList.getPlayer(discriminator)
                if player is None:
                    print("player dont exist, so making new one")
                    newUser = self._userQuery(discriminator)
                    player = {
                        "name" : newUser["name"],
                        "discriminator" : newUser["discriminator"],
                        "id" : newUser["id"],
                        "link" : "https://www.start.gg/user/"+newUser["discriminator"],
                        "tournaments" : [],
                        "setOfEntrantIds" : set(),
                        "topCut" : False
                    }
                print("adding player")
                self.playerList.addPlayer(player)
                print("adding to track")
                self.trackedPlayers.addTrackedPlayer(player)

            except:
                logger.error("Uh oh enterPlayer error", exc_info=True)
                return -1
        self.getTrackedPlayers()    
        self.system.updateTracklist()
    
    def updateTopCut(self, discriminator, topCutBool):
        print("updating topcut")
        newPlayer = self.playerList.getPlayer(discriminator)
        newPlayer["topCut"] = topCutBool
        print("adding new player")
        self.playerList.toggleTopCut(newPlayer)

    def updateTournamentTier(self, newTier, tournamentId):
        self.events.updateTournamentTier(newTier, tournamentId)

    def _fillEventEntrants(self, tournaments, predone):
        """
        Get all event entrants
        Avoids predone events
        """
        self.system.UI.status.set("Getting entrants...")
        tourneyNum = len(tournaments)
        i=1
        for tournament in tournaments:
            self.system.UI.status.set(f"Getting entrants in tourney {i} of {tourneyNum}...")
            i+=1
            logger.info(f"\nQuerying entrants:\n{tournament["link"]}\n{tournament["mainEvent"]["name"]}")
            entrants, attendeeAmount = self._tournamentEntrantsQuery(tournament["mainEvent"]["id"])

            tournament["mainEvent"]["entrants"] = entrants
            
            tournament["attendeeAmount"] = attendeeAmount
            if attendeeAmount >= 55:
                attendeeBonus = 2
            elif attendeeAmount >= 40:
                attendeeBonus = 1
            else:
                attendeeBonus = 0
            tournament["attendeeBonus"] = attendeeBonus

    def getTournaments(self, start, end):
        with self.system.startggLock:
            self._queryTournaments(start, end)

    def save(self):
        with self.system.databaseLock:
            logger.info("Saving tournaments")
            self.events.saveEvents()
            logger.info("Entrants")
            self.playerList.savePlayers()
            logger.info("Tracked players")
            self.trackedPlayers.saveTracklist()
            logger.info("All saved up")

    def toggleTopCut(self, playerDiscriminator, isTopCut):
        with self.system.databaseLock:
            self.playerList.toggleTopCut(playerDiscriminator, isTopCut)
        self.system.queue.put(("status", "Toggled top cut"))

    def toggleTournamentCounts(self, tournamentId, isCounting,):
        with self.system.databaseLock:
            self.events.toggleTournamentCounts(tournamentId, isCounting)
        self.system.queue.put(("status", "Toggled tournament PR"))

    def removeTrackedPlayer(self, discriminator):
        with self.system.databaseLock:
            self.trackedPlayers.removeTrackedPlayer(discriminator)
        self.system.queue.put(("status", "Removed tracked player"))
        self.system.queue.put(("removedTracked", None))

    def updateTournamentTier(self, newTier : str, tournamentId):
        with self.system.databaseLock:
            self.events.updateTournamentTier(newTier, tournamentId)
        self.system.queue.put(("status", "Changed tier"))

    def _queryTournaments(self, after, before):
        """
        Function getting processed, and processing un-processed tournaments, and returns in correct format
        after, before are timestamps
        """
        logger.info("Checking for tournaments")
        #if there are gaps in previous searches, search all tournament ids within the specified timeframe
        tournamentsToProcess = []
        if not self.events.isWithinTime(after, before):
            tournamentsToProcess = self._getAllTournamentsQuery(after, before)
            #this time has now been checked
            with self.system.databaseLock:
                self.events.addTime(after, before)
        

        #get previous events ids
        predoneEventIds = self.events.getProcessedEventIds(after, before)
        predoneTournaments = self.events.getEvents(predoneEventIds)

        allTournaments = []
        #if empty, means we only need to get tournaments
        ranked=None
        allTournaments = predoneTournaments
        tournamentsToQuery = []
        logger.info(f"Length of tournaments with predones {len(allTournaments)}")
        for tournament in tournamentsToProcess:
            if not tournament["id"] in predoneEventIds:
                tournamentsToQuery.append(tournament)
        if not tournamentsToProcess == []:
            logger.info(f"How many tournaments to process: {len(tournamentsToQuery)}")
            self._fillEventEntrants(tournamentsToQuery, predoneEventIds)
            self.rankTournamentTiers(tournamentsToQuery, self.trackedPlayers.getTracklist())

            
        else:
            self.system.queue.put(("status","All tournaments found in storage"))
            logger.info("All tournaments are stored")
        if not tournamentsToQuery is None:
            tournamentsToQuery.sort(key=lambda x: x["startAt"], reverse=True)
            print(len(tournamentsToQuery))
            allTournaments.extend(tournamentsToQuery)
            with self.system.databaseLock:
                self.addEvents(tournamentsToQuery)
        allTournaments.sort(key=lambda x: x["startAt"])
        logger.info("Got all the tournaments o7")
        self.system.queue.put(("getTournaments",allTournaments))
    
    def removeEvent(self, eventId):
        with self.system.databaseLock:
            self.events.removeEvent(eventId)
        self.system.queue.put(("removedEvent", None))

    def fillEventSets(self, tournaments, tracklist):
        with self.system.databaseLock:
            for tournament in tournaments:
                entrantIds = [entrant["entrantId"] for entrant in tournament["mainEvent"]["entrants"] if entrant["discriminator"] in tracklist]
                if not tournament["mainEvent"].get("sets") is None:
                    continue
                sets = self._querySets(tournament["mainEvent"]["id"], entrantIds)
                prettySets = []
                for set in sets:
                    try:
                        slots = set["slots"]
                        #(slots)
                        #print("getting winnerid")
                        winnerId = (slots[0]["standing"]["placement"] == 1) and slots[0]["standing"]["entrant"]["id"] or slots[1]["standing"]["entrant"]["id"]
                        #print("getting loserid")
                        loserId = (slots[0]["standing"]["placement"] == 2) and slots[0]["standing"]["entrant"]["id"] or slots[1]["standing"]["entrant"]["id"]
                        #print("winner")
                        winner = self.playerList.getPlayerFromEntrant(winnerId)
                        #print("loser")
                        loser = self.playerList.getPlayerFromEntrant(loserId)

                        prettySets.append({
                            "winner" : winner,
                            "loser" : loser
                        })
                    except:
                        logger.error(f"Some unknwon edlritch error, filtering sets within {tournament["name"]}. \nLink: {tournament["link"]}")
                tournament["mainEvent"]["sets"] = prettySets



    def rankTournamentTiers(self, tournaments, trackSet):
        self.system.queue.put(("status","Ranking tournaments..."))
        tourneyNum = len(tournaments)
        i=1
        for tournament in tournaments:
            self.system.queue.put(("status",f"Ranking tournaments {i} of {tourneyNum}..."))
            i+=1
            tournamentTier(tournament, trackSet)

        self.system.queue.put(("status","Ranking finished"))


    def _querySets(self, tournamentId, entrantIds):

        sets = []

        response = run_query(query=setsInTournament, variables={"page" : 1, "id" : tournamentId, "entrantIds" : entrantIds}, header=self.header, auto_retry=True)
        try:
            remainingPages = response["data"]["event"]["sets"]["pageInfo"]["totalPages"]-1
        except:
            return sets
        if remainingPages > 10:
            print(response)
            input()
        sets.extend(response["data"]["event"]["sets"]["nodes"])
        for i in range(remainingPages):
            response = run_query(query=setsInTournament, variables={"page" : 1, "id" : tournamentId, "entrantIds" : entrantIds}, header=self.header, auto_retry=True)

            sets.extend(response["data"]["event"]["sets"]["nodes"])
        return sets


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
        else:
            tournament["counting"] = True
    except:
        logger.error(f"Unknown error with {tournament["name"]}", exc_info=True)



    
