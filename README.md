# email-listener

**email-listener** is a tool to receive incoming email and then send it to an application server that need it (using HTTP Rest API).

The original source code is [shimofuri/imap_monitor](https://gist.github.com/shimofuri/4348943). I just modified it to meet my requirements and can be used on python 3.8.x environment.

This script use [mjs/imapclient](https://github.com/mjs/imapclient).

## How to Use

1. Configure the mail server, email account, password, and callback url using environment variable. Here just an example. If you need to [launch this script when device boot](#terminated-protection-and-launch-on-device-booting), place the environment variable on `/etc/profile` too.
```
export IMAP_HOST="mail.webiptek.com"
export IMAP_EMAIL="user@webiptek.com"
export IMAP_PASSWORD="yourpassword"
export IMAP_SSL=True
export CALLBACK_URL="https://pay.tokomini.net/api/v1"
```

2. Install the required packages.
```
$ pip3 install -r requirements.txt
```

3. Run the monitor.py

```
$ python3 monitor.py
```

Example output:
```
22-05-2021 19:23:46 | imap_monitor | INFO | ... script started
22-05-2021 19:23:46 | imap_monitor | INFO | setting path for email downloads - ./download
22-05-2021 19:23:46 | imap_monitor | INFO | connecting to IMAP server - sng123.hawkhost.com
22-05-2021 19:23:47 | imap_monitor | INFO | server connection established
22-05-2021 19:23:47 | imap_monitor | INFO | logging in to IMAP server - test1@webiptek.com
22-05-2021 19:23:47 | imap_monitor | INFO | login successful - b'Logged in'
22-05-2021 19:23:47 | imap_monitor | INFO | selecting IMAP folder - INBOX
22-05-2021 19:23:47 | imap_monitor | INFO | folder selected
22-05-2021 19:23:47 | imap_monitor | WARNING | 0 unread messages seen - []
22-05-2021 19:24:08 | imap_monitor | WARNING | 1 new unread messages - [57]
22-05-2021 19:24:08 | imap_monitor | INFO | -----------------------------------------------
22-05-2021 19:24:08 | imap_monitor | INFO | processing email {0} - {1}
22-05-2021 19:24:08 | imap_monitor | INFO | {
    "auth": "fad919e48529b457895dc041c4bb23df3178ee21915a0eee9b5b8a9e0f26543c",
    "from": "Rizqi Aldi <xdnbot@gmail.com>",
    "date": "Sat, 22 May 2021 19:23:53 +0700",
    "subject": "2",
    "body_plaintext": "2\r\n"
}
22-05-2021 19:24:08 | imap_monitor | INFO | push email to callback server
22-05-2021 19:24:09 | imap_monitor | INFO | {
    "status": false,
    "message": "Forbidden: your host are not allowed."
}
22-05-2021 19:24:09 | imap_monitor | INFO | -----------------------------------------------
```

The output logs will be saved in file imap_monitor.log


## API Documentation

This script will sends a JSON data by using HTTP POST Request to CALLBACK_URL. This is the JSON format that you can customize it in file monitor.py.
```
{
    "from": "Rizqi Aldi <xdnbot@gmail.com>",
    "date": "Sat, 22 May 2021 21:39:35 +0700",
    "subject": "Congratulation!",
    "body_plaintext": "Hi, this is the body of the message."
}
```
There is also *body_html* which is commented out, it will display the email in html format, instead of plaintext format. 

## Terminated Protection and Launch on Device Booting 

Script will be terminated when connection to the IMAP server failed. To auto relaunch script when it terminated and also make it autorun when device booting, we can use [PM2 Process Management](https://pm2.keymetrics.io/docs/usage/pm2-doc-single-page/).

PM2 requires [NodeJS](https://nodejs.org/en/). Make sure you have install it.

1. Install PM2. If you get permission denied, run this command as superuser (or sudoers).
```
$ npm install pm2@latest -g
```

2. Add the script to pm2. This command will add the monitor.py as a pm2 proccess named `imap`.
```
pm2 start monitor.py --interpreter="/usr/bin/python3" --name="imap" --watch --ignore-watch="imap_monitor.log"
```

3. To make it pm2 launch every startup (booting).
```
$ pm2 startup
[PM2] Init System found: systemd
[PM2] To setup the Startup Script, copy/paste the following command:
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u xdnroot --hp /home/xdnroot
$ sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u xdnroot --hp /home/xdnroot
```
The save all current proccess
```
$ pm2 save
```

## Term of Use

I am not responsible for any errors or failures. My script still has a lot of bugs. I would appreciate you if help me to fix those bugs.

You are free to customize the script according to your needs at your risk.
