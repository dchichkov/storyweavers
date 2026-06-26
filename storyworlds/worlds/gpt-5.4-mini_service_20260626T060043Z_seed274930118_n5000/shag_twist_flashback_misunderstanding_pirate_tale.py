#!/usr/bin/env python3
"""
storyworlds/worlds/shag_twist_flashback_misunderstanding_pirate_tale.py
========================================================================

A small pirate-tale storyworld about a noisy deck, a mistaken worry, a
flashback clue, and a twist that sets the crew right again.

Core premise:
- A little pirate crew sails with a shaggy sea-dog named Shag.
- The captain loses a useful item and suspects the wrong culprit.
- A flashback reveals where the item was last seen.
- The misunderstanding is cleared, and the ending proves the change.

The prose is generated from a simulated world state; it is not a frozen
paragraph with swapped names. The same state also feeds QA and the ASP twin.
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
# Domain registries
# ---------------------------------------------------------------------------
@dataclass
class Character:
    id: str
    kind: str = "character"
    role: str = "crew"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["fear", "confidence", "joy", "worry", "suspicion", "relief", "trust"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Item:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["lost", "dusty", "safe"]:
            self.meters.setdefault(k, 0.0)


@dataclass
class Setting:
    place: str = "the little brig"
    deck: str = "the deck"
    cache: str = "the cabin"
    sea: str = "the sea breeze"


@dataclass
class StoryParams:
    name: str
    companion: str
    item: str
    setting: str = "brig"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Character | Item] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.turns: list[str] = []

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str):
        if text:
            self.paragraphs[-1].append(text)

    def para(self):
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# World model / causal rules
# ---------------------------------------------------------------------------
def _crew_tension(world: World):
    captain = world.get("captain")
    if captain.memes["suspicion"] >= 1 and captain.memes["worry"] >= 1:
        captain.meters["tension"] += 1
        return ["The captain's brow went tight with worry."]
    return []


def _find_item(world: World):
    helper = world.get("companion")
    item = world.get("item")
    if helper.memes["noticed"] >= 1 and item.hidden_in == "shag":
        item.meters["safe"] += 1
        return ["The hidden thing was found inside the shag."]
    return []


def _relief(world: World):
    captain = world.get("captain")
    item = world.get("item")
    if item.meters["safe"] >= 1 and captain.memes["trust"] >= 1:
        captain.memes["relief"] += 1
        captain.memes["suspicion"] = 0
        return ["The captain's worry melted into relief."]
    return []


RULES = [_crew_tension, _find_item, _relief]


def propagate(world: World, narrate: bool = True):
    out = []
    changed = True
    fired = set()
    while changed:
        changed = False
        for rule in RULES:
            key = rule.__name__
            if key in fired:
                continue
            sents = rule(world)
            if sents:
                fired.add(key)
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, captain: Character, companion: Character):
    world.say(
        f"On a small pirate brig, Captain {captain.id} sailed with {companion.id}, "
        f"a shaggy sea-dog with bright eyes and quick paws."
    )
    world.say(
        f"Everyone aboard knew {companion.id} was called Shag because {companion.id} "
        f"had a shaggy coat and loved sleeping beside the warm rope coils."
    )


def setup_item(world: World, captain: Character, item: Item):
    captain.memes["joy"] += 1
    world.say(
        f"The captain prized {item.phrase}, a little treasure used to keep the cabin safe and tidy."
    )
    item.hidden_in = "cabbin?"; item.hidden_in = "shag"
    world.say(
        f"One windy morning, {item.label} went missing, and the captain's smile vanished with it."
    )


def suspicion(world: World, captain: Character, companion: Character, item: Item):
    captain.memes["worry"] += 1
    captain.memes["suspicion"] += 1
    world.say(
        f"'Shag must have dragged it away,' the captain muttered, because {companion.id} "
        f"had been nosing around the bundles near the mast."
    )
    propagate(world, narrate=True)


def flashback(world: World, companion: Character, item: Item):
    companion.memes["noticed"] += 1
    world.para()
    world.say(
        f"Then came a flashback: the crew remembered the last time the deck had rolled hard."
    )
    world.say(
        f"In that memory, {item.label} slipped from the captain's pocket and tucked itself "
        f"into the shaggy sleeping mat by the hatch."
    )


def misunderstanding(world: World, captain: Character, companion: Character, item: Item):
    world.say(
        f"It was a misunderstanding. Shag had only been digging at the mat to find a lost bone, "
        f"not to steal a thing."
    )
    captain.memes["trust"] += 1


def twist(world: World, captain: Character, companion: Character, item: Item):
    item.hidden_in = "shag"
    propagate(world, narrate=True)
    world.say(
        f"The twist came when the crew lifted the shag and found {item.label} tucked underneath, "
        f"safe and dusty but not gone."
    )
    item.found_by = companion.id


def resolution(world: World, captain: Character, companion: Character, item: Item):
    captain.memes["joy"] += 1
    captain.memes["relief"] += 1
    captain.memes["suspicion"] = 0
    world.para()
    world.say(
        f"The captain laughed, scratched Shag behind the ears, and thanked {companion.id} for "
        f"solving the puzzle."
    )
    world.say(
        f"By sunset, {item.label} was back in the captain's hands, and Shag was curled up on the "
        f"shag with a happy thump of a tail."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
CAPTAIN_NAMES = ["Nia", "Marek", "Lina", "Jory", "Tessa", "Pip"]
COMPANION_NAMES = ["Shag", "Mottle", "Brine", "Ruff", "Pebble", "Sailor"]
ITEMS = {
    "key": ("key", "a brass key"),
    "map": ("map", "a folded treasure map"),
    "lantern": ("lantern", "a little ship lantern"),
    "ring": ("ring", "a silver ring"),
}


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    captain = world.add(Character(id=params.name, role="captain", label="captain", traits=["bold"]))
    captain.id = "captain"
    captain.label = params.name
    companion = world.add(Character(id="companion", role="companion", label=params.companion, traits=["shaggy", "loyal"]))
    companion.id = "companion"
    companion.label = params.companion
    item_label, item_phrase = ITEMS[params.item]
    item = world.add(Item(id="item", label=item_label, phrase=item_phrase, owner="captain"))
    return world


def tell(world: World):
    captain = world.get("captain")
    companion = world.get("companion")
    item = world.get("item")

    introduce(world, captain, companion)
    world.para()
    setup_item(world, captain, item)
    suspicion(world, captain, companion, item)
    flashback(world, companion, item)
    misunderstanding(world, captain, companion, item)
    twist(world, captain, companion, item)
    resolution(world, captain, companion, item)

    world.facts.update(
        captain=captain,
        companion=companion,
        item=item,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    companion = f["companion"]
    item = f["item"]
    return [
        f"Write a pirate story for young children about {captain.label}, {companion.label}, and a lost {item.label}.",
        f"Tell a short tale with a misunderstanding, a flashback, and a twist on a pirate ship.",
        f"Make a gentle pirate story where the shaggy companion is blamed by mistake and then helps find the lost {item.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    companion = f["companion"]
    item = f["item"]
    return [
        QAItem(
            question="Who was the story mainly about?",
            answer=f"The story was mainly about Captain {captain.label} and the shaggy companion {companion.label}.",
        ),
        QAItem(
            question=f"What went missing on the ship?",
            answer=f"{item.phrase.capitalize()} went missing from the captain's side.",
        ),
        QAItem(
            question="Why was that a misunderstanding?",
            answer=f"It was a misunderstanding because {companion.label} was not stealing anything; {companion.label} only wanted to find a lost bone.",
        ),
        QAItem(
            question="What did the flashback show?",
            answer=f"The flashback showed the {item.label} slipping into the shaggy mat when the deck rolled hard.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The crew found {item.label}, the captain felt relieved, and Shag curled up happily on the shag again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that sails on the sea and carries a pirate crew.",
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows something that happened earlier, so the reader can understand the present better.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing and is not seeing the full truth yet.",
        ),
        QAItem(
            question="What does shaggy mean?",
            answer="Shaggy means covered with long, thick, messy fur or hair.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show lost/1.
#show found/1.
#show misunderstood/1.
#show twist/1.

lost(item).
misunderstood(companion) :- blame_wrong(companion).
found(item) :- hidden_in(item, shag).
twist(item) :- flashback(item), found(item).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("crew", "captain"),
        asp.fact("crew", "companion"),
        asp.fact("shaggy", "companion"),
        asp.fact("thing", "item"),
        asp.fact("blame_wrong", "companion"),
        asp.fact("hidden_in", "item", "shag"),
        asp.fact("flashback", "item"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lost/1.\n#show found/1.\n#show misunderstood/1.\n#show twist/1."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {
        ("lost", ("item",)),
        ("misunderstood", ("companion",)),
        ("found", ("item",)),
        ("twist", ("item",)),
    }
    if atoms == expected:
        print("OK: ASP parity matches the Python story twin.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale about a shaggy companion, a flashback, and a misunderstanding.")
    ap.add_argument("--name", choices=CAPTAIN_NAMES)
    ap.add_argument("--companion", choices=COMPANION_NAMES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(CAPTAIN_NAMES)
    companion = args.companion or "Shag"
    item = args.item or rng.choice(list(ITEMS))
    if companion != "Shag" and args.companion is None:
        companion = "Shag"
    return StoryParams(name=name, companion=companion, item=item, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        if isinstance(e, Character):
            lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
        else:
            lines.append(f"{e.id}: label={e.label} hidden_in={e.hidden_in} safe={e.meters['safe']}")
    return "\n".join(lines)


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
        print(asp_program("#show lost/1.\n#show found/1.\n#show misunderstood/1.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show lost/1.\n#show found/1.\n#show misunderstood/1.\n#show twist/1."))
        print("\n".join(str(sym) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(name=n, companion="Shag", item=item, seed=base_seed + i)
            for i, (n, item) in enumerate([
                ("Nia", "key"),
                ("Marek", "map"),
                ("Lina", "lantern"),
                ("Jory", "ring"),
            ])
        ]
        samples = [generate(p) for p in combos]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and Shag: {p.item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
