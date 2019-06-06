import uuid,os
from PIL import Image

def isValidImageFile(filename):
    file_extension = os.path.splitext(filename)[1]
    if file_extension in [".jpg", ".jpeg", ".png", ".gif", ".tiff"]
        return True
    return False
        