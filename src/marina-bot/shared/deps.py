"""Everything the dialogs need from the outside world, passed in once."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from shared.agent_node import AgentRunner
from shared.attachments import AttachmentUploader
from shared.documents import DocumentApi
from shared.dates import utc_today
from shared.flow import PromptRunner
from shared.llm_dates import DateReader
from shared.llm_products import ProductReader
from shared.osw import OswApi
from shared.zendesk import ZendeskApi


@dataclass
class Deps:
    run_prompt: PromptRunner   # prompt nodes: one-shot LLM call
    run_agent: AgentRunner     # agent nodes: tool-calling LLM loop
    osw: OswApi                # OneSpaWorld vessel + itinerary APIs
    today: Callable[[], date] = utc_today        # the clock (UTC)
    read_dates: DateReader | None = None         # model fallback for dates the parser cannot read (optional)
    zendesk: ZendeskApi | None = None            # Zendesk (ticket + private note)
    attachments: AttachmentUploader | None = None    # scan and stage the customer's files
    documents: DocumentApi | None = None         # return and transaction document requests
    read_products: ProductReader | None = None   # model reader for the product questions (optional)
