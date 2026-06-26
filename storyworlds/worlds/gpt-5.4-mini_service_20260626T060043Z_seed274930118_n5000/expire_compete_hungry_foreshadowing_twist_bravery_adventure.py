#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/expire_compete_hungry_foreshadowing_twist_bravery_adventure.py
==============================================================================================================

A compact adventure storyworld about a hungry child, a dwindling supply,
a competition, and a brave twist that turns a foreshadowed problem into a win.

Seed tale:
---
A small adventurer finds a packed lunch and a trail map before a hill race.
The lunch will expire by sunset, and two kids compete to reach the flag first.
The hero grows hungry, notices earlier clues about a shortcut, and bravely
takes the narrow path. The twist is that the shortcut reaches the snack tent
before the lunch goes bad, so the hero finishes the adventure fed and proud.

World model:
- physical meters: distance, hunger, freshness, tiredness, speed, clue strength
- emotional memes: courage, worry, hope, pride, rivalry
- expiration is a state change when freshness falls too low
- competition advances both racers, but only the brave route reaches the goal
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    route: str
    goal: str
    shelter: str


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    race_noun: str
    hazard: str
    shortcut: str
    foreshadow: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Supply:
    id: str
    label: str
    phrase: str
    freshness: float = 2.0
    expires_after: float = 1.0
    edible: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.challenge: Optional[Challenge] = None

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.challenge = self.challenge
        w.paragraphs = [[]]
        return w


GIRL_NAMES = ["Mina", "Nora", "Lia", "Ivy", "Zoe", "Pia", "Tess"]
BOY_NAMES = ["Arlo", "Finn", "Owen", "Jace", "Theo", "Leo", "Milo"]
TRAITS = ["curious", "brave", "quick", "steady", "spirited", "bold"]


SETTINGS = {
    "hill": Setting(place="the hill trail", route="narrow trail", goal="flag on the ridge", shelter="the snack tent"),
    "woods": Setting(place="the woods path", route="rooty path", goal="map post", shelter="the ranger shed"),
    "canyon": Setting(place="the canyon walk", route="stone ledge", goal="bright arch", shelter="the cave kiosk"),
}


CHALLENGES = {
    "race": Challenge(
        id="race",
        verb="compete in the hill race",
        gerund="racing up the trail",
        race_noun="race",
        hazard="the lunch would go stale before the finish",
        shortcut="a narrow shortcut behind the rocks",
        foreshadow="a scribbled arrow on the map had hinted at a shortcut earlier",
        twist="the shortcut reached the snack tent just before the lunch expired",
        tags={"race", "shortcut", "hungry"},
    ),
    "treasure": Challenge(
        id="treasure",
        verb="compete for the hidden chest",
        gerund="searching for treasure",
        race_noun="hunt",
        hazard="the trail would close after sunset",
        shortcut="a side path under the branches",
        foreshadow="a bent sign had pointed toward the side path",
        twist="the side path led straight to the chest room",
        tags={"treasure", "shortcut"},
    ),
    "relay": Challenge(
        id="relay",
        verb="compete in the lantern relay",
        gerund="running the relay",
        race_noun="relay",
        hazard="the lantern oil would expire before the last hill",
        shortcut="a quick cut through the meadow",
        foreshadow="a breeze had shown that the meadow was the faster way",
        twist="the meadow cut saved enough time to light the last lantern",
        tags={"relay", "lantern", "shortcut"},
    ),
}


SUPPLIES = {
    "lunchbox": Supply(id="lunchbox", label="lunchbox", phrase="a packed lunch", freshness=2.0, expires_after=1.0),
    "cookie": Supply(id="cookie", label="cookie", phrase="a sugar cookie", freshness=1.5, expires_after=1.0),
    "juice": Supply(id="juice", label="juice", phrase="a berry juice", freshness=1.5, expires_after=1.0),
}


@dataclass
class StoryParams:
    setting: str
    challenge: str
    supply: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with expiry, competition, hunger, foreshadowing, twist, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def reasonableness_gate(challenge: Challenge, supply: Supply) -> bool:
    return challenge.id == "race" and supply.id == "lunchbox"


