from utility import toDate
from startggModules.errors import *
import logging

logger = logging.getLogger("my_app")



def setUser(entrant : dict) -> tuple[bool,dict|None]:
    try:
        #entrant id most likely guaranteed to be available
        entrantId : int = entrant["id"]

        if len(entrant["participants"]) == 0:

            raise UserError(entrantId)
        
        try:
            user : dict | None = entrant["participants"][0]["user"]
        except:
            raise UserError(entrantId)
        if user["discriminator"] is None:

            raise UserDiscriminatorError(entrantId)
        if user is None:
            raise UserIdError(entrantId)
        if user["id"] is None:
            raise UserIdError(entrantId)
        
        
        #IF SUCCESS
        return True, {
                "id" : user["id"],
                "discriminator" : user["discriminator"],
                "link" : "https://www.start.gg/user/"+user["discriminator"]
            }
    #These errors are fine enough
    except UserDiscriminatorError:
        logger.error(f"Entrant has no user at all")
        return True, {
            "id" : None,
            "discriminator" : None,
            "link" : None
        }
    except UserIdError:
        logger.error(f"Entrant doesnt have user id: {entrant["id"]}, {user["discriminator"]}", exc_info=True)
        return True, {
            "id" : None,
            "discriminator" : user["discriminator"],
            "link" : "https://www.start.gg/user/"+user["discriminator"]
        }
    except UserError:
        return True, {
            "id" : None,
            "discriminator" : None,
            "link" : None
        }
    except:
        return False, None

def entrantFilter(entrant : dict, tournamentId: int) -> tuple[bool, dict | None]:
    """
    Safe function for filtering entrants into dicts:\n
        "Name"\t\t #startgg gamerTag
        "id"\t\t #startgg user id
        "discriminator"\t #startgg user discriminator
        "link"\t\t #startgg user link
        "entrantId"\t\t #tournament specific entrant id
        "placement"\t\t #placement in specific tournament
    """
    try:
        #always guaranteed
        entrantId : int = entrant["id"]

        #set gamertag
        tournamentGamerTag : str | None = None
        placement = None
        try:
            placement = entrant["standing"]["placement"]
        except:
            placement = None
            return False, None
        try:
            tournamentGamerTag = entrant["participants"][0]["gamerTag"]
        except:
            logger.error(f"GamerTag not found. {entrantId}", exc_info=True)
            return False, None
        if tournamentGamerTag is None:
            logger.error(f"GamerTag not found. {entrantId}")
            return False, None
        #set user
        
        success, user = setUser(entrant)
        if not success:
            if not placement is None:
                logger.error(f"User not found. {entrantId}, {entrant["participants"][0]["gamerTag"]}")
            return False, None
        newEntrant = {
            "name" : entrant["participants"][0]["gamerTag"],
            "id" : user["id"],
            "discriminator" : user["discriminator"],
            "link" : user["link"],
            "entrantId" : entrantId,
            "tournamentId" : tournamentId,
            "placement" : placement,
            
        }
        return True, newEntrant
    except:
        logger.error(f"Unknown error. {entrantId}", exc_info=True)
        return False, None
    

def allEntrantsFilter(response : dict, tournamentId : int) -> tuple[list, int]:
    """
    Filters an events entrants in desired format. Returns the entrants list
    """
    filteredEntrants = []
    
    attendeeAmount = 0
    for entrant in response["data"]["event"]["entrants"]["nodes"]:
        success, filteredEntrant = entrantFilter(entrant, tournamentId)
        attendeeAmount+=1
        if success:
            filteredEntrant["tournamentId"] = tournamentId
            filteredEntrants.append(filteredEntrant)
        continue
    filteredEntrants.sort(key= lambda x: x["placement"])
    return filteredEntrants, attendeeAmount

def setOwner(tournament) -> dict | None:
    """
    Safe function to get startgg tournament owner info:\n
        "name"\t\t #startgg player gamertag of tournament owner
        "discriminator"\t #startgg user discriminator of tournament owner
        "link"\t\t #"https://www.start.gg/user/" + startgg user discriminator of tournament owner,
        "id"\t\t #startgg user id of tournament owner

        #or

        None
    """
    try:
        tournamentLink = "https://www.start.gg/"+tournament["slug"]

        #Check owner
        if tournament["owner"] is None:
            raise OwnerError(tournamentLink, None)
        #Assign owner
        tournamentOwner = tournament["owner"]
        
        #Check owners gamertag
        if tournamentOwner["player"] is None:
            raise OwnerGamerTagError
        else:
            if tournamentOwner["player"]["gamerTag"] is None or tournamentOwner["player"]["gamerTag"] == "":
                raise OwnerGamerTagError
        #Assign
        tournamentOwnerName = tournamentOwner["player"]["gamerTag"]

        #Check discriminator
        if tournamentOwner["discriminator"] is None or tournamentOwner["discriminator"] == "":
            raise OwnerDiscriminatorError
        #Assign
        tournamentOwnerDiscriminator = tournamentOwner["discriminator"]

        #Check id
        if tournamentOwner["id"] is None:
            raise OwnerIdError
        #Assign
        tournamentOwnerId = tournamentOwner["id"]
        return {
            "name" : tournamentOwnerName,
            "discriminator" : tournamentOwnerDiscriminator,
            "link" : "https://www.start.gg/user/"+tournamentOwnerDiscriminator,
            "id" : tournamentOwnerId
        }
    except OwnerError:
        logger.error("Owner doesnt exist", exc_info=True)
        return None
    except OwnerDiscriminatorError:
        logger.error("Owner discriminator doesnt exist", exc_info=True)
        return None
    except OwnerIdError:
        logger.error("Owner id doesnt exist??", exc_info=True)
        return None
    except OwnerGamerTagError:
        logger.error("Owner player/gamertag doesnt exist", exc_info=True)
        return None
    except:
        logger.error("Unknown error. Contact", exc_info=True)
        return None

