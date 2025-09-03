import xlsxwriter as xl
from xlsxwriter.color import Color
import os
from time import sleep

def addSuffix(number):
    """
    Adds the appropriate ordinal suffix (st, nd, rd, th) to a number
    """
    if 11 <= number % 100 <= 13:
        return str(number) + "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
        return str(number) + suffix


def tourneyScore(placement, eventTier):
    maxScore = float(tierEnum[eventTier]*100)
    placeScore = placementScore(placement)
    return maxScore/(float(placeScore)**0.5)

def tournamentIterator(countingTournaments, tournamentIds):
    for tournament in countingTournaments:
        if tournament.get("mainEvent") is None:
            continue
        if tournament["mainEvent"] is None:
            continue
        if tournament["mainEvent"].get("id") is None:
            continue
        if tournament["mainEvent"]["id"] is None:
            continue
        if tournament["mainEvent"]["id"] in tournamentIds:
            yield tournament

def placementScore(placement):
    """takes player seed as input, gives expected rounds from winning the tournament."""
    import math
    placement = int(placement)
    if placement <= 1:
        return 1
    return 1+(math.floor(math.log2(placement - 1)) + math.ceil(math.log2(2 * placement / 3)))

tourneyFormats = {
        "2-3" : {"bg_color" : "#ffffff", "font_color" : "#000000", "border" : 1},
        "4-6" : {"bg_color" : "#60b66f", "font_color" : "#000000", "border" : 1},
        "7-9" : {"bg_color" : "#5e7ce0", "font_color" : "#000000", "border" : 1},
        "10-17" : {"bg_color" : "#7954a3", "font_color" : "#000000", "border" : 1},
        "18+" : {"bg_color" : "#cd891b", "font_color" : "#000000", "border" : 1},
        "Regional" : {"bg_color" : "#d852ab", "font_color" : "#000000", "border" : 1, "bold" : True},
        "Major" : {"bg_color" : "#e70f0f", "font_color" : "#FFFFFF", "border" : 1, "bold" : True},
        "OOR Major" :{"bg_color" : "#f1dc7b", "font_color" : "#000000", "border" : 1, "bold" : True}
    } 

tierPlaceEnum = {
        "2-3" : 3    ,
        "4-6" : 6    ,
        "7-9" : 8    ,
        "10-17" : 12  ,
        "18+" : 12    ,
        "Regional" : 32    ,
        "Major" : 48   ,
        "OOR Major" : 0   
    }

tierEnum = {
        "2-3" : 1    ,
        "4-6" : 2    ,
        "7-9" : 3    ,
        "10-17" : 5  ,
        "18+" : 6    ,
        "Regional" : 7    ,
        "Major" : 8   ,
        "OOR Major" : 9   
    } 

