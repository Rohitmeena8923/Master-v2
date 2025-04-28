import os

class Config(object):
    BOT_TOKEN = os.environ.get("7012934382:AAHd7-DqrVkFYzWdIxkarwC3KnYNVwrKy3A")
    API_ID = int(os.environ.get("27775431"))
    API_HASH = os.environ.get("b70bb1d45a1d05236671d4cc615e40f9")
    VIP_USER = os.environ.get('VIP_USERS', '6414266397').split(',')
    VIP_USERS = [int(6414266397) for user_id in VIP_USER]
