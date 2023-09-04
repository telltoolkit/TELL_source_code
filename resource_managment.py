import random
import boto3
import requests
import base64 


class OwnException(Exception):
    "own exception"
    pass


def fail(msg=''):
    "fail function"
    raise OwnException({'statusCode': 500, 'body': msg})


def get_random_filename():
    "get random filename"
    return str(random.random()).split('.')[1]+'.wav'


def save_audio_in_random_file(audio_file_content):
    "save audio in random file"
    file_name = get_random_filename()
    fout = open('/tmp/'+file_name, 'wb')
    fout.write(audio_file_content)
    fout.close()
    return fout.name


def get_resource_from_link(link):
    "get resource from link"
    url_resource = link
    res_request = requests.get(url_resource, timeout=60)
    if res_request.status_code != 200:
        raise OwnException
    return res_request.content


def get_resource_from_s3(audio_file):
    "get resource from s3"
    print("get_resource_from_s3", audio_file)
    s3_client = boto3.client('s3')
    bucket = audio_file['bucket']
    name = audio_file['name']
    obj = s3_client.get_object(Bucket=bucket, Key=name)
    return obj['Body'].read()


def get_resource_from_file(event):
    content_file_in_bytes = base64.b64decode(event['file'].encode('utf-8'))
    return content_file_in_bytes


def get_resource(event):
    if 'audio_file' in event:
        audio_file_dic = event['audio_file']

        if 'bucket' in audio_file_dic:
            try:
                return get_resource_from_s3(audio_file_dic)
            except:
                return fail('s3 fail')
        else:
            if 'file' in audio_file_dic:
                try:
                    return get_resource_from_file(audio_file_dic)
                except:
                    return fail('error in reading file from event')

            elif 'url' in audio_file_dic:
                try:
                    return get_resource_from_link(audio_file_dic['url'])
                except:
                    return fail('url requests exception')


def delete_temp_files(fn):
    try:
        os.remove(fn)
    except:
        pass


def get_resource_and_return_file_name(event):
    "get the resource file with the audio from bucket, file or url and store in a temp file"
    audio_file_content = get_resource(event)
    file_name = save_audio_in_random_file(audio_file_content)
    return file_name