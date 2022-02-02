import json
import argparse
import tempfile
import zipfile
import sha256
import os
from addonManifest import AddonManifest

TEMP_DIR = tempfile.gettempdir()
VALID_JSON = os.path.join(
	os.path.dirname(__file__), "..", "_tests", "testData", "addons", "fake", "13.0.0.json"
)


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


def getSha256(addonPath: str) -> str:
	with open(addonPath, "rb") as f:
		sha256Addon = sha256.sha256_checksum(f)
	return sha256Addon


def generateJsonFile(addonPath, parentDir, channel, publisher, sourceUrl, url) -> None:
	manifest = getAddonManifest(addonPath)
	sha256 = getSha256(addonPath)
	addonId = manifest["name"]
	addonDisplayName = manifest["summary"]
	addonDescription = manifest["description"]
	addonHomepage = manifest["url"]
	addonVersionNumber = manifest["version"]
	addonMinVersion = manifest["minimumNVDAVersion"]
	addonLastTestedVersion = manifest["lastTestedNVDAVersion"]
	with open(VALID_JSON, "r") as f:
		data = json.load(f)
	del data["sha256-comment"]
	data["addonId"] = addonId
	data["displayName"] = addonDisplayName
	data["description"] = addonDescription
	data["URL"] = url
	data["homepage"] = addonHomepage
	data["addonVersionName"] = addonVersionNumber
	versionMajor = int(addonVersionNumber.split(".")[0])
	versionMinor = int(addonVersionNumber.split(".")[1])
	if len(addonVersionNumber.split(".")) > 2:
		versionPatch = int(addonVersionNumber.split(".")[2])
	else:
		versionPatch = 0
	data["addonVersionNumber"]["major"] = versionMajor
	data["addonVersionNumber"]["minor"] = versionMinor
	data["addonVersionNumber"]["patch"] = versionPatch
	stringVersion = ".".join([str(versionMajor), str(versionMinor), str(versionPatch)])
	minVersionMajor = int(addonMinVersion.split(".")[0])
	minVersionMinor = int(addonMinVersion.split(".")[1])
	if len(addonMinVersion.split(".")) > 2:
		minVersionPatch = int(addonMinVersion.split(".")[2])
	else:
		minVersionPatch = 0
	data["minNVDAVersion"]["major"] = minVersionMajor
	data["minNVDAVersion"]["minor"] = minVersionMinor
	data["minNVDAVersion"]["patch"] = minVersionPatch
	lastVersionMajor = int(addonLastTestedVersion.split(".")[0])
	lastVersionMinor = int(addonLastTestedVersion.split(".")[1])
	if len(addonLastTestedVersion.split(".")) > 2:
		lastVersionPatch = int(addonLastTestedVersion.split(".")[2])
	else:
		lastVersionPatch = 0
	data["lastTestedVersion"]["major"] = lastVersionMajor
	data["lastTestedVersion"]["minor"] = lastVersionMinor
	data["lastTestedVersion"]["patch"] = lastVersionPatch
	data["sha256"] = sha256
	data["channel"] = channel
	data["publisher"] = publisher
	data["sourceURL"] = sourceUrl
	dir = os.path.join(parentDir, addonId)
	if not os.path.isdir(dir):
		os.makedirs(dir)
	filename = f"{stringVersion}.json"
	filePath = os.path.join(dir, filename)
	if os.path.isfile(filePath):
		with open(filePath, "rt") as f:
			previousData = json.load(f)
			previousPublisher = previousData["publisher"]
		assert publisher == previousData["publisher"], f"publisher should be {previousPublisher}"
	with open(filePath, "wt") as f:
		json.dump(data, f, indent="\t")
	print(f"Json file is in {dir}/{filename}.")


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		dest="file",
		help="The add-on (nvda-addon) file to create json from manifest."
	)
	parser.add_argument(
		dest="parentDir",
		help="Parent directory to store the json file."
	)
	parser.add_argument(
		dest="channel",
		help="The channel for this release."
	)
	parser.add_argument(
		dest="publisher",
		help="The publisher for this submission."
	)
	parser.add_argument(
		dest="sourceUrl",
		help="The URL to review source code."
	)
	parser.add_argument(
		dest="url",
		help="URL to download the add-on."
	)
	args = parser.parse_args()
	filename = args.file
	parentDir = args.parentDir
	channel = args.channel
	publisher = args.publisher
	sourceUrl = args.sourceUrl
	url = args.url
	generateJsonFile(filename, parentDir, channel, publisher, sourceUrl, url)


if __name__ == '__main__':
	main()
