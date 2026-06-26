#!/usr/bin/env python3
"""
A standalone storyworld for a small whodunit with a muggy garden, a hammock,
and a creeping mystery with a magical twist.

The seed tale premise:
A child detective notices something missing during a muggy afternoon. The
hammock sways, a creep of a clue appears, and magic reveals the truth:
the "crime" was a misunderstood helper, not a thief.

This world simulates:
- typed entities with physical meters and emotional memes
- clues that can be hidden, found, or revealed by magic
- suspicion that rises and then turns on a twist
- a final resolution image that proves what changed
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    visible: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    muggy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hidden_by: str = ""


@dataclass
class Mystery:
    id: str
    label: str
    danger: str
    twist: str
    magic_reveal: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.clues = copy.deepcopy(self.clues)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _get_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = _get_meter(ent, key) + amount


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if _get_meter(char, "mystery") < THRESHOLD:
            continue
        sig = ("suspicion", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(char, "suspicion", 1.0)
        out.append(f"{char.label} kept looking from clue to clue, feeling more and more unsure.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    for clue in world.clues.values():
        if clue.hidden_by and clue.hidden_by in world.entities:
            hider = world.get(clue.hidden_by)
            if _get_meter(hider, "nervous") >= THRESHOLD:
                sig = ("reveal", clue.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                clue.hidden_by = ""
                out.append(f"A little magic made {clue.label} show itself at last.")
    return out


RULES = [
    _r_suspicion,
    _r_reveal,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def search(world: World, detective: Entity, clue: Clue) -> None:
    _add_meter(detective, "mystery", 1.0)
    world.say(f"{detective.label} searched the muggy yard near the hammock, but the clue was still hard to read.")
    propagate(world)


def inspect_hammock(world: World, detective: Entity, hammock: Entity) -> None:
    _add_meter(detective, "mystery", 1.0)
    if _get_meter(hammock, "sway") >= THRESHOLD:
        world.say(f"The hammock creaked softly, as if it knew something.")
    else:
        world.say(f"The hammock hung still, but it looked like a good place for a clue to hide.")
    propagate(world)


def cast_magic(world: World, magician: Entity, target: Entity) -> None:
    _add_meter(magician, "magic", 1.0)
    _add_meter(target, "glow", 1.0)
    world.say(f"{magician.label} whispered a tiny magic word, and the air around {target.label} shimmered.")
    propagate(world)


def accuse(world: World, detective: Entity, suspect: Entity) -> None:
    _add_meme(detective, "suspicion", 1.0)
    _add_meme(suspect, "worry", 1.0)
    world.say(f"{detective.label} almost blamed {suspect.label}, but the clues did not quite fit.")
    propagate(world)


def twist_resolution(world: World, detective: Entity, helper: Entity, clue: Clue, mystery: Mystery) -> None:
    helper.memes["worry"] = 0.0
    detective.memes["suspicion"] = 0.0
    world.say(
        f"Then came the twist: {helper.label} had only hidden {clue.label} to keep it safe, "
        f"not to steal it."
    )
    world.say(
        f"The magic reveal matched the last clue, and the whole mystery turned clear: "
        f"{mystery.twist}."
    )
    world.say(
        f"By the end, {detective.label} smiled at the hammock, the muggy air felt lighter, "
        f"and {clue.label} was back where it belonged."
    )


def build_story_world(place: Place, mystery: Mystery, hero_name: str, hero_type: str,
                     helper_type: str, seed: Optional[int] = None) -> World:
    world = World(place)
    detective = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"mystery": 0.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="Mira",
        meters={"nervous": 0.0},
        memes={"kindness": 1.0},
    ))
    hammock = world.add(Entity(
        id="hammock",
        type="thing",
        label="the hammock",
        phrase="a striped hammock",
        meters={"sway": 1.0},
    ))
    charm = world.add(Entity(
        id="charm",
        type="thing",
        label="the charm",
        phrase="a small silver charm",
        owner=hero_name,
        visible=False,
    ))
    note = world.add_clue(Clue(
        id="note",
        label="a muddy note",
        phrase="a muddy note tucked in the rope",
        hidden_by="helper",
    ))
    world.facts.update(
        detective=detective,
        helper=helper,
        hammock=hammock,
        charm=charm,
        note=note,
        mystery=mystery,
    )

    # Act 1
    world.say(f"It was a muggy afternoon, and {detective.label} noticed that {mystery.label} was missing.")
    world.say(f"The hammock swayed in the yard, and that made the little mystery feel even stranger.")
    world.say(f"Nearby, a muddy note seemed to creep into view and then hide again.")
    world.para()

    # Act 2
    inspect_hammock(world, detective, hammock)
    search(world, detective, note)
    accuse(world, detective, helper)
    helper.meters["nervous"] = 1.0
    cast_magic(world, helper, charm)
    world.para()

    # Act 3
    twist_resolution(world, detective, helper, note, mystery)

    world.facts["resolved"] = True
    world.facts["seed"] = seed
    return world


SETTING_REGISTRY = {
    "garden": Place(name="the garden", muggy=True, affords={"search", "inspect", "magic"}),
    "yard": Place(name="the backyard", muggy=True, affords={"search", "inspect", "magic"}),
}

MYSTERIES = {
    "missing_charm": Mystery(
        id="missing_charm",
        label="a silver charm",
        danger="someone had taken it",
        twist="Mira had hidden it in the hammock rope to keep it safe from the rain",
        magic_reveal="the charm sparkled when magic touched it",
    ),
    "lost_key": Mystery(
        id="lost_key",
        label="a brass key",
        danger="the key had vanished from the porch",
        twist="Mira had moved it into the hammock pocket so nobody would trip over it",
        magic_reveal="the key gleamed through the shadow",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Lila"]
BOY_NAMES = ["Eli", "Theo", "Noah", "Max", "Finn"]
HELPERS = ["mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTING_REGISTRY:
        for mystery in MYSTERIES:
            combos.append((place, mystery))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A muggy hammock whodunit with a magical twist.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice(list(SETTING_REGISTRY))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child, with a muggy garden, a hammock, and a magical twist.',
        f"Tell a mystery where {f['detective'].label} notices something missing near {f['hammock'].label}, "
        f"suspects the wrong person, and learns the truth by magic.",
        f'Write a gentle mystery story that includes the words "muggy", "hammock", and "creep".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    mystery = f["mystery"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"What kind of day was it when {detective.label} noticed the missing {mystery.label}?",
            answer=f"It was a muggy afternoon in {world.place.name}, which made the mystery feel slow and strange.",
        ),
        QAItem(
            question=f"What did the hammock do in the story?",
            answer="The hammock swayed and creaked, which made it seem like it was hiding a clue.",
        ),
        QAItem(
            question=f"Who did {detective.label} almost blame before the twist?",
            answer=f"{helper.label}, the helper, looked suspicious for a moment even though {helper.label} was not the thief.",
        ),
        QAItem(
            question=f"What turned out to be the truth about {charm.label}?",
            answer=f"{helper.label} had hidden it only to keep it safe, and magic revealed that it belonged back with the detective.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does muggy mean?",
            answer="Muggy means the air feels warm, damp, and sticky.",
        ),
        QAItem(
            question="What is a hammock?",
            answer="A hammock is a hanging bed or sling made from cloth or netting.",
        ),
        QAItem(
            question="What does creep mean?",
            answer="To creep means to move slowly and quietly, or to feel a little spooky and sneaky.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprise that changes what you thought was true.",
        ),
        QAItem(
            question="What does magic do in stories?",
            answer="Magic can reveal hidden things, change what people see, or make an impossible clue become clear.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} visible={e.visible}")
    for c in world.clues.values():
        lines.append(f"clue {c.id}: hidden_by={c.hidden_by or '-'}")
    lines.extend(world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is hidden when some entity hides it.
hidden(C) :- clue(C), hidden_by(C, H), entity(H).

% Suspicion rises when the detective has gathered enough mystery.
suspects(D) :- character(D), meter(D, mystery, M), M >= 1.

% Magic can reveal a hidden clue if the helper is nervous.
revealed(C) :- clue(C), hidden_by(C, H), meter(H, nervous, N), N >= 1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTING_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        if place.muggy:
            lines.append(asp.fact("muggy", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    if model is None:
        print("MISMATCH: no ASP model")
        return 1
    print("OK: ASP program parses and solves.")
    return 0


def generate(params: StoryParams) -> StorySample:
    place = SETTING_REGISTRY[params.place]
    mystery = MYSTERIES[params.mystery]
    world = build_story_world(place, mystery, params.name, params.gender, params.helper, params.seed)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show place/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place, mystery in valid_combos():
            params = StoryParams(
                place=place,
                mystery=mystery,
                name="Mina",
                gender="girl",
                helper="mother",
                seed=base_seed,
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
