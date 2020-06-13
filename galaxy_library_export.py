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
		for k,v in self.__args.__dict__.items():
			if (k not in exceptions) and v:
				return True
		return False

	def __getitem__(self, name):
		return self.__getattr__(name)

	def __getattr__(self, name):
		ret = getattr(self.__args, name)
		if isinstance(ret, bool):
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
	
	def includeField(object, columnName, fieldName=None, fieldType=Type.STRING, paramName=None):
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

	with OpenDB() as cursor:
		# Create a view of GameLinks joined on GamePieces for a full owned game data DB
		owned_game_database = """CREATE TEMP VIEW MasterList AS
				SELECT GamePieces.releaseKey, GamePieces.gamePieceTypeId, GamePieces.value FROM GameLinks
				JOIN GamePieces ON GameLinks.releaseKey = GamePieces.releaseKey;"""

		# Set up default queries and processing metadata, and always extract the game title along with any parameters
		prepare.nextPos = 2
		positions = Positions({'releaseKey': 0, 'title': 1})
		fieldnames = ['title']
		og_fields = ["""CREATE TEMP VIEW MasterDB AS SELECT DISTINCT(MasterList.releaseKey) AS releaseKey, MasterList.value AS title, PLATFORMS.value AS platformList"""]
		og_references = [""" FROM MasterList, MasterList AS PLATFORMS"""]
		og_conditions = [""" WHERE ((MasterList.gamePieceTypeId={}) OR (MasterList.gamePieceTypeId={})) AND ((PLATFORMS.releaseKey=MasterList.releaseKey) AND (PLATFORMS.gamePieceTypeId={}))""".format(
					id('originalTitle'),
					id('title'),
					id('allGameReleases')
				)]
		og_order = """ ORDER BY title;"""
		og_resultFields = ['GROUP_CONCAT(DISTINCT MasterDB.releaseKey)', 'MasterDB.title']
		og_resultGroupBy = ['MasterDB.platformList']

		# Create parameterised filtered view of owned games using multiple joins: the order
		# in which we `prepare` them, is the same as they will appear as CSV columns
		if args.summary:
			prepare(
				'summary',
				{'summary': True},
				'SUMMARY.value AS summary',
				'MasterList AS SUMMARY',
				'(SUMMARY.releaseKey=MasterList.releaseKey) AND (SUMMARY.gamePieceTypeId={})'.format(id('summary')),
				'MasterDB.summary'
			)

		if args.platforms:
			prepare(
				'platforms',
				{'platformList': True},
			)

		if args.criticsScore or args.developers or args.genres or args.publishers or args.releaseDate or args.themes:
			prepare(
				'metadata',
				{
					'criticsScore': args.criticsScore,
					'developers': args.developers,
					'genres': args.genres,
					'publishers': args.publishers,
					'releaseDate': args.releaseDate,
					'themes': args.themes,
				},
				'METADATA.value AS metadata',
				'MasterList AS METADATA',
				'(METADATA.releaseKey=MasterList.releaseKey) AND ((METADATA.gamePieceTypeId={}) OR (METADATA.gamePieceTypeId={}))'.format(id('originalMeta'), id('meta')),
				'MasterDB.metadata'
			)

		if args.playtime:
			prepare(
				'playtime',
				{'gameMins': True},
				'GAMETIMES.minutesInGame AS time',
				'GAMETIMES',
				'GAMETIMES.releaseKey=MasterList.releaseKey',
				'sum(MasterDB.time)'
			)

		prepare(  # Grab a list of DLCs for filtering, regardless of whether we're exporting them or not
			'dlcs',
			{'dlcs': args.dlcs},
			'DLC.value AS dlcs',
			'MasterList AS DLC',
			'(DLC.releaseKey=MasterList.releaseKey) AND (DLC.gamePieceTypeId={})'.format(id('dlcs')),
			'MasterDB.dlcs'
		)

		if args.imageBackground or args.imageSquare or args.imageVertical:
			prepare(
				'images',
				{
					'backgroundImage': args.imageBackground,
					'squareIcon': args.imageSquare,
					'verticalCover': args.imageVertical
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
		results = natsorted(results, key=lambda r: str.casefold(r[1][positions['title']]))

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
					if 0 < len([x for x in ids if x in dlcs]):
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
							includeField(metadata, 'criticsScore', fieldType=Type.DATE)
							includeField(metadata, 'themes')

						# Original images
						if args.imageBackground or args.imageSquare or args.imageVertical:
							images = jld('images')
							includeField(images, 'backgroundImage', 'background', paramName='imageBackground')
							includeField(images, 'squareIcon', paramName='imageSquare')
							includeField(images, 'verticalCover', paramName='imageVertical')
						
						# DLCs
						if args.dlcs:
							row['dlcs'] = set()
							for dlc in jld('dlcs', True):
								try:
									# Check the availability of the DLC in the games list (uncertain)
									d = next(x[1] for x in results if dlc in x[0])
									if d:
										row['dlcs'].add(jld('title', True, d))
								except StopIteration:
									pass

						# Set conversion, list sorting, empty value reset
						for k,v in row.items():
							if v:
								if list == type(v) or set == type(v):
									row[k] = natsorted(list(row[k]), key=str.casefold)
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
			[['--dlcs'], ba('dlcs', 'list of dlc titles for the specified game')],
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

	if args.anyOption(['delimiter', 'fileCSV', 'fileDB']):
		if exists(args.fileDB):
			extractData(args)
		else:
			print('Unable to find the DB “{}”, make sure that {}'.format(
				args.fileDB,
				'GOG Galaxy 2 is installed' if defaultDBlocation == args.fileDB else 'you specified the correct path'
			))
	else:
		args.help()
