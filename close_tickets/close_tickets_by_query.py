import configparser
import requests
import time

from datetime import datetime
from dcdatabase.phishstorymongo import PhishstoryMongo

"""
Script to close tickets given a database query.
Use this script if you're asked to do something like: close Open or Paused phishing tickets older
 than 1/1/2021 (close reason resolved)
"""


class ProductionAppConfig():
    # Prod Mongo DB Settings
    def __init__(self, _config):
        self.COLLECTION = _config.get('COLLECTION')
        self.DB = _config.get('DB')
        self.DBURL = 'mongodb://{}:{}@{}/{}'.format(_config.get('DB_USER'),
                                                     _config.get('DB_PASS'),
                                                     _config.get('DB_IP'),
                                                     self.DB)


if __name__ in '__main__':
    # exit('Comment out this line if you want to close tickets')
    PAYLOAD = {'closed': 'true', 'close_reason': 'resolved'}
    RUN_ENVIRONMENT = 'prod'
    _config_file = configparser.ConfigParser()
    _config_file.read('./settings.ini')
    _config = _config_file[RUN_ENVIRONMENT]
    HEADER = {'Authorization': _config.get('API_TOKEN')}

    #####################################################################
    #  The database query used to select tickets to close. !!BE CAREFUL!!
    _query = {
        'type': 'PHISHING',
        'phishstory_status': {'$in': ['OPEN', 'PAUSED']},
        'created': {'$lt': datetime.strptime('2021-01-01', '%Y-%m-%d')}
    }
    #####################################################################

    try:
        _db = PhishstoryMongo(ProductionAppConfig(_config))
        _cursor = _db.find_incidents(_query)
    except Exception as e:
        exit('DB query failed. Check variable defined in settings file: {}'.format(e))
    _cnt = 0

    for _row in _cursor:
        if _cnt % 10 == 0:
            time.sleep(1)
        _cnt += 1
        _ticket_id = _row.get('_id')
        try:
            _r = requests.patch('{}/{}'.format(_config.get('API_URL'), _ticket_id),
                                json=PAYLOAD,
                                headers=HEADER)
            if _r.status_code == 204:
                print('{}: Closed {}'.format(_cnt, _ticket_id))
            else:
                print('{}: Unable to close ticket {} {}'.format(_cnt, _ticket_id, _r.content))
        except Exception as e:
            print('{}: Exception while closing ticket {} {}'.format(_cnt, _ticket_id, e))
