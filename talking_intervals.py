import os
import json
import datetime
import torch
from resource_managment import get_resource_and_return_file_name, delete_temp_files, convert_audio_to_wav
import numpy as np


def add_time_information_to_output(start_time):
    "add time information to output"
    end_time = datetime.datetime.now()
    return {'query_duration': (end_time - start_time).total_seconds(),
            'query_timestamp_start': str(start_time),
            'query_timestamp_end': str(end_time)}


def get_scores(timeline_activity, n_words):
    talking_time = np.nansum([e-s for s, e in timeline_activity])
    silences = [(a2.start-a1.end)
                for a1, a2 in zip(timeline_activity, timeline_activity[1:])]

    words_per_minute = (60*n_words) / \
        talking_time if talking_time > 0 else np.nan
    silence_median = np.nanmedian(silences)
    n_words_per_silence = n_words / \
        len(silences) if len(silences) > 0 else np.nan

    res = {'__words_per_minute': words_per_minute,
           '__silence_median_duration': silence_median,
           '__n_words_per_silence': n_words_per_silence,
           }

    return res


def remove_nan_values(res):
    "remove nan values from the results"
    key_to_delete = []
    for k, v in res.items():
        if np.isnan(v):
            key_to_delete.append(k)
    for k in key_to_delete:
        del res[k]

    return res


def handler(event, context):
    start_timestamp = datetime.datetime.now()

    # levanto n_words de transcript
    transcript = event['dependency_args']['transcript']['data']['transcript']
    print("transcript", transcript)
    n_words = len(transcript.split())
    print('n_words', n_words)

    # get the audio file (from bucket, from link or from file) and store in a temp file
    file_name = get_resource_and_return_file_name(event)

    file_name_wav = convert_audio_to_wav(file_name)
    # load models
    # local version
    # pyannotate_pipeline = torch.hub.load('/tmp/pyannote_pyannote-audio_master',
    #                                      'sad', pipeline=True,source='local')
    # pyannotate_pipeline = torch.hub.load('pyannote/pyannote-audio',
    #                                      'sad', pipeline=True)

    # pyannotate_pipeline = torch.hub.load('/tmp/torch_home/hub/pyannote_pyannote-audio_master/',
    #                                      'sad', pipeline=True, source='local')
    pyannotate_pipeline = torch.hub.load('/var/task/pyannote-audio-1.1.0/',
                                         'sad', pipeline=True, source='local')

    # # compute
    speech_activity_detection = pyannotate_pipeline({'audio': file_name_wav})
    timeline_activity = speech_activity_detection.get_timeline()

    res = {'data': {}, 'scores': {}}
    res['data']['timeline_activity'] = [
        (t.start, t.end) for t in timeline_activity]
    res['scores'] = remove_nan_values(get_scores(timeline_activity, n_words))

    # clean the temp files
    delete_temp_files(file_name)
    delete_temp_files(file_name_wav)

    res['data'].update(add_time_information_to_output(start_timestamp))

    return {
        'statusCode': 200,
        'body': json.dumps(res)
    }
