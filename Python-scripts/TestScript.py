import numpy as np
from scipy import signal
#import matplotlib.pyplot as plt
from scipy.stats.stats import pearsonr
from scipy import ndimage
#from joblib import Parallel, delayed
#import multiprocessing
#import parmap
#import image_registration

#M1312000377_1438367187.563086.raw
#processed_data/Concatenated Stacks.raw
#file_to_filter = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/Videos/M2015050115_1438365772.086721.raw"
#file_to_filter2 = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/Videos/M2015050115_1438366080.539013.raw"
#file_to_save = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/global_signal.rawf"
#corrfile_to_save = "/media/ch0l1n3/DataFB/AutoHeadFix_Data/0802/EL_LRL/corr.rawf"
#sd_file = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/mean_filter.rawf"

#save_dir = "/media/user/DataFB/AutoHeadFix_Data/0731/EL_LRL/"


#width = 256
#height = 256
#frame_rate = 30.0
#frame_size = width * height * 3

starting_frame = 100

def get_frames(rgb_file,width,height):
    frame_size = width * height * 3
    with open(rgb_file, "rb") as file:
        frames = np.fromfile(file, dtype=np.uint8)
        total_number_of_frames = int(np.size(frames)/frame_size)
        print(total_number_of_frames)
        frames = np.reshape(frames, (total_number_of_frames, width, height, 3))

        frames = frames[starting_frame:, :, :, 1]
        frames = np.asarray(frames, dtype=np.float32)
        total_number_of_frames = frames.shape[0]

    frames=frames.tolist()

    return frames

#frames=get_frames("/home/cornelis/Downloads/M1302000139_1442697993.722772.raw",256,256)
#print(frames)