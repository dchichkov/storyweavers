#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/courteous_ail_lesson_learned_magic_space_adventure.py
==========================================================================================================

A small, classical story world for a space-adventure seed with a courteous
twist, a little ailment/ail hook, and a magical lesson learned.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("spark", "damage", "wear", "care", "joy", "worry", "courtesy", "lesson"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)
    spacey: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


MESS_KINDS = {"spark", "dust"}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "orbital_hub": Place("the orbital hub", affords={"starglow", "comet_race"}),
    "moon_dock": Place("the moon dock", affords={"starglow"}),
    "nebula_garden": Place("the nebula garden", affords={"starglow", "comet_race"}),
}

ACTIVITIES = {
    "starglow": Activity(
        id="starglow",
        verb="stir the star glitter",
        gerund="stirring the star glitter",
        rush="run toward the glowing bowl",
        risk="sparkly dust could cling to the suit",
        zone={"torso", "arms"},
        keyword="magic",
        tags={"magic", "spark"},
    ),
    "comet_race": Activity(
        id="comet_race",
        verb="race the comet kites",
        gerund="racing comet kites",
        rush="dash after the bright kites",
        risk="fast turns could bump the helmet",
        zone={"head", "torso"},
        keyword="lesson learned",
        tags={"lesson", "space"},
    ),
}

PRIZES = {
    "helmet": Prize("helmet", "a shiny new helmet", "head"),
    "sash": Prize("sash", "a bright command sash", "torso"),
    "boots": Prize("boots", "little moon boots", "feet", plural=True),
}

GEAR = [
    Gear("visor", "a clear bubble visor", {"head"}, {"spark", "dust"}, "put on a clear bubble visor first", "slid on the clear bubble visor"),
    Gear("wrap", "a dustwrap", {"torso"}, {"spark", "dust"}, "wear a dustwrap first", "buckled the dustwrap"),
    Gear("boots_guard", "soft star boots", {"feet"}, {"dust"}, "put on soft star boots first", "pulled on the soft star boots", plural=True),
]

GIRL_NAMES = ["Nova", "Mira", "Luna", "Zia", "Iris"]
BOY_NAMES = ["Orion", "Finn", "Theo", "Kai", "Arlo"]
TRAITS = ["courteous", "curious", "brave", "gentle"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if prize.region in g.covers and any(k in g.guards for k in activity.tags):
            return g
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not threaten {prize.label} in a way any gear here can fix.)"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pname, place in SETTINGS.items():
        for aid in place.affords:
            act = ACTIVITIES[aid]
            for prn, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((pname, aid, prn))
    return out


def _do_activity(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    world.zone = set(act.zone)
    actor.memes["joy"] += 1
    actor.meters["spark"] += 1
    if prize := world.facts.get("prize_entity"):
        if prize.region in world.zone and not world.covered(actor, prize.region):
            prize.meters["damage"] += 1
    if narrate:
        world.say(f"{actor.id} started {act.gerund}.")
        if prize and prize.meters["damage"] > 0:
            world.say(f"{prize.label.capitalize()} got a little dusty.")


def predict(world: World, actor: Entity, act: Activity, prize_id: str) -> bool:
    sim = World(world.place)
    sim.entities = {k: Entity(**{**e.__dict__, "meters": dict(e.meters), "memes": dict(e.memes), "covers": set(e.covers)}) for k, e in world.entities.items()}
    sim.facts = dict(world.facts)
    _do_activity(sim, sim.get(actor.id), act, narrate=False)
    return sim.entities[prize_id].meters["damage"] > 0


def tell(place: Place, act: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    prize = world.add(Entity(id="prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=helper.id, region=prize_cfg.region, plural=prize_cfg.plural))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["prize_entity"] = prize
    world.facts["activity"] = act
    world.facts["prize_cfg"] = prize_cfg

    world.say(f"{hero.id} was a {trait} little {hero.type} who traveled through {place.name}.")
    world.say(f"{hero.pronoun().capitalize()} loved {act.gerund}, and {helper.label} kept a {prize.label} ready for the journey.")
    world.say(f"One day, {hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} {prize.label} could get damaged.")

    world.para()
    world.say(f"{hero.id} looked at the glittering station and took a careful breath.")
    if predict(world, hero, act, prize.id):
        world.say(f'"If I rush," {hero.pronoun()} said, "my {prize.label} will get {act.risk}."')
    world.say(f"{helper.label.capitalize()} nodded and said, " + f'"Let\'s be {trait} and choose the safe way."')

    gear = select_gear(act, prize_cfg)
    if gear is None:
        raise StoryError(explain_rejection(act, prize_cfg))
    gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, protective=True, covers=set(gear.covers), plural=gear.plural))
    gear_ent.worn_by = hero.id

    world.para()
    hero.memes["courtesy"] += 1
    hero.memes["lesson"] += 1
    world.say(f"{hero.id} smiled, thanked {helper.label}, and chose the polite plan.")
    world.say(f'They {gear.tail} and then went back to the fun part of the trip.')
    _do_activity(world, hero, act)
    world.say(f"In the end, {hero.id} was {act.gerund}, the {prize.label} stayed safe, and everyone learned that magic worked best with courtesy.")

    world.facts.update(gear=gear_ent, resolved=True, risk=predict(world, hero, act, prize.id))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short space-adventure story for preschoolers that includes the word "{act.keyword}".',
        f"Tell a gentle story about {hero.id}, who is {hero.pronoun('possessive')} {hero.type}, and a magical choice that keeps {prize.label} safe.",
        f'Write a tiny story where a courteous child learns a lesson in space and uses magic the careful way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    act = f["activity"]
    prize = f["prize_cfg"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the story about at {world.place.name}?",
            answer=f"It is about {hero.id}, a {hero.type} who travels through {world.place.name} with {helper.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before choosing the safer plan?",
            answer=f"{hero.id} wanted to {act.verb}, but that could have hurt {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep the {prize.label} safe?",
            answer=f"{gear.label} helped because it covered the right part of the body and matched the magical, dusty part of the adventure.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that being courteous and careful can make magic work out well in space.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a space helmet for?",
            answer="A space helmet helps protect your head and lets you breathe safely in space.",
        ),
        QAItem(
            question="What does courteous mean?",
            answer="Courteous means being polite, kind, and respectful to other people.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wondrous that can do special things that do not happen in ordinary life.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for prn, p in PRIZES.items():
        lines.append(asp.fact("prize", prn))
        lines.append(asp.fact("worn_on", prn, p.region))
        if p.plural:
            lines.append(asp.fact("plural", prn))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gg in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gg))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), tag(A,T), guards(G,T), covers(G,R), worn_on(P,R), zone(A,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure with courtesy, ail, magic, and a learned lesson.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, activity, prize, hero_name, gender, helper_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero_name, params.hero_type, params.helper_type, params.trait)
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


GIRL_NAMES = ["Nova", "Mira", "Luna", "Zia", "Ivy"]
BOY_NAMES = ["Orion", "Finn", "Theo", "Kai", "Arlo"]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams("orbital_hub", "starglow", "helmet", "Nova", "girl", "mother", "courteous"),
            StoryParams("moon_dock", "starglow", "sash", "Orion", "boy", "father", "gentle"),
            StoryParams("nebula_garden", "comet_race", "helmet", "Mira", "girl", "mother", "brave"),
        ]:
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
