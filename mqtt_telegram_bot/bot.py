from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import os
import argparse
import configparser

import paho.mqtt.client as paho
from telegram.ext import Updater, CommandHandler, Filters
import telegram
import logging
import threading
import queue
import time


class MQTTHandler(threading.Thread):
    # define callback
    def on_message(self, client, userdata, message):
        logger.debug('received message =' +
                     str(message.payload.decode('utf-8')))
        self.q.put(message.payload.decode('utf-8'))

    def on_connect(self, client, userdata, rc, _):
        logger.info('Connected with result code ' + str(rc))
        self.mqttc.subscribe('outTopic')

    def cancel(self):
        self.do_run = False
        self.mqttc.loop_stop()
        logger.info('mqtt stop')

    def run(self):
        self.mqttc.loop_start()
        logger.info('mqtt running...')
        while self.do_run:
            time.sleep(1)
        logger.info('mqtt not running anymore...')

    def __init__(self, broker, ca, q):
        super().__init__()
        self.q = q

        self.mqttc = paho.Client()
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.tls_set(ca)

        logger.info('connecting to broker ' + broker)
        self.mqttc.connect(broker, 8883, 60)
        logger.info('connected')

        self.do_run = True


class TelegramBot(threading.Thread):
    def on_start(self, bot, update):
        """Send a message when the command /start is issued."""
        update.message.reply_text('Hi!')
        user = update.message.from_user
        logger.info('You talk with user {} and his user ID: {} '.format(
            user['username'], user['id']))

    def error(self, bot, update, error):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, error)

    def run(self):
        while self.do_run:
            try:
                message = self.q.get(timeout=1)
                self.updater.bot.send_message(self.chat_id, text=message)
            except queue.Empty:
                pass
            except telegram.error.Unauthorized:
                logger.debug('bot not connected')
            except Exception as e:
                logger.debug(e)

        self.updater.stop()
        logger.info('stop telegram bot')

    def cancel(self):
        self.do_run = False

    def __init__(self, token, chat_id, q):
        super().__init__()
        self.q = q
        self.chat_id = chat_id
        self.do_run = True

        # Create the EventHandler and pass it your bot's token.
        self.updater = Updater(token)

        # Get the dispatcher to register handlers
        dp = self.updater.dispatcher

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler('start', self.on_start,
                       Filters.user(user_id=chat_id)))

        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        self.updater.start_polling()


def main():
    __version__ = '0.0.1'

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="store intermediate results",
                        action="store_true")
    parser.add_argument("-c", "--conf_file", help="Specify config file",
                        metavar="FILE",
                        default=os.path.expanduser(
                            "~/.mqtt_telegram_bot.ini"))
    parser.add_argument('-V', '--version', action='version',
                        version=__version__)
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    config = configparser.ConfigParser()
    config.read([args.conf_file])

    ca = os.path.expanduser(config.get('MQTT', 'ca'))
    broker = config.get('MQTT', 'broker')
    token = config.get('Telegram', 'token')
    chat_id = config.get('Telegram', 'chat_id')

    q = queue.Queue()

    mqtt_handler = MQTTHandler(broker, ca, q)
    telegram_bot = TelegramBot(token, chat_id, q)

    mqtt_handler.daemon = True
    telegram_bot.daemon = True

    mqtt_handler.start()
    telegram_bot.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mqtt_handler.cancel()
        telegram_bot.cancel()

    mqtt_handler.join()
    telegram_bot.join()


if __name__ == '__main__':
    # Enable logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    logger = logging.getLogger(__name__)

    main()
