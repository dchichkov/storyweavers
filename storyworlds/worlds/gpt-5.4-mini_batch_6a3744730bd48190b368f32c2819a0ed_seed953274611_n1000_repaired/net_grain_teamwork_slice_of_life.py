#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/net_grain_teamwork_slice_of_life.py
====================================================================

A small, slice-of-life storyworld about a homey teamwork moment with a net and
grain. A child helps a grown-up in an ordinary afternoon task: they use a net to
catch spilled grain, clean the counter, and finish the little job together.

The world keeps the classical storyworld shape:
- typed entities with physical meters and emotional memes
- a small forward-chaining world model
- a reasonableness gate plus an inline ASP twin
- three Q&A sets grounded in the simulated story/world

The core premise is gentle: a grain sack splits or a bowl tips, grain spills, a
net becomes useful, and teamwork turns a small mess into a finished chore.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
class Setting:
    id: str
    place: str
    mood: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    mesh: str
    tags: set[str] = field(default_factory=set)
    makes_help: bool = True
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
class Grain:
    id: str
    label: str
    phrase: str
    spill_word: str
    scoop_word: str
    tags: set[str] = field(default_factory=set)
    loose: bool = True
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
class HelperMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def people(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_spill(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("floor").meters["grain"] += e.meters["spilled"]
        for p in world.people():
            p.memes["worry"] += 0.5
        out.append("__spill__")
    return out


def _r_teamwork(world: World) -> list[str]:
    if world.get("child").memes["helping"] >= THRESHOLD and world.get("adult").memes["helping"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("task").meters["done"] += 1
            world.get("child").memes["pride"] += 1
            world.get("adult").memes["pride"] += 1
            return ["__done__"]
    return []


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("teamwork", "social", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reasonable(tool: Tool, grain: Grain) -> bool:
    return tool.makes_help and grain.loose


def sensible_moves() -> list[HelperMove]:
    return [m for m in MOVES.values() if m.sense >= SENSE_MIN]


def best_move() -> HelperMove:
    return max(MOVES.values(), key=lambda m: m.sense)


def would_clean(move: HelperMove, grain: Grain) -> bool:
    return move.power >= 1


def predict(world: World, move: HelperMove) -> dict:
    sim = world.copy()
    sim.get("child").memes["helping"] += 1
    sim.get("adult").memes["helping"] += 1
    sim.get("task").meters["done"] += 1 if would_clean(move, GRAINS["rice"]) else 0
    return {"done": sim.get("task").meters["done"] >= THRESHOLD}


def setup(world: World, child: Entity, adult: Entity, setting: Setting, grain: Grain, tool: Tool) -> None:
    child.memes["curious"] += 1
    adult.memes["calm"] += 1
    world.say(
        f"On a quiet afternoon at {setting.place}, {child.id} and {adult.id} were "
        f"doing an ordinary chore together. {setting.mood.capitalize()}, a small bowl of {grain.label} waited on the counter."
    )
    world.say(
        f"{adult.id} pointed at the {tool.label} and said it could help sort the {grain.label} without making a bigger mess."
    )


def spill_turn(world: World, child: Entity, grain: Grain) -> None:
    child.memes["surprised"] += 1
    world.say(
        f"Then the bowl tipped. {grain.phrase.capitalize()} spilled across the table and onto the floor."
    )
    world.say(f"{child.id} blinked at the little scatter of {grain.label} and froze for a moment.")


def teamwork_turn(world: World, child: Entity, adult: Entity, tool: Tool, grain: Grain, move: HelperMove) -> None:
    child.memes["helping"] += 1
    adult.memes["helping"] += 1
    world.say(
        f'"Let\'s work together," {adult.id} said. {child.id} held the bowl while {adult.id} used the {tool.label} to catch the loose {grain.label}.'
    )
    world.say(
        f"{child.id} scooped the stray bits back in with both hands, and the {tool.label} kept the grain from slipping through again."
    )
    world.say(
        f"{adult.id} smiled and said {move.qa_text}."
    )


def finish(world: World, child: Entity, adult: Entity, grain: Grain, tool: Tool) -> None:
    child.memes["joy"] += 1
    adult.memes["joy"] += 1
    world.say(
        f"By the end, the counter was neat again, the {grain.label} was back in the bowl, and the {tool.label} was set by the sink."
    )
    world.say(
        f"{child.id} washed {child.pronoun('possessive')} hands, {adult.id} wiped the table, and both of them felt proud of the small job they had finished together."
    )


def tell(setting: Setting, grain: Grain, tool: Tool, move: HelperMove,
         child_name: str = "Mina", child_gender: str = "girl",
         adult_name: str = "Grandma", adult_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    floor = world.add(Entity(id="floor", label="the floor"))
    task = world.add(Entity(id="task", label="the chore"))

    setup(world, child, adult, setting, grain, tool)
    world.para()
    spill_turn(world, child, grain)
    child.memes["helping"] += 1
    adult.memes["helping"] += 1
    if not reasonable(tool, grain):
        raise StoryError("This tool and grain do not make a sensible teamwork story.")
    teamwork_turn(world, child, adult, tool, grain, move)
    world.para()
    finish(world, child, adult, grain, tool)

    world.facts.update(
        child=child,
        adult=adult,
        floor=floor,
        task=task,
        setting=setting,
        grain=grain,
        tool=tool,
        move=move,
        done=task.meters["done"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", mood="the room smelled like toast"),
    "pantry": Setting(id="pantry", place="the pantry", mood="the shelves were tidy and warm"),
    "market": Setting(id="market", place="the little market stall", mood="the morning was busy but friendly"),
    "bakery": Setting(id="bakery", place="the neighborhood bakery", mood="the oven had just finished baking"),
}

TOOLS = {
    "net": Tool(id="net", label="net", phrase="a fine net", purpose="catch loose grain", mesh="small", tags={"net", "grain", "teamwork"}),
    "tray_net": Tool(id="tray_net", label="tray with a net liner", phrase="a tray lined with netting", purpose="sort grain", mesh="small", tags={"net", "grain", "teamwork"}),
    "sieve": Tool(id="sieve", label="sieve", phrase="a small sieve", purpose="hold grain", mesh="small", tags={"grain", "teamwork"}),
}

GRAINS = {
    "rice": Grain(id="rice", label="rice", phrase="The rice", spill_word="rice", scoop_word="rice", tags={"grain"}),
    "wheat": Grain(id="wheat", label="wheat berries", phrase="The wheat berries", spill_word="wheat berries", scoop_word="wheat berries", tags={"grain"}),
    "oats": Grain(id="oats", label="oats", phrase="The oats", spill_word="oats", scoop_word="oats", tags={"grain"}),
}

MOVES = {
    "catch": HelperMove(id="catch", sense=3, power=2, text="caught the spilling grain before it rolled too far", fail="tried to catch the grain, but some of it still skittered away", qa_text="caught the grain before it spread across the whole floor", tags={"teamwork"}),
    "sort": HelperMove(id="sort", sense=2, power=1, text="sorted the grain into a neat pile", fail="sorted a little, but not enough to finish the job", qa_text="sorted the grain into a neat pile together", tags={"teamwork"}),
    "gather": HelperMove(id="gather", sense=3, power=2, text="gathered the grain back into the bowl", fail="gathered it slowly, but the spill was too wide", qa_text="gathered the grain back into the bowl together", tags={"teamwork"}),
    "brush": HelperMove(id="brush", sense=1, power=1, text="brushed the grain with an old cloth", fail="brushed the grain around without really collecting it", qa_text="brushed the grain together and made the counter tidy again", tags={"teamwork"}),
}

@dataclass
class StoryParams:
    theme: str
    grain: str
    tool: str
    move: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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
    StoryParams(theme="kitchen", grain="rice", tool="net", move="catch", child_name="Mina", child_gender="girl", adult_name="Grandma", adult_gender="woman"),
    StoryParams(theme="pantry", grain="oats", tool="tray_net", move="sort", child_name="Theo", child_gender="boy", adult_name="Dad", adult_gender="man"),
    StoryParams(theme="bakery", grain="wheat", tool="sieve", move="gather", child_name="Lena", child_gender="girl", adult_name="Aunt Jo", adult_gender="woman"),
]

def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for gid in GRAINS:
            for tid, tool in TOOLS.items():
                if not reasonable(tool, GRAINS[gid]):
                    continue
                for mid in MOVES:
                    out.append((sid, gid, tid, mid))
    return out


KNOWLEDGE = {
    "net": [("What is a net?", "A net is something with holes in it. People use nets to catch or hold things while letting tiny bits pass through.")],
    "grain": [("What is grain?", "Grain is a small hard food, like rice or wheat, that people cook or bake with.")],
    "teamwork": [("What is teamwork?", "Teamwork is when people help each other and do a job together.")],
    "kitchen": [("What happens in a kitchen?", "A kitchen is where people cook food, wash dishes, and do simple daily jobs together.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "{f["tool"].label}" and "{f["grain"].label}".',
        f"Tell a gentle teamwork story where {f['child'].id} helps {f['adult'].id} with grain using a {f['tool'].label}.",
        f"Write a cozy everyday story about a small spill, a net, and two people fixing it together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, a, g, t = f["child"], f["adult"], f["grain"], f["tool"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {c.id} and {a.id}, who work together during an ordinary chore."),
        QAItem(question="What spilled?", answer=f"{g.phrase} spilled across the table and floor, which made the task suddenly messy."),
        QAItem(question=f"What did {c.id} and {a.id} use to help?", answer=f"They used a {t.label} to catch and gather the loose grain. The tool helped them keep the grain from sliding away while they cleaned it up."),
        QAItem(question="How did the story end?", answer=f"It ended with the grain back in a bowl, the counter neat again, and both of them feeling proud of working together."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["tool"].tags) | set(world.facts["grain"].tags) | {"teamwork"}
    out = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
grain_spilled(G) :- grain(G), spilled(G).
teamwork_done :- helper(child), helper(adult), move_ok.
valid(S,T,G,M) :- setting(S), tool(T), grain(G), move(M), makes_help(T), loose(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.makes_help:
            lines.append(asp.fact("makes_help", tid))
    for gid, g in GRAINS.items():
        lines.append(asp.fact("grain", gid))
        if g.loose:
            lines.append(asp.fact("loose", gid))
    for mid in MOVES:
        lines.append(asp.fact("move", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAILED: generate() smoke test crashed: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life teamwork story with a net and grain.")
    ap.add_argument("--theme", choices=SETTINGS)
    ap.add_argument("--grain", choices=GRAINS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
    if args.tool and args.grain and not reasonable(TOOLS[args.tool], GRAINS[args.grain]):
        raise StoryError("This tool does not sensibly help with that grain.")
    choices = [c for c in valid_combos()
               if (args.theme is None or c[0] == args.theme)
               and (args.grain is None or c[1] == args.grain)
               and (args.tool is None or c[2] == args.tool)
               and (args.move is None or c[3] == args.move)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    theme, grain, tool, move = rng.choice(sorted(choices))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(["Mina", "Theo", "Lena", "June", "Noah"])
    adult_name = args.adult_name or rng.choice(["Grandma", "Dad", "Aunt Jo", "Mom", "Grandpa"])
    return StoryParams(theme=theme, grain=grain, tool=tool, move=move,
                       child_name=child_name, child_gender=child_gender,
                       adult_name=adult_name, adult_gender=adult_gender)


def generate(params: StoryParams) -> StorySample:
    if params.theme not in SETTINGS or params.grain not in GRAINS or params.tool not in TOOLS or params.move not in MOVES:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.theme]
    grain = GRAINS[params.grain]
    tool = TOOLS[params.tool]
    move = MOVES[params.move]
    world = tell(setting, grain, tool, move, params.child_name, params.child_gender, params.adult_name, params.adult_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, grain, tool, move) combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
