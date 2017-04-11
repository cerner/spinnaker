# DC/OS Conceptual Mapping

The following table describes the relationship between the clouddriver model Spinnaker uses and the underlying DC/OS entities that back that model.

| clouddriver     | details     | DC/OS
| :------------- | :------------- | :------------- |
| Account       |       | DC/OS user or service account       |
| Project       | 0..N applications | Logical grouping in Spinnaker with no direct analog in DCOS |
| Application | 0..N Clusters<br>1..N Accounts |   |
| Cluster | 0..N Server Group<br> 1 Account | |
| Load Balancer | 1 Account | A load balancer is an instance of [marathon-lb](https://github.com/mesosphere/marathon-lb).  Unlike load balancers in other Spinnaker providers that can be associated with applications through Spinnaker, marathon-lb's approach is to automatically manage load balancer pools using metadata (labels) in Marathon applications. |
| Server Group | 1 Account<br>1..N Instance<br>1 Region<br>| A server group in Spinnaker is a Marathon application in DC/OS. The name of the Marathon application will have the format `/account/region/app_stack_detail_sequence` Adding the label "HAPROXY_GROUP" with a value of the name of the Spinnaker load balancer to a server group will assign that server group to that marathon-lb instance.|
| Security Group | | No DC/OS concept applies to security groups today.  In the future perhaps this would be able control CNI plugins (like Calico) to limit access between server groups  |
| Instance | Belongs to one server group | An instance represents a Marathon task.
| Region | | DC/OS doesn't have any concept of regions in the sense that an IaaS provider like AWS does.  Spinnaker has an expectation that there must be a region for a server group so we have to implement it somehow. We have decided to take a somewhat similar approach to the way that Kubernetes handles regions.  In Kubernetes a region is a namespace and so its purpose is more organization than resiliency.  In DC/OS we consider the region for a server group to be one or more subgroups between the account name and the marathon application name.  
| Availability Zone | | Availability zones are not an entity in DC/OS. [Marathon constraints](https://github.com/mesosphere/marathon/blob/master/docs/docs/constraints.md) allow the spreading of server group instances across availability zones.  This is not integrated with Spinnaker beyond the ability to set these constraints as part of the server group definition.
| Stack | | Qualification for an application name that distinguishes one cluster from another.  In Spinnaker this is often used to have a non-prod and prod stack.  In DC/OS, region can also be used for this purpose (e.g. /account/prod/app, where "prod is the region name") |
| Detail | | Qualification for an application name that further distinguishes one cluster from another |
