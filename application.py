#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os, json, logging, time
import psycopg2, psycopg2.extras
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from urlparse import urlparse
from bottle import auth_basic, route, request, response, error, default_app, view, static_file
from logentries import LogentriesHandler
from LatLon import LatLon
from modules import Nominatim

def check(user, token):
	if user == os.getenv('APP_USER', 'update') and token == os.getenv('APP_TOKEN', 'testtoken'):
		return True
	return False

def submit(lat, lon, deviceID=''):
	try:
		locationData = Nominatim()
		locationData = locationData.reverse(lat, lon, 11)

		# Get the last check-in
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT latitude, longitude FROM "checkins" ORDER BY id DESC')
		row = cur.fetchone()
		cur.close()

		# If we have moved more than 100m, then we'll accept the check-in
		try:
			distance = LatLon(lat, lon).distance(LatLon(row['latitude'],row['longitude']))
			if distance < 0.1:
				message = "Not updating as latitude and longitude have not been modified by more than 100m: {}, {}".format(lat, lon)
				log.info(message)
				return message
		except TypeError:
			pass

		# Insert the requisite check-in record
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute(
			'INSERT INTO "checkins" (latitude, longitude, display_name, timestamp) VALUES (%s, %s, %s, %s)',
			(lat, lon, locationData['display_name'], int(time.time()))
		)
		log.info("Updated location to: {}, {}".format(lat, lon))
		conn.commit()
		cur.close()

	except ValueError:
		# Something was wrong with the latitude or logitude (probably invalid data)
		message = "You provided invalid data: {}, {}".format(lat, lon)
		log.info(message)
		return message

	return True

@route('/static/<filename>')
def css_static(filename):
	return static_file(filename, root='static')

@error('404')
@error('403')
def returnError(code, msg, contentType="text/plain"):
    response.status = int(code)
    response.content_type = contentType
    return msg

@route('/favicon.ico')
def error_404():
	response.status = 404
	response.content_type = 'text/plain'
	return 'Nothing here, sorry'

@route('/submit', method='POST')
@auth_basic(check)
def submitPOST():
	try:
		lat, lon = request.forms.get('location').split(',')
		deviceID = request.forms.get('device')
		if submit(lat, lon, deviceID):
			return "ok"
		return "error"
	except ValueError:
		response.status = 400
		response.content_type = 'text/plain'
		return 'Bad request'

@route('/submit/owntracks', method='POST')
@auth_basic(check)
def submitOwnTracks():
	try:
		postdata = json.loads(request.body.read())
		if postdata['_type'] == "location" and submit(postdata['lat'], postdata['lon']):
			return json.dumps({})
		return "error"
	except:
		response.status = 400
		response.content_type = 'text/plain'
		return 'Bad request'

@route('/api')
@view('api')
def api():
	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT latitude, longitude, display_name, timestamp FROM "checkins" ORDER BY id DESC')
		row = cur.fetchone()
		cur.close()

		# And return this data, and all lookups to the script
		response.content_type = 'application/json'
		return dict(
			name=row['display_name'],
			time=datetime.fromtimestamp(row['timestamp']).strftime('%d/%m/%Y %H:%M:%S')
		)
	except Exception as e:
		conn.rollback()
		pass

@route('/')
@view('home')
def home():
	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT latitude, longitude, display_name, timestamp FROM "checkins" ORDER BY id DESC')
		row = cur.fetchone()
		cur.close()

		attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
		human_readable = lambda delta: ['%d %s' % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1]) for attr in attrs if getattr(delta, attr)]
		timeSince = human_readable(relativedelta(datetime.now(), datetime.fromtimestamp(row['timestamp'])))

		# And return this data, and all lookups to the script
		return dict(
			name=row['display_name'],
			timeSince="({} ago)".format(', '.join(timeSince)),
			time=datetime.fromtimestamp(row['timestamp']).strftime('%d/%m/%Y %H:%M:%S')
		)
	except Exception as e:
		conn.rollback()
		pass

if __name__ == '__main__':

	app = default_app()

	serverHost = os.getenv('IP', 'localhost')
	serverPort = os.getenv('PORT', '5000')

	if not os.getenv('DATABASE_URL', '') == '':
		connectString = urlparse(os.getenv('DATABASE_URL', ''))
		postgresHost = os.getenv('POSTGRES_HOST', connectString.hostname)
		postgresPort = os.getenv('POSTGRES_PORT', connectString.port)
		postgresUser = os.getenv('POSTGRES_USER', connectString.username)
		postgresPassword = os.getenv('POSTGRES_PASS', connectString.password)
		postgresDatabase = os.getenv('POSTGRES_DB', connectString.path[1:])
	
	# Now we're ready, so start the server
	# Instantiate the logger
	log = logging.getLogger('log')
	console = logging.StreamHandler()
	log.setLevel(logging.INFO)
	log.addHandler(console)

	# Instantiate a connection
	try:
		conn = psycopg2.connect(
			database=postgresDatabase,
			user=postgresUser,
			password=postgresPassword,
			host=postgresHost,
			port=postgresPort
		)
	except:
		log.error("Unable to connect to postgreSQL server")
		exit(1)

	if os.getenv('LOGENTRIES_TOKEN') == '':
		log.addHandler(LogentriesHandler(os.getenv('LOGENTRIES_TOKEN', '')))

	# Now we're ready, so start the server
	try:
		app.run(host=serverHost, port=serverPort, server='cherrypy')
	except:
		log.error("Failed to start application server")
