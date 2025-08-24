import xlsxwriter as xl
from xlsxwriter.color import Color
import os

class Exporter:

    def __init__(self, system):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.system = system
        pass

    def _getFilepath(self, itemName):
        return os.path.join(self.script_dir, itemName+".xlsx")
        
    def export(self, seasonNumber):
        self.workbook = xl.Workbook(self._getFilepath(seasonNumber))
        self.createTracklist(self.workbook)
        """self.createBrackets(self.workbook)
        self.createCompetitors(self.workbook)
        self.createH2H(self.workbook)"""
        self.workbook.close()

    def createTracklist(self, workbook: xl.Workbook):
        self.system.getTracklist()
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
