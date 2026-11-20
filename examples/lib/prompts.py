"""The prompt texts every recording uses, and the functions that build their messages.

Settled before the first recording: a recorded reply is only as fixed as the text it was made from, and each
recording's manifest names the sha256 of its prompt text. Nothing here is tuned on held-out items.

- P1 and P2 answer a question from sections of the docs (the assistant under test).
- The HelpSteer2 judge rubric grades a response for correctness, reference-free (calibration).
- The reference-guided judge rubric grades an assistant's answer against the written reference.

The worked example in P1 and P2 uses a made-up tool, `svc`, and the section `example-start`. No test item may use
either (checked by a test in lib/tests/).
"""
from __future__ import annotations

import hashlib
from typing import Sequence

from lib.contract import DECLINE
from lib.docs import Section

P1_SYSTEM = f"""You answer questions about sablefile, a command-line tool, using only the documentation sections given in the user message.

Rules:
1. Use only what the sections say. Do not use outside knowledge, and do not name a flag, key or command the sections do not name.
2. Cite every statement with the ID of the section it comes from, in the form [sec:ID]. Use only IDs of the sections given.
3. If the sections do not answer the question, reply with exactly this sentence and nothing else: {DECLINE}
4. Never give an answer and that sentence in the same reply.

Example.

Sections:
[sec:example-start] Start the service
Run `svc start` to start the service. The service listens on port 8080 by default.

Question: How do I start the svc service?

Reply:
Run `svc start` to start the service. [sec:example-start]"""

P2_SYSTEM = f"""You answer questions about sablefile, a command-line tool, using only the documentation sections given in the user message.

Rules:
1. Use only what the sections say. Do not use outside knowledge, and do not name a flag, key or command the sections do not name.
2. Cite every statement with the ID of the section it comes from, in the form [sec:ID]. Use only IDs of the sections given.
3. Start the reply with the sentence from the sections that your answer relies on, in quotation marks, then its citation, on a line of its own, in this form: Quote: "..." [sec:ID]
4. On the next line, give the answer, in this form: Answer: ... [sec:ID]
5. If the sections do not answer the question, reply with exactly this sentence and nothing else: {DECLINE}
6. Never give a quote and answer and that sentence in the same reply.

Example.

Sections:
[sec:example-start] Start the service
Run `svc start` to start the service. The service listens on port 8080 by default.

Question: How do I start the svc service?

Reply:
Quote: "Run `svc start` to start the service." [sec:example-start]
Answer: Run `svc start` to start the service. [sec:example-start]"""

HS2_SYSTEM = """You check the correctness of an AI assistant's response to a user's request.

Judge correctness only: whether what the response states is true, whether any calculation, result, code or reasoning in it is right, and whether it does not mislead. Do not judge length, tone, style or formatting, and do not reward confidence.

- A response that states a factual error, gets a calculation or result wrong, contains code or logic that does not work, or answers a different question from the one asked, is incorrect.
- A response that makes no false claim is not incorrect, even if it is incomplete, asks for more information, or does not finish the task. Judge the claims it makes.

Examples (made up for this rubric):

Request: What is the capital of Australia?
Response: The capital of Australia is Canberra.
VERDICT: PASS
Reason: The response names the correct city.

Request: How many sides does a hexagon have?
Response: A hexagon has five sides.
VERDICT: FAIL
Reason: A hexagon has six sides, so the response states a wrong count.

Reply in this form: on the first line, write exactly VERDICT: PASS if the response is correct, or VERDICT: FAIL if it is not. Then, on the next line, one short sentence of reason."""

HS2_TEMPLATE = "Request:\n<<<\n{request}\n>>>\n\nResponse:\n<<<\n{response}\n>>>\n"

REF_SYSTEM = f"""You check an AI assistant's answer about the sablefile tool against the written reference answer for the question.

Rules:
1. The response is correct only if it says what the reference says. It may use other words, and may add detail that does not contradict the reference.
2. A response that says something the reference does not support, or that contradicts it, is incorrect.
3. If the reference has several readings, the response must answer every reading. A partial answer is incorrect.
4. If the reference is "none", the docs do not answer the question, and the response is correct only when it is exactly this sentence: {DECLINE}
5. A response that gives an answer and also says "{DECLINE}" is incorrect.

Reply in this form: on the first line, write exactly VERDICT: PASS if the response is correct, or VERDICT: FAIL if it is not. Then, on the next line, one short sentence of reason."""

