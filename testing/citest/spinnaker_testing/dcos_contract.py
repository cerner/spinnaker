"""Provides a means for specifying and verifying expectations of Kubernetes."""

# Standard python modules.
import json
import logging
import traceback

# Our modules.
# from .. import json_predicate as jp
# from .. import json_contract as jc
# from ..service_testing import cli_agent

import citest.json_contract as jc
import citest.json_predicate as jp
import citest.service_testing as st

class DcosObjectObserver(jc.ObjectObserver):
  """Observe DC/OS resources."""

  def __init__(self, dcoscli, args, filter=None):
    """Construct observer.

    Args:
      kubectl: KubeCtlAgent instance to use.
      args: Command-line argument list to execute.
    """
    super(DcosObjectObserver, self).__init__(filter)
    self.__dcoscli = dcoscli
    self.__args = args

  def export_to_json_snapshot(self, snapshot, entity):
    """Implements JsonSnapshotableEntity interface."""
    snapshot.edge_builder.make_control(entity, 'Args', self.__args)
    super(DcosObjectObserver, self).export_to_json_snapshot(snapshot, entity)

  def __str__(self):
    return 'DcosObjectObserver({0})'.format(self.__args)

  def collect_observation(self, context, observation, trace=True):
    return []
    # args = context.eval(self.__args)
    # kube_response = self.__kubectl.run(args, trace=trace)
    # if not kube_response.ok():
    #   observation.add_error(
    #       cli_agent.CliAgentRunError(self.__kubectl, kube_response))
    #   return []

    # decoder = json.JSONDecoder()
    # try:
    #   doc = decoder.decode(kube_response.output)
    #   if not isinstance(doc, list):
    #     doc = [doc]
    #   self.filter_all_objects_to_observation(context, doc, observation)
    # except ValueError as vex:
    #   error = 'Invalid JSON in response: %s' % str(kube_response)
    #   logging.getLogger(__name__).info('%s\n%s\n----------------\n',
    #                                    error, traceback.format_exc())
    #   observation.add_error(jp.JsonError(error, vex))
    #   return []

    # return observation.objects


class DcosObjectFactory(object):
  # pylint: disable=too-few-public-methods

  def __init__(self, dcoscli):
    self.__dcoscli = dcoscli

  def new_get_resources(self, type, extra_args=None):
    """Specify a resource list to be returned later.

    Args:
      type: kubectl's name for the Kubernetes resource type.

    Returns:
      A jc.ObjectObserver to return the specified resource list when called.
    """
    if extra_args is None:
      extra_args = []

    # cmd = self.__kubectl.build_kubectl_command_args(
    #     action='get', resource=type, args=['--output=json'] + extra_args)
    return DcosObjectObserver(self.__dcoscli, None)


class DcosClauseBuilder(jc.ContractClauseBuilder):
  """A ContractClause that facilitates observing Kubernetes state."""

  def __init__(self, title, dcoscli, retryable_for_secs=0, strict=False):
    """Construct new clause.

    Args:
      title: The string title for the clause is only for reporting purposes.
      kubectl: The KubeCtlAgent to make the observation for the clause to
         verify.
      retryable_for_secs: Number of seconds that observations can be retried
         if their verification initially fails.
      strict: DEPRECATED flag indicating whether the clauses (added later)
         must be true for all objects (strict) or at least one (not strict).
         See ValueObservationVerifierBuilder for more information.
         This is deprecated because in the future this should be on a per
         constraint basis.
    """
    super(DcosClauseBuilder, self).__init__(
        title=title, retryable_for_secs=retryable_for_secs)
    self.__factory = DcosObjectFactory(dcoscli)
    self.__strict = strict

  def get_resources(self, type, extra_args=None, no_resource_ok=False):
    """Observe resources of a particular type.

    This ultimately calls a "kubectl ... get |type| |extra_args|"

    Args:
      no_resource_ok: Whether or not the resource is required.
          If the resource is not required, "not found" is treated as a valid
          check. Because resource deletion is asynchronous, there is no
          explicit API here to confirm that a resource does not exist.
    """
    self.observer = self.__factory.new_get_resources(
        type, extra_args=extra_args)

    if no_resource_ok:
      # Unfortunately gcloud does not surface the actual 404 but prints an
      # error message saying that it was not found.
      error_verifier = cli_agent.CliAgentObservationFailureVerifier(
          title='Not Found Permitted', error_regex='.* not found')
      disjunction_builder = jc.ObservationVerifierBuilder(
          'Get {0} {1} or Not Found'.format(type, extra_args))
      disjunction_builder.append_verifier(error_verifier)

      get_builder = jc.ValueObservationVerifierBuilder(
          'Get {0} {1}'.format(type, extra_args), strict=self.__strict)
      disjunction_builder.append_verifier_builder(
          get_builder, new_term=True)
      self.verifier_builder.append_verifier_builder(
          disjunction_builder, new_term=True)
    else:
      get_builder = jc.ValueObservationVerifierBuilder(
          'Get {0} {1}'.format(type, extra_args), strict=self.__strict)
      self.verifier_builder.append_verifier_builder(get_builder)

    return get_builder


class DcosContractBuilder(jc.ContractBuilder):
  """Specialized contract that facilitates observing Kubernetes."""

  def __init__(self, dcoscli):
    """Constructs a new contract.

    Args:
      kubectl: The KubeCtlAgent to use for communicating with Kubernetes.
    """
    super(DcosContractBuilder, self).__init__(
        lambda title, retryable_for_secs=0, strict=False:
        DcosClauseBuilder(
            title, dcoscli=dcoscli,
            retryable_for_secs=retryable_for_secs, strict=strict))