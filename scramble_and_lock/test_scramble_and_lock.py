import json
import requests
from mock import patch
from http import HTTPStatus
from nose.tools import assert_is_none, assert_equal, assert_false, assert_true

from scramble_and_lock import _inquire, _is_affirmative, ScrambleAndLock

POST_DATA = {"data": "test_jwt"}


class MockResponse(requests.Response):
    status_code = 200
    text = json.dumps({"data": POST_DATA})


class TestScramble:
    NO = 'N'
    TEST_QUESTION = 'Test Question'
    YES = 'Y'

    @classmethod
    @patch('scramble_and_lock.post')
    def setup_class(cls, mock_post):
        """
        Since the ScrambleAndLock constructor calls _get_jwt() which calls requests.post, we need to mock it
        :param mock_post:
        :return: None
        """
        cls._mr = MockResponse()
        cls._mr.status_code = HTTPStatus.CREATED
        mock_post.return_value = cls._mr
        cls._scram = ScrambleAndLock('test_crt', 'test_key', 'test_note')

    @patch('builtins.input', return_value=YES)
    def test_inquire_yes(self, mock_input):
        """
        Test _inquire when user enters 'Y'
        :param mock_input:
        :return: None
        """
        assert_equal(self.YES, _inquire('Test question'))

    @patch('builtins.input', return_value=NO)
    def test_inquire_no(self, mock_input):
        """
        Test _inquire when user enters 'N'
        :param mock_input:
        :return: None
        """
        assert_equal(self.NO, _inquire('Test question'))

    def test_is_affirmative_yes(self):
        """
        _is_affirmative should return True when provided 'Y'
        :return: None
        """
        assert_true(_is_affirmative(self.YES))

    def test_is_affirmative_no(self):
        """
        _is_affirmative should return False when provided anything but 'Y'
        :return: None
        """
        assert_false(_is_affirmative(self.NO))

    @patch('scramble_and_lock.post')
    def test_get_jwt_success(self, mock_post):
        """
        Test when _get_jwt() returns successfully 201
        :param mock_post:
        :return: None
        """
        self._mr.status_code = HTTPStatus.CREATED
        mock_post.return_value = self._mr
        assert_equal(POST_DATA, self._scram._get_jwt('test_cert'))

    @patch('scramble_and_lock.post')
    def test_get_jwt_fail(self, mock_post):
        """
        Test when _get_jwt() returns failed 400
        :param mock_post:
        :return: None
        """
        self._mr.status_code = HTTPStatus.BAD_REQUEST
        mock_post.return_value = self._mr
        assert_is_none(self._scram._get_jwt('test_cert'))

    @patch('scramble_and_lock.post')
    def test_perform_success(self, mock_post):
        """
        Test when _perform() returns successfully 201
        :param mock_post:
        :return: None
        """
        self._mr.status_code = HTTPStatus.CREATED
        mock_post.return_value = self._mr
        success, message = self._scram._perform('test_action', ['test_shoppers'])
        assert_true(success)
        assert_equal('SUCCESS: 1: {"data": {"data": "test_jwt"}}', message)

    @patch('scramble_and_lock.post')
    def test_perform_fail(self, mock_post):
        """
        Test when _perform() returns failed 400
        :param mock_post:
        :return: None
        """
        self._mr.status_code = HTTPStatus.BAD_REQUEST
        mock_post.return_value = self._mr
        success, message = self._scram._perform('test_action', ['test_shoppers'])
        assert_false(success)
        assert_equal("FAILURE [status code:400]: ['test_shoppers']", message)

    @patch('scramble_and_lock.post', side_effect=Exception('MockException'))
    def test_perform_exception(self, mock_post):
        """
        Test when _perform() throws exception
        :param mock_post:
        :return: None
        """
        success, message = self._scram._perform('test_action', ['test_shoppers'])
        assert_false(success)
        assert_equal("MockException: Exception while updating block: ['test_shoppers']", message)
