#!/usr/bin/env python3
"""
storyworlds/worlds/chord_suspense_dialogue_foreshadowing_superhero_story.py
============================================================================

A small superhero storyworld built around a tense clue: a chord heard in the
city at the wrong moment. The story keeps the classic shape of setup, suspense,
dialogue, foreshadowing, a turn, and a rescue-style ending.

The seed idea:
---
A young hero hears a strange chord from the skybridge while the city sleeps.
Their mentor warns that the sound is not music at all; it is a signal. The chord
foreshadows a trap at the power station, and the hero must race there before the
lights go out. A careful plan, a short dialogue, and a brave choice save the
night.

This world models:
- a hero and mentor with courage, trust, and worry
- a city with a power station and a skybridge
- a villain who uses a chord signal to start trouble
- suspense from a countdown to blackout
- foreshadowing from a repeated chord clue
- dialogue that moves the story forward
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    clue_place: str
    danger_place: str
    night: bool = True


@dataclass
class Signal:
    chord: str
    phrase: str
    foreshadow: str
    danger: str
    loud: bool = True


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: str
    protects: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    mentor_name: str
    villain_name: str
    setting: str
    signal: str
    gear: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


SETTINGS = {
    "skybridge": Setting(place="the skybridge", clue_place="the skybridge", danger_place="the power station"),
    "rooftop": Setting(place="the rooftop garden", clue_place="the rooftop", danger_place="the power station"),
    "harbor": Setting(place="the harbor pier", clue_place="the harbor", danger_place="the power station"),
}

SIGNALS = {
    "minor_chord": Signal(
        chord="a soft chord",
        phrase="a soft chord drifted through the night air",
        foreshadow="something important was about to happen",
        danger="the city lights would flicker out",
        loud=False,
    ),
    "minor_sting": Signal(
        chord="a minor chord",
        phrase="a minor chord rang from the shadows",
        foreshadow="someone was setting a trap",
        danger="the power station would be targeted",
        loud=True,
    ),
    "triple_chord": Signal(
        chord="a sharp three-note chord",
        phrase="a sharp three-note chord snapped through the dark",
        foreshadow="the villain was close",
        danger="the alarm grid would fail",
        loud=True,
    ),
}

GEAR = {
    "cape": Gear(
        id="cape",
        label="a blue cape",
        phrase="a blue cape",
        helps="whip through the wind and land fast",
        protects="bravery",
    ),
    "gloves": Gear(
        id="gloves",
        label="signal gloves",
        phrase="signal gloves",
        helps="climb the metal beams without slipping",
        protects="steady hands",
    ),
    "visor": Gear(
        id="visor",
        label="a light visor",
        phrase="a light visor",
        helps="see the blinking wires in the dark",
        protects="clear sight",
    ),
}

VILLAINS = ["Dr. Static", "Lady Echo", "Captain Pulse"]
HERO_TYPES = ["girl", "boy"]
NAMES = ["Nova", "Milo", "Rae", "Ivy", "Leo", "Zane", "Mina", "Tess"]
MOTTOES = ["brave", "quick", "kind", "sharp-eyed", "steady"]


class StoryWorld:
    pass


def foreshadow_line(signal: Signal, setting: Setting) -> str:
    return (
        f"At {setting.place}, {signal.phrase}; it was a clue that {signal.foreshadow}."
    )


def build_scene(world: World, hero: Entity, mentor: Entity, villain: Entity, signal: Signal, gear: Gear) -> None:
    hero_story = hero.traits[0] if hero.traits else "brave"
    world.say(
        f"{hero.id} was a {hero_story} young hero who liked to listen for trouble before it arrived."
    )
    world.say(
        f"{mentor.id} was {hero.pronoun('possessive')} mentor, and {hero.id} trusted {mentor.pronoun('object')} when the city felt strange."
    )
    world.say(
        f"That night, as the wind brushed {world.setting.place}, {signal.phrase}."
    )
    world.say(
        f"{hero.id} stopped and whispered, 'Did you hear that?'"
    )
    world.say(
        f"{mentor.id} listened, then said, 'Yes. That chord is not music. It is a warning.'"
    )
    world.say(
        f"The sound foreshadowed that {signal.danger}."
    )

    world.para()
    world.say(
        f"{hero.id} grabbed {gear.label} and looked toward {world.setting.danger_place}."
    )
    world.say(
        f"'If the warning is real, we have to move now,' {hero.id} said."
    )
    world.say(
        f"{mentor.id} nodded. 'Stay low, watch the wires, and do not let {villain.id} hear you coming.'"
    )
    _add_meme(hero, "suspense", 1)
    _add_meme(hero, "focus", 1)
    _add_meme(mentor, "worry", 1)
    _add_meter(hero, "distance", 1)

    world.para()
    world.say(
        f"Near {world.setting.danger_place}, they saw {villain.id} reach for the control box."
    )
    world.say(
        f"{villain.id} smiled and said, 'Too late. One chord, and the whole block goes dark.'"
    )
    world.say(
        f"{hero.id} answered, 'Not if I can help it.'"
    )
    world.say(
        f"Then {hero.id} used {gear.helps} while {mentor.id} distracted {villain.id} with a flash of light."
    )
    _add_meter(hero, "skill", 1)
    _add_meter(villain, "pressure", 1)
    _add_meme(villain, "frustration", 1)

    world.para()
    world.say(
        f"The wires stopped sparking, and the control box clicked shut before the blackout could spread."
    )
    world.say(
        f"{villain.id} backed away as the siren rose, and the city stayed bright."
    )
    world.say(
        f"{mentor.id} smiled. 'You heard the clue and saved the night.'"
    )
    world.say(
        f"{hero.id} looked up at the glowing windows and said, 'That chord was scary, but it led us exactly where we needed to go.'"
    )
    _add_meme(hero, "pride", 1)
    _add_meme(hero, "relief", 1)
    _add_meme(mentor, "pride", 1)
    _add_meter(world.get("city"), "saved", 1)
    world.facts.update(
        hero=hero,
        mentor=mentor,
        villain=villain,
        signal=signal,
        gear=gear,
        setting=world.setting,
    )


def _story_intro(hero: Entity, mentor: Entity, signal: Signal, setting: Setting) -> list[str]:
    return [
        f"Write a short superhero story for a child about {hero.id} and {mentor.id} at {setting.place}.",
        f"Tell a suspenseful story where a mysterious chord warns that trouble is coming, and the hero must act fast.",
        f"Write a scene with dialogue and foreshadowing where {signal.chord} becomes the clue that saves the city.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mentor: Entity = f["mentor"]  # type: ignore[assignment]
    villain: Entity = f["villain"]  # type: ignore[assignment]
    signal: Signal = f["signal"]  # type: ignore[assignment]
    gear: Gear = f["gear"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who heard the chord first at {setting.place}?",
            answer=f"{hero.id} heard it first and stopped to listen, because {hero.id} knew the sound might be a clue.",
        ),
        QAItem(
            question="Why did the chord matter in the story?",
            answer=f"It mattered because {signal.foreshadow} and the chord warned that {signal.danger}.",
        ),
        QAItem(
            question=f"What did {mentor.id} tell {hero.id} about the chord?",
            answer=f"{mentor.id} said it was not music but a warning, so {hero.id} should pay attention and move fast.",
        ),
        QAItem(
            question=f"What gear helped {hero.id} stop the danger?",
            answer=f"{gear.label} helped {hero.id} {gear.helps}, which made it easier to protect the city.",
        ),
        QAItem(
            question=f"What happened to {villain.id} at the end?",
            answer=f"{villain.id} failed to break the power station, backed away, and got caught in the hero's plan.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chord in music?",
            answer="A chord is several notes played together at the same time to make one sound.",
        ),
        QAItem(
            question="Why does foreshadowing help a story?",
            answer="Foreshadowing gives an early clue about what may happen later, so the reader can feel suspense and notice important details.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next and worrying about whether the characters can solve the problem.",
        ),
        QAItem(
            question="Why do superheroes often work with mentors?",
            answer="Mentors help superheroes learn, stay calm, and make smart choices when danger gets serious.",
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
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Nova", "girl", "Mentor Vale", "Dr. Static", "skybridge", "minor_chord", "visor"),
    StoryParams("Milo", "boy", "Captain Reed", "Lady Echo", "rooftop", "minor_sting", "gloves"),
    StoryParams("Ivy", "girl", "Aunt Spark", "Captain Pulse", "harbor", "triple_chord", "cape"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    signal = args.signal or rng.choice(list(SIGNALS))
    gear = args.gear or rng.choice(list(GEAR))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(NAMES)
    mentor_name = args.mentor_name or f"Mentor {rng.choice(['Vale', 'Aster', 'Quill', 'Nova'])}"
    villain_name = args.villain_name or rng.choice(VILLAINS)

    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        mentor_name=mentor_name,
        villain_name=villain_name,
        setting=setting,
        signal=signal,
        gear=gear,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    signal = SIGNALS[params.signal]
    gear = GEAR[params.gear]

    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["brave", "sharp-eyed"],
    ))
    mentor = world.add(Entity(
        id=params.mentor_name,
        kind="character",
        type="adult",
        traits=["calm", "wise"],
    ))
    villain = world.add(Entity(
        id=params.villain_name,
        kind="character",
        type="adult",
        traits=["scheming", "quiet"],
    ))
    city = world.add(Entity(
        id="city",
        kind="place",
        type="city",
        label="the city",
        traits=["bright"],
    ))

    build_scene(world, hero, mentor, villain, signal, gear)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=_story_intro(hero, mentor, signal, setting),
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
    ap = argparse.ArgumentParser(description="Superhero storyworld with suspense, dialogue, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--hero-name")
    ap.add_argument("--mentor-name")
    ap.add_argument("--villain-name")
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


ASP_RULES = r"""
hero(X) :- hero_name(X).
mentor(X) :- mentor_name(X).
villain(X) :- villain_name(X).
signal(S) :- signal_name(S).
gear(G) :- gear_name(G).

