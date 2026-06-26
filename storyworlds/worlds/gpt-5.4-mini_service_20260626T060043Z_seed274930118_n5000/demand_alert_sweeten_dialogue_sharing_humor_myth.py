#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/demand_alert_sweeten_dialogue_sharing_humor_myth.py
================================================================================================

A small myth-style story world about a stern demand, an early alert, and a
softening turn through sharing, dialogue, and humor.

Seed tale:
---
In an old valley, the River Oak kept the village safe, and the villagers left
honey at its roots each new moon. One dusk, a stone owl cried out that the river
spirit had made a harsher demand: not just honey, but the whole lantern of song
from the market shrine. The people grew worried, because the lantern was the
only light for the night paths.

A clever child named Nara did not argue at once. She listened to the alert,
carried sweet cakes to the oak, and told a bright joke about a goose wearing a
crown. The elder who heard her laughed, then spoke kindly to the spirit. Nara
shared the cakes, and the spirit agreed to accept them and a song instead of
the lantern.

This script turns that premise into a constrained simulation. The spirit's
demand creates pressure, the alert arrives before damage, and sharing plus
humor can sweeten the exchange into a better bargain.
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
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "spirit" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    plurality: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "elder", "child"}
        male = {"boy", "man", "father", "king", "bard", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def plural_pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old valley"
    holy_site: str = "the river oak"


@dataclass
class Demand:
    label: str
    ask: str
    risk: str
    target: str


@dataclass
class Gift:
    label: str
    phrase: str
    sweetens: set[str]
    shares: bool = True


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.alerted: bool = False
        self.angered: bool = False
        self.resolved: bool = False
        self.offer: Optional[str] = None

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.alerted = self.alerted
        clone.angered = self.angered
        clone.resolved = self.resolved
        clone.offer = self.offer
        return clone


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------
NAMES = ["Nara", "Milo", "Ari", "Sera", "Lio", "Tavi"]
VOICE_TYPES = ["girl", "boy", "child"]
ELDER_TYPES = ["elder", "bard"]
TRAITS = ["clever", "brave", "kind", "quick-witted", "gentle"]

DEMANDS = {
    "lantern": Demand(
        label="the lantern of song",
        ask="bring the lantern of song from the shrine",
        risk="the night paths would lose their light",
        target="lantern",
    ),
    "bread": Demand(
        label="the basket of sunrise bread",
        ask="leave the basket of sunrise bread at the river root",
        risk="the morning feast would be short",
        target="bread",
    ),
    "bells": Demand(
        label="the silver bells",
        ask="hang the silver bells on the oak branch",
        risk="the blessing-chime would be taken from the village gate",
        target="bells",
    ),
}

GIFTS = {
    "honey": Gift(
        label="honey cakes",
        phrase="warm honey cakes wrapped in leaf cloth",
        sweetens={"stern", "hungry", "wary"},
    ),
    "berries": Gift(
        label="sweet berries",
        phrase="a little bowl of ripe berries",
        sweetens={"stern", "hungry", "wary"},
    ),
    "milk": Gift(
        label="milk bread",
        phrase="milk bread still soft from the oven",
        sweetens={"stern", "hungry", "wary"},
    ),
    "song": Gift(
        label="a song",
        phrase="a bright song with a steady refrain",
        sweetens={"stern", "lonely", "wary"},
    ),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    hero_type: str
    trait: str
    elder_type: str
    demand: str
    gift: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Facts and reasonableness
# ---------------------------------------------------------------------------
def demand_is_reasonable(demand: Demand) -> bool:
    return bool(demand.ask and demand.risk and demand.target)


def gift_helps(demand: Demand, gift: Gift) -> bool:
    return bool(gift.sweetens) and demand.target in {"lantern", "bread", "bells"}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for did, demand in DEMANDS.items():
        if not demand_is_reasonable(demand):
            continue
        for gid, gift in GIFTS.items():
            if gift_helps(demand, gift):
                combos.append((did, gid))
    return combos


def explain_rejection(demand: Demand, gift: Gift) -> str:
    return (
        f"(No story: the demand for {demand.label} is not matched by {gift.label} "
        f"as a believable sweetening gift.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def alert(world: World, hero: Entity, elder: Entity, demand: Demand) -> None:
    world.alerted = True
    hero.memes["alertness"] = hero.memes.get("alertness", 0) + 1
    world.say(
        f"At dusk, a stone owl cried out, and {hero.id} heard the warning first. "
        f"The owl said the river spirit had made a demand for {demand.label}."
    )
    world.say(
        f"{elder.id} looked toward the old valley road and said the message came "
        f"before any harm was done."
    )


def confront(world: World, hero: Entity, spirit: Entity, demand: Demand) -> None:
    spirit.memes["demand"] = spirit.memes.get("demand", 0) + 1
    world.angered = True
    world.say(
        f"At the holy root, {spirit.id} stood in the shadow of the oak and "
        f"repeated its demand: {demand.ask}."
    )
    world.say(
        f"The village grew still, because everyone feared {demand.risk}."
    )


def share(world: World, hero: Entity, elder: Entity, gift: Gift) -> None:
    hero.meters["sharing"] = hero.meters.get("sharing", 0) + 1
    elder.meters["sharing"] = elder.meters.get("sharing", 0) + 1
    world.offer = gift.label
    world.say(
        f"Then {hero.id} did not rush to argue. {hero.pronoun().capitalize()} "
        f"shared {gift.phrase} with the elder and the waiting villagers."
    )
    world.say(
        f"The smell of the gift softened the air around the oak."
    )


def joke(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    elder.memes["humor"] = elder.memes.get("humor", 0) + 1
    world.say(
        f'{hero.id} smiled and told a joke about a goose wearing a crown and '
        f"trying to bow to a pond."
    )
    world.say(
        f"{elder.id} laughed so hard that even the leaves seemed to quiver."
    )


def sweeten(world: World, spirit: Entity, demand: Demand, gift: Gift, elder: Entity) -> None:
    spirit.memes["softness"] = spirit.memes.get("softness", 0) + 1
    spirit.memes["sweetened"] = spirit.memes.get("sweetened", 0) + 1
    world.resolved = True
    world.say(
        f"The spirit listened, and the laughter made the old demand less hard."
    )
    world.say(
        f"By the end, the spirit accepted {gift.label} and a promise of {demand.label.split()[-1]}-song instead of taking the lantern."
    )


def tell(setting: Setting, demand: Demand, gift: Gift,
         hero_name: str = "Nara", hero_type: str = "girl",
         trait: str = "clever", elder_type: str = "elder") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    spirit = world.add(Entity(id="RiverSpirit", kind="spirit", type="thing", label="the river spirit"))

    world.say(
        f"In {setting.place}, the people honored {setting.holy_site} with small gifts each new moon."
    )
    world.say(
        f"{hero.id} was a {trait} {hero_type} who listened carefully to every sign."
    )

    world.para()
    alert(world, hero, elder, demand)

    world.para()
    confront(world, hero, spirit, demand)
    share(world, hero, elder, gift)
    joke(world, hero, elder)
    sweeten(world, spirit, demand, gift, elder)

    world.facts.update(
        hero=hero,
        elder=elder,
        spirit=spirit,
        demand=demand,
        gift=gift,
        setting=setting,
        resolved=world.resolved,
        alerted=world.alerted,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, demand, gift = f["hero"], f["demand"], f["gift"]
    return [
        f'Write a short myth about a child named {hero.id}, an alert from an owl, '
        f'and a spirit who makes a demand for {demand.label}.',
        f'Create a child-friendly legend where sharing {gift.label} and using humor '
        f'help soften a river spirit\'s demand.',
        f'Write a gentle myth in which a warning arrives in time, then dialogue and '
        f'shared food change the ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, spirit = f["hero"], f["elder"], f["spirit"]
    demand, gift = f["demand"], f["gift"]
    return [
        QAItem(
            question=f"Who heard the alert first in the story?",
            answer=f"{hero.id} heard the alert first when the stone owl cried out.",
        ),
        QAItem(
            question=f"What demand did the river spirit make?",
            answer=f"The river spirit demanded {demand.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} share to soften the moment?",
            answer=f"{hero.id} shared {gift.phrase} with the elder and the villagers.",
        ),
        QAItem(
            question=f"How did the child use humor?",
            answer=f"{hero.id} told a joke about a goose wearing a crown, and that made {elder.id} laugh.",
        ),
        QAItem(
            question=f"How did the ending change after the sharing and joke?",
            answer=f"The spirit became softer and agreed to accept {gift.label} and a song instead of taking the lantern.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alert?",
            answer="An alert is a warning that tells people something important is happening soon.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to give some of what you have to other people so everyone can enjoy it.",
        ),
        QAItem(
            question="Why can humor help?",
            answer="Humor can help because a funny moment can make people feel less tense and more willing to talk kindly.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  alerted={world.alerted} angered={world.angered} resolved={world.resolved}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Demand, alert, sharing, humor, and sweetening.
valid_story(D, G) :- demand(D), gift(G), demand_ok(D), gift_ok(G), sweeten_ok(D, G).
demand_ok(D) :- demand(D).
gift_ok(G) :- gift(G).
sweeten_ok(D, G) :- demand(D), gift(G), target(D, T), sweetens(G, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for did, d in DEMANDS.items():
        lines.append(asp.fact("demand", did))
        lines.append(asp.fact("ask", did, d.ask))
        lines.append(asp.fact("risk", did, d.risk))
        lines.append(asp.fact("target", did, d.target))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for t in sorted(g.sweetens):
            lines.append(asp.fact("sweetens", gid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((d, g) for d, g in valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth story world about demand, alert, sweeten, dialogue, sharing, and humor.")
    ap.add_argument("--demand", choices=DEMANDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "child"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.demand and args.gift:
        if not gift_helps(DEMANDS[args.demand], GIFTS[args.gift]):
            raise StoryError(explain_rejection(DEMANDS[args.demand], GIFTS[args.gift]))
    combos = valid_combos()
    if args.demand:
        combos = [c for c in combos if c[0] == args.demand]
    if args.gift:
        combos = [c for c in combos if c[1] == args.gift]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    demand_id, gift_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(VOICE_TYPES)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    return StoryParams(
        name=name,
        hero_type=hero_type,
        trait=trait,
        elder_type=elder_type,
        demand=demand_id,
        gift=gift_id,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        Setting(),
        DEMANDS[params.demand],
        GIFTS[params.gift],
        hero_name=params.name,
        hero_type=params.hero_type,
        trait=params.trait,
        elder_type=params.elder_type,
    )
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
        import asp
        models = asp_valid_stories()
        print(f"{len(models)} compatible demand/gift pairs:\n")
        for d, g in models:
            print(f"  {d:10} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for d, g in valid_combos():
            p = StoryParams(
                name="Nara",
                hero_type="girl",
                trait="clever",
                elder_type="elder",
                demand=d,
                gift=g,
            )
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
