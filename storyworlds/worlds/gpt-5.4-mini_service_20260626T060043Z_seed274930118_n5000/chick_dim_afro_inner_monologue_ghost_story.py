#!/usr/bin/env python3
"""
storyworlds/worlds/chick_dim_afro_inner_monologue_ghost_story.py
=================================================================

A small storyworld for a child-friendly ghost story with inner monologue.

Seed premise:
- A little chick-dim hero notices a ghost in a quiet place.
- The hero is scared, then thinks through the fear in an inner monologue.
- The ghost is not harmful; the hero learns what the ghost needs.
- The turn comes from listening carefully instead of fleeing.
- The ending image proves the fear changed into comfort.

This world keeps the prose concrete and state-driven:
- meters: coldness, fear, glow, comfort, dust, tidiness
- memes: bravery, curiosity, worry, relief, loneliness, kindness

The "afro" seed word is included as a valid style/world adjective in the registry
for hair/appearance and can appear in the generated hero description.
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
    kind: str = "thing"  # character | thing | ghost | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    alive: bool = True
    visible: bool = True
    friendly: bool = False
    spooky: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("cold", "fear", "glow", "comfort", "dust", "tidy"):
            self.meters.setdefault(k, 0.0)
        for k in ("bravery", "curiosity", "worry", "relief", "loneliness", "kindness"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    quiet: bool = True
    dark: bool = True
    has_mirror: bool = False
    has_lamp: bool = False
    has_blanket: bool = False
    has_window: bool = False
    has_wood_floor: bool = False
    has_dusty_corner: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(
        id="attic", label="the attic", quiet=True, dark=True, has_window=True,
        has_wood_floor=True, has_dusty_corner=True
    ),
    "bedroom": Place(
        id="bedroom", label="the bedroom", quiet=True, dark=True,
        has_lamp=True, has_blanket=True, has_window=True
    ),
    "hallway": Place(
        id="hallway", label="the hallway", quiet=True, dark=True,
        has_lamp=True, has_mirror=True, has_wood_floor=True
    ),
}

HERO_TYPES = {
    "girl": ["girl", "little girl"],
    "boy": ["boy", "little boy"],
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ava", "Ivy", "Zoe"],
    "boy": ["Eli", "Noah", "Finn", "Theo", "Max", "Leo"],
}

HERO_TRAITS = ["chick-dim", "curious", "small", "careful", "brave", "sleepy"]
HAIR_TRAITS = ["afro", "curly", "soft curls", "dark curls", "short hair"]

GHOST_KINDS = {
    "gentle": {
        "label": "a gentle ghost",
        "phrase": "a small, pale ghost with a round smile",
        "spooky": False,
        "need": "a listening friend",
        "haunt": "a lonely whisper",
    },
    "dusty": {
        "label": "a dusty ghost",
        "phrase": "a gray ghost with a dusty scarf",
        "spooky": False,
        "need": "someone to open the window",
        "haunt": "the dust in the corner",
    },
    "lamp": {
        "label": "a lamp ghost",
        "phrase": "a bright ghost that flickered like a little lamp",
        "spooky": False,
        "need": "the lamp to be switched on",
        "haunt": "the dark spot by the wall",
    },
}

OBJECTS = {
    "blanket": ("a warm blanket", "blanket"),
    "lamp": ("a small lamp", "lamp"),
    "window": ("the window", "window"),
    "broom": ("a broom", "broom"),
    "toy": ("a tiny toy box", "toy"),
}

ASP_RULES = r"""
% A ghostly fear is reasonable when a child is in a quiet dark place
% with a ghost and no comforting object nearby.
haunted(P,G) :- place(P), ghost(G), in_place(P,G), quiet(P), dark(P).
needs_comfort(H) :- haunted(P,G), child(H), in_place(P,H), not has_comfort(H).

% Inner monologue can reduce fear if it recognizes a harmless explanation.
safe_ghost(G) :- ghost(G), friendly(G).
can_reassure(H,G) :- child(H), ghost(G), safe_ghost(G).

