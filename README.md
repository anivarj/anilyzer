# anilyzer
An ImageJ script to process your images.

# Dependencies
This script depends on understanding the file hierarchy inside the main scan directory. It can accommodate two main styles:

- Olympus FV style: The main scan directory includes individual scan directories and their accompanying .oif files.

- Bruker Prairieview style: The main scan directory only includes individual scan directories. Each .xlm file and all TIFs are inside the individual scan directory.


# A popup dialogue will ask you for the following:
- Input directory: Choose the location where your scans are stored.

- Slices to remove for difference movie: Choose how many slices are deleted to make difference movies (preserving moving objects, and removing static signal). Removing more frames will make the subtraction less harsh. Set to 0 if you do not want to make any difference movies.

- Select channel colors: Choose which LUTs will be used for each channel. Right now, choices are Red, Blue, Green and Grays. You can add any LUT you like to the parameter list.


# Breakdown of events:
- The script imports a hyperstack via bio-formats importer, then splits the channels and saves them.
- Next, the script makes MAX projections if you have multi-z data.
- LUTs are applied to each channel based on what you specified in the dialogue box.
- If there are multiple channels, the script will create a merged file for the user.
- The script makes difference movies based on a number that the user inputs in the beginning of the script.
- The script will run clean-up and remove any empty directories (or any that you specify)

# Error logging
If errors occur, they will be logged in a file called errorFile, located in the main scan folder. If no errors occur, the log will be created and will state that there were no errors. If the script encounters an error, it should log the scan name and error type and continue on. Occasionally, an error will cause a dialogue box to pop up that the used must interact with. If this occurs, please note what caused the issue and let me know, as I'd like to try to eliminate pausing.

# Common errors:

- Extra slices: If you have an extra partial slice from stopping the acquisition manually, the script should close it, but occasionally this might throw an error and/or produce extra files if it tries to run them through the stream.

- Incorrect channels: If you select the wrong number of LUTs from the dropdown, the script will fail. 

Hopefully this script will be helpful, and feel free to check out a branch and make your own edits/improvements!
Let me know if there is anything you would like to see implemented.

-Ani
