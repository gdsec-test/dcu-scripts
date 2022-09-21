# NFS Storage

The Kubernete's YAML files in this directory are based on the [NFS Client Provisioner](https://github.com/kubernetes-incubator/external-storage/tree/master/nfs-client). This provides dynamic provisioning of external storage via [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) (PV). PV's provide storage that is not tied to the lifecycle of a given Pod or Worker Node, that is, the availability of the workers do not impact the availability of the storage. Furthermore, this allows pods to be _stateful_ rather than _stateless_, in which their access to disk persists across pod restarts.

NFS currently provides access based on IP exports effectively providing whitelisting based on IP Addresses. The current approach requires that we whitelist each new [worker node's](https://cloud.int.godaddy.com/compute/vms/servers?nameFilter=wk&projectGuid=p3%7C7b5c56c1a3a5471f8f4762237ff8c3e0&regionId=p3) IP using the following [GetHelp Request](https://godaddy.service-now.com/gdsp?id=gd_sc_cat_item&sys_id=d5b912ab378f6680362896d543990eb6). This request only needs to occur if we expand the cluster to include more worker nodes, otherwise the new worker nodes will not be able to communicate with the NFS share and provide PV's to workloads on that node using this provisioner.

If you need to _extend_ or _expand_ an existing NFS share to include more storage it can be done via this [GetHelp Request](https://godaddy.service-now.com/gdsp?id=gd_sc_cat_item&sys_id=d5b912ab378f6680362896d543990eb6) by specifying the new NFS Share size in the "Misc Information" section.

If it becomes necessary to request a _new_ NFS share it can be done so via this [GetHelp Request](https://godaddy.service-now.com/gdsp?id=gd_sc_cat_item&sys_id=89880a63378b6680362896d543990e9b). Be sure to select the approach Network Security Zone e.g. Production as well as the Physical Location of the source e.g. P3/Buckeye. Otherwise the NFS Share may be unreachable.

## Other Solutions Considered

There are _many, many, many_ storage solutions provided by Kubernetes both in-tree and out-of-tree, so why NFS? Options that were considered and ultimately ruled out include the following:

1. HostPath Volumes
2. Local Storage
3. Other External Storage

### HostPath Volumes

HostPath volumes provide little guarantess of _real_ persistence and mounts a volume on the local worker node. However, if a pod restarts and is rescheduled on a separate node it no longer has access to this disk; anything stored would then be lost. This may be acceptable if dealing with a one node development cluster, but we have a production cluster of arbitrary size and this just will not work.

### Local Storage

Local Storage is a bit better than HostPaths for our use cases. The disk storage is still provisioned on the local worker node but it is _guaranteed_ that if a pod restarts that it will be re-scheduled on the node that has the storage block. Additionally, disk access is quite a bit faster than network storage because it is quite literally accesses to local disk.

However, there is currently no way to dynamically provision local storage and it was just pushed to General Availability (GA) in Kubernetes v1.14. This means a few things, we would have to provision the same volume mounts on all of our worker nodes or otherwise relegate specific workloads to run on specific nodes that had specific volume mounts. This generally seems against the spirit of Kubernetes and would require some customization to those workloads. Furthermore, the availability of the data relies on the availability of the worker node. If the node goes down, the data also goes down, and the pod will not be restarted on a separate node.

### Other External Storage

There are plenty of other external storage options as Kubernetes supports a plugin-based system a few of these include AWS EBS, AzureFile, CephFS, Cinder, Glusterfs, ScaleIO, StorageOS, etc. A more exhaustive list of provisioners can be found [here](https://kubernetes.io/docs/concepts/storage/storage-classes/#provisioner) and whether they are in-tree or out-of-tree. Additionally, each of these provisioners provide a myriad of [different access modes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes) such as _ReadWriteOnce_, _ReadOnlyMany_, and _ReadWriteMany_.

NFS supports all three of the above access modes and is readily supported via the Storage Team in-house. Other solutions are insufficient because they are off-prem integrations and we are responsible for sensitive workloads with specific legal requirements. In general, many solutions would require owning _even more_ architecture than we already do.
