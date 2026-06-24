#!/usr/bin/env python3
"""
storyworlds/worlds/fate_kindness_humor_magic_ghost_story.py
===========================================================

A small, child-facing ghost-story world with fate, kindness, humor, and magic.

Premise:
- A lonely ghost lingers in an old place because of a tiny fate-bound wish.
- A gentle child notices the ghost, uses kindness and humor, and a little magic
  helps them finish what the ghost could not.

The simulation keeps track of:
- physical meters: glow, chill, dust, light, open, calm
- emotional memes: fear, kindness, humor, hope, relief, curiosity, haunting

The prose is built from state changes, not from a frozen template with swapped
nouns. The ending image proves what changed.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    spooky: bool = True
    magic: bool = True
    contains: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    effect: str
    target: str


@dataclass
class StoryParams:
    place: str
    relic: str
    child_name: str
    child_gender: str
    helper_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "attic": Place(id="attic", label="the attic", spooky=True, magic=True),
    "library": Place(id="library", label="the old library", spooky=True, magic=True),
    "garden": Place(id="garden", label="the moonlit garden", spooky=True, magic=True),
}

RELICS = {
    "bell": Relic(id="bell", label="a little bell", phrase="a silver bell with a cracked ribbon", effect="ring", target="ghost"),
    "lantern": Relic(id="lantern", label="a lantern", phrase="a lantern with a blue glass door", effect="shine", target="dark"),
    "puzzle": Relic(id="puzzle", label="a puzzle box", phrase="a tiny puzzle box with three sleepy stars", effect="open", target="secret"),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Maya", "Eve", "Sage"]
BOY_NAMES = ["Owen", "Finn", "Noah", "Theo", "Eli", "Leo", "Ben"]


@dataclass
class Spell:
    id: str
    label: str
    verb: str
    effect: str


SPELLS = {
    "giggle": Spell(id="giggle", label="a giggle spell", verb="giggle", effect="humor"),
    "kind": Spell(id="kind", label="a kindness charm", verb="offer a gentle hand", effect="kindness"),
    "glow": Spell(id="glow", label="a glow charm", verb="make a soft light", effect="magic"),
}

CURATED = [
    StoryParams(place="attic", relic="bell", child_name="Mina", child_gender="girl", helper_kind="giggle"),
    StoryParams(place="library", relic="puzzle", child_name="Owen", child_gender="boy", helper_kind="kind"),
    StoryParams(place="garden", relic="lantern", child_name="Ivy", child_gender="girl", helper_kind="glow"),
]


@dataclass
class Ghost:
    entity: Entity
    fate: str = "must_finish"
    wish: str = "hear a laugh"
    bound_to: str = "place"
    freed: bool = False


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        meters={"light": 0.0, "calm": 0.0},
        memes={"curiosity": 1.0, "fear": 0.0, "kindness": 0.0, "humor": 0.0, "hope": 0.0, "relief": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="ghost",
        type="ghost",
        label="the ghost",
        meters={"chill": 2.0, "glow": 0.2, "dust": 1.0},
        memes={"haunting": 2.0, "fear": 1.0, "sadness": 1.0, "hope": 0.0},
    ))
    relic = world.add(Entity(
        id=params.relic,
        kind="thing",
        type="relic",
        label=RELICS[params.relic].label,
        phrase=RELICS[params.relic].phrase,
        owner=ghost.id,
        meters={"light": 0.0},
        memes={"mystery": 1.0},
    ))
    spell = world.add(Entity(
        id=params.helper_kind,
        kind="thing",
        type="spell",
        label=SPELLS[params.helper_kind].label,
        phrase=SPELLS[params.helper_kind].label,
        owner=child.id,
        meters={"magic": 1.0},
        memes={"kindness": 1.0 if params.helper_kind == "kind" else 0.0,
               "humor": 1.0 if params.helper_kind == "giggle" else 0.0,
               "magic": 1.0 if params.helper_kind == "glow" else 0.5},
    ))

    world.facts.update(child=child, ghost=ghost, relic=relic, spell=spell, params=params)
    return world


def intro(world: World) -> None:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    world.say(f"{child.id} came to {world.place.label} on a quiet night.")
    world.say(f"There, {ghost.pronoun('subject')} was: {ghost.label}, pale as mist and lonely as a window left open.")


def fate_call(world: World) -> None:
    ghost = world.facts["ghost"]
    relic: Entity = world.facts["relic"]
    ghost.memes["hope"] += 1.0
    world.say(
        f"The old fate of {world.place.label} kept {ghost.label} waiting beside {relic.phrase}, "
        f"because one tiny wish had never been finished."
    )


def child_notices(world: World) -> None:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    child.memes["curiosity"] += 1.0
    child.memes["fear"] += 0.5
    world.say(
        f"{child.id} did not run away. {child.pronoun('subject').capitalize()} noticed the soft chill, "
        f"then noticed that {ghost.pronoun('subject')} looked more sad than scary."
    )


def helper_act(world: World) -> None:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    spell: Entity = world.facts["spell"]
    params: StoryParams = world.facts["params"]
    spell_def = SPELLS[params.helper_kind]

    if params.helper_kind == "giggle":
        child.memes["humor"] += 1.0
        child.memes["kindness"] += 0.5
        ghost.memes["hope"] += 1.0
        world.say(
            f"{child.id} tried {spell_def.label}. {child.pronoun('subject').capitalize()} made a tiny joke about "
            f"a bat wearing slippers, and even the dusty rafters seemed to smile."
        )
    elif params.helper_kind == "kind":
        child.memes["kindness"] += 1.0
        ghost.memes["hope"] += 1.2
        world.say(
            f"{child.id} chose {spell_def.label}. {child.pronoun('subject').capitalize()} held out a gentle hand "
            f"and said it was all right to be lonely."
        )
    else:
        child.meters["light"] += 1.0
        ghost.meters["glow"] += 1.0
        world.say(
            f"{child.id} whispered the words of {spell_def.label}. A warm little light lifted from the floor "
            f"and made the cobwebs look like silver threads."
        )


def ghost_turn(world: World) -> None:
    ghost = world.facts["ghost"]
    child = world.facts["child"]
    relic: Entity = world.facts["relic"]
    ghost.metes = ghost.meters
    if child.memes["humor"] >= THRESHOLD:
        ghost.memes["fear"] = max(0.0, ghost.memes["fear"] - 0.6)
        ghost.memes["hope"] += 0.7
        world.say(
            f"The ghost let out a surprised little chuckle. It sounded like wind tapping a spoon against glass."
        )
    if child.memes["kindness"] >= THRESHOLD:
        ghost.memes["sadness"] = max(0.0, ghost.memes.get("sadness", 0.0) - 0.8)
        world.say(
            f"That kindness reached the ghost like a blanket on a cold night."
        )
    if child.meters["light"] >= THRESHOLD or world.facts["spell"].type == "spell":
        ghost.meters["glow"] += 0.8
        relic.meters["light"] += 1.0
        world.say(
            f"The little relic began to shine, and the ghost remembered the lost wish tied to it."
        )


def resolve_fate(world: World) -> None:
    ghost = world.facts["ghost"]
    child = world.facts["child"]
    relic: Entity = world.facts["relic"]

    ghost.memes["hope"] += 1.0
    child.memes["relief"] += 1.0

    if relic.id == "bell":
        world.say(
            f"{child.id} gave the bell a soft ring. The sound floated through {world.place.label} like a silver fish."
        )
    elif relic.id == "puzzle":
        world.say(
            f"{child.id} turned the puzzle box over and found the last star-shaped piece hiding underneath."
        )
    else:
        world.say(
            f"{child.id} opened the lantern door, and the blue glass made the shadows look kindly instead of sharp."
        )

    ghost.memes["haunting"] = 0.0
    ghost.memes["relief"] = 1.0
    ghost.meters["chill"] = 0.0
    ghost.freed = True

    world.say(
        f"At last, the ghost's fate changed. {ghost.pronoun('subject').capitalize()} was not stuck anymore, "
        f"because {child.id} had answered the wish with kindness, humor, and a touch of magic."
    )


def ending(world: World) -> None:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    world.para()
    if ghost.freed:
        world.say(
            f"By the end, {world.place.label} felt warm and gentle. {ghost.pronoun('subject').capitalize()} drifted up "
            f"like moonlit steam, smiling at {child.id}, and {child.id} smiled back."
        )
        world.say(
            f"The old room was still spooky, but it was no longer lonely."
        )
    else:
        world.say(
            f"The room stayed quiet, and the ghost still waited."
        )


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    fate_call(world)
    child_notices(world)
    helper_act(world)
    ghost_turn(world)
    resolve_fate(world)
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a small ghost story for a young child in {PLACES[p.place].label} about fate and a lonely ghost.",
        f"Tell a spooky-but-kind story where {p.child_name} uses {SPELLS[p.helper_kind].label} to help a ghost finish an old wish.",
        f"Write a gentle story with humor, kindness, and magic that ends with the ghost no longer haunting the place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    ghost: Entity = world.facts["ghost"]
    relic: Entity = world.facts["relic"]
    spell: Entity = world.facts["spell"]

    return [
        QAItem(
            question=f"Who was the story about in {PLACES[p.place].label}?",
            answer=f"It was about {child.id}, a child who met the ghost in {PLACES[p.place].label}.",
        ),
        QAItem(
            question=f"What was the ghost waiting for?",
            answer=f"The ghost was waiting beside {relic.phrase} because an old fate-bound wish was still unfinished.",
        ),
        QAItem(
            question=f"What helped {child.id} deal with the ghost?",
            answer=f"{spell.label} helped, along with {('a funny joke' if p.helper_kind == 'giggle' else 'a gentle act of kindness' if p.helper_kind == 'kind' else 'a soft magical light')}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The ghost was freed, the chill faded, and {child.id} was smiling in the warm, quiet room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fate?",
            answer="Fate is the idea that some events are meant to happen, even if the people in the story do not see it right away.",
        ),
        QAItem(
            question="What does kindness do?",
            answer="Kindness helps by making another person or creature feel safe, seen, and cared for.",
        ),
        QAItem(
            question="Why can humor help?",
            answer="Humor can help because a small joke or laugh can make fear feel less heavy.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is a special power that can change what is possible, like making light glow or opening a sealed thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v:.1f}' for k, v in e.meters.items())}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v:.1f}' for k, v in e.memes.items())}}}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fate-and-kindness ghost story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-kind", choices=SPELLS)
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
    relic = args.relic or rng.choice(list(RELICS))
    helper_kind = args.helper_kind or rng.choice(list(SPELLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if args.gender and args.name is None:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, relic=relic, child_name=name, child_gender=gender, helper_kind=helper_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


ASP_RULES = r"""
place(P) :- setting(P).
relic(R) :- relic_kind(R).
helper(H) :- spell(H).

spooky_story(P,R,H) :- place(P), relic(R), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for rid in RELICS:
        lines.append(asp.fact("relic_kind", rid))
    for hid in SPELLS:
        lines.append(asp.fact("spell", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show spooky_story/3."))
    atoms = set(asp.atoms(model, "spooky_story"))
    expected = {(p, r, h) for p in PLACES for r in RELICS for h in SPELLS}
    if atoms == expected:
        print(f"OK: ASP gate matches Python registry product ({len(expected)} combos).")
        return 0
    print("MISMATCH between ASP and Python registry product.")
    print("only in asp:", sorted(atoms - expected))
    print("only in python:", sorted(expected - atoms))
    return 1


def asp_valid_triples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show spooky_story/3."))
    return sorted(set(asp.atoms(model, "spooky_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show spooky_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_triples()
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = CURATED
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
