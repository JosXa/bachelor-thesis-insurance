from model import *


def reset_answers():
    UserAnswers.drop_table(fail_silently=True, cascade=True)
    UserAnswers.create_table()


def reset_all():
    Update.drop_table(fail_silently=True, cascade=True)
    Update.create_table()
    User.drop_table(fail_silently=True, cascade=True)
    User.create_table()
    reset_answers()

if __name__ == '__main__':
    reset_all()
