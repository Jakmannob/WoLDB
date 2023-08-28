import os
import discord
from dotenv import load_dotenv
from wakeonlan import send_magic_packet


load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')
server_id = int(os.getenv('SERVER_ID'))
mac = os.getenv('MAC')
ip = os.getenv('IP')
port = int(os.getenv('PORT'))


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@tree.command(name="wakeupserver",
    description="A command that will invoke Wake on LAN to wake up the server.",
    guild=discord.Object(id=server_id))
async def wake_up_server(interaction):
    send_magic_packet(mac, ip_address=ip, port=port)
    await interaction.response.send_message("Starting server! Please stand by.")

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=server_id))


client.run(discord_token)
