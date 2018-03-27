import os
from typing import List

from logzero import logger as log

import settings
from appglobals import ROOT_DIR
from clients.botapiclients import IBotAPIClient
from clients.nlpclients import NLPEngine
from clients.voice import VoiceRecognitionClient
from core.context import ContextManager
from core.planningagent import IPlanningAgent
from core.understanding import MessageUnderstanding
from logic.intents import MEDIA_INTENT
from model import Update
from core.recorder import ConversationRecorder


class DialogManager:
    """
    Enriches incoming updates with a MessageUnderstanding and lets the PlanningAgent decide on the next actions to
    perform.
    """

    def __init__(self,
                 context_manager: ContextManager,
                 bot_clients: List[IBotAPIClient],
                 nlp_client: NLPEngine,
                 planning_agent: IPlanningAgent,
                 recorder: ConversationRecorder = None,
                 voice_recognition_client: VoiceRecognitionClient = None,
                 ):
        self.context_manager = context_manager
        self.bots = bot_clients
        self.nlp = nlp_client
        self.recorder = recorder
        self.voice = voice_recognition_client
        self.planning_agent = planning_agent

        for bot in bot_clients:
            bot.set_start_handler(self.start_callback)
            bot.add_plaintext_handler(self.text_update_received)
            bot.add_voice_handler(self.voice_received)
            bot.add_media_handler(self.media_received)

    def __get_client_by_name(self, client_name: str) -> IBotAPIClient:
        return next(x for x in self.bots if client_name == x.client_name)

    def start_callback(self, bot: IBotAPIClient, update: Update):
        update.understanding = MessageUnderstanding(
            text=update.message_text,
            intent='start')
        self._process_update(bot, update)

    def voice_received(self, bot: IBotAPIClient, update: Update):
        bot.show_typing(update.user)

        path = os.path.join(ROOT_DIR, 'assets', 'files')
        filepath = bot.download_voice(update.voice_id, path)

        converted = self.voice.convert_audio_ffmpeg(filepath, os.path.join(path, 'voice.flac'))

        text = self.voice.recognize(converted)
        if text is None:
            log.warning("Could not recognize user input.")
            return

        update.message_text = text
        log.debug(f"Voice message received: {text}")

        self.text_update_received(bot, update)

    def media_received(self, bot: IBotAPIClient, update: Update):
        update.understanding = MessageUnderstanding(None, MEDIA_INTENT, media_location=update.media_location)
        self._process_update(bot, update)

    def text_update_received(self, bot: IBotAPIClient, update: Update):
        self.nlp.insert_understanding(update)
        self._process_update(bot, update)

    def _process_update(self, bot, update):
        print()  # newline on incoming request, formats the logs a bit better
        context = self.context_manager.add_incoming_update(update)

        try:
            try:
                next_response = self.planning_agent.build_next_actions(context)
            except ForceReevaluation:
                # Some handlers require to reevaluate the template parameters
                next_response = self.planning_agent.build_next_actions(context)
        finally:
            context.dialog_states.update_step()

        actions = next_response.collect_actions()

        if self.recorder:
            self.recorder.record_dialog(update, actions, context.dialog_states)

        if settings.NO_DELAYS:
            # No delays while debugging
            for a in actions:
                a.delay = None

        try:
            bot.perform_actions(actions)
        except Exception as e:
            log.error("Error while processing update:")
            log.exception(e)
        context.add_actions(actions)

        update.save()


class ForceReevaluation(Exception):
    pass
