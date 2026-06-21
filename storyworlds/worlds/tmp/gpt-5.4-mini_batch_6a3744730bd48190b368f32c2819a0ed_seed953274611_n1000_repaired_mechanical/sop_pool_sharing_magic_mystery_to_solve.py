#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sop_pool_sharing_magic_mystery_to_solve.py
==========================================================================

A small standalone storyworld about a child superhero team, a shared poolside
helper tool called a sop, a mysterious magic splash, and a problem that can be
solved by sharing.

The premise is intentionally tiny and state-driven:
- heroes protect a neighborhood pool day,
- one hero needs a sop to soak up magic water,
- another hero wants to keep it for themselves,
- a mystery appears at the pool,
- sharing the sop and using it wisely reveals the cause,
- the ending proves what changed.

This world follows the shared storyworld contract:
- typed entities with meters and memes,
- generated prose driven by simulated state,
- story-grounded and world-knowledge QA sets,
- a Python reasonableness gate plus an inline ASP twin,
- standard CLI modes including --verify, --asp, --show-asp, --json, --qa.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    has_pool: bool = False
    has_magic_water: bool = False
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
class Hero:
    id: str
    type: str
    suit: str
    power: str
    share_style: str
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
    phrase: str
    absorb: str
    shared_use: str
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
class Mystery:
    id: str
    label: str
    clue: str
    reveal: str
    solved_with: str
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


