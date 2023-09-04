import os
import json
import datetime
import openai
from resource_managment import get_resource_and_return_file_name, delete_temp_files


def add_time_information_to_output(start_time):
    "add time information to output"
    end_time = datetime.datetime.now()
    return {'query_duration': (end_time - start_time).total_seconds(),
            'query_timestamp_start': str(start_time),
            'query_timestamp_end': str(end_time)}


def handler(event, context):
    start_timestamp = datetime.datetime.now()

    # get the audio file (from bucket, from link or from file) and store in a temp file
    file_name = get_resource_and_return_file_name(event)

    # call openai api to get the transcript
    f = open(file_name, 'rb')
    transcript = openai.Audio.transcribe("whisper-1", f)

    # get the text
    transcript_text = transcript.to_dict()['text']

    # store in res variable
    res = {'data': {}, 'scores': {}}
    res['data']['transcript'] = transcript_text

    # clean the temp files
    delete_temp_files(file_name)

    res['data'].update(add_time_information_to_output(start_timestamp))

    return {
        'statusCode': 200,
        'body': json.dumps(res)
    }