def explain_rejection(challenge: Challenge, supply: Supply) -> str:
    return (
        f"(No story: this adventure depends on a hungry race with food that can expire, "
        f"but {supply.label} is not a fit for {challenge.verb}. Try --challenge race --supply lunchbox.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.supply:
        if not reasonableness_gate(CHALLENGES[args.challenge], SUPPLIES[args.supply]):
            raise StoryError(explain_rejection(CHALLENGES[args.challenge], SUPPLIES[args.supply]))
    combos = [
        (s, c, p)
        for s in SETTINGS
        for c in CHALLENGES
        for p in SUPPLIES
        if reasonableness_gate(CHALLENGES[c], SUPPLIES[p])
        and (args.setting is None or args.setting == s)
        and (args.challenge is None or args.challenge == c)
        and (args.supply is None or args.supply == p)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, supply = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, supply=supply, name=name, gender=gender, parent=parent, trait=trait)


def _advance(world: World) -> None:
    hero = world.get("hero")
    rival = world.get("rival")
    supply = world.get("supply")
    ch = world.challenge
    if not ch:
        return
    if hero.meters["distance"] < 3:
        hero.meters["distance"] += 1.3
        rival.meters["distance"] += 1.1
        hero.meters["hunger"] += 0.6
        hero.meters["tiredness"] += 0.2
        rival.meters["tiredness"] += 0.2
    if hero.meters["distance"] >= 1.5 and "foreshadowed" not in world.fired:
        world.fired.add(("foreshadowed",))
        world.say(f"Earlier, {ch.foreshadow}.")
    if hero.meters["hunger"] >= THRESHOLD and not world.fired.__contains__(("hungry",)):
        world.fired.add(("hungry",))
        hero.memes["worry"] += 1
        world.say(f"By the middle of the trail, {hero.id} felt hungry and slow.")
    if supply.meters["freshness"] > 0:
        supply.meters["freshness"] -= 0.7
        if supply.meters["freshness"] <= 0 and ("expired",) not in world.fired:
            world.fired.add(("expired",))
            world.say(f"The food in the {supply.label} expired right as the path grew steep.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    challenge = CHALLENGES[params.challenge]
    supply_cfg = SUPPLIES[params.supply]
    world = World(setting)
    world.challenge = challenge

    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, meters={"distance": 0.0, "hunger": 0.0, "tiredness": 0.0, "freshness": supply_cfg.freshness}, memes={"courage": 0.0, "worry": 0.0, "hope": 0.0, "pride": 0.0, "rivalry": 0.0}))
    rival = world.add(Entity(id="rival", kind="character", type="boy" if params.gender == "girl" else "girl", label="the other kid", meters={"distance": 0.0, "tiredness": 0.0}, memes={"rivalry": 1.0}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    supply = world.add(Entity(id="supply", type="thing", label=supply_cfg.label, phrase=supply_cfg.phrase, meters={"freshness": supply_cfg.freshness}, owner="hero"))

    world.say(f"{hero.label} was a {params.trait} little {params.gender} who loved adventure.")
    world.say(f"Before the {challenge.race_noun}, {hero.label} carried {supply.phrase} and watched the trail sign.")
    world.say(f"{params.parent.capitalize()} said the day would be safer if they kept an eye on the lunch, because it could expire before sunset.")

    world.para()
    world.say(f"At {setting.place}, {hero.label} and {rival.label} started to {challenge.verb}.")
    world.say(f"{challenge.foreshadow.capitalize()}.")
    world.say(f"{hero.label} kept the clue in mind while the two kids began to compete.")

    for _ in range(2):
        _advance(world)

    world.say(f"Then {hero.label} got extra hungry and looked at the steep path ahead.")
    world.say(f"The others wanted the easy road, but {hero.label} noticed {challenge.shortcut}.")

    world.para()
    hero.memes["courage"] += 1
    world.say(f"That was the brave choice.")
    world.say(f"{hero.label} took a deep breath and went first.")
    world.say(f"{hero.pronoun().capitalize()} trusted the clue, even though the shortcut looked narrow.")

    # twist / resolution
    _advance(world)
    _advance(world)
    world.say(f"{challenge.twist.capitalize()}.")
    hero.memes["hope"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.label} reached {setting.shelter} with the lunch still good, then ate while the rival arrived behind.")
    world.say(f"In the end, bravery turned the hungry race into a happy adventure.")

    world.facts.update(
        hero=hero,
        rival=rival,
        parent=parent,
        supply=supply,
        challenge=challenge,
        setting=setting,
        resolved=True,
        expired=supply.meters["freshness"] <= 0,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    ch = f["challenge"]
    supply = f["supply"]
    return [
        f'Write a short adventure story for a young child that uses the word "hungry" and includes a brave choice.',
        f"Tell a story where {hero.label} must compete in a {ch.race_noun} while carrying {supply.phrase} that can expire.",
        f"Write an adventure with foreshadowing, a twist, and bravery where a child notices an earlier clue and takes a shortcut.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    parent = f["parent"]
    supply = f["supply"]
    ch = f["challenge"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.label}, a {hero.type} who loved adventure and had to make a brave choice.",
        ),
        QAItem(
            question=f"What did {hero.label} and {rival.label} do at {setting.place}?",
            answer=f"They competed in a {ch.race_noun} at {setting.place}, trying to get ahead on the trail.",
        ),
        QAItem(
            question=f"Why did the {parent.type} warn about {supply.label}?",
            answer=f"{parent.label.capitalize()} warned because {supply.phrase} could expire before the end of the day.",
        ),
        QAItem(
            question=f"What helped {hero.label} choose the shortcut?",
            answer=f"An earlier clue foreshadowed the shortcut, so {hero.label} remembered it and chose the narrow path.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.label} reaching {setting.shelter} in time, brave and proud, with the lunch still good to eat.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean for food to expire?", answer="When food expires, it is too old to eat safely or it no longer tastes fresh."),
        QAItem(question="What is competition?", answer="Competition is when people try to do their best and see who reaches a goal first or does the best job."),
        QAItem(question="What is bravery?", answer="Bravery means doing something scary or hard even when you feel nervous."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is when a story gives a small clue early that helps later events make sense."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise that changes what you expected to happen."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(parts)


CURATED = [
    StoryParams(setting="hill", challenge="race", supply="lunchbox", name="Mina", gender="girl", parent="mother", trait="brave"),
    StoryParams(setting="woods", challenge="race", supply="lunchbox", name="Arlo", gender="boy", parent="father", trait="curious"),
    StoryParams(setting="canyon", challenge="race", supply="lunchbox", name="Ivy", gender="girl", parent="mother", trait="steady"),
]


ASP_RULES = r"""
setting(hill). setting(woods). setting(canyon).
challenge(race).
supply(lunchbox).

valid(S,C,P) :- setting(S), challenge(C), supply(P), C = race, P = lunchbox.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for p in SUPPLIES:
        lines.append(asp.fact("supply", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("hill", "race", "lunchbox"), ("woods", "race", "lunchbox"), ("canyon", "race", "lunchbox")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_story_combinations(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.setting or args.challenge or args.supply or args.gender:
        return [resolve_params(args, rng)]
    combos = CURATED if args.all else [resolve_params(args, rng)]
    return combos


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
