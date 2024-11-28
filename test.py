import can
import time
import binascii
import sys
import requests
import datetime
from datetime import datetime, timedelta,timezone
import scratch_3
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer

from mainwindow import Ui_MainWindow

# Expected CAN IDs and their frame counts
expected_frame_counts = {0x100: 3, 0x101 :3}

# Initialize received_frames with empty lists for each CAN ID
received_frames = {0x100: [],0x101 : []}

class MyClass(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize the CAN bus connection (initialize once here)
        self.bus = None
        self.busy = False  # Flag to track whether the system is busy processing a CAN ID
        self.IMEI_ascii = None
        self.ICCID_ascii = None
        #self.status = True
        self.ui.pushButton_2.setEnabled(False)
        self.URL = "http://192.168.2.253:6101/api/stage5"
        self.stage4_url = "http://192.168.2.253:6101/api/stage4"
        self.ui.pushButton.clicked.connect(self.send_data)
        self.ui.barcode_Input.textChanged.connect(self.on_barcode_text_changed)
        self.barcode_checked = False
        self.timer = QTimer(self)  # Initialize QTimer for delayed barcode check
        self.timer.timeout.connect(self.check_barcode)  # Connect the timer to the check_barcode function
        self.barcode_text = ""
        # Initialize CAN bus in the __init__ method to avoid reinitializing it every time
        self.initialize_can_bus()

        self.data = {
            "QR_code": "SENSOR926",
            "final_testing_status": True,
            "IMEI": self.IMEI_ascii,
            "ICCID": "89911234567890123456",
            "SystemRtc": "2024-03-21 15:30:45",

            "AppFWVersion": "1.0.5",

            "BLFWVersion": "2.1.0",

            "GPSFWVersion": "3.2.1",

            "GSMFWVersion": "4.0.2",

            "HWVersion": "V2.0",

            "GPSFix": "3D Fix",

            "HDOP": "1.2",

            "PDOP": "2.4",

            "No_satelite": "8",

            "GSMStatus": "Connected",

            "signalStrength": "-67",

            "Network_code": "40414",

            "Network_Type": "4G",

            "SIM": "Active",

            "MEMS": "Working",

            "Voltage": "12.5",

            "Memory": "75",

            "Ignition": "ON",

            "Tamper": "No",

            "DI_1_H": "1",

            "DI_1_L": "0",

            "DI_2_H": "1",

            "DI_2_L": "0",

            "DI_3_H": "1",

            "DI_3_L": "0",

            "DO_1_H": "1",

            "DO_1_L": "0",

            "DO_2_H": "1",

            "DO_2_L": "0",

            "CAN": "OK",

            "RS485": "Connected",

            "AnalogInput1": "4.5",

            "AnalogInput2": "3.2",

        }

 

        self.headers = {"Content-Type": "application/json"}




    def initialize_can_bus(self):
        try:
            # Initialize the bus once, not inside each function
            self.bus = can.interface.Bus(interface='pcan', channel='PCAN_USBBUS1', bitrate=250000)
            print(f"CAN Bus initialized: {self.bus.channel_info}")
        except can.CanError as e:
            print(f"Error initializing CAN bus: {str(e)}")
            self.bus = None  # Set bus to None if there's an initialization error

    def on_barcode_text_changed(self):
        # Get the current barcode text from the input field
        barcode = self.ui.barcode_Input.toPlainText().replace(" ", "")  # Remove all spaces

        print(f"Barcode detected: {barcode}")

        # If the barcode is changing and is not being checked yet
        if barcode != self.barcode_text:  # Only proceed if the barcode text is different from the last one
            self.barcode_text = barcode  # Update the stored barcode text
            self.timer.start(1000)  # Start or restart the timer for 1-second delay
            self.barcode_checked = False  # Reset the checked flag


    def check_barcode(self):
        print('Barcode check function called')

        barcode = self.ui.barcode_Input.toPlainText().strip()  # Remove any leading/trailing whitespaces
        print(f"Final Barcode: {barcode}")

        # Check if the barcode has a valid length or format (adjust according to your needs)
        if barcode and len(barcode) >= 11:  # You can add a length check here
            # Call API or do necessary actions
            response = requests.put(self.stage4_url, json=self.data, headers=self.headers)
            print(response)
            if response.status_code == 200:
                print('Barcode data scanned successfully')
                self.ui.pushButton_2.setEnabled(True)
            else:
                print('Error reading barcode')
        else:
            print('No valid barcode data scanned')

        # Reset the flag for the next barcode scan
        self.barcode_checked = False
        self.timer.stop()  # Stop the timer after processing the barcode


    # Function to process CAN ID 0x100
    def fun_0x100(self):
        if self.busy:  # Check if the system is busy
            print("System is busy, please wait...")
            return
 
        if self.bus is None:  # Check if the bus was initialized properly
            print("CAN Bus not initialized. Cannot send message.")
            return
 
        self.busy = True  # Mark the system as busy
        try:
            msg = can.Message(arbitration_id=0x100, data=[0, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False)
           
            # Send the message
            self.bus.send(msg)
            print(f"Message sent on {self.bus.channel_info}")
 
            # Wait for the response
            for i in range(expected_frame_counts[0x100]):
                message = self.bus.recv(timeout=2)  # 2 second timeout for each frame
                if message:
                    print(f"Received message from CAN ID {hex(message.arbitration_id)}: {message.data.hex()}")
                    received_frames[0x100].append(message)
                else:
                    print(f"Timeout waiting for message for CAN ID 0x100. No response received.")
 
            # Check if we have received all expected frames for 0x100
            if len(received_frames[0x100]) == expected_frame_counts[0x100]:
                frames = received_frames[0x100]
                frames.sort(key=lambda x: x.data[0])  # Sort by sequence number
                complete_message = b''.join(frame.data[1:] for frame in frames)
                print(f"Reassembled message for CAN ID 0x100: {complete_message.hex()}")
 
                IMEI = complete_message[:15]
                print(f"Extracted IMEI: {IMEI.hex()}")
 
            
                try:
                  IMEI_ascii = IMEI.decode('ascii')  # Decode bytes into ASCII string
                  print(f"Extracted IMEI (ASCII): {IMEI_ascii}")
                  self.ui.IMIE_input.setPlainText(IMEI_ascii)   

 
                except UnicodeDecodeError:
                  print("Error decoding IMEI to ASCII. The data may contain non-ASCII characters.")
 
            else:
                print(f"Not all frames received for CAN ID 0x100. Expected {expected_frame_counts[0x100]}, but received {len(received_frames[0x100])}.")
 
        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x100].clear()
            print("Frames cleared for CAN ID 0x100")


    def fun_0x101(self):
        if self.busy:  # Check if the system is busy
            print("System is busy, please wait...")
            return
 
        if self.bus is None:  # Check if the bus was initialized properly
            print("CAN Bus not initialized. Cannot send message.")
            return
 
        self.busy = True  # Mark the system as busy
        try:
            msg = can.Message(arbitration_id=0x101, data=[0, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False)
           
            # Send the message
            self.bus.send(msg)
            print(f"Message sent on {self.bus.channel_info}")
 
            # Wait for the response
            for i in range(expected_frame_counts[0x101]):
                message = self.bus.recv(timeout=2)  # 1 second timeout for each frame
                if message:
                    print(f"Received message from CAN ID {hex(message.arbitration_id)}: {message.data.hex()}")
                    received_frames[0x101].append(message)
                else:
                    print(f"Timeout waiting for message for CAN ID 0x100. No response received.")
 
            # Check if we have received all expected frames for 0x100
            if len(received_frames[0x101]) == expected_frame_counts[0x101]:
                frames = received_frames[0x101]
                frames.sort(key=lambda x: x.data[0])  # Sort by sequence number
                complete_message = b''.join(frame.data[1:] for frame in frames)
                print(f"Reassembled message for CAN ID 0x100: {complete_message.hex()}")
 
                ICCID = complete_message[:15]
                print(f"Extracted IMEI: {ICCID.hex()}")
 
            
                try:
                  self.ICCID_ascii = ICCID.decode('ascii')  # Decode bytes into ASCII string
                  print(f"Extracted IMEI (ASCII): {self.ICCID_ascii}")
                  self.ui.ICCID_input.setPlainText(self.ICCID_ascii)
 
                except UnicodeDecodeError:
                  print("Error decoding IMEI to ASCII. The data may contain non-ASCII characters.")
 
            else:
                print(f"Not all frames received for CAN ID 0x100. Expected {expected_frame_counts[0x101]}, but received {len(received_frames[0x101])}.")
 
        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x101].clear()
            print("Frames cleared for CAN ID 0x100")


    def process_can_ids(self, can_ids):
        for can_id in can_ids:
            if self.busy:
                print("System is busy, waiting for previous operation to complete...")
                time.sleep(1)  # Wait for the system to finish the current task
                continue  # Skip to the next iteration if the system is busy

            if can_id == 0x100:
                self.fun_0x100()
                time.sleep(3)
            elif can_id == 0x101:
                self.fun_0x101()
            else:
                print(f"No function defined for CAN ID {hex(can_id)}")


    def send_data(self):
        print('button clicked')
        myobj = {"Status":True,
            "QR_code": "SENSOR965",  # This can be dynamically changed
    "visual_inspection_status": True,
    "visual_inspection_timestamp": {
        "$date": datetime.now(timezone.utc).isoformat()
    },
    "board_flashing_status": True,
    "board_flashing_timestamp": {
        "$date": datetime.now(timezone.utc).isoformat()
    },
    "screw_fitting_status": None,
    "mechanical_fitting_status": None,
    "mechanical_fitting_timestamp": None,
    "final_testing_status": None,
    "final_testing_timestamp": None,
    "IMEI": self.IMEI_ascii,
    "ICCID": "78910",
    "SystemRtc": None,
    "AppFWVersion": "88888",
    "BLFWVersion": None,
    "GPSFWVersion": None,
    "GSMFWVersion": None,
    "HWVersion": None,
    "GPSFix": None,
    "HDOP": None,
    "PDOP": 'xxxxx',
    "No_satelite": None,
    "GSMStatus": 'yyyyy',
    "signalStrength": None,
    "Network_code": None,
    "Network_Type": None,
    "SIM": None,
    "MEMS": None,
    "Voltage": None,
    "Memory": '111111',
    "Ignition": None,
    "Tamper": None,
    "DI_1_H": None,
    "DI_1_L": None,
    "DI_2_H": None,
    "DI_2_L": None,
    "DI_3_H": None,
    "DI_3_L": None,
    "DO_1_H": None,
    "DO_1_L": None,
    "DO_2_H": None,
    "DO_2_L": '22222',
    "CAN": None,
    "RS485": None,
    "AnalogInput1": None,
    "AnalogInput2": None,
    "sticker_printing_status": None,
    "sticker_printing_timestamp": None,
    "last_updated": {
        "$date": datetime.now(timezone.utc).isoformat()
    },
    "UID": None
        }
        headers = {'Content-Type': 'application/json'}  # Ensure correct headers
        x = requests.put(scratch_3.stage5_url, json=myobj, headers=headers,)
        print(x.status_code)

        if x.status_code == 200:
            print("POST request successful!")
            print(x.text)  # Print the response from the server
        else:
            print(f"POST request failed with status code {x.status_code}: {x.text}")


# Entry point of the program
if __name__ == "__main__":
    app = QApplication(sys.argv)    
    # Create an instance of the MyClass class
    processor = MyClass()
    processor.show()

    #calling barcode function first
    #processor.barcode_scan()
    

    # Define CAN IDs to be processed
    can_ids = (0x100,0x101)  # You can modify this list to include other CAN IDs

    # Process CAN IDs sequentially
    processor.process_can_ids(can_ids)
    
    sys.exit(app.exec_())
