# GOG Galaxy 2.0 Export Script

This script helps a user export their GOG Galaxy 2.0 Library.

## TL;DR / brief how to use

1. Install Python 3, through Windows Store or manually if you prefer
2. Download the [source files](https://github.com/AB1908/GOG-Galaxy-Export-Script/archive/refs/heads/master.zip) and unzip it in a directory of your choice
3. Open the command prompt (`Win+R`, write `cmd` and press Enter) and enter the directory you chose with `cd /d DIRECTORY`, replacing `DIRECTORY` with the directory in which `galaxy_library_export.py` resides
4. Install python's requirements:
   ```
   python -m pip install csv natsort
   ```
5. Export the CSV with:
   ```
   python galaxy_library_export.py
   ```

By default this scripts export everything it can into the CSV. If you would like to customize the results, read below.

## Usage

Through the use of command line parameters, you can decide what data you want exported to the CSV. Some of the options include the list of platforms (`--platforms`), playtime in minutes (`--playtime`), developers, publishers, genres and much more. You can read the help manual by invoking the script without parameters, to find an up to date list of all the possible export options.

If you want to use the CSV in a different tool, such as the [HTML5 library exporter](https://github.com/Varstahl/GOG-Galaxy-HTML5-exporter), you can default to the `-a` parameter to export everything.

When a different locale wants a different CSV delimiter (such as the Italian), you can manually specify the character to use (`-d <character>`).

Also, you can manually specify the database location (`-i`) and the CSV location (`-o`), instead of using the default ones.

If the CSV has to be read by a Python script, you can use the option `--py-lists` to export python compatible list strings that can be reconverted in python objects through `ast`'s `literal_eval`, which avoids several (potentially incorrect) string split/joins.

If you also want to export all available dlcs use the `--dlcs-details` argument. With that all dlcs are handled as "games" and will be exported with all available infos.

## settings.json

The settings.json allows to handle dlcs as game and export them accordingly or treat any release (game, dlc, soundtrack, goodies pack etc.) as dlc of another game, if they are not already linked in the database.

- *TreatDLCAsGame*: Aarray of release-keys which should be treated as a game instead of a dlc
  - Used to mark games which are (mistakenly) treated as dlcs by the gog galaxy client as games.
  - All entries with a matching release-key will be exported with all available data.
  - This will not change the link between a dlc and his parent game if it really is a dlc.
- *TreatReleaseAsDLC*: Dictionary which maps the releaseKey of a game to a list of dlcs.
  - Used to mark any release which is (mistakenly) treated as a game by the gog galaxy client as dlc.
  - The dlcs specified in the settings.json are joined with the list of dlcs found in the database.
  - *TreatReleaseAsDLC* is evaluated after *TreatDLCAsGame*. If a release-key is present in *TreatDLCAsGame* and also mapped to another release-key with *TreatReleaseAsDLC* than this release-key is handled as dlc.
  - This will not override the original link between a dlc and it's parent game. If a dlc is mapped to another game it will be present in the dlc list of this game and the original game.


## Dependencies

- Python 3
  - csv
  - natsort

## Platform Support

All platforms from the [official list](https://github.com/gogcom/galaxy-integrations-python-api/blob/master/PLATFORM_IDs.md) are supported. Some are not listed at the moment but should still show up correctly in the output.

## Wiki

Check the [Wiki tab](https://github.com/AB1908/GOG-Galaxy-Export-Script/wiki).

## Roadmap 

Check the [Projects tab](https://github.com/AB1908/GOG-Galaxy-Export-Script/projects).

## Contribution

Feel free to add issues and pull requests.

## License

This repository is licensed under the [MIT License](https://github.com/AB1908/GOG-Galaxy-Export-Script/blob/master/LICENSE).
