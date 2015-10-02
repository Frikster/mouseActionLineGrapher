"""
Script holding all attributes/functions/globals related to pre-processing textFiles
This script has been rewritten to avoid classes so as to avoid issues when using the rPython package

Please note that you may need to change global fields for the program to work for you

args:
    working_dir (str): Full path of the directory that contains all textFiles to be analyzed
    folders_to_ignore ([str]): List of folders that are ignored. Only the folders name is required, not each one's full path
    output_loc (str): where any analysis is outputted to
    bin_time (int): the time in seconds of bins for the graph (86400 = seconds in a day) (deprecated. Binning is handled by R now)
    """

from datetime import datetime
import os
import numpy as np
from datetime import datetime
import itertools
import csv
import copy

# Column Numbers
TAG_COL = 0
TIME_COL = 1
DATE_COL = 2
ACTION_COL = 3
TEXT_LOC_COL = 4

TAG_COL_NAME = "Tag"
TIME_COL_NAME = "Time"
DATE_COL_NAME = "Date"
ACTION_COL_NAME = "Action"
TEXT_LOC_COL_NAME = "Source"

#MICE_GROUPS = {
#    'EL':[2015050115,1312000377,1312000159,1302000245,1312000300],
#    'EP': [1302000139, 2015050202, 1412000238],
#    'AB': [1312000592, 1312000573, 1312000090]
#}
#TAGS = []
#for i in range(len(MICE_GROUPS.items())):
#    TAGS.extend(list(MICE_GROUPS.items())[i][1])

#DIR_WITH_TEXTFILES = "/media/cornelis/DataCDH/Raw-data"
#FOLDERS_TO_IGNORE = ["Old and or nasty data goes here"]
#OUTPUT_LOC = "/home/cornelis/Downloads/"

seshStart_str = 'SeshStart'
seshEnd_str = 'SeshEnd'
seshStartTag_str = '0000000000'
seshEndTag_str = '0000000000'

def PreprocessTextfiles(absolute_start_time, absolute_end_time, dir_with_textfiles, folders_to_ignore, output_loc):
	global DIR_WITH_TEXTFILES
	global FOLDERS_TO_IGNORE
	global OUTPUT_LOC	
	FOLDERS_TO_IGNORE = folders_to_ignore.split(',')
	DIR_WITH_TEXTFILES = str(dir_with_textfiles)
	OUTPUT_LOC = str(output_loc)
	absolute_start_time = datetime.strptime(absolute_start_time, '%Y-%m-%d %H:%M:%S')
	absolute_end_time = datetime.strptime(absolute_end_time, '%Y-%m-%d %H:%M:%S')
	# texts_not_imported gets its value at the end of the import_texts_to_list_of_mat function
	# Yes it is set to the same thing very inefficiently three times since the function is called
	# three times and it clearly will change to the last run of the function if any run is different
	# TODO: fix this inefficiency and poor design. 
	# TODO: Obviously this no longer works after you removed classes
	texts_not_imported = None
	txt_list = get_all_text_locs()
	
	# First get all the lines between the two times with only exact duplicates removed (same line in same text file)
	all_lines = import_texts_to_list_of_mat(txt_list, absolute_start_time, absolute_end_time)
	all_lines = list(itertools.chain.from_iterable(all_lines))
	# Sort the lines
	times = get_col(all_lines, TIME_COL)
	all_lines = sort_X_BasedOn_Y_BeingSorted(all_lines, times)

	# Make a list of all the text files we took data from
	texts_imported = get_col(all_lines, TEXT_LOC_COL)
	texts_imported = list(set(texts_imported))

	# Now do it again but remove all the duplicates
	all_lines_no_dupes = get_all_lines_no_dupes(txt_list, absolute_start_time, absolute_end_time)
	# Sort the lines
	times = get_col(all_lines_no_dupes, TIME_COL)
	all_lines_no_dupes = sort_X_BasedOn_Y_BeingSorted(all_lines_no_dupes, times)

	# if an output_dir was specified, output a csv to it
	output_all_lines_to_csv("all_lines", all_lines)
	output_all_lines_to_csv("all_lines_no_dupes",all_lines_no_dupes)
   
def output_all_lines_to_csv(title, lines):
	"""ouput all lines imported to a single csv"""
	print("Outputting "+title+" to "+OUTPUT_LOC)
	with open(OUTPUT_LOC+title+".csv", "wb") as f:
	    writer = csv.DictWriter(f, fieldnames = [TAG_COL_NAME, TIME_COL_NAME, DATE_COL_NAME,
		                                     ACTION_COL_NAME, TEXT_LOC_COL_NAME], delimiter=',')
	    writer.writeheader()
	    writer = csv.writer(f)
	    writer.writerows(lines)
	print("Finished Outputting")
            
def sort_X_BasedOn_Y_BeingSorted(X, Y):
	"""Sorts X based on the result from Y being sorted"""
	X = np.array(X)
	Y = np.array(Y)
	inds = Y.argsort()
	return(X[inds]) 

def get_col(list_of_lists,col_num):
	"""return desired column from list of lists as a list"""
	#print(list_of_lists)
	#print(np.asarray(list_of_lists))
	return list(np.asarray(list_of_lists)[:,col_num])    

