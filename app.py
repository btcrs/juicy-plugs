import os
import json
import boto3
from chalice import Chalice
from datetime import datetime
from geopy.distance import vincenty
from boto3.dynamodb.conditions import Key, Attr

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

now = datetime.utcnow()
app = Chalice(app_name='plugs')


@app.route('/')
def index():
    return {'hello': 'world'}


@app.route('/locations/{city}/{lat}/{lng}')
def get_locations(city, lat, lng):
    lat = float(lat)
    lng = float(lng)
    me = (lat, lng)

    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Plugs')
        response = table.scan(
            FilterExpression=Attr('City').eq('San Francisco')
        )
    except Exception as inst:
        logger.info(inst)

    items = response['Items']

    for item in items:
        try:
            coordinates = json.loads(item['Location'])
            you = (float(coordinates['lat']), float(coordinates['lng']))
            coordinates['distance'] = vincenty(me, you).miles
            item['Location'] = coordinates
        except Exception as inst:
            logger.info(inst)

    sorted_locations = sorted(items, key=lambda k: k['Location']['distance'])
    return sorted_locations


@app.route('/locations/sanfrancisco', methods=['POST'])
def create_location():
    args = app.current_request.json_body
    coordinates = args.get('coordinates')
    lat, lng = coordinates['lat'], coordinates['lng']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Plugs')
    try:
        response = table.put_item(Item={
            'Address': args.get('address'),
            'Type': args.get('type'),
            'Images': args.get('images'),
	    'Name': args.get('name'),
            'Location': json.dumps(coordinates),
            'City':  args.get('city'),
            'MapLink': "comgooglemapsurl:://maps.google.com/maps?q={},{}".format(lat, lng)
        })
    except Exception as inst:
        logger.info((inst))

    return response
  
@app.route('/locations/sanfrancisco', methods=['PUT'])
def update_location():
    args = app.current_request.json_body
    coordinates = args.get('coordinates')
    lat, lng = coordinates['lat'], coordinates['lng']
    #dynamodb = boto3.resource('dynamodb')
    #table = dynamodb.Table('Plugs')
    #try:
	#response = table.put_item(Item={
	    #'Address': args.get('address'),
	    #'Type': args.get('type'),
	    #'Images': args.get('images'),
	    #'Location': json.dumps(coordinates),
	    #'City':  args.get('city'),
	    #'MapLink': "comgooglemapsurl:://maps.google.com/maps?q={},{}".format(lat, lng)
	#})
    #except Exception as inst:
	#logger.info((inst))

    #return response
    return {"updated": "true"}

@app.route('/locations/sanfrancisco', methods=['DELETE'])
def delete_location():
    args = app.current_request.json_body
    try:
      address = args.get('address')
      dynamodb = boto3.resource('dynamodb')
      table = dynamodb.Table('Plugs')
      table.delete_item(
	Key={
	    'Address': address
	    }
      )
    except Exception as inst:
	logger.info((inst))

    return response

@app.route('/mailing' , methods=['POST'], cors=True)
def add_email():
    args = app.current_request.json_body
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Mailing')
    try:
	response = table.put_item(Item={
	    'email': args.get('email')
	})
    except Exception as inst:
	logger.info((inst))

    return response
