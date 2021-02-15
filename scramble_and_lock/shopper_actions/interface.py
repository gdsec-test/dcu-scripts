import abc
import json

from requests import post


class Action(object, metaclass=abc.ABCMeta):
    """
    Abstract base class for all shopper actions
    """
    HEADERS = {'Accept': 'application/json'}
    _confirm = 'n'
    _note = ''
    _question = 'Do you want to {} these shopper accounts? (y/n)'

    @abc.abstractmethod
    def confirm(self):
        """
        Determine whether a domain is hosted with a given brand
        :return:
        """

    @abc.abstractmethod
    def perform(self, _list_of_shoppers):
        """
        Determine whether a domain is registered with a given brand
        :param _list_of_shoppers: list of strings representing shopper accounts to action
        :return:
        """

    @abc.abstractmethod
    def get_message(self):
        """
        Returns a confirmation message
        :return: string message
        """

    @staticmethod
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

    @staticmethod
    def _is_affirmative(_response):
        """
        Did the user respond affirmatively?
        :param _response: string
        :return: boolean
        """
        if _response.lower() == 'y':
            return True
        return False

    @staticmethod
    def _get_jwt(cert, _url):
        """
        Attempt to retrieve the JWT associated with the cert/key pair from SSO
        :param cert: tuple of path to cert and key
        :param _url: string url to sso api
        :return: jwt string or None
        """
        try:
            response = post(_url, data={'realm': 'cert'}, cert=cert)
            response.raise_for_status()

            body = json.loads(response.text)
            # body = {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
            return 'sso-jwt {}'.format(body.get('data'))
        except Exception as e:
            print('EXCEPTION: {}'.format(e))
        return None

    def get_action_name(self):
        """
        Returns the name of the action instance
        :return: string
        """
        return self._my_action

    def get_confirm(self):
        """
        Just returns True if confirmation is 'y' or False otherwise
        :return: boolean
        """
        return self._is_affirmative(self._confirm)

    def set_note(self, _note):
        """
        Sets the note used to write to CRM
        :param _note: string
        :return:
        """
        self._note = _note