compatible_story(P,G,O) :- haunted(P,G), comfort_object(O), place_supports(P,O), ghost_need_matches(G,O).
"""

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    gender: str
    name: str
    trait: str
    hair: str
    ghost_kind: str
    comfort_object: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def initial_story_params(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(HERO_TRAITS)
    hair = args.hair or rng.choice(HAIR_TRAITS)
    ghost_kind = args.ghost_kind or rng.choice(list(GHOST_KINDS))
    comfort_object = args.comfort_object or rng.choice(list(OBJECTS))
    return StoryParams(
        place=place,
        gender=gender,
        name=name,
        trait=trait,
        hair=hair,
        ghost_kind=ghost_kind,
        comfort_object=comfort_object,
    )


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.gender not in HERO_TYPES:
        raise StoryError("Unknown gender.")
    if params.ghost_kind not in GHOST_KINDS:
        raise StoryError("Unknown ghost kind.")
    if params.comfort_object not in OBJECTS:
        raise StoryError("Unknown comfort object.")


def build_hero(world: World, params: StoryParams) -> Entity:
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["little", params.trait, params.hair],
    ))
    hero.memes["worry"] = 0.0
    return hero


def build_ghost(world: World, params: StoryParams) -> Entity:
    g = GHOST_KINDS[params.ghost_kind]
    ghost = world.add(Entity(
        id="ghost",
        kind="ghost",
        type="ghost",
        label=g["label"],
        phrase=g["phrase"],
        alive=False,
        visible=True,
        friendly=True,
        spooky=False,
    ))
    ghost.memes["loneliness"] = 1.0
    ghost.meters["glow"] = 1.0
    return ghost


def world_supports_comfort(place: Place, comfort_object: str) -> bool:
    if comfort_object == "blanket":
        return place.has_blanket
    if comfort_object == "lamp":
        return place.has_lamp
    if comfort_object == "window":
        return place.has_window
    if comfort_object == "broom":
        return place.has_wood_floor or place.has_dusty_corner
    if comfort_object == "toy":
        return True
    return False


def ghost_need_matches(ghost_kind: str, comfort_object: str) -> bool:
    if ghost_kind == "gentle":
        return comfort_object in {"toy", "blanket"}
    if ghost_kind == "dusty":
        return comfort_object in {"window", "broom"}
    if ghost_kind == "lamp":
        return comfort_object == "lamp"
    return False


def fear_reason(world: World, hero: Entity, ghost: Entity) -> bool:
    return world.place.dark and ghost.visible and hero.memes["curiosity"] < 2.0


def inner_monologue(hero: Entity, ghost: Entity, comfort_object: str) -> str:
    obj_label = OBJECTS[comfort_object][0]
    return (
        f"{hero.pronoun('subject').capitalize()} thought, "
        f'"It feels spooky, but maybe it is only a lonely ghost. '
        f'If I look carefully, I might learn what {ghost.pronoun("subject")} needs. '
        f"Maybe {obj_label} can help."'
    )


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _rule_cold(world: World) -> list[str]:
    out: list[str] = []
    if world.place.dark:
        for e in world.entities.values():
            if e.kind == "character":
                sig = ("cold", e.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    e.meters["cold"] += 1
                    e.memes["worry"] += 1
                    out.append(f"The air felt cold around {e.id}.")
    return out


def _rule_haunt(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    ghost = world.entities.get("ghost")
    if not hero or not ghost:
        return out
    if fear_reason(world, hero, ghost):
        sig = ("fear", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["fear"] += 1
            hero.memes["worry"] += 1
            out.append(f"{hero.id}'s chest went tight when {ghost.label} appeared.")
    return out


def _rule_comfort(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    ghost = world.entities.get("ghost")
    if not hero or not ghost:
        return out
    if hero.memes["curiosity"] >= THRESHOLD and ghost.memes["loneliness"] >= THRESHOLD:
        sig = ("comfort", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["kindness"] += 1
            ghost.memes["loneliness"] = max(0.0, ghost.memes["loneliness"] - 1.0)
            hero.meters["comfort"] += 1
            out.append(f"Listening made the room feel less empty.")
    return out


CAUSAL_RULES = [_rule_cold, _rule_haunt, _rule_comfort]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                produced.extend(got)
    for s in produced:
        world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    validate_params(params)
    place = PLACES[params.place]
    world = World(place)
    hero = build_hero(world, params)
    ghost = build_ghost(world, params)
    comfort_name, comfort_short = OBJECTS[params.comfort_object]

    world.facts.update(
        place=place.id,
        hero=hero,
        ghost=ghost,
        comfort_object=params.comfort_object,
        comfort_label=comfort_name,
        comfort_short=comfort_short,
        ghost_kind=params.ghost_kind,
    )

    # Act 1: setup
    world.say(
        f"{hero.id} was a little {params.trait} {params.gender} with {params.hair} "
        f"and a chick-dim kind of way of noticing small things."
    )
    world.say(
        f"That evening, {hero.id} went into {place.label} and saw {ghost.phrase}."
    )
    world.para()

    # Act 2: fear and inner monologue
    propagate(world)
    hero.memes["curiosity"] += 1.0
    world.say(
        inner_monologue(hero, ghost, params.comfort_object)
    )
    if hero.meters["fear"] >= THRESHOLD:
        world.say(
            f"{hero.id} wanted to run, but {hero.pronoun('possessive')} feet stayed still."
        )
    world.para()

    # Act 3: turn and resolution
    if params.comfort_object == "window" and not place.has_window:
        raise StoryError("The chosen comfort object cannot help in this place.")
    if not world_supports_comfort(place, params.comfort_object):
        raise StoryError("No reasonable story: that comfort object does not fit the place.")
    if not ghost_need_matches(params.ghost_kind, params.comfort_object):
        raise StoryError("No reasonable story: that comfort object does not match the ghost's need.")

    hero.memes["curiosity"] += 1.0
    ghost.memes["loneliness"] += 0.5
    if params.ghost_kind == "dusty":
        world.say(
            f"{hero.id} noticed the dusty corner and wondered if the ghost was not mean at all."
        )
    elif params.ghost_kind == "lamp":
        world.say(
            f"{hero.id} noticed the dark spot by the wall and wondered if the ghost was asking for light."
        )
    else:
        world.say(
            f"{hero.id} noticed the quiet room and wondered if the ghost was simply lonely."
        )

    world.say(
        f"Then {hero.id} used {comfort_name}."
    )
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - 1.0)
    hero.meters["comfort"] += 1.0
    hero.memes["relief"] += 1.0
    hero.memes["bravery"] += 1.0
    ghost.memes["loneliness"] = max(0.0, ghost.memes["loneliness"] - 1.0)
    ghost.meters["glow"] += 1.0
    world.say(
        f"The ghost looked less spooky and more like a quiet friend."
    )
    world.say(
        f"At the end, {hero.id} stood in {place.label} feeling brave, and {ghost.label} "
        f"glowed softly near {comfort_name}."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    ghost_kind = f["ghost_kind"]
    comfort = f["comfort_label"]
    return [
        f'Write a child-friendly ghost story set in {place} with an inner monologue and the word "chick-dim".',
        f"Tell a short story about {hero.id}, who notices {ghost_kind} ghost in {place} and finds a calmer way to respond.",
        f'Write a spooky-but-gentle story where a small hero thinks to themself, then helps a ghost using {comfort}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    ghost: Entity = f["ghost"]
    place: str = f["place"]
    comfort_label: str = f["comfort_label"]
    question1 = f"Who was the story about when {hero.id} went into {place}?"
    answer1 = (
        f"It was about {hero.id}, a little {hero.traits[1]} {hero.type} with {hero.traits[2]}. "
        f"{hero.id} saw {ghost.label} in {place} and stayed long enough to understand what was happening."
    )
    question2 = f"Why did {hero.id} feel scared at first?"
    answer2 = (
        f"{hero.id} felt scared because {ghost.phrase} appeared in the dark room, "
        f"and the air felt cold. But {hero.id} thought carefully instead of running away."
    )
    question3 = f"What did {hero.id} think in {hero.id}'s inner monologue?"
    answer3 = (
        f"{hero.id} thought the ghost might just be lonely, and that {comfort_label} might help. "
        f"That thought changed fear into curiosity."
    )
    qas = [
        QAItem(question=question1, answer=answer1),
        QAItem(question=question2, answer=answer2),
        QAItem(question=question3, answer=answer3),
    ]
    qas.append(
        QAItem(
            question=f"How did the story end for {hero.id} and the ghost?",
            answer=(
                f"By the end, {hero.id} felt brave and calm, and {ghost.label} glowed softly "
                f"near {comfort_label}. The room stopped feeling so spooky."
            ),
        )
    )
    return qas


WORLD_KNOWLEDGE = {
    "ghost": [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is often a spooky-looking spirit character, but in gentle stories it can be lonely, kind, or in need of help.",
        )
    ],
    "blanket": [
        QAItem(
            question="Why can a blanket make a room feel safer?",
            answer="A blanket can make a room feel safer because it is warm and cozy, and cozy things help people relax.",
        )
    ],
    "lamp": [
        QAItem(
            question="What does a lamp do in a dark room?",
            answer="A lamp gives light, which helps people see better when a room is dark.",
        )
    ],
    "window": [
        QAItem(
            question="Why does opening a window help a dusty room?",
            answer="Opening a window can let fresh air move through the room and help the space feel less stuffy or dusty.",
        )
    ],
    "chick-dim": [
        QAItem(
            question="What does chick-dim mean here?",
            answer="Here, chick-dim means very small and a little dim or shy, like a tiny hero moving carefully through a spooky room.",
        )
    ],
    "afro": [
        QAItem(
            question="What is an afro?",
            answer="An afro is a round, fluffy hairstyle made by curly hair growing out naturally.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["ghost"])
    out.extend(WORLD_KNOWLEDGE["chick-dim"])
    out.extend(WORLD_KNOWLEDGE["afro"])
    comfort = world.facts["comfort_object"]
    if comfort in WORLD_KNOWLEDGE:
        out.extend(WORLD_KNOWLEDGE[comfort])
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.quiet:
            lines.append(asp.fact("quiet", pid))
        if place.dark:
            lines.append(asp.fact("dark", pid))
        if place.has_mirror:
            lines.append(asp.fact("has", pid, "mirror"))
        if place.has_lamp:
            lines.append(asp.fact("has", pid, "lamp"))
        if place.has_blanket:
            lines.append(asp.fact("has", pid, "blanket"))
        if place.has_window:
            lines.append(asp.fact("has", pid, "window"))
        if place.has_wood_floor:
            lines.append(asp.fact("has", pid, "wood_floor"))
        if place.has_dusty_corner:
            lines.append(asp.fact("has", pid, "dusty_corner"))
    for gk, g in GHOST_KINDS.items():
        lines.append(asp.fact("ghost_kind", gk))
        if g["label"]:
            lines.append(asp.fact("ghost_label", gk, g["label"]))
        if g["spooky"]:
            lines.append(asp.fact("spooky", gk))
        else:
            lines.append(asp.fact("friendly", gk))
    for obj, (_, short) in OBJECTS.items():
        lines.append(asp.fact("comfort_object", obj))
        lines.append(asp.fact("comfort_short", obj, short))
    lines.append(asp.fact("seed_word", "chick-dim"))
    lines.append(asp.fact("seed_word", "afro"))
    return "\n".join(lines)


ASP_RULES = ASP_RULES + r"""

