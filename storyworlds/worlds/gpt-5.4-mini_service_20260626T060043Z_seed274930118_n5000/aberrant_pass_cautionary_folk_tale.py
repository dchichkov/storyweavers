#!/usr/bin/env python3
"""
A cautionary folk-tale world about a mountain pass, a lantern, and an
aberrant warning that should have been heeded.

The seed tale imagined for this world:
---
In a small hill village, there was an old pass through the mountains. Every
winter, travelers used it to reach the market on the far side. A wise elder told
the children that the pass was safe only by day and only when the wind was calm.

One evening, a young traveler named Oren met a strange, aberrant stranger who
smiled too wide and said the pass was quick even in the dark. Oren wanted to
believe him, because the market was waiting and the road around the mountains
was long.

But the elder's daughter, Mara, noticed the stranger never left footprints in
the snow. She warned Oren to wait for morning and to take a lantern. Oren first
laughed, then saw the lantern's light reveal hidden ice on the pass. He turned
back, and by morning the village had a safer story to tell.

This script turns that premise into a small stateful world:
- the pass can be safe or dangerous,
- weather and time affect whether a crossing is wise,
- an aberrant stranger can tempt the traveler,
- a warning can be accepted or refused,
- the ending proves what changed in the world.
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


SAFE_LIGHT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "daughter"}
        male = {"boy", "man", "father", "son", "traveler", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    safe_by_day: bool
    sheltered: bool = False


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "clear"
        self.time: str = "day"
        self.pass_state: str = "safe"

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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.time = self.time
        clone.pass_state = self.pass_state
        return clone


def folk_opening(hero: Entity, elder: Entity, place: Place) -> str:
    return f"Once in a little village, {hero.id} and the old {elder.type} watched the {place.label} like a narrow door in the hills."


def pass_is_risky(world: World) -> bool:
    return world.time != "day" or world.weather in {"wind", "snow"}


def predict_crossing(world: World, hero: Entity, lantern: Entity) -> dict:
    sim = world.copy()
    simulate_crossing(sim, hero, lantern, narrate=False)
    return {
        "safe": sim.pass_state == "safe",
        "light": sim.get(lantern.id).meters.get("light", 0.0),
    }


def simulate_crossing(world: World, hero: Entity, lantern: Entity, narrate: bool = True) -> None:
    if lantern.worn_by != hero.id:
        raise StoryError("The lantern must be carried by the traveler.")
    if world.time == "night":
        lantern.meters["light"] = 1.0
    if pass_is_risky(world):
        if lantern.meters.get("light", 0.0) >= SAFE_LIGHT:
            world.pass_state = "safe"
        else:
            world.pass_state = "slippery"
    else:
        world.pass_state = "safe"
    if narrate:
        if world.pass_state == "safe":
            world.say(f"{hero.id} crossed the pass with steady steps.")
        else:
            world.say(f"The stones of the pass gave a sly little slip under {hero.pronoun('possessive')} boots.")


def warn_about_pass(world: World, elder: Entity, hero: Entity, stranger: Entity, lantern: Entity) -> None:
    if not pass_is_risky(world):
        return
    world.facts["aberrant"] = True
    world.facts["caution"] = True
    world.say(
        f'"Do not trust the {world.place.label} after dusk," said the old {elder.type}. '
        f'"Take a lantern, and mind any aberrant voice that praises the pass too much."'
    )


def tempt(world: World, stranger: Entity, hero: Entity) -> None:
    stranger.memes["deceit"] = 1.0
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1.0
    world.say(
        f"A strange, aberrant stranger smiled too wide and said the pass was quick even in the dark."
    )
    world.say(f"{hero.id} felt the pull of a shorter road and looked once toward the mountains.")


def accept_caution(world: World, hero: Entity, elder: Entity, lantern: Entity) -> None:
    hero.memes["prudence"] = hero.memes.get("prudence", 0.0) + 1.0
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} eyes, took the lantern, and chose the safer hour."
    )
    world.say(
        f"By morning, the pass was bright and honest, and the village kept its feet on firm ground."
    )


def reject_caution(world: World, hero: Entity, lantern: Entity) -> None:
    hero.memes["rashness"] = hero.memes.get("rashness", 0.0) + 1.0
    world.say(f"{hero.id} ignored the warning and went on at once.")
    world.say(
        f"But the hidden ice shone in the lantern-light, and {hero.pronoun('subject')} had to turn back in shame."
    )


def tell(place: Place, name: str = "Oren", elder_name: str = "Mara", stranger_name: str = "The Stranger") -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="traveler", label=name))
    elder = world.add(Entity(id=elder_name, kind="character", type="elder", label=elder_name))
    stranger = world.add(Entity(id=stranger_name, kind="character", type="traveler", label=stranger_name))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase="a brass lantern with a small steady flame",
        owner=hero.id,
        worn_by=hero.id,
    ))
    lantern.meters["light"] = 0.0

    world.say(folk_opening(hero, elder, place))
    world.say(f"{hero.id} loved the market on the far side, but the road around the hills was long.")
    world.say(f"{elder.id} kept a lantern by the door and spoke kindly of careful things.")

    world.para()
    world.time = "night"
    world.weather = "wind"
    world.say(f"One windy night, {hero.id} stood at the mouth of the {place.label} and thought of the waiting market.")
    warn_about_pass(world, elder, hero, stranger, lantern)
    tempt(world, stranger, hero)

    world.para()
    if pass_is_risky(world):
        if hero.memes.get("doubt", 0.0) > 0.5:
            lantern.meters["light"] = 1.0
            accept_caution(world, hero, elder, lantern)
            simulate_crossing(world, hero, lantern, narrate=True)
        else:
            simulate_crossing(world, hero, lantern, narrate=True)
            reject_caution(world, hero, lantern)
    else:
        lantern.meters["light"] = 1.0
        simulate_crossing(world, hero, lantern, narrate=True)

    world.facts.update(
        hero=hero,
        elder=elder,
        stranger=stranger,
        lantern=lantern,
        place=place,
        risky=pass_is_risky(world),
        safe=world.pass_state == "safe",
    )
    return world


SETTINGS = {
    "mountain_pass": Place(id="mountain_pass", label="mountain pass", safe_by_day=True),
    "river_pass": Place(id="river_pass", label="river crossing", safe_by_day=True, sheltered=False),
    "forest_pass": Place(id="forest_pass", label="forest pass", safe_by_day=True, sheltered=True),
}

NAMES = ["Oren", "Milo", "Anya", "Lena", "Jory", "Pia", "Evan", "Sela"]
ELDER_NAMES = ["Mara", "Bram", "Ilya", "Soren"]
STRAINGER_NAMES = ["The Stranger", "The Wanderer", "The Reed-Man"]

CURATED = [
    ("mountain_pass", "Oren", "Mara", "The Stranger"),
    ("forest_pass", "Anya", "Bram", "The Wanderer"),
    ("river_pass", "Milo", "Ilya", "The Reed-Man"),
]


@dataclass
class StoryParams:
    place: str
    name: str
    elder: str
    stranger: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary folk tale about an aberrant pass and a lantern.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--stranger")
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    stranger = args.stranger or rng.choice(STRAINGER_NAMES)
    return StoryParams(place=place, name=name, elder=elder, stranger=stranger)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a cautionary folk tale about an aberrant stranger and a mountain pass.',
        f"Tell a short story where {f['hero'].id} is warned about the {f['place'].label} and carries a lantern.",
        f"Write a child-friendly tale in which a traveler chooses caution over a quick pass through the hills.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, stranger, lantern, place = f["hero"], f["elder"], f["stranger"], f["lantern"], f["place"]
    return [
        QAItem(
            question=f"Who was warned about the {place.label}?",
            answer=f"{hero.id} was warned by {elder.id} to be careful at the {place.label}.",
        ),
        QAItem(
            question="What was strange about the stranger?",
            answer="The stranger was aberrant: he smiled too wide and praised the pass even though the warning said to wait.",
        ),
        QAItem(
            question=f"What did {hero.id} take in the end?",
            answer=f"{hero.id} took the lantern and used it to choose the safer way.",
        ),
        QAItem(
            question=f"Why was the tale cautionary?",
            answer=f"It is cautionary because {hero.id} learned that a quick path through the pass can hide danger, especially at night and in wind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mountain pass?",
            answer="A mountain pass is a path through high mountains that people use to travel from one side to the other.",
        ),
        QAItem(
            question="Why do travelers carry lanterns at night?",
            answer="Travelers carry lanterns at night so they can see the ground, avoid danger, and keep their way steady.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and not rushing into danger.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"time={world.time} weather={world.weather} pass_state={world.pass_state}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
unsafe_pass(P) :- place(P), risky_time, place_is_pass(P).
unsafe_pass(P) :- place(P), windy, place_is_pass(P).
safe_pass(P) :- place(P), not unsafe_pass(P).

cautionary_story(P) :- place(P), safe_pass(P).
aberrant_warning(X) :- stranger(X), odd_voice(X).
valid_story(P) :- cautionary_story(P), aberrant_warning(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if "pass" in place.label:
            lines.append(asp.fact("place_is_pass", pid))
    lines.append(asp.fact("risky_time"))
    lines.append(asp.fact("windy"))
    for s in ["stranger_a", "stranger_b"]:
        lines.append(asp.fact("stranger", s))
        lines.append(asp.fact("odd_voice", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {("mountain_pass",), ("river_pass",), ("forest_pass",)}
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: ASP parity holds for {len(cl)} places.")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def explain_choice(place: Place) -> str:
    return f"(No story: the chosen place must be a pass-like crossing, not {place.label}.)"


def valid_places() -> list[str]:
    return list(SETTINGS)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.elder, params.stranger)
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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, name, elder, stranger in CURATED:
            samples.append(generate(StoryParams(place=place, name=name, elder=elder, stranger=stranger)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
