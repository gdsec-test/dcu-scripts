import configparser
from datetime import datetime
from enum import IntEnum
from http import HTTPStatus
from pathlib import Path
from pprint import pprint
from time import sleep

import shlex
import subprocess
import OpenSSL
import requests
import yaml
import encodings
import getpass
import json

"""
Check out the production API calls and schema for cert api at
cert-api swagger: https://certificates.api.int.godaddy.com/doc/#!/_v1_certificates/list
"""

BASE_URL = 'https://certificates.api.int.godaddy.com:443/v1/certificates'
SSO_URL = 'https://sso.godaddy.com/v1/api/token'
CONFLUENCE_URL = 'https://confluence.godaddy.com/display/ITSecurity/Replacing+SSL+Certs#ReplacingSSLCerts-InSaltstack'
KEY_COMMON_NAME = 'commonName'

encoding = encodings.utf_8.getregentry().name

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

body = {
    'group': 'ENG-DCU'
}


class Action(IntEnum):
    Issue = 1
    Retire = 2
    Renew = 3


def execute(command):
    """
    This function executes the list of commands on the shell as subprocess
    :param command: set of commands to be executed on shell
    :return: output of the executed command on the shell
    """

    for cmd in [shlex.split(x) for x in command]:
        data = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
    return data


def backup_old_secret(context, secret_name):
    """
    This function backs up the old secret in kubernetes under a given context
    :param context: Kubernetes context
    :param secret_name: name of the secret that needs to be edited
    :return: None
    """

    print('Backing up old secret in kube context {} secret name {}'.format(context, secret_name))

    command = []
    command_string = 'kubectl get secrets {} --context {} -o yaml'.format(secret_name, context)
    command.append(command_string)

    data = execute(command)

    out = data[0].decode(encoding)
    file = open('oldtls_{}_{}.yaml'.format(context, secret_name), 'w', encoding=encoding)
    yaml.dump(out, file)
    file.close()


def issue_new_certificate():
    """
    This function issues a new certificate for given commonName
    :return: None
    """

    print('Issuing a new certificate for {}'.format(body.get(KEY_COMMON_NAME)))
    issue_new_certificate_response = do_post_request(body)
    if issue_new_certificate_response.status_code == HTTPStatus.OK:
        print('Certificate Issued - Certificate Name: {}, HTTP Response Code: {}'
              .format(body.get(KEY_COMMON_NAME), issue_new_certificate_response.status_code))
        print('New Certificate will be in PENDING_ISSUANCE status. Waiting 300s')
        sleep(300)
    else:
        print('Invalid HTTP Response for cert api post request while issuing the certificate'
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body.get(KEY_COMMON_NAME), issue_new_certificate_response.status_code))
        exit(1)


def do_post_request(data):
    """
    This function performs the post request
    :param data: contains the values for group and commonName
    :return: response
    """

    return requests.post(BASE_URL, json=data, headers=HEADERS)


def get_latest_certificate():
    """
    This function fetches the latest certificate for given commonName
    :return: response json of the latest certificate for a given commonName
    """

    print('Fetching the current certificate {}'.format(body.get(KEY_COMMON_NAME)))
    get_latest_certificate_response = requests.get('{}/cn/{}/latest'.format(BASE_URL, body.get(KEY_COMMON_NAME)),
                                                   params=body, headers=HEADERS)

    if get_latest_certificate_response.status_code == HTTPStatus.OK:
        return get_latest_certificate_response.json()
    else:
        print('Invalid HTTP Response for cert api get request while fetching the current certificate for '
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body.get(KEY_COMMON_NAME), get_latest_certificate_response.status_code))
        exit(1)


def get_certificate_data(url):
    """
    :param url: Get the certificate data
    :return:
    """
    download_response = requests.get(url, params=body, headers=HEADERS)

    if download_response.status_code == HTTPStatus.OK:
        return download_response.text
    else:
        print('Invalid HTTP Response for cert api get request while fetching the latest certificate text for '
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body.get(KEY_COMMON_NAME), download_response.status_code))
        return None


def download_file(file_type):
    """
    This function downloads the required part (crt, key or chain) of the certificate
    :param file_type: crt, chain or key
    :return: response text
    """
    print('Downloading {} file for certificate {}'.format(file_type, body.get(KEY_COMMON_NAME)))
    url = '{}/cn/{}/latest.{}'.format(BASE_URL, body.get(KEY_COMMON_NAME), file_type)
    return get_certificate_data(url)


def generate_new_cert_package(crt, chain, key):
    """
    This function generates the new cert package by creating tls.crt, tls.key files
    :param crt: crt text of the latest certificate
    :param chain: chain text of the latest certificate
    :param key: key text of the latest certificate
    :return: None
    """

    print('Generating crt package for certificate {}'.format(body.get(KEY_COMMON_NAME)))
    f = open('tls.crt', 'a')
    f.write('{}\n{}'.format(crt, chain))
    f.close()

    f = open('tls.key', 'a')
    f.write('{}'.format(key))
    f.close()


