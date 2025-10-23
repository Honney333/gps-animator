import os
import platform

os_name = platform.system()

class Settings:
    # needs to be the number of rotations. For 4 the files would need to be named 0.gif, 90.gif, 180.gif and 270.gif
    # 0 is up direction, 90 left, 180 down, 270 right
    # there are also example Blender files to create the images and Python files that name them correctly.
    WALKING_DIRECTIONS = 4
    TRAIN_DIRECTIONS = 64
    CAR_DIRECTIONS = 64
    end     = 0
    walking = 1
    train   = 2
    car     = 3

    ### Output folder
    # here will be the directory where the animation gets put
    if os.path.exists(os.path.expanduser("~/Dokumente/gps-animator/output")):
        OUTPUT = os.path.expanduser("~/Dokumente/gps-animator/output")
    else:
        OUTPUT = os.path.expanduser("~/Documents/gps-animator/output")

    ### Input folder
    # here will be the safe spot for the points (points.txt)
    if os.path.exists(os.path.expanduser("~/Dokumente/gps-animator/input")):
        INPUT = os.path.expanduser("~/Dokumente/gps-animator/input")
    else:
        INPUT = os.path.expanduser("~/Documents/gps-animator/input")

    ### Cache folder
    # here will be the safe spot for the walking, driving or train paths (this will be hard to read do to hashing)
    if os.path.exists(os.path.expanduser("~/Dokumente/gps-animator/cache")):
        CACHE = os.path.expanduser("~/Dokumente/gps-animator/cache")
    else:
        CACHE = os.path.expanduser("~/Documents/gps-animator/cache")

settings = Settings()