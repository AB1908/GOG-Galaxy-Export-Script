import sqlite3
import re
import json
import time
import csv


platforms = {"humble": "Humble Bundle", "xbox": "Microsoft Store", "gog": "GOG", "steam": "Steam", "epic": "Epic Games Store", "origin": "Origin", "uplay": "Uplay", "discord": "Discord", "generic": "Other"}
dataId1 = 170
dataId2 = 239
titleId1 = 171
titleId2 = 244
# Create a view of OwnedGames joined on GamePieces for a full OwnedGames db
owned_games_query = """CREATE VIEW MasterList AS
				SELECT GamePieces.releaseKey,GamePieces.gamePieceTypeId,GamePieces.value FROM OwnedGames
				JOIN GamePieces ON OwnedGames.releaseKey = GamePieces.releaseKey;"""
# Create view of unique items using details
unique_owned_games_query = """CREATE VIEW UniqueMasterList AS
				SELECT DISTINCT(MasterList.value) AS info,MasterCopy.value AS title FROM MasterList, MasterList
				AS MasterCopy WHERE ((MasterList.gamePieceTypeId = ?) OR (MasterList.GamePieceTypeId = ?)) AND
				((MasterCopy.gamePieceTypeId = ?) OR (MasterCopy.gamePieceTypeId = ?)) AND
				(MasterCopy.releaseKey = MasterList.releaseKey);"""
# Display each game and its details along with corresponding release key grouped by details
aggr_game_data = """SELECT UniqueMasterList.title, GROUP_CONCAT(DISTINCT MasterList.releaseKey), UniqueMasterList.info
				FROM UniqueMasterList, MasterList WHERE UniqueMasterList.info = MasterList.value
				GROUP BY UniqueMasterList.title;"""
title_regex = re.compile(r"""(?<=\{"title":").*(?="\})""")
conn = sqlite3.connect("C:\\ProgramData\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db")
cursor = conn.cursor()
cursor.execute(owned_games_query)
cursor.execute(unique_owned_games_query, dataId1, dataId2, titleId1, titleId2)
cursor.execute(aggr_game_data)
with open("gameDB.csv", "w") as csvfile:
	fieldnames = ['title', 'platform', 'developers', 'publishers', 'genres', 'themes', 'criticsRating']
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	writer.writeheader()
	while True:
		result = cursor.fetchone()
		if result:
			# JSON string needs to be converted to dict
			# For json.load() to work correctly, all double quotes must be correctly escaped
			info = json.load(result[2].replace('"','\"'))
			row = info
			row['title'] = title_regex.match(result[0])
			row['platformList'] = []
			for platform in result[1].split(","):
				if platform in platforms:
					row['platformList'].append(platforms[platform])
				else:
					row['platformList'].append("Placeholder")
			row['releaseDate'] = time.strftime("%y-%m-%d", time.localtime(info['releaseDate']))
			writer.writerow(row)
		else:
			break
cursor.close()
conn.close()