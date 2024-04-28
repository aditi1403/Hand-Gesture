import cv2
import os
import numpy as np
import threading
import time
import speech_recognition as sr
from gtts import gTTS
# import pyttsx
# import cvzone
from cvzone.HandTrackingModule import HandDetector

class PresentationController:
    def __init__(self, folderPath, gestureThreshold=300, delay=30):
        self.width, self.height = 640, 360
        self.gestureThreshold = gestureThreshold
        self.folderPath = folderPath
        self.delay = delay
        self.buttonPressed = False
        self.imgNumber = 0
        self.annotations = [[]]
        self.annotationNumber = -1
        self.annotationStart = False
        self.counter = 0
        self.hs, self.ws = int(60 * 1), int(107 * 1)

        # Camera Setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.width)
        self.cap.set(4, self.height)

        # Hand Detector
        self.detectorHand = HandDetector(detectionCon=0.7, maxHands=1)

        # Get list of presentation images
        self.pathImages = sorted(os.listdir(self.folderPath), key=len)

        # Speech Recognition Setup
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Threading
        self.thread = threading.Thread(target=self.run_voice_recognition, daemon=True)
        self.thread.start()

    def run_voice_recognition(self):
        listening = False
        while True:
            if not listening and not self.buttonPressed:
                time.sleep(0.5)  # To avoid cpu usage while not speaking
                continue

            if self.buttonPressed:
                self.buttonPressed = False
                listening = True
                print("Listening...")
                time.sleep(1)  # avoid mutiple commands
                continue

            if listening:
                voice_command = self.recognize_voice_command()
                if voice_command:
                    if "start listening" in voice_command:
                        print("Already listening.")
                    elif "stop listening" in voice_command:
                        listening = False
                        print("Stopped listening.")
                    elif "next" in voice_command:
                        if self.imgNumber < len(self.pathImages) - 1:
                            self.imgNumber += 1
                            self.annotations = [[]]
                            self.annotationNumber = -1
                            self.annotationStart = False
                    elif "previous" in voice_command:
                        if self.imgNumber > 0:
                            self.imgNumber -= 1
                            self.annotations = [[]]
                            self.annotationNumber = -1
                            self.annotationStart = False
                    elif voice_command.isdigit() and int(voice_command) > 0 and int(voice_command) <= len(self.pathImages):
                        selected_slide = int(voice_command) - 1
                        if selected_slide != self.imgNumber:
                            self.imgNumber = selected_slide
                            self.annotations = [[]]
                            self.annotationNumber = -1
                            self.annotationStart = False
                            print(f"Selected slide {self.imgNumber + 1}")

    def recognize_voice_command(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source)
                command = self.recognizer.recognize_google(audio)
                print("Command:", command)
                return command.lower()
            except sr.UnknownValueError:
                print("Could not understand audio.")
                return None
            except sr.RequestError:
                print("Could not request results. Check your internet connection.")
                return None

    def speak(self, text):
        tts = gTTS(text=text, lang='en')
        tts.save("temp.mp3")
        os.system("mpg123 temp.mp3")  # Play the generated speech

    def run(self):
        while True:
            # Get image frame
            success, img = self.cap.read()
            if not success:
                print("Failed to grab frame")
                continue
            img = cv2.flip(img, 1)
            pathFullImage = os.path.join(self.folderPath, self.pathImages[self.imgNumber])
            imgCurrent = cv2.imread(pathFullImage)

            # Find the hand and its landmarks
            hands, _ = self.detectorHand.findHands(img)  # with draw
            # Draw Gesture Threshold line
            cv2.line(img, (0, self.gestureThreshold), (self.width, self.gestureThreshold), (0, 255, 0), 5)

            if hands and not self.buttonPressed:  # If hand is detected
                hand = hands[0]
                cx, cy = hand["center"]
                lmList = hand["lmList"]  # List of 21 Landmark points
                fingers = self.detectorHand.fingersUp(hand)  # List of which fingers are up

                # Constrain values for easier drawing
                xVal = int(np.interp(lmList[8][0], [self.width // 2, self.width], [0, self.width]))
                yVal = int(np.interp(lmList[8][1], [150, self.height - 150], [0, self.height]))
                indexFinger = xVal, yVal

                if cy <= self.gestureThreshold:  # If hand is at the height of the face
                    if fingers == [1, 0, 0, 0, 0]:
                        print("Left")
                        self.buttonPressed = True
                        if self.imgNumber > 0:
                            self.imgNumber -= 1
                            self.annotations = [[]]
                            self.annotationNumber = -1
                            self.annotationStart = False
                    if fingers == [0, 0, 0, 0, 1]:
                        print("Right")
                        self.buttonPressed = True
                        if self.imgNumber < len(self.pathImages) - 1:
                            self.imgNumber += 1
                            self.annotations = [[]]
                            self.annotationNumber = -1
                            self.annotationStart = False

                if fingers == [0, 1, 1, 0, 0]:
                    cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)

                if fingers == [0, 1, 0, 0, 0]:
                    if not self.annotationStart:
                        self.annotationStart = True
                        self.annotationNumber += 1
                        self.annotations.append([])
                    print(self.annotationNumber)
                    self.annotations[self.annotationNumber].append(indexFinger)
                    cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)

                else:
                    self.annotationStart = False

                if fingers == [0, 1, 1, 1, 0]:
                    if self.annotations:
                        self.annotations.pop(-1)
                        self.annotationNumber -= 1
                        self.buttonPressed = True

            else:
                self.annotationStart = False

            if self.buttonPressed:
                self.counter += 1
                if self.counter > self.delay:
                    self.counter = 0
                    self.buttonPressed = False

            for i, annotation in enumerate(self.annotations):
                for j in range(len(annotation)):
                    if j != 0:
                        cv2.line(imgCurrent, annotation[j - 1], annotation[j], (0, 0, 200), 12)

            imgSmall = cv2.resize(img, (self.ws, self.hs))
            h, w, _ = imgCurrent.shape
            imgCurrent[0:self.hs, w - self.ws: w] = imgSmall

            cv2.imshow("Slides", imgCurrent)
            cv2.imshow("Image", img)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

if __name__ == "__main__":
    folderPath = "Presentation"
    presentationController = PresentationController(folderPath)
    presentationController.run()

