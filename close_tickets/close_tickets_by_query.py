import configparser
import requests
import time
import json

from datetime import datetime
from dcdatabase.phishstorymongo import PhishstoryMongo
from getpass import getuser

"""
Script to close tickets given a database query.
Use this script if you're asked to do something like: close Open or Paused phishing tickets older
 than 1/1/2021 (close reason resolved)
"""
def generate_jwt():
    response = requests.post(_config.get('API_TOKEN_URL'),
                             json={'username': _config.get('API_USER'), 'password': _config.get('API_PASS')},
                             params={'realm': 'idp'})
    print(f'response sso: {response.content}')
    body = json.loads(response.text)
    return body.get('data')

class ProductionAppConfig():
    # Prod Mongo DB Settings
    def __init__(self, _config):
        self.COLLECTION = _config.get('COLLECTION')
        self.DB = _config.get('DB')
        self.DB_USER = _config.get('DB_USER')
        self.DB_PASS = _config.get('DB_PASS')
        self.DB_IP = _config.get('DB_IP')
        mongo_cert = _config.get('MONGO_CLIENT_CERT')
        self.DBURL = f'mongodb://{self.DB_USER}:{self.DB_PASS}@{self.DB_IP}/?authSource={self.DB}&readPreference=primary&directConnection=true&tls=true&tlsCertificateKeyFile={mongo_cert}'


def _get_value(_question):
    """
    Get the value from the user
    :param _question: string
    :return: string
    """
    _response = input('\n{}'.format(_question))
    return _response.lstrip('\"\'').rstrip('\"\'')


def _inquire(_question):
    """
    Ask the user a question, force a non null response
    :param _question: string
    :return: string
    """
    while True:
        _answer = _get_value(_question)
        if _answer:
            break
    return _answer


def _is_affirmative(_response):
    """
    Did the user respond affirmatively?
    :param _response: string
    :return: boolean
    """
    if _response.lower() == 'y':
        return True
    return False


if __name__ in '__main__':
    CLOSE_REASON = 'admin_close'
    PAYLOAD = {'closed': 'true', 'close_reason': CLOSE_REASON}
    RUN_ENVIRONMENT = 'dev'
    _config_file = configparser.ConfigParser()
    _config_file.read('./close_tickets/settings.ini')
    _config = _config_file[RUN_ENVIRONMENT]
    HEADER = {'Authorization': f'sso-jwt {generate_jwt()}'}
    # HEADER = {'Authorization': _config.get("API_TOKEN")}

    _user = getuser()
    while True:
        _answer = _inquire('Do you want "{}" as your username in the actions sub-document? (y/n)'.format(_user))
        if _is_affirmative(_answer):
            break
        _user = _get_value('Enter username to use: ')

    #####################################################################
    #  The database query used to select tickets to close. !!BE CAREFUL!!
    _query = {
        'type': {'$in': ['PHISHING', 'MALWARE']},
        'phishstory_status': {'$in': ['OPEN', 'PAUSED']},
        'created': {'$lt': datetime.strptime('2023-06-01', '%Y-%m-%d')},
        'reporter': { '$nin': [ "129092584", "276848701" ] }
    }
    #####################################################################

    _answer = _inquire('Do you want to close tickets as "{}" with this query? (y/n)\n{} '.format(CLOSE_REASON, _query))
    if not _is_affirmative(_answer):
        exit('\n\nBailing...')

    _cursor = []
    try:
        _db = PhishstoryMongo(ProductionAppConfig(_config))
        _cursor = _db.find_incidents(_query)
    except Exception as e:
        exit('DB query failed. Check variable defined in settings file: {}'.format(e))
    _cnt = _success = 0

    for _row in _cursor:
        if _cnt % 10 == 0:
            time.sleep(1)
        _cnt += 1

        _ticket_id = _row.get('_id')
        _created_date = _row.get('created')

        try:
            _r = requests.patch('{}/{}'.format(_config.get('API_URL'), _ticket_id),
                                json=PAYLOAD,
                                headers=HEADER)
            if _r.status_code == 204:
                _success += 1
                print('{}: Closed ticket {}, created on {}'.format(_cnt, _ticket_id, _created_date))
                _db.update_actions_sub_document(_ticket_id, CLOSE_REASON, user=_user)
            else:
                print('{}: Unable to close ticket {} {}'.format(_cnt, _ticket_id, _r.content))
        except Exception as e:
            print('{}: Exception while closing ticket {} {}'.format(_cnt, _ticket_id, e))
    print('Process complete. Successfully closed {} records'.format(_success))
