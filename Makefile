# Run App
app.run.dev:
	@echo $(PYTHONPATH)
	cd project/ && gunicorn -w 3 -t 600 -b 0.0.0.0:8080 wsgi_dev:app

app.run.prod:
	@echo $(PYTHONPATH)
	cd project/ && gunicorn -w 3 -t 600 -b 0.0.0.0:8080 wsgi_prod:app

app.run.flask:
	@echo $(PYTHONPATH)
	cd project/ && export FLASK_APP=application.py && flask run

# Run Tests
# test.all:
# 	@echo $(PYTHONPATH)
# 	cd tests/ && py.test
