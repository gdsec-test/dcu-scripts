from requests import post
from .interface import Action


class LockShopper(Action):
    """
    Actions required when locking a shopper account
    """
    _my_action = 'lock'

    def __init__(self, _config):
        """
        :param _config: object containing required cert path and api url
        """
        self._headers = dict(Authorization=Action._get_jwt((_config.get('PATH_TO_SHOPLOCKED_CRT'),
                                                            _config.get('PATH_TO_SHOPLOCKED_KEY')),
                                                           _config.get('URL_SSO_API')))
        self._headers.update(self.HEADERS)
        self._url = _config.get('URL_SHOPLOCKED_API')

    def confirm(self):
        self._confirm = self._inquire(self._question.format(self._my_action))

    def get_message(self):
        return '{} Accounts: {}'.format(self._my_action.upper(), self._confirm)

    def set_note(self, _note):
        self._note = _note

    def perform(self, _list_of_shoppers):
        """
        Makes the REST call to ShopLocked API
        :param _list_of_shoppers: list of shopper users to perform an action for
        :return: Boolean, String
        """
        payload = {
            'creds': _list_of_shoppers,
            'note': self._note,
            'products': ['crm']
        }
        try:
            r = post(self._url, json=payload, headers=self._headers)
            if r.status_code not in [201, 504]:
                return False, 'FAILURE [status code:{}]'.format(r.status_code)
            else:
                return True, 'SUCCESS: {}'.format(r.text)
        except Exception as e:
            return False, 'Exception while updating block: {}'.format(e)
