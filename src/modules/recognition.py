import face_recognition
import numpy as np
import csv
import sys
import logging
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from deepface import DeepFace
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)
import config as cfg
from pprint import pprint
import cv2
from keras.models import load_model

logger = logging.getLogger('recognition')


known_face_encodings_names = ([],[],[]) #imaged encoded to use for recognition, name of the  people in image, CF of the people



def setUpImages(lt_usersMlInfo):
    global known_face_encodings_names
    known_faces_name=[]
    known_faces_encoded=[]
    cf=[]

    for (u_name,u_cf,u_fname)  in lt_usersMlInfo:  #skipping header at row 0
        _image = face_recognition.load_image_file(u_fname)
        _face_encoding = face_recognition.face_encodings(_image)[0]
        known_faces_encoded.append(_face_encoding)
        known_faces_name.append(u_name)
        cf.append(u_cf)
    logger.info("Loader  %d image from dataset",len(known_faces_name))
    known_face_encodings_names=(known_faces_encoded,known_faces_name,cf)
  #  return (known_faces_encoded,known_faces_name,cf)


def setUpImagesFromFile(pathFileDataset):
    known_faces_name=[]
    known_faces_encoded=[]
    cf=[]

    try:
        file = open(pathFileDataset, "r")
        data = list(csv.reader(file, delimiter=","))
        file.close()
    except:
        logger.info("Missing file:"+pathFileDataset)
        return (known_faces_encoded,known_faces_name,cf)
    for i in range(1,len(data)):  #skipping header at row 0
        _image = face_recognition.load_image_file(data[i][2])
        _face_encoding = face_recognition.face_encodings(_image)[0]
        known_faces_encoded.append(_face_encoding)
        known_faces_name.append(data[i][0])
        cf.append(data[i][1])
    logger.info("Loader  %d image from dataset",len(known_faces_name))
    return (known_faces_encoded,known_faces_name,cf)

def printInfo(face_distances):
    global known_face_encodings_names
    logger.debug("Name,CF,distance")
    for i in range(len(face_distances)):
        logger.debug(known_face_encodings_names[1][i],known_face_encodings_names[2][i],face_distances[i])

def analyze(fileImageToMatch, pathFileDataset=None,debug=False,maximumdistance=0.6):
    global known_face_encodings_names
    name,cf,face_distance = "Unknown","",0.0
    if pathFileDataset :
        logger.info("Load from file:"+pathFileDataset)
        known_face_encodings_names=setUpImagesFromFile(pathFileDataset)
    if len(known_face_encodings_names[0])>0:
        unknow_face_image=face_recognition.load_image_file(fileImageToMatch)
        unknow_face_encoded=face_recognition.face_encodings(unknow_face_image)
        if len(unknow_face_encoded)>0:
            unknow_face_encoded=face_recognition.face_encodings(unknow_face_image)[0]
        else:
            return (name,face_distance,cf)
        #maximu distance match default is 0.6 distance > 0.6 is False true otherwise
        matches = face_recognition.compare_faces(known_face_encodings_names[0], unknow_face_encoded,tolerance=maximumdistance)
        #face_distance contains ecuclidean distance betweeen unknow image and images of dataset, lesser valuue best match
        face_distances = face_recognition.face_distance(known_face_encodings_names[0], unknow_face_encoded)
        if debug:
            logger.debug("maximum distance to have a match:",maximumdistance)
            logger.debug(matches)
            logger.debug(face_distances)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_encodings_names[1][best_match_index]
            cf=known_face_encodings_names[2][best_match_index]
            #trasform the eculidean value to percentage of match
            face_distance=face_distances[best_match_index]
    return (name,face_distance,cf)


models=["Dlib"]
metrics=["euclidean"]
attributes=["emotion"]

def sentiment_detection(fileImageToMatch):
     sentiment = DeepFace.analyze(img_path = fileImageToMatch, actions = attributes,enforce_detection=False)
     return sentiment


#size: resaize factor
#pre traines tensorflow model
mask_model=load_model(current+"/models/mask_model.hdf5")
#opencv classifier to detect face
classifier = cv2.CascadeClassifier(current+'/models/haarcascade_frontalface_default.xml')

def mask_detection(fileImageToMatch,size=4):
    im = cv2.imread(fileImageToMatch)
     # Resize the image to speed up detection
    mini = cv2.resize(im, (im.shape[1] // size, im.shape[0] // size))

    # detect MultiScale / faces
    faces = classifier.detectMultiScale(mini)
    logger.debug("Check for face ")
    # Draw rectangles around each face
    for f in faces:
        logger.debug("Face found")
        (x, y, w, h) = [v * size for v in f] #Scale the shapesize backup
        #Save just the rectangle faces in SubRecFaces
        face_img = im[y:y+h, x:x+w]
        resized=cv2.resize(face_img,(150,150))
        normalized=resized/255.0
        reshaped=np.reshape(normalized,(1,150,150,3))
        reshaped = np.vstack([reshaped])
        result=mask_model.predict(reshaped)
        print("INSIDE:"+str(result))
        label=np.argmax(result,axis=1)[0]
        if label>0:
            return True #WITH MASK
        else:
            return False #WITHOUT MASK


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(cfg)
        print("REQUIRED FULLPATH OF UNKNOW IMAGE")
    else:    
        result=analyze(sys.argv[1],cfg.csvInfoPath,debug=True)
        pprint(result)
        sentiment=sentiment_detection(sys.argv[1])
        pprint(sentiment)
        mask=mask_detection(sys.argv[1])
        pprint(mask)
