dockerrepo := docker-dcu-local.artifactory.secureserver.net/cset-dev-image

.PHONY: devimage
devimage:
	@echo "----- building $(dockerrepo):latest -----"
	docker build -t $(dockerrepo):latest -f Dockerfile.devimage .
	docker push $(dockerrepo):latest
