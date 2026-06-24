#!/usr/bin/env python3
"""
storyworlds/worlds/retard_sound_effects_happy_ending_adventure.py
==================================================================

A small adventure storyworld built from a seed about sound effects, a happy
ending, and a careful, high-spirited rescue.

Core premise:
- A young adventurer wants to cross a lively place and reach a glittering prize.
- The journey becomes risky when the path gets noisy, slippery, or fast.
- A helper uses a simple tool or signal to slow the danger down.
- The story ends with a cheerful victory image and an audible sound effect.

This world keeps the prose child-facing, concrete, and state-driven.
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
    plural: bool = False
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


@dataclass(frozen=True)
class Setting:
    place: str
    outdoors: bool = True
    affords: tuple[str, ...] = ()


@dataclass(frozen=True)
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    sound: str
    zone: str
    keyword: str


@dataclass(frozen=True)
class Prize:
    id: str
    label: str
    phrase: str
    zone: str
    plural: bool = False


@dataclass(frozen=True)
class Gear:
    id: str
    label: str
    help_verb: str
    sound: str
    protects: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "canyon_trail": Setting(place="the canyon trail", outdoors=True, affords=("bridge", "cave", "rope")),
    "harbor_docks": Setting(place="the harbor docks", outdoors=True, affords=("boat", "bridge", "rope")),
    "forest_pass": Setting(place="the forest pass", outdoors=True, affords=("bridge", "cave")),
}

CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        verb="cross the swaying bridge",
        gerund="crossing the swaying bridge",
        rush="dash over the bridge",
        danger="the boards could wobble and shake",
        sound="creak",
        zone="feet",
        keyword="bridge",
    ),
    "cave": Challenge(
        id="cave",
        verb="enter the dark cave",
        gerund="exploring the cave",
        rush="hurry into the cave",
        danger="rocks could rattle down",
        sound="drip",
        zone="torso",
        keyword="cave",
    ),
    "boat": Challenge(
        id="boat",
        verb="ride the little boat",
        gerund="riding the little boat",
        rush="jump into the boat",
        danger="the current could pull too fast",
        sound="splash",
        zone="whole",
        keyword="boat",
    ),
    "rope": Challenge(
        id="rope",
        verb="slide down the rope",
        gerund="sliding down the rope",
        rush="grab the rope and go",
        danger="the rope could zip too quickly",
        sound="whoosh",
        zone="hands",
        keyword="rope",
    ),
}

PRIZES = {
    "crown": Prize(id="crown", label="golden crown", phrase="a tiny golden crown", zone="head"),
    "lantern": Prize(id="lantern", label="lantern", phrase="a bright lantern", zone="hands"),
    "map": Prize(id="map", label="map", phrase="a curled treasure map", zone="hands"),
}

GEAR = {
    "brake": Gear(id="brake", label="a brake lever", help_verb="slow the danger down", sound="click", protects="whole"),
    "gloves": Gear(id="gloves", label="soft gloves", help_verb="hold on safely", sound="zip", protects="hands"),
    "helm": Gear(id="helm", label="a sturdy helm", help_verb="keep the head safe", sound="clink", protects="head"),
}

NAMES = ["Mina", "Tobi", "Jasper", "Lila", "Nora", "Pip", "Theo", "Ada"]
TYPES = ["girl", "boy"]
PARENTS = ["mother", "father", "guardian"]
TRAITS = ["brave", "curious", "cheerful", "bold"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    hero_type: str
    parent: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
% A challenge risks a prize when the challenge zone matches the prize zone,
% or when the challenge affects the whole body.
risk(C, P) :- challenge(C), prize(P), zone(C, Z), zone(P, Z).
risk(C, P) :- challenge(C), prize(P), zone(C, whole).

% Gear is a valid help when it protects the threatened zone.
fix(G, P) :- gear(G), prize(P), zone(G, whole).
fix(G, P) :- gear(G), prize(P), zone(G, Z), zone(P, Z).
valid_story(Place, C, P) :- setting(Place), affords(Place, C), risk(C, P), fix(_, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for c in s.affords:
            lines.append(asp.fact("affords", sid, c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("zone", cid, c.zone))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("zone", pid, p.zone))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("zone", gid, g.protects))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for c in s.affords:
            ch = CHALLENGES[c]
            for p in PRIZES.values():
                if ch.zone == p.zone or ch.zone == "whole":
                    if p.zone == "head" and "helm" not in GEAR:
                        continue
                    out.append((place, c, p.id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure world with sound effects and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", dest="hero_type", choices=TYPES)
    ap.add_argument("--parent", choices=PARENTS)
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
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid adventure combination matches those choices.")
    place, challenge, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        challenge=challenge,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        hero_type=args.hero_type or rng.choice(TYPES),
        parent=args.parent or rng.choice(PARENTS),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    w = World(SETTINGS[params.place])
    hero = w.add(Entity(id=params.name, kind="character", type=params.hero_type))
    parent = w.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    prize = w.add(Entity(id="prize", type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    gear = GEAR["brake"] if params.challenge == "boat" else (GEAR["gloves"] if params.challenge == "rope" else GEAR["helm"])
    w.facts.update(hero=hero, parent=parent, prize=prize, gear=gear, challenge=CHALLENGES[params.challenge], params=params)

    ch = CHALLENGES[params.challenge]

    w.say(f"{hero.id} was a little {params.trait} {hero.type} who loved adventures.")
    w.say(f"{hero.pronoun().capitalize()} carried {hero.pronoun('possessive')} {prize.label} like a real explorer.")
    w.para()
    w.say(f"At {w.setting.place}, the path opened toward the {ch.keyword}.")
    w.say(f"{hero.id} wanted to {ch.verb}, but {ch.danger}.")
    w.say(f"\"{ch.sound}!\" went the place as the danger woke up.")
    w.para()
    w.say(f"{hero.pronoun('possessive').capitalize()} {params.parent} saw the trouble and held up {gear.label}.")
    w.say(f"\"We can {gear.help_verb},\" {params.parent} said. \"Then you can keep going.\"")
    w.say(f"\"{gear.sound}!\" {gear.label} went as it settled into place.")
    w.say(f"{hero.id} used it and began {ch.gerund} more slowly and safely.")
    w.para()
    if params.challenge == "boat":
        w.say(f"The little boat rocked, then steadied.")
    elif params.challenge == "bridge":
        w.say(f"The bridge still said \"creak-creak,\" but it did not scare {hero.id} anymore.")
    elif params.challenge == "cave":
        w.say(f"The cave answered with a soft \"drip-drip,\" and the lantern made a warm gold circle.")
    else:
        w.say(f"The rope went \"whoosh,\" but the gloves kept {hero.id}'s hands snug.")
    w.say(f"At the end, {hero.id} reached the prize, and {hero.id}'s {params.parent} laughed with relief.")
    w.say(f"\"Hooray!\" went the air, and the happy ending sparkled like a bright little star.")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    ch = f["challenge"]
    return [
        f'Write a short adventure story for a young child that includes the sound effect "{ch.sound}".',
        f"Tell a happy ending story where {p.name} must {ch.verb} and learns to be safe with help.",
        f'Write a simple adventure about a child at {world.setting.place} that ends with "Hooray!"',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    ch = f["challenge"]
    return [
        QAItem(
            question=f"Who is the adventure about?",
            answer=f"It is about {p.name}, a little {p.trait} {p.hero_type} who wanted an adventure at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {p.name} want to do?",
            answer=f"{p.name} wanted to {ch.verb}. That was tricky because {ch.danger}.",
        ),
        QAItem(
            question=f"How did the helper keep the adventure safe?",
            answer=f"{p.parent.capitalize()} brought {f['gear'].label} so the danger could slow down and {p.name} could keep going safely.",
        ),
        QAItem(
            question=f"What sound was heard when the problem started?",
            answer=f"The story says \"{ch.sound}!\" when the danger woke up.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with {p.name} reaching the prize and everyone cheering, \"Hooray!\"",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does retard mean in a machine or story tool?",
            answer="It means to slow something down so it moves more carefully.",
        ),
        QAItem(
            question="What is a brake for?",
            answer="A brake is used to slow down or stop motion so something stays safe.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help the reader imagine the action, like creaks, splashes, and whooshes.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} kind={e.kind}")
    return "\n".join(lines)


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_story_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP and Python agree on {len(python_set)} combos.")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(python_set - clingo_set))
    print("only asp:", sorted(clingo_set - python_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


CURATED = [
    StoryParams(place="canyon_trail", challenge="bridge", prize="map", name="Mina", hero_type="girl", parent="mother", trait="brave"),
    StoryParams(place="harbor_docks", challenge="boat", prize="lantern", name="Theo", hero_type="boy", parent="father", trait="cheerful"),
    StoryParams(place="forest_pass", challenge="rope", prize="crown", name="Lila", hero_type="girl", parent="guardian", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid adventure triples:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
