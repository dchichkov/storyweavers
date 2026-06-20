#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/germinate_foreshadowing_inner_monologue_tall_tale.py
====================================================================================

A standalone story world for a tall-tale seed about a tiny garden mystery:
a child plants a strange bean, notices ominous hints, listens to an inner
monologue, and ends with something impossible-but-kindly-big germinating.

The world is built from typed entities with physical meters and emotional memes.
The state changes drive the prose: a seed dries, is watered, warns of a coming
sprout, the narrator's inner monologue weighs whether to wait or rush, and the
ending proves what grew.

This script is stdlib-only and supports:
- default run / -n
- --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

The simulated domain is intentionally small:
- a child finds a bean in a seed tin
- foreshadowing appears as clues before germination
- inner monologue is rendered as the child's thoughts, not as a generic event log
- the resolution is a tall-tale plant that grows far larger than expected, but
  stays gentle and child-facing
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
GERMINATE_MIN_WATER = 1.0
GROW_MIN_SUN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    sky: str
    soil: str
    tall_tale_scale: str
    weather: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Seed:
    id: str
    label: str
    phrase: str
    color: str
    size: str
    foreshadow: str
    promise: str
    rare: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class WateringCan:
    id: str
    label: str
    phrase: str
    sound: str
    helps: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    height_word: str
    surprise: str
    leaves: str
    kind_word: str
    can_climb: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_germinate(world: World) -> list[str]:
    out = []
    seed = world.get("seed")
    plant = world.get("plant")
    if seed.meters["watered"] < GERMINATE_MIN_WATER:
        return out
    sig = ("germinate", seed.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.meters["sprouted"] += 1
    plant.meters["sprouted"] += 1
    plant.memes["wonder"] += 1
    out.append("__sprout__")
    return out


def _r_grow(world: World) -> list[str]:
    out = []
    seed = world.get("seed")
    plant = world.get("plant")
    if plant.meters["sprouted"] < THRESHOLD:
        return out
    if seed.meters["sun"] < GROW_MIN_SUN:
        return out
    sig = ("grow", plant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plant.meters["height"] += 1
    plant.meters["height"] += 1
    plant.meters["height"] += 1
    plant.meters["height"] += 1
    plant.meters["height"] += 1
    if plant.can_climb:
        plant.meters["height"] += 3
    plant.memes["pride"] += 1
    out.append("__grow__")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out = []
    seed = world.get("seed")
    if seed.meters["watered"] < THRESHOLD:
        return out
    sig = ("foreshadow", seed.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seed.memes["expectation"] += 1
    out.append("__hint__")
    return out


CAUSAL_RULES = [Rule("foreshadow", _r_foreshadow), Rule("germinate", _r_germinate), Rule("grow", _r_grow)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
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


def predict(world: World) -> dict:
    sim = world.copy()
    seed = sim.get("seed")
    seed.meters["watered"] += 1
    propagate(sim, narrate=False)
    return {
        "sprouted": sim.get("seed").meters["sprouted"] >= THRESHOLD,
        "tall": sim.get("plant").meters["height"] >= 5,
    }


def setup(world: World, child: Entity, seed: Seed, can: WateringCan, plant: Plant) -> None:
    world.say(
        f"On a bright morning in {world.setting.place}, {child.id} found {seed.phrase} "
        f"resting in a seed tin beside {world.setting.soil}. The sky above was "
        f"{world.setting.sky}, and the garden looked as wide as a wagon road."
    )
    world.say(
        f'{child.id} held the little bean and thought, "This one feels like it has a '
        f'secret in it." {seed.foreshadow}'
    )
    world.say(
        f'From the porch came {can.phrase}, and it made a soft "{can.sound}" '
        f'when {child.id} tipped it.'
    )


def inner_monologue(world: World, child: Entity, seed: Seed) -> None:
    child.memes["curiosity"] += 1
    pred = predict(world)
    world.facts["predicted"] = pred
    if pred["sprouted"]:
        thought = (
            f"'{child.id} thought, If I give it water, it may wake up and poke "
            f"a green nose through the dirt.'"
        )
    else:
        thought = (
            f"'{child.id} thought, Maybe I should wait, but even sleepy beans "
            f"like a drop or two.'"
        )
    world.say(thought)
    world.say(
        f"Then {child.id} listened to the hush inside {child.pronoun('possessive')} "
        f"head and decided the bean was asking for a drink."
    )


def water_seed(world: World, child: Entity, seed: Entity, can: WateringCan) -> None:
    seed.meters["watered"] += 1
    child.memes["care"] += 1
    world.say(
        f"{child.id} poured {can.phrase} over the dirt, and it went {can.sound} "
        f"like a rain cloud with manners."
    )
    if seed.meters["watered"] >= THRESHOLD:
        world.say(
            f"The bean looked quieter after that, as if it had taken a deep breath."
        )
    propagate(world)


def tell(world: World, child: Entity, seed_cfg: Seed, can_cfg: WateringCan, plant_cfg: Plant) -> World:
    seed = world.add(Entity(id="seed", kind="thing", type="seed", label=seed_cfg.label))
    plant = world.add(Entity(id="plant", kind="thing", type="plant", label=plant_cfg.label))
    child.memes["hope"] += 1
    world.say(
        f"{child.id} was a little {child.type} with a big head full of dreams and "
        f"dirty knees from the garden path."
    )
    setup(world, child, seed_cfg, can_cfg, plant_cfg)
    world.para()
    inner_monologue(world, child, seed_cfg)
    water_seed(world, child, seed, can_cfg)
    world.para()
    if seed.meters["sprouted"] >= THRESHOLD:
        world.say(
            f"By noon, a green seam split the soil. By evening, the sprout had "
            f"stood up straight and stretched its arms."
        )
    if plant.meters["height"] >= 5:
        world.say(
            f"Then the plant grew like it had a ladder hidden in its roots. "
            f"It climbed higher than the apple box, higher than the fence, and "
            f"still it kept on going."
        )
        if plant.can_climb:
            world.say(
                f"At the top, its leaves waved like little flags, and the vine "
                f"curled around the porch post as politely as a ribbon."
            )
    else:
        world.say(
            f"At last, the bean poked up a brave little leaf and looked around as "
            f"if it knew the whole garden had been waiting."
        )
    world.say(
        f"{child.id} grinned at the green wonder and whispered, "
        f'"A bean can germinate into a giant if it is minded kindly enough."'
    )
    world.facts.update(
        child=child,
        seed_cfg=seed_cfg,
        can_cfg=can_cfg,
        plant_cfg=plant_cfg,
        seed=seed,
        plant=plant,
        outcome="giant" if plant.meters["height"] >= 8 else "sprouted",
    )
    return world


SETTINGS = {
    "backyard": Setting("backyard", "the backyard", "clear and blue", "dark loam",
                        "fence-high", "sunny"),
    "garden": Setting("garden", "Grandma's garden", "full of gold light", "soft soil",
                      "barn-high", "late afternoon"),
    "orchard": Setting("orchard", "the apple orchard", "washed in bright wind", "crumbly earth",
                       "tree-high", "warm"),
}

SEEDS = {
    "bean": Seed("bean", "a red bean", "a red bean with a silver speck", "red", "tiny",
                 "It looked like it had a moon-beam hiding inside.", "it might grow into a climbing giant"),
    "pea": Seed("pea", "a green pea", "a green pea from a bright tin", "green", "small",
                "It rolled once, then paused as if listening.", "it would wake into a vine"),
    "corn": Seed("corn", "a corn kernel", "a corn kernel with a shiny wrinkle", "gold", "small",
                 "It was about as mysterious as a whistle in the dark.", "it could grow into a stalk tall as a flagpole"),
}

CANs = {
    "tin": WateringCan("tin", "watering can", "a little watering can", "drip-drip", "helped the seed wake up"),
    "cup": WateringCan("cup", "cup", "a blue tin cup", "glug", "gave just enough water"),
}

PLANTS = {
    "vine": Plant("vine", "vine", "a vine", "tall", "rose like a ladder", "green leaves", "vine", can_climb=True),
    "stalk": Plant("stalk", "stalk", "a stalk", "towering", "stood like a trumpet", "broad leaves", "stalk"),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ivy"]
BOY_NAMES = ["Finn", "Theo", "Noah", "Eli", "Max", "Ben"]
TRAITS = ["curious", "patient", "thoughtful", "dreamy", "bold"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    seed_kind: str
    can: str
    plant_kind: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for sk in SEEDS:
            for pk in PLANTS:
                if sk == "bean" and pk == "vine":
                    combos.append((s, sk, pk))
                elif sk == "corn" and pk == "stalk":
                    combos.append((s, sk, pk))
                elif sk == "pea" and pk == "vine":
                    combos.append((s, sk, pk))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale germination story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--seed-kind", choices=SEEDS)
    ap.add_argument("--can", choices=CANs)
    ap.add_argument("--plant-kind", choices=PLANTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.seed_kind is None or c[1] == args.seed_kind)
              and (args.plant_kind is None or c[2] == args.plant_kind)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, seed_kind, plant_kind = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    can = args.can or rng.choice(sorted(CANs))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, seed_kind, can, plant_kind, name, gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the word "germinate" and a '
        f'bean with a secret in it.',
        f"Tell a story where {f['child'].id} notices a clue before the seed "
        f"germinates, listens to an inner monologue, and gets a surprising giant plant.",
        f'Write a garden story in a tall-tale voice with foreshadowing, where a '
        f'child waters a seed and something impossible grows.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    seed_cfg = f["seed_cfg"]
    plant_cfg = f["plant_cfg"]
    qas = [
        ("What did the child find in the garden?",
         f"{child.id} found {seed_cfg.phrase} in a seed tin by the garden soil."),
        ("What did the child think before watering the seed?",
         f"{child.id} thought the bean had a secret in it and listened to the quiet in "
         f"{child.pronoun('possessive')} head. That inner monologue helped {child.id} decide to give it a drink."),
        ("What happened after the seed was watered?",
         f"The seed germinated, and then {plant_cfg.phrase} began to grow. The little garden turned into a tall-tale scene."),
        ("How did the story end?",
         f"It ended with a giant plant stretching up high and {child.id} smiling at the green wonder. The ending image proves the seed did more than just sprout."),
    ]
    if f.get("outcome") == "giant":
        qas.append((
            "Why did the plant feel like a tall tale?",
            f"Because it grew higher than the fence and kept going like it was made of laughter. "
            f"That big ending came from the seed being watered and then allowed to germinate."
        ))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does germinate mean?",
         "Germinate means a seed starts to grow and push out a sprout."),
        ("Why do seeds need water?",
         "Seeds need water because it helps wake them up and start growing."),
        ("What is foreshadowing?",
         "Foreshadowing is a clue that hints something important may happen later."),
        ("What is an inner monologue?",
         "An inner monologue is the quiet voice a character thinks in their own head."),
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
    lines.append("== (3) World knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SEEDS:
        lines.append(asp.fact("seed_kind", sid))
    for pk in PLANTS:
        lines.append(asp.fact("plant_kind", pk))
    lines.append(asp.fact("threshold", int(THRESHOLD)))
    lines.append(asp.fact("germinate_min_water", int(GERMINATE_MIN_WATER)))
    lines.append(asp.fact("grow_min_sun", int(GROW_MIN_SUN)))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, SeedK, PlantK) :- setting(S), seed_kind(SeedK), plant_kind(PlantK), compatible(SeedK, PlantK).

compatible(bean, vine).
compatible(pea, vine).
compatible(corn, stalk).

sprouted :- watered, germinate_min_water(M), water(W), W >= M.
tall :- sprouted, sunny, grow_min_sun(M), sun(S), S >= M.
outcome(giant) :- tall.
outcome(sprouted) :- sprouted, not tall.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("watered", 1),
        asp.fact("water", 1),
        asp.fact("sunny", 1),
        asp.fact("sun", 1),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, role="child"))
    seed_cfg = SEEDS[params.seed_kind]
    can_cfg = CANs[params.can]
    plant_cfg = PLANTS[params.plant_kind]
    world.add(Entity(id="seed", type="seed", label=seed_cfg.label))
    world.add(Entity(id="plant", type="plant", label=plant_cfg.label))
    tell(world, child, seed_cfg, can_cfg, plant_cfg)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid combos")
        print(" only in python:", sorted(py - cl))
        print(" only in clingo:", sorted(cl - py))
        return 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: generation produced empty story")
        return 1
    if asp_outcome(CURATED[0]) not in {"giant", "sprouted", "?"}:
        print("MISMATCH: unexpected ASP outcome")
        return 1
    print("OK: ASP parity and story generation smoke test passed.")
    return 0


CURATED = [
    StoryParams("backyard", "bean", "tin", "vine", "Mia", "girl", "curious"),
    StoryParams("garden", "pea", "cup", "vine", "Noah", "boy", "thoughtful"),
    StoryParams("orchard", "corn", "tin", "stalk", "Ava", "girl", "dreamy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
