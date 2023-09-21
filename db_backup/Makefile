DOCKER_IMAGE=gdartifactory1.jfrog.io/docker-dcu-local/dcu-db-backup

image/build:
	docker build -t dcu-db-backup:local ./
	docker tag dcu-db-backup:local $(DOCKER_IMAGE):prod

image/push: image/build
	docker push $(DOCKER_IMAGE):prod

k8s/deploy:
	$(eval DIGEST:=$(shell docker inspect --format='{{index .RepoDigests 0}}' $(DOCKER_IMAGE):prod))
	kubectl --context=prod-cset apply --dry-run=server -o yaml -f k8s/ | sed 's#REPLACE_WITH_GIT_COMMIT#$(DIGEST)#' | kubectl --context=prod-cset apply -f -