REF_TEMPLATE = (
    "Question:\n<<<\n{question}\n>>>\n\nReference answer:\n<<<\n{reference}\n>>>\n\nResponse:\n<<<\n{response}\n>>>\n"
)


def sha256_text(*parts: str) -> str:
    """The sha256 of the parts joined with a fixed separator. A recording's manifest records this for its prompt."""
    return hashlib.sha256("\n---\n".join(parts).encode("utf-8")).hexdigest()


def render_section(section: Section, show_version: bool) -> str:
    """One section as the model reads it: its ID (and version, when shown), its title, and its body."""
    header = f"[sec:{section.section_id}]" + (f" (version {section.version})" if show_version else "")
    return f"{header} {section.title}\n{section.text}"


def answer_messages(system: str, question: str, sections: Sequence[Section], show_version: bool) -> list[dict[str, str]]:
    """The chat messages that ask the assistant one question with its retrieved sections."""
    body = "\n\n".join(render_section(s, show_version) for s in sections)
    user = f"Sections:\n\n{body}\n\nQuestion: {question}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def hs2_messages(request: str, response: str) -> list[dict[str, str]]:
    """The chat messages for the HelpSteer2 correctness judge."""
    user = HS2_TEMPLATE.format(request=request, response=response)
    return [{"role": "system", "content": HS2_SYSTEM}, {"role": "user", "content": user}]


def ref_messages(question: str, reference: str | None, response: str) -> list[dict[str, str]]:
    """The chat messages for the reference-guided judge. A None reference is shown as 'none'."""
    user = REF_TEMPLATE.format(question=question, reference=reference or "none", response=response)
    return [{"role": "system", "content": REF_SYSTEM}, {"role": "user", "content": user}]


P1_SHA256 = sha256_text(P1_SYSTEM)
P2_SHA256 = sha256_text(P2_SYSTEM)
HS2_SHA256 = sha256_text(HS2_SYSTEM, HS2_TEMPLATE)
REF_SHA256 = sha256_text(REF_SYSTEM, REF_TEMPLATE)

# ---- Added for the recordings of section 8.3. Each constant is new; none above was changed. ----
# Their examples are made up, and none is an item of the HelpSteer2, GSM8K or TruthfulQA samples.

PAIR_SYSTEM = """You compare two AI assistant responses to the same request and say which one is better.

Judge which response better answers the request: first whether what it states is correct and does what was asked, then how helpful and clear it is. Do not prefer a response because it is longer, more formal or more confident.

Example (made up for this prompt).

Request: Name the planet closest to the sun.
Response A: Venus is the planet closest to the sun.
Response B: Mercury is the planet closest to the sun.
VERDICT: B
Reason: Response B names the correct planet; Response A names the wrong one.

Reply in this form: on the first line, write exactly VERDICT: A if Response A is better, or VERDICT: B if Response B is better. Then, on the next line, one short sentence of reason."""

PAIR_TEMPLATE = "Request:\n<<<\n{request}\n>>>\n\nResponse A:\n<<<\n{first}\n>>>\n\nResponse B:\n<<<\n{second}\n>>>\n"

FAITH_SYSTEM = """You check whether an answer about the sablefile tool is supported by the documentation sections it was given.

Read the answer claim by claim. A claim is supported when the sections state it, or it follows directly from what they state. A claim the sections do not state, or that contradicts them, is unsupported. The citations in brackets, such as [sec:ID], are labels, not claims: ignore them. Wording may differ from the sections; meaning must not.

Example (made up for this prompt).

Sections:
[vlt-sync] Sync the vault
Run `vlt sync` to copy the local vault to the remote. The copy keeps the newest version of each file.

Answer: Run `vlt sync` to copy the local vault to the remote. It keeps the newest version of each file. It deletes files that are not in the remote.
VERDICT: UNSUPPORTED
Reason: The sections do not say that files missing from the remote are deleted.

Reply in this form: on the first line, write exactly VERDICT: SUPPORTED if every claim is supported, or VERDICT: UNSUPPORTED if any claim is not. Then, on the next line, one short sentence of reason."""

FAITH_TEMPLATE = "Sections:\n<<<\n{sections}\n>>>\n\nAnswer:\n<<<\n{answer}\n>>>\n"

