shell := /bin/bash

define deploy_k8s
	kubectl --context $(1)-cset apply -k k8s/$(1)
endef

.PHONY: init
init:
	@echo "----- Make init-----"

.PHONY: unit-test
unit-test:
	@echo "----- No unit tests-----"

.PHONY: testcov
testcov:
	@echo "----- No tests to run for coverage-----"

.PHONY: prod-deploy
prod-deploy:
	@echo "----- deploying $(reponame) prod -----"
	$(call deploy_k8s,prod)
