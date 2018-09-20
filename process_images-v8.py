# @File(label = "Input directory", style = "directory") experimentFolder
# @Integer(label = "Slices to remove for difference movie", value = 4) differenceNumber
import os, sys, traceback
from ij import IJ, WindowManager, ImagePlus
from ij.gui import GenericDialog
from ij.plugin import ImageCalculator
import datetime

experimentFolder = str(experimentFolder)
# Get a list of all scans inside the experimentFolder and save them as a list
def list_scans(experimentFolder):
    scanList = []
    for scan in os.listdir(experimentFolder):
        if os.path.isdir(os.path.join(experimentFolder, scan)):
            scanList.append(os.path.join(experimentFolder, scan))
    return scanList

# check to see if directories already exist. If not, make them. Needs to be passed the full path from "scan" in "main()"
def make_directories(scan):
    # defining all the paths to the output folders
    processed = os.path.join(scan, "processed")
    raw = os.path.join(processed, "raw")
    diff = os.path.join(processed, "diff")
    MAX = os.path.join(processed, "MAX")
    filteredMAX = os.path.join(MAX, "filteredMAX")
    rawMAX = os.path.join(MAX, "rawMAX")
    directories = [processed, raw, diff, filteredMAX, rawMAX]
    # check to see if the folders exist, if not, make them
    for d in directories:
        if os.path.exists(d):
            base = os.path.basename(d)
            print "The directory'", base, "'already exists!"
        else:
            os.makedirs(d)
            print d, "created"
    print "Finished creating directories!"
    return directories

def make_hyperstack(scan, basename):
    print basename
    xmlFile = basename + ".xml"
    xmlFile = os.path.join(scan, xmlFile)
    print "Opening file"
    IJ.run("Bio-Formats Importer", "open=" + xmlFile + " color_mode=Default concatenate_series open_all_series rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT")
    print "File opened"
    imp = IJ.getImage()
    imp.setTitle(basename + "_raw.tif")

def split_channels(directories, channels):
    imp = IJ.getImage()
    if channels >1:
        IJ.run("Split Channels")
    else:
        print "Only one channel, bypassing channel splitter..."
        imp = IJ.getImage()
        windowName = imp.getTitle()
        imp = imp.setTitle("C1-" + windowName)

    image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
    for i in image_titles:
        imp = WindowManager.getImage(i)
        windowName = imp.getTitle()
        IJ.saveAsTiff(imp, os.path.join(directories[1], windowName))

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
        IJ.saveAsTiff(imp, os.path.join(directories[x], windowName))
        imp = WindowManager.getImage(i)
        imp.changes = False
        imp.close()

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
        IJ.saveAsTiff(imp, os.path.join(directories[x], windowName))
        IJ.run("Close All")
    else:
        print "Only 1 channel, skipping merge..."
        IJ.run("Close All")
    print "Closing all files..."

def median_filter(rawFiles, directories):
    for f in rawFiles:
        IJ.open(os.path.join(directories[1], f))
    image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
    for i in image_titles:
        imp = WindowManager.getImage(i)
        IJ.run(imp, "Median...", "radius =1 stack")
        windowName = WindowManager.getImage(i).getTitle().replace("raw", "filtered")
        imp.setTitle(windowName)

def make_difference(directories, x, differenceNumber):
    print "Making Difference movies..."
    for file in os.listdir(directories[3]):
        if "MAX" in file:
            IJ.open(os.path.join(directories[3], file))
    image_titles = [WindowManager.getImage(id).getTitle() for id in WindowManager.getIDList()]
    for i in image_titles:
        imp = WindowManager.getImage(i)
        windowName = imp.getTitle()
        imp.setT(1)
        dup = imp.duplicate()
        dup.show()
        dup.setTitle(windowName + "_dup")

        differenceNumberString = str(differenceNumber)

        for n in range(1, differenceNumber+1):
            if n >= 1:
                IJ.run(imp, "Delete Slice", "")

        dup = WindowManager.getImage(windowName + "_dup")
        IJ.run(dup,"Reverse", "")

        for n in range(1, differenceNumber+1):
            if n >= 1:
                IJ.run(dup, "Delete Slice", "")

        IJ.run(dup, "Reverse", "")
        calc = ImageCalculator()
        impDiff = calc.calculate("Subtract create stack", imp, dup)
        impDiff = WindowManager.getImage("Result of "+ windowName)
        windowName = impDiff.getTitle().replace("Result of ", "Diff" + differenceNumberString + "-")
        impDiff.setTitle(windowName)
        IJ.saveAsTiff(impDiff, os.path.join(directories[x], windowName))
        impDiff.changes = False
        imp.changes = False
        dup.changes = False
        impDiff.close()
        imp.close()
        dup.close()
        print "Finished making difference movies..."

def run_it():
    errorFilePath = os.path.join(experimentFolder, "errorFile.txt")
    scanList = list_scans(experimentFolder) # gets a list of all the scan paths in experiment folder
    for scan in scanList:
    	try:
            basename = os.path.basename(scan)
            print "Checking for output directories in ", scan
            directories = make_directories(scan)
            make_hyperstack(scan, basename)
            imp = IJ.getImage()
            channels = imp.getNChannels()
            print "The number of channels is", channels
            split_channels(directories, channels)
            make_MAX(directories, 4)
            print "Making rawMAX merge"
            merge_channels(basename, channels, directories, 4) #makes rawMAX merge (the 4 determines where it saves)
            

            # processing stream to make filtered images
            #print "Making filtered movies..."
            rawFiles = os.listdir(directories[1])
            median_filter(rawFiles, directories)
            make_MAX(directories, 3)
            merge_channels(basename, channels, directories, 3)


            #make difference movie
            print "Making difference movies..."
            make_difference(directories, 2, differenceNumber)
        except:
            print "Error with ", basename, "continuing on..."
            if os.path.exists(errorFilePath):
                append_write = "a"
            else:
                append_write = "w"

            now = datetime.datetime.now() #gets the current date and time
            errorFile = open(errorFilePath, append_write)
            errorFile.write("\n" + now.strftime("%Y-%m-%d %H:%M") + "\n")
            errorFile.write("Error with " + basename + "\n")
            traceback.print_exc(file = errorFile)
            errorFile.close()
            IJ.run("Close All")
            continue
run_it()
print "The fahkin script is ovah bub..."
