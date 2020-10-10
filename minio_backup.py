'''This script will take a snapshot of your home-assistant deployment, upload the snapshot to a minio bucket and then remove the snapshot from home-assistant.
You will need to replace certain variables with values specific to your existing setup. The preferred way to do this is with environmental variables on 
the host system that will be running the script. While you can put those values into this script directly, they contain sensitve keys that would give anyone
who finds them access to you home-assistant and/or minio deployments. You likely will need to install the requests and/or minio libraries, this can be done via pip
or with the included requirements file.'''

import requests
import json
import datetime
import os
from minio import Minio
from minio.error import ResponseError

#Change these variables to suit your particular setup.
home_assistant_url = "Enter Home-Assistant URL Here"
ha_api_key = os.getenv("ha_api_key")
minio_access_key = os.getenv("minio_access_key")
minio_secret_key = os.getenv("minio_secret_key")
minio_host = "Enter Minio URL Here"
minio_bucket = "Enter the name of the minio bucket in which to store snapshots"

minioClient = Minio(minio_host,
               access_key=minio_access_key,
               secret_key=minio_secret_key,
               secure=False) #Change this to True if using proper TLS certs/setup.

def get_datetime():
    current_time = datetime.datetime.now()
    return(current_time)

def take_snapshot():
    url = home_assistant_url + "/api/hassio/snapshots/new/full"
    headers = {
        "Authorization": "Bearer " + api_token 
    }
    timestamp = get_datetime()
    test = {"name": str(timestamp)[0:19]}
    payload = json.dumps(test)
    response = requests.post(url, headers=headers, data=payload)
    snapshotJson = json.loads(response.text)
    slug = snapshotJson['data']['slug']
    return(slug)

def download_snapshot():
    slug = take_snapshot()
    date = str(get_datetime())[0:19]
    filename = date + ".tar"
    url = home_assistant_url + "/api/hassio/snapshots/" + slug + "/download"
    headers = {
        "Authorization": "Bearer " + api_token 
    }
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192): 
                if chunk:
                    f.write(chunk)
    print("File saved as", filename)
    print("Uploading snapshot")
    upload(filename)
    return(slug)

def upload(filename):
    try:
       minioClient.fput_object(minio_bucket, filename, filename)
       os.remove(filename)
    except ResponseError as err:
       print(err)

def delete_snapshot(slug):
    url = home_assistant_url + "/api/hassio/snapshots/" + slug + "/remove"
    headers = {
        "Authorization": "Bearer " + api_token 
    }
    response = requests.post(url, headers=headers)
    deleteJson = json.loads(response.text)
    print(deleteJson)

def main():
    slug = download_snapshot()
    delete_snapshot(slug)

main()
