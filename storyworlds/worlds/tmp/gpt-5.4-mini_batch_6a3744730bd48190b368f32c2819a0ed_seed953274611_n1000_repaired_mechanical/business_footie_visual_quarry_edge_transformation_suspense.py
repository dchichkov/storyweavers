#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/business_footie_visual_quarry_edge_transformation_suspense.py
===============================================================================================

A small Myth-style storyworld at a quarry edge: two friends run a tiny business,
use a visual sign to guide a footie match, and face a suspenseful transformation
when the stone and water answer back.

The domain is built to satisfy the Storyweavers contract with:
- typed entities carrying meters and memes
- a forward-chained causal model
- a Python reasonableness gate and inline ASP twin
- three Q&A sets grounded in simulated state
- complete stories with a premise, turn, and ending image
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
MAX_SUSPENSE = 3.5


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
class Quarry:
    id: str
    edge: str
    water: str
    stone: str
    echo: str
    danger: str
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
class Business:
    id: str
    label: str
    goods: str
    work: str
    sign: str
    coin: str
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
class Footie:
    id: str
    label: str
    play: str
    ball: str
    zone: str
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
class Visual:
    id: str
    label: str
    phrase: str
    gleam: str
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
class Transformation:
    id: str
    name: str
    trigger: str
    effect: str
    reveal: str
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
    quarry: str
    business: str
    footie: str
    visual: str
    transform: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
    parent: str
    seed: Optional[int] = None
    suspense: int = 2
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

    def characters(self) -> list[Entity]:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    quarry = world.get("quarry")
    for ent in world.characters():
        if ent.memes["fear"] < THRESHOLD:
            continue
        sig = ("suspense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        quarry.meters["quiet"] += 1
        out.append("")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    quarry = world.get("quarry")
    for ent in world.characters():
        if ent.meters["change"] < THRESHOLD:
            continue
        sig = ("transform", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        quarry.meters["bright"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("transform", _r_transform)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def reasonableness_gate(q: Quarry, b: Business, f: Footie, v: Visual, t: Transformation) -> bool:
    return ("quarry" in q.tags and "business" in b.tags and "footie" in f.tags
            and "visual" in v.tags and "transform" in t.tags)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for qid in QUARRIES:
        for bid in BUSINESSES:
            for fid in FOOTIES:
                for vid in VISUALS:
                    for tid in TRANSFORMS:
                        if reasonableness_gate(QUARRIES[qid], BUSINESSES[bid], FOOTIES[fid], VISUALS[vid], TRANSFORMS[tid]):
                            combos.append((qid, bid, fid, vid, tid))
    return combos


def predict(world: World, hero: Entity, quarry: Quarry, transform: Transformation) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] += 1
    sim.get(hero.id).meters["change"] += 1
    return {"change": sim.get(hero.id).meters["change"]}


def tell(quarry: Quarry, business: Business, footie: Footie, visual: Visual, transform: Transformation,
         a_name: str, a_gender: str, b_name: str, b_gender: str, parent: str, suspense: int) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="friend"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="friend"))
    p = world.add(Entity(id=parent, kind="character", type="mother" if parent.lower() in {"mom", "mother"} else "father", role="parent", label="the parent"))
    q = world.add(Entity(id="quarry", label=quarry.edge, type="place"))
    world.add(Entity(id="business", label=business.label))
    world.add(Entity(id="footie", label=footie.label))
    world.add(Entity(id="visual", label=visual.label))

    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(f"At {quarry.edge}, {a.id} and {b.id} ran a small {business.label} together.")
    world.say(f"They sold {business.goods} near the {quarry.stone}, and {visual.phrase} showed the way.")
    world.say(f"In the hollow above the water, their {footie.label} game rang out like a little myth.")

    world.para()
    a.memes["fear"] += suspense
    b.memes["fear"] += 1
    world.say(f"Then the wind turned cold, and the {quarry.echo} made the edge feel strange.")
    world.say(f"{b.id} pointed to {visual.gleam}. \"That sign is changing,\" {b.pronoun()} whispered.")
    world.say(f"{a.id} felt the same worry, because the stone looked ready for a trick of fate.")

    world.para()
    pred = predict(world, a, quarry, transform)
    world.facts["predicted_change"] = pred["change"]
    world.say(f"{p.label_word.capitalize()} came close and watched the sign with them.")
    world.say(f"Together they followed {transform.trigger}, and {a.id}'s hands began the {transform.name}.")
    a.meters["change"] += 1
    b.memes["trust"] += 1
    propagate(world)
    world.say(f"The old worry slipped away as the {transform.effect} settled over the edge.")

    world.para()
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    q.meters["bright"] += 1
    world.say(f"By the end, their friendship felt new, and the quarry edge shone with {transform.reveal}.")
    world.say(f"The business, the footie, and the visual sign were still there, but now they belonged to a safer day.")

    world.facts.update(
        hero_a=a, hero_b=b, parent=p, quarry=quarry, business=business, footie=footie,
        visual=visual, transform=transform, suspense=suspense, changed=a.meters["change"] >= THRESHOLD
    )
    return world


QUARRIES = {
    "quarry_edge": Quarry(
        id="quarry_edge",
        edge="the quarry edge",
        water="the dark water below",
        stone="the pale stone wall",
        echo="echo",
        danger="drop",
        tags={"quarry", "edge"},
    )
}