chord_signal(S) :- signal_name(S).
foreshadowing(S) :- signal_foreshadows(S).
suspense(S) :- signal_causes_suspense(S).

needs_attention(S) :- chord_signal(S), foreshadowing(S).
valid_story(H, M, V, S, G) :-
    hero_name(H), mentor_name(M), villain_name(V),
    signal_name(S), gear_name(G).
#show valid_story/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in SETTINGS:
        lines.append(asp.fact("setting_name", name))
    for name in SIGNALS:
        lines.append(asp.fact("signal_name", name))
    for name, sig in SIGNALS.items():
        lines.append(asp.fact("signal_foreshadows", name))
        if sig.loud:
            lines.append(asp.fact("signal_causes_suspense", name))
    for name in GEAR:
        lines.append(asp.fact("gear_name", name))
    for n in VILLAINS:
        lines.append(asp.fact("villain_name", n))
    for n in NAMES:
        lines.append(asp.fact("hero_name", n))
    lines.append(asp.fact("mentor_name", "Mentor Vale"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    expected = []
    for hero in NAMES:
        expected.append(("hero",))
    if atoms:
        print(f"OK: ASP produced {len(atoms)} story skeleton atom(s).")
        return 0
    print("MISMATCH: no ASP atoms returned.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.signal} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
