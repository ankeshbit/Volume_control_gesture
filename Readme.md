# Hand Gesture Volume Control 🎛️

A Python-based computer vision project that allows you to control your system's volume using hand gestures through a webcam. The program detects the distance between the thumb and index finger and adjusts the system volume accordingly in real time.

## Features

* Real-time hand tracking using **MediaPipe**
* Webcam video processing using **OpenCV**
* Dynamic volume control using **PyCAW**
* Visual volume bar and percentage display
* Simple gesture-based interaction (thumb–index distance)

## How It Works

The program uses MediaPipe to detect hand landmarks from the webcam feed. It specifically tracks the positions of the **thumb tip (landmark 4)** and **index finger tip (landmark 8)**.

1. The distance between the thumb and index finger is calculated.
2. This distance is mapped to the system’s volume range.
3. As the distance increases, the volume increases.
4. As the distance decreases, the volume decreases.
5. A visual volume bar and percentage indicator are displayed on the screen.

## Technologies Used

* Python
* OpenCV
* MediaPipe
* NumPy
* PyCAW
* Computer Vision

## Requirements

Install the required libraries before running the project:

```
pip install opencv-python mediapipe numpy pycaw comtypes
```

## How to Run

1. Clone the repository
2. Install the required dependencies
3. Run the Python script

```
python volume_control.py
```

4. Show your hand to the webcam and move your **thumb and index finger** closer or farther apart to control the system volume.

## Controls

* Increase distance between thumb and index finger → Increase volume
* Decrease distance between thumb and index finger → Decrease volume
* Press **ESC** to exit the program

## Use Cases

* Touchless computer control
* Computer vision learning projects
* Human-computer interaction experiments
* Beginner AI/ML portfolio project

## Author

Created as a computer vision project using Python and MediaPipe.
