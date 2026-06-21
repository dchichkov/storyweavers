#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/inspection_lesson_learned_moral_value_humor_comedy.py
======================================================================================

A small comedy storyworld about an inspection, a silly shortcut, and a gentle
lesson learned. The domain is intentionally tiny: a child wants to pass a room
inspection, tries a goofy shortcut, a careful helper notices the problem, and
they fix it honestly before the inspector arrives.

The story aims for:
- child-facing prose
- state-driven turns and ending image
- humor without cruelty
- a clear lesson learned and moral value

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/inspection_lesson_learned_moral_value_humor_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/inspection_lesson_learned_moral_value_humor_comedy.py --qa
    python storyworlds/worlds/gpt-5.4-mini/inspection_lesson_learned_moral_value_humor_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/inspection_lesson_learned_moral_value_humor_comedy.py --verify
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
MAX_MESS = 2.0


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
    scene: str
    detail: str
    inspection_point: str
    hiding_spot: str
    tidy_image: str
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
class MessItem:
    id: str
    label: str
    phrase: str
    messy_kind: str
    hides_evidence: bool = False
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
class FixTool:
    id: str
    label: str
    phrase: str
    power: int
    humor: str
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
class Inspector:
    id: str
    label: str
    type: str
    tone: str
    finds: str
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


