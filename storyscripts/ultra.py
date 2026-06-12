#!/usr/bin/env python3
"""
gen_stories_extended.py
-----------------------
Generate short, coherent stories without any LLM.

Features
--------
* Pure Python + NLTK (no external APIs)
* WordNet‑driven vocabularies (large, automatically curated)
* Grammatical inflection (plural nouns, past‑tense verbs, comparative adjectives)
* Multiple story templates (3‑5 sentences) with a simple plot state (goal, conflict, resolution)
* CLI options for:
    - number of stories (default 100)
    - sentences per story (3, 4 or 5)
    - output format (text, json, csv)
    - random seed for reproducibility
* Optional title line and pretty printing

Usage examples
--------------
    # 100 three‑sentence stories, plain text
    python gen_stories_extended.py

    # 250 five‑sentence stories, JSON output
    python gen_stories_extended.py -n 250 -s 5 -f json > stories.json

    # reproducible run with seed 42
    python gen_stories_extended.py --seed 42

Dependencies
------------
    pip install nltk

The script will automatically download the tiny NLTK data packages it needs
(punkt, averaged_perceptron_tagger, wordnet, omw-1.4).
"""

# ----------------------------------------------------------------------
# Standard‑library imports
# ----------------------------------------------------------------------
import argparse
import csv
import json
import random
import sys
import textwrap
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Tuple, Any

# ----------------------------------------------------------------------
# NLTK set‑up (download only what we need)
# ----------------------------------------------------------------------
try:
    import nltk
    from nltk.corpus import wordnet as wn
    from nltk import pos_tag, word_tokenize
    from nltk.stem import WordNetLemmatizer
except ImportError:
    sys.stderr.write("NLTK not installed. Install with: pip install nltk\n")
    sys.exit(1)

# Minimal required NLTK resources
for resource in ("punkt", "averaged_perceptron_tagger", "wordnet", "omw-1.4"):
    try:
        nltk.data.find(
            f"tokenizers/{resource}"
            if resource == "punkt"
            else f"taggers/{resource}"
            if resource == "averaged_perceptron_tagger"
            else f"corpora/{resource}"
        )
    except LookupError:
        nltk.download(resource, quiet=True)

# ----------------------------------------------------------------------
# Helper: WordNet → POS mapping
# ----------------------------------------------------------------------
_WN_POS_MAP = {
    "n": wn.NOUN,
    "v": wn.VERB,
    "a": wn.ADJ,
    "s": wn.ADJ,   # satellite adjectives are treated as adjectives
    "r": wn.ADV,
}


def _wn_pos(tag: str) -> str:
    """Map a coarse NLTK POS tag to a WordNet POS key."""
    if tag.startswith("NN"):
        return "n"
    if tag.startswith("VB"):
        return "v"
    if tag.startswith("JJ"):
        return "a"
    if tag.startswith("RB"):
        return "r"
    return "n"  # default fallback


# ----------------------------------------------------------------------
# Vocabulary extraction (cached for speed)
# ----------------------------------------------------------------------
lemmatizer = WordNetLemmatizer()


@lru_cache(maxsize=None)
def _wordnet_words(pos: str, limit: int = 5000) -> List[str]:
    """
    Return a list of lemma names for the given WordNet POS.
    `pos` must be one of 'n', 'v', 'a', 'r'.
    The list is trimmed to `limit` entries to keep memory modest.
    """
    synsets = list(wn.all_synsets(_WN_POS_MAP[pos]))
    # Shuffle once for deterministic yet varied selection when a seed is set
    random.shuffle(synsets)
    words = []
    for syn in synsets:
        for lemma in syn.lemmas():
            name = lemma.name().replace("_", " ")
            # Keep only simple alphabetic tokens (no multi‑word phrases for now)
            if name.isalpha() and len(name) > 2:
                words.append(name.lower())
        if len(words) >= limit:
            break
    # Remove duplicates while preserving order
    seen = set()
    uniq = []
    for w in words:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq


# Pull a reasonably sized pool for each POS
NOUNS = _wordnet_words("n", limit=2000)
VERBS = _wordnet_words("v", limit=2000)
ADJECTIVES = _wordnet_words("a", limit=1500)
ADVERBS = _wordnet_words("r", limit=800)

