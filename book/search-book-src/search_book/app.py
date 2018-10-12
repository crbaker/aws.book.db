import json
import requests
import base64
import uuid
import logging
import boto3
import random
from xml.etree import ElementTree

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    logger.debug("Checking for book")
    logger.debug(event)

    records = event['Records']
    for record in records:

        json_data = base64.b64decode(record['kinesis']['data'])

        dic = json.loads(json_data)

        book_isbn = dic['isbn']
        subject = dic['sub']

        results = search_book(book_isbn)

        if results['totalItems'] == 1:
            book_item = results_to_book(book_isbn, subject, results['items'][0])
            save_book(book_item, 'books')
        else:
            fuzzy_result = fuzzy_resolve(book_isbn)
            if fuzzy_result:
                book_item = results_to_book(book_isbn, subject, fuzzy_result)
                save_book(book_item, 'books')
            else:
                results['isbn'] = book_isbn
                results['subject'] = subject
                results['reputation'] = 'inconclusive'
                save_book(results, 'books')

def fuzzy_resolve(book_isbn):
    match = resolve_from_goodreads(book_isbn)
    if match:
        return resolve_fuzzy_from_google(match[0], match[1])
    return None

def results_to_book(book_isbn, subject, book_item):
    book_item['isbn'] = book_isbn
    book_item['subject'] = subject
    book_item['reputation'] = 'conclusive'

    # fix this float, decimal issue
    volume_info = book_item['volumeInfo']
    if 'averageRating' in volume_info:
        volume_info['averageRating'] = str(volume_info['averageRating'])

    if 'saleInfo' in book_item:
        del book_item['saleInfo']

    return book_item

def search_book(isbn):
    logger.info("searching for book " + isbn)
    p = {"q":"isbn:" + isbn, "key":"AIzaSyAobwxOZis0BWKeSmSpEKJWdb3Nc0TAwtE"}
    response = requests.get(url="https://www.googleapis.com/books/v1/volumes", params=p)

    return response.json()

def save_book(book, table):
    table = dynamodb.Table(table)
    table.put_item (Item=book)

def resolve_from_goodreads(isbn):
    p = {"q":isbn, "key":"qJEqEXBpCfX0RqtXM8rmEg"}
    response = requests.get(url="https://www.goodreads.com/search/index.xml", params=p)
    
    tree = ElementTree.fromstring(response.content)
    total_results = int(tree.find('./search/total-results').text)
    
    if total_results > 0:
        # take the first result
        results = tree.find('./search/results')
        work = results[0]
        best_book = work.find('best_book')
        title = best_book.find('title').text
        author = best_book.find('author/name').text
        return (title, author)
    else:
        return None

def resolve_fuzzy_from_google(title, author):
    p = {"q":f"title:'{title}'+inauthor:'{author}'", "key":"AIzaSyAobwxOZis0BWKeSmSpEKJWdb3Nc0TAwtE"}
    response = requests.get(url="https://www.googleapis.com/books/v1/volumes", params=p)
    json = response.json()
    if json['totalItems'] > 0:
        return json['items'][0]
    else:
        return None