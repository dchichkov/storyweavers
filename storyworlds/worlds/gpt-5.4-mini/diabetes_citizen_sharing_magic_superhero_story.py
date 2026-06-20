#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/diabetes_citizen_sharing_magic_superhero_story.py
=================================================================================

A standalone story world built from the seed words **diabetes** and **citizen**,
with the themes of **sharing** and **magic**, told in a **superhero story** style.

The domain is small and classical: a child superhero notices that a neighbor
with diabetes needs help during a busy day in the city, learns that sharing
simple supplies can make a big difference, and uses a little "magic" in the
storybook sense: a magic bag, a magic cape, and a helpful trick of calm
attention. The story stays grounded in world state: meters and memes change,
items are shared, a low-blood-sugar moment is handled safely, and the ending
proves the change with a brighter, kinder city.

The script supports:
- default random generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp

It also includes a Python reasonableness gate plus an inline ASP twin.
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
SAFE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    needs_sugar: bool = False
    shares: bool = False
    magic: bool = False
    helpful: bool = False

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
    details: str
    crowd: str
    ends: str
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    helpful: bool = False
    magic: bool = False
    shares: bool = False
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
class Problem:
    id: str
    trigger: str
    sign: str
    risk: str
    fix: str
    power: int
    sense: int
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
    out = []
    for e in world.characters():
        if e.meters["low"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__worry__")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["helped"] < THRESHOLD:
            continue
        sig = ("help", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        e.memes["safety"] += 1
        out.append("__help__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("help", "social", _r_help)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for iid, item in ITEMS.items():
                if reason_ok(problem, item):
                    combos.append((sid, pid, iid))
    return combos


def reason_ok(problem: Problem, item: Item) -> bool:
    return problem.sense >= SAFE_MIN and problem.power > 0 and item.helpful


def setting_intro(world: World, hero: Entity, citizen: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright day in {setting.place}, {hero.id} watched over the streets "
        f"like a tiny superhero. {setting.details}"
    )
    world.say(
        f"{citizen.id} was a kind citizen who knew every shortcut and every smile "
        f"in the neighborhood."
    )


def setup_need(world: World, hero: Entity, citizen: Entity, problem: Problem) -> None:
    hero.memes["alert"] += 1
    citizen.meters["low"] += 1
    world.say(
        f"Then {citizen.id}'s tummy felt strange. The little sign was clear: "
        f"{problem.sign}."
    )
    world.say(
        f"{hero.id} remembered that {citizen.id} had diabetes, so a low sugar day "
        f"could not be ignored."
    )


def share_item(world: World, hero: Entity, citizen: Entity, item: Item) -> None:
    hero.memes["sharing"] += 1
    citizen.meters["helped"] += 1
    world.say(
        f"{hero.id} opened a magic bag and found {item.phrase}. "
        f"{hero.id} said, \"Let's share this and help our friend.\""
    )


def magic_fix(world: World, hero: Entity, citizen: Entity, problem: Problem, item: Item) -> None:
    citizen.meters["low"] = 0.0
    hero.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The magic cape fluttered once, and {hero.id} used {item.label} with a calm "
        f"superhero smile. The careful fix matched {problem.fix}."
    )
    world.say(
        f"{citizen.id} breathed easier, and the city seemed less noisy at once."
    )


def ending(world: World, hero: Entity, citizen: Entity, setting: Setting, item: Item) -> None:
    hero.memes["pride"] += 1
    citizen.memes["gratitude"] += 1
    world.say(
        f"By sunset, {setting.ends}. {citizen.id} walked home safely, and "
        f"{hero.id} tucked the sharing item back into the magic bag, ready for the "
        f"next good deed."
    )


def warn(world: World, hero: Entity, citizen: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} knew the risk: if nobody helped, {problem.risk}."
    )


def tell(setting: Setting, problem: Problem, item: Item) -> World:
    world = World()
    hero = world.add(Entity(id="Nova", kind="character", type="girl", role="hero", traits=["brave", "kind"]))
    citizen = world.add(Entity(id="Mr. Lane", kind="character", type="man", role="citizen", traits=["patient", "gentle"], needs_sugar=True))
    world.add(Entity(id="bag", type="thing", label="magic bag", magic=True, helpful=True))
    world.add(Entity(id="cape", type="thing", label="magic cape", magic=True, helpful=True))
    world.add(Entity(id="item", type="thing", label=item.label, shares=True, helpful=True, magic=item.magic))
    setting_intro(world, hero, citizen, setting)
    world.para()
    setup_need(world, hero, citizen, problem)
    warn(world, hero, citizen, problem)
    share_item(world, hero, citizen, item)
    world.para()
    magic_fix(world, hero, citizen, problem, item)
    ending(world, hero, citizen, setting, item)
    world.facts.update(hero=hero, citizen=citizen, setting=setting, problem=problem, item=item)
    return world


SETTINGS = {
    "city": Setting("city", "Sunbeam City", "The traffic hummed, the bakery smelled sweet, and the park fountain sparkled.", "people", "the streets glowed gold", tags={"city"}),
    "plaza": Setting("plaza", "Civic Plaza", "Banners waved over benches, and the little clock ticked beside the fountain.", "citizens", "the plaza grew calm", tags={"plaza"}),
    "neighborhood": Setting("neighborhood", "Maple Block", "Windows blinked open, and neighbors waved from porches.", "neighbors", "the block felt safe again", tags={"neighborhood"}),
}

PROBLEMS = {
    "low_sugar": Problem("low_sugar", "diabetes", "a low-sugar wobble", "faintness and shaky hands", "quick sugar and calm help", power=3, sense=3, tags={"diabetes"}),
    "tired": Problem("tired", "diabetes", "a tired, slow step", "too much wobbling to keep walking", "a pause and a snack", power=2, sense=3, tags={"diabetes"}),
}

ITEMS = {
    "juice": Item("juice", "juice box", "a juice box", "snack", helpful=True, shares=True, tags={"sharing"}),
    "candy": Item("candy", "fruit candies", "a handful of fruit candies", "snack", helpful=True, shares=True, tags={"sharing"}),
    "granola": Item("granola", "granola bar", "a granola bar", "snack", helpful=True, shares=True, tags={"sharing", "magic"}),
}

GIRL_NAMES = ["Nova", "Mina", "Lena", "Iris", "Aya"]
BOY_NAMES = ["Max", "Eli", "Theo", "Jude", "Leo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    item: str
    hero_name: str
    hero_gender: str
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
    "diabetes": [("What is diabetes?", "Diabetes is a health condition that affects how the body uses sugar for energy. Some people with diabetes need careful help to stay feeling well.")],
    "citizen": [("What is a citizen?", "A citizen is a person who lives in a city, town, or country and belongs to that community.")],
    "sharing": [("What is sharing?", "Sharing means letting someone use or have some of what you have. It can help people feel cared for.")],
    "magic": [("What does magic mean in a story?", "In a story, magic can mean a special helpful thing that works like a wonder, even if it is pretend.")],
    "sugar": [("Why do some people need sugar quickly?", "If someone has low sugar, a quick sweet snack or drink can help them feel better.")],
    "help": [("Why is it good to help?", "Helping can keep someone safe and show kindness. A small helpful act can change a whole day.")],
}
KNOWLEDGE_ORDER = ["diabetes", "citizen", "sharing", "magic", "sugar", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "{f["problem"].trigger}" and "{f["citizen"].id}".',
        f"Tell a gentle city superhero story where {f['hero'].id} helps a citizen with diabetes by sharing a helpful snack.",
        f"Write a story about magic, sharing, and a brave helper in {f['setting'].place} that ends safely and kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, citizen, problem, item = f["hero"], f["citizen"], f["problem"], f["item"]
    return [
        ("Who is the story about?", f"It is about {hero.id}, a small superhero, and {citizen.id}, a citizen in the city."),
        ("What problem did the citizen have?", f"{citizen.id} had a diabetes-related low-sugar wobble, which made it hard to keep walking. That is why {hero.id} needed to help quickly."),
        ("How did the hero help?", f"{hero.id} shared {item.phrase} and used the magic bag and cape to stay calm. The shared snack matched {problem.fix} and helped the day feel safe again."),
        ("How did the story end?", f"It ended with {citizen.id} feeling better and the city growing calm. {hero.id} proved that sharing can be a kind of superpower."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["problem"].trigger, "sharing", "magic", "citizen", "diabetes"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.magic:
            bits.append("magic=True")
        if e.shares:
            bits.append("shares=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("city", "low_sugar", "juice", "Nova", "girl"),
    StoryParams("plaza", "tired", "granola", "Mina", "girl"),
    StoryParams("neighborhood", "low_sugar", "candy", "Eli", "boy"),
]


def explain_rejection(problem: Problem, item: Item) -> str:
    if not reason_ok(problem, item):
        return "(No story: the chosen ingredients do not make a safe, helpful superhero problem-and-fix.)"
    return "(No story: this combination is not reasonable.)"


def valid_story_checks(args: argparse.Namespace) -> None:
    if args.item and not ITEMS[args.item].helpful:
        raise StoryError("(No story: the item must be helpful for a sharing-and-magic superhero tale.)")


ASP_RULES = r"""
valid(S, P, I) :- setting(S), problem(P), item(I), reasonable(P, I).
reasonable(P, I) :- sense(P, X), safe_min(M), X >= M, helpful(I).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("trigger", pid, p.trigger))
        lines.append(asp.fact("sense", pid, p.sense))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.helpful:
            lines.append(asp.fact("helpful", iid))
    lines.append(asp.fact("safe_min", SAFE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, item=None, hero_name=None, hero_gender=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test failed: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with diabetes, citizen, sharing, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
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
    valid_story_checks(args)
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, item = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    return StoryParams(setting, problem, item, hero_name, hero_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], ITEMS[params.item])
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            params.seed = base_seed + i
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
