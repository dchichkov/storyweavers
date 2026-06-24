#!/usr/bin/env python3
"""
storyworlds/worlds/tame_secure_molt_suspense_happy_ending_lesson.py
====================================================================

A small superhero-style story world about keeping a tame little sidekick secure
while it molts, with suspense, a happy ending, and a lesson learned.

Seed tale:
---
Nova was a young hero who wore a bright blue mask and helped the city from a
tiny rooftop hideout. Her best friend was Pip, a tame little sky-lizard with
shiny scales and a brave squeak. One morning, Nova noticed Pip’s scales were
starting to molt. The shed skin was itchy, and Pip wanted to hide.

Nova knew molting could be uncomfortable, so she prepared a soft nest, closed
the window, and secured the hideout so nothing would blow in. But then a gust
rattled the door and made Pip panic. Nova took a deep breath, held Pip gently,
and explained that molting was safe and natural. Pip relaxed, finished shedding
the old scales, and slept in the cozy nest.

Narrative instruments:
---
- Suspense: the hideout is secure, but a gust and rattling door test the plan.
- Happy Ending: the molt finishes safely and the sidekick rests happily.
- Lesson Learned: gentle patience and a secure space help during change.
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
    protected: bool = False
    secure: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "heroine"}
        male = {"boy", "man", "father", "uncle", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    secure_space: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    type: str
    size: str
    molt_style: str
    molt_result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafetyItem:
    id: str
    label: str
    phrase: str
    protects: set[str]
    purpose: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    sidekick: str
    creature: str
    safety_item: str
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": Setting(place="the rooftop hideout", secure_space="the skylight room", indoors=False, affords={"molt"}),
    "tower": Setting(place="the watch tower", secure_space="the quiet signal room", indoors=False, affords={"molt"}),
    "hideout": Setting(place="the secret hideout", secure_space="the lamp room", indoors=True, affords={"molt"}),
}

CREATURES = {
    "mothling": Creature(
        id="mothling",
        label="mothling",
        phrase="a tiny tame mothling with silver wings",
        type="mothling",
        size="small",
        molt_style="molt out of its old fuzzy coat",
        molt_result="wore a fresh, bright coat",
        tags={"tame", "molt"},
    ),
    "sky_lizard": Creature(
        id="sky_lizard",
        label="sky-lizard",
        phrase="a tame sky-lizard with bright scales",
        type="sky-lizard",
        size="small",
        molt_style="shed its old scales",
        molt_result="shone with new scales",
        tags={"tame", "secure", "molt"},
    ),
    "cubsprite": Creature(
        id="cubsprite",
        label="cubsprite",
        phrase="a tame cubsprite with a curly tail",
        type="cubsprite",
        size="small",
        molt_style="molt a soft shell",
        molt_result="looked glossy and new",
        tags={"tame", "molt"},
    ),
}

SAFETY_ITEMS = {
    "nest": SafetyItem(
        id="nest",
        label="soft nest",
        phrase="a soft nest lined with blankets",
        protects={"comfort", "security"},
        purpose="keep the creature calm",
    ),
    "screen": SafetyItem(
        id="screen",
        label="window screen",
        phrase="a sturdy window screen",
        protects={"wind", "draft"},
        purpose="keep gusts out",
    ),
    "blanket": SafetyItem(
        id="blanket",
        label="blanket fort",
        phrase="a blanket fort",
        protects={"comfort", "security"},
        purpose="make a quiet shelter",
    ),
    "crate": SafetyItem(
        id="crate",
        label="safe crate",
        phrase="a safe crate with a soft pillow",
        protects={"security"},
        purpose="hold the creature safely",
    ),
}

HERO_NAMES = ["Nova", "Mira", "Jade", "Riley", "Penny", "Zuri", "Ivy", "Luna"]
SIDEKICK_NAMES = ["Spark", "Comet", "Byte", "Pip", "Echo", "Dash"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for creature_id, creature in CREATURES.items():
            for item_id, item in SAFETY_ITEMS.items():
                if "security" in item.protects and "molt" in creature.tags:
                    combos.append((place, creature_id, item_id))
    return combos


def explain_rejection(creature: Creature, item: SafetyItem) -> str:
    return (
        f"(No story: {item.label} does not fit a gentle molt story for {creature.label}. "
        f"Choose a safety item that makes the creature feel secure during the molt.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero-style story world: a tame sidekick, a secure space, and a molt."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--safety-item", choices=SAFETY_ITEMS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.creature:
        combos = [c for c in combos if c[1] == args.creature]
    if args.safety_item:
        combos = [c for c in combos if c[2] == args.safety_item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, creature_id, item_id = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(place=place, hero=hero, hero_type=hero_type, sidekick=sidekick, creature=creature_id, safety_item=item_id)


def _warn(world: World, hero: Entity, creature: Entity) -> None:
    world.say(
        f"{hero.name_or_label()} noticed that {creature.label} was starting to molt, "
        f"and the old fuzzy coat looked itchy and loose."
    )
    world.say(
        f"{hero.pronoun().capitalize()} knew it was time to help, because change can feel wobbly even for a brave sidekick."
    )


def _prepare(world: World, hero: Entity, creature: Entity, item: SafetyItem) -> Entity:
    safety = world.add(Entity(
        id=item.id,
        type="thing",
        label=item.label,
        phrase=item.phrase,
        protected=True,
        secure=True,
        owner=hero.id,
    ))
    safety.worn_by = creature.id
    world.say(
        f"{hero.name_or_label()} set up {item.phrase} so {creature.label} could stay secure while it molted."
    )
    return safety


def _suspense(world: World, hero: Entity, sidekick: Entity, creature: Entity) -> None:
    world.say(
        f"Then a sharp gust tapped the door, and the hideout gave a little rattle."
    )
    sidekick.memes["alarm"] = sidekick.memes.get("alarm", 0.0) + 1
    creature.memes["fear"] = creature.memes.get("fear", 0.0) + 1
    world.say(
        f"{creature.name_or_label()} froze for a moment, and {sidekick.name_or_label()} held still beside {hero.name_or_label()}."
    )
    world.say(
        f"The room stayed secure, but the sound made the moment feel suspenseful."
    )


def _calm(world: World, hero: Entity, creature: Entity) -> None:
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    creature.memes["calm"] = creature.memes.get("calm", 0.0) + 1
    world.say(
        f"{hero.name_or_label()} took a slow breath, gently tucked the blanket higher, and whispered that molting is safe."
    )
    world.say(
        f"{creature.label} listened, relaxed, and finished shedding the old covering."
    )


def _finish(world: World, hero: Entity, creature: Entity) -> None:
    creature.meters["molt_done"] = 1
    creature.memes["joy"] = creature.memes.get("joy", 0.0) + 1
    world.say(
        f"Soon {creature.label} wore a fresh new look, brighter than before."
    )
    world.say(
        f"{hero.name_or_label()} smiled at the cozy nest, because the secure room had helped turn worry into a happy ending."
    )
    world.say(
        f"{hero.name_or_label()} learned that patience and a safe place can help a friend through a big change."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    creature_cfg = CREATURES[params.creature]
    item_cfg = SAFETY_ITEMS[params.safety_item]

    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="hero", label=params.sidekick))
    creature = world.add(Entity(id=creature_cfg.id, kind="character", type=creature_cfg.type, label=creature_cfg.label))
    world.facts.update(hero=hero, sidekick=sidekick, creature=creature, item=item_cfg, setting=setting)

    world.say(
        f"{hero.name_or_label()} was a young superhero with a bright mask and a heart that liked to help."
    )
    world.say(
        f"{creature_cfg.phrase} lived with {hero.name_or_label()} at {setting.place}, and {hero.name_or_label()} always tried to keep {creature_cfg.label} tame and secure."
    )
    world.para()
    _warn(world, hero, creature)
    _prepare(world, hero, creature, item_cfg)
    world.para()
    _suspense(world, hero, sidekick, creature)
    _calm(world, hero, creature)
    _finish(world, hero, creature)
    return world


ASP_RULES = r"""
% A story is reasonable when a creature that can molt is paired with a safety item
% that can make the space secure.
reasonably_story(P, C, S) :- place(P), creature(C), safety_item(S),
                             can_molt(C), secures(S), valid_place(P).

