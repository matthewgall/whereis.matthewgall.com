.PHONY init setup rebuild-virtualenv
init:
	pip install -r requirements.txt

setup:
	source bin/activate
	pip install -r requirements.txt

rebuild-virtualenv:
	rm -rf bin/ include/ lib/ .Python
	virtualenv .