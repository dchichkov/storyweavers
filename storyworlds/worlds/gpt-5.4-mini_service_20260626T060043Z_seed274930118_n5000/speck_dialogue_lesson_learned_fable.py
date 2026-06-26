#!/usr/bin/env python3
"""
storyworlds/worlds/speck_dialogue_lesson_learned_fable.py
=========================================================

A small fable-style story world about a tiny speck, a bit of trouble,
and a lesson learned through dialogue.

Premise:
- A neat little animal notices a speck on a prized thing.
- The speck looks small, but it causes worry and unkind words.
- A wiser helper explains that tiny things can still matter.
- The ending proves the change: the speck is cleaned, and the lesson sticks.

This world keeps the prose classical and child-facing, with a clear beginning,
a turn, and a closing moral image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen", "fox", "rabbit", "squirrel"}
        male = {"boy", "father", "man", "owl", "bear", "badger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the meadow"
    afford: str = "speck"
    light: str = "morning"


@dataclass
class Speck:
    label: str
    phrase: str
    kind: str  # dust, ink, mud, soot, pollen
    source: str
    can_clean_with: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    speck: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _clean_spot(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("speck", 0) < THRESHOLD:
            continue
        if ("cleaned", ent.id) in world.fired:
            continue
        world.fired.add(("cleaned", ent.id))
        ent.meters["speck"] = 0
        ent.memes["relief"] = ent.memes.get("relief", 0) + 1
        out.append(f"The little speck was wiped away.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        produced = _clean_spot(world)
        if produced:
            changed = True
            for s in produced:
                world.say(s)


SETTINGS = {
    "meadow": Setting(place="the meadow", afford="speck", light="morning"),
    "riverbank": Setting(place="the riverbank", afford="speck", light="morning"),
    "barnyard": Setting(place="the barnyard", afford="speck", light="afternoon"),
    "orchard": Setting(place="the orchard", afford="speck", light="evening"),
}

SPECKS = {
    "dust": Speck(
        label="speck of dust",
        phrase="a tiny speck of dust",
        kind="dust",
        source="the road",
        can_clean_with="a soft cloth",
        lesson="even a tiny speck can make a fine thing look untidy",
    ),
    "ink": Speck(
        label="ink speck",
        phrase="a little ink speck",
        kind="ink",
        source="a tipped bottle",
        can_clean_with="a damp cloth",
        lesson="small stains are easier to clean when someone notices them soon",
    ),
    "mud": Speck(
        label="mud speck",
        phrase="a brown speck of mud",
        kind="mud",
        source="a wet paw",
        can_clean_with="a damp leaf",
        lesson="a little dirt can travel farther than it first seems",
    ),
    "soot": Speck(
        label="soot speck",
        phrase="a black speck of soot",
        kind="soot",
        source="the chimney",
        can_clean_with="a clean rag",
        lesson="tiny marks can hide on bright things",
    ),
    "pollen": Speck(
        label="pollen speck",
        phrase="a yellow speck of pollen",
        kind="pollen",
        source="the flowers",
        can_clean_with="a gentle brush",
        lesson="even things from flowers can leave a dusting behind",
    ),
}

HERO_NAMES = ["Milo", "Luna", "Pip", "Fern", "Toby", "Mira", "Robin", "Nina"]
HELPER_NAMES = ["Iris", "Otis", "June", "Sage", "Wren", "Rowan", "Penny", "Bram"]
ANIMALS = ["rabbit", "fox", "crow", "squirrel", "mole", "hedgehog", "deer"]
TRAITS = ["neat", "proud", "careful", "quick", "gentle", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, speck) for setting in SETTINGS for speck in SPECKS]


def explain_rejection(setting: str, speck: str) -> str:
    return f"(No story: the {speck} fable needs a setting that can honestly host a tiny speck.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable-style story world about a tiny speck, dialogue, and a lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--speck", choices=SPECKS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=ANIMALS)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=ANIMALS)
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
    if args.setting and args.speck and (args.setting, args.speck) not in combos:
        raise StoryError(explain_rejection(args.setting, args.speck))
    valid = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.speck is None or c[1] == args.speck)]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    setting, speck = rng.choice(valid)
    hero_type = args.hero_type or rng.choice(ANIMALS)
    helper_type = args.helper_type or rng.choice([a for a in ANIMALS if a != hero_type])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        speck=speck,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def tell(setting: Setting, speck: Speck, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "proud", "careful"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["wise", "kind"]))
    prized = world.add(Entity(id="lantern", type="thing", label="lantern", phrase="a bright little lantern", owner=hero.id))
    hero.meters["speck"] = 1
    world.facts.update(hero=hero, helper=helper, prized=prized, speck=speck)

    world.say(f"In {world.setting.place}, {hero_name} the {hero_type} admired {hero.pronoun('possessive')} bright lantern.")
    world.say(f"But one day, {hero_name} saw {speck.phrase} on it and frowned.")
    world.say(f'"Oh no," said {hero_name}, "a {speck.label} has spoiled my lantern."')
    world.para()
    world.say(f'{helper_name} the {helper_type} looked closer and said, "{speck.label.capitalize()} or not, it is still only a little thing."')
    world.say(f'"Little things can still matter," said {helper_name}. "Let us clean it gently."')
    world.say(f'"Then we should not scold the lantern," said {hero_name}, "but care for it."')
    world.para()
    propagate(world)
    world.say(f"Together they used {speck.can_clean_with}, and soon the lantern shone again.")
    world.say(f'{hero_name} smiled and said, "I learned that a small speck is best handled with a calm heart and a kind hand."')
    world.say(f"The lesson was kept like a treasure: {speck.lesson}.")
    world.facts["lesson"] = speck.lesson
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    speck = f["speck"]
    return [
        f'Write a short fable for children about a {hero.type} who finds {speck.phrase} and learns a lesson.',
        f'Tell a gentle dialogue story where {hero.id} and {helper.id} talk about {speck.label}.',
        f'Write a simple moral tale that ends with a lesson learned about tiny mistakes and kind cleaning.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    speck = f["speck"]
    qa = [
        QAItem(
            question=f"What did {hero.id} notice on the lantern?",
            answer=f"{hero.id} noticed {speck.phrase} on the lantern.",
        ),
        QAItem(
            question=f"Who talked gently to {hero.id} about the speck?",
            answer=f"{helper.id} the {helper.type} talked gently and said the speck should be cleaned, not feared.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"The story taught that {speck.lesson}.",
        ),
        QAItem(
            question=f'What did {hero.id} say after the lantern was cleaned?',
            answer=f'{hero.id} said that a small speck is best handled with a calm heart and a kind hand.',
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    speck = f["speck"]
    return [
        QAItem(
            question="What is a speck?",
            answer="A speck is a very small spot or bit of something.",
        ),
        QAItem(
            question=f"What can help clean a {speck.kind} speck?",
            answer=f"The story says {speck.can_clean_with} can help clean it gently.",
        ),
        QAItem(
            question="Why should people notice small messes?",
            answer="Small messes are often easier to clean before they spread or become harder to see.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- char(X).
helper(X) :- char(X).
has_speck(X) :- specked(X).
needs_care(X) :- has_speck(X).
lesson_learned(X) :- needs_care(X), kind_reply(X).
cleaned(X) :- has_speck(X), fixed(X).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for spid, sp in SPECKS.items():
        lines.append(asp.fact("speck", spid))
        lines.append(asp.fact("kind_of", spid, sp.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    # A tiny parity check: every registered speck is a valid option.
    model = asp.one_model(asp_program("#show speck/1."))
    clingo_set = set(asp.atoms(model, "speck"))
    python_set = set((k,) for k in SPECKS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches registries ({len(clingo_set)} specks).")
        return 0
    print("MISMATCH between clingo and registries.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SPECKS[params.speck], params.hero_name, params.hero_type, params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    StoryParams(setting="meadow", speck="dust", hero_name="Milo", hero_type="rabbit", helper_name="Iris", helper_type="fox"),
    StoryParams(setting="orchard", speck="pollen", hero_name="Luna", hero_type="squirrel", helper_name="Sage", helper_type="owl"),
    StoryParams(setting="riverbank", speck="mud", hero_name="Pip", hero_type="hedgehog", helper_name="Wren", helper_type="deer"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show speck/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero_name}: {p.speck} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
