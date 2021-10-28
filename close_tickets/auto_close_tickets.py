import configparser
import json

import requests
import time
from dateutil import relativedelta
from datetime import datetime, timedelta
from dcdatabase.phishstorymongo import PhishstoryMongo
from getpass import getuser

from requests import sessions

"""
Script to close tickets based on criteria discussed in auto-closure design:
phishing tickets and hosted malware older than 6 months
phislabs, malware scanner, spam, and registered malware older then 15 days 
"""


def generate_jwt():
    response = requests.post(_config.get('API_TOKEN_URL'),
                             json={'username': _config.get('API_USER') , 'password': _config.get('API_PASS')},
                             params={'realm': 'idp'})
    print(f'response sso: {response.content}')
    body = json.loads(response.text)
    return body.get('data')


class ProductionAppConfig():
    # Prod Mongo DB Settings
    def __init__(self, _config):
        self.COLLECTION = _config.get('COLLECTION')
        self.DB = _config.get('DB')
        self.DBURL = 'mongodb://{}:{}@{}/{}'.format(_config.get('DB_USER'),
                                                    _config.get('DB_PASS'),
                                                    _config.get('DB_IP'),
                                                    self.DB)


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
    CLOSE_REASON = 'resolved'
    PAYLOAD = {'closed': 'true', 'close_reason': CLOSE_REASON}
    RUN_ENVIRONMENT = 'dev'
    _config_file = configparser.ConfigParser()
    _config_file.read('./settings.ini')
    _config = _config_file[RUN_ENVIRONMENT]
    HEADER = {'Authorization': generate_jwt()}
    ONE_WEEK = 604800

    _user = getuser()
    while True:
        _answer = _inquire('Do you want "{}" as your username in the actions sub-document? (y/n)'.format(_user))
        if _is_affirmative(_answer):
            break
        _user = _get_value('Enter username to use: ')

    phishlabs = "1054985"
    malware_scanner = "2122818"
    n = datetime.utcnow()
    sixmonths = n - relativedelta.relativedelta(months=6)
    fifteendays = n - timedelta(hours=405)

    _phishing_query = {
        'type': 'PHISHING',
        'phishstory_status': {'$in': ['OPEN', 'PAUSED']},
        'reporter': {'$ne': phishlabs},
        'created': {'$lte': sixmonths}
    }
    _malware_hosted_query = {
        'type': 'MALWARE',
        'phishstory_status': {'$in': ['OPEN', 'PAUSED']},
        'reporter': {'$ne': malware_scanner},
        'hosted_status': "HOSTED",
        'created': {'$lte': sixmonths}
    }
    _spam_query = {
        'type': 'SPAM',
        'phishstory_status': {'$in': ['OPEN', 'PAUSED']},
        'created': {'$lte': fifteendays}
    }
    _phishlabs_query = {
        'type': 'PHISHING',
        'phishstory_status': {'$in': ['OPEN', 'PAUSED']},
        'reporter': phishlabs,
        'created': {'$lte': fifteendays}
    }
    _malware_registered_query = {
        'type': 'MALWARE',
        'phishstory_status': {'$in': ['OPEN', 'PAUSED']},
        'reporter': {'$ne': malware_scanner},
        'hosted_status': "REGISTERED",
        'created': {'$lte': fifteendays}
    }
    _malware_scanner_query = {
        'type': 'MALWARE',
        'phishstory_status': {'$in': ['OPEN', 'PAUSED']},
        'reporter': malware_scanner,
        'created': {'$lte': fifteendays}
    }

    _queries = [_phishing_query, _malware_hosted_query, _spam_query, _malware_scanner_query, _phishlabs_query,
                _malware_registered_query]


    _incidents = []
    try:
        _db = PhishstoryMongo(ProductionAppConfig(_config))
        for _query in _queries:
            print(_query)
            _incidents += _db.find_incidents(_query)
    except Exception as e:
        exit('DB query failed. Check variable defined in settings file: {}'.format(e))
    _cnt = _success = 0

    for _row in _incidents:
        if _cnt % 10 == 0:
            time.sleep(1)
        _cnt += 1
        _ticket_id = _row.get('_id')
        _ticket_last_modified = _row.get('last_modified')
        now = datetime.utcnow()
        diff = now - timedelta(hours=72)
        _header = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if diff <= _ticket_last_modified <= now:
            _api_url = "http://localhost:5000"
            try:
                with sessions.Session() as session:
                    r = session.post(_api_url + '/closure/schedule/' + _ticket_id,
                                     data=json.dumps({'period': ONE_WEEK}), headers=_header)
                    if r.status_code != 201:
                        print(_api_url + '/closure/schedule' + _ticket_id)
                        print(f'Scheduling of {_ticket_id} failed with status code: {r.status_code}')
                    else:
                        print("succesfully scheduleded")
            except Exception as e:
                print(f'Error in scheduling attempt on {_ticket_id}: {e}')
        else:
            try:
                print('{}/{}'.format(_config.get('API_URL'), _ticket_id))
                _r = requests.patch('{}/{}'.format(_config.get('API_URL'), _ticket_id),
                                    json=PAYLOAD,
                                    headers=HEADER)
                if _r.status_code == 204:
                    _success += 1
                    print('{}: Closed {}'.format(_cnt, _ticket_id))
                    _db.update_actions_sub_document(_ticket_id, CLOSE_REASON, user=_user)
                else:
                    print('{}: Unable to close ticket {} {}'.format(_cnt, _ticket_id, _r.content))
            except Exception as e:
                print('{}: Exception while closing ticket {} {}'.format(_cnt, _ticket_id, e))
    print('Process complete. Successfully closed {} records'.format(_success))
