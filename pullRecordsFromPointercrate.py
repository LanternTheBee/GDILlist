# Written by ByteLaw
# This script will automatically make files for records on pointercrate that are still on the list
# WARNING - IT WILL REWRITE FILES FOR LIST LEVELS AND REWRITE _list.json WITHOUT ANY OTHER LEVELS!

import requests
import time
import json

listLength = 75
urlV1 = "https://pointercrate.com/api/v1"
urlV2 = "https://pointercrate.com/api/v2"
headers = {"Accept":"application/json", "Content-Type": "application/json"}
session = requests.Session()

def get(requestURL):
    response = session.get(url=requestURL, headers=headers)
    if(response.status_code == 200):
        return response.json()
    else:
        print("Status code " + str(response.status_code))
        return None
    
def convertToCamelCase(string: str):
    string = string.lower() # make entire string lowercase
    words = string.split(" ") # split by spaces
    otherWords = words.copy()
    del otherWords[0] # dont process first word
    result = "".join(otherWords) # combine back into a string
    result = result.title() # turns every first letter of word into capital letter
    result = words[0] + result # add first word back
    return result
    
pointercrateRecords = {}
demons = {}
israelPlayers = get(urlV1+"/players/?nation=IL&banned=false") # Get all players from IL that aren't banned
if israelPlayers == None:
    print("Couldn't retrieve Israeli players")
print("Retrieved Israeli players")
for player in israelPlayers:
    time.sleep(0.5) # Neccesary so we wont get rate limited

    playerObject = get(urlV1+"/players/" + str(player["id"]))

    if playerObject == None:
        print("Couldn't retrieve player data for " + player["name"])
        continue

    for record in playerObject["data"]["records"]:
        if record["progress"] < 100: # Don't save non-completions
            continue
        if record["demon"]["position"] > 150: # Don't save legacy levels
            continue
        record["playerName"] = playerObject["data"]["name"] # Save player name
        recordDemonName = convertToCamelCase(record["demon"]["name"])

        if not recordDemonName in demons:
            demons[recordDemonName] = {
                "position": record["demon"]["position"],
                "id": record["demon"]["id"]
            }
        
        if not recordDemonName in pointercrateRecords:
            pointercrateRecords[recordDemonName] = [record]
        else:
            pointercrateRecords[recordDemonName].append(record)
        
    print("Added " + player["name"] + "'s records")

demons = {k: v for k, v in sorted(demons.items(), key=lambda item: item[1]["position"])} # Sort demons by position
for records in pointercrateRecords.values():
    records.sort(key=lambda record: record["id"]) # Sort records by time submitted (bigger ID, later submission)
print("Finished retrieving Israeli records")

currentListLength = 0
for name, data in demons.items():
    if currentListLength >= listLength:
        break
    time.sleep(0.5)
    demonData = get(urlV2 + "/demons/" + str(data["id"]))
    if demonData == None:
        print("Could'nt retrieve demon data")
        continue
    print("Got data for the demon " + demonData["data"]["name"])
    demonRecords = pointercrateRecords[name] # Get records for this demon
    verifierRecord = demonRecords[0] # The first one will always be the first victor
    otherRecords = []
    for i in range(1, len(demonRecords)):
        record = demonRecords[i]
        otherRecords.append({
            "user": record["playerName"],
            "link": record["video"],
            "percent": 100,
            "hz": 240,
            "mobile": False,
        })
    path = "data/" + name + ".json"
    with open(path, "w+") as demonFile:
        demonFile.write(json.dumps({
            "id": demonData["data"]["level_id"],
            "name": demonData["data"]["name"],
            "author": demonData["data"]["publisher"]["name"],
            "verifier": verifierRecord["playerName"],
            "verification": verifierRecord["video"],
            "records": otherRecords,
            "percentToQualify": 100,
            "creators": [],
        }, indent=4))
        print("Wrote to " + path)
    currentListLength += 1
    print(str(currentListLength) + "/" + str(listLength))

session.close()

with open("data/_list.json", "w+") as listData:
    listData.write(json.dumps(list(demons.keys()), indent=4))

print("Finished")
