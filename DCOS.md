# DCOS Support Design Documentation

## Questions for Scrum

* []

## General

### Naming

In Spinnaker, a server group is identified by an account, region, app, stack (optional), detail (optional), and sequence; attributes that go from general to specific in that order.  Each of these attributes must appear in the name of the Marathon app representing that server group in order to avoid potential naming collisions.  Since Marathon supports groups for organization (and permissions in DC/OS) it seems like a good fit to make some of these attributes into groups rather than forcing all Marathon apps to share a single group.  

The Marathon app name for a Spinnaker server group will have the structure:

`/account/region/app_stack_detail_sequence`

While stack is more specific than app in Spinnaker terms, we think it should be the opposite in the Marathon name.  If the last segment of the fully qualified Marathon app did not contain the app name it would look odd in the Marathon UI.  

"Region" here would be similar to the way Kubernetes replaces regions with namespaces.  It will be optional, however. Instead of "region" it may be called "group" or "path" and allow an arbitrary number of subgroups to be added to the path:

`/account/foo/bar/baz/app_stack_detail_sequence`

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
