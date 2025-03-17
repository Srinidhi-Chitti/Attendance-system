import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import json
from datetime import date

class AttendanceApp:
    def __init__(self, master):
        self.master = master
        master.title("QR Attendance System")
        master.geometry("800x600")

        self.today = str(date.today())
        self.attendance = {}
        self.load_attendance()

        # Configure styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=('Arial', 10))
        self.style.configure("Header.TLabel", font=('Arial', 12, 'bold'))
        self.style.configure("Present.TLabel", foreground="green")
        self.style.configure("Absent.TLabel", foreground="red")

        # Create main container
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Camera preview panel
        self.camera_frame = ttk.Frame(self.main_frame, width=500)
        self.camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.camera_label = ttk.Label(self.camera_frame)
        self.camera_label.pack()

        # Attendance panel
        self.attendance_frame = ttk.Frame(self.main_frame, width=300)
        self.attendance_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)

        self.header_label = ttk.Label(self.attendance_frame, text="Attendance Status", style="Header.TLabel")
        self.header_label.pack(pady=5)

        self.tree = ttk.Treeview(self.attendance_frame, columns=('Status',), show='headings', height=15)
        self.tree.heading('#0', text='Roll Number')
        self.tree.heading('Status', text='Status')
        self.tree.column('#0', width=150)
        self.tree.column('Status', width=100)
        self.tree.pack(pady=5)

        self.status_label = ttk.Label(self.attendance_frame, text="Ready to scan...", style="Header.TLabel")
        self.status_label.pack(pady=10)

        self.update_treeview()

        # Initialize video capture
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera")
            master.destroy()
            return

        self.scanning = True
        self.update_camera()

        # Quit button
        self.quit_btn = ttk.Button(self.attendance_frame, text="Exit", command=self.on_closing)
        self.quit_btn.pack(pady=10)

    def load_attendance(self):
        try:
            with open(f"{self.today}_attendance.json", "r") as f:
                self.attendance = json.load(f)
        except FileNotFoundError:
            self.attendance = {
                "VU22CSEN0100508": 0,
                "VU22CSEN0101122": 0,
                "VU22CSEN0101443": 0,
                "VU22CSEN0100897": 0,
                "VU22CSEN0100219": 0,
            }
            with open(f"{self.today}_attendance.json", "w") as f:
                json.dump(self.attendance, f)

    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        for roll_no, status in self.attendance.items():
            status_text = "Present" if status else "Absent"
            self.tree.insert('', 'end', text=roll_no, values=(status_text,),
                             tags=('present' if status else 'absent'))
        self.tree.tag_configure('present', foreground='green')
        self.tree.tag_configure('absent', foreground='red')

    def decoder(self, image):
        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        qrCodeDetector = cv2.QRCodeDetector()
        data, bbox, _ = qrCodeDetector.detectAndDecode(image)
        return data if data else None

    def update_camera(self):
        if self.scanning:
            ret, frame = self.cap.read()
            if ret:
                roll_number = self.decoder(frame)
                
                # Convert image for Tkinter
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)
                img.thumbnail((480, 480))
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)

                if roll_number:
                    self.process_attendance(roll_number)

            self.master.after(10, self.update_camera)

    def process_attendance(self, roll_number):
        if roll_number in self.attendance:
            if self.attendance[roll_number] == 0:
                self.attendance[roll_number] = 1
                self.status_label.config(text=f"Attendance marked for\n{roll_number}", foreground="green")
                with open(f"{self.today}_attendance.json", "w") as f:
                    json.dump(self.attendance, f)
                self.update_treeview()
            else:
                self.status_label.config(text=f"{roll_number}\nalready marked", foreground="orange")
        else:
            self.status_label.config(text="Invalid QR Code", foreground="red")

        self.master.after(2000, lambda: self.status_label.config(text="Ready to scan...", foreground="black"))

    def on_closing(self):
        self.scanning = False
        if self.cap.isOpened():
            self.cap.release()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()