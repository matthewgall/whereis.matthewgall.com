<!DOCTYPE html>
<html>
<head>
	<title>Where is Matthew? | Matthew Gall</title>

	<link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/font-awesome/4.5.0/css/font-awesome.min.css">
	<link rel="stylesheet" href="//fonts.googleapis.com/css?family=Gafata" type="text/css" media="all">
	<link rel="stylesheet" href='//api.mapbox.com/mapbox.js/v2.2.3/mapbox.css' />
	<link rel="stylesheet" href="/public/css/style.css" />

	<script src='//api.mapbox.com/mapbox.js/v2.2.3/mapbox.js'></script>
</head>
<body>
	<div id="map" class="dark"></div>
	<div id="location">
		<p>{{town}}</p>
		<p>{{county}}</p>
		<p>{{country}}</p>
	</div>
	<script>
		L.mapbox.accessToken = 'pk.eyJ1IjoibWF0dGhld2dhbGwiLCJhIjoiY2lobTFpZnB1MDBlMHVza3FqNDcxcWJuOCJ9.ZXH7wvxQNQxOneG5vT_znA';
		var map = L.mapbox.map('map', 'mapbox.streets')
			.setView([{{lat}}, {{lon}}], 11);

		L.mapbox.featureLayer({
			type: 'Feature',
			geometry: {
				type: 'Point',
				// coordinates here are in longitude, latitude order because
				// x, y is the standard for GeoJSON and many formats
				coordinates: [
					{{lon}},
					{{lat}}
				]
			},
			properties: {
				title: '{{town}}, {{country}}',
				description: 'Last Reported: {{timestamp}}',
				// one can customize markers by adding simplestyle properties
				// https://www.mapbox.com/guides/an-open-platform/#simplestyle
				'marker-size': 'large',
				'marker-color': '#151515'
			}
		}).addTo(map);
	</script>
</body>
</html>