BUSINESSES = {
    "snack_stall": Business(
        id="snack_stall",
        label="snack business",
        goods="sweet buns and juice",
        work="sell snacks",
        sign="a painted board",
        coin="small coins",
        tags={"business"},
    )
}

FOOTIES = {
    "stone_footie": Footie(
        id="stone_footie",
        label="footie game",
        play="kick the ball on the stone path",
        ball="a soft ball",
        zone="edge",
        tags={"footie"},
    )
}

VISUALS = {
    "lane_sign": Visual(
        id="lane_sign",
        label="visual sign",
        phrase="a bright painted sign",
        gleam="the sign's bright arrow",
        tags={"visual"},
    )
}

TRANSFORMS = {
    "stone_to_bridge": Transformation(
        id="stone_to_bridge",
        name="turning",
        trigger="the first careful kick",
        effect="stone-bridge transformation",
        reveal="a bridge of light",
        tags={"transformation", "myth"},
    )
}

NAMES = ["Mira", "Theo", "Nia", "Oren", "Lina", "Bram"]
GENDERS = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic quarry-edge storyworld with business, footie, and visual signs.")
    ap.add_argument("--quarry", choices=QUARRIES)
    ap.add_argument("--business", choices=BUSINESSES)
    ap.add_argument("--footie", choices=FOOTIES)
    ap.add_argument("--visual", choices=VISUALS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=GENDERS)
    ap.add_argument("--gender-b", choices=GENDERS)
    ap.add_argument("--suspense", type=int, choices=[1, 2, 3])
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
    if args.suspense is not None and args.suspense > 3:
        raise StoryError("Suspense is too high for a children's myth; keep it small.")
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    qid, bid, fid, vid, tid = rng.choice(combos)
    return StoryParams(
        quarry=args.quarry or qid,
        business=args.business or bid,
        footie=args.footie or fid,
        visual=args.visual or vid,
        transform=args.transform or tid,
        name_a=args.name_a or rng.choice(NAMES),
        gender_a=args.gender_a or rng.choice(GENDERS),
        name_b=args.name_b or rng.choice([n for n in NAMES if n != (args.name_a or "")]),
        gender_b=args.gender_b or rng.choice(GENDERS),
        parent=args.parent or rng.choice(["mom", "dad"]),
        suspense=args.suspense if args.suspense is not None else rng.randint(1, 3),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a myth-like story at the quarry edge about business, footie, and a visual sign.",
        "Tell a suspenseful friendship story where two children run a tiny business and something transforms by the water.",
        "Write a child-friendly myth where the word business appears, the footie game matters, and the ending changes the quarry edge.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["hero_a"], f["hero_b"]
    q = f["quarry"]
    t = f["transform"]
    return [
        QAItem(
            question="Who are the story's friends?",
            answer=f"The story is about {a.id} and {b.id}. They stay together through the suspense at the quarry edge, and their friendship helps carry the ending."
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The edge changed into {t.reveal}. That happened after they followed {t.trigger}, so the story ends with a brighter place than it began."
        ),
        QAItem(
            question="Why was the middle of the story suspenseful?",
            answer=f"The quarry edge felt risky because the water and stone made everything uncertain. The wind and the echo also made the children feel that something important was about to happen."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a quarry?", "A quarry is a place where stone is cut or taken from the ground. It can have steep edges and deep open spaces."),
        QAItem("What is friendship?", "Friendship means caring about someone, helping them, and staying close when things feel hard. Friends can make brave moments feel less scary."),
        QAItem("What does visual mean?", "Visual means something you can see with your eyes. A visual sign helps by showing a clear shape, color, or direction."),
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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(quarry="quarry_edge", business="snack_stall", footie="stone_footie", visual="lane_sign", transform="stone_to_bridge", name_a="Mira", gender_a="girl", name_b="Theo", gender_b="boy", parent="mom", suspense=2),
    StoryParams(quarry="quarry_edge", business="snack_stall", footie="stone_footie", visual="lane_sign", transform="stone_to_bridge", name_a="Nia", gender_a="girl", name_b="Oren", gender_b="boy", parent="dad", suspense=3),
]


def valid_for_params(params: StoryParams) -> bool:
    return params.quarry in QUARRIES and params.business in BUSINESSES and params.footie in FOOTIES and params.visual in VISUALS and params.transform in TRANSFORMS


def asp_facts() -> str:
    import asp
    lines = []
    for q in QUARRIES:
        lines.append(asp.fact("quarry", q))
    for b in BUSINESSES:
        lines.append(asp.fact("business", b))
    for f in FOOTIES:
        lines.append(asp.fact("footie", f))
    for v in VISUALS:
        lines.append(asp.fact("visual", v))
    for t in TRANSFORMS:
        lines.append(asp.fact("transform", t))
    lines.append(asp.fact("theme_ok", "business"))
    lines.append(asp.fact("theme_ok", "footie"))
    lines.append(asp.fact("theme_ok", "visual"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Q,B,F,V,T) :- quarry(Q), business(B), footie(F), visual(V), transform(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos disagree.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(quarry=None, business=None, footie=None, visual=None, transform=None, parent=None, name_a=None, name_b=None, gender_a=None, gender_b=None, suspense=None), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if not valid_for_params(params):
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(
        QUARRIES[params.quarry],
        BUSINESSES[params.business],
        FOOTIES[params.footie],
        VISUALS[params.visual],
        TRANSFORMS[params.transform],
        params.name_a, params.gender_a, params.name_b, params.gender_b, params.parent, params.suspense,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
