import xlsxwriter as xl
from xlsxwriter.color import Color
import os

def addSuffix(number):
    """
    Adds the appropriate ordinal suffix (st, nd, rd, th) to a number
    """
    if 11 <= number % 100 <= 13:
        return str(number) + "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
        return str(number) + suffix

class Exporter:

    def __init__(self, system):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.system = system
        pass

    def _getFilepath(self, itemName):
        return os.path.join(self.script_dir, itemName+".xlsx")
        
    def export(self, seasonNumber):
        self.number = seasonNumber
        self.workbook = xl.Workbook(self._getFilepath(seasonNumber))

        self.createTracklist()
        self.createBrackets()
        """self.createCompetitors()
        self.createH2H()"""
        self.workbook.close()

    def createTracklist(self):
        self.system.getTracklist()
        workbook = self.workbook
        tracklist = self.system.tracklistInfo
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
        tourneyFormats = {
        "2-3" : {"bg_color" : "#ffffff", "font_color" : "#000000", "border" : 1},
        "4-6" : {"bg_color" : "#60b66f", "font_color" : "#000000", "border" : 1},
        "7-9" : {"bg_color" : "#5e7ce0", "font_color" : "#000000", "border" : 1},
        "10-17" : {"bg_color" : "#7954a3", "font_color" : "#000000", "border" : 1},
        "18+" : {"bg_color" : "#d852ab", "font_color" : "#000000", "border" : 1},
        "Regional" : {"bg_color" : "#aaaaaa", "font_color" : "#000000", "border" : 1},
        "Major" : {"bg_color" : "#e70f0f", "font_color" : "#FFFFFF", "border" : 1},
        "OOR Major" :{"bg_color" : "#f1dc7b", "font_color" : "#000000", "border" : 1}
    }   
        borderFormat = workbook.add_format({"border" : 1})
        borderFormat.set_text_wrap()
        for i, tournament in enumerate(tournaments):
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
            for entrant in tournament["mainEvent"]["entrants"]:
                if not entrant["discriminator"] in tracklist:
                    continue
                notable+=f"{entrant["name"]} ({addSuffix(entrant["placement"])}), "
            trackSheet.write(1+index, 6, notable, borderFormat)
            index+=1
        
