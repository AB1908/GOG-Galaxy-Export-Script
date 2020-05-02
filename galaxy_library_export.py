import sqlite3
import json
import time
import csv
import re


database_location = "C:\\ProgramData\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db"
platforms = {"3do": "3DO Interactive Multiplayer", "3ds": "Nintendo 3DS", "aion": "Aion", "aionl": "Aion: Legions of War", "amazon": "Amazon", "amiga": "Amiga", "arc": "ARC", "atari": "Atari 2600", "battlenet": "Battle.net", "bb": "BestBuy", "beamdog": "Beamdog", "bethesda": "Bethesda.net", "blade": "Blade & Soul", "c64": "Commodore 64", "d2d": "Direct2Drive", "dc": "Dreamcast", "discord": "Discord", "dotemu": "DotEmu", "egg": "Newegg", "elites": "Elite Dangerous", "epic": "Epic Games Store", "eso": "The Elder Scrolls Online", "fanatical": "Fanatical", "ffxi": "Final Fantasy XI", "ffxiv": "Final Fantasy XIV", "fxstore": "Placeholder", "gamehouse": "GameHouse", "gamesessions": "GameSessions", "gameuk": "GAME UK", "generic": "Other", "gg": "GamersGate", "glyph": "Trion World", "gmg": "Green Man Gaming", "gog": "GOG", "gw": "Guild Wars", "gw2": "Guild Wars 2", "humble": "Humble Bundle", "indiegala": "IndieGala", "itch": "Itch.io", "jaguar": "Atari Jaguar", "kartridge": "Kartridge", "lin2": "Lineage 2", "minecraft": "Minecraft", "n64": "Nintendo 64", "ncube": "Nintendo GameCube", "nds": "Nintendo DS", "neo": "NeoGeo", "nes": "Nintendo Entertainment System", "ngameboy": "Game Boy", "nswitch": "Nintendo Switch", "nuuvem": "Nuuvem", "nwii": "Wii", "nwiiu": "Wii U", "oculus": "Oculus", "origin": "Origin", "paradox": "Paradox Plaza", "pathofexile": "Path of Exile", "pce": "PC Engine", "playasia": "Play-Asia", "playfire": "Playfire", "ps2": "PlayStation 2", "psn": "PlayStation Network", "psp": "PlayStation Portable", "psvita": "PlayStation Vita", "psx": "PlayStation", "riot": "Riot", "rockstar": "Rockstar Games Launcher", "saturn": "Sega Saturn", "sega32": "32X", "segacd": "Sega CD", "segag": "Sega Genesis", "sms": "Sega Master System", "snes": "Super Nintendo Entertainment System", "stadia": "Google Stadia", "star": "Star Citizen", "steam": "Steam", "test": "Test", "totalwar": "Total War", "twitch": "Twitch", "unknown": "Unknown", "uplay": "Uplay", "vision": "ColecoVision", "wargaming": "Wargaming", "weplay": "WePlay", "winstore": "Windows Store", "xboxog": "Xbox", "xboxone": "Xbox Live", "zx": "ZX Spectrum PC"}

conn = sqlite3.connect(database_location)
cursor = conn.cursor()

# gamePieceTypeId is stored in GamePieceTypes
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type='originalMeta'""")
originalMetaID = cursor.fetchone()[0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type='meta'""")
metaID = cursor.fetchone()[0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type='originalTitle'""")
originalTitleID = cursor.fetchone()[0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type='title'""")
titleID = cursor.fetchone()[0]
cursor.execute("""SELECT id FROM GamePieceTypes WHERE type='allGameReleases'""")
releasesList = cursor.fetchone()[0]
# Create a view of GameLinks joined on GamePieces for a full owned game data DB
owned_game_database = """CREATE TEMP VIEW MasterList AS
				SELECT GamePieces.releaseKey, GamePieces.gamePieceTypeId, GamePieces.value FROM GameLinks
				JOIN GamePieces ON GameLinks.releaseKey = GamePieces.releaseKey;"""
# Create filtered view of owned games with game times using multiple joins
owned_game_filtered_data = """CREATE TEMP VIEW MasterDB AS SELECT DISTINCT(MasterList.releaseKey) AS releaseKey,
				MasterList.value AS title, MC1.value AS metadata, MC2.value AS platformList, GameTimes.minutesInGame AS time
				from MasterList, MasterList AS MC1, MasterList AS MC2, GameTimes WHERE (((MasterList.gamePieceTypeId={}) OR
				(MasterList.gamePieceTypeId={})) AND ((MC1.gamePieceTypeId={}) OR (MC1.gamePieceTypeId={}))) AND
				MC1.releaseKey=MasterList.releaseKey AND MC2.gamePieceTypeId={} AND MC2.releaseKey=MasterList.releaseKey
				AND GameTimes.releaseKey=MasterList.releaseKey ORDER BY title;""".format(originalTitleID, titleID, originalMetaID, metaID, releasesList)
# Display each game and its details along with corresponding release key grouped by releasesList
unique_game_data = """SELECT GROUP_CONCAT(DISTINCT MasterDB.releaseKey), MasterDB.title, MasterDB.metadata, sum(MasterDB.time)
				FROM MasterDB GROUP BY MasterDB.platformList ORDER BY MasterDB.title;"""
cursor.execute(owned_game_database)
cursor.execute(owned_game_filtered_data)
cursor.execute(unique_game_data)
title_regex = re.compile(r"""(?<=\{"title": ").*(?="})""")
with open("gameDB.csv", "w", encoding='utf-8', newline='') as csvfile:
	fieldnames = ['title', 'platformList', 'developers', 'publishers', 'releaseDate', 'genres', 'themes', 'criticsScore', 'gameMins']
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	writer.writeheader()
	while True:
		result = cursor.fetchone()
		if result:
			# JSON string needs to be converted to dict
			# For json.load() to work correctly, all double quotes must be correctly escaped
			metadata = json.loads(result[2].replace('"','\"'))
			row = metadata
			row['title'] = result[1].replace("\\","")
			row['title'] = title_regex.match(row["title"])
			row['platformList'] = []
			if any(platform in releaseKey for platform in platforms for releaseKey in result[0].split(",")):
				row['platformList'] = set(platforms[platform] for releaseKey in result[0].split(",") for platform in platforms if releaseKey.startswith(platform))
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
			row['gameMins'] = result[3]
			writer.writerow(row)
		else:
			break
cursor.close()
conn.close()