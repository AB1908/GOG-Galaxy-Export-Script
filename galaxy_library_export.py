import sqlite3
import json
import time
import csv
import re

class Arguments():
	""" argparse wrapper, to reduce code verbosity """
	__parser = None
	__args = None

	def __init__(self, args, **kwargs):
		import argparse
		self.__parser = argparse.ArgumentParser(**kwargs)
		for arg in args:
			self.__parser.add_argument(*arg[0], **arg[1])
		self.__args = self.__parser.parse_args()

	def help(self):
		self.__parser.print_help()

	def anyOption(self, exceptions):
		for k,v in self.__args.__dict__.items():
			if (k not in exceptions) and v:
				return True
		return False

	def __getattr__(self, name):
		return getattr(self.__args, name)

def extractData(args):
	database_location = "C:\\ProgramData\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db"
	platforms = {"3do": "3DO Interactive Multiplayer", "3ds": "Nintendo 3DS", "aion": "Aion", "aionl": "Aion: Legions of War", "amazon": "Amazon", "amiga": "Amiga", "arc": "ARC", "atari": "Atari 2600", "battlenet": "Battle.net", "bb": "BestBuy", "beamdog": "Beamdog", "bethesda": "Bethesda.net", "blade": "Blade & Soul", "c64": "Commodore 64", "d2d": "Direct2Drive", "dc": "Dreamcast", "discord": "Discord", "dotemu": "DotEmu", "egg": "Newegg", "elites": "Elite Dangerous", "epic": "Epic Games Store", "eso": "The Elder Scrolls Online", "fanatical": "Fanatical", "ffxi": "Final Fantasy XI", "ffxiv": "Final Fantasy XIV", "fxstore": "Placeholder", "gamehouse": "GameHouse", "gamesessions": "GameSessions", "gameuk": "GAME UK", "generic": "Other", "gg": "GamersGate", "glyph": "Trion World", "gmg": "Green Man Gaming", "gog": "GOG", "gw": "Guild Wars", "gw2": "Guild Wars 2", "humble": "Humble Bundle", "indiegala": "IndieGala", "itch": "Itch.io", "jaguar": "Atari Jaguar", "kartridge": "Kartridge", "lin2": "Lineage 2", "minecraft": "Minecraft", "n64": "Nintendo 64", "ncube": "Nintendo GameCube", "nds": "Nintendo DS", "neo": "NeoGeo", "nes": "Nintendo Entertainment System", "ngameboy": "Game Boy", "nswitch": "Nintendo Switch", "nuuvem": "Nuuvem", "nwii": "Wii", "nwiiu": "Wii U", "oculus": "Oculus", "origin": "Origin", "paradox": "Paradox Plaza", "pathofexile": "Path of Exile", "pce": "PC Engine", "playasia": "Play-Asia", "playfire": "Playfire", "ps2": "PlayStation 2", "psn": "PlayStation Network", "psp": "PlayStation Portable", "psvita": "PlayStation Vita", "psx": "PlayStation", "riot": "Riot", "rockstar": "Rockstar Games Launcher", "saturn": "Sega Saturn", "sega32": "32X", "segacd": "Sega CD", "segag": "Sega Genesis", "sms": "Sega Master System", "snes": "Super Nintendo Entertainment System", "stadia": "Google Stadia", "star": "Star Citizen", "steam": "Steam", "test": "Test", "totalwar": "Total War", "twitch": "Twitch", "unknown": "Unknown", "uplay": "Uplay", "vision": "ColecoVision", "wargaming": "Wargaming", "weplay": "WePlay", "winstore": "Windows Store", "xboxog": "Xbox", "xboxone": "Xbox Live", "zx": "ZX Spectrum PC"}

	def id(name):
		""" Returns the numeric ID for the specified type """
		return cursor.execute('SELECT id FROM GamePieceTypes WHERE type="{}"'.format(name)).fetchone()[0]

	def jls(name, bReturnCleanedString=False):
		""" json.loads(`name`), optionally returning the purified sub-object of the same name,
		    for cases such as {`name`: {`name`: "string"}}
		"""
		v = json.loads(result[positions[name]])
		return re.sub(r'<br\s*/?>', '\\\\n', v[name].replace('\n', '\\n')) if bReturnCleanedString else v


	def prepare(resultName, fields, dbField=None, dbRef=None, dbCondition=None, dbResultField=None, dbGroupBy=None):
		""" Wrapper around the statement preparation and result parsing\n
			`resultName` cli argument variable name\n
			`fields` {`title` to be inserted in the CSV: `boolean condition`, …}\n
			SELECT `dbField` FROM `dbRef` WHERE `dbCondition`\n
			SELECT `dbResultField` FROM MasterDB GROUP BY `dbGroupBy`
		"""
		# CSV field names
		for name,condition in fields.items():
			if condition:
				fieldnames.append(name)

		if dbField:
			og_fields.append(', {}'.format(dbField))
			# Position of the results
			positions[resultName] = prepare.nextPos
			prepare.nextPos += 1
		if dbRef:
			og_references.append(', {}'.format(dbRef))
		if dbCondition:
			og_conditions.append(' AND ({})'.format(dbCondition))
		if dbResultField:
			og_resultFields.append(dbResultField)
		if dbGroupBy:
			og_resultGroupBy.append(dbGroupBy)

	from contextlib import contextmanager
	@contextmanager
	def OpenDB():
		# Prepare the DB connection
		_connection = sqlite3.connect(database_location)
		_cursor = _connection.cursor()

		_exception = None
		try:
			yield _cursor
		except Exception as e:
			_exception = e

		# Close the DB connection
		_cursor.close()
		_connection.close()

		# Re-raise the unhandled exception if needed
		if _exception:
			raise _exception

	with OpenDB() as cursor:
		# Create a view of GameLinks joined on GamePieces for a full owned game data DB
		owned_game_database = """CREATE TEMP VIEW MasterList AS
				SELECT GamePieces.releaseKey, GamePieces.gamePieceTypeId, GamePieces.value FROM GameLinks
				JOIN GamePieces ON GameLinks.releaseKey = GamePieces.releaseKey;"""

		# Set up default queries and processing metadata, and always extract the game title along with any parameters
		prepare.nextPos = 2
		positions = {'releaseKey': 0, 'title': 1}
		fieldnames = ['title']
		og_fields = ["""CREATE TEMP VIEW MasterDB AS SELECT DISTINCT(MasterList.releaseKey) AS releaseKey, MasterList.value AS title"""]
		og_references = [""" FROM MasterList"""]
		og_conditions = [""" WHERE ((MasterList.gamePieceTypeId={}) OR (MasterList.gamePieceTypeId={}))""".format(id('originalTitle'), id('title'))]
		og_order = """ ORDER BY title;"""
		og_resultFields = ['GROUP_CONCAT(DISTINCT MasterDB.releaseKey)', 'MasterDB.title']
		og_resultGroupBy = ['MasterDB.title']

		# Create parameterised filtered view of owned games using multiple joins
		if args.all or args.summary:
			prepare(
				'summary',
				{'summary': True},
				'SUMMARY.value AS summary',
				'MasterList AS SUMMARY',
				'(SUMMARY.releaseKey=MasterList.releaseKey) AND (SUMMARY.gamePieceTypeId={})'.format(id('summary')),
				'MasterDB.summary'
			)

		if args.all or args.platforms:
			prepare(
				'platforms',
				{'platformList': True},
			)

		if args.all or args.criticsScore or args.developers or args.genres or args.publishers or args.releaseDate or args.themes:
			prepare(
				'metadata',
				{
					'criticsScore': args.all or args.criticsScore,
					'developers': args.all or args.developers,
					'genres': args.all or args.genres,
					'publishers': args.all or args.publishers,
					'releaseDate': args.all or args.releaseDate,
					'themes': args.all or args.themes,
				},
				'METADATA.value AS metadata',
				'MasterList AS METADATA',
				'(METADATA.releaseKey=MasterList.releaseKey) AND ((METADATA.gamePieceTypeId={}) OR (METADATA.gamePieceTypeId={}))'.format(id('originalMeta'), id('meta')),
				'MasterDB.metadata'
			)

		if args.all or args.playtime:
			prepare(
				'playtime',
				{'gameMins': True},
				'GAMETIMES.minutesInGame AS time',
				'GAMETIMES',
				'GAMETIMES.releaseKey=MasterList.releaseKey',
				'sum(MasterDB.time)'
			)

		if args.all or args.imageBackground or args.imageSquare or args.imageVertical:
			prepare(
				'images',
				{
					'backgroundImage': args.all or args.imageBackground,
					'squareIcon': args.all or args.imageSquare,
					'verticalCover': args.all or args.imageVertical
				},
				'IMAGES.value AS images',
				'MasterList AS IMAGES',
				'(IMAGES.releaseKey=MasterList.releaseKey) AND (IMAGES.gamePieceTypeId={})'.format(id('originalImages')),
				'MasterDB.images'
			)

		# Display each game and its details along with corresponding release key grouped by releasesList
		unique_game_data = """SELECT {} FROM MasterDB GROUP BY {} ORDER BY MasterDB.title;""".format(
			', '.join(og_resultFields),
			', '.join(og_resultGroupBy)
		)

		# Perform the queries
		cursor.execute(owned_game_database)
		cursor.execute(''.join(og_fields + og_references + og_conditions) + og_order)
		cursor.execute(unique_game_data)

		#title_regex = re.compile(r"""(?<=\{"title":").*(?="})""")
		with open("gameDB.csv", "w", encoding='utf-8', newline='') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=args.delimiter)
			writer.writeheader()
			while True:
				result = cursor.fetchone()
				if not result:
					break

				# JSON string needs to be converted to dict
				# For json.load() to work correctly, all double quotes must be correctly escaped
				row = {'title': jls('title', True)}

				# Playtime
				if args.all or args.playtime:
					row['gameMins'] = result[positions['playtime']]

				# Summaries
				if args.all or args.summary:
					row['summary'] = jls('summary', True)

				# Platforms
				if args.all or args.platforms:
					rkeys = result[positions['releaseKey']].split(',')
					if any(platform in releaseKey for platform in platforms for releaseKey in rkeys):
						row['platformList'] = set(platforms[platform] for releaseKey in rkeys for platform in platforms if releaseKey.startswith(platform))
					else:
						row['platformList'] = ["Placeholder"]

				# Various metadata
				if args.all or args.criticsScore or args.developers or args.genres or args.publishers or args.releaseDate or args.themes:
					metadata = jls('metadata')

					if args.all or args.criticsScore:
						try:
							row['criticsScore'] = round(metadata['criticsScore'])
						except:
							row['criticsScore'] = metadata['criticsScore']

					if args.all or args.developers:
						row['developers'] = metadata['developers']

					if args.all or args.genres:
						row['genres'] = metadata['genres']

					if args.all or args.publishers:
						row['publishers'] = metadata['publishers']

					if args.all or args.releaseDate:
						try:
							row['releaseDate'] = time.strftime("%Y-%m-%d", time.localtime(metadata['releaseDate']))
						except:
							row['releaseDate'] = metadata['releaseDate']

					if args.all or args.themes:
						row['themes'] = metadata['themes']

				# Original images
				if args.all or args.imageBackground or args.imageSquare or args.imageVertical:
					images = jls('images')
					if args.all or args.imageBackground:
						row['backgroundImage'] = images['background'] or ''
					if args.all or args.imageSquare:
						row['squareIcon'] = images['squareIcon'] or ''
					if args.all or args.imageVertical:
						row['verticalCover'] = images['verticalCover'] or ''

				# CSV listification
				for key, value in row.items():
					if type(value) == list or type(value) == set:
						row[key] = ",".join(value)

				writer.writerow(row)

