import json
import boto3
import logging
import requests
from chalice import Chalice
from datetime import datetime
from geopy.distance import vincenty
from boto3.dynamodb.conditions import Attr
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

now = datetime.utcnow()
app = Chalice(app_name='plugs')

@app.route('/')
def index():
    return {'hello': 'world'}

@app.route('/locations/{city}/{lat}/{lng}', cors=True)
def get_locations(city, lat, lng):
    lat = float(lat)
    lng = float(lng)
    me = (lat, lng)

    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Plugs')
        response = table.scan(
            FilterExpression=Attr('city').eq(
                'San Francisco') and Attr('enabled').eq(True)
        )
    except Exception as inst:
        logger.info(inst)
    items = response['Items']
    for item in items:
        try:
            coordinates = json.loads(item['location'])
            you = (float(coordinates['lat']), float(coordinates['lng']))
            coordinates['distance'] = vincenty(me, you).miles
            item['location'] = coordinates
        except Exception as inst:
            logger.info(inst)

    sorted_locations = sorted(items, key=lambda k: k['location']['distance'])
    return sorted_locations


@app.route('/locations/sanfrancisco', methods=['POST'])
def create_location():
    args = app.current_request.json_body
    coordinates = args.get('coordinates')
    lat, lng = coordinates['lat'], coordinates['lng']
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Plugs')
    try:
        plug = {
            'address': args.get('address'),
            'type': args.get('type'),
            'images': args.get('images'),
            'name': args.get('name'),
            'location': json.dumps(coordinates),
            'city':  args.get('city'),
            'mapLink': "comgooglemapsurl:://maps.google.com/maps?q={},{}".format(lat, lng),
            'enabled': args.get('enabled') or False
        }
        response = table.put_item(Item=plug)
        requests.post("https://carothers-hubot.herokuapp.com/plug", data=plug)
    except Exception as inst:
        logger.info((inst))

    return response


@app.route('/locations/sanfrancisco', methods=['PUT'])
def update_location():
    args = app.current_request.json_body
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Plugs')
    try:
        response = table.get_item(Key={
            'address': args.get('address')
        })
        plug = response['Item']
        item = {
            'address': args.get('address', plug['address']),
            'name': args.get('name', plug['name']),
            'type': args.get('type', plug['type']),
            'images': args.get('images', plug['images']),
            'location': json.dumps(args.get('coordinates', json.loads(plug['location']))),
            'city':  args.get('city', plug['city']),
            'mapLink': plug['mapLink'],
            'enabled': args.get('enabled', plug['enabled'])
        }
        logger.info(item)
        response = table.put_item(Item=item)
    except Exception as inst:
        logger.info((inst))

    return response


@app.route('/locations/sanfrancisco', methods=['DELETE'])
def delete_location():
    args = app.current_request.json_body
    try:
        address = args.get('address')
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('Plugs')
        response = table.delete_item(
            Key={
                'address': address
            }
        )
    except Exception as inst:
        logger.info((inst))

    return response


@app.route('/mailing', methods=['POST'], cors=True)
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
