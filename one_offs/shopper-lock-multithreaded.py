import requests
from concurrent.futures import ThreadPoolExecutor
import argparse
import time

CERT_PATH = 'zeus.client.cset.int.gdcorp.tools.crt'
KEY_PATH = 'zeus.client.cset.int.gdcorp.tools.key'
SSO_URL = 'https://sso.godaddy.com'
SHOPPER_DATA_FILE = 'data/ru_shoppers.csv'
log_file = open('log.txt', 'a')
error_file = open('error.txt', 'a')


def log_message(message: str):
    print(message)
    log_file.write(f'{message}\n')


def log_error_shopper(shopperid: str, message: str):
    print(f'Error with shopper {shopperid}')
    error_file.write(f'{shopperid}, {message}\n')


def get_jwt():
    response = requests.post(
        f'{SSO_URL}/v1/secure/api/token', cert=(CERT_PATH, KEY_PATH), data={
            'realm': 'cert'
        })
    response.raise_for_status()
    return response.json()['data']


def lock_shopper(shopperid: str, sso_jwt: str, index: int):
    # Make changes here based on lock team id cause and employee.
    # employee should have perms to put the lock
    response = requests.put(f'https://sso.gdcorp.tools/v1/api/idp/{shopperid}/adminLocks/adminTerminated',
                            headers={'Authorization': f'sso-jwt {sso_jwt}'},
                            json={
                                'lockTeamId': 'LT_RISK',
                                'cause': 'Policy - Compliance',
                                'employee': '' # jomax id of empoyee here
                            })
    if response.status_code != 201:
        error_response_text = response.text
        log_error_shopper(shopperid, error_response_text)
        print(f'Error status code {response.status_code} for shopper {shopperid}')
        print(f'Response text {error_response_text}')
    else:
        log_message(f'Successfully locked shopper {shopperid} at index {index}')


def lock_shoppers(shopper_list: list[str],
                  start_counter: int, end_counter: int, n_threads: int):
    if end_counter > len(shopper_list):
        end_counter = len(shopper_list)
    print(
        f'Setting {n_threads} threads to lock shoppers from {start_counter} to {end_counter}')
    executor = ThreadPoolExecutor(max_workers=n_threads)
    sso_jwt = get_jwt()
    counter = 0
    results = []
    start_time = time.time()
    for i in range(start_counter, end_counter):
        if counter == 2 * n_threads:
            for result in results:
                result.result()
            counter = 0
            results = []
            log_message(
                f'Processed shoppers from {i - 2 * n_threads} to {i} in {time.time() - start_time} seconds')
            start_time = time.time()
        results.append(executor.submit(lock_shopper, shopper_list[i], sso_jwt, i))
        counter += 1
    for result in results:
        result.result()
    log_message(
        f'Processed shoppers from {start_counter} to {end_counter}')


def get_shopper_list(file_path: str) -> list[str]:
    file_contents = []
    with open(file_path, 'r') as file:
        file_contents = file.read().splitlines()
    shopper_list = []
    for line in file_contents:
        shopper_list.append(line.split(',')[0].strip())
    return shopper_list[1:]


def main():
    parser = argparse.ArgumentParser(description='Lock shoppers utility')
    parser.add_argument('-s', '--startindex', type=int,
                        required=True, help='Start index')
    parser.add_argument('-e', '--endindex', type=int,
                        required=True, help='End index(exclusive)')
    parser.add_argument('-t', '--threads', type=int,
                        default=10, help='Number of threads')
    args = parser.parse_args()
    shopper_list = get_shopper_list(SHOPPER_DATA_FILE)
    lock_shoppers(shopper_list, args.startindex, args.endindex, args.threads)
    log_file.close()
    error_file.close()


main()
