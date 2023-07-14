#!/usr/bin/env python

# Copyright (C) 2023 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

import argparse
import glob
import json
import os
import sys
from urllib.request import urlretrieve

from typing import (
	Optional,
)

sys.path.append(os.path.dirname(__file__))  # To allow this module to be run as a script by runcreatejson.bat
# E402 module level import not at top of file
from manifestLoader import getAddonManifest, getAddonManifestLocalizations, TEMP_DIR  # noqa:E402
del sys.path[-1]


def regenerateJsonFile(filePath: str, errorFilePath: Optional[str]) -> None:
	with open(filePath) as f:
		addonData = json.load(f)
	addonData["translations"] = []
	addonFilePath = os.path.join(TEMP_DIR, "addon.nvda-addon")
	urlretrieve(addonData["URL"], addonFilePath)
	manifest = getAddonManifest(addonFilePath)
	if manifest.errors:
		if errorFilePath:
			with open(errorFilePath, "w") as errorFile:
				errorFile.write(f"Validation Errors:\n{manifest.errors}")
		raise ValueError(f"Invalid manifest file: {manifest.errors}")

	for langCode, manifest in getAddonManifestLocalizations(manifest):
		addonData["translations"].append(
			{
				"language": langCode,
				"displayName": manifest["summary"],
				"description": manifest["description"],
			}
		)
	
	with open(filePath, "wt") as f:
		json.dump(addonData, f, indent="\t")
	print(f"Wrote json file: {filePath}")


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--dir",
		dest="parentDir",
		help="Parent directory to regenerate the JSON files inside.",
		required=True,
	)
	parser.add_argument(
		"--output",
		dest="errorOutputFile",
		help="The text file to output errors from the validation, if any.",
		default=None,
	)
	args = parser.parse_args()
	errorFilePath: Optional[str] = args.errorOutputFile
	for addonJsonFile in glob.glob(f"{args.parentDir}/**/*.json"):
		regenerateJsonFile(addonJsonFile, errorFilePath)


if __name__ == '__main__':
	main()
