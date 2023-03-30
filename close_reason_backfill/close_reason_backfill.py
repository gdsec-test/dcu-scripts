from dcdatabase.phishstorymongo import PhishstoryMongo
import configparser

class AppConfig():
    def __init__(self, _config):
        self.COLLECTION = _config.get('COLLECTION')
        self.DB = _config.get('DB')
        self.DB_USER = _config.get('DB_USER')
        self.DB_PASS = _config.get('DB_PASS')
        self.DB_IP = _config.get('DB_IP')
        mongo_cert = _config.get('MONGO_CLIENT_CERT')
        self.DBURL = f'mongodb://{self.DB_USER}:{self.DB_PASS}@{self.DB_IP}/?authSource={self.DB}&readPreference=primary&directConnection=true&tls=true&tlsCertificateKeyFile={mongo_cert}'

if __name__ in '__main__':
    RUN_ENVIRONMENT = 'dev'
    _config_file = configparser.ConfigParser()
    _config_file.read('./settings.ini')
    _config = _config_file[RUN_ENVIRONMENT]
    _db = PhishstoryMongo(AppConfig(_config))

    incidents = _db.find_incidents({
        'close_reason': 'resolved'
    }, limit=1000)

    for incident in incidents:
        print(incident["_id"])
        _db.update_incident(incident["_id"], {'close_reason': 'resolved_no_action'})

    incidents = _db.find_incidents({
        'close_reason': 'suspended'
    }, limit=1000)

    for incident in incidents:
        print(incident["_id"])
        _db.update_incident(incident["_id"], {'close_reason': 'suspended_after_warning'})
