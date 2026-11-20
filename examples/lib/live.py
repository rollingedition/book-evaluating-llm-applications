"""LiveModel: the pinned Qwen3-0.6B, run on this machine's CPU through transformers.

This is the live half of the one-line swap. Examples replay the recorded replies (ReplayModel) and never import this
module, so they stay offline and reproducible. A reader who wants the model to answer replaces the replay with this
class, with the same `reply` call for the same messages. Live runs are never written into the text.

The repository and revision come from examples/models.toml, written by `re-check models --pin`. The files are read
offline from the runtime's Hugging Face cache (HF_HOME, HF_HUB_OFFLINE=1), so the load fails on a file that is not
the pinned one. Decoding is greedy, with the seed fixed and thinking switched off in the chat template.
"""
from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from lib import SEED, THREADS

MODEL_REPO = "Qwen/Qwen3-0.6B"
MODELS_TOML = Path(__file__).resolve().parent.parent / "models.toml"


def pinned_revision(repo: str, models_toml: Path = MODELS_TOML) -> str:
    """The full commit that examples/models.toml pins for one repository. Raises KeyError when it is not pinned."""
    entries = tomllib.loads(models_toml.read_text(encoding="utf-8")).get("model", [])
    for entry in entries:
        if entry["repo"] == repo:
            return str(entry["revision"])
    raise KeyError(f"{repo!r} is not pinned in examples/models.toml")


class LiveModel:
    """The pinned model, loaded offline. `reply` takes chat messages and returns the model's text, nothing else."""

    def __init__(self, max_new_tokens: int = 160) -> None:
        """Load the tokenizer and the weights from the cache at the pinned commit, in eval mode, on the CPU."""
        torch.set_num_threads(THREADS)
        torch.manual_seed(SEED)
        self.name = MODEL_REPO
        self.max_new_tokens = max_new_tokens
        revision = pinned_revision(MODEL_REPO)
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO, revision=revision)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_REPO, revision=revision, dtype=torch.float32, attn_implementation="eager"
        )
        self.model.eval()

    def reply(self, messages: Sequence[Mapping[str, str]], sample: int = 0) -> str:
        """The model's greedy reply to one chat. `sample` is accepted for the ReplayModel signature and must be 0.

        Greedy decoding gives the same text on every run, so there is no sample to draw; a second sample raises.
        """
        if sample != 0:
            raise ValueError("LiveModel decodes greedily: it has one reply per prompt, sample 0")
        text = self.tokenizer.apply_chat_template(
            list(messages), tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        inputs = self.tokenizer(text, return_tensors="pt")
        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                do_sample=False,
                temperature=None,
                top_p=None,
                top_k=None,
                max_new_tokens=self.max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        new_tokens = output[0, inputs["input_ids"].shape[1]:]
        return str(self.tokenizer.decode(new_tokens, skip_special_tokens=True)).strip()
