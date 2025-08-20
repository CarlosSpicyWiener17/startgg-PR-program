from json import dump, load
with open("trackedTOs.json", "r") as tournamentOrganizerJSON:
    if tournamentOrganizerJSON.read() == "":
        tournamentOrganizers = []
    else:
        tournamentOrganizers = load(tournamentOrganizerJSON)
    tournamentOrganizerJSON.close()
def addTO(name, startggDiscriminator) -> None:
    for TO in tournamentOrganizers:
        if TO["name"] == name or TO["startgg"] == startggDiscriminator:
            print("Already exists")
            return
    tournamentOrganizers.append({
        "name" : name,
        "startgg" : startggDiscriminator
    })
    return

def removeTO(startggDiscriminator) -> None:
    for TO in tournamentOrganizers:
        if TO["startgg"] == startggDiscriminator:
            tournamentOrganizers.remove(TO)
    return

def saveTOs():
    with open("trackedTOs.json", "w") as tournamentOrganizerSave:
        dump(tournamentOrganizers, tournamentOrganizerSave)
        tournamentOrganizerSave.close()
