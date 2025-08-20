from tkinter import *
from customtkinter import *
import tkcalendar
import threading
from storage.tracklist import TrackedPlayers
from storage.playerList import savePlayers
from startggModules.startggInterface import startggInterface
set_default_color_theme("green")

startgg = startggInterface()

global queryLock, trackLock
queryLock, trackLock = threading.Lock(),threading.Lock()

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

#Settings
windowSizeRatio = 1/0.5
def setup():
    global tournamentsInfo, scrollFrame, scrollTab, tournamentsFrame, updatedTracklist, root, updatedTournaments, trackedPlayersFrame, tracklistInfo, scrollPlayersFrame
    updatedTournaments = False
    tournamentsInfo, scrollFrame, scrollTab = None, None, None
    tracklistInfo, updatedTracklist, scrollPlayersFrame = None, False, None
    #Main window setup
    root = Tk(screenName="Wiener PR Program", baseName="Wiener PR Program", className="Wiener PR Program", )
    root.protocol("WM_DELETE_WINDOW", exit_app)
    screenSize = (root.winfo_screenwidth(), root.winfo_screenheight())
    root.geometry(str(int(screenSize[0]//windowSizeRatio))+"x"+str(int(screenSize[1]//windowSizeRatio)))
    root.resizable(width=False, height=False)
    window = CTkFrame(master=root, fg_color="gray")
    window.pack(fill="both", expand=True)
    frames, visualFrame = initTabs(window)
    tournamentsFrame = frames["Tournaments"]
    trackedPlayersFrame = frames["Tracked Players"]
    createMain(frames["Main"],)
    root.after(1000,lambda: createTournaments())
    root.after(1000,lambda: createTracklist())
    root.after(1000, fillTrackedPlayersInfo)
    return root

def raiseTab(frame : Frame):
    frame.tkraise()
    
def createMain(frame):
    createSeasonChoice(frame)
    createTrackedPlayersAdd(frame)

def fillTrackedPlayersInfo():
    global tracklistInfo, updatedTracklist, trackLock
    trackLock.acquire()
    try:
        newTracklistInfo = getTracklist()
        if newTracklistInfo != tracklistInfo:
            tracklistInfo = newTracklistInfo
            updatedTracklist = True
    finally:
        trackLock.release()
        root.after(2000, fillTrackedPlayersInfo)


def fillTournamentsInfo(dateStart, dateEnd):
    global tournamentsInfo, tournamentsFrame, updatedTournaments, queryLock, loadingFrame
    queryLock.acquire()
    try:
        loadingFrame.configure(text="Querying start.gg... Please wait")
        tournamentsInfo = []
        tournamentsInfo = startgg.getTournaments(dateStart, dateEnd)
        updatedTournaments = True
        loadingFrame.configure(text="All tournaments loaded")
    finally:
        queryLock.release()
        
def exit_app():
    startgg.saveEvents()
    saveTracklist()
    savePlayers()
    quit()


def addPlayer(field : CTkEntry):
    global updatedTracklist
    updatedTracklist = True
    discriminator = field.get().strip()
    field.delete(0,'end')
    
    playerStatus = startgg.enterPlayer(discriminator)
    if playerStatus == -1:
        field.insert(0,"Error. Wrong discriminator?")
    if playerStatus == 0:
        field.insert(0, "Player already tracked")
    if playerStatus == 1:
        field.insert(0, "Player added to tracklist")


def createTrackedPlayersAdd(frame):
    playerName = StringVar()
    addPlayerFrame = CTkFrame(master=frame,)
    entryField = CTkEntry(master=addPlayerFrame, textvariable=playerName, width=200)
    playerName.set("startgg discriminator")
    entryField
    entryField.bind("<Button-1>", lambda event: playerName.set(""))
    addButton = CTkButton(master=addPlayerFrame, command= lambda: addPlayer(entryField), text="Track player")
    entryField.pack(side="left", padx=8, pady=8)
    addButton.pack(side="left", padx=8, pady=8)
    addPlayerFrame.pack(side="top")
    pass

def createSeasonChoice(frame):
    global loadingFrame
    #Main frame
    seasonFrameChoose = CTkFrame(master=frame,height=200, bg_color="transparent")
    seasonFrameChoose.pack(side="top")

    #Container for season picker
    seasonStartFrame, seasonEndFrame = CTkFrame(master=seasonFrameChoose),CTkFrame(master=seasonFrameChoose)
    #Date picker
    seasonStart, seasonEnd = tkcalendar.DateEntry(master=seasonStartFrame, selectmode = "none"),tkcalendar.DateEntry(master=seasonEndFrame)
    loadingFrame = CTkLabel(master=seasonFrameChoose, text="")
    getTournamentsButton = CTkButton(master=seasonFrameChoose, text="Get tournaments", command=lambda: threading.Thread(target=lambda: fillTournamentsInfo(seasonStart, seasonEnd)).start())
    #The text
    seasonStartText, seasonEndText = CTkLabel(master=seasonStartFrame, text="Start of season"), CTkLabel(master=seasonEndFrame, text="End of season")
    
    #pack
    seasonStartText.pack(side="top")
    seasonEndText.pack(side="top")
    seasonStart.pack(side="top")
    seasonEnd.pack(side="top")
    seasonStartFrame.pack(side="left", padx=8, pady=8)
    seasonEndFrame.pack(side="left", padx=8, pady=8)
    getTournamentsButton.pack(side="left",padx=8, pady=8)
    loadingFrame.pack(side="left", padx=8, pady=8)

def deleteTrackedPlayer(frame,discriminator):
    global updatedTracklist
    updatedTracklist = True
    removeTrackedPlayer(discriminator)
    frame.pack_forget()


def createTracklist():
    global trackedPlayersFrame, scrollPlayersFrame, tracklistInfo, updatedTracklist
    root.after(2000,lambda: createTracklist())
    if updatedTracklist == False:
        return
    updatedTracklist = False
    if scrollPlayersFrame is not None:
        scrollPlayersFrame.pack_forget()
        scrollPlayersFrame.destroy()
    scrollPlayersFrame = CTkScrollableFrame(master=trackedPlayersFrame, orientation="vertical")
    if tracklistInfo == None:
        print("OHNO NOT THIS ERROR NOOO")
        return
    for trackedPlayer in tracklistInfo:
        #master frame
        playerFrame = CTkFrame(master=scrollPlayersFrame, height=80)

        nameShow = CTkFrame(master=playerFrame)
        namelabel = CTkLabel(master=nameShow, text=trackedPlayer["name"])

        discriminatorShow = CTkFrame(master=playerFrame)
        discriminatorLabel = CTkLabel(master=discriminatorShow, text=trackedPlayer["discriminator"])

        removeButton = CTkButton(master=playerFrame, command=lambda: threading.Thread(target=deleteTrackedPlayer, args=[playerFrame, trackedPlayer["discriminator"]]).start(), text="Remove from tracking")
        
        playerFrame.pack(side="top")

        namelabel.pack()
        nameShow.pack(side="left", padx=10, pady=10)
        discriminatorShow.pack(side="left", padx=10, pady=10)
        discriminatorLabel.pack()
        removeButton.pack(side="left", padx=10, pady=10)
        #tournament name
        
        #Does tournament count
    scrollPlayersFrame.pack(expand=True, fill="both", )

    
def createTournaments():
    global scrollFrame, scrollTab, updatedTournaments, tournamentsFrame
    root.after(1000,lambda: createTournaments())
    if updatedTournaments == False:
        return
    startgg.addEvents(tournamentsInfo)
    updatedTournaments = False
    if scrollFrame is not None:
        scrollFrame.pack_forget()
        scrollFrame.destroy()
    if scrollTab is None:
        scrollTab = CTkFrame(master=tournamentsFrame, height=40)
        dateLabel = CTkLabel(master=scrollTab, text="Date", width=60)
        dateLabel.pack(side="left")
        nameLabel = CTkLabel(master=scrollTab, text="TournamentName", width=300)
        nameLabel.pack(side="left")
        scrollTab.pack(side="top", fill="x")
    scrollFrame = CTkScrollableFrame(master=tournamentsFrame, orientation="vertical")
    if tournamentsInfo == None:
        print("OHNO NOT THIS ERROR NOOO")
        return
    for tournament in tournamentsInfo:
        #tournament tier
        tournamentColor = tournamentTierColors[tournament["eventTier"]]
        #master frame
        tournamentFrame = CTkFrame(master=scrollFrame, height=80, bg_color=tournamentColor)

        #date left side first
        dateShow = CTkFrame(master=tournamentFrame, )
        dateLabel = CTkLabel(master=dateShow, text=tournament["date"],height=40, width=60,)
        dateLabel.pack()
        dateShow.pack(side=LEFT, fill="y")

        #tournament name
        nameShow = CTkFrame(master=tournamentFrame, )
        nameLabel = CTkLabel(master=nameShow, text=tournament["name"],height=40, width=300)
        nameLabel.pack()
        nameShow.pack(side=LEFT ,fill="y")

        tournamentTiers = ["OOR Major", "Maor", "Regional","18+","10-17","7-9","4-6","2-3","None"]
        tierString = StringVar(value=tournament["eventTier"])
        tierShow = CTkFrame(master=tournamentFrame, height=80, width=100)
        custom_font = CTkFont(family="Arial", size=15, weight="bold", slant="roman")
        tierLabel = Label(master=tierShow, background=tournamentColor, font=custom_font, textvariable=tierString)
        tierLabel.pack()
        tierList = CTkComboBox(master=tournamentFrame, values=tournamentTiers, variable=tierString, command=lambda x: recolour(x, tierLabel, tournament["id"]))
        tierShow.pack(side="left")
        tierList.pack(side="left")
        tournamentFrame.pack(side=TOP, fill="x")
        #Does tournament count
    scrollFrame.pack(expand=True, fill="both", )
   
def recolour(x,tierlabel, id):
    tournamentColor = tournamentTierColors[x]
    tierlabel.configure(background = tournamentColor)
    startgg.updateTournamentTier(x, id)



def initTabs(window):
    #main tabs
    tabs = CTkFrame(master=window, height=20)
    visualFrame = CTkFrame(master=window, border_width=12,)
    
    #all tabs of different types
    showFrames : dict[CTkFrame] = {
        "Main" : CTkFrame(master=visualFrame),
        "Tracked Players" : CTkFrame(master=visualFrame),
        "Tournaments" : CTkFrame(master=visualFrame, ),
        "All players" : CTkFrame(master=visualFrame,),
        "Settings" : CTkFrame(master=visualFrame, ),
    }

    #setup tournaments shower

    showButtons = {}
    for key in showFrames.keys():
        newButton = CTkButton(master=tabs, command=lambda x=key : raiseTab(showFrames[x]),text=key)
        showButtons[key] = newButton
        newButton.pack(side="left", expand=True)

    #pack buttons
    tabs.pack(side="top", fill="x",)
    visualFrame.pack(side="top", fill="both",expand=True)

    for frame in showFrames.values():
        frame.place(x=0, y=0, relwidth=1, relheight=1)
    return showFrames, visualFrame
#pack button labels

def start():
    root = setup()
    root.mainloop()
