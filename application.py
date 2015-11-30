#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os
import json
import socket
import logging
import time
import psycopg2
import psycopg2.extras
import requests
from urlparse import urlparse
from bottle import route, request, response, error, default_app, view, static_file
from logentries import LogentriesHandler
import pprint

@route('/public/css/<filename>')
def css_static(filename):
	return static_file(filename, root='public/css')

@route('favicon.ico')
@error(404)
def error_404(error):
	response.status = 404
	response.content_type = 'text/plain'
	return 'Nothing here, sorry'

@route('/submit', method='POST')
def process_data():

	# First, we'll verify the token provided in the request
	if not request.forms.get('token') == os.getenv('APP_TOKEN', 'testtoken'):
		response.status = 403
		response.content_type = 'text/plain'
		log.info("Invalid token provided: " + request.forms.get('token'))
		return 'Forbidden'

	# Now the token is verified, we'll be gathering other data
	try:
		lat, lon = request.forms.get('location').split(',')
		deviceID = request.forms.get('device')

		# At a minimum, the app needs the latitude and longitude
		if not (lat or lon):
			raise ValueError

		# Latitude measures how far north or south of the equator a place is located. 
		# The equator is situated at 0°, the North Pole at 90° north (or 90°, because a positive 
		# latitude implies north), and the South Pole at 90° south (or -90°). Latitude measurements
		# range from 0° to (+/–)90°.
		if not (float(lat) <= -90) and (float(lat) >= 90):
			raise ValueError

		# Longitude measures how far east or west of the prime meridian a place is located.
		# The prime meridian runs through Greenwich, England. Longitude measurements range from 0° 
		# to (+/–)180°.
		if not (float(lon) <= -180) and (float(lon) >= 180):
			raise ValueError

		# Once all this checks out, we can move to do some data insertion, first, we'll double check
		# that we haven't been here before
		try:
			cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
			cur.execute('SELECT * FROM "checkins" ORDER BY id DESC')
			row = cur.fetchone()
			cur.close()
		except:
			conn.rollback()
			raise SystemError

		if (lat == row['latitude']) and (lon == row['longitude']):
			log.info("Not updating as latitude and longitude have not been modified: " + lat + "," + lon)
			return "Still here, ignoring."

		## Finally, we can process the insertion
		try:
			cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
			cur.execute(
				'INSERT INTO "checkins" (latitude, longitude, timestamp) VALUES (%s, %s, %s)',
				(lat, lon, int(time.time()))
			)
			log.info("Updated location to: " + lat + "," + lon)
			conn.commit()
		except Exception as e:
			conn.rollback()
			raise SystemError

		return "ok"

	except ValueError:
		response.status = 400
		response.content_type = 'text/plain'
		return 'Bad request'

	except SystemError:
		response.status = 503
		response.content_type = 'text/plain'
		return 'Server error'

@route('/')
@view('home')
def load_data():

	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT * FROM "checkins" ORDER BY id DESC')
		row = cur.fetchone()
		cur.close()
	except Exception as e:
		conn.rollback()
		pass

	# Now, we run a request against nominatim (a service provided by openstreetmap)
	payload = {
		'format': 'json',
		'lat': row['latitude'],
		'lon': row['longitude'],
		'zoom': 10,
		'addressdetails': 1
	}
	locationData = requests.get('http://nominatim.openstreetmap.org/reverse', params=payload)
	locationData = locationData.json()

	# And return this data, and all lookups to the script
	return dict(
		display_name=locationData['display_name'],
		lat=row['latitude'],
		lon=row['longitude'],
		timestamp=row['timestamp']
	)

if __name__ == '__main__':

	app = default_app()

	serverHost = os.getenv('SERVER_HOST', 'localhost')
	serverPort = os.getenv('SERVER_PORT', '5000')

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
		log.info("Successfully connected to postgreSQL server at " + postgresHost)
	except:
		log.error("Unable to connect to postgreSQL server")
		exit(1)

	if os.getenv('LOGENTRIES_TOKEN') == '':
		log.addHandler(LogentriesHandler(os.getenv('LOGENTRIES_TOKEN', '')))

	# Now we're ready, so start the server
	try:
		log.info("Successfully started application server on " + socket.gethostname())
		app.run(host=serverHost, port=serverPort)
	except:
		log.info("Failed to start application server on " + socket.gethostname())
