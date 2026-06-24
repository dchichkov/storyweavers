#!/usr/bin/env python3
"""
storyworlds/worlds/nerve_strangle_magic_rhyming_story.py
=========================================================

A tiny story world about a child, a little burst of magic, and a rhyming
problem that turns into a brave fix.

Seed tale:
---
A child wanted to try a magic rhyme at the fair. The rhyme made a ribbon of
spell-smoke twist too tight around a silver bell, and the child lost their nerve.
A helper showed a gentle counter-rhyme, the smoke loosened, and the bell rang
clear again.

World model:
---
- A hero can practice a rhyme in one small place.
- A magic charm can be safe, but if used too boldly it tangles a target.
- The target can be tied, muffled, or trapped by the spell.
- A helper can answer with a counter-rhyme that frees the target.
- The story ends with the same magic, now guided by nerve instead of fear.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Place:
    id: str
    name: str
    detail: str
    setting_line: str
    affords_magic: bool = True


@dataclass(frozen=True)
class HeroCfg:
    id: str
    name: str
    gender: str
    trait: str


@dataclass(frozen=True)
class MagicItem:
    id: str
    label: str
    phrase: str
    shimmer: str
    risk: str
    fix: str
    safe_word: str


@dataclass(frozen=True)
class TargetCfg:
    id: str
    label: str
    phrase: str
    region: str
    sound: str


@dataclass(frozen=True)
class HelperCfg:
    id: str
    name: str
    trait: str
    rhyme: str


PLACES = {
    "fair": Place(
        id="fair",
        name="the fair",
        detail="The fair was bright with banners and a music cart.",
        setting_line="The fair was bright, and the music cart hummed in the air.",
    ),
    "garden": Place(
        id="garden",
        name="the garden",
        detail="The garden had a stone path and a row of tiny blue flowers.",
        setting_line="The garden was quiet, and the blue flowers nodded in a row.",
    ),
    "stage": Place(
        id="stage",
        name="the little stage",
        detail="The little stage had a red rug and a curtain that fluttered.",
        setting_line="The little stage was ready, with a red rug and a curtain's glow.",
    ),
}

HEROES = {
    "mira": HeroCfg(id="mira", name="Mira", gender="girl", trait="curious"),
    "noah": HeroCfg(id="noah", name="Noah", gender="boy", trait="brave"),
    "luna": HeroCfg(id="luna", name="Luna", gender="girl", trait="cheery"),
    "elliot": HeroCfg(id="elliot", name="Elliot", gender="boy", trait="lively"),
}

MAGIC_ITEMS = {
    "wand": MagicItem(
        id="wand",
        label="magic wand",
        phrase="a shiny little magic wand",
        shimmer="sparkled",
        risk="twisted too tight",
        fix="softened and swayed",
        safe_word="gentlegleam",
    ),
    "bell": MagicItem(
        id="bell",
        label="silver bell",
        phrase="a small silver bell",
        shimmer="rang",
        risk="got muffled",
        fix="rang clear again",
        safe_word="ring-around",
    ),
    "ribbon": MagicItem(
        id="ribbon",
        label="red ribbon",
        phrase="a bright red ribbon",
        shimmer="fluttered",
        risk="knotted up",
        fix="unwound in a wink",
        safe_word="loose-and-low",
    ),
}

TARGETS = {
    "bell": TargetCfg(
        id="bell",
        label="silver bell",
        phrase="the silver bell",
        region="air",
        sound="ding",
    ),
    "ribbon": TargetCfg(
        id="ribbon",
        label="red ribbon",
        phrase="the red ribbon",
        region="hands",
        sound="swish",
    ),
    "kite": TargetCfg(
        id="kite",
        label="paper kite",
        phrase="the paper kite",
        region="sky",
        sound="flutter",
    ),
}

HELPERS = {
    "grandma": HelperCfg(id="grandma", name="Grandma", trait="kind", rhyme="soft and slow"),
    "teacher": HelperCfg(id="teacher", name="the teacher", trait="calm", rhyme="small and bright"),
    "brother": HelperCfg(id="brother", name="his brother", trait="patient", rhyme="clear and near"),
}

GENTLE_NAMES = ["Mira", "Noah", "Luna", "Elliot"]
TRAITS = ["curious", "brave", "cheery", "lively", "careful", "bright"]


# ---------------------------------------------------------------------------
# Params and world
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    magic_item: str
    target: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    worn_by: Optional[str] = None
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero_cfg = HEROES[params.hero]
    item = MAGIC_ITEMS[params.magic_item]
    target = TARGETS[params.target]
    helper = HELPERS[params.helper]

    world = World(place)
    hero = world.add(Entity(
        id=hero_cfg.id, kind="character", type=hero_cfg.gender, label=hero_cfg.name
    ))
    helper_ent = world.add(Entity(
        id=helper.id, kind="character", type="adult", label=helper.name
    ))
    item_ent = world.add(Entity(
        id=item.id, kind="thing", type="magic_item", label=item.label, phrase=item.phrase,
        owner=hero.id
    ))
    target_ent = world.add(Entity(
        id=target.id, kind="thing", type="thing", label=target.label, phrase=target.phrase,
        caretaker=helper_ent.id
    ))

    hero.memes["nerve"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 0.0
    target_ent.meters["tangle"] = 0.0

    # Act 1
    world.say(f"{hero_cfg.name} was a {hero_cfg.trait} child who loved to try a rhyme.")
    world.say(f"{place.setting_line} {hero_cfg.name} held {item.phrase} and smiled at {target.phrase}.")
    world.say(f"{hero_cfg.name} wanted the magic to sound sweet and light, with a song that could bounce.")

    # Act 2
    world.para()
    world.say(f"But when {hero_cfg.name} spoke the rhyme, the spell {item.shimmer} and went off with a little leap.")
    hero.memes["worry"] += 1
    hero.memes["nerve"] -= 1
    target_ent.meters["tangle"] += 1
    if target.id == "bell":
        world.say(f"The spell-smoke curled round {target.phrase} and made it {item.risk}.")
    elif target.id == "ribbon":
        world.say(f"The spell-smoke curled round {target.phrase} and made it {item.risk}.")
    else:
        world.say(f"The spell-smoke zipped around {target.phrase} and made it {item.risk}.")
    world.say(f"{hero_cfg.name} felt the wobble in the chest and lost a bit of nerve.")

    # helper enters with counter-rhyme
    world.say(f"Then {helper.name} came near and said, '{item.safe_word}, {helper.rhyme}, let the tight thing unwind.'")
    target_ent.meters["tangle"] -= 1
    hero.memes["worry"] = 0.0
    hero.memes["nerve"] = 1.0
    hero.memes["joy"] += 1

    # Act 3
    world.para()
    world.say(f"The counter-rhyme worked. The spell {item.fix}, and {target.phrase} was free again.")
    world.say(f"{hero_cfg.name} stood tall, took a breath, and tried once more with nerve instead of fright.")
    world.say(f"This time the little magic went neat and true, and {target.phrase} gave a clean {target.sound}.")
    world.say(f"{hero_cfg.name} and {helper.name} laughed as the bright rhyme drifted away like a happy tune.")

    world.facts.update(
        hero=hero_cfg,
        helper=helper,
        item=item,
        target=target,
        place=place,
        resolved=True,
        tangled=True,
        countered=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    target = f["target"]
    place = f["place"]
    return [
        f'Write a short rhyming story about {hero.name} at {place.name} with {item.label} and {target.label}.',
        f"Tell a gentle magic story where a child loses a little nerve, then finds it again with a helping rhyme.",
        f'Write a small story with the words "nerve" and "strangle" where magic gets tangled and then made safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    target = f["target"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where did {hero.name} try the magic rhyme?",
            answer=f"{hero.name} tried the rhyme at {place.name}, where the little scene was set and the magic could be heard clearly.",
        ),
        QAItem(
            question=f"What happened to {target.label} when the rhyme went wrong?",
            answer=f"{target.phrase} got tangled by the spell and became tight for a moment, until the counter-rhyme loosened it.",
        ),
        QAItem(
            question=f"Who helped {hero.name} fix the magic?",
            answer=f"{helper.name} helped by speaking a calm counter-rhyme that made the spell unwind and the target free again.",
        ),
        QAItem(
            question=f"How did {hero.name} feel after the fix?",
            answer=f"{hero.name} felt brave again, because the helper's rhyme brought back nerve and turned the tricky moment into a happy one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words that sound alike at the end, which can make a song or chant feel fun and bouncy.",
        ),
        QAItem(
            question="What does nerve mean in a story like this?",
            answer="Nerve means brave feeling or courage, the bit of inside strength that helps someone try again.",
        ),
        QAItem(
            question="What does it mean to tangle something?",
            answer="To tangle something means to twist it into a mess so it is harder to use or pull apart.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
hero(H) :- hero_cfg(H).
item(I) :- magic_item(I).
target(T) :- target_cfg(T).
helper(X) :- helper_cfg(X).

tangled(T) :- spell_mess(T).
resolved(T) :- tangled(T), counter_rhyme(T).

valid_story(P,H,I,T,X) :- place(P), hero(H), item(I), target(T), helper(X), magic_ok(I,T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("setting", p.id))
    for h in HEROES.values():
        lines.append(asp.fact("hero_cfg", h.id))
    for i in MAGIC_ITEMS.values():
        lines.append(asp.fact("magic_item", i.id))
    for t in TARGETS.values():
        lines.append(asp.fact("target_cfg", t.id))
    for x in HELPERS.values():
        lines.append(asp.fact("helper_cfg", x.id))
    for i in MAGIC_ITEMS.values():
        for t in TARGETS.values():
            ok = (i.id != "wand" or t.id != "kite")
            if ok:
                lines.append(asp.fact("magic_ok", i.id, t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set()
    for p in PLACES:
        for h in HEROES:
            for i in MAGIC_ITEMS:
                for t in TARGETS:
                    for x in HELPERS:
                        if i != "wand" or t != "kite":
                            py.add((p, h, i, t, x))
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming magic story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--magic-item", choices=MAGIC_ITEMS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.magic_item == "wand" and args.target == "kite":
        raise StoryError("(No story: this wand is too twirly for the paper kite; the rhymes would only tangle more.)")
    choices = []
    for p in PLACES:
        if args.place and p != args.place:
            continue
        for h in HEROES:
            if args.hero and h != args.hero:
                continue
            for i in MAGIC_ITEMS:
                if args.magic_item and i != args.magic_item:
                    continue
                for t in TARGETS:
                    if args.target and t != args.target:
                        continue
                    for x in HELPERS:
                        if args.helper and x != args.helper:
                            continue
                        if i == "wand" and t == "kite":
                            continue
                        choices.append((p, h, i, t, x))
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    p, h, i, t, x = rng.choice(sorted(choices))
    return StoryParams(place=p, hero=h, magic_item=i, target=t, helper=x)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="fair", hero="mira", magic_item="bell", target="bell", helper="grandma"),
    StoryParams(place="garden", hero="noah", magic_item="ribbon", target="ribbon", helper="teacher"),
    StoryParams(place="stage", hero="luna", magic_item="wand", target="bell", helper="brother"),
]


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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} with {p.magic_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
