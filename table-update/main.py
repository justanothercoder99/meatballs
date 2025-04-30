from cloudevents.http import CloudEvent
import functions_framework
import os
import pandas as pd
from io import StringIO

import pandas.io.sql as pd_sql
pd_sql._maybe_cast_to_sqlalchemy = lambda con: con

from dbHandler import DBHandler
from google.cloud import storage

dbHandler = DBHandler()
dbHandler.setupEngine()

# Initialize storage client
storage_client = storage.Client()

# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def blob_trigger(cloud_event: CloudEvent) -> None:
    data = cloud_event.data

    event_id = cloud_event["id"]
    event_type = cloud_event["type"]

    #"""Triggered by a change to a Cloud Storage bucket."""
    bucket_name = data['bucket']
    blob_name = data['name']

    print(f"[ID:{event_id}] Data: {cloud_event.data}")
    print(f"[ID:{event_id}] Processing file: {blob_name} from bucket: {bucket_name}")

    # Download CSV into pandas
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    csv_data = blob.download_as_text()
    df = pd.read_csv(StringIO(csv_data))

    # Example: Insert data into a table (replace 'your_table')
    # with dbHandler.engine.begin() as con:
    #     df.to_sql(blob_name, con=con, if_exists='replace', index=False, method="multi")
    df.to_sql(
        name=blob_name,
        con=dbHandler.engine,
        if_exists='replace',
        index=False,
        method='multi'
    )

    print(f"[ID:{event_id}] Table your_table updated successfully with {len(df)} rows.")

