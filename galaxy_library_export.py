import sqlite3
import json
import time
import csv
import random
import sys, getopt

database_location = "C:\\ProgramData\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db"
platforms = { "3do": "3DO Interactive", "3ds": "Nintendo 3DS", "aion": "Aion", "aionl": "Aion: Legions of War", "amazon": "Amazon", "amiga": "Amiga", "arc": "ARC", "atari": "Atari", "battlenet": "Battle.net", "bb": "BestBuy", "beamdog": "Beamdog", "bethesda": "Bethesda.net", "blade": "Blade & Soul", "c64": "Commodore 64", "d2d": "Direct2Drive", "dc": "Sega Dreamcast", "discord": "Discord", "dotemu": "DotEmu", "egg": "Newegg", "elites": "Elite Dangerous", "epic": "Epic Games Store", "eso": "ESO", "fanatical": "Fanatical store", "ffxi": "Final Fantasy XI", "ffxiv": "Final Fantasy XIV", "fxstore": "Placeholder", "gamehouse": "GameHouse", "gamesessions": "GameSessions", "gameuk": "Game UK", "generic": "Other", "gg": "GamersGate", "glyph": "Trion World", "gmg": "Green Man Gaming", "gog": "GOG", "gw": "Guild Wars", "gw2": "Guild Wars 2", "humble": "Humble Bundle", "indiegala": "IndieGala", "itch": "Itch.io", "jaguar": "Atari Jaguar", "kartridge": "Kartridge", "lin2": "Lineage 2", "minecraft": "Minecraft", "n64": "Nintendo64", "ncube": "Nintendo GameCube", "nds": "Nintendo DS", "neo": "NeoGeo", "nes": "NES", "ngameboy": "Nintendo Game Boy", "nswitch": "Nintendo Switch", "nuuvem": "Nuuvem", "nwii": "Nintendo Wii", "nwiiu": "Nintendo Wii U", "oculus": "Oculus", "origin": "Origin", "paradox": "Paradox Plaza", "pathofexile": "Path of Exile", "pce": "PC Engine", "playasia": "Play-Asia", "playfire": "Playfire", "ps2": "Sony PlayStation 2", "psn": "PlayStation Network", "psp": "PlayStation Portable", "psvita": "PlayStation Vita", "psx": "Sony PlayStation", "riot": "Riot", "rockstar": "Rockstar Games Launcher", "saturn": "SegaSaturn", "sega32": "Sega 32X", "segacd": "Sega CD", "segag": "Sega Genesis", "sms": "Sega Master System", "snes": "SNES", "stadia": "Google Stadia", "star": "Star Citizen", "steam": "Steam", "test": "Test", "totalwar": "Total War", "twitch": "Twitch", "unknown": "Unknown", "uplay": "Uplay", "vision": "ColecoVision", "wargaming": "Wargaming", "weplay": "WePlay", "winstore": "Windows Store", "xboxog": "Original Xbox games", "xboxone": "Xbox Live", "zx": "Zx Spectrum PC" }

# Read parameters
arguments = sys.argv
arguments = arguments[1:]

numberOfPicks = 0
try:
  opts, args = getopt.getopt(arguments,"r:",["picks="])
except getopt.GetoptError:
	print ("galaxy_library_export.py -r <number_of_random_picks>")
	sys.exit(2)
for opt, arg in opts:
	if opt == '-r':
		numberOfPicks = arg

#print("N: ", numberOfPicks)
  
conn = sqlite3.connect(database_location)
cursor = conn.cursor()

# gamePieceTypeId is stored in GamePieceTypes
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type = 'originalMeta'""")
originalMetaID = cursor.fetchall()[0][0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type = 'meta'""")
metaID = cursor.fetchall()[0][0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type = 'originalTitle'""")
originalTitleID = cursor.fetchall()[0][0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type = 'title'""")
titleID = cursor.fetchall()[0][0]
# Create a view of GameLinks joined on GamePieces for a full GameLinks DB
owned_games_query = """CREATE TEMP VIEW MasterList AS
				SELECT GamePieces.releaseKey, GamePieces.gamePieceTypeId, GamePieces.value FROM GameLinks
				JOIN GamePieces ON GameLinks.releaseKey = GamePieces.releaseKey;"""
# Create view of unique items using details
unique_owned_games_query = """CREATE TEMP VIEW UniqueMasterList AS
				SELECT DISTINCT(MasterList.value) AS metadata, MasterCopy.value AS title FROM MasterList, MasterList
				AS MasterCopy WHERE ((MasterList.gamePieceTypeId = {}) OR (MasterList.GamePieceTypeId = {})) AND
				((MasterCopy.gamePieceTypeId = {}) OR (MasterCopy.gamePieceTypeId = {})) AND
				(MasterCopy.releaseKey = MasterList.releaseKey);""".format(originalMetaID, metaID, originalTitleID, titleID)
# Display each game and its details along with corresponding release key grouped by details
aggr_game_data = """CREATE TEMP VIEW FinalList AS
				SELECT UniqueMasterList.title, GROUP_CONCAT(DISTINCT MasterList.releaseKey), UniqueMasterList.metadata
				FROM UniqueMasterList, MasterList WHERE UniqueMasterList.metadata = MasterList.value
				GROUP BY UniqueMasterList.metadata ORDER BY UniqueMasterList.title;"""
# count distinct games
number_of_games = """SELECT COUNT(*) FROM FinalList;"""
				
cursor.execute(owned_games_query)
cursor.execute(unique_owned_games_query)
cursor.execute(aggr_game_data)

# pick random game
cursor.execute("""SELECT COUNT(*) from FinalList;""")
numberOfGames = cursor.fetchone()[0]
print("Number of games: ", numberOfGames)

picks = random.sample(range(0, int(numberOfGames)), int(numberOfPicks))
#print(picks)

cursor.execute("""SELECT * FROM FinalList""")

with open("gameDB.csv", "w", encoding='utf-8', newline='') as csvfile:
	fieldnames = ['title', 'platformList', 'developers', 'publishers', 'releaseDate', 'genres', 'themes', 'criticsScore']
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	writer.writeheader()
	gameIndex = 0
	while True:
		result = cursor.fetchone()
		if result:
			# JSON string needs to be converted to dict
			# For json.load() to work correctly, all double quotes must be correctly escaped
			metadata = json.loads(result[2].replace('"','\"'))
			row = metadata
			row['title'] = result[0].split('"')[3]
			row['title'] = row['title'].replace("\\","")
			
			if (gameIndex in picks):
				print("Random selection [{:d}]: ".format(gameIndex), row['title'])

			row['platformList'] = []
			if any(platform in releaseKey for platform in platforms for releaseKey in result[1].split(",")):
				row['platformList'] = set(platforms[platform] for releaseKey in result[1].split(",") for platform in platforms if releaseKey.startswith(platform))
			else:
				row['platformList'].append("Placeholder")
			if metadata['releaseDate']:
				row['releaseDate'] = time.strftime("%Y-%m-%d", time.localtime(metadata['releaseDate']))
			else:
				row['releaseDate'] = metadata['releaseDate']
			if metadata['criticsScore']:
				row['criticsScore'] = round(metadata['criticsScore'])
			else:
				row['criticsScore'] = metadata['criticsScore']
			for key, value in row.items():
				if type(value) == list or type(value) == set:
					row[key] = ",".join(value)
			writer.writerow(row)
			
			gameIndex = gameIndex + 1
		else:
			break
cursor.close()
conn.close()
