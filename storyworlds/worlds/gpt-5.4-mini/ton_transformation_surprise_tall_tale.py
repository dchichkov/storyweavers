#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ton_transformation_surprise_tall_tale.py
========================================================================

A tiny standalone storyworld for a tall-tale-style transformation surprise.

Seed idea
---------
A child finds a huge "ton" of ordinary, heavy stuff and expects a boring chore.
Then, with a surprise twist, the pile transforms into something wondrous and
useful. The story should feel oversized, a little playful, and complete.

This world keeps the simulation small:
- typed entities with physical meters and emotional memes,
- a state-driven causal turn,
- a transformation beat,
- a surprise beat,
- a tall-tale ending image proving what changed.

It supports the shared Storyweavers contract:
- build_parser, resolve_params, generate, emit, main
- --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- eager import of storyworlds/results.py
- inline ASP twin and Python reasonableness gate
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
    traits: list[str] = field(default_factory=list)
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
    affordance: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Ton:
    id: str
    label: str
    phrase: str
    mass: int
    surprise: str
    transform_into: str
    transformed_label: str
    transformed_phrase: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Trigger:
    id: str
    label: str
    cue: str
    kind: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    pile = world.get("pile")
    if pile.meters["waiting"] < THRESHOLD:
        return out
    sig = ("surprise", pile.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pile.memes["wonder"] += 1
    out.append("__surprise__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    pile = world.get("pile")
    if pile.memes["wonder"] < THRESHOLD:
        return out
    sig = ("transform", pile.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pile.meters["changed"] = 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("surprise", "social", _r_surprise), Rule("transform", "physical", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def reasonableness_gate(tale: Ton, trigger: Trigger) -> bool:
    return tale.mass >= 1 and trigger.kind == "surprise"


def surprise_predict(world: World) -> bool:
    sim = world.copy()
    sim.get("pile").meters["waiting"] += 1
    propagate(sim, narrate=False)
    return sim.get("pile").meters["changed"] >= THRESHOLD


def setup(world: World, child: Entity, grownup: Entity, setting: Setting, ton: Ton) -> None:
    child.memes["curiosity"] += 1
    grownup.memes["calm"] += 1
    world.say(
        f"On a bright morning at {setting.place}, {child.id} and {grownup.id} found "
        f"{ton.phrase}. The whole thing looked about as heavy as {ton.label}."
    )
    world.say(
        f"{child.id} blinked at the sky. {setting.sky.capitalize()} over the yard, "
        f"and the ordinary pile waited under it like a sleepy hill."
    )


def tension(world: World, child: Entity, ton: Ton, trigger: Trigger) -> None:
    world.say(
        f"{child.id} expected a boring job. {child.pronoun().capitalize()} thought the "
        f"{ton.label} would just sit there and never budge."
    )
    world.say(
        f"Then came a surprise: {trigger.cue}. The air shivered, and the pile grew "
        f"so eager that even the fence seemed to lean closer."
    )


def awaken(world: World) -> None:
    pile = world.get("pile")
    pile.meters["waiting"] += 1
    propagate(world, narrate=False)


def transform(world: World, ton: Ton, child: Entity) -> None:
    pile = world.get("pile")
    pile.memes["wonder"] += 1
    pile.label = ton.transformed_label
    world.say(
        f"In that instant, the {ton.label} changed its mind and transformed into "
        f"{ton.transformed_phrase}. It rose up {ton.transform_into}, bright enough "
        f"to make {child.id} laugh out loud."
    )


def ending(world: World, child: Entity, grownup: Entity, ton: Ton) -> None:
    child.memes["joy"] += 1
    grownup.memes["pride"] += 1
    world.say(
        f'{grownup.id} clapped once, slow and pleased. "{child.id}, you were patient '
        f'enough to see it happen," {grownup.pronoun()} said.'
    )
    world.say(
        f"{child.id} reached up and touched the new shape. It no longer looked like "
        f"a ton of trouble; it looked like a giant, golden gift ready for the road."
    )
    world.say(
        f"So the two of them rolled away under {world.setting.sky}, following the tall "
        f"shadow of the transformed thing as if it were the biggest surprise in the county."
    )


def tell(setting: Setting, ton: Ton, trigger: Trigger, child_name: str, child_gender: str,
         grownup_name: str, grownup_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(child_name, kind="character", type=child_gender))
    grownup = world.add(Entity(grownup_name, kind="character", type=grownup_gender))
    pile = world.add(Entity("pile", label=ton.label, type="thing"))
    pile.meters["waiting"] = 0.0

    setup(world, child, grownup, setting, ton)
    world.para()
    tension(world, child, ton, trigger)

    if not reasonableness_gate(ton, trigger):
        raise StoryError("This tale needs a real surprise that can start the transformation.")

    if surprise_predict(world):
        awaken(world)
        world.para()
        transform(world, ton, child)
        ending(world, child, grownup, ton)
    else:
        raise StoryError("The transformation would not happen in this world.")

    world.facts.update(
        child=child, grownup=grownup, ton=ton, trigger=trigger, setting=setting,
        transformed=pile.meters["changed"] >= THRESHOLD
    )
    return world


SETTINGS = {
    "farm": Setting("farm", "the old farm", "the sun was big as a wagon wheel", "yard"),
    "harbor": Setting("harbor", "the river harbor", "the clouds marched like white geese", "dock"),
    "prairie": Setting("prairie", "the wide prairie", "the wind sang like a fiddle", "field"),
}

TONS = {
    "hay": Ton("hay", "a ton of hay", "a ton of hay", mass=1, surprise="a sudden breeze",
               transform_into="into a towering kite", transformed_label="kite",
               transformed_phrase="a giant kite made of gold and sky", tags={"hay", "transform"}),
    "beans": Ton("beans", "a ton of beans", "a ton of beans", mass=1, surprise="a crack of thunder",
                 transform_into="into a shiny train", transformed_label="train",
                 transformed_phrase="a shiny train with brass sides", tags={"beans", "transform"}),
    "buttons": Ton("buttons", "a ton of buttons", "a ton of buttons", mass=1, surprise="a flash of moonlight",
                   transform_into="into a riverboat balloon", transformed_label="balloon",
                   transformed_phrase="a riverboat balloon bigger than a barn", tags={"buttons", "transform"}),
}

TRIGGERS = {
    "breeze": Trigger("breeze", "breeze", "a sudden breeze slipped through the yard", "surprise", tags={"surprise"}),
    "thunder": Trigger("thunder", "thunder", "a crack of thunder rolled across the sky", "surprise", tags={"surprise"}),
    "moonlight": Trigger("moonlight", "moonlight", "a flash of moonlight landed right on the pile", "surprise", tags={"surprise"}),
}

GIRL_NAMES = ["Mabel", "Ruby", "Clara", "Nell", "June", "Annie"]
BOY_NAMES = ["Hank", "Otis", "Bert", "Jesse", "Walt", "Tom"]
GROWNUP_NAMES = ["Grandma", "Grandpa", "Aunt May", "Uncle Joe"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    ton: str
    trigger: str
    child_name: str
    child_gender: str
    grownup_name: str
    grownup_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    return [(s, t, g) for s in SETTINGS for t in TONS for g in TRIGGERS if reasonableness_gate(TONS[t], TRIGGERS[g])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a ton and a surprise transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ton", choices=TONS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-gender", choices=["mother", "father", "woman", "man"])
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
              and (args.ton is None or c[1] == args.ton)
              and (args.trigger is None or c[2] == args.trigger)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ton, trigger = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    ggender = args.grownup_gender or rng.choice(["mother", "father"])
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    return StoryParams(setting, ton, trigger, name, gender, grownup, ggender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TONS[params.ton], TRIGGERS[params.trigger],
                 params.child_name, params.child_gender, params.grownup_name, params.grownup_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child that includes the words "{f["ton"].label}" and "surprise".',
        f"Tell a fanciful story where {f['child'].id} finds {f['ton'].phrase} and a surprise makes it transform into something huge.",
        f"Write a story with an enormous transformation ending, using the word ton and a happy, astonished mood.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    ton = f["ton"]
    child = f["child"]
    grownup = f["grownup"]
    return [
        ("What did the child find?",
         f"{child.id} found {ton.phrase}, which looked as heavy as a ton of work."),
        ("What caused the change?",
         f"A surprise cue started the change. The strange little moment made the pile wake up and transform."),
        ("How did the story end?",
         f"It ended with the pile transformed into {ton.transformed_phrase}, and {grownup.id} smiling beside {child.id}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    ton = f["ton"]
    return [
        ("What does the word ton mean?",
         "A ton is a very large amount or a very heavy weight. People use it to mean something huge."),
        ("What is a surprise?",
         "A surprise is something unexpected. It happens when you do not know it is coming."),
        ("What is a transformation?",
         "A transformation is a change from one form into another. Something transformed does not stay the same."),
    ] + [(f"Why does this story fit the word {ton.label}?", f"It uses {ton.phrase}, so the story keeps the big, heavy feeling of a ton.")]
   


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, _ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
surprise(P) :- waiting(P), trigger(T), cue(T).
transform(P) :- surprise(P), wonder(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TONS.items():
        lines.append(asp.fact("ton", tid))
        lines.append(asp.fact("mass", tid, t.mass))
    for gid in TRIGGERS:
        lines.append(asp.fact("trigger", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        print("OK: generate smoke test passed.")
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"FAIL: generate smoke test crashed: {e}")
    return rc


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
    StoryParams("farm", "hay", "breeze", "Mabel", "girl", "Grandpa", "man"),
    StoryParams("harbor", "beans", "thunder", "Hank", "boy", "Grandma", "woman"),
    StoryParams("prairie", "buttons", "moonlight", "Ruby", "girl", "Aunt May", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combos:")
        for c in valid_combos():
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
