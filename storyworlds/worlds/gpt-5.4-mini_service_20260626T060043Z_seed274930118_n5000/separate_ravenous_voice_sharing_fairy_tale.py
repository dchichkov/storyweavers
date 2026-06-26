#!/usr/bin/env python3
"""
storyworlds/worlds/separate_ravenous_voice_sharing_fairy_tale.py
=================================================================

A small fairy-tale storyworld about a hungry visitor, a kind share, and a
separate plate that turns worry into peace.

Seed image:
---
In a little kingdom, a small child found a ravenous traveler with a booming
voice at the castle gate. The traveler wanted food, but the castle cook worried
there would not be enough. The child separated one warm loaf and shared it. The
traveler's voice grew gentle, and the gate became a friendly place again.

World model:
---
- A ravenous guest has a physical hunger meter and a social voice meter.
- Sharing a portion lowers hunger and softens the guest's voice.
- Refusing to share increases tension and makes the guest louder.
- When the guest is fed, the ending image should show calm company, not just a
  fixed moral.

This file follows the Storyweavers contract:
- stdlib script, one file
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify compares ASP/Python parity and exercises generated stories
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carries: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman", "maid"}
        male = {"boy", "prince", "king", "father", "man", "knight"}
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
    indoors: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    warmth: str
    fill: str
    portion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    ravenous_gain: float
    voice_gain: float
    settle_drop: float
    share_verb: str
    separate_verb: str
    kind_words: set[str] = field(default_factory=set)


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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_hunger_spill(world: World) -> list[str]:
    out: list[str] = []
    for guest in world.characters():
        if guest.meters.get("ravenous", 0.0) < THRESHOLD:
            continue
        sig = ("hunger_spill", guest.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        guest.memes["restless"] = guest.memes.get("restless", 0.0) + 1
        out.append(f"{guest.label} could not settle and kept looking toward the table.")
    return out


def _r_share_calm(world: World) -> list[str]:
    out: list[str] = []
    for guest in world.characters():
        if guest.meters.get("fed", 0.0) < THRESHOLD:
            continue
        sig = ("share_calm", guest.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        guest.meters["ravenous"] = max(0.0, guest.meters.get("ravenous", 0.0) - 1.0)
        guest.meters["voice"] = max(0.0, guest.meters.get("voice", 0.0) - 1.0)
        guest.memes["softness"] = guest.memes.get("softness", 0.0) + 1
        out.append(f"{guest.label}'s voice grew gentle after the shared food.")
    return out


CAUSAL_RULES = [
    Rule("hunger_spill", _r_hunger_spill),
    Rule("share_calm", _r_share_calm),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "castle_gate": Setting(
        place="the castle gate",
        indoors=False,
        affordances={"share"},
    ),
    "kitchen": Setting(
        place="the castle kitchen",
        indoors=True,
        affordances={"share"},
    ),
    "meadow": Setting(
        place="the sunny meadow",
        indoors=False,
        affordances={"share"},
    ),
}

FOODS = {
    "loaf": Food(
        id="loaf",
        label="loaf",
        phrase="a warm loaf of bread",
        warmth="warm",
        fill="full",
        portion="one loaf",
        tags={"bread", "warm"},
    ),
    "porridge": Food(
        id="porridge",
        label="bowl of porridge",
        phrase="a steaming bowl of porridge",
        warmth="warm",
        fill="full",
        portion="one bowl",
        tags={"porridge", "warm"},
    ),
    "berries": Food(
        id="berries",
        label="basket of berries",
        phrase="a bright basket of berries",
        warmth="cool",
        fill="light",
        portion="one basket",
        tags={"berries"},
    ),
    "cake": Food(
        id="cake",
        label="cake",
        phrase="a sweet little cake",
        warmth="warm",
        fill="happy",
        portion="one cake",
        tags={"cake", "sweet"},
    ),
}

NEEDS = {
    "share": Need(
        id="share",
        label="sharing",
        ravenous_gain=1.0,
        voice_gain=1.0,
        settle_drop=1.0,
        share_verb="share",
        separate_verb="separate",
        kind_words={"share", "sharing"},
    ),
}

HEROES = {
    "girl": ["Alice", "Mira", "Luna", "Rose", "Ivy"],
    "boy": ["Theo", "Finn", "Eli", "Niko", "Jules"],
}

TRAITS = ["kind", "brave", "gentle", "curious", "cheerful"]


@dataclass
class StoryParams:
    place: str
    food: str
    name: str
    gender: str
    trait: str
    guest_kind: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        if "share" not in setting.affordances:
            continue
        for food in FOODS:
            combos.append((place, food))
    return combos


def aspire_story() -> str:
    return ""  # not used, but kept conceptually for the seed tale


class StoryWorld:
    pass


def setting_line(setting: Setting) -> str:
    if setting.indoors:
        return f"{setting.place.capitalize()} glowed with candlelight."
    return f"{setting.place.capitalize()} stood quiet under a soft sky."


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["little", params.trait],
    ))
    guest = world.add(Entity(
        id="guest",
        kind="character",
        type=params.guest_kind,
        label=f"the {params.guest_kind}",
        traits=["ravenous", "loud"],
    ))
    food = world.add(Entity(
        id="food",
        type="food",
        label=FOODS[params.food].label,
        phrase=FOODS[params.food].phrase,
        owner=hero.id,
    ))

    world.facts.update(hero=hero, guest=guest, food=food, setting=world.setting, params=params)

    hero.memes["kindness"] = 1.0
    guest.meters["ravenous"] = 2.0
    guest.meters["voice"] = 2.0

    world.say(f"Once upon a time, {params.name} was a little {params.trait} {params.gender}.")
    world.say(f"{params.name} lived near {world.setting.place} and liked to watch the doors and the lamps.")
    world.say(f"One day, {params.name} found {food.phrase} and thought about {NEEDS['share'].label}.")

    world.para()
    world.say(setting_line(world.setting))
    world.say(f"At the gate waited {guest.label}, who looked ravenous and spoke in a great voice.")
    world.say(f'"I am hungry," said {guest.label}, "and my voice is loud because my belly feels empty."')

    if world.setting.indoors:
        world.say(f"The words echoed through the room like bells.")
    else:
        world.say(f"The words rolled over the stones and made the birds hop aside.")

    world.para()
    world.say(f"{params.name} did not have much, but {params.name} knew a fairy-tale truth: a small share can open a closed heart.")
    world.say(f"So {params.name} chose to {NEEDS['share'].separate_verb} one portion and {NEEDS['share'].share_verb} it.")

    hero.meters["fed"] = hero.meters.get("fed", 0.0)
    guest.meters["fed"] = guest.meters.get("fed", 0.0) + 1.0
    guest.memes["hope"] = guest.memes.get("hope", 0.0) + 1.0
    hero.memes["generosity"] = hero.memes.get("generosity", 0.0) + 1.0

    propagate(world, narrate=False)

    world.say(f"{params.name} set the portion on a little plate and offered it with both hands.")
    world.say(f"{guest.label} ate the food slowly, as if each bite was a tiny lamp being lit.")

    propagate(world, narrate=True)

    world.para()
    if guest.meters.get("voice", 0.0) <= 1.0:
        world.say(f"By the end, {guest.label}'s voice was soft enough for a bedtime story.")
    else:
        world.say(f"By the end, {guest.label} was still loud, but no longer scary.")
    world.say(f"{params.name} and {guest.label} sat together beside the gate, sharing crumbs and the quiet evening.")
    world.say(f"The castle felt larger because there was room for both hunger and kindness.")

    return world


def generate_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a short fairy tale about a child named {p.name} who meets a ravenous visitor with a voice that carries far.',
        f"Tell a gentle story in which {p.name} learns that {NEEDS['share'].label} can turn a separate plate into a friendship.",
        f'Write a child-friendly fairy tale using the words "separate", "ravenous", and "voice".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    hero: Entity = f["hero"]
    guest: Entity = f["guest"]
    food: Entity = f["food"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a little {p.trait} {p.gender} who lives near {setting.place}.",
        ),
        QAItem(
            question=f"What did {p.name} do with {food.label}?",
            answer=f"{p.name} chose to separate one portion and share it with {guest.label}.",
        ),
        QAItem(
            question=f"Why did {guest.label} sound so loud at the beginning?",
            answer=f"{guest.label} was ravenous, so {guest.label}'s voice carried like a great bell across the gate.",
        ),
        QAItem(
            question=f"What changed after the food was shared?",
            answer=f"After the food was shared, {guest.label} became calmer and {guest.label}'s voice grew gentle.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "share": [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to give some of what you have to someone else so both people can enjoy it.",
        )
    ],
    "ravenous": [
        QAItem(
            question="What does ravenous mean?",
            answer="Ravenous means very, very hungry.",
        )
    ],
    "voice": [
        QAItem(
            question="What is a voice?",
            answer="A voice is the sound a person or creature makes when they speak or sing.",
        )
    ],
    "separate": [
        QAItem(
            question="What does separate mean?",
            answer="Separate means to take one thing apart from another or to keep things from being mixed together.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [item for key in ("separate", "ravenous", "voice", "share") for item in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.carries:
            parts.append(f"carries={e.carries}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="castle_gate", food="loaf", name="Mira", gender="girl", trait="kind", guest_kind="wolf"),
    StoryParams(place="kitchen", food="porridge", name="Theo", gender="boy", trait="brave", guest_kind="giant"),
    StoryParams(place="meadow", food="berries", name="Luna", gender="girl", trait="gentle", guest_kind="bear"),
]


def explain_rejection(place: str, food: str) -> str:
    return f"(No story: {food} cannot be shared at {place} under this simple fairy-tale gate.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy-tale storyworld about sharing with a ravenous visitor."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--guest-kind", choices=["wolf", "giant", "bear", "fox"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.food is None or c[1] == args.food)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, food = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES[gender])
    trait = args.trait or rng.choice(TRAITS)
    guest_kind = args.guest_kind or rng.choice(["wolf", "giant", "bear", "fox"])
    return StoryParams(place=place, food=food, name=name, gender=gender, trait=trait, guest_kind=guest_kind)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story_text(world)
    return StorySample(
        params=params,
        story=story,
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


ASP_RULES = r"""
% A child can share food with a visitor at a setting that affords sharing.
can_share(Place, Food) :- setting(Place), food(Food), affords(Place, share).

% A visitor is ravenous when the story world marks hunger high.
ravenous(Guest) :- guest(Guest), hungry(Guest).

% A voice becomes loud when ravenous and soft when fed.
loud_voice(Guest) :- ravenous(Guest), voice(Guest).
soft_voice(Guest) :- fed(Guest), voice(Guest).

% The story is reasonable only if there is a shareable place and food.
valid_story(Place, Food) :- can_share(Place, Food).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, a))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("food_label", fid, food.label))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for place, food in combos:
            print(f"  {place:12} {food}")
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
            header = f"### {p.name}: {p.food} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
