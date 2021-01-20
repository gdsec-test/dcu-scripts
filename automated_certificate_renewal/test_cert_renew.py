import unittest
from http import HTTPStatus
from unittest.mock import patch

from automated_certificate_renewal.cert_renew import getAuthToken, read_certificate_secret_mapping_file, \
    get_latest_certificate, get_user_selection, Action

POST_DATA = {"foo": "bar"}


class MockPost:

    @staticmethod
    def json():
        return {"data": POST_DATA}

    status_code = HTTPStatus.CREATED


class MyTestCase(unittest.TestCase):

    def test_read_certificate_secret_mapping_file_secret_exists(self):
        self.assertIsNotNone(read_certificate_secret_mapping_file('autorenew.int.dev-godaddy.com'))

    def test_read_certificate_secret_mapping_file_secret_does_not_exist(self):
        self.assertIsNone(read_certificate_secret_mapping_file('no.certificate'))

    @patch('cert_renew.requests.get')
    def test_get_latest_certificate_success(self, mock_post):
        mp = MockPost()
        mp.status_code = 200
        mock_post.return_value = mp
        ret_val = get_latest_certificate()
        self.assertEqual(ret_val, {'data': POST_DATA})

    @patch('cert_renew.requests.get')
    def test_get_latest_certificate_fail(self, mock_post):
        mp = MockPost()
        mp.status_code = 400
        mock_post.return_value = mp
        with self.assertRaises(SystemExit) as cm:
            ret_val = get_latest_certificate()
        self.assertEqual(cm.exception.code, 1)

    @patch('cert_renew.requests.post', return_value=MockPost())
    def test_getAuthToken_success(self, mock_post):
        ret_val = getAuthToken('user', 'pass', 'cert', 'key')
        self.assertEqual(ret_val, POST_DATA)

    @patch('cert_renew.requests.post')
    def test_getAuthToken_fail(self, mock_post):
        mp = MockPost()
        mp.status_code = 400
        mock_post.return_value = mp
        with self.assertRaises(SystemExit) as cm:
            getAuthToken('user', 'pass', 'cert', 'key')
        self.assertEqual(cm.exception.code, 1)

    @patch('builtins.input', return_value=3)
    def test_user_selection_renew(self, input):
        self.assertEqual(get_user_selection(), Action.Renew)

    @patch('builtins.input', return_value=2)
    def test_user_selection_retire(self, input):
        self.assertEqual(get_user_selection(), Action.Retire)

    @patch('builtins.input', return_value=1)
    def test_user_selection_issue(self, input):
        self.assertEqual(get_user_selection(), Action.Issue)


if __name__ == '__main__':
    unittest.main()
