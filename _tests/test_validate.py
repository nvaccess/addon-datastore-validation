#!/usr/bin/env python

# Copyright (C) 2021 Noelia Ruiz Martínez, NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.
# For more details see: https://www.gnu.org/licenses/gpl-2.0.html

import unittest
from mock import patch
import os
import json
from jsonschema import exceptions
from _validate import validate, addonManifest


JSON_SCHEMA = validate.JSON_SCHEMA
TOP_DIR = os.path.abspath(os.path.dirname(__file__))
SOURCE_DIR = os.path.dirname(TOP_DIR)
TEST_DATA_PATH = os.path.join(SOURCE_DIR, '_tests', 'testData')
ADDON_PACKAGE = os.path.join(TEST_DATA_PATH, 'fake.nvda-addon')
ADDON_SUBMISSIONS_DIR = os.path.join(TEST_DATA_PATH, 'addons')
VALID_SUBMISSION_JSON_FILE = os.path.join(ADDON_SUBMISSIONS_DIR, 'fake', '13.0.json')
MANIFEST_FILE = os.path.join(TEST_DATA_PATH, 'manifest.ini')


def getValidAddonSubmission() -> validate.JsonObjT:
	with open(VALID_SUBMISSION_JSON_FILE) as f:
		submission = json.load(f)
	return submission


def getAddonManifest():
	with open(MANIFEST_FILE) as f:
		manifest = addonManifest.AddonManifest(f)
	return manifest


class TestValidate(unittest.TestCase):

	def setUp(self):
		self.submissionData = getValidAddonSubmission()
		self.manifest = getAddonManifest()

	def tearDown(self):
		self.submissionData = None
		self.manifest = None

	def test_validateJson_validDoesNotRaise(self):
		validate._validateJson(self.submissionData)

	def test_validateJson_SchemaNonConformance_Raises(self):
		self.submissionData["description"] = 3  # should be a string
		with self.assertRaises(exceptions.ValidationError):
			validate._validateJson(self.submissionData)

	def test_checkDownloadUrlFormat_validExampleURL(self):
		url = (
			"https://github.com/nvdaes/clipContentsDesigner/releases/download/13.0/"
			"clipContentsDesigner-13.0.nvda-addon"
		)
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(errors, [])

	def test_checkDownloadUrlFormat_minimalRequirementsURL(self):
		url = "https://something.nvda-addon"
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(errors, [])

	def test_checkDownloadUrlFormat_missingHTTPS(self):
		url = "http://something.nvda-addon"
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(
			errors,
			[validate.ValidationErrorMessage.URL_MISSING_HTTPS.value]
		)

	def test_checkDownloadUrlFormat_missingExt(self):
		url = "https://example.com"
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(
			errors,
			[validate.ValidationErrorMessage.URL_MISSING_ADDON_EXT.value]
		)

	def test_checkDownloadUrlFormat_missingHTTPsAndExt(self):
		url = "http://example.com"
		errors = list(
			validate.checkDownloadUrlFormat(url)
		)
		self.assertEqual(
			errors,
			[
				validate.ValidationErrorMessage.URL_MISSING_HTTPS.value,
				validate.ValidationErrorMessage.URL_MISSING_ADDON_EXT.value,
			]
		)

	def test_checkSha256_valid(self):
		sha: str = self.submissionData["sha256"]
		errors = validate.checkSha256(
			ADDON_PACKAGE,
			expectedSha=sha.upper()
		)
		self.assertEqual(list(errors), [])

		errors = validate.checkSha256(
			ADDON_PACKAGE,
			expectedSha=sha.lower()
		)

	def test_checkSha256_invalid(self):
		errors = validate.checkSha256(
			# just do a SHA for the manifest file so we don't need to include the whole *.nvda-addon file
			ADDON_PACKAGE,
			expectedSha='abc'
		)
		errors = list(errors)
		expectedErrorMessage = validate.ValidationErrorMessage.CHECKSUM_FAILURE.value
		actualSha = self.submissionData["sha256"].lower()
		self.assertEqual(
			errors,
			[expectedErrorMessage.format(actualSha)]
		)

	def test_checkSummaryMatchesName_valid(self):
		errors = list(
			validate.checkSummaryMatchesName(self.manifest, self.submissionData)
		)
		self.assertEqual(errors, [])

	def test_checkSummaryMatchesName_invalid(self):
		self.submissionData["name"] = "notCorrect"
		errors = list(
			validate.checkSummaryMatchesName(self.manifest, self.submissionData)
		)
		expectedErrorMessage = validate.ValidationErrorMessage.NAME.value
		self.assertEqual(
			errors,
			[expectedErrorMessage.format(self.manifest["summary"])]
		)

	def test_checkDescriptionMatches_valid(self):
		errors = list(
			validate.checkDescriptionMatches(self.manifest, self.submissionData)
		)
		self.assertEqual(errors, [])

	def test_checkDescriptionMatches_invalid(self):
		self.submissionData["description"] = "incorrect"
		errors = list(
			validate.checkDescriptionMatches(self.manifest, self.submissionData)
		)
		expectedErrorMessage = validate.ValidationErrorMessage.DESC.value
		self.assertEqual(
			errors,
			[expectedErrorMessage.format(self.manifest["description"])]
		)

	def test_checkNameMatchesPath_valid(self):
		errors = list(
			validate.checkNameMatchesPath(self.manifest, VALID_SUBMISSION_JSON_FILE)
		)
		self.assertEqual(errors, [])

	def test_checkNameMatchesPath_invalid(self):
		filename = os.path.join(TOP_DIR, "invalid")
		errors = list(
			validate.checkNameMatchesPath(self.manifest, filename)
		)
		expectedErrorMessage = validate.ValidationErrorMessage.SUBMISSION_DIR_ADDON_NAME.value
		self.assertEqual(
			errors,
			[expectedErrorMessage.format(self.manifest['name'])]
		)

	def test_checkVersionMatchesFilename_valid(self):
		errors = list(
			validate.checkVersionMatchesFilename(self.manifest, VALID_SUBMISSION_JSON_FILE)
		)
		self.assertEqual(errors, [])

	def test_checkVersionMatchesFilename_invalid(self):
		filename = os.path.join(ADDON_SUBMISSIONS_DIR, "fake", "12.2.json")
		errors = list(
			validate.checkVersionMatchesFilename(self.manifest, filename)
		)
		expectedErrorMessage = validate.ValidationErrorMessage.SUBMISSION_DIR_ADDON_VER.value
		self.assertEqual(
			errors,
			[expectedErrorMessage.format(self.manifest['version'])]
		)

	def test_output_errorRaises(self):
		singleErrorGen = ("error string" for _ in range(1))
		with self.assertRaises(ValueError):
			validate.outputResult(singleErrorGen)

	def test_output_noError(self):
		noErrorGen = ("error string" for _ in range(0))
		validate.outputResult(noErrorGen)


