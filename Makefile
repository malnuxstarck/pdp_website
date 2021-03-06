# Progdupeupl's Makefile
#
# May provides useful targets in order to avoid a lot of typing when we want to
# run all the tests and other commands that require specific options.

MANAGE = manage.py
PMANAGE = venv/bin/python $(MANAGE)

FIXTURES = fixtures/auth.yaml \
	fixtures/forum.yaml \
	fixtures/member.yaml \
	fixtures/messages.yaml \
	fixtures/tutorial.yaml

ASSETS_DIR = ./assets/

# If you add a new target, do not forget to put it here so that make will not
# think your target is a real file.
.PHONY: tests \
	test \
	syncdb \
	migrate \
	initsearch \
	updatesearch \
	assets \
	collectstatic \
	loadfixtures \
	coverage \
	celery \
	bootstrap \
	cloc \
	installdeps \
	gitversion \
	pep8

# Test all the project
tests:
	$(PMANAGE) test

test: tests

# Synchronize the Django database with the models.
syncdb:
	$(PMANAGE) syncdb --no-initial-data --noinput

# Run the South database migrations.
migrate:
	$(PMANAGE) migrate

# Initialize the search engine and its cache.
initsearch:
	$(PMANAGE) rebuild_index --noinput

# Update the search engine cache.
updatesearch:
	$(PMANAGE) update_index

# Execute the Makefile in the assets directory.
assets:
	cd $(ASSETS_DIR) && $(MAKE)

# Collect and process all the static content.
collectstatic:
	$(PMANAGE) collectstatic --noinput

# Load fake data and put them in the database.
loadfixtures:
	$(PMANAGE) loaddata $(FIXTURES)

# Launch coverage report.
coverage:
	coverage run --source="." $(MANAGE) test $(TEST_APPS)
	coverage html

# Start the celery tasks server
celery:
	celery worker --app=pdp.celeryapp:app

# Initialize the whole project for the first time
bootstrap: installdeps syncdb migrate initsearch assets collectstatic loadfixtures updatesearch
	mkdir -p media/tutorials
	@echo "PDP Bootstrap finished!"

# Count lines of code, avoiding irrelevant files
cloc:
	cloc . --exclude-dir='assets,__pycache__,venv,media,static,migrations,fixtures'

# Install dependencies
installdeps:
	./install_dependencies.sh

gitversion:
	git describe | tee git_version.txt

pep8:
	flake8 --exclude=venv,'*/migrations/*',doc,pdp/wsgi.py .