def create_new_secret(context, secret_name):
    """
    This function creates a new secret with a given name under provided kubernetes context
    :param context: Kubernetes context
    :param secret_name: secret name that needs to be edited
    :return: None
    """

    print('Creating new secret in kube context {} secret name {}'.format(context, secret_name))

    command = ['kubectl create secret tls {} --cert {} --key {} --context {}'.format(secret_name, 'tls.crt',
                                                                                     'tls.key', context)]
    run_kubectl_command(command)


def get_certificate_serial_number():
    """
    This function fetches the serial number of the certificate
    :return: Fetch the serial number of the certificate
    """

    print('Fetching Serial Number for certificate {}'.format(body.get(KEY_COMMON_NAME)))
    get_certificate_serial_number_response = requests.get(
        '{}/cn/{}/latest'.format(BASE_URL, body.get(KEY_COMMON_NAME)), params=body, headers=HEADERS)

    if get_certificate_serial_number_response.status_code == HTTPStatus.OK:
        last_certificate_response = get_certificate_serial_number_response.json()
        print('Details of the current certificate with commonName {}'.format(body.get(KEY_COMMON_NAME)))
        pprint(last_certificate_response)
        return last_certificate_response['certificate']['serialNumber']
    else:
        print('Invalid HTTP Response for cert api get request while fetching the latest certificate serial number for '
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body.get(KEY_COMMON_NAME), get_certificate_serial_number_response.status_code))
        exit(1)


def retire_old_certificate(certificate_serial_number):
    """
    This function retires the certificate with the given serial number
    :param certificate_serial_number: Serial number of the certificate
    :return:response json
    """

    print('Retiring old certificate {} with Serial Number: {}'.format(body.get(KEY_COMMON_NAME),
                                                                      certificate_serial_number))
    body['serialNumber'] = certificate_serial_number
    retire_old_certificate_response = requests.post('{}/sn/{}/retire'.format(BASE_URL, certificate_serial_number),
                                                    params=body, headers=HEADERS)

    if retire_old_certificate_response.status_code == HTTPStatus.OK:
        return retire_old_certificate_response.json()
    else:
        print('Invalid HTTP Response for cert api post request while retiring the certificate for '
              '- Certificate Name: {}, Serial Number: {}, HTTP Response Code: {}'
              .format(body.get(KEY_COMMON_NAME), certificate_serial_number,
                      retire_old_certificate_response.status_code))
        exit(1)


def delete_downloaded_files():
    """
    The function deletes the downloaded files (if any)
    :return: None
    """

    print('Delete the downloaded files')
    for p in Path(".").glob("tls.*"):
        p.unlink()

    for p in Path(".").glob("oldtls_*.yaml"):
        p.unlink()


def delete_old_secret(context, secret_name):
    """
    This function deletes the old secret in kubernetes for a given context
    :param context: Kubernetes context
    :param secret_name: Name of the secret that needs to be edited
    :return: None
    """

    print('Deleting old secret in kube context {} secret name {}'.format(context, secret_name))
    command = ['kubectl delete secret {} --context {}'.format(secret_name, context)]
    run_kubectl_command(command)


def run_kubectl_command(command):
    """
    This function calls the execution of command on the shell
    :param command: The kubectl command
    :return: None
    """
    data = execute(command)
    out = data[0].decode(encoding)
    print(out)


def read_certificate_secret_mapping_file(common_name):
    with open('certificate_secret_mapping.json') as f:
        certificate_secret_mapping = json.load(f)

    if common_name not in certificate_secret_mapping:
        print('{} not found in the certificate secret mapping file. Kindly update the file - Exiting'
              .format(common_name))
        return None
    return certificate_secret_mapping[common_name]


