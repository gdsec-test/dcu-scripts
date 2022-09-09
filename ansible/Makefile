OSFLAG :=
ifeq ($(OS),Windows_NT)
	OSFLAG=WINDOWS
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		OSFLAG=LINUX
	endif
	ifeq ($(UNAME_S),Darwin)
		OSFLAG=DARWIN
	endif
endif

.PHONY: env
env:
	@pip install -r requirements.txt
	@ansible-galaxy collection install community.general
	@ansible-galaxy collection install community.mongodb
ifeq ($(OSFLAG),LINUX)
	@command -v sshpass >/dev/null || sudo yum install sshpass -y
else
	@command -v sshpass >/dev/null || brew install hudochenkov/sshpass/sshpass
endif

.PHONY: auth-dev
auth-dev:
	@osoktaauth --cloud phx --project-name abusepipeline-dev

.PHONY: auth-prod
auth-prod:
	@osoktaauth --cloud phx --project-name abusepipeline-prod
