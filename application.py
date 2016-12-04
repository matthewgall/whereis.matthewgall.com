#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import os, json, logging, time
import psycopg2, psycopg2.extras
import requests
from datetime import datetime
from urlparse import urlparse
from bottle import route, request, response, error, default_app, view, static_file
from logentries import LogentriesHandler
from LatLon import LatLon
from modules import Nominatim

@route('/public/css/<filename>')
def css_static(filename):
	return static_file(filename, root='public/css')

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
def process_data():

	# First, we'll verify the token provided in the request
	if not request.forms.get('token') == os.getenv('APP_TOKEN', 'testtoken'):
		response.status = 403
		response.content_type = 'text/plain'
		log.info("Invalid token provided: {}".format(request.forms.get('token')))
		return "Invalid token provided: {}".format(request.forms.get('token'))

	# Now the token is verified, we'll be gathering other data
	try:
		lat, lon = request.forms.get('location').split(',')
		deviceID = request.forms.get('device')

		try:
			locationData = Nominatim()
			locationData = locationData.reverse(lat, lon)

			# Get the last check-in
			cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
			cur.execute('SELECT latitude, longitude FROM "checkins" ORDER BY id DESC')
			row = cur.fetchone()
			cur.close()

			# If we have moved more than 100m, then we'll accept the check-in
			distance = LatLon(lat, lon).distance(LatLon(row['latitude'],row['longitude']))
			if distance < 0.1:
				message = "Not updating as latitude and longitude have not been modified by more than 100m: {}, {}".format(lat, lon)
				log.info(message)
				return message

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
		except:
			conn.rollback()
			message = "We encountered a system error performing your request. Please try again later"
			log.error(message)
			return message
		return "ok"

	except ValueError:
		response.status = 400
		response.content_type = 'text/plain'
		return 'Bad request'

@route('/history')
@view('history.tpl')
def api_history():
	try:
		# Get our last check-in to frame the map correctly
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT latitude, longitude FROM "checkins" ORDER BY id DESC')
		row = cur.fetchone()
		cur.close()

		# And return a dictionary to display the view, a later AJAX call will complete it
		return dict(
			display_name="History",
			lat=row['latitude'],
			lon=row['longitude']
		)
	except Exception as e:
		conn.rollback()
		pass

@route('/history.json')
def api_history_json():

	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT * FROM "checkins" ORDER BY id DESC LIMIT 500')
		row = cur.fetchall()
		cur.close()
	except Exception as e:
		conn.rollback()
		pass

	body = {
		"type": "FeatureCollection",
		"features": []
	}

	for location in row:

		# Now, if display_name is empty, we're going to populate it for this row
		if location['display_name'] is None:

			# Perform the lookup
			locationData = Nominatim()
			locationData = locationData.reverse(lat, lon)

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
				description="<strong>Last seen at: </strong> {}".format(datetime.fromtimestamp(location['timestamp']).strftime('%d/%m/%Y %H:%M:%S'))
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
		cur.execute('SELECT latitude, longitude, display_name, timestamp FROM "checkins" ORDER BY id DESC')
		row = cur.fetchone()
		cur.close()
	except Exception as e:
		conn.rollback()
		pass

	# And return this data, and all lookups to the script
	response.content_type = 'application/json'

	body = {
		"type": "FeatureCollection",
		"features": [],
	}

	body['features'].append(dict(
		type="Feature",
		geometry=dict(
			type="Point",
			coordinates=[float(row['longitude']),float(row['latitude'])]
		),
		properties=dict(
			title=row['display_name'],
			description="<strong>Last seen at: </strong> {}".format(datetime.fromtimestamp(row['timestamp']).strftime('%d/%m/%Y %H:%M:%S'))
		)
	))

	return json.dumps(body)

@route('/')
@view('home')
def load_data():

	# First, we'll perform the select of the latest checkin
	try:
		cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		cur.execute('SELECT latitude, longitude, display_name, timestamp FROM "checkins" ORDER BY id DESC')
		row = cur.fetchone()
		cur.close()

		if row is None:
			return dict(
				lat='',
				lon=''
			)
		else:
			# And return this data, and all lookups to the script
			return dict(
				display_name=row['display_name'],
				lat=row['latitude'],
				lon=row['longitude'],
				timestamp=datetime.fromtimestamp(row['timestamp']).strftime('%d/%m/%Y %H:%M:%S')
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
