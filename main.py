import cv2
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading
import time

# Import our custom modules
try:
    from accident_detector import AccidentDetector
    from email_sender import EmailSender
except ImportError as e:
    print(f"Import error: {e}. Using fallback classes.")
    # Create simple fallback classes if imports fail
    class AccidentDetector:
        def __init__(self, config_file="config.json"):
            self.min_contour_area = 500
            self.threshold_sensitivity = 25
            self.accident_frames_threshold = 5
            self.previous_frame = None
            self.accident_detected = False
            self.consecutive_accident_frames = 0
        
        def detect_accident(self, frame):
            # Simple motion detection logic
            if self.accident_detected:
                return True
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if self.previous_frame is None:
                self.previous_frame = gray
                return False
            
            frame_diff = cv2.absdiff(self.previous_frame, gray)
            _, thresh = cv2.threshold(frame_diff, self.threshold_sensitivity, 255, cv2.THRESH_BINARY)
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            # Fixed contour detection
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            significant_motion = False
            for contour in contours:
                if cv2.contourArea(contour) > self.min_contour_area:
                    significant_motion = True
                    break
            
            self.previous_frame = gray
            
            if significant_motion:
                self.consecutive_accident_frames += 1
                if self.consecutive_accident_frames >= self.accident_frames_threshold:
                    self.accident_detected = True
                    return True
            else:
                self.consecutive_accident_frames = max(0, self.consecutive_accident_frames - 1)
                
            return False
        
        def capture_screenshot(self, frame, video_name, timestamp):
            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            
            safe_video_name = "".join(c for c in video_name if c.isalnum() or c in (' ', '.', '_')).rstrip()
            timestamp_str = timestamp.replace(':', '-')
            filename = f"screenshots/accident_{safe_video_name}_{timestamp_str}.jpg"
            
            cv2.imwrite(filename, frame)
            return filename
        
        def reset(self):
            self.previous_frame = None
            self.accident_detected = False
            self.consecutive_accident_frames = 0

    class EmailSender:
        def __init__(self, config_file="config.json"):
            self.sender = "accident.alert.system00@gmail.com"
            self.recipient = "singhpunitice00@gmail.com"
        
        def send_alert(self, video_name, timestamp, screenshot_path=None):
            print(f"SIMULATION: Would send email to {self.recipient} about accident in {video_name} at {timestamp}")
            if screenshot_path:
                print(f"Screenshot saved at: {screenshot_path}")
            return True

class AccidentDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Accident Detection System")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize detector and email sender
        self.detector = AccidentDetector()
        self.email_sender = EmailSender()
        
        self.video_path = None
        self.cap = None
        self.playing = False
        self.processing_thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="Accident Detection System", 
                              font=("Arial", 20, "bold"), bg="#f0f0f0", fg="#2c3e50")
        title_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(main_frame, 
                               text="Upload a video file to detect accidents. The system will send an email alert to singhpunitice00@gmail.com when an accident is detected.",
                               font=("Arial", 10), bg="#f0f0f0", fg="#34495e", wraplength=600)
        instructions.pack(pady=5)
        
        # Upload section
        upload_frame = tk.Frame(main_frame, bg="#f0f0f0")
        upload_frame.pack(pady=15, fill=tk.X)
        
        upload_btn = tk.Button(upload_frame, text="Upload Video", command=self.upload_video,
                              font=("Arial", 12), bg="#3498db", fg="white", padx=15, pady=8)
        upload_btn.pack(side=tk.LEFT)
        
        self.video_path_label = tk.Label(upload_frame, text="No video selected", 
                                        font=("Arial", 10), bg="#f0f0f0", fg="#7f8c8d")
        self.video_path_label.pack(side=tk.LEFT, padx=20)
        
        # Control buttons
        control_frame = tk.Frame(main_frame, bg="#f0f0f0")
        control_frame.pack(pady=15)
        
        self.play_btn = tk.Button(control_frame, text="Start Detection", command=self.toggle_play,
                                 font=("Arial", 12), bg="#2ecc71", fg="white", padx=15, pady=8, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(control_frame, text="Stop", command=self.stop_video,
                                 font=("Arial", 12), bg="#e74c3c", fg="white", padx=15, pady=8, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Video display
        video_frame = tk.Frame(main_frame, bg="#2c3e50", relief=tk.SUNKEN, bd=2)
        video_frame.pack(pady=15, fill=tk.BOTH, expand=True)
        
        self.video_label = tk.Label(video_frame, text="Video will appear here", 
                                   bg="black", fg="white", font=("Arial", 12))
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Status section
        status_frame = tk.Frame(main_frame, bg="#f0f0f0")
        status_frame.pack(pady=15, fill=tk.X)
        
        status_title = tk.Label(status_frame, text="Status:", 
                               font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#2c3e50")
        status_title.pack(anchor=tk.W)
        
        self.status_label = tk.Label(status_frame, text="Ready to upload video", 
                                   font=("Arial", 11), bg="#f0f0f0", fg="#34495e")
        self.status_label.pack(anchor=tk.W, pady=5)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=600)
        self.progress.pack(fill=tk.X, pady=5)
        
        # Footer
        footer = tk.Label(main_frame, text="Emails will be sent to: singhpunitice00@gmail.com", 
                         font=("Arial", 9), bg="#f0f0f0", fg="#7f8c8d")
        footer.pack(side=tk.BOTTOM, pady=10)
    
    def upload_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.video_path = file_path
            self.video_path_label.config(text=os.path.basename(file_path))
            self.status_label.config(text="Video loaded. Click 'Start Detection' to begin.")
            self.play_btn.config(state=tk.NORMAL)
            self.stop_video()
    
    def toggle_play(self):
        if not self.video_path:
            messagebox.showerror("Error", "Please upload a video first")
            return
        
        if self.playing:
            self.playing = False
            self.play_btn.config(text="Resume Detection", bg="#2ecc71")
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.playing = True
            self.play_btn.config(text="Pause Detection", bg="#f39c12")
            self.stop_btn.config(state=tk.NORMAL)
            
            # Start processing in a separate thread
            if not self.processing_thread or not self.processing_thread.is_alive():
                self.processing_thread = threading.Thread(target=self.process_video)
                self.processing_thread.daemon = True
                self.processing_thread.start()
    
    def stop_video(self):
        self.playing = False
        self.play_btn.config(text="Start Detection", bg="#2ecc71", state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_label.config(image='', text="Video will appear here")
        self.status_label.config(text="Video stopped")
        self.detector.reset()
        self.progress.stop()
    
    def process_video(self):
        # Initialize video capture
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open video file")
            self.stop_video()
            return
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = 0
        self.accident_detected = False
        self.status_label.config(text="Processing video...")
        self.progress.start()
        
        video_name = os.path.basename(self.video_path)
        
        while self.playing:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            self.frame_count += 1
            timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Current timestamp in seconds
            
            # Detect accident in the current frame
            if not self.accident_detected and self.detector.detect_accident(frame):
                self.accident_detected = True
                self.progress.stop()
                
                # Format timestamp for display and email
                mins = int(timestamp // 60)
                secs = int(timestamp % 60)
                formatted_timestamp = f"{mins:02d}:{secs:02d}"
                
                # Capture screenshot
                screenshot_path = self.detector.capture_screenshot(frame, video_name, formatted_timestamp)
                
                # Update status
                self.status_label.config(text=f"Accident detected at {formatted_timestamp}! Sending email...")
                
                # Send email alert
                email_sent = self.email_sender.send_alert(video_name, formatted_timestamp, screenshot_path)
                
                if email_sent:
                    self.status_label.config(text=f"Accident detected at {formatted_timestamp}! Email sent to singhpunitice00@gmail.com")
                else:
                    self.status_label.config(text=f"Accident detected at {formatted_timestamp}! But failed to send email.")
            
            # Display the frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail((800, 500))
            img_tk = ImageTk.PhotoImage(img)
            
            self.video_label.config(image=img_tk, text="")
            self.video_label.image = img_tk
            
            # Control playback speed
            time.sleep(0.03)  # Adjust for reasonable playback speed
        
        # Video ended
        if not self.accident_detected:
            self.status_label.config(text="Video processing completed. No accident detected.")
        self.progress.stop()
        self.stop_video()

# Create and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = AccidentDetectionApp(root)
    root.mainloop()