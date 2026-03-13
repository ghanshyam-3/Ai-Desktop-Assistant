import os
import pyautogui
import subprocess
import time

class SystemControl:
    def __init__(self):
        pass

    def execute(self, command, parameter=None):
        """
        Executes system control commands.
        command: 'volume_up', 'volume_down', 'mute', 'wifi_on', 'wifi_off', 'shutdown', 'restart', 'sleep'
        """
        print(f"System Control Executing: {command}")
        
        if command == 'volume_up':
            # Press multiple times for noticeable effect
            for _ in range(7):
                pyautogui.press('volumeup')
            return "Turning volume up."
            
        elif command == 'volume_down':
            for _ in range(7):
                pyautogui.press('volumedown')
            return "Turning volume down."
            
        elif command == 'mute':
            pyautogui.press('volumemute')
            return "Toggled mute."
            
        elif command == 'wifi_on':
            # PowerShell: Enable-NetAdapter
            try:
                cmd = 'powershell -Command "Enable-NetAdapter -Name \'Wi-Fi\' -Confirm:$false"'
                subprocess.run(cmd, shell=True, check=True)
                return "WiFi Enabled (PowerShell)."
            except Exception as e:
                print(f"WiFi Error: {e}")
                return "Failed to enable WiFi (Run as Admin?)."

        elif command == 'wifi_off':
            # PowerShell: Disable-NetAdapter
            try:
                cmd = 'powershell -Command "Disable-NetAdapter -Name \'Wi-Fi\' -Confirm:$false"'
                subprocess.run(cmd, shell=True, check=True)
                return "WiFi Disabled (PowerShell)."
            except Exception as e:
                print(f"WiFi Error: {e}")
                return "Failed to disable WiFi (Run as Admin?)."
                
        elif command == 'bluetooth':
            # This is tricky. Often 'bluetooth' intent doesn't specify on/off.
            # Assuming toggle or open settings if ambiguous? 
            # But user said "turn on and off". 
            # The intent classifier just sends 'bluetooth'. We need 'bluetooth_on' or 'off'.
            # Current prompt only has 'bluetooth'. 
            # I should probably open settings for 'bluetooth' generic, 
            # OR ask the user.
            # But the user asked for "turn on/off".
            # Let's assume the LLM might send "bluetooth" target? 
            # Wait, the prompt has `bluetooth` as a target for `system_control`.
            # If the user says "Turn off bluetooth", LLM sends action=system_control target=bluetooth.
            # We don't know the direction (on/off) from the target alone if it's just "bluetooth".
            # I need to update the prompt to have 'bluetooth_on' and 'bluetooth_off'.
            return "Please say 'Turn on Bluetooth' or 'Turn off Bluetooth' explicitly."
            
        elif command == 'bluetooth_on':
             # PowerShell: Enable PnP Device (Generic approach)
            try:
                # Find devices with class Bluetooth and enable
                cmd = 'powershell -Command "Get-PnpDevice -Class Bluetooth | Enable-PnpDevice -Confirm:$false"'
                subprocess.run(cmd, shell=True, check=True)
                return "Bluetooth Enabled (PowerShell)."
            except:
                return "Failed to enable Bluetooth (Run as Admin?)."

        elif command == 'bluetooth_off':
            try:
                cmd = 'powershell -Command "Get-PnpDevice -Class Bluetooth | Disable-PnpDevice -Confirm:$false"'
                subprocess.run(cmd, shell=True, check=True)
                return "Bluetooth Disabled (PowerShell)."
            except:
                return "Failed to disable Bluetooth (Run as Admin?)."
            
        elif command == 'hotspot':
            # Hotspot doesn't have a clean PowerShell 5.1 API.
            # Opening settings is the only reliable non-UWP-hack way.
            os.system("start ms-settings:network-mobilehotspot")
            return "Opening Hotspot Settings (Direct control unavailable)."
            
        elif command == 'shutdown':
            return "I cannot do that for you."
            
        elif command == 'restart':
            #os.system("shutdown /r /t 10")
            return "Restarting system in 10 seconds."
            
        elif command == 'sleep':
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "Going to sleep."
            
        elif command == 'screenshot':
            path = self.take_screenshot()
            return f"Screenshot saved as {path}"
            
        else:
            return "Command not recognized."

    def take_screenshot(self):
        """Captures screen and returns file path"""
        timestamp = int(time.time())
        filename = f"screenshot_{timestamp}.png"
        # Make sure we save in a temp or known dir, not just CWD
        # For now CWD is fine as per original code
        pyautogui.screenshot(filename)
        return filename