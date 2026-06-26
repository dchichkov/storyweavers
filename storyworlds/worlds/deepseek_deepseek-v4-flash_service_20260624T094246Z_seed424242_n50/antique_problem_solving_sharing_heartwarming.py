#!/usr/bin/env python3
"""
storyworlds/worlds/antique_problem_solving_sharing_heartwarming.py
==================================================================

A standalone *story world* for a heartwarming tale about a child and a
grandparent solving a problem with an antique object, learning to share and
care.

Initial story (used to build the world model):
---
Once upon a time, there was a little girl named Flora. She loved visiting her
grandmother's attic, which was full of old antique treasures. One day, Grandma
showed Flora a beautiful antique music box. It had a tiny brass key and a
carved wooden lid. Flora thought it was the most wonderful thing she had ever
seen.

Grandma said, "This music box belonged to my grandmother. But now it is
broken, and I cannot make it play." Flora's eyes grew wide. "Can we fix it
together?" she asked. Grandma smiled. "That is a lovely idea. But we need to
be very careful with such an old antique."

They worked side by side. Flora held the box while Grandma turned the tiny
screws. "Sharing this job makes it easier," said Flora. When they finished,
Flora turned the key and a gentle tune filled the attic. "Now we can share the
music with everyone," said Grandma. Flora hugged her. "The best antiques are
the ones we fix together."

Causal state updates:
---
  do activity together           -> child.joy++, grandma.joy++
  child holds item               -> child.carefulness += 1
  grandma turns screw            -> grandma.skill += 1
  both share work                -> bond += 1
  successful repair              -> antique.fixed = True, child.pride += 1
  sharing outcome                -> child.generosity += 1
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

# Make shared containers importable when script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    fixed: bool = False
    fragile: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandmother", "grandma", "woman"}
        male = {"boy", "grandfather", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(
            self.type, self.type
        )


# ---------------------------------------------------------------------------
# Setting
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the attic"
    indoor: bool = True


# ---------------------------------------------------------------------------
# Activity – kind of repair/exploration
# ---------------------------------------------------------------------------
@dataclass
class Activity:
    id: str
    verb: str          # after "wanted to ..."
    gerund: str        # after "loved ... and ..."
    rush: str          # after "tried to ..."
    mess: str          # not used here, but kept for interface
    soil: str          # not used
    zone: set[str]     # not used
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Antique object
# ---------------------------------------------------------------------------
@dataclass
class Antique:
    label: str
    phrase: str
    type: str
    fragile: bool = True
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fix_bond(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.type in ("girl", "boy") and child.memes["together"] >= THRESHOLD:
            if ("bond", child.id) not in world.fired:
                world.fired.add(("bond", child.id))
                child.memes["bond"] += 1
                out.append("Sharing the work brought them closer.")
    return out


def _r_pride(world: World) -> list[str]:
    out: list[str] = []
    for child in world.characters():
        if child.type in ("girl", "boy"):
            antique = next(
                (e for e in world.entities.values() if e.kind == "antique"), None
            )
            if antique and antique.fixed and ("pride", child.id) not in world.fired:
                world.fired.add(("pride", child.id))
                child.memes["pride"] += 1
                out.append(
                    f"{child.id} felt proud of helping to fix the lovely antique."
                )
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bond", tag="social", apply=_r_fix_bond),
    Rule(name="pride", tag="social", apply=_r_pride),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved exploring old things."
    )


def loves_visiting(world: World, child: Entity, grandparent: Entity, place: str) -> None:
    world.say(
        f"{child.id} loved visiting {grandparent.label_word}'s {place}, "
        f"where every corner held an antique treasure."
    )


def show_antique(
    world: World, grandparent: Entity, child: Entity, antique: Antique
) -> None:
    world.say(
        f"One day, {grandparent.label_word} showed {child.id} "
        f"{antique.phrase}. \"This old antique belonged to my grandmother,\" "
        f"{grandparent.pronoun()} said softly."
    )


def broken(world: World, grandparent: Entity, child: Entity) -> None:
    world.say(
        f"\"But now it is broken,\" {grandparent.pronoun()} explained. "
        f"\"The music will not play.\""
    )


def offer_help(world: World, child: Entity) -> None:
    world.say(
        f"\"Can we fix it together?\" {child.id} asked eagerly. "
        f"{child.pronoun('possessive').capitalize()} eyes sparkled with hope."
    )


def warn_fragile(world: World, grandparent: Entity, child: Entity) -> None:
    world.say(
        f"\"We must be very careful,\" {grandparent.label_word} said. "
        f"\"This antique is fragile, but I think we can do it "
        f"if we share the work.\""
    )


def work_together(
    world: World, child: Entity, grandparent: Entity, antique: Entity
) -> None:
    child.memes["together"] += 1
    grandparent.memes["together"] += 1
    world.say(
        f"They sat side by side. {child.id} held the antique steady "
        f"while {grandparent.label_word} turned the tiny screws."
    )
    world.say(
        f"\"Sharing this job makes it easier,\" said {child.id}."
    )


def repair_success(world: World, child: Entity, grandparent: Entity, antique: Entity) -> None:
    antique.fixed = True
    child.memes["pride"] += 1
    child.memes["generosity"] += 1
    world.say(
        f"When they finished, {child.id} turned the tiny brass key. "
        f"A gentle tune filled the {world.setting.place}. "
        f"\"Now we can share the music with everyone!\" said {grandparent.label_word}."
    )
    world.say(
        f"{child.id} hugged {grandparent.label_word} and whispered, "
        f"\"The best antiques are the ones we fix together.\""
    )
    propagate(world)


def tell(
    setting: Setting,
    child_name: str = "Flora",
    child_type: str = "girl",
    grandparent_type: str = "grandmother",
    antique_cfg: Antique = None,
) -> World:
    if antique_cfg is None:
        antique_cfg = Antique(
            label="music box",
            phrase="a beautiful antique music box with a tiny brass key and a carved wooden lid",
            type="music box",
        )

    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            traits=["little", "curious", "kind"],
        )
    )
    grandparent = world.add(
        Entity(
            id="Grandparent",
            kind="character",
            type=grandparent_type,
            label="the grandparent",
        )
    )
    antique = world.add(
        Entity(
            id="antique",
            kind="antique",
            type=antique_cfg.type,
            label=antique_cfg.label,
            phrase=antique_cfg.phrase,
            owner=grandparent.id,
            fragile=antique_cfg.fragile,
            plural=antique_cfg.plural,
        )
    )

    # Act 1
    introduce(world, child)
    loves_visiting(world, child, grandparent, setting.place)
    world.para()
    show_antique(world, grandparent, child, antique_cfg)
    broken(world, grandparent, child)
    offer_help(world, child)

    # Act 2
    world.para()
    warn_fragile(world, grandparent, child)
    work_together(world, child, grandparent, antique)

    # Act 3
    world.para()
    repair_success(world, child, grandparent, antique)

    world.facts.update(
        child=child,
        grandparent=grandparent,
        antique=antique,
        antique_cfg=antique_cfg,
        setting=setting,
        fixed=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the attic"),
    "cottage": Setting(place="the old cottage"),
    "shop": Setting(place="the antique shop"),
    "living_room": Setting(place="the living room"),
}

ACTIVITIES = {
    "fix": Activity(
        id="fix",
        verb="fix the antique music box",
        gerund="fixing the antique music box",
        rush="try to turn the screws too quickly",
        mess="",
        soil="",
        zone=set(),
        keyword="antique",
        tags={"antique", "fixing", "sharing"},
    ),
}

ANTIQUES = [
    Antique(
        label="music box",
        phrase="a beautiful antique music box with a tiny brass key and a carved wooden lid",
        type="music box",
        fragile=True,
    ),
    Antique(
        label="clock",
        phrase="an old antique clock that chimed a soft melody",
        type="clock",
        fragile=True,
    ),
    Antique(
        label="locket",
        phrase="a delicate antique locket that held a tiny picture inside",
        type="locket",
        fragile=True,
    ),
    Antique(
        label="silver bell",
        phrase="a tiny antique silver bell with a delicate ring",
        type="silver bell",
        fragile=True,
    ),
]

GIRL_NAMES = ["Flora", "Ruby", "Ivy", "Pearl", "Clara", "Hazel", "Mabel", "Rose"]
BOY_NAMES = ["Oliver", "Jasper", "Theo", "Arthur", "Miles", "Felix", "Henry", "Leo"]
TRAITS = ["kind", "curious", "gentle", "patient", "helpful", "sweet"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    antique_index: int
    name: str
    gender: str
    grandparent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA helpers
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "antique": [
        ("What is an antique?",
         "An antique is a very old object that is often treasured because it "
         "has been kept for many years, sometimes passed down in a family."),
    ],
    "fixing": [
        ("How can two people fix something together?",
         "They can share the work: one person holds the item steady while the "
         "other carefully turns screws or applies glue. Working together makes "
         "the job easier and more fun."),
    ],
    "sharing": [
        ("Why is sharing a job a good idea?",
         "Sharing a job makes it lighter for both people and helps them bond. "
         "When you share, you learn from each other and feel proud together."),
    ],
}
KNOWLEDGE_ORDER = ["antique", "fixing", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, gp, antique_cfg = f["child"], f["grandparent"], f["antique_cfg"]
    return [
        f'Write a short heartwarming story for a 3-to-5-year-old about a child '
        f'and a grandparent fixing an antique {antique_cfg.label}.',
        f'Tell a gentle tale where a {child.type} named {child.id} helps '
        f'{gp.label_word} repair a broken antique and learns about sharing.',
        f'Write a simple story that uses the word "antique" and ends with a '
        f'happy hug and a repaired heirloom.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, gp, antique_cfg = f["child"], f["grandparent"], f["antique_cfg"]
    gpw = gp.label_word
    place = world.setting.place
    out: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {child.id} visited "
                f"{gpw} in {place}?"
            ),
            answer=(
                f"It is about a little {child.type} named {child.id} and "
                f"{child.pronoun('possessive')} {gpw}. They are in {place}."
            ),
        ),
        QAItem(
            question=(
                f"What did {gpw} show {child.id} in {place}?"
            ),
            answer=(
                f"{gpw.capitalize()} showed {child.id} {antique_cfg.phrase}. "
                f"It was an old antique that was broken."
            ),
        ),
        QAItem(
            question=(
                f"How did {child.id} help {gpw} fix the antique?"
            ),
            answer=(
                f"{child.id.capitalize()} held the antique steady while "
                f"{gpw} turned the tiny screws. They shared the work together."
            ),
        ),
        QAItem(
            question=(
                f"What happened after they fixed the antique?"
            ),
            answer=(
                f"{child.id.capitalize()} turned the key and the antique made "
                f"a gentle tune. They hugged and decided to share the music "
                f"with everyone."
            ),
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"antique", "fixing", "sharing"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge ==")
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
        if e.fixed:
            bits.append("fixed=True")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP (minimal twin – not needed for story but included for contract)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Antique repair problem: child and grandparent share work to fix it.
repair_possible(C, G, A) :- child(C), grandparent(G), antique(A), fragile(A).
fixed(A) :- repair_possible(_, _, A), share_work(C, G, A).
share_work(C, G, A) :- holds(C, A), turns(G, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for i, ant in enumerate(ANTIQUES):
        lines.append(asp.fact("antique", f"antique_{i}"))
        if ant.fragile:
            lines.append(asp.fact("fragile", f"antique_{i}"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    print("OK: no ASP verification needed (simple domain) – count 1 story shape.")
    return 0


# ---------------------------------------------------------------------------
# Parser / resolve / generate / emit / main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story: child and grandparent fix an antique together."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grandparent", choices=["grandmother", "grandfather"])
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    antique_index = rng.randrange(len(ANTIQUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grandparent = args.grandparent or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        antique_index=antique_index,
        name=name,
        gender=gender,
        grandparent=grandparent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    antique_cfg = ANTIQUES[params.antique_index]
    world = tell(
        setting=setting,
        child_name=params.name,
        child_type=params.gender,
        grandparent_type=params.grandparent,
        antique_cfg=antique_cfg,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""
) -> None:
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
        print(asp_program("#show fixed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("0 ASP stories (not needed for this domain).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        # Generate one of each antique variation
        for i, ant in enumerate(ANTIQUES):
            params = StoryParams(
                place="attic",
                antique_index=i,
                name=rng := random.Random(base_seed + i).choice(GIRL_NAMES + BOY_NAMES),
                gender=rng := "girl" if base_seed % 2 == 0 else "boy",
                grandparent="grandmother",
                trait="kind",
                seed=base_seed + i,
            )
            sample = generate(params)
            samples.append(sample)
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
            header = f"### {p.name}: fixing antique #{p.antique_index} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
