# P3 Kubernetes Manifests
This folder is intended to contain Kubernetes definitions that we host for external stakeholders. We should not use this location to host definitions which need associated containers(those should live in their own repos), or which are part of the Kubernetes cluster infrastructure itself(those should live in `ansible/services/roles/k3s/manifests`).

## Services

### Splunk Broker
We run the SOAR Splunk Automation broker for the Product Security team within our P3 Kubernetes cluster. This service must run as a single container, as it's persistent storage usage is not multi-process safe. It requires a persistent NFS share to store the configuration data it receives from SOAR.

## Deployment
Run `make <env>-deploy` to deploy changes to the environment you are updating.

## Testing
We have no easy way to test these definitions, you will need to work with the project stakeholders.

## Stakeholder Mapping
|Project|Slack Channel
--------|---------------
|splunk_broker|#product-security


