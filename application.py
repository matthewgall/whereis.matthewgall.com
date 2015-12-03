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
from datetime import datetime
from urlparse import urlparse
from bottle import route, request, response, error, default_app, view, static_file
from logentries import LogentriesHandler
from LatLon import LatLon

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
			cur.execute('SELECT latitude,longitude FROM "checkins" ORDER BY id DESC')
			row = cur.fetchone()
			cur.close()
		except:
			conn.rollback()
			raise SystemError

		oldLocation = LatLon(row['latitude'],row['longitude'])
		newLocation = LatLon(lat, lon)
		distance = newLocation.distance(oldLocation)

		# If we have moved more than 200m, then we'll accept the movement
		if distance < 0.1:
			log.info("Not updating as latitude and longitude have not been modified by more than 100m: " + lat + "," + lon)
			return "Updated lat/lon is less than 100m away from previous checkin, ignoring"

		# Next, we'll do a display name lookup (to save the Nominatium API)
		payload = {
			'format': 'json',
			'lat': lat,
			'lon': lon,
			'zoom': 10,
			'addressdetails': 1
		}
		locationData = requests.get('http://nominatim.openstreetmap.org/reverse', params=payload)
		locationData = locationData.json()

		## Finally, we can process the insertion
		try:
			cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
			cur.execute(
				'INSERT INTO "checkins" (latitude, longitude, display_name, timestamp) VALUES (%s, %s, %s, %s)',
				(lat, lon, locationData['display_name'], int(time.time()))
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

@route('/history')
@view('history.tpl')
def api_history():

	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT latitude,longitude FROM "checkins" ORDER BY id DESC')
		row = cur.fetchone()
		cur.close()
	except Exception as e:
		conn.rollback()
		pass

	return dict(
		display_name="History",
		lat=row['latitude'],
		lon=row['longitude']
	)

@route('/history.json')
def api_history_json():

	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT * FROM "checkins" ORDER BY id DESC')
		row = cur.fetchall()
		cur.close()
	except Exception as e:
		conn.rollback()
		pass

	body = {
		"type": "FeatureCollection",
		"features": [],
	}

	for location in row:

		# Now, if display_name is empty, we're going to populate it for this row
		if location['display_name'] is None:

			# Perform the lookup
			payload = {
				'format': 'json',
				'lat': location['latitude'],
				'lon': location['longitude'],
				'zoom': 10,
				'addressdetails': 1
			}
			locationData = requests.get('http://nominatim.openstreetmap.org/reverse', params=payload)
			locationData = locationData.json()

			# Now, we have the data, so we'll update the lookup
			try:
				cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
				cur.execute(
					'UPDATE checkins SET display_name=%s WHERE id=%s', (locationData['display_name'], location['id'])
				)
				conn.commit()
			except Exception as e:
				conn.rollback()
				pass

			# Finally, as the change won't reflect until the next lookup, set the display_name variable
			display_name = locationData['display_name']
		else:
			# Otherwise, we'll just set this variable
			display_name = location['display_name']

		body['features'].append(dict(
			type="Feature",
			geometry=dict(
				type="Point",
				coordinates=[float(location['longitude']),float(location['latitude'])]
			),
			properties=dict(
				title=display_name,
				description="<strong>Last seen at: </strong>" + datetime.fromtimestamp(location['timestamp']).strftime('%d/%m/%Y %H:%M:%S')
			)
		))

	# And return this data, and all lookups to the script
	response.content_type = 'application/json'
	return json.dumps(body)

@route('/api')
def api_data():

	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT latitude,longitude,display_name,timestamp FROM "checkins" ORDER BY id DESC')
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

	# And return this data, and all lookups to the script
	response.content_type = 'application/json'
	return json.dumps(dict(
		displayname=row['display_name'],
		lat=row['latitude'],
		lon=row['longitude'],
		timestamp=datetime.fromtimestamp(row['timestamp']).strftime('%d/%m/%Y %H:%M:%S')
	))

@route('/')
@view('home')
def load_data():

	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT latitude,longitude,timestamp FROM "checkins" ORDER BY id DESC')
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
		timestamp=datetime.fromtimestamp(row['timestamp']).strftime('%d/%m/%Y %H:%M:%S')
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
