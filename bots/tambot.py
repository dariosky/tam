#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import django
from django.conf import settings
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logger = logging.getLogger('tam.bot')


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.


def about(bot, update):
    username = update.message.from_user.username
    logger.info("Help was asked by %s" % username)
    bot.sendMessage(update.message.chat_id,
                    text=("TAM bot - un aiuto digitale per le prenotazioni"
                          "\n\n"
                          "Tam invierà in questo canale le richieste di prenotazioni rapide.\n"
                          "Si può confermare la propria disponibilità ed interagire con il cliente."
                          )
                    )


def message_handler(bot, update):
    bot.sendMessage(update.message.chat_id, text="".join([x for x in update.message.text][::-1]))
    text = update.message.text
    username = update.message.from_user.username
    chat_type = update.message.chat.type
    logger.info("message from {username} in the {chat_type} chat".format(
        username=username,
        chat_type=chat_type
    ))


def error(bot, update, error):
    logger.error('Update "%s" caused error "%s"' % (update, error))


def run_tambot():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(settings.BOT_TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("about", about))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, message_handler))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    django.setup()

    logger.info('TaM Telegram Bot is running ...')
    run_tambot()
