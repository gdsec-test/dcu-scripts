from typing import List
import boto3
from datetime import datetime, timedelta
import argparse
import json

from config import NON_PCI_CONFIG, PCI_CONFIG

# Mapping requested indexes to configuration.
SQS_INDEX_MAP = {**NON_PCI_CONFIG, **PCI_CONFIG}

# A set of log paths that contain garbage we can not re-hydrate.
NOT_ALLOWED = [
    'fluent-logs/OTHER/',
    'fluent-logs/SECURITY//',
    'fluent-logs/SECURITY/REHYDRATE/INCIDENT',
    'fluent-logs/SECURITY/GEN/ALL/EXOLOGS//',
    'fluent-logs/SECURITY/GEN/ALL/SAFELINKLOG//',
    'fluent-logs/SECURITY/SABLE////',
    'fluent-logs/SECURITY/SABLE/GDDEV///',
    'fluent-logs/SECURITY/THREATHUNT////',
    'fluent-logs/SECURITY/log////',
    'fluent-logs/SECURITY/revenueshare/application///',
    'fluent-logs/SECURITY/webpro/application///'
]


def generate_sqs_event(bucket: str, sqs_url: str, key: str, size: int, etag: str):
    """
    Dumps a mock S3 SNS notification event into the specified SQS queue.
    """
    sqs = boto3.client('sqs')
    event = {
        'Records': [
            {
                'eventVersion': '2.1',
                'eventSource': 'aws:s3',
                'awsRegion': 'us-west-2',
                'eventTime': '2023-11-06T12:40:01.570Z',
                'eventName': 'ObjectCreated:Put',
                'userIdentity': {
                    'principalId': 'AWS:AROA3Z2X2LDOHMEN3H7YU:ODhmMjFkYzktZDI3Ny00ODA2LWJjYjktMWI3MzhlMGM1MmFk'
                },
                'requestParameters': {
                    'sourceIPAddress': '192.168.29.75'
                },
                'responseElements': {
                    'x-amz-request-id': '7WKF3PZAAHG42DMA',
                    'x-amz-id-2': 'huD2EDc4LsPSZHnpXBNzm+A9wwibDy5GM+wnjLpon1YsfG8SqQIB7e/q8F5iBCsbmo+hGmEMgmFeBaXVMbY6nUgRFozw35ga'
                },
                's3': {
                    's3SchemaVersion': '1.0',
                    'configurationId': '4879613d-ed79-4172-bdaa-8d53fedeac46',
                    'bucket': {
                        'name': bucket,
                        'ownerIdentity': {
                            'principalId': 'A1YMC81S5O154Z'
                        },
                        'arn': f'arn:aws:s3:::{bucket}'
                    },
                    'object': {
                        'key': key,
                        'size': size,
                        'eTag': etag,
                        'versionId': None,
                        'sequencer': '006548DEA17F261206'
                    }
                }
            }
        ]
    }
    sqs.send_message(
        QueueUrl=sqs_url,
        MessageBody=json.dumps(event)
    )


def build_initial_prefix_list(bucket: str, initial_prefix: str, start_date: datetime, end_date: datetime) -> List[str]:
    """
    Iterate throught the shared prefixes following the initial prefix until a year marker is hit. Most
    of the security logs in S3 share this approximate format:
    <initial prefix>/<app identifier>/<year>/<month>/<day>/<different time of day signifiers>/<filename.gz>

    This function finds all of the paths up through app identifier, and then suffixes them with the needed
    date range. This prevents us from needing to recursively enumerate all objects in the bucket, we only
    need to walk down to the year signifier. This approach will need to change if we ever want to slice
    by hours/minutes/etc.
    """
    session = boto3.Session()
    s3 = session.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    keys = []
    for page in paginator.paginate(Bucket=bucket, Prefix=initial_prefix, Delimiter='/'):
        if 'CommonPrefixes' in page:
            for prefix in page['CommonPrefixes']:
                if prefix['Prefix'] in NOT_ALLOWED:
                    continue
                prefix_value = prefix['Prefix'].split(initial_prefix)[-1]
                value = prefix_value.split('/')[0]
                # If we have encountered an integer and its a year, don't parse further. Some
                # applications use integers as the app name, but none of them seem to be four digits.
                if not value.isdigit() or len(value) != 4:
                    keys.extend(build_initial_prefix_list(bucket, prefix['Prefix'], start_date, end_date))
                else:
                    results = []
                    for n in range(int((end_date - start_date).days) + 1):
                        date = start_date + timedelta(n)
                        results.append(f'{initial_prefix}{date.year}/{date.month:02d}/{date.day:02d}/')
                    return results
    return keys


def enumerate_s3_keys(prefixes: List[str], bucket: str, sqs_url: str):
    """
    Enumerate all of the files in each of the supplied prefixes. Dump
    the found files into SQS. Print out periodic messages so the
    monitors know the script isn't stuck.
    """
    session = boto3.Session()
    s3 = session.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    i = 0
    for prefix in prefixes:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' in page:
                for file in page['Contents']:
                    generate_sqs_event(bucket, sqs_url, file['Key'], file['Size'], file['ETag'])
                    i += 1
                    if i % 500 == 0:
                        print(f'{i} files processed')
    print(f'{i} files processed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rehydrate the specified index.')
    dt_lambda = lambda s: datetime.strptime(s, '%Y-%m-%d')  # noqa: E731
    parser.add_argument('--start_date', help='The date in format YYYY-MM-DD', type=dt_lambda, required=True)
    parser.add_argument('--end_date', help='The date in format YYYY-MM-DD', type=dt_lambda, required=True)
    parser.add_argument('--tag', help='The tag for the logs you are looking to rehydrate', type=str)
    parser.add_argument('--index', help='The index to load logs from.', type=str, required=True)
    args = parser.parse_args()

    if args.index not in SQS_INDEX_MAP.keys():
        raise ValueError(f'{args.index} is not a support index.')

    prefix = SQS_INDEX_MAP['on_prem']['prefix']
    if args.tag:
        prefix = prefix + args.tag.replace('.', '/')

    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()['Account']
    needed_account_id = SQS_INDEX_MAP[args.index]['aws_account_id']
    if account_id != needed_account_id:
        raise ValueError(f'Authed into the incorrect account({account_id}), {needed_account_id} is needed.')

    start = datetime.utcnow()
    # Build list of S3 prefixes we will need to re-trigger events within.
    result = build_initial_prefix_list(
        SQS_INDEX_MAP[args.index]['s3_bucket'],
        prefix,
        args.start_date,
        args.end_date
    )
    # Generate a S3 event for every file within every specified prefix.
    enumerate_s3_keys(
        result,
        SQS_INDEX_MAP[args.index]['s3_bucket'],
        SQS_INDEX_MAP[args.index]['sqs_url']
    )
    end = datetime.utcnow()
    print(end - start)
