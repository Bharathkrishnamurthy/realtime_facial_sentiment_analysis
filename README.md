AI Proctoring System (Real-Time Monitoring)
📌 Project Overview

This project is a real-time AI-based proctoring system built to monitor online examinations or assessments.
It uses computer vision and deep learning to detect suspicious activities such as the use of electronic devices or the presence of multiple people.

The system shows a clean live video feed and generates a detailed report after the session ends.

🎯 Key Objectives

Monitor candidates during online exams

Detect electronic devices (mobile, laptop, tablet, etc.)

Detect multiple faces or absence of face

Avoid showing confidence or predictions during live monitoring

Generate an unbiased and professional final report

🧠 Technologies Used

Python

Streamlit – for web interface

OpenCV – for webcam and face detection

YOLOv8 – for object detection

SQLite – for logging session data

NumPy & Pandas – for analysis and reporting

⚙️ System Features
🔴 Live Monitoring

Real-time webcam feed

Face detection using Haar Cascade

Object detection for malpractice-related devices

No confidence scores or labels shown on screen

Neutral bounding boxes only

📱 Malpractice Detection

Detects the following electronic devices:

Mobile phone

Laptop

Tablet

Headphones

Remote control

Multiple devices in the same frame are treated as a malpractice event.

📄 Final Proctoring Report

Generated after monitoring stops:

Session duration

Multiple face detection count

No-face detection count

Electronic device detection summary

Multiple device events

Overall detection confidence score

Professional confidence disclosure

🔒 Confidence Handling (Important Design Choice)

Confidence scores are hidden during live monitoring

Confidence is calculated in the backend

Final confidence is shown only in the report

This avoids bias and misleading real-time interpretation

📂 Project Structure
realtime_proctoring_system/
│
├── app.py                    # Streamlit application
├── object_detection.py       # YOLO-based object detection
├── generate_report.py        # Offline report generation
├── logs/
│   └── emotion_logs.db       # SQLite database
├── models/
│   └── yolov8n.pt
└── README.md

▶️ How to Run the Project
1️⃣ Install dependencies
pip install streamlit opencv-python ultralytics pandas numpy

2️⃣ Start the application
streamlit run app.py

3️⃣ Generate offline report (optional)
python generate_report.py

📊 Overall Detection Confidence

Calculated as the average of frame-level object detection confidence

Displayed only in the final report

Helps in audit and review without affecting live monitoring

🎓 Academic / Viva Explanation

“Live confidence scores are intentionally suppressed to avoid bias.
All detections are logged per frame and aggregated into a final report that includes an overall detection confidence.”

✅ Advantages of This System

Real-time monitoring

Bias-free evaluation

Professional reporting

Scalable and modular design

Suitable for academic projects and demos

🚀 Future Enhancements

PDF report export

Evidence image capture

Emotion analysis summary

Confidence trend charts

Multi-person tracking timeline