if __name__ == "__main__":
	def ba(variableName, description, defaultValue=False):
		""" Boolean argument: creates a default boolean argument with the name of the storage variable and
			the description to be shown in the help screen
		"""
		return {
			'action': 'store_true',
			'required': defaultValue,
			'help': description,
			'dest': variableName,
		}

	args = Arguments(
		[
			[
				['-d'],
				{
					'default': ',',
					'type': str,
					'required': False,
					'metavar': 'CHARACTER',
					'help': 'CSV field separator, defaults to comma',
					'dest': 'delimiter',
				}
			],
			[['-a', '--all'], ba('all', 'extracts all the fields')],
			[['--critics-score'], ba('criticsScore', 'critics rating score')],
			[['--developers'], ba('developers', 'list of developers')],
			[['--genres'], ba('genres', 'game genres')],
			[['--image-background'], ba('imageBackground', 'background image')],
			[['--image-square'], ba('imageSquare', 'square icon')],
			[['--image-vertical'], ba('imageVertical', 'vertical cover image')],
			[['--platforms'], ba('platforms', 'list of platforms the game is available on')],
			[['--publishers'], ba('publishers', 'list of publishers')],
			[['--release-date'], ba('releaseDate', 'release date of the software')],
			[['--summary'], ba('summary', 'game summary')],
			[['--themes'], ba('themes', 'game themes')],
			[['--playtime'], ba('playtime', 'time spent playing the game')],
		],
		description='GOG Galaxy 2 exporter: scans the local Galaxy 2 database to export a list of games and related information into a CSV'
	)

	if args.anyOption(['delimiter']):
		extractData(args)
	else:
		args.help()