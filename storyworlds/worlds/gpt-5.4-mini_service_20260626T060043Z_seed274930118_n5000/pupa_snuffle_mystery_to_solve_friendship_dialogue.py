#!/usr/bin/env python3
"""
A small storyworld about a child, a friendly ghost mystery, and a snuffling clue.

Seed premise:
- A child hears a pupa-like whisper and a snuffle in a quiet old place.
- A mystery must be solved through friendship and dialogue.
- The tone is ghost-story flavored, but warm and child-friendly.

The world model tracks:
- physical meters: sound, chill, glow, trust, clue, dust
- emotional memes: fear, curiosity, friendship, relief, bravery

The story is built from state changes:
- a quiet place makes small sounds noticeable
- a mysterious snuffle raises curiosity and fear
- the child speaks gently, making a ghostly friend appear
- the friend helps reveal the hidden cause
- the ending proves the mystery was solved and friendship grew
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    mood: str
    quiet: bool = True
    hidden_spots: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    clue_word: str
    sound_word: str
    source: str
    reveal: str
    solve_method: str
    setting_hint: str = ""


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    mystery: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, mystery: Mystery) -> None:
        self.place = place
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace_notes: list[str] = []

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
        w = World(self.place, self.mystery)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(name="the attic", mood="dusty", hidden_spots=["under the trunk", "behind the old curtain"]),
    "garden": Place(name="the garden", mood="moonlit", hidden_spots=["near the stone path", "under the rose bush"]),
    "hallway": Place(name="the hallway", mood="echoing", hidden_spots=["by the umbrella stand", "inside the coat nook"]),
    "shed": Place(name="the shed", mood="creaky", hidden_spots=["behind the rake", "under the shelf"]),
}

MYSTERIES = {
    "pupa": Mystery(
        clue_word="pupa",
        sound_word="snuffle",
        source="a tiny moth tucked inside a folded blanket",
        reveal="a sleepy moth pupal case that was making the strange little snuffle when the blanket moved",
        solve_method="gently open the blanket and look together",
        setting_hint="soft things and dusty corners",
    ),
    "snuffle": Mystery(
        clue_word="snuffle",
        sound_word="snuffle",
        source="a lost kitten hiding behind a basket",
        reveal="a frightened kitten with a snuffly nose, warm and safe at last",
        solve_method="speak softly and follow the sound",
        setting_hint="quiet places and careful listening",
    ),
}

CHILD_NAMES = ["Mina", "Noah", "Lina", "Theo", "Maya", "Eli", "Nora", "Finn"]
TRAITS = ["curious", "brave", "gentle", "listening", "careful", "kind"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def _inc(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(place, mystery)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        traits=["little", random.choice(TRAITS)],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        traits=["patient"],
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        label="the friendly ghost",
        traits=["soft", "glowy"],
    ))
    clue = world.add(Entity(
        id="Clue",
        kind="thing",
        type="clue",
        label=mystery.clue_word,
        phrase=f"a small {mystery.clue_word} clue",
    ))
    hidden = world.add(Entity(
        id="Hidden",
        kind="thing",
        type="mystery",
        label=mystery.source,
        phrase=mystery.reveal,
    ))

    # Initial state
    _mem(child, "curiosity", 1)
    _mem(child, "fear", 0.5)
    _inc(world.add(Entity(id="Room", kind="thing", type="place", label=place.name)).meters, "quiet" if place.quiet else "noise", 1)  # type: ignore

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        clue=clue,
        hidden=hidden,
        mystery=mystery,
        place=place,
    )
    return world


def setting_line(world: World) -> str:
    if world.place.name == "the attic":
        return "The attic was dusty and soft with old boxes, where even a tiny sound seemed to float."
    if world.place.name == "the garden":
        return "The garden was moonlit and still, with leaves shining like little silver hands."
    if world.place.name == "the hallway":
        return "The hallway echoed in a hush, and every step seemed to carry a secret."
    return "The shed was creaky and dark, with tools waiting like sleepy shadows."


def introduce(world: World) -> None:
    c = world.facts["child"]
    p = world.facts["parent"]
    world.say(f"{c.id} was a little {c.type} who liked to listen carefully in quiet places.")
    world.say(f"{c.id} lived with {p.label} near {world.place.name}, and {c.id} loved stories about friendly ghosts.")
    world.say(setting_line(world))


def first_whisper(world: World) -> None:
    c = world.facts["child"]
    m = world.facts["mystery"]
    _mem(c, "curiosity", 1)
    _mem(c, "fear", 1)
    _inc(c, "sound", 1)
    world.say(f"Then {c.id} heard a small {m.sound_word} from the shadows.")
    world.say(f"It was not a scary roar or a big bang, just a tiny, fuzzy sound that made {c.id} look around twice.")


def ask_question(world: World) -> None:
    c = world.facts["child"]
    p = world.facts["parent"]
    _mem(c, "bravery", 1)
    _mem(c, "friendship", 0.5)
    world.say(f'"Did you hear that?" {c.id} asked {p.label}.')
    world.say(f'{p.label} listened too, but the sound was hidden somewhere small, so {c.id} had to keep asking gentle questions.')


def ghost_appears(world: World) -> None:
    c = world.facts["child"]
    g = world.facts["ghost"]
    _inc(g, "glow", 1)
    _mem(c, "fear", -0.5)
    _mem(c, "friendship", 1)
    world.say(f"A soft glow drifted out from the dark, and the friendly ghost appeared without a single scary cry.")
    world.say(f'{g.label.capitalize()} gave {c.id} a tiny wave and said, "I can help if you speak kindly and listen closely."')


def dialogue_search(world: World) -> None:
    c = world.facts["child"]
    g = world.facts["ghost"]
    m = world.facts["mystery"]
    world.say(f'"What is the sound?" {c.id} whispered.')
    world.say(f'"Follow the {m.clue_word}," {g.label} said. "It hides near {random.choice(world.place.hidden_spots)}."')
    _inc(c, "clue", 1)
    _mem(c, "curiosity", 1)
    world.say(f"{c.id} tiptoed where the ghost pointed, and the whispering clue grew clearer with every careful step.")


def solve_mystery(world: World) -> None:
    c = world.facts["child"]
    p = world.facts["parent"]
    g = world.facts["ghost"]
    m = world.facts["mystery"]
    hidden = world.facts["hidden"]
    _inc(c, "clue", 1)
    _mem(c, "relief", 1)
    _mem(c, "friendship", 1)
    world.say(f"{c.id} and {g.label} worked together and found the hiding place.")
    world.say(f"There was {hidden.phrase}, and the strange little {m.sound_word} finally made sense.")
    world.say(f"It had only been {m.source}, tucked away and waiting to be noticed.")
    world.say(f"{p.label} smiled, because the mystery was not dangerous at all; it just needed someone gentle enough to solve it.")


def ending_image(world: World) -> None:
    c = world.facts["child"]
    g = world.facts["ghost"]
    p = world.facts["parent"]
    m = world.facts["mystery"]
    _inc(c, "glow", 1)
    _mem(c, "fear", -1)
    _mem(c, "friendship", 1)
    world.say(f'At the end, {c.id} was laughing softly instead of shivering.')
    world.say(f'{g.label} floated beside {c.id} like a silver lantern, and together they looked at the solved mystery with bright eyes.')
    world.say(f"The little {m.clue_word} clue was no longer strange. It was only a sign that a new friend had been waiting in the dark.")


def tell_story(world: World) -> World:
    introduce(world)
    world.para()
    first_whisper(world)
    ask_question(world)
    world.para()
    ghost_appears(world)
    dialogue_search(world)
    world.para()
    solve_mystery(world)
    ending_image(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is interesting when a child hears the clue sound and feels fear and curiosity.
interesting(C) :- hears(C,S), clue_sound(S), curiosity(C), fear(C).

% A friendly ghost can appear when the place is quiet enough and the child speaks kindly.
ghost_appears(C,G) :- quiet_place(P), in_place(C,P), kind_speaking(C), ghost(G).

% The mystery is solved when the child and ghost use dialogue to find the hidden source.
solved(C,M) :- dialogue(C,G), ghost_appears(C,G), mystery(M), found_source(C,M).

% Friendship grows after a solved mystery.
friendship_grows(C) :- solved(C,_), solved_with_ghost(C).

#show interesting/1.
#show ghost_appears/2.
#show solved/2.
#show friendship_grows/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet_place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_word", m.clue_word))
        lines.append(asp.fact("sound", m.sound_word))
        lines.append(asp.fact("clue_sound", m.sound_word))
    lines.append(asp.fact("ghost", "Ghost"))
    lines.append(asp.fact("kind_speaking", "Hero"))
    lines.append(asp.fact("in_place", "Hero", "attic"))
    lines.append(asp.fact("dialogue", "Hero", "Ghost"))
    lines.append(asp.fact("found_source", "Hero", "pupa"))
    lines.append(asp.fact("solved_with_ghost", "Hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/2."))
    atoms = set(asp.atoms(model, "solved"))
    if ("Hero", "pupa") in atoms:
        print("OK: ASP twin produces the expected solved mystery.")
        return 0
    print("MISMATCH: ASP twin did not solve the mystery as expected.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    m = f["mystery"]
    return [
        f'Write a short ghost-story for a child who hears the word "{m.clue_word}" and a small "{m.sound_word}" in a quiet place.',
        f"Tell a child-friendly mystery where {c.id} solves a strange sound through friendship and dialogue.",
        f"Write a gentle spooky story in {world.place.name} with a friendly ghost, a clue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"]
    p = f["parent"]
    g = f["ghost"]
    m = f["mystery"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where does {c.id} hear the strange {m.sound_word}?",
            answer=f"{c.id} hears it in {place.name}, where everything is quiet and a little spooky.",
        ),
        QAItem(
            question=f"Who helps {c.id} solve the mystery?",
            answer=f"The friendly ghost helps {c.id}, and {p.label} listens too.",
        ),
        QAItem(
            question=f"What was the mystery really about?",
            answer=f"It was really about {m.source}, which turned out to be harmless and easy to explain.",
        ),
        QAItem(
            question=f"How did {c.id} and {g.label} solve it?",
            answer=f"They used gentle dialogue, followed the clue, and looked carefully until they found the source.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="Why does talking kindly help in a mystery story?",
            answer="Kind words help people feel safe, so they can listen, share, and solve a problem together.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a story with spooky feelings or a ghost in it, often with a mystery to solve.",
        ),
        QAItem(
            question=f"What does {m.clue_word} mean in this story?",
            answer=f'In this story, "{m.clue_word}" is a little mystery word that points to something hidden.',
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world with friendship and dialogue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name", choices=sorted(CHILD_NAMES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender.")
    return StoryParams(place=place, child_name=name, child_type=gender, parent_type=parent, mystery=mystery)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell_story(world)
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


CURATED = [
    StoryParams(place="attic", child_name="Mina", child_type="girl", parent_type="mother", mystery="pupa"),
    StoryParams(place="garden", child_name="Theo", child_type="boy", parent_type="father", mystery="snuffle"),
    StoryParams(place="hallway", child_name="Nora", child_type="girl", parent_type="mother", mystery="pupa"),
    StoryParams(place="shed", child_name="Finn", child_type="boy", parent_type="father", mystery="snuffle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/2."))
        print(sorted(asp.atoms(model, "solved")))
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
            header = f"### {p.child_name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
