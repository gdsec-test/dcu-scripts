import configparser
import json
from requests import post


class ScrambleAndLock:
    _headers = {'Accept': 'application/json'}
    _endpoint_lock = 'lockAdmin'
    _endpoint_scramble = 'scramblePassword'
    _source = './source.txt'  # File to read credentials from, 1 per line
    _url = 'shoplocked.api.int.godaddy.com'
    _sso_endpoint = 'https://sso.godaddy.com/v1/secure/api/token'
    NUMBER_OF_CREDS_TO_BUNDLE = 1  # The number of credentials to batch process.  If one fails, the whole batch fails
    _cnt = 0

    def __init__(self, _cert, _key, note, product='crm'):
        """
        Constructor
        :param _cert: string path to the zeus certificate file
        :param _key: string path to the zeus key file
        :param note: string note which will be added to CRM
        :param product: string, 'crm' by default, since that's the only product we lock/scramble for
        """
        self._note = note
        self._products = product
        self._headers.update({'Authorization': self._get_jwt((_cert, _key))})

    def _perform(self, action, list_of_shoppers):
        """
        Makes the REST call to ShopLocked
        :param action: string representing endpoint to call
        :param list_of_shoppers: list of shopper users to perform an action for
        :return: Boolean, String
        """
        payload = {
            'creds': list_of_shoppers,
            'note': self._note,
            'products': [self._products]
        }
        try:
            r = post('https://{}/{}'.format(self._url, action), json=payload, headers=self._headers)
            if r.status_code not in [201, 504]:
                return False, 'FAILURE [status code:{}]: {}'.format(r.status_code, list_of_shoppers)
            else:
                self._cnt += 1
                return True, 'SUCCESS: {}: {}'.format(self._cnt, r.text)
        except Exception as e:
            return False, '{}: Exception while updating block: {}'.format(e, list_of_shoppers)

    def _extract_shoppers(self, endpoint, number_to_process=100):
        """
        Reads file and batches in number_to_process, sending batches to either scramble or lock
        :param endpoint: string representing endpoint to call
        :param number_to_process: integer representing number of shopper users to batch in a REST call
        :return:
        """
        if number_to_process < 1:
            raise Exception('Number of shoppers to batch must be at least 1')
        cnt = 0
        shoppers = []
        ticket_file = open(self._source, 'r')
        lines = ticket_file.readlines()
        for line in lines:
            shoppers.append(line.strip())
            cnt += 1
            if cnt % number_to_process == 0:
                status, message = self._perform(endpoint, shoppers)
                print(message)
                # Check for failure and that shoppers were batched in a list greater than 1 shopper,
                #  because there are cases where 1 or more shoppers in a batch is bad, causing the
                #  whole batch to fail scrambling
                if not status and number_to_process > 1:
                    # If there was a failure, re-scramble 1 shopper at a time
                    for shopper in shoppers:
                        _, message = self._perform(endpoint, shopper)
                        print(message)
                shoppers = []
        if shoppers:
            self._perform(endpoint, shoppers)

    def scramble(self):
        """
        Endpoint to only scramble shopper's password
        :return:
        """
        self._extract_shoppers(self._endpoint_scramble, self.NUMBER_OF_CREDS_TO_BUNDLE)

    def lock(self):
        """
        Endpoint to only lock shopper's account
        :return:
        """
        self._extract_shoppers(self._endpoint_lock, self.NUMBER_OF_CREDS_TO_BUNDLE)

    def _get_jwt(self, cert):
        """
        Attempt to retrieve the JWT associated with the cert/key pair from SSO
        :param cert:
        :return: jwt string or None
        """
        try:
            response = post(self._sso_endpoint, data={'realm': 'cert'}, cert=cert)
            response.raise_for_status()

            body = json.loads(response.text)
            return body.get('data')  # {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
        except Exception as e:
            print('EXCEPTION: {}'.format(e))
        return None


def _inquire(_question):
    """
    Ask the user a question, force a non null response
    :param _question: string
    :return: string
    """
    while True:
        _answer = input('\n{} '.format(_question))
        _answer = _answer.lstrip('\"\'').rstrip('\"\'')
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


if __name__ == '__main__':
    """
    This script expects a source file of shopper users (named source.txt), 1 cred per line, and will
    batch them up into lock and/or scramble endpoint calls, printing the result of each call
    """
    config = configparser.ConfigParser()
    config.read('./settings.ini')

    # Canned run notes... if one is not provided, the script will prompt for a run note
    # Typically we dont check in commented code, but these notes have been used often, and you may be referred to
    # use one of them in the future.
    # _run_note = "Customer's credentials identified in list of credentials stolen by commodity malware. Their password has been scrambled for their protection. Ensure the customer has reset their password recently, and review the customer's security details with the customer for accuracy."
    # _run_note = 'During a routine audit of our systems, we noticed some unusual activity on this account. In order to play it safe, security is asking for an admin lock/password reset'
    # _run_note = 'Scrambling password in relation to a security incident. Account is permanently closed.'
    # _run_note = "Password scrambled for customer's security. Password needs to be reset by the customer."

    _lock = _inquire('Do you want to lock these accounts? (y/n)')
    _scramble = _inquire('Do you want to scramble these accounts? (y/n)')
    if '_run_note' not in locals():
        _run_note = _inquire('Enter a valid run note: ')

    _msg = 'LOCK Accounts: {}\nSCRAMBLE Accounts: {}\nRun Note: "{}"\nProceed? (y/n)'.format(_lock.upper(),
                                                                                             _scramble.upper(),
                                                                                             _run_note)
    _continue = _inquire(_msg)

    if _is_affirmative(_continue):
        sl = ScrambleAndLock(config['default'].get('PATH_TO_CRT'),
                             config['default'].get('PATH_TO_KEY'),
                             _run_note)
        if _is_affirmative(_lock):
            sl.lock()
        if _is_affirmative(_scramble):
            sl.scramble()
