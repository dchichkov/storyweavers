#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/giant_cautionary_nursery_rhyme.py
============================================================

A standalone story world for a cautionary nursery-rhyme tale about a child who
tries to clomp about in giant shoes.

The core constraint is simple and physical: oversized shoes make balance worse,
and a safe replacement must actually fit and suit the ground. The story is
state-driven: a child feels proud, wobbles, gets frightened, is steadied by a
grown-up, and ends by marching safely in shoes that fit.

Run it
------
    python storyworlds/worlds/gpt-5.4/giant_cautionary_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/giant_cautionary_nursery_rhyme.py --place stairs
    python storyworlds/worlds/gpt-5.4/giant_cautionary_nursery_rhyme.py --shoe clogs --safe-shoe slippers
    python storyworlds/worlds/gpt-5.4/giant_cautionary_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/giant_cautionary_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/giant_cautionary_nursery_rhyme.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    ground: str
    danger: str
    weather: str
    risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class GiantShoe:
    id: str
    label: str
    phrase: str
    sound: str
    owner: str
    sway: str
    slip_bonus: int
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeShoe:
    id: str
    label: str
    phrase: str
    grips: set[str] = field(default_factory=set)
    weathers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    giant = world.get("giant_shoe")
    if child.meters["walking"] < THRESHOLD:
        return out
    if giant.meters["worn"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["balance_loss"] += 1 + giant.attrs.get("slip_bonus", 0)
    child.memes["pride"] += 1
    out.append("__wobble__")
    return out


def _r_stumble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    setting = world.get("place")
    helper = world.get("parent")
    if child.meters["balance_loss"] < THRESHOLD:
        return out
    sig = ("stumble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["stumble"] += setting.attrs.get("risk", 1)
    child.memes["fear"] += 1
    helper.memes["alarm"] += 1
    out.append("__stumble__")
    return out


def _r_steady(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    safe = world.get("safe_shoe")
    if safe.meters["worn"] < THRESHOLD or child.meters["walking"] < THRESHOLD:
        return out
    sig = ("steady",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["steady"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    out.append("__steady__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="stumble", tag="physical", apply=_r_stumble),
    Rule(name="steady", tag="physical", apply=_r_steady),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def compatible(setting: Setting, safe_shoe: SafeShoe) -> bool:
    return setting.ground in safe_shoe.grips and setting.weather in safe_shoe.weathers


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in SETTINGS:
        for shoe_id in GIANT_SHOES:
            for safe_id, safe in SAFE_SHOES.items():
                if compatible(SETTINGS[place_id], safe):
                    out.append((place_id, shoe_id, safe_id))
    return out


def predict_tumble(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["walking"] += 1
    sim.get("giant_shoe").meters["worn"] += 1
    propagate(sim, narrate=False)
    return {
        "balance_loss": sim.get("child").meters["balance_loss"],
        "stumble": sim.get("child").meters["stumble"],
        "fear": sim.get("child").memes["fear"],
    }


def intro(world: World, child: Entity, giant_cfg: GiantShoe, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Little {child.id} found {giant_cfg.phrase} by the door. "
        f'"{giant_cfg.label.capitalize()}, giant {giant_cfg.label}, '
        f'clomp for me once more!"'
    )
    world.say(
        f"They belonged to {giant_cfg.owner}, and they looked grand and wide. "
        f"{child.id} slipped tiny toes inside and stood up full of pride."
    )
    world.say(
        f"Out by {setting.place}, the {setting.ground} waited under the {setting.weather} sky. "
        f"It looked like just the place for a marching rhyme."
    )


def warning(world: World, child: Entity, parent: Entity, giant_cfg: GiantShoe, setting: Setting) -> None:
    pred = predict_tumble(world)
    world.facts["predicted_stumble"] = pred["stumble"]
    child.memes["defiance"] += 1
    world.say(
        f'But {parent.label_word} saw the giant shoes and called, '
        f'"Slow feet, sweet feet, do not race. Those {giant_cfg.label} are too big for {setting.place}."'
    )
    if pred["stumble"] >= THRESHOLD:
        world.say(
            f'{parent.pronoun().capitalize()} pointed at the {setting.ground} and said, '
            f'"One long slip could send you toward {setting.danger}."'
        )


def attempt(world: World, child: Entity, giant_cfg: GiantShoe) -> None:
    world.get("giant_shoe").meters["worn"] += 1
    child.meters["walking"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Yet {child.id} sang, "Clompity, clompity, giant and tall!" '
        f"{child.pronoun().capitalize()} took a step, then another, "
        f"while the loose shoes {giant_cfg.sway} and {giant_cfg.sound} on the floor."
    )


def near_fall(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    if child.meters["stumble"] < THRESHOLD:
        return
    world.say(
        f"Then came the turn: one heel slid, one toe flew, and {child.id} wobbled hard. "
        f"{child.pronoun().capitalize()} tipped toward {setting.danger} with a surprised little gasp."
    )
    world.say(
        f"{parent.label_word.capitalize()} hurried over, caught {child.pronoun('object')} under the arms, "
        f"and set {child.pronoun('object')} safe and still."
    )
    child.memes["fear"] += 1


def lesson(world: World, child: Entity, parent: Entity) -> None:
    child.memes["pride"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'For half a breath, {child.id} looked very small beside the giant shoes. '
        f'"I was trying to be tall," {child.pronoun()} whispered.'
    )
    world.say(
        f'"Tall can wait," said {parent.label_word}. "Feet must fit before they flit. '
        f'Great big shoes are not for little rushing feet."'
    )


def safe_change(world: World, child: Entity, parent: Entity, safe_cfg: SafeShoe, setting: Setting) -> None:
    world.get("giant_shoe").meters["worn"] = 0.0
    world.get("safe_shoe").meters["worn"] += 1
    child.meters["walking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {parent.label_word} fetched {safe_cfg.phrase}. "
        f"They hugged {child.id}'s feet snugly, light and neat."
    )
    world.say(
        f'Together they tried again: "Tapity, trim, let the right shoes win." '
        f"This time {child.id} crossed {setting.place} with steady steps and a bright grin."
    )
    world.say(
        f"So ends the rhyme of giant shoes: look first, listen fast, and choose what fits. "
        f"The giant pair stayed by the door, and the safe small pair danced on."
    )


def tell(
    setting: Setting,
    giant_cfg: GiantShoe,
    safe_cfg: SafeShoe,
    child_name: str = "Mabel",
    child_type: str = "girl",
    parent_type: str = "mother",
    trait: str = "brisk",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    place = world.add(Entity(id="place", type="place", label=setting.place, attrs={"risk": setting.risk}))
    giant = world.add(
        Entity(
            id="giant_shoe",
            type="shoe",
            label=giant_cfg.label,
            phrase=giant_cfg.phrase,
            attrs={"slip_bonus": giant_cfg.slip_bonus},
            tags=set(giant_cfg.tags),
        )
    )
    safe = world.add(
        Entity(
            id="safe_shoe",
            type="shoe",
            label=safe_cfg.label,
            phrase=safe_cfg.phrase,
            tags=set(safe_cfg.tags),
        )
    )
    child.attrs["name"] = child_name
    child.traits = [trait]
    parent.attrs["name"] = parent.label_word
    place.attrs["ground"] = setting.ground
    place.attrs["danger_text"] = setting.danger

    intro(world, child, giant_cfg, setting)
    world.para()
    warning(world, child, parent, giant_cfg, setting)
    attempt(world, child, giant_cfg)
    world.para()
    near_fall(world, child, parent, setting)
    lesson(world, child, parent)
    world.para()
    safe_change(world, child, parent, safe_cfg, setting)

    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        giant_cfg=giant_cfg,
        safe_cfg=safe_cfg,
        stumbled=child.meters["stumble"] >= THRESHOLD,
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "stairs": Setting(
        id="stairs",
        place="the front stairs",
        ground="painted steps",
        danger="the bottom step",
        weather="dry",
        risk=2,
        tags={"stairs"},
    ),
    "path": Setting(
        id="path",
        place="the garden path",
        ground="wet stones",
        danger="the rose bush",
        weather="rainy",
        risk=2,
        tags={"rain", "path"},
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen tiles",
        ground="smooth tiles",
        danger="the table leg",
        weather="dry",
        risk=1,
        tags={"kitchen"},
    ),
    "yard": Setting(
        id="yard",
        place="the cobbled yard",
        ground="round cobbles",
        danger="the gate",
        weather="windy",
        risk=2,
        tags={"yard"},
    ),
}

GIANT_SHOES = {
    "boots": GiantShoe(
        id="boots",
        label="boots",
        phrase="a giant pair of rain boots",
        sound="boom-boomed",
        owner="dad",
        sway="flopped from side to side",
        slip_bonus=1,
        tags={"boots", "giant"},
    ),
    "clogs": GiantShoe(
        id="clogs",
        label="clogs",
        phrase="a giant pair of wooden clogs",
        sound="clack-clacked",
        owner="grandma",
        sway="rattled and rocked",
        slip_bonus=1,
        tags={"clogs", "giant"},
    ),
    "snowboots": GiantShoe(
        id="snow boots",
        label="snow boots",
        phrase="a giant pair of snow boots",
        sound="thump-thumped",
        owner="uncle",
        sway="swooshed and swayed",
        slip_bonus=1,
        tags={"boots", "giant"},
    ),
}

SAFE_SHOES = {
    "slippers": SafeShoe(
        id="slippers",
        label="slippers",
        phrase="soft house slippers with grippy bottoms",
        grips={"painted steps", "smooth tiles"},
        weathers={"dry"},
        tags={"slippers"},
    ),
    "rainboots": SafeShoe(
        id="rainboots",
        label="rain boots",
        phrase="little rain boots with snug straps",
        grips={"wet stones", "round cobbles"},
        weathers={"rainy", "windy"},
        tags={"rainboots", "rain"},
    ),
    "sneakers": SafeShoe(
        id="sneakers",
        label="sneakers",
        phrase="small sneakers with tidy laces",
        grips={"painted steps", "smooth tiles", "round cobbles"},
        weathers={"dry", "windy"},
        tags={"sneakers"},
    ),
}

GIRL_NAMES = ["Mabel", "Nell", "Daisy", "Lucy", "Poppy", "Tess", "Mina", "Rose"]
BOY_NAMES = ["Robin", "Toby", "Ned", "Finn", "Milo", "Sam", "Jack", "Theo"]
TRAITS = ["brisk", "bouncy", "eager", "curious", "cheery"]


@dataclass
class StoryParams:
    place: str
    shoe: str
    safe_shoe: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "giant": [
        (
            "What does giant mean?",
            "Giant means very, very big. When something is giant compared with your body, it can be hard to hold or wear safely.",
        )
    ],
    "boots": [
        (
            "Why can giant boots be hard to walk in?",
            "Boots that are far too big can slide and flap around your feet. That makes it harder to balance and easier to trip.",
        )
    ],
    "clogs": [
        (
            "What are clogs?",
            "Clogs are hard shoes, often made of wood or with stiff soles. If they are much too big, they can knock and slip when you walk.",
        )
    ],
    "slippers": [
        (
            "What are grippy slippers for?",
            "Grippy slippers help your feet stay steady on indoor floors. They fit closely and can stop some slipping.",
        )
    ],
    "sneakers": [
        (
            "Why are sneakers good for walking?",
            "Sneakers fit your feet and have bendy soles with grip. That helps you balance and step more safely.",
        )
    ],
    "rain": [
        (
            "Why are wet stones slippery?",
            "Water makes some stones slick, so your shoes can slide more easily. Careful steps and the right shoes help.",
        )
    ],
    "stairs": [
        (
            "Why should children go slowly on stairs?",
            "Stairs have edges and different levels, so a stumble can quickly turn into a fall. Slow feet are safer feet.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    giant_cfg = f["giant_cfg"]
    safe_cfg = f["safe_cfg"]
    return [
        'Write a short cautionary nursery-rhyme story for a 3-to-5-year-old that includes the word "giant".',
        f"Tell a rhythmic story where {child.attrs['name']} tries on {giant_cfg.phrase} at {setting.place}, nearly tumbles, and learns to wear shoes that fit.",
        f"Write a child-facing rhyme with a warning beat and a happy ending, where {safe_cfg.phrase} solve the problem after a wobble.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    setting = f["setting"]
    giant_cfg = f["giant_cfg"]
    safe_cfg = f["safe_cfg"]
    name = child.attrs["name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a little child who wanted to march in {giant_cfg.phrase}. It is also about {pw}, who watched carefully and helped at the right time.",
        ),
        (
            f"Why did {name} want the giant shoes?",
            f"{name} thought the giant shoes looked grand and fun, and wearing them made {child.pronoun('object')} feel tall. That proud feeling is why {child.pronoun()} tried them on even after the warning.",
        ),
        (
            f"Why did {pw} tell {name} to slow down?",
            f"{pw.capitalize()} could see the shoes were too big for walking safely on {setting.ground}. One bad slip could send {name} toward {setting.danger}, so the warning came before the tumble.",
        ),
    ]
    if f["stumbled"]:
        qa.append(
            (
                f"What happened when {name} tried to walk in the giant shoes?",
                f"{name} wobbled and nearly fell. The shoes slid and flopped, which made balancing hard on {setting.ground}.",
            )
        )
    if f["learned"]:
        qa.append(
            (
                f"How was the problem fixed?",
                f"{pw.capitalize()} took away the giant pair and brought {safe_cfg.phrase} instead. Because the new shoes fit and suited {setting.place}, {name} could walk with steady steps.",
            )
        )
        qa.append(
            (
                f"What did {name} learn at the end?",
                f"{name} learned that big-looking things are not always safe for little feet. Shoes should fit before you rush and run.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"giant"} | set(f["giant_cfg"].tags) | set(f["safe_cfg"].tags) | set(f["setting"].tags)
    out: list[tuple[str, str]] = []
    order = ["giant", "boots", "clogs", "slippers", "sneakers", "rain", "stairs"]
    for tag in order:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="stairs",
        shoe="clogs",
        safe_shoe="slippers",
        child_name="Mabel",
        child_type="girl",
        parent_type="mother",
        trait="eager",
    ),
    StoryParams(
        place="path",
        shoe="boots",
        safe_shoe="rainboots",
        child_name="Robin",
        child_type="boy",
        parent_type="father",
        trait="curious",
    ),
    StoryParams(
        place="kitchen",
        shoe="snowboots",
        safe_shoe="sneakers",
        child_name="Nell",
        child_type="girl",
        parent_type="mother",
        trait="bouncy",
    ),
    StoryParams(
        place="yard",
        shoe="boots",
        safe_shoe="rainboots",
        child_name="Toby",
        child_type="boy",
        parent_type="father",
        trait="cheery",
    ),
]


def explain_rejection(place: str, safe_shoe: str) -> str:
    setting = SETTINGS[place]
    safe = SAFE_SHOES[safe_shoe]
    return (
        f"(No story: {safe.phrase} are not a sensible fix for {setting.place}. "
        f"They do not match the {setting.weather} weather or the {setting.ground}, "
        f"so they would not honestly solve the slipping problem.)"
    )


ASP_RULES = r"""
compatible(P, S) :- setting(P), safe_shoe(S),
                    ground_of(P, G), grips(S, G),
                    weather_of(P, W), weather_ok(S, W).
valid(P, Gt, S) :- setting(P), giant_shoe(Gt), compatible(P, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        lines.append(asp.fact("ground_of", place_id, setting.ground))
        lines.append(asp.fact("weather_of", place_id, setting.weather))
    for shoe_id in GIANT_SHOES:
        lines.append(asp.fact("giant_shoe", shoe_id))
    for safe_id, safe in SAFE_SHOES.items():
        lines.append(asp.fact("safe_shoe", safe_id))
        for grip in sorted(safe.grips):
            lines.append(asp.fact("grips", safe_id, grip))
        for weather in sorted(safe.weathers):
            lines.append(asp.fact("weather_ok", safe_id, weather))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(123)))
    except StoryError as err:
        rc = 1
        print(f"Smoke setup failed: {err}")
        smoke_cases = []

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"Smoke generation failed for {params}: {err}")
            break
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, giant shoes, a near tumble, and shoes that fit."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--shoe", choices=GIANT_SHOES)
    ap.add_argument("--safe-shoe", choices=SAFE_SHOES, dest="safe_shoe")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.safe_shoe:
        if not compatible(SETTINGS[args.place], SAFE_SHOES[args.safe_shoe]):
            raise StoryError(explain_rejection(args.place, args.safe_shoe))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.shoe is None or combo[1] == args.shoe)
        and (args.safe_shoe is None or combo[2] == args.safe_shoe)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, shoe, safe_shoe = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        shoe=shoe,
        safe_shoe=safe_shoe,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.shoe not in GIANT_SHOES:
        raise StoryError(f"(Unknown shoe: {params.shoe})")
    if params.safe_shoe not in SAFE_SHOES:
        raise StoryError(f"(Unknown safe shoe: {params.safe_shoe})")
    if not compatible(SETTINGS[params.place], SAFE_SHOES[params.safe_shoe]):
        raise StoryError(explain_rejection(params.place, params.safe_shoe))

    world = tell(
        setting=SETTINGS[params.place],
        giant_cfg=GIANT_SHOES[params.shoe],
        safe_cfg=SAFE_SHOES[params.safe_shoe],
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
        trait=params.trait,
    )
    story = world.render().replace("child", params.child_name)
    story = story.replace("parent", world.get("parent").label_word)
    story = story.replace("Little child", f"Little {params.child_name}")
    story = story.replace("child's", f"{params.child_name}'s")
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, giant-shoe, safe-shoe) combos:\n")
        for place, shoe, safe in combos:
            print(f"  {place:8} {shoe:10} {safe}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            p = StoryParams(
                place=params.place,
                shoe=params.shoe,
                safe_shoe=params.safe_shoe,
                child_name=params.child_name,
                child_type=params.child_type,
                parent_type=params.parent_type,
                trait=params.trait,
                seed=params.seed,
            )
            samples.append(generate(p))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.shoe} at {p.place} -> {p.safe_shoe}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
