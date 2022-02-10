image/build:
	docker build -t dcu-db-backup:local ./
	$(eval COMMIT:=$(shell git rev-parse --short HEAD))
	docker tag dcu-db-backup:local docker-dcu-local.artifactory.secureserver.net/dcu-db-backup:$(COMMIT)

image/push/prod: image/build
	read -p "About to build production image from origin/main branch. Are you sure? (Y/N): " response ; \
	if [[ $$response == 'N' || $$response == 'n' ]] ; then exit 1 ; fi
	if [[ `git status --porcelain | wc -l` -gt 0 ]] ; then echo "You must stash your changes before proceeding" ; exit 1 ; fi
	$(eval COMMIT:=$(shell git rev-parse --short HEAD))
	docker push docker-dcu-local.artifactory.secureserver.net/dcu-db-backup:$(COMMIT)

k8s/deploy/prod:
	$(eval COMMIT:=$(shell git rev-parse --short HEAD))
	kubectl --context=prod-admin apply --dry-run=server -o yaml -f k8s/ | sed 's/REPLACE_WITH_GIT_COMMIT/$(COMMIT)/' | kubectl --context=prod-admin apply -f -
