#!/usr/bin/env python3
"""
storyworlds/worlds/index_artichoke_indoor_gym_sound_effects_repetition.py
=========================================================================

A standalone story world about a spooky-feeling indoor gym, an index card,
and an artichoke. The story leans toward a gentle ghost-story mood with sound
effects and repetition.

Initial story premise:
---
A child visits an indoor gym for a quiet after-school game and finds an index
card tucked into the bleachers. The card keeps pointing to a strange artichoke
near the lost-and-found shelf. At first the gym seems haunted by soft noises:
"tap, tap," "swish," "thump." The child gets nervous, follows the clues, and
discovers that the "ghost" is only a skittering paper fan and a playful coach
making a spooky game of hide-and-seek. The artichoke is the prize for finding
the clue trail.

The story model tracks:
- physical meters: location, hiddenness, noise, distance, held objects
- emotional memes: fear, curiosity, relief, delight

Narrative instruments:
- sound effects are narrated as world state crosses thresholds
- repetition is used as a tension rhythm: the same clue phrase returns, then
  changes meaning when the mystery resolves
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the indoor gym"
    indoors: bool = True
    echo: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _narrate(world: World, key: str, text: str) -> None:
    if key not in world.fired:
        world.fired.add(key)
        world.say(text)


def introduce(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes.get('traits', ['curious'])) if False else ''}".strip()
    )
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'curious')} {hero.type} who liked quiet games."
    )
    world.say(
        f"After school, {hero.id} went to {world.setting.place} with {hero.pronoun('possessive')} {parent.type}."
    )


def sound(world: World, name: str, line: str) -> None:
    _narrate(world, ("sound", name), line)


def clue_repeats(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say('On the bleachers, a little card waited. It said, "Look again."')
    world.say('The card said it once more: "Look again."')
    world.say('Then it said it a third time, softer now: "Look again."')


def seek(world: World, hero: Entity, clue: Entity, prize: Entity) -> None:
    hero.meters["distance_to_clue"] = 1
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} held the index card and looked toward the lost-and-found shelf."
    )
    world.say(
        f"Something round and green sat there, half-hidden in shadow: an artichoke."
    )
    world.say('Tap, tap. Tap, tap. The gym seemed to answer back.')
    world.say(
        f"{hero.id} whispered, 'Look again,' because the card had said it first."
    )
    world.say(
        f"{hero.id} took one careful step, then another. Tap, tap. Tap, tap."
    )
    hero.meters["distance_to_prize"] = 1


def false_ghost(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(
        "A paper fan on the wall suddenly swished open with a soft whoosh."
    )
    world.say(
        f"{hero.id} jumped and almost dropped the card. 'Boo?' {hero.id} whispered."
    )
    world.say("Swish. Thump. Swish. Thump.")


def reveal(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["fear"] = 0
    hero.memes["relief"] += 1
    hero.memes["delight"] += 1
    prize.carried_by = hero.id
    prize.hidden_in = ""
    world.say(
        f"Then {hero.id}'s {parent.type} laughed from behind the mats and called, "
        f"'You found it!'"
    )
    world.say(
        f"The spooky sounds were only the fan, the echo, and a game."
    )
    world.say(
        f"The artichoke was the prize, and the index card was the clue."
    )
    world.say(
        f"{hero.id} laughed too, because the gym was not haunted at all."
    )
    world.say(
        f"It was just a quiet place where someone had made a mystery on purpose."
    )


def ending_image(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} carried the artichoke out of the gym and kept the index card in {hero.pronoun('possessive')} pocket."
    )
    world.say(
        f"Tap, tap, the card seemed to say one last time, but now it sounded friendly."
    )


SETTINGS = {
    "gym": Setting(place="the indoor gym", indoors=True, echo=True),
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Eli", "Ava", "Finn", "Zoe", "Noah"]
TRAITS = ["curious", "quiet", "brave", "careful", "spirited", "thoughtful"]


def tell(setting: Setting, hero_name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=gender,
            memes={"fear": 0.0, "curiosity": 0.0, "relief": 0.0, "delight": 0.0, "trait_word": trait},
        )
    )
    parent_ent = world.add(Entity(id="Parent", kind="character", type=parent))
    clue = world.add(Entity(id="IndexCard", type="index card", label="index card", phrase="a small index card"))
    prize = world.add(Entity(id="Artichoke", type="artichoke", label="artichoke", phrase="a green artichoke"))

    world.say(
        f"At {setting.place}, {hero.id} noticed a small index card near the bleachers."
    )
    clue_repeats(world, hero)
    world.para()
    seek(world, hero, clue, prize)
    false_ghost(world, hero)
    world.para()
    reveal(world, hero, parent_ent, prize)
    ending_image(world, hero, prize)

    world.facts.update(
        hero=hero,
        parent=parent_ent,
        clue=clue,
        prize=prize,
        trait=trait,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a gentle ghost-story for a child in an indoor gym that uses repetition and sound effects.",
        f"Tell a spooky-but-safe story about {hero.id}, an index card, and an artichoke in an indoor gym.",
        "Write a short story where repeated clues sound eerie at first and then turn out to be a game.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, clue, parent = f["hero"], f["prize"], f["clue"], f["parent"]
    return [
        QAItem(
            question=f"What did {hero.id} find near the bleachers in the indoor gym?",
            answer=f"{hero.id} found a small index card near the bleachers.",
        ),
        QAItem(
            question=f"What was the strange green thing the card pointed toward?",
            answer=f"It was an artichoke on the lost-and-found shelf.",
        ),
        QAItem(
            question=f"Why did the gym seem spooky before the truth came out?",
            answer=(
                "It sounded spooky because of the echo, the fan, and the repeated "
                'clue words "Look again," which made the room feel haunted for a little while.'
            ),
        ),
        QAItem(
            question=f"Who was really making the mystery?",
            answer=f"{parent.id} was helping make the mystery as a playful game.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an index card?",
            answer="An index card is a small stiff card used for notes, lists, or clues.",
        ),
        QAItem(
            question="What is an artichoke?",
            answer="An artichoke is a green vegetable with many thick leaves that you pull off to eat.",
        ),
        QAItem(
            question="Why do indoor gyms echo?",
            answer="Indoor gyms can echo because their big hard walls and floors bounce sound around.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound that helps a story feel lively or spooky.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "gym"),
        asp.fact("indoors", "gym"),
        asp.fact("echoes", "gym"),
        asp.fact("thing", "index_card"),
        asp.fact("thing", "artichoke"),
        asp.fact("sound_word", "tap_tap"),
        asp.fact("sound_word", "swish"),
        asp.fact("sound_word", "thump"),
        asp.fact("repeats", "look_again"),
        asp.fact("clue_points_to", "index_card", "artichoke"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
spooky(Place) :- setting(Place), indoors(Place), echoes(Place).
tension(Story) :- sound_word(tap_tap), sound_word(swish), repeats(look_again), spooky(gym), Story=gym_story.
resolved(gym_story) :- clue_points_to(index_card, artichoke).
#show spooky/1.
#show tension/1.
#show resolved/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show spooky/1.\n#show resolved/1."))
    atoms = {(sym.name, tuple(a.name if hasattr(a, "name") else str(a) for a in sym.arguments)) for sym in model}
    want = {("spooky", ("gym",)), ("resolved", ("gym_story",))}
    if atoms == want:
        print("OK: ASP and Python story gate agree.")
        return 0
    print("MISMATCH:", atoms, want)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story style indoor gym world with an index card and an artichoke.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["gym"], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show spooky/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", parent="mother", trait="curious"),
            StoryParams(name="Leo", gender="boy", parent="father", trait="careful"),
            StoryParams(name="Nora", gender="girl", parent="mother", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name} ({p.gender})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
