# @File(label = "Input directory", style = "directory") experimentFolder
# @Integer(label = "Slices to remove for difference movie", value = 4) differenceNumber
#@ String (visibility=MESSAGE, value="Please select your channel colors. If you have one channel, assign it to Channel 1.") msg
#@ String(label="Channel 1",choices={"Select", "Red", "Green", "Blue"}, value = "Select", persist=false) ch1color
#@ String(label="Channel 2",choices={"Select","Red", "Green", "Blue"}, value = "Select", persist=false) ch2color
#@ String(label="Channel 3",choices={"Select","Red", "Green", "Blue"}, value = "Select", persist=false) ch3color

"""
##AUTHOR: Ani Michaud (Varjabedian)

## DESCRIPTION: This script is for automating common Fiji processing commands for imaging datasets. The user inputs a directory where their imaging data is stored, and also information about channel color assignments. If the user is not interested in making difference movies, they can set the integer to "0" or comment out that function call in the main function run_it().

The script first checks the file structure of the input directory, as different microscopes store information in different ways, and then it assigns a value to microscopeType. This value allows the correct files to be parsed and the output directories to be placed in the correct location.

The script makes a list of all the scan directories, and for each scan, it assembles a hyperstack, splits channels, makes MAX projections and also does some filtering (but saves the raw data as well). It merges multi-channel images using the colors you specify in the beginning. At the end, it makes difference movies, which are useful for enhancing moving signals and eliminating static ones. Everything is saved along the way, so feel free to comment out bits that you don't have use for.

For more information and up-to-date changes, visit the GitHub repository: https://github.com/anivarj/anilyzer

"""

#importing modules and other shit
import os, sys, traceback, shutil, glob
from ij import IJ, WindowManager, ImagePlus
from ij.gui import GenericDialog
from ij.plugin import ImageCalculator
import datetime
import fnmatch

experimentFolder = str(experimentFolder)

# Assesses the file structure of experimentFolder and assigns a "microscope type" which gets passed to other functions. This helps with determining where certain files and directories should be located.
def microscope_check(experimentFolder):
	#If it finds .oif files inside the main folder, it calls the microscope "Olympus"
	if any(File.endswith(".oif") for File in os.listdir(experimentFolder)):
		print(".oif files present, running Olympus pipeline")
		microscopeType = "Olympus"
		return microscopeType
	else:
		#If there are no .oif files in the main folder, it calls the microscope "Bruker"
		print("No .oif files present, running Bruker pipeline")
		microscopeType = "Bruker"
		return microscopeType

# Get a list of all scan folders inside the experimentFolder and save them as a list called scanList
def list_scans(experimentFolder, microscopeType):
	scanList = []
	# This bit is to screen out text files and other things that might be in the main folder, and only make a list of the scan directories
	if microscopeType == "Bruker":
		for File in os.listdir(experimentFolder):
			dirpath = os.path.join(experimentFolder, File)
			if os.path.isdir(dirpath):
				print "dirpath is " + dirpath
				scanList.append(dirpath)
		return scanList

	# If the microscope is "Olympus" type, the directories end in .oif.files
	if microscopeType == "Olympus":
		oifList = []
		for File in os.listdir(experimentFolder):
			if File.endswith(".oif.files"):
				dirpath = os.path.join(experimentFolder, File)
				print "dirpath is " + dirpath
				scanList.append(dirpath)
		return scanList


# check to see if directories already exist. If not, make them. Needs to be passed the full path to the scan
def make_directories(scan):
	# defining all the paths to the output folders
	processed = os.path.join(scan, "processed") #this is where your processed data will go
	raw = os.path.join(processed, "raw")
	diff = os.path.join(processed, "diff")
	MAX = os.path.join(processed, "MAX")
	filteredMAX = os.path.join(MAX, "filteredMAX")
	rawMAX = os.path.join(MAX, "rawMAX")
	directories = [processed, raw, diff, filteredMAX, rawMAX] # a list of all the paths to the directories

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
	return directories

