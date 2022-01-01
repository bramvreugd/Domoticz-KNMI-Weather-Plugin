# Domoticz-KNMI-Weather-Plugin
Get the KNMI (Dutch) weather information<br>
This plugin receives the temperatures, the weather forecast and wind information from the KNMI.
#
# New
- Day after tommorow temp, wind, rain and sunshine devices
- More precise wind degree
- Default names of devices in dutch. Prediction and wind direction of KNMi is also in dutch.

# before upgrade 
Before upgrade you should remove wind direction tommorow and windforce tommorow device. 

# Usage
To use it you should get a free API key at https://weerlive.nl/delen.php.
<br>
There is more information available in the KNMI api.
<br>If you want it just let me know.


Domoticz hardcoded references to english wind directions for te icon names. 
KNMI uses dutch names and that will result in no icon. To fix  that you could copy the icon names or create a link.
Running the script below fixes the icons.
```
cd <domoticz_dir>/www/images
ln WindE.png WindO.png
ln WindNE.png WindNO.png
ln WindS.png WindZ.png
ln WindSSW.png WindZZW.png
ln WindWSW.png WindWZW.png
ln WindENE.png WindONO.png
ln WindESE.png WindOZO.png
ln WindNNE.png WindNNO.png
ln WindSE.png WindZO.png
ln WindSSE.png WindZZO.png
ln WindSW.png WindZW.png
ln WindSW.png WindZW.png
```
