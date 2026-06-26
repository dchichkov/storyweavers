#!/usr/bin/env python3
"""
Storyworld: a small ghost story about greed, humor, dialogue, and kindness.

A child or small helper finds a strange whatchamacallit at a lonely place at night.
A greedy choice wakes a harmless ghost, but a funny conversation and a kind act
turn the scare into a gentle ending.
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
    kind: str = "thing"  # character | thing | spirit
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "spirit":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    mood: str
    ghosty: bool = True


@dataclass
class Relic:
    label: str
    phrase: str
    thing_type: str
    shiny: bool = True


@dataclass
class GhostPlan:
    name: str
    reveal_line: str
    funny_line: str
    kind_line: str
    ending_line: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    place: str
    hero_type: str
    name: str
    sidekick: str
    relic: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place("the attic", "dusty and moonlit", True),
    "hallway": Place("the hallway", "quiet and echoing", True),
    "garden": Place("the garden", "soft and dark", True),
    "cellar": Place("the cellar", "cold and creaky", True),
}

HERO_TYPES = ["girl", "boy"]
NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Pia", "Tess"],
    "boy": ["Finn", "Owen", "Milo", "Theo", "Ben"],
}
SIDEKICKS = ["cat", "dog", "mouse", "lantern", "ribbon"]

RELICS = {
    "whatchamacallit": Relic(
        label="whatchamacallit",
        phrase="a tiny whatchamacallit with a silver handle",
        thing_type="whatchamacallit",
    ),
    "key": Relic(
        label="key",
        phrase="an old brass key",
        thing_type="key",
    ),
    "candle": Relic(
        label="candle",
        phrase="a warm little candle in a glass jar",
        thing_type="candle",
    ),
}

GHOST_PLAN = GhostPlan(
    name="Murmur",
    reveal_line="A pale ghost drifted out of the dark and blinked at the greedy hand.",
    funny_line="The ghost wore a crooked hat and whispered, 'I was hiding that all along, but I do not mind sharing.'",
    kind_line="Then the child laughed, because the ghost had a squeaky voice like a small door.",
    ending_line="In the end, the whatchamacallit stayed in the room, and the room felt less scary and more like a friend.",
)

TRAITS = ["curious", "gentle", "brave", "silly", "thoughtful"]


class GhostWorld:
    def __init__(self, world: World):
        self.w = world

    def introduce(self, hero: Entity, sidekick: Entity, relic: Entity) -> None:
        self.w.say(
            f"{hero.id} was a little {hero.type} who loved quiet places and strange old things. "
            f"{hero.pronoun('subject').capitalize()} had a {sidekick.label} and a big wish to see what was hidden in {self.w.place.name}."
        )
        self.w.say(
            f"On a shelf sat {relic.phrase}, and {hero.id} kept thinking about it."
        )

    def greed_turn(self, hero: Entity, relic: Entity) -> None:
        hero.memes["greed"] = hero.memes.get("greed", 0) + 1
        self.w.say(
            f"{hero.id} reached out and thought, 'If I take {relic.pronoun('object')}, no one will know.'"
        )
        self.w.say(
            f"But the old room went still, as if the dark itself had heard that greedy thought."
        )

    def ghost_reveal(self, ghost: Entity) -> None:
        self.w.say(GHOST_PLAN.reveal_line)
        self.w.say(
            f"'{ghost.label}, did you mean to scare me?' {self.w.facts['hero'].id} asked."
        )
        self.w.say(
            f"'Only a little,' the ghost answered, 'because you were trying to snatch what was not yours.'"
        )

    def humor_dialogue(self, hero: Entity, ghost: Entity) -> None:
        hero.memes["fear"] = hero.memes.get("fear", 0) + 1
        ghost.memes["amused"] = ghost.memes.get("amused", 0) + 1
        self.w.say(
            f"{hero.id} swallowed hard and said, 'You are a real spooky {ghost.role}, aren't you?'"
        )
        self.w.say(GHOST_PLAN.funny_line)
        self.w.say(GHOST_PLAN.kind_line)

    def kindness_turn(self, hero: Entity, ghost: Entity, relic: Entity) -> None:
        hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
        hero.memes["greed"] = 0
        self.w.say(
            f"{hero.id} put {relic.pronoun('object')} back where it had been and said, "
            f"'I'm sorry. You can keep it here, and I can look at it without taking it.'"
        )
        self.w.say(
            f"The ghost's cloudy face softened. 'That was the right answer,' {ghost.pronoun('subject')} said."
        )
        self.w.say(
            f"Then {ghost.label} shared the story of the whatchamacallit, and it turned out to be only a little house key for a tiny night shelf."
        )
        self.w.say(GHOST_PLAN.ending_line)

    def finish(self, hero: Entity) -> None:
        hero.memes["relief"] = hero.memes.get("relief", 0) + 1
        self.w.say(
            f"{hero.id} smiled, and {hero.pronoun('subject')} and {self.w.facts['sidekick'].label} walked home without feeling scared."
        )
        self.w.say(
            f"The moon stayed up over {self.w.place.name}, and the old place seemed kind instead of creepy."
        )


def tell(place: Place, hero_type: str, name: str, sidekick: str, relic: str) -> World:
    if relic not in RELICS:
        raise StoryError(f"Unknown relic: {relic}")
    if hero_type not in HERO_TYPES:
        raise StoryError(f"Unknown hero type: {hero_type}")
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=hero_type, label=name))
    helper = world.add(Entity(id="sidekick", kind="character", type=sidekick, label=sidekick))
    relic_ent = world.add(Entity(
        id="relic",
        kind="thing",
        type=RELICS[relic].thing_type,
        label=RELICS[relic].label,
        phrase=RELICS[relic].phrase,
    ))
    ghost = world.add(Entity(id="ghost", kind="spirit", type="ghost", label=GHOST_PLAN.name, role="ghost"))
    world.facts.update(hero=hero, sidekick=helper, relic=relic_ent, ghost=ghost)

    gw = GhostWorld(world)
    gw.introduce(hero, helper, relic_ent)
    world.para()
    gw.greed_turn(hero, relic_ent)
    gw.ghost_reveal(ghost)
    world.para()
    gw.humor_dialogue(hero, ghost)
    gw.kindness_turn(hero, ghost, relic_ent)
    gw.finish(hero)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    relic = world.facts["relic"]
    return [
        f"Write a short ghost story for a young child about {hero.id} and {relic.label}.",
        f"Tell a spooky-but-gentle tale set in {world.place.name} that includes greed, humor, dialogue, and kindness.",
        f"Write a tiny story where someone wants to take {relic.label}, then learns to be kind to a ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    ghost = world.facts["ghost"]
    relic = world.facts["relic"]
    sidekick = world.facts["sidekick"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} who went into {world.place.name} with a {sidekick.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} try to take at first?",
            answer=f"{hero.id} tried to take {relic.label} because {hero.pronoun('subject')} felt greedy for a moment.",
        ),
        QAItem(
            question=f"Who was the ghost in the story?",
            answer=f"The ghost was {ghost.label}, a pale spirit who came out of the dark to talk instead of hurt anyone.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with kindness, laughter, and the whatchamacallit safely staying where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story like this?",
            answer="A ghost is a spooky spirit character in a story. In gentle stories, ghosts can talk, feel sad, and become friendly.",
        ),
        QAItem(
            question="What does greed mean?",
            answer="Greed means wanting more than you should, especially when you try to take something that belongs elsewhere or to someone else.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="Why can humor help in a scary story?",
            answer="Humor can make a scary moment feel lighter, so the characters can keep talking and solve the problem without mean behavior.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = [f"place={world.place.name} mood={world.place.mood}"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% greed_story / declarative twin
greedy(H) :- hero(H), wants_take(H).
ghost_reveals(G) :- ghost(G), greedy(_).
humor(H) :- says_joke(H).
kindness(H) :- apologizes(H).
resolved :- ghost_reveals(_), humor(_), kindness(_).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("ghost", "ghost"),
        asp.fact("relic", "relic"),
        asp.fact("wants_take", "hero"),
        asp.fact("says_joke", "hero"),
        asp.fact("apologizes", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    got = bool(asp.atoms(model, "resolved"))
    want = True
    if got == want:
        print("OK: ASP and Python story gate agree.")
        return 0
    print("MISMATCH: ASP and Python story gate disagree.")
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for htype in HERO_TYPES:
            for relic in RELICS:
                combos.append((place, htype, relic))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with greed, humor, dialogue, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", dest="hero_type", choices=HERO_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--relic", choices=RELICS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.hero_type:
        combos = [c for c in combos if c[1] == args.hero_type]
    if args.relic:
        combos = [c for c in combos if c[2] == args.relic]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, hero_type, relic = rng.choice(combos)
    name = args.name or rng.choice(NAMES[hero_type])
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(place=place, hero_type=hero_type, name=name, sidekick=sidekick, relic=relic)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero_type, params.name, params.sidekick, params.relic)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    return sorted(set(asp.atoms(model, "resolved")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world uses a tiny ASP twin; verification is the main supported ASP mode.")
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, hero_type=h, name=NAMES[h][0], sidekick=SIDEKICKS[0], relic=r)) for p, h, r in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
