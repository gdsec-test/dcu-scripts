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
## K3s

### Bootstrapping K3s
Before configuring any K3s nodes you must first have the MySQL database brought up to the latest version. The K3s cluster bootstrapping is semi-stateful. You need to control the VM startup in a particular order to ensure there isn't a race condition for cluster initialization. Run the playbooks in this order;

```sh
ansible-playbook site.yaml -e "env=dev" --tags "k3s"
ansible-playbook oncall/k3s-init.yaml -e "env=dev" -i inventory/dev.yaml
# You can now SSH to the modified host and retrieve the kubeconfig from /etc/rancher/k3s/k3s.yaml
# You will need to swap in the NCM LB IP for 0.0.0.0 in the config.
ansible-playbook oncall/k3s-servers.yaml -e "env=dev" -i inventory/dev.yaml
ansible-playbook oncall/k3s-agents.yaml -e "env=dev" -i inventory/dev.yaml
```
You will also need to update your NFS shares per the documentation in `services/roles/k3s/manifests/nfs/README.md`.

### Updating K3s Manifests in the cluster
The Kubernetes cluster manifests are built from kustomize templates at playbook run time and loaded to the cluster. The K3s server process will detect the change to the manifest and apply the new state to the cluster. To just push a manifset update, run the command below(changing the env for your environment).

```sh
ansible-playbook oncall/k3s-manifests.yaml -e "env=dev" -i inventory/dev.yaml
```

### Kubernetes cluster access.
Retrieve the certs from `/KeePass/K8s/dev-ng-client.crt`/`/KeePass/K8s/dev-ng-client.key`/`/KeePass/K8s/dev-ng-root.crt`. Save them to your ~/.kube/ folder. You can then run; `kubectl config set-cluster dev-admin-ng --server=https://10.37.81.90:6443 --certificate-authority=~/.kube/dev-ng-root.crt`. Create your user with `kubectl config set-credentials dev-admin-ng --client-certificate=~/.kube/dev-ng-client.crt --client-key=~/.kube/dev-ng-client.key`. Create needed contexts with `kubectl config set-context dev-cset --cluster=dev-admin-ng --user=dev-admin-ng --namespace=abuse-api-dev` and `kubectl config set-context test-cset --cluster=dev-admin-ng --user=dev-admin-ng --namespace=abuse-api-test`.

Same instructions will apply for prod/ote, just switch dev for prod and test for ote.

## RabbitMQ

### Bootstrapping RabbitMQ
You will need to create some DNS records after running the first palybook.
Run the playbooks in this order;

```sh
ansible-playbook openstack/rabbitmq.yaml -e "env=<env name>"
# Now go to the Cloud UI and create DNS records in the format of;
# "node001.rmq.cset.int.dev-gdcorp.tools" where the number is the node
# id.
ansible-playbook openstack/inventory.yaml -e "env=<env name>"
ansible-playbook services/rabbitmq.yaml -e "env=<env name>" -i inventory/<env name>.yaml
ansible-playbook oncall/rabbitmq-init.yaml -e "env=<env name>" -i inventory/<env name>.yaml
# At this point you will have rabbitmq nodes, but they will not be clustering. On each node you
# will need to stop the application, join a cluster, and then start the app again. This is done
# like so;
#   rabbitmqctl stop_app
#   rabbitmqctl join_cluster <env>-cset
#   rabbitmqctl start_app
# Example of running one of these commands with Ansible.
#   ansible p3dlrmqsvr003.cloud.phx3.gdg --extra-vars "@oncall/vars.yaml" -i inventory/<env name>.yaml -a "systemctl status rabbitmq-server"
# If you have an existing cluster, login to the web UI to check the name. Otherwise pick a node
# for the initial cluster name and use that one.

# if creating a new cluster you will want to install the base config using this command.
ansible-playbook oncall/rabbitmq-bootstrap.yaml -e "env=<env name>" -i inventory/<env name>.yaml
```

### Removing old RMQ nodes
To remove a RabbitMQ node, you first must ensure all queues on that node are on other nodes. You can do this by running;
```sh
sudo rabbitmq-queues add_member --vhost "<vhost name>" "<queue name>" "<new node name>"
```
You can then delete the node from that queue.
```sh
sudo rabbitmq-queues delete_member --vhost "<vhost name>" "<queue name>" "<old node name>"
```
You can verify the changes with;
```sh
sudo rabbitmq-queues quorum_status --vhost "<vhost name>" "<queue name>"
```
Once you have done these steps for all queues to be moved off of the node, you need to stop the application on the node.
```sh
sudo rabbitmqctl stop_app
```
You then need to login to another node to remove the node from the cluster.
```sh
sudo rabbitmqctl forget_cluster_node <node name>
```