class Validate_End2End(unittest.TestCase):

	class OpenUrlResult:
		def __init__(self, readFunc):
			self.read = readFunc
			self.code = 200
			self.headers = {
				"content-length": os.path.getsize(ADDON_PACKAGE)
			}

	def setUp(self) -> None:
		self.addonReader = open(ADDON_PACKAGE, 'rb')
		self.urlOpenResult = self.OpenUrlResult(self.addonReader.read)

	def tearDown(self) -> None:
		self.addonReader.close()

	@patch('_validate.validate.urllib.request.urlopen')
	def test_success(self, mock_urlopen):
		"""Run validate on a known good file.
		"""
		mock_urlopen.return_value = self.urlOpenResult
		errors = list(
			validate.validateSubmission(VALID_SUBMISSION_JSON_FILE)
		)
		self.assertEqual(list(errors), [])

	@patch('_validate.validate.urllib.request.urlopen')
	def test_downloadFailure(self, mock_urlopen):
		"""Unable to download addon
		"""
		self.urlOpenResult.code = 404  # add-on not found
		mock_urlopen.return_value = self.urlOpenResult
		errors = list(
			validate.validateSubmission(VALID_SUBMISSION_JSON_FILE)
		)
		self.assertEqual(
			list(errors),
			[
				'Download of addon failed',
				'Fatal error, unable to continue: Unable to download from '
				# note this the mocked urlopen function actually fetches from ADDON_PACKAGE
				'https://github.com/'
				'nvdaes/clipContentsDesigner/releases/download/13.0/'
				'clipContentsDesigner-13.0.nvda-addon, '
				'HTTP response status code: 404'
			]
		)
