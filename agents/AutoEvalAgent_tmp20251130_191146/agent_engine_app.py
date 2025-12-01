
import os
import vertexai
from vertexai.agent_engines import AdkApp

if False:
  from google.adk.agents import config_agent_utils
  try:
    # This path is for local loading.
    root_agent = config_agent_utils.from_config("C:\Capstone\CortexMetaAgent\agents\AutoEvalAgent/root_agent.yaml")
  except FileNotFoundError:
    # This path is used to support the file structure in Agent Engine.
    root_agent = config_agent_utils.from_config("./AutoEvalAgent_tmp20251130_191146/AutoEvalAgent/root_agent.yaml")
else:
  from .agent import root_agent

if False: # Whether or not to use Express Mode
  vertexai.init(api_key=os.environ.get("GOOGLE_API_KEY"))
else:
  vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION"),
  )

adk_app = AdkApp(
    agent=root_agent,
    enable_tracing=None,
)
