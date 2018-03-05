import json
from abc import ABCMeta, abstractmethod
from pprint import pprint
from typing import List, TypeVar

import apiai
from dateutil.parser import parse

from core.understanding import MessageUnderstanding
from model import User

Update = TypeVar('Update')


class NLPEngine(metaclass=ABCMeta):
    @abstractmethod
    def insert_understanding(self, update: Update) -> MessageUnderstanding: pass

    @abstractmethod
    def get_user_entities(self, user: User) -> List[str]: pass


class DialogflowClient(NLPEngine):
    def __init__(self, token):
        self.ai = apiai.ApiAI(token)

    def perform_nlu(self, text, user_id):
        request = self.ai.text_request()

        request.lang = 'de'
        request.session_id = user_id
        request.query = text

        response = json.loads(request.getresponse().read())

        pprint(response)
        return response.get('result'), parse(response['timestamp'])

    def insert_understanding(self, update) -> MessageUnderstanding:
        result_obj, timestamp = self.perform_nlu(update.message_text, update.user.id)

        nlu = MessageUnderstanding(
            update.message_text,
            result_obj['metadata']['intentName'],
            result_obj['parameters'],
            result_obj.get('contexts'),
            score=result_obj['score'],
            date=timestamp
        )
        update.understanding = nlu
        return nlu

    def get_user_entities(self, user):
        request = self.ai.user_entities_request()

        response = request.getresponse()
        return json.loads(response.read())

    @staticmethod
    def extract_status(response: dict):
        """
        Returns a tuple of (status_code, errorType)
        """
        return response['status']['code'], response['status']['errorType']
