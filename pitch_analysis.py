import os
import json
import datetime
import random
import requests
import fonisoun
import boto3
import base64
import numpy as np
from fonisoun.opensmile import opensmile_process_file
from fonisoun.utils import resample
from resource_managment import get_resource_and_return_file_name, delete_temp_files


def compute_pitch(file_name):
    "compute the pitch series using opensmile"
    wav_file = '.'.join(file_name.split('.')[:-1])+'_1600.wav'
    resample(file_name, wav_file)

    data = opensmile_process_file(
        wav_file, 'eGeMAPSv02', 'LowLevelDescriptors')
    series_pitch = data['F0semitoneFrom27.5Hz_sma3nz'].values.tolist()
    return series_pitch, wav_file


def pitch2hz(vv):
    return 440 * 2**((vv-48)/12)


def remove_nan_values(res):
    "remove nan values from the results"
    key_to_delete = []
    for k, v in res.items():
        if np.isnan(v):
            key_to_delete.append(k)
    for k in key_to_delete:
        del res[k]

    return res


def get_scores(pitch_series):
    "compute the scores"

    # remove series where the pitch does not exist
    # and with not valid values (>500hz)
    pitch_series = np.array([pitch2hz(v) for v in pitch_series])
    pitch_series_with_data = pitch_series[(
        pitch_series > 30) & (pitch_series < 500)]

    pitch_std = np.nanstd(pitch_series_with_data)
    pitch_mean = np.nanmean(pitch_series_with_data)

    return {'pitch__pitch_mean': pitch_mean,
            'pitch__pitch_std': pitch_std}


def get_raw_outputs(pitch_series):
    pitch_series_v = np.array(pitch_series)
    return {'pitch__pitch_series': pitch_series_v[~np.isnan(pitch_series_v)].tolist(), 'pitch__sample_hz': 100}


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

    # compute the pitch
    pitch_series, file_name_wav_1600 = compute_pitch(file_name)

    # compute the scores and outputs
    res = {}
    res['scores'] = remove_nan_values(get_scores(pitch_series))
    res['data'] = get_raw_outputs(pitch_series)
    res['data'].update(add_time_information_to_output(start_timestamp))

    # clean the temp files
    delete_temp_files(file_name)
    delete_temp_files(file_name_wav_1600)

    return {
        'statusCode': 200,
        'body': json.dumps(res)
    }
