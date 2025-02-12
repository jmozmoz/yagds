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

from .garage_door_state_machine import GarageDoor


class MQTTHandler(threading.Thread):
    # define callback
    def on_message(self, client, userdata, message):
        logger.info('received message: ' +
                    str(message.topic) +
                    ' = ' +
                    str(message.payload.decode('utf-8')))

        if message.topic == 'homie/door_sensor/reeds/lowerReed':
            pl = message.payload.decode('utf-8')
            if pl == '0':
                self.garage_door.lower_reed_zero()
            elif pl == '1':
                self.garage_door.lower_reed_one()

        if message.topic == 'homie/door_sensor/reeds/upperReed':
            pl = message.payload.decode('utf-8')
            if pl == '0':
                self.garage_door.upper_reed_zero()
            elif pl == '1':
                self.garage_door.upper_reed_one()
        if message.topic == 'homie/door_sensor/powerSupply/voltage':
            self.voltage = message.payload.decode('utf-8')

        if message.topic == 'homie/door_sensor/$stats/signal':
            self.signal_strength = message.payload.decode('utf-8')

        if message.topic == 'messagehomie/door_sensor/$stats/uptime':
            self.uptime = message.payload.decode('utf-8')

    def on_connect(self, client, userdata, rc, _):
        logger.info('Connected with result code ' + str(rc))
        self.mqttc.subscribe(self.config['topics_path'])

    def cancel(self):
        self.do_run = False
        self.mqttc.loop_stop()
        logger.info('mqtt stop')

    def run(self):
        self.mqttc.loop_start()
        logger.info('mqtt running...')
        while self.do_run:
            if self.garage_door.state != 'closed' and self.garage_door.last_send == 0:
                self.garage_door.send(
                    f'door state: {self.garage_door.state}'
                )
            self.garage_door.last_send = (
                (self.garage_door.last_send + 1) % int(self.config['remind_interval'])
            )

            if not self.in_queue.empty():
                new_state = self.in_queue.get()
                if new_state == 'open':
                    self.garage_door.to_open()
                elif new_state == 'closed':
                    self.garage_door.to_closed()
                elif new_state == 'reconnect':
                    self.mqttc.reconnect()

            time.sleep(1)
        logger.info('mqtt not running anymore...')

    def __init__(self, config, q, qq):
        super().__init__()
        self.garage_door = GarageDoor(lambda m: q.put(m))
        self.config = config
        self.in_queue = qq

        self.mqttc = paho.Client()
        self.mqttc.username_pw_set(self.config['username'],
                                   self.config['password'])
        self.mqttc.on_message = self.on_message
        self.mqttc.on_connect = self.on_connect
        self.mqttc.tls_set(os.path.expanduser(self.config['ca']))

        logger.info('connecting to broker ' + self.config['broker'])
        self.mqttc.connect(self.config['broker'], 8883, 60)
        logger.info('connected')

        self.do_run = True
        self.voltage = '0'
        self.signal_strength = '0'
        self.uptime = '0'


class TelegramBot(threading.Thread):
    def on_start(self, update, context):
        """Send a message when the command /start is issued."""
        update.message.reply_text('Hi!')
        if self._last_message:
            update.message.reply_text(self._last_message)
        user = update.message.from_user
        logger.info('You talk with user {} and his user ID: {} '.format(
            user['username'], user['id']))

    def on_state(self, update, context):
        """Explicitly set the state."""
        update.message.reply_text('Set state')
        user = update.message.from_user
        if self._last_message:
            update.message.reply_text(f'Old state: {self._last_message}')
        args = context.args
        logger.info(f'requested state: {args}')
        if args and len(args) > 0:
            if args[0] == 'closed' or args[0] == 'open':
                self.out_queue.put(args[0])
                update.message.reply_text(f'New state: {args[0]}')
            else:
                update.message.reply_text(f'invalid state: {args[0]}')

    def on_reconnect(self, update, context):
        """Reconnect to mqtt server to reset state to actual measured values."""
        update.message.reply_text('Reconnect')
        self.out_queue.put('reconnect')

    def error(self, bot, update, error):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, error)

    def run(self):
        while self.do_run:
            try:
                message = self.q.get(timeout=1)
                self._last_message = message
                logger.info(f'Send message to telegram: {message}')
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

    def __init__(self, telegram_config, q, qq):
        super().__init__()
        self.q = q
        self.out_queue = qq
        config = telegram_config
        self.chat_id = int(config['chat_id'])
        self.do_run = True
        self._last_message = ''

        # Create the EventHandler and pass it your bot's token.
        self.updater = Updater(config['token'])

        # Get the dispatcher to register handlers
        dp = self.updater.dispatcher

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler('start', self.on_start,
                       Filters.user(user_id=self.chat_id)))

        dp.add_handler(CommandHandler('state', self.on_state,
                       Filters.user(user_id=self.chat_id)))

        dp.add_handler(CommandHandler('reconnect', self.on_reconnect,
                       Filters.user(user_id=self.chat_id)))
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

    q = queue.Queue()
    qq = queue.Queue()

    mqtt_handler = MQTTHandler(config['MQTT'], q, qq)
    telegram_bot = TelegramBot(config['Telegram'], q, qq)

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
