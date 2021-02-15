import configparser

from shopper_actions.email import EmailShopper
from shopper_actions.interface import Action
from shopper_actions.lock import LockShopper
from shopper_actions.scramble import ScrambleShopper


class ActionShoppers:
    _source = './source.txt'  # File to read credentials from, 1 per line
    _valid = (True, '')

    def __init__(self, _bundle):
        """
        Constructor
        :param _bundle: int number of credentials to process at a time
        """
        if _bundle < 1:
            self._set_invalid('Number of shoppers to bundle must be at least 1')
        self._number_of_shoppers_to_bundle = _bundle
        self._fail_log = dict()
        self._shoppers_to_action = []
        self._extract_shoppers()

    def _set_invalid(self, _note):
        """
        If there is any major blocking issue reported, set valid to False to prevent all methods from functioning
        :param _note: string describing the blocking issue
        :return:
        """
        self._valid = (False, _note)

    def _is_valid(self):
        """
        All methods should call to ensure the instance is valid before executing method functionality
        :return:
        """
        if self._valid[1]:
            print(self._valid[1])
        return self._valid[0]

    def _extract_shoppers(self):
        """
        Reads file into _shoppers_to_action set
        :return:None
        """
        if self._is_valid():
            try:
                ticket_file = open(self._source, 'r')
                lines = ticket_file.readlines()
                for line in lines:
                    self._shoppers_to_action.append(line.strip())
            except Exception as e:
                self._set_invalid(e)

    def _capture_failure(self, _action, _message, _credential):
        """
        Create the run log structure and append values in appropriate keys.
        EXAMPLE STRUCTURE:
            {
                'scramble': {
                    'FAILURE [status code:401]': ['cred1', 'cred2', ...]
                },
                'lock': {
                    'FAILURE [status code:403]': ['cred3', 'cred4', ...]
                },
                'email': {
                    'Test Failure': ['cred5', 'cred2', ...]
                }
            }
        :param _action: string action class instance name
        :param _message: string error message
        :param _credential: string shopper credential
        :return: None
        """
        if self._is_valid():
            if _action not in self._fail_log:
                self._fail_log[_action] = dict()
            if _message not in self._fail_log[_action]:
                self._fail_log[_action][_message] = []
            self._fail_log[_action][_message].append(_credential)

    def action_shopper(self, _action_instance):
        """
        Generic function to kick off the desired shopper action(s)
        :param _action_instance: object instance
        :return: None
        """
        if self._is_valid():
            _action_string = _action_instance.get_action_name()

            for _batch_index in range(0, len(self._shoppers_to_action), self._number_of_shoppers_to_bundle):
                _shopper_batch = self._shoppers_to_action[_batch_index:
                                                          _batch_index + self._number_of_shoppers_to_bundle]

                _status, _message = _action_instance.perform(_shopper_batch)
                if _status:
                    print(_message)
                else:
                    if self._number_of_shoppers_to_bundle > 1:
                        # If the batch contained more than 1 credential, process each credential separately
                        for _single_shopper in _shopper_batch:
                            _status, _message = _action_instance.perform(_single_shopper)
                            if not _status:
                                self._capture_failure(_action_string, _message, _single_shopper)
                    else:
                        self._capture_failure(_action_string, _message, _shopper_batch)

    def print_fail_log(self):
        """
        Print the run log failures
        :return:
        """
        if self._fail_log:
            print(self._fail_log)


if __name__ == '__main__':
    """
    This script expects a source file of shopper users (named source.txt), 1 cred per line, and will
    batch them up into lock and/or scramble endpoint calls, printing the result of each call
    """
    NUMBER_OF_CREDENTIALS_TO_BUNDLE = 2  # The number of credentials to batch process.  int value between 1 & 100
    RUN_ENVIRONMENT = 'prod'

    config = configparser.ConfigParser()
    config.read('./settings.ini')

    _email = EmailShopper(config[RUN_ENVIRONMENT])
    _lock = LockShopper(config[RUN_ENVIRONMENT])
    _scramble = ScrambleShopper(config[RUN_ENVIRONMENT])

    _possible_actions = [_scramble, _lock, _email]

    # Canned run notes... if one is not provided, the script will prompt for a run note
    # Typically we dont check in commented code, but these notes have been used often, and you may be referred to
    # use one of them in the future.
    #
    # _run_note = "Customer's credentials identified in list of credentials stolen by commodity malware. Their password has been scrambled for their protection. Ensure the customer has reset their password recently, and review the customer's security details with the customer for accuracy."
    # _run_note = 'During a routine audit of our systems, we noticed some unusual activity on this account. In order to play it safe, security is asking for an admin lock/password reset'
    # _run_note = 'Scrambling password in relation to a security incident. Account is permanently closed.'
    # _run_note = "Password scrambled for customer's security. Password needs to be reset by the customer."
    # _run_note = "Password scrambled for customer's security. Password needs to be reset by the customer and the customer needs to review their DNS for accuracy and update where needed."

    _msg = ''
    for _action in _possible_actions:
        _action.confirm()
        _msg = '{}{}\n'.format(_msg, _action.get_message())

    if _msg != 'SCRAMBLE Accounts (MUST use shopper ids ONLY!): n\nLOCK Accounts: n\nEMAIL Shoppers (MUST use shopper ids ONLY!): y\n':
        if '_run_note' not in locals():
            _run_note = Action._inquire('Enter a valid run note (Leave blank for no note): ')
    else:
        _run_note = None

    _continue = Action._inquire('{}Run Note: "{}"\nProceed? (y/n)'.format(_msg, _run_note))
    if Action._is_affirmative(_continue):
        sl = ActionShoppers(NUMBER_OF_CREDENTIALS_TO_BUNDLE)
        for _action in _possible_actions:
            if _action.get_confirm():
                _action.set_note(_run_note)
                sl.action_shopper(_action)
        sl.print_fail_log()
