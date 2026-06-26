#!/usr/bin/env python3
"""
A small storyworld about animals, a little flirt, a rhyming feel, and a bad ending.

The domain is intentionally tiny:
- one animal wants to flirt with another animal
- a shared setting gives the scene
- a small social mismatch creates tension
- the ending lands on rejection, embarrassment, or a lonely walk away

The prose is child-facing, but the emotional turn is a bad ending by design.
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

ANIMALS = {
    "cat": {"type": "cat", "sound": "meow", "gait": "soft paws"},
    "dog": {"type": "dog", "sound": "woof", "gait": "bouncy steps"},
    "duck": {"type": "duck", "sound": "quack", "gait": "waddling feet"},
    "fox": {"type": "fox", "sound": "yip", "gait": "quick toes"},
    "rabbit": {"type": "rabbit", "sound": "thump", "gait": "hoppy hops"},
    "panda": {"type": "panda", "sound": "hum", "gait": "slow steps"},
}

PLACES = {
    "meadow": {"place": "the meadow", "rhymes": "glow/show"},
    "pond": {"place": "the pond", "rhymes": "pond/pond"},
    "orchard": {"place": "the orchard", "rhymes": "peach/reach"},
    "barnyard": {"place": "the barnyard", "rhymes": "corn/charm"},
    "garden": {"place": "the garden", "rhymes": "bloom/room"},
}

GIFTS = {
    "flower": {"label": "flower", "phrase": "a tiny red flower", "mood": "sweet"},
    "berry": {"label": "berry", "phrase": "a shiny berry", "mood": "tasty"},
    "ribbon": {"label": "ribbon", "phrase": "a bright blue ribbon", "mood": "pretty"},
    "pebble": {"label": "pebble", "phrase": "a smooth little pebble", "mood": "plain"},
}

REACTIONS = {
    "shy": "looked down and stayed quiet",
    "startled": "blinked and stepped back",
    "refused": "said no and turned away",
    "mocked": "giggle-squeaked and pointed",
}

RHYME_LINES = {
    "flirt": [
        "The cat felt a spark in the soft green grass.",
        "It tried to sound sweet, but the words did not last.",
    ],
    "rejected": [
        "The duck heard the line and shook its small head.",
        "The moon looked pale as the flirty hope fled.",
    ],
    "lonely": [
        "So the little friend walked off through the blue evening glow.",
        "With a tiny sad sigh, it had nowhere to go.",
    ],
}

ASP_RULES = r"""
flirt_attempt(F) :- flirt(F).
bad_end(F) :- flirt_attempt(F), rejected(F).
bad_end(F) :- flirt_attempt(F), mocked(F).
"""

@dataclass
class Creature:
    id: str
    kind: str = "animal"
    species: str = "animal"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    key: str
    label: str
    rhyme_pair: str = ""


@dataclass
class Gift:
    key: str
    label: str
    phrase: str
    mood: str = ""


@dataclass
class StoryParams:
    place: str
    suitor: str
    target: str
    gift: str
    reaction: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Creature] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Creature) -> Creature:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _adjective_line(suitor: Creature, target: Creature, gift: Gift) -> str:
    return f"The {suitor.species} had a soft-heart plan and brought {gift.phrase}."


def _flirt_line(suitor: Creature, target: Creature, gift: Gift, place: Place) -> str:
    return (
        f"By {place.label}, the {suitor.species} smiled and tried to flirt: "
        f'"{target.label}, you are my moonbeam bloom!"'
    )


def _response_line(reaction: str, target: Creature) -> str:
    return f"The {target.species} {REACTIONS[reaction]}."


def _bad_ending_line(reaction: str, suitor: Creature) -> str:
    if reaction == "mocked":
        return f"The joke stung, and the {suitor.species} went home with a wobble in its heart."
    if reaction == "refused":
        return f"No one cheered, and the {suitor.species} walked away with droopy ears."
    return f"The moment felt small and awkward, and the {suitor.species} had no brave reply."


def tell(params: StoryParams) -> World:
    place = Place(**PLACES[params.place])
    world = World(place)
    suitor_data = ANIMALS[params.suitor]
    target_data = ANIMALS[params.target]
    gift_data = GIFTS[params.gift]

    suitor = world.add(Creature(id="suitor", species=params.suitor, label=params.suitor))
    target = world.add(Creature(id="target", species=params.target, label=params.target))
    gift = Gift(key=params.gift, **gift_data)

    suitor.memes["hope"] = 1.0
    suitor.memes["flirt"] = 1.0
    target.memes["guarded"] = 1.0

    world.say(
        f"In {place.label}, a {suitor.species} with {suitor_data['gait']} saw a {target.species} "
        f"near the water and felt brave."
    )
    world.say(_adjective_line(suitor, target, gift))
    world.say(_flirt_line(suitor, target, gift, place))
    world.para()
    world.say(
        f"The line rhymed a little, but it was still too bold for the quiet {target.species}."
    )
    world.say(_response_line(params.reaction, target))
    world.para()
    world.say(_bad_ending_line(params.reaction, suitor))
    if params.reaction == "mocked":
        world.say("The meadow stayed bright, but the feeling was not bright at all.")

    world.facts.update(
        suitor=suitor,
        target=target,
        gift=gift,
        place=place,
        reaction=params.reaction,
        bad_end=True,
        flirt=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story in a gentle rhyming style about a {f["suitor"].species} trying to flirt with a {f["target"].species} in {f["place"].label}.',
        f"Tell an animal story where a {f['suitor'].species} brings {f['gift'].phrase} and gets rejected.",
        f"Write a tiny rhyming story with a bad ending about animals at {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Which animal tried to flirt in the story?",
            answer=f"The {f['suitor'].species} tried to flirt with the {f['target'].species}.",
        ),
        QAItem(
            question=f"Where did the animals meet?",
            answer=f"They met in {f['place'].label}.",
        ),
        QAItem(
            question=f"What did the flirting animal bring?",
            answer=f"It brought {f['gift'].phrase}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly, with rejection and a lonely feeling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is flirting?",
            answer="Flirting is a playful way of showing special liking to someone.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like moon and tune.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things do not work out happily for the main character.",
        ),
        QAItem(
            question=f"Is the {f['gift'].label} a very serious gift?",
            answer=f"No, it is a small, simple gift, and in this story it was meant to seem sweet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.species}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.label}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with flirt, rhyme, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suitor", choices=ANIMALS)
    ap.add_argument("--target", choices=ANIMALS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--reaction", choices=REACTIONS)
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
    suitor = args.suitor or rng.choice(list(ANIMALS))
    target = args.target or rng.choice([a for a in ANIMALS if a != suitor])
    gift = args.gift or rng.choice(list(GIFTS))
    reaction = args.reaction or rng.choice(list(REACTIONS))
    if suitor == target:
        raise StoryError("The suitor and target must be different animals.")
    return StoryParams(place=place, suitor=suitor, target=target, gift=gift, reaction=reaction)


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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for r in REACTIONS:
        lines.append(asp.fact("reaction", r))
        if r in {"rejected", "mocked"}:
            lines.append(asp.fact("bad_end_reaction", r))
    return "\n".join(lines)


ASP_RULES = r"""
flirt_story(P,S,T,G,R) :- place(P), animal(S), animal(T), S != T, gift(G), bad_end_reaction(R).
show_flirt(P,S,T,G,R) :- flirt_story(P,S,T,G,R).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show show_flirt/5."))
    return sorted(set(asp.atoms(model, "show_flirt")))


def asp_verify() -> int:
    py = []
    for p in PLACES:
        for s in ANIMALS:
            for t in ANIMALS:
                if s == t:
                    continue
                for g in GIFTS:
                    for r in ("rejected", "mocked"):
                        py.append((p, s, t, g, r))
    cl = asp_valid()
    if set(py) == set(cl):
        print(f"OK: ASP matches Python ({len(cl)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


CURATED = [
    StoryParams(place="meadow", suitor="cat", target="duck", gift="flower", reaction="rejected"),
    StoryParams(place="pond", suitor="fox", target="duck", gift="berry", reaction="mocked"),
    StoryParams(place="garden", suitor="rabbit", target="cat", gift="ribbon", reaction="refused"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show show_flirt/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} flirt/bad-ending combinations:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
