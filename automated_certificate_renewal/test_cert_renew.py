import getpass
import unittest
from automated_certificate_renewal.cert_renew import getAuthToken, read_certificate_secret_mapping_file


class MyTestCase(unittest.TestCase):
    def test_getAuthToken(self):
        user = getpass.getuser()
        password = getpass.getpass('Enter your password')
        auth_token = getAuthToken(user, password)
        self.assertIsNotNone(auth_token)

    def test_read_certificate_secret_mapping_file(self):
        secret_name = 'autorenew.int.dev-godaddy.com'
        val = read_certificate_secret_mapping_file(secret_name)
        self.assertIsNotNone(val)

        secret_name = 'no.certificate'
        val = read_certificate_secret_mapping_file(secret_name)
        self.assertIsNone(val)


if __name__ == '__main__':
    unittest.main()
