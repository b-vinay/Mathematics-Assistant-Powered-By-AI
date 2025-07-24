from flask import Flask, render_template, Response, jsonify,request
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import google.generativeai as genai
from dotenv import load_dotenv
import os
from PIL import Image
import io
import base64

load_dotenv()  
genai.configure(api_key="AIzaSyAYSPoLsk5zyVvIWTZIzXl3iyGTL8kVhcg")
model = genai.GenerativeModel('gemini-2.0-flash')

app = Flask(__name__)

# Initialize OpenCV & MediaPipe
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)  # Capture from webcam

# Color choices
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)]
colorIndex = 0

# Drawing storage
bpoints, gpoints, rpoints, ypoints = [deque(maxlen=1024)], [deque(maxlen=1024)], [deque(maxlen=1024)], [deque(maxlen=1024)]
blue_index, green_index, red_index, yellow_index = 0, 0, 0, 0

# Initialize current_canvas as a black canvas
current_canvas = np.zeros((480, 640, 3), dtype=np.uint8)

def generate_frames():
    global blue_index, green_index, red_index, yellow_index, colorIndex,current_canvas

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(framergb)
        canvas = np.ones_like(frame) * 255

        # Draw UI buttons
        frame = cv2.rectangle(frame, (40, 1), (140, 65), (0, 0, 0), 2)
        frame = cv2.rectangle(frame, (160, 1), (255, 65), (255, 0, 0), 2)
        frame = cv2.rectangle(frame, (275, 1), (370, 65), (0, 255, 0), 2)
        frame = cv2.rectangle(frame, (390, 1), (485, 65), (0, 0, 255), 2)
        frame = cv2.rectangle(frame, (505, 1), (600, 65), (0, 255, 255), 2)
        cv2.putText(frame, "CLEAR", (49, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        cv2.putText(frame, "BLUE", (185, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        cv2.putText(frame, "GREEN", (298, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        cv2.putText(frame, "RED", (420, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        cv2.putText(frame, "YELLOW", (520, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        if result.multi_hand_landmarks:
            landmarks = []
            for handslms in result.multi_hand_landmarks:
                for lm in handslms.landmark:
                    lmx, lmy = int(lm.x * 640), int(lm.y * 480)
                    landmarks.append([lmx, lmy])

                mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)

            fore_finger, thumb = (landmarks[8][0], landmarks[8][1]), (landmarks[4][0], landmarks[4][1])
            cv2.circle(frame, fore_finger, 3, (0, 255, 0), -1)

            if fore_finger[1] <= 65:
                if 40 <= fore_finger[0] <= 140:
                    bpoints.clear(); gpoints.clear(); rpoints.clear(); ypoints.clear()
                    bpoints.append(deque(maxlen=1024)); gpoints.append(deque(maxlen=1024))
                    rpoints.append(deque(maxlen=1024)); ypoints.append(deque(maxlen=1024))
                    blue_index = green_index = red_index = yellow_index = 0
                elif 160 <= fore_finger[0] <= 255:
                    colorIndex = 0
                elif 275 <= fore_finger[0] <= 370:
                    colorIndex = 1
                elif 390 <= fore_finger[0] <= 485:
                    colorIndex = 2
                elif 505 <= fore_finger[0] <= 600:
                    colorIndex = 3

            elif (thumb[1] - fore_finger[1] < 30):
                bpoints.append(deque(maxlen=1024)); blue_index += 1
                gpoints.append(deque(maxlen=1024)); green_index += 1
                rpoints.append(deque(maxlen=1024)); red_index += 1
                ypoints.append(deque(maxlen=1024)); yellow_index += 1
            else:
                if colorIndex == 0:
                    bpoints[blue_index].appendleft(fore_finger)
                elif colorIndex == 1:
                    gpoints[green_index].appendleft(fore_finger)
                elif colorIndex == 2:
                    rpoints[red_index].appendleft(fore_finger)
                elif colorIndex == 3:
                    ypoints[yellow_index].appendleft(fore_finger)

        else:
            bpoints.append(deque(maxlen=1024)); blue_index += 1
            gpoints.append(deque(maxlen=1024)); green_index += 1
            rpoints.append(deque(maxlen=1024)); red_index += 1
            ypoints.append(deque(maxlen=1024)); yellow_index += 1

        # Draw the stored points
        points = [bpoints, gpoints, rpoints, ypoints]
        for i in range(len(points)):
            for j in range(len(points[i])):
                for k in range(1, len(points[i][j])):
                    if points[i][j][k - 1] is None or points[i][j][k] is None:
                        continue
                    cv2.line(frame, points[i][j][k - 1], points[i][j][k], colors[i], 2)
                    cv2.line(canvas, points[i][j][k - 1], points[i][j][k], colors[i], 2)


        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        current_canvas = canvas.copy()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/analyze_canvas', methods=['GET'])
def analyze_canvas():
    global current_canvas  # Declare we're using the global variable
    
    try:
        # Check if canvas exists
        if 'current_canvas' not in globals():
            return jsonify({"error": "Canvas not initialized"}), 400
            
        # Make sure canvas is not empty
        if current_canvas is None or current_canvas.size == 0:
            return jsonify({"error": "Canvas is empty"}), 400

        # Convert canvas to PNG
        success, image_bytes = cv2.imencode('.png', current_canvas)
        if not success:
            return jsonify({"error": "Failed to encode image"}), 500

        image_bytes = image_bytes.tobytes()
        
        # Get response from Gemini
        response = model.generate_content([
            "You are a mathematical problem solver. Given a mathematical problem, provide a step-by-step solution in a detailed and structured manner. Explain each step clearly to ensure easy understanding. If an image is provided, first extract the text using OCR before solving. Format the response neatly using equations where necessary. Use this format:\n\nStep 1: Identify the numbers and operators\nStep 2: Perform the calculation\nAnswer: [Final result]\n\n\nUse clear spacing and avoid special characters like $ or \\.  ",
            {"mime_type": "image/png", "data": image_bytes}
        ])
        result = (response.text).replace("[**]*", "")  
        return jsonify({
            "response": result,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route("/ai_board")
def ai_board():
    return render_template("ai_board.html")



@app.route('/solve', methods=['POST'])
def solve():
    image_file = request.files['image']
    image = Image.open(image_file)

    # Convert image to bytes
    img_io = io.BytesIO()
    image.save(img_io, format='PNG')
    image_bytes = img_io.getvalue()

    # Send to Gemini for processing
    response = model.generate_content([
        "You are a mathematical problem solver. Given a mathematical problem, provide a step-by-step solution in a detailed and structured manner. Explain each step clearly to ensure easy understanding. If an image is provided, first extract the text using OCR before solving. Format the response neatly using equations where necessary. Use this format:\n\nStep 1: Identify the numbers and operators\nStep 2: Perform the calculation\nAnswer: [Final result]\n\n\nUse clear spacing and avoid special characters like $ or \\.  ",
            {"mime_type": "image/png", "data": image_bytes}
    ])

    result = response.text.strip()

    return jsonify({
        'result': result,
        'status': 'success'
    })

if __name__ == '__main__':
    app.run(debug=True)