def getMainEvent(events : list, link : str, name : str) -> dict | None:
    contenders = []
    if len(events) == 1:
        return True, events[0]
    hasNames = []
    for event in events:
        try:
            if event["name"].find(name) != 1:
                hasNames.append(event)
        except:
            logger.info(f"error with {link}, {event["name"]}")
    nonCasuals = []
    if len(hasNames) > 1:
        for event in hasNames:
            try:
                isCasual = (event["name"].find("Casual") != -1) or (event["name"].find("casual") != -1) or (event["name"].find("CASUAL") != -1)
                if not isCasual:
                    nonCasuals.append(event)
            except:
                logger.info(f"event[{event} error]")
    elif len(hasNames) == 1:
        contenders = hasNames
    nonRedemption = []
    if len(nonCasuals) >1:
        for event in nonCasuals:
            try:
                redemption = (event["name"].find("redemption") != -1) or (event["name"].find("REDEMPTION") != -1) or (event["name"].find("Redemption") != -1)
                amateur = (event["name"].find("amateur") != -1) or (event["name"].find("AMATEUR") != -1) or (event["name"].find("Amateur") != -1)
                isRedemption = redemption or amateur
                if not isRedemption:
                    nonRedemption.append(event)
            except:
                logger.info(f"event[{event} error]")
    elif len(nonCasuals) == 1:
        contenders = nonCasuals
    if len(nonRedemption) > 1:
        for event in nonRedemption:
            try:
                completed = event["state"] == "COMPLETED"
                if completed:
                    contenders.append(event)
            except:
                logger.info(f"event[{event} error]")
    elif len(nonRedemption) == 1:
        contenders = nonRedemption
    singlesEvents = []
    if len(contenders)==1:
        return True, contenders[0]
    else:
        for event in contenders:
            isSingles = (event["name"].find("Singles") != -1) or (event["name"].find("SINGLES") != -1) or (event["name"].find("singles") != -1)
            completed = event["state"] == "COMPLETED"
            if isSingles and completed:
                singlesEvents.append(event)
    if singlesEvents == []:
        logger.info(f"No tournaments fit.\nLink: {link}\n")
        return False, None
    try:
        if len(singlesEvents) == 1:
            completed = singlesEvents[0]["state"] == "COMPLETED"
            if not completed:
                raise InProgressError(link, singlesEvents[0]["name"])
            return True, singlesEvents[0]
        else:
            logger.info(f"Too many tournaments fit.\nLink: {link}")
            return False, None
    except InProgressError:
        logger.error("Tournament hasnt been completed", exc_info=True)
    except:
        logger.error(f"Tournament getMainEvent unknown error:\n {link}", exc_info=True)


    
def tournamentFilterNoMain(tournament : dict) -> tuple[bool, dict | None]:
    """
    Safe function to get startgg tournament info:\n

    """
    try:
        #If these dont work i dont even know. Should always work
        tournamentLink = "https://www.start.gg/"+tournament["slug"]
        tournamentStartAt = tournament["startAt"]
        
        return True, {
            "name" : tournament["name"],
            "id" : tournament["id"],
            "state" : tournament["state"],
            "Owner" : setOwner(tournament),
            "link" : tournamentLink,
            "mainEvent" : dict(),
            "attendeeAmount" : 0,
            "attendeeBonus" : 0,
            "trackedScore" : 0,
            "totalScore" : 0,
            "eventTier" : "None",
            "startAt" : tournamentStartAt,
            "date" : toDate(tournamentStartAt),
            "counting" : True
        }

        
    except EventMissingError:
        logger.info("None of the events matches requirements for singles", exc_info=True)
        return False, None
    except:
        logger.error("Unknown error", exc_info=True)
        return False, None

def tournamentFilter(tournament : dict) -> tuple[bool, dict | None]:
    """
    Safe function to get startgg tournament info:\n

    """
    try:
        #If these dont work i dont even know. Should always work
        tournamentLink = "https://www.start.gg/"+tournament["slug"]
        tournamentStartAt = tournament["startAt"]
        success, tournamentMainEvent = getMainEvent(tournament["events"], tournamentLink, tournament["name"])
        if success:
            return True, {
                "name" : tournament["name"],
                "id" : tournament["id"],
                "state" : tournament["state"],
                "Owner" : setOwner(tournament),
                "mainEvent" : tournamentMainEvent,
                "link" : tournamentLink,
                "attendeeAmount" : 0,
                "attendeeBonus" : 0,
                "trackedScore" : 0,
                "totalScore" : 0,
                "eventTier" : "None",
                "startAt" : tournamentStartAt,
                "date" : toDate(tournamentStartAt),
                "counting" : True
            }
        else:
            raise EventMissingError(tournamentLink, None)
        
    except EventMissingError:
        logger.error("None of the events matches requirements for singles", exc_info=True)
        return False, None
    except:
        logger.error("Unknown error", exc_info=True)
        return False, None
    
        
    

def allTournamentsFilter(response):
    try:
        filteredTournaments = []
        for tournament in response["data"]["tournaments"]["nodes"]:
            #Filter
            success, filteredTournament = tournamentFilter(tournament)
            #If good, append
            if success:
                filteredTournaments.append(filteredTournament)
    except:
        logger.error("bad response object", response, exc_info=True)

    return filteredTournaments