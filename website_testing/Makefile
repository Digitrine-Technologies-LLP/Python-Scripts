.PHONY: install test test-responsive test-cross clean

URL ?= https://example.com

install:
	pip3 install -r requirements.txt

test-responsive:
	python3 -m pytest test_responsive.py -v --url=$(or $(url),$(URL))

test-cross:
	python3 -m pytest test_cross_browser.py -v --url=$(or $(url),$(URL))

test:
	python3 -m pytest -v --url=$(or $(url),$(URL))

clean:
	rm -f screenshot_*.png
