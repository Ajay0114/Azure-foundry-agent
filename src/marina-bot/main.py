import os

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import HostedResponseRequest, ResponsesHostServer, WorkflowTurn
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

try:
    from agent_framework_foundry_hosting import CheckpointStoreProvider
except ImportError:  # not re-exported in this release
    from agent_framework_foundry_hosting._state_store import CheckpointStoreProvider

from models import TurnInput
from orchestrator import build_orchestrator
from shared.agent_node import FoundryAgentRunner
from shared.deps import Deps
from shared.llm_dates import FoundryDateReader
from shared.llm_products import FoundryProductReader
from shared.osw import OswClient
from shared.state_store import FileStateStore

load_dotenv()

# "module:qualname" of every application type that travels through the workflow as a message.
ALLOWED_CHECKPOINT_TYPES = ["models:TurnInput", "models:Turn"]


def make_prompt_runner(client):
    """Prompt nodes: a stateless one-shot LLM call (history is injected into the prompt text)."""
    agent = Agent(client=client, name="prompt_node")

    async def run_prompt(prompt: str) -> str:
        response = await agent.run(prompt, stream=False)
        return response.text or ""

    return run_prompt


async def parse_response(request: HostedResponseRequest) -> WorkflowTurn[TurnInput]:
    """Map one Responses request to one workflow turn.

    Dialog state is looked up by conversation id, or by the previous response id when the caller
    chains with previous_response_id, and saved under this conversation / response id.
    """
    text = await request.get_input_text() or ""
    previous = request.request.get("previous_response_id")
    load_keys = [k for k in (request.conversation_id, previous) if k]
    save_keys = [k for k in (request.conversation_id, request.response_id) if k]
    return WorkflowTurn(input=TurnInput(text=text, load_keys=load_keys, save_keys=save_keys))


def main():
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )
    deps = Deps(
        run_prompt=make_prompt_runner(client),
        run_agent=FoundryAgentRunner(client),
        osw=OswClient.from_env(),
        read_dates=FoundryDateReader(client),      # model fallback for dates the parser cannot read
        read_products=FoundryProductReader(client),  # reads one reply in the product-details questions
    )
    store = FileStateStore()

    def factory(request: HostedResponseRequest):
        return build_orchestrator(deps, store)

    # The host checkpoints each turn's input and messages and only restores types allowed by name.
    checkpoints = CheckpointStoreProvider(allowed_checkpoint_types=ALLOWED_CHECKPOINT_TYPES)
    ResponsesHostServer(
        workflow=factory, parse_response=parse_response, checkpoint_store_provider=checkpoints
    ).run()


if __name__ == "__main__":
    main()
