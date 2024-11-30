import can
import time
import binascii
import sys
import requests
import datetime
from datetime import datetime, timedelta,timezone
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QTimer
from finalTesting import Ui_MainWindow
import resources_rc

# Expected CAN IDs and their frame counts
expected_frame_counts = {0x100: 3, 0x101 :3, 0x103 : 3, 0x105 :2, 0x106 :3 , 0x115 : 1, 0x116 : 1}

# Initialize received_frames with empty lists for each CAN ID
received_frames = {0x100: [],0x101 : [] , 0x103 :[],0x105 :[],0x106 :[] , 0x115 :[], 0x116 : []}



class MyClass(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.stackedWidget = self.ui.stackedWidget
        self.bus = None
        self.busy = False
        self.ui.pushButton.clicked.connect(self.goToPage2)
        self.ui.pushButton_3.clicked.connect(self.start_functions)
        self.initialize_can_bus()
        self.IMEI_ascii= None
        self.ICCID_ascii = None
        self.appln_ver = None
        self.GSM_ver = None
        self.Gps_ver = None

        # Initialize flags
        self.function100_done = False
        self.function101_done = False
        self.function103_done = False
        self.function105_done = False
        self.function106_done = False
        self.function115_done = False
        self.function116_done = False

        # Timer for delays
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)  # Ensure it only fires once
        self.timer.timeout.connect(self.execute_next_function)

    def initialize_can_bus(self):
        try:
            # Initialize the bus once, not inside each function
            self.bus = can.interface.Bus(interface='pcan', channel='PCAN_USBBUS1', bitrate=250000)
            print(f"CAN Bus initialized: {self.bus.channel_info}")
        except can.CanError as e:
            print(f"Error initializing CAN bus: {str(e)}")
            self.bus = None  # Set bus to None if there's an initialization error

    def start_functions(self):
        """Start the series of functions when the button is clicked."""
        print("Button clicked. Starting functions.")
        
        # Reset flags
        self.function100_done = False
        self.function101_done = False
        self.function103_done = False
        self.function105_done = False
        self.function106_done = False
        self.function115_done = False
        self.function116_done = False
        
        # Call the first function
        self.fun_0x100()

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
                  self.IMEI_ascii = IMEI.decode('ascii')  # Decode bytes into ASCII string
                  print(f"Extracted IMEI (ASCII): {self.IMEI_ascii}")
                  self.ui.IMIE_input.setPlainText(self.IMEI_ascii)
                  self.ui.plainTextEdit_4.appendPlainText(f"IMEI : {self.IMEI_ascii}\n")

                  if len(self.IMEI_ascii) < 15:
                     self.ui.IMIE_input.setStyleSheet("background-color: red;")
                  else:
                      self.ui.IMIE_input.setStyleSheet("background-color: white;")
                  
                except UnicodeDecodeError:
                  print("Error decoding IMEI to ASCII. The data may contain non-ASCII characters.")
 
            else:
                print(f"Not all frames received for CAN ID 0x100. Expected {expected_frame_counts[0x100]}, but received {len(received_frames[0x100])}.")
 
        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x100].clear()
            self.function100_done = True
            time.sleep(2)
            self.execute_next_function()
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
                print(f"Reassembled message for CAN ID 0x101: {complete_message.hex()}")
 
                ICCID = complete_message[:20]
                print(f"Extracted IMEI: {ICCID.hex()}")
 
                try:
                  self.ICCID_ascii = ICCID.decode('ascii')  # Decode bytes into ASCII string
                  print(f"Extracted IMEI (ASCII): {self.ICCID_ascii}")
                  self.ui.ICCID_input.setPlainText(self.ICCID_ascii)
                  self.ui.plainTextEdit_4.appendPlainText(f"ICCID : {self.ICCID_ascii}\n")

                  if len(self.ICCID_ascii)<20:
                      self.ui.ICCID_input.setStyleSheet("background-color: red;")
                  else:
                      self.ui.ICCID_input.setStyleSheet("background-color: white;")
                      
                except UnicodeDecodeError:
                  print("Error decoding IMEI to ASCII. The data may contain non-ASCII characters.")
 
            else:
                print(f"Not all frames received for CAN ID 0x101. Expected {expected_frame_counts[0x101]}, but received {len(received_frames[0x101])}.")
 
        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x101].clear()
            self.function101_done = True
            time.sleep(2)
            self.execute_next_function()
            print("Frames cleared for CAN ID 0x101")

    def fun_0x103(self):
        if self.busy:  # Check if the system is busy
            print("System is busy, please wait...")
            return
 
        if self.bus is None:  # Check if the bus was initialized properly
            print("CAN Bus not initialized. Cannot send message.")
            return
 
        self.busy = True  # Mark the system as busy
        try:
            msg = can.Message(arbitration_id=0x103, data=[0, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False)
           
            # Send the message
            self.bus.send(msg)
            print(f"Message sent on {self.bus.channel_info}")
 
            # Wait for the response
            for i in range(expected_frame_counts[0x103]):
                message = self.bus.recv(timeout=2)  # 1 second timeout for each frame
                if message:
                    print(f"Received message from CAN ID {hex(message.arbitration_id)}: {message.data.hex()}")
                    received_frames[0x103].append(message)
                else:
                    print(f"Timeout waiting for message for CAN ID 0x103. No response received.")
 
            # Check if we have received all expected frames for 0x100
            if len(received_frames[0x103]) == expected_frame_counts[0x103]:
                frames = received_frames[0x103]
                frames.sort(key=lambda x: x.data[0])  # Sort by sequence number
                complete_message = b''.join(frame.data[1:] for frame in frames)
                print(f"Reassembled message for CAN ID 0x100: {complete_message.hex()}")
 
                try:
                  self.appln_ver = complete_message.decode('ascii')  # Decode bytes into ASCII string
                  print('appln ver ASCII :',self.appln_ver)
                  print(f"Application version: {self.appln_ver}")
                  self.ui.IMIE_input_4.setPlainText(self.appln_ver)
                  self.ui.plainTextEdit_4.appendPlainText(f"Application Version : {self.appln_ver}\n")

                  if self.appln_ver != 'SAM01_APP_0.0.6_TST06':
                      self.ui.IMIE_input_4.setStyleSheet("background-color: red;")
                  else:
                      self.ui.IMIE_input_4.setStyleSheet("background-color: white;")
                      
                except UnicodeDecodeError:
                  print("Error decoding IMEI to ASCII. The data may contain non-ASCII characters.")
 
            else:
                print(f"Not all frames received for CAN ID 0x103. Expected {expected_frame_counts[0x103]}, but received {len(received_frames[0x103])}.")
 
        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x103].clear()
            self.function103_done = True
            time.sleep(2)
            self.execute_next_function()
            print("Frames cleared for CAN ID 0x103")

    def fun_0x105(self):
        if self.busy:  # Check if the system is busy
            print("System is busy, please wait...")
            return
 
        if self.bus is None:  # Check if the bus was initialized properly
            print("CAN Bus not initialized. Cannot send message.")
            return
 
        self.busy = True  # Mark the system as busy
        try:
            msg = can.Message(arbitration_id=0x105, data=[0, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False)
           
            # Send the message
            self.bus.send(msg)
            print(f"Message sent on {self.bus.channel_info}")
 
            # Wait for the response
            for i in range(expected_frame_counts[0x105]):
                message = self.bus.recv(timeout=2)  # 1 second timeout for each frame
                if message:
                    print(f"Received message from CAN ID {hex(message.arbitration_id)}: {message.data.hex()}")
                    received_frames[0x105].append(message)
                else:
                    print(f"Timeout waiting for message for CAN ID 0x100. No response received.")
 
            # Check if we have received all expected frames for 0x100
            if len(received_frames[0x105]) == expected_frame_counts[0x105]:
                frames = received_frames[0x105]
                frames.sort(key=lambda x: x.data[0])  # Sort by sequence number
                complete_message = b''.join(frame.data[1:] for frame in frames)
                print(f"Complete for CAN ID 0x105: {complete_message.hex()}")
 
                try:
                  self.Gps_ver = complete_message.decode('ascii')  # Decode bytes into ASCII string
                  print('GPS ver ASCII :',self.Gps_ver)
                  self.ui.GPS_version.setPlainText(self.Gps_ver)
                  self.ui.plainTextEdit_4.appendPlainText(f"GPS Version : {self.Gps_ver}\n")
                  #gps_ver_cleaned = self.Gps_ver.strip()
                  print('gps strip',self.Gps_ver)
                  
                  if self.Gps_ver == 'L89HANR01A07S':
                      self.ui.GPS_version.setStyleSheet("background-color: white;")
                  else:
                      self.ui.GPS_version.setStyleSheet("background-color: red;")
                      
                except UnicodeDecodeError:
                  print("Error decoding IMEI to ASCII. The data may contain non-ASCII characters.")
 
            else:
                print(f"Not all frames received for CAN ID 0x105. Expected {expected_frame_counts[0x105]}, but received {len(received_frames[0x105])}.")
 
        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x105].clear()
            self.function105_done = True
            time.sleep(2)
            self.execute_next_function()
            print("Frames cleared for CAN ID 0x105")

    def fun_0x106(self):
        print('fun 0x106 called')
        if self.busy:  # Check if the system is busy
            print("System is busy, please wait...")
            return
 
        if self.bus is None:  # Check if the bus was initialized properly
            print("CAN Bus not initialized. Cannot send message.")
            return
 
        self.busy = True  # Mark the system as busy
        try:
            msg = can.Message(arbitration_id=0x106, data=[0, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False)
           
            # Send the message
            self.bus.send(msg)
            print(f"Message sent on {self.bus.channel_info}")
 
            # Wait for the response
            for i in range(expected_frame_counts[0x106]):
                message = self.bus.recv(timeout=2)  # 1 second timeout for each frame
                if message:
                    print(f"Received message from CAN ID {hex(message.arbitration_id)}: {message.data.hex()}")
                    received_frames[0x106].append(message)
                else:
                    print(f"Timeout waiting for message for CAN ID 0x100. No response received.")
 
            # Check if we have received all expected frames for 0x100
            if len(received_frames[0x106]) == expected_frame_counts[0x106]:
                frames = received_frames[0x106]
                frames.sort(key=lambda x: x.data[0])  # Sort by sequence number
                complete_message = b''.join(frame.data[1:] for frame in frames)
                print(f"Complete message for CAN ID 0x106: {complete_message.hex()}")
 
                try:
                  self.GSM_ver = complete_message.decode('ascii')  # Decode bytes into ASCII string
                  print('GSM ver ASCII :',self.GSM_ver)
                  self.ui.GSM_version.setPlainText(self.GSM_ver)
                  self.ui.plainTextEdit_4.appendPlainText(f"GSM Version : {self.GSM_ver}\n")

                  if self.GSM_ver != 'EC200UCNAAR03A03M08':
                      self.ui.IMIE_input_4.setStyleSheet("background-color: red;")
                  else:
                      self.ui.IMIE_input_4.setStyleSheet("background-color: white;")
                      
                except UnicodeDecodeError:
                  print("Error decoding IMEI to ASCII. The data may contain non-ASCII characters.")
 
            else:
                print(f"Not all frames received for CAN ID 0x106. Expected {expected_frame_counts[0x106]}, but received {len(received_frames[0x106])}.")
 
        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x106].clear()
            self.function106_done = True
            time.sleep(2)
            self.execute_next_function()
            print("Frames cleared for CAN ID 0x106")

    def fun_0x115(self):
        if self.busy:  # Check if the system is busy
            print("System is busy, please wait...")
            return

        if self.bus is None:  # Check if the bus was initialized properly
            print("CAN Bus not initialized. Cannot send message.")
            return

        self.busy = True  # Mark the system as busy

        try:
            # Create the CAN message
            msg = can.Message(arbitration_id=0x115, data=[0, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False)

            # Send the message once
            self.bus.send(msg)
            print(f"Message sent on {self.bus.channel_info}")

            # Wait for a response with a timeout (e.g., 2 seconds)
            message = self.bus.recv(timeout=2)  # 2 seconds timeout for response

            if message:
                exttracted_mains = message.data[1:]
                # Process the received message
                print(f"Received message from CAN ID {hex(message.arbitration_id)}: {message.data.hex()}")
            
                # Decode the received message and update the UI
                self.mains_vtg = exttracted_mains.decode('ascii')  # Decode bytes into ASCII string
                print('Mains vtg:', self.mains_vtg)
            
                # Update the UI with the decoded message
                self.ui.Analog1.setPlainText(self.mains_vtg)
                self.ui.plainTextEdit_4.appendPlainText(f"Mains Voltage: {self.mains_vtg}\n")
            else:
                # If no message is received within the timeout period
                print(f"Timeout waiting for message for CAN ID 0x115. No response received.")

        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x115].clear()
            self.function115_done = True
            time.sleep(2)
            self.execute_next_function()
            print("Frames cleared for CAN ID 0x115")

    def fun_0x116(self):
        if self.busy:  # Check if the system is busy
            print("System is busy, please wait...")
            return

        if self.bus is None:  # Check if the bus was initialized properly
            print("CAN Bus not initialized. Cannot send message.")
            return

        self.busy = True  # Mark the system as busy

        try:
            # Create the CAN message
            msg = can.Message(arbitration_id=0x116, data=[0, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False)

            # Send the message once
            self.bus.send(msg)
            print(f"Message sent on {self.bus.channel_info}")

            # Wait for a response with a timeout (e.g., 2 seconds)
            message = self.bus.recv(timeout=2)  # 2 seconds timeout for response

            if message:
                exttracted_IntVtg = message.data[1:]
                # Process the received message
                print(f"Received message from CAN ID {hex(message.arbitration_id)}: {message.data.hex()}")
            
                # Decode the received message and update the UI
                self.Int_vtg = exttracted_IntVtg.decode('ascii')  # Decode bytes into ASCII string
                print('Internal vtg:', self.Int_vtg)
            
                # Update the UI with the decoded message
                self.ui.IntBat_input.setPlainText(self.Int_vtg)
                self.ui.plainTextEdit_4.appendPlainText(f"Mains Voltage: {self.Int_vtg}\n")
            else:
                # If no message is received within the timeout period
                print(f"Timeout waiting for message for CAN ID 0x116. No response received.")

        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x116].clear()
            self.function116_done = True
            time.sleep(2)
            self.execute_next_function()
            print("Frames cleared for CAN ID 0x116")

    def fun_0x116(self):
        if self.busy:  # Check if the system is busy
            print("System is busy, please wait...")
            return

        if self.bus is None:  # Check if the bus was initialized properly
            print("CAN Bus not initialized. Cannot send message.")
            return

        self.busy = True  # Mark the system as busy

        try:
            # Create the CAN message
            msg = can.Message(arbitration_id=0x116, data=[0, 0, 0, 0, 0, 0, 0, 0], is_extended_id=False)

            # Send the message once
            self.bus.send(msg)
            print(f"Message sent on {self.bus.channel_info}")

            # Wait for a response with a timeout (e.g., 2 seconds)
            message = self.bus.recv(timeout=2)  # 2 seconds timeout for response

            if message:
                exttracted_IntVtg = message.data[1:]
                # Process the received message
                print(f"Received message from CAN ID {hex(message.arbitration_id)}: {message.data.hex()}")
            
                # Decode the received message and update the UI
                self.Int_vtg = exttracted_IntVtg.decode('ascii')  # Decode bytes into ASCII string
                print('Internal vtg:', self.Int_vtg)
            
                # Update the UI with the decoded message
                self.ui.IntBat_input.setPlainText(self.Int_vtg)
                self.ui.plainTextEdit_4.appendPlainText(f"Mains Voltage: {self.Int_vtg}\n")
            else:
                # If no message is received within the timeout period
                print(f"Timeout waiting for message for CAN ID 0x116. No response received.")

        except can.CanError as e:
            print(f"CAN error: {str(e)}")
 
        finally:
            self.busy = False  # Mark the system as not busy
            received_frames[0x116].clear()
            self.function116_done = True
            time.sleep(2)
            self.execute_next_function()
            print("Frames cleared for CAN ID 0x116")


    def execute_next_function(self):
        """Check which function is done and call the next one."""
        if self.function100_done and not self.function101_done:
            self.fun_0x101()  # Call function 2 after function 1 is done

        elif self.function101_done and not self.function103_done:
             self.fun_0x103()  # Call function 3 after function 2 is done

        elif self.function103_done and not self.function105_done:
            self.fun_0x105()

        elif self.function105_done and not self.function106_done:
            self.fun_0x106()

        elif self.function106_done and not self.function115_done:
            self.fun_0x115()

        elif self.function115_done and not self.function116_done:
            self.fun_0x116()
        else:
            print("All functions completed.")
            # You can enable a button or perform other tasks once all functions are done
            self.ui.pushButton_2.setEnabled(True)  # Enable button after all functions are done

 
 
    def login(self):
        # Get the username and password entered by the user
        Operator = self.ui.plainTextEdit.toPlainText()
        QC_head = self.ui.plainTextEdit_2.toPlainText()
 
        # Logic to check the username and password
        if Operator is not None and QC_head is not None:
            #self.ui.pushButton.clicked.connect(self.goToPage2)
            self.show_message("Login Successful", "Welcome, Operator!")
        else:
            self.show_message("Login Failed", "Invalid username or password. Please try again.")
 
    def goToPage2(self):
        self.stackedWidget.setCurrentIndex((self.stackedWidget.currentIndex()+1)%2)

       
        

   
    

   
    

# Entry point of the program
if __name__ == "__main__":
    app = QApplication(sys.argv)    
    # Create an instance of the MyClass class
    processor = MyClass()
    processor.show()
    sys.exit(app.exec_())
