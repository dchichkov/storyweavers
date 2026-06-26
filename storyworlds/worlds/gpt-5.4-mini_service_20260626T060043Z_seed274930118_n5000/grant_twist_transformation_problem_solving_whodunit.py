#!/usr/bin/env python3
"""
A tiny whodunit story world about a grant ceremony, a sudden twist, a
transformation, and a piece of problem solving.

The seed idea is simple:
- A child helps at a small grant announcement.
- Something odd happens that changes the shape of the problem.
- The clues reveal who caused the trouble.
- The characters solve it by thinking carefully and acting kindly.

The world is intentionally small and constraint-checked so every story reads
like a complete miniature mystery.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective"}
        male = {"boy", "man", "father", "gardener"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    place: str
    light: str = "warm"
    clues: set[str] = field(default_factory=set)
    suspects: set[str] = field(default_factory=set)


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy
        w = World(self.room)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    detective: str
    grant: str
    suspect: str
    twist: str
    seed: Optional[int] = None


PLACES = {
    "hall": Room(place="the town hall", light="bright", clues={"paper", "ink", "footprints"}, suspects={"clerk", "gardener"}),
    "museum": Room(place="the small museum", light="soft", clues={"frame", "key", "dust"}, suspects={"curator", "janitor"}),
    "library": Room(place="the library", light="golden", clues={"book", "stamp", "string"}, suspects={"librarian", "helper"}),
}

HEROES = [
    ("Mina", "girl"),
    ("Leo", "boy"),
    ("Nora", "girl"),
    ("Toby", "boy"),
]

DETECTIVES = [
    ("Mrs. Vale", "woman"),
    ("Mr. Finch", "man"),
    ("Aunt Iva", "woman"),
]

GRANTS = [
    ("a little grant for the music room", "grant"),
    ("a science grant for new tools", "grant"),
    ("a grant for the garden club", "grant"),
]

TWISTS = [
    "the envelope was empty",
    "the winner's name had been changed",
    "the clue on the desk pointed to the wrong room",
]

SUSPECTS = [
    "clerk",
    "gardener",
    "curator",
    "janitor",
    "librarian",
    "helper",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with a grant, a twist, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--grant")
    ap.add_argument("--suspect")
    ap.add_argument("--twist")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    hero_name, hero_type = rng.choice(HEROES) if not args.hero else (args.hero, "girl" if args.hero in {"Mina", "Nora"} else "boy")
    detective_name, detective_type = rng.choice(DETECTIVES)
    grant, grant_word = rng.choice(GRANTS) if not args.grant else (args.grant, "grant")
    room = PLACES[place]
    suspect = args.suspect or rng.choice(sorted(room.suspects))
    twist = args.twist or rng.choice(TWISTS)
    if suspect not in room.suspects:
        raise StoryError(f"(No story: {suspect} does not fit the clues in {room.place}.)")
    return StoryParams(place=place, hero=hero_name, hero_type=hero_type, detective=detective_name, grant=grant, suspect=suspect, twist=twist, seed=args.seed)


def _speak(world: World, text: str) -> None:
    world.say(text)


def build_world(params: StoryParams) -> World:
    room = PLACES[params.place]
    world = World(room)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    detective = world.add(Entity(id=params.detective, kind="character", type="detective", label=params.detective))
    suspect = world.add(Entity(id=params.suspect, kind="character", type=params.suspect, label=params.suspect))
    award = world.add(Entity(id="grant", type="grant", label="grant", phrase=params.grant, owner=hero.id))
    clue = world.add(Entity(id="clue", type="clue", label="clue", hidden=True))
    world.facts.update(hero=hero, detective=detective, suspect=suspect, award=award, clue=clue, twist=params.twist, place=room)
    return world


def generate_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    detective: Entity = f["detective"]
    suspect: Entity = f["suspect"]
    award: Entity = f["award"]
    room: Room = f["place"]

    _speak(world, f"At {room.place}, {hero.id} stood with {detective.label} for the grant announcement.")
    _speak(world, f"Everyone hoped the {award.phrase} would help the little room grow brighter.")
    world.para()
    _speak(world, f"Then came the twist: {f['twist']}.")
    _speak(world, f"That strange change turned a cheerful announcement into a puzzle.")

    world.para()
    _speak(world, f"{detective.label} looked at the clues: {', '.join(sorted(room.clues))}.")
    _speak(world, f"{hero.id} noticed that {suspect.label} had moved too quickly near the table.")
    _speak(world, f"Together they followed the clues and saw that the trick was not a theft at all, but a switch.")

    world.para()
    _speak(world, f"{suspect.label} had hidden the real paper and left the wrong one behind by mistake.")
    _speak(world, f"When {hero.id} asked why, {suspect.pronoun('subject')} admitted being nervous about the crowd.")
    _speak(world, f"{detective.label} helped solve the problem by matching the clue to the right envelope and restoring the grant.")

    world.para()
    _speak(world, f"In the end, the grant was announced properly, {suspect.label} felt relieved, and {hero.id} smiled at the tidy new answer.")
    _speak(world, f"The room seemed lighter, as if the mystery had been folded neatly back into place.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    detective: Entity = f["detective"]
    suspect: Entity = f["suspect"]
    room: Room = f["place"]
    twist: str = f["twist"]
    award: Entity = f["award"]
    return [
        QAItem(
            question=f"Who was at {room.place} when the grant announcement started?",
            answer=f"{hero.id} was there with {detective.label}, and they were waiting for the {award.phrase}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {twist}, which turned the grant announcement into a mystery.",
        ),
        QAItem(
            question=f"Who turned out to be part of the problem?",
            answer=f"{suspect.label} was part of the problem because {suspect.pronoun('subject')} had made the wrong switch near the table.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"They solved it by following the clues, asking careful questions, and putting the grant paper back where it belonged.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grant?",
            answer="A grant is money or support given to help a person, group, or project do something useful.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to find out what really happened.",
        ),
        QAItem(
            question="Why are clues important in a mystery?",
            answer="Clues are important because they help people solve the problem and discover the truth.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    return [
        f"Write a short whodunit for children where {hero.id} helps with a grant and a mystery appears.",
        "Tell a gentle mystery story with a twist, a clue, and a happy solution.",
        "Write a child-facing story about a grant ceremony that turns into problem solving.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% room(R). clue(R,C). suspect(R,S). grant(G). twist(T).

has_twist(R) :- twist(R,_).
mystery(R) :- grant(R), has_twist(R), clue(R,_).

% A culprit is compatible with the room if it appears among the room suspects.
possible_culprit(R,S) :- suspect(R,S).

% The puzzle is solvable when there is at least one clue and one culprit.
solvable(R) :- clue(R,_), possible_culprit(R,_).

#show mystery/1.
#show solvable/1.
#show possible_culprit/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key, room in PLACES.items():
        lines.append(asp.fact("room", key))
        for clue in sorted(room.clues):
            lines.append(asp.fact("clue", key, clue))
        for sus in sorted(room.suspects):
            lines.append(asp.fact("suspect", key, sus))
    for _name, _type in HEROES:
        pass
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    if ("mystery", 1) in atoms and ("solvable", 1) in atoms:
        print("OK: ASP program produces a mystery and solvable room.")
        return 0
    print("MISMATCH: ASP program did not produce expected atoms.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="hall", hero="Mina", hero_type="girl", detective="Mrs. Vale", grant="a little grant for the music room", suspect="clerk", twist="the envelope was empty"),
            StoryParams(place="museum", hero="Leo", hero_type="boy", detective="Mr. Finch", grant="a science grant for new tools", suspect="janitor", twist="the winner's name had been changed"),
            StoryParams(place="library", hero="Nora", hero_type="girl", detective="Aunt Iva", grant="a grant for the garden club", suspect="helper", twist="the clue on the desk pointed to the wrong room"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
