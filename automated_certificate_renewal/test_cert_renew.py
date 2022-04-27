import unittest

from datetime import datetime
from http import HTTPStatus
from mock import patch

from automated_certificate_renewal import cert_renew


POST_DATA = {"foo": "bar"}
VALID_CERTIFICATE = 'abuse.api.int.ote-godaddy.com'
INVALID_CERTIFICATE = 'no.certificate'
CERT_LIST = {'test-cert-name': {
    'secret': {
        'tls-test': ['test']
    }
}}
CERT_INFO = {'certificate': {
    'commonName': 'test-cert-name',
    'notValidAfter': datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%SZ'),
    'notValidBefore': '2021-12-20T08:00:15Z',
    'issuedOn': '2021-12-20T08:00:15Z'}
}
BODY = {'group': 'test-group',
        'commonName': 'test-cert-name'}


class MockPost:
    status_code = HTTPStatus.CREATED

    @staticmethod
    def json():
        return {"data": POST_DATA}


class AutomatedCertificateRenewalTestCases(unittest.TestCase):

    def test_read_certificate_secret_mapping_file_secret_exists(self):
        self.assertIsNotNone(cert_renew.read_certificate_secret_mapping_file(VALID_CERTIFICATE))

    def test_read_certificate_secret_mapping_file_secret_does_not_exist(self):
        self.assertIsNone(cert_renew.read_certificate_secret_mapping_file(INVALID_CERTIFICATE))

    @patch('cert_renew.requests.get')
    def test_get_latest_certificate_success(self, mock_post):
        mp = MockPost()
        mp.status_code = 200
        mock_post.return_value = mp
        ret_val = cert_renew.get_latest_certificate(BODY)
        self.assertEqual(ret_val, {'data': POST_DATA})

    @patch('cert_renew.requests.get')
    def test_get_latest_certificate_fail(self, mock_post):
        mp = MockPost()
        mp.status_code = 400
        mock_post.return_value = mp
        with self.assertRaises(SystemExit) as cm:
            cert_renew.get_latest_certificate(BODY)
        self.assertEqual(cm.exception.code, 1)

    @patch('cert_renew.requests.post', return_value=MockPost())
    def test_getAuthToken_success(self, mock_post):
        ret_val = cert_renew.get_auth_token('user', 'pass')
        self.assertEqual(ret_val, POST_DATA)

    @patch('cert_renew.requests.post')
    def test_getAuthToken_fail(self, mock_post):
        mp = MockPost()
        mp.status_code = 400
        mock_post.return_value = mp
        with self.assertRaises(SystemExit) as cm:
            cert_renew.get_auth_token('user', 'pass')
        self.assertEqual(cm.exception.code, 1)

    @patch('builtins.input', return_value=3)
    def test_user_selection_renew(self, input):
        self.assertEqual(cert_renew.get_user_selection(), cert_renew.Action.Renew)

    @patch('builtins.input', return_value=2)
    def test_user_selection_retire(self, input):
        self.assertEqual(cert_renew.get_user_selection(), cert_renew.Action.Retire)

    @patch('builtins.input', return_value=1)
    def test_user_selection_issue(self, input):
        self.assertEqual(cert_renew.get_user_selection(), cert_renew.Action.Issue)

    @patch.object(cert_renew, 'slack_message', return_value=None)
    @patch.object(cert_renew, 'get_expiring_certificates_list', return_value=None)
    def test_successful_expiring_certificates(self, mock_certs_list, mock_slack_message):
        cert_renew.SYS_ARGV_TWO = '1'
        cert_renew.expiring_certificates(BODY)
        assert mock_certs_list.called
        assert mock_slack_message.called

    @patch.object(cert_renew, 'slack_message', return_value=None)
    @patch.object(cert_renew, 'get_expiring_certificates_list', return_value=None)
    def test_not_int_expiring_certificates(self, mock_certs_list, mock_slack_message):
        cert_renew.SYS_ARGV_TWO = 'a'
        with self.assertRaises(SystemExit) as e:
            cert_renew.expiring_certificates(BODY)
            assert mock_certs_list.notcalled
            assert mock_slack_message.notcalled
        self.assertEqual(e.exception.code, 1)

    @patch.object(cert_renew, 'slack_message', return_value=None)
    @patch.object(cert_renew, 'get_expiring_certificates_list', return_value=None)
    def test_no_argv_expiring_certificates(self, mock_certs_list, mock_slack_message):
        with self.assertRaises(SystemExit) as e:
            cert_renew.expiring_certificates(BODY)
            assert mock_certs_list.notcalled
            assert mock_slack_message.notcalled
        self.assertEqual(e.exception.code, 1)

    def test_convert_list_to_csv(self):
        test_list = ['1', '2', '3']
        expected_return = '1,2,3'
        self.assertEqual(cert_renew.convert_list_to_csv(test_list), expected_return)

    @patch.object(cert_renew, 'get_latest_certificate', return_value=CERT_INFO)
    @patch.object(cert_renew, 'read_mapping_file', return_value=CERT_LIST)
    def test_successful_get_expiring_certificates_list(self, mock_map_file, mock_latest_cert):
        expected_result = 'test-cert-name'
        self.assertEqual(cert_renew.get_expiring_certificates_list(90, BODY), expected_result)

    @patch.object(cert_renew, 'get_latest_certificate', return_value=CERT_INFO)
    @patch.object(cert_renew, 'read_mapping_file', return_value=CERT_LIST)
    def test_not_int_get_expiring_certificates_list(self, mock_map_file, mock_latest_cert):
        with self.assertRaises(SystemExit) as e:
            cert_renew.get_expiring_certificates_list('not an int', BODY)
            assert mock_map_file.notcalled
            assert mock_latest_cert.notcalled
        self.assertEqual(e.exception.code, 1)

    @patch('requests.post')
    def test_successful_slack_message(self, mock_post):
        cert_renew.SLACK_WEBHOOK_URL = 'test webhook url'
        cert_renew.slack_message('test')
        assert mock_post.called

    @patch('requests.post')
    def test_no_webhook_slack_message(self, mock_post):
        cert_renew.slack_message('test')
        assert mock_post.notcalled

    @patch.object(cert_renew, 'execute', return_value=(b'api-5cf97dc97d-whs2w,default-token-s45d5,\n', None))
    def test_success_kubernetes_secrets_search(self, mock_execute):
        expected_results = [['api-5cf97dc97d-whs2w', 'default-token-s45d5']]
        cert_renew.kubernetes_secrets_search('dev')
        self.assertEqual(cert_renew.kubernetes_secrets_search('dev'), expected_results)
        assert mock_execute.called

    @patch.object(cert_renew, 'execute', return_value=None)
    def test_failed_kubernetes_secrets_search(self, mock_execute):
        with self.assertRaises(SystemExit) as e:
            cert_renew.kubernetes_secrets_search('dev')
            assert mock_execute.called
        self.assertEqual(e.exception.code, 1)

    def test_missing_arg_certificates_renewal(self):
        with self.assertRaises(SystemExit) as e:
            cert_renew.certificates_renewal(BODY)
        self.assertEqual(e.exception.code, 1)

    def test_no_valid_certs_certificates_renewal(self):
        cert_renew.SYS_ARGV_TWO = INVALID_CERTIFICATE
        with self.assertRaises(SystemExit) as e:
            cert_renew.certificates_renewal(BODY)
        self.assertEqual(e.exception.code, 1)

    @patch.object(cert_renew, 'slack_message', return_value=None)
    @patch.object(cert_renew, 'find_pods_to_roll', return_value=[])
    @patch.object(cert_renew, 'process_cert_renewal', return_value=None)
    def test_valid_certs_certificates_renewal(self, mock_process_cert, mock_find_pods, mock_slack):
        cert_renew.DEV_SECRETS_LIST = ['test-secret']
        cert_renew.SYS_ARGV_TWO = VALID_CERTIFICATE
        cert_renew.certificates_renewal(BODY)
        assert mock_process_cert.called
        assert mock_find_pods.called
        assert mock_slack.called

    @patch.object(cert_renew, 'delete_downloaded_files', return_value=None)
    @patch.object(cert_renew, 'retire_old_certificate', return_value=None)
    @patch.object(cert_renew, 'create_new_secret', return_value=None)
    @patch.object(cert_renew, 'delete_old_secret', return_value=None)
    @patch.object(cert_renew, 'backup_old_secret', return_value=None)
    @patch.object(cert_renew, 'verify_new_certificate', return_value=None)
    @patch.object(cert_renew, 'generate_new_cert_package', return_value=None)
    @patch.object(cert_renew, 'download_file', return_value='test')
    @patch.object(cert_renew, 'issue_new_certificate', return_value=None)
    @patch.object(cert_renew, 'get_latest_certificate', return_value={'certificate': {'serialNumber': None}})
    def test_process_cert_renewal(self, mock_latest_cert, mock_new_cert, mock_download, mock_gen_cert, mock_verify_cert,
                                  mock_backup_secret, mock_delete_secret, mock_create_secret, mock_retire,
                                  mock_delete_files):
        cert = 'dcu.zeus.int.dev-godaddy.com'
        BODY['commonName'] = cert
        cert_renew.process_cert_renewal(BODY)
        self.assertEqual(cert_renew.DEV_SECRETS_LIST, ['tls-zeus'])
        assert mock_latest_cert.called
        assert mock_new_cert.called
        assert mock_download.called
        assert mock_gen_cert.called
        assert mock_verify_cert.called
        assert mock_backup_secret.called
        assert mock_delete_secret.called
        assert mock_create_secret.called
        assert mock_retire.called
        assert mock_delete_files.called
