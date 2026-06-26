#!/usr/bin/env python3
"""
storyworlds/worlds/somewhere_distress_reconciliation_cautionary_heartwarming.py
==============================================================================

A small heartwarming storyworld about something going missing somewhere,
distress rising, a cautious search, and reconciliation at the end.

Seed-tale premise:
- A child leaves a beloved small treasure somewhere.
- Nobody can find it right away, and the child feels distress.
- A parent encourages a calm, careful search instead of panicking.
- The missing thing is found through honest conversation.
- A misunderstanding is repaired with an apology and a hug.

This world is intentionally small and constraint-driven:
- only plausible combinations are generated
- the story changes from world state, not from a frozen template
- the ending proves what changed in the world
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    found_at: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    search_zones: tuple[str, ...] = ("kitchen", "hall", "yard")
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectWish:
    id: str
    label: str
    phrase: str
    risk_zone: str
    can_hide: set[str]
    cue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    wish: str
    name: str
    gender: str
    parent: str
    sibling: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "home": Setting(place="home", indoors=True, search_zones=("kitchen", "hall", "sofa", "bedroom"), affords={"search"}),
    "garden": Setting(place="the garden", indoors=False, search_zones=("path", "bushes", "shed"), affords={"search"}),
    "school": Setting(place="the school", indoors=True, search_zones=("classroom", "cloakroom", "play corner"), affords={"search"}),
}

WISHES = {
    "bear": ObjectWish(
        id="bear",
        label="teddy bear",
        phrase="a soft brown teddy bear with one red ribbon",
        risk_zone="somewhere",
        can_hide={"sofa", "bedroom", "cloakroom"},
        cue="teddy",
        tags={"toy", "soft"},
    ),
    "snackbox": ObjectWish(
        id="snackbox",
        label="snack box",
        phrase="a little blue snack box with stars on it",
        risk_zone="somewhere",
        can_hide={"kitchen", "hall", "classroom"},
        cue="snack",
        tags={"food", "box"},
    ),
    "key": ObjectWish(
        id="key",
        label="house key",
        phrase="a tiny silver house key on a green string",
        risk_zone="somewhere",
        can_hide={"kitchen", "hall", "yard"},
        cue="key",
        tags={"metal", "key"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Iris", "Maya"]
BOY_NAMES = ["Theo", "Noah", "Finn", "Eli", "Ben", "Leo"]
TRAITS = ["careful", "gentle", "brave", "curious", "quiet", "bright"]


# ---------------------------------------------------------------------------
# Helper logic
# ---------------------------------------------------------------------------
def pronoun_word(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for setting_id, setting in SETTINGS.items():
        if "search" not in setting.affords:
            continue
        for wish_id, wish in WISHES.items():
            if setting.place == "home" and wish_id == "key":
                combos.append((setting_id, wish_id))
            elif setting.place != "home":
                combos.append((setting_id, wish_id))
    return combos


def explain_rejection(setting_id: str, wish_id: str) -> str:
    return (
        f"(No story: the combination of {setting_id!r} and {wish_id!r} does not "
        f"leave enough room for a believable somewhere-distress-search-reconciliation arc.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def initialize_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    wish = WISHES[params.wish]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"calm": 1.0}, memes={"love": 1.0}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}", meters={"calm": 1.0}, memes={"care": 1.0}))
    sibling = world.add(Entity(id="sibling", kind="character", type="boy", label=f"the {params.sibling}", meters={"calm": 1.0}, memes={"care": 0.5}))
    item = world.add(Entity(
        id=wish.id,
        kind="thing",
        type=wish.id,
        label=wish.label,
        phrase=wish.phrase,
        owner=hero.id,
        caretaker=parent.id,
        hidden=True,
        found_at="somewhere",
        meters={"lost": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, sibling=sibling, item=item, wish=wish, setting=setting)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    sibling: Entity = f["sibling"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    wish: ObjectWish = f["wish"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]

    world.say(f"{hero.id} was a {next(t for t in [hero.type, hero.type] if True)} child who loved {wish.label}.")
    world.say(f"One day, {hero.id} put {hero.pronoun('possessive')} {item.label} down somewhere and did not remember where.")
    world.say(f"{sibling.label} was nearby, and {parent.label} was busy making sure everything at {setting.place} stayed calm and kind.")


def search_turn(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    sibling: Entity = f["sibling"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    wish: ObjectWish = f["wish"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]

    hero.memes["distress"] = hero.memes.get("distress", 0.0) + 1.0
    hero.meters["tension"] = hero.meters.get("tension", 0.0) + 1.0

    world.para()
    world.say(f"At first, {hero.id} felt distress and wanted to hurry, but {parent.label} held up a gentle hand.")
    world.say(f'"Let\'s look carefully," {parent.label} said. "If we rush, we may miss it somewhere."')
    world.say(f"So they searched the {setting.place} slowly, checking the {", ".join(setting.search_zones[:-1])} and the {setting.search_zones[-1]} one by one.")

    # Sibling accidentally caused the misunderstanding.
    sibling.memes["guilt"] = sibling.memes.get("guilt", 0.0) + 1.0
    item.hidden = False
    item.found_at = setting.search_zones[0]
    sibling.meters["noticed"] = sibling.meters.get("noticed", 0.0) + 1.0
    hero.memes["blame"] = hero.memes.get("blame", 0.0) + 1.0
    world.say(f"Then {sibling.label} blushed and admitted that {sibling.pronoun('subject')} had moved the {item.label} to {item.found_at} earlier, trying to keep it safe.")
    world.say(f"{hero.id} looked upset for a moment, because the missing {wish.label} had felt much bigger than it was.")

    # Reconciliation.
    world.para()
    hero.memes["distress"] = 0.0
    hero.memes["forgiveness"] = hero.memes.get("forgiveness", 0.0) + 1.0
    sibling.memes["guilt"] = 0.0
    parent.memes["joy"] = parent.memes.get("joy", 0.0) + 1.0
    world.say(f"{parent.label} helped everyone breathe again, and {sibling.label} said sorry in a small, honest voice.")
    world.say(f"{hero.id} forgave {sibling.pronoun('object')} right away, and the two of them found the {item.label} together.")
    world.say(f"At the end, the {item.label} was safe, the worry was gone, and the whole room felt warm and quiet again.")


def build_story(params: StoryParams) -> World:
    world = initialize_world(params)
    narrate_setup(world)
    search_turn(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(home). setting(garden). setting(school).
affords(home,search). affords(garden,search). affords(school,search).

wish(bear). wish(snackbox). wish(key).

valid(Setting,Wish) :- setting(Setting), wish(Wish).
valid(Setting,Wish) :- setting(Setting), wish(Wish), Setting = home, Wish = key.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for act in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, act))
    for wid in WISHES:
        lines.append(asp.fact("wish", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP and Python agree on {len(asp_set)} valid combos.")
        return 0
    print("MISMATCH:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    wish: ObjectWish = f["wish"]  # type: ignore[assignment]
    return [
        f'Write a heartwarming story for a young child about someone who loses a {wish.label} somewhere and then finds it again.',
        f"Tell a cautionary but gentle story where {hero.id} learns not to panic when a beloved {item.label} goes missing at {setting.place}.",
        f"Write a short story that includes the word 'somewhere' and ends in reconciliation after a worried search.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    sibling: Entity = f["sibling"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    wish: ObjectWish = f["wish"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was {hero.id} worried about at {setting.place}?",
            answer=f"{hero.id} was worried about {hero.pronoun('possessive')} missing {item.label}. It had been put down somewhere, so nobody could see it right away.",
        ),
        QAItem(
            question=f"Who helped keep the search calm when the distress started?",
            answer=f"{parent.label} helped keep the search calm. {parent.label.capitalize()} told everyone to look carefully instead of rushing.",
        ),
        QAItem(
            question=f"What did {sibling.label} do that helped solve the problem?",
            answer=f"{sibling.label} admitted that {sibling.pronoun('subject')} had moved the {item.label} to {item.found_at} earlier. That honest explanation made the misunderstanding go away.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {sibling.label}?",
            answer=f"They forgave each other and found the {wish.label} together. The ending was warm, peaceful, and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    wish: ObjectWish = f["wish"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What does 'somewhere' mean?",
            answer="Somewhere means an unknown place. It tells you that a thing exists, but you do not yet know exactly where it is.",
        ),
        QAItem(
            question="What is distress?",
            answer="Distress is a strong feeling of worry or upset, like when something important seems lost or unsafe.",
        ),
        QAItem(
            question=f"Why can a {wish.label} be easy to misplace?",
            answer=f"A {wish.label} can be easy to misplace because it is small and can blend into a couch, shelf, bag, or other quiet spot.",
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming cautionary storyworld about distress, somewhere, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--sibling", choices=["older sister", "older brother", "little sister", "little brother"])
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
    combos = valid_combos()
    if args.setting and args.wish and (args.setting, args.wish) not in combos:
        raise StoryError(explain_rejection(args.setting, args.wish))
    valid = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.wish is None or c[1] == args.wish)
    ]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    setting, wish = rng.choice(sorted(valid))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or select_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    sibling = args.sibling or rng.choice(["older sister", "older brother", "little sister", "little brother"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, wish=wish, name=name, gender=gender, parent=parent, sibling=sibling, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.hidden:
            parts.append("hidden=True")
        if e.found_at:
            parts.append(f"found_at={e.found_at}")
        lines.append(f"{e.id}: {', '.join(parts)}")
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} valid setting/wish combos:")
        for s, w in combos:
            print(f"  {s:7} {w}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="home", wish="bear", name="Mina", gender="girl", parent="mother", sibling="older brother", trait="gentle"),
            StoryParams(setting="garden", wish="key", name="Theo", gender="boy", parent="father", sibling="little sister", trait="careful"),
            StoryParams(setting="school", wish="snackbox", name="Ava", gender="girl", parent="mother", sibling="older sister", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
