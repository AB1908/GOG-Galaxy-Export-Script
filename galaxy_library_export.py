#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from enum import Enum
import json
from natsort import natsorted
from os.path import exists
import re
import sqlite3
import time

class Arguments():
	""" argparse wrapper, to reduce code verbosity """
	__parser = None
	__args = None
	__bAll = False  # Extract all fields

	def __init__(self, args, **kwargs):
		import argparse
		self.__parser = argparse.ArgumentParser(**kwargs)
		for arg in args:
			self.__parser.add_argument(*arg[0], **arg[1])
		self.__args = self.__parser.parse_args()
		self.__bAll = getattr(self.__args, 'all')

	def help(self):
		self.__parser.print_help()

	def anyOption(self, exceptions):
		self.notExportOptions = exceptions
		for k,v in self.__args.__dict__.items():
			if (k not in exceptions) and v:
				return True
		return False

	def extractAll(self):
		self.__bAll = True

	def __getitem__(self, name):
		return self.__getattr__(name)

	def __getattr__(self, name):
		ret = getattr(self.__args, name)
		if isinstance(ret, bool) and (name not in self.notExportOptions):
			ret = self.__bAll or ret
		elif isinstance(ret, list) and (1 == len(ret)):
			ret = ret[0]
		return ret

class Type(Enum):
	""" used to specify the field type while parsing the raw data """
	STRING = 0
	STRING_JSON = 1
	INTEGER = 10
	DATE = 20
	LIST = 30

class Positions(dict):
	""" small dictionary to avoid errors while parsing non-exported field positions """
	def __getitem__(self, key):
		try:
			return dict.__getitem__(self, key)
		except KeyError:
			return None

