# KNMI plugin
#
# Author: Bramv, 2021
#
#   This get the weather information from the Ductch national weather institute (KNMI)
#
#
"""
<plugin key="KNMI" name="KNMI weather info" author="Bramv" version="1.0.0" externallink="https://www.github.com">
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
        #forecast   use 1 for now
        # // Pressure Status
        #if (pres < 966) {
        #    forecast = "4";
        #} else if (pres < 993) {
        #    forecast = "3";
        #} else if (pres < 1007) {
        #    forecast = "2";
        #} else if (pres < 1013) {
        #    forecast = "3";
        #} else if (pres < 1033) {
        #    forecast = "0";
        #} else {
        #    forecast = "1";
        #}
        Devices[1].Update(0,Response[0]['temp']+";"+Response[0]['lv']+";1;"+Response[0]['luchtd']+";1")
        Devices[2].Update(0,Response[0]["samenv"]+"<br>"+Response[0]["verw"])
        Devices[2].Update(0,"-1;"+Response[0]["windr"]+";"+Response[0]["windms"]+";"+Response[0]["windms"]+";"+Response[0]["temp"]+";"+Response[0]["gtemp"])
        
                
    def onMessage(self, Connection, Data):
        #DumpHTTPResponseToLog(Data)
        
        strData = Data["Data"].decode("utf-8", "ignore")
        Status = int(Data["Status"])
        #Domoticz.Log("data:"+str(Data)  )

        if (Status == 200):
            if ((self.disconnectCount & 1) == 1):
                Domoticz.Log("Good Response received from vbus, Disconnecting.")
                self.httpConn.Disconnect()                
            else:
                Domoticz.Log("Good Response received from vbus, Dropping connection.")
                self.httpConn = None
            self.disconnectCount = self.disconnectCount + 1
            Domoticz.Log("data"+str(Data["Data"][:17],'cp1252'))
                
            if(str(Data["Data"][:17],'cp1252')=="Dagelijkse limiet"):
                Devices[2].Update(0,str(Data["Data"],'UTF-8'))
            else:
                Response = json.loads( Data["Data"].decode("utf-8", "ignore") )

                #Domoticz.Log("KNMI:"+str(type(Response)))
                self.processResponse(Response["liveweer"])
                
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
