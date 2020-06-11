# @File(label = "Input directory", style = "directory") experimentFolder
# @Integer(label = "Slices to remove for difference movie", value = 4) differenceNumber
#@ String (visibility=MESSAGE, value="Please select your channel colors. If you have one channel, assign it to Channel 1.") msg
#@ String(label="Channel 1",choices={"Select", "Red", "Magenta", "Green", "Cyan", "Blue", "Grays"}, value = "Select", persist=false) ch1color
#@ String(label="Channel 2",choices={"Select","Red", "Magenta", "Green", "Cyan", "Blue", "Grays"}, value = "Select", persist=false) ch2color
#@ String(label="Channel 3",choices={"Select","Red", "Magenta", "Green", "Cyan", "Blue", "Grays"}, value = "Select", persist=false) ch3color

"""
##AUTHOR: Ani Michaud (Varjabedian)

## DESCRIPTION: This script is for automating common Fiji processing commands for imaging datasets. See README for the general overview.

The organization of this code is as follows:

1. Script parameters (at the top, preceded by a "#@") that gather information for the dialogue box
2. Import statements for all the modules needed
3. All of the main functions for processing data
4. The run_it() function, which sets up the error logging, and then calls all of the other processing functions. It should eventually just be in it's own file, but I like having everything where you can see it.

If you want to know the general flow of events, check the order of calls in the run_it() function. If you want to skip certain steps, comment them out in the run_it() function. Although, be aware that some functions pass arguments to each other, and commenting out certain functions can result in errors. It's best to read the particular function before you comment it out to make sure you avoid this.

For more information and up-to-date changes, visit the GitHub repository: https://github.com/anivarj/anilyzer

"""

# Importing modules and other shit
import os, sys, traceback, shutil, glob
from ij import IJ, WindowManager, ImagePlus
from ij.gui import GenericDialog
from ij.plugin import ImageCalculator
import datetime
import fnmatch

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
				print "dirpath is " + dirpath
				scanList.append(dirpath)
		return scanList # Returns scanList to run_it()


# make_directories takes an individual scan (passed from the run_it() function) and checks to see if a "processed" directory already exist inside the scan folder. If so, it overwrites it.
def make_directories(scan):
	print "Checking for output directories in ", scan
	processed = os.path.join(scan, "processed") # makes full path to processed folder, inside the scan folder
	raw = os.path.join(processed, "raw") # makes full path to raw folder, inside processed
	diff = os.path.join(processed, "diff") # makes full path to diff folder, inside processed
	MAX = os.path.join(processed, "MAX") # makes full path to MAX folder, inside processed
	filteredMAX = os.path.join(MAX, "filteredMAX") # makes full path to filteredMAX, inside MAX
	rawMAX = os.path.join(MAX, "rawMAX") # makes full path to rawMAX, inside MAX
	filtered = os.path.join(processed, "filtered") # makes full path to filtered, inside processed
	directories = [processed, raw, diff, filteredMAX, rawMAX, filtered] # a list of all the full paths you just made

	#If a processed folder exists, it will erase and remake fresh folders
	if os.path.exists(processed):
		print "The directory", processed, "already exists! Overwriting..."
		shutil.rmtree(processed)
		for d in directories:
			os.makedirs(d)
			print d, "created"
	else:
		for d in directories:
			os.makedirs(d)
			print d, "created"

	print "Finished creating directories!"
	return directories # returns directories list to run_it()


