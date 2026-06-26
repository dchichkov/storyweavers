#!/usr/bin/env python3
"""
storyworlds/worlds/span_deceive_pro_conflict_fairy_tale.py
============================================================

A standalone story world sketch for a fairy tale about a deceitful bridge crossing,
featuring a span (the bridge), a deceiver, and a pro (wise helper).  The core
conflict is the deceiver's trick, resolved by the pro's advice.
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

# ---------------------------------------------------------------------------
# Registry keys used by the world model
# ---------------------------------------------------------------------------
TRUST = "trust"
FEAR = "fear"
WISDOM = "wisdom"
DECEIT = "deceit"
CONFLICT = "conflict"
COURAGE = "courage"

# ---------------------------------------------------------------------------
# Entity dataclass (shared chars + objects)
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"               # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "witch", "fairy"}
        male = {"boy", "father", "fox", "dwarf", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


@dataclass
class Setting:
    place: str = "the enchanted forest"
    affords: set[str] = field(default_factory=set)


@dataclass
class Trick:
    id: str
    verb: str               # after "wanted to …"  e.g. "cross the bridge"
    gerund: str             # after "loved … and …"
    rush: str               # after "tried to …"
    danger: str             # the fake danger the deceiver describes
    safe_advice: str        # what the helper says
    keyword: str = "deceive"
    tags: set[str] = field(default_factory=lambda: {"deceive", "bridge"})


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "feet"     # the hero's shoes (always at risk when crossing)
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    advice: str              # advice to the hero
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_deceit_effect(world: World) -> list[str]:
    """If deceiver has DECEIT memes above threshold, hero loses trust and gains fear."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get(DECEIT, 0) < THRESHOLD:
            continue
        # find the hero (the one not marked as deceiver)
        hero = next((e for e in world.characters()
                     if e.id != actor.id and not e.traits.count("deceiver")), None)
        if hero is None:
            continue
        sig = ("deceived", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes[TRUST] -= 1
        hero.memes[FEAR] += 1
        hero.memes[CONFLICT] += 1
        out.append(f"{hero.id} felt a knot of worry in {hero.pronoun('possessive')} belly.")
    return out


def _r_helper_calm(world: World) -> list[str]:
    """If a helper (pro) speaks, reduce hero's fear and conflict."""
    out: list[str] = []
    helper = next((e for e in world.entities.values()
                   if e.kind == "thing" and e.type == "helper"), None)
    if not helper:
        return out
    hero = next((e for e in world.characters() if e.kind == "character"), None)
    if hero is None:
        return out
    sig = ("helped", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes[FEAR] = max(0.0, hero.memes[FEAR] - THRESHOLD)
    hero.memes[CONFLICT] = max(0.0, hero.memes[CONFLICT] - THRESHOLD)
    hero.memes[COURAGE] += 1
    out.append(f"{hero.id} listened and felt steadier.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="deceit_effect", tag="emotional", apply=_r_deceit_effect),
    Rule(name="helper_calm", tag="emotional", apply=_r_helper_calm),
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
                produced.extend(sets)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verbs / screenplay
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    return f"The {setting.place.removeprefix('the ')} was deep and quiet."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"Once upon a time, {hero.id} was a little {hero.type} who lived near {world.setting.place}.")


def loves_adventure(world: World, hero: Entity) -> None:
    hero.memes[COURAGE] += 1
    world.say(f"{hero.pronoun().capitalize()} loved exploring and always wished for an adventure.")


def deceive(world: World, deceiver: Entity, trick: Trick, hero: Entity) -> None:
    deceiver.memes[DECEIT] += 1
    world.say(f"One day, a {deceiver.type} appeared and said, 'I know a shortcut across the river. The bridge {trick.danger}.'")
    propagate(world, narrate=True)


def hero_wants(world: World, hero: Entity, trick: Trick, prize: Entity) -> None:
    hero.memes[TRUST] += 0.5
    world.say(f"{hero.id} wanted to {trick.verb} and took a step toward the bridge, wearing {hero.pronoun('possessive')} {prize.phrase}.")


def conflict_peak(world: World, hero: Entity, trick: Trick) -> None:
    hero.memes[CONFLICT] += 1
    world.say(f"But {hero.id} stopped, unsure. The {trick.keyword} did not feel right.")


def helper_appears(world: World, helper_entity: Entity, trick: Trick, hero: Entity) -> None:
    world.say(f"Then a wise {helper_entity.type} {helper_entity.label} appeared and said, '{trick.safe_advice}.'")
    propagate(world, narrate=True)


def resolution(world: World, hero: Entity, trick: Trick, prize: Entity, helper_entity: Entity) -> None:
    hero.memes[CONFLICT] = 0.0
    hero.memes[COURAGE] += 1
    world.say(f"{hero.id} thanked the {helper_entity.type}. {hero.pronoun().capitalize()} walked across the real bridge, {hero.pronoun('possessive')} {prize.label} safe, and the clever {trick.keyword} was left behind.")


def tell(setting: Setting, trick: Trick, prize_cfg: Prize,
         hero_name: str = "Elara", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         deceiver_type: str = "fox",
         helper_type: str = "owl") -> World:
    world = World(setting)
    # hero
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["brave", "curious"])))
    # deceiver
    deceiver_id = "Deceiver"
    world.add(Entity(id=deceiver_id, kind="character", type=deceiver_type,
                     traits=["deceiver"]))
    # prize (the hero's shoes)
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, plural=prize_cfg.plural,
        region="feet",
    ))
    # helper (pro)
    helper_ent = world.add(Entity(
        id="Helper", kind="thing", type=helper_type,
        label=helper_type, phrase=f"a wise {helper_type}",
        protective=True,
    ))
    # Acts
    introduce(world, hero)
    loves_adventure(world, hero)
    deceive(world, world.get(deceiver_id), trick, hero)
    hero_wants(world, hero, trick, prize)
    conflict_peak(world, hero, trick)
    helper_appears(world, helper_ent, trick, hero)
    resolution(world, hero, trick, prize, helper_ent)

    world.facts.update(hero=hero, deceiver=world.get(deceiver_id),
                       prize=prize, prize_cfg=prize_cfg, trick=trick,
                       helper=helper_ent, setting=setting,
                       conflict_resolved=hero.memes[CONFLICT] == 0)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the enchanted forest", affords={"bridge"},),
    "meadow": Setting(place="the whispering meadow", affords={"bridge"},),
    "mountain": Setting(place="the misty mountain", affords={"bridge"},),
}

