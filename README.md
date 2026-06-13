# WoLDB

A Wake-on-LAN Discord Bot that lets you remotely wake machines on your home
network via Discord slash commands.

This project was rewritten with the help of Claude Opus 4.6

## Architecture

```
Discord User
    |  /wake <machine>
    v
VPS (bot/)  ---- TLS + shared secret ---->  Home RPi (listener/)
  Discord bot                                  |
                                               v
                                         wakeonlan --> Target PC
```

- **bot/** runs on a public-facing VPS, hosts the Discord bot
- **listener/** runs on a home server (e.g. RPi), receives authenticated wake
  commands over TLS and sends WoL packets on the local network
- Communication is secured with TLS (self-signed cert) and a pre-shared secret
- The listener sends a response back so the bot can confirm success to the user

## Setup

### 1. Listener (home server / RPi)

```bash
cd listener/
./setup.sh
```

This will:
- Install dependencies via `uv`
- Generate a TLS certificate (`certs/cert.pem` + `certs/key.pem`)
- Generate a `.env` with a random shared secret
- Create `machines.json` from the example

Edit `machines.json` (in the repo root) to set your machines' names, MAC
addresses, and descriptions.

Note the `SHARED_SECRET` from `.env` -- you'll need it for the bot.

### 2. Bot (VPS)

Copy `listener/certs/cert.pem` to `bot/certs/cert.pem`, then:

```bash
cd bot/
./setup.sh
```

Edit `bot/.env` and fill in:
- `DISCORD_TOKEN` -- your Discord bot token
- `GUILD_ID` -- your Discord server (guild) ID
- `LISTENER_HOST` -- IP/hostname of your home server
- `LISTENER_PORT` -- must match the listener (default: 9443)
- `SHARED_SECRET` -- the secret from the listener's `.env`

### 3. Systemd services

Both setup scripts generate a `.service` file with the correct paths.
Install them with:

```bash
# On the listener host:
sudo cp listener/woldb-listener.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now woldb-listener

# On the bot host:
sudo cp bot/woldb.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now woldb
```

## Adding machines

1. Add an entry to `machines.json` (repo root) with the machine's name, MAC
   address, and description
2. Restart both services

## Usage

In Discord, type `/wake` and select a machine from the autocomplete list.
The bot will contact the listener over TLS, which sends a WoL magic packet
and reports back whether it succeeded.
