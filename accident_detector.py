import cv2
import numpy as np
import imutils
import os
import json  # Added this import
from datetime import datetime

class AccidentDetector:
    def __init__(self, config_file="config.json"):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            detection_config = config['detection']
            self.min_contour_area = detection_config['min_contour_area']
            self.threshold_sensitivity = detection_config['threshold_sensitivity']
            self.accident_frames_threshold = detection_config['accident_frames_threshold']
        except:
            # Default settings if config file is missing
            self.min_contour_area = 500
            self.threshold_sensitivity = 25
            self.accident_frames_threshold = 5
        
        self.previous_frame = None
        self.accident_detected = False
        self.consecutive_accident_frames = 0
    
    def detect_accident(self, frame):
        if self.accident_detected:
            return True
            
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if self.previous_frame is None:
            self.previous_frame = gray
            return False
        
        # Calculate the difference between current and previous frame
        frame_diff = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_diff, self.threshold_sensitivity, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours in the thresholded image
        contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        
        # Check for significant motion
        significant_motion = False
        motion_area = 0
        for contour in contours:
            contour_area = cv2.contourArea(contour)
            motion_area += contour_area
            if contour_area > self.min_contour_area:
                significant_motion = True
        
        # Update previous frame
        self.previous_frame = gray
        
        # Check for consecutive frames with significant motion (potential accident)
        if significant_motion and motion_area > self.min_contour_area * 2:
            self.consecutive_accident_frames += 1
            if self.consecutive_accident_frames >= self.accident_frames_threshold:
                self.accident_detected = True
                return True
        else:
            self.consecutive_accident_frames = max(0, self.consecutive_accident_frames - 1)
            
        return False
    
    def capture_screenshot(self, frame, video_name, timestamp):
        # Create screenshots directory if it doesn't exist
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        
        # Format filename
        safe_video_name = "".join(c for c in video_name if c.isalnum() or c in (' ', '.', '_')).rstrip()
        timestamp_str = timestamp.replace(':', '-')
        filename = f"screenshots/accident_{safe_video_name}_{timestamp_str}.jpg"
        
        # Save the frame
        cv2.imwrite(filename, frame)
        return filename
    
    def reset(self):
        self.previous_frame = None
        self.accident_detected = False
        self.consecutive_accident_frames = 0