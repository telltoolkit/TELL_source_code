import os
import json
import datetime
from google.cloud import language_v1
from google.cloud.language_v1 import enums
from google.oauth2 import service_account
import six


class OwnException(Exception):
    pass


def fail(msg=''):
    raise OwnException({'statusCode': 500, 'body': msg})


def add_time_information_to_output(start_time):
    "add time information to output"
    end_time = datetime.datetime.now()
    return {'query_duration': (end_time - start_time).total_seconds(),
            'query_timestamp_start': str(start_time),
            'query_timestamp_end': str(end_time)}


def get_google_client_with_credentials():
    credentials_data = json.loads(os.environ['GOOGLE_CLOUD_CREDENTIALS'])
    if len(credentials_data) == 0:
        fail('GOOGLE_CLOUD_CREDENTIALS is empty')

    credentials = service_account.Credentials.from_service_account_info(
        credentials_data)
    return language_v1.LanguageServiceClient(credentials=credentials)


def handler(event, context):
    start_timestamp = datetime.datetime.now()

    # read parameters: language and transcript
    content = event['dependency_args']['transcript']['data']['transcript']
    lang_arg = event['args']['participant']['locale']['code']

    # gente the client object api google
    client = get_google_client_with_credentials()

    # create parameters to call google api
    document = {'type': enums.Document.Type.PLAIN_TEXT, 'content': content}

    # set language
    lang = None
    if 'es-' in lang_arg:
        lang = 'es'
    if 'en-' in lang_arg:
        lang = 'en'
    if lang is not None:
        document['language'] = lang

    # call the api
    response = client.analyze_sentiment(document)
    sentiment = response.document_sentiment
    
    res = {'data': {'lang': response.language},
           'scores':
           {
               'score': sentiment.score,
               'magnitude': sentiment.magnitude,
               }}

    # add time information
    res['data'].update(add_time_information_to_output(start_timestamp))

    return {
        'statusCode': 200,
        'body': json.dumps(res)
    }
