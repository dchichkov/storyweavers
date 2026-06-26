#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teethe_variable_jumble_bravery_repetition_tall_tale.py
====================================================================================================

A tiny, self-contained story world with a tall-tale feel.

Seed-imagined tale:
- A small child named Pip is teething and very brave.
- The day keeps changing in a variable jumble: first the train whistle is loud,
  then the kite wind is wild, then the chair squeaks, then the moon looks like a
  silver spoon.
- Pip repeats a courage trick each time the world gets jumbled: breathe, bite
  the teether, and grin.
- The repetition steadies Pip, and bravery turns the jumble into a parade.

This script models that premise as a stateful simulation:
- physical meters: ache, chaos, relief, steadiness
- emotional memes: bravery, worry, delight, repetition
- the story changes because the world state changes, not because of template swaps
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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    variable_weather: list[str]
    affords: set[str] = field(default_factory=set)


@dataclass
class Teether:
    id: str
    label: str
    phrase: str
    calms: float = 1.0


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_type: str
    teether: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.weather_cycle: list[str] = []
        self.weather_index = 0
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
        clone = World(self.place)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.weather_cycle = list(self.weather_cycle)
        clone.weather_index = self.weather_index
        clone.fired = set(self.fired)
        return clone

    def next_weather(self) -> str:
        w = self.weather_cycle[self.weather_index % len(self.weather_cycle)]
        self.weather_index += 1
        return w


def _speak_entity(entity: Entity) -> str:
    return entity.label or entity.id


def _clamp(x: float) -> float:
    return max(0.0, min(10.0, x))


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("bravery", hero.id, world.weather_index)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["steadiness"] = _clamp(hero.meters.get("steadiness", 0.0) + 1.0)
        out.append(f"{hero.id stood straighter than a fencepost in a thunderwind.")
    return out


def _r_teething(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("ache", 0.0) < THRESHOLD:
            continue
        sig = ("teethe", hero.id, world.weather_index)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] = _clamp(hero.memes.get("worry", 0.0) + 1.0)
        hero.meters["jumble"] = _clamp(hero.meters.get("jumble", 0.0) + 0.5)
        out.append(f"{hero.id}'s tooth-ache made the whole morning feel a little wobbly.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("repetition", 0.0) < THRESHOLD:
            continue
        sig = ("repeat", hero.id, world.weather_index)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["steadiness"] = _clamp(hero.meters.get("steadiness", 0.0) + 0.5)
        hero.meters["chaos"] = _clamp(hero.meters.get("chaos", 0.0) - 0.5)
        out.append(f"Again and again, the same calm trick made the world less jumpy.")
    return out


RULES = [_r_teething, _r_bravery, _r_repetition]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            res = rule(world)
            if res:
                changed = True
                lines.extend(res)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


PLACES = {
    "porch": Place("the porch", ["sunny", "windy", "rainy"], affords={"watch"}),
    "kitchen": Place("the kitchen", ["quiet", "clattery", "quiet"], affords={"bake"}),
    "yard": Place("the yard", ["breezy", "thundery", "moonlit"], affords={"march"}),
}

TEETHERS = {
    "moonring": Teether("moonring", "moon-shaped teether", "a moon-shaped teether"),
    "starberry": Teether("starberry", "starry teether", "a starry teether"),
    "gumleaf": Teether("gumleaf", "soft leaf teether", "a soft leaf teether"),
}

GIRL_NAMES = ["Pip", "Mina", "Luna", "Ivy", "Nora"]
BOY_NAMES = ["Bo", "Finn", "Toby", "Milo", "Jude"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["brave", "spry", "cheerful", "determined"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TEETHERS]


@dataclass
class WorldState:
    world: World
    hero: Entity
    helper: Entity
    teether: Entity


def build_world(params: StoryParams) -> WorldState:
    place = PLACES[params.place]
    world = World(place)
    world.weather_cycle = list(place.variable_weather)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"ache": 0.0, "jumble": 0.0, "steadiness": 0.0, "chaos": 0.0},
        memes={"bravery": 1.0, "worry": 0.0, "repetition": 0.0, "delight": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label=f"the {params.helper_type}",
        meters={"patience": 2.0},
        memes={"care": 2.0},
    ))
    teether_cfg = TEETHERS[params.teether]
    teether = world.add(Entity(
        id=teether_cfg.id,
        type="thing",
        label=teether_cfg.label,
        phrase=teether_cfg.phrase,
        owner=hero.id,
    ))

    return WorldState(world=world, hero=hero, helper=helper, teether=teether)