def _r_magic_stain(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["magic_splash"] < THRESHOLD:
            continue
        sig = ("magic_stain", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "pool" in world.entities:
            world.get("pool").meters["glow"] += 1
        out.append("__magic__")
    return out


def _r_shared_tool(world: World) -> list[str]:
    out: list[str] = []
    if "sop" not in world.entities:
        return out
    sop = world.get("sop")
    if sop.memes["shared"] < THRESHOLD:
        return out
    sig = ("shared_tool", sop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "pool" in world.entities:
        world.get("pool").meters["calm"] += 1
    out.append("__shared__")
    return out


CAUSAL_RULES = [
    Rule("magic_stain", "physical", _r_magic_stain),
    Rule("shared_tool", "social", _r_shared_tool),
]


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


def hazard_at_risk(tool: Tool, mystery: Mystery) -> bool:
    return "magic" in tool.absorb and "water" in mystery.tags


def sharing_needed(hero: Hero, tool: Tool, mystery: Mystery) -> bool:
    return "share" in hero.share_style and tool.shared_use == "together"


def solveable(tool: Tool, mystery: Mystery) -> bool:
    return tool.absorb == mystery.solved_with


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for hero in HEROES:
            for tool in TOOLS:
                for mystery in MYSTERIES:
                    if place.has_pool and place.has_magic_water and hazard_at_risk(tool, mystery):
                        combos.append((place.id, hero.id, tool.id, mystery.id))
    return combos


@dataclass
class StoryParams:
    place: str
    hero1: str
    hero2: str
    tool: str
    mystery: str
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


PLACES = {
    "pool": Place(id="pool", label="the moonlit pool", has_pool=True, has_magic_water=True, tags={"pool", "water", "magic"}),
    "roofpool": Place(id="roofpool", label="the rooftop pool", has_pool=True, has_magic_water=True, tags={"pool", "superhero"}),
}

HEROES = {
    "splash": Hero(id="Splash Star", type="girl", suit="blue suit", power="water sense", share_style="likes to share", tags={"hero", "share"}),
    "beam": Hero(id="Beam Kid", type="boy", suit="red suit", power="light burst", share_style="learns to share", tags={"hero", "share"}),
    "comet": Hero(id="Comet Ace", type="boy", suit="silver suit", power="quick jump", share_style="does not like to share at first", tags={"hero"}),
}

TOOLS = {
    "sop": Tool(id="sop", label="sop", phrase="the soft sop", absorb="magic water", shared_use="together", tags={"sop", "tool", "magic"}),
    "net": Tool(id="net", label="net", phrase="the floating net", absorb="magic foam", shared_use="together", tags={"tool"}),
    "towel": Tool(id="towel", label="towel", phrase="the big towel", absorb="magic water", shared_use="together", tags={"tool"}),
}

MYSTERIES = {
    "glimmer": Mystery(id="glimmer", label="the glimmer mystery", clue="a shiny trail on the pool steps", reveal="a dropped magic pearl had made the water sparkle", solved_with="magic water", tags={"mystery", "water"}),
    "splashmark": Mystery(id="splashmark", label="the splashmark mystery", clue="swirly marks on the water", reveal="the marks came from a tiny pool sprite hiding under a float", solved_with="magic water", tags={"mystery", "water"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero pool story about sharing a sop and solving a magic mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero1", choices=HEROES)
    ap.add_argument("--hero2", choices=HEROES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.mystery and not solveable(TOOLS[args.tool], MYSTERIES[args.mystery]):
        raise StoryError("The chosen tool cannot solve that mystery.")
    place = args.place or rng.choice(list(PLACES))
    hero1 = args.hero1 or rng.choice(list(HEROES))
    hero2 = args.hero2 or rng.choice([k for k in HEROES if k != hero1])
    tool = args.tool or "sop"
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if not PLACES[place].has_pool:
        raise StoryError("This world needs a pool setting.")
    return StoryParams(place=place, hero1=hero1, hero2=hero2, tool=tool, mystery=mystery)


def tell(world: World, place: Place, h1: Entity, h2: Entity, tool: Entity, mystery: Entity) -> None:
    h1.memes["hope"] += 1
    h2.memes["hope"] += 1
    world.say(
        f"At {place.label}, {h1.id} and {h2.id} watched the water glitter like a secret. "
        f"{h1.id} wore {h1.pronoun('possessive')} {HEROES[h1.attrs['hero_key']].suit if 'hero_key' in h1.attrs else 'bright suit'}, and {h2.id} kept watch beside {h1.pronoun('object')}."
    )
    world.say(
        f"Then they noticed {mystery.label}: {mystery.clue}. "
        f"It looked like magic was making the pool act strange."
    )
    world.para()
    h2.memes["want"] += 1
    world.say(
        f"{h2.id} reached for {tool.label} first because {h2.pronoun()} wanted to keep {tool.label_word if hasattr(tool, 'label_word') else tool.label} close."
    )
    h1.memes["need"] += 1
    world.say(
        f'But {h1.id} shook {h1.pronoun("possessive")} head. "{tool.label_word if hasattr(tool, "label_word") else tool.label} works best when we share it," {h1.id} said.'
    )


def _ensure_share(world: World, h1: Entity, h2: Entity, tool: Entity) -> None:
    h1.memes["shared"] += 1
    h2.memes["shared"] += 1
    tool.memes["shared"] += 1
    world.get("pool").meters["calm"] += 1


def _do_magic(world: World, mystery: Entity, tool: Entity) -> None:
    mystery.meters["magic_splash"] += 1
    tool.meters["soaked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{tool.id} soaked up the glowing water, and the shine stopped spreading."
    )
    world.say(
        f"With the splash contained, the heroes followed the clues until the answer appeared."
    )


def _reveal(world: World, mystery: Entity, h1: Entity, h2: Entity) -> None:
    world.say(
        f"{mystery.reveal}. {h1.id} and {h2.id} smiled because the mystery made sense at last."
    )
    world.say(
        f"They shared the sop, saved the pool, and turned the strange sparkle into a safe trick."
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hero1 not in HEROES or params.hero2 not in HEROES or params.tool not in TOOLS or params.mystery not in MYSTERIES:
        raise StoryError("Unknown parameter key.")
    place = PLACES[params.place]
    hero_cfg1 = HEROES[params.hero1]
    hero_cfg2 = HEROES[params.hero2]
    tool_cfg = TOOLS[params.tool]
    mystery_cfg = MYSTERIES[params.mystery]
    if not place.has_pool:
        raise StoryError("This storyworld needs a pool.")
    if not hazard_at_risk(tool_cfg, mystery_cfg):
        raise StoryError("The tool cannot address the mystery in this pool story.")

    world = World()
    pool = world.add(Entity(id="pool", kind="place", type="place", label=place.label, tags=set(place.tags)))
    h1 = world.add(Entity(id=hero_cfg1.id, kind="character", type=hero_cfg1.type, role="leader", attrs={"hero_key": hero_cfg1.id}, tags=set(hero_cfg1.tags)))
    h2 = world.add(Entity(id=hero_cfg2.id, kind="character", type=hero_cfg2.type, role="helper", attrs={"hero_key": hero_cfg2.id}, tags=set(hero_cfg2.tags)))
    tool = world.add(Entity(id=tool_cfg.id, kind="thing", type="tool", label=tool_cfg.label, tags=set(tool_cfg.tags)))
    mystery = world.add(Entity(id=mystery_cfg.id, kind="thing", type="mystery", label=mystery_cfg.label, tags=set(mystery_cfg.tags)))
    world.facts.update(place=place, hero1=h1, hero2=h2, tool=tool, mystery=mystery)

    tell(world, place, h1, h2, tool, mystery)
    world.para()
    _ensure_share(world, h1, h2, tool)
    _do_magic(world, mystery, tool)
    _reveal(world, mystery, h1, h2)

    world.facts["shared"] = True
    world.facts["solved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the word "sop" and takes place at {f["place"].label}.',
        f"Tell a story where {f['hero1'].id} and {f['hero2'].id} share a sop to solve a mystery at the pool.",
        f'Write a gentle superhero story about magic water, sharing, and a mystery to solve.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    h1, h2, tool, mystery = f["hero1"], f["hero2"], f["tool"], f["mystery"]
    return [
        ("Who are the story heroes?",
         f"The story is about {h1.id} and {h2.id}. They worked together like superhero friends and stayed close to the pool."),
        ("What problem did they solve?",
         f"They solved {mystery.label}. The clue in the pool made them look carefully, and sharing the sop helped them find the answer."),
        ("Why did they share the sop?",
         f"They shared the sop because it worked best when both heroes used it together. That kept the magic water from spreading and let them solve the mystery safely."),
        ("What happened at the end?",
         f"The pool turned calm again, and the mystery was solved. The ending shows that sharing the sop changed the trouble into a clear answer."),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pool?",
         "A pool is a place with water where people can splash, swim, and play. In this storyworld, the pool is also where the mystery appears."),
        ("What does it mean to share something?",
         "To share means more than one person uses it kindly. Sharing helps friends work together instead of fighting over the same thing."),
        ("What is a mystery?",
         "A mystery is something puzzling that needs clues and careful thinking to solve. The fun part is following the clues until the answer makes sense."),
        ("Why can magic be tricky?",
         "Magic can be tricky because it may cause surprising changes. In this story, the heroes had to use it carefully so the pool stayed safe."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("absorb", tid, t.absorb))
        lines.append(asp.fact("shared_use", tid, t.shared_use))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("mtag", mid, tag))
        lines.append(asp.fact("solved_with", mid, m.solved_with))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, H, T, M) :- place(P), hero(H), tool(T), mystery(M), shared_use(T,together), solved_with(M,SW), absorb(T,SW).
show_story(P, H, T, M) :- valid(P, H, T, M).
"""


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(build_asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    pset = set(valid_combos())
    cset = set(asp_valid_combos())
    if pset == cset:
        print(f"OK: gate matches valid_combos() ({len(pset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
        print("python-only:", sorted(pset - cset))
        print("clingo-only:", sorted(cset - pset))
    try:
        sample = generate(StoryParams(place="pool", hero1="splash", hero2="beam", tool="sop", mystery="glimmer"))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def asp_program(show: str) -> str:
    return build_asp_program(show)


def explain_rejection() -> str:
    return "(No story: this world needs a pool, a magic-water mystery, and a sop that works together.)"


def explain_response() -> str:
    return "(No story: the selected tool cannot solve the mystery in this pool story.)"


def resolve_names(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.hero1 and args.hero1 not in HEROES:
        raise StoryError("Unknown hero1.")
    if args.hero2 and args.hero2 not in HEROES:
        raise StoryError("Unknown hero2.")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    return resolve_params(args, rng)


def valid_story_keys() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def _choices_without(x: str, keys: list[str]) -> list[str]:
    return [k for k in keys if k != x]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.mystery:
        if not solveable(TOOLS[args.tool], MYSTERIES[args.mystery]):
            raise StoryError(explain_response())
    place = args.place or rng.choice(list(PLACES))
    hero1 = args.hero1 or rng.choice(list(HEROES))
    hero2 = args.hero2 or rng.choice(_choices_without(hero1, list(HEROES)))
    tool = args.tool or "sop"
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    return StoryParams(place=place, hero1=hero1, hero2=hero2, tool=tool, mystery=mystery)


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    return _generate(params)


def _generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hero1 not in HEROES or params.hero2 not in HEROES or params.tool not in TOOLS or params.mystery not in MYSTERIES:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    h1_cfg = HEROES[params.hero1]
    h2_cfg = HEROES[params.hero2]
    tool_cfg = TOOLS[params.tool]
    mystery_cfg = MYSTERIES[params.mystery]
    if not place.has_pool or not place.has_magic_water:
        raise StoryError(explain_rejection())
    if not solveable(tool_cfg, mystery_cfg):
        raise StoryError(explain_response())

    world = World()
    world.add(Entity(id="pool", kind="place", type="place", label=place.label, tags=set(place.tags)))
    h1 = world.add(Entity(id=h1_cfg.id, kind="character", type=h1_cfg.type, role="leader", attrs={"hero_key": h1_cfg.id}, tags=set(h1_cfg.tags)))
    h2 = world.add(Entity(id=h2_cfg.id, kind="character", type=h2_cfg.type, role="helper", attrs={"hero_key": h2_cfg.id}, tags=set(h2_cfg.tags)))
    tool = world.add(Entity(id=tool_cfg.id, kind="thing", type="tool", label=tool_cfg.label, tags=set(tool_cfg.tags)))
    mystery = world.add(Entity(id=mystery_cfg.id, kind="thing", type="mystery", label=mystery_cfg.label, tags=set(mystery_cfg.tags)))
    world.facts.update(place=place, hero1=h1, hero2=h2, tool=tool, mystery=mystery)
    tell(world, place, h1, h2, tool, mystery)
    _ensure_share(world, h1, h2, tool)
    world.para()
    _do_magic(world, mystery, tool)
    _reveal(world, mystery, h1, h2)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_qa(world)],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="pool", hero1="splash", hero2="beam", tool="sop", mystery="glimmer", seed=base_seed),
            StoryParams(place="roofpool", hero1="beam", hero2="splash", tool="towel", mystery="splashmark", seed=base_seed + 1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("absorb", tid, tool.absorb))
        lines.append(asp.fact("shared_use", tid, tool.shared_use))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("solved_with", mid, mystery.solved_with))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,H,T,M) :- place(P), hero(H), tool(T), mystery(M), shared_use(T,together), solved_with(M,SW), absorb(T,SW).
"""


if __name__ == "__main__":
    main()