#Uses Bio-formats importer to import a hyperstack 
def make_hyperstack(scan, microscopeType):
	basename = os.path.basename(scan)
	if microscopeType == "Olympus":
		initiatorFileName = os.path.splitext(basename) [0]
		basename = os.path.splitext(initiatorFileName) [0]
		print "basename is ", basename
		print ".oif file is ",  initiatorFileName
		initiatorFilePath = os.path.join(experimentFolder, initiatorFileName)
		print "Opening file ", initiatorFilePath

	elif microscopeType == "Bruker":
		#xmlFile = basename + ".xml"
		#xmlFile = os.path.join(scan, xmlFile) #makes path to the xml file
		print "basename is ", basename
		initiatorFileName = basename + "_Cycle00001_Ch?_000001.ome.tif"
		initiatorFilePath = os.path.join(scan, initiatorFileName)
		print "initiatorFilePath ", initiatorFilePath
		initiatorFilePath = glob.glob(initiatorFilePath)
		initiatorFilePath = initiatorFilePath[0]
		print "Opening file", initiatorFilePath

	IJ.run("Bio-Formats Importer", "open=[" + initiatorFilePath + "] color_mode=Grayscale concatenate_series open_all_series rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT")
	print "File opened"
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	for i in image_titles:
		print i
		imp = WindowManager.getImage(i)
		if imp.getNFrames() == 1: #if it is a partial slice, will close it
			imp.close()

	try:
		image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	except TypeError:
		raise Exception("No windows open! Is this a single slice acquisition?")
		return
	imp = IJ.getImage()
	imp.setTitle(basename + "_raw.tif")
	return basename

#Runs the channel splitter if it detects multiple channels.
def split_channels(directories, channels, ):
	imp = IJ.getImage()
	if channels >1:
		IJ.run("Split Channels")
	else:
		print "Only one channel, bypassing channel splitter..."
		imp = IJ.getImage()
		windowName = imp.getTitle()
		imp = imp.setTitle("C1-" + windowName) #just renames the window

	#saving the hyperstacks
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	for i in image_titles:
		imp = WindowManager.getImage(i)
		windowName = imp.getTitle()
		IJ.saveAsTiff(imp, os.path.join(directories[1], windowName))

# If there are more than one z-slice, runs the max projector function. Else, returns and error and quits the program
def make_MAX(directories, x):
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	for i in image_titles:
		imp = WindowManager.getImage(i)
		if imp.getNSlices() == 1:
			print "oops, cannot z-project"
			IJ.run("Close All")
			raise Exception("Not a stack!")

		IJ.run(imp, "Z Project...", "projection=[Max Intensity] all")
		imp = WindowManager.getImage("MAX_" + i)
		windowName = imp.getTitle()
		IJ.saveAsTiff(imp, os.path.join(directories[x], windowName)) #saves to rawMAX directory. Passed the directory from run_it()
		imp = WindowManager.getImage(i)
		imp.changes = False #Answers "no" to the dialog asking if you want to save any changes
		imp.close()

def applyLut (ch1color, ch2color, ch3color):
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	for i in image_titles:
		print i
		imp = WindowManager.getImage(i)
		print "imp is ", imp

		if fnmatch.fnmatch(i, "*C1*"):
			IJ.run(imp, ch1color, "")
			print "CH1 set"
		if fnmatch.fnmatch(i, "*C2*"):
			IJ.run(imp, ch2color, "")
			print "CH2 set"
		if fnmatch.fnmatch(i, "*C3*"):
			IJ.run(imp, ch3color, "")
			print "CH3 set"
		else:
			print "Done setting LUTs"


#If there is more than one channel, runs merge_channels. Else skips this step
def merge_channels(basename, channels, directories, x):
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	if channels >1:
		print "Found", channels, "channels...merging them together...."
		if channels == 2:
			IJ.run("Merge Channels...", "c1=[" + image_titles[0] + "] c2=[" + image_titles[1] + "] create keep")
		if channels == 3:
			IJ.run("Merge Channels...", "c1=[" + image_titles[0] + "] c2=[" + image_titles[1] + "] c3=[" + image_titles[2] + "] create keep")
		imp = WindowManager.getImage("Merged")
		imp.setTitle("Merged_" + basename)
		windowName = imp.getTitle()
		IJ.saveAsTiff(imp, os.path.join(directories[x], windowName)) #saves to rawMAX. Passed directory from run_it()
		IJ.run("Close All")
	else:
		print "Only 1 channel, skipping merge..."
		IJ.run("Close All")
	print "Closing all files..."

# Opens up the raw hyperstacks and runs a median filter
def median_filter(rawFiles, directories):
	for f in rawFiles:
		IJ.open(os.path.join(directories[1], f)) #this opens anything in the raw directory. If there are random files, this might cause problems
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	for i in image_titles:
		imp = WindowManager.getImage(i)
		IJ.run(imp, "Median...", "radius =1 stack")
		windowName = WindowManager.getImage(i).getTitle().replace("raw", "filtered") #save as _filtered.tif extension
		imp.setTitle(windowName)

