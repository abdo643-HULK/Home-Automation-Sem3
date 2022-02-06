#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Face and body recognition code
"""

import time
import sys
import signal

### external dependecies ###

# used for the detection
# https://docs.opencv.org/4.x/d2/d75/namespacecv.html
import cv2

# needed by opencv
# https://numpy.org/doc/stable/
import numpy

# used fto call our webhook
# https://docs.python-requests.org/en/latest/
import requests

from queue import Queue
from typing import List, Tuple
from threading import Thread, Event

__all__ = []
__version__ = '1.0'
__author__ = "Shehata Abd El Rahaman, Milosavljevic Marko, Züger Lukas"

TIME_WINDOW = 5
"""
the time window to gather information about how 
often a person was detected
"""

FRAME_SIZE = (320, 240)
"""The size the input frame gets resized to"""

DISPLAY_OUTPUT = False
"""To be able to use `detect_and_show` this needs to be true """

# global variables before we started adding threads
# thismodule = sys.modules[__name__]
# thismodule.is_person_in_room = False
# thismodule.last_toggle = time.time()
# thismodule.in_room = numpy.full(TIME_WINDOW + 1, False)
# thismodule.in_room_length = len(thismodule.in_room)

# loads the cascade file to detect faces
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# hog = cv2.HOGDescriptor((48,96), (16,16), (8,8), (8,8), 9)
# hog.setSVMDetector(cv2.HOGDescriptor_getDaimlerPeopleDetector())

video = cv2.VideoCapture(0)

if DISPLAY_OUTPUT:
    cv2.startWindowThread()
    cv2.namedWindow("output")


class WebhookThread(Thread):
    """
    The class is responsible for sending caculating if
    there was a change since the last time window and if so
    send a reuest to the home assistant with the help of a webhook

    Attributes
    ----------
    queue
        The message queue

    Methods
    -------
    stop()
        sets an interal flag to stop the thread
    stopped()
        returns if the stop flag was set or not
    """

    # our custom event to stop the thread
    _stop_event = Event()
    _is_person_in_room = False

    def __init__(self, queue: Queue, *args, **keywords):
        """initalized the queue and sets the thread name to that of the class"""
        super(WebhookThread, self).__init__(*args, **keywords)
        self.queue = queue
        self.setName("WebhookThread")

    def run(self) -> None:
        """Waits for a message and calculates if there was a change and sends a message to the webhook"""
        while True:
            in_room = self.queue.get()
            if self.stopped():
                break

            number_of_opposits = len(
                [*filter(lambda x: x != self._is_person_in_room, in_room)])

            if (number_of_opposits > (TIME_WINDOW + 1) * 0.7):
                self._is_person_in_room = not self._is_person_in_room
                toggle_environment(self._is_person_in_room)

        print(f"{self.getName()} closing")

    def stop(self) -> None:
        """kills the thread by setting the stop_event flag"""
        self._stop_event.set()
        self.queue.put(0)

    def stopped(self) -> bool:
        """checks if the stop flag was set"""
        return self._stop_event.is_set()


def toggle_environment(is_person_in_room: bool) -> None:
    """calls our webhook with the provided param

        Parameters
        ----------
        is_person_in_room
            the param to send as json to the webhook
    """
    try:
        # the webhook url to call to toggle the devices
        # https://www.home-assistant.io/docs/automation/trigger/#webhook-trigger
        URL = "http://homeassistant.local:8123/api/webhook/room"

        json = {
            "person_in_room": str(is_person_in_room).lower()
        }

        requests.post(URL, json=json)
    except Exception as err:
        print(err)


def detect_and_show(frame: numpy.ndarray, bodies: List[Tuple[float, ...]], faces: List[Tuple[float, ...]]) -> Tuple[numpy.ndarray, bool]:
    """Draws rectangles in the frame where openvc detected a face or a body

        Parameters
        ----------
        frame
            the frame that was captured
        bodies
            the list of coordinates where the bodies where detected
        faces
            the list of coordinates where the faces where detected

        Returns
        -------
        tuple
            contains the frame with the drawings and a boolean to indicate if a person was found
    """

    facesCnt = 1
    personCnt = 1
    person_in_room = False

    for x, y, w, h in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
        facesCnt += 1
        person_in_room = True

    for x, y, w, h in bodies:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f'person {personCnt}', (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        personCnt += 1
        person_in_room = True

    print("Faces count:", personCnt)
    print("Person count:", facesCnt)

    cv2.putText(frame, 'Status : Detecting ', (40, 40),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 0, 0), 2)
    cv2.putText(frame, f'Total Persons : {personCnt}',
                (40, 70), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 0, 0), 2)
    cv2.putText(frame, f'Total Faces : {facesCnt}',
                (40, 100), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 0, 0), 2)
    cv2.imshow('output', frame)

    return (frame, person_in_room)


def detect(frame: numpy.ndarray, bodies: List[Tuple[float, ...]], faces: List[Tuple[float, ...]]) -> Tuple[numpy.ndarray, bool]:
    """Checks if a face or body was detected and returns the result

        The function doesn't need the frame but to make it compatible with the `detect_and_show` 
        we took the same function signature

        Parameters
        ----------
        frame
            the frame that was captured
        bodies
            the list of coordinates where the bodies where detected
        faces
            the list of coordinates where the faces where detected

        Returns
        -------
        tuple
            contains the passed in frame and a boolean to indicate if a person was found
    """
    person_in_room = False

    # we only need to detect one of them to count it as a person
    if len(bodies) > 0 or len(faces) > 0:
        person_in_room = True

    return (frame, person_in_room)


def run_detection(queue: Queue) -> None:
    """
    Runs the face/body detection code in a loop.
    On each rotation we get the time difference between the last comparison in 
    the specified time window to detect how often we detected someone or not.
    For each second we save the result and after the time window has passed
    we send that array to be processed on another thread.
    """

    in_room = numpy.full(TIME_WINDOW + 1, False)
    last_toggle = time.time()

    while True:
        _, frame = video.read()
        # because we get a frame with the resolution of the camera,
        # it needs to be resized so the device can process it in a
        # reasonable amount of time
        frame = cv2.resize(frame, FRAME_SIZE)

        # detect people in the image
        # returns the bounding bodies for the detected objects
        (bodies, _) = hog.detectMultiScale(
            frame, winStride=(8, 8), padding=(16, 16), scale=1.1)
        # does the same thing but for faces
        faces = face_cascade.detectMultiScale(
            frame, scaleFactor=1.02, minNeighbors=5)

        (frame, person_in_room) = detect(frame, bodies, faces)

        diff = int(time.time() - last_toggle)

        in_room[diff] = person_in_room

        # just for debugging
        print(diff, person_in_room)

        # can be changed to be event based interval and by that remove a branch and
        # let the os/language call the provided callback
        if (diff >= TIME_WINDOW):
            last_toggle = time.time()
            queue.put(in_room)

        # We wait 1ms for a keypress and if you detect the user pressed "q" quit
        # The "&" is a precaution for os behaviour: https://stackoverflow.com/questions/57690899/how-cv2-waitkey1-0xff-ordq-works
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def main() -> None:
    # We use message passing (Actor Model) for multithreading and a queue is perfect for this.
    # If we would use more threads we would create one for each
    webhook_queue = Queue()
    webhook_thread = WebhookThread(webhook_queue)

    def clean_up() -> None:
        print()
        # openvc cleanup
        video.release()
        cv2.destroyAllWindows()
        # thread cleanup
        webhook_thread.stop()
        webhook_thread.join()

        # app cleaned so close with success
        sys.exit(0)

    # Listen for Ctrl+C and clean up
    signal.signal(signal.SIGINT, lambda *_: clean_up())

    webhook_thread.start()
    # start the detction loop
    run_detection(webhook_queue)
    clean_up()


if __name__ == '__main__':
    main()
