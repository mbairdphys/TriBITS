# @HEADER
# ************************************************************************
#
#            TriBITS: Tribal Build, Integrate, and Test System
#                    Copyright 2013 Sandia Corporation
#
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the Corporation nor the names of the
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY SANDIA CORPORATION "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SANDIA CORPORATION OR THE
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ************************************************************************
# @HEADER

import os
import sys
import re
import copy
import shutil
import unittest
import pprint

from FindCISupportDir import *
import CDashQueryAnalyzeReport as CDQAR

g_testBaseDir = CDQAR.getScriptBaseDir()

tribitsBaseDir=os.path.abspath(g_testBaseDir+"/../../tribits")
mockProjectBaseDir=os.path.abspath(tribitsBaseDir+"/examples/MockTrilinos")

g_pp = pprint.PrettyPrinter(indent=4)


#
# Some helper functions
# 


# Search for a list of regexs in order in a list of strings
def assertFindStringInListOfStrings(
  testObj,
  stringToFind,
  stringsList,
  stringsListName,
  ):
  foundStringToFind = False
  for stdoutLine in stringsList:
    if stdoutLine.find(stringToFind) != -1:
      foundStringToFind = True
      break
  testObj.assertTrue(foundStringToFind,
    "Error, could not find string '"+stringToFind+"' in "+stringsListName+"!")


# Search for a list of regexs in order in a list of strings
def assertListOfRegexsFoundInLinstOfStrs(
  testObj,
  regexList,
  stringsList,
  stringsListName,
  debugPrint=False,
  ):
  # Set up for first regex
  current_regex_idx = 0
  currentRe = re.compile(regexList[current_regex_idx])
  # Loop over the lines in the input strings list and look for the regexes in
  # order!
  strLine_idx = -1
  for strLine in stringsList:
    strLine_idx += 1
    if current_regex_idx == len(regexList):
      # Found all the regexes so we are done!
      break
    if debugPrint:
      print("\nstrLine_idx = '"+str(strLine_idx)+"'")
      print("strLine = '"+strLine+"'")
      print("regexList["+str(current_regex_idx)+"] = '"+regexList[current_regex_idx]+"'")
    if currentRe.match(strLine):
      # Found the current regex being looked for!
      if debugPrint:
        print("Found match!")
      current_regex_idx += 1
      if current_regex_idx < len(regexList):
        if debugPrint:
          print("regexList["+str(current_regex_idx)+"] = '"+regexList[current_regex_idx]+"'")
        currentRe = re.compile(regexList[current_regex_idx])
      continue
  # Look to see if you have found all of the regexes being searched for.  If
  # the current one has not been found, then report that you could not find
  # it!
  if current_regex_idx < len(regexList):
    testObj.assertTrue(False,
      "Error, could not find the regex '"+regexList[current_regex_idx]+"'"+\
      " in "+stringsListName+"!")


# Base test directory in the build tree
g_baseTestDir="cdash_analyze_and_report"


# Set up the test case directory and copy starter files into it
#
# These files can then be modified in order to define other test cases.
#
def cdash_analyze_and_report_setup_test_dir(
  testCaseName,
  buildSetName="ProjectName Nightly Builds",
  copyFrom="raw_cdash_data_twoif_12_twif_9",
  ):
  testInputDir = testCiSupportDir+"/"+g_baseTestDir+"/"+copyFrom
  testOutputDir = g_baseTestDir+"/"+testCaseName
  shutil.copytree(testInputDir, testOutputDir)
  baseFilePrefix = CDQAR.getFileNameStrFromText(buildSetName)
  filesToRename = [ "fullCDashIndexBuilds.json", "fullCDashNonpassingTests.json" ]
  for fileToRename in filesToRename:
    oldName = testOutputDir+"/"+fileToRename
    newName = testOutputDir+"/"+baseFilePrefix+"_"+fileToRename
    os.rename(oldName, newName)
  return testOutputDir


# Extract test dicts list from a cdash/queryTests.php JSON cache file
def getTestsDictListFromCDashJsonFile(testOutputDir, testJsonRelFilePath):
  testsJsonFileFullPath = testOutputDir+"/"+testJsonRelFilePath
  with open(testsJsonFileFullPath, 'r') as testsJsonFile:
    testsJson = eval(testsJsonFile.read())
  return testsJson['builds']


# Write test dicts list to cdash/queryTests.php JSON cache file
def writeTestsDictListToCDashJsonFile(testsLOD, testOutputDir, testJsonRelFilePath):
  testsJsonFileFullPath = testOutputDir+"/"+testJsonRelFilePath
  testsJson = { 'builds': testsLOD }
  CDQAR.pprintPythonDataToFile(testsJson, testsJsonFileFullPath)


# Extract test history dicts list from a cdash/queryTests.php JSON cache file
def getTestHistoryDictListFromCDashJsonFile(testOutputDir, testHistoryFileName):
  testsJsonRelFilePath = "test_history/"+testHistoryFileName
  return getTestsDictListFromCDashJsonFile(testOutputDir, testsJsonRelFilePath)


# Write test history dicts list to a cdash/queryTests.php JSON cache file
def writeTestHistoryDictListFromCDashJsonFile(testHistoryLOD,
    testOutputDir, testHistoryFileName,
  ):
  testHistoryJsonRelFilePath = "test_history/"+testHistoryFileName
  writeTestsDictListToCDashJsonFile(testHistoryLOD, testOutputDir,
    testHistoryJsonRelFilePath)


# Extract nonpassing test dicts lists from ctest/queryTests.php cache file
def getNonpassTestsDictListFromCDashJsonFile(testOutputDir,
    buildSetName="ProjectName Nightly Builds",
  ):
  baseFilePrefix = CDQAR.getFileNameStrFromText(buildSetName)
  testsJsonRelFilePath = baseFilePrefix+"_fullCDashNonpassingTests.json"
  return getTestsDictListFromCDashJsonFile(testOutputDir, testsJsonRelFilePath)


# Write nonpassing test dicts lists to ctest/queryTests.php cache file
def writeNonpassTestsDictListToCDashJsonFile(testsLOD, testOutputDir,
    buildSetName="ProjectName Nightly Builds",
  ):
  baseFilePrefix = CDQAR.getFileNameStrFromText(buildSetName)
  testsJsonRelFilePath = baseFilePrefix+"_fullCDashNonpassingTests.json"
  writeTestsDictListToCDashJsonFile(testsLOD, testOutputDir, testsJsonRelFilePath)


# Run a test case involving the cdash_analyze_and_report.py
#
# This function runs a test case involving a the script
# cdash_analyze_and_report.py.
#
def cdash_analyze_and_report_run_case(
  testObj,
  testCaseName,
  extraCmndLineOptionsList,
  expectedRtnCode,
  expectedSummaryLineStr,
  stdoutRegexList,
  htmlFileRegexList,
  verbose=False,
  debugPrint=False,
  ):

  # Change into test directory
  pwdDir = os.getcwd()
  testOutputDir = g_baseTestDir+"/"+testCaseName
  os.chdir(testOutputDir)

  try:

    # Create expression commandline to run
  
    htmlFileName = "htmlFile.html"
    htmlFileAbsPath = os.getcwd()+"/"+htmlFileName
  
    cmnd = ciSupportDir+"/cdash_analyze_and_report.py"+\
      " --date=2018-10-28"+\
      " --cdash-project-name='ProjectName'"+\
      " --build-set-name='ProjectName Nightly Builds'"+\
      " --cdash-site-url='https://something.com/cdash'"+\
      " --cdash-builds-filters='builds_filters'"+\
      " --cdash-nonpassed-tests-filters='nonpasssing_tests_filters'"+\
      " --use-cached-cdash-data=on"+\
      " --expected-builds-file=expectedBuilds.csv"+\
      " --tests-with-issue-trackers-file=testsWithIssueTrackers.csv"+\
      " --write-email-to-file="+htmlFileName+\
      " "+" ".join(extraCmndLineOptionsList)
  
    # Run cdash_analyze_and_report.py
    stdoutFile = "stdout.out"
    stdoutFileAbsPath = os.getcwd()+"/"+stdoutFile
    rtnCode = CDQAR.echoRunSysCmnd(cmnd, throwExcept=False,
      outFile=stdoutFile, verbose=verbose)
  
    # Check the return code
    testObj.assertEqual(rtnCode, expectedRtnCode)
  
    # Read the STDOUT into a array of string so we can grep it
    with open(stdoutFile, 'r') as stdout:
      stdoutStrList = stdout.read().split("\n")
  
    # Grep the STDOUT for other grep strings
    assertListOfRegexsFoundInLinstOfStrs(testObj, stdoutRegexList,
      stdoutStrList, stdoutFileAbsPath, debugPrint=debugPrint)
  
    # Look for STDOUT for expected summary line
    assertFindStringInListOfStrings(testObj, expectedSummaryLineStr,
      stdoutStrList, stdoutFileAbsPath)
    # NOTE: We search for this last in STDOUT so that we can match the
    # individual parts first.
  
    # Release the list of strings for the STDOUT file
    stdoutStrList = None
  
    # Search for expected regexes and in HTML file
    with open(htmlFileName, 'r') as htmlFile:
      htmlFileStrList = htmlFile.read().split("\n")
    assertListOfRegexsFoundInLinstOfStrs(testObj, htmlFileRegexList,
      htmlFileStrList, htmlFileAbsPath, debugPrint=debugPrint)

  finally:
    os.chdir(pwdDir)


