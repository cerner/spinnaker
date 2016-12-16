# Standard python modules.
import logging

# Our modules.
from citest.service_testing import cli_agent
from citest.base.json_scrubber import JsonScrubber

class DcosCliAgent(cli_agent.CliAgent):
  """Agent that uses the DC/OS CLI (dcos) program to interact with DC/OS."""

  def __init__(self, trace=True):
    """Construct instance.

    Args:
      trace: Whether to trace all the calls by default for debugging.
    """
    super(DcosCliAgent, self).__init__(
        'dcos', output_scrubber=JsonScrubber())
    self.trace = trace
    self.logger = logging.getLogger(__name__)

  @staticmethod
  def build_dcoscli_command_args(subcommand, resource=None, action=None, args=None):
    """Build commandline for an action.
 
    Args:
      subcommand: The dcos subcommand to execute
      resource: The dcos resource we are going to operate on (if applicable).
      action: The action to take on the resource (if applicable).
      args: The arguments following [gcloud_module, gce_type].
 
    Returns:
      list of complete command line arguments following implied 'dcos'
    """
    return [subcommand] + ([resource] if resource else []) + ([action] if action else []) + (args if args else [])