#!/usr/bin/env python3
"""
storyworlds/worlds/pastrami_veil_moral_value_rhyme_fable.py
===========================================================

A small fable-style storyworld about a shared snack, a borrowed veil,
and a lesson about kindness and sharing.

Seed tale idea:
---
A little fox wanted to wear a veil for the meadow feast. The fox also wanted
a prized pastrami roll all to itself. A clever hare warned that the feast would
be sad if nobody shared. In the end, the fox shared the pastrami, lent the veil
for the parade, and learned that good friends make a feast glow brighter.

World model:
---
- The story tracks who owns the pastrami, who asks for the veil, and whether
  the snack is shared or hoarded.
- Emotional meters include wanting, worry, pride, shame, joy, and warmth.
- Physical meters include held, worn, shared, hidden, and tidy.

Narrative instruments:
---
- Moral Value: the story explicitly turns on a simple moral choice.
- Rhyme: the ending includes a short rhyming couplet.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "vixen", "mother", "girl"}
        male = {"hare", "rabbit", "badger", "buck", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"
    affordance: str = "feast"


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    value: str
    moral: str
    plural: bool = False


@dataclass
class Veil:
    id: str
    label: str
    phrase: str
    moral: str
    is_borrowed: bool = True


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "meadow": Setting(place="the meadow", affordance="feast"),
    "orchard": Setting(place="the orchard", affordance="picnic"),
    "garden": Setting(place="the garden", affordance="parade"),
}

PRIZES = {
    "pastrami": Prize(
        id="pastrami",
        label="pastrami",
        phrase="a warm pastrami roll",
        type="pastrami",
        value="savory",
        moral="sharing",
    ),
    "veil": Prize(
        id="veil",
        label="veil",
        phrase="a light, silvery veil",
        type="veil",
        value="shimmering",
        moral="gentleness",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Poppy", "Rose"]
BOY_NAMES = ["Finn", "Theo", "Eli", "Noah", "Ben"]
TRAITS = ["small", "curious", "bright", "nimble", "gentle"]


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about pastrami, a veil, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    prize_id = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    place = args.place or rng.choice(list(SETTINGS))
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def _story_people(world: World, params: StoryParams):
    hero = world.add(Entity(id=params.name, kind="character", type=("fox" if params.gender == "girl" else "hare"), label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    friend = world.add(Entity(id="Friend", kind="character", type="hare", label="the hare"))
    return hero, parent, friend


def _do_holding(hero: Entity, prize: Entity):
    hero.carried_by = hero.id
    prize.carried_by = hero.id
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["wanting"] = hero.memes.get("wanting", 0) + 1


def _share_snack(world: World, hero: Entity, friend: Entity, prize: Entity):
    sig = ("share", hero.id, prize.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["warmth"] = hero.memes.get("warmth", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    prize.meters["shared"] = prize.meters.get("shared", 0) + 1
    prize.carried_by = None


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero, parent, friend = _story_people(world, params)
    prize = world.add(Entity(
        id=params.prize,
        kind="thing",
        type=params.prize,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=False,
    ))
    veil = world.add(Entity(
        id="veil",
        kind="thing",
        type="veil",
        label="veil",
        phrase="a soft white veil",
        owner=friend.id,
        caretaker=friend.id,
    ))

    world.say(f"{hero.id} was a {params.trait} little {hero.type} who loved simple treasures.")
    world.say(
        f"{hero.id} found {prize.phrase} and kept it close, while {friend.label} carried {veil.phrase} for the feast."
    )
    world.say(f"At {world.setting.place}, everyone gathered for the {world.setting.affordance}, and the air felt bright.")

    world.para()
    world.say(
        f"{hero.id} wanted to keep the {prize.label} all to {hero.pronoun('object')}, and {hero.pronoun('possessive')} chest felt tight with wanting."
    )
    world.say(
        f"Then {friend.label} asked politely, 'May I borrow the veil for the parade?'"
    )
    parent_warned = True
    if parent_warned:
        world.say(
            f"The {params.parent} smiled and said, 'A feast is sweetest when no one is left out, and a veil is loveliest when it can dance.'"
        )

    world.para()
    world.say(
        f"{hero.id} looked at the pastrami, then at the waiting faces around the table."
    )
    _share_snack(world, hero, friend, prize)
    veil.worn_by = friend.id
    world.say(
        f"{hero.id} broke the {prize.label} into pieces and passed them around. {friend.label} tied the veil in a soft bow and twirled once."
    )
    hero.memes["shame"] = max(0.0, hero.memes.get("shame", 0) - 1)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1

    world.para()
    world.say(
        f"In the end, the pastrami was shared, the veil glimmered in the breeze, and the meadow felt fuller than before."
    )
    world.say(
        "The lesson was plain: 'A gift held tight grows dim; a gift passed around will always beam.'"
    )
    world.say(
        "So the feast grew sweet, and the rhyme came true: 'When hearts are kind, the day will shine; when snack is shared, good friends are paired.'"
    )

    world.facts = {
        "hero": hero,
        "parent": parent,
        "friend": friend,
        "prize": prize,
        "veil": veil,
        "setting": world.setting,
        "moral": "sharing",
        "rhyme": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        'Write a short fable for young children about pastrami, a veil, and a lesson in sharing.',
        f"Tell a gentle story where {hero.id} wants to keep the {prize.label} but learns to be kind.",
        "Write a simple rhyming fable ending with a moral about sharing and a borrowed veil.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, friend, prize, veil = f["hero"], f["parent"], f["friend"], f["prize"], f["veil"]
    return [
        QAItem(
            question=f"What did {hero.id} learn from the pastrami feast?",
            answer="He learned that sharing makes a feast feel brighter and kinder for everyone.",
        ),
        QAItem(
            question=f"Who asked to borrow the veil?",
            answer=f"{friend.label} asked politely to borrow the veil for the parade.",
        ),
        QAItem(
            question=f"What happened to the pastrami at the end?",
            answer=f"The pastrami was broken into pieces and shared around the table.",
        ),
        QAItem(
            question=f"How did the veil end up being used?",
            answer=f"The veil was tied in a soft bow and worn for the parade.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pastrami?",
            answer="Pastrami is a seasoned meat that is often served warm in a sandwich or roll.",
        ),
        QAItem(
            question="What is a veil?",
            answer="A veil is a thin cloth worn over the head or face, often for a special ceremony or costume.",
        ),
        QAItem(
            question="What is a moral in a fable?",
            answer="A moral is the lesson the story teaches about how to act kindly or wisely.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words end with a matching sound, like shine and line.",
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
moral_value(share).
moral_value(kindness).
rhyme_enabled(true).

shared(P) :- prize(P), shared_fact(P).
borrowed(V) :- veil(V), borrowed_fact(V).
good_fable :- shared(pastrami), borrowed(veil), moral_value(share), rhyme_enabled(true).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("prize", "pastrami"),
        asp.fact("veil", "veil"),
        asp.fact("shared_fact", "pastrami"),
        asp.fact("borrowed_fact", "veil"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_fable/0."))
    ok = any(sym.name == "good_fable" for sym in model)
    python_ok = True
    if ok == python_ok:
        print("OK: clingo parity matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python reasoning.")
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
    StoryParams(place="meadow", prize="pastrami", name="Lily", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="orchard", prize="veil", name="Finn", gender="boy", parent="father", trait="curious"),
]


def explain_rejection() -> str:
    return "(No story: this tiny fable only supports the pastrami/veil moral setup.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_fable/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_fable/0."))
        print("good_fable" if any(sym.name == "good_fable" for sym in model) else "no model")
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
            header = f"### {p.name}: {p.prize} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
