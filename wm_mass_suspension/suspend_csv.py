import csv
import os
import requests
from datetime import datetime
from json import dumps, loads
from dcdatabase.phishstorymongo import PhishstoryMongo

"""
"""


class AppConfig():
    def __init__(self):
        self.COLLECTION = os.getenv('COLLECTION')
        self.DB = os.getenv('DB')
        self.DBURL = f'mongodb://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_IP")}/?authSource={self.DB}'
        self.GOCENTRAL_URL = os.getenv('GOCENTRAL_URL')
        self.GOCENTRAL_SSL_CERT = os.getenv('GOCENTRAL_SSL_CERT')
        self.GOCENTRAL_SSL_KEY = os.getenv('GOCENTRAL_SSL_KEY')
        self.SNOW_USER = os.getenv('SNOW_USER')
        self.SNOW_PASS = os.getenv('SNOW_PASS')
        self.SNOW_URL = os.getenv('SNOW_URL')
        self.SUSPENSION_NOTE = os.getenv(
            'SUSPENSION_NOTE', 'Auto-suspending W&M account')
        self.REPORTER = os.getenv('REPORTER', 'automation')


ORION_SUSPENSION_HEADERS = {
    'Content-Type': 'text/xml',
    'SOAPAction': 'http://schemas.orion.starfieldtech.com/account/Suspend'
}
ORION_SUSPENSION_PAYLOAD = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Suspend xmlns="http://schemas.orion.starfieldtech.com/account">
      <MessageID></MessageID>
      <Requests>
        <OperationRequest>
          <RequestIdx>123</RequestIdx>
          <Identifier>
            <SystemNamespace>GoDaddy</SystemNamespace>
            <ResellerId>1</ResellerId>
            <CustomerNum>{shopperid}</CustomerNum>
            <AccountUid>{guid}</AccountUid>
          </Identifier>
          <dtl>
            <RequestedBy>dcu</RequestedBy>
            <RequestedByLoginName>dcu</RequestedByLoginName>
            <ReasonForRequest>suspend for abuse</ReasonForRequest>
            <Messages xsi:nil="true" />
          </dtl>
          <objType>ACCOUNT</objType>
          <opType>ABUSE_SUSPEND</opType>
          <ObjectUid>{guid}</ObjectUid>
          <requestItems>
            <RequestItem>
                <ItemName>TYPE</ItemName>
                <ItemValue>ABUSE</ItemValue>
            </RequestItem>
          </requestItems>
        </OperationRequest>
      </Requests>
    </Suspend>
  </soap:Body>
</soap:Envelope>"""


def suspend_via_orion(accountId, shopper, settings):
    try:
        xml_body = ORION_SUSPENSION_PAYLOAD.format(
            guid=accountId, shopperid=shopper)
        r = requests.post(settings.GOCENTRAL_URL,
                          data=xml_body,
                          headers=ORION_SUSPENSION_HEADERS,
                          cert=(settings.GOCENTRAL_SSL_CERT,
                                settings.GOCENTRAL_SSL_KEY),
                          verify=False)
        if r.status_code not in [200]:
            print('Unable to suspend W&M product: {} - bad status code {}, body {}'.format(
                accountId, r.status_code, r.text))
            return False, r.status_code, r.text
        print('Suspended W&M ticket product: {}'.format(accountId))
        return True, 0, r.text
    except Exception as e:
        print('Unable to suspend W&M product: {} - {}'.format(accountId, e))
        return False, -1, str(e)


def create_snow_ticket(accountId, domain, closed_time, settings):
    try:
        data = {
            'u_type': 'PHISHING',
            'u_source': f'https://{domain}',
            'u_source_domain_or_ip': domain,
            'u_reporter': settings.REPORTER,
            'u_closed': True,
            'u_closed_date': closed_time,
            'u_info': f'{settings.SUSPENSION_NOTE} - {accountId}'
        }
        r = requests.post(settings.SNOW_URL + '/u_dcu_ticket',
                          auth=(settings.SNOW_USER, settings.SNOW_PASS),
                          headers={
                              'Accept': 'application/json',
                              'Content-Type': 'application/json'
                          },
                          data=dumps(data),
                          timeout=10)

        if r.status_code not in [201]:
            print('Unable to create snow ticket for: {} - bad status code {}, body {}'.format(
                domain, r.status_code, r.text))
            return False, ''

        snow_data = loads(r.content)
        ticket = snow_data['result']['u_number']
        print('Created Snow ticket {} for {}'.format(ticket, domain))
        return True, ticket
    except Exception as e:
        print('Unable to create snow ticket for: {} - {}'.format(domain, e))
        return False, ''


def create_mongodb_ticket(ticketId, domain, accountId, closed_time, settings):
    db = PhishstoryMongo(settings)
    data = {
        'type': 'PHISHING',
        'source': f'https://{domain}',
        'sourceDomainOrIp': domain,
        'reporter': settings.REPORTER,
        'closed': closed_time,
        'close_reason': f'{settings.SUSPENSION_NOTE} - {accountId}',
        'ticketId': ticketId
    }
    mongoId = db.add_new_incident(ticketId, data, status='CLOSED')
    return mongoId


def process_row(writer, row, settings):
    try:
        account = row['account_id']
        shopper = row['shopper_id']
        domain = row['domain_name']
        orion_result = ''
        orion_code = ''
        error = ''
        snow_result = ''
        snow_ticket = ''
        mongo_id = ''
        closed_time = str(datetime.utcnow())

        # Kick an event to orion.
        orion_result, orion_code, error = suspend_via_orion(
            account, shopper, settings)
        orion_result = True
        # Only create the tickets if we were able to suspend the web site.
        if orion_result:
            # Create tracking tickets in SNOW.
            snow_result, snow_ticket = create_snow_ticket(
                account, domain, closed_time, settings)
            if snow_result:
                # And finish adding the link to mongo.
                mongo_id = create_mongodb_ticket(
                    snow_ticket, domain, account, closed_time, settings)
    except Exception as e:
        print('Failed to suspend {} because {}'.format(
            account, e))
        error = str(e)
    finally:
        writer.writerow({
            'account_id': account,
            'shopper_id': shopper,
            'orion-result': orion_result,
            'error': error,
            'snow-result': snow_result,
            'snow-ticket': snow_ticket,
            'mongo-id': mongo_id
        })


if __name__ in '__main__':
    settings = AppConfig()
    fields = ['account_id', 'shopper_id',
              'orion-result',
              'error', 'snow-result', 'snow-ticket', 'mongo-id']
    with open('results.csv', 'w') as csvfile:
        # Build output CSV.
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        with open('accounts_to_suspend.csv') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                process_row(writer, row, settings)
