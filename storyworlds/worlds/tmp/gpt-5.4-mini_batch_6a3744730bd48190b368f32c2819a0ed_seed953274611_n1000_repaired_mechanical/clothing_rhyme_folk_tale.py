#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clothing_rhyme_folk_tale.py
============================================================

A small storyworld about a folk-tale sewing circle: cloth, rhyme, a missing
clothing item, a wise helper, and a repaired ending.

The world is built from a tiny simulation:
- one child needs clothing for a festival or journey,
- a wind or snag causes a problem,
- a helper predicts the trouble,
- a sensible fix restores the outfit,
- the ending image proves what changed.

The stories are intentionally child-facing and lightly rhymed.
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

THRESHOLD = 1.0


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
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
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
    rhyme: str
    wind: str
    festival: str
    ground: str
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
class Garment:
    id: str
    label: str
    phrase: str
    body: str
    likely_to_lost: bool = False
    protective: bool = True
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
class Mishap:
    id: str
    label: str
    verb: str
    cause: str
    danger: str
    fix_strength: int
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
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    rhyme: str
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
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_rumple(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters["snagged"] < THRESHOLD:
            continue
        sig = ("rumple", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.role == "garment":
            ent.meters["ruined"] += 1
            world.get("child").memes["worry"] += 1
            out.append("__rumple__")
    return out


CAUSAL_RULES = [Rule("rumple", "physical", _r_rumple)]


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


def predict_problem(world: World, garment_id: str, mishap: Mishap) -> dict:
    sim = world.copy()
    g = sim.get(garment_id)
    g.meters["snagged"] += 1
    propagate(sim, narrate=False)
    return {"ruined": sim.get(garment_id).meters["ruined"] >= THRESHOLD, "worry": sim.get("child").memes["worry"]}


def hazard(mishap: Mishap, garment: Garment) -> bool:
    return "cloth" in garment.tags and mishap.id in {"snag", "mud"}


def valid_fix(mishap: Mishap, garment: Garment, remedy: Remedy) -> bool:
    return remedy.power >= mishap.fix_strength and "repair" in remedy.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for mishap in MISHAPS:
            for garment in GARMENTS:
                if hazard(MISHAPS[mishap], GARMENTS[garment]) and any(valid_fix(MISHAPS[mishap], GARMENTS[garment], REMEDIES[r]) for r in REMEDIES):
                    combos.append((place, mishap, garment))
    return combos


@dataclass
class StoryParams:
    place: str
    mishap: str
    garment: str
    remedy: str
    child: str
    child_type: str
    helper: str
    helper_type: str
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


def _make_story(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    place = world.facts["place"]
    p = PLACES[place]
    mishap = MISHAPS[world.facts["mishap"]]
    garment = GARMENTS[world.facts["garment"]]
    remedy = REMEDIES[world.facts["remedy"]]

    child.memes["joy"] += 1
    helper.memes["kind"] += 1

    world.say(
        f"In {p.scene}, where the old folk songs go, {child.id} wore {garment.phrase} and hummed in the sun and wind. "
        f"{p.rhyme}"
    )
    world.say(
        f"{helper.id} heard the tune and smiled, for in that bright little town, "
        f"everyone loved a tidy cloth and a well-made gown."
    )
    world.para()
    world.say(
        f"But {p.wind} came soft and sly, and {mishap.cause}. "
        f"{child.id} gasped, for {garment.label} was caught by a rough small stitch."
    )
    child.memes["worry"] += 1
    pred = predict_problem(world, garment.id, mishap)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"Oh dear," said {helper.id}, "if that goes on, your {garment.label} will be spoiled." '
        f"{helper.id} knew the old rhyme: {remedy.rhyme}."
    )
    if valid_fix(mishap, garment, remedy):
        world.para()
        world.say(
            f"So {helper.id} came close and {remedy.phrase}. "
            f"The snag let go, the hem came neat, and the little tear was mended sweet."
        )
        world.get(garment.id).meters["snagged"] = 0.0
        world.get(garment.id).meters["ruined"] = 0.0
        child.memes["worry"] = 0.0
        child.memes["relief"] += 1
        helper.memes["pride"] += 1
        world.say(
            f"{child.id} twirled once, then twice, and laughed, because {garment.label} sat true again. "
            f"By the firelight glow, the clothes were ready for the dance."
        )
    else:
        world.para()
        world.say(
            f"But the fix was too weak, and the tear stayed mean. "
            f"Still, {helper.id} stayed kind, and promised a stronger mend by morning."
        )
        world.get(garment.id).meters["ruined"] += 1
        child.memes["worry"] += 1

    world.facts.update(
        child=child,
        helper=helper,
        place_cfg=p,
        mishap_cfg=mishap,
        garment_cfg=garment,
        remedy_cfg=remedy,
        outcome="mended" if world.get(garment.id).meters["ruined"] < THRESHOLD else "tattered",
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.mishap not in MISHAPS:
        raise StoryError("Unknown mishap.")
    if params.garment not in GARMENTS:
        raise StoryError("Unknown clothing item.")
    if params.remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")
    if not valid_fix(MISHAPS[params.mishap], GARMENTS[params.garment], REMEDIES[params.remedy]):
        raise StoryError("That remedy is too weak for this clothing trouble.")

    world = World()
    world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child"))
    world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    world.add(Entity(id="garment", kind="thing", type=params.garment, label=GARMENTS[params.garment].label, role="garment"))
    world.facts["place"] = params.place
    world.facts["mishap"] = params.mishap
    world.facts["garment"] = params.garment
    world.facts["remedy"] = params.remedy
    _make_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = PLACES[f["place"]]
    m = MISHAPS[f["mishap"]]
    g = GARMENTS[f["garment"]]
    r = REMEDIES[f["remedy"]]
    return [
        f'Write a folk-tale story in rhyme that includes the word "clothing" and takes place in {p.scene}.',
        f"Tell a gentle story where {f['child'].id} wears {g.phrase}, then {m.label} causes trouble, and a helper uses {r.label} to fix it.",
        f"Write a child-friendly rhyming folk tale about clothing, a snag, and a kind repair that ends with the garment ready for a festival.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    g = f["garment_cfg"]
    m = f["mishap_cfg"]
    p = f["place_cfg"]
    r = f["remedy_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}. {child.id} is the one wearing the clothing, and {helper.id} is the wise helper who fixes the trouble."),
        ("What went wrong?",
         f"{m.label} caught the {g.label} and made it snagged. That was a problem because the clothing was needed for the festival."),
        ("How was it fixed?",
         f"{helper.id} used {r.label} to mend it. The repair worked because {r.label} had enough power for this kind of cloth trouble."),
    ]
    if f["outcome"] == "mended":
        qa.append((
            "How did the story end?",
            f"It ended happily. {child.id} wore the {g.label} again, and it sat neat and ready while the {p.festival} waited."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with a tattered garment, but the helper stayed kind and promised a stronger mend. The clothing still needed more care."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["garment_cfg"].tags) | set(world.facts["mishap_cfg"].tags) | set(world.facts["remedy_cfg"].tags)
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


PLACES = {
    "village_green": Place(id="village_green", scene="the village green", rhyme="The piper played and the children swayed, as bright as a ribbon in the shade.", wind="a little breeze", festival="Lantern Night", ground="grass", tags={"outdoor", "folk"}),
    "market_lane": Place(id="market_lane", scene="the market lane", rhyme="The baker laughed, and the seamstress sang, while silver bells in the doorway rang.", wind="a cheeky gust", festival="Market Day", ground="stones", tags={"outdoor", "folk"}),
    "river_path": Place(id="river_path", scene="the river path", rhyme="The water hummed, and the reeds did lean, as if they knew what the dancers mean.", wind="the river wind", festival="Midsummer Fair", ground="earth", tags={"outdoor", "folk"}),
}

GARMENTS = {
    "cloak": Garment(id="cloak", label="cloak", phrase="a wool cloak with a bright red clasp", body="shoulders", tags={"cloth", "clothing"}),
    "shawl": Garment(id="shawl", label="shawl", phrase="a woven shawl with little blue stitches", body="shoulders", tags={"cloth", "clothing"}),
    "cap": Garment(id="cap", label="cap", phrase="a green cap with a feather", body="head", tags={"cloth", "clothing"}),
}

MISHAPS = {
    "snag": Mishap(id="snag", label="snag", verb="snag", cause="a thorn snagged the hem", danger="ruined cloth", fix_strength=2, tags={"repair", "cloth"}),
    "mud": Mishap(id="mud", label="mud", verb="muddy", cause="a muddy splash leapt from the lane", danger="stained cloth", fix_strength=2, tags={"repair", "cloth"}),
}

REMEDIES = {
    "needle": Remedy(id="needle", label="needle and thread", phrase="stitched the tear with needle and thread", power=3, rhyme="A stitch in time keeps cloth in line.", tags={"repair"}),
    "patch": Remedy(id="patch", label="patch", phrase="sewed on a neat little patch", power=2, rhyme="Patch the cloth and calm the broth.", tags={"repair"}),
}

CURATED = [
    StoryParams(place="village_green", mishap="snag", garment="cloak", remedy="needle", child="Mara", child_type="girl", helper="Gran", helper_type="grandmother"),
    StoryParams(place="market_lane", mishap="mud", garment="shawl", remedy="needle", child="Tobin", child_type="boy", helper="Uncle Bram", helper_type="man"),
    StoryParams(place="river_path", mishap="snag", garment="cap", remedy="patch", child="Nina", child_type="girl", helper="Old Edith", helper_type="grandmother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhymed folk-tale storyworld about clothing and repair.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy", "woman", "man", "grandmother", "grandfather"], dest="child_type")
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man", "grandmother", "grandfather"], dest="helper_type")
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


def _pick_name(rng: random.Random, kind: str) -> str:
    pools = {
        "girl": ["Mara", "Nina", "Elsa", "June", "Clara"],
        "boy": ["Tobin", "Hugh", "Oren", "Pip", "Jory"],
        "woman": ["Aunt Elin", "Old Edith", "Rose", "Mina"],
        "man": ["Uncle Bram", "Mister Lark", "Silas", "Orin"],
        "grandmother": ["Gran", "Grandma Faye", "Old Edith"],
        "grandfather": ["Grandpa Moss", "Old Jonah", "Granddad Rye"],
    }
    return rng.choice(pools[kind])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.mishap and args.mishap not in MISHAPS:
        raise StoryError("Unknown mishap.")
    if args.garment and args.garment not in GARMENTS:
        raise StoryError("Unknown clothing item.")
    if args.remedy and args.remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")
    if args.mishap and args.garment and not valid_fix(MISHAPS[args.mishap], GARMENTS[args.garment], REMEDIES[args.remedy or "needle"]):
        raise StoryError("That remedy is too weak for this clothing trouble.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mishap is None or c[1] == args.mishap)
              and (args.garment is None or c[2] == args.garment)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mishap, garment = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["grandmother", "grandfather", "woman", "man"])
    child = args.child or _pick_name(rng, child_type)
    helper = args.helper or _pick_name(rng, helper_type)
    return StoryParams(place=place, mishap=mishap, garment=garment, remedy=remedy,
                       child=child, child_type=child_type, helper=helper, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mishap not in MISHAPS or params.garment not in GARMENTS or params.remedy not in REMEDIES:
        raise StoryError("Invalid params.")
    world = World()
    world.facts["place"] = params.place
    world.facts["mishap"] = params.mishap
    world.facts["garment"] = params.garment
    world.facts["remedy"] = params.remedy
    world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child"))
    world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    world.add(Entity(id="garment", kind="thing", type=params.garment, label=GARMENTS[params.garment].label, role="garment"))
    _make_story(world)
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


ASP_RULES = r"""
valid(P, M, G) :- place(P), mishap(M), garment(G), hazard(M, G), fixable(M, G).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m, mv in MISHAPS.items():
        lines.append(asp.fact("mishap", m))
        for t in mv.tags:
            lines.append(asp.fact("mishap_tag", m, t))
    for g, gv in GARMENTS.items():
        lines.append(asp.fact("garment", g))
        for t in gv.tags:
            lines.append(asp.fact("garment_tag", g, t))
    for r, rv in REMEDIES.items():
        lines.append(asp.fact("remedy", r))
        lines.append(asp.fact("power", r, rv.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            rc = 1
            print("MISMATCH between ASP and Python valid_combos().")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: verify smoke test and parity check passed.")
    except Exception:
        traceback.print_exc()
        return 1
    return rc


def format_story_header(sample: StorySample) -> str:
    p = sample.params
    return f"### {p.child} and {p.helper}: {p.garment} in {p.place} ({p.mishap}, {p.remedy})"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(map(str, combo)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = format_story_header(sample) if args.all or len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
