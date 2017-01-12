# DCOS Support Design Documentation

## Clouddriver

### Marathon app to Server Group conversion

* [ ] TODO: document any questions about mapping Marathon apps to the server group concept

### Regions & Availability Zones

Spinnaker does not seem to prescribe an availability zone distribution strategy for instances in server groups.  Server groups may be assigned to a region in the provider but the distribution of instances within the region is not specified. It may be implicit that providers are expected to do this without being directed to so.

As an aside, Kubernetes appears to use its namespaces as Spinnaker regions, which seems confusing because as far as I'm aware namespaces are for organization of multi-tenant clusters and don't imply the same isolation that regions would in an IaaS provider.

For DCOS we have 2 decisions to make:

* [ ] Do we support multiple regions, and if so, what is a region in DC/OS?
* [ ] Given that DC/OS does not really have availability zones but can use attributes and constraints to achieve a similar purpose, do we want to establish a convention that Spinnaker can automatically do this, or leave it entirely up to the user by letting constraints be set?

### Load Balancers

### Security Groups

## Orca

## Deck

---

## Cerner-specific concerns

### Logical multi-tenant deployments

### Security Tiers
