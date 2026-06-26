#!/usr/bin/env python3
"""
A small storyworld about a canyon adventure where bravery and a misunderstanding
shape the moral lesson.

The premise:
- A child hears a clatter echo from a canyon trail.
- The child thinks someone is in trouble.
- A brave choice reveals the sound had a harmless cause.
- The story ends with a clear moral value: courage paired with kindness.

This script keeps the world tiny but state-driven:
- meters track physical conditions like distance, noise, height, and risk
- memes track emotional conditions like fear, bravery, misunderstanding, relief
- the narrative changes as the world changes
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    adjective: str
    echo: str
    danger: str
    clues: str


@dataclass
class Challenge:
    id: str
    sound: str
    cause: str
    risky: str
    brave_action: str
    turn: str
    moral: str


@dataclass
class StoryParams:
    place: str
    challenge: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, challenge: Challenge) -> None:
        self.place = place
        self.challenge = challenge
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place, self.challenge)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


PLACES = {
    "canyon": Place(
        name="the canyon",
        adjective="wide and sunlit",
        echo="the rocks made every sound bounce back",
        danger="the path felt high and steep",
        clues="a little nest of pebbles near a loose tin cup",
    ),
    "trail": Place(
        name="the mountain trail",
        adjective="rocky and bright",
        echo="each step clattered against the stones",
        danger="the path curled close to the edge",
        clues="a dropped snack bag snagged on a bush",
    ),
}

CHALLENGES = {
    "clatter": Challenge(
        id="clatter",
        sound="a sharp clatter",
        cause="a tin cup rolling among the rocks",
        risky="someone might have fallen",
        brave_action="go closer and look carefully",
        turn="the sound came from an ordinary cup, not a person in danger",
        moral="Being brave means checking on others, but also noticing the truth before you panic.",
    ),
    "echo": Challenge(
        id="echo",
        sound="a strange echo",
        cause="a bird knocking pebbles from a ledge",
        risky="it sounded like a call for help",
        brave_action="climb a little higher to see",
        turn="the echo came from a bird's small feet and not from an accident",
        moral="A kind heart should listen closely before it decides what is wrong.",
    ),
}


def reasonableness_gate(place: Place, challenge: Challenge) -> None:
    if challenge.id == "clatter" and place.name != "the canyon":
        raise StoryError("The clatter story needs the canyon setting so the echo can shape the misunderstanding.")
    if challenge.id == "echo" and place.name != "the canyon":
        raise StoryError("The echo story needs the canyon setting so the height and sound make sense.")


def narrate_setup(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"{hero.id} was a curious {hero.type} who loved adventure at {world.place.name}. "
        f"{world.place.name.capitalize()} was {world.place.adjective}, and {world.place.echo}."
    )
    world.say(
        f"{hero.id} went there with {companion.id}, {hero.pronoun('possessive')} {companion.type}, "
        f"because both of them liked exploring safe paths."
    )


def narrate_misunderstanding(world: World, hero: Entity, companion: Entity) -> None:
    ch = world.challenge
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.memes["misunderstanding"] = hero.memes.get("misunderstanding", 0.0) + 1
    world.say(
        f"Then came {ch.sound}. It bounced through {world.place.name}, and {hero.id} thought {ch.risky}."
    )
    world.say(
        f"{hero.id} froze for a moment. {hero.pronoun().capitalize()} felt scared, because the echo made the trail sound bigger and stranger than it was."
    )


def narrate_bravery(world: World, hero: Entity, companion: Entity) -> None:
    ch = world.challenge
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 0.5)
    world.say(
        f"Still, {hero.id} took a brave breath and chose to {ch.brave_action}."
    )
    world.say(
        f"{hero.id} stepped slowly toward the sound, keeping one hand on the rock wall and listening for clues."
    )


def narrate_turn(world: World, hero: Entity, companion: Entity) -> None:
    ch = world.challenge
    hero.memes["misunderstanding"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"At last, {hero.id} found the truth: {ch.turn}."
    )
    world.say(
        f"The canyon was only noisy, not cruel, and the strange clatter turned into a simple little thing."
    )


def narrate_resolution(world: World, hero: Entity, companion: Entity) -> None:
    ch = world.challenge
    hero.memes["moral_value"] = hero.memes.get("moral_value", 0.0) + 1
    world.say(
        f"{hero.id} smiled at {companion.id} and said that bravery is not the same as guessing."
    )
    world.say(
        f"Together they walked home more carefully, remembering the lesson: {ch.moral}"
    )


def tell(place: Place, challenge: Challenge, hero_name: str, hero_type: str,
         companion_name: str, companion_type: str) -> World:
    world = World(place, challenge)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_type, meters={}, memes={}))

    narrate_setup(world, hero, companion)
    world.para()
    narrate_misunderstanding(world, hero, companion)
    narrate_bravery(world, hero, companion)
    world.para()
    narrate_turn(world, hero, companion)
    narrate_resolution(world, hero, companion)

    world.facts.update(
        hero=hero,
        companion=companion,
        place=place,
        challenge=challenge,
    )
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    place = f["place"]
    return [
        f'Write a short adventure story for a small child set at {place.name} where {hero.id} hears {challenge.sound}.',
        f'Tell a gentle canyon adventure story about a misunderstanding, bravery, and a moral value.',
        f'Write a story where a child thinks {challenge.risky}, then finds out what really made the noise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    ch = f["challenge"]
    place = f["place"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel worried at {place.name}?",
            answer=f"{hero.id} felt worried because {ch.sound} echoed through {place.name}, and {hero.pronoun().capitalize()} thought {ch.risky}.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do?",
            answer=f"{hero.id} chose to {ch.brave_action} instead of running away from the sound.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end of the story?",
            answer=f"{hero.id} learned that {ch.moral}",
        ),
        QAItem(
            question=f"Who was with {hero.id} on the adventure?",
            answer=f"{hero.id} was with {companion.id}, who stayed nearby during the misunderstanding.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canyon?",
            answer="A canyon is a deep, narrow valley with steep sides, often made of rock.",
        ),
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces off walls or rocks and comes back to you.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary when it is the right thing to do.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good lesson about how to act kindly, honestly, or wisely.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: clatter, canyon, bravery, misunderstanding, moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--companion-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(PLACES))
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    reasonableness_gate(PLACES[place], CHALLENGES[challenge])

    hero_gender = args.gender or rng.choice(["girl", "boy"])
    comp_gender = args.companion_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(["Mia", "Nia", "Leo", "Finn", "Ava", "Noah"])
    companion_name = args.companion_name or rng.choice(["Jon", "Pip", "Rae", "Tess", "Milo", "June"])
    hero_type = hero_gender
    companion_type = comp_gender
    return StoryParams(
        place=place,
        challenge=challenge,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        CHALLENGES[params.challenge],
        params.hero_name,
        params.hero_type,
        params.companion_name,
        params.companion_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
place(canyon).
challenge(clatter).
challenge(echo).

echoes(canyon).
steep(canyon).

sound(clatter,sound1).
cause(sound1,cup_rolls).

sound(echo,sound2).
cause(sound2,bird_knocks_pebbles).

brave_when(Child, clatter) :- hears(Child, clatter), thinks_danger(Child).
misunderstanding(Child, clatter) :- hears(Child, clatter), thinks_danger(Child).
turns_clear(Child, clatter) :- brave_action(Child), cause(sound1, cup_rolls).

moral_value(clatter, bravery_and_kindness).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if p == "canyon":
            lines.append(asp.fact("echoes", p))
            lines.append(asp.fact("steep", p))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    lines.append(asp.fact("hears", "child", "clatter"))
    lines.append(asp.fact("thinks_danger", "child"))
    lines.append(asp.fact("brave_action", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show misunderstanding/2.\n#show brave_when/2.\n#show turns_clear/2.\n#show moral_value/2."))
    atoms = set((s.name, tuple(a.name if a.type != a.type.Number and a.type != a.type.String else (a.number if a.type == a.type.Number else a.string) for a in s.arguments)) for s in model)
    if atoms:
        print("OK: ASP program solved with shown atoms.")
        return 0
    print("ASP verification failed: no shown atoms.")
    return 1


def asp_valids() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show moral_value/2."))
    return sorted(set(asp.atoms(model, "moral_value")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show moral_value/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        vals = asp_valids()
        print(f"{len(vals)} ASP moral facts:")
        for item in vals:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [StoryParams(place="canyon", challenge="clatter", hero_name="Mia", hero_type="girl", companion_name="Jon", companion_type="boy"),
                  StoryParams(place="canyon", challenge="echo", hero_name="Leo", hero_type="boy", companion_name="Rae", companion_type="girl")]:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
