.PHONY: install run clean

install:
	pip3 install -r requirements.txt
	python3 -m playwright install chromium

run:
	python3 site_crawler.py $(or $(url),$(URL)) $(ARGS)

clean:
	rm -f *.csv
