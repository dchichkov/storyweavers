#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/argue_symbol_bathing_suspense_adventure.py
============================================================================

A standalone story world for a small suspense-adventure tale built around three
seed words: argue, symbol, bathing.

Premise:
- Two children or siblings are exploring a bathhouse-like old map room / spa ruin
  / river camp.
- They find a strange symbol that seems important.
- They argue about what it means.
- A bathing-related detail becomes the clue that resolves the suspense.
- The ending should feel adventurous, concrete, and state-driven.

This world keeps the model small and classical:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate
- an ASP twin
- three Q&A sets grounded in world state
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Theme:
    id: str
    place: str
    setup: str
    quest: str
    dark: str
    adventure_title: str
    send_off: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Symbol:
    id: str
    glyph: str
    meaning: str
    risky: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class BathItem:
    id: str
    label: str
    phrase: str
    makes_scary_sound: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.get("corridor").meters["dark"] >= THRESHOLD:
        for kid in world.characters():
            if kid.role in {"finder", "speaker"}:
                kid.memes["fear"] += 1
                kid.meters["alert"] += 1
        if ("fear",) not in world.fired:
            world.fired.add(("fear",))
            out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(symbol: Symbol, item: BathItem) -> bool:
    return symbol.glyph == "wave" and item.makes_scary_sound


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def danger_level(delay: int) -> int:
    return 1 + delay


def outcome_of(params: "StoryParams") -> str:
    if params.delay >= 2:
        return "lost"
    return "safe"


def predict_tension(world: World, item_id: str) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["dark"] += 1
    propagate(sim, narrate=False)
    return {"fear": sum(e.memes["fear"] for e in sim.characters())}


def open_scene(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    world.say(
        f"At the old riverside bathhouse, {a.id} and {b.id} turned the quiet hall "
        f"into {theme.place}. {theme.setup}"
    )
    world.say(
        f"They had come looking for {theme.quest}, the sort of adventure that made "
        f"the dark corners feel bigger than they were."
    )


def find_symbol(world: World, finder: Entity, symbol: Symbol, item: BathItem, theme: Theme) -> None:
    finder.memes["curiosity"] += 1
    world.say(
        f"Behind a cracked stone basin, {finder.id} found a carved {symbol.glyph} "
        f"symbol. It looked like {symbol.meaning}, but it sat beside {item.phrase}."
    )
    world.say(
        f"The mark gave the hall a hush, and the air near {theme.dark} felt strange."
    )


def argue(world: World, a: Entity, b: Entity, symbol: Symbol, item: BathItem) -> None:
    a.memes["stubborn"] += 1
    b.memes["worry"] += 1
    world.say(
        f'"It means go this way," {a.id} said. "No, it means stay away," {b.id} '
        f'replied. They began to argue, each pointing at the {symbol.glyph} mark.'
    )
    world.say(
        f'For a moment, neither child wanted to listen, and {item.label} seemed '
        f'even creepier in the dim hall.'
    )


def whisper_warning(world: World, b: Entity, symbol: Symbol, item: BathItem) -> None:
    pred = predict_tension(world, item.id)
    b.memes["caution"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"{b.id} glanced at the {symbol.glyph} mark again. "
        f'"Wait," {b.id} whispered, "it matches the old bathing room signs. '
        f"It might show where the water used to go."
    )


def resolve_clue(world: World, a: Entity, b: Entity, item: BathItem, theme: Theme) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"Then {a.id} noticed the clue in {item.phrase}: a damp trail led toward "
        f"the open drain. The symbol was not a warning after all."
    )
    world.say(
        f'It was a map mark for the bathing channel, and the scary sound from '
        f"{item.label} was only the water drumming through the pipes."
    )
    world.say(
        f"The two children stopped arguing, followed the trail, and saw a small "
        f"stone door tucked behind the basin."
    )


