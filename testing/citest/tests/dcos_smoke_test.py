"""
Smoke test to see if Spinnaker can interoperate with DC/OS.

See testable_service/integration_test.py and spinnaker_testing/spinnaker.py
for more details.

Sample Usage:
TODO
"""

# Standard python modules.
import sys

# citest modules.
import citest.json_contract as jc
import citest.json_predicate as jp
import citest.service_testing as st

# Spinnaker modules.
import spinnaker_testing as sk
import spinnaker_testing.gate as gate
import spinnaker_testing.dcos_contract as dcos
import spinnaker_testing.frigga as frigga
import citest.base

class DcosSmokeTestScenario(sk.SpinnakerTestScenario):
  """Defines the scenario for the smoke test.

  This scenario defines the different test operations.
  We're going to:
    Create a Spinnaker Application
    Create a Spinnaker Load Balancer
    TODO Create a Spinnaker Server Group
    TODO Create a Pipeline with the following stages
      - Find Image
      - Deploy
    Delete each of the above (in reverse order)
  """

  @classmethod
  def new_agent(cls, bindings):
    """Implements citest.service_testing.AgentTestScenario.new_agent."""
    agent = gate.new_agent(bindings)
    agent.default_max_wait_secs = 180
    return agent

  def __init__(self, bindings, agent=None):
    """Constructor.

    Args:
      bindings: [dict] The data bindings to use to configure the scenario.
      agent: [GateAgent] The agent for invoking the test operations on Gate.
    """
    super(DcosSmokeTestScenario, self).__init__(bindings, agent)
    bindings = self.bindings

    # No detail because name length is restricted too much to afford one!
    self.__lb_detail = ''
    self.__lb_name = frigga.Naming.cluster(
        app=bindings['TEST_APP'],
        stack=bindings['TEST_STACK'])

    # We'll call out the app name because it is widely used
    # because it scopes the context of our activities.
    # pylint: disable=invalid-name
    self.TEST_APP = bindings['TEST_APP']

  def create_app(self):
    """Creates OperationContract that creates a new Spinnaker Application."""
    contract = jc.Contract()
    return st.OperationContract(
        self.agent.make_create_app_operation(
            bindings=self.bindings, application=self.TEST_APP,
            account_name=self.bindings['SPINNAKER_DCOS_ACCOUNT']),
        contract=contract)

  def delete_app(self):
    """Creates OperationContract that deletes a new Spinnaker Application."""
    contract = jc.Contract()
    return st.OperationContract(
        self.agent.make_delete_app_operation(
            application=self.TEST_APP,
            account_name=self.bindings['SPINNAKER_DCOS_ACCOUNT']),
        contract=contract)

  def upsert_load_balancer(self):
    """Creates OperationContract for upsertLoadBalancer.

    Calls Spinnaker's upsertLoadBalancer with a configuration, then verifies
    that the expected resources and configurations are visible on DC/OS.
    See the contract builder for more info on what the expectations are.
    """
    bindings = self.bindings
    payload = self.agent.make_json_payload_from_kwargs(
        job=[{
            'cloudProvider': 'dcos',
            'availabilityZones': {'global': ['global']},
            'provider': 'dcos',
            'app': bindings['TEST_APP'],
            'stack': bindings['TEST_STACK'],
            'detail': self.__lb_detail,
            'name': self.__lb_name,
            'bindHttpHttps': False,
            'account': bindings['SPINNAKER_DCOS_ACCOUNT'],
            'credentials': bindings['SPINNAKER_DCOS_ACCOUNT'],
            'cpus': 1,
            'instances': 1,
            'mem': 64,
            'acceptedResourceRoles': [],
            'portRange': {
              'protocol': 'tcp',
              'minPort': 10000,
              'maxPort': 10001
            },
            'type': 'upsertLoadBalancer',
            'user': '[anonymous]'
        }],
        description='Create Load Balancer: ' + self.__lb_name,
        application=self.TEST_APP)

    builder = dcos.DcosContractBuilder(self.dcos_observer)
    (builder.new_clause_builder('Load Balancer Added', retryable_for_secs=15)
     .get_marathon_resources('app')
     .contains_path_value('id', '/{0}/{1}'.format(bindings['SPINNAKER_DCOS_ACCOUNT'], self.__lb_name)))
    
    return st.OperationContract(
        self.new_post_operation(
            title='upsert_load_balancer', data=payload, path='tasks'),
        contract=builder.build())

  def delete_load_balancer(self):
    """Creates OperationContract for deleteLoadBalancer.

    To verify the operation, we just check that the DC/OS resources
    created by upsert_load_balancer are no longer visible in the cluster.
    """
    bindings = self.bindings
    payload = self.agent.make_json_payload_from_kwargs(
        job=[{
            'type': 'deleteLoadBalancer',
            'cloudProvider': 'dcos',
            'loadBalancerName': self.__lb_name,
            'account': bindings['SPINNAKER_DCOS_ACCOUNT'],
            'credentials': bindings['SPINNAKER_DCOS_ACCOUNT'],
            #'regions': ['default'],
            'user': '[anonymous]'
        }],
        description='Delete Load Balancer: {0} in {1}'.format(
            self.__lb_name,
            bindings['SPINNAKER_DCOS_ACCOUNT']),
        application=self.TEST_APP)

    builder = dcos.DcosContractBuilder(self.dcos_observer)
    (builder.new_clause_builder('Load Balancer Added', retryable_for_secs=15)
     .get_marathon_resources('app')
     .excludes_path_value('id', '/{0}/{1}'.format(bindings['SPINNAKER_DCOS_ACCOUNT'], self.__lb_name)))
    
    contract = jc.Contract()
    return st.OperationContract(
        self.new_post_operation(
            title='delete_load_balancer', data=payload, path='tasks'),
        contract=contract)

  def create_server_group(self):
    """Creates OperationContract for createServerGroup.

    To verify the operation, we just check that the server group was created.
    """
    bindings = self.bindings

    # Spinnaker determines the group name created,
    # which will be the following:
    group_name = frigga.Naming.server_group(
        app=self.TEST_APP, 
        stack=bindings['TEST_STACK'],
        version='v000')

    payload = self.agent.make_json_payload_from_kwargs(
        job=[{
            'cloudProvider': 'dcos',
            'application': self.TEST_APP,
            'account': bindings['SPINNAKER_DCOS_ACCOUNT'],
            'env': {},
            'desiredCapacity': 1,
            'cpus': 0.1,
            'mem': 64,
            'docker': {
              'image': {
                'repository': 'wg9059/nginx-test',
                'tag': 'canary',
                'imageId': 'dockerhub.cerner.com/wg9059/nginx-test:canary',
                'registry': 'dockerhub.cerner.com',
                'account': 'my-docker-registry-account'
              }
            },
            'networkType': {
              "type": "BRIDGE",
              "name": "Bridge"
            },
            'stack': bindings['TEST_STACK'],
            'type': 'createServerGroup',
            'region': 'default',
            'user': '[anonymous]'
        }],
        description='Create Server Group in ' + group_name,
        application=self.TEST_APP)
    
    builder = dcos.DcosContractBuilder(self.dcos_observer)
    (builder.new_clause_builder('Marathon App Added', retryable_for_secs=15)
     .get_marathon_resources('app'.format(bindings['SPINNAKER_DCOS_ACCOUNT']))
     .contains_path_value('id', '/{0}/default/{1}'.format(bindings['SPINNAKER_DCOS_ACCOUNT'], group_name)))
    
    return st.OperationContract(
        self.new_post_operation(
            title='create_server_group', data=payload, path='tasks'),
        contract=builder.build())


  def delete_server_group(self, version='v000'):
    """Creates OperationContract for deleteServerGroup.

    To verify the operation, we just check that the Kubernetes container
    is no longer visible (or is in the process of terminating).
    """
    bindings = self.bindings
    group_name = frigga.Naming.server_group(
        app=self.TEST_APP, stack=bindings['TEST_STACK'], version=version)

    payload = self.agent.make_json_payload_from_kwargs(
        job=[{
            'cloudProvider': 'dcos',
            'type': 'destroyServerGroup',
            'account': bindings['SPINNAKER_DCOS_ACCOUNT'],
            'credentials': bindings['SPINNAKER_DCOS_ACCOUNT'],
            'user': '[anonymous]',
            'serverGroupName': group_name,
            'asgName': group_name,
            'regions': ['default'],
            'region': 'default',
            'zones': ['default']
        }],
        application=self.TEST_APP,
        description='Destroy Server Group: ' + group_name)

    builder = dcos.DcosContractBuilder(self.dcos_observer)
    (builder.new_clause_builder('Marathon App Added', retryable_for_secs=15)
     .get_marathon_resources('app'.format(bindings['SPINNAKER_DCOS_ACCOUNT']))
     .excludes_path_value('id', '/{0}/default/{1}'.format(bindings['SPINNAKER_DCOS_ACCOUNT'], group_name)))
    
    contract = jc.Contract()
    return st.OperationContract(
        self.new_post_operation(
            title='delete_load_balancer', data=payload, path='tasks'),
        contract=contract)


