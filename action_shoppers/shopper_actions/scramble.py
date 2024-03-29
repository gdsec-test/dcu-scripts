from requests import post
from .interface import Action


class ScrambleShopper(Action):
    """
    Actions required when changing a shopper account password
    """
    _my_action = 'scramble'

    def __init__(self, _config):
        """
        :param _config: object containing required cert path and api url
        """
        self._headers = dict(Authorization=Action._get_jwt((_config.get('PATH_TO_SHOPLOCKED_CRT'),
                                                            _config.get('PATH_TO_SHOPLOCKED_KEY')),
                                                           _config.get('URL_SSO_API')))
        self._headers.update(self.HEADERS)
        self._url = _config.get('URL_SCRAMBLE_API')

    def confirm(self):
        self._confirm = self._inquire(self._question.format(self._my_action))

    def get_message(self):
        return '{} Accounts (MUST use shopper ids ONLY!): {}'.format(self._my_action.upper(), self._confirm)

    def perform(self, _list_of_shoppers):
        """
        Makes the REST call to the Scramble API
        :param _list_of_shoppers: list of shopper users to perform an action for
        :return: Boolean, String
        """
        payload = {
            'creds': _list_of_shoppers,
            'note': self._note
        }
        try:
            r = post(self._url, json=payload, headers=self._headers)
            if r.status_code not in [201]:
                return False, 'FAILURE [status code:{}]: {}'.format(r.status_code, _list_of_shoppers)
            else:
                return True, 'SUCCESS All shoppers not listed in failed or ignored succeeded {}'.format(r.text)
        except Exception as e:
            return False, '{}: Exception while updating block: {}'.format(e, _list_of_shoppers)