def reveal_treasure(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    world.say(
        f"Inside, they found a dry little chamber with a lantern hook, an old towel "
        f"bench, and a silver key tied to a rope."
    )
    world.say(
        f"{a.id} grinned, {b.id} laughed, and together they stepped into the room "
        f"like real explorers at the end of a long trail."
    )
    world.say(
        f"They left the bathhouse with the key, the symbol's secret, and a brave "
        f"new story to tell."
    )


def lose_way(world: World, a: Entity, b: Entity, item: BathItem) -> None:
    a.memes["fear"] += 1
    b.memes["fear"] += 1
    world.say(
        f"But the hall grew darker, the echo from {item.label} got louder, and the "
        f"children hurried away before they could solve it."
    )
    world.say(
        f"They escaped the scary place together, still holding hands, but the clue "
        f"stayed hidden in the shadows."
    )


THEMES = {
    "bathhouse": Theme(
        "bathhouse",
        "an old bathhouse",
        "The stone floor was slick and shiny, with mosaic fish under their feet and "
        "a broken fountain sleeping in the middle.",
        "the lost bathing channel",
        "the shadowy archway",
        "A Suspense Adventure in the Bathhouse",
        "followed the wet clue",
    ),
    "river": Theme(
        "river",
        "a river camp",
        "The camp lanterns blinked beside the river, and the wooden boardwalk creaked "
        "in the night wind.",
        "the hidden bathing path",
        "the reeds beyond the campfire",
        "A Suspense Adventure by the River",
        "followed the wet clue",
    ),
    "ruins": Theme(
        "ruins",
        "some old ruins",
        "The broken arches leaned over a cold courtyard, and every step made a soft echo.",
        "the bathing spring",
        "the dark arch below the stairs",
        "A Suspense Adventure in the Ruins",
        "followed the wet clue",
    ),
}

SYMBOLS = {
    "wave": Symbol("wave", "wave", "a path for water", "a warning to turn back",
                   tags={"symbol", "bathing"}),
    "drop": Symbol("drop", "drop", "a tiny falling drop", "a sign of dripping water",
                   tags={"symbol", "bathing"}),
    "spiral": Symbol("spiral", "spiral", "a turning path", "a clue hidden in old stone",
                     tags={"symbol"}),
}

ITEMS = {
    "bowl": BathItem("bowl", "a copper bowl", "the copper bowl", makes_scary_sound=True,
                     tags={"bathing"}),
    "pipe": BathItem("pipe", "a narrow pipe", "the narrow pipe", makes_scary_sound=True,
                     tags={"bathing"}),
    "bell": BathItem("bell", "a hanging bell", "the hanging bell", makes_scary_sound=False,
                     tags={"suspense"}),
}

RESPONSES = {
    "listen": Response("listen", 3, 3,
                       "followed the clue calmly and found the hidden door",
                       "followed the clue too late and lost the trail",
                       "followed the clue and found the hidden door",
                       tags={"adventure"}),
    "light": Response("light", 2, 2,
                      "lit a lantern and saw the wet mark on the floor",
                      "lit the lantern, but the dark stayed too thick",
                      "lit a lantern and saw the wet mark",
                      tags={"adventure"}),
    "call_help": Response("call_help", 3, 4,
                          "called for a grown-up who knew the old bathhouse",
                          "called for help, but nobody came in time",
                          "called for a grown-up who knew the old bathhouse",
                          tags={"help"}),
}

GIRL_NAMES = ["Mina", "Lina", "Ava", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Leo", "Max"]
TRAITS = ["curious", "bold", "careful", "brave", "thoughtful"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    symbol: str
    item: str
    response: str
    finder: str
    finder_gender: str
    speaker: str
    speaker_gender: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for s in SYMBOLS:
            for i in ITEMS:
                if is_reasonable(SYMBOLS[s], ITEMS[i]):
                    combos.append((t, s, i))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspense-adventure story world with a symbol and bathing clue.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--symbol", choices=SYMBOLS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.symbol and args.item and not is_reasonable(SYMBOLS[args.symbol], ITEMS[args.item]):
        raise StoryError("(No story: this symbol does not fit this bathing clue.)")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.symbol is None or c[1] == args.symbol)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, symbol, item = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    finder_gender = rng.choice(["girl", "boy"])
    speaker_gender = "boy" if finder_gender == "girl" else "girl"
    finder = rng.choice(GIRL_NAMES if finder_gender == "girl" else BOY_NAMES)
    speaker_pool = GIRL_NAMES if speaker_gender == "girl" else BOY_NAMES
    speaker = rng.choice([n for n in speaker_pool if n != finder])
    return StoryParams(theme, symbol, item, response, finder, finder_gender, speaker, speaker_gender,
                       delay=rng.randint(0, 2))


def tell(theme: Theme, symbol: Symbol, item: BathItem, response: Response,
         finder: str, finder_gender: str, speaker: str, speaker_gender: str,
         delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(finder, kind="character", type=finder_gender, role="finder"))
    b = world.add(Entity(speaker, kind="character", type=speaker_gender, role="speaker"))
    corridor = world.add(Entity("corridor", type="place", label=theme.dark))
    sig = world.add(Entity("symbol", type="thing", label=symbol.glyph))
    obj = world.add(Entity("item", type="thing", label=item.label))
    world.facts["theme"] = theme
    world.facts["symbol"] = symbol
    world.facts["item"] = item
    world.facts["response"] = response
    world.facts["delay"] = delay

    open_scene(world, a, b, theme)
    world.para()
    find_symbol(world, a, symbol, item, theme)
    argue(world, a, b, symbol, item)
    whisper_warning(world, b, symbol, item)
    world.para()
    resolve_clue(world, a, b, item, theme)
    if delay >= 2:
        lose_way(world, a, b, item)
    else:
        body = response.text.replace("{target}", item.label)
        world.say(f"They {body}.")
        reveal_treasure(world, a, b, theme)
    world.facts.update(outcome="lost" if delay >= 2 else "safe", corridor=corridor, sig=sig, obj=obj)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], SYMBOLS[params.symbol], ITEMS[params.item], RESPONSES[params.response],
                 params.finder, params.finder_gender, params.speaker, params.speaker_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspense adventure story that includes the words "argue", "symbol", and "bathing".',
        f"Tell a child-friendly adventure where two children argue about a strange symbol in an old bathing place, then solve the mystery.",
        f"Write a story with a dark, exciting mood that ends with a bathing clue revealing what a symbol means.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    theme: Theme = f["theme"]
    symbol: Symbol = f["symbol"]
    item: BathItem = f["item"]
    outcome = f["outcome"]
    qa = [
        ("What were the children exploring?",
         f"They were exploring {theme.place}, which felt like the start of an adventure. The old place was quiet, so every sound seemed important."),
        ("Why did they argue?",
         f"They argued because they read the {symbol.glyph} symbol differently. One child thought it was a direction, and the other thought it was a warning."),
        ("What clue helped them understand the symbol?",
         f"The clue was {item.phrase}. The wet trail and the sound from it showed the symbol was about bathing water, not danger."),
    ]
    if outcome == "safe":
        qa.append(("How did the story end?",
                   "It ended safely with the children finding the hidden door and the secret room. They turned the scary moment into a real adventure."))
    else:
        qa.append(("How did the story end?",
                   "They left before they solved it, still safe but without the treasure. The mystery stayed in the dark hall."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["symbol"].tags) | set(f["item"].tags)
    out = []
    if "symbol" in tags:
        out.append(("What is a symbol?",
                     "A symbol is a mark that stands for an idea, a place, or a message. People use symbols to help others understand something quickly."))
    if "bathing" in tags:
        out.append(("What is bathing?",
                     "Bathing means washing your body in water so you can be clean. People bathe in tubs, showers, or special washing places."))
    if "suspense" in tags or True:
        out.append(("What is suspense?",
                     "Suspense is the feeling that something important is about to happen, so you keep wondering what comes next."))
    out.append(("Why do people use clues in adventures?",
                 "Clues help explorers figure out where to go and what something means. That makes the journey feel like a mystery to solve."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid, s in SYMBOLS.items():
        lines.append(asp.fact("symbol", sid))
        lines.append(asp.fact("glyph", sid, s.glyph))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.makes_scary_sound:
            lines.append(asp.fact("scary_sound", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S,I) :- symbol(S), item(I), glyph(S,"wave"), scary_sound(I).
valid(T,S,I) :- theme(T), reasonable(S,I).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, symbol=None, item=None, response=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation failed: {e}")
    return rc


def valid_response_ids() -> list[str]:
    return [r.id for r in sensible_responses()]


def story_knowledge_tags(world: World) -> set[str]:
    f = world.facts
    return set(f["symbol"].tags) | set(f["item"].tags)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t} {s} {i}" for t, s, i in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        params_list = [StoryParams(t, s, i, "listen", "girl", "Max", "boy")
                       for t, s, i in valid_combos()[:5]]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
