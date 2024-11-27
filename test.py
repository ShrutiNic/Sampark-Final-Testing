import can
import time
import binascii
import sys
import requests
from PyQt5.QtWidgets import QMainWindow, QApplication
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
        self.ICCID = None
        self.status = True
        self.URL = "http://192.168.2.253:6101/api/stage5"

        # Initialize CAN bus in the __init__ method to avoid reinitializing it every time
        self.initialize_can_bus()

    def initialize_can_bus(self):
        try:
            # Initialize the bus once, not inside each function
            self.bus = can.interface.Bus(interface='pcan', channel='PCAN_USBBUS1', bitrate=250000)
            print(f"CAN Bus initialized: {self.bus.channel_info}")
        except can.CanError as e:
            print(f"Error initializing CAN bus: {str(e)}")
            self.bus = None  # Set bus to None if there's an initialization error

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
                message = self.bus.recv(timeout=2)  # 1 second timeout for each frame
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

                  myobj = {'IMEI': IMEI_ascii}
                  headers = {'Content-Type': 'application/json'}  # Ensure correct headers
                  x = requests.put(self.URL, json=myobj, headers=headers,)

                  # Handle the response
                  if x.status_code == 200:
                    print("POST request successful!")
                    print(x.text)  # Print the response from the server
                  else:
                    print(f"POST request failed with status code {x.status_code}: {x.text}")
 
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
                  ICCID_ascii = ICCID.decode('ascii')  # Decode bytes into ASCII string
                  print(f"Extracted IMEI (ASCII): {ICCID_ascii}")
                  self.ui.ICCID_input.setPlainText(ICCID_ascii)
 
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

   
    

# Entry point of the program
if __name__ == "__main__":
    app = QApplication(sys.argv)    
    # Create an instance of the MyClass class
    processor = MyClass()
    processor.show()

    # Define CAN IDs to be processed
    can_ids = (0x100,0x101)  # You can modify this list to include other CAN IDs
    
    # Process CAN IDs sequentially
    processor.process_can_ids(can_ids)
    
    sys.exit(app.exec_())