# Based on the number you put in in the beginning dialogue box, it will remove slices to make a difference movie
# This function looks in filteredMAX to make the movies, but you can always point it to the rawMAX if you prever
def make_difference(directories, x, differenceNumber):
	for file in os.listdir(directories[x]): #opens up the MAX files in filteredMAX
		if "MAX" in file:
			IJ.open(os.path.join(directories[x], file))
	image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
	for i in image_titles:
		imp = WindowManager.getImage(i)
		windowName = imp.getTitle()
		imp.setT(1)
		dup = imp.duplicate()
		dup.show()
		dup.setTitle(windowName + "_dup")

		differenceNumberString = str(differenceNumber) #turns the integer input into a string (str)

		for n in range(1, differenceNumber+1):
			if n >= 1:
				IJ.run(imp, "Delete Slice", "")

		dup = WindowManager.getImage(windowName + "_dup")
		IJ.run(dup,"Reverse", "") #reverse the array so that the slices in the back become the front

		for n in range(1, differenceNumber+1):
			if n >= 1:
				IJ.run(dup, "Delete Slice", "")

		IJ.run(dup, "Reverse", "") #reverse the array back to native orientation
		calc = ImageCalculator()
		impDiff = calc.calculate("Subtract create stack", imp, dup)
		impDiff = WindowManager.getImage("Result of "+ windowName)
		windowName = impDiff.getTitle().replace("Result of ", "Diff" + differenceNumberString + "-")
		impDiff.setTitle(windowName)
		IJ.saveAsTiff(impDiff, os.path.join(directories[2], windowName)) #saves in diff folder
		impDiff.changes = False #Answers "no" to the dialog asking if you want to save any changes
		imp.changes = False #Answers "no" to the dialog asking if you want to save any changes
		dup.changes = False #Answers "no" to the dialog asking if you want to save any changes
		impDiff.close()
		imp.close()
		dup.close()

# the main function that calls all the other functions
def run_it():
	errorFilePath = os.path.join(experimentFolder, "errorFile.txt") #makes an error log file path
	now = datetime.datetime.now() # gets the current date and time
	errorFile = open(errorFilePath, "w")
	errorFile.write("\n" + now.strftime("%Y-%m-%d %H:%M") + "\n") #writes the date and time
	errorFile.write("Here we go...don't fuck it up...\n")
	errorFile.close()

	microscopeType = microscope_check(experimentFolder)
	if microscopeType == "Olympus":
		scanList = list_scans(experimentFolder, microscopeType)
		print "The returned scanList is "
		print scanList
	elif microscopeType == "Bruker":
		scanList = list_scans(experimentFolder, microscopeType) # gets a list of all the scan paths in experiment folder

	for scan in scanList:
		try:
			print "Checking for output directories in ", scan
			directories = make_directories(scan)
			basename = make_hyperstack(scan, microscopeType)
			print "The returned basename is ", basename
			imp = IJ.getImage()
			channels = imp.getNChannels() #gets the number of channels
			print "The number of channels is", channels
			split_channels(directories, channels)
			make_MAX(directories, 4)
			applyLut(ch1color, ch2color, ch3color)
			print "Making rawMAX merge"
			merge_channels(basename, channels, directories, 4) #makes rawMAX merge (the 4 determines where it saves)

			# processing stream to make filtered images. Comment out if you dont want to make any.
			print "Making filtered movies..."
			rawFiles = os.listdir(directories[1])
			median_filter(rawFiles, directories)
			make_MAX(directories, 3)
			merge_channels(basename, channels, directories, 3)

			# Make difference movies. As it stands, it currently looks in directories[2] aka filteredMAX.
			#If you commented out that stream or want them for the rawMAX, change the number to 4
			if differenceNumber >0:
				print "Making difference movies..."
				make_difference(directories, 3, differenceNumber)

			errorFile = open(errorFilePath, "a")
			errorFile.write("Processing " + basename + "\n")
			errorFile.write("Congrats, you didn't fuck it up!\n")
			errorFile.close()
			IJ.freeMemory() #runs garbage collector

		except:  #if there is an exception to the above code, create or append to an errorFile with the traceback
			print "Error with ", basename, "continuing on..."

			errorFile = open(errorFilePath, "a")
			errorFile.write("\n" + now.strftime("%Y-%m-%d %H:%M") + "\n") #writes the date and time
			errorFile.write("You fucked it up\n")
			errorFile.write("\nError with " + basename + "\n")
			traceback.print_exc(file = errorFile)
			errorFile.close()
			IJ.run("Close All")
			IJ.freeMemory() #runs garbage collector
			continue #continue on with the next scan, even if the current one threw an error

	errorFile = open(errorFilePath, "a")
	errorFile.write("\nDone with script.\n")
	errorFile.close()
run_it()
print "Done with script"
