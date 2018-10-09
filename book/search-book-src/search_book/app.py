import json
import requests
import base64
import uuid
import logging
import boto3
import random

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    logger.debug("Checking for book")

    records = event['Records']
    for record in records:

        json_data = base64.b64decode(record['kinesis']['data'])
        book_isbn = json.loads(json_data)['isbn']

        results = search_book(book_isbn)

        if results['totalItems'] == 1:
            book_item = results['items'][0]
            book_item['isbn'] = book_isbn
            book_item['reputation'] = 'conclusive'

            # fix this float, decimal issue
            volume_info = book_item['volumeInfo']
            if 'averageRating' in volume_info:
                volume_info['averageRating'] = str(volume_info['averageRating'])

            save_book(book_item, 'books')
        else:
            d = {"isbn": book_isbn, "search_result": results}
            results['isbn'] = book_isbn
            results['reputation'] = 'inconclusive'
            save_book(results, 'books')

def search_book(isbn):
    logger.info("searching for book " + isbn)
    p = {"q":"isbn:" + isbn, "key":"AIzaSyAobwxOZis0BWKeSmSpEKJWdb3Nc0TAwtE"}
    response = requests.get(url="https://www.googleapis.com/books/v1/volumes", params=p)

    return response.json()

def save_book(book, table):
    table = dynamodb.Table(table)
    table.put_item (Item=book)