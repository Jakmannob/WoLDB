import asyncio
import json
import logging
import os
import ssl
from pathlib import Path

from dotenv import load_dotenv
from wakeonlan import send_magic_packet

load_dotenv()

LISTENER_HOST = os.environ.get('LISTENER_HOST', '0.0.0.0')
LISTENER_PORT = int(os.environ['LISTENER_PORT'])
SHARED_SECRET = os.environ['SHARED_SECRET']

BASE_DIR = Path(__file__).parent
with open(BASE_DIR.parent / 'machines.json') as f:
    MACHINES = json.load(f)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
log = logging.getLogger('woldb-listener')


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    log.info('Connection from %s', addr)
    try:
        data = await asyncio.wait_for(reader.readline(), timeout=10)
        request = json.loads(data.decode())

        if request.get('token') != SHARED_SECRET:
            log.warning('Authentication failed from %s', addr)
            response = {'status': 'error', 'message': 'Authentication failed'}
        else:
            machine_name = request.get('machine')
            if machine_name not in MACHINES:
                log.warning('Unknown machine requested: %s', machine_name)
                response = {'status': 'error', 'message': f'Unknown machine: {machine_name}'}
            else:
                machine = MACHINES[machine_name]
                mac = machine['mac']
                log.info('Sending WoL packet to %s (%s)', machine_name, mac)
                send_magic_packet(mac)
                log.info('WoL packet sent successfully to %s', machine_name)
                response = {
                    'status': 'ok',
                    'message': f'Magic packet sent to {machine_name}',
                }

        writer.write((json.dumps(response) + '\n').encode())
        await writer.drain()
    except asyncio.TimeoutError:
        log.warning('Client %s timed out', addr)
    except json.JSONDecodeError:
        log.warning('Invalid JSON from %s', addr)
    except Exception:
        log.exception('Error handling client %s', addr)
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_dir = BASE_DIR / 'certs'
    ssl_ctx.load_cert_chain(str(cert_dir / 'cert.pem'), str(cert_dir / 'key.pem'))

    server = await asyncio.start_server(
        handle_client, LISTENER_HOST, LISTENER_PORT, ssl=ssl_ctx,
    )
    addrs = ', '.join(str(s.getsockname()) for s in server.sockets)
    log.info('Listening on %s (TLS)', addrs)
    log.info('Configured machines: %s', ', '.join(MACHINES))

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info('Shutting down.')
