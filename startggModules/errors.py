class EntrantError(Exception):
    def __init__(self, message, entrantId):
        self.entrantId = entrantId
        super().__init__(f"{message} entrantId({entrantId})")

class GamerTagError(EntrantError):
    def __init__(self, entrantId):
        super().__init__("No gamer tag present", entrantId)

class UserIdError(EntrantError):
    def __init__(self, entrantId):
        super().__init__("No user id", entrantId)

class UserError(EntrantError):
    def __init__(self, entrantId):
        super().__init__("No user", entrantId)

class PlacementError(EntrantError):
    def __init__(self, entrantId):
        super().__init__("No placement", entrantId)

class UserDiscriminatorError(EntrantError):
    def __init__(self, entrantId):
        super().__init__("No discriminator", entrantId)

class DiscriminatorError(Exception):
    def __init__(self, discriminator):
        self.discriminator= discriminator
        super().__init__(f"Not valid discriminator: {discriminator}")

class TournamentError(Exception):
    def __init__(self, message, link, eventName):
        self.eventName = eventName
        self.link = link        
        super().__init__(f"{message}.\nLink: {link}\nEvent name: {eventName}")

class ZeroAttendees(TournamentError):
    def __init__(self, link, eventName):
        super().__init__("This event has 0 attendees", link, eventName)

class InProgressError(TournamentError):
    def __init__(self, link, eventName):
        super().__init__("This tournament is still in progress", link, eventName)

class EventMissingError(TournamentError):
    def __init__(self, link, eventName):
        super().__init__("Error with finding event. Let me know if this happens", link, eventName)

class OwnerError(TournamentError):
    def __init__(self, link, eventName):
        super().__init__("Error with tournament owner. Let me know if this happens", link, eventName)

class OwnerDiscriminatorError(TournamentError):
    def __init__(self, link, eventName):
        super().__init__("Error with tournament owner. Let me know if this happens", link, eventName)

class OwnerGamerTagError(TournamentError):
    def __init__(self, link, eventName):
        super().__init__("Error with tournament owner. Let me know if this happens", link, eventName)

class OwnerIdError(TournamentError):
    def __init__(self, link, eventName):
        super().__init__("Error with tournament owner. Let me know if this happens", link, eventName)