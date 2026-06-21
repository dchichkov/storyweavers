#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/arrow_transformation_bravery_folk_tale.py
=========================================================================

A standalone folk-tale storyworld about an arrow, a brave child, and a small
transformation that changes what the village believes is possible.

Premise
-------
A young archery trainee meets an old woodsman who can turn plain ash wood into
a talking arrow. The child must decide whether to shoot the enchanted arrow into
the dark of the hill, where a shy shape waits, or back away from the unknown.

The storyworld keeps a tiny simulation:
- physical meters: carried, shining, broken, transformed, open_path
- emotional memes: bravery, fear, wonder, trust, resolve

The turn:
- the child chooses bravery and looses the arrow
- the arrow transforms a hidden willow sprout into a lantern-tree
- the village gains a safe light and a way through the hill

The ending:
- the child keeps the bow, the arrow is changed into a seed-silver charm, and
  the hill path is no longer dark.

Contract notes:
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
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
from typing import Optional

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
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    material: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king", "woodsman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Setting:
    id: str
    place: str
    dark_place: str
    village_need: str
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
class ArrowKind:
    id: str
    label: str
    wood: str
    tip: str
    song: str
    transform_to: str
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
class Transformation:
    id: str
    label: str
    cause: str
    result_label: str
    result_use: str
    power: int
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
class BraveryChoice:
    id: str
    label: str
    fear_need: int
    resolve_gain: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTING = Setting(
    id="hill_village",
    place="a quiet hill village",
    dark_place="the black mouth of the hill cave",
    village_need="a safe way to cross the hill",
    mood="old and whispery",
)

ARROWS = {
    "ash": ArrowKind(
        id="ash",
        label="ash arrow",
        wood="ash",
        tip="silver tip",
        song="It sang like a reed in the wind.",
        transform_to="seed-silver charm",
        tags={"arrow", "wood", "song"},
    ),
    "birch": ArrowKind(
        id="birch",
        label="birch arrow",
        wood="birch",
        tip="bone tip",
        song="It hummed like a small bee.",
        transform_to="moon-white key",
        tags={"arrow", "light"},
    ),
}

TRANSFORMATIONS = {
    "lantern_tree": Transformation(
        id="lantern_tree",
        label="lantern-tree",
        cause="brave shot",
        result_label="lantern-tree",
        result_use="glow in the dark and guide travelers",
        power=2,
        tags={"transformation", "light"},
    ),
    "seed_charm": Transformation(
        id="seed_charm",
        label="seed-silver charm",
        cause="brave choice",
        result_label="seed-silver charm",
        result_use="be kept as a promise of courage",
        power=1,
        tags={"transformation", "bravery"},
    ),
}

BRAVERY = {
    "steady": BraveryChoice(
        id="steady",
        label="steady bravery",
        fear_need=2,
        resolve_gain=2,
        tags={"bravery"},
    ),
    "bold": BraveryChoice(
        id="bold",
        label="bold bravery",
        fear_need=4,
        resolve_gain=3,
        tags={"bravery"},
    ),
}

YOUNG_NAMES = ["Mira", "Tomas", "Elin", "Niko", "Sela", "Aron", "Lina", "Pavel"]
OLDER_NAMES = ["Grandmother Rowan", "Old Marek", "Aunt Iva", "Grandfather Birch"]


@dataclass
class StoryParams:
    setting: str
    arrow: str
    transformation: str
    bravery: str
    hero: str
    elder: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in [SETTING.id]:
        for a in ARROWS:
            for t in TRANSFORMATIONS:
                if a == "ash" and t == "lantern_tree":
                    combos.append((s, a, t))
                if a == "birch" and t == "seed_charm":
                    combos.append((s, a, t))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting != SETTING.id:
        raise StoryError("This tale only knows the hill village.")
    if params.arrow not in ARROWS:
        raise StoryError("Unknown arrow kind.")
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError("Unknown transformation.")
    if params.bravery not in BRAVERY:
        raise StoryError("Unknown bravery choice.")
    if params.arrow == "ash" and params.transformation != "lantern_tree":
        raise StoryError("That arrow can only become a lantern-tree tale.")
    if params.arrow == "birch" and params.transformation != "seed_charm":
        raise StoryError("That arrow can only become a charm tale.")


