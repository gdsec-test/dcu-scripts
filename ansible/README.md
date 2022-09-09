# Ansible Playbooks
The CSET team manages our infrastructure via a series of Ansible Playbooks. These playbooks are used to create/configure the openstack components themselves, as well as the configuration of the VMs.

The `site.yaml` playbook is a way to run end-to-end provisioning like so; `ansible-playbook site.yaml -e "env=dev" --tags "mongo"`. This will create the mongo tagged openstack VMs, install mongo on them, and configure general access. You can also run the calls individually by running things like `ansible-playbook openstack/k3s.yaml -e "env=dev"`  to create the dev openstack K3s nodes. You can re-generate the inventory files by running `ansible-playbook oncall/openstack-sync.yaml -e "env=dev"`. You can install service configuration on-top of the openstack VMs via `ansible-playbook services/k3s.yaml -e "env=dev" -i inventory/dev.yaml`.

## Access and more details
Before running any of the Ansible playbooks, you will need your shell configured to access both openstack and AWS. Run `make env` to install the needed tools first. You can then run `eval $(make auth-dev)` to auth into openstack and `okta` to auth into AWS.

You can then run playbooks like so;
```sh
ansible-playbook site.yaml -e "env=<env name>" --tags "<tag name>"
```

If you are running a specific service playbook, you will need to specify a inventory file. The inventory file name will change depending on the environment.
```sh
ansible-playbook oncall/k3s-agents.yaml -e "env=<env name>" -i inventory/<env name>.yaml
```

## Github Action Usage
TBD

## Bootstrapping K3s
Before configuring any K3s nodes you must first have the MySQL database brought up to the latest version. The K3s cluster bootstrapping is semi-stateful. You need to control the VM startup in a particular order to ensure there isn't a race condition for cluster initialization. Run the playbooks in this order;

```sh
ansible-playbook site.yaml -e "env=dev" --tags "k3s"
ansible-playbook oncall/k3s-init.yaml -e "env=dev" -i inventory/dev.yaml
ansible-playbook oncall/k3s-servers.yaml -e "env=dev" -i inventory/dev.yaml
ansible-playbook oncall/k3s-agents.yaml -e "env=dev" -i inventory/dev.yaml
```
