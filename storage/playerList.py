from pickle import load, dump
import gzip
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "allPlayers.pkl")

if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
    with gzip.open(file_path, "rb") as trackedPlayers:
        tracklist = load(trackedPlayers)
        trackedPlayers.close()       
else:
    tracklist = {
                "players" : [],
                "playerDiscriminators" : set()
            }
    

def getPlayerlist():
    return tracklist["players"]

def addPlayer(player : dict) -> None:
    if player["discriminator"] in tracklist["playerDiscriminators"]:
        return False
    tracklist["players"].append(player)
    tracklist["playerDiscriminators"].add(player["discriminator"])
    print("adding", player["discriminator"])
    return True

def removePlayer(startggDiscriminator) -> None:
    exist = False
    if startggDiscriminator in tracklist["playerDiscriminators"]:
        exist = True
    if exist:
        tracklist["playerDiscriminators"].remove(startggDiscriminator)
    for player in tracklist["players"]:
        if player["discriminator"] == startggDiscriminator:
            tracklist["players"].remove(player)
            break
        
def getPlayersSetCheck() -> set:
    discriminators = set()
    for player in tracklist:
        discriminators.add(player["startgg"])
    return discriminators

def savePlayers():
    with gzip.open(file_path, "wb") as trackedPlayers:
        dump(tracklist, trackedPlayers)
        trackedPlayers.close()