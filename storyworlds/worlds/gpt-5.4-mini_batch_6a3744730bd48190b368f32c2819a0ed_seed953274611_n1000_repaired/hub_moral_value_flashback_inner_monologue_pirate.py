#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hub_moral_value_flashback_inner_monologue_pirate.py
===================================================================================

A standalone storyworld for a tiny pirate tale about a harbor hub, a moral
choice, a flashback, and an inner monologue.

Premise:
A small crew docks at a busy harbor hub with a tempting shortcut: sell a found
pearl before telling the harbor keeper. The captain remembers a past mistake,
thinks through the choice, and decides to do the honest thing. That choice brings
help, trust, and a brighter ending image.

This script follows the Storyweavers contract:
- stdlib-only story engine
- typed entities with physical meters and emotional memes
- state-driven prose
- three QA sets from world state
- Python reasonableness gate + inline ASP twin
- CLI support for default, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

HUB_THRESHOLD = 1.0
MORAL_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "mate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Harbor:
    id: str
    label: str
    bustle: str
    reward: str
    truth: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    value: str
    story: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Choice:
    id: str
    honesty: int
    risk: int
    text: str
    payoff: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_doubt(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["doubt"] < HUB_THRESHOLD:
            continue
        sig = ("doubt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__inner__")
    return out


def _r_honesty(world: World) -> list[str]:
    out: list[str] = []
    if "crew" not in world.entities or "keeper" not in world.entities:
        return out
    crew = world.get("crew")
    keeper = world.get("keeper")
    if crew.memes["honesty"] < HUB_THRESHOLD:
        return out
    sig = ("honesty", crew.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.memes["trust"] += 1
    keeper.meters["help"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [Rule("doubt", "social", _r_doubt), Rule("honesty", "social", _r_honesty)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def honest_choices() -> list[Choice]:
    return [c for c in CHOICES.values() if c.honesty >= MORAL_MIN]


def best_choice() -> Choice:
    return max(CHOICES.values(), key=lambda c: c.honesty)


def can_keep_silent(choice: Choice) -> bool:
    return choice.honesty < MORAL_MIN


def resolve_choice(choice: Choice, value: Treasure) -> bool:
    return choice.honesty >= MORAL_MIN and choice.risk <= value.risk


def flashback_trigger(world: World, captain: Entity, choice: Choice) -> None:
    captain.memes["doubt"] += 1
    captain.memes["memory"] += 1
    world.say(
        f"As the pearls glinted, {captain.id} paused. The sight pulled up a flashback: "
        f"long ago, {captain.id} had kept a found coin and lost a friend's trust."
    )


def inner_monologue(world: World, captain: Entity, choice: Choice, treasure: Treasure) -> None:
    captain.memes["thought"] += 1
    world.say(
        f"In {captain.pronoun('possessive')} own head, {captain.id} argued with {captain.pronoun('object')}self: "
        f'"If I hide this {treasure.label}, I might get a quick grin. '
        f'But the hub keeps everyone tied together, and a lie can split a crew."'
    )


def tell_on_world(world: World, keeper: Entity, captain: Entity, treasure: Treasure) -> None:
    keeper.memes["trust"] += 1
    captain.memes["honesty"] += 1
    world.say(
        f'{captain.id} carried the {treasure.label} to {keeper.label_word} and told the whole truth. '
        f"{keeper.label_word.capitalize()} listened, then nodded like a lantern in the dark."
    )


def reward(world: World, keeper: Entity, treasure: Treasure, hub: Harbor) -> None:
    keeper.meters["gift"] += 1
    world.say(
        f"{keeper.label_word.capitalize()} shared a fair reward, and the harbor hub hummed softly with busy, safe work. "
        f"{hub.reward}"
    )


def lesson(world: World, captain: Entity, crew: Entity, treasure: Treasure) -> None:
    captain.memes["pride"] += 1
    crew.memes["relief"] += 1
    world.say(
        f"{captain.id} felt taller after the choice. {crew.id} smiled too, because honest hands kept the ship welcome at every dock."
    )
    world.say(
        f"The pearl stayed bright, and so did the crew's name."
    )


def stumble(world: World, captain: Entity, crew: Entity, treasure: Treasure) -> None:
    captain.memes["greed"] += 1
    world.say(
        f"{captain.id} almost reached for the hidden {treasure.label}, but {crew.id} saw the hesitation and waited."
    )


def setup(world: World, hub: Harbor, captain: Entity, crew: Entity, treasure: Treasure) -> None:
    captain.memes["doubt"] += 1
    crew.memes["hope"] += 1
    world.say(
        f"At {hub.label}, the ships bumped gently against the docks and gulls circled above the market carts."
    )
    world.say(
        f"{captain.id} and {crew.id} had brought in a small net with a shining {treasure.label} inside."
    )


def tell_story(hub: Harbor, treasure: Treasure, choice: Choice,
               captain_name: str = "Ria", captain_type: str = "captain",
               crew_name: str = "Milo", crew_type: str = "sailor") -> World:
    world = World()
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type, role="captain"))
    crew = world.add(Entity(id=crew_name, kind="character", type=crew_type, role="crew"))
    keeper = world.add(Entity(id="HarborKeeper", kind="character", type="keeper", label="the harbor keeper"))
    world.add(Entity(id="hub", type="place", label=hub.label))

    setup(world, hub, captain, crew, treasure)
    world.para()
    flashback_trigger(world, captain, choice)
    inner_monologue(world, captain, choice, treasure)
    stumble(world, captain, crew, treasure)

    if resolve_choice(choice, treasure):
        world.para()
        tell_on_world(world, keeper, captain, treasure)
        reward(world, keeper, treasure, hub)
        lesson(world, captain, crew, treasure)
        outcome = "honest"
    else:
        world.para()
        world.say(
            f"{captain.id} kept quiet instead, but the choice sat heavy like wet rope in a storm."
        )
        world.say(
            f"By sunset the crew had no welcome at the hub, and the pearly shine felt smaller than a clear conscience."
        )
        outcome = "dishonest"

    world.facts.update(
        captain=captain,
        crew=crew,
        keeper=keeper,
        hub=hub,
        treasure=treasure,
        choice=choice,
        outcome=outcome,
    )
    return world


HUBS = {
    "harbor": Harbor(
        id="harbor",
        label="the harbor hub",
        bustle="The harbor hub was full of ropes, crates, and red sails.",
        reward="The docks smelled of salt and tar, and every honest boat had a place to rest.",
        truth="At the harbor hub, a fair report matters more than a quick secret.",
        tags={"hub", "harbor"},
    ),
    "market": Harbor(
        id="market",
        label="the market hub",
        bustle="The market hub was full of baskets, fish, and cheerful calls.",
        reward="The stall bells chimed, and trade flowed best when everyone told the truth.",
        truth="At the market hub, trust keeps the tables busy.",
        tags={"hub", "market"},
    ),
}

TREASURES = {
    "pearl": Treasure(
        id="pearl",
        label="pearl",
        phrase="a small pearl",
        value="bright and rare",
        story="It sparkled like a tiny moon caught in a net.",
        tags={"pearl"},
    ),
    "compass": Treasure(
        id="compass",
        label="compass",
        phrase="an old brass compass",
        value="useful and precious",
        story="It pointed home even when the fog rolled in.",
        tags={"compass"},
    ),
}

CHOICES = {
    "honest": Choice(
        id="honest",
        honesty=3,
        risk=1,
        text="tell the harbor keeper",
        payoff="The crew stayed welcome, and the harbor keeper smiled.",
        lesson="Honesty keeps a crew together.",
        tags={"honest", "truth"},
    ),
    "hide": Choice(
        id="hide",
        honesty=1,
        risk=2,
        text="hide the find and say nothing",
        payoff="The secret felt heavy and lonely.",
        lesson="A hidden lie makes a small pocket of trouble.",
        tags={"hide", "lie"},
    ),
}

@dataclass
class StoryParams:
    hub: str
    treasure: str
    choice: str
    captain_name: str
    captain_type: str
    crew_name: str
    crew_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(
        hub="harbor",
        treasure="pearl",
        choice="honest",
        captain_name="Ria",
        captain_type="captain",
        crew_name="Milo",
        crew_type="sailor",
        seed=None,
    ),
    StoryParams(
        hub="market",
        treasure="compass",
        choice="honest",
        captain_name="Nia",
        captain_type="captain",
        crew_name="Oren",
        crew_type="sailor",
        seed=None,
    ),
    StoryParams(
        hub="harbor",
        treasure="pearl",
        choice="hide",
        captain_name="Tess",
        captain_type="captain",
        crew_name="Jory",
        crew_type="sailor",
        seed=None,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hub in HUBS:
        for treasure in TREASURES:
            for choice in CHOICES:
                combos.append((hub, treasure, choice))
    return combos


KNOWLEDGE = {
    "hub": [("What is a hub?", "A hub is a busy place where people meet, trade, or change boats. It helps things connect.")],
    "harbor": [("What is a harbor?", "A harbor is a safe place where ships can stop near land.")],
    "pearl": [("What is a pearl?", "A pearl is a smooth, shiny gem that can form inside a shell.")],
    "compass": [("What does a compass do?", "A compass helps sailors know which way is north.")],
    "honesty": [("Why is honesty important?", "Honesty helps people trust each other. Trust makes a crew work well together.")],
    "lie": [("Why can lying cause trouble?", "A lie can hide the truth and make other people unsure what is safe or fair.")],
}
KNOWLEDGE_ORDER = ["hub", "harbor", "pearl", "compass", "honesty", "lie"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hub = f["hub"]
    treasure = f["treasure"]
    choice = f["choice"]
    return [
        f'Write a pirate tale for a young child that includes the word "hub" and a moral choice about a {treasure.label}.',
        f"Tell a story set at {hub.label} where {f['captain'].id} has a flashback and an inner monologue before choosing whether to {choice.text}.",
        f"Write a child-friendly pirate story where the crew learns a moral value at the harbor hub.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    crew = f["crew"]
    keeper = f["keeper"]
    treasure = f["treasure"]
    hub = f["hub"]
    choice = f["choice"]
    out = [
        ("Where does the story take place?", f"It takes place at {hub.label}. {hub.truth}"),
        ("What did the crew find?", f"They found {treasure.phrase} in their net. {treasure.story}"),
        ("What choice did the captain think about?", f"{captain.id} thought about whether to {choice.text}. That was the moral choice in the story."),
        ("What helped the captain decide?", f"A flashback reminded {captain.id} of an old mistake, and the inner monologue helped {captain.id} think clearly."),
    ]
    if f["outcome"] == "honest":
        out.append((
            "How did the story end?",
            f"{captain.id} told the truth to {keeper.label_word}, and the harbor stayed friendly. The honest choice brought a fair reward and a calm ending image."
        ))
        out.append((
            "Why was the ending good?",
            f"The captain chose honesty, so the crew kept trust at the hub. That mattered because a pirate crew needs trust more than a secret treasure."
        ))
    else:
        out.append((
            "How did the story end?",
            f"{captain.id} stayed quiet, and the secret felt heavy. The crew lost the easy welcome that comes with honesty."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["hub"].tags) | set(world.facts["treasure"].tags) | set(world.facts["choice"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
honesty_choice(C) :- choice(C), honesty(C, H), moral_min(M), H >= M.
trust_built :- honesty_choice(C).
outcome(honest) :- honesty_choice(C).
outcome(dishonest) :- choice(C), not honesty_choice(C).
valid(H, T, C) :- harbor(H), treasure(T), choice(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HUBS:
        lines.append(asp.fact("harbor", hid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("honesty", cid, c.honesty))
    lines.append(asp.fact("moral_min", MORAL_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("choice", params.choice) + "\n"
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    sample = resolve_params(argparse.Namespace(hub=None, treasure=None, choice=None, captain_name=None, captain_type=None, crew_name=None, crew_type=None), random.Random(7))
    if asp_outcome(sample) != outcome_of(sample):
        rc = 1
        print("MISMATCH in outcome.")
    try:
        sample2 = generate(sample)
        assert sample2.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def outcome_of(params: StoryParams) -> str:
    return "honest" if CHOICES[params.choice].honesty >= MORAL_MIN else "dishonest"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate hub storyworld with a moral choice, flashback, and inner monologue.")
    ap.add_argument("--hub", choices=HUBS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--captain-name")
    ap.add_argument("--crew-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.choice and CHOICES[args.choice].honesty < MORAL_MIN:
        raise StoryError("The storyworld refuses a choice that is too dishonest for a moral tale.")
    combos = [c for c in valid_combos()
              if args.hub in (None, c[0])
              and args.treasure in (None, c[1])
              and args.choice in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hub, treasure, choice = rng.choice(sorted(combos))
    return StoryParams(
        hub=hub,
        treasure=treasure,
        choice=choice,
        captain_name=args.captain_name or rng.choice(["Ria", "Tess", "Nia", "Luz"]),
        captain_type="captain",
        crew_name=args.crew_name or rng.choice(["Milo", "Jory", "Oren", "Paz"]),
        crew_type="sailor",
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hub not in HUBS or params.treasure not in TREASURES or params.choice not in CHOICES:
        raise StoryError("Invalid StoryParams supplied.")
    world = tell_story(HUBS[params.hub], TREASURES[params.treasure], CHOICES[params.choice],
                       captain_name=params.captain_name, captain_type=params.captain_type,
                       crew_name=params.crew_name, crew_type=params.crew_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show honesty_choice/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
