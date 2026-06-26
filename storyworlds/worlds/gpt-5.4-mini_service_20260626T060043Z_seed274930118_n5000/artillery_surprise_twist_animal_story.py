#!/usr/bin/env python3
"""
A small storyworld about an animal parade, a surprising artillery display, and a twist
that turns a scare into a celebration.

The premise is simple:
- an animal crowd prepares for a show
- a loud artillery prop is supposed to stay harmless
- a surprise changes how everyone reads the noise
- a twist reveals the sound was part of a rescued celebration all along

This world keeps the simulation tiny and child-facing. The main state tracks:
- who is present
- what prop is being used
- whether the crowd feels worried or excited
- whether the artillery item is safe, hidden, or used for a surprise finale

The generated story should feel like a complete Animal Story:
beginning, worry, turn, and a happy ending image.
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


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "thing"
    name: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.species in {"cat", "dog", "rabbit", "fox", "bear", "mouse", "duck", "owl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap_pronoun(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()


@dataclass
class Venue:
    place: str = "the meadow"
    indoor: bool = False
    echoes: bool = True
    hides_artillery: bool = False


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    surprise: str
    twist: str
    loud: bool = True
    safe: bool = True


@dataclass
class StoryParams:
    venue: str
    prop: str
    hero: str
    friend: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
VENUES = {
    "meadow": Venue(place="the meadow", indoor=False, echoes=True, hides_artillery=False),
    "barnyard": Venue(place="the barnyard", indoor=False, echoes=False, hides_artillery=True),
    "fairground": Venue(place="the fairground", indoor=False, echoes=True, hides_artillery=False),
    "stable": Venue(place="the stable", indoor=True, echoes=False, hides_artillery=True),
}

PROPS = {
    "toy_cannon": Prop(
        id="toy_cannon",
        label="toy cannon",
        phrase="a bright toy cannon",
        surprise="a surprise pop of confetti",
        twist="the cannon was only a confetti launcher",
        loud=True,
        safe=True,
    ),
    "festival_horn": Prop(
        id="festival_horn",
        label="festival horn",
        phrase="a shiny festival horn",
        surprise="a sudden burst of music",
        twist="the horn was meant to call everyone in for cake",
        loud=True,
        safe=True,
    ),
    "drum_cart": Prop(
        id="drum_cart",
        label="drum cart",
        phrase="a little drum cart",
        surprise="a fast drumroll",
        twist="the cart hid a banner that said Surprise!",
        loud=False,
        safe=True,
    ),
}

ANIMALS = [
    ("Pip", "rabbit"),
    ("Momo", "cat"),
    ("Toby", "dog"),
    ("Luna", "fox"),
    ("Nell", "bear"),
    ("Roo", "duck"),
]

FRIENDS = ["mouse", "owl", "goat", "hen", "pony", "squirrel"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        import copy

        c = World(self.venue)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _meter(ent: Entity, key: str, amount: float = 1.0) -> float:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount
    return ent.meters[key]


def _meme(ent: Entity, key: str, amount: float = 1.0) -> float:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount
    return ent.memes[key]


def venue_detail(venue: Venue) -> str:
    if venue.place == "the meadow":
        return "The grass was soft, and the daisies leaned toward the sun."
    if venue.place == "the barnyard":
        return "The barnyard was warm and busy, with hay stacked into golden squares."
    if venue.place == "the fairground":
        return "The fairground buzzed with bunting, balloons, and sweet smells."
    return "The stable was quiet, except for the tiny sounds of shuffling paws."


def safe_artillery(prop: Prop, venue: Venue) -> bool:
    return prop.safe and (venue.hides_artillery or prop.id != "toy_cannon" or venue.place != "the stable")


def story_tension(world: World, hero: Entity, friend: Entity, prop: Prop) -> None:
    _meme(hero, "curiosity", 1)
    _meme(friend, "worry", 1)
    world.say(
        f"{hero.name} the {hero.species} and {friend.name} the {friend.species} had been "
        f"waiting for the show all morning."
    )
    world.say(
        f"They had a {prop.phrase} ready behind a little curtain."
    )


def surprise_turn(world: World, hero: Entity, friend: Entity, prop: Prop) -> None:
    _meme(hero, "surprise", 1)
    _meme(friend, "surprise", 1)
    _meter(world.get("artillery"), "hidden", 1)
    world.say(
        f"Then, with a sudden {prop.surprise}, the curtain jumped open."
    )
    world.say(
        f"{friend.name} blinked hard, because that loud artillery sound felt bigger than expected."
    )


def twist_reveal(world: World, hero: Entity, friend: Entity, prop: Prop) -> None:
    _meme(hero, "joy", 2)
    _meme(friend, "joy", 2)
    _meme(friend, "relief", 1)
    world.say(
        f"But here was the twist: {prop.twist}."
    )
    world.say(
        f"Instead of danger, the noise sent confetti floating over their heads like little snowflakes."
    )


def ending_image(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.name} laughed, {friend.name} clapped, and the animals danced under the soft paper rain."
    )
    world.say(
        f"By the end, the artillery prop was just a harmless part of the celebration, and the meadow felt bright and safe."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(venue: Venue, prop: Prop, hero_name: str, hero_species: str, friend_species: str) -> World:
    world = World(venue)
    hero = world.add(Entity(id="hero", kind="character", species=hero_species, name=hero_name))
    friend = world.add(Entity(id="friend", kind="character", species=friend_species, name="Milo"))
    artillery = world.add(Entity(id="artillery", kind="thing", species="artillery", name=prop.label, role="prop"))

    world.say(f"It was a day for a show at {venue.place}.")
    world.say(venue_detail(venue))
    world.say(f"{hero.name} the {hero.species} noticed the {prop.label} first and wagged with excitement.")
    story_tension(world, hero, friend, prop)

    world.para()
    world.say(f"At first, {friend.name} thought the artillery might be a real danger.")
    _meme(friend, "fear", 1)
    if prop.loud:
        _meter(artillery, "noise", 1)
    surprise_turn(world, hero, friend, prop)

    world.para()
    twist_reveal(world, hero, friend, prop)
    ending_image(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        artillery=artillery,
        prop=prop,
        venue=venue,
        safe=safe_artillery(prop, venue),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    prop: Prop = f["prop"]  # type: ignore[assignment]
    venue: Venue = f["venue"]  # type: ignore[assignment]
    return [
        f'Write a short Animal Story about {hero.name} the {hero.species} at {venue.place}, featuring {prop.label} and a surprise.',
        f"Tell a gentle story where {friend.name} the {friend.species} worries about artillery, then learns it is only part of a twist ending.",
        f'Write a child-friendly story that uses the words "Surprise" and "Twist" and ends with animals celebrating at {venue.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    prop: Prop = f["prop"]  # type: ignore[assignment]
    venue: Venue = f["venue"]  # type: ignore[assignment]
    safe: bool = bool(f["safe"])
    return [
        QAItem(
            question=f"Who was the story about at {venue.place}?",
            answer=f"The story was about {hero.name} the {hero.species}, who went with {friend.name} the {friend.species} to see a show at {venue.place}.",
        ),
        QAItem(
            question=f"What made the animals surprised?",
            answer=f"They were surprised by {prop.phrase}, because it made a sudden sound and opened the curtain all at once.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {prop.twist}, so the loud sound was part of a fun celebration instead of something scary.",
        ),
        QAItem(
            question=f"Was the artillery safe in the end?",
            answer=f"Yes. The artillery was safe, because it was only used as part of the show and ended with confetti and happy cheering.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that appears or happens when you do not know it is coming.",
        ),
        QAItem(
            question="What does twist mean in a story?",
            answer="A twist is a new part of the story that changes how you understand what was happening.",
        ),
        QAItem(
            question="What is artillery?",
            answer="Artillery usually means big loud weapons, but in a child-safe story it can be a pretend prop that only makes a sound or a show.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
safe_artillery(A) :- prop(A), safe(A).
twist_show(A) :- prop(A), surprise(A), twist(A).
happy_end(V, A) :- venue(V), prop(A), safe_artillery(A), twist_show(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for v in VENUES.values():
        lines.append(asp.fact("venue", v.place.replace("the ", "").replace(" ", "_")))
        if v.indoor:
            lines.append(asp.fact("indoor", v.place.replace("the ", "").replace(" ", "_")))
        if v.hides_artillery:
            lines.append(asp.fact("hide_artillery", v.place.replace("the ", "").replace(" ", "_")))
    for p in PROPS.values():
        lines.append(asp.fact("prop", p.id))
        if p.safe:
            lines.append(asp.fact("safe", p.id))
        if p.surprise:
            lines.append(asp.fact("surprise", p.id))
        if p.twist:
            lines.append(asp.fact("twist", p.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2."))
    atoms = set(asp.atoms(model, "happy_end"))
    expected = {(v.place.replace("the ", "").replace(" ", "_"), p.id)
                for v in VENUES.values() for p in PROPS.values()
                if p.safe and p.surprise and p.twist}
    if atoms == expected:
        print(f"OK: ASP parity holds ({len(atoms)} happy-end combos).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Generation interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with artillery, Surprise, and Twist.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    venue = args.venue or rng.choice(list(VENUES))
    prop = args.prop or rng.choice(list(PROPS))
    hero = args.hero or rng.choice([n for n, _ in ANIMALS])
    friend = args.friend or rng.choice(FRIENDS)
    if hero == friend:
        raise StoryError("The hero and friend should be different characters.")
    return StoryParams(venue=venue, prop=prop, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    venue = VENUES[params.venue]
    prop = PROPS[params.prop]
    hero_species = dict(ANIMALS).get(params.hero, "rabbit")
    friend_species = params.friend
    world = tell(venue, prop, params.hero, hero_species, friend_species)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} species={e.species} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
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


CURATED = [
    StoryParams(venue="meadow", prop="toy_cannon", hero="Pip", friend="owl"),
    StoryParams(venue="barnyard", prop="festival_horn", hero="Momo", friend="goat"),
    StoryParams(venue="fairground", prop="drum_cart", hero="Luna", friend="squirrel"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_end/2."))
        atoms = sorted(set(asp.atoms(model, "happy_end")))
        for v, p in atoms:
            print(v, p)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