def verify_new_certificate():
    cert = OpenSSL.crypto.load_certificate(
        OpenSSL.crypto.FILETYPE_PEM,
        open('tls.crt').read()
    )
    print('Certificate Validity')
    print('Not After: {}'.format(datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')))
    print('Not Before: {}'.format(datetime.strptime(cert.get_notBefore().decode('ascii'), '%Y%m%d%H%M%SZ')))


def get_auth_token(user, password, path_to_crt, path_to_secret):
    """
    This function generates the signed jwt token for a user
    :param path_to_crt: path to apiuser.cmap.int.godaddy.com.crt file
    :param path_to_secret: path to apiuser.cmap.int.godaddy.com.key file
    :param user: The JOMAX username of the user
    :param password: User Password
    :return: 
    """

    data = {
        "realm": "jomax",
        "username": user,
        "password": password
    }

    response = requests.post(SSO_URL, json=data, headers=HEADERS, cert=(path_to_crt, path_to_secret))

    if response.status_code == HTTPStatus.CREATED:
        return response.json()['data']
    else:
        print('Unable to retrieve the jomax auth token - exiting')
        exit(1)


def get_user_selection():
    choices = [f'{action.name}[{action.value}]' for action in Action]
    choices_str = ', '.join(choices)
    selection = int(input(f'Enter a choice ({choices_str}): '))
    action = Action(selection)
    return action


def main():
    config = configparser.ConfigParser()
    config.read('./settings.ini')

    user = input('Enter jomax username: ').strip()
    password = getpass.getpass('Enter password for user {}: '.format(user))

    if not user or not password:
        print('Invalid Credentials - Exiting')
        exit(1)

    authorization_token = get_auth_token(user, password, config['DEFAULT'].get('PATH_TO_CRT'),
                                         config['DEFAULT'].get('PATH_TO_KEY'))

    if authorization_token:
        print('Authorization Token retrieved')
    else:
        print('Authorization Token is null - Exiting')
        exit(1)

    HEADERS['Authorization'] = 'sso-jwt {}'.format(authorization_token)

    certificate_name = input('Enter the name of certificate to be issued/renewed/retired:').strip()

    if not certificate_name:
        print('Certificate Name is null')
        exit(1)
    body[KEY_COMMON_NAME] = certificate_name

    user_action = get_user_selection()

    if user_action == Action.Retire:
        certificate_serial_number = input('Enter the serial number of the certificate you want to retire:').strip()
        if not certificate_serial_number:
            print('Serial Number is null')
            exit(1)
        retire_old_certificate(certificate_serial_number)
    elif user_action == Action.Issue:
        issue_new_certificate()
    elif user_action == Action.Renew:

        cert_secret_mapping = read_certificate_secret_mapping_file(body.get(KEY_COMMON_NAME))
        if not cert_secret_mapping:
            print('Unable to fetch information of {} certificate from certificate_secret_mapping.json file - Exiting ')
            exit(1)

        print('The following certificate and secret(s) will get renewed under respective context')
        print('Certificate_Name \t Secret_Name \t Context')

        for secret_name in cert_secret_mapping['secret']:
            for context in cert_secret_mapping['secret'][secret_name]:
                context = '{}-dcu'.format(context)
                print('{} \t {} \t {} \n'.format(body.get(KEY_COMMON_NAME), secret_name, context))

        user_input = input('Do you wish to continue (Y/N)? ').strip()

        if user_input.lower() != 'y':
            print('You do not wish to continue. - Exiting')
            exit(1)

        retry = 0

        # Step 1: Get the last certificate's serial Number
        last_certificate = get_latest_certificate()
        last_certificate_serial_number = last_certificate['certificate']['serialNumber']

        # Step 2: Issue a new certificate
        issue_new_certificate()
        latest_certificate = get_latest_certificate()

        # Step 3: Get Serial Number of the newly issued certificate
        latest_certificate_serial_number = latest_certificate['certificate']['serialNumber']

        # Step 4: Wait until the latest_certificate_serial_number != last_certificate_serial_number
        while latest_certificate_serial_number and \
                last_certificate_serial_number == latest_certificate_serial_number:
            retry += 1
            print('New certificate is still pending_issuance. Retrying again. Waiting for 300s. Retry#: '
                  .format(str(retry)))
            sleep(300)
            latest_certificate_serial_number = get_certificate_serial_number()
            if retry >= 5:
                print('Exceeded maximum number of retries')
                exit(1)

        # Step 5: Download the crt text from the latest certificate
        latest_certificate_crt = download_file('crt')

        # Step 6: Download the chain text from the latest certificate
        latest_certificate_intermediate_chain = download_file('chain')

        # Step 7: Download the key text from the latest certificate
        latest_certificate_key = download_file('key')

        if not latest_certificate_crt or not latest_certificate_intermediate_chain or \
                not latest_certificate_key:
            print('Unable to download cert, chain or key file - Exiting')
            exit(1)

        # Step 8: Generate the new cert package
        generate_new_cert_package(latest_certificate_crt, latest_certificate_intermediate_chain, latest_certificate_key)

        # Step 9: Verify the new date of the certificate
        verify_new_certificate()

        user_input = input('Do you wish to continue (Y/N)? ').strip()

        if user_input.lower() != 'y':
            print('New certificate- {} is issued, but you do not wish to continue - Exiting. '
                  'Please perform manual updates to secrets'.format(certificate_name))
            exit(1)

        # Step 10: Loop over all cert_secret_mappings
        for secret_name in cert_secret_mapping['secret']:
            for context in cert_secret_mapping['secret'][secret_name]:
                context = '{}-dcu'.format(context)
                # Step 10.1: Back up the old secret in kubernetes
                backup_old_secret(context, secret_name)

                # Step 10.2: Delete old secret from the kubernetes
                delete_old_secret(context, secret_name)

                # Step 10.3: Create new secret in kubernetes
                create_new_secret(context, secret_name)

        # Step 11: Retire old certificate
        retire_old_certificate(last_certificate_serial_number)

        # Step 12: Delete all the generated files
        delete_downloaded_files()

        print('Certificate and corresponding secrets are updated')

        # Step 13: If salt key is found, print the statement to update the same.
        if 'salt' in cert_secret_mapping:
            print('Kindly update salt: {}. Visit the confluence page- {} for more information.'
                  .format(cert_secret_mapping['salt'], CONFLUENCE_URL))

        print('Done')
    else:
        print('Invalid Selection - Exiting')
        exit(1)


if __name__ == '__main__':
    main()