#############################################################################
#
# System-level tests for cdash_analyze_and_report.py
#
#############################################################################


class test_cdash_analyze_and_report(unittest.TestCase):


  # Base case for raw CDash data we happened to choose for all fo tests tests
  #
  # This first test checks several parts of the STDOUT and HTML output that
  # other tests will not check.  In particular, this really pins down the
  # tables 'twoif' and 'twif'.  Other tests will not do this to avoid
  # duplication in testing.
  #
  def test_twoif_12_twif_9(self):

    testCaseName = "twoif_12_twif_9"

    cdash_analyze_and_report_setup_test_dir(testCaseName)

    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      ["--print-details=on"],  # grep for verbose output
      1,
      "FAILED (twoif=12, twif=9): ProjectName Nightly Builds on 2018-10-28",
      [
        "[*][*][*] Query and analyze CDash results for ProjectName Nightly Builds for testing day 2018-10-28",
        "Num expected builds = 6",
        "Num tests with issue trackers = 9",
        "Num builds = 6",
        "Num nonpassing tests direct from CDash query = 21",
        "Num nonpassing tests after removing duplicate tests = 21",
        "Num nonpassing tests without issue trackers = 12",
        "Num nonpassing tests with issue trackers = 9",
        "Num nonpassing tests without issue trackers Failed = 12",
        "Num nonpassing tests without issue trackers Not Run = 0",
        "Num nonpassing tests with issue trackers Failed = 9",
        "Num nonpassing tests with issue trackers Not Run = 0",
        "Num tests with issue trackers gross passing or missing = 0",

        "Builds Missing: bm=0",
        "Builds with Configure Failures: cf=0",
        "Builds with Build Failures: bf=0",
        "Num tests with issue trackers Passed = 0",
        "Num tests with issue trackers Missing = 0",
        "Tests without issue trackers Failed: twoif=12",

        "Getting 30 days of history for Anasazi_Epetra_BKS_norestart_test_MPI_4 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "  Since the file exists, using cached data from file:",
        "    .+/twoif_12_twif_9/test_history/2018-10-28-mutrino-Trilinos-atdm-mutrino-intel-opt-openmp-KNL-Anasazi_Epetra_BKS_norestart_test_MPI_4-HIST-30.json",
        "Getting 30 days of history for Belos_gcrodr_hb_MPI_4 in the build ",
        # Above grep order should pin down the file name matched with the test
        # name.

        "Tests with issue trackers Failed: twif=9",
        ],
      [
        # Top title
        "<h2>Build and Test results for ProjectName Nightly Builds on 2018-10-28</h2>",

        # First paragraph with with links to build and nonpassing tests results on cdsah
        "<p>",
        "<a href=\"https://something[.]com/cdash/index[.]php[?]project=ProjectName&date=2018-10-28&builds_filters\">Builds on CDash</a> [(]num/expected=6/6[)]<br>",
        "<a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&date=2018-10-28&nonpasssing_tests_filters\">Non-passing Tests on CDash</a> [(]num=21[)]<br>",
        "</p>",

        # Second paragraph with listing of different types of tables below
        "<p>",
        "<font color=\"red\">Tests without issue trackers Failed: twoif=12</font><br>",
        "Tests with issue trackers Failed: twif=9<br>",
        "</p>",
         
        # twoif table
        "<h3><font color=\"red\">Tests without issue trackers Failed [(]limited to 10[)]: twoif=12</font></h3>",
        # Pin down table headers
        "<th>Site</th>",
        "<th>Build Name</th>",
        "<th>Test Name</th>",
        "<th>Status</th>",
        "<th>Details</th>",
        "<th>Consec&shy;utive Non-pass Days</th>",
        "<th>Non-pass Last 30 Days</th>",
        "<th>Pass Last 30 Days</th>",
        "<th>Issue Tracker</th>",
        # Pin down the first row of this table (pin down this first row
        "<tr>",
        "<td align=\"left\"><a href=\"https://something[.]com/cdash/index[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=4&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-mutrino-intel-opt-openmp-KNL&field2=site&compare2=61&value2=mutrino&field3=buildstarttime&compare3=84&value3=2018-10-29T00:00:00&field4=buildstarttime&compare4=83&value4=2018-09-29T00:00:00\">Trilinos-atdm-mutrino-intel-opt-openmp-KNL</a></td>",
        "<td align=\"left\"><a href=\"https://something[.]com/cdash/testDetails[.]php[?]test=57860629&build=4107240\">Anasazi_&shy;Epetra_&shy;BKS_&shy;norestart_&shy;test_&shy;MPI_&shy;4</a></td>",
        "<td align=\"left\"><a href=\"https://something[.]com/cdash/testDetails[.]php[?]test=57860629&build=4107240\"><font color=\"red\">Failed</font></a></td>",
        "<td align=\"left\">Completed [(]Failed[)]</td>",
        "<td align=\"right\"><a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=5&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-mutrino-intel-opt-openmp-KNL&field2=testname&compare2=61&value2=Anasazi_Epetra_BKS_norestart_test_MPI_4&field3=site&compare3=61&value3=mutrino&field4=buildstarttime&compare4=84&value4=2018-10-29T00:00:00&field5=buildstarttime&compare5=83&value5=2018-09-29T00:00:00\"><font color=\"red\">30</font></a></td>",
        "<td align=\"right\"><a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=5&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-mutrino-intel-opt-openmp-KNL&field2=testname&compare2=61&value2=Anasazi_Epetra_BKS_norestart_test_MPI_4&field3=site&compare3=61&value3=mutrino&field4=buildstarttime&compare4=84&value4=2018-10-29T00:00:00&field5=buildstarttime&compare5=83&value5=2018-09-29T00:00:00\"><font color=\"red\">30</font></a></td>",
        "<td align=\"right\"><a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=5&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-mutrino-intel-opt-openmp-KNL&field2=testname&compare2=61&value2=Anasazi_Epetra_BKS_norestart_test_MPI_4&field3=site&compare3=61&value3=mutrino&field4=buildstarttime&compare4=84&value4=2018-10-29T00:00:00&field5=buildstarttime&compare5=83&value5=2018-09-29T00:00:00\"><font color=\"green\">0</font></a></td>",
        "<td align=\"right\"></td>",
        "</tr>",
        # Second row
        "<td align=\"left\"><a href=\"https://something[.]com/cdash/testDetails[.]php[?]test=57860535&build=4107241\">Belos_&shy;gcrodr_&shy;hb_&shy;MPI_&shy;4</a></td>",

        # twif table
        "<h3>Tests with issue trackers Failed: twif=9</h3>",
        "<td align=\"left\"><a href=\"https://something[.]com/cdash/index[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=4&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-cee-rhel6-clang-opt-serial&field2=site&compare2=61&value2=cee-rhel6&field3=buildstarttime&compare3=84&value3=2018-10-29T00:00:00&field4=buildstarttime&compare4=83&value4=2018-09-29T00:00:00\">Trilinos-atdm-cee-rhel6-clang-opt-serial</a></td>"
        ],
      #verbose=True,
      #debugPrint=True,
      )


  # Base case for raw CDash data but no expected builds or tests with issue
  # trackers CSV files
  #
  # This test shows that you can leave these arguments blank and just run the
  # script pointing to a CDash site and get useful info.
  #
  def test_twoif_21_no_input_csv_files(self):

    testCaseName = "twoif_21_no_input_csv_files"

    cdash_analyze_and_report_setup_test_dir(testCaseName)

    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      [
        "--expected-builds-file=",
        "--tests-with-issue-trackers-file=",
        ],
      1,
      "FAILED (twoif=21): ProjectName Nightly Builds on 2018-10-28",
      [
        "Num expected builds = 0",
        "Num tests with issue trackers = 0",
        "Num builds = 6",
        "Num nonpassing tests direct from CDash query = 21",
        "Num nonpassing tests after removing duplicate tests = 21",
        "Num nonpassing tests without issue trackers = 21",
        "Num nonpassing tests with issue trackers = 0",
        "Num nonpassing tests without issue trackers Failed = 21",
        "Num nonpassing tests without issue trackers Not Run = 0",
        "Num nonpassing tests with issue trackers Failed = 0",
        "Num nonpassing tests with issue trackers Not Run = 0",
        "Num tests with issue trackers gross passing or missing = 0",

        "Builds Missing: bm=0",
        "Builds with Configure Failures: cf=0",
        "Builds with Build Failures: bf=0",
        "Num tests with issue trackers Passed = 0",
        "Num tests with issue trackers Missing = 0",
        "Tests without issue trackers Failed: twoif=21",

        "Getting 30 days of history for Anasazi_Epetra_BKS_norestart_test_MPI_4 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        ],
      [
        # Top title
        "<h2>Build and Test results for ProjectName Nightly Builds on 2018-10-28</h2>",

        # First paragraph with with links to build and nonpassing tests results on cdsah
        "<p>",
        "<a href=\"https://something[.]com/cdash/index[.]php[?]project=ProjectName&date=2018-10-28&builds_filters\">Builds on CDash</a> [(]num/expected=6/0[)]<br>",
        "<a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&date=2018-10-28&nonpasssing_tests_filters\">Non-passing Tests on CDash</a> [(]num=21[)]<br>",
        "</p>",

        # Second paragraph with listing of different types of tables below
        "<p>",
        "<font color=\"red\">Tests without issue trackers Failed: twoif=21</font><br>",
        "</p>",
         
        # twoif table
        "<h3><font color=\"red\">Tests without issue trackers Failed [(]limited to 10[)]: twoif=21</font></h3>",
        ],
      #verbose=True,
      #debugPrint=True,
      )


  # Test out Not Run tests
  #
  # This test checks the tables 'twoinr' and 'twinr' in detail and checks some
  # of the contents of the 'twoif' and 'twif'.  To do this, we just change the
  # 'status' of a few tests in the fullCDashNonpassingTests.json file from
  # 'Failed' to 'Not Run'.
  #
  def test_twoif_10_twoinr2_twif_8_twinr_1(self):

    testCaseName = "twoif_10_twoinr2_twif_8_twinr_1"

    # Copy the raw files to get started
    testOutputDir = cdash_analyze_and_report_setup_test_dir(testCaseName)

    # Change the status for few tests from 'Failed' to 'Not Run'.

    daysOfHistory = 30

    # Get list of nonpassing tests from Json file
    testsLOD = getNonpassTestsDictListFromCDashJsonFile(testOutputDir)
    testListSLOD = CDQAR.createSearchableListOfTests(testsLOD)

    # make twoif test Anasazi_Epetra_BKS_norestart_test_MPI_4 Not Run

    testStatusBuildTestList = [
      'mutrino',
      'Trilinos-atdm-mutrino-intel-opt-openmp-KNL',
      'Anasazi_Epetra_BKS_norestart_test_MPI_4',
      ]
    testDict = testListSLOD.lookupDictGivenKeyValuesList(testStatusBuildTestList)
    testDict['status'] = u'Not Run'
    testDict['details'] = u'Required Files Missing'

    testHistoryFileName = CDQAR.getTestHistoryCacheFileName( "2018-10-28",
      testStatusBuildTestList[0], testStatusBuildTestList[1], testStatusBuildTestList[2],
      daysOfHistory)
    testHistoryLOD = getTestHistoryDictListFromCDashJsonFile(
      testOutputDir, testHistoryFileName)
    testHistoryLOD.sort(reverse=True, key=CDQAR.DictSortFunctor(['buildstarttime']))
    testHistoryLOD[0]['status'] = u'Not Run'
    testHistoryLOD[0]['details'] = u'Missing Required Files'
    writeTestHistoryDictListFromCDashJsonFile(testHistoryLOD, testOutputDir,
      testHistoryFileName) 

    # make twoif test Belos_gcrodr_hb_MPI_4 Not Run 

    testStatusBuildTestList = [
      'mutrino',
      'Trilinos-atdm-mutrino-intel-opt-openmp-KNL',
      'Belos_gcrodr_hb_MPI_4',
      ]
    testDict = testListSLOD.lookupDictGivenKeyValuesList(testStatusBuildTestList)
    testDict['status'] = u'Not Run'
    testDict['details'] = u'Required Files Missing'

    testHistoryFileName = CDQAR.getTestHistoryCacheFileName( "2018-10-28",
      testStatusBuildTestList[0], testStatusBuildTestList[1], testStatusBuildTestList[2],
      daysOfHistory)
    testHistoryLOD = getTestHistoryDictListFromCDashJsonFile(
      testOutputDir, testHistoryFileName)
    testHistoryLOD.sort(reverse=True, key=CDQAR.DictSortFunctor(['buildstarttime']))
    testHistoryLOD[0]['status'] = u'Not Run'
    testHistoryLOD[0]['details'] = u'Missing Required Files'
    writeTestHistoryDictListFromCDashJsonFile(testHistoryLOD, testOutputDir,
      testHistoryFileName) 

    # make twif test Teko_ModALPreconditioner_MPI_1 Not Run

    testStatusBuildTestList = [
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-clang-opt-serial',
      'Teko_ModALPreconditioner_MPI_1',
      ]
    testDict = testListSLOD.lookupDictGivenKeyValuesList(testStatusBuildTestList)
    testDict['status'] = u'Not Run'
    testDict['details'] = u'Required Files Missing'

    testHistoryFileName = CDQAR.getTestHistoryCacheFileName( "2018-10-28",
      testStatusBuildTestList[0], testStatusBuildTestList[1], testStatusBuildTestList[2],
      daysOfHistory)
    testHistoryLOD = getTestHistoryDictListFromCDashJsonFile(
      testOutputDir, testHistoryFileName)
    testHistoryLOD.sort(reverse=True, key=CDQAR.DictSortFunctor(['buildstarttime']))
    testHistoryLOD[0]['status'] = u'Not Run'
    testHistoryLOD[0]['details'] = u'Missing Required Files'
    writeTestHistoryDictListFromCDashJsonFile(testHistoryLOD, testOutputDir,
      testHistoryFileName) 

    # Write updated test data back to file
    writeNonpassTestsDictListToCDashJsonFile(testsLOD, testOutputDir)

    # Run the script and make sure it outputs the right stuff
    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      [
        "--limit-test-history-days=30",   # Test that you can set this as int
        "--write-failing-tests-without-issue-trackers-to-file=twoif.csv"
        ],
      1,
      "FAILED (twoif=10, twoinr=2, twif=8, twinr=1): ProjectName Nightly Builds on 2018-10-28",
      [
        "Num builds = 6",
        "Num nonpassing tests direct from CDash query = 21",
        "Num nonpassing tests after removing duplicate tests = 21",
        "Num nonpassing tests without issue trackers = 12",
        "Num nonpassing tests with issue trackers = 9",
        "Num nonpassing tests without issue trackers Failed = 10",
        "Num nonpassing tests without issue trackers Not Run = 2",
        "Num nonpassing tests with issue trackers Failed = 8",
        "Num nonpassing tests with issue trackers Not Run = 1",

        "Builds Missing: bm=0",
        "Builds with Configure Failures: cf=0",
        "Builds with Build Failures: bf=0",

        "Tests without issue trackers Failed: twoif=10",
        "Getting 30 days of history for Intrepid2_unit-test_Discretization_Basis_HCURL_TRI_In_FEM_Serial_Test_01_SLFadDouble_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for KokkosKernels_blas_serial_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for KokkosKernels_common_serial_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for KokkosKernels_graph_serial_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for KokkosKernels_sparse_serial_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for MueLu_ConvergenceTpetra_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for MueLu_ConvergenceTpetra_MPI_4 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for Sacado_tradoptest_55_EQA_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for Teko_testdriver_tpetra_MPI_1 in the build Trilinos-atdm-waterman-cuda-9.2-release-debug on waterman from cache file",
        "Getting 30 days of history for Teko_testdriver_tpetra_MPI_4 in the build Trilinos-atdm-waterman-cuda-9.2-release-debug on waterman from cache file",

        "Tests without issue trackers Not Run: twoinr=2",
        "Getting 30 days of history for Anasazi_Epetra_BKS_norestart_test_MPI_4 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for Belos_gcrodr_hb_MPI_4 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",

        "Tests with issue trackers Failed: twif=8",
        "Getting 30 days of history for MueLu_UnitTestsBlockedEpetra_MPI_1 in the build Trilinos-atdm-cee-rhel6-clang-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2 in the build Trilinos-atdm-cee-rhel6-clang-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2 in the build Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2 in the build Trilinos-atdm-cee-rhel6-intel-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager3_MPI_3 in the build Trilinos-atdm-cee-rhel6-clang-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager3_MPI_3 in the build Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager3_MPI_3 in the build Trilinos-atdm-cee-rhel6-intel-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for Stratimikos_test_single_belos_thyra_solver_driver_nos1_nrhs8_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",

        "Tests with issue trackers Not Run: twinr=1",
        "Getting 30 days of history for Teko_ModALPreconditioner_MPI_1 in the build Trilinos-atdm-cee-rhel6-clang-opt-serial on cee-rhel6 from cache file",
        ],
      [

        # Second paragraph with listing of different types of tables below
        "<p>",
        "<font color=\"red\">Tests without issue trackers Failed: twoif=10</font><br>",
        "<font color=\"orange\">Tests without issue trackers Not Run: twoinr=2</font><br>",
        "Tests with issue trackers Failed: twif=8<br>",
        "Tests with issue trackers Not Run: twinr=1<br>",
        "</p>",
         
        # twoif table
        "<h3><font color=\"red\">Tests without issue trackers Failed [(]limited to 10[)]: twoif=10</font></h3>",
        # Pin down the first row of this table
        "<tr>",
        "<td align=\"left\">mutrino</td>",
        "<td align=\"left\"><a href=\"https://something[.]com/cdash/index[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=4&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-mutrino-intel-opt-openmp-KNL&field2=site&compare2=61&value2=mutrino&field3=buildstarttime&compare3=84&value3=2018-10-29T00:00:00&field4=buildstarttime&compare4=83&value4=2018-09-29T00:00:00\">Trilinos-atdm-mutrino-intel-opt-openmp-KNL</a></td>",
        "<td align=\"left\"><a href=\"https://something[.]com/cdash/testDetails[.]php[?]test=57859582&build=4107243\">Intrepid2_&shy;unit-test_&shy;Discretization_&shy;Basis_&shy;HCURL_&shy;TRI_&shy;In_&shy;FEM_&shy;Serial_&shy;Test_&shy;01_&shy;SLFadDouble_&shy;MPI_&shy;1</a></td>",
        "<td align=\"left\"><a href=\"https://something[.]com/cdash/testDetails[.]php[?]test=57859582&build=4107243\"><font color=\"red\">Failed</font></a></td>",
        "<td align=\"left\">Completed [(]Failed[)]</td>",
        "<td align=\"right\"><a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=5&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-mutrino-intel-opt-openmp-KNL&field2=testname&compare2=61&value2=Intrepid2_unit-test_Discretization_Basis_HCURL_TRI_In_FEM_Serial_Test_01_SLFadDouble_MPI_1&field3=site&compare3=61&value3=mutrino&field4=buildstarttime&compare4=84&value4=2018-10-29T00:00:00&field5=buildstarttime&compare5=83&value5=2018-09-29T00:00:00\"><font color=\"red\">1</font></a></td>",
        "<td align=\"right\"><a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=5&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-mutrino-intel-opt-openmp-KNL&field2=testname&compare2=61&value2=Intrepid2_unit-test_Discretization_Basis_HCURL_TRI_In_FEM_Serial_Test_01_SLFadDouble_MPI_1&field3=site&compare3=61&value3=mutrino&field4=buildstarttime&compare4=84&value4=2018-10-29T00:00:00&field5=buildstarttime&compare5=83&value5=2018-09-29T00:00:00\"><font color=\"red\">1</font></a></td>",
        "<td align=\"right\"><a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&filtercombine=and&filtercombine=&filtercount=5&showfilters=1&filtercombine=and&field1=buildname&compare1=61&value1=Trilinos-atdm-mutrino-intel-opt-openmp-KNL&field2=testname&compare2=61&value2=Intrepid2_unit-test_Discretization_Basis_HCURL_TRI_In_FEM_Serial_Test_01_SLFadDouble_MPI_1&field3=site&compare3=61&value3=mutrino&field4=buildstarttime&compare4=84&value4=2018-10-29T00:00:00&field5=buildstarttime&compare5=83&value5=2018-09-29T00:00:00\"><font color=\"green\">29</font></a></td>",
        "<td align=\"right\"></td>",
        "</tr>",

        # twoinr table
        "<h3><font color=\"orange\">Tests without issue trackers Not Run [(]limited to 10[)]: twoinr=2</font></h3>",
        # Pin down the first row of this table
        "<tr>",
        "<td .+mutrino</td>",
        "<td align=\"left\"><a .+>Trilinos-atdm-mutrino-intel-opt-openmp-KNL</a></td>",
        "<td align=\"left\"><a .+>Anasazi_&shy;Epetra_&shy;BKS_&shy;norestart_&shy;test_&shy;MPI_&shy;4</a></td>",
        "<td align=\"left\"><a .+><font color=\"orange\">Not Run</font></a></td>",
        "<td align=\"left\">Required Files Missing</td>",
        "<td align=\"right\"><a .+><font color=\"red\">30</font></a></td>",
        "<td align=\"right\"><a .+><font color=\"red\">30</font></a></td>",
        "<td align=\"right\"><a .+><font color=\"green\">0</font></a></td>",
        "<td align=\"right\"></td>",
        "</tr>",
         
        # twif table
        "<h3>Tests with issue trackers Failed: twif=8</h3>",
        # Pin down the first row of this table
        "<tr>",
        "<td align=\"left\">cee-rhel6</td>",
        "<td align=\"left\"><a .+>Trilinos-atdm-cee-rhel6-clang-opt-serial</a></td>",
        "<td align=\"left\"><a .+>MueLu_&shy;UnitTestsBlockedEpetra_&shy;MPI_&shy;1</a></td>",
        "<td align=\"left\"><a .+><font color=\"red\">Failed</font></a></td>",
        "<td align=\"left\">Completed [(]Failed[)]</td>",
        "<td align=\"right\"><a .+><font color=\"red\">15</font></a></td>",
        "<td align=\"right\"><a .+><font color=\"red\">15</font></a></td>",
        "<td align=\"right\"><a .+><font color=\"green\">0</font></a></td>",
        "<td align=\"right\"><a href=\"https://github.com/trilinos/Trilinos/issues/3640\">#3640</a></td>",
        "</tr>",
         
        # twinr table
        "<h3>Tests with issue trackers Not Run: twinr=1</h3>",
        # Pin down the first row of this table
        "<tr>",
        "<td align=\"left\">cee-rhel6</td>",
        "<td align=\"left\"><a .+>Trilinos-atdm-cee-rhel6-clang-opt-serial</a></td>",
        "<td align=\"left\"><a .+>Teko_&shy;ModALPreconditioner_&shy;MPI_&shy;1</a></td>",
        "<td align=\"left\"><a .+><font color=\"orange\">Not Run</font></a></td>",
        "<td align=\"left\">Required Files Missing</td>",
        "<td align=\"right\"><a .+><font color=\"red\">15</font></a></td>",
        "<td align=\"right\"><a .+><font color=\"red\">15</font></a></td>",
        "<td align=\"right\"><a .+><font color=\"green\">0</font></a></td>",
        "<td align=\"right\"><a .+>#3638</a></td>",
        "</tr>",

        ],
      #verbose=True,
      #debugPrint=True,
      )

    # Read the written file 'twoif.csv' and verify that it is correct
    twoifCsvLOD = \
      CDQAR.getTestsWtihIssueTrackersListFromCsvFile(testOutputDir+"/twoif.csv")
    self.assertEqual(len(twoifCsvLOD), 10)
    self.assertEqual(twoifCsvLOD[0],
      {
        'site': 'mutrino',
        'buildName': 'Trilinos-atdm-mutrino-intel-opt-openmp-KNL',
        'testname': 'Intrepid2_unit-test_Discretization_Basis_HCURL_TRI_In_FEM_Serial_Test_01_SLFadDouble_MPI_1',
        'issue_tracker_url': '',
        'issue_tracker': '',
        }
      )
    self.assertEqual(twoifCsvLOD[9],
      {
        'site': 'waterman',
        'buildName': 'Trilinos-atdm-waterman-cuda-9.2-release-debug',
        'testname': 'Teko_testdriver_tpetra_MPI_4',
        'issue_tracker_url': '',
        'issue_tracker': '',
        }
      )
    # NOTE: Don't need to bother checking other entires.  There are good unit
    # tests for the guts of what is being called.  Just want to macke sure the
    # right number of tests are being written and the first and last are
    # correct.


  # Test with some duplicate tests from CDash query (this happens in real life
  # sometimes!)
  #
  # Here we add a duplicate test to the file fullCDashNonpassingTests.json.
  #
  def test_twoif_12_twif_9_with_duplicate_nonpassing_tests(self):

    testCaseName = "twoif_12_twif_9_with_duplicate_nonpassing_tests"

    # Copy the raw files to get started
    testOutputDir = cdash_analyze_and_report_setup_test_dir(testCaseName)

    # Get list of nonpassing tests from JSON file
    testsLOD = getNonpassTestsDictListFromCDashJsonFile(testOutputDir)
    # Duplicate the test Belos_gcrodr_hb_MPI_4
    testDict = copy.deepcopy(testsLOD[1])
    testsLOD.insert(2, testDict)
    # Write updated test data back to file
    writeNonpassTestsDictListToCDashJsonFile(testsLOD, testOutputDir)

    # Run the script and make sure it outputs the right stuff
    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      [],
      1,
      "FAILED (twoif=12, twif=9): ProjectName Nightly Builds on 2018-10-28",
      [
        "Num builds = 6",
        "Num nonpassing tests direct from CDash query = 22",
        "Num nonpassing tests after removing duplicate tests = 21",
        "Num nonpassing tests without issue trackers = 12",
        "Num nonpassing tests with issue trackers = 9",
        "Num nonpassing tests without issue trackers Failed = 12",
        "Num nonpassing tests with issue trackers Failed = 9",
        "Builds Missing: bm=0",
        "Builds with Configure Failures: cf=0",
        "Builds with Build Failures: bf=0",
        "Tests without issue trackers Failed: twoif=12",
        "Tests with issue trackers Failed: twif=9",
        ],
      [

        # Second paragraph with listing of different types of tables below
        "<p>",
        "<font color=\"red\">Tests without issue trackers Failed: twoif=12</font><br>",
        "Tests with issue trackers Failed: twif=9<br>",
        "</p>",

        ],
      #verbose=True,
      #debugPrint=True,
      )


  # Test with some duplicate tests from CDash query that have the same buildid
  # but different testids (this happens in real life sometimes!)
  #
  # Here we add a duplicate test to the file fullCDashNonpassingTests.json
  # with the same buidlid but a different test id.  See:
  #
  #   https://gitlab.kitware.com/snl/project-1/issues/77
  #
  def test_twoif_12_twif_9_with_duplicate_nonpasing_testids(self):

    testCaseName = "twoif_12_twif_9_with_duplicate_nonpasing_testids"

    # Copy the raw files to get started
    testOutputDir = cdash_analyze_and_report_setup_test_dir(testCaseName)

    # Get list of nonpassing tests from JSON file
    testsLOD = getNonpassTestsDictListFromCDashJsonFile(testOutputDir)
    # Duplicate the test Belos_gcrodr_hb_MPI_4 bug give different testid
    testDict = copy.deepcopy(testsLOD[1])
    testDict['testDetailsLink'] = 'testDetails.php?test=57860536&build=4107241'
    testsLOD.insert(2, testDict)
    # Write updated test data back to file
    writeNonpassTestsDictListToCDashJsonFile(testsLOD, testOutputDir)

    # Run the script and make sure it outputs the right stuff
    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      [],
      1,
      "FAILED (twoif=12, twif=9): ProjectName Nightly Builds on 2018-10-28",
      [
        "Num builds = 6",
        "Num nonpassing tests direct from CDash query = 22",
        "Num nonpassing tests after removing duplicate tests = 21",
        "Num nonpassing tests without issue trackers = 12",
        "Num nonpassing tests with issue trackers = 9",
        "Num nonpassing tests without issue trackers Failed = 12",
        "Num nonpassing tests with issue trackers Failed = 9",
        "Builds Missing: bm=0",
        "Builds with Configure Failures: cf=0",
        "Builds with Build Failures: bf=0",
        "Tests without issue trackers Failed: twoif=12",
        "Tests with issue trackers Failed: twif=9",
        ],
      [

        # Second paragraph with listing of different types of tables below
        "<p>",
        "<font color=\"red\">Tests without issue trackers Failed: twoif=12</font><br>",
        "Tests with issue trackers Failed: twif=9<br>",
        "</p>",

        ],
      #verbose=True,
      #debugPrint=True,
      )


  # Add some missing builds, some builds with configure failuires, and builds
  # with build failures
  #
  # Here we just a couple of new builds to the file expectedBuilds.csv that
  # will become missing expected builds and we modfiy the dicts for a few
  # builds to change them from passing to failing.
  #
  def test_bm_2_c_1_b_2_twoif_12_twif_9(self):

    testCaseName = "bm_2_c_1_b_2_twoif_12_twif_9"
    buildSetName = "Project Specialized Builds"

    # Copy the raw files from CDash to get started
    testOutputDir = cdash_analyze_and_report_setup_test_dir(testCaseName,
      buildSetName)

    # Add some expected builds that don't exist
    expectedBuildsFilePath = testOutputDir+"/expectedBuilds.csv"
    with open(expectedBuildsFilePath, 'r') as expectedBuildsFile:
      expectedBuildsStrList = expectedBuildsFile.readlines()
    expectedBuildsStrList.extend(
      [
        "Specialized, missing_site, Trilinos-atdm-waterman-gnu-release-debug-openmp\n",
        "Specialized, waterman, Trilinos-atdm-waterman-missing-build\n",
        ]
      )
    with open(expectedBuildsFilePath, 'w') as expectedBuildsFile:
      expectedBuildsFile.write("".join(expectedBuildsStrList))

    # Add some configure and build failures
    fullCDashIndexBuildsJsonFilePath = \
      testOutputDir+"/"+CDQAR.getFileNameStrFromText(buildSetName)+\
      "_fullCDashIndexBuilds.json"
    with open(fullCDashIndexBuildsJsonFilePath, 'r') as fullCDashIndexBuildsJsonFile:
      fullCDashIndexBuildsJson = eval(fullCDashIndexBuildsJsonFile.read())
    specializedGroup = fullCDashIndexBuildsJson['buildgroups'][0]
    specializedGroup['builds'][1]['configure']['error'] = 1
    specializedGroup['builds'][3]['compilation']['error'] = 2
    specializedGroup['builds'][5]['compilation']['error'] = 1
    # ToDo: Replace above [i] access with dict lookups with
    # SearchableListOfDicts
    CDQAR.pprintPythonDataToFile(fullCDashIndexBuildsJson, fullCDashIndexBuildsJsonFilePath)

    # Run cdash_analyze_and_report.py and make sure that it prints
    # the right stuff
    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      [
        "--build-set-name='"+buildSetName+"'",  # Test changing this
        "--limit-table-rows=15",  # Check that this is read correctly
        ],
      1,
      "FAILED (bm=2, cf=1, bf=2, twoif=12, twif=9): Project Specialized Builds on 2018-10-28",
      [
        "Num expected builds = 8",
        "Num tests with issue trackers = 9",
        "Num builds = 6",
        "Num nonpassing tests direct from CDash query = 21",
        "Num nonpassing tests after removing duplicate tests = 21",
        "Builds Missing: bm=2",
        "Builds with Configure Failures: cf=1",
        "Builds with Build Failures: bf=2",
        "Tests without issue trackers Failed: twoif=12",
        "Tests with issue trackers Failed: twif=9",
        ],
      [
        "<h2>Build and Test results for Project Specialized Builds on 2018-10-28</h2>",

        # Links to build and non-passing tests
        "<a href=\"https://something[.]com/cdash/index[.]php[?]project=ProjectName&date=2018-10-28&builds_filters\">Builds on CDash</a> [(]num/expected=6/8[)]<br>",
        "<a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&date=2018-10-28&nonpasssing_tests_filters\">Non-passing Tests on CDash</a> [(]num=21[)]<br>",

        # Top listing of types of data/tables to be displayed below 
        "<font color=\"red\">Builds Missing: bm=2</font><br>",
        "<font color=\"red\">Builds with Configure Failures: cf=1</font><br>",
        "<font color=\"red\">Builds with Build Failures: bf=2</font><br>",
        "<font color=\"red\">Tests without issue trackers Failed: twoif=12</font><br>",
        "Tests with issue trackers Failed: twif=9<br>",
        
        # 'bm' table (Really pin down this table)
        "<h3>Builds Missing: bm=2</h3>",
        "<table.*>",  # NOTE: Other unit test code checks the default style!
        "<tr>",
        "<th>Group</th>",
        "<th>Site</th>",
        "<th>Build Name</th>",
        "<th>Missing Status</th>",
        "</tr>",
        "<tr>",
        "<td align=\"left\">Specialized</td>",
        "<td align=\"left\">missing_&shy;site</td>",
        "<td align=\"left\">Trilinos-atdm-waterman-gnu-release-debug-openmp</td>",
        "<td align=\"left\">Build not found on CDash</td>",
        "</tr>",
        "<tr>",
        "<td align=\"left\">Specialized</td>",
        "<td align=\"left\">waterman</td>",
        "<td align=\"left\">Trilinos-atdm-waterman-missing-build</td>",
        "<td align=\"left\">Build not found on CDash</td>",
        "</tr>",
        "</table>",

        # 'c' table (Really pin this down)
        "<h3>Builds with Configure Failures [(]limited to 15[)]: cf=1</h3>",
        "<table.*>",
        "<tr>",
        "<th>Group</th>",
        "<th>Site</th>",
        "<th>Build Name</th>",
        "</tr>",
        "<tr>",
        "<td align=\"left\">Specialized</td>",
        "<td align=\"left\">cee-rhel6</td>",
        "<td align=\"left\">Trilinos-atdm-cee-rhel6-clang-opt-serial</td>",
        "</tr>",
        "</table>",
        # NOTE: Above checks that --limit-table-rows=15 is getting used
        # correctly!

        # 'b' table (Really pin this down)
        "<h3>Builds with Build Failures [(]limited to 15[)]: bf=2</h3>",
        "<table.*>",
        "<tr>",
        "<th>Group</th>",
        "<th>Site</th>",
        "<th>Build Name</th>",
        "</tr>",
        "<tr>",
        "<td align=\"left\">Specialized</td>",
        "<td align=\"left\">cee-rhel6</td>",
        "<td align=\"left\">Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial</td>",
        "</tr>",
        "<tr>",
        "<td align=\"left\">Specialized</td>",
        "<td align=\"left\">cee-rhel6</td>",
        "<td align=\"left\">Trilinos-atdm-cee-rhel6-intel-opt-serial</td>",
        "</tr>",
        "</table>",

        # 'twoif' table
        "<h3><font color=\"red\">Tests without issue trackers Failed [(]limited to 15[)]: twoif=12</font></h3>",

        # 'twif' table
        "<h3>Tests with issue trackers Failed: twif=9</h3>",
       ],
      #verbose=True,
      )
  # NOTE: That above test really pin down the contents of the 'bm', 'c', and
  # 'b' tables.  Other tests will not do that to avoid duplication in testing.


  # Test the all passing case
  #
  # To run this test case, we just need to empty out the set of tests in the
  # file fullCDashNonpassingTests.json.
  #
  def test_passed_clean(self):

    testCaseName = "passed_clean"
    buildSetName = "Project Specialized Builds"

    # Copy the raw files from CDash to get started
    testOutputDir = cdash_analyze_and_report_setup_test_dir(testCaseName,
      buildSetName)

    # Remove all of the failing tests
    testListFilePath = \
      testOutputDir+"/Project_Specialized_Builds_fullCDashNonpassingTests.json"
    CDQAR.pprintPythonDataToFile( {'builds':[]}, testListFilePath )

    # Remove all of the tests with issue trackers (no open issues!)
    testsWithIssueTrackersStr = \
      "site, buildName, testname, issue_tracker_url, issue_tracker\n"
    testsWithIssueTrackersFilePath = testOutputDir+"/testsWithIssueTrackers.csv"
    with open(testsWithIssueTrackersFilePath, 'w') as testsWithIssueTrackersFile:
      testsWithIssueTrackersFile.write(testsWithIssueTrackersStr)

    # Run cdash_analyze_and_report.py and make sure that it prints the
    # right stuff
    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      [
        "--build-set-name='"+buildSetName+"'",  # Test changing this
        ],
      0,
      "PASSED: Project Specialized Builds on 2018-10-28",
      [
        "Num expected builds = 6",
        "Num tests with issue trackers = 0",
        "Num builds = 6",
        "Num nonpassing tests direct from CDash query = 0",
        "Num nonpassing tests after removing duplicate tests = 0",
        "Num nonpassing tests without issue trackers = 0",
        "Num nonpassing tests with issue trackers = 0",
        "Num nonpassing tests without issue trackers Failed = 0",
        "Num nonpassing tests without issue trackers Not Run = 0",
        "Num nonpassing tests with issue trackers Failed = 0",
        "Num nonpassing tests with issue trackers Not Run = 0",
        "Num tests with issue trackers gross passing or missing = 0",
        "Builds Missing: bm=0",
        "Builds with Configure Failures: cf=0",
        "Builds with Build Failures: bf=0",
        "Tests without issue trackers Failed: twoif=0",
        "Tests with issue trackers Failed: twif=0",
        ],
      [
        "<h2>Build and Test results for Project Specialized Builds on 2018-10-28</h2>",

        # Links to build and non-passing tests
        "<p>",
        "<a href=\"https://something[.]com/cdash/index[.]php[?]project=ProjectName&date=2018-10-28&builds_filters\">Builds on CDash</a> [(]num/expected=6/6[)]<br>",
        "<a href=\"https://something[.]com/cdash/queryTests[.]php[?]project=ProjectName&date=2018-10-28&nonpasssing_tests_filters\">Non-passing Tests on CDash</a> [(]num=0[)]<br>",
        "</p>",
       ],
      #verbose=True,
      )


  # Test the error behavior when one of the tests with issue trackers does not
  # match the expected builds
  #
  # To perform this test, we need to add an extra test to the file
  # testsWithIssueTrackers.csv in order to trigger this failure.
  #
  def test_tests_with_issue_trackers_no_match_expected_builds(self):

    testCaseName = "tests_with_issue_trackers_no_match_expected_builds"

    # Copy the raw files to get started
    testOutputDir = cdash_analyze_and_report_setup_test_dir(testCaseName)

    # Add an test with an issue tracker that does not match an expected builds
    testsWithIssueTrackersFilePath = testOutputDir+"/testsWithIssueTrackers.csv"
    with open(testsWithIssueTrackersFilePath, 'r') as testsWithIssueTrackersFile:
      testsWithIssueTrackersStr = testsWithIssueTrackersFile.read()
    testsWithIssueTrackersStr += \
      "othersite, otherbuild, Teko_ModALPreconditioner_MPI_1, githuburl, #3638\n"
    with open(testsWithIssueTrackersFilePath, 'w') as testsWithIssueTrackersFile:
      testsWithIssueTrackersFile.write(testsWithIssueTrackersStr)

    # Run the script and make sure it outputs the right stuff
    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      [],
      1,
      "FAILED (SCRIPT CRASHED): ProjectName Nightly Builds on 2018-10-28",
      [
        "Num expected builds = 6",
        "Num tests with issue trackers = 10",
        ".+File \".+/cdash_analyze_and_report.py\", line.+",
        ".+Error: The following tests with issue trackers did not match 'site' and 'buildName' in one of the expected builds:",
        ".+{'site'='othersite', 'buildName'=otherbuild', 'testname'=Teko_ModALPreconditioner_MPI_1'}",
        ],
      [
        # Top title
        "<h2>Build and Test results for ProjectName Nightly Builds on 2018-10-28</h2>",

        # The error message
        "<pre><code>",
        "Traceback [(]most recent call last[)]:",
        "  File \".+/cdash_analyze_and_report.py\".+",
        "    raise Exception[(]errMsg[)]",
        "Exception: Error: The following tests with issue trackers did not match 'site' and 'buildName' in one of the expected builds:",
        "  {'site'='othersite', 'buildName'=otherbuild', 'testname'=Teko_ModALPreconditioner_MPI_1'}",
        "</code></pre>",
        ],
      )


  # Test to check the behavior for tests with issue trackers that are passing
  # and missing
  #
  # We want to test two use cases for missing tests.  First, we want to
  # display tests with issue trackers that are missing in the current testing
  # day where the matching build exists and have test results.  Second, we
  # want some tests with issue trackers that are missing in the current
  # testing day for expected builds that are missing entirely or don't have
  # test results.  For those missing tests that match missing expected builds,
  # we we don't want to bother displaying them or even listing them as missing
  # at all (other than in the STDOUT).  Finally, we want to to check tests
  # with issue trackers that are passing in the current testing day.  In order
  # implement this test, we don't want to use any extra data than what already
  # exists in the raw_cdash_data_twoif_12_twif_9/ test directory.  To
  # accomplish this, we will remove some of the tests with issue trackers from
  # the file fullCDashNonpassingTests.json and the ones that we remove will be
  # for used to represent tests with issue trackers passing and missing tests.
  # That way, we have the test history for these tests.  We will just need to
  # manipulate that test history by deleting some days from the test history
  # files for the missing tests and we will need to change the history for the
  # passing tests to be passed for the current testing day (and a few days
  # before that?).  Also, it is easiest to just manipulate for the existing
  # set of tests with issue trackers so that we don't have to modify the file
  # testsWithIssueTrackers.csv.
  def test_twip_twim(self):

    testCaseName = "twip_twim"

    # Copy the raw files to get started
    testOutputDir = cdash_analyze_and_report_setup_test_dir(testCaseName)

    # Get full list of nonpassing tests from Json file
    nonpassingTestsLOD = getNonpassTestsDictListFromCDashJsonFile(testOutputDir)
    nonpassingTestsSLOD = CDQAR.createSearchableListOfTests(nonpassingTestsLOD)

    # Mark which tests with issue trackers to remove from the list of
    # non-passing tests.  (These will be used for passing tests and msising
    # tests with history)

    nonpassingTestsToRemoveIndexes = []

    # Mark test that will become passing test
    (testDict, testIdx) = nonpassingTestsSLOD.lookupDictGivenKeyValuesList([
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-clang-opt-serial',
      'MueLu_UnitTestsBlockedEpetra_MPI_1',
      ], True)
    nonpassingTestsToRemoveIndexes.append(testIdx)

    # Mark test that will become passing test
    (testDict, testIdx) = nonpassingTestsSLOD.lookupDictGivenKeyValuesList([
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-intel-opt-serial',
      'PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2',
      ], True)
    nonpassingTestsToRemoveIndexes.append(testIdx)

    # Mark test that will become missing test
    (testDict, testIdx) = nonpassingTestsSLOD.lookupDictGivenKeyValuesList([
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial',
      'PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2',
      ], True)
    nonpassingTestsToRemoveIndexes.append(testIdx)

    # Mark test that will become missing test
    (testDict, testIdx) = nonpassingTestsSLOD.lookupDictGivenKeyValuesList([
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial',
      'PanzerAdaptersIOSS_tIOSSConnManager3_MPI_3',
      ], True)
    nonpassingTestsToRemoveIndexes.append(testIdx)

    # Remove marked tests from list of nonpassing and missing tests with
    # history
    nonpassingTestsSLOD = None  # Must delete since changing underlying list
    CDQAR.removeElementsFromListGivenIndexes( nonpassingTestsLOD,
      nonpassingTestsToRemoveIndexes)

    # Write the reduced list of nonpassing test data back to file
    writeNonpassTestsDictListToCDashJsonFile(nonpassingTestsLOD, testOutputDir)

    # Add some dummy builds to the list of expected builds so that some new
    # added dummy matching tests will be missing but not listed in the table
    # fo missing tests.
    expectedBuildsFilePath = testOutputDir+"/expectedBuilds.csv"
    with open(expectedBuildsFilePath, 'r') as expectedBuildsFile:
      expectedBuildsStrList = expectedBuildsFile.readlines()
    expectedBuildsStrList.append(
      "Specialized, waterman, Trilinos-atdm-waterman-missing-build\n" )
    with open(expectedBuildsFilePath, 'w') as expectedBuildsFile:
      expectedBuildsFile.write("".join(expectedBuildsStrList))

    # Add some dummy tests with issue trackers to match the new dummy expected
    # builds so that we can test that the tool does not try to get test
    # history for a missing test that matches a missing expected build.
    testsWithIssueTrackersFilePath = testOutputDir+"/testsWithIssueTrackers.csv"
    with open(testsWithIssueTrackersFilePath, 'r') as testsWithIssueTrackersFile:
      testsWithIssueTrackersStrList = testsWithIssueTrackersFile.readlines()
    testsWithIssueTrackersStrList.extend( [
      "waterman, Trilinos-atdm-waterman-missing-build, missing_test_1, url1, issue1\n",
      "waterman, Trilinos-atdm-waterman-missing-build, missing_test_2, url2, issue2\n",
      ] )
    with open(testsWithIssueTrackersFilePath, 'w') as testsWithIssueTrackersFile:
      testsWithIssueTrackersFile.write("".join(testsWithIssueTrackersStrList))

    # Change the history for some tests so that they show up correctly as
    # Passing and Missing

    daysOfHistory = 30

    # Make a test passed
    testHistoryFileName = CDQAR.getTestHistoryCacheFileName( "2018-10-28",
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-clang-opt-serial',
      'MueLu_UnitTestsBlockedEpetra_MPI_1',
      daysOfHistory)
    testHistoryLOD = getTestHistoryDictListFromCDashJsonFile(
      testOutputDir, testHistoryFileName)
    testHistoryLOD.sort(reverse=True, key=CDQAR.DictSortFunctor(['buildstarttime']))
    testHistoryLOD[0]['status'] = u'Passed'
    testHistoryLOD[0]['details'] = u'Completed (Passed)'
    writeTestHistoryDictListFromCDashJsonFile(testHistoryLOD, testOutputDir,
      testHistoryFileName) 

    # Make a test passed
    testHistoryFileName = CDQAR.getTestHistoryCacheFileName( "2018-10-28",
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-intel-opt-serial',
      'PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2',
      daysOfHistory)
    testHistoryLOD = getTestHistoryDictListFromCDashJsonFile(
      testOutputDir, testHistoryFileName)
    testHistoryLOD.sort(reverse=True, key=CDQAR.DictSortFunctor(['buildstarttime']))
    testHistoryLOD[0]['status'] = u'Passed'
    testHistoryLOD[0]['details'] = u'Completed (Passed)'
    writeTestHistoryDictListFromCDashJsonFile(testHistoryLOD, testOutputDir,
      testHistoryFileName) 

    # Make a test missing (here, we need to move the date back)
    testHistoryFileName = CDQAR.getTestHistoryCacheFileName( "2018-10-28",
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial',
      'PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2',
      daysOfHistory)
    testHistoryLOD = getTestHistoryDictListFromCDashJsonFile(
      testOutputDir, testHistoryFileName)
    testHistoryLOD.sort(reverse=True, key=CDQAR.DictSortFunctor(['buildstarttime']))
    # There is just one day in history so we need to duplicate it
    testHistoryLOD.append(copy.deepcopy(testHistoryLOD[0]))
    # Make first non-missing day failed
    testHistoryLOD[0]['buildstarttime'] = "2018-10-26T12:00:00 UTC"
    testHistoryLOD[0]['status'] = u'Failed'
    testHistoryLOD[0]['details'] = u'Completed (Failed)'
    # Make second non-missing day passed
    testHistoryLOD[1]['buildstarttime'] = "2018-10-25T12:00:00 UTC"
    testHistoryLOD[1]['status'] = u'Passed'
    testHistoryLOD[1]['details'] = u'Completed (Passed)'
    writeTestHistoryDictListFromCDashJsonFile(testHistoryLOD, testOutputDir,
      testHistoryFileName) 

    # Make a test missing (no days of test history)
    testHistoryFileName = CDQAR.getTestHistoryCacheFileName( "2018-10-28",
      'cee-rhel6',
      'Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial',
      'PanzerAdaptersIOSS_tIOSSConnManager3_MPI_3',
      daysOfHistory)
    testHistoryLOD = []
    writeTestHistoryDictListFromCDashJsonFile(testHistoryLOD, testOutputDir,
      testHistoryFileName) 

    # ToDo: Remove history for missing tests to test different numbers of
    # missing days.  (This will need to be done once we tablulate "Consecutive
    # Pass Days" and "Consecutive Missing Days".)

    # Run the script and make sure it outputs the right stuff
    cdash_analyze_and_report_run_case(
      self,
      testCaseName,
      ["--limit-test-history-days=30"], # Test that you can set this as int
      1,
      "FAILED (bm=1, twoif=12, twip=2, twim=2, twif=5):"+\
        " ProjectName Nightly Builds on 2018-10-28",
      [
        "Num expected builds = 7",
        "Num tests with issue trackers = 11",
        "Num builds = 6",
        "Num nonpassing tests direct from CDash query = 17",
        "Num nonpassing tests after removing duplicate tests = 17",
        "Num nonpassing tests without issue trackers = 12",
        "Num nonpassing tests with issue trackers = 5",
        "Num nonpassing tests without issue trackers Failed = 12",
        "Num nonpassing tests without issue trackers Not Run = 0",
        "Num nonpassing tests with issue trackers Failed = 5",
        "Num nonpassing tests with issue trackers Not Run = 0",
        "Num tests with issue trackers gross passing or missing = 6",

        "Builds Missing: bm=1",
        "Builds with Configure Failures: cf=0",
        "Builds with Build Failures: bf=0",

        "Num tests with issue trackers passing or missing matching posted builds = 4",

        "Tests with issue trackers missing that match missing expected builds: num=2",
        "  {'buildName': 'Trilinos-atdm-waterman-missing-build', 'issue_tracker': 'issue1', 'issue_tracker_url': 'url1', 'site': 'waterman', 'testname': 'missing_test_1'}",
        "  {'buildName': 'Trilinos-atdm-waterman-missing-build', 'issue_tracker': 'issue2', 'issue_tracker_url': 'url2', 'site': 'waterman', 'testname': 'missing_test_2'}",
        "NOTE: The above tests will NOT be listed in the set 'twim'!",

        "Getting test history for tests with issue trackers passing or missing: num=4",
        "Getting 30 days of history for MueLu_UnitTestsBlockedEpetra_MPI_1 in the build Trilinos-atdm-cee-rhel6-clang-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2 in the build Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2 in the build Trilinos-atdm-cee-rhel6-intel-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager3_MPI_3 in the build Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial on cee-rhel6 from cache file",

        "Num tests with issue trackers Passed = 2",
        "Num tests with issue trackers Missing = 2",

        "Tests without issue trackers Failed: twoif=12",

        "Tests with issue trackers Passed: twip=2",

        "Tests with issue trackers Missing: twim=2",

        "Tests with issue trackers Failed: twif=5",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager2_MPI_2 in the build Trilinos-atdm-cee-rhel6-clang-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager3_MPI_3 in the build Trilinos-atdm-cee-rhel6-clang-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for PanzerAdaptersIOSS_tIOSSConnManager3_MPI_3 in the build Trilinos-atdm-cee-rhel6-intel-opt-serial on cee-rhel6 from cache file",
        "Getting 30 days of history for Stratimikos_test_single_belos_thyra_solver_driver_nos1_nrhs8_MPI_1 in the build Trilinos-atdm-mutrino-intel-opt-openmp-KNL on mutrino from cache file",
        "Getting 30 days of history for Teko_ModALPreconditioner_MPI_1 in the build Trilinos-atdm-cee-rhel6-clang-opt-serial on cee-rhel6 from cache file",

        "Tests with issue trackers Not Run: twinr=0",

        ],
      [

        "<h3><font color=\"red\">Tests without issue trackers Failed [(]limited to 10[)]: twoif=12</font></h3>",

        "<h3><font color=\"green\">Tests with issue trackers Passed: twip=2</font></h3>",
        # Pin down table headers
        "<th>Site</th>",
        "<th>Build Name</th>",
        "<th>Test Name</th>",
        "<th>Status</th>",
        "<th>Details</th>",
        "<th>Consec&shy;utive Pass Days</th>",
        "<th>Non-pass Last 30 Days</th>",
        "<th>Pass Last 30 Days</th>",
        "<th>Issue Tracker</th>",
        # Pin down first row
        "<td align=\"left\">cee-rhel6</td>",
        "<td align=\"left\"><a href=\".+\">Trilinos-atdm-cee-rhel6-clang-opt-serial</a></td>",
        "<td align=\"left\"><a href=\".+\">MueLu_&shy;UnitTestsBlockedEpetra_&shy;MPI_&shy;1</a></td>",
        "<td align=\"left\"><a href=\".+\"><font color=\"green\">Passed</font></a></td>",
        "<td align=\"left\">Completed [(]Passed[)]</td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"green\">1</font></a></td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"red\">14</font></a></td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"green\">1</font></a></td>",
        "<td align=\"right\"><a href=\".+\">#3640</a></td>",

        "<h3>Tests with issue trackers Missing: twim=2</h3>",
        # Pin down table headers
        "<th>Site</th>",
        "<th>Build Name</th>",
        "<th>Test Name</th>",
        "<th>Status</th>",
        "<th>Details</th>",
        "<th>Consec&shy;utive Missing Days</th>",
        "<th>Non-pass Last 30 Days</th>",
        "<th>Pass Last 30 Days</th>",
        "<th>Issue Tracker</th>",
        # Pin down first row
        "<td align=\"left\">cee-rhel6</td>",
        "<td align=\"left\"><a href=\".+\">Trilinos-atdm-cee-rhel6-gnu-4.9.3-opt-serial</a></td>",
        "<td align=\"left\">PanzerAdaptersIOSS_&shy;tIOSSConnManager2_&shy;MPI_&shy;2</td>",
        "<td align=\"left\"><font color=\"gray\">Missing</font></td>",
        "<td align=\"left\">Missing</td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"gray\">2</font></a></td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"red\">1</font></a></td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"green\">1</font></a></td>",
        "<td align=\"right\"><a href=\".+\">#3632</a></td>",

        "<h3>Tests with issue trackers Failed: twif=5</h3>",
        "<td align=\"left\">cee-rhel6</td>",
        "<td align=\"left\"><a href=\".+\">Trilinos-atdm-cee-rhel6-clang-opt-serial</a></td>",
        "<td align=\"left\"><a href=\".+\">PanzerAdaptersIOSS_&shy;tIOSSConnManager2_&shy;MPI_&shy;2</a></td>",
        "<td align=\"left\"><a href=\".+\"><font color=\"red\">Failed</font></a></td>",
        "<td align=\"left\">Completed [(]Failed[)]</td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"red\">15</font></a></td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"red\">15</font></a></td>",
        "<td align=\"right\"><a href=\".+\"><font color=\"green\">0</font></a></td>",
        "<td align=\"right\"><a href=\".+\">#3632</a></td>",

        ],
      #verbose=True,
      #debugPrint=True,
      )

#
# Run the unit tests!
#

if __name__ == '__main__':

  # Clean out and re-recate the base test directory
  if os.path.exists(g_baseTestDir): shutil.rmtree(g_baseTestDir)
  os.mkdir(g_baseTestDir)

  unittest.main()