class DcosSmokeTest(st.AgentTestCase):
  """The test fixture for the DcosSmokeTest.

  This is implemented using citest OperationContract instances that are
  created by the DcosSmokeTestScenario.
  """
  # pylint: disable=missing-docstring

  @property
  def scenario(self):
    return citest.base.TestRunner.global_runner().get_shared_data(
        DcosSmokeTestScenario)

  def test_a_create_app(self):
    self.run_test_case(self.scenario.create_app())

  def test_b_upsert_load_balancer(self):
    self.run_test_case(self.scenario.upsert_load_balancer())

  def test_c_create_server_group(self):
    self.run_test_case(self.scenario.create_server_group(),
                       max_retries=1,
                       timeout_ok=True)

  def test_x_delete_server_group(self):
    self.run_test_case(self.scenario.delete_server_group('v000'), max_retries=2)

  def test_y_delete_load_balancer(self):
    self.run_test_case(self.scenario.delete_load_balancer(),
                       max_retries=2)

  def test_z_delete_app(self):
    # Give a total of a minute because it might also need
    # an internal cache update
    self.run_test_case(self.scenario.delete_app(),
                       retry_interval_secs=8, max_retries=8)


def main():
  """Implements the main method running this smoke test."""

  defaults = {
      'TEST_STACK': 'tst',
      'TEST_APP': 'dcossmok' + DcosSmokeTestScenario.DEFAULT_TEST_ID
  }

  return citest.base.TestRunner.main(
      parser_inits=[DcosSmokeTestScenario.initArgumentParser],
      default_binding_overrides=defaults,
      test_case_list=[DcosSmokeTest])


if __name__ == '__main__':
  sys.exit(main())
