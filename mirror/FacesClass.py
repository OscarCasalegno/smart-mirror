import numpy as np
import cv2
import pickle
import os
from datetime import datetime
from PIL import Image
from time import sleep


def path_getter(end_path):
    path = __file__ + ""
    temp = path.split("\\")
    uri_file = ""
    for direct in temp:
        uri_file = uri_file + direct + "\\"
        if direct == "smart-mirror":
            break
    return uri_file + end_path


class Faces:
    image_dir = path_getter('\\mirror\\images')

    def __init__(self):

        pass

    def newface(self, user_id):
        """
        used to add a new person to the database, asks for the name of the new person and checks wether it is already present.
        After opening the frame and receiving the 's' command, it start to capture images for 10 seconds.
        saves all the images in the image_dir in a folder named after the person.
        :return: True if person added, False if person already present
        """
        while True:
            if os.path.exists(os.path.join(self.image_dir, user_id)):
                print('Person already present')
                return False
            else:
                path = os.path.join(self.image_dir, user_id)
                os.mkdir(path)
                break

        # Read the video from specified path
        cam = cv2.VideoCapture(0)
        # frame
        currentframe = 0

        start = False
        while (True):
            # reading from frame
            ret, frame = cam.read()
            name = str(currentframe) + '.jpg'

            if start == False:
                cv2.putText(frame, 'Press s to Start', (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
                            cv2.LINE_AA)
            else:
                cv2.putText(frame, str(int(round(10 - (datetime.now() - t1).seconds))), (0, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                # writing the extracted images
                cv2.imwrite(os.path.join(path, name), frame)
                # increasing counter so that it will
                # show how many frames are created
                currentframe += 1
                if (datetime.now() - t1).seconds > 10:
                    break

            cv2.imshow('frame', frame)

            if cv2.waitKey(20) & 0xff == ord("s"):
                start = True
                t1 = datetime.now()

        # Release all space and windows once done
        cam.release()
        cv2.destroyAllWindows()
        return True

    def removeface(self, user_id):
        """
        Used to remove a person from the database, asks for the person and deletes every image and the folder.
        :return: True if person deleted, False if person not present
        """
        while True:
            if os.path.exists(os.path.join(self.image_dir, user_id)):
                path = os.path.join(self.image_dir, user_id)
                for file in os.listdir(path):
                    file_path = os.path.join(path, file)
                    os.remove(file_path)
                os.rmdir(path)
                return True
            else:
                print('Person not present')
                return False

    def get_registered_faces(self):
        return os.listdir(self.image_dir)

    def personnumber(self):
        persons = os.listdir(self.image_dir)
        return len(persons)

    def train(self):
        """
        Trains the face recognition to recognize the persons in the database.
        Generates a .yml file that contains the training data.
        """
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
        recognizer = cv2.face.LBPHFaceRecognizer_create()

        current_id = 0
        label_ids = {}
        y_labels = []
        x_train = []

        for root, dirs, files in os.walk(self.image_dir):
            for file in files:
                if file.endswith("png") or file.endswith('jpg') or file.endswith('pgm'):
                    path = os.path.join(root, file)
                    label = os.path.basename(os.path.dirname(path)).replace(" ", "-").lower()
                    # print(label, path)
                    if not label in label_ids:
                        label_ids[label] = current_id
                        current_id += 1
                    id_ = label_ids[label]
                    # print label_ids
                    pil_image = Image.open(path).convert('L')
                    size = (550, 550)
                    final_image = pil_image.resize(size, Image.ANTIALIAS)
                    image_array = np.array(final_image, 'uint8')
                    # print image_array
                    faces = face_cascade.detectMultiScale(image_array)

                    for (x, y, w, h) in faces:
                        roi = image_array[y:y + h, x:x + w]
                        x_train.append(roi)
                        y_labels.append(id_)

        with open(path_getter('mirror/labels.pickle'), 'wb') as f:
            pickle.dump(label_ids, f)

        recognizer.train(x_train, np.array(y_labels))
        recognizer.save('mirror/trainer.yml')

    def recognize(self):
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        try:
            recognizer.read(path_getter('mirror/trainer.yml'))
        except:
            print 'No training file found'
            return 'ERROR_TRAINING'

        labels = {'person_name': 1}
        with open(path_getter('mirror/labels.pickle'), 'rb') as f:
            old_labels = pickle.load(f)
            labels = {v: k for k, v in old_labels.items()}

        cap = cv2.VideoCapture(0)
        if cap is None or not cap.isOpened():
            return 'ERROR_CAMERA'

        # Capture frame-by-frame
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detection of faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=5)

        # recognition
        if len(faces) == 0:
            return 'no_face'
        if len(faces) > 1:
            return 'unknown'
        else:
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y + h, x:x + w]
                id_, conf = recognizer.predict(roi_gray)
                if 50 <= conf <= 85:
                    return labels[id_]
                else:
                    return 'unknown'

        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()