def extractData(args):
	database_location = args.fileDB
	platforms = {"3do": "3DO Interactive Multiplayer", "3ds": "Nintendo 3DS", "aion": "Aion", "aionl": "Aion: Legions of War", "amazon": "Amazon", "amiga": "Amiga", "arc": "ARC", "atari": "Atari 2600", "battlenet": "Battle.net", "bb": "BestBuy", "beamdog": "Beamdog", "bethesda": "Bethesda.net", "blade": "Blade & Soul", "c64": "Commodore 64", "d2d": "Direct2Drive", "dc": "Dreamcast", "discord": "Discord", "dotemu": "DotEmu", "egg": "Newegg", "elites": "Elite Dangerous", "epic": "Epic Games Store", "eso": "The Elder Scrolls Online", "fanatical": "Fanatical", "ffxi": "Final Fantasy XI", "ffxiv": "Final Fantasy XIV", "fxstore": "Placeholder", "gamehouse": "GameHouse", "gamesessions": "GameSessions", "gameuk": "GAME UK", "generic": "Other", "gg": "GamersGate", "glyph": "Trion World", "gmg": "Green Man Gaming", "gog": "GOG", "gw": "Guild Wars", "gw2": "Guild Wars 2", "humble": "Humble Bundle", "indiegala": "IndieGala", "itch": "Itch.io", "jaguar": "Atari Jaguar", "kartridge": "Kartridge", "lin2": "Lineage 2", "minecraft": "Minecraft", "n64": "Nintendo 64", "ncube": "Nintendo GameCube", "nds": "Nintendo DS", "neo": "NeoGeo", "nes": "Nintendo Entertainment System", "ngameboy": "Game Boy", "nswitch": "Nintendo Switch", "nuuvem": "Nuuvem", "nwii": "Wii", "nwiiu": "Wii U", "oculus": "Oculus", "origin": "Origin", "paradox": "Paradox Plaza", "pathofexile": "Path of Exile", "pce": "PC Engine", "playasia": "Play-Asia", "playfire": "Playfire", "ps2": "PlayStation 2", "psn": "PlayStation Network", "psp": "PlayStation Portable", "psvita": "PlayStation Vita", "psx": "PlayStation", "riot": "Riot", "rockstar": "Rockstar Games Launcher", "saturn": "Sega Saturn", "sega32": "32X", "segacd": "Sega CD", "segag": "Sega Genesis", "sms": "Sega Master System", "snes": "Super Nintendo Entertainment System", "stadia": "Google Stadia", "star": "Star Citizen", "steam": "Steam", "test": "Test", "totalwar": "Total War", "twitch": "Twitch", "unknown": "Unknown", "uplay": "Uplay", "vision": "ColecoVision", "wargaming": "Wargaming", "weplay": "WePlay", "winstore": "Windows Store", "xboxog": "Xbox", "xboxone": "Xbox Live", "zx": "ZX Spectrum PC"}

	def loadOptions():
		""" Loads options from `settings.json` and initialises defaults """
		defaults = {"TreatDLCAsGame": [], "TreatReleaseAsDLC": {}}

		# Load settings from disk
		try:
			with open('settings.json', 'r', encoding='utf-8') as f:
				o = json.load(f)
		except:
			o = {}
		
		# Initialise defaults
		for k, v in defaults.items():
			if k not in o:
				o[k] = v

		return o

	def id(name):
		""" Returns the numeric ID for the specified type """
		return cursor.execute('SELECT id FROM GamePieceTypes WHERE type="{}"'.format(name)).fetchone()[0]

	def clean(s):
		""" Cleans strings for CSV consumption """
		for f in clean.filters:
			s = f.sub('\\\\n', s)  # Convert CRLF, LF, <br> into '\n' string
		return s
	clean.filters = [
		re.compile(r'\s*?(?:\r?\n|<br\s*/?>)')
	]

	def jld(name, bReturnParsed=False, object=None):
		""" json.loads(`name`), optionally returning the purified sub-object of the same name,
		    for cases such as {`name`: {`name`: "string"}}
		"""
		v = json.loads((object if object else result)[positions[name]])
		if not bReturnParsed:
			return v
		v = v[name]
		return clean(v) if isinstance(v, str) else v

	def prepare(resultName, fields, dbField=None, dbRef=None, dbCondition=None, dbCustomJoin=None, dbResultField=None, dbGroupBy=None):
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
		if dbCustomJoin:
			og_joins.append(' ' + dbCustomJoin)
		if dbResultField:
			og_resultFields.append(dbResultField)
		if dbGroupBy:
			og_resultGroupBy.append(dbGroupBy)
	
	def includeField(object, columnName, fieldName=None, fieldType=Type.STRING, paramName=None, delimiter=','):
		if args[columnName if not paramName else paramName]:
			if None is fieldName:
				fieldName = columnName
			try:
				if Type.INTEGER is fieldType:
					row[columnName] = round(object[fieldName])
				elif Type.DATE is fieldType:
					row[columnName] = time.strftime("%Y-%m-%d", time.localtime(object[fieldName]))
				elif Type.STRING is fieldType:
					row[columnName] = object[fieldName]
				elif Type.STRING_JSON is fieldType:
					row[columnName] = jld(fieldName, True)
				elif Type.LIST is fieldType:
					s = object[fieldName].split(delimiter)
					row[columnName] = set(s) if 1 < len(s) else objectFieldName
			except:
				row[columnName] = object[fieldName]

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

	# Load options before opening the DB
	options = loadOptions()

	with OpenDB() as cursor:
		# Create a view of ProductPurchaseDates (= purchased/added games) joined on GamePieces for a full owned game data DB
		owned_game_database = """CREATE TEMP VIEW MasterList AS
				SELECT GamePieces.releaseKey, GamePieces.gamePieceTypeId, GamePieces.value FROM ProductPurchaseDates
				JOIN GamePieces ON ProductPurchaseDates.gameReleaseKey = GamePieces.releaseKey;"""

		# Set up default queries and processing metadata, and always extract the game title along with any parameters
		prepare.nextPos = 2
		positions = Positions({'releaseKey': 0, 'title': 1})
		fieldnames = ['title']
		og_fields = ["""CREATE TEMP VIEW MasterDB AS SELECT DISTINCT(MasterList.releaseKey) AS releaseKey, MasterList.value AS title, PLATFORMS.value AS platformList"""]
		og_references = [""" FROM MasterList, MasterList AS PLATFORMS"""]
		og_joins = []
		og_conditions = [""" WHERE MasterList.gamePieceTypeId={} AND PLATFORMS.releaseKey=MasterList.releaseKey AND PLATFORMS.gamePieceTypeId={}""".format(
					id('title'),
					id('allGameReleases')
				)]
		og_order = """ ORDER BY title;"""
		og_resultFields = ['GROUP_CONCAT(DISTINCT MasterDB.releaseKey)', 'MasterDB.title']
		og_resultGroupBy = ['MasterDB.platformList']

		# title can be customized by user, allow extraction of original title
		if args.originalTitle:
			prepare(
				'originalTitle',
				{'originalTitle': True},
				dbField='ORIGINALTITLE.value AS originalTitle',
				dbRef='MasterList AS ORIGINALTITLE',
				dbCondition='ORIGINALTITLE.releaseKey=MasterList.releaseKey AND ORIGINALTITLE.gamePieceTypeId={}'.format(id('originalTitle')),
				dbResultField='MasterDB.originalTitle'
			)

		# (User customised) sorting title, same export data sorting as in the Galaxy client
		prepare(
			'sortingTitle',
			{'sortingTitle': args.sortingTitle},
			dbField='SORTINGTITLE.value AS sortingTitle',
			dbRef='MasterList AS SORTINGTITLE',
			dbCondition='(SORTINGTITLE.releaseKey=MasterList.releaseKey) AND (SORTINGTITLE.gamePieceTypeId={})'.format(id('sortingTitle')),
			dbResultField='MasterDB.sortingTitle'
		)

		# Create parameterised filtered view of owned games using multiple joins: the order
		# in which we `prepare` them, is the same as they will appear as CSV columns
		if args.summary:
			prepare(
				'summary',
				{'summary': True},
				dbField='SUMMARY.value AS summary',
				dbRef='MasterList AS SUMMARY',
				dbCondition='(SUMMARY.releaseKey=MasterList.releaseKey) AND (SUMMARY.gamePieceTypeId={})'.format(id('summary')),
				dbResultField='MasterDB.summary'
			)

		if args.platforms:
			prepare(
				'platforms',
				{'platformList': True},
			)

		# add filednames of metadata and orginalMetadata
		# this allows to order them in a way that metadata values are followed by their related originalMetadata value in the export
		for name,condition in {
					'criticsScore': args.criticsScore,
					'developers': args.developers,
					'genres': args.genres,
					'publishers': args.publishers,
					'releaseDate': args.releaseDate,
					'originalReleaseDate': args.originalReleaseDate,
					'themes': args.themes,
				}.items():
			if condition:
				fieldnames.append(name)
			
		if args.criticsScore or args.developers or args.genres or args.publishers or args.releaseDate or args.themes:
			prepare(
				'metadata',
				{}, # fieldnames are added separateley together with their related originalMetadata fields
				dbField='METADATA.value AS metadata',
				dbRef='MasterList AS METADATA',
				dbCondition='METADATA.releaseKey=MasterList.releaseKey AND METADATA.gamePieceTypeId={}'.format(id('meta')),
				dbResultField='MasterDB.metadata'
			)

		if args.originalReleaseDate:
			prepare(
				'originalMetadata',
				{}, # fieldnames are added separateley together with their related metadata fields
				dbField='ORIGINALMETADATA.value AS originalMetadata',
				dbRef='MasterList AS ORIGINALMETADATA',
				dbCondition='ORIGINALMETADATA.releaseKey=MasterList.releaseKey AND ORIGINALMETADATA.gamePieceTypeId={}'.format(id('originalMeta')),
				dbResultField='MasterDB.originalMetadata'
			)

		if args.playtime:
			prepare(
				'playtime',
				{'gameMins': True},
				dbField='GAMETIMES.minutesInGame AS time',
				dbRef='GAMETIMES',
				dbCondition='GAMETIMES.releaseKey=MasterList.releaseKey',
				dbResultField='sum(MasterDB.time)'
			)

		if args.tags:
			prepare(
				'tags',
				{'tags': True},
				dbField='USERRELEASETAGS.tag AS tags',
				dbCustomJoin='LEFT JOIN USERRELEASETAGS ON USERRELEASETAGS.releaseKey=MasterList.releaseKey',
				dbResultField='GROUP_CONCAT(MasterDB.tags)'
			)

		prepare(  # Grab a list of DLCs for filtering, regardless of whether we're exporting them or not
			'dlcs',
			{'dlcs': args.dlcs},
			# concatenate all dlcs of the game in one list to make sure all dlcs from the different platforms are found
			dbField="""DLC.value AS dlcs,
						CASE
							WHEN DLC.value IS NULL OR DLC.value IN ('{"dlcs":null}', '{"dlcs":[]}')
							THEN NULL
							ELSE REPLACE(REPLACE(DLC.value, '{"dlcs":[', ''), ']}', '')
						END AS dlcList""",
			dbRef='MasterList AS DLC',
			dbCondition='(DLC.releaseKey=MasterList.releaseKey) AND (DLC.gamePieceTypeId={})'.format(id('dlcs')),
			dbResultField="""'{"dlcs":[' || COALESCE(GROUP_CONCAT(MasterDB.dlcList), '') || ']}'"""
		)

		if args.isHidden:
			prepare(
				'isHidden',
				{'isHidden': True},
				dbField='UserReleaseProperties.isHidden AS isHidden',
				dbCustomJoin='LEFT JOIN USERRELEASEPROPERTIES ON USERRELEASEPROPERTIES.releaseKey=MasterList.releaseKey',
				dbResultField='CASE WHEN MasterDB.isHidden = 1 THEN \'True\' ELSE \'False\' END'
			)

		if args.osCompatibility:
			prepare(
				'osCompatibility',
				{'osCompatibility': True},
				# concatenate lists of operating systems because different platforms can support different systems
				dbField="""OSCOMPATIBILITY.value AS osCompatibility,
							CASE
								WHEN OSCOMPATIBILITY.value IS NULL OR OSCOMPATIBILITY.value IN ('{"supported":[]}', '{"supported":null}') 
								THEN NULL 
								ELSE REPLACE(REPLACE(OSCOMPATIBILITY.value, '{"supported":[', ''), ']}', '')
							END AS osList""",
				dbRef='MasterList AS OSCOMPATIBILITY',
				dbCondition='OSCOMPATIBILITY.releaseKey=MasterList.releaseKey AND OSCOMPATIBILITY.gamePieceTypeId={}'.format(id('osCompatibility')),
				dbResultField="""'{"supported":[' || COALESCE(GROUP_CONCAT(MasterDB.osList), '') || ']}'"""
			)

		if args.imageBackground or args.imageSquare or args.imageVertical:
			prepare(
				'images',
				{
					'backgroundImage': args.imageBackground,
					'squareIcon': args.imageSquare,
					'verticalCover': args.imageVertical
				},
				dbField='IMAGES.value AS images',
				dbRef='MasterList AS IMAGES',
				dbCondition='(IMAGES.releaseKey=MasterList.releaseKey) AND (IMAGES.gamePieceTypeId={})'.format(id('originalImages')),
				dbResultField='MasterDB.images'
			)

		# Display each game and its details along with corresponding release key grouped by releasesList
		unique_game_data = """SELECT {} FROM MasterDB GROUP BY {} ORDER BY MasterDB.title;""".format(
			', '.join(og_resultFields),
			', '.join(og_resultGroupBy)
		)

		# Perform the queries
		cursor.execute(owned_game_database)
		cursor.execute(''.join(og_fields + og_references + og_joins + og_conditions) + og_order)
		cursor.execute(unique_game_data)

		# Prepare a list of games and DLCs
		results = []
		dlcs = set()
		while True:
			result = cursor.fetchone()
			if not result: break
			results.append((result[0].split(','), result))
			d = jld('dlcs', True)
			if d:
				for dlc in d:
					dlcs.add(dlc)
		results = natsorted(results, key=lambda r: str.casefold(str(json.loads(r[1][positions['sortingTitle']])['title'])))

		# Exclude games mistakenly treated as DLCs, such as "3 out of 10, EP2"
		for dlc in options['TreatDLCAsGame']:
			dlcs.discard(dlc)

		# Add dlcs mistakenly treated as games, such as "Grey Goo - Emergence Campaign"
		additionalDLCs = options['TreatReleaseAsDLC']
		for game in additionalDLCs.keys():
			dlcs.update(additionalDLCs[game])

		# There are spurious random dlcNUMBERa entries in the library, plus a few DLCs which appear
		# multiple times in different ways and are not attached to a game
		titleExclusion = re.compile(r'^(?:'
				r'dlc_?[0-9]+_?a'
				r'|alternative look for yennefer(?:\s+\[[a-z]+\])?'
				r'|beard and hairstyle set for geralt(?:\s+\[[a-z]+\])?'
				r'|new quest - contract: missing miners(?:\s+\[[a-z]+\])?'
				r'|temerian armor set(?:\s+\[[a-z]+\])?'
		r')$')

		# Compile the CSV
		try:
			with open(args.fileCSV, 'w', encoding='utf-8', newline='') as csvfile:
				writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=args.delimiter)
				writer.writeheader()
				for (ids, result) in results:
					# Only consider games for the list, not DLCs
					if not args.exportDlcDetails and 0 < len([x for x in ids if x in dlcs]):
						continue

					try:
						# JSON string needs to be converted to dict
						# For json.load() to work correctly, all double quotes must be correctly escaped
						try:
							row = {'title': jld('title', True)}
							if (not row['title']) or (titleExclusion.match(str.casefold(row['title']))):
								continue
						except:
							# No title or {'title': null}
							continue


						# SortingTitle
						if args.sortingTitle:
							try:
								sortingTitle = jld('sortingTitle')
								row['sortingTitle'] = sortingTitle['title']
							except:
								row['sortingTitle'] = ''

						# OriginalTitle
						if args.originalTitle:
							try:
								originalTitle = jld('originalTitle')
								row['originalTitle'] = originalTitle['title']
							except:
								row['originalTitle'] = ''


						# Playtime
						includeField(result, 'gameMins', positions['playtime'], paramName='playtime')

						# Summaries
						includeField(result, 'summary', fieldType=Type.STRING_JSON)

						# Platforms
						if args.platforms:
							rkeys = result[positions['releaseKey']].split(',')
							if any(platform in releaseKey for platform in platforms for releaseKey in rkeys):
								row['platformList'] = set(platforms[platform] for releaseKey in rkeys for platform in platforms if releaseKey.startswith(platform))
							else:
								row['platformList'] = []

						# Various metadata
						if args.criticsScore or args.developers or args.genres or args.publishers or args.releaseDate or args.themes:
							metadata = jld('metadata')
							includeField(metadata, 'criticsScore', fieldType=Type.INTEGER)
							includeField(metadata, 'developers')
							includeField(metadata, 'genres')
							includeField(metadata, 'publishers')
							includeField(metadata, 'releaseDate', fieldType=Type.DATE)
							includeField(metadata, 'themes')

						# Original metadata
						if args.originalReleaseDate:
							originalMetadata = jld('originalMetadata')
							includeField(originalMetadata, 'originalReleaseDate', 'releaseDate', fieldType=Type.DATE)

						# Original images
						if args.imageBackground or args.imageSquare or args.imageVertical:
							images = jld('images')
							includeField(images, 'backgroundImage', 'background', paramName='imageBackground')
							includeField(images, 'squareIcon', paramName='imageSquare')
							includeField(images, 'verticalCover', paramName='imageVertical')
						
						# DLCs
						if args.dlcs:
							row['dlcs'] = set()
							dlcList = jld('dlcs', True)
							if dlcList == None:
								dlcList = []
							if options["TreatReleaseAsDLC"]:
								rkeys = result[positions['releaseKey']].split(',')
								for key in rkeys:
									if options["TreatReleaseAsDLC"].get(key) != None:
										dlcList.extend(options["TreatReleaseAsDLC"][key])
								
							for dlc in dlcList:
								try:
									# Check the availability of the DLC in the games list (uncertain)
									d = next(x[1] for x in results if dlc in x[0])
									if d:
										row['dlcs'].add(jld('title', True, d))
								except StopIteration:
									pass

						# Tags
						if args.tags:
							includeField(result, 'tags', positions['tags'], fieldType=Type.LIST)

						# isHidden
						if args.isHidden:
							includeField(result, 'isHidden', positions['isHidden'], fieldType=Type.STRING)

						# osCompatibility
						if args.osCompatibility:
							row['osCompatibility'] = set()
							osCompatibility = jld('osCompatibility')
							osList = osCompatibility['supported']
							if osList:
								for operatingSystem in osList:
									row['osCompatibility'].add(operatingSystem['name'])

						# Set conversion, list sorting, empty value reset
						for k,v in row.items():
							if v:
								if list == type(v) or set == type(v):
									row[k] = natsorted(list(row[k]), key=str.casefold)
									if not args.pythonLists:
										row[k] = args.delimiter.join(row[k])
							else:
								row[k] = ''

						writer.writerow(row)
					except Exception as e:
						print('Parsing failed on: {}'.format(result))
						raise e
		except FileNotFoundError:
			print('Unable to write to “{}”, make sure that the path exists and that you have the write permissions'.format(args.fileCSV))
			return

