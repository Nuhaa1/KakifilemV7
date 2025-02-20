from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys  # Add this import
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add bot directory to Python path
bot_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../bot'))
if bot_dir not in sys.path:
    sys.path.insert(0, bot_dir)

from telegram_bot import main, init_client

class Command(BaseCommand):
    help = 'Runs the Telegram bot'

    def handle(self, *args, **options):
        # Get Telegram credentials
        api_id = int(os.getenv('API_ID', '24492108'))
        api_hash = os.getenv('API_HASH', '82342323c63f78f9b0bc7a3ecd7c2509')
        bot_token = os.getenv('BOT_TOKEN', '7303681517:AAFQg_QXYScFJNeub-Cp8qmB7IIUNn_9E5M')

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
            self.stdout.write('Stopping bot...')
        except Exception as e:
            self.stdout.write(f'Error running bot: {e}')
