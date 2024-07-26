-include Makefile.local

compose:
	docker compose -f docker-compose-dev.yml up -d --build

compose-dbg:
	DOCKER_BUILDKIT=0 docker compose up --build

# e.g. make run root=~/Desktop/anchor-test source=programs/anchor-test/src/lib.rs
#      make build root=~/Desktop/anchor-test source=programs/anchor-test/src/lib.rs
run:
	docker compose -f docker-compose-dev.yml run --rm -v $(root):/contract radar --path $(root) --container-path /contract/$(source)
	@docker cp radar-api:/radar_data/output.json .

build-run:
	$(MAKE) compose
	$(MAKE) run

test:
	cd api/ && poetry run pytest -s -v

update-docs:
	git clone https://github.com/Auditware/radar.wiki.git
	cp -r docs/* radar.wiki/
	cd radar.wiki/ && \
	git add . && \
	git commit -m "Update docs" && \
	git push origin master
	rm -rf radar.wiki/
	
include .env
export
api-local:
	cd api/ && poetry run python manage.py makemigrations
	cd api/ && poetry run python manage.py migrate
	cd api/ && poetry run gunicorn --bind 0.0.0.0:8000 api.wsgi:application