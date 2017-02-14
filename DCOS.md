# DCOS Support Design Documentation

## General

### Naming

In Spinnaker, a server group is identified by an account, region, app, stack (optional), detail (optional), and sequence; attributes that go from general to specific in that order.  Each of these attributes must appear in the name of the Marathon app representing that server group in order to avoid potential naming collisions.  Since Marathon supports groups for organization (and permissions in DC/OS) it seems like a good fit to make some of these attributes into groups rather than forcing all Marathon apps to share a single group.  

The Marathon app name for a Spinnaker server group will have the structure:

`/account/region/app_stack_detail_sequence`

example:

`/my_organization/my_team/usersService_prod_v001`

#### Account

We're making the assumption that anyone using multiple DC/OS accounts is doing so in order to allow permissions to control access and thus would always want the Marathon apps to be placed under a group for their account.  We've considered whether there would still be a need to allow Spinnaker to deploy apps in the root group, perhaps by only the primary account.  However we've decided to exclude that for now.

#### Region

"Region" here would be similar to the way Kubernetes replaces regions with namespaces.   Instead of "region" it may be called "group" or "path" and allow an arbitrary number of subgroups to be added to the path:

`/account/foo/bar/baz/app_stack_detail_sequence`

This is not exactly a conceptual fit with what Spinnaker regions are used for in AWS, Azure, etc but given that Kubernetes makes a similar stretch it seems reasonable.  One difference is that a namespace is required with Kubernetes but we would prefer to allow a group to be optional and deploy apps directly under the account group:

`/account/app_stack_detail_sequence`

Region seems to be assumed as required by parts of Spinnaker (orca at least) and so we can't entirely make it optional.  We think that duplicating the account into the region would be the best compromise, since account is always required.  In other words, the above app `/account/app_stack_detail_sequence` would belong to the spinnaker account `account` and the region `account`.  An app `/account/foo/bar/baz/app_stack_detail_sequence` would have account `account` and region `account/foo/bar/baz`.  This may cause some UI elements to seem redundant but apart from that seems to be good enough.

We considered automatically making stack part of the group hierarchy rather than leaving it in the Marathon app name.  While that fits the way we would plan to use it, other users may have different opinions.  Since stack is optional in Spinnaker and region will allow any number of subgroups, the same effect could be achieved without forcing it on everyone.


### Error conditions

---

# Projects

## Clouddriver

### Marathon app to Server Group conversion

* [ ] TODO: document any questions about mapping Marathon apps to the server group concept

### Marathon groups

* [x] decide if and how Marathon groups will be used by Spinnaker. (see General/Naming)

A Marathon group has some similarity with a Kubernetes namespace so it could be possible to use them the same way in Spinnaker.  However there are some problems:

* Namespaces are flat, groups can be nested
* Namespaces apply to all Kubernetes deployments, including jobs.  Groups are marathon only and wouldn't apply to Metronome jobs.

### Regions & Availability Zones

Spinnaker does not seem to prescribe an availability zone distribution strategy for instances in server groups.  Server groups may be assigned to a region in the provider but the distribution of instances within the region is not specified. It may be implicit that providers are expected to do this without being directed to so.

As an aside, Kubernetes appears to use its namespaces as Spinnaker regions, which seems confusing because as far as I'm aware namespaces are for organization of multi-tenant clusters and don't imply the same isolation that regions would in an IaaS provider.

For DCOS we have 2 decisions to make:

* [x] Do we support multiple regions, and if so, what is a region in DC/OS?
  * see General/Naming
* [ ] Given that DC/OS does not really have availability zones but can use attributes and constraints to achieve a similar purpose, do we want to establish a convention that Spinnaker can automatically do this, or leave it entirely up to the user by letting constraints be set?

### Clusters

* Clusters can contain server groups in different regions/namespaces and treat each as a separate deployment sequence


![TODO: local image references](https://www.evernote.com/l/AAG_UHU0zL1HALnrHOhgS2kA3cDzQhdf8UAB/image.png)

### Load Balancers

#### Marathon-LB

* Identifying marathon-lb instances as spinnaker loadbalancers: Load balancer instances created by Spinnaker will have a label with the key `SPINNAKER_LOAD_BALANCER`

#### Enterprise Load balancer

#### Minuteman

Minuteman VIPs can be supported minimally by allowing arbitrary attributes to be set when creating a server group, although the UI could handle these as a separate concern too.  Unlike marathon-lb there's really no need (or even a way) to interact with Minuteman through Spinnaker as it is autonomous and has no API. It does not support the zero-downtime deployment strategy but this might not disqualify it from use in canary deployment pipelines:

* It may use the TASK_KILLING state as an indication to stop routing traffic to instances that are being stopped. (TODO: awaiting response from Mesosphere)
* Applications should reasonably be expected to attempt to complete current requests after receiving SIGTERM.

In this case it should always be safe to stop a marathon app behind a Minuteman VIP, as long as there are instances of a new version running behind the same VIP.

### Security Groups

### Caching

#### Agents

Clouddriver allows each provider to register a set of agents that can be used to periodically query and cache data from the deployment target.  This allows Spinnaker to be able to construct a view of what entities exist in that target.  Caching agents can handle server groups, applications, load balancers, instances, etc.  They cache both data as well as relationships between the concepts (for example, the list of instances in a server group).  Every agent can serve as an authoritative or informational source for one or more types of entities.

#### OnDemand

OnDemand caching exists in order to allow Orca to refresh the cache for specific entities that are expected to change due to a pipeline step.

A TTL of 10 minutes seems to be the convention, hard-coded across all the different providers.  Unclear why or what the consequences of choosing a different value would be.

## Orca

## Deck

---

## Cerner-specific concerns

### Logical multi-tenant deployments

### Security Tiers

---

## Questions for Mesosphere

* [ ] Will region/namespace make sense for the new LB?