TRICKS = {
    "bridge": Trick(
        id="bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        rush="rush across the bridge",
        danger="is old and creaks terribly! The planks will break if you step on them.",
        safe_advice="The bridge is sound. The deceiver wants you to turn back so they can steal your shoes.",
        keyword="deceive",
        tags={"deceive", "bridge"},
    ),
}

# Prizes: the hero's beloved footwear
PRIZES = {
    "shoes": Prize(label="shoes", phrase="shiny red shoes", type="shoes", plural=True),
    "boots": Prize(label="boots", phrase="sturdy leather boots", type="boots", plural=True),
    "slippers": Prize(label="slippers", phrase="soft blue slippers", type="slippers", plural=True),
}

HELPERS = {
    "owl": Helper(id="owl", label="owl", phrase="a wise old owl",
                  advice="Beware the fox's tale; the bridge is strong and your shoes are safe."),
    "dwarf": Helper(id="dwarf", label="dwarf", phrase="a kind dwarf",
                    advice="Don't trust the deceiver. Use your courage, child."),
}

GIRL_NAMES = ["Elara", "Freya", "Lilia", "Nora", "Tara"]
BOY_NAMES = ["Finn", "Kael", "Orin", "Ravi", "Tobin"]
TRAITS = ["brave", "curious", "kind", "clever", "determined"]


def valid_combos() -> list[tuple]:
    """Place, trick, prize combos (always valid for this simple domain)."""
    return [(p, t, pr) for p in SETTINGS for t in TRICKS for pr in PRIZES]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    trick: str
    prize: str
    name: str
    gender: str
    hero_trait: str
    deceiver_type: str = "fox"
    helper_type: str = "owl"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "deceive": [
        ("What does it mean to deceive someone?",
         "To deceive means to trick or mislead someone on purpose, often to get something from them."),
    ],
    "bridge": [
        ("Why are bridges useful?",
         "Bridges let people cross over rivers, valleys, or roads without getting wet or walking around."),
    ],
    "courage": [
        ("What is courage?",
         "Courage is doing something even when you feel a little scared or unsure, because you know it is the right thing."),
    ],
}
KNOWLEDGE_ORDER = ["deceive", "bridge", "courage"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, trick = f["hero"], f["trick"]
    return [
        f'Write a short fairy tale on the theme "deception and courage" that includes the word "{trick.keyword}".',
        f"Tell a story about a {hero.type} named {hero.id} who meets a {world.facts['deceiver'].type} "
        f"near a bridge and learns to trust a wise {world.facts['helper'].type}.",
        f'Write a simple story that includes the nouns "bridge" and "fox" and ends with a lesson about trust.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, dec, prize, trick = f["hero"], f["deceiver"], f["prize_cfg"], f["trick"]
    helper_ent = f["helper"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} visits {world.setting.place}?",
            answer=f"It is about a little {hero.traits[0]} {hero.type} named {hero.id} who "
                   f"wears {prize.phrase} and meets a {dec.type} at a bridge.",
        ),
        QAItem(
            question=f"What does the {dec.type} try to do to {hero.id} near the bridge?",
            answer=f"The {dec.type} tries to deceive {obj} by telling {obj} that the bridge "
                   f"is unsafe, hoping {sub} will turn back and leave {pos} {prize.label} behind.",
        ),
        QAItem(
            question=f"Who helps {hero.id} see the truth?",
            answer=f"A wise {helper_ent.type} {helper_ent.label} appears and gives {obj} the right "
                   f"advice: the bridge is safe and the {dec.type} is lying.",
        ),
    ]
    if f.get("conflict_resolved", False):
        qa.append(QAItem(
            question=f"How does {hero.id} feel after listening to the {helper_ent.label}?",
            answer=f"{sub} feels brave again and crosses the bridge safely, keeping {pos} "
                   f"{prize.label} and leaving the {dec.type} behind.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"deceive", "bridge"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated set
CURATED = [
    StoryParams(place="forest", trick="bridge", prize="shoes",
                name="Elara", gender="girl", hero_trait="brave"),
    StoryParams(place="meadow", trick="bridge", prize="boots",
                name="Finn", gender="boy", hero_trait="curious"),
    StoryParams(place="mountain", trick="bridge", prize="slippers",
                name="Lilia", gender="girl", hero_trait="kind"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story exists when place, trick, prize are all registered.
valid(Place, Trick, Prize) :- setting(Place), trick(Trick), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy tale: a child, a deceiver, a bridge, and a wise helper.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.trick:
        combos = [c for c in combos if c[1] == args.trick]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid combination matches.")
    place, trick_id, prize_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, trick=trick_id, prize=prize_id,
                       name=name, gender=gender, hero_trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TRICKS[params.trick],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.hero_trait])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(combos)} compatible (place, trick, prize) combos:\n")
        for p, t, pr in combos:
            print(f"  {p:10} {t:7} {pr:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.trick} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