if __name__ == "__main__":
	defaultDBlocation = 'C:\\ProgramData\\GOG.com\\Galaxy\\storage\\galaxy-2.0.db'

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

	# Set up the arguments
	args = Arguments(
		[
			[
				['-i', '--input'],
				{
					'default': defaultDBlocation,
					'type': str,
					'nargs': 1,
					'required': False,
					'metavar': 'FN',
					'help': 'pathname of the galaxy2 database',
					'dest': 'fileDB',
				}
			],
			[
				['-o', '--output'],
				{
					'default': 'gameDB.csv',
					'type': str,
					'nargs': 1,
					'required': False,
					'metavar': 'FN',
					'help': 'pathname of the generated CSV',
					'dest': 'fileCSV',
				}
			],
			[
				['-d'],
				{
					'default': '\t',
					'type': str,
					'required': False,
					'metavar': 'CHARACTER',
					'help': 'CSV field separator, defaults to comma',
					'dest': 'delimiter',
				}
			],
			[['-a', '--all'], ba('all', '(default) extracts all the fields')],
			[['--sorting-title'], ba('sortingTitle', '(user customised) sorting title')],
			[['--title-original'], ba('originalTitle', 'original title independent of any user changes')],
			[['--critics-score'], ba('criticsScore', 'critics rating score')],
			[['--developers'], ba('developers', 'list of developers')],
			[['--dlcs'], ba('dlcs', 'list of dlc titles for the specified game')],
			[['--genres'], ba('genres', 'game genres')],
			[['--image-background'], ba('imageBackground', 'background image')],
			[['--image-square'], ba('imageSquare', 'square icon')],
			[['--image-vertical'], ba('imageVertical', 'vertical cover image')],
			[['--platforms'], ba('platforms', 'list of platforms the game is available on')],
			[['--publishers'], ba('publishers', 'list of publishers')],
			[['--release-date'], ba('releaseDate', '(user customized) release date of the software')],
			[['--release-date-original'], ba('originalReleaseDate', 'original release date independent of any user changes')],
			[['--summary'], ba('summary', 'game summary')],
			[['--tags'], ba('tags', 'user tags')],
			[['--hidden'], ba('isHidden', 'is gamne hidden in galaxy client')],
			[['--os-compatibility'], ba('osCompatibility', 'list of supported operating systems')],
			[['--themes'], ba('themes', 'game themes')],
			[['--playtime'], ba('playtime', 'time spent playing the game')],
			[['--dlcs-details'], ba('exportDlcDetails', 'add a separate entry for each dlc with all available information to the exported csv')],
			[['--py-lists'], ba('pythonLists', 'export lists as Python parseable instead of delimiter separated strings')],
		],
		description='GOG Galaxy 2 exporter: scans the local Galaxy 2 database to export a list of games and related information into a CSV'
	)

	if not args.anyOption(['delimiter', 'fileCSV', 'fileDB', 'pythonLists', 'exportDlcDetails']):
		args.extractAll()
	if exists(args.fileDB):
		extractData(args)
	else:
		print('Unable to find the DB “{}”, make sure that {}'.format(
			args.fileDB,
			'GOG Galaxy 2 is installed' if defaultDBlocation == args.fileDB else 'you specified the correct path'
		))

