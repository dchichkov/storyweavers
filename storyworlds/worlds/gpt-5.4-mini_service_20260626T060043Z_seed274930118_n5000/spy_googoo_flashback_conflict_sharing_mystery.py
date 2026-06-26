#!/usr/bin/env python3
"""
storyworlds/worlds/spy_googoo_flashback_conflict_sharing_mystery.py
===================================================================

A small mystery storyworld about a spy, a googoo, a flashback, conflict, and sharing.

Premise:
- A child spy looks for a missing googoo.
- A flashback reveals where the googoo came from and why it matters.
- The mystery turns on a conflict about who gets to keep the googoo.
- Sharing becomes the reasonable resolution.
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
    holder: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    place: str = "the attic"
    hiding_places: list[str] = field(default_factory=lambda: ["behind the chair", "under the crate", "inside the hatbox"])


@dataclass
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


PLACES = {
    "attic": Location(place="the attic"),
    "treehouse": Location(place="the treehouse"),
    "library": Location(place="the little library"),
}

HERO_NAMES = ["Milo", "Nia", "Toby", "Lina", "Zed", "Pia"]
FRIEND_NAMES = ["June", "Omar", "Elsie", "Finn", "Mina", "Rex"]

GOOGOO_LABELS = [
    ("googoo", "a tiny googoo with a shiny blue shell"),
    ("googoo", "a small googoo that glowed softly in the dark"),
]

HIDING_SPOTS = ["behind the chair", "under the crate", "inside the hatbox", "near the old lamp"]


def _noun_phrase(ent: Entity) -> str:
    return ent.label or ent.type


def tell(params: StoryParams) -> World:
    loc = PLACES[params.place]
    world = World(location=loc)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    googoo_type, googoo_phrase = random.Random(0).choice(GOOGOO_LABELS)
    googoo = world.add(Entity(id="googoo", type=googoo_type, label="googoo", phrase=googoo_phrase, owner=hero.id))
    note = world.add(Entity(id="note", type="note", label="secret note", phrase="a folded secret note", owner=hero.id, holder=hero.id))

    hero.memes["curiosity"] = 1
    hero.memes["mystery"] = 1
    googoo.meters["hidden"] = 1
    note.meters["hidden"] = 1

    world.say(
        f"{hero.id} was a little spy who loved solving quiet mysteries."
        f" {hero.pronoun().capitalize()} kept a careful eye on {world.location.place}."
    )
    world.say(
        f"One gray afternoon, {hero.id} noticed that the googoo was gone from its usual spot."
        f" Only a small empty mark was left on the shelf."
    )

    world.para()
    world.say(
        f"{hero.id} searched {loc.hiding_places[0]}, then {loc.hiding_places[1]}, and then {loc.hiding_places[2]}."
        f" But the googoo stayed missing."
    )
    world.say(
        f"That made the mystery feel bigger, because the googoo had been part of {hero.id}'s most important clue kit."
    )

    world.para()
    hero.memes["flashback"] = 1
    world.say(
        f"Then {hero.id} had a flashback."
        f" {hero.pronoun().capitalize()} remembered finding the googoo with {friend.id} on a rainy day."
        f" They had promised to share it when either one needed help with a secret puzzle."
    )
    world.say(
        f"In the memory, {friend.id} had tucked the googoo into {hero.pronoun('possessive')} pocket and said,"
        f" \"We can both use it when the clues get tricky.\""
    )

    world.para()
    friend.holder = "friend_hand"
    googoo.holder = friend.id
    world.say(
        f"At last, {hero.id} found {friend.id} in the corner by the window."
        f" The googoo was there too, glowing beside {friend.id}'s hands."
    )
    friend.memes["wanting"] = 1
    hero.memes["conflict"] = 1
    world.say(
        f"{friend.id} said {friend.pronoun().capitalize()} needed the googoo for a puzzle first."
        f" {hero.id} wanted it back right away, and the two friends grew tense."
    )

    world.para()
    world.say(
        f"{hero.id} looked at the googoo and remembered the promise from the flashback."
        f" {hero.pronoun().capitalize()} took a slow breath and said they could share it instead of arguing."
    )
    friend.memes["conflict"] = 0
    hero.memes["conflict"] = 0
    hero.memes["kindness"] = 1
    friend.memes["relief"] = 1
    googoo.holder = "both"
    world.say(
        f"They made a simple plan: {friend.id} would use the googoo for the first clue, and then {hero.id} would hold it for the next one."
        f" The mystery could wait, because sharing worked better than fighting."
    )
    world.say(
        f"By the end, the googoo shone between them like a tiny moon, and the empty shelf was no longer a problem."
    )

    world.facts = {
        "hero": hero,
        "friend": friend,
        "googoo": googoo,
        "note": note,
        "place": loc.place,
        "hiding_spots": list(loc.hiding_places),
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        'Write a short mystery story for a young child about a spy and a googoo.',
        f"Tell a gentle mystery where {hero.id} finds a missing googoo, remembers a flashback, and resolves a conflict by sharing with {friend.id}.",
        "Write a simple story with a hidden object, a flashback, and a happy ending about friends learning to share.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    googoo: Entity = f["googoo"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the spy in the story?",
            answer=f"The spy was {hero.id}, who loved solving mysteries in {place}.",
        ),
        QAItem(
            question=f"What was missing at the start of the mystery?",
            answer=f"The missing thing was the googoo, which was not on its usual shelf spot.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered finding the googoo with {friend.id} on a rainy day and promising to share it.",
        ),
        QAItem(
            question=f"How was the conflict solved?",
            answer=f"The friends solved the conflict by sharing the googoo and taking turns using it.",
        ),
        QAItem(
            question=f"What did the googoo look like?",
            answer=f"The googoo was described as {googoo.phrase}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spy?",
            answer="A spy is someone who looks carefully for clues and tries to solve secrets.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory scene that shows something from earlier.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let more than one person use or enjoy something fairly.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story with a hidden problem or unanswered question that people try to figure out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.holder:
            bits.append(f"holder={e.holder}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_fact(H).
friend(F) :- friend_fact(F).
googoo(G) :- googoo_fact(G).
missing(G) :- googoo(G), not held(G).
flashback_needed(H) :- hero(H), missing(_).
conflict(H,F) :- hero(H), friend(F), wants_both(H,F), not sharing(H,F).
sharing(H,F) :- hero(H), friend(F), agree_share(H,F).
resolution(H,F) :- conflict(H,F), sharing(H,F).
#show missing/1.
#show conflict/2.
#show sharing/2.
#show resolution/2.
"""


