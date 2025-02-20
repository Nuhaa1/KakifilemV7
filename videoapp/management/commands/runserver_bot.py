from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings
import asyncio
import threading
import os
import sys
from dotenv import load_dotenv
import django.core.servers.basehttp
from django.core.servers.basehttp import WSGIServer, WSGIRequestHandler
from django.core.wsgi import get_wsgi_application
import socketserver

# Load environment variables
load_dotenv()

# Add bot directory to Python path
bot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../bot'))
if bot_dir not in sys.path:
    sys.path.insert(0, bot_dir)

from telegram_bot import main, init_client

class ThreadedWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = True

class ThreadedWSGIRequestHandler(WSGIRequestHandler):
    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError):
            pass

class Command(BaseCommand):
    help = 'Runs both Django server and Telegram bot'

    def handle(self, *args, **options):
        # Get Telegram credentials
        api_id = int(os.getenv('API_ID', '24492108'))
        api_hash = os.getenv('API_HASH', '82342323c63f78f9b0bc7a3ecd7c2509')
        bot_token = os.getenv('BOT_TOKEN', '7303681517:AAFQg_QXYScFJNeub-Cp8qmB7IIUNn_9E5M')

        # Run Django server in main thread but in non-blocking way
        def run_django():
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
            app = get_wsgi_application()
            server_address = ('127.0.0.1', 8000)
            
            httpd = ThreadedWSGIServer(server_address, ThreadedWSGIRequestHandler)
            httpd.set_app(app)
            
            self.stdout.write(f"Django server is running at http://{server_address[0]}:{server_address[1]}/")
            httpd.serve_forever()

        django_thread = threading.Thread(target=run_django)
        django_thread.daemon = True
        django_thread.start()

        self.stdout.write('Django server is starting...')
        self.stdout.write('Starting Telegram bot...')

        # Initialize the Telegram client with settings
        client = init_client(
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token
        )

        # Run the Telegram bot
        try:
            with client:
                client.loop.run_until_complete(
                    main(
                        api_id=api_id,
                        api_hash=api_hash,
                        bot_token=bot_token
                    )
                )
        except KeyboardInterrupt:
            self.stdout.write('Stopping services...')
        except Exception as e:
            self.stdout.write(f'Error running services: {e}')