# Make_hyperstack uses Bio-formats importer to import a hyperstack from an initiator file
def make_hyperstack(basename, scan, microscopeType): # basename is defined in run_it() and is the name of the scan (not the full path)

	# Defines an "initator file" to give bioformats importer, and also modifies basename (which has an .oif.files extension) to make the scan name
	if microscopeType == "Olympus":
		initiatorFileName = os.path.splitext(basename) [0] # Removes .file extension from the .oif.file path to get the name of the .oif initiator file
		basename = os.path.splitext(initiatorFileName) [0] # Removes .oif extension from initiatorFile to get the name of the scan (for naming windows and stuff)
		print "basename is ", basename
		print ".oif file is ",  initiatorFileName # This is the file that will get passed to bioformats importer
		initiatorFilePath = os.path.join(experimentFolder, initiatorFileName) # Gets the full path to the initiatorFile
		print "Opening file ", initiatorFilePath

	elif microscopeType == "Bruker": # With Bruker microscopes, you can initiate from the .xml file, or from a single TIF. I have found that initiation from the .xml file slows down the import on windows computers, so I got rid of .xml initiation (commented out below)
		#xmlFile = basename + ".xml"
		#xmlFile = os.path.join(scan, xmlFile) # Makes path to the xml file
		print "basename is ", basename # The basename doesn't need to be modified here, because there is no .oif.files suffix to remove (Thanks Bruker!)
		initiatorFileName = basename + "_Cycle00001_Ch?_000001.ome.tif" # Defines the pattern to look for. The Ch? is because if you have one color, it's not always on CH1
		initiatorFilePath = os.path.join(scan, initiatorFileName) # Gets the full path to the initiator file
		print "initiatorFilePath ", initiatorFilePath
		initiatorFilePath = glob.glob(initiatorFilePath) # Looks for the first file in the folder. If there are more than one channel, it makes a list of them.
		initiatorFilePath = initiatorFilePath[0] # Takes the first item in the list. This is the file that will get passed to bioformats importer
		print "Opening file", initiatorFilePath

	IJ.run("Bio-Formats Importer", "open=[" + initiatorFilePath + "] color_mode=Grayscale concatenate_series open_all_series quiet rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT")
	print "File opened"

	# Get a list of the windows that are open
	try:
		image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	except TypeError:
		raise TypeError("No windows open! Bio-formats failed. Check metadata for completeness.")
		return

	#Checks to see if multiple windows are open. There should only be one hyperstack. If there are multiple, it will close windows with a single frame (because it sees them as partial slices).
	# If you have single z-stack data but somehow also have a partial slice, this might close everything (seems like a rare situation though).

	if len(image_titles) > 1:
		for i in image_titles:
			print i
			imp = WindowManager.getImage(i)
			if imp.getNFrames() == 1: # If it is a partial slice, will close it
				imp.close()
	try:
		image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	except TypeError:
		raise Exception("No windows open! Is this a single slice acquisition?")
		return

	imp = IJ.getImage()
	imp.setTitle(basename + "_raw.tif")
	return basename

# checks for single plane acquisition. Don't need since you ask up front
def single_plane_check():
	print "Checking for z-planes..."
	imp = IJ.getImage()
	if imp.getNSlices() > 1:
		print "The number of z-planes is ", imp.getNSlices()
		singleplane = False

	elif imp.getNSlices() == 1:
		print "The number of z-planes is ", imp.getNSlices()
		singleplane = True

	return singleplane

# Runs the channel splitter if it detects multiple channels.
def split_channels(directories, channels):
	imp = IJ.getImage()
	if channels >1:
		IJ.run("Split Channels")
	else:
		print "Only one channel, bypassing channel splitter..."
		imp = IJ.getImage()
		windowName = imp.getTitle()
		imp = imp.setTitle("C1-" + windowName) #just renames the window for continuity

	# Saving the hyperstacks
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	for i in image_titles:
		imp = WindowManager.getImage(i)
		windowName = imp.getTitle()
		IJ.saveAsTiff(imp, os.path.join(directories[1], windowName)) # Save in raw folder

