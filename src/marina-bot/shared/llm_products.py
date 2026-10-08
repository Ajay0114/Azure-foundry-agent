"""Model reader for the product questions (Kore: the ProductCount and ProductDetails agent nodes).

Kore's agent nodes let the model decide what to ask, what to store and when to stop, then patch its mistakes with a
long post-processing script (provenance flags, bleed guards, vetoes). Here the model only READS one reply and returns
typed fields through Foundry structured output. Which question comes next, which slot a value belongs to, and when
the list is complete are decided by ordinary code (`product_details.py`), so a model slip cannot corrupt the list.
"""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from agent_framework import Agent
from pydantic import BaseModel, Field, ValidationError

from shared.validators import clean_product_name

log = logging.getLogger(__name__)

CONDITIONS = ("new", "used", "damaged", "wrong product")


@dataclass
class ProductMention:
    product_name: str | None = None
    quantity: int | None = None
    condition: str | None = None
    expected_product_name: str | None = None


@dataclass
class ProductReading:
    products: list[ProductMention] = field(default_factory=list)
    expected_product_name: str | None = None       # the product they ordered instead, when that was the question
    finished: bool = False                         # "that's all" / "no more"
    applies_to_all: bool = False                   # a condition meant for every product ("they are all new")


# (customer's reply, what the bot asked, products so far as text) -> a reading, or None when the model could not help
ProductReader = Callable[[str, str, str], Awaitable[ProductReading | None]]

INSTRUCTIONS = """You read ONE reply from a customer who is listing the cruise-ship spa products they want to return.
You are given the question the bot just asked, the products captured so far, and the customer's reply.
Report ONLY what the reply itself says. Never take anything from the captured products or from the question.

products: one entry per product (or per product + condition) mentioned in the reply.
- product_name: the product noun only, without filler such as "product", "item", "unit". Null when the reply names no product.
- quantity: a whole number 1-999, null if not stated. Words count ("two" = 2, "a pair" = 2, "a" or "an" before a product = 1).
- condition: exactly one of new | used | damaged | wrong product, or null.
    new: never opened, sealed, unused, arrived late, no longer needed, changed my mind.
    used: tried, opened, tested, partly used.
    damaged: broken, defective, faulty, not working, cracked, leaked.
    wrong product: not what I ordered, wrong item, sent the wrong one.
- expected_product_name: only for a wrong product, the item they ordered instead.
- A reply that names two or more products, or the same product in two conditions ("1 new and 1 used cleanser"),
  gets one entry for each. A reply that gives only a quantity or only a condition gets a single entry with the
  other fields null: it answers about the product already under discussion.

expected_product_name (top level): set it when the bot asked what the customer ordered or expected instead; the
product named in that answer is the expected item, NOT a product being returned, so add no entry for it.
finished: true when the customer says they have nothing more to add ("that's all", "no more", "done", "nope").
applies_to_all: true when ONE condition is meant for every product ("they are all new", "all damaged").
Never invent a value. If the reply says nothing useful, return an empty products list."""


class LlmProduct(BaseModel):
    product_name: str | None = None
    quantity: int | None = Field(None, ge=1, le=999)
    condition: Literal["new", "used", "damaged", "wrong product"] | None = None
    expected_product_name: str | None = None


class LlmProductReading(BaseModel):
    products: list[LlmProduct] = Field(default_factory=list, max_length=20)
    expected_product_name: str | None = None
    finished: bool = False
    applies_to_all: bool = False


def to_reading(parsed: LlmProductReading) -> ProductReading:
    """Validate the model's answer and convert it to plain data. Anything unusable is dropped, not repaired."""
    products = []
    for item in parsed.products:
        mention = ProductMention(clean_product_name(item.product_name), item.quantity, item.condition,
                                 clean_product_name(item.expected_product_name))
        if mention.product_name or mention.quantity or mention.condition or mention.expected_product_name:
            products.append(mention)
    return ProductReading(products, clean_product_name(parsed.expected_product_name), parsed.finished,
                          parsed.applies_to_all)


class FoundryProductReader:
    """ProductReader backed by a Foundry chat client using structured output."""

    def __init__(self, client: Any):
        self._agent = Agent(client=client, name="product_reader", instructions=INSTRUCTIONS)

    async def __call__(self, reply: str, asked: str, captured: str) -> ProductReading | None:
        prompt = (f"Question the bot just asked: {asked or '(none)'}\n"
                  f"Products captured so far: {captured or '(none)'}\n"
                  f"Customer's reply:\n{reply}")
        try:
            response = await self._agent.run(prompt, stream=False, options={"response_format": LlmProductReading})
            parsed = response.value
        except (ValidationError, ValueError):
            log.warning("product reader returned something outside the schema; ignoring it")
            return None
        return to_reading(parsed) if isinstance(parsed, LlmProductReading) else None
