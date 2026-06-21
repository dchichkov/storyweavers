#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ravioli_audit_dale_problem_solving_cautionary_magic.py
======================================================================================

A small, standalone story world for a tiny mystery domain: a child named Dale,
a missing bowl of ravioli, and an audit of the pantry clues. The story keeps a
cautionary tone and includes a little magic, but the solution comes from careful
problem solving rather than from the spell alone.

The world is built around:
- a mystery setting with a kitchen, hallway, and pantry
- a missing ravioli dish
- an audit/checklist beat that reveals clues
- a cautious magic helper that can reveal what was hidden
- a child-sized resolution with a concrete ending image

It supports the standard Storyweavers CLI contract, including --verify and the
inline ASP twin.
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
MAGIC_MIN = 2
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    mood: str
    rooms: list[str]

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    hidden_in: str
    edible: bool = False
    mystery: bool = False

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
class MagicTool:
    id: str
    label: str
    phrase: str
    caution: str
    reveal: str
    sense: int
    power: int

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
    tag: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["missing"] >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            for ch in list(world.entities.values()):
                if ch.role in {"child", "adult"}:
                    ch.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_order(world: World) -> list[str]:
    out: list[str] = []
    if world.get("audit_sheet").meters["checked"] >= THRESHOLD and ("order",) not in world.fired:
        world.fired.add(("order",))
        world.get("audit_sheet").meters["clue"] += 1
        out.append("__order__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("order", "mystery", _r_order),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def cautious_magic_ok(tool: MagicTool) -> bool:
    return tool.sense >= MAGIC_MIN


def missing_with_reason(dish: Entity) -> bool:
    return dish.meters["missing"] >= THRESHOLD


def predict_clue(world: World, tool: MagicTool) -> dict:
    sim = world.copy()
    sim.get("magic_wand").meters["used"] += 1
    sim.get("ravioli_bowl").meters["revealed"] += tool.power
    return {
        "revealed": sim.get("ravioli_bowl").meters["revealed"] >= THRESHOLD,
        "worry": sim.get("dale").memes["worry"],
    }


def kitchen_open(world: World, setting: Setting, hero: Entity, dish: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"On a gray afternoon, {hero.id} stood in {setting.place}, where every room "
        f"felt a little too quiet. The air smelled faintly of tomato and cheese, but "
        f"the bowl of ravioli was nowhere to be seen."
    )
    world.say(
        f"{hero.id} looked from the counter to the sink and then to the pantry door. "
        f"Something small had gone missing, and that made the whole house feel like a mystery."
    )


def audit_begin(world: World, sheet: Entity, hero: Entity) -> None:
    sheet.meters["checked"] += 1
    world.say(
        f"{hero.id} found an audit sheet on the table with boxes to tick: counter, sink, "
        f"pantry, and floor. {hero.pronoun().capitalize()} knew a careful check was better "
        f"than guessing."
    )


def search(world: World, hero: Entity, obj: ObjectCfg, room: str) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} checked the {room} first, because clues often hide in plain sight."
    )
    if room == obj.hidden_in:
        world.get("ravioli_bowl").meters["missing"] = 0
        world.get("ravioli_bowl").meters["found"] += 1
        world.get("audit_sheet").meters["clue"] += 1
        world.say(
            f"Behind a stack of napkins, {hero.id} found the ravioli bowl tucked away like a secret."
        )
    else:
        world.say(f"The {room} was empty, neat, and not the place the clue was waiting.")


def warn_about_magic(world: World, hero: Entity, tool: MagicTool, adult: Entity) -> None:
    if not cautious_magic_ok(tool):
        raise StoryError("The magic tool is too wild for this story; it must be cautious magic.")
    world.say(
        f'{adult.id} gently warned, "{tool.caution} Magic is helpful, but it should never be used '
        f'carelessly around food or sharp corners."'
    )
    hero.memes["respect"] += 1


def use_magic(world: World, hero: Entity, tool: MagicTool, dish: Entity) -> None:
    world.get("magic_wand").meters["used"] += 1
    dish.meters["revealed"] += tool.power
    if dish.meters["revealed"] >= THRESHOLD:
        world.say(
            f"{hero.id} lifted the {tool.label} and spoke the tiniest spell. A soft shimmer floated "
            f"over the kitchen, and the hidden bowl seemed to glow where it was tucked away."
        )
    else:
        world.say(
            f"{hero.id} tried the {tool.label}, but the glow was too weak to help."
        )


def solve(world: World, hero: Entity, adult: Entity, dish: Entity, tool: MagicTool) -> None:
    world.say(
        f"{hero.id} did not trust the shimmer alone. {hero.id} used the audit sheet, retraced the "
        f"corners, and checked the pantry shelves one by one."
    )
    if missing_with_reason(dish):
        world.say(
            f"At last, the clue made sense: the ravioli had been moved to keep it warm, not lost for good."
        )
    world.say(
        f"{adult.label_word.capitalize()} smiled and said the best mystery was one solved with careful eyes, "
        f"a calm voice, and only a little magic."
    )


