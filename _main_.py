#@ File(label = "Input directory", style = "directory") experimentFolder
#@ Integer(label = "Slices to remove for difference movie", value = 0) differenceNumber
#@ String(label="Microscope",choices={"Bruker", "Olympus"}, value = "Bruker", persist=false) microscopeType

import functionfile as ff

experimentFolder = str(experimentFolder) # Converts the input directory you chose to a path string that can be used later on

def run_it():
    ff.make_log(experimentFolder) #make log file



