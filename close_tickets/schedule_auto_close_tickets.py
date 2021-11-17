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
    phishlabs = _config.get("PHISHLABS")
    malware_scanner = _config.get("MALWARE_SCANNER")
    _user = getuser()
    while True:
        _answer = _inquire('Do you want "{}" as your username in the actions sub-document? (y/n)'.format(_user))
        if _is_affirmative(_answer):
            break
        _user = _get_value('Enter username to use: ')

    n = datetime.utcnow()
    sixmonths = n - relativedelta.relativedelta(months=6)
    fifteendays = n - timedelta(hours=405)

    _phishing_query = {
        'type': 'PHISHING',
        'phishstory_status': 'OPEN',
        'reporter': {'$ne': phishlabs},
        'created': {'$gte': sixmonths}
    }
    _malware_hosted_query = {
        'type': 'MALWARE',
        'phishstory_status': 'OPEN',
        'reporter': {'$ne': malware_scanner},
        'hosted_status': "HOSTED",
        'created': {'$gte': sixmonths}
    }
    _spam_query = {
        'type': 'SPAM',
        'phishstory_status': 'OPEN',
        'created': {'$gte': fifteendays}
    }
    _phishlabs_query = {
        'type': 'PHISHING',
        'phishstory_status': 'OPEN',
        'reporter': phishlabs,
        'created': {'$gte': fifteendays}
    }
    _malware_registered_query = {
        'type': 'MALWARE',
        'phishstory_status': 'OPEN',
        'reporter': {'$ne': malware_scanner},
        'hosted_status': "REGISTERED",
        'created': {'$gte': fifteendays}
    }
    _malware_scanner_query = {
        'type': 'MALWARE',
        'phishstory_status': 'OPEN',
        'reporter': malware_scanner,
        'created': {'$gte': fifteendays}
    }

    _queries = [_phishing_query, _malware_hosted_query, _spam_query, _malware_scanner_query, _phishlabs_query,
                _malware_registered_query]

    _incidents = []
    try:
        _db = PhishstoryMongo(ProductionAppConfig(_config))
        for _query in _queries:
            _incidents += _db.find_incidents(_query)
    except Exception as e:
        exit('DB query failed. Check variable defined in settings file: {}'.format(e))
    _cnt = _success = 0

    for _row in _incidents:
        if _cnt % 10 == 0:
            time.sleep(1)
        _cnt += 1
        _ticket_id = _row.get('_id')
        _ticket_created = _row.get('created')
        now = datetime.utcnow()

        _header = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        _api_url = "http://localhost:5000"

        try:
            _type = _row.get('type')
            _reporter = _row.get('reporter')
            with sessions.Session() as session:
                if (_type == "PHISHING" and _reporter != phishlabs) or (
                        _type == "MALWARE" and _row.get("hosted_status") == "HOSTED" and _reporter != malware_scanner):
                    _close_date = _ticket_created + relativedelta.relativedelta(months=6)
                    diff = _close_date - now
                    period = diff.total_seconds()
                else:
                    _close_date = _ticket_created + relativedelta.relativedelta(hours=360)
                    diff = _close_date - now
                    period = diff.total_seconds()
                r = session.post(_api_url + '/closure/schedule/' + _ticket_id,
                                 data=json.dumps({'period': int(period)}), headers=_header)
                if r.status_code != 201:
                    print(_api_url + '/closure/schedule/' + _ticket_id)
                    print(f'Scheduling of {_ticket_id} failed with status code: {r.status_code}')
                else:
                    print("succesfully scheduleded")
                    _success += 1
        except Exception as e:
            print(f'Error in scheduling attempt on {_ticket_id}: {e}')
    print('Process complete. Successfully closed {} records'.format(_success))
