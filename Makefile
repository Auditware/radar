-include Makefile.local

compose:
	docker compose up -d --build

compose-dbg:
	DOCKER_BUILDKIT=0 docker compose up --build

# e.g. make run root=~/Desktop/anchor-test source=programs/anchor-test/src/lib.rs
#      make build root=~/Desktop/anchor-test source=programs/anchor-test/src/lib.rs
run:
	docker compose run --rm -v $(root):/contract radar --path /contract/$(source)

build:
	$(MAKE) compose
	$(MAKE) try
	
	
include .env
export
api-local:
	cd api/ && poetry run python manage.py makemigrations
	cd api/ && poetry run python manage.py migrate
	cd api/ && poetry run gunicorn --bind 0.0.0.0:8000 api.wsgi:application