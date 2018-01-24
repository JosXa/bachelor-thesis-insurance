from decouple import config

PORT = config('PORT', cast=int, default=5000)
APP_URL = 'https://bachelor-thesis.herokuapp.com/'
TEST_MODE = config('DEBUG', cast=bool, default=False)

DIALOGFLOW_ACCESS_TOKEN = config('DIALOGFLOW_ACCESS_TOKEN')
FACEBOOK_ACCESS_TOKEN = config('FACEBOOK_ACCESS_TOKEN')
TELEGRAM_ACCESS_TOKEN = config('TELEGRAM_ACCESS_TOKEN')
TWILIO_ACCESS_TOKEN = config('TWILIO_ACCESS_TOKEN')
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
DATABASE_URI = config('DATABASE_URI')

ENABLE_CONVERSATION_RECORDING = TEST_MODE

CONTEXT_LOOKUP_RECENCY = 15
