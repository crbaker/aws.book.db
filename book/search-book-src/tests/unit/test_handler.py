from collections import namedtuple
import json

import pytest

from search_book import app

@pytest.fixture()
def apigw_event():
    return {
        "Records": [
        {
        "eventID": "shardId-000000000000:49545115243490985018280067714973144582180062593244200961",
        "eventVersion": "1.0",
        "kinesis": {
            "approximateArrivalTimestamp": 1428537600,
            "partitionKey": "partitionKey-3",
            "data": "ewogICAgImlzYm4iOiIxMjM0NTUzNCIKfQ==",
            "kinesisSchemaVersion": "1.0",
            "sequenceNumber": "49545115243490985018280067714973144582180062593244200961"
        },
        "invokeIdentityArn": "arn:aws:iam::EXAMPLE",
        "eventName": "aws:kinesis:record",
        "eventSourceARN": "arn:aws:kinesis:EXAMPLE",
        "eventSource": "aws:kinesis",
        "awsRegion": "eu-central-1"
        }
    ]
}


def test_lambda_handler(apigw_event, mocker):

    request_mock = mocker.patch.object(
        app, 'save_book', side_effect=None)

    app.lambda_handler(apigw_event, "")