def asp_facts() -> str:
    import asp
    f = SAMPLE_REGISTRY if "SAMPLE_REGISTRY" in globals() else {}
    lines = []
    if f:
        lines.append(asp.fact("hero_fact", f["hero"]))
        lines.append(asp.fact("friend_fact", f["friend"]))
        lines.append(asp.fact("googoo_fact", f["googoo"]))
        lines.append(asp.fact("wants_both", f["hero"], f["friend"]))
        lines.append(asp.fact("agree_share", f["hero"], f["friend"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show missing/1.\n#show conflict/2.\n#show sharing/2.\n#show resolution/2."))
    atoms = {sym.name for sym in model}
    if "missing" in atoms or "conflict" in atoms or "sharing" in atoms or "resolution" in atoms:
        print("OK: ASP rules produced a model.")
        return 0
    print("MISMATCH: ASP model did not contain expected atoms.")
    return 1


CURATED = [
    StoryParams(place="attic", hero_name="Milo", hero_type="boy", friend_name="June", friend_type="girl"),
    StoryParams(place="treehouse", hero_name="Nia", hero_type="girl", friend_name="Omar", friend_type="boy"),
    StoryParams(place="library", hero_name="Toby", hero_type="boy", friend_name="Elsie", friend_type="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery storyworld about a spy and a googoo.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    hero_type = args.gender or rng.choice(["girl", "boy"])
    friend_type = args.friend_gender or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if hero_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    global SAMPLE_REGISTRY
    SAMPLE_REGISTRY = {
        "hero": world.facts["hero"].id,
        "friend": world.facts["friend"].id,
        "googoo": world.facts["googoo"].id,
    }
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
        print(asp_program("#show resolution/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show missing/1.\n#show conflict/2.\n#show sharing/2.\n#show resolution/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
