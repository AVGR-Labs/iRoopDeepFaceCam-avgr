import modules.globals
global camera
camera = None

ROOT = None
ROOT_HEIGHT = 900
ROOT_WIDTH = 600

PREVIEW = None
PREVIEW_MAX_HEIGHT = 700
PREVIEW_MAX_WIDTH  = 1200
PREVIEW_DEFAULT_WIDTH  = 640
PREVIEW_DEFAULT_HEIGHT = 360
BLUR_SIZE=1

# Set initial size of the preview window
WEBCAM_PREVIEW_WIDTH= 640
WEBCAM_PREVIEW_HEIGHT = 360
RECENT_DIRECTORY_SOURCE = None
RECENT_DIRECTORY_TARGET = None
RECENT_DIRECTORY_OUTPUT = None

preview_label = None
preview_slider = None
source_label = None
target_label = None
status_label = None

img_ft, vid_ft = modules.globals.file_types

stickiness_factor_size = None
face_tracking = None
y_start = 0.01
y_increment = 0.05