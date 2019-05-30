# anilyzer
An ImageJ script to process your images.

The user specifies which folder their scans are stored in, and the script will process each scan individually.
The user also specifies which LUT they want for each channel, which will be used later when the channels are merged together.
The script imports a hyperstack via bio-formats importer, then splits the channels and saves them.
Next, the script makes MAX projections (both a raw version, and then a version from median-filtered data with a radius=1).
If there is more than one channel, the script will create a merged file for the user.
Lastly, the script makes difference movies based on a number that the user inputs in the beginning of the script, stating how many frames to delete.

If errors occur, they will be logged in a file called errorFile, located in the main experiment folder where all the scans are stored. If no errors occur, the log will be created and will state that there were no errors. If the script encounters an error, it should log the scan name and error type and continue on. Occasionally, an error will cause a dialogue box to pop up that the used must interact with. If this occurs, please note what caused the issue and let me know, as I'd like to try to eliminate pausing.

COMMON ERRORS:

Extra slices: If you have an extra partial slice from stopping the acquisition manually, this might throw an error at MAX projecting and/or produce extra files if it tries to run them through the stream. 

Stack problems: If the script finds a movie that does not have multiple z-stacks, it will skip MAX projection and log in the errorfile that the acquisition was single plane.

Hopefully this script will be helpful, and feel free to check out a branch and make your own edits/improvements!
Let me know if there is anything you would like to see implemented.

-Ani
