# WoLDB
A Wake-on-Lan Discord Bot (WoLDB), that can be used to remotely wake up a server via Discord.

## Setup

First, set up a Discord application with bot, add it to your server and note down
the bot token. You will need it for the `DISCORD_TOKEN` in the following step.
Then create an environment file named `.env` with the content:

```conf
DISCORD_TOKEN=<your token>
SERVER_ID=<your server id>
MAC=<your target computers MAC address>
IP=<your target computers IP address>
PORT=<your target computers WoL port>
```

And run the python script.

## Usage

In the Discord server, type `/wakeupserver` in any channel. This will trigger a
WoL of your computer.
