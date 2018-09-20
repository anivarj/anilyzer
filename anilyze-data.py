# @File(label = "Input directory", style = "directory") experimentFolder
# @Integer(label = "Slices to remove for difference movie", value = 4) differenceNumber
import os, sys, traceback, shutil
from ij import IJ, WindowManager, ImagePlus
from ij.gui import GenericDialog
from ij.plugin import ImageCalculator
import datetime

experimentFolder = str(experimentFolder) #changes the selected directory into a string for future use

# Get a list of all scan folders inside the experimentFolder and save them as a list called scanList
def list_scans(experimentFolder):
    scanList = []
    for scan in os.listdir(experimentFolder): #gets a list of all the names inside experimentFolder
        if os.path.isdir(os.path.join(experimentFolder, scan)): #if the name is a directory, get the full path to it and add to scanList
            scanList.append(os.path.join(experimentFolder, scan))
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

#Uses Bio-formats importer to import a hyperstack from an xml file. The xml file must have the same name as the scan
# Gets basename of the scan from run_it() function
def make_hyperstack(scan, basename):
    print basename
    xmlFile = basename + ".xml"
    xmlFile = os.path.join(scan, xmlFile) #makes path to the xml file
    print "Opening file"
    IJ.run("Bio-Formats Importer", "open=" + xmlFile + " color_mode=Default concatenate_series open_all_series rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT")
    print "File opened"
    imp = IJ.getImage()
    imp.setTitle(basename + "_raw.tif")

#Runs the channel splitter if it detects multiple channels.
def split_channels(directories, channels):
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

#If there is more than one channel, runs merge_channels. Else skips this step 
def merge_channels(basename, channels, directories, x):
    image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
    if channels >1:
        print "Found", channels, "channels...merging them together...."
        if channels == 2:
            IJ.run("Merge Channels...", "c1=" + image_titles[0] + " c2=" + image_titles[1] + " create keep")
        if channels == 3:
            IJ.run("Merge Channels...", "c1=" + image_titles[0] + " c2=" + image_titles[1] + " c3=" + image_titles[2] + " create keep")
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
        print "Finished making difference movies..."

# the main function that calls all the other functions
def run_it():
    errorFilePath = os.path.join(experimentFolder, "errorFile.txt") #makes an error log file path
    now = datetime.datetime.now() # gets the current date and time
    errorFile = open(errorFilePath, "w")
    errorFile.write("\n" + now.strftime("%Y-%m-%d %H:%M") + "\n") #writes the date and time
    errorFile.write("Here we go...don't fuck it up...\n")
    errorFile.close()
            
    scanList = list_scans(experimentFolder) # gets a list of all the scan paths in experiment folder
    for scan in scanList:
    	try:
            basename = os.path.basename(scan)
            print "Checking for output directories in ", scan
            directories = make_directories(scan)
            make_hyperstack(scan, basename)
            imp = IJ.getImage()
            channels = imp.getNChannels() #gets the number of channels
            print "The number of channels is", channels
            split_channels(directories, channels)
            make_MAX(directories, 4)
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
            make_difference(directories, 3, differenceNumber)
            
            errorFile = open(errorFilePath, "a")
            errorFile.write("Congrats, you didn't fuck it up!\n")
            errorFile.close()
        
        except:  #if there is an exception to the above code, create or append to an errorFile with the traceback
            print "Error with ", basename, "continuing on..."
 
            errorFile = open(errorFilePath, "a")
            errorFile.write("\n" + now.strftime("%Y-%m-%d %H:%M") + "\n") #writes the date and time
            errorFile.write("You fucked it up\n")
            errorFile.write("\nError with " + basename + "\n")
            traceback.print_exc(file = errorFile)
            errorFile.close()
            IJ.run("Close All")
            continue #continue on with the next scan, even if the current one threw an error
            
    errorFile = open(errorFilePath, "a")
    errorFile.write("\nThe fahkin script is ovah bub...\n")
    errorFile.close()
run_it()
print "Done with script"
