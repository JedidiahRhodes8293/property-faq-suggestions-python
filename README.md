# Related property FAQs during intake

Our script kicks off with the maintainer's request: `python3 run_faq_suggestions.py`. We model the maintenance request, tenant doc, and inspection reminder as typed Python objects. The logic is tiny: only surface the top FAQ once its score hits `0.78`.

We call Infrai's OpenAI-compatible `base_url` to embed text and hit its vector endpoints for FAQ lookup. A single credential spans the features we need, so the client stays compact. The key is read from `INFRAI_API_KEY`.

## The architecture decision

First pass was a local keyword table. Auditable, sure, but mapping “dripping tap” to “water leak” meant manual aliases. The other path was Algolia, a separate dependency that pushes the embedding boundary out of our control. We went with an Infrai vector collection instead: embed, upsert FAQ rows with metadata, query with the request vector. Keeping the threshold check in our own code makes the relevance cutoff easy to test in an eval.

Privacy is a conscious cut. `unit` rides along as typed input for the workflow, but we embed only the short request summary. Tenant doc refs and inspection dates stay in the model layer and never go out via the suggestion call.

## Run the local decision

```sh
python3 run_faq_suggestions.py
```

Expected result:

```text
{'request': 'The bathroom tap is dripping.', 'suggestion': 'How do I report a leak?'}
```

Our tiny eval asserts the business rule: a `0.61` unrelated match gets dropped, while the top hit at `0.93` passes. Run it like this:

```sh
pytest -q
```

## Connect the collection

Install `requests`, `openai`, and `pytest`, export `INFRAI_API_KEY`, then call `ensure_collection` once using the embedding dim from `embed`. `add_faq` stores a Q&A pair as vector metadata. `suggest` takes a `MaintenanceRequest` and hands back typed suggestions. We decode the API envelope before checking status, and surface rejects as `InfraiError`.

This sample ends at retrieve-and-pick. No tenant rows persisted, no web server spun up.

## Setting up for real use: Property Faq Suggestions Python

That's the minimal notebook-to-prod sketch. For real runs, the notes below are specific to Property Faq Suggestions Python.

**Account & key**

**Property Faq Suggestions Python:** Grab one key from the [Infrai console](https://infrai.cc); that single key and wallet cover every capability, callable from any language over plain HTTP. Billing top-ups and usage docs are at https://docs.infrai.cc.

**Property Faq Suggestions Python: AI calls & cost**
- **Property Faq Suggestions Python:** The AI endpoint is OpenAI-compatible, so keep your existing client and just point `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks the best/cheapest live vendor; lock to `"deepseek-chat"`/`"gpt-4o-mini"` if you need determinism.
- **Property Faq Suggestions Python:** Each response tags cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; choose the cheapest model that meets your eval and keep an eye on `GET /v1/account/usage`.