class Exporter:

    def __init__(self, system, docuDir):
        self.script_dir = docuDir
        self.system = system
        pass

    def competitor_results(self, competitor, tracklist, countingTournaments):

        def laa():
            for tournament in tournamentIterator(countingTournaments, {t["tournamentId"] for t in competitor["tournaments"]}):
                wins, losses = {}, {}
                for set in tournament["mainEvent"]["sets"]:
                    try:
                        if not (set["winner"]["discriminator"]) in tracklist or not (set["winner"]["discriminator"]):
                            continue
                        if set["winner"]["discriminator"] == competitor["discriminator"]:
                            if set["loser"]["discriminator"] in tracklist:
                                wins[set["loser"]["discriminator"]] = wins.get(set["loser"]["discriminator"], 0) + 1
                        elif set["loser"]["discriminator"] == competitor["discriminator"]:
                            losses[set["winner"]["discriminator"]] = losses.get(set["winner"]["discriminator"], 0) + 1
                    except:
                        self.system.st(f"Error with a set in {tournament["name"]}")

                placement = next((entrant["placement"] for entrant in tournament["mainEvent"]["entrants"] if entrant["entrantId"] in competitor["setOfEntrantIds"]), 0)
                yield {"tournament": tournament, "wins": wins, "losses": losses, "placement": placement}
        return laa()

    def _getFilepath(self, itemName):
        return os.path.join(self.script_dir, itemName+".xlsx")
        
    def export(self, seasonNumber):
        acquiered = self.system.writerLock.acquire(timeout=3)

        if acquiered:
            self.number = seasonNumber
            self.system.st(f"Exporting Season {self.number}")
            self.workbook = xl.Workbook(self._getFilepath(seasonNumber))
            self.system.st("Creating tracklist")
            self.createTracklist()
            self.system.st(f"Creating Season {self.number} Brackets")
            self.createBrackets()
            self.system.st(f"Creating Season {self.number} Contenders")
            status = self.createCompetitors()

            self.createH2H()
            print("through exporting")
            self.workbook.close()
            self.system.UI.status.set("Exported to Documents/Wiener Exports folder")
            self.system.writerLock.release()
        else:
            return

    def createTracklist(self):
        self.system.getTracklist()
        workbook = self.workbook
        tracklist = self.system.tracklistInfo
        if len(tracklist) == 0:
            self.system.st("Tracklist is empty")
            sleep(3)

        trackSheet = workbook.add_worksheet("Tracklist")
        blacked = workbook.add_format({"bg_color" : Color("#000000")})
        tabFormat = workbook.add_format({"align" : "center", "valign" : "center", "bold" : True, "bottom" : 2})
        rightBorderTabFormat = workbook.add_format({"align" : "center", "valign" : "center", "bold" : True, "right" : 5,"bottom" : 2})
        rightBorder = workbook.add_format({"right" : 5})
        trackSheet.set_column(1,2,2.5)
        trackSheet.set_column(3,3,15)
        trackSheet.set_column(4,5,16)
        trackSheet.set_column(6,6,50)
        #Blacked top row
        for i in range(8):
            trackSheet.write(0,i,"",blacked)

        trackSheet.write(1, 0, "", blacked)
        trackSheet.merge_range(1, 1, 1, 3, "Player", tabFormat)
        trackSheet.write(1,4,"Region", rightBorderTabFormat)
        trackSheet.write(1,5,"startgg", tabFormat)
        trackSheet.write(1,6, "Notes", tabFormat)
        trackSheet.write(1, 7, "", blacked)

        for i, player in enumerate(tracklist):
            trackSheet.write(2+i, 0, "", blacked)

            trackSheet.write(2+i, 3, player["name"])
            trackSheet.write(2+i, 4, "", rightBorder)
            trackSheet.write(2+i, 5, player["discriminator"])
            trackSheet.write(2+i, 7, "", blacked)
        
        return trackSheet

    def createBrackets(self):
        workbook = self.workbook
        tournaments = self.system.tournamentsInfo
        tracklist = self.system.getTrackedDiscriminators()
        tabFormat = workbook.add_format({"valign":"center", "bold" : True, "bg_color" : "#aaaaaa"})

        trackSheet = workbook.add_worksheet(f"S{self.number}B")
        trackSheet.set_column(0,0,8)
        trackSheet.set_column(1,1,40)
        trackSheet.set_column(2,4,15)
        trackSheet.set_column(5,5,30)
        trackSheet.set_column(6,6,50)
        trackSheet.write(0,0, "Date", tabFormat)
        trackSheet.write(0,1, "Tournament", tabFormat)
        trackSheet.write(0,2, "T. Players", tabFormat)
        trackSheet.write(0,3, "Bracket Size", tabFormat)
        trackSheet.write(0,4, "Total Points", tabFormat)
        trackSheet.write(0,5, "Link", tabFormat)
        trackSheet.write(0,6, "Notable Placements", tabFormat)
        index = 0
          
        borderFormat = workbook.add_format({"border" : 1})
        borderFormat.set_text_wrap()
        tourneyNum = len(tournaments)
        for i, tournament in enumerate(tournaments):
            try:
                self.system.st(f"Creating Season {self.number} Brackets\tTournament {i+1} of {tourneyNum}")
                if not tournament["counting"]:
                    continue
                tourneyFormat = workbook.add_format(tourneyFormats[tournament["eventTier"]])
                trackSheet.write(1+index,0,tournament["date"])
                trackSheet.write(1+index,1,tournament["name"], tourneyFormat)
                trackSheet.write(1+index,2,tournament["trackedScore"], tourneyFormat)
                trackSheet.write(1+index,3,tournament["attendeeAmount"], tourneyFormat)
                trackSheet.write(1+index,4,tournament["totalScore"], tourneyFormat)
                trackSheet.write(1+index,5,tournament["link"], tourneyFormat)
                notable = ""
                placements = tierPlaceEnum[tournament["eventTier"]]
                for j, entrant in enumerate(tournament["mainEvent"]["entrants"]):
                    if (j) > placements and not entrant["discriminator"] in tracklist:
                        continue
                    notable+=f"{entrant["name"]} ({addSuffix(entrant["placement"])}), "
                trackSheet.write(1+index, 6, notable, borderFormat)
                index+=1
            except:
                self.system.st(f"Unknown error when making bracket {tournament["name"]}")
                sleep(3)
        
    def createCompetitors(self):
        workbook = self.workbook
        tracklist = self.system.getTrackedDiscriminators()

        countingTournaments = self.system.getValidTournaments()
        trackSheet = workbook.add_worksheet(f"S{self.number}C")
        tabFormat = workbook.add_format({"valign":"center", "bold" : True, "bg_color" : "#aaaaaa"})
        boldFormat = workbook.add_format({"bold" : True})
        trackSheet.set_column(0,0,14)
        trackSheet.set_column(1,1,47)
        trackSheet.set_column(2,3,30)
        trackSheet.write(0, 0, "Player", tabFormat)
        trackSheet.write(0, 1, "Notable Placements", tabFormat)
        trackSheet.write(0, 2, "Notable Wins", tabFormat)
        trackSheet.write(0, 3, "Losses", tabFormat)
        rowt = 1

        nform = workbook.add_format({"top" : 5,})
        nform.set_text_wrap(True)
        normalform = workbook.add_format()
        normalform.set_text_wrap(True)
        bform = workbook.add_format({"top" : 5, "bold" : True})
        newCompetitors = []
        tracklist = self.system.getTrackedDiscriminators()
        countingTournaments = self.system.getValidTournaments()
        contenderNum = len(tracklist)
        self.competitors = self.system.getCompetitors()
        self.competitors = self.sortCompetitors()
        for i, competitor in enumerate(self.competitors):
            try:
                self.system.st(f"Creating Season {self.number} Contenders. {i+1} of {contenderNum}")
                if competitor["tournaments"] is None or competitor["tournaments"] == []:
                    continue
                
                hasBorder = False
                if hasBorder:
                    trackSheet.write(rowt, 0, competitor["name"], boldFormat)
                else:
                    trackSheet.write(rowt, 0, competitor["name"], bform)
                
                for result in self.competitor_results(competitor, tracklist, countingTournaments):
                    tform = tourneyFormats[result["tournament"]["eventTier"]]
                    tform["top"] = 5
                    tform = workbook.add_format(tform)
                    tourneyForm = workbook.add_format(tourneyFormats[result["tournament"]["eventTier"]])
                    placementName = ""
                    for entrant in result["tournament"]["mainEvent"]["entrants"]:
                        if entrant["id"] == competitor["id"]:
                            placementName = addSuffix(entrant["placement"])
                            break
                    placementName += " - "+result["tournament"]["name"]

                    if hasBorder:
                        trackSheet.write(rowt, 1, placementName, tform)
                    else:
                        trackSheet.write(rowt, 1, placementName, tourneyForm)
                    winLen = len(result["wins"].keys())
                    currentI=1
                    Wins = ""
                    for discriminator, winAmount in result["wins"].items():
                        name = self.system.getPlayer(discriminator)["name"]
                        Wins+=name
                        if winAmount != 1:
                            Wins+= f"({winAmount}x)"
                        if currentI != winLen:
                            Wins+=", "
                        currentI+=1
                    if hasBorder:
                        trackSheet.write(rowt, 2, Wins, normalform)
                    else:
                        trackSheet.write(rowt, 2, Wins, nform)
                    Losses = ""
                    lossLen = len(result["losses"].keys())
                    currentI = 1
                    for discriminator, lossAmount in result["losses"].items():
                        name = self.system.getPlayer(discriminator)["name"]
                        Losses+=name
                        if not lossAmount == 1:
                            Losses+= f"({lossAmount}x)"
                        if currentI != lossLen:
                            Losses+=", "
                        currentI+=1
                    if hasBorder:
                        trackSheet.write(rowt, 3, Losses, normalform)
                    else:
                        trackSheet.write(rowt, 3, Losses, nform)

                    if not hasBorder:
                        hasBorder = True
                    rowt+=1
            except:
                self.system.st(f"Some error with contender {competitor["name"]}")
                sleep(3)
        self.competitors = self.system.getCompetitors()
        return True

    def sortCompetitors(self):
        self.system.st("Approx. Contender sorting based on result")
        newCompetitors = []
        tracklist = self.system.getTrackedDiscriminators()
        countingTournaments = self.system.getValidTournaments()
        for competitor in self.competitors:
            try:
                totalScore = 0
                totalWins = dict()
                totalLosses = dict()
                
                for result in self.competitor_results(competitor, tracklist, countingTournaments):
                    totalScore+=tourneyScore(result["placement"], result["tournament"]["eventTier"])
                    for k, v in result["wins"].items():
                        totalWins[k] = totalWins.get(k, 0) + v
                    for k, v in result["losses"].items():
                        totalLosses[k] = totalLosses.get(k, 0) + v
                competitor["rankScore"] = totalScore
                competitor["setWins"] = totalWins
                competitor["setLosses"] = totalLosses
                newCompetitors.append(competitor)
            except:
                self.system.st(f"Unknown sort error with competitor {competitor["name"]}")
                sleep(3)
        newCompetitors.sort(key=lambda c: c["rankScore"], reverse=True)
        return newCompetitors
    
    def createH2H(self):
        self.competitors = self.system.getCompetitors()
        self.competitors = self.sortCompetitors()
        self.system.st("Creating H2H")
        workbook = self.workbook
        tracksheet = workbook.add_worksheet(f"S'{self.number} H2H")
        blacked = workbook.add_format({"bg_color" : Color("#000000")})
        for i, competitor in enumerate(self.competitors):
            try:
                tracksheet.write(0, i+1, competitor["name"])
                tracksheet.write(i+1, 0, competitor["name"])
                for j, competitor2 in enumerate(self.competitors):
                    if i==j:
                        tracksheet.write(i+1, j+1, "", blacked)
                    else:
                        msg = ""
                        msg+=str(competitor["setWins"].get(competitor2["discriminator"],0)) + "-" + str(competitor["setLosses"].get(competitor2["discriminator"],0))
                        tracksheet.write(i+1, j+1, msg)
            except:
                self.system.st(f"Unknown error with {competitor["name"]}")
                sleep(3)
        pass