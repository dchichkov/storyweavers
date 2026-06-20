#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flop_curiosity_heartwarming.py
==============================================================

A tiny storyworld for a heartwarming curiosity tale: a child notices a small
problem, asks questions, gets a kind answer, and ends up helping in a way that
feels warm and complete.

The seed word is "flop", and the world is built around a simple kitchen scene
where something flimsy or failed can still become part of a sweet ending.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scene:
    id: str
    place: str
    food: str
    sound: str
    warmth: str
    ending: str

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
class Snack:
    id: str
    label: str
    phrase: str
    shape: str
    can_flop: bool = False
    can_share: bool = True
    tags: set[str] = field(default_factory=set)

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
class Fix:
    id: str
    label: str
    power: int
    text: str
    finish: str
    tags: set[str] = field(default_factory=set)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_melt(world: World) -> list[str]:
    out: list[str] = []
    snack = world.entities.get("snack")
    if not snack or snack.meters["flopped"] < THRESHOLD:
        return out
    sig = ("melt", snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["surprise"] += 1
    world.get("adult").memes["gentle"] += 1
    out.append("__melt__")
    return out


CAUSAL_RULES = [Rule("melt", _r_melt)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def curious_notice(world: World, child: Entity, snack: Snack) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} spotted a {snack.label} on the kitchen table and leaned closer. "
        f"It looked a little {snack.shape}, and that made {child.pronoun('possessive')} eyes brighten."
    )


def ask_why(world: World, child: Entity, adult: Entity, snack: Snack) -> None:
    world.say(
        f'"Why did it {snack.id}?" {child.id} asked. '
        f'{adult.label_word.capitalize()} smiled and patted the table. '
        f'"Sometimes breakfast tries its best and still slips," {adult.pronoun()} said.'
    )


def try_help(world: World, child: Entity, snack: Snack) -> None:
    child.memes["helpfulness"] += 1
    snack.meters["flopped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} carefully nudged the {snack.label} onto a plate. It gave a tiny flop, "
        f"like it was embarrassed, and then settled down."
    )


def warm_fix(world: World, adult: Entity, fix: Fix, snack: Snack) -> None:
    snack.meters["saved"] += 1
    world.say(
        f"{adult.label_word.capitalize()} laughed softly, then {fix.text.replace('{snack}', snack.label)}."
    )
    world.say(
        f"With {fix.label}, the little {snack.label} became a happy treat instead of a mistake."
    )


def share_end(world: World, child: Entity, adult: Entity, scene: Scene, snack: Snack) -> None:
    child.memes["joy"] += 2
    adult.memes["joy"] += 1
    world.say(
        f"They sat together in the {scene.place}, sharing the warm snack and smiling at the silly flop. "
        f"{child.id} still wanted to know everything, and {adult.id} was glad to answer."
    )
    world.say(
        f"By the end, the table felt cozy, the kitchen smelled sweet, and the little flop had turned into a lovely moment."
    )


