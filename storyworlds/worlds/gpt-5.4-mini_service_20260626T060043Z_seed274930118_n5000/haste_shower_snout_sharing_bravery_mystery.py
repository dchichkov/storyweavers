#!/usr/bin/env python3
"""
storyworlds/worlds/haste_shower_snout_sharing_bravery_mystery.py
==================================================================

A standalone tiny story world about a rushed bath-time mystery:
a child or little animal with a snout, a shower that is suddenly too cold
or too splashy, and a gentle resolution shaped by sharing and bravery.

Premise:
- A small character wants to hurry through a shower.
- Something mysterious makes the shower feel wrong: the water is chilly,
  the soap is missing, or the towel disappears.
- The character must be brave enough to look, ask, or try again.
- Sharing a useful item or the warm water fixes the problem.

The world is intentionally small and classical: one child, one helper,
one problem, one turn, one clean ending image.
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
# Core model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
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
    place: str = "the bathroom"
    affords: set[str] = field(default_factory=lambda: {"shower", "sharing"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    weather: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    tags: set[str]
    helps: set[str]


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bathroom": Setting(place="the bathroom", affords={"shower", "sharing"}),
    "washroom": Setting(place="the washroom", affords={"shower", "sharing"}),
}

ACTIVITIES = {
    "shower": Activity(
        id="shower",
        verb="take a shower",
        gerund="taking a shower",
        rush="rush under the water",
        keyword="shower",
        tags={"shower"},
    ),
    "sharing": Activity(
        id="sharing",
        verb="share the warm water",
        gerund="sharing the warm water",
        rush="hurry to share the towel",
        keyword="sharing",
        tags={"sharing"},
    ),
}

PROTAGONISTS = {
    "piglet": ObjectCfg(
        label="piglet",
        phrase="a little piglet with a pink snout",
        type="piglet",
        tags={"snout"},
    ),
    "child": ObjectCfg(
        label="child",
        phrase="a small child with a curious snout-shaped nose",
        type="child",
        tags={"snout"},
    ),
}

HELPERS = {
    "sibling": SharedThing(
        id="sibling",
        label="older sibling",
        phrase="an older sibling",
        tags={"sharing", "bravery"},
        helps={"sharing"},
    ),
    "parent": SharedThing(
        id="parent",
        label="parent",
        phrase="a calm parent",
        tags={"sharing", "bravery"},
        helps={"sharing"},
    ),
}

ITEMS = {
    "soap": ObjectCfg(
        label="soap",
        phrase="the bright yellow soap",
        type="soap",
        tags={"sharing"},
    ),
    "towel": ObjectCfg(
        label="towel",
        phrase="the soft blue towel",
        type="towel",
        tags={"sharing"},
    ),
    "duck": ObjectCfg(
        label="duck",
        phrase="a small bath duck",
        type="duck",
        tags={"mystery"},
    ),
}

NAMES = {
    "piglet": ["Pip", "Milo", "Tilly", "Poppy", "Nina"],
    "child": ["Maya", "Theo", "Luna", "Ari", "Noah"],
}

TRAITS = ["curious", "gentle", "sly", "bright", "careful", "brave"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    hero_kind: str
    helper_kind: str
    missing_item: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

def _do_shower(world: World, hero: Entity, item: Entity, narrate: bool = True) -> None:
    hero.meters["wet"] = hero.meters.get("wet", 0.0) + 1.0
    hero.memes["unease"] = hero.memes.get("unease", 0.0) + 1.0
    if item.id == "soap":
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    if narrate:
        if item.id == "soap":
            world.say(f"{hero.id} stepped into the shower and washed carefully with the soap.")
        else:
            world.say(f"{hero.id} stepped into the shower, but something felt missing.")


def _mystery_turn(world: World, hero: Entity, helper: Entity, missing: Entity) -> None:
    if world.fired:
        return
    world.fired.add(("mystery", missing.id))
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"Then {hero.id} noticed that {missing.label} was gone, and the little bathroom felt mysterious."
    )
    world.say(
        f"{hero.id} took a brave breath and looked around instead of giving up."
    )


def _share_fix(world: World, hero: Entity, helper: Entity, missing: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.memes["shared"] = hero.memes.get("shared", 0.0) + 1.0
    helper.memes["sharing"] = helper.memes.get("sharing", 0.0) + 1.0
    world.say(
        f"{helper.id} shared {missing.phrase} and pointed to the shelf."
    )
    world.say(
        f"{hero.id} smiled, because brave questions were easier when someone shared a clue."
    )


def _resolve(world: World, hero: Entity, helper: Entity, missing: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    world.say(
        f"With {missing.label} back in place, {hero.id} finished the shower and felt warm and clean."
    )
    world.say(
        f"At the end, {hero.id}'s snout was dry, the room smelled fresh, and the mystery was gone."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def tell(setting: Setting, hero_cfg: ObjectCfg, helper_cfg: SharedThing, missing_cfg: ObjectCfg, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=hero_cfg.type,
        label=hero_cfg.label,
        phrase=hero_cfg.phrase,
        meters={"wet": 0.0},
        memes={"curiosity": 0.0, "bravery": 0.0, "unease": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_cfg.label,
        kind="character",
        type="person",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        memes={"sharing": 0.0, "bravery": 0.0},
    ))
    missing = world.add(Entity(
        id=missing_cfg.label,
        type=missing_cfg.type,
        label=missing_cfg.label,
        phrase=missing_cfg.phrase,
    ))

    world.say(f"{hero.id} was a {trait} little {hero_cfg.label} with a snout that twitched when anything felt strange.")
    world.say(f"{hero.id} loved {ACTIVITIES['shower'].gerund} because warm water made the day feel new.")
    world.say(f"One evening, {hero.id} hurried into {setting.place} with {helper.id} nearby.")

    world.para()
    _do_shower(world, hero, missing, narrate=True)
    if missing.id != "soap":
        world.say(f"{hero.id} frowned, because the shower was supposed to be quick, but the missing thing made it feel odd.")
    _mystery_turn(world, hero, helper, missing)

    world.para()
    _share_fix(world, hero, helper, missing)
    _resolve(world, hero, helper, missing)

    world.facts.update(
        hero=hero,
        helper=helper,
        missing=missing,
        setting=setting,
        hero_cfg=hero_cfg,
        helper_cfg=helper_cfg,
        missing_cfg=missing_cfg,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    missing = f["missing"]
    return [
        f'Write a short mystery story for children about {hero.id}, a shower, and a missing {missing.label}.',
        f'Tell a gentle story where sharing and bravery help {hero.id} solve a bathroom mystery.',
        f'Write a simple story that includes the words "haste", "shower", and "snout".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    missing = f["missing"]
    setting = f["setting"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {trait} little {hero.label} with a snout, and {helper.id}, who helps solve the mystery.",
        ),
        QAItem(
            question=f"What mysterious problem happened in {setting.place}?",
            answer=f"The mysterious problem was that {missing.label} was missing, so the shower felt strange and unfinished.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{helper.id} shared {missing.phrase}, and {hero.id} was brave enough to look around and keep going.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} clean, warm, and calm, after the shower mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shower for?",
            answer="A shower is for washing your body with water so you can get clean.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something or enjoy it with you.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel a little scared.",
        ),
        QAItem(
            question="Why might a snout twitch?",
            answer="A snout or nose can twitch when someone smells something surprising or interesting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
# Parameters / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny mystery story world: haste, shower, snout, sharing, bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-kind", choices=PROTAGONISTS)
    ap.add_argument("--helper-kind", choices=HELPERS)
    ap.add_argument("--missing-item", choices=ITEMS)
    ap.add_argument("--name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_kind = args.hero_kind or rng.choice(list(PROTAGONISTS))
    helper_kind = args.helper_kind or rng.choice(list(HELPERS))
    missing_item = args.missing_item or rng.choice(list(ITEMS))
    if missing_item == "duck" and hero_kind != "piglet":
        raise StoryError("The bath duck only makes sense as a clue, not as the missing item here.")
    name = args.name or rng.choice(NAMES["piglet"] if hero_kind == "piglet" else NAMES["child"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        hero_kind=hero_kind,
        helper_kind=helper_kind,
        missing_item=missing_item,
        name=name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROTAGONISTS[params.hero_kind],
        HELPERS[params.helper_kind],
        ITEMS[params.missing_item],
        params.name,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts emitted by asp_facts():
% setting(S). hero_kind(K). helper_kind(K). item(I). has_tag(X,T).

% A valid story needs a shower, a hero with a snout, and a clue-like missing item.
valid_story(S, H, M, P) :- setting(S), hero_kind(H), item(M), has_tag(H, snout), has_tag(M, mystery), has_tag(P, sharing).

% Sharing and bravery are required features of the world.
feature(sharing).
feature(bravery).

% The mystery is interesting only if the missing item is not itself the hero.
reasonable(H, M) :- hero_kind(H), item(M), H != M.

#show valid_story/4.
#show feature/1.
#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in PROTAGONISTS.items():
        lines.append(asp.fact("hero_kind", hid))
        for tag in h.tags:
            lines.append(asp.fact("has_tag", hid, tag))
    for kid, k in HELPERS.items():
        lines.append(asp.fact("helper_kind", kid))
        for tag in k.tags:
            lines.append(asp.fact("has_tag", kid, tag))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in item.tags:
            lines.append(asp.fact("has_tag", iid, tag))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    features = set(asp.atoms(model, "feature"))
    if ("sharing",) not in features or ("bravery",) not in features:
        print("MISMATCH: missing required features in ASP model.")
        return 1
    print("OK: ASP twin contains required features.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams("bathroom", "piglet", "sibling", "soap", "Pip", "curious"),
    StoryParams("washroom", "piglet", "parent", "towel", "Milo", "brave"),
    StoryParams("bathroom", "child", "sibling", "soap", "Maya", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

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
        if len(samples) > 1:
            header = f"### sample {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
