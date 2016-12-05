<!DOCTYPE html>
<html>
<head>
	<title>Where is Matthew?</title>

	<link rel="stylesheet" href="//fonts.googleapis.com/css?family=Roboto" type="text/css" media="all">
	<link rel="stylesheet" href="/static/style.css" />
</head>
<body>
	<h1>{{get('name', 'Matthew has not checked in yet...')}}</h1>
	<h2>{{get('time', '')}} {{get('timeSince', '')}}</h2>
</body>
</html>