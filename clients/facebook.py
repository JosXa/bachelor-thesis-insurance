# -*- coding: utf-8 -*-
import logging
import time
import traceback
from typing import Callable, List, TypeVar

import dateutil
from fbmq import Event, NotificationType, Page, QuickReply
from flask import request

from clients.botapiclients import IBotAPIClient
from model import Update, User

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

ChatAction = TypeVar('ChatAction')


class FacebookClient(IBotAPIClient):

    def __init__(self, app, token):
        self._app = app
        self._token = token

        self._page = None  # type: Page
        self._error_handler = None  # type: Callable[Exception]

    @property
    def client_name(self):
        return 'facebook'

    def unify_update(self, event: Event):
        ud = Update()
        ud.original_update = event
        ud.client_name = self.client_name
        ud.message_id = event.message_mid
        print(event.timestamp)
        ud.datetime = dateutil.parser.parse(event.timestamp)

        ud.user, created = User.get_or_create(facebook_id=event.sender_id)
        if created:
            ud.user.save()

        if hasattr(event, 'message_text'):
            ud.message_text = event.message_text
        ud.save()
        return ud

    def initialize(self):
        self._page = Page(self._token)
        self._page.show_starting_button("START_BOT")

        # Add webhook handlers
        self._app.add_url_rule('/', 'index', self._authentication, methods=['GET'])
        self._app.add_url_rule('/', 'request', self._webhook, methods=['POST'])

        # try:
        #     self.page.send(1441586482543309, "Up and running.")
        # except:
        #     print("Could not contact 1441586482543309.")

    def perform_actions(self, actions: List[ChatAction]):
        try:
            for action in actions:
                user_id = action.peer.facebook_id

                if action.show_typing:
                    self._page.typing_on(user_id)
                if action.delay:
                    time.sleep(action.delay.value)

                quick_replies = None
                if action.action_type == ChatAction.Type.ASKING_QUESTION:
                    if action.choices:
                        quick_replies = [QuickReply(title=x, payload=f"test_{x}") for x in action.choices]

                self._page.send(user_id,
                                action.render(),
                                quick_replies=quick_replies)
        except Exception as e:
            if self._error_handler:
                self._error_handler(e)
            else:
                traceback.print_exc()

    def _authentication(self):
        all_args = request.args
        if 'hub.challenge' in all_args:
            return all_args['hub.challenge']

    def _webhook(self):
        self._page.handle_webhook(request.get_data(as_text=True))
        return "ok"

    def __shutdown_server(self):
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    def start_listening(self):
        pass

    def stop_listening(self):
        self.__shutdown_server()

    def add_plaintext_handler(self, callback):
        # XXX: An issue was written to fbmq on GitHub to expose the `page` attribute as a public member
        self._page._webhook_handlers['message'] = lambda event: callback(self, self.unify_update(event))

    def set_start_handler(self, callback):
        pass

    def _send_message(self, recipient: User, text):
        """
        Sends a markdown-formatted message to the `recipient`.
        """
        self._page.send(recipient.facebook_id,
                        text,
                        callback=None,
                        notification_type=NotificationType.REGULAR)

    def add_error_handler(self, callback):
        self._error_handler = callback


"""
import logging
import random

from decouple import config
from fbmq import QuickReply, Event
from fbpage import page
from flask import request, Flask

import settings
from model import User
# parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# os.sys.path.insert(0, parentdir)
log = logging.getLogger(__name__)

app = Flask(__name__)

page.show_starting_button("START_BOT")


@app.route('/', methods=['POST'])
def webhook():
    page.handle_webhook(request.get_data(as_text=True))
    return "ok"


@page.handle_delivery
def delivery(event: Event):
    pass


# @page.handle_referral
# def referral(event: Event):
#     user = User.from_event(event)
#     user.referral = event.referral_ref
#     user.save()
#     start(None, event)


@page.callback(['START_BOT'])
def start_handler(payload, event):
    user = User.from_event(event)

    quick_replies = [
        QuickReply(title="Yeah, sure", payload="yes-more-info"),
    ]

    page.send(user.sender_id,
              "STARTED",
              quick_replies=quick_replies)


@page.handle_message
def message_handler(event: Event):
    query = event.message_text.lower()

    if query == 'start':
        return start(None, event)
    elif query == 'love':
        page.send(1433118220058887, random.choice(loveyous))
        return

        # start(None, event)

def start():
    log.info("Listening...")
    app.run(host=config('WEBHOOK_URL'), port=config('WEBHOOK_PORT'), ssl_context=(
        '/home/joscha/cert/josxa.jumpingcrab.com/fullchain.pem',
        '/home/joscha/cert/josxa.jumpingcrab.com/privkey.pem'))
"""
