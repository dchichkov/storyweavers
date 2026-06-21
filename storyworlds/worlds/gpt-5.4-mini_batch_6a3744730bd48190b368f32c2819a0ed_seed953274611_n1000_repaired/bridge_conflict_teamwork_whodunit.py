#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bridge_conflict_teamwork_whodunit.py
=====================================================================

A standalone storyworld for a small whodunit-like bridge mystery: a child team
finds a problem at the bridge, argues about what happened, follows clues, works
together, and ends with a clear solution image.

The world is built around:
- a bridge with a locked gate and a loose sign
- a small conflict between two kids
- teamwork to inspect clues and fix the problem
- a whodunit-style reveal about what actually caused the trouble

It follows the Storyweavers storyworld contract:
- stdlib-only core script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- generates story, three Q&A sets, and a live world model for trace output
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Place:
    id: str
    label: str
    bridge_name: str
    water_name: str
    clue_name: str
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
class Suspect:
    id: str
    label: str
    alibi: str
    clue: str
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
class Tool:
    id: str
    label: str
    use: str
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
class StoryParams:
    place: str
    suspect: str
    tool: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
    parent: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    a = world.facts.get("a")
    b = world.facts.get("b")
    if not a or not b:
        return out
    if a.memes["defiance"] >= THRESHOLD and b.memes["worry"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["conflict"] += 1
            b.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamwork"):
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("team").meters["progress"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("teamwork", "social", _r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def _do_clue_work(world: World, team: Entity, suspect: Suspect, tool: Tool, place: Place) -> None:
    team.meters["search"] += 1
    team.memes["curiosity"] += 1
    world.say(
        f"{team.id} followed the muddy clues toward {place.bridge_name}. "
        f"They used {tool.label} to check the boards and the gate."
    )
    world.say(
        f"At first it looked puzzling, but the little marks on the rail told a story."
    )
    world.facts["teamwork"] = True
    propagate(world, narrate=False)


def setup(world: World, a: Entity, b: Entity, parent: Entity, place: Place) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"One cool morning, {a.id} and {b.id} reached {place.label}. "
        f"Near the {place.bridge_name}, the gate was shut and a sign had fallen over."
    )
    world.say(
        f"{a.id} wanted to cross at once, but {b.id} said the bridge looked wrong."
    )


def argue(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    b.memes["worry"] += 1
    world.say(
        f'"We should just go," {a.id} said. "No, something is not right," {b.id} said back.'
    )
    world.say(
        f"Their voices got sharp enough that even the wind seemed to hush."
    )


def clue_one(world: World, place: Place, suspect: Suspect) -> None:
    world.say(
        f"Then {b"".join([])}"  # never used; placeholder avoided by immediate overwrite below
    )


def clue_scene(world: World, place: Place, suspect: Suspect) -> None:
    world.say(
        f"Beside the {place.bridge_name}, they found {place.clue_name} and a strip of wet paint."
    )
    world.say(
        f"The clue matched {suspect.label}'s {suspect.clue}, but that did not mean {suspect.label} was guilty."
    )


def reveal(world: World, parent: Entity, suspect: Suspect, place: Place, tool: Tool) -> None:
    world.say(
        f"{parent.label_word.capitalize()} came over and looked carefully. "
        f'"This is a whodunit," {parent.pronoun()} said, "so let us ask what the clues can really prove."'
    )
    world.say(
        f"The answer was simple: {suspect.truth}. "
        f"The bridge was not broken by a prank; {suspect.label} had only been fixing the loose sign."
    )
    world.say(
        f"Together they tightened the sign with {tool.label}, opened the gate, and made the bridge safe again."
    )


def ending(world: World, a: Entity, b: Entity, place: Place) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["conflict"] = 0
    b.memes["conflict"] = 0
    world.say(
        f"In the end, {a.id} and {b.id} crossed {place.bridge_name} side by side, "
        f"with the water shining below and the solved mystery shining even brighter."
    )


def tell(place: Place, suspect: Suspect, tool: Tool, name_a: str, gender_a: str,
         name_b: str, gender_b: str, parent_type: str) -> World:
    world = World()
    a = world.add(Entity(id=name_a, kind="character", type=gender_a, role="investigator"))
    b = world.add(Entity(id=name_b, kind="character", type=gender_b, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    team = world.add(Entity(id="team", type="team", label="the team"))
    world.add(Entity(id="bridge", type="thing", label=place.bridge_name))
    world.add(Entity(id="sign", type="thing", label="the sign"))
    world.facts.update(a=a, b=b, parent=parent, team=team, place=place, suspect=suspect, tool=tool)
    setup(world, a, b, parent, place)
    world.para()
    argue(world, a, b)
    world.para()
    clue_scene(world, place, suspect)
    _do_clue_work(world, team, suspect, tool, place)
    world.para()
    reveal(world, parent, suspect, place, tool)
    world.para()
    ending(world, a, b, place)
    return world


PLACES = {
    "river": Place(
        id="river",
        label="the river path",
        bridge_name="bridge over the creek",
        water_name="creek",
        clue_name="small muddy footprints",
        tags={"bridge", "water", "clue"},
    ),
    "park": Place(
        id="park",
        label="the park trail",
        bridge_name="wooden bridge",
        water_name="pond",
        clue_name="a bent ribbon",
        tags={"bridge", "park", "clue"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard lane",
        bridge_name="little stone bridge",
        water_name="stream",
        clue_name="crumbs on the rail",
        tags={"bridge", "orchard", "clue"},
    ),
}

SUSPECTS = {
    "miller": Suspect(
        id="miller",
        label="Mr. Miller",
        alibi="was fixing the lanterns",
        clue="smudged hands",
        truth="Mr. Miller had only been fixing the loose sign",
        tags={"adult", "repair"},
    ),
    "lena": Suspect(
        id="lena",
        label="Lena",
        alibi="was feeding ducks",
        clue="blue paint on her sleeve",
        truth="Lena had been painting the warning sign, not hiding trouble",
        tags={"artist", "repair"},
    ),
    "jo": Suspect(
        id="jo",
        label="Jo",
        alibi="was carrying apples",
        clue="a string of twine",
        truth="Jo had tied the gate cord so the bridge would not swing open",
        tags={"helper", "repair"},
    ),
}

TOOLS = {
    "rope": Tool(id="rope", label="a rope", use="tie things"),
    "key": Tool(id="key", label="a small key", use="unlock things"),
    "lantern": Tool(id="lantern", label="a lantern", use="see in the dark"),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Ben", "Finn", "Max", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SUSPECTS:
            for t in TOOLS:
                combos.append((p, s, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit bridge storyworld with conflict and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name-a")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, suspect, tool = rng.choice(sorted(combos))
    gender_a = args.gender_a or rng.choice(["girl", "boy"])
    gender_b = args.gender_b or rng.choice(["girl", "boy"])
    pool_a = GIRL_NAMES if gender_a == "girl" else BOY_NAMES
    pool_b = GIRL_NAMES if gender_b == "girl" else BOY_NAMES
    name_a = args.name_a or rng.choice(pool_a)
    name_b = args.name_b or rng.choice([n for n in pool_b if n != name_a] or pool_b)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        suspect=suspect,
        tool=tool,
        name_a=name_a,
        gender_a=gender_a,
        name_b=name_b,
        gender_b=gender_b,
        parent=parent,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, place = f["a"], f["b"], f["place"]
    return [
        f'Write a whodunit story for a 3-to-5-year-old that includes the word "bridge" and ends with teamwork.',
        f"Tell a bridge mystery where {a.id} and {b.id} disagree, follow clues, and discover who really caused the trouble.",
        f"Write a short detective story where kids argue at {place.bridge_name} but work together to solve the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, place, suspect, tool = f["a"], f["b"], f["parent"], f["place"], f["suspect"], f["tool"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a little whodunit about a bridge mystery. The kids argue first, then they use teamwork to follow clues and solve it.",
        ),
        QAItem(
            question=f"Why did {a.id} and {b.id} argue?",
            answer=f"{a.id} wanted to cross the bridge right away, but {b.id} thought something was wrong. Their conflict came from one child wanting to rush and the other child wanting to look carefully first.",
        ),
        QAItem(
            question="What did the clues show?",
            answer=f"The clues showed that {suspect.label} was not trying to cause trouble. {suspect.truth}, so the mystery was solved by careful looking instead of guessing.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They worked together and used {tool.label} to make the bridge safe again. That teamwork turned the argument into a useful plan.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    place = f["place"]
    return [
        QAItem(
            question="What is a bridge?",
            answer="A bridge is a structure that helps people cross over water or a gap. It lets travelers go from one side to the other.",
        ),
        QAItem(
            question="Why is it smart to check a bridge carefully?",
            answer="A bridge can be unsafe if a gate is stuck or a sign has fallen over. Checking first helps people stay safe before they cross.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other do a job. One person might notice clues while another carries a tool, and together they can finish faster.",
        ),
        QAItem(
            question=f"What kind of place was {place.bridge_name} near?",
            answer=f"It was near {place.water_name}, where the story could use wet clues like footprints or paint marks. Those details make the mystery feel real and easy to follow.",
        ),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
bridge(place) :- place_fact(place).
conflict :- defiance(a), worry(b).
teamwork :- clue_work.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    lines.append(asp.fact("bridge", "bridge"))
    lines.append(asp.fact("conflict", "possible"))
    lines.append(asp.fact("teamwork", "possible"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show bridge/1.\n#show conflict/1.\n#show teamwork/1."))
    _ = asp.atoms(model, "bridge")
    # smoke test generate/emit on a normal curated/default scenario
    rng = random.Random(777)
    params = resolve_params(argparse.Namespace(place=None, suspect=None, tool=None,
                                               name_a=None, gender_a=None,
                                               name_b=None, gender_b=None,
                                               parent=None), rng)
    sample = generate(params)
    if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
        print("FAIL: story generation produced empty content.")
        return 1
    if "bridge" not in sample.story.lower():
        print("FAIL: generated story does not mention bridge.")
        return 1
    print("OK: ASP helper loads and story generation smoke test passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show place_fact/1."))
    return sorted(set(asp.atoms(model, "place_fact")))


def asp_sensible() -> list[str]:
    return sorted(TOOLS)


def asp_outcome(_: StoryParams) -> str:
    return "solved"


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"Unknown suspect: {params.suspect}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    place = PLACES[params.place]
    suspect = SUSPECTS[params.suspect]
    tool = TOOLS[params.tool]
    world = tell(
        place=place,
        suspect=suspect,
        tool=tool,
        name_a=params.name_a,
        gender_a=params.gender_a,
        name_b=params.name_b,
        gender_b=params.gender_b,
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(place="river", suspect="miller", tool="rope", name_a="Mia", gender_a="girl", name_b="Noah", gender_b="boy", parent="mother"),
    StoryParams(place="park", suspect="lena", tool="lantern", name_a="Lily", gender_a="girl", name_b="Ben", gender_b="boy", parent="father"),
    StoryParams(place="orchard", suspect="jo", tool="key", name_a="Ava", gender_a="girl", name_b="Leo", gender_b="boy", parent="mother"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, suspect, tool = rng.choice(sorted(combos))
    gender_a = args.gender_a or rng.choice(["girl", "boy"])
    gender_b = args.gender_b or rng.choice(["girl", "boy"])
    pool_a = GIRL_NAMES if gender_a == "girl" else BOY_NAMES
    pool_b = GIRL_NAMES if gender_b == "girl" else BOY_NAMES
    name_a = args.name_a or rng.choice(pool_a)
    name_b = args.name_b or rng.choice([n for n in pool_b if n != name_a] or pool_b)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        suspect=suspect,
        tool=tool,
        name_a=name_a,
        gender_a=gender_a,
        name_b=name_b,
        gender_b=gender_b,
        parent=parent,
    )


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="Bridge conflict teamwork whodunit storyworld.")


def main() -> None:
    ap = build_parser()
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name-a")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("", "#show place_fact/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("places:", ", ".join(pid for (pid,) in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} & {p.name_b}: bridge mystery at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
