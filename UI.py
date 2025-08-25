import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import tkcalendar

tournamentTiers = ["OOR Major", "Major", "Regional","18+","10-17","7-9","4-6","2-3","None"]
tournamentTierColors = {
    "2-3" : "white smoke",
    "None" : "gray",
    "4-6" : "dark sea green",
    "7-9" : "SlateBlue1",
    "10-17" : "DarkOrchid4",
    "18+" : "dark orange",
    "Regional" : "maroon1",
    "Major" : "red2",
    "OOR Major" : "DarkGoldenrod1"
}

#Functions
def createLabelFrame(text, parent, height, color = None):
    if color is None:
        frame = ctk.CTkFrame(master=parent, height=height)
    else:
        frame = ctk.CTkFrame(master=parent, height=height, fg_color=color)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    label = ctk.CTkLabel(master=frame, text=text, anchor="center")
    label.grid(row=0, column=0)
    return frame

class UI:

    def __init__(self, system):
        self.system = system
        self.schedule = []
        self._createWindow()
        self._createMainTabs()
        self._createMainPage()
        self.currentPage = 1
        self.tournaments = dict()
        pass

    def start(self):
        self.window.mainloop()

    def _exit(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.system.exit()
            self.window.destroy()

    def _createWindow(self):
        self.window = ctk.CTk()
        self.window.protocol("WM_DELETE_WINDOW", self._exit)
        self.window.geometry(str(400)+"x"+str(300))
        self.window.title("Wiener PR Helper")
        
    def createLinkFrame(self, link, parent, height, color = None):
        if color is None:
            frame = ctk.CTkFrame(master=parent, height=height)
        else:
            frame = ctk.CTkFrame(master=parent, height=height, fg_color=color)
        frame.grid_propagate(False)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        linkLabel = ctk.CTkLabel(master=frame, text=link, anchor="center")
        linkLabel.bind("<Button-1>", lambda event, x=link: self.system.openLink(x))
        linkLabel.grid(row=0, column=0, padx=2, pady=2)

        return frame

    def _start(self):
        self.window.mainloop()
    
    def _getTournaments(self):
        start, end = self.seasonStart, self.seasonEnd
        startTimestamp = datetime.combine(start.get_date(), datetime.min.time()).timestamp()
        endTimestamp = datetime.combine(end.get_date(), datetime.max.time()).timestamp()
        self.system.getTournaments(startTimestamp, endTimestamp)

    def _createMainPage(self):
        mainPage = self.mainTabs["tabs"]["Main"]
        mainPage.columnconfigure(0, weight=1)
        mainPage.columnconfigure(2, weight=1)
        
        self._createSeasonPicker()
        self._createTrackPlayers()
        self._createExport()

    def _createSeasonPicker(self):
        mainPage = self.mainTabs["tabs"]["Main"]
        #Container for season picker
        seasonFrameChoose = ctk.CTkFrame(master=mainPage,height=200)
        seasonStartText, seasonEndText = ctk.CTkLabel(master=seasonFrameChoose, text="Start of season"), ctk.CTkLabel(master=seasonFrameChoose, text="End of season")
        self.seasonStart, self.seasonEnd = tkcalendar.DateEntry(master=seasonFrameChoose), tkcalendar.DateEntry(master=seasonFrameChoose)
        getTournamentsButton = ctk.CTkButton(master=seasonFrameChoose, text="Get tournaments", command=self._getTournaments)
        
        #Grid season date
        seasonFrameChoose.grid(row=0, column=1, sticky="n", pady=7)
        seasonFrameChoose.columnconfigure(1, minsize=40)
        seasonFrameChoose.columnconfigure(3, minsize=40)
        seasonStartText.grid(row=0, column=0), seasonEndText.grid(row=0, column=2)
        self.seasonStart.grid(row=1, column=0), self.seasonEnd.grid(row=1, column=2)
        getTournamentsButton.grid(row=0, rowspan=2, column=4,)

    def _createExport(self):
        mainPage = self.mainTabs["tabs"]["Main"]

        exportFrame = ctk.CTkFrame(master=mainPage, height=200)

        #Entry field
        seasonNum = ctk.StringVar()
        seasonEntryField = ctk.CTkEntry(master=exportFrame, textvariable=seasonNum, width=140)
        exportButton = ctk.CTkButton(master=exportFrame, command=lambda: self.system.export(seasonEntryField), text="Export")
        seasonEntryField.grid(row=0, column=0)
        exportButton.grid(row=0, column=1)
        exportFrame.grid(row=2, column=1)

    def _trackPlayer(self):
        field = self.trackPlayerEntry
        discriminator = field.get().strip()
        field.delete(0,'end')
        
        playerStatus = self.system.trackPlayer(discriminator)
        if playerStatus == -1:
            field.insert(0,"Error. Wrong discriminator?")
        if playerStatus == 0:
            field.insert(0, "Player already tracked")
        if playerStatus == 1:
            field.insert(0, "Player added to tracklist")

    def _createTrackPlayers(self):
        mainPage = self.mainTabs["tabs"]["Main"]
        windowBG = self.window.cget("bg")
        
        #Main frame
        addPlayerFrame = ctk.CTkFrame(master=mainPage)

        #Text within entry field
        self.playerName = ctk.StringVar()
        playerName = self.playerName
        playerName.set("startgg discriminator")

        #Entry field
        self.trackPlayerEntry = ctk.CTkEntry(master=addPlayerFrame, textvariable=playerName, width=200)
        entryField = self.trackPlayerEntry
        entryField.bind("<Button-1>", lambda event: playerName.set(""))

        #Track button
        addButton = ctk.CTkButton(master=addPlayerFrame, command=self._trackPlayer, text="Track player")

        #Layout
        addPlayerFrame.grid(row=1, column=1, pady=7)
        entryField.grid(row=0, column=0)
        addButton.grid(row=0, column=2)

        addPlayerFrame.columnconfigure(1, minsize=40)


    def _switchTab(self, tabName):
        for child in self.mainBody.winfo_children():
            child.grid_forget()
        self.mainTabs["tabs"][tabName].grid(row=0, column=0, sticky="nswe")
    
    def updateTournamentTier(self, chosenTier, tournamentId, tournamentFrame):
        self.system.updateTournamentTier(chosenTier, tournamentId)
        newColour = tournamentTierColors[chosenTier]
        tournamentFrame.configure(fg_color=newColour)

    def _createSingleTournamentFrame(self, tournament, parent):
        #Text and properties
        date = tournament["date"]
        name = tournament["name"]
        attendeeAmount = tournament["attendeeAmount"]
        link = tournament["link"]
        tournamentColor = tournamentTierColors[tournament["eventTier"]]
        
        #Creation
        tournamentFrame = ctk.CTkFrame(master=parent, height=80,)
        dateFrame = createLabelFrame(date, tournamentFrame, 80, ["#2d9f8c", "#186155"])
        dateFrame.grid(row=0, column=0,sticky="nswe", padx=2, pady=2)

        nameLinkFrame = ctk.CTkFrame(master=tournamentFrame, height=80)
        nameLinkFrame.columnconfigure(0, weight=1)
        nameLinkFrame.rowconfigure(0, weight=1)
        nameLinkFrame.rowconfigure(1, weight=1)

        nameFrame = createLabelFrame(name, nameLinkFrame, 40)
        nameFrame.grid(row=0, column=0, sticky="nswe")
        linkFrame = self.createLinkFrame(link, nameLinkFrame, 40, ["#2d9f8c", "#186155"])
        linkFrame.grid(row=1, column=0, sticky="nswe")

        nameLinkFrame.grid(row=0, column=1, sticky="nswe", padx=2, pady=2)

        attendeeFrame = createLabelFrame(attendeeAmount, tournamentFrame, 80)
        attendeeFrame.grid(row=0, column=2, sticky="nswe", padx=2, pady=2)

        #Gotta have openable link

        #Choose tier
        tierFrame = ctk.CTkFrame(master=tournamentFrame, fg_color=tournamentColor, height=80)
        tierFrame.grid(row=0, column=3, sticky="wens", padx=2, pady=2)
        tierFrame.columnconfigure(0, weight=1)
        tierFrame.rowconfigure(0, weight=1)
        tierString = ctk.StringVar(value=tournament["eventTier"])
        tierList = ctk.CTkComboBox(master=tierFrame, values=tournamentTiers, variable=tierString,command=lambda chosenTier, tournamentId=tournament["id"], frame=tierFrame: self.updateTournamentTier(chosenTier, tournamentId, frame))
        tierList.grid(row=0, column=0)

        #Wether it counts
        countingVar = ctk.IntVar(value=(tournament["counting"] and 1 or 0))
        countingFrame = ctk.CTkFrame(master=tournamentFrame, width=80, height=80)
        countingCheck = ctk.CTkCheckBox(master=countingFrame, text="",variable=countingVar, command=lambda id=tournament["id"]: self.system.updateCounting(id, countingVar.get()), width=40, height=40, checkbox_width=40, checkbox_height=40)
        countingFrame.grid(row=0, column=4, sticky="wnse", padx=2, pady=2)
        countingFrame.grid_propagate(False)
        countingFrame.rowconfigure(0, weight=1)
        countingFrame.columnconfigure(0, weight=1)
        countingCheck.pack(expand=True)
        
        tournamentFrame.rowconfigure(0, minsize=40, weight=0)
        tournamentFrame.columnconfigure(0,minsize=80, weight=0)
        tournamentFrame.columnconfigure(1, minsize=60,weight=1)
        tournamentFrame.columnconfigure(2, minsize=160,weight=0)
        tournamentFrame.columnconfigure(3, minsize=220,weight=0)
        tournamentFrame.columnconfigure(4, minsize=80,weight=0)

        return tournamentFrame

    def createPlayerlist(self):
        trackedFrame = self.mainTabs["tabs"]["All players"]
        trackedFrame.rowconfigure(0, weight=1)
        trackedFrame.columnconfigure(0, weight=1)
        trackedPlayers = self.system.tracklistInfo
        for widget in trackedFrame.winfo_children():
            widget.destroy()

        scrollbar = ctk.CTkScrollableFrame(master=trackedFrame)
        
        for i, player in enumerate(trackedPlayers):
            #print("creating a frame")
            masterFrame = ctk.CTkFrame(master=scrollbar)
            masterFrame.columnconfigure(0, weight=1)
            masterFrame.columnconfigure(1, weight=1)
            singleFrame = createLabelFrame(player["name"], masterFrame, 40)
            singleFrame.grid(row=0, column=0, sticky="nswe")
            untrackButton = ctk.CTkButton(master=masterFrame, text="Untrack", command= lambda x=player["discriminator"]: self.system.untrackPlayer(x))
            untrackButton.grid(row=0, column=1, sticky="nswe")
            masterFrame.grid(row=i, column=1, sticky="nswe", padx=2, pady=2)

        scrollbar.columnconfigure(0, minsize=10, weight=1)
        scrollbar.columnconfigure(1, weight=4, minsize=200)
        scrollbar.columnconfigure(2, minsize=10, weight=1)

        scrollbar.grid(row=0, column = 0, sticky = "nswe")

    def createTracklist(self):
        trackedFrame = self.mainTabs["tabs"]["Tracked Players"]
        trackedFrame.rowconfigure(0, weight=1)
        trackedFrame.columnconfigure(0, weight=1)
        trackedPlayers = self.system.tracklistInfo
        for widget in trackedFrame.winfo_children():
            widget.destroy()

        scrollbar = ctk.CTkScrollableFrame(master=trackedFrame)
        
        for i, player in enumerate(trackedPlayers):
            #print("creating a frame")
            masterFrame = ctk.CTkFrame(master=scrollbar)
            masterFrame.columnconfigure(0, weight=1)
            masterFrame.columnconfigure(1, weight=1)
            singleFrame = createLabelFrame(player["name"], masterFrame, 40)
            singleFrame.grid(row=0, column=0, sticky="nswe")
            untrackButton = ctk.CTkButton(master=masterFrame, text="Untrack", command= lambda x=player["discriminator"]: self.system.untrackPlayer(x))
            untrackButton.grid(row=0, column=1, sticky="nswe")
            masterFrame.grid(row=i, column=1, sticky="nswe", padx=2, pady=2)

        scrollbar.columnconfigure(0, minsize=10, weight=1)
        scrollbar.columnconfigure(1, weight=4, minsize=200)
        scrollbar.columnconfigure(2, minsize=10, weight=1)

        scrollbar.grid(row=0, column = 0, sticky = "nswe")



    def createTournaments(self):
        print("hey im creating some frames")
        tournamentsFrame = self.mainTabs["tabs"]["Tournaments"]
        tournaments = self.system.tournamentsInfo
        for widget in tournamentsFrame.winfo_children():
            widget.destroy()
        #Creation
        scrollbar = ctk.CTkScrollableFrame(master=tournamentsFrame)
        tabsFrame = ctk.CTkFrame(master=tournamentsFrame)
        dateFrame = createLabelFrame("Date", tabsFrame, 40,["#2d9f8c", "#186155"])
        tournamentFrame = createLabelFrame("Tournament", tabsFrame, 40,["#2d9f8c", "#186155"])
        attendeeFrame = createLabelFrame("Attendees", tabsFrame, 40,["#2d9f8c", "#186155"])
        tierFrame = createLabelFrame("Event tier", tabsFrame, 40,["#2d9f8c", "#186155"])
        countingFrame = createLabelFrame("PR?", tabsFrame, 40,["#2d9f8c", "#186155"])

        #

        dateFrame.grid(row=0, column=0, sticky="nswe", padx=2, pady=2)
        tournamentFrame.grid(row=0, column=1, sticky="nswe", padx=2, pady=2)
        attendeeFrame.grid(row=0, column=2, sticky="nswe", padx=2, pady=2)
        tierFrame.grid(row=0, column=3, sticky="nswe", padx=2, pady=2)
        countingFrame.grid(row=0, column=4, sticky="nswe", padx=2, pady=2)

        tabsFrame.columnconfigure(0,minsize=100, weight=0)
        tabsFrame.columnconfigure(1,minsize=60, weight=1)
        tabsFrame.columnconfigure(2,minsize=160, weight=0)
        tabsFrame.columnconfigure(3,minsize=220, weight=0)
        tabsFrame.columnconfigure(4,minsize=80, weight=0)
        tabsFrame.rowconfigure(0, minsize=60, weight=0)
        tabsFrame.grid(row=0, column=0, padx=[40,60], sticky="we")
        tabsFrame.grid_propagate(True)

        if len(tournaments)>50:
            lastIndex = 0
            for i, tournament in enumerate(tournaments[(self.currentPage-1)*50:self.currentPage*50]):
                singleFrame = self._createSingleTournamentFrame(tournament, scrollbar)
                singleFrame.grid(row=i, column = 0, padx=2, pady= 2,sticky="nswe")
                lastIndex = i
            pageFrame = ctk.CTkFrame(master=scrollbar)
            prevButton, nextButton = ctk.CTkButton(master=pageFrame, text="Prev page", command= lambda: self.changeTPage(-1) ), ctk.CTkButton(master=pageFrame, text="Next page", command= lambda: self.changeTPage(1) )
            prevButton.grid(row=0, column = 0)
            nextButton.grid(row=0, column = 1)
            pageFrame.grid(row=lastIndex+1, column=0)
        else:
            for i, tournament in enumerate(tournaments[(self.currentPage-1)*50:self.currentPage*50]):
                singleFrame = self._createSingleTournamentFrame(tournament, scrollbar)
                singleFrame.grid(row=i, column = 0, padx=2, pady= 2,sticky="nswe")
            

        scrollbar.columnconfigure(0, weight=1)
        #The poor children!
        

        scrollbar.grid(row=1, column=0, padx=30, sticky="nswe")
        tournamentsFrame.rowconfigure(1, minsize=100, weight=1)
        tournamentsFrame.columnconfigure(0, minsize=300, weight=1)
        tournamentsFrame.rowconfigure(0, minsize=40, weight=0)
        print("should be done now")

    def changeTPage(self, add):
        self.currentPage += add
        self.createTournaments()

    def _createMainTabs(self):
        #Creation
        self.mainTabs = {
            "tabsFrame" : ctk.CTkFrame(master=self.window, height=50),
        }
        self.mainBody = ctk.CTkFrame(master=self.window, width=300, height=300)
        self.mainTabs["tabs"] = {
            "Main" : ctk.CTkFrame(master=self.mainBody),
            "Tracked Players" : ctk.CTkFrame(master=self.mainBody),
            "Tournaments" : ctk.CTkFrame(master=self.mainBody),
            "All players" : ctk.CTkFrame(master=self.mainBody),
            "Settings" : ctk.CTkFrame(master=self.mainBody),
        }
       
        self.mainTabs["buttons"] = {}
        for name in self.mainTabs["tabs"].keys():
            self.mainTabs["buttons"][name] = ctk.CTkButton(master=self.mainTabs["tabsFrame"], text=name, command= lambda n=name: self._switchTab(n))

        for i, button in enumerate(self.mainTabs["buttons"].values()):
            button.grid(row=0, column=1+i, padx=6, pady=6)
            self.mainTabs["tabsFrame"].columnconfigure(1+i, minsize=30,weight=1)
        
        #Layout
        self.mainTabs["tabsFrame"].grid(row=0, column=0, sticky="nesw")
        self.mainBody.grid(row=1, column=0, sticky="nwes")

        #Grid settings
        self.mainTabs["tabsFrame"].columnconfigure(0, weight=10)
        self.mainTabs["tabsFrame"].columnconfigure(len(self.mainTabs["buttons"])+1, weight=10)

        self.mainBody.columnconfigure(0, weight=1)
        self.mainBody.rowconfigure(0, weight=1)

        self.window.rowconfigure(0, minsize=50, weight=0)
        self.window.rowconfigure(1, minsize=300, weight=1)
        self.window.columnconfigure(0, minsize=200, weight=1)

        #Make main page be first one visible
        self._switchTab("Main")
