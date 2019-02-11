# LGACSmartThing
*This plugin uses the [wideq](https://github.com/sampsyo/wideq) modified library.*
*This plugin contains some modified functions from the [domoticz-mirobot-plugin](https://github.com/mrin/domoticz-mirobot-plugin) library.*
*This plugin contains some modified functions from the  [domoticz_daikin_BRP069A42](https://github.com/leejoow/domoticz_daikin_BRP069A42) library.*
LG AC Smarthing Unit control for Domoticz


Before installation plugin check the `python3`, `python3-dev`, `pip3` is installed for Domoticz plugin system:

```sudo apt-get install python3 python3-dev python3-pip```.

Make sure you have libffi and openssl headers installed, you can do this on Debian-based systems (like Rasperry Pi) with:

```sudo apt-get install libffi-dev libssl-dev```.

Also do note that the setuptools version is too old for installing some requirements, so before trying to install this package you should update the setuptools with:

```sudo pip3 install -U setuptools```.

Install all necessary libraries for LGACServer.py:

```sudo pip3 install gevent msgpack-python greenlet```.

Install [LGAC_SmartT] by typing something like:
```
$ git clone https://github.com/olinek2/LGAC_SmartT
$ cd LGAC_SmartT
$ sudo pip3 install -e .
```

Update region data inside wideq.py file. For US it looks like this:

```
GATEWAY_URL = 'https://kic.lgthinq.com:46030/api/common/gatewayUriList'
APP_KEY = 'wideq'
SECURITY_KEY = 'nuts_securitykey'
DATA_ROOT = 'lgedmRoot'
COUNTRY = 'US'
LANGUAGE = 'en-US'
SVC_CODE = 'SVC202'
CLIENT_ID = 'LGAO221A02'
OAUTH_SECRET_KEY = 'c053c2a6ddeb7ad97cb0eed0dcb31cf8'
OAUTH_CLIENT_KEY = 'LGAO221A02'
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S +0000'
```

For Poland and probably rest of EU like that:

```
GATEWAY_URL = 'https://kic.lgthinq.com:46030/api/common/gatewayUriList'
APP_KEY = 'wideq'
SECURITY_KEY = 'nuts_securitykey'
DATA_ROOT = 'lgedmRoot'
COUNTRY = 'PL'
LANGUAGE = 'en-EN'
SVC_CODE = 'SVC202'
CLIENT_ID = 'LGAO221A02'
OAUTH_SECRET_KEY = 'c053c2a6ddeb7ad97cb0eed0dcb31cf8'
OAUTH_CLIENT_KEY = 'LGAO221A02'
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S +0000'
```

To do that just open it in nano and save (Ctrl+X. yes and enter):
```nano wideq.py```

Authenticate with the SmartThing service to get a refresh token by running the WideQ example script.Run this in the `wideq` directory:

```python3 example.py```

The script will ask you to open a browser, log in, and then paste the URL you're redirected to. It will then write a JSON file called `wideq_state.json`.

Look inside this file for a key called `"refresh_token"` and copy the value.

We also need an AC Device Number. To obtain it run:

```python3 example.py ls```

Device number looks like that:
```"????????-????-????-????-????????????": KLIMATYZATOR (AC Rxxx_xxx_xx)```


After obtaining this two values just put them inside LGACServerNew.py file at default parser arguments.
```
parser.add_argument('--acDevNum', type=str, help='AC Device Number', default='copied dev num')
parser.add_argument('--token', type=str, help='Refresh Token', default='copied token')
```

Make it executable:
```sudo chmod +x LGACServerNew.py```

To check if the server is operating properly type:
```./LGACServerNew.py```.

It will start operation. Open another terminal window, log in, navigate to 'LGAC_SmartT' folder ```cd LGAC_SmartT``` and run testServer.py file:

```sudo python3 testServer.py```. 

You should observe communication between this two applications.

To run server automatically the service has to be made. Paths in line ```ExecStart=/usr/bin/python3 /home/pi/wideq/LGACServerNew.py``` is for python path (use:  ```which python3```) and second phrase is for location of  ```LGACServerNew.py``` path. 
Make service file in systemd:
```sudo nano /lib/systemd/system/lgac_server.service```.
Paste this text with path modification:
```
[Unit]
Description=LG AC Device Server
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pi/LGAC_SmartT/LGACServerNew.py
Restart=on-abort

[Install]
WantedBy=multi-user.target
```
Press Ctrl+X, hit Y to save and enter.Then set privilidges:
```sudo chmod 644 /lib/systemd/system/lgac_server.service```.
Reload daemon and make service running, then check a status of service:
```
sudo systemctl daemon-reload
sudo systemctl enable lgac_server.service
sudo systemctl start lgac_server
sudo systemctl status lgac_server
```

Status should look like this:
```sh
● lgac_server.service - LG AC Device Server
   Loaded: loaded (/lib/systemd/system/lgac_server.service; enabled; vendor preset: enabled
   Active: active (running) since Tue 2018-06-19 08:15:57 CEST; 2s ago
 Main PID: 9288 (python3)
      CPU: 1.958s
   CGroup: /system.slice/lgac_server.service
           └─9288 /usr/bin/python3 /home/pi/wideq/LGACServerNew.py

Jun 19 08:15:57 raspberrypi systemd[1]: Started LG AC Device Server.
Jun 19 08:15:59 raspberrypi python3[9288]: server: Starting server on 127.0.0.1 22233
```

Copy plugin to domoticz plugins folder and restart domoticz. Add hardware from list after restart and check if it is operating:
``` 
cp -Rf LG-SThinq-AC ~/domoticz/plugins/LG-SThinq-AC 
sudo service domoticz restart
```



