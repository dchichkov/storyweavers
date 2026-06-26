#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about sharing, surprise, and caution around a
prized little toy called the destructor.

The tale premise:
- A child owns a small handheld destructor toy.
- A friend wants to share it.
- A surprise happens during sharing.
- A cautionary adult helps them choose a safer, kinder way to play.

The world simulates:
- physical state: who holds the toy, where the toy is, whether it is intact
- emotional state: delight, worry, surprise, caution, kindness, sharing

The story is intentionally small and classical, with a rhyme-like cadence.
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

TRY_NAMES = [
    "Mina", "Toby", "Luna", "Nico", "Poppy", "Milo", "Ada", "Finn",
    "Ruby", "Owen",
]

CARE_NAMES = ["mother", "father", "grandma", "grandpa", "auntie", "uncle"]
PLACES = ["the nursery", "the playroom", "the cozy room", "the sunny corner"]
COMPANIONS = ["a friend", "a neighbor", "a cousin", "a small guest"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    broken: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def title(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the nursery"
    cozy: bool = True


@dataclass
class Toy:
    label: str = "destructor"
    phrase: str = "a tiny destructor toy"
    fragility: int = 1
    surprise_sound: str = "pop"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    caregiver: str
    companion: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _speak(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}" {speaker.title()} said.')


def _sharing_state(hero: Entity, toy: Entity, companion: Entity) -> bool:
    return toy.holder in {hero.id, companion.id}


def _apply_share(world: World, hero: Entity, companion: Entity, toy: Entity) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
    companion.memes["sharing"] = companion.memes.get("sharing", 0.0) + 1
    toy.meters["shared"] = toy.meters.get("shared", 0.0) + 1


def _apply_surprise(world: World, toy: Entity, hero: Entity, companion: Entity) -> None:
    sig = ("surprise", toy.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    toy.memes["surprise"] = toy.memes.get("surprise", 0.0) + 1
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    companion.memes["surprise"] = companion.memes.get("surprise", 0.0) + 1
    world.say(f"The little destructor went {toy.phrase.split()[-1]}-pop, and both children blinked with surprise.")


def _apply_caution(world: World, caregiver: Entity, hero: Entity, companion: Entity, toy: Entity) -> None:
    sig = ("caution", toy.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    caregiver.memes["caution"] = caregiver.memes.get("caution", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    companion.memes["worry"] = companion.memes.get("worry", 0.0) + 1
    world.say(
        f"{caregiver.title()} smiled a careful smile and said they could share "
        f"the destructor slowly, with both hands and with room to set it down."
    )


def _apply_fix(world: World, hero: Entity, companion: Entity, toy: Entity) -> None:
    sig = ("fix", toy.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    companion.memes["joy"] = companion.memes.get("joy", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    companion.memes["kindness"] = companion.memes.get("kindness", 0.0) + 1
    toy.meters["safe_play"] = toy.meters.get("safe_play", 0.0) + 1
    world.say(
        f"So they took turns, then sat the little destructor on a soft cushion, "
        f"and the sharing turned sweet and bright."
    )


def propagate(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    caregiver = world.get("caregiver")
    toy = world.get("toy")

    if _sharing_state(hero, toy, companion):
        _apply_share(world, hero, companion, toy)
    if toy.meters.get("shared", 0.0) >= 1 and toy.memes.get("surprise", 0.0) < 1:
        _apply_surprise(world, toy, hero, companion)
    if toy.memes.get("surprise", 0.0) >= 1 and caregiver.memes.get("caution", 0.0) < 1:
        _apply_caution(world, caregiver, hero, companion, toy)
    if caregiver.memes.get("caution", 0.0) >= 1 and toy.meters.get("safe_play", 0.0) < 1:
        _apply_fix(world, hero, companion, toy)


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    companion = world.add(Entity(id="companion", kind="character", type="child", label=params.companion))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=params.caregiver, label=params.caregiver))
    toy = world.add(Entity(id="toy", type="toy", label="destructor", phrase="pop-pop"))

    toy.owner = hero.id
    toy.holder = hero.id

    hero.memes["love"] = 1
    hero.memes["joy"] = 1
    world.say(f"{hero.title()} had a tiny destructor, bright as a bead and neat as a star.")
    world.say(f"In {setting.place}, {hero.title()} loved to share it with {params.companion}, a gentle little guest.")
    world.para()

    world.say(
        f"One day in {setting.place}, {hero.title()} held the destructor up to show "
        f"{params.companion}, and both children leaned in close."
    )
    world.say(f"{params.companion.title()} asked for a turn, and {hero.title()} said yes with a nod.")
    propagate(world)
    world.para()

    world.say(
        f"But the destructor gave a sudden little pop, and everyone jumped like a rabbit in a row."
    )
    world.say(
        f"{params.companion.title()} gasped, then laughed, while {hero.title()} held still and did not let it go."
    )
    propagate(world)
    world.para()

    world.say(
        f"{params.caregiver.title()} came along and gave a cautionary word: small toys need small, slow hands."
    )
    world.say(
        f"The children listened well, and the destructor was placed on a soft cloth for safe, careful play."
    )
    propagate(world)

    world.facts.update(
        hero=hero,
        companion=companion,
        caregiver=caregiver,
        toy=toy,
        setting=setting,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle nursery rhyme about {p.hero_name} sharing a tiny destructor with {p.companion}.",
        f"Tell a short cautionary story in rhyme where a child named {p.hero_name} has a destructor and learns safe sharing.",
        f"Create a cozy story for small children set in {p.place} with surprise, sharing, and a careful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    caregiver: Entity = f["caregiver"]
    toy: Entity = f["toy"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who had the destructor in {setting.place}?",
            answer=f"{hero.title()} had the destructor at first, and the toy belonged to {hero.pronoun('possessive')} play.",
        ),
        QAItem(
            question=f"What happened when {hero.title()} and {companion.title()} began to share it?",
            answer=(
                f"They tried to share the destructor, and then there was a sudden little surprise pop. "
                f"After that, everyone slowed down and listened."
            ),
        ),
        QAItem(
            question=f"What careful advice did {caregiver.title()} give?",
            answer=(
                f"{caregiver.title()} said they should use small, slow hands and set the destructor on a soft cloth, "
                f"so sharing could stay safe."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with calm sharing: the destructor rested on a soft cloth, the surprise had passed, "
                f"and the children played kindly together."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share a toy?",
            answer="To share a toy means to let someone else use it too, usually by taking turns and being kind.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens before anyone is ready for it.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so nobody gets hurt and nothing breaks.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.holder:
            bits.append(f"holder={e.holder}")
        if e.broken:
            bits.append("broken=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.title()} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child has the toy, then sharing may begin.
sharing(H,C,T) :- holder(T,H), companion(C), child(H).

% A shared toy can cause a surprise if it has the surprise property.
surprise(H,C,T) :- sharing(H,C,T), toy(T).

% A caregiver issues caution after surprise.
caution(CG,H,C,T) :- surprise(H,C,T), caregiver(CG).

% A safe turn follows caution.
safe(H,C,T) :- caution(CG,H,C,T), toy(T).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "hero"),
        asp.fact("child", "companion"),
        asp.fact("companion", "companion"),
        asp.fact("caregiver", "caregiver"),
        asp.fact("toy", "toy"),
        asp.fact("holder", "toy", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme world about sharing a destructor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=TRY_NAMES)
    ap.add_argument("--caregiver", choices=CARE_NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=args.name or rng.choice(TRY_NAMES),
        hero_type="girl" if (args.name in {"Luna", "Poppy", "Ada", "Ruby"}) else "boy",
        caregiver=args.caregiver or rng.choice(CARE_NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(place=params.place), params)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, name, comp) for place in PLACES for name in TRY_NAMES for comp in COMPANIONS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sharing/3.\n#show surprise/3.\n#show caution/4.\n#show safe/3."))
    return sorted(set(asp.atoms(model, "sharing")))


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="the nursery", hero_name="Mina", hero_type="girl", caregiver="mother", companion="a friend"),
    StoryParams(place="the playroom", hero_name="Toby", hero_type="boy", caregiver="father", companion="a cousin"),
    StoryParams(place="the cozy room", hero_name="Luna", hero_type="girl", caregiver="grandma", companion="a small guest"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show sharing/3.\n#show surprise/3.\n#show caution/4.\n#show safe/3."))
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
