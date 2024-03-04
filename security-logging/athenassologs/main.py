import sys
import boto3
from datetime import datetime

QUERY_BATCH_MAP_US_WEST_2 = {
    1 : ['queries/query1.txt', 'queries/query4.txt', 'queries/query5.txt'],
    2 : ['queries/query2.txt'],
    3: ['queries/query3.txt']
}
QUERY_BATCH_MAP_US_EAST_1 = {
    1: ['queries/query6_us_east_2.txt']
}

def execute_query(uuid, query_string, shopper_email_query_string, 
                  athena_client, region='us-west-2'):
    if region == 'us-west-2':
        s3_location = 's3://gd-security-prod-assets-athena-uswest2/march-athena-queries'
    else:
        s3_location = 's3://gd-security-prod-assets-athena/march-athena-queries'
    s3_location = f'{s3_location}/{uuid}/'
    query_string = query_string.replace('<place_holder>', shopper_email_query_string)
    response = athena_client.start_query_execution(
        ResultConfiguration = {
            'OutputLocation': s3_location
        },
        QueryString=query_string,
        WorkGroup='SSOLegalComplianceWorkGroup'
    )
    return response['QueryExecutionId']

def main():
    batch_counter = int(sys.argv[1])
    uuid = sys.argv[2]
    print(f'Batch Counter: {batch_counter}')
    athena_client = boto3.client('athena',region_name='us-west-2')
    shopper_email_query_string = open('shopper_email_query.txt', 'r').read()
    # Execute queries for us-west-2
    query_execution_ids = []
    for file_path in QUERY_BATCH_MAP_US_WEST_2[batch_counter]:
        query_string = open(file_path, 'r').read()
        query_execution_ids.append(execute_query(uuid, query_string, shopper_email_query_string, athena_client))
    # Execute queries for us-east-1
    if batch_counter == 1:
        athena_client = boto3.client('athena',region_name='us-east-1')
        query_string = open(QUERY_BATCH_MAP_US_EAST_1[batch_counter][0], 'r').read()
        query_execution_ids.append(execute_query(uuid, query_string, shopper_email_query_string, athena_client, 'us-east-1'))
       
main()