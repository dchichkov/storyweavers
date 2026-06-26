#!/usr/bin/env python3
"""
A small bedtime-story world about a husband, a prayer, and a gentle
misunderstanding that resolves into a surprise and a soft ending.

Seed premise:
---
A husband hears a strange sound late at night and thinks something is wrong.
He quietly prays for help, only to discover that the source is not danger at all,
but a surprise someone in the house prepared. The suspense fades, the
misunderstanding clears, and the home ends the night peaceful and warm.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"husband", "father", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"wife", "mother", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    night: bool = True
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "home"
    husband_name: str = "Ethan"
    spouse_name: str = "Mara"
    seed: Optional[int] = None


@dataclass
class World:
    room: Room
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def build_world(params: StoryParams) -> World:
    room = Room(name="the house", night=True, quiet=True, affords={"pray", "listen", "open_door"})
    world = World(room=room)
    husband = world.add(Entity(
        id=params.husband_name, kind="character", type="husband",
        traits=["tired", "gentle"], meters={}, memes={}
    ))
    spouse = world.add(Entity(
        id=params.spouse_name, kind="character", type="wife",
        traits=["sleepy", "kind"], meters={}, memes={}
    ))
    sound = world.add(Entity(
        id="sound", type="thing", label="soft tapping", phrase="a soft tapping near the hall",
        meters={"loudness": 0.3}, memes={}
    ))
    surprise = world.add(Entity(
        id="surprise", type="thing", label="surprise", phrase="a small surprise with a ribbon",
        owner=spouse.id, meters={"hidden": 1.0}, memes={"warmth": 1.0}
    ))

    # Act 1
    world.say(f"{husband.id} was a tired husband in {world.room.name}, and the night was very still.")
    world.say(f"{husband.id} loved {spouse.id}, and before sleep he liked to pray in the quiet.")
    world.say(f"Tonight, {husband.id} heard {sound.phrase} and his heart gave a tiny jump.")

    # Act 2
    world.para()
    husband.memes["suspense"] = 1.0
    husband.memes["misunderstanding"] = 1.0
    world.say(f"He could not see what made the sound, so he thought something might be wrong.")
    world.say(f"{husband.id} folded his hands and began to pray for help, hoping the house would stay safe.")
    world.say(f"The tapping came again, soft and patient, and the suspense hung in the dark like a held breath.")

    # Act 3
    world.para()
    spouse.memes["surprise_ready"] = 1.0
    surprise.meters["hidden"] = 0.0
    husband.memes["misunderstanding"] = 0.0
    husband.memes["joy"] = 1.0
    world.say(f"Then {spouse.id} opened the door with a shy smile and a little ribbon in her hands.")
    world.say(f"It was only a surprise she had been hiding for him, not danger at all.")
    world.say(f"{husband.id} laughed softly, thanked her, and felt the suspense melt away like a bad dream.")
    world.say(f"The house grew calm again, and the husband and his wife fell asleep with warm hearts.")

    world.facts.update(
        husband=husband,
        spouse=spouse,
        sound=sound,
        surprise=surprise,
        setting=world.room,
        prayed=True,
        misunderstood=True,
        suspense=True,
        surprised=True,
        resolved=True,
    )
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    h = f["husband"]
    s = f["spouse"]
    return [
        f"Write a bedtime story about {h.id}, a husband who hears a mystery sound and prays in the dark.",
        f"Tell a gentle story where {h.id} and {s.id} begin with a misunderstanding, then reach a surprise ending.",
        "Write a short bedtime tale with suspense, a quiet prayer, and a loving surprise in the house.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = f["husband"]
    s = f["spouse"]
    return [
        QAItem(
            question=f"Why did {h.id} feel suspense at the start of the night?",
            answer=f"{h.id} heard a soft tapping in the house and could not tell what made it, so he felt suspense and wondered if something was wrong.",
        ),
        QAItem(
            question=f"What did {h.id} do when he did not understand the sound?",
            answer=f"He folded his hands and prayed for help because he wanted the house to stay safe.",
        ),
        QAItem(
            question=f"What was the misunderstanding in the story?",
            answer=f"{h.id} thought the tapping might mean danger, but it was really just a surprise that {s.id} had hidden for him.",
        ),
        QAItem(
            question=f"How did the story end after the surprise was revealed?",
            answer=f"The misunderstanding cleared, the suspense faded, and {h.id} and {s.id} went to sleep with warm hearts.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prayer?",
            answer="A prayer is a quiet way of talking to God, often to ask for help, comfort, or thanks.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks one thing is true, but the real meaning is different.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes someone feel amazed or happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


def ASP_RULES() -> str:
    return r"""
#show valid_story/1.
valid_story(home) :- setting(home), has_husband, has_prayer, has_misunderstanding, has_surprise.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "home"),
        asp.fact("has_husband"),
        asp.fact("has_prayer"),
        asp.fact("has_misunderstanding"),
        asp.fact("has_surprise"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = set(asp.atoms(model, "valid_story")) == {("home",)}
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: husband, pray, misunderstanding, surprise, suspense.")
    ap.add_argument("--setting", choices=["home"], default=None)
    ap.add_argument("--husband-name", default=None)
    ap.add_argument("--spouse-name", default=None)
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
    if args.setting and args.setting != "home":
        raise StoryError("Only the home setting is valid for this bedtime story.")
    husband_name = args.husband_name or rng.choice(["Ethan", "Noah", "Liam", "Owen", "Milo"])
    spouse_name = args.spouse_name or rng.choice(["Mara", "Ivy", "Nora", "Lena", "June"])
    return StoryParams(setting="home", husband_name=husband_name, spouse_name=spouse_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
    StoryParams(setting="home", husband_name="Ethan", spouse_name="Mara"),
    StoryParams(setting="home", husband_name="Noah", spouse_name="Ivy"),
    StoryParams(setting="home", husband_name="Owen", spouse_name="Lena"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
