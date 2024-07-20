# Sincroni López

A special version of JDBot by me.

## Tables

That's Right, this guide will be on the table designs I use.
This way you can set it up yourself.

All tables in [table.sql](table.sql).

## Systemd Service

Here is the template for the systemd service file.

```
[Unit]
Description=Runs the Bot Sincroni
After=network-online.target
StartLimitIntervalSec = 1day
StartLimitBurst = 50

[Service]
ExecStart=/path/to/python -u main.py
WorkingDirectory=/path/to/working/directory
EnvironmentFile=/path/to/env/.env
Restart=on-failure
RestartSec=15


[Install]
WantedBy=default.target
```

## Environment File

Here is the template for the environment file.

```env
TOKEN = 
# Token of the bot

DB_key = 
# Postgresql url to connect to

SUPPORT_WEBHOOK = 
# Webhook that you will use to contact yourself from the bot

MOD_WEBHOOK = 
# Webhook that will log the messages sent in global chat for moderation purposes

MOD_CHANNEL =
# ID of the channel that will be used as fallback for moderation Webhooks
```