def scene(world: World, hero: Entity, helper: Entity, teether: Entity) -> None:
    weather1 = world.next_weather()
    hero.meters["ache"] += 1.0
    hero.meters["chaos"] += 0.5
    hero.memes["repetition"] += 1.0
    world.say(
        f"{hero.id} was a little {hero.type} with a tooth that was trying to teethe "
        f"like a fiddle string learning to sing."
    )
    world.say(
        f"On the {world.place.name}, where the weather could turn variable as a carousel, "
        f"{hero.id} held {hero.pronoun('possessive')} {teether.label} and watched the {weather1} sky."
    )

    world.para()
    weather2 = world.next_weather()
    hero.meters["jumble"] += 1.0
    hero.memes["bravery"] += 1.0
    world.say(
        f"Then the day jumble-jangled: the {weather2} wind shook the laundry, and the fence "
        f"seemed to tiptoe in place."
    )
    world.say(
        f"But {hero.id} was brave enough to grin and do the same calm thing twice: bite the teether, breathe, and nod."
    )
    propagate(world)

    world.para()
    weather3 = world.next_weather()
    hero.meters["chaos"] += 1.0
    hero.memes["repetition"] += 1.0
    world.say(
        f"The third turn brought {weather3} shadows and a great tall-tale rattle from the gate."
    )
    world.say(
        f"Again and again, {hero.id} repeated the brave little routine, and the routine was so steady it could have tamed a brass band."
    )
    propagate(world)

    world.para()
    hero.memes["delight"] += 1.0
    hero.meters["steadiness"] += 1.0
    world.say(
        f"At last the ache settled down, the jumble loosened its grip, and {hero.id} laughed with a mouth no longer grumpy."
    )
    world.say(
        f"{helper.label} smiled beside {hero.pronoun('object')}, and the {teether.label} gleamed like a tiny silver promise."
    )

    world.facts.update(hero=hero, helper=helper, teether=teether, place=world.place)


def tell(params: StoryParams) -> World:
    state = build_world(params)
    scene(state.world, state.hero, state.helper, state.teether)
    return state.world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    teether = f["teether"]
    return [
        f'Write a tall-tale style story about {hero.id} teething with {teether.label} during a variable day.',
        f"Tell a short brave story where {hero.id} repeats a calm trick until the jumble becomes gentle, with {helper.label} nearby.",
        'Write a child-friendly story that includes the words "teethe", "variable", and "jumble".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    teether = f["teether"]
    return [
        QAItem(
            question=f"Who is the story mostly about?",
            answer=f"The story is mostly about {hero.id}, a little {hero.type} who is brave while teething.",
        ),
        QAItem(
            question=f"What helped {hero.id} stay calm when the day felt jumbled?",
            answer=f"{hero.id} stayed calm by repeating a brave little routine and using {teether.label}.",
        ),
        QAItem(
            question=f"Who smiled at the end of the story?",
            answer=f"The {helper.type} smiled at the end because {hero.id} grew steadier and the jumble settled down.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teethe mean?",
            answer="To teethe means a baby's teeth are pushing through the gums, which can make the mouth sore.",
        ),
        QAItem(
            question="What does variable mean?",
            answer="Variable means something changes instead of staying exactly the same.",
        ),
        QAItem(
            question="What is a jumble?",
            answer="A jumble is a mix of things that are all tangled up or out of order.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the courage to keep going even when something feels hard or scary.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition is doing or saying something again and again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for w in PLACES[pid].variable_weather:
            lines.append(asp.fact("weather", pid, w))
    for tid in TEETHERS:
        lines.append(asp.fact("teether", tid))
    lines.append(asp.fact("feature", "Bravery"))
    lines.append(asp.fact("feature", "Repetition"))
    lines.append(asp.fact("seedword", "teethe"))
    lines.append(asp.fact("seedword", "variable"))
    lines.append(asp.fact("seedword", "jumble"))
    return "\n".join(lines)


ASP_RULES = r"""
feature_story(P,T) :- place(P), teether(T).
challenging(P) :- place(P), weather(P,_).
resolved(P) :- feature_story(P,T), feature("Bravery"), feature("Repetition"), teether(T).
#show feature_story/2.
#show challenging/1.
#show resolved/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show feature_story/2."))
    have = set(asp.atoms(model, "feature_story"))
    want = {(p, t) for p in PLACES for t in TEETHERS}
    if have != want:
        print("MISMATCH between ASP and Python registries")
        return 1
    print(f"OK: ASP matches Python registry ({len(have)} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale teething story world with variable jumble and brave repetition.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=sorted(set(HELPERS)))
    ap.add_argument("--teether", choices=sorted(TEETHERS))
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    teether = args.teether or rng.choice(list(TEETHERS))
    return StoryParams(place=place, hero_name=name, hero_type=gender, helper_type=helper, teether=teether)


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
    StoryParams(place="porch", hero_name="Pip", hero_type="boy", helper_type="mother", teether="moonring"),
    StoryParams(place="yard", hero_name="Mina", hero_type="girl", helper_type="father", teether="starberry"),
    StoryParams(place="kitchen", hero_name="Toby", hero_type="boy", helper_type="grandmother", teether="gumleaf"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show feature_story/2. #show challenging/1. #show resolved/1."))
        print("feature_story:", sorted(set(asp.atoms(model, "feature_story"))))
        print("challenging:", sorted(set(asp.atoms(model, "challenging"))))
        print("resolved:", sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.hero_name} at {p.place} with {p.teether}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