# make_MAX checks for multi-z plane images and makes MAX projections if it finds them.
def make_MAX(directories, x, singleplane): # singleplane is Boolean True/False
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]

	for i in image_titles:
		imp = WindowManager.getImage(i)
		if singleplane == False: # If the data is not single z-plane, runs max projection
			IJ.run(imp, "Z Project...", "projection=[Max Intensity] all")
			imp = WindowManager.getImage("MAX_" + i)
			windowName = imp.getTitle()
			IJ.saveAsTiff(imp, os.path.join(directories[x], windowName)) #saves to appropriate MAX directory (rawMAX or filteredMAX). Passed from run_it()
			imp = WindowManager.getImage(i) # Gets the original hyperstack
			imp.changes = False # Answers "no" to the dialog asking if you want to save any changes
			imp.close() # Closes the hyperstack

		# If the data is single plane, it skipes projection and moves to LUT setting
		elif singleplane == True:
			windowName = imp.getTitle()
			print "Single plane data detected. Skipping Z-projection for ", windowName

# apply_LUT applies the LUT specified in the dialogue window and applies it to the appropriate channel
def applyLut (channels, ch1color, ch2color, ch3color): # channels var is passed from run_it()
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	print "Setting LUTs... "
	windowname = image_titles[0] # The first item in the list should be C1
	imp = WindowManager.getImage(windowname)
	IJ.run(imp, ch1color, "") # Applies ch1color (from dialogue box) to the image
	print "CH1 LUT set for ", image_titles[0]

	if channels ==2: # CH1 already set, so just need to worry about CH2
		windowname2 = image_titles[1]
		imp2 = WindowManager.getImage(windowname2)
		IJ.run(imp2, ch2color, "")
		print "CH2 LUT set for ", image_titles[1]

	elif channels == 3: # CH1 already set, so just need to worry about CH2 and CH3
		windowname2 = image_titles[1]
		imp2 = WindowManager.getImage(windowname2)
		IJ.run(imp2, ch2color, "")
		print "CH2 LUT set for ", image_titles[1]

		windowname3 = image_titles[2]
		imp3 = WindowManager.getImage(windowname3)
		IJ.run(imp3, ch3color, "")
		print "CH3 LUT set for ", image_titles[2]

	else:
		print "something went wrong with LUT assignment..."

	print "Done setting LUTs"

# merge_channels will merge the channels together after LUT assignment if there are more than 1.
#If there is only 1 channel, it skips the merge
def merge_channels(basename, channels, directories, x, suffix):
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	if channels >1:
		print "Found", channels, "channels...merging them together...."
		if channels == 2:
			IJ.run("Merge Channels...", "c1=[" + image_titles[0] + "] c2=[" + image_titles[1] + "] create")
		if channels == 3:
			IJ.run("Merge Channels...", "c1=[" + image_titles[0] + "] c2=[" + image_titles[1] + "] c3=[" + image_titles[2] + "] create")
		imp = IJ.getImage() # gets the resulting image
		imp.setTitle("Merged_" + basename + suffix)
		windowName = imp.getTitle()
		IJ.saveAsTiff(imp, os.path.join(directories[x], windowName)) # saves to output location x. Passed from run_it()
		IJ.run("Close All")
	else:
		print "Only 1 channel, skipping merge..."
		IJ.run("Close All")
	print "Closing all files..."

# median_filter runs a median filter with kernel = 1 on the raw hyperstacks
def median_filter(rawFiles, directories, x): # all arguments are passed from run_it()
	for f in rawFiles:
		if fnmatch.fnmatch(f, "C?*"): # pattern matching to only open the C1, C2 and C3 files (skips merge)
			IJ.open(os.path.join(directories[1], f))

	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	for i in image_titles:
		imp = WindowManager.getImage(i)
		IJ.run(imp, "Median...", "radius=1 stack")
		windowName = WindowManager.getImage(i).getTitle().replace("raw", "filtered") # save as "*_filtered.tif" extension
		imp.setTitle(windowName)
		IJ.saveAsTiff(imp, os.path.join(directories[x], windowName)) # saves to filtered directory. Passed the directory from run_it()


