import datetime
import json
from abc import ABCMeta, abstractmethod

import apiai

from model import User

from typing import List, TypeVar
from dateutil.parser import parse
Update = TypeVar('Update')


class MessageUnderstanding:
    def __init__(self, intent, parameters, contexts, date=None, score=None):
        self.intent = intent
        self.parameters = parameters
        self.contexts = contexts,
        self.score = score
        self.date = date if date else datetime.datetime.now()

    def __str__(self):
        return f"{self.intent}\n[{', '.join(self.parameters)}] - [{', '.join(self.contexts)}]"


class NLPEngine(metaclass=ABCMeta):
    @abstractmethod
    def insert_understanding(self, update: Update) -> MessageUnderstanding: pass

    @abstractmethod
    def get_user_entities(self, user: User) -> List[str]: pass


class DialogflowClient(NLPEngine):
    def __init__(self, token):
        self.ai = apiai.ApiAI(token)

    def insert_understanding(self, update) -> MessageUnderstanding:
        request = self.ai.text_request()

        request.lang = 'de'
        request.session_id = update.user.id
        request.query = update.message_text

        response = json.loads(request.getresponse().read())
        result_obj = response.get('result')

        nlu = MessageUnderstanding(
            result_obj['metadata']['intentName'],
            result_obj['parameters'],
            result_obj.get('contexts'),
            score=result_obj['score'],
            date=parse(response['timestamp'])
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
