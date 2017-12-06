from threading import Thread

from logzero import logger
from telegram import Update
from typing import List

import settings
from appglobals import app
from clients.facebook import FacebookClient
from clients.telegram import TelegramClient

threads = list()  # type: List[Thread]

USER_SEQ = dict()


def error_handler(error):
    logger.exception(error)


def test_handler_tg(client, update: Update):
    client.send_message(update.effective_user.id, update.message.text)


def test_handler_fb(client, event):
    sender_id = event.sender_id
    recipient_id = event.recipient_id
    time_of_message = event.timestamp
    message = event.message

    seq = message.get("seq", 0)
    message_id = message.get("mid")
    app_id = message.get("app_id")
    metadata = message.get("metadata")

    message_text = message.get("text")
    message_attachments = message.get("attachments")
    quick_reply = message.get("quick_reply")

    seq_id = sender_id + ':' + recipient_id
    if USER_SEQ.get(seq_id, -1) >= seq:
        print("Ignore duplicated request")
        return None
    else:
        USER_SEQ[seq_id] = seq

    if quick_reply:
        quick_reply_payload = quick_reply.get('payload')
        print("quick reply for message %s with payload %s" % (message_id, quick_reply_payload))

        client.page.send(sender_id, "Quick reply tapped")

    if message_text:
        client.send_message(sender_id, message_text)
    elif message_attachments:
        client.send_message(sender_id, "Message with attachment received")


def main():
    fb = FacebookClient(
        app,
        settings.FACEBOOK_ACCESS_TOKEN
    )
    fb.initialize()

    tg = TelegramClient(
        app,
        settings.APP_URL,
        settings.TELEGRAM_ACCESS_TOKEN
    )
    tg.initialize()

    tg.add_plaintext_handler(test_handler_tg)
    fb.add_plaintext_handler(test_handler_fb)

    tg.start_listening()
    fb.start_listening()

    app.run(host='0.0.0.0', port=settings.PORT)


if __name__ == '__main__':
    main()
