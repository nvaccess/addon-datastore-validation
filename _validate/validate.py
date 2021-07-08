#!/usr/bin/env python

# Copyright (C) 2021 Noelia Ruiz Martínez, NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

import argparse
import os
import sys
import tempfile
import zipfile
import urllib.request

sys.path.append(os.path.dirname(__file__))
import sha256
from addonManifest import AddonManifest
del sys.path[-1]

DOWNLOAD_BLOCK_SIZE = 8192 # 8 kb
TEMP_DIR = tempfile.gettempdir()

def getDownloadUrlErrors(url):
	errors = []
	if not url.startswith("https://"):
		errors.append("add-on download url must start with https://")
	if not url.endswith(".nvda-addon"):
		errors.append("add-on download url must end with .nvda-addon")
	return errors

def downloadAddon(url):
	destPath = os.path.join(TEMP_DIR, "addon.nvda-addon")
	remote = urllib.request.urlopen(url)
	if remote.code != 200:
		raise RuntimeError("Download failed with code %d" % remote.code)
	size = int(remote.headers["content-length"])
	with open(destPath, "wb") as local:
		read = 0
		chunk=DOWNLOAD_BLOCK_SIZE
		while True:
			if size -read <chunk:
				chunk =size -read
			block = remote.read(chunk)
			if not block:
				break
			read += len(block)
			local.write(block)
	return destPath

def getSha256(destPath):
	with open(destPath, "rb") as f:
		sha256Addon = sha256.sha256_checksum(f)
		return sha256Addon

def getAddonManifest(destPath):
	expandedPath = os.path.join(TEMP_DIR, "nvda-addon")
	with zipfile.ZipFile(destPath, "r") as z:
		for info in z.infolist():
			z.extract(info, expandedPath)
	filePath = os.path.join(expandedPath, "manifest.ini")
	try:
		manifest = AddonManifest(filePath)
		return manifest
	except Exception as err:
		raise err

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		dest="file",
		help="The add-on download URL."
	)
	args = parser.parse_args()
	url = args.file
	destPath = downloadAddon(url=url)
	manifest = getAddonManifest(destPath=destPath)
	addonName = manifest["summary"]
	addonAuthor = manifest["author]"]
	addonVersion = manifest["version"]
	metadata = "### Release information\r\n"
	metadata += f"- Addon name: {addonName}"
	metadata += f"- Addon author: {addonAuthor}"
	metadata += f"- Addon version: {addonVersion}"
	with open(os.pat.join(os.path.dirname(__file__), "metadata.txt"), "w", encoding="utf-8") as f:
		f.write(metadata)




if __name__ == '__main__':
	main()