def ending(world: World, hero: Entity, adult: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"In the end, {hero.id} set the bowl on the table, the audit sheet got its final checkmark, "
        f"and the kitchen felt tidy again."
    )
    world.say(
        f"{adult.id} served the ravioli, and the little detective ate dinner under a warm lamp, happy "
        f"that the mystery had been solved the careful way."
    )


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "quiet", ["counter", "sink", "pantry", "floor"]),
    "backroom": Setting("backroom", "the backroom kitchen", "dim", ["counter", "pantry", "table"]),
    "cottage": Setting("cottage", "the cottage kitchen", "cozy", ["counter", "pantry", "window"]),
}

OBJECTS = {
    "ravioli": ObjectCfg("ravioli", "ravioli bowl", "the ravioli bowl", "pantry", edible=True, mystery=True),
    "audit": ObjectCfg("audit", "audit sheet", "the audit sheet", "table", mystery=True),
    "dale": ObjectCfg("dale", "Dale's note", "Dale's note", "counter", mystery=True),
}

MAGIC = {
    "lantern_spell": MagicTool(
        "lantern_spell",
        "lantern charm",
        "a lantern charm",
        "do not wave it near the stove",
        "reveals hidden things without touching them",
        2,
        2,
    ),
    "magnifier_spell": MagicTool(
        "magnifier_spell",
        "glimmer magnifier",
        "a glimmer magnifier",
        "keep it slow and steady",
        "makes hidden clues shine softly",
        3,
        3,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Ivy", "Lena", "June"]
BOY_NAMES = ["Dale", "Owen", "Noah", "Eli", "Finn"]
TRAITS = ["careful", "cautious", "thoughtful", "patient", "curious"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    object_kind: str
    magic: str
    name: str
    gender: str
    adult: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery story world about ravioli, audit, and Dale.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_kind", choices=OBJECTS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--adult", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, o, m) for s in SETTINGS for o in OBJECTS for m in MAGIC]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object_kind is None or c[1] == args.object_kind)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, magic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or ("Dale" if gender == "boy" else _pick_name(rng, gender))
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, obj, magic, name, gender, adult, trait)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, role="child", traits=[params.trait]))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult, role="adult", label="the adult"))
    dish = world.add(Entity(id="ravioli_bowl", type="thing", label="the ravioli bowl"))
    sheet = world.add(Entity(id="audit_sheet", type="thing", label="the audit sheet"))
    wand = world.add(Entity(id="magic_wand", type="thing", label="the magic tool"))
    world.facts.update(hero=hero, adult=adult, dish=dish, sheet=sheet, wand=wand,
                       setting=SETTINGS[params.setting], obj=OBJECTS[params.object_kind],
                       magic=MAGIC[params.magic], params=params)

    kitchen_open(world, SETTINGS[params.setting], hero, dish)
    world.para()
    audit_begin(world, sheet, hero)
    search(world, hero, OBJECTS[params.object_kind], "counter")
    search(world, hero, OBJECTS[params.object_kind], "sink")
    search(world, hero, OBJECTS[params.object_kind], "pantry")
    world.para()
    warn_about_magic(world, hero, MAGIC[params.magic], adult)
    use_magic(world, hero, MAGIC[params.magic], dish)
    solve(world, hero, adult, dish, MAGIC[params.magic])
    world.para()
    ending(world, hero, adult)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].id
    setting = f["setting"].place
    return [
        f'Write a mystery story for a 3-to-5-year-old that includes the words "ravioli", "audit", and "Dale".',
        f"Tell a cautious mystery set in {setting} where {hero} solves a missing-ravioli problem with an audit sheet and a tiny bit of magic.",
        f"Write a child-friendly detective story where careful checking matters more than magic tricks, but a magic helper still appears.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    adult = f["adult"].label_word
    setting = f["setting"].place
    tool = f["magic"]
    return [
        QAItem(
            question="What was missing at the start?",
            answer="The ravioli bowl was missing, and that made the kitchen feel like a mystery.",
        ),
        QAItem(
            question="What did Dale use to look for clues?",
            answer=f"Dale used an audit sheet and checked the kitchen carefully, room by room. "
                   f"That helped because clues are easier to spot when you slow down and look again.",
        ),
        QAItem(
            question="Was the magic used carelessly?",
            answer=f"No. {adult.capitalize()} warned Dale to use the magic tool carefully, and Dale listened. "
                   f"The spell was only used as a gentle helper, not as a shortcut.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The ravioli was found, the audit sheet got its final checkmark, and everyone ate dinner in a tidy kitchen.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ravioli?",
            answer="Ravioli is pasta with filling inside, often served in a bowl with sauce.",
        ),
        QAItem(
            question="What is an audit?",
            answer="An audit is a careful check of things to make sure they are in the right place or match the list.",
        ),
        QAItem(
            question="Why should magic be used carefully?",
            answer="Magic can help, but careless magic can make a mess or cause trouble, so it should be used slowly and safely.",
        ),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] if x else '' for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "ravioli", "lantern_spell", "Dale", "boy", "mother", "careful"),
    StoryParams("backroom", "audit", "magnifier_spell", "Dale", "boy", "father", "cautious"),
    StoryParams("cottage", "ravioli", "magnifier_spell", "Dale", "boy", "mother", "thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
valid(S, O, M) :- setting(S), object(O), magic(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for m in MAGIC:
        lines.append(asp.fact("magic", m))
    return "\n".join(lines)


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
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.setting} / {p.object_kind} / {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
