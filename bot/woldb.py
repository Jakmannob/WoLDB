import asyncio
import json
import logging
import os
import ssl
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
GUILD_ID = int(os.environ['GUILD_ID'])
LISTENER_HOST = os.environ['LISTENER_HOST']
LISTENER_PORT = int(os.environ['LISTENER_PORT'])
SHARED_SECRET = os.environ['SHARED_SECRET']

BASE_DIR = Path(__file__).parent
with open(BASE_DIR.parent / 'machines.json') as f:
    MACHINES = json.load(f)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
log = logging.getLogger('woldb')

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
guild = discord.Object(id=GUILD_ID)


async def send_wake_command(machine_name: str) -> dict:
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = False
    ssl_ctx.load_verify_locations(str(BASE_DIR / 'certs' / 'cert.pem'))

    reader, writer = await asyncio.open_connection(
        LISTENER_HOST, LISTENER_PORT, ssl=ssl_ctx,
    )
    try:
        request = json.dumps({'token': SHARED_SECRET, 'machine': machine_name})
        writer.write((request + '\n').encode())
        await writer.drain()

        response_data = await asyncio.wait_for(reader.readline(), timeout=10)
        return json.loads(response_data.decode())
    finally:
        writer.close()
        await writer.wait_closed()


@tree.command(
    name='wake',
    description='Send a Wake-on-LAN packet to a configured machine.',
    guild=guild,
)
@app_commands.describe(machine='The machine to wake up')
async def wake(interaction: discord.Interaction, machine: str):
    if machine not in MACHINES:
        await interaction.response.send_message(
            f'Unknown machine: `{machine}`. '
            f'Available: {", ".join(MACHINES)}',
            ephemeral=True,
        )
        return

    log.info('Wake command invoked for %s by %s', machine, interaction.user)
    await interaction.response.defer()
    try:
        response = await send_wake_command(machine)
        if response.get('status') == 'ok':
            log.info('Wake command successful for %s', machine)
            await interaction.followup.send(response['message'])
        else:
            msg = response.get('message', 'Unknown error')
            log.warning('Wake command failed for %s: %s', machine, msg)
            await interaction.followup.send(f'Error: {msg}')
    except Exception as e:
        log.error('Failed to contact listener: %s', e)
        await interaction.followup.send(
            f'Failed to contact wake listener: {e}',
        )


@wake.autocomplete('machine')
async def machine_autocomplete(
    interaction: discord.Interaction, current: str,
) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=info['description'], value=name)
        for name, info in MACHINES.items()
        if current.lower() in name.lower()
        or current.lower() in info['description'].lower()
    ]


synced = False

@client.event
async def on_ready():
    global synced
    if not synced:
        await tree.sync(guild=guild)
        synced = True
    log.info('Bot ready. Logged in as %s', client.user)
    log.info('Configured machines: %s', ', '.join(MACHINES))


client.run(DISCORD_TOKEN)
