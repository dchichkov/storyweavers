#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/moan_zest_drool_bravery_suspense_bedtime_story.py
==================================================================================

A standalone tiny storyworld for a bedtime tale about a child, a sleepy little
creature, and a moonlit question of bravery.

Seed words: moan, zest, drool
Features: Bravery, Suspense
Style: Bedtime Story

The world models one small domain:
- a child hears a strange bedtime noise,
- suspense grows as they decide whether to investigate,
- they find a sleepy creature with a leaky snack,
- bravery turns fear into a gentle fix,
- the ending settles into a calm bedtime image.

The story variations are constraint-checked so they stay plausible and complete.
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
SUSPENSE_START = 1.0
BRAVERY_START = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Snack:
    id: str
    label: str
    phrase: str
    zest: bool = False
    drooly: bool = False

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
class Creature:
    id: str
    label: str
    moans: bool = True
    drools: bool = True
    sleepy: bool = True

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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_moan_to_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["suspense"] >= THRESHOLD:
        sig = ("suspense",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["bravery"] += 1
        out.append("__suspense__")
    return out


def _r_brave_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    creature = world.entities.get("creature")
    snack = world.entities.get("snack")
    if not child or not creature or not snack:
        return out
    if child.memes["bravery"] < THRESHOLD:
        return out
    if creature.meters["moaning"] < THRESHOLD or snack.meters["sticky"] < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["relief"] += 1
    snack.meters["mess"] = 0
    out.append("__fix__")
    return out


CAUSAL_RULES = [
    Rule("moan_to_suspense", "social", _r_moan_to_suspense),
    Rule("brave_fix", "physical", _r_brave_fix),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(creature: Creature, snack: Snack) -> bool:
    return creature.moans and creature.drools and snack.zest and snack.drooly


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for creature_id, creature in CREATURES.items():
            for snack_id, snack in SNACKS.items():
                if reasonableness_gate(creature, snack):
                    combos.append((setting, creature_id, snack_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    creature: str
    snack: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


SETTINGS = {
    "moonlit_room": {
        "label": "a moonlit room",
        "intro": "The room was quiet, with silver moonlight on the quilt and a soft lamp by the bed.",
        "ending": "The quilt stayed warm, the lamp stayed low, and the room felt sleepy again.",
    },
    "nursery": {
        "label": "a cozy nursery",
        "intro": "The nursery was cozy, with a teddy on the shelf and a little star above the crib.",
        "ending": "The teddy watched over the room, and the nursery drifted back toward sleep.",
    },
    "attic_nest": {
        "label": "a little attic nest",
        "intro": "The attic nest was tucked under the roof, with pillows piled high and the moon making pale squares on the floor.",
        "ending": "The pillows stayed piled high, and the attic nest settled into hush and moonshine.",
    },
}

CREATURES = {
    "puff": Creature("puff", "a sleepy puffcat"),
    "murmur": Creature("murmur", "a drowsy mouse"),
    "bloom": Creature("bloom", "a tiny porch-fox"),
}

SNACKS = {
    "citrus_biscuit": Snack("citrus_biscuit", "citrus biscuit", "a crumbly citrus biscuit with a bright zest", zest=True, drooly=True),
    "orange_cake": Snack("orange_cake", "orange cake", "a soft orange cake slice with zest frosting", zest=True, drooly=True),
    "honey_roll": Snack("honey_roll", "honey roll", "a honey roll that had a little zest on the glaze", zest=True, drooly=True),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Leo", "Theo", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny bedtime storyworld with moan, zest, drool, bravery, and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("creature", cid) for cid in CREATURES]
    lines += [asp.fact("snack", sid) for sid in SNACKS]
    lines += [asp.fact("moans", cid) for cid, c in CREATURES.items() if c.moans]
    lines += [asp.fact("drools", cid) for cid, c in CREATURES.items() if c.drools]
    lines += [asp.fact("zesty", sid) for sid, s in SNACKS.items() if s.zest]
    lines += [asp.fact("sticky", sid) for sid, s in SNACKS.items() if s.drooly]
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,C,SN) :- setting(S), creature(C), snack(SN), moans(C), drools(C), zesty(SN), sticky(SN).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: empty story")
        rc = 1
    else:
        print("OK: smoke story generation succeeded.")
    return rc


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.creature is None or c[1] == args.creature)
              and (args.snack is None or c[2] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, creature, snack = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        creature=creature,
        snack=snack,
        child_name=args.child_name or _pick_name(rng, child_gender),
        child_gender=child_gender,
        helper_name=args.helper_name or _pick_name(rng, helper_gender),
        helper_gender=helper_gender,
    )


def predict(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["suspense"] += 1
    propagate(sim, narrate=False)
    return {"bravery": sim.get("child").memes["bravery"], "relief": sim.get("creature").memes["relief"]}


def tell(setting_id: str, creature_id: str, snack_id: str, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World()
    setting = SETTINGS[setting_id]
    creature = CREATURES[creature_id]
    snack = SNACKS[snack_id]
    child = world.add(Entity("child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity("helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    c = world.add(Entity("creature", kind="character", type="thing", label=creature.label, role="creature"))
    s = world.add(Entity("snack", kind="thing", type="thing", label=snack.label, role="snack"))

    child.memes["bravery"] = BRAVERY_START
    child.memes["suspense"] = SUSPENSE_START
    c.meters["moaning"] = 1
    s.meters["sticky"] = 1
    s.meters["zest"] = 1

    world.say(f"At bedtime, {child_name} was tucked into {setting['label']}. {setting['intro']}")
    world.say(f"Then came a soft moan from the dark corner, and the air had a little zest of orange on it.")
    world.para()
    child.memes["suspense"] += 1
    world.say(f"{child_name} listened under the blanket and felt the suspense grow. {child_name} wondered if the sound was a monster, or only a sleepy friend.")
    pred = predict(world)
    world.facts["pred"] = pred
    world.say(f"{child_name} took one brave breath and looked toward the sound.")
    if child.memes["bravery"] >= THRESHOLD:
        world.say(f"{helper_name} stayed by the door, ready with a soft word, while {child_name} tiptoed closer.")
        world.say(f"There on a cushion was {creature.label}, drooling beside {snack.phrase}, with one tiny moan between sleepy blinks.")
        world.say(f"{child_name} did not run. {child_name} smiled, picked up a napkin, and wiped the drool from the spoon.")
        propagate(world, narrate=True)
        world.para()
        world.say(f"After that, the room felt safe again. {setting['ending']}")
        world.say(f"{child_name} and {helper_name} tucked {creature.label} in beside the pillow, and the little moan turned into a yawn.")
    world.facts.update(child=child, helper=helper, creature=c, snack=s, setting=setting, creature_id=creature_id, snack_id=snack_id, setting_id=setting_id)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story for a young child that includes the words moan, zest, and drool.",
        f"Tell a gentle suspense story where {f['child'].label} hears a moan at bedtime and finds {f['creature'].label} near {f['snack'].label}.",
        f"Write a calm bedtime tale with bravery and suspense, ending with a cozy room and a sleepy friend.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    creature = f["creature"]
    snack = f["snack"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?", f"It is about {child.label} and {helper.label}, who were getting ready for bed in {setting['label']}."),
        ("What strange sound did {0} hear?".format(child.label), f"{child.label} heard a soft moan from the dark corner. That sound made the room feel suspenseful at first."),
        ("What did {0} find?".format(child.label), f"{child.label} found {creature.label} drooling beside {snack.phrase}. The creature was sleepy, not scary, and the snack had a bright zest smell."),
        ("How did the problem get solved?", f"{child.label} bravely wiped the drool from the spoon and stayed calm. That gentle action helped everyone settle down for bed."),
        ("How did the story end?", f"It ended with a cozy room, a sleepy friend, and {setting['ending'].lower()}"),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is moaning?", "Moaning is a soft, low sound people or animals make when they are sleepy, unhappy, or uncomfortable."),
        ("What is zest?", "Zest is the bright outer part of a citrus fruit, and it smells fresh and lively."),
        ("What is drool?", "Drool is spit that slips out of a mouth, often when someone is very sleepy."),
        ("What does bravery mean?", "Bravery means doing the right thing even when something feels a little scary."),
        ("What does suspense mean?", "Suspense is the feeling of wondering what will happen next."),
    ]


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moonlit_room", "puff", "citrus_biscuit", "Mia", "girl", "Noah", "boy"),
    StoryParams("nursery", "murmur", "orange_cake", "Leo", "boy", "Ava", "girl"),
    StoryParams("attic_nest", "bloom", "honey_roll", "Nora", "girl", "Eli", "boy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.creature, params.snack, params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        hdr = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