# For make_difference, it will remove slices to make a difference movie, based on the number you put in the beginning dialogue box.
# This function looks in either filteredMAX or filtered, depending on if the data is single plane. You can change what data you want to us in run_it by altering x
def make_difference(directories, x, differenceNumber, singleplane):
	for file in os.listdir(directories[x]): # looks in the folder and makes a list of the directories
		if singleplane == False: # if data is multi-z plane, looks for the MAX projections
			if fnmatch.fnmatch(file, "MAX*"):
				IJ.open(os.path.join(directories[x], file))
		elif singleplane == True: # if singleplane data, looks for C1, C2 and C3 hyperstacks (there are no MAX projections)
			if fnmatch.fnmatch(file, "C?*"):
				IJ.open(os.path.join(directories[x], file))

	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]

	for i in image_titles:
		imp = WindowManager.getImage(i)
		windowName = imp.getTitle()
		if imp.getNFrames() == 1: # if it is a single timepoint, will raise exception and quit
			imp.close()
			raise Exception("Single timepoint data. Cannot create difference movies.")
			return
		else:
			imp.setT(1) # sets the cursor at the first frame
			dup = imp.duplicate()
			dup.show() # shows the duplicate
			dup.setTitle(windowName + "_dup") # renames the duplicate


		differenceNumberString = str(differenceNumber) # turns the integer input into a string

		# the range is differenceNumber+1 because range goes up to but does not include the last value. So a range of (1,3) Would only check n = 1, 2
		for n in range(1, differenceNumber+1):
			if n >= 1:
				IJ.run(imp, "Delete Slice", "")

		dup = WindowManager.getImage(windowName + "_dup")
		IJ.run(dup,"Reverse", "") # reverse the array so that the slices in the back become the front

		for n in range(1, differenceNumber+1):
			if n >= 1:
				IJ.run(dup, "Delete Slice", "")

		IJ.run(dup, "Reverse", "") # reverse the array back to native orientation
		calc = ImageCalculator()
		impDiff = calc.calculate("Subtract create stack", imp, dup) # subtract the imp - dup
		impDiff = WindowManager.getImage("Result of "+ windowName) # selects the result
		windowName = impDiff.getTitle().replace("Result of ", "Diff" + differenceNumberString + "-")
		impDiff.setTitle(windowName) # renames it to include the differenceNumber

		IJ.saveAsTiff(impDiff, os.path.join(directories[2], windowName)) # saves in diff folder
		impDiff.changes = False # Answers "no" to the dialog asking if you want to save any changes
		imp.changes = False # Answers "no" to the dialog asking if you want to save any changes
		dup.changes = False # Answers "no" to the dialog asking if you want to save any changes
		impDiff.close()
		imp.close()
		dup.close()

# A script to move files around and delete things you don't want
def clean_up(directories, singleplane):

	# First check for empty directories and delete them
	for d in directories:
		if len(os.listdir(d)) == 0:
			print "Directory ", d, " is empty"
			shutil.rmtree(d)
		else:
			print "Directory ", d, "is not empty"

	# Additionally, if the data is z-stacks, delete the "filtered" directory (because filtered data will be in filteredMAX)
	if singleplane == False and os.path.exists(directories[5]):
		print "Deleting " + directories[5]
		shutil.rmtree(directories[5])

	# If the data is single plane, delete the whole MAX folder and also the filtered individual channels
	elif singleplane == True:
		print "Deleting MAX directory..."
		MAX = os.path.join(directories[0], "MAX")
		shutil.rmtree(MAX)
		#print "Deleting filtered channels..."
		#for file in glob.glob(os.path.join(directories[5], "C?*")):
			#os.remove(os.path.join(directories[5], file))

	# DOWN HERE YOU CAN ADD OTHER DIRECTORIES THAT YOU NEVER USE AND WANT TO DELETE
	# if os.path.exists(directories[4]): # this checks for rawMAX
	# 	shutil.rmtree(directories[4]) # this removes rawMAX