def _r_mess_spreads(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.meters["mess"] < THRESHOLD:
        return out
    sig = ("mess_spreads",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["inspection_risk"] += 1
    child.memes["worry"] += 1
    out.append("")
    return out


def _r_honesty_cools(world: World) -> list[str]:
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if child is None or helper is None:
        return out := []
    if child.memes["honesty"] < THRESHOLD:
        return out := []
    sig = ("honesty_cools",)
    if sig in world.fired:
        return out := []
    world.fired.add(sig)
    helper.memes["pride"] += 1
    child.memes["relief"] += 1
    return out := []


CAUSAL_RULES: list[Rule] = [
    Rule("mess_spreads", "physical", _r_mess_spreads),
    Rule("honesty_cools", "social", _r_honesty_cools),
]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def enough_to_notice(tool: FixTool, item: MessItem) -> bool:
    return tool.power >= (2 if item.hides_evidence else 1)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id in MESS_ITEMS:
            item = MESS_ITEMS[item_id]
            for tool_id, tool in FIX_TOOLS.items():
                if enough_to_notice(tool, item):
                    combos.append((place_id, item_id, tool_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mess_item: str
    fix_tool: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    inspector_kind: str
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mess_item and args.fix_tool:
        if (args.place, args.mess_item, args.fix_tool) not in valid_combos():
            raise StoryError("That combination would not create a believable inspection story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mess_item is None or c[1] == args.mess_item)
              and (args.fix_tool is None or c[2] == args.fix_tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mess_item, fix_tool = rng.choice(sorted(combos))
    child_gender = args.child_gender if hasattr(args, "child_gender") and args.child_gender else rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=child_name)
    inspector_kind = rng.choice(sorted(INSPECTORS))
    return StoryParams(
        place=place,
        mess_item=mess_item,
        fix_tool=fix_tool,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        inspector_kind=inspector_kind,
        seed=None,
    )


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES or params.mess_item not in MESS_ITEMS or params.fix_tool not in FIX_TOOLS:
        raise StoryError("Invalid StoryParams.")
    if params.inspector_kind not in INSPECTORS:
        raise StoryError("Invalid inspector kind.")

    place = PLACES[params.place]
    mess = MESS_ITEMS[params.mess_item]
    tool = FIX_TOOLS[params.fix_tool]
    inspector = INSPECTORS[params.inspector_kind]

    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child",
                             label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, role="helper",
                              label=params.helper_name))
    inspector_ent = world.add(Entity(id="inspector", kind="character", type=inspector.type, role="inspector",
                                     label=inspector.label))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.scene))
    mess_ent = world.add(Entity(id="mess", kind="thing", type="thing", label=mess.label))
    tool_ent = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label))
    child.attrs.update(place=place.id, mess_item=mess.id, fix_tool=tool.id)
    helper.attrs.update(place=place.id)
    inspector_ent.attrs.update(tone=inspector.tone)

    child.memes["pride"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["honesty"] = 0.0
    helper.memes["care"] = 1.0

    world.say(
        f"{child.label} and {helper.label} were getting the {place.scene} ready for an inspection. "
        f"{place.detail}"
    )
    world.say(
        f"{child.label} wanted the place to look perfect, but {mess.phrase} was in the way."
    )

    world.para()
    world.say(
        f"{child.label} had a silly idea. \"What if I just hide it under the {place.hiding_spot}?\""
    )
    child.meters["mess"] += 1
    child.memes["sneaky"] += 1
    if mess.hides_evidence:
        room.meters["inspection_risk"] += 1
    if tool.id == "gloves":
        world.say(
            f"{helper.label} blinked. \"That would make the room look like a banana in a tuxedo,\" "
            f"said {helper.label}, trying not to laugh."
        )
    else:
        world.say(
            f"{helper.label} pointed at the spot and snorted. \"That plan has the dignity of a wobbling spoon.\""
        )

    world.para()
    world.say(
        f"Then {helper.label} said, \"Let's fix it the honest way before the inspector comes.\""
    )
    child.memes["honesty"] += 1
    if enough_to_notice(tool, mess):
        child.meters["mess"] = 0.0
        room.meters["inspection_risk"] = 0.0
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(
            f"They used {tool.phrase} and soon the place looked {place.tidy_image}. "
            f"{tool.humor}"
        )
        world.say(
            f"When the inspector arrived, {inspector.label} smiled and said, \"{inspector.finds}.\""
        )
        world.say(
            f"{child.label} grinned. {child.pronoun().capitalize()} had learned that honesty cleans up faster than hiding."
        )
    else:
        world.say(
            f"They tried to use {tool.phrase}, but it was too small to help. Luckily, they still told the truth and asked for a better idea."
        )
        child.memes["relief"] += 1
        world.say(
            f"The inspector arrived, looked around, and said, \"I can tell you tried. Let me help.\""
        )

    propagate(world)

    world.facts.update(
        child=child,
        helper=helper,
        inspector=inspector_ent,
        place=place,
        mess=mess,
        tool=tool,
        outcome="clean" if child.meters["mess"] == 0 else "messy",
    )
    return world


def tell(params: StoryParams) -> World:
    return build_world(params)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a comedy story about an inspection where {f['child'].label} worries about a messy room and learns an honest fix.",
        f"Tell a short story for a young child that includes the word 'inspection' and ends with a kind lesson learned.",
        f"Write a funny, gentle story where a child tries a goofy shortcut, then chooses the moral value of honesty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    mess = f["mess"]
    tool = f["tool"]
    qa = [
        QAItem(
            question="What kind of day was it in the story?",
            answer=f"It was an inspection day at {place.scene}. Everyone was trying to make the place look ready and neat.",
        ),
        QAItem(
            question=f"What silly idea did {child.label} have?",
            answer=f"{child.label} wanted to hide {mess.phrase} under the {place.hiding_spot}. That would have looked funny for a moment, but it would not have been honest.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} encouraged the honest fix and used {tool.phrase} with {child.label}. Together they cleaned up the room before the inspector came.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that being honest is better than making a sneaky shortcut. Honesty fixes trouble faster and leaves everyone feeling proud.",
        ),
    ]
    if world.facts["outcome"] == "clean":
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the room looking {place.tidy_image} and the inspector smiling. The child felt relieved because the truth made the inspection go well.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inspection?",
            answer="An inspection is when someone checks things carefully to see if they are neat, safe, or done properly.",
        ),
        QAItem(
            question="Why is honesty important?",
            answer="Honesty helps people trust each other. When you tell the truth, problems can be fixed in a calm and sensible way.",
        ),
        QAItem(
            question="Why can hiding a mess be a bad idea?",
            answer="A hidden mess can become a bigger problem later. It is usually better to clean it up or ask for help right away.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


PLACES = {
    "classroom": Place(
        id="classroom",
        scene="the classroom",
        detail="The desks were lined up like shy little boats, and the floor already sparkled in the morning light.",
        inspection_point="the corner by the cubbies",
        hiding_spot="desk",
        tidy_image="bright and shiny",
        tags={"inspection", "classroom"},
    ),
    "bedroom": Place(
        id="bedroom",
        scene="the bedroom",
        detail="The bed was made, the window was open a crack, and one toy sock had somehow become the king of the floor.",
        inspection_point="the shelf by the bed",
        hiding_spot="pillow",
        tidy_image="cozy and tidy",
        tags={"inspection", "bedroom"},
    ),
    "library": Place(
        id="library",
        scene="the library corner",
        detail="The books stood in neat rows, and even the quiet chair seemed to be whispering, 'Please don't spill anything.'",
        inspection_point="the reading nook",
        hiding_spot="rug",
        tidy_image="quiet and neat",
        tags={"inspection", "library"},
    ),
}

MESS_ITEMS = {
    "crayons": MessItem(
        id="crayons",
        label="a spilled pile of crayons",
        phrase="a spilled pile of crayons",
        messy_kind="color",
        hides_evidence=False,
        tags={"inspection", "crayons"},
    ),
    "cookies": MessItem(
        id="cookies",
        label="crumbly cookie crumbs",
        phrase="crumbly cookie crumbs",
        messy_kind="crumbs",
        hides_evidence=False,
        tags={"inspection", "cookies"},
    ),
    "glitter": MessItem(
        id="glitter",
        label="sparkly glitter",
        phrase="sparkly glitter",
        messy_kind="sparkle",
        hides_evidence=True,
        tags={"inspection", "glitter"},
    ),
}

FIX_TOOLS = {
    "broom": FixTool(
        id="broom",
        label="a broom",
        phrase="a broom",
        power=2,
        humor="The broom swept so fast it looked like it was late for school.",
        tags={"inspection", "broom"},
    ),
    "cloth": FixTool(
        id="cloth",
        label="a cloth",
        phrase="a cloth",
        power=1,
        humor="The cloth did a tiny victory dance after the last crumb vanished.",
        tags={"inspection", "cloth"},
    ),
    "vacuum": FixTool(
        id="vacuum",
        label="the little vacuum",
        phrase="the little vacuum",
        power=3,
        humor="The vacuum made a loud slurp and then looked proud of itself.",
        tags={"inspection", "vacuum"},
    ),
}

INSPECTORS = {
    "teacher": Inspector(
        id="teacher",
        label="the teacher",
        type="woman",
        tone="kind",
        finds="Nice work. This room looks ready",
        tags={"inspection", "teacher"},
    ),
    "landlord": Inspector(
        id="landlord",
        label="the landlord",
        type="man",
        tone="serious",
        finds="I can see the room is tidy now",
        tags={"inspection", "landlord"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Noah", "Finn", "Theo", "Leo", "Max"]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MESS_ITEMS:
        lines.append(asp.fact("mess", mid))
    for tid in FIX_TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,T) :- place(P), mess(M), tool(T).
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
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("Mismatch between ASP and Python valid_combos().")
    try:
        sample = generate(StoryParams(
            place="classroom",
            mess_item="glitter",
            fix_tool="vacuum",
            child_name="Mia",
            child_gender="girl",
            helper_name="Noah",
            helper_gender="boy",
            inspector_kind="teacher",
            seed=0,
        ))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"Smoke test failed: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy inspection storyworld with a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mess-item", dest="mess_item", choices=MESS_ITEMS)
    ap.add_argument("--fix-tool", dest="fix_tool", choices=FIX_TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--inspector-kind", choices=INSPECTORS)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def tell(params: StoryParams) -> World:
    return build_world(params)


def _sample_default(rng: random.Random) -> StoryParams:
    return resolve_params(argparse.Namespace(
        place=None, mess_item=None, fix_tool=None,
        child_name=None, child_gender=None, helper_name=None, helper_gender=None,
        inspector_kind=None,
    ), rng)


CURATED = [
    StoryParams(place="classroom", mess_item="glitter", fix_tool="vacuum", child_name="Mia", child_gender="girl",
                helper_name="Noah", helper_gender="boy", inspector_kind="teacher", seed=1),
    StoryParams(place="bedroom", mess_item="cookies", fix_tool="broom", child_name="Leo", child_gender="boy",
                helper_name="Ava", helper_gender="girl", inspector_kind="landlord", seed=2),
    StoryParams(place="library", mess_item="crayons", fix_tool="cloth", child_name="Nora", child_gender="girl",
                helper_name="Finn", helper_gender="boy", inspector_kind="teacher", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
