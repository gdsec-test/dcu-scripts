import getpass
import json
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from pprint import pprint
from time import sleep

import shlex
import subprocess

import OpenSSL
import requests
import yaml

BASE_URL = 'https://certificates.api.int.godaddy.com:443/v1/certificates'
SSO_URL = 'https://sso.godaddy.com/v1/api/token'

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

body = {
    'group': 'ENG-DCU'
}


def execute(command):
    """
    This function executes the list of commands on the shell as subprocess
    :param command: set of commands to be executed on shell
    :return: output of the executed command on the shell
    """

    cmds = [shlex.split(x) for x in command]
    for cmd in cmds:
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

    out = data[0].decode('UTF-8')
    file = open('oldtls_{}_{}.yaml'.format(context, secret_name), 'w', encoding='UTF-8')
    yaml.dump(out, file)
    file.close()


def issue_new_certificate():
    """
    This function issues a new certificate for given commonName
    :return: None
    """

    print('Issuing a new for certificate {}'.format(body['commonName']))
    issue_new_certificate_response = doPostRequest(body)
    if issue_new_certificate_response.status_code == HTTPStatus.OK:
        print('Certificate Issued - Certificate Name: {}, HTTP Response Code: {}'
              .format(body['commonName'], issue_new_certificate_response.status_code))
        print('New Certificate will be in PENDING_ISSUANCE status. Waiting 300s')
        sleep(300)
    else:
        print('Invalid HTTP Response for cert api post request while issuing the certificate'
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body['commonName'], issue_new_certificate_response.status_code))
        exit(1)


def doPostRequest(data):
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

    print('Fetching the latest certificate {}'.format(body['commonName']))
    get_latest_certificate_response = requests.get(BASE_URL + '/cn/{}'
                                                              '/latest'.format(body['commonName']), params=body,
                                                   headers=HEADERS)

    if get_latest_certificate_response.status_code == HTTPStatus.OK:
        return get_latest_certificate_response.json()
    else:
        print('Invalid HTTP Response for cert api get request while fetching the latest certificate for '
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body['commonName'], get_latest_certificate_response.status_code))
        exit(1)


def download_new_certificate_crt_file():
    """
    This function fetches the crt text of the latest certificate
    :return: response text (crt) for latest certificate
    """

    print('Downloading crt file for certificate {}'.format(body['commonName']))
    download_new_certificate_crt_file_response = requests.get(
        BASE_URL + '/cn/{}/latest.crt'.format(body['commonName'])
        , params=body, headers=HEADERS)

    if download_new_certificate_crt_file_response.status_code == HTTPStatus.OK:
        return download_new_certificate_crt_file_response.text
    else:
        print('Invalid HTTP Response for cert api get request while fetching the latest certificate crt text for '
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body['commonName'], download_new_certificate_crt_file_response.status_code))
        exit(1)


def download_new_certificate_intermediate_chain_file():
    """
    This function fetches the chain text of the latest certificate
    :return: response text (chain) for latest certificate
    """

    print('Downloading chain file for certificate {}'.format(body['commonName']))
    download_new_certificate_intermediate_chain_file_response = requests.get(
        BASE_URL + '/cn/{}/latest.chain'.format(body['commonName'])
        , params=body, headers=HEADERS)

    if download_new_certificate_intermediate_chain_file_response.status_code == HTTPStatus.OK:
        return download_new_certificate_intermediate_chain_file_response.text
    else:
        print('Invalid HTTP Response for cert api get request while fetching the latest certificate chain text for '
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body['commonName'], download_new_certificate_intermediate_chain_file_response.status_code))
        exit(1)


def download_new_certificate_key_file():
    """
    This function fetches the key text of the latest certificate
    :return: response text (key) for latest certificate
    """

    print('Downloading key file for certificate {}'.format(body['commonName']))
    download_new_certificate_key_file_response = requests.get(
        BASE_URL + '/cn/{}/latest.key'.format(body['commonName'])
        , params=body, headers=HEADERS)

    if download_new_certificate_key_file_response.status_code == HTTPStatus.OK:
        return download_new_certificate_key_file_response.text
    else:
        print('Invalid HTTP Response for cert api get request while fetching the latest certificate key text for '
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body['commonName'], download_new_certificate_key_file_response.status_code))
        exit(1)


