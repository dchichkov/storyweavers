#!/usr/bin/env python3
"""
A small adventure storyworld built from the seed words extraction, crapper, and treaty.
The domain follows a child-friendly quest: a brave hero must extract a stubborn clog
from a crapper in an old tower, remember a flashback about a past mistake, and use
magic plus a treaty to achieve a transformation and a peaceful ending.
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
# Core domain objects
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    portable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Spell:
    id: str
    label: str
    effect: str
    requires_flashback: bool = False
    transforms: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Treaty:
    id: str
    label: str
    promise: str
    benefit: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    name: str
    companion: str
    place: str
    spell: str
    treaty: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "old_tower": Entity(
        id="old_tower",
        kind="place",
        label="old tower",
        phrase="the old tower on the hill",
        tags={"adventure", "tower"},
    ),
    "river_gate": Entity(
        id="river_gate",
        kind="place",
        label="river gate",
        phrase="the stone gate by the river",
        tags={"adventure", "river"},
    ),
    "moon_dock": Entity(
        id="moon_dock",
        kind="place",
        label="moon dock",
        phrase="the moonlit dock at the edge of town",
        tags={"adventure", "dock"},
    ),
}

SPELLS = {
    "spark_extract": Spell(
        id="spark_extract",
        label="spark extraction magic",
        effect="pull out the stuck clog with a shining tug",
        requires_flashback=True,
        transforms="clean and open",
        tags={"magic", "extraction"},
    ),
    "mirror_shift": Spell(
        id="mirror_shift",
        label="mirror-shift magic",
        effect="change one locked shape into a gentle new shape",
        transforms="transformed",
        tags={"magic", "transformation"},
    ),
    "soft_lift": Spell(
        id="soft_lift",
        label="soft-lift magic",
        effect="lift the heavy piece just enough to free it",
        transforms="freed",
        tags={"magic", "extraction"},
    ),
}

TREATIES = {
    "peace_treaty": Treaty(
        id="peace_treaty",
        label="peace treaty",
        promise="no more sneaking into the gate room without asking first",
        benefit="the guards will help instead of blocking the door",
        tags={"treaty", "adventure"},
    ),
    "work_treaty": Treaty(
        id="work_treaty",
        label="work treaty",
        promise="the team will share the cleaning after the mission",
        benefit="everyone can act together without arguing",
        tags={"treaty", "extraction"},
    ),
}

COMPANIONS = ["fox", "goat", "sparrow", "mapmaker", "little lantern"]

# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------

@dataclass
class World:
    hero: Entity
    companion: Entity
    place: Entity
    clog: Entity
    spell: Spell
    treaty: Treaty
    story: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.story.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def intro(world: World) -> None:
    world.say(
        f"{world.hero.id} was a small brave adventurer who loved clues, hidden doors, and long paths."
    )
    world.say(
        f"One morning, {world.hero.id} and {world.companion.label} went to {world.place.phrase} to solve a problem."
    )


def setup_problem(world: World) -> None:
    world.clog.meters["stuck"] = 1.0
    world.clog.meters["blocked"] = 1.0
    world.say(
        f"Deep inside the tower, the old crapper was blocked by a stubborn stone clog."
    )
    world.say(
        f"Nobody could use it until the clog was gone, and the whole hall smelled sour."
    )


def flashback(world: World) -> None:
    world.hero.memes["worry"] = 1.0
    world.hero.memes["memory"] = 1.0
    world.say(
        f"As {world.hero.id} stared at the stuck crapper, a flashback came back."
    )
    world.say(
        f"Last winter, {world.hero.id} had rushed a job, and the broken mess had spread everywhere."
    )
    world.say(
        f"That memory taught {world.hero.id} to slow down and make a careful plan."
    )


def treaty_scene(world: World) -> None:
    world.hero.memes["hope"] = 1.0
    world.companion.memes["trust"] = 1.0
    world.say(
        f"{world.companion.label.capitalize()} pulled out {world.treaty.label}."
    )
    world.say(
        f"It promised that everyone would share the work, and in return the guards would help."
    )
    world.say(
        f"With the treaty signed, the team could enter the room without a fight."
    )


def cast_spell(world: World) -> None:
    if world.spell.requires_flashback and world.hero.memes.get("memory", 0.0) < 1.0:
        raise StoryError("This spell needs a flashback so the hero learns to be careful first.")
    world.hero.memes["focus"] = 1.0
    world.clog.meters["stuck"] = 0.0
    world.clog.meters["blocked"] = 0.0
    if world.spell.transforms:
        world.clog.tags.add(world.spell.transforms)
    world.say(
        f"{world.hero.id} whispered the spell, and the magic began to glow."
    )
    world.say(
        f"The spell did exactly what was needed: it could {world.spell.effect}."
    )


def transformation(world: World) -> None:
    world.clog.label = "clean passage"
    world.clog.phrase = "a clean, open passage"
    world.clog.meters["clean"] = 1.0
    world.clog.meters["open"] = 1.0
    world.hero.memes["joy"] = 1.0
    world.companion.memes["joy"] = 1.0
    world.say(
        f"With a soft pop, the crapper changed into a clean open passage."
    )
    world.say(
        f"The dark blockage was transformed into a bright path of fresh stone."
    )


def resolution(world: World) -> None:
    world.facts["resolved"] = True
    world.facts["place"] = world.place.label
    world.facts["spell"] = world.spell.id
    world.facts["treaty"] = world.treaty.id
    world.say(
        f"{world.hero.id} and {world.companion.label} stepped back, smiling at the new opening."
    )
    world.say(
        f"Thanks to the treaty, the flashback, and the magic, the adventure ended in peace."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    hero = Entity(id=params.name, kind="character", label=params.name)
    companion = Entity(id=params.companion, kind="character", label=f"the {params.companion}")
    place = SETTINGS[params.place]
    clog = Entity(id="crapper_clog", kind="thing", label="clog", phrase="the stubborn clog")
    spell = SPELLS[params.spell]
    treaty = TREATIES[params.treaty]
    world = World(hero=hero, companion=companion, place=place, clog=clog, spell=spell, treaty=treaty)

    intro(world)
    world.say("")
    setup_problem(world)
    flashback(world)
    treaty_scene(world)
    cast_spell(world)
    transformation(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# Registries for selection / validation
# ---------------------------------------------------------------------------

VALID_COMBOS = [
    ("old_tower", "spark_extract", "work_treaty"),
    ("old_tower", "mirror_shift", "peace_treaty"),
    ("river_gate", "soft_lift", "work_treaty"),
    ("moon_dock", "mirror_shift", "peace_treaty"),
    ("moon_dock", "spark_extract", "work_treaty"),
]

NAMES = ["Mina", "Perry", "Tobi", "Rin", "Luca", "Sana"]
COMPANION_POOL = COMPANIONS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: extraction, crapper, treaty, magic, flashback, transformation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--spell", choices=sorted(SPELLS))
    ap.add_argument("--treaty", choices=sorted(TREATIES))
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANION_POOL)
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
    combos = VALID_COMBOS
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.spell is None or c[1] == args.spell)
        and (args.treaty is None or c[2] == args.treaty)
    ]
    if not filtered:
        raise StoryError("No valid adventure combination matches those choices.")

    place, spell, treaty = rng.choice(filtered)
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANION_POOL)
    return StoryParams(name=name, companion=companion, place=place, spell=spell, treaty=treaty)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f'Write an adventure story about extraction, a crapper, and a treaty, with magic and a flashback.',
        f'Tell a child-friendly quest where {world.hero.id} uses {world.spell.label} to fix a blocked crapper.',
        f'Write a short story that includes a treaty, a flashback, and a transformation at {world.place.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What problem did {world.hero.id} and {world.companion.label} find at {world.place.label}?",
            answer=f"They found a blocked crapper with a stubborn clog, so nobody could use it until it was fixed.",
        ),
        QAItem(
            question=f"Why did {world.hero.id} remember a flashback before using the spell?",
            answer=f"{world.hero.id} remembered a past rushed mistake and decided to be careful before starting the extraction.",
        ),
        QAItem(
            question=f"How did the treaty help the adventure move forward?",
            answer=f"The treaty promised shared work and friendly help, so the guards let the team enter the room peacefully.",
        ),
        QAItem(
            question=f"What changed after the magic worked?",
            answer=f"The clog was extracted and transformed into a clean open passage, so the blocked crapper became usable again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is extraction?",
            answer="Extraction means pulling something out or removing it carefully from where it is stuck.",
        ),
        QAItem(
            question="What is a treaty?",
            answer="A treaty is a promise between sides to follow agreed rules and avoid a fight.",
        ),
        QAItem(
            question="What does magic do in a story?",
            answer="Magic can change things in special ways, like lifting, cleaning, or transforming an object.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory from earlier that comes into the story for a moment.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes from one state or shape into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    clog = world.clog
    return "\n".join([
        "--- trace ---",
        f"hero: {world.hero.id} memes={world.hero.memes}",
        f"companion: {world.companion.label} memes={world.companion.memes}",
        f"place: {world.place.label}",
        f"clog: label={clog.label} meters={clog.meters} tags={sorted(clog.tags)}",
        f"spell: {world.spell.label}",
        f"treaty: {world.treaty.label}",
    ])


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(old_tower). place(river_gate). place(moon_dock).
spell(spark_extract). spell(mirror_shift). spell(soft_lift).
treaty(peace_treaty). treaty(work_treaty).

has_tag(spark_extract, magic). has_tag(spark_extract, extraction).
has_tag(mirror_shift, magic). has_tag(mirror_shift, transformation).
has_tag(soft_lift, magic). has_tag(soft_lift, extraction).

needs_flashback(spark_extract).
valid_combo(old_tower, spark_extract, work_treaty) :- place(old_tower), spell(spark_extract), treaty(work_treaty).
valid_combo(old_tower, mirror_shift, peace_treaty) :- place(old_tower), spell(mirror_shift), treaty(peace_treaty).
valid_combo(river_gate, soft_lift, work_treaty) :- place(river_gate), spell(soft_lift), treaty(work_treaty).
valid_combo(moon_dock, mirror_shift, peace_treaty) :- place(moon_dock), spell(mirror_shift), treaty(peace_treaty).
valid_combo(moon_dock, spark_extract, work_treaty) :- place(moon_dock), spell(spark_extract), treaty(work_treaty).
#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in SPELLS:
        lines.append(asp.fact("spell", s))
    for t in TREATIES:
        lines.append(asp.fact("treaty", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(VALID_COMBOS)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", companion="fox", place="old_tower", spell="spark_extract", treaty="work_treaty"),
        StoryParams(name="Perry", companion="goat", place="river_gate", spell="soft_lift", treaty="work_treaty"),
        StoryParams(name="Rin", companion="sparrow", place="moon_dock", spell="mirror_shift", treaty="peace_treaty"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(*c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
