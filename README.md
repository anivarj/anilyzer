# anilyzer
An ImageJ script to process your images.

# Dependencies
This script depends on understanding the file hierarchy inside the main scan directory. It can accommodate two main styles:

- Olympus FV style: The main scan directory includes individual scan directories and their accompanying .oif files.

- Bruker Prairieview style: The main scan directory only includes individual scan directories. Each .xlm file and all TIFs are inside the individual scan directory.


# A popup dialogue will ask you for the following:
- Input directory: choose the location where your scans are stored.

- Output directory: choose the location where the max projections will be stored.



# Breakdown of events:
- The script imports a hyperstack via bio-formats importer
- Next, the script makes MAX projections if you have multi-z data.
- Max projections are saved to the output directory
- The script will run clean-up and remove any empty directories (or any that you specify)

# Error logging
If errors occur, they will be logged in a file called errorFile, located in the main scan folder. If no errors occur, the log will be created and will state that there were no errors. If the script encounters an error, it should log the scan name and error type and continue on. Occasionally, an error will cause a dialogue box to pop up that the used must interact with. If this occurs, please note what caused the issue and let me know, as I'd like to try to eliminate pausing.

# Common errors:

- Extra slices: If you have an extra partial slice from stopping the acquisition manually, the script should close it, but occasionally this might throw an error and/or produce extra files if it tries to run them through the stream.

Hopefully this script will be helpful, and feel free to check out a branch and make your own edits/improvements!
Let me know if there is anything you would like to see implemented.

-Ani