def generate_new_cert_package(crt, chain, key):
    """
    This function generates the new cert package by creating tls.crt, tls.key files
    :param crt: crt text of the latest certificate
    :param chain: chain text of the latest certificate
    :param key: key text of the latest certificate
    :return: None
    """

    print('Generating crt package for certificate {}'.format(body['commonName']))
    f = open('tls.crt', 'a')
    f.write('{}\n'.format(crt))
    f.write(chain)
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

    command = []
    command_string = 'kubectl create secret tls {} --cert {} --key {} --context {}'.format(secret_name, 'tls.crt',
                                                                                           'tls.key', context)
    command.append(command_string)
    data = execute(command)
    out = data[0].decode('UTF-8')
    print(out)


def get_certificate_serial_number():
    """
    This function fetches the serial number of the certificate
    :return: Fetch the serial number of the certificate
    """

    print('Fetching Serial Number for certificate {}'.format(body['commonName']))
    get_certificate_serial_number_response = requests.get(
        BASE_URL + '/cn/{}'
                   '/latest'.format(body['commonName']), params=body, headers=HEADERS)

    if get_certificate_serial_number_response.status_code == HTTPStatus.OK:
        last_certificate_response = get_certificate_serial_number_response.json()
        print('Details of the current certificate with commonName {}'.format(body['commonName']))
        pprint(last_certificate_response)
        return last_certificate_response['certificate']['serialNumber']
    else:
        print('Invalid HTTP Response for cert api get request while fetching the latest certificate serial number for '
              '- Certificate Name: {}, HTTP Response Code: {}'
              .format(body['commonName'], get_certificate_serial_number_response.status_code))
        exit(1)


def retire_old_certificate(certificate_serial_number):
    """
    This function retires the certificate with the given serial number
    :param certificate_serial_number: Serial number of the certificate
    :return:response json
    """

    print('Retiring old certificate {} with Serial Number: {}'.format(body['commonName'], certificate_serial_number))
    body['serialNumber'] = certificate_serial_number
    retire_old_certificate_response = requests.post(BASE_URL + '/sn/{}/retire'.format(certificate_serial_number),
                                                    params=body, headers=HEADERS)

    if retire_old_certificate_response.status_code == HTTPStatus.OK:
        return retire_old_certificate_response.json()
    else:
        print('Invalid HTTP Response for cert api post request while retiring the certificate for '
              '- Certificate Name: {}, Serial Number: {}, HTTP Response Code: {}'
              .format(body['commonName'], certificate_serial_number, retire_old_certificate_response.status_code))
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

    command = []
    command_string = 'kubectl delete secret {} --context {}'.format(secret_name, context)
    command.append(command_string)
    data = execute(command)
    out = data[0].decode('UTF-8')
    print(out)


def read_certificate_secret_mapping_file(common_name):
    with open('certificate_secret_mapping.json') as f:
        certificate_secret_mapping = json.load(f)

    if common_name not in certificate_secret_mapping:
        print('{} not found in the certificate secret mapping file. Kindly update the file - Exiting'
              .format(body['commonName']))
        exit(1)
    return certificate_secret_mapping[common_name]


