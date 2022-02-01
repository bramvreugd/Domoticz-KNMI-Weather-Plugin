# KNMI plugin
#
# Author: Bramv, 2021
#
#   This get the weather information from the Ductch national weather institute (KNMI)
#
#
"""
<plugin key="KNMI" name="KNMI weather info" author="Bramv" version="1.2.0" externallink="https://www.github.com">
    <description>
        <h2>KNMI weer info</h2><br/>
        Maximaal 300 x per dag mag de data opgevraagd worden. Door niet minder 1 x per 5 minuten op te halen blijft het aantal onder de 288.
        Iconen voor de plugin zijn op te halen op :  https://github.com/jackd248/weather-iconic
        The free service is limited to 300 updates per day. That is once per 5 minutes. 
    </description>
    <params>
        <param field="Address" label="Plaats of lat long" width="200px" required="true" default="Utrecht"/>
        <param field="Mode1" label="API key" width="150px" default="Demo"/>
        <param field="Mode2" label="    (min)" width="200px" required="true" default="5"/>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2" />
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import urllib
import urllib.parse

class BasePlugin:
    httpConn = None
    disconnectCount = 0
    sProtocol = "HTTP"
    previousDate = 0
    sUrl  = ""
    sPort = "80"
    sHost ="weerlive.nl"
    #sHost="192.168.178.13"
    Interval = 5*3
    runAgain = Interval
    
    def __init__(self):
        return

    def onStart(self):
        Domoticz.Log("onstart")

        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
        Domoticz.Log("mode 6:" + Parameters["Mode6"])
        Domoticz.Log("Name="+self.sProtocol+" Test" +", Transport=""TCP/IP"", Protocol="+str(self.sProtocol)+", Address="+Parameters["Address"]) 
        self.Interval =int(Parameters["Mode2"])*3        
        Domoticz.Heartbeat(20)
        
        self.httpConn = Domoticz.Connection(Name="KNMIConn", Transport="TCP/IP", Protocol="HTTP", Address=self.sHost, Port=self.sPort) 
        Domoticz.Log("Sending connect")
        self.httpConn.Connect()
        Domoticz.Log("Sended connect")

    def onStop(self):
        Domoticz.Log("onStop - Plugin is stopping.")

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            self.sUrl="/api/json-data-10min.php?key="+Parameters["Mode1"]+"&locatie="+urllib.parse.quote(Parameters["Address"]).replace(' ',"%20")
            Domoticz.Debug("Connected successfully. Getting     :"+self.sUrl)
            sendData = { 'Verb' : 'GET',
                         'URL'  :  self.sUrl, 
                         'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                       'Connection': 'keep-alive', \
                                       'Accept': 'Content-Type: text/html; charset=UTF-8', \
                                       'Host': self.sHost+":"+self.sPort, \
                                       'User-Agent':'Domoticz/1.0' }
                       }
            Connection.Send(sendData)
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description) 
                
    def processResponse(self,Response):
        Domoticz.Log("Response received:"+str(Response))
        if not(1 in Devices):
           Domoticz.Device(Name="Temperatuur", Unit=1, TypeName="Temp+Hum+Baro").Create()
        if not(2 in Devices):
           Domoticz.Device(Name="Verwachting", Unit=2, TypeName="Text").Create()
        if not(3 in Devices):
           Domoticz.Device(Name="Wind", Unit=3, TypeName="Wind+Temp+Chill").Create()
        
        if not(4 in Devices):
           Domoticz.Device(Name="Min temp morgen", Unit=4, TypeName="Temperature").Create()
        if not(5 in Devices):
           Domoticz.Device(Name="Max temp morgen", Unit=5, TypeName="Temperature").Create()
        if not(6 in Devices):
           Domoticz.Device(Name="Wind morgen", Unit=6, TypeName="Wind").Create()
        if not(7 in Devices):                                                         
           Domoticz.Device(Name="Wind overmorgen", Unit=7, TypeName="Wind").Create()
        if not(8 in Devices):
           Domoticz.Device(Name="Regen morgen", Unit=8, TypeName="Percentage").Create()
        if not(9 in Devices):
           Domoticz.Device(Name="Zon morgen", Unit=9, TypeName="Percentage").Create()     
        if not(10 in Devices):
           Domoticz.Device(Name="Zon", Unit=10, TypeName="Percentage").Create()     
        if not(11 in Devices):
           Domoticz.Device(Name="Alarm", Unit=11, TypeName="Text").Create()     
        if not(12 in Devices):
           Domoticz.Device(Name="Dauwpunt", Unit=12, TypeName="Temperature").Create()     
        if not(13 in Devices):
           Domoticz.Device(Name="Zicht", Unit=13, Type=243, Subtype=1).Create()     
        if not(14 in Devices):
           Domoticz.Device(Name="Min temp overmorgen", Unit=14, TypeName="Temperature").Create()
        if not(15 in Devices):
           Domoticz.Device(Name="Max temp overmorgen", Unit=15, TypeName="Temperature").Create()
        if not(16 in Devices):
           Domoticz.Device(Name="Regen overmorgen", Unit=16, TypeName="Percentage").Create()
        if not(17 in Devices):
           Domoticz.Device(Name="Zon overmorgen", Unit=17, TypeName="Percentage").Create()     
                
        #calculate forecast from air pressure
        pres=float(Response['luchtd'])
        if (pres < 990):     # Rain
            forecast = "4"
        elif (pres < 1010):  # Cloudy
            forecast = "3"
        elif (pres < 1030):  # Partly Cloudy
            forecast = "2"
        else:
            forecast = "1"   # Sunny
        
        humi = float(Response['lv'])
        temp = float(Response['temp'])
        if (humi < 31):
            humistat = "2"
        elif (humi > 69):
            humistat = "3"
        elif (humi > 34 and humi < 66 and temp > 21 and temp < 27):
            humistat = "1"
        else:
            humistat = "0"
        UpdateDevice(1, 0, Response['temp']+";"+Response['lv']+";"+humistat+";"+Response['luchtd']+";"+forecast)                   
        UpdateDevice(2,0,Response["samenv"]+"<br>"+Response["verw"])
        UpdateDevice(3,0,Response["d0windrgr"]+";"+Response["windr"]+";"+str(10*float(Response["windms"]))+";"+str(10*float(Response["windms"]))+";"+Response["temp"]+";"+Response["gtemp"])
        UpdateDevice(4,0,Response["d1tmin"])
        UpdateDevice(5,0,Response["d1tmax"])
        UpdateDevice(6,0,Response["d1windrgr"]+";"+Response["d1windr"]+";"+str(10*float(Response["d1windms"]))+";"+str(10*float(Response["d1windms"]))+";"+Response["d1tmax"]+";"+Response["d1tmax"])
        UpdateDevice(7,0,Response["d2windrgr"]+";"+Response["d2windr"]+";"+str(10*float(Response["d2windms"]))+";"+str(10*float(Response["d2windms"]))+";"+Response["d2tmax"]+";"+Response["d2tmax"])
        UpdateDevice(8,0,Response["d1neerslag"])
        UpdateDevice(9,0,Response["d1zon"])
        UpdateDevice(10,0,Response["d0zon"])
        if(Response["alarm"] !="0"):
           UpdateDevice(11,0,Response["alarmtxt"])
        else:
           UpdateDevice(11,0,"")
        UpdateDevice(12,0,Response["dauwp"])
        UpdateDevice(13,0,Response["zicht"])
        UpdateDevice(14,0,Response["d2tmin"])
        UpdateDevice(15,0,Response["d2tmax"])
        UpdateDevice(16,0,Response["d2neerslag"])        
        UpdateDevice(17,0,Response["d2zon"])
                
    def onMessage(self, Connection, Data):
        #DumpHTTPResponseToLog(Data)
        
        strData = Data["Data"].decode("utf-8", "ignore")
        Status = int(Data["Status"])
        #Domoticz.Log("data:"+str(Data)  )

        if (Status == 200):
            if ((self.disconnectCount & 1) == 1):
                Domoticz.Log("Good Response received from KNMI, Disconnecting.")
                self.httpConn.Disconnect()                
            else:
                Domoticz.Log("Good Response received from KNMI, Dropping connection.")
                self.httpConn = None
            self.disconnectCount = self.disconnectCount + 1
                
            if(str(Data["Data"][:17],'cp1252')=="Dagelijkse limiet"):
                Devices[2].Update(0,str(Data["Data"],'UTF-8'))
            else:
                Response = json.loads( Data["Data"].decode("utf-8", "ignore") )

                #Domoticz.Log("KNMI:"+str(type(Response)))
                self.processResponse(Response["liveweer"][0])
                
        elif (Status == 302):
            Domoticz.Log("KNMI returned a Page Moved Error.")
            sendData = { 'Verb' : 'GET',
                         'URL'  : Data["Headers"]["Location"],
                         'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                       'Connection': 'keep-alive', \
                                       'Accept': 'Content-Type: text/html; charset=UTF-8', \
                                       'Host': self.sHost+":"+self.sPort, \
                                       'User-Agent':'Domoticz/1.0' },
                        }
            Connection.Send(sendData)
        elif (Status == 400):
            Domoticz.Error("KNMI returned a Bad Request Error.")
        elif (Status == 500):
            Domoticz.Error("KNMI returned a Server Error.")
        else:
            Domoticz.Error("KNMI returned a status: "+str(Status))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called for connection to: "+Connection.Address+":"+Connection.Port)

    def onHeartbeat(self):
        #Domoticz.Trace(True)
        if (self.httpConn != None and (self.httpConn.Connecting() or self.httpConn.Connected())):
            Domoticz.Debug("onHeartbeat called, Connection is alive.")
        else:
            self.runAgain = self.runAgain - 1
            if self.runAgain <= 0:
                if (self.httpConn == None):
                    self.httpConn = Domoticz.Connection(Name="KNMIConn", Transport="TCP/IP", Protocol="HTTP", Address=self.sHost , Port=self.sPort)
                self.httpConn.Connect()
                self.runAgain = self.Interval
            else:
                Domoticz.Debug("onHeartbeat called, run again in "+str(self.runAgain)+" heartbeats.")
        #Domoticz.Trace(False)

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

def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
    return

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"http.html","w")
        f.write(Message)
        f.close()
        Domoticz.Log("File written")

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

def DumpHTTPResponseToLog(httpResp, level=0):
    if (level==0): Domoticz.Debug("HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(indentStr + ">'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