def _apply_fire(world: World, arrow: Entity, tree: Entity, tfm: Transformation) -> None:
    sig = ("transform", arrow.id, tree.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    arrow.meters["shining"] += 1
    tree.meters["transformed"] += 1
    tree.label = tfm.result_label
    tree.tags.add("changed")
    world.get("path").meters["open"] += tfm.power
    world.get("hero").memes["wonder"] += 1
    world.get("hero").memes["bravery"] += 1


def propagate(world: World, narrate: bool = True) -> None:
    if world.get("arrow").meters["loosed"] >= THRESHOLD and world.get("sprout").meters["hidden"] >= THRESHOLD:
        _apply_fire(world, world.get("arrow"), world.get("sprout"), TRANSFORMATIONS[world.facts["transformation"]])


def _setup(world: World, hero_name: str, elder_name: str, arrow_kind: ArrowKind, bravery: BraveryChoice, tfm: Transformation) -> None:
    hero = world.add(Entity(id="hero", kind="character", type="boy" if hero_name in {"Tomas", "Niko", "Aron", "Pavel"} else "girl", label=hero_name, role="hero"))
    elder = world.add(Entity(id="elder", kind="character", type="woodsman", label=elder_name, role="elder"))
    arrow = world.add(Entity(id="arrow", label=arrow_kind.label, material=arrow_kind.wood, tags=set(arrow_kind.tags)))
    sprout = world.add(Entity(id="sprout", label="willow sprout", tags={"plant", "hidden"}))
    path = world.add(Entity(id="path", label="hill path", tags={"path"}))
    cave = world.add(Entity(id="cave", label=SETTING.dark_place, tags={"dark"}))
    hero.memes["fear"] = float(bravery.fear_need)
    hero.memes["trust"] = 1.0
    elder.memes["trust"] = 2.0
    arrow.meters["carried"] = 1.0
    sprout.meters["hidden"] = 1.0
    cave.meters["dark"] = 1.0
    world.facts.update(setting=SETTING.id, transformation=tfm.id, bravery=bravery.id)


def tell(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    elder = world.get("elder")
    arrow = world.get("arrow")
    sprout = world.get("sprout")
    path = world.get("path")
    tfm = TRANSFORMATIONS[params.transformation]
    brave = BRAVERY[params.bravery]
    kind = ARROWS[params.arrow]

    world.say(f"In {SETTING.place}, {hero.label} met {elder.label_word} beside the old ash fence.")
    world.say(f"{elder.label_word} showed {hero.label} an arrow and said, '{kind.song}'")
    world.say(f"The child felt {SETTING.mood}, but the village needed {SETTING.village_need}.")
    world.para()
    hero.memes["fear"] += brave.fear_need
    hero.memes["resolve"] += brave.resolve_gain
    world.say(f"{hero.label} looked toward {SETTING.dark_place} where a shy willow sprout waited in the dark.")
    world.say(f'"If I am brave," {hero.label} whispered, "I will not run from the hill."')
    arrow.meters["loosed"] += 1
    world.say(f"{hero.label} drew the bow and loosed the {kind.label}.")
    propagate(world)
    world.para()
    if sprout.meters["transformed"] >= THRESHOLD:
        world.say(f"The arrow struck the hidden sprout, and the sprout changed into a {tfm.result_label}.")
        world.say(f"Warm light rose from its leaves and showed {tfm.result_use}.")
        world.say(f"{hero.label} stood taller, brave enough to lead the villagers by the new glow.")
        world.say(f"The old arrow was no longer only wood and tip; it became a {kind.transform_to} kept at the elder's belt.")
    else:
        world.say(f"The arrow vanished into the hill, and the cave kept its secret.")
        world.say(f"But {hero.label} did not turn away; {hero.pronoun()} waited and listened until courage returned.")
        world.say(f"At last, the child found the hidden sprout and named the hill path by heart.")
    world.para()
    world.say(f"By evening, {path.label_word} was open and the village could cross without fear.")
    world.say(f"{hero.label} carried home a simple charm, and the folk told the tale to every child who needed a brave heart.")

    world.facts.update(hero=hero, elder=elder, arrow=arrow, sprout=sprout, path=path, kind=kind, tfm=tfm)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child that includes the word "arrow" and shows bravery leading to a transformation.',
        f"Tell a story where {f['hero'].label} uses an arrow near a hidden thing and something changes into a bright helper.",
        f"Write a gentle folk tale about courage, an arrow, and a magical change that helps a village."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, elder, arrow, sprout, path, kind, tfm = f["hero"], f["elder"], f["arrow"], f["sprout"], f["path"], f["kind"], f["tfm"]
    return [
        ("Who was the story about?", f"It was about {hero.label} and {elder.label_word}, with an enchanted {kind.label} at the center of the tale."),
        ("What did the child do that showed bravery?", f"{hero.label} chose to loose the arrow toward the dark hill instead of backing away. That brave choice let the hidden sprout change and helped the village."),
        ("What changed in the story?", f"The willow sprout transformed into a {tfm.result_label}, and the hill path opened. The old arrow also became a small charm to remember the brave moment."),
        ("Why was the ending good for the village?", f"The new {tfm.result_label} gave light and guidance through the hill. Because of that, people could cross safely instead of fearing the dark cave."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an arrow?", "An arrow is a thin shaft made to fly from a bow. People use it to shoot straight toward a target."),
        ("What is bravery?", "Bravery is choosing to do a hard thing even when you feel scared. A brave person keeps going and does the needed thing anyway."),
        ("What does transformation mean?", "Transformation means something changes into something else. In stories, a plain thing can become something magical or useful."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", SETTING.id)]
    for aid in ARROWS:
        lines.append(asp.fact("arrow", aid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for bid in BRAVERY:
        lines.append(asp.fact("bravery", bid))
    lines.append(asp.fact("compatible", "ash", "lantern_tree"))
    lines.append(asp.fact("compatible", "birch", "seed_charm"))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(A, T) :- arrow(A), transformation(T), compat(A, T).
valid(S, A, T, B) :- setting(S), arrow(A), transformation(T), bravery(B), compatible(A, T).
brave(B) :- bravery(B).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for a in ARROWS:
        for t in TRANSFORMATIONS:
            if (a == "ash" and t == "lantern_tree") or (a == "birch" and t == "seed_charm"):
                for b in BRAVERY:
                    out.append((SETTING.id, a, t, b))
    return out


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("Mismatch between ASP and Python combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, arrow=None, transformation=None, bravery=None, hero=None, elder=None, seed=None), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"Generation smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about arrow, bravery, and transformation.")
    ap.add_argument("--setting", choices=[SETTING.id])
    ap.add_argument("--arrow", choices=list(ARROWS))
    ap.add_argument("--transformation", choices=list(TRANSFORMATIONS))
    ap.add_argument("--bravery", choices=list(BRAVERY))
    ap.add_argument("--hero")
    ap.add_argument("--elder")
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
    setting = args.setting or SETTING.id
    arrow = args.arrow or rng.choice(list(ARROWS))
    if arrow == "ash":
        transformation = args.transformation or "lantern_tree"
    elif arrow == "birch":
        transformation = args.transformation or "seed_charm"
    else:
        transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    bravery = args.bravery or rng.choice(list(BRAVERY))
    reasonableness_gate(StoryParams(setting=setting, arrow=arrow, transformation=transformation, bravery=bravery, hero="", elder=""))
    hero = args.hero or rng.choice(YOUNG_NAMES)
    elder = args.elder or rng.choice(OLDER_NAMES)
    return StoryParams(setting=setting, arrow=arrow, transformation=transformation, bravery=bravery, hero=hero, elder=elder)


def generate(params: StoryParams) -> StorySample:
    if params.arrow not in ARROWS:
        raise StoryError("Invalid arrow selection.")
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError("Invalid transformation selection.")
    if params.bravery not in BRAVERY:
        raise StoryError("Invalid bravery selection.")
    reasonableness_gate(params)
    world = World()
    _setup(world, params.hero, params.elder, ARROWS[params.arrow], BRAVERY[params.bravery], TRANSFORMATIONS[params.transformation])
    tell(world, params)
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


CURATED = [
    StoryParams(setting=SETTING.id, arrow="ash", transformation="lantern_tree", bravery="steady", hero="Mira", elder="Grandmother Rowan", seed=11),
    StoryParams(setting=SETTING.id, arrow="birch", transformation="seed_charm", bravery="bold", hero="Tomas", elder="Old Marek", seed=12),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4.\n#show brave/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible stories:")
        for row in valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as exc:
                print(exc)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