in_place(P,H) :- hero(H), place(H, P).
in_place(P,G) :- ghost_entity(G), place(G, P).

"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show compatible_story/3."))
    clingo_set = set(asp.atoms(model, "compatible_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("clingo only:", sorted(clingo_set - py_set))
    print("python only:", sorted(py_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, p in PLACES.items():
        for ghost_kind in GHOST_KINDS:
            for comfort in OBJECTS:
                if world_supports_comfort(p, comfort) and ghost_need_matches(ghost_kind, comfort):
                    out.append((place, ghost_kind, comfort))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Child-friendly ghost story world with inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=list(HERO_TYPES))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=HERO_TRAITS)
    ap.add_argument("--hair", choices=HAIR_TRAITS)
    ap.add_argument("--ghost-kind", choices=list(GHOST_KINDS))
    ap.add_argument("--comfort-object", choices=list(OBJECTS))
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
    params = initial_story_params(rng, args)
    validate_params(params)
    if args.place and params.place != args.place:
        params.place = args.place
    if args.gender and params.gender != args.gender:
        params.gender = args.gender
    if args.ghost_kind and params.ghost_kind != args.ghost_kind:
        params.ghost_kind = args.ghost_kind
    if args.comfort_object and params.comfort_object != args.comfort_object:
        params.comfort_object = args.comfort_object
    if args.name:
        params.name = args.name
    if args.trait:
        params.trait = args.trait
    if args.hair:
        params.hair = args.hair

    if not (world_supports_comfort(PLACES[params.place], params.comfort_object) and
            ghost_need_matches(params.ghost_kind, params.comfort_object)):
        raise StoryError("No valid story for the chosen place, ghost kind, and comfort object.")
    return params


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
        print()
        print("--- world trace ---")
        for line in sample.world.trace_log:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="bedroom", gender="girl", name="Mina", trait="chick-dim", hair="afro", ghost_kind="gentle", comfort_object="blanket"),
    StoryParams(place="attic", gender="boy", name="Eli", trait="curious", hair="afro", ghost_kind="dusty", comfort_object="window"),
    StoryParams(place="hallway", gender="girl", name="Ivy", trait="small", hair="curly", ghost_kind="lamp", comfort_object="lamp"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n * 40)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
