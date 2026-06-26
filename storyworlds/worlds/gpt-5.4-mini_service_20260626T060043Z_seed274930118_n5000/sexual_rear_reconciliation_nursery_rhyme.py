#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sexual_rear_reconciliation_nursery_rhyme.py
==============================================================================================================

A tiny nursery-rhyme story world about two small friends, a bump to the rear,
and a gentle reconciliation.

Premise seed:
- A little animal is embarrassed after an accidental bump to the rear.
- A friend worries, quarrels, then the pair make up.
- The ending should feel sing-song, warm, and resolved.

The seed words "sexual" and "rear" are included as registry/metadata anchors
for the generated domain, but the child-facing story remains gentle and age-
appropriate.
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

RHYME_CADENCE = [
    "by the brook",
    "under the moon",
    "beside the hedge",
    "near the hay",
]

EMOTION_SCALE = ("miffed", "sad", "softened", "glad")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Turn:
    id: str
    verb: str
    bustle: str
    accident: str
    hurt: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _mood_name(v: float) -> str:
    if v <= 0:
        return "calm"
    if v < 1:
        return "miffed"
    if v < 2:
        return "sad"
    if v < 3:
        return "softened"
    return "glad"


def _closeness(v: float) -> str:
    if v <= 0:
        return "far apart"
    if v < 1:
        return "a little apart"
    if v < 2:
        return "near again"
    return "side by side"


def _turn_overlaps(turn: Turn) -> set[str]:
    return {turn.zone}


def predict(world: World, actor: Entity, turn: Turn, comfort: Comfort) -> dict:
    sim = world.copy()
    _do_turn(sim, sim.get(actor.id), turn, narrate=False)
    return {
        "hurt": bool(sim.get(actor.id).memes.get("hurt", 0) >= 1),
        "quarrel": bool(sim.get(actor.id).memes.get("quarrel", 0) >= 1),
        "reconciled": bool(sim.get(actor.id).memes.get("reconcile", 0) >= 1),
    }


def _do_turn(world: World, actor: Entity, turn: Turn, narrate: bool = True) -> None:
    actor.meters[turn.id] = actor.meters.get(turn.id, 0) + 1
    actor.memes["bustle"] = actor.memes.get("bustle", 0) + 1
    if narrate:
        world.say(f"{actor.noun().capitalize()} loved to {turn.verb} {turn.bustle}.")
    if narrate:
        world.say(f"Then came a wee mishap: {turn.accident}, and {actor.pronoun('possessive')} {turn.zone} felt {turn.hurt}.")
    actor.memes["hurt"] = actor.memes.get("hurt", 0) + 1


def _do_quarrel(world: World, a: Entity, b: Entity) -> None:
    a.memes["quarrel"] = a.memes.get("quarrel", 0) + 1
    b.memes["quarrel"] = b.memes.get("quarrel", 0) + 1
    world.say(f"{a.noun().capitalize()} frowned, and {b.noun()} frowned too.")
    world.say("For a little while, the meadow grew quiet and blue.")


def _do_reconcile(world: World, a: Entity, b: Entity, comfort: Comfort) -> None:
    a.memes["reconcile"] = a.memes.get("reconcile", 0) + 1
    b.memes["reconcile"] = b.memes.get("reconcile", 0) + 1
    a.memes["quarrel"] = 0
    b.memes["quarrel"] = 0
    a.memes["hurt"] = max(0, a.memes.get("hurt", 0) - 1)
    b.memes["hurt"] = max(0, b.memes.get("hurt", 0) - 1)
    world.say(f"Then {a.noun()} spoke low and kind: \"{comfort.prep}, and let us be friends again.\"")
    world.say(f"{b.noun().capitalize()} nodded, and the two went {comfort.tail}.")
    world.say("Soon they were side by side, with smiles as bright as a pie.")


def tell(world: World, hero: Entity, friend: Entity, turn: Turn, comfort: Comfort) -> World:
    world.say(f"{hero.noun().capitalize()} was a little {hero.type}, merry in the {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} liked {turn.verb} {turn.bustle}, {world.setting.detail}.")
    world.say(f"{friend.noun().capitalize()} was nearby, with a tidy little grin.")
    world.para()
    _do_turn(world, hero, turn)
    _do_quarrel(world, hero, friend)
    world.para()
    if comfort.helps and turn.id in comfort.helps:
        _do_reconcile(world, hero, friend, comfort)
    else:
        raise StoryError("No gentle reconciliation is available for this turn.")
    world.facts.update(hero=hero, friend=friend, turn=turn, comfort=comfort)
    return world


SETTINGS = {
    "meadow": Setting(
        place="meadow",
        detail="the grass was soft as a pillow",
        afford={"trot", "race", "skip"},
    ),
    "brook": Setting(
        place="brook",
        detail="the water sang over the stones",
        afford={"skip", "hop"},
    ),
    "orchard": Setting(
        place="orchard",
        detail="the apples hung low and sweet",
        afford={"trot", "skip"},
    ),
}

