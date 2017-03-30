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
	<h3><a target="_blank" href="http://w3w.co/{{get('threeWords', '')}}">{{get('threeWords', '')}}</a></h3>
</body>
</html>