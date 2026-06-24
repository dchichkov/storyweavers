#!/usr/bin/env python3
"""
storyworlds/worlds/gristle_whir_real_ist_dialogue_ghost_story.py
=================================================================

A standalone story world for a small Ghost-Story-style domain with dialogue,
spooky-but-child-facing atmosphere, and state-driven turns.

Premise seed:
- A child hears a gristle-like creak and a whir in an old house.
- A ghost is real, but the child is a real-ist and wants proof.
- The ghost is not scary once understood; it is trying to help.

This world generates one complete little story: a beginning in a quiet house,
a middle with tension and dialogue, and an ending where the ghost's helpful
nature is proven by a real change in the world.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SCARE_LIMIT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    hush: str
    nook: str


@dataclass
class Sound:
    id: str
    label: str
    onomatopoeia: str
    source: str
    intensity: int
    ghostly: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Ghost:
    id: str
    label: str
    name: str
    kind: str
    helps_with: str
    proof: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.event_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.event_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scare(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["sound"] < THRESHOLD:
            continue
        sig = ("scare", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["fear"] += 1
        out.append("__scare__")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("ghost_helping") and not world.facts.get("found_clue"):
        sig = ("help",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["hope"] += 1
            out.append("__help__")
    return out


CAUSAL_RULES = [
    Rule("scare", "emotional", _r_scare),
    Rule("help", "emotional", _r_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_ghost(world: World, sound: Sound, ghost: Ghost) -> dict:
    sim = world.copy()
    sim.get("sound").meters["sound"] += sound.intensity
    sim.facts["ghost_helping"] = True
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "hope": sim.get("child").memes["hope"],
    }


def set_scene(world: World, child: Entity, parent: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"The {world.place.label} was quiet, with {world.place.hush} in the air and "
        f"{world.place.nook} waiting in the dim room."
    )
    world.say(
        f"{child.id} was a little real-ist who liked proof. "
        f'"If ghosts are real," {child.id} said, "they should leave a sign."'
    )
    world.say(
        f'{parent.id} smiled and said, "Then let us listen carefully."'
    )


def make_sound(world: World, child: Entity, sound: Sound) -> None:
    world.get("sound").meters["sound"] += sound.intensity
    child.memes["unease"] += 1
    world.say(
        f"Then came a {sound.label} from {sound.source}: "
        f'"{sound.onomatopoeia}."'
    )
    world.say(f'"Did you hear that?" {child.id} whispered.')


def answer_with_dialogue(world: World, child: Entity, ghost: Ghost) -> None:
    child.memes["fear"] += 1
    world.facts["ghost_helping"] = True
    world.say(f'"I heard you," said a soft voice from the {world.place.nook}.')
    world.say(f'"Who are you?" asked {child.id}.')
    world.say(
        f'"I am {ghost.name}," said the ghost. "I make the {ghost.helps_with} whir, "
        f"and I can show you something real."'
    )


def prove(world: World, child: Entity, ghost: Ghost) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    child.memes["joy"] += 1
    world.facts["found_clue"] = True
    world.say(
        f"The ghost pointed to a little hidden latch, and with a gentle push, the "
        f"old panel opened."
    )
    world.say(
        f"Inside was a lost key that had been stuck behind the wall all along."
    )
    world.say(
        f'"That is real," said {child.id}. "{ghost.proof}."'
    )


def resolve(world: World, child: Entity, parent: Entity, ghost: Ghost) -> None:
    child.memes["fear"] = 0.0
    child.memes["warmth"] += 1
    world.say(
        f'{parent.id} said, "Good listening. The sound was scary, but it led us to '
        f"a real answer.""
    )
    world.say(
        f'{child.id} nodded. "So the ghost was real, and helpful too."'
    )
    world.say(
        f'The ghost gave a tiny bow from the corner, and the {world.place.id} felt '
        f"less like a mystery and more like a friend."
    )


def tell(place: Place, sound: Sound, ghost: Ghost,
         child_name: str = "Mina", parent_name: str = "Mom") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type="girl"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother"))
    noise = world.add(Entity(id="sound", type="thing", label=sound.label))
    ghost_ent = world.add(Entity(id="ghost", kind="character", type="thing", label=ghost.name))

    # initialize all read-before-write values
    child.memes["curiosity"] = 0.0
    child.memes["unease"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["warmth"] = 0.0
    noise.meters["sound"] = 0.0
    noise.memes["silence"] = 0.0
    ghost_ent.meters["sound"] = 0.0
    ghost_ent.memes["mystery"] = 1.0

    world.facts["ghost_helping"] = False
    world.facts["found_clue"] = False

    set_scene(world, child, parent)
    world.para()
    make_sound(world, child, sound)
    answer_with_dialogue(world, child, ghost)
    world.para()
    prove(world, child, ghost)
    resolve(world, child, parent, ghost)

    world.facts.update(child=child, parent=parent, sound=sound, ghost=ghost, place=place)
    return world


PLACEs = {
    "attic": Place(id="attic", label="attic", hush="dusty hush", nook="the rafters"),
    "hall": Place(id="hall", label="hallway", hush="a long still hush", nook="the old coat nook"),
    "kitchen": Place(id="kitchen", label="kitchen", hush="a sleepy hush", nook="the pantry door"),
}

SOUNDS = {
    "gristle": Sound(
        id="gristle",
        label="gristle",
        onomatopoeia="grrrk-skrip",
        source="the old stair",
        intensity=1,
        ghostly=True,
        tags={"gristle", "ghost"},
    ),
    "whir": Sound(
        id="whir",
        label="whir",
        onomatopoeia="whirrr",
        source="the wall fan",
        intensity=1,
        ghostly=False,
        tags={"whir", "machine"},
    ),
}

GHOSTS = {
    "real-ist": Ghost(
        id="real-ist",
        label="real-ist ghost",
        name="Pip",
        kind="ghost",
        helps_with="whir",
        proof="It moved",
        tags={"real-ist", "ghost", "proof"},
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Max", "Sam"]


@dataclass
class StoryParams:
    place: str
    sound: str
    ghost: str
    child_name: str
    child_gender: str
    parent_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACEs:
        for sound in SOUNDS:
            for ghost in GHOSTS:
                combos.append((place, sound, ghost))
    return combos


KNOWLEDGE = {
    "gristle": [("What is a gristle sound?", "A gristle sound is a rough, scratchy sound, like old wood rubbing together.")],
    "whir": [("What makes a whir sound?", "A whir is a steady spinning or humming sound, like a fan or a little motor.")],
    "ghost": [("What is a ghost in a story?", "A ghost in a story is a spooky character, but it can be friendly or helpful.")],
    "proof": [("What is proof?", "Proof is something real that shows an idea is true.")],
    "real-ist": [("What does real-ist mean?", "A real-ist is someone who likes real answers and wants proof before believing something.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story with dialogue set in the {f["place"].label} that includes the words "gristle" and "whir".',
        f"Tell a spooky-but-gentle story where {f['child'].id}, a real-ist, hears a strange sound and talks to a helpful ghost.",
        f'Write a short ghost story where a child says "If ghosts are real, they should leave a sign," and then gets one.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, sound, ghost, place = f["child"], f["parent"], f["sound"], f["ghost"], f["place"]
    return [
        QAItem(
            question=f"Who is the story about in the {place.label}?",
            answer=(
                f"It is about {child.id}, a little real-ist, and {parent.id}, who listened with {child.id}. "
                f"They heard a {sound.label} and met {ghost.name}."
            ),
        ),
        QAItem(
            question=f"What strange sound did {child.id} hear?",
            answer=(
                f"{child.id} heard a {sound.label} from {sound.source}, and it sounded like '{sound.onomatopoeia}'. "
                f"That was the sound that started the mystery."
            ),
        ),
        QAItem(
            question=f"What did the ghost say to {child.id}?",
            answer=(
                f"The ghost said, '{ghost.name} is here,' and then explained that it could make the {ghost.helps_with} whir. "
                f"It spoke softly from the {place.nook}."
            ),
        ),
        QAItem(
            question=f"What proof did {child.id} get that the ghost was real?",
            answer=(
                f"{child.id} got a real clue when the hidden panel opened and a lost key was found. "
                f"{ghost.proof} was the proof that something real had happened."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["sound"].tags) | set(world.facts["ghost"].tags)
    out: list[QAItem] = []
    for tag in ["gristle", "whir", "ghost", "proof", "real-ist"]:
        if tag in tags or tag == "real-ist":
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(place: Place, sound: Sound, ghost: Ghost) -> str:
    return f"(No story: the chosen setup cannot make a useful ghost-story turn in the {place.label}.)"


ASP_RULES = r"""
sound_like(S) :- sound(S).
ghost_real(G) :- ghost(G), helps(G, _).
mystery_turn(P, S, G) :- place(P), sound(S), ghost(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACEs:
        lines.append(asp.fact("place", p))
    for s in SOUNDS:
        lines.append(asp.fact("sound", s))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
        lines.append(asp.fact("helps", g, GHOSTS[g].helps_with))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_turn/3."))
    clingo_set = set(asp.atoms(model, "mystery_turn"))
    python_set = set(valid_combos())
    if len(clingo_set) == len(python_set):
        print("OK: ASP and Python agree on story availability.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with gristle, whir, and a real-ist ghost.")
    ap.add_argument("--place", choices=PLACEs)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.sound is None or c[1] == args.sound)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sound, ghost = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent_name = args.parent or ("Mom" if child_gender == "girl" else "Dad")
    return StoryParams(place=place, sound=sound, ghost=ghost, child_name=child_name, child_gender=child_gender, parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACEs[params.place], SOUNDS[params.sound], GHOSTS[params.ghost], params.child_name, params.parent_name)
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
        print(asp_program("#show mystery_turn/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid story combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, sound=s, ghost=g, child_name="Mina", child_gender="girl", parent_name="Mom")) for p, s, g in valid_combos()]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
