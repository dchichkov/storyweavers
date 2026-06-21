#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/desk_teamwork_transformation_mystery.py
======================================================================

A small story world about a mysterious desk, two helpers, and a quiet
transformation. The story begins with a puzzling problem, moves through
teamwork, and ends with a changed desk that proves the mystery was solved.

The domain is child-facing and concrete:
- A desk hides or reveals a missing thing.
- Two characters investigate together.
- Their joint action transforms the desk from ordinary to surprising.
- The ending image shows the change clearly.

Supported modes:
- default generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

This script is self-contained except for the shared result containers and the
optional ASP helper.
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
        return self.label or self.type
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
    hidden_spot: str
    clue: str
    surprise_image: str
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
class MysteryObject:
    id: str
    label: str
    phrase: str
    clue_text: str
    transformation: str
    tags: set[str] = field(default_factory=set)
    transformed_label: str = ""
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
class Tool:
    id: str
    label: str
    phrase: str
    use_text: str
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
class StoryParams:
    setting: str
    object: str
    tool1: str
    tool2: str
    detective1: str
    detective1_gender: str
    detective2: str
    detective2_gender: str
    adult: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
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


def _r_messy(world: World) -> list[str]:
    out: list[str] = []
    desk = world.get("desk")
    if desk.meters["opened"] < THRESHOLD:
        return out
    sig = ("messy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    desk.meters["mystery"] += 1
    out.append("A small secret seemed to wake up inside the desk.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    desk = world.get("desk")
    if desk.meters["solved"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    desk.meters["transformed"] += 1
    desk.label = "music desk"
    out.append("The desk changed its look and revealed a bright new purpose.")
    return out


CAUSAL_RULES = [Rule("mystery", _r_messy), Rule("transform", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, obj: MysteryObject) -> bool:
    return "desk" in setting.tags and "transformation" in obj.tags


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for oid, o in OBJECTS.items():
            if reasonableness_gate(s, o):
                combos.append((sid, oid))
    return combos


def predict_transformation(world: World, obj_id: str) -> dict:
    sim = world.copy()
    sim.get(obj_id).meters["opened"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.get("desk").meters["mystery"] >= THRESHOLD,
        "transformed": sim.get("desk").meters["transformed"] >= THRESHOLD,
    }


def start(world: World, s: Setting, a: Entity, b: Entity, obj: MysteryObject) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} found a desk in a dim room. "
        f"{s.mood.capitalize()} light touched its top, and the {s.hidden_spot} looked odd."
    )
    world.say(
        f"There was a tiny clue: {obj.clue_text}. "
        f"It made the desk feel like it was hiding a secret."
    )


def investigate(world: World, a: Entity, b: Entity, obj: MysteryObject, tool1: Tool, tool2: Tool) -> None:
    world.say(
        f"{a.id} held {tool1.phrase}, and {b.id} held {tool2.phrase}. "
        f"Together they listened, looked, and tapped gently."
    )
    world.say(
        f"{a.id} whispered, \"Maybe the clue is trying to tell us something.\" "
        f"{b.id} nodded, because mystery stories need careful helpers."
    )


def open_desk(world: World, a: Entity, b: Entity, obj: MysteryObject) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    desk = world.get("desk")
    desk.meters["opened"] += 1
    desk.meters["teamwork"] += 1
    world.say(
        f"Then {a.id} and {b.id} worked together. One pulled the drawer, the other shined a light."
    )
    propagate(world, narrate=True)


def solve_mystery(world: World, a: Entity, b: Entity, adult: Entity, obj: MysteryObject, setting: Setting) -> None:
    desk = world.get("desk")
    desk.meters["solved"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"They found the answer at last: the desk was not just a desk. "
        f"It was a hidden little stage that could become {obj.transformation}."
    )
    world.say(
        f"{adult.label_word.capitalize()} smiled and said the best part was how {a.id} and {b.id} solved it together."
    )
    world.say(
        f"By the end, the old desk had turned into {setting.surprise_image}, "
        f"and the room felt less strange and more magical."
    )


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, adult = f["detective1"], f["detective2"], f["adult"]
    setting = f["setting_obj"]
    obj = f["object_obj"]
    return [
        (
            "Who worked together in the story?",
            f"{a.id} and {b.id} worked together. They looked carefully at the desk and solved the mystery as a team.",
        ),
        (
            "What was mysterious about the desk?",
            f"The desk seemed to hide a secret, because there was a clue nearby and the room felt odd. The clue made everyone wonder what the desk could become.",
        ),
        (
            "What changed by the end?",
            f"The desk transformed into {setting.surprise_image}. That change happened after {a.id} and {b.id} opened it together and found the answer.",
        ),
        (
            f"Why did {adult.id} smile at the end?",
            f"{adult.id} smiled because the children used teamwork and careful thinking. They solved the mystery without giving up, and the finished desk showed their success.",
        ),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What is teamwork?",
            "Teamwork means people help each other to do something together. Each helper does a part, and the job is easier and better that way.",
        ),
        (
            "What is transformation?",
            "Transformation means something changes into a new form or a new purpose. It can look surprising, but the old thing is still the starting point.",
        ),
        (
            "What is a desk for?",
            "A desk is a piece of furniture where people can write, draw, read, or keep things organized. It gives a steady surface to work on.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting_obj"]
    obj = f["object_obj"]
    return [
        f'Write a child-friendly mystery story that includes the word "desk" and ends with a surprising transformation.',
        f"Tell a gentle mystery where {f['detective1'].id} and {f['detective2'].id} solve a puzzle about a desk by working together.",
        f"Write a story about teamwork and transformation in {setting.place}, and make the desk clue matter to the ending.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "studio": Setting(
        id="studio",
        place="a quiet studio",
        mood="soft",
        hidden_spot="desk drawer",
        clue="a tiny brass key",
        surprise_image="a little music box stage",
        tags={"desk"},
    ),
    "library": Setting(
        id="library",
        place="a small library",
        mood="dusty",
        hidden_spot="desk lamp corner",
        clue="a scrap of blue ribbon",
        surprise_image="a story nook with bright lamps",
        tags={"desk"},
    ),
    "attic": Setting(
        id="attic",
        place="a warm attic",
        mood="golden",
        hidden_spot="desk drawer",
        clue="a neat line of pencil marks",
        surprise_image="a tiny map table",
        tags={"desk"},
    ),
}

OBJECTS = {
    "key": MysteryObject(
        id="key",
        label="brass key",
        phrase="a brass key",
        clue_text="a tiny brass key was tucked near the desk",
        transformation="a music box stage",
        transformed_label="music box stage",
        tags={"transformation"},
    ),
    "ribbon": MysteryObject(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon",
        clue_text="a blue ribbon peeked from under the desk",
        transformation="a story nook",
        transformed_label="story nook",
        tags={"transformation"},
    ),
    "note": MysteryObject(
        id="note",
        label="paper note",
        phrase="a paper note",
        clue_text="a paper note rested beside the desk",
        transformation="a map table",
        transformed_label="map table",
        tags={"transformation"},
    ),
}

TOOLS = {
    "lamp": Tool(
        id="lamp",
        label="lamp",
        phrase="a lamp",
        use_text="shine a light on the clue",
        tags={"desk"},
    ),
    "brush": Tool(
        id="brush",
        label="brush",
        phrase="a dust brush",
        use_text="brush away the dust",
        tags={"desk"},
    ),
    "notebook": Tool(
        id="notebook",
        label="notebook",
        phrase="a notebook",
        use_text="write down what they found",
        tags={"desk"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Ben", "Leo", "Theo", "Sam", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A desk mystery story world with teamwork and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--tool1", choices=TOOLS)
    ap.add_argument("--tool2", choices=TOOLS)
    ap.add_argument("--detective1")
    ap.add_argument("--detective1-gender", choices=["girl", "boy"])
    ap.add_argument("--detective2")
    ap.add_argument("--detective2-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father", "woman", "man"])
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


def valid_name(gender: str, rng: random.Random, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    if not reasonableness_gate(SETTINGS[setting], OBJECTS[obj]):
        raise StoryError("(No story: this setting and object do not fit the desk mystery.)")
    g1 = args.detective1_gender or rng.choice(["girl", "boy"])
    g2 = args.detective2_gender or ("boy" if g1 == "girl" else "girl")
    a_gender = args.adult_gender or rng.choice(["mother", "father"])
    d1 = args.detective1 or valid_name(g1, rng, set())
    d2 = args.detective2 or valid_name(g2, rng, {d1})
    adult = args.adult or ("Mom" if a_gender in {"mother", "woman"} else "Dad")
    t1 = args.tool1 or rng.choice(list(TOOLS))
    t2 = args.tool2 or rng.choice([k for k in TOOLS if k != t1])
    return StoryParams(
        setting=setting,
        object=obj,
        tool1=t1,
        tool2=t2,
        detective1=d1,
        detective1_gender=g1,
        detective2=d2,
        detective2_gender=g2,
        adult=adult,
        adult_gender=a_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS.get(params.setting)
    obj = OBJECTS.get(params.object)
    t1 = TOOLS.get(params.tool1)
    t2 = TOOLS.get(params.tool2)
    if not setting or not obj or not t1 or not t2:
        raise StoryError("Invalid story parameters.")
    if params.tool1 == params.tool2:
        raise StoryError("The two helpers need different tools for this mystery.")

    a = world.add(Entity(id=params.detective1, kind="character", type=params.detective1_gender, role="detective"))
    b = world.add(Entity(id=params.detective2, kind="character", type=params.detective2_gender, role="detective"))
    adult_type = "mother" if params.adult_gender in {"mother", "woman"} else "father"
    adult = world.add(Entity(id=params.adult, kind="character", type=adult_type, role="adult", label_word="grown-up"))
    desk = world.add(Entity(id="desk", kind="thing", type="furniture", label="desk"))
    world.facts.update(setting_obj=setting, object_obj=obj, detective1=a, detective2=b, adult=adult, desk=desk)

    start(world, a, b, obj)
    world.para()
    investigate(world, a, b, obj, t1, t2)
    open_desk(world, a, b, obj)
    world.para()
    solve_mystery(world, a, b, adult, obj, setting)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
desk_story(S,O) :- setting(S), object(O), desk_setting(S), transformation(O).
teamwork(A,B) :- detective(A), detective(B), A != B.
solved :- teamwork(A,B), desk_opened, clue_present.
transformed :- solved, transformation_object(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("desk_setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if "transformation" in obj.tags:
            lines.append(asp.fact("transformation_object", oid))
            lines.append(asp.fact("transformation", oid))
    lines.append(asp.fact("detective", "a"))
    lines.append(asp.fact("detective", "b"))
    lines.append(asp.fact("clue_present"))
    lines.append(asp.fact("desk_opened"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show desk_story/2."))
    return sorted(set(asp.atoms(model, "desk_story")))


def asp_verify() -> int:
    rc = 0
    try:
        import io
        from contextlib import redirect_stdout
        args = build_parser().parse_args([])
        with redirect_stdout(io.StringIO()):
            sample = generate(resolve_params(args, random.Random(7)))
            _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"FAIL: generate smoke test crashed: {exc}")
        return 1

    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: ASP matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
        print("  only in ASP:", sorted(c - p))
        print("  only in Python:", sorted(p - c))
    return rc


def valid_story_params() -> list[StoryParams]:
    out = []
    for sid, oid in valid_combos():
        out.append(StoryParams(
            setting=sid,
            object=oid,
            tool1="lamp",
            tool2="brush",
            detective1="Mia",
            detective1_gender="girl",
            detective2="Ben",
            detective2_gender="boy",
            adult="Mom",
            adult_gender="mother",
        ))
    return out


def explain_rejection() -> str:
    return "(No story: the chosen desk mystery pieces do not fit together well enough.)"


def generation_prompts_from_params(params: StoryParams) -> list[str]:
    return [
        'Write a child-friendly mystery story that includes the word "desk" and ends with teamwork and transformation.',
        f"Tell a short mystery where {params.detective1} and {params.detective2} solve a desk clue together.",
        "Write a story in which a desk seems ordinary at first, then changes in a surprising way after careful teamwork.",
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show desk_story/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible desk-story combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="studio", object="key", tool1="lamp", tool2="brush", detective1="Mia", detective1_gender="girl", detective2="Ben", detective2_gender="boy", adult="Mom", adult_gender="mother"),
            StoryParams(setting="library", object="ribbon", tool1="brush", tool2="notebook", detective1="Leo", detective1_gender="boy", detective2="Ava", detective2_gender="girl", adult="Dad", adult_gender="father"),
            StoryParams(setting="attic", object="note", tool1="lamp", tool2="notebook", detective1="Nora", detective1_gender="girl", detective2="Sam", detective2_gender="boy", adult="Mom", adult_gender="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