HS2B_SYSTEM = """You grade whether an AI assistant's reply to a user is right.

A reply is right when every fact it states is true, every calculation or result in it is correct, and any code or reasoning in it works. Mark it wrong when any of those fail, or when it answers a different question from the one asked. A reply that makes no false claim is right, even when it is short, asks a question back, or leaves something out. Do not grade style, length or tone.

Examples (made up for this rubric).

Request: Is 17 a prime number?
Response: No, 17 is divisible by 3 and 5.
VERDICT: FAIL
Reason: 17 has no divisors other than 1 and itself, and 17 is not divisible by 3 or 5.

Request: Convert 2 kilometres to metres.
Response: 2 kilometres is 2000 metres.
VERDICT: PASS
Reason: The conversion is correct.

Reply in this form: on the first line, write exactly VERDICT: PASS if the reply is right, or VERDICT: FAIL if it is wrong. Then, on the next line, one short sentence of reason."""

HS2B_TEMPLATE = "Request:\n<<<\n{request}\n>>>\n\nReply:\n<<<\n{response}\n>>>\n"

BENCH_GSM8K_SYSTEM = """You solve grade-school maths word problems.

Work through the problem in a few short sentences, with each step's arithmetic written out. On the last line, write exactly "Final answer: " followed by the number only, with no units and no words after it.

Example (made up for this prompt).

Problem: A pen costs 2 dollars. How much do 4 pens cost?
Each pen costs 2 dollars, so 4 pens cost 4 x 2 = 8 dollars.
Final answer: 8"""

BENCH_GSM8K_TEMPLATE = "Problem: {question}"

BENCH_TQA_SYSTEM = """You answer multiple-choice questions about facts.

Read the question and its lettered options. Reply with the letter of the one option that is correct, and nothing else.

Example (made up for this prompt).

Question: Which gas do plants take in for photosynthesis?
A. Oxygen
B. Carbon dioxide
C. Helium
D. Nitrogen

Reply: B"""

BENCH_TQA_TEMPLATE = "Question: {question}\n{options}"

PAIR_SHA256 = sha256_text(PAIR_SYSTEM, PAIR_TEMPLATE)
FAITH_SHA256 = sha256_text(FAITH_SYSTEM, FAITH_TEMPLATE)
HS2B_SHA256 = sha256_text(HS2B_SYSTEM, HS2B_TEMPLATE)
BENCH_GSM8K_SHA256 = sha256_text(BENCH_GSM8K_SYSTEM, BENCH_GSM8K_TEMPLATE)
BENCH_TQA_SHA256 = sha256_text(BENCH_TQA_SYSTEM, BENCH_TQA_TEMPLATE)


def pair_messages(request: str, first: str, second: str) -> list[dict[str, str]]:
    """The chat messages for the pairwise judge. `first` is shown as Response A, `second` as Response B."""
    user = PAIR_TEMPLATE.format(request=request, first=first, second=second)
    return [{"role": "system", "content": PAIR_SYSTEM}, {"role": "user", "content": user}]


def faith_messages(sections: Sequence[Section], answer: str) -> list[dict[str, str]]:
    """The chat messages for the faithfulness judge: the sections as the assistant read them, then the answer."""
    body = "\n\n".join(render_section(s, False) for s in sections)
    user = FAITH_TEMPLATE.format(sections=body, answer=answer)
    return [{"role": "system", "content": FAITH_SYSTEM}, {"role": "user", "content": user}]


def hs2b_messages(request: str, response: str) -> list[dict[str, str]]:
    """The chat messages for the second HelpSteer2 correctness rubric (the wording under test)."""
    user = HS2B_TEMPLATE.format(request=request, response=response)
    return [{"role": "system", "content": HS2B_SYSTEM}, {"role": "user", "content": user}]


def bench_gsm8k_messages(question: str) -> list[dict[str, str]]:
    """The chat messages for one GSM8K item."""
    return [{"role": "system", "content": BENCH_GSM8K_SYSTEM},
            {"role": "user", "content": BENCH_GSM8K_TEMPLATE.format(question=question)}]


def bench_tqa_messages(question: str, options: Sequence[str]) -> list[dict[str, str]]:
    """The chat messages for one TruthfulQA item; the options are lettered A, B, C... in the order given."""
    lettered = "\n".join(f"{chr(65 + i)}. {text}" for i, text in enumerate(options))
    user = BENCH_TQA_TEMPLATE.format(question=question, options=lettered)
    return [{"role": "system", "content": BENCH_TQA_SYSTEM}, {"role": "user", "content": user}]
