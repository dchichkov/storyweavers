#!/usr/bin/env python3
"""
Standalone storyworld: a Greek sorting adventure with surprise and reconciliation.

A child goes on a small adventure to sort a mixed pile of Greek-themed items for
a little festival. A surprise mishap makes the task tense, but a thoughtful
reconciliation restores the mood and finishes the sort.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the market square"
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    sort_key: str
    color: str
    origin: str
    owner: str = ""
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    surprise: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTINGS = {
    "square": Setting(place="the market square", affords={"sort"}),
    "harbor": Setting(place="the little harbor", affords={"sort"}),
    "museum": Setting(place="the museum courtyard", affords={"sort"}),
    "garden": Setting(place="the garden patio", affords={"sort"}),
}

GIRL_NAMES = ["Mina", "Zoe", "Lina", "Iris", "Nora", "Hera"]
BOY_NAMES = ["Theo", "Niko", "Ari", "Leo", "Dimitri", "Oren"]
TRAITS = ["brave", "curious", "lively", "gentle", "spirited", "bold"]


ITEMS = {
    "amphora": Thing("amphora", "amphora", "a painted amphora", "vase", "blue", "Greece"),
    "laurel": Thing("laurel", "laurel wreath", "a green laurel wreath", "crown", "green", "Greece"),
    "coin": Thing("coin", "coin", "an old bronze coin", "money", "bronze", "Greece"),
    "tile": Thing("tile", "tile", "a bright mosaic tile", "stone", "red", "Greece"),
    "shell": Thing("shell", "shell", "a sea shell", "sea", "white", "sea"),
}

SORT_BINS = {
    "vase": "the vase basket",
    "crown": "the wreath tray",
    "money": "the coin bowl",
    "stone": "the stone pile",
    "sea": "the sea basket",
}

SURPRISES = {
    "wind": "a sudden wind blew through the square",
    "spill": "a splash of water tipped the sorting table",
    "cat": "a curious cat leaped onto the cloth",
    "crowd": "a laughing crowd crowded close to watch",
}

ASP_RULES = r"""
item(I) :- item_name(I).
sort_key(I,K) :- item_sort(I,K).
fits_bin(I,B) :- sort_key(I,K), bin_for(K,B).
valid(I,B) :- fits_bin(I,B).

surprising(S) :- surprise_name(S).
can_reconcile(I,S) :- valid(I,_), surprising(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_name", iid))
        lines.append(asp.fact("item_sort", iid, item.sort_key))
        lines.append(asp.fact("bin_for", item.sort_key, SORT_BINS[item.sort_key]))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise_name", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(iid, SORT_BINS[item.sort_key]) for iid, item in ITEMS.items()}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} valid item/bin pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Greek sorting adventure with surprise and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def valid_choices() -> list[tuple[str, str]]:
    return [(place, sid) for place in SETTINGS for sid in SURPRISES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_choices()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.surprise:
        combos = [c for c in combos if c[1] == args.surprise]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    place, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent, surprise=surprise)


def _sort_label(item: Thing) -> str:
    return SORT_BINS[item.sort_key]


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}", meters={}, memes={}))
    world.facts.update(hero=hero, parent=parent, params=params)

    chosen = [ITEMS["amphora"], ITEMS["laurel"], ITEMS["coin"], ITEMS["tile"], ITEMS["shell"]]
    world.facts["items"] = chosen

    world.say(f"{hero.id} was a {rng_trait(hero.id)} {hero.type} who loved little adventures.")
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.label.rstrip()} went to {world.setting.place} to sort Greek treasures into neat piles."
    )
    world.say(
        f"{hero.id} liked the painted amphora, the laurel wreath, the bronze coin, the mosaic tile, and the sea shell, because each one felt like a tiny story."
    )

    world.para()
    world.say(
        f"At the table, {hero.id} began to sort the items by shape and home: vases together, wreaths together, coins together, stones together, and sea things together."
    )
    world.say(
        f"Then {SURPRISES[params.surprise]}. {hero.id} gasped, and the tidy piles slipped apart."
    )
    hero.memes["surprise"] = 1
    hero.memes["worry"] = 1
    hero.meters["scattered"] = 1

    world.para()
    world.say(
        f"{hero.id} wanted to cry, but {hero.pronoun('possessive')} {parent.label.rstrip()} smiled and said, \"We can fix this together.\""
    )
    world.say(
        f"So they made a new game: first gather each thing, then place it in the right basket again."
    )
    hero.memes["reconciliation"] = 1
    hero.memes["joy"] = 1
    hero.meters["sorted"] = 1
    world.say(
        f"In the end, {hero.id} sorted the amphora with the vase basket, the laurel wreath with the tray, the coin with the bowl, the tile with the stone pile, and the shell with the sea basket."
    )
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.label.rstrip()} laughed side by side, and the whole courtyard looked brave and peaceful again."
    )

    world.facts["sorted_bins"] = {item.id: _sort_label(item) for item in chosen}
    return world


def rng_trait(name: str) -> str:
    return TRAITS[sum(ord(c) for c in name) % len(TRAITS)]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    return [
        f'Write a short adventure story about {hero.id} sorting Greek treasures at {p.place} when an unexpected surprise interrupts the work.',
        f'Create a child-friendly story where a {hero.type} named {hero.id} learns to sort amphorae, laurel wreaths, coins, tiles, and shells, then reconciles with a helper after a mishap.',
        f'Write a gentle adventure with the words "sort", "Greek", "surprise", and "reconciliation" in which a child restores order after a sudden distraction.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    surprise = SURPRISES[p.surprise]
    return [
        QAItem(
            question=f"Where did {hero.id} go to sort the Greek treasures?",
            answer=f"{hero.id} went to {world.setting.place} with {hero.pronoun('possessive')} {parent.label.split()[-1]} to sort the Greek treasures.",
        ),
        QAItem(
            question=f"What happened to interrupt the sorting adventure?",
            answer=f"{surprise.capitalize()}, which made the neat piles slip apart and gave the story its surprise.",
        ),
        QAItem(
            question=f"How did {hero.id} and {hero.pronoun('possessive')} {parent.label.split()[-1]} fix the problem?",
            answer=f"They reconciled by working together, gathering the items again, and putting each one back in the right basket.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"The courtyard ended peaceful and tidy, with {hero.id} laughing beside {hero.pronoun('possessive')} {parent.label.split()[-1]} after the sort was finished.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to sort things?",
            answer="To sort things means to put objects into groups that go together, like by shape, size, color, or purpose.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you are not ready for it.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement or a problem.",
        ),
        QAItem(
            question="What is Greek in this story?",
            answer="Greek means it comes from Greece or is inspired by the people, places, and objects from Greece.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="square", name="Mina", gender="girl", parent="mother", surprise="wind"),
    StoryParams(place="harbor", name="Theo", gender="boy", parent="father", surprise="spill"),
    StoryParams(place="museum", name="Iris", gender="girl", parent="mother", surprise="cat"),
    StoryParams(place="garden", name="Ari", gender="boy", parent="father", surprise="crowd"),
]


def asp_facts_and_rules(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_facts_and_rules("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify_stub() -> int:
    return asp_verify()


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
        print(asp_facts_and_rules("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify_stub())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid item/bin pairs:\n")
        for iid, b in pairs:
            print(f"  {iid:8} -> {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: sort at {p.place} (surprise: {p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
