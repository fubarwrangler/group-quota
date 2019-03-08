rpm: gq-rpm web-rpm

tar: gq web

clean:
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf build/

gq:
	python setup-gq.py bdist

web:
	python setup-web.py bdist

gq-rpm:
	 python setup-gq.py bdist_rpm --requires MySQL-python

web-rpm:
	python setup-web.py bdist_rpm