def tell(scene: Scene, snack: Snack, fix: Fix, child_name: str, child_type: str, adult_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    adult = world.add(Entity(id="Caregiver", kind="character", type=adult_type, role="adult", label="the caregiver"))
    world.add(Entity(id="snack", type="thing", label=snack.label))
    world.facts["scene"] = scene
    world.facts["snack_cfg"] = snack
    world.facts["fix"] = fix

    curious_notice(world, child, snack)
    world.para()
    ask_why(world, child, adult, snack)
    try_help(world, child, snack)
    world.para()
    warm_fix(world, adult, fix, snack)
    share_end(world, child, adult, scene, snack)

    world.facts.update(child=child, adult=adult, snack=world.get("snack"))
    return world


SCENES = {
    "kitchen": Scene("kitchen", "kitchen", "pancakes", "sizzle", "warm", "shared breakfast"),
    "sunnytable": Scene("sunnytable", "sunny kitchen table", "toast", "pop", "bright", "a cheerful snack"),
    "cafe": Scene("cafe", "small cafe corner", "muffins", "hum", "gentle", "a little treat"),
}

SNACKS = {
    "pancake": Snack("pancake", "pancake", "a soft pancake", "floppy", can_flop=True, tags={"flop", "food"}),
    "toast": Snack("toast", "toast", "a buttered slice of toast", "tilty", can_flop=True, tags={"flop", "food"}),
    "muffin": Snack("muffin", "muffin", "a crumbly muffin", "lopsided", can_flop=True, tags={"flop", "food"}),
}

FIXES = {
    "honey": Fix("honey", "a little honey", 2, "drizzled a little honey over the {snack}", "made it shiny"),
    "jam": Fix("jam", "a spoonful of jam", 2, "spread a spoonful of jam on the {snack}", "made it sweet"),
    "smile": Fix("smile", "a gentle smile", 1, "set the {snack} right and gave it a gentle smile", "made the moment warm"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Sam", "Finn", "Noah"]
TRAITS = ["curious", "gentle", "helpful", "thoughtful", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for snack_id, snack in SNACKS.items():
            if not snack.can_flop:
                continue
            for fix_id in FIXES:
                combos.append((scene_id, snack_id, fix_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    scene: str
    snack: str
    fix: str
    child: str
    child_type: str
    adult_type: str
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


KNOWLEDGE = {
    "flop": [("What does it mean when something flops?",
             "When something flops, it falls down loosely or lands with a soft, messy little drop. It is not always bad; sometimes it is just wobbly.")],
    "pancake": [("What is a pancake?",
                 "A pancake is a soft, flat breakfast food cooked on a pan. People often eat it warm with syrup or fruit.")],
    "toast": [("What is toast?",
               "Toast is bread that has been heated until it is crisp and golden. It is often eaten with butter or jam.")],
    "muffin": [("What is a muffin?",
                "A muffin is a small baked treat that is soft inside. It can have fruit or chocolate in it.")],
    "honey": [("What is honey?",
               "Honey is a sweet food made by bees. Grown-ups often drizzle it on food to make it extra tasty.")],
    "jam": [("What is jam?",
             "Jam is sweet, fruity spread made from cooked fruit and sugar. It is good on bread and toast.")],
}
KNOWLEDGE_ORDER = ["flop", "pancake", "toast", "muffin", "honey", "jam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a child where the word "{f["snack_cfg"].id}" appears and a small flop becomes something sweet.',
        f"Tell a gentle story about {f['child'].id}, who is curious about {f['snack_cfg'].label}, and a caregiver who answers kindly.",
        f'Write a cozy story in a kitchen where curiosity leads to help, and the ending feels warm and loving.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, snack, scene = f["child"], f["adult"], f["snack"], f["scene"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and the caregiver in the {scene.place}. {child.id} is the one whose curiosity starts the story."),
        ("What did {0} notice?".format(child.id),
         f"{child.id} noticed {snack.label} on the table and wondered why it looked so {snack.shape}. That question led to a kind answer."),
        ("What did the caregiver do?",
         f"The caregiver smiled, explained what happened, and helped turn the little flop into a sweet treat. The answer was gentle instead of scolding."),
        ("How did the story end?",
         f"It ended with them sharing a warm snack together. Curiosity brought them closer, and the kitchen felt cozy and happy."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["snack_cfg"].tags) | set(world.facts["fix"].tags) | {"flop"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
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
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "pancake", "honey", "Mia", "girl", "mother", "curious"),
    StoryParams("sunnytable", "toast", "jam", "Ben", "boy", "father", "thoughtful"),
    StoryParams("cafe", "muffin", "smile", "Lily", "girl", "grandmother", "helpful"),
]


def explain_rejection(scene: Scene, snack: Snack) -> str:
    if not snack.can_flop:
        return f"(No story: {snack.label} does not fit the little flop premise.)"
    return "(No story: this combination does not make a gentle curiosity story.)"


def valid_story(params: StoryParams) -> bool:
    return params.snack in SNACKS and params.scene in SCENES and params.fix in FIXES


ASP_RULES = r"""
valid(Scene, Snack, Fix) :- scene(Scene), snack(Snack), can_flop(Snack), fix(Fix).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.can_flop:
            lines.append(asp.fact("can_flop", sid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, snack=None, fix=None, child=None, child_type=None, adult_type=None, trait=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming curiosity story world about a small flop.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father", "grandmother", "grandfather"])
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
              if (args.scene is None or c[0] == args.scene)
              and (args.snack is None or c[1] == args.snack)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, snack, fix = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(scene, snack, fix, child, child_type, adult_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], SNACKS[params.snack], FIXES[params.fix],
                 params.child, params.child_type, params.adult_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for item in asp_valid_combos():
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child}: {p.snack} / {p.fix} ({p.scene})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
