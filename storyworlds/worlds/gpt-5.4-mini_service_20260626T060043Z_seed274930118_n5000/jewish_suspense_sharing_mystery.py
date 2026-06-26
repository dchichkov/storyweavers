#!/usr/bin/env python3
"""
A standalone storyworld for a small Jewish suspense/sharing mystery.

Premise:
- A Jewish child is at a special family meal.
- A small mystery creates suspense: a shared treat or ritual item seems to be missing.
- The family searches together, shares clues, and ends with a warm, concrete reveal.

The world is designed to produce a complete, child-facing story with:
- a clear setup,
- a suspenseful middle,
- a turn that uses sharing,
- and a resolved ending image.

It follows the Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

# Physical meters / emotional memes are tracked on entities.
# meters: hidden, searched, shared, found, warm, hungry
# memes: worry, curiosity, joy, trust, suspense, generosity

# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_label: str
    missing_phrase: str
    hide_place: str
    clue_place: str
    suspense_word: str
    share_item: str
    resolution_image: str
    tags: set[str] = field(default_factory=set)


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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------

SETTINGS = {
    "seder_table": Setting(
        place="the Seder table",
        detail="The room was bright with candles, folded napkins, and a plate waiting in the middle.",
        affords={"search", "share", "wait"},
    ),
    "kitchen": Setting(
        place="the kitchen",
        detail="The kitchen smelled like warm soup and fresh bread.",
        affords={"search", "share", "wait"},
    ),
}

MYSTERIES = {
    "afikoman": Mystery(
        id="afikoman",
        missing_label="afikoman",
        missing_phrase="the hidden piece of matzah",
        hide_place="under the blue cushion",
        clue_place="the napkin basket",
        suspense_word="mystery",
        share_item="another piece of matzah",
        resolution_image="the hidden matzah piece under the blue cushion",
        tags={"jewish", "matzah", "passover", "sharing", "mystery", "suspense"},
    ),
    "honey_cake": Mystery(
        id="honey_cake",
        missing_label="honey cake slice",
        missing_phrase="the sweet slice of honey cake",
        hide_place="inside the covered cake box",
        clue_place="the cookbook stand",
        suspense_word="secret",
        share_item="a second slice of honey cake",
        resolution_image="the cake box with a ribbon still tied around it",
        tags={"jewish", "cake", "sharing", "mystery", "suspense"},
    ),
    "candle_match": Mystery(
        id="candle_match",
        missing_label="matchbox",
        missing_phrase="the little matchbox for the candles",
        hide_place="behind the tea tin",
        clue_place="the windowsill",
        suspense_word="clue",
        share_item="a spare candle",
        resolution_image="the matchbox hiding behind the tea tin",
        tags={"jewish", "candles", "sharing", "mystery", "suspense"},
    ),
}

NAMES = ["Noa", "Mira", "Leah", "Ari", "Eli", "Sara", "Tali", "David"]
TRAITS = ["curious", "gentle", "brave", "quiet", "bright", "careful"]

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is reasonable when the missing item belongs in the chosen setting.
reasonable(S, M) :- setting(S), mystery(M), place_of(M, S).

% A sharing ending is possible if the story has a shared item and a clue.
has_share(M) :- mystery(M), shared_item(M, _).
has_clue(M) :- mystery(M), clue_place(M, _).

valid_story(S, M, G) :- reasonable(S, M), has_share(M), has_clue(M), gender_ok(M, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("place_of", mid, "seder_table" if mid == "afikoman" else "kitchen"))
        lines.append(asp.fact("shared_item", mid, m.share_item))
        lines.append(asp.fact("clue_place", mid, m.clue_place))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
        lines.append(asp.fact("gender_ok", mid, "girl"))
        lines.append(asp.fact("gender_ok", mid, "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set((s, m, g) for (s, m, g) in asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            combos.append((sid, mid, "any"))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen options do not make a clear Jewish mystery with a real sharing ending.)"


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["jewish", params.trait, "little"],
        meters={"search": 0.0},
        memes={"curiosity": 1.0, "suspense": 0.0, "joy": 0.0, "trust": 0.0, "worry": 0.0, "generosity": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"share": 0.0},
        memes={"worry": 0.0, "trust": 1.0, "generosity": 1.0},
    ))
    missing = world.add(Entity(
        id="Missing",
        type="thing",
        label=mystery.missing_label,
        phrase=mystery.missing_phrase,
        hidden_in=mystery.hide_place,
        owner=hero.id,
        meters={"hidden": 1.0, "found": 0.0},
    ))
    clue = world.add(Entity(
        id="Clue",
        type="thing",
        label="clue",
        phrase=f"a tiny clue near {mystery.clue_place}",
        meters={"shared": 0.0},
    ))
    share = world.add(Entity(
        id="ShareItem",
        type="thing",
        label=mystery.share_item,
        phrase=mystery.share_item,
        meters={"shared": 0.0},
    ))

    world.facts.update(hero=hero, parent=parent, missing=missing, clue=clue, share=share, mystery=mystery)
    return world


def _suspense(world: World, hero: Entity, parent: Entity, missing: Entity, mystery: Mystery) -> None:
    hero.memes["suspense"] += 1.0
    parent.memes["worry"] += 1.0
    world.say(
        f"At {world.setting.place}, {hero.id} noticed something was missing: {mystery.missing_phrase}."
    )
    world.say(
        f"{hero.id} looked once, then twice, and the room felt full of {mystery.suspense_word}s."
    )


def _share_clues(world: World, hero: Entity, parent: Entity, clue: Entity, mystery: Mystery) -> None:
    hero.meters["search"] += 1.0
    clue.meters["shared"] += 1.0
    hero.memes["curiosity"] += 1.0
    world.say(
        f"{hero.id} and {parent.label} shared clues quietly, checking {mystery.clue_place} together."
    )
    world.say(
        f"That made the search feel less scary, because they were looking as a family."
    )


def _find(world: World, hero: Entity, missing: Entity, mystery: Mystery) -> None:
    missing.meters["found"] = 1.0
    hero.memes["joy"] += 1.0
    world.say(
        f"Then {hero.id} spotted {mystery.resolution_image}."
    )


def _share_ending(world: World, hero: Entity, parent: Entity, share: Entity, missing: Entity) -> None:
    hero.memes["generosity"] += 1.0
    parent.memes["trust"] += 1.0
    share.meters["shared"] = 1.0
    world.say(
        f"{parent.label} shared {share.label} with {hero.id}, and everyone smiled."
    )
    world.say(
        f"In the end, the missing thing was back on the table, and the room felt warm and calm again."
    )


def tell(world: World) -> World:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    missing: Entity = f["missing"]
    clue: Entity = f["clue"]
    share: Entity = f["share"]
    mystery: Mystery = f["mystery"]

    world.say(
        f"At {world.setting.place}, a Jewish family sat together in the soft light."
    )
    world.say(
        f"{hero.id} liked this night because everyone stayed close and listened carefully."
    )

    world.para()
    _suspense(world, hero, parent, missing, mystery)

    world.para()
    _share_clues(world, hero, parent, clue, mystery)

    world.para()
    _find(world, hero, missing, mystery)
    _share_ending(world, hero, parent, share, missing)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short Jewish suspense story for a small child about {hero.id} and {mystery.missing_label}.',
        f"Tell a gentle mystery where a family shares clues and finds {mystery.missing_phrase}.",
        f"Write a child-facing story with suspense, sharing, and a warm ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    mystery: Mystery = f["mystery"]
    missing: Entity = f["missing"]
    share: Entity = f["share"]
    return [
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was that {mystery.missing_phrase} seemed to be missing from {world.setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for it?",
            answer=f"{hero.id} looked with {parent.label}, and they shared clues together.",
        ),
        QAItem(
            question=f"What did the family share at the end?",
            answer=f"They shared {share.label}, and the missing {missing.label} was found again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.facts["mystery"]
    qas = []
    if "jewish" in mystery.tags:
        qas.append(QAItem(
            question="What does Jewish mean?",
            answer="Jewish means connected to the Jewish people, their family life, faith, and traditions.",
        ))
    qas.append(QAItem(
        question="What is a mystery?",
        answer="A mystery is something puzzling that people try to figure out by looking for clues.",
    ))
    qas.append(QAItem(
        question="What does sharing mean?",
        answer="Sharing means letting other people use, enjoy, or have some of something too.",
    ))
    qas.append(QAItem(
        question="What is suspense in a story?",
        answer="Suspense is the worried, excited feeling you get when you do not know what will happen next.",
    ))
    return qas


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="seder_table", mystery="afikoman", name="Noa", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="seder_table", mystery="afikoman", name="Eli", gender="boy", parent="father", trait="careful"),
    StoryParams(setting="kitchen", mystery="honey_cake", name="Mira", gender="girl", parent="mother", trait="bright"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Jewish suspense/sharing mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(build_world(params))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:\n")
        for s, m, g in triples:
            print(f"  {s:12} {m:12} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
