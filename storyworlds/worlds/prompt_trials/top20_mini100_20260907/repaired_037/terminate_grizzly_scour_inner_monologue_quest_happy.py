#!/usr/bin/env python3
"""
Storyworld: a superhero quest about a grizzly, a careful scour, and a happy ending.

Seed tale:
A young hero and a grizzly had to scour a ruined rooftop for a missing signal
battery before sunset. The hero worried the grizzly would cause trouble, but
the grizzly turned out to be gentle and helpful. Together they found the battery
under a broken vent, restored the signal, and saved the city watch from losing
contact. The hero's inner monologue shifted from fear to trust, and the quest
ended happily with a bright evening sky.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hero", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    skyline: str = ""


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
    setting: str
    hero_name: str
    grizzly_name: str
    seed: Optional[int] = None
    opening: int = 0
    worry: int = 0
    turn: int = 0
    ending: int = 0


SETTINGS = {
    "rooftop": Setting(place="the rooftop", affords={"battery", "vent", "signal"}, skyline="bright towers"),
    "alley": Setting(place="the alley", affords={"battery", "vent", "signal"}, skyline="glimmering windows"),
    "bridge": Setting(place="the bridge", affords={"battery", "vent", "signal"}, skyline="river lights"),
}

HERO_NAMES = ["Nova", "Jet", "Mira", "Spark", "Sky", "Comet"]
GRIZZLY_NAMES = ["Grumble", "Bruno", "Paws", "Moss", "Tundra", "Atlas"]

OPENINGS = [
    "At dusk, {hero}, a young hero, landed softly on {place} for a quest with {grizzly}, the grizzly.",
    "The city hummed below while {hero} and {grizzly} stepped onto {place} to begin a rescue quest.",
    "With a red cape fluttering, {hero} checked {place} beside {grizzly} and promised to finish the quest before dark.",
    "{hero} and {grizzly} arrived at {place} just as the skyline turned gold, ready for one important quest.",
]

WORRIES = [
    "{hero} thought, If the grizzly charges ahead, the battery might be smashed.",
    "{hero} thought, Maybe I should have come alone.",
    "{hero}'s inner monologue whispered, What if this grizzly is too wild for a careful mission?",
    "{hero} wondered in silence whether trust could survive a rooftop search.",
]

TURNS = [
    "Then {grizzly} sniffed a bent vent cover and pointed a paw at a tiny blue light.",
    "{grizzly} crouched low, listened, and rumbled, 'I hear a buzz under this vent.'",
    "{grizzly} said, 'Look closely.' Then {hero} noticed scratch marks leading to the vent.",
    "A gentle voice came from {grizzly}: 'The battery is near. Let's scour the edges first.'",
]

ENDINGS = [
    "Together they lifted the vent cover, found the missing battery, and restored the signal with a happy flash across the city.",
    "They scoured the rooftop edge, uncovered the battery, and watched the watchtower light blink back to life in a happy ending.",
    "The grizzly reached under the broken vent, the battery clicked into {hero}'s hands, and the whole city breathed easier.",
    "After one final scour, {hero} and {grizzly} repaired the signal and smiled at the bright, happy sky.",
]


ASP_RULES = r"""
#show valid/2.
setting(rooftop). setting(alley). setting(bridge).
affords(rooftop,battery). affords(rooftop,vent). affords(rooftop,signal).
affords(alley,battery). affords(alley,vent). affords(alley,signal).
affords(bridge,battery). affords(bridge,vent). affords(bridge,signal).
valid(S,A) :- affords(S,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple]:
    return sorted((sid, a) for sid, s in SETTINGS.items() for a in s.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_world(params: StoryParams) -> StoryState:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = SETTINGS[params.setting]
    world = StoryState(setting=setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero", traits=["brave", "careful"], memes={"hope": 1}))
    grizzly = world.add(Entity(id=params.grizzly_name, kind="character", type="grizzly", traits=["strong", "gentle"], memes={"calm": 1}))
    battery = world.add(Entity(id="battery", kind="thing", type="battery", label="signal battery", owner="city_watch", caretaker="city_watch"))
    vent = world.add(Entity(id="vent", kind="thing", type="vent", label="broken vent", owner="city_watch", caretaker="city_watch"))
    signal = world.add(Entity(id="signal", kind="thing", type="signal", label="signal beacon", owner="city_watch", caretaker="city_watch"))

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(hero=hero.id, grizzly=grizzly.id, place=setting.place))
    world.say(f"The mission was simple: scour {setting.place} and terminate the silence before the watch lost contact.")
    world.say(f'"Stay close," {hero.id} said. "This is a quest, not a race."')
    world.say(f'"I know," {grizzly.id} answered. "I am here to help."')

    world.para()
    world.say(WORRIES[params.worry % len(WORRIES)].format(hero=hero.id))
    hero.memes["fear"] = 1
    hero.memes["doubt"] = 1
    world.say(f"But {grizzly.id} padded carefully over the metal and sniffed the wind instead of barging ahead.")
    world.say(TURNS[params.turn % len(TURNS)].format(hero=hero.id, grizzly=grizzly.id))
    world.say(f'{hero.id} listened, then said, "You were right. We should scour the edges first."')
    grizzly.memes["trust"] = 1
    hero.memes["trust"] = 1

    world.para()
    world.say(f"Under the broken vent, they found the battery tucked in dust and a curl of wire.")
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(hero=hero.id, grizzly=grizzly.id))
    world.say(f'"We did it together," {hero.id} said with a grin. "{grizzly.id}, you were my best teammate."')
    world.say(f'"And you were mine," {grizzly.id} replied, and the happy ending shone over {setting.place}.')
    world.facts.update(hero=hero, grizzly=grizzly, battery=battery, vent=vent, signal=signal, setting=params.setting)
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero'].id} and {f['grizzly'].id} on a quest to scour {world.setting.place}.",
        "Include inner monologue, spoken dialogue, and a happy ending after the missing battery is found.",
        "Make the grizzly helpful and keep the tone adventurous, child-friendly, and heroic.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who went on the quest?",
            answer=f"{f['hero'].id} and {f['grizzly'].id} went on the quest together.",
        ),
        QAItem(
            question="What did they need to find?",
            answer="They needed to find the missing signal battery.",
        ),
        QAItem(
            question="What changed in the hero's inner monologue?",
            answer="At first the hero worried the grizzly might cause trouble, but after watching the grizzly help, the hero started to trust the grizzly.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The battery was restored, the signal came back, and the ending was happy.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large kind of bear.",
        ),
        QAItem(
            question="What does it mean to scour something?",
            answer="To scour something means to search it carefully and thoroughly.",
        ),
        QAItem(
            question="What is a quest in a story?",
            answer="A quest is a journey or mission to achieve an important goal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    hero = args.hero or rng.choice(HERO_NAMES)
    grizzly = args.grizzly or rng.choice(GRIZZLY_NAMES)
    if hero == grizzly:
        grizzly = rng.choice([n for n in GRIZZLY_NAMES if n != hero])
    return StoryParams(
        setting=setting,
        hero_name=hero,
        grizzly_name=grizzly,
        opening=rng.randrange(len(OPENINGS)),
        worry=rng.randrange(len(WORRIES)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: a quest with a grizzly and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--grizzly")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid()
        print(f"{len(model)} valid combinations:\n")
        for setting, afford in model:
            print(f"  {setting:10} {afford}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            params = StoryParams(setting=setting, hero_name="Nova", grizzly_name="Grumble")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