% The gentle superhero ending is available when the creature is tame and the
% chosen safety item supports a secure molt.
happy_ending(P, C, S) :- reasonably_story(P, C, S), tame(C), secure_item(S).

% The lesson learned is included when the story has a secure setup and a molt.
lesson_learned(P, C, S) :- happy_ending(P, C, S), molt(C).

#show reasonably_story/3.
#show happy_ending/3.
#show lesson_learned/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("valid_place", p))
    for c in CREATURES.values():
        lines.append(asp.fact("creature", c.id))
        if "tame" in c.tags:
            lines.append(asp.fact("tame", c.id))
        if "molt" in c.tags:
            lines.append(asp.fact("can_molt", c.id))
            lines.append(asp.fact("molt", c.id))
    for s in SAFETY_ITEMS.values():
        lines.append(asp.fact("safety_item", s.id))
        if "security" in s.protects:
            lines.append(asp.fact("secures", s.id))
        if "security" in s.protects:
            lines.append(asp.fact("secure_item", s.id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def valid_asp_models() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "reasonably_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(valid_asp_models())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].name_or_label()
    creature = f["creature"].label
    item = f["item"].label
    place = f["setting"].place
    return [
        f'Write a short superhero story for a child where {hero} helps a tame {creature} molt in {place}.',
        f'Write a gentle story with suspense, a happy ending, and a lesson learned about keeping {creature} secure during change.',
        f'Write a simple superhero tale that includes the words "tame", "secure", and "molt".',
        f"Tell a small action story where {hero} calms a friend, protects a {item}, and everything ends safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    creature = f["creature"]
    setting = f["setting"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who helped the {creature.label} stay secure while it molted?",
            answer=f"{hero.name_or_label()} did. {hero.name_or_label()} set up {item.phrase} and stayed close while {creature.label} molted.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful in {setting.place}?",
            answer="A sharp gust rattled the door, and the noisy moment made everyone pause for a second.",
        ),
        QAItem(
            question=f"What did {hero.name_or_label()} learn by the end?",
            answer="That patience and a secure, gentle space can help a friend through a big change.",
        ),
        QAItem(
            question=f"How did {sidekick.name_or_label()} act when the gust came?",
            answer=f"{sidekick.name_or_label()} stayed near {hero.name_or_label()} and kept still while they helped {creature.label}.",
        ),
        QAItem(
            question=f"Why was {creature.label} tame important?",
            answer=f"Because a tame {creature.label} could be comforted and helped through molting without a big fuss.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for a place to be secure?",
            answer="A secure place is safe and steady, so it helps keep things from getting disturbed by wind or trouble.",
        ),
        QAItem(
            question="What is molting?",
            answer="Molting is when an animal sheds old skin, fur, or scales so a new covering can grow.",
        ),
        QAItem(
            question="What does tame mean?",
            answer="Tame means a creature is calm around people and not wild or hard to handle.",
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
        bits = []
        if e.protected:
            bits.append("protected=True")
        if e.secure:
            bits.append("secure=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="rooftop", hero="Nova", hero_type="girl", sidekick="Pip", creature="sky_lizard", safety_item="screen"),
    StoryParams(place="tower", hero="Mira", hero_type="girl", sidekick="Comet", creature="mothling", safety_item="blanket"),
    StoryParams(place="hideout", hero="Jade", hero_type="boy", sidekick="Dash", creature="cubsprite", safety_item="nest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'reasonably_story'))} compatible stories")
        for t in asp.atoms(model, "reasonably_story"):
            print(t)
        return

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
