"""Words become explicit dictionaries, without vector embeddings or a tagger."""

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import re


DATA_DIR = Path(__file__).parent / "data" / "nltk_data"
TOKEN_PATTERN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*|\d+(?:\.\d+)?|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Keep punctuation as tokens and contractions intact; preserve surface case."""
    return TOKEN_PATTERN.findall(text)


def token_key(token: str) -> str:
    return token.casefold().replace("’", "'")


class WordNetLexicon:
    """First WordNet sense is the default, with ambiguity retained explicitly.

    `pos` is a lexical candidate, not a contextual POS prediction. Function
    words and unknown words remain unclassified instead of inventing features.
    No corpus is downloaded implicitly during inference.
    """

    def __init__(self, data_dir: str | Path | None = None):
        try:
            import nltk
            from nltk.corpus import wordnet
        except ImportError as error:
            raise RuntimeError("Install storyformers/requirements.txt to use WordNet latents.") from error
        directory = str(data_dir or DATA_DIR)
        if directory not in nltk.data.path:
            nltk.data.path.insert(0, directory)
        try:
            wordnet.ensure_loaded()
        except LookupError as error:
            raise RuntimeError(
                "WordNet data is missing. Run: .venv/bin/python -m nltk.downloader "
                "-d storyformers/data/nltk_data wordnet"
            ) from error
        self.wordnet = wordnet

    @lru_cache(maxsize=32768)
    def _lookup(self, token: str) -> dict:
        senses = self.wordnet.synsets(token)
        if not senses:
            return {"pos": None, "pos_candidates": [], "lemma": token,
                    "synsets": [], "lexname": None, "hypernyms": [], "lexicon": "unknown"}
        first = senses[0]
        pos = first.pos()
        return {
            "pos": pos,
            "pos_candidates": list(dict.fromkeys(s.pos() for s in senses)),
            "lemma": self.wordnet.morphy(token, pos) or token,
            "synsets": [s.name() for s in senses],
            "lexname": first.lexname(),
            "hypernyms": sorted(s.name() for s in first.hypernyms()),
            "lexicon": "wordnet",
        }

    def lookup(self, token: str) -> dict:
        # Callers can extend their residual dictionary without mutating the cache.
        return deepcopy(self._lookup(token_key(token)))


def encode(tokens: list[str], lexicon: WordNetLexicon, *, offset: int = 0) -> list[dict]:
    """One independent latent dictionary per token occurrence."""
    return [dict(lexicon.lookup(token), token=token_key(token), surface=token,
                 position=offset + i) for i, token in enumerate(tokens)]