# run_it is the main function that calls all the other functions
# This is the place to comment out certain function calls if you don't have a need for them
def run_it():
	# Make an error log file that can be written to
	errorFilePath = os.path.join(experimentFolder, "errorFile.txt")
	now = datetime.datetime.now()
	errorFile = open(errorFilePath, "w")
	errorFile.write("\n" + now.strftime("%Y-%m-%d %H:%M") + "\n")
	errorFile.write("#### anilyze-data  ####" + "\n")
	#errorFile.write("Here we go...\n")
	errorFile.close()

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
		try:
			directories = make_directories(scan) # make the directories
			basename = os.path.basename(scan) # get the scan name (basename)

			errorFile = open(errorFilePath, "a")
			errorFile.write("\n \n -- Processing " + basename + " --" + "\n")
			errorFile.close()

			make_hyperstack(basename, scan, microscopeType) # open the hyperstack
			imp = IJ.getImage() # select the open image
			channels = imp.getNChannels() #gets the number of channels
			print "The number of channels is", channels
			singleplane = single_plane_check()
			print "The returned value of singleplane is ", singleplane
			split_channels(directories, channels) # split the hyperstack into channels (skips if channels == 1)
			make_MAX(directories, 4, singleplane) # make max projection (skips if singleplane == True)
			applyLut(channels, ch1color, ch2color, ch3color) # apply the user specified LUT(s)

			# calls merge_channels for raw data (skips if singleplane == True)
			print "Making raw merge..."
			if singleplane == False:
				merge_channels(basename, channels, directories, 4, "_raw") # makes rawMAX merge (4 = rawMax)
			elif singleplane == True:
				merge_channels(basename, channels, directories, 1, "_raw") # for single z-plane (1 = raw)

			## makes filtered images. Comment out if you dont want to make any.
			#print "Making filtered movies..."
			#rawFiles = os.listdir(directories[1]) # makes a list of the files in "raw"
			#median_filter(rawFiles, directories, 5) # saves output in filtered
			#print "making filtered max" # max projection of filtered data
			#make_MAX(directories, 3, singleplane) # makes filteredMAX (3 = filteredMAX)
			#applyLut(channels, ch1color, ch2color, ch3color) # apply the user specified LUT(s)
			#print "Making filtered merge..."

			## # calls merge_channels for filtered data (skips if singleplane == True)
			#if singleplane == False:
			#	merge_channels(basename, channels, directories, 3, "_filtered") # makes filteredMAX merge
			#elif singleplane == True:
			#	merge_channels(basename, channels, directories, 5, "_filtered") # for single z-plane (5 = filtered)

			# Make difference movies. Uses either filtered MAX projections or filtered hyperstacks (if singleplane == True)
			if differenceNumber >0:
				print "Making difference movies..."
				if singleplane == False:
					make_difference(directories, 4, differenceNumber, singleplane) # passes rawMAX directory. Change to 3 if you want filteredMAX
				elif singleplane == True:
					make_difference(directories, 1, differenceNumber, singleplane) # passes raw directory for raw hyperstacks. Change to 5 if you want filtered

			clean_up(directories, singleplane)	# clean up directory structure

			errorFile = open(errorFilePath, "a")
			errorFile.write("Congrats, it was successful!\n")
			errorFile.close()
			IJ.freeMemory() # runs garbage collector

		except:  #if there is an exception to the above code, create or append to an errorFile with the traceback
			print "Error with ", basename, "continuing on..."

			errorFile = open(errorFilePath, "a")
			errorFile.write("\n" + now.strftime("%Y-%m-%d %H:%M") + "\n") #writes the date and time
			#errorFile.write("Error detected...\n")
			errorFile.write("Error with " + basename + "\n" + "\n")
			traceback.print_exc(file = errorFile) # writes the error traceback to the file
			errorFile.close()
			IJ.run("Close All")
			#clean_up(directories, singleplane)	# clean up directory structure
			IJ.freeMemory() # runs garbage collector
			continue # continue on with the next scan, even if the current one threw an error

	errorFile = open(errorFilePath, "a")
	errorFile.write("\nDone with script.\n")
	errorFile.close()
run_it()
print "Done with script"
