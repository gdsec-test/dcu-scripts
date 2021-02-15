import json
import requests
from mock import patch
from http import HTTPStatus
from nose.tools import assert_is_none, assert_equal, assert_false, assert_true

from action_shopper import ActionShoppers
from shopper_actions.scramble import ScrambleShopper
from shopper_actions.interface import Action

POST_DATA = {"data": "test_jwt"}


class MockResponse(requests.Response):
    status_code = 200
    text = json.dumps({"data": POST_DATA})


class TestScramble:
    CERT = 'test_cert'
    CONFIG = {
        'PATH_TO_SCRAMBLE_CRT': '',
        'PATH_TO_SCRAMBLE_KEY': '',
        'URL_SCRAMBLE_API': '',
        'URL_SSO_API': ''
    }
    LIST_OF_SHOPPERS = ['test_shoppers']
    NO = 'N'
    TEST_QUESTION = 'Test Question'
    URL = 'http://test.url'
    YES = 'Y'

    @classmethod
    @patch('shopper_actions.interface.post')
    def setup_class(cls, mock_post):
        """
        :return: None
        """
        cls._mr = MockResponse()
        cls._mr.status_code = HTTPStatus.CREATED
        mock_post.return_value = cls._mr
        cls._actions = ActionShoppers(1)
        cls._scramble = ScrambleShopper(cls.CONFIG)

    @patch('builtins.input', return_value=YES)
    def test_inquire_yes(self, mock_input):
        """
        Test _inquire when user enters 'Y'
        :param mock_input:
        :return: None
        """
        assert_equal(self.YES, Action._inquire('Test question'))

    @patch('builtins.input', return_value=NO)
    def test_inquire_no(self, mock_input):
        """
        Test _inquire when user enters 'N'
        :param mock_input:
        :return: None
        """
        assert_equal(self.NO, Action._inquire('Test question'))

    def test_is_affirmative_yes(self):
        """
        _is_affirmative should return True when provided 'Y'
        :return: None
        """
        assert_true(Action._is_affirmative(self.YES))

    def test_is_affirmative_no(self):
        """
        _is_affirmative should return False when provided anything but 'Y'
        :return: None
        """
        assert_false(Action._is_affirmative(self.NO))

    @patch('shopper_actions.interface.post')
    def test_get_jwt_success(self, mock_post):
        """
        Test when _get_jwt() returns successfully 201
        :param mock_post:
        :return: None
        """
        self._mr.status_code = HTTPStatus.CREATED
        mock_post.return_value = self._mr
        expected_value = 'sso-jwt {}'.format(POST_DATA)
        assert_equal(expected_value, Action._get_jwt(self.CERT, self.URL))
        mock_post.assert_called()

    @patch('shopper_actions.interface.post')
    def test_get_jwt_fail(self, mock_post):
        """
        Test when _get_jwt() returns failed 400
        :param mock_post:
        :return: None
        """
        self._mr.status_code = HTTPStatus.BAD_REQUEST
        mock_post.return_value = self._mr
        assert_is_none(Action._get_jwt(self.CERT, self.URL))
        mock_post.assert_called()

    @patch('shopper_actions.scramble.post')
    def test_perform_success(self, mock_post):
        """
        Test when _perform() returns successfully 201
        :param mock_post:
        :return: None
        """
        self._mr.status_code = HTTPStatus.OK
        mock_post.return_value = self._mr
        success, message = self._scramble.perform(self.LIST_OF_SHOPPERS)
        assert_true(success)
        assert_equal('SUCCESS: {"data": {"data": "test_jwt"}}', message)
        mock_post.assert_called()

    @patch('shopper_actions.scramble.post')
    def test_perform_fail(self, mock_post):
        """
        Test when _perform() returns failed 400
        :param mock_post:
        :return: None
        """
        self._mr.status_code = HTTPStatus.BAD_REQUEST
        mock_post.return_value = self._mr
        success, message = self._scramble.perform(self.LIST_OF_SHOPPERS)
        assert_false(success)
        assert_equal("FAILURE [status code:400]: ['test_shoppers']", message)
        mock_post.assert_called()

    @patch('shopper_actions.scramble.post', side_effect=Exception('MockException'))
    def test_perform_exception(self, mock_post):
        """
        Test when _perform() throws exception
        :param mock_post:
        :return: None
        """
        success, message = self._scramble.perform(self.LIST_OF_SHOPPERS)
        assert_false(success)
        assert_equal("MockException: Exception while updating block: ['test_shoppers']", message)
        mock_post.assert_called()
