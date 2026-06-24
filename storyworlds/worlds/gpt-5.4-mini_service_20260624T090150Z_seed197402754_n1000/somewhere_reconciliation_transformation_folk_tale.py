#!/usr/bin/env python3
"""
storyworlds/worlds/somewhere_reconciliation_transformation_folk_tale.py
========================================================================

A small folk-tale story world about a traveler, a guarded place, and a
reconciliation that brings about a transformation.

Seed tale used to build the world:
---
Somewhere beyond the pine hills, a little traveler named Mina kept a tiny
lantern and a bright red scarf. One dusk, Mina came to a narrow bridge where an
old bridge-sprite sat in a knot of roots and refused to let anyone cross. The
sprite was not cruel, only lonely: long ago, people had crossed without greeting
it, and the sprite had turned the bridge cold and stiff.

Mina bowed politely and offered the sprite a warm berry bun. The sprite sniffed,
then remembered how nice kindness felt. It uncurled, the bridge warmed, and the
little stream sang under its boards. Mina crossed safely, and the sprite smiled
for the first time in many seasons.

Causal state updates:
---
    kindness offered            -> loner.memes["lonely"] -= 1
                                  loner.memes["trust"] += 1
                                  guest.memes["hope"] += 1
    apology accepted            -> both parties.memes["hurt"] -= 1
                                  both parties.memes["peace"] += 1
    warm gift shared            -> spirit.meters["cold"] -= 1
                                  spirit.meters["soft"] += 1
    reconciliation completed    -> spirit.memes["resentment"] = 0
                                  spirit.meters["stiff"] -= 1
                                  spirit.meters["warm"] += 1
    transformation completed    -> spirit.kind changes from "stony" to "helpful"
                                  bridge becomes safe to cross
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
# World entities and state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | spirit | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    transformed_from: str = ""

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "soft": 0.0, "stiff": 0.0, "warm": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"lonely": 0.0, "trust": 0.0, "hope": 0.0, "hurt": 0.0, "peace": 0.0, "resentment": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str = "somewhere beyond the pine hills"
    bridge_name: str = "the narrow bridge"
    stream_name: str = "the little stream"
    folk_detail: str = "pine trees leaned over the path like old listeners"


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    warm: bool = False
    shared: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0


def is_transformed(spirit: Entity) -> bool:
    return spirit.kind == "helpful" or spirit.meters["warm"] >= THRESHOLD and spirit.memes["peace"] >= THRESHOLD


# ---------------------------------------------------------------------------
# Tale engine
# ---------------------------------------------------------------------------
def offer_kindness(world: World, guest: Entity, spirit: Entity, gift: Gift) -> None:
    guest.memes["hope"] += 1
    spirit.memes["trust"] += 1
    spirit.memes["lonely"] = max(0.0, spirit.memes["lonely"] - 1)
    world.say(
        f"{guest.id} stopped at {world.place.bridge_name} and bowed low. "
        f"{guest.pronoun().capitalize()} offered {spirit.pronoun('object')} {gift.phrase}, "
        f"because even a small traveler can carry a gentle heart."
    )


def apology(world: World, guest: Entity, spirit: Entity) -> None:
    guest.memes["peace"] += 1
    spirit.memes["hurt"] = max(0.0, spirit.memes["hurt"] - 1)
    spirit.memes["peace"] += 1
    world.say(
        f'"I am sorry for the people who forgot to greet you," {guest.id} said. '
        f"The old air around the bridge softened a little."
    )


def accept_gift(world: World, spirit: Entity, gift: Gift) -> None:
    if gift.warm:
        spirit.meters["cold"] = max(0.0, spirit.meters["cold"] - 1)
        spirit.meters["soft"] += 1
        world.say(
            f"The sprite sniffed {gift.phrase} and let out a tiny sigh. "
            f"Warm steam curled up from the crust, and the roots beneath {world.place.bridge_name} felt less sharp."
        )
    else:
        spirit.meters["soft"] += 1
        world.say(
            f"The sprite accepted the gift carefully, as if it were a pebble from a memory long ago."
        )


def reconcile(world: World, guest: Entity, spirit: Entity) -> None:
    if spirit.memes["trust"] < THRESHOLD or guest.memes["peace"] < THRESHOLD:
        return
    if "reconcile" in world.fired:
        return
    world.fired.add("reconcile")
    guest.memes["hurt"] = max(0.0, guest.memes["hurt"] - 1)
    guest.memes["peace"] += 1
    spirit.memes["hurt"] = max(0.0, spirit.memes["hurt"] - 1)
    spirit.memes["peace"] += 1
    spirit.memes["resentment"] = 0.0
    spirit.meters["stiff"] = max(0.0, spirit.meters["stiff"] - 1)
    spirit.meters["warm"] += 1
    world.say(
        f"The old grudge unknotted at last. The traveler and the sprite looked at each other, "
        f"and both chose to be gentle."
    )


def transform(world: World, spirit: Entity, bridge_safe: Entity) -> None:
    if spirit.meters["warm"] < THRESHOLD or spirit.meters["soft"] < THRESHOLD:
        return
    if "transform" in world.fired:
        return
    world.fired.add("transform")
    spirit.transformed_from = spirit.kind
    spirit.kind = "helpful"
    spirit.type = "bridge-sprite"
    bridge_safe.meters["safe"] = 1.0
    world.say(
        f"Then something old and stubborn changed. The sprite straightened, smiled, "
        f"and became a helper instead of a watcher."
    )


def crossing(world: World, guest: Entity, bridge_safe: Entity) -> None:
    if bridge_safe.meters["safe"] < THRESHOLD:
        raise StoryError("the bridge cannot be crossed before the reconciliation transforms the sprite")
    world.say(
        f"{guest.id} crossed the bridge safely, while the stream sang below like a happy little harp."
    )


def tell(place: Place, hero_name: str, hero_type: str, spirit_name: str, gift: Gift) -> World:
    world = World(place)
    guest = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["small", "polite", "brave"],
        meters={"tired": 0.0},
        memes={"hope": 0.0, "peace": 0.0, "hurt": 0.0},
    ))
    spirit = world.add(Entity(
        id=spirit_name,
        kind="spirit",
        type="stony",
        label="old bridge-sprite",
        phrase="an old bridge-sprite with moss on its elbows",
        traits=["lonely", "grumpy"],
        meters={"cold": 1.0, "soft": 0.0, "stiff": 1.0, "warm": 0.0, "safe": 0.0},
        memes={"lonely": 1.0, "trust": 0.0, "hope": 0.0, "hurt": 1.0, "peace": 0.0, "resentment": 1.0},
    ))
    bridge_safe = world.add(Entity(
        id="bridge",
        kind="thing",
        type="bridge",
        label=place.bridge_name,
        phrase=place.bridge_name,
        meters={"safe": 0.0},
        memes={},
    ))

    world.say(
        f"Somewhere beyond the pine hills, {place.folk_detail}. "
        f"{guest.id} followed the path until {guest.pronoun()} reached {place.bridge_name}."
    )
    world.say(
        f"There sat {spirit.phrase}, and it would not let anyone cross."
    )
    world.para()

    offer_kindness(world, guest, spirit, gift)
    apology(world, guest, spirit)
    accept_gift(world, spirit, gift)
    reconcile(world, guest, spirit)
    transform(world, spirit, bridge_safe)
    world.para()
    crossing(world, guest, bridge_safe)

    world.facts.update(
        guest=guest,
        spirit=spirit,
        bridge=bridge_safe,
        gift=gift,
        place=place,
        transformed=is_transformed(spirit),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "somewhere": Place(),
}

GIFTS = {
    "berry_bun": Gift(id="berry_bun", label="berry bun", phrase="a warm berry bun", warm=True),
    "honey_cup": Gift(id="honey_cup", label="honey cup", phrase="a little cup of honey", warm=False),
    "apple_pie": Gift(id="apple_pie", label="apple pie", phrase="a small apple pie", warm=True),
}

HERO_NAMES = ["Mina", "Pip", "Tara", "Owen", "Lena", "Sora"]
SPIRIT_NAMES = ["Brindle", "Moss", "Glim", "Tarn"]


@dataclass
class StoryParams:
    place: str
    gift: str
    hero_name: str
    hero_type: str
    spirit_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="somewhere", gift="berry_bun", hero_name="Mina", hero_type="girl", spirit_name="Moss"),
    StoryParams(place="somewhere", gift="apple_pie", hero_name="Pip", hero_type="boy", spirit_name="Brindle"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(somewhere).
gift(berry_bun). gift(honey_cup). gift(apple_pie).
warm_gift(berry_bun). warm_gift(apple_pie).

kindness(P) :- gift(P).
reconciliation(P) :- warm_gift(P).
transformation(P) :- reconciliation(P).

valid_story(Place, Gift) :- place(Place), gift(Gift), reconciliation(Gift), transformation(Gift).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for g in GIFTS.values():
        lines.append(asp.fact("gift", g.id))
        if g.warm:
            lines.append(asp.fact("warm_gift", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("somewhere", g.id) for g in GIFTS.values() if g.warm}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale about reconciliation and transformation.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--gift", choices=GIFTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--spirit-name")
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
    gift_id = args.gift or rng.choice(list(GIFTS.keys()))
    gift = GIFTS[gift_id]
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    spirit_name = args.spirit_name or rng.choice(SPIRIT_NAMES)
    if gift_id not in GIFTS:
        raise StoryError("unknown gift")
    return StoryParams(
        place=args.place or "somewhere",
        gift=gift_id,
        hero_name=name,
        hero_type=hero_type,
        spirit_name=spirit_name,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale set {f["place"].name} about {f["guest"].id} and an old bridge-sprite.',
        f"Tell a gentle story where {f['guest'].id} offers {f['gift'].phrase} and a lonely sprite changes its mind.",
        "Write a child-friendly story about kindness that turns a grumpy guardian into a helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    guest, spirit, gift = f["guest"], f["spirit"], f["gift"]
    return [
        QAItem(
            question=f"Who visited the bridge in the story?",
            answer=f"{guest.id} visited the bridge and spoke kindly to the old bridge-sprite.",
        ),
        QAItem(
            question=f"What gift did {guest.id} offer?",
            answer=f"{guest.id} offered {gift.phrase} to the sprite.",
        ),
        QAItem(
            question=f"Why did the sprite change by the end?",
            answer="The sprite changed because the traveler offered kindness, accepted the old hurt with an apology, and shared a warm gift until trust grew into peace.",
        ),
        QAItem(
            question=f"What happened after the reconciliation?",
            answer=f"After the reconciliation, the sprite transformed into a helpful guardian and {guest.id} crossed safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bridge for?",
            answer="A bridge is built so people can cross over water, a road, or a gap safely.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a hurt or disagreement.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form or becomes different in an important way.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind:8} type={e.type:10} "
            f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    gift = GIFTS[params.gift]
    world = tell(place, params.hero_name, params.hero_type, params.spirit_name, gift)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for place, gift in stories:
            print(f"  {place} / {gift}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