TURNS = {
    "trot": Turn(
        id="trot",
        verb="trot",
        bustle="in the sunny lane",
        accident="a bump sent a pebble to the rear",
        hurt="sore",
        zone="rear",
        keyword="rear",
        tags={"rear", "bump"},
    ),
    "skip": Turn(
        id="skip",
        verb="skip",
        bustle="under the willows",
        accident="a hop and a twist made a tumble at the rear",
        hurt="stung",
        zone="rear",
        keyword="rear",
        tags={"rear", "stumble"},
    ),
    "race": Turn(
        id="race",
        verb="race",
        bustle="along the lane",
        accident="a hurried dart brushed the rear and made a fuss",
        hurt="aching",
        zone="rear",
        keyword="rear",
        tags={"rear", "rush"},
    ),
    "hop": Turn(
        id="hop",
        verb="hop",
        bustle="beside the brook",
        accident="a splash and a slip nudged the rear on a stone",
        hurt="bruised",
        zone="rear",
        keyword="rear",
        tags={"rear", "water"},
    ),
}

COMFORTS = {
    "bandage": Comfort(
        id="bandage",
        label="a soft bandage",
        phrase="soft bandage",
        helps={"trot", "skip", "race", "hop"},
        covers={"rear"},
        prep="let me mend your rear with a soft bandage",
        tail="home by the hedge with a slow and steady pace",
    ),
    "apology": Comfort(
        id="apology",
        label="a gentle apology",
        phrase="gentle apology",
        helps={"trot", "skip", "race", "hop"},
        covers={"rear"},
        prep="let me say I'm sorry for the bump",
        tail="to sit together and share a little cake",
    ),
    "song": Comfort(
        id="song",
        label="a merry song",
        phrase="merry song",
        helps={"trot", "skip", "race", "hop"},
        covers={"rear"},
        prep="let us sing a merry song and mend our hearts",
        tail="to the shade of the old plum tree",
    ),
}

HERO_NAMES = ["Milo", "Pip", "Nell", "Tilly", "Toby", "Bess", "Rory", "Poppy"]
FRIEND_NAMES = ["Dot", "Lark", "Bean", "Moss", "June", "Wren", "Clover", "Fern"]
TRAITS = ["merry", "tiny", "brave", "spry", "cheery", "gentle"]


@dataclass
class StoryParams:
    place: str
    turn: str
    comfort: str
    hero_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world with a rear bump and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--turn", choices=TURNS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["rabbit", "mouse", "duck", "fox", "bear"], default="rabbit")
    ap.add_argument("--friend-type", choices=["rabbit", "mouse", "duck", "fox", "bear"], default="mouse")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, c) for p in SETTINGS for t in SETTINGS[p].afford for c in COMFORTS if t in COMFORTS[c].helps]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.turn and args.comfort and args.turn not in COMFORTS[args.comfort].helps:
        raise StoryError("That comfort cannot mend this sort of rear bump.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.turn is None or c[1] == args.turn)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("No valid combination matches the chosen options.")
    place, turn, comfort = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        turn=turn,
        comfort=comfort,
        hero_name=hero_name,
        friend_name=friend_name,
        hero_type=args.hero_type,
        friend_type=args.friend_type,
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about {f["hero"].id} and {f["friend"].id} in the {world.setting.place}, with a bump to the rear and a warm reconciliation.',
        f'Tell a gentle sing-song tale where {f["hero"].id} gets sore in the rear, then makes up with {f["friend"].id}.',
        f'Write a child-friendly rhyme using the word "rear" and ending with two friends smiling again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, turn, comfort = f["hero"], f["friend"], f["turn"], f["comfort"]
    return [
        QAItem(
            question=f"Who got hurt in the rear during the story?",
            answer=f"{hero.id} got hurt in the rear after a little bump while {hero.pronoun()} was {turn.verb}ing.",
        ),
        QAItem(
            question=f"What helped {hero.id} and {friend.id} make up?",
            answer=f"{comfort.label} helped them reconcile, because it led to kind words and a gentle ending.",
        ),
        QAItem(
            question=f"Where did the mishap happen?",
            answer=f"It happened in the {world.setting.place}, where the story began in a soft and sing-song way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people or friends stop being upset and make peace again.",
        ),
        QAItem(
            question="What is the rear on an animal?",
            answer="The rear is the back part of an animal's body.",
        ),
        QAItem(
            question="Why do friends say sorry after a bump?",
            answer="They say sorry to be kind, fix hurt feelings, and help everyone feel better again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    turn = TURNS[params.turn]
    comfort = COMFORTS[params.comfort]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=[params.trait, "little"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type, traits=["nearby", "kind"]))
    tell(world, hero, friend, turn, comfort)
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
    StoryParams("meadow", "trot", "bandage", "Milo", "Dot", "rabbit", "mouse", "merry"),
    StoryParams("brook", "hop", "song", "Pip", "Lark", "duck", "rabbit", "gentle"),
    StoryParams("orchard", "skip", "apology", "Nell", "Bean", "rabbit", "mouse", "cheery"),
]


ASP_RULES = r"""
valid_combo(P,T,C) :- place(P), turn(T), comfort(C), affords(P,T), helps(C,T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for t in sorted(s.afford):
            lines.append(asp.fact("affords", p, t))
    for t, turn in TURNS.items():
        lines.append(asp.fact("turn", t))
        lines.append(asp.fact("rear_zone", t, turn.zone))
    for c, com in COMFORTS.items():
        lines.append(asp.fact("comfort", c))
        for t in sorted(com.helps):
            lines.append(asp.fact("helps", c, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid_combo/3.\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
