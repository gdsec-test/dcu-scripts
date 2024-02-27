
def generate_aws_logging_config(bucket: str, account_id: str, index_prefix: str):
    return {
        f'{index_prefix}aws_cloudtrail': {
            's3_bucket': bucket,
            'prefix': 'compliance-trails/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-CloudTrail-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}aws_config': {
            's3_bucket': bucket,
            'prefix': 'awsconfig/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-Config-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}aws_syslog': {
            's3_bucket': bucket,
            'prefix': 'syslogs/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-Syslog-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}aws_service_logs': {
            's3_bucket': bucket,
            'prefix': 'service-logs/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-Service-Audit_logs-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}aws_eks': {
            's3_bucket': bucket,
            'prefix': 'ekslogs/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-EKS-Logs-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}aws_waf': {
            's3_bucket': bucket,
            'prefix': 'waflogs/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-WAF-Logs-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}app_security': {
            's3_bucket': bucket,
            'prefix': 'appseclogs/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-S3-App-Sec-Logs-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}windows_events_pki': {
            's3_bucket': bucket,
            'prefix': 'WEC-PKI/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-WEC-Logs-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}windows_events': {
            's3_bucket': bucket,
            'prefix': 'WEC/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-WEC-Logs-SQS',
            'aws_account_id': account_id
        },
        f'{index_prefix}aws_guardduty': {
            's3_bucket': bucket,
            'prefix': 'guardduty/',
            'sqs_url': f'https://sqs.us-west-2.amazonaws.com/{account_id}/GD-AWS-GuardDuty-SQS',
            'aws_account_id': account_id
        }
    }


NON_PCI_CONFIG = {
    'on_prem': {
        's3_bucket': 'gd-security-prod-aggregated-logs-uswest2',
        'prefix': 'fluent-logs/',
        'sqs_url': 'https://sqs.us-west-2.amazonaws.com/811396126940/GD-AWS-Log-Aggregator-SQS',
        'aws_account_id': '811396126940'
    },
    **generate_aws_logging_config('godaddy-aws-logs-replica-non-pci-us-west-2', '811396126940', '')
}

PCI_CONFIG = generate_aws_logging_config('godaddy-aws-logs-replica-pci-us-west-2', '356944415242', 'pci_')
