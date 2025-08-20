from utility import toDate
from startggModules.errors import *
import logging

# Configure logging once in your app
logging.basicConfig(
    filename="error.log",  # or just leave it blank to log to console
    level=logging.ERROR,   # Only log warnings/errors
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
        
        if user["id"] is None:
            raise UserIdError(entrantId)
        
        if user["discriminator"] is None:

            raise UserDiscriminatorError(entrantId)
        
        #IF SUCCESS
        return True, {
                "id" : user["id"],
                "discriminator" : user["discriminator"],
                "link" : "https://www.start.gg/"+user["slug"]
            }
    #These errors are fine enough
    except (UserError, UserIdError, UserDiscriminatorError):
        logging.error("Issue with entrant in tournament", exc_info=True)
        return True, {
            "id" : None,
            "discriminator" : None,
            "link" : None
        }
    except:
        logging.error("Error in setUser()", exc_info=True)
        return False, None

def entrantFilter(entrant : dict) -> tuple[bool, dict | None]:
    """
    Safe function for filtering entrants into dicts:\n
        "Name"\t\t #startgg gamerTag
        "userId"\t\t #startgg user id
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
        try:
            tournamentGamerTag = entrant["participants"][0]["gamerTag"]
        except:
            logging.error(f"GamerTag not found. {entrantId}", exc_info=True)
            return False, None
        if tournamentGamerTag is None:
            logging.error(f"GamerTag not found. {entrantId}", exc_info=True)
            return False, None
        
        #set user
        success, user = setUser(entrant)
        if not success:
            logging.error(f"User not found. {entrantId}", exc_info=True)
            return False, None
        try:
            placement = entrant["standing"]["placement"]
        except:
            placement = None
            logging.error("No placement", exc_info=True)
            return False, None
        
        newEntrant = {
            "name" : entrant["participants"][0]["gamerTag"],
            "userId" : user["id"],
            "discriminator" : user["discriminator"],
            "link" : user["link"],
            "entrantId" : entrantId,
            "placement" : placement
        }
        return True, newEntrant
    except:
        logging.error(f"Unknown error. {entrantId}", exc_info=True)
        return False, None
    

def allEntrantsFilter(response : dict) -> tuple[list, int]:
    """
    Filters an events entrants in desired format. Returns the entrants list
    """
    filteredEntrants = []
    attendeeAmount = 0
    for entrant in response["data"]["event"]["entrants"]["nodes"]:
        success, filteredEntrant = entrantFilter(entrant)
        attendeeAmount+=1
        if success:
            filteredEntrants.append(filteredEntrant)
        continue
    
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
        logging.error("Owner doesnt exist", exc_info=True)
        return None
    except OwnerDiscriminatorError:
        logging.error("Owner discriminator doesnt exist", exc_info=True)
        return None
    except OwnerIdError:
        logging.error("Owner id doesnt exist??", exc_info=True)
        return None
    except OwnerGamerTagError:
        logging.error("Owner player/gamertag doesnt exist", exc_info=True)
        return None
    except:
        logging.error("Unknown error. Contact", exc_info=True)
        return None

def getMainEvent(events : list, link : str) -> dict | None:
    singlesEvents = []
    for event in events:
        try:
            isSingles = (event["name"].find("Singles") != -1) or (event["name"].find("SINGLES") != -1) or (event["name"].find("singles") != -1)
            isCasual = (event["name"].find("Casual") != -1) or (event["name"].find("casual") != -1) or (event["name"].find("CASUAL") != -1)
            redemption = (event["name"].find("redemption") != -1) or (event["name"].find("REDEMPTION") != -1) or (event["name"].find("Redemption") != -1)
            amateur = (event["name"].find("amateur") != -1) or (event["name"].find("AMATEUR") != -1) or (event["name"].find("Amateur") != -1)
            isRedemption = redemption or amateur
            completed = event["state"] == "COMPLETED"
            if isSingles and (not isCasual) and (not isRedemption):
                if completed:
                    singlesEvents.append(event)
                else:
                    raise InProgressError(link, event["name"])
        except InProgressError:
            logging.error("Tournament hasnt been completed", exc_info=True)
    if singlesEvents == []:
        return False, None
    if len(singlesEvents) == 1:
        return True, singlesEvents[0]
    else:
        return False, None
    

    
    

def tournamentFilter(tournament : dict) -> tuple[bool, dict | None]:
    """
    Safe function to get startgg tournament info:\n

    """
    try:
        #If these dont work i dont even know. Should always work
        tournamentLink = "https://www.start.gg/"+tournament["slug"]
        tournamentStartAt = tournament["startAt"]
        success, tournamentMainEvent = getMainEvent(tournament["events"], tournamentLink)
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
                "date" : toDate(tournamentStartAt)
            }
        else:
            raise EventMissingError(tournamentLink, None)
        
    except EventMissingError:
        logging.error("None of the events matches requirements for singles", exc_info=True)
        return False, None
    except:
        logging.error("Unknown error", exc_info=True)
        return False, None
    
        
    

def allTournamentsFilter(response):
    filteredTournaments = []
    for tournament in response["data"]["tournaments"]["nodes"]:
        #Filter
        success, filteredTournament = tournamentFilter(tournament)
        #If good, append
        if success:
            filteredTournaments.append(filteredTournament)

    return filteredTournaments