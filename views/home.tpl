<!DOCTYPE html>
<html>
<head>
	<title>Where is Matthew? | Matthew Gall</title>

	<link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/font-awesome/4.5.0/css/font-awesome.min.css">
	<link rel="stylesheet" href="//fonts.googleapis.com/css?family=Gafata" type="text/css" media="all">
	<link rel="stylesheet" href='//api.mapbox.com/mapbox.js/v2.4.0/mapbox.css' />
	<link rel="stylesheet" href="/public/css/style.css" />

	<script src='//api.mapbox.com/mapbox.js/v2.4.0/mapbox.js'></script>
</head>
<body>
	<div id="map" class="dark"></div>
	<script>
		L.mapbox.accessToken = 'pk.eyJ1IjoibWF0dGhld2dhbGwiLCJhIjoiQmhiMlNDdyJ9.V-0y6h1GnVcVZAMrdJRYcg';
		var map = L.mapbox.map('map')
			.setView([{{lat}}, {{lon}}], 14);
		L.mapbox.styleLayer('mapbox://styles/mapbox/dark-v9').addTo(map);
		
		var featureLayer = L.mapbox.featureLayer()
			.loadURL('/api')
			.addTo(map);

		window.setInterval(function() {
			featureLayer.loadURL('/api')
		}, 60000);
	</script>
</body>
</html>