def verify_new_certificate():
    cert = OpenSSL.crypto.load_certificate(
        OpenSSL.crypto.FILETYPE_PEM,
        open('tls.crt').read()
    )
    print('Certificate Validity')
    print('Not After: {}'.format(datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ')))
    print('Not Before: {}'.format(datetime.strptime(cert.get_notBefore().decode('ascii'), '%Y%m%d%H%M%SZ')))


def getAuthToken(user, password, certificate_file='apiuser.cmap.int.godaddy.com.crt',
                 certificate_secret='apiuser.cmap.int.godaddy.com.key'):
    """
    This function generates the signed jwt token for a user
    :param certificate_secret: path to apiuser.cmap.int.godaddy.com.crt file
    :param certificate_file: path to apiuser.cmap.int.godaddy.com.key file
    :param user: The JOMAX username of the user
    :param password: User Password
    :return: 
    """

    data = {
        "realm": "jomax",
        "username": user,
        "password": password
    }

    response = requests.post(SSO_URL, json=data,
                             headers=HEADERS, cert=(certificate_file, certificate_secret))

    if response.status_code == HTTPStatus.CREATED:
        return response.json()['data']
    else:
        print('Unable to retrieve the jomax auth token - exiting')
        exit(1)


def main():
    user = getpass.getuser()

    password = getpass.getpass('Enter password for user {}: '.format(user))

    if user is None or password is None:
        print('Invalid Credentials - Exiting')
        exit(1)

    authorization_token = getAuthToken(user, password)

    if authorization_token:
        print('Authorization Token retrieved')
    else:
        print('Authorization Token is null')
        exit(1)

    HEADERS['Authorization'] = 'sso-jwt {}'.format(authorization_token)

    certificate_name = input('Enter the name of certificate to be issued/renewed/retired:')
    if certificate_name is None:
        print('Certificate Name is null')
        exit(1)
    body['commonName'] = certificate_name

    user_input = int(input('Do you want to retire this certificate (1), '
                           'issue a new certificate (2) or '
                           'renew this certificate (3):'))

    if user_input == 1:
        certificate_serial_number = input('Enter the serial number of the certificate you want to retire:')
        if certificate_serial_number is None:
            print('Serial Number is null')
            exit(1)
        retire_old_certificate(certificate_serial_number)
    elif user_input == 2:
        issue_new_certificate()
    else:
        cert_secret_mapping = read_certificate_secret_mapping_file(body['commonName'])

        print('The following certificate and secret(s) will get renewed under respective context')
        print('Certificate_Name \t Secret_Name \t Context')

        for secret_name in cert_secret_mapping['secret']:
            for context in cert_secret_mapping['secret'][secret_name]:
                context += '-dcu'
                print('{} \t {} \t {} \n'.format(body['commonName'], secret_name, context))

        user_input = input('Do you wish to continue (Y/N)? ')

        if user_input.lower() != 'y':
            print('Invalid user_input:{}'.format(user_input))
            exit(1)

        # HEADERS['Authorization'] = 'sso-jwt {}'.format(authorization_token)
        retry = 0

        # body['commonName'] = certificate_name

        # Step 1: Get the last certificate's serial Number
        last_certificate_serial_number = get_certificate_serial_number()

        # Step 2: Issue a new certificate
        issue_new_certificate()

        # Step 3: Get Serial Number of the newly issued certificate
        latest_certificate_serial_number = get_certificate_serial_number()

        # Step 4: Wait until the latest_certificate_serial_number != last_certificate_serial_number
        while latest_certificate_serial_number and \
                last_certificate_serial_number == latest_certificate_serial_number:
            retry += 1
            print('New certificate is still pending_issuance. Retrying again in 300s. Retry#: '.format(str(retry)))
            sleep(300)
            latest_certificate_serial_number = get_certificate_serial_number()
            if retry >= 5:
                print('Exceeded maximum number of retries')
                exit(1)

        # Step 5: Get the latest Certificate
        latest_certificate = get_latest_certificate()

        # Step 6: Download the crt text from the latest certificate
        latest_certificate_crt = download_new_certificate_crt_file()

        # Step 7: Download the chain text from the latest certificate
        latest_certificate_intermediate_chain = download_new_certificate_intermediate_chain_file()

        # Step 8: Download the key text from the latest certificate
        latest_certificate_key = download_new_certificate_key_file()

        # Step 9: Generate the new cert package
        generate_new_cert_package(latest_certificate_crt, latest_certificate_intermediate_chain, latest_certificate_key)

        # Step 10: Verify the new date of the certificate
        verify_new_certificate()

        user_input = input('Do you wish to continue (Y/N)? ')

        if user_input.lower() != 'y':
            print('Invalid user_input while verifying the new certificate:{}'.format(user_input))
            exit(1)

        # Step 11: Loop over all cert_secret_mappings
        for secret_name in cert_secret_mapping['secret']:
            for context in cert_secret_mapping['secret'][secret_name]:
                context += '-dcu'
                # Step 10.1: Back up the old secret in kubernetes
                backup_old_secret(context, secret_name)

                # Step 10.2: Delete old secret from the kubernetes
                delete_old_secret(context, secret_name)

                # Step 10.3: Create new secret in kubernetes
                create_new_secret(context, secret_name)

        # Step 12: Retire old certificate
        retire_old_certificate(last_certificate_serial_number)

        # Step 13: Delete all the generated files
        delete_downloaded_files()


if __name__ == '__main__':
    main()
