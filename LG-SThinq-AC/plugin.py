#       
#       LG AC SmartThinq Plugin
#       Author: olinek2, 2018
#       
"""
<plugin key="LG-SmartThinq-AC" name="LG AC SmartThinq" author="olinek2" version="0.1.0" wikilink="https://github.com/olinek2/LGAC_SmartT">
    <description>
        LG AC SmartThinq Plugin
    </description>
    <params>
        <param field="Mode1" label="LGACServer host:port" width="200px" required="true" default="127.0.0.1:22233"/>
        <param field="Mode3" label="Update interval (sec)" width="30px" required="true" default="60"/>
        <param field="Mode5" label="Ionizer" width="75px">
            <options>
                <option label="True" value="true" default="true"/>
                <option label="False" value="false"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug" default="true"/>
                <option label="False" value="Normal"/>
            </options>
        </param>
    </params>
</plugin>
"""
#        <param field="Mode4" label="Refresh Token" width="200px"  required="true" default="e746522c66ff6ec2116e876d80f755984cb0d289bc7d11ae55f70af9bd0551cf0b91a6fd22f32be211c7675b715d2dd5"/>
#        <param field="Mode2" label="LG AC ID" width="200px" required="true" default="0750d920-689f-11dc-a10a-a06faaad2e3e"/>

import sys
import os 
#module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
#for mp in module_paths:
#    sys.path.append(mp)

import Domoticz
sys.path.append('/usr/local/lib/python3.5/dist-packages')
import msgpack
import time
from datetime import datetime 