# A short list of proper names (hand‑crafted – WordNet has very few)
PROPER_NAMES = [
    "Aria", "Bran", "Celia", "Dorian", "Elara", "Finn", "Gwen",
    "Halen", "Iris", "Joren", "Kira", "Lorin", "Mira", "Nolan",
    "Ophelia", "Pax", "Quinn", "Riven", "Soren", "Talia",
    "Mara", "Jax", "Leif", "Nia", "Orin", "Selene", "Thorne",
]

# ----------------------------------------------------------------------
# Inflection helpers (very small rule‑based system – good enough for short stories)
# ----------------------------------------------------------------------
def _pluralize(noun: str) -> str:
    """Naïve English pluralisation (covers most common cases)."""
    if noun.endswith(("s", "x", "z", "ch", "sh")):
        return noun + "es"
    if noun.endswith("y") and not noun[-2] in "aeiou":
        return noun[:-1] + "ies"
    return noun + "s"


def _past_tense(verb: str) -> str:
    """Convert a base‑form verb to simple past (regular + a handful of irregulars)."""
    irregular = {
        "be": "was",
        "go": "went",
        "do": "did",
        "have": "had",
        "see": "saw",
        "take": "took",
        "make": "made",
        "find": "found",
        "think": "thought",
        "run": "ran",
        "eat": "ate",
        "write": "wrote",
        "speak": "spoke",
        "drink": "drank",
        "begin": "began",
        "sing": "sang",
        "swim": "swam",
        "fly": "flew",
        "drive": "drove",
        "ride": "rode",
        "rise": "rose",
        "fall": "fell",
        "break": "broke",
        "choose": "chose",
        "grow": "grew",
        "throw": "threw",
        "catch": "caught",
        "teach": "taught",
        "bring": "brought",
        "buy": "bought",
        "sell": "sold",
        "send": "sent",
        "build": "built",
        "feel": "felt",
        "keep": "kept",
        "sleep": "slept",
        "leave": "left",
        "meet": "met",
        "read": "read",  # same spelling
        "hit": "hit",
        "cut": "cut",
        "put": "put",
        "set": "set",
        "cost": "cost",
        "let": "let",
        "shut": "shut",
        "split": "split",
        "spread": "spread",
        "quit": "quit",
        "bet": "bet",
        "bid": "bid",
        "burst": "burst",
        "cast": "cast",
        "cut": "cut",
        "hit": "hit",
        "hurt": "hurt",
        "rid": "rid",
        "shed": "shed",
        "slit": "slit",
        "split": "split",
        "spread": "spread",
        "thrust": "thrust",
        "wet": "wet",
    }
    if verb in irregular:
        return irregular[verb]
    # Regular verbs – simple heuristic
    if verb.endswith("e"):
        return verb + "d"
    if verb.endswith("y") and not verb[-2] in "aeiou":
        return verb[:-1] + "ied"
    if len(verb) > 2 and verb[-1] in "bcdfgklmnprstvwxz" and verb[-2] in "aeiou" and verb[-3] not in "aeiou":
        # double final consonant for CVC pattern (e.g., "stop" → "stopped")
        return verb + verb[-1] + "ed"
    return verb + "ed"


def _comparative(adj: str) -> str:
    """Turn a base adjective into its comparative form (very naive)."""
    # One‑syllable short adjectives → add "er"
    # For the sake of brevity we treat everything as regular
    if adj.endswith("y"):
        return adj[:-1] + "ier"
    if adj.endswith("e"):
        return adj + "r"
    return adj + "er"


# ----------------------------------------------------------------------
# Word picker with POS awareness & optional inflection
# ----------------------------------------------------------------------
def _pick_word(pos_tag: str, *, plural: bool = False, past: bool = False,
               comparative: bool = False) -> str:
    """
    Choose a random word that matches `pos_tag` (coarse NLTK tag).
    Optional flags request inflection (plural noun, past‑tense verb, comparative adjective).
    """
    tag = pos_tag.upper()
    if tag.startswith("NN"):
        word = random.choice(NOUNS)
        if plural:
            word = _pluralize(word)
        return word
    if tag.startswith("VB"):
        word = random.choice(VERBS)
        if past:
            word = _past_tense(word)
        return word
    if tag.startswith("JJ"):
        word = random.choice(ADJECTIVES)
        if comparative:
            word = _comparative(word)
        return word
    if tag.startswith("RB"):
        return random.choice(ADVERBS)
    if tag == "IN":
        # Prepositions are a closed set – keep a tiny static list
        preps = [
            "through", "over", "under", "beyond", "across", "into",
            "beneath", "within", "along", "past", "above", "below",
            "around", "between", "among", "against", "upon", "inside"
        ]
        return random.choice(preps)
    if tag == "NNP":
        return random.choice(PROPER_NAMES)
    # Fallback – noun
    return random.choice(NOUNS)


