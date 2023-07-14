# Copyright (C) 2022 Noelia Ruiz Martínez, NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

from glob import glob
import os
import pathlib
from typing import Generator, Tuple
import zipfile
from addonManifest import AddonManifest
import tempfile
TEMP_DIR = tempfile.gettempdir()


def getAddonManifest(addonPath: str) -> AddonManifest:
	""" Extract manifest.ini from *.nvda-addon and parse.
	Raise on error.
	"""
	expandedPath = os.path.join(TEMP_DIR, "nvda-addon")
	with zipfile.ZipFile(addonPath, "r") as z:
		for info in z.infolist():
			z.extract(info, expandedPath)
	filePath = os.path.join(expandedPath, "manifest.ini")
	try:
		manifest = AddonManifest(filePath)
		return manifest
	except Exception as err:
		raise err


def getAddonManifestLocalizations(
		manifest: AddonManifest
) -> Generator[Tuple[str, AddonManifest], None, None]:
	""" Extract data from translated manifest.ini from *.nvda-addon and parse.
	Raise on error.
	"""
	if manifest.filename is None:
		# Ignore during tests
		return
	addonFolder = pathlib.Path(manifest.filename).parent.absolute().as_posix()
	filePaths = os.path.join(addonFolder, "locale", "*", "manifest.ini")
	for translationFile in glob(filePaths):
		languageCode = pathlib.Path(translationFile).parent.name
		try:
			translatedManifest = AddonManifest(translationFile)
			yield languageCode, translatedManifest
		except Exception as err:
			print(f"Error in {translationFile}")