class BasePlugin:

    customSensorOptions = {"Custom": "1;%"}
    
    iconCondName = 'CondStatus'
    iconIonName = 'IonStatus'
    
    enabled = False
    def __init__(self):
        #self.var = 123
        self.heartBeatCnt = 0
        self.subHost = None
        self.subPort = None
        self.tcpConn = None
        powerOn = 0
        self.unpacker = msgpack.Unpacker(encoding='utf-8')
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)

        self.heartBeatCnt = 0
        self.subHost, self.subPort = Parameters['Mode1'].split(':')

        self.tcpConn = Domoticz.Connection(Name='LGACServer', Transport='TCP/IP', Protocol='None',
                                           Address=self.subHost, Port=self.subPort)
        #Domoticz.Device(Unit= 1, Name="kWh", TypeName="kWh").Create()
        Domoticz.Log("onStart called:" +Parameters['Mode3'])
        #if self.iconName not in Images: Domoticz.Image('CondStatus.zip').Create()
        #if ("CondStatus" not in Images): 
        #    Domoticz.Image('CondStatus.zip').Create()
        #iconCondID = Images["CondStatus"].ID Images[self.iconName].ID
        if self.iconCondName not in Images: Domoticz.Image('CondStatus.zip').Create()
        #iconCondID = Images[self.iconCondName].ID
        #Domoticz.Debug("Image created. ID: "+str(iconCondID))
        #if ("IonStatus" not in Images): 
        #    Domoticz.Image('IonStatus.zip').Create()
        #iconIonID = Images["IonStatus"].ID
        if self.iconIonName not in Images: Domoticz.Image('IonStatus.zip').Create()
        #iconIonID = Images[self.iconIonName].ID
        #Domoticz.Debug("Image created. ID: "+str(iconIonID))
        #Domoticz.Device(Name='Status', Unit=2, Type=17,  Switchtype=17, Image=iconID).Create()
        #Domoticz.Device(Name='Setpoint', Unit=3, Type=242, Subtype=1, Image=iconID).Create()


        if (len(Devices) == 0):
            Domoticz.Device(Name="Power", Unit=1, Image=19, TypeName="Switch", Used=1).Create()
            Domoticz.Device(Name="Ambient Temp", Unit=2, TypeName="Temperature", Used=1).Create()
            Options = {"LevelActions" : "||||",
                       "LevelNames" : "|Heat|Cool|Dry|Fan|Auto",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "0"}
            
            Domoticz.Device(Name="Mode", Unit=4, TypeName="Selector Switch", Image=16, Options=Options, Used=1).Create()
            
            Options = {"LevelActions" : "||||||",
                       "LevelNames" : "|Auto|F1|F2|F3|F4|F5",
                       "LevelOffHidden" : "true",
                       "SelectorStyle" : "0"}
            
            Domoticz.Device(Name="Fan Rate", Unit=5, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()
            Domoticz.Device(Name="Setpoint Temp", Unit=6, Type=242, Subtype=1, Image=15, Used=1).Create()
            if Parameters["Mode5"] == "true":
                Domoticz.Device(Name="Ionizer", Unit=7, Image=20, TypeName="Switch", Used=1).Create()
            Domoticz.Device(Name="Care Filter", Unit=8, TypeName='Custom', Image=19, Options=self.customSensorOptions, Used=1).Create()
        
        Domoticz.Heartbeat(int(Parameters['Mode3']))
        
        Domoticz.Log("On Start")
        DumpConfigToLog()
        
    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("LGACServer connection status is [%s] [%s]" % (Status, Description))

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")
        try:
            self.unpacker.feed(Data)
            for result in self.unpacker:

                Domoticz.Debug("Got: %s" % result)
                if 'exception' in result: return
                if 'code' not in result:
                    if result['cmd'] == 'status':
                        #POWER
                        if result['state'] == 'on':
                            self.powerOn = 1
                            if (Devices[1].nValue != 1):
                                Devices[1].Update(nValue = 1, sValue ="100")
                        else:
                            self.powerOn = 0
                            if (Devices[1].nValue != 0):
                                Devices[1].Update(nValue = 0, sValue ="0")
                        
                        #Measured Temp
                        Devices[2].Update(0, str(result['temp_actual']))
                        
                        #Mode
                        op_mode = result['mode']
                        if op_mode == "HEAT":
                            sValueNew = "10" # Heat
                            iconNum = 15
                        elif op_mode == "COOL":
                            sValueNew = "20" # Cool
                            iconNum = 16
                        elif op_mode == "DRY":
                            sValueNew = "30" # Dry
                            iconNum = 11
                        elif op_mode == "FAN":
                            sValueNew = "40" # Fan
                            iconNum = 7
                        elif op_mode == "AI":
                            sValueNew = "19" # Auto
                            iconNum = 16
                        else: 
                            sValueNew = "0"
                            iconNum = 16
                        
                        if (Devices[4].nValue != self.powerOn or Devices[4].sValue != sValueNew):
                            Devices[4].Update(nValue = self.powerOn, sValue = sValueNew, Image = iconNum)
                    
                        #Wind strength
                        w_rate=result['wind_strength']
                        if w_rate == "8":
                            sValueNew = "10" # Auto
                        elif w_rate == "6" or w_rate == "7":
                            sValueNew = "60" # F5
                        elif w_rate == "5":
                            sValueNew = "50" # F4
                        elif w_rate == "4":
                            sValueNew = "40" # F3
                        elif w_rate == "3":
                            sValueNew = "30" # F2
                        elif w_rate == "2" or w_rate == "1" or w_rate == "0":
                            sValueNew = "20" # F1
                        else:
                            sValueNew='0'
                        
                        if (Devices[5].nValue != self.powerOn or Devices[5].sValue != sValueNew):
                            Devices[5].Update(nValue = self.powerOn, sValue = sValueNew)
                        
                        
                        #Temp Setpoint, update once per 30 minutes if no changes
                        lastUpdate = datetime.strptime(Devices[6].LastUpdate, "%Y-%m-%d %H:%M:%S")
                        delta = datetime.now() - lastUpdate
                        if (Devices[6].nValue != self.powerOn or Devices[6].sValue != result['temp_setpoint'] or delta.total_seconds() > 1800):
                            Devices[6].Update(nValue = self.powerOn, sValue = str(result['temp_setpoint']))
                        
                        #Update ionizer if it is used
                        if Parameters["Mode5"] == "true":
                            if result['air_ionizer'] == '1':
                                if (Devices[7].nValue != 1):
                                    Devices[7].Update(nValue = 1, sValue ="100")
                            else:
                                if (Devices[7].nValue != 0):
                                    Devices[7].Update(nValue = 0, sValue ="0")
                    
                    #Update Filter status
                    elif result['cmd'] == 'check_Filter':
                        Domoticz.Log("Filter:" + str(result['filter_percentage_state']))
                        Devices[8].Update(nValue = result['filter_percentage_state'], sValue = str(result['filter_percentage_state']))
        except msgpack.UnpackException as e:
            Domoticz.Error('Unpacker exception' + str(e))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if (Unit == 1):
            if(Command == "On"):
                self.powerOn = 1
                Devices[1].Update(nValue = 1, sValue ="100") 
                self.apiRequest('turn_AC', 'on')
            else:
                self.powerOn = 0
                Devices[1].Update(nValue = 0, sValue ="0")
                self.apiRequest('turn_AC', 'off')
            
            #Update state of all other devices
            Devices[4].Update(nValue = self.powerOn, sValue = Devices[4].sValue)
            Devices[5].Update(nValue = self.powerOn, sValue = Devices[5].sValue)
            Devices[6].Update(nValue = self.powerOn, sValue = Devices[6].sValue)
        
        elif (Unit == 4):
            if Level == 10: # HEAT"
                self.apiRequest('set_Mode', 'HEAT')
                iconNum = 15
            elif Level == 20:
                self.apiRequest('set_Mode', 'COOL')
                iconNum = 16
            elif Level == 30:
                self.apiRequest('set_Mode', 'DRY')
                iconNum = 11
            elif Level == 40:
                self.apiRequest('set_Mode', 'FAN')
                iconNum = 7
            elif Level == 50:
                self.apiRequest('set_Mode', 'AI')
                iconNum = 16
            else:
                Domoticz.Error('Usupported AC mode Level!')
            Devices[4].Update(nValue = self.powerOn, sValue = str(Level), Image = iconNum)
 
        elif (Unit == 5):
            Devices[5].Update(nValue = self.powerOn, sValue = str(Level))
            if Level == 10:
                self.apiRequest('set_Wind', 'AI')
            elif Level == 20:
                self.apiRequest('set_Wind', 'F1')
            elif Level == 30:
                self.apiRequest('set_Wind', 'F2')
            elif Level == 40:
                self.apiRequest('set_Wind', 'F3')
            elif Level == 50:
                self.apiRequest('set_Wind', 'F4')
            elif Level == 60:
                self.apiRequest('set_Wind', 'F5')
            else:
                Domoticz.Error('Usupported AC wind Level!')
                
        elif (Unit == 6):
            Devices[6].Update(nValue = self.powerOn, sValue = str(Level))
            self.apiRequest('set_Temp', str(Level))
            
        elif (Unit == 7):
            if(Command == "On"):
                Devices[7].Update(nValue = 1, sValue ="100") 
                self.apiRequest('turn_Ionizer', 'on')
            else:
                Devices[7].Update(nValue = 0, sValue ="0")
                self.apiRequest('turn_Ionizer', 'off')
        
        self.apiRequest('status')

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("LGAC onDisconnect called")
        Domoticz.Debug("LGACServer disconnected")

    def onHeartbeat(self):
        if not self.tcpConn.Connecting() and not self.tcpConn.Connected():
            self.tcpConn.Connect()
            Domoticz.Debug("Trying connect to LGACServer %s:%s" % (self.subHost, self.subPort))

        elif self.tcpConn.Connecting():
            Domoticz.Debug("Still connecting to LGACServer %s:%s" % (self.subHost, self.subPort))

        elif self.tcpConn.Connected():
            if self.heartBeatCnt % 60 == 0 or self.heartBeatCnt == 0: #every hour
                self.apiRequest('check_Filter')
            self.apiRequest('status')
            self.heartBeatCnt += 1
    
    def apiRequest(self, cmd_name, cmd_value=None):
        if not self.tcpConn.Connected(): return False
        cmd = [cmd_name]
        if cmd_value: cmd.append(cmd_value)
        try:
            self.tcpConn.Send(msgpack.packb(cmd, use_bin_type=True))
            return True
        except msgpack.PackException as e:
            Domoticz.Error('Pack exception [%s]' % str(e))
            return False
        
        
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)
def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return