# ----------------------------------------------------------------------
# Tiny template engine (same idea as before but a bit more flexible)
# ----------------------------------------------------------------------
import re

_PLACEHOLDER_RE = re.compile(r"\{(\w+)(?::([^}]+))?\}")  # {TAG} or {TAG:mod1,mod2}


def _render_template(tmpl: str, ctx: Dict[str, Any]) -> str:
    """
    Replace placeholders in `tmpl` using values from `ctx`.
    Placeholder syntax:
        {TAG}               → plain substitution (must exist in ctx)
        {TAG:plural}        → request plural noun
        {TAG:past}          → request past‑tense verb
        {TAG:comp}          → request comparative adjective
        {TAG:plural,past}   → combine modifiers (order matters only for our tiny set)
    If a tag is not found in ctx, a POS‑guided random word is generated.
    """
    def repl(m: re.Match) -> str:
        tag = m.group(1)
        mods = (m.group(2) or "").split(",") if m.group(2) else []
        # Resolve base value
        if tag in ctx:
            base = ctx[tag]
        else:
            # Infer a coarse POS from the tag name (convention)
            # Noun‑like tags → NN, Verb‑like → VB, etc.
            if tag.upper() in {"PROTAGONIST", "NAME", "CHARACTER"}:
                base_pos = "NNP"
            elif tag.upper() in {"GOAL", "THEME", "OBJECT", "ITEM"}:
                base_pos = "NN"
            elif tag.upper() in {"ACTION", "VERB"}:
                base_pos = "VB"
            elif tag.upper() in {"DESC", "ADJECTIVE"}:
                base_pos = "JJ"
            elif tag.upper() in {"ADVERB", "ADV"}:
                base_pos = "RB"
            elif tag.upper() in {"PREP", "PREPOSITION"}:
                base_pos = "IN"
            else:
                base_pos = "NN"
            base = _pick_word(base_pos)

        # Apply modifiers
        if "plural" in mods:
            # Only makes sense for nouns
            base = _pluralize(base)
        if "past" in mods:
            base = _past_tense(base)
        if "comp" in mods:
            base = _comparative(base)
        return base

    return _PLACEHOLDER_RE.sub(repl, tmpl)


# ----------------------------------------------------------------------
# Story‑state container (goal, conflict, resolution)
# ----------------------------------------------------------------------
class PlotState:
    """Holds the reusable elements for a single story."""
    def __init__(self):
        # Choose a protagonist name once
        self.protagonist = random.choice(PROPER_NAMES)

        # Goal / theme (noun) – the thing the hero seeks
        self.goal = _pick_word("NN")               # e.g., "crystal"
        self.goal_plural = _pluralize(self.goal)

        # Conflict (noun) – an obstacle or antagonist
        self.conflict = _pick_word("NN")           # e.g., "dragon"
        self.conflict_plural = _pluralize(self.conflict)

        # Resolution (verb phrase) – how the story ends
        self.resolution_verb = _pick_word("VB", past=True)   # e.g., "saved"
        self.resolution_adverb = random.choice(ADVERBS)

        # A couple of supporting characters (optional)
        self.sidekick = random.choice(PROPER_NAMES)
        self.mentor = random.choice(PROPER_NAMES)

        # Random adjectives for colour
        self.adj1 = _pick_word("JJ")
        self.adj2 = _pick_word("JJ")
        self.adj3 = _pick_word("JJ")

        # Random adverb for flavour
        self.adv1 = random.choice(ADVERBS)

        # Preposition (used in many slots)
        self.prep = _pick_word("IN")

    def as_dict(self) -> Dict[str, Any]:
        """Return a flat dict ready for the template engine."""
        return {
            "PROTAGONIST": self.protagonist,
            "SIDEKICK": self.sidekick,
            "MENTOR": self.mentor,
            "GOAL": self.goal,
            "GOAL_PL": self.goal_plural,
            "CONFLICT": self.conflict,
            "CONFLICT_PL": self.conflict_plural,
            "RES_VERB": self.resolution_verb,
            "RES_ADV": self.resolution_adverb,
            }
