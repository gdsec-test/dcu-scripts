dockerrepo := gdartifactory1.jfrog.io/docker-dcu-local
DOCKER_TAG ?= latest

define build_docker_base
	docker pull $$(cat $(1)| grep FROM | awk '{print $$2}')
	docker build --label "BASE_DIGEST=$(dockerrepo)/$(2):$(DOCKER_TAG)" -t $(dockerrepo)/$(2):$(DOCKER_TAG) -f $(1) .
	docker push $(dockerrepo)/$(2):$(DOCKER_TAG)
endef

.PHONY: devimage
devimage:
	@echo "----- building $(dockerrepo)/cset-dev-image:latest -----"
	docker build --no-cache -t $(dockerrepo)/cset-dev-image:latest -f Dockerfile.devimage .
	docker push $(dockerrepo)/cset-dev-image:latest

.PHONY: alpine3.15
dcu-alpine3.15:
	$(call build_docker_base,dockerfiles/Dockerfile.dcu-alpine3.15,dcu-alpine3.15)

.PHONY: python3.10
dcu-python3.10:
	$(call build_docker_base,dockerfiles/Dockerfile.dcu-python3.10,dcu-python3.10)

.PHONY: python3.11
dcu-python3.11:
	$(call build_docker_base,dockerfiles/Dockerfile.dcu-python3.11,dcu-python3.11)