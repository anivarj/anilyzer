# @File(label = "Input directory", style = "directory") experimentFolder

"""
##AUTHOR: Ani Michaud (Varjabedian)

## DESCRIPTION: This script is for automating opening MAX projection files after running the anilyzer. It will make a list of all the scans and then find the MAXs for each channel and open them. IF YOU WANT TO OPEN A DIFFERENT DIRECTORY, CHANGE RUN_IT() TO LOOK IN A DIFFERENT FOLDER (LINE 95)

The organization of this code is as follows:

1. Script parameters (at the top, preceded by a "#@") that gather information for the dialogue box
2. Import statements for all the modules needed
3. All of the main functions for processing data
4. The run_it() function, which sets up the error logging, and then calls all of the other processing functions.

## NOTE: This script will not work with Zac's branch, as the file heirarchy is different (all output is saved to a single output folder)

"""

import os, sys, shutil, glob, fnmatch
from java.io import File
from ij.gui import GenericDialog
from ij import IJ

experimentFolder = str(experimentFolder) # Converts the input directory you chose to a path string that can be used later on

# Microscope_check assesses the file structure of the experimentFolder and assigns a "microscope type" which gets passed to other functions. This helps with determining where certain files and directories should be located.
def microscope_check(experimentFolder):
	#If it finds .oif files inside the main folder, it calls the microscope "Olympus"
	if any(File.endswith(".oif") for File in os.listdir(experimentFolder)):
		print(".oif files present, running Olympus pipeline")
		microscopeType = "Olympus"
		return microscopeType #returns microscopeType to run_it()
	else:
		#If there are no .oif files in the main folder, it calls the microscope "Bruker"
		print("No .oif files present, running Bruker pipeline")
		microscopeType = "Bruker"
		return microscopeType #returns microscopeType to run_it()

# list_scans gets a list of all scan folders inside the experimentFolder you selected, and saves them as a list called scanList.
def list_scans(experimentFolder, microscopeType):
	scanList = [] # Makes an empty list

	# This section screens out text files and other things that might be in the main experimentFolder, and only makes a list of the actual scan directories
	# For Bruker microscopes, the scan directories are plain, so os.isdir is used to look for them
	if microscopeType == "Bruker":
		for File in sorted(os.listdir(experimentFolder)):
			dirpath = os.path.join(experimentFolder, File) # Makes a complete path to the file
			if os.path.isdir(dirpath): # If the dirpath is a directory, print it and add it to scanList. If it's a file, do not add it.
				print "dirpath is " + dirpath
				scanList.append(dirpath)
		return scanList # Returns scanList to run_it()

	# If the microscope is "Olympus" type, the directories end in .oif.files, so .endswith needs to be used to find them
	if microscopeType == "Olympus":
		oifList = [] # This doesn't look like it was used, so I should delete it in the future once I have verified this.
		for File in sorted(os.listdir(experimentFolder)):
			if File.endswith(".oif.files"): # If the item ends with .oif.files, make the complete path and append it to scanList
				dirpath = os.path.join(experimentFolder, File)
				#print "dirpath is " + dirpath
				scanList.append(dirpath)
		return scanList # Returns scanList to run_it()

# make_directories takes an individual scan (passed from the run_it() function) and checks to see if a "processed" directory already exist inside the scan folder. If so, it overwrites it.
def define_directories(scan):
	processed = os.path.join(scan, "processed") # makes full path to processed folder, inside the scan folder
	raw = os.path.join(processed, "raw") # makes full path to raw folder, inside processed
	diff = os.path.join(processed, "diff") # makes full path to diff folder, inside processed
	MAX = os.path.join(processed, "MAX") # makes full path to MAX folder, inside processed
	filteredMAX = os.path.join(MAX, "filteredMAX") # makes full path to filteredMAX, inside MAX
	rawMAX = os.path.join(MAX, "rawMAX") # makes full path to rawMAX, inside MAX
	filtered = os.path.join(processed, "filtered") # makes full path to filtered, inside processed
	directories = [processed, raw, diff, filteredMAX, rawMAX, filtered] # a list of all the full paths you just made

	return directories # defines directory structure returns directories list to run_it()

def run_it():
	#Runs microscope_check and defines the scanList accordingly
	microscopeType = microscope_check(experimentFolder)

	# Call list_scans and pass it the microscopeType variable. Gets the scanList
	if microscopeType == "Olympus":
		scanList = list_scans(experimentFolder, microscopeType)
		print "The returned scanList is", len(scanList), "item(s) long"

	elif microscopeType == "Bruker":
		scanList = list_scans(experimentFolder, microscopeType)
		print "The returned scanList is", len(scanList), "item(s) long"

	# For each scan in the scanList, call the following functions
	for scan in scanList:
		directories = define_directories(scan) # get paths to the directories
		basename = os.path.basename(scan) # get the scan name (basename)
		print "Opening " + basename
		files = os.listdir(directories[3]) # makes a list of all the files in filteredMAX directory
		for f in files: # finds the MAX projections and only opens them (skips merged)
			if fnmatch.fnmatch(f, "MAX_C*"): #finds MAX projections. change if you only want 1 channel
				IJ.open(os.path.join(directories[3], f))


run_it()
print "Done with script."
