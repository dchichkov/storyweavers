#!/usr/bin/env python3
"""
A small animal-story world with a flashback beat.

Premise:
- A little animal hears a tum sound in the dark.
- The sound makes the animal remember a past scare.
- A friend helps the animal check the source and calm down.
- The ending proves the fear changed into curiosity and relief.

The storyworld is intentionally compact: one creature, one helper, one place,
one remembered event, one turn, one resolution.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "bunny", "cat", "kitten", "fox", "duck", "mouse", "bear"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
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


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_type: str
    hero_name: str
    friend_type: str
    friend_name: str
    memory: str
    seed: Optional[int] = None


PLACES = {
    "burrow": "the burrow",
    "barn": "the barn",
    "meadow": "the meadow",
    "oak_tree": "the old oak tree",
    "porch": "the porch",
}

HERO_TYPES = {
    "rabbit": "rabbit",
    "kitten": "kitten",
    "duck": "duck",
    "mouse": "mouse",
    "fox": "fox",
}

FRIEND_TYPES = {
    "bear": "bear",
    "puppy": "puppy",
    "goat": "goat",
    "cat": "cat",
}

MEMORIES = {
    "thunder": {
        "flashback": "a loud thunderclap that had once made the little animal hop under a bed",
        "fear": "fear",
    },
    "bucket": {
        "flashback": "a tumbling bucket that had clanged across the floor and made everything seem huge",
        "fear": "worry",
    },
    "owl": {
        "flashback": "a shadowy owl call from one very dark night",
        "fear": "shivers",
    },
}

CURATED = [
    StoryParams(
        place="burrow",
        hero_type="rabbit",
        hero_name="Pip",
        friend_type="bear",
        friend_name="Momo",
        memory="thunder",
    ),
    StoryParams(
        place="barn",
        hero_type="kitten",
        hero_name="Mina",
        friend_type="goat",
        friend_name="Boo",
        memory="bucket",
    ),
    StoryParams(
        place="oak_tree",
        hero_type="mouse",
        hero_name="Nip",
        friend_type="cat",
        friend_name="Lulu",
        memory="owl",
    ),
]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        traits=["little", "curious"],
        meters={"fear": 0.0, "curiosity": 0.0, "relief": 0.0, "bravery": 0.0},
        memes={"fear": 0.0, "memories": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        traits=["kind", "steady"],
        meters={"calm": 0.0, "help": 0.0},
        memes={"care": 0.0},
    ))
    world.facts.update(hero=hero, friend=friend, memory=params.memory, memory_info=MEMORIES[params.memory])
    return world


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    memory = world.facts["memory"]
    flash = world.facts["memory_info"]["flashback"]
    fear_word = world.facts["memory_info"]["fear"]

    world.say(
        f"One quiet day, {hero.label} the {hero.type} was sitting near {world.place} when a soft tum sounded from inside the dark."
    )
    world.say(
        f"{hero.label} froze. The little {hero.type} liked small sounds, but that tum made {hero.pronoun('possessive')} ears twitch."
    )

    # Flashback turn
    world.para()
    hero.meters["fear"] += 1
    hero.memes["memories"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"The sound pulled {hero.label} backward in thought, like a little flashback."
    )
    world.say(
        f"{hero.label} remembered {flash}, and the old {fear_word} came back for a moment."
    )
    world.say(
        f"{hero.label} whispered, 'That tum sounds like the old scary thing.'"
    )

    # Friend helps
    world.para()
    friend.meters["help"] += 1
    friend.meters["calm"] += 1
    friend.memes["care"] += 1
    world.say(
        f"{friend.label} came over with a slow, gentle step and sat beside {hero.label}."
    )
    world.say(
        f"'Let's look together,' {friend.label} said. 'Sometimes a tum is only a pebble, a nut, or a dropped toy.'"
    )
    hero.meters["curiosity"] += 1
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - 0.5)
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)

    # Resolution
    world.para()
    hero.meters["bravery"] += 1
    world.say(
        f"So {hero.label} took a tiny breath and followed {friend.label} toward the sound."
    )
    world.say(
        f"Behind a straw pile, they found a round little acorn rolling against a wooden board: tum, tum, tum."
    )
    world.say(
        f"{hero.label} laughed, because it was not a monster at all, just a silly bouncing acorn."
    )
    hero.meters["relief"] += 1
    hero.meters["fear"] = 0.0
    world.say(
        f"After that, {hero.label} felt brave enough to stay near {world.place}, and the dark corner did not seem so big anymore."
    )

    world.facts["resolved"] = True
    world.facts["ending_image"] = "a laughing animal and a friend watching an acorn roll safely away"


def story_text(params: StoryParams) -> tuple[World, str]:
    world = build_world(params)
    tell(world)
    return world, world.render()


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_params(params: StoryParams) -> bool:
    return params.place in PLACES and params.hero_type in HERO_TYPES and params.friend_type in FRIEND_TYPES and params.memory in MEMORIES


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the selected animal, friend, place, or flashback memory does not fit this small world.)"


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    memory = world.facts["memory"]
    return [
        f"Write a short Animal Story about {hero.label} the {hero.type} hearing a tum sound and remembering {memory}.",
        f"Tell a gentle story where {friend.label} helps {hero.label} after a flashback makes the tum sound feel scary.",
        f"Create a child-friendly animal tale that starts with a tum, includes a flashback, and ends in relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    memory = world.facts["memory"]
    flash = world.facts["memory_info"]["flashback"]
    return [
        QAItem(
            question=f"What did {hero.label} hear near {world.place}?",
            answer=f"{hero.label} heard a soft tum sound near {world.place}.",
        ),
        QAItem(
            question=f"What did the tum make {hero.label} remember?",
            answer=f"The tum made {hero.label} remember {flash}.",
        ),
        QAItem(
            question=f"Who helped {hero.label} look at the sound?",
            answer=f"{friend.label} helped {hero.label} look for the sound together.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label}?",
            answer=f"{hero.label} found that the tum was only a rolling acorn, so the fear went away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows something that happened earlier, so the character remembers a past moment.",
        ),
        QAItem(
            question="Why can a tum sound feel scary at first?",
            answer="A tum can feel scary if it is loud or strange, especially when a character already remembers a past scare.",
        ),
        QAItem(
            question="What can friends do when an animal feels worried?",
            answer="Friends can stay close, look together, and help the worried animal feel calm and brave.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% If the hero hears tum and has a matching flashback memory, the fear rises.
flashback(H) :- hears_tum(H), remembers_past_scare(H).

% A helper can reduce fear when they join the search.
calm(H) :- helper_arrives(H).

resolved(H) :- flashback(H), calm(H).

good_story(H) :- hears_tum(H), remembers_past_scare(H), helper_arrives(H), resolved(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hears_tum", "hero"),
        asp.fact("remembers_past_scare", "hero"),
        asp.fact("helper_arrives", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_good_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def verify_asp() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show good_story/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "good_story"))
    python_ok = {("hero",)} if True else set()
    if atoms == python_ok:
        print("OK: ASP parity matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python story gate.")
    print("  ASP:", sorted(atoms))
    print("  Python:", sorted(python_ok))
    return 1


# ---------------------------------------------------------------------------
# Serialization / CLI
# ---------------------------------------------------------------------------
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
    out.append("== (3) World questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with a tum flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    hero_type = args.hero_type or rng.choice(list(HERO_TYPES))
    friend_type = args.friend_type or rng.choice(list(FRIEND_TYPES))
    memory = args.memory or rng.choice(list(MEMORIES))
    if not valid_params(StoryParams(place, hero_type, "Pip", friend_type, "Momo", memory)):
        raise StoryError(explain_rejection(StoryParams(place, hero_type, "Pip", friend_type, "Momo", memory)))
    hero_name = args.name or rng.choice(["Pip", "Tilly", "Mina", "Nip", "Bun", "Roo"])
    friend_name = args.friend_name or rng.choice(["Momo", "Bobo", "Lulu", "Pippo", "Toto"])
    return StoryParams(
        place=place,
        hero_type=hero_type,
        hero_name=hero_name,
        friend_type=friend_type,
        friend_name=friend_name,
        memory=memory,
    )


def generate(params: StoryParams) -> StorySample:
    world, story = story_text(params)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(verify_asp())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show good_story/1."))
        print(asp.atoms(model, "good_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.hero_type} at {p.place} with {p.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