def get_all_text_locs():
	"""Get a list of all text files in the given folder (including subdirectories)"""
	txt_list = []
	for root, dirs, files in os.walk(DIR_WITH_TEXTFILES):
	    for file in files:
		if file.endswith(".txt"):
			print(os.path.join(root, file))
			txt_list.append(os.path.join(root, file))
	    
	 # Remove all the paths that are subdirectories of the ignore folders
	for i in range(len(FOLDERS_TO_IGNORE)):
	    txt_list=[x for x in txt_list if not (FOLDERS_TO_IGNORE[i] in x)]
	return txt_list

def import_texts_to_list_of_mat(txtList, absolute_start_time, absolute_end_time):
	""" Import viable text_files to a list of matrices
	    Returns a list of lists where each list is a textFile. A line column is added
	    to each line specifying where the text file is that this line came from
	"""    
	lines_list = []  
	text_file_loc = []
	texts_not_imported_col_condition = []
	texts_not_imported_row_condition = []
	texts_not_imported_absolute_start_condition = []

	# Add a column that records where each line is from (directory location)
	text_file_loc_each_line = []
			
	# Append them all into one matrix (the ones with the appropriate number of columns)
	for i in range(len(txtList)):
	    text_file = txtList[i]
	    try:
		with open(text_file) as f:
		    reader = csv.reader(f, delimiter="\t")
		    new_lines = list(reader)
		print(str(len(new_lines))+" - "+text_file)
		# Don't consider textfiles before specified time
		text_start_date = datetime.strptime(new_lines[0][DATE_COL], '%Y-%m-%d %H:%M:%S.%f')
		# TODO: Figure textFile selection criteria out
		text_end_date = datetime.strptime(new_lines[len(new_lines)-1][DATE_COL], '%Y-%m-%d %H:%M:%S.%f')
		if absolute_end_time > text_start_date > absolute_start_time:
		    # Only consider textFile with more than 2 rows and that have 'SeshStart' in first line                                                                                               
		    if len(new_lines) > 2 and new_lines[0][ACTION_COL] == seshStart_str:
		        # Add a row for textFiles missing a SeshEnd          
		        if new_lines[-1][ACTION_COL] != seshEnd_str:
		            new_lines.append(new_lines[-1][:])
		            new_lines[-1][ACTION_COL] = seshEnd_str
		            new_lines[-1][TAG_COL] = seshEndTag_str
		        for line_ind in range(len(new_lines)):
		            text_file_loc_each_line.append(txtList[i])
		            new_lines[line_ind] = new_lines[line_ind] + [txtList[i]]
			print("TEXT FILE ACCEPTED")
		        lines_list.append(new_lines)
		        text_file_loc.append(txtList[i])
		    else:
		        print("Text file does not have enough rows - "+text_file)
		        texts_not_imported_row_condition.append(text_file)
		else:
		    print("Text file was taken too early - "+text_file)
		    texts_not_imported_absolute_start_condition.append(text_file)
	    except BaseException:
		print("Text file does not have enough columns - "+text_file)
		texts_not_imported_col_condition.append(text_file)
	texts_not_imported = [texts_not_imported_col_condition,texts_not_imported_row_condition, texts_not_imported_absolute_start_condition]

	# Sort the text file contents and names by startSeshes
	startSeshes = []
	for i in range(len(lines_list)):
	    startSeshes.append(lines_list[i][0][TIME_COL])
	# print(startSeshes[0:5])
	# print(text_file_loc[0:5])
	# print(lines_list[0:5])
	text_file_loc = sort_X_BasedOn_Y_BeingSorted(text_file_loc, startSeshes)
	lines_list = sort_X_BasedOn_Y_BeingSorted(lines_list, startSeshes)
	# print(text_file_loc[0:5])
	# print(lines_list[0:5])
	return(lines_list)

def get_all_lines_no_dupes(txt_list, absolute_start_time, absolute_end_time):
	"""Returns a list of lists that contains all lines from all text files in txt_list with duplicates removed"""
	lines_list = import_texts_to_list_of_mat(txt_list, absolute_start_time, absolute_end_time)
	lines_list = list(itertools.chain.from_iterable(lines_list))

	# Delete the column containing textFile locations so that duplicates can be properly removed
	# Create a copy
	lines_list_copy = copy.deepcopy(lines_list)
	for x in lines_list_copy:
	  del x[TEXT_LOC_COL]
	lines_list_copy = [list(x) for x in set(tuple(x) for x in lines_list_copy)]
	# The copy now contains all the unique lines without the textFile locs

	# Re-ad the textFile locs to the copy
	for line_copy_ind in range(len(lines_list_copy)):
	    for line_ind in range(len(lines_list)):
		if lines_list_copy[line_copy_ind][TIME_COL] == lines_list[line_ind][TIME_COL] and \
		        len(lines_list_copy[line_copy_ind]) == 4:
		    lines_list_copy[line_copy_ind].append(lines_list[line_ind][TEXT_LOC_COL])
	lines_list = lines_list_copy

	return lines_list

def eAnd(*args):
	"""Returns a list that is the element-wise 'and' operation along each index of each list in args"""
	return [all(tuple) for tuple in zip(*args)]   