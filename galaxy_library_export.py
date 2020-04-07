import sqlite3
import json
import time
import csv


database_location = "C:\\ProgramData\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db"
platforms = {"humble": "Humble Bundle", "xbox": "Microsoft Store", "gog": "GOG", "steam": "Steam", "epic": "Epic Games Store", "origin": "Origin", "uplay": "Uplay", "discord": "Discord", "generic": "Other"}
dataId1 = 170
dataId2 = 239
titleId1 = 171
titleId2 = 244
# Create a view of OwnedGames joined on GamePieces for a full OwnedGames DB
owned_games_query = """CREATE TEMP VIEW MasterList AS
				SELECT GamePieces.releaseKey,GamePieces.gamePieceTypeId,GamePieces.value FROM OwnedGames
				JOIN GamePieces ON OwnedGames.releaseKey = GamePieces.releaseKey;"""
# Create view of unique items using details
unique_owned_games_query = """CREATE TEMP VIEW UniqueMasterList AS
				SELECT DISTINCT(MasterList.value) AS info,MasterCopy.value AS title FROM MasterList, MasterList
				AS MasterCopy WHERE ((MasterList.gamePieceTypeId = {}) OR (MasterList.GamePieceTypeId = {})) AND
				((MasterCopy.gamePieceTypeId = {}) OR (MasterCopy.gamePieceTypeId = {})) AND
				(MasterCopy.releaseKey = MasterList.releaseKey);""".format(dataId1, dataId2, titleId1, titleId2)
# Display each game and its details along with corresponding release key grouped by details
aggr_game_data = """SELECT UniqueMasterList.title, GROUP_CONCAT(DISTINCT MasterList.releaseKey), UniqueMasterList.info
				FROM UniqueMasterList, MasterList WHERE UniqueMasterList.info = MasterList.value
				GROUP BY UniqueMasterList.info ORDER BY UniqueMasterList.title;"""
conn = sqlite3.connect(database_location)
cursor = conn.cursor()
cursor.execute(owned_games_query)
cursor.execute(unique_owned_games_query)
cursor.execute(aggr_game_data)
with open("gameDB.csv", "w", encoding='utf-8') as csvfile:
	fieldnames = ['title', 'platformList', 'developers', 'publishers', 'releaseDate', 'genres', 'themes', 'criticsScore']
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	writer.writeheader()
	while True:
		result = cursor.fetchone()
		if result:
			# JSON string needs to be converted to dict
			# For json.load() to work correctly, all double quotes must be correctly escaped
			info = json.loads(result[2].replace('"','\"'))
			row = info
			row['title'] = result[0].split('"')[3]
			row['platformList'] = []
			if any(platform in releaseKey for platform in platforms for releaseKey in result[1].split(",")):
				row['platformList'] = set(platforms[platform] for releaseKey in result[1].split(",") for platform in platforms if platform in releaseKey)
			else:
				row['platformList'].append("Placeholder")
			row['releaseDate'] = time.strftime("%y-%m-%d", time.localtime(info['releaseDate']))
			for key, value in row.items():
				if type(value) == list or type(value) == set:
					row[key] = ",".join(value)
			writer.writerow(row)
		else:
			break
cursor.close()
conn.close()