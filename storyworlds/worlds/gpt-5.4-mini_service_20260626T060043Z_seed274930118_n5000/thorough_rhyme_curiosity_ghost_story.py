#!/usr/bin/env python3
"""
storyworlds/worlds/thorough_rhyme_curiosity_ghost_story.py
===========================================================

A small, standalone storyworld about a curious child, a ghostly rhyme,
and a thorough search that turns fear into understanding.

Premise:
- A child hears a spooky rhyme in an old house.
- Curiosity pulls them toward a hidden sound in the dark.
- The ghost is not mean; it is lonely, and the child's thorough attention
  helps uncover what it needs.
- The ending proves the change with a concrete, calm image.

This world is intentionally narrow: only a few compatible stories are allowed,
so every generated sample has a clear setup, tension, turn, and resolution.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
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
class Place:
    id: str
    label: str
    dark: bool = True
    echoes: bool = False


@dataclass
class Rhyme:
    id: str
    verse: str
    clue: str
    scare: str
    reveal: str
    comfort: str
    keyword: str = "rhyme"


@dataclass
class Ghost:
    id: str
    label: str
    sound: str
    need: str
    hidden_item: str


@dataclass
class StoryParams:
    place: str
    rhyme: str
    ghost: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        return World(
            place=self.place,
            entities=copy.deepcopy(self.entities),
            facts=dict(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(id="attic", label="the attic", dark=True, echoes=True),
    "hall": Place(id="hall", label="the old hall", dark=True, echoes=True),
    "library": Place(id="library", label="the dusty library", dark=True, echoes=False),
    "porch": Place(id="porch", label="the moonlit porch", dark=True, echoes=True),
}

RHYMES = {
    "whisper_steps": Rhyme(
        id="whisper_steps",
        verse="When the floorboards sigh, three whispers rise.",
        clue="three soft taps near the stairs",
        scare="the taps made the child freeze",
        reveal="the taps were pointing to a loose latch",
        comfort="the room felt less spooky once the latch was found",
    ),
    "bell_song": Rhyme(
        id="bell_song",
        verse="If the bell rings once, look for the sunken tongue.",
        clue="a small bell sound under the rug",
        scare="the bell sounded like a warning",
        reveal="the bell was tied to a key in a drawer",
        comfort="the key made the hidden box easy to open",
    ),
    "lantern_line": Rhyme(
        id="lantern_line",
        verse="Follow the glow, and the lost will show.",
        clue="a pale glow by the cabinet",
        scare="the glow looked like a ghost face",
        reveal="the glow was only moonlight on glass",
        comfort="moonlight made the hallway seem kind again",
    ),
}

GHOSTS = {
    "hush_ghost": Ghost(
        id="hush_ghost",
        label="the hush ghost",
        sound="a soft hush-hush sound",
        need="its lost songbook",
        hidden_item="songbook",
    ),
    "bell_ghost": Ghost(
        id="bell_ghost",
        label="the bell ghost",
        sound="a little tinkling bell",
        need="its missing key",
        hidden_item="key",
    ),
    "lamp_ghost": Ghost(
        id="lamp_ghost",
        label="the lamp ghost",
        sound="a trembling glow",
        need="its lantern shade",
        hidden_item="shade",
    ),
}

CHILD_NAMES = ["Mia", "Nora", "Theo", "Ben", "Lina", "Eli", "Ada", "Ivy"]
TRAITS = ["curious", "careful", "brave", "quiet", "thoughtful"]


# ---------------------------------------------------------------------------
# ASP twin + reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- room(P).
rhyme(R) :- verse(R,_).
ghost(G) :- need(G,_).

compatible(P,R,G) :- room(P), verse(R,_), need(G,_), echoes(P), dark(P).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("room", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.echoes:
            lines.append(asp.fact("echoes", pid))
    for rid, r in RHYMES.items():
        lines.append(asp.fact("verse", rid, r.verse))
        lines.append(asp.fact("clue", rid, r.clue))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("need", gid, g.need))
        lines.append(asp.fact("sound", gid, g.sound))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def reasonableness_gate(place: str, rhyme: str, ghost: str) -> None:
    p, r, g = PLACES[place], RHYMES[rhyme], GHOSTS[ghost]
    if not (p.dark and p.echoes):
        raise StoryError("This story needs a dark, echoing place for the spooky clue to feel real.")
    if not r.verse or not g.need:
        raise StoryError("The rhyme and ghost must both have something concrete to uncover.")
    # Python gate is simple; ASP must agree in verify mode.


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def _sneakiness(world: World, child: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["tension"] = child.memes.get("tension", 0) + 1
    world.say(
        f"{child.id} heard a strange little rhyme and felt curiosity tugging at "
        f"{child.pronoun('possessive')} sleeve."
    )


def _echo(world: World, rhyme: Rhyme) -> None:
    world.say(f'In the dark, the words seemed to return: "{rhyme.verse}"')


def _thorough_search(world: World, child: Entity, ghost: Ghost, rhyme: Rhyme) -> None:
    child.memes["thorough"] = child.memes.get("thorough", 0) + 1
    child.meters["searching"] = child.meters.get("searching", 0) + 1
    world.say(
        f"{child.id} did not run away. {child.pronoun().capitalize()} looked under "
        f"the rug, behind the chair, and along every board, very thoroughly."
    )
    world.say(
        f"At last, {child.id} found the clue: {rhyme.clue}. "
        f"That was enough to show {ghost.label} was not hunting anyone at all."
    )
    world.say(f"{rhyme.reveal.capitalize()}.")
    world.say(
        f"{ghost.label} only wanted {ghost.need}, and the room felt softer after that."
    )


def _comfort(world: World, child: Entity, ghost: Ghost, rhyme: Rhyme) -> None:
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["fear"] = 0
    ghost_ent = world.get(ghost.id)
    ghost_ent.memes["lonely"] = 0
    ghost_ent.memes["grateful"] = 1
    world.say(
        f"{child.id} smiled and helped {ghost.label} look for the lost thing. "
        f"Then the haunting sound turned into a thankful little hum."
    )
    world.say(
        f"By the end, {rhyme.comfort}, and {child.id} could hear only the gentle hush of the house."
    )


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params.place, params.rhyme, params.ghost)
    place = PLACES[params.place]
    rhyme = RHYMES[params.rhyme]
    ghost = GHOSTS[params.ghost]
    world = World(place=place)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        meters={},
        memes={"curiosity": 0, "fear": 0, "tension": 0, "thorough": 0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        meters={},
        memes={},
    ))
    g = world.add(Entity(
        id=ghost.id,
        kind="character",
        type="ghost",
        label=ghost.label,
        owner=None,
        caretaker=None,
        location=place.id,
        meters={},
        memes={"lonely": 1, "spooky": 1},
    ))
    item = world.add(Entity(
        id=ghost.hidden_item,
        kind="thing",
        type=ghost.hidden_item,
        label=ghost.hidden_item,
        phrase=f"a lost {ghost.hidden_item}",
        owner=ghost.id,
        location=place.id,
    ))

    world.facts.update(child=child, parent=parent, ghost=ghost, rhyme=rhyme, item=item, place=place)

    world.say(
        f"{child.id} went with {child.pronoun('possessive')} {parent.label} to {place.label}."
    )
    world.say(
        f"{child.id} was a curious child, and {child.pronoun('subject')} liked to listen for strange sounds."
    )
    world.say(f"That night, {ghost.label} made {ghost.sound} from somewhere in the dark.")
    world.para()
    _sneakiness(world, child)
    _echo(world, rhyme)
    world.say(f"{rhyme.scare.capitalize()}.")
    world.para()
    world.say(
        f"{child.id} took a breath and decided to be thorough instead of scared."
    )
    _thorough_search(world, child, ghost, rhyme)
    world.para()
    _comfort(world, child, ghost, rhyme)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, ghost, rhyme = f["child"], f["ghost"], f["rhyme"]
    return [
        f'Write a ghost story for young children that includes the word "{rhyme.keyword}" and a very thorough search.',
        f"Tell a gentle spooky story about {child.id}, who is curious enough to follow {ghost.label} and solve the mystery.",
        f"Write a short story in an eerie but comforting style where a rhyme leads a child to discover what a ghost really needs.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, rhyme, place = f["child"], f["ghost"], f["rhyme"], f["place"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Why did {child.id} go into {place.label}?",
            answer=f"{child.id} went into {place.label} with {child.pronoun('possessive')} parent because the sound there was strange and {child.pronoun('subject')} wanted to find out what made it.",
        ),
        QAItem(
            question=f"What made {child.id} feel curious in the dark room?",
            answer=f"{rhyme.verse} made {child.id} feel curious, because it sounded like a secret waiting to be understood.",
        ),
        QAItem(
            question=f"What did {child.id} do to stay brave?",
            answer=f"{child.id} searched very thoroughly, looking under things and behind things until the clue made sense.",
        ),
        QAItem(
            question=f"What did {ghost.label} really want?",
            answer=f"{ghost.label} only wanted {ghost.need}, not to frighten anyone.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ghost, rhyme = f["ghost"], f["rhyme"]
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little pattern of words where the sounds at the ends match or repeat in a playful way.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more about something and asking questions or looking closely.",
        ),
        QAItem(
            question="What does it mean to be thorough?",
            answer="Being thorough means paying close attention and not missing small details.",
        ),
        QAItem(
            question=f"What kind of sound did {ghost.label} make?",
            answer=f"{ghost.label} made {ghost.sound}.",
        ),
        QAItem(
            question="Why can an old house feel spooky?",
            answer="An old house can feel spooky because it is dark, quiet, and full of creaks, shadows, and echoes.",
        ),
    ]


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
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(CHILD_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.rhyme and args.rhyme not in RHYMES:
        raise StoryError("Unknown rhyme.")
    if args.ghost and args.ghost not in GHOSTS:
        raise StoryError("Unknown ghost.")
    place = args.place or rng.choice(list(PLACES))
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    ghost = args.ghost or rng.choice(list(GHOSTS))
    reasonableness_gate(place, rhyme, ghost)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        rhyme=rhyme,
        ghost=ghost,
        child_name=name,
        child_gender=gender,
        parent_type=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    asp_set = set(asp_compatible())
    py_set = {
        (p, r, g)
        for p in PLACES
        for r in RHYMES
        for g in GHOSTS
        if PLACES[p].dark and PLACES[p].echoes
    }
    if asp_set == py_set:
        print(f"OK: ASP matches Python gate ({len(py_set)} compatible triples).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with rhyme and curiosity.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
    ap.add_argument("--ghost", choices=sorted(GHOSTS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


CURATED = [
    StoryParams(place="attic", rhyme="whisper_steps", ghost="hush_ghost", child_name="Mia", child_gender="girl", parent_type="mother"),
    StoryParams(place="hall", rhyme="bell_song", ghost="bell_ghost", child_name="Theo", child_gender="boy", parent_type="father"),
    StoryParams(place="library", rhyme="lantern_line", ghost="lamp_ghost", child_name="Ivy", child_gender="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        triples = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(triples)} compatible triples:")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.child_name}: {p.place} / {p.rhyme} / {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
