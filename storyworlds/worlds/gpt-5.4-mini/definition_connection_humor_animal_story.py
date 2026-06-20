#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/definition_connection_humor_animal_story.py
===========================================================================

A small standalone story world for a humorous animal tale about two animals
arguing over what a word means, discovering a surprising connection, and ending
with a playful laugh that changes how they see each other.

The seed words are:
- definition
- connection

Style target:
- animal story
- humorous
- child-facing
- complete beginning / turn / ending
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    vibe: str
    props: str
    noises: str
    kind: str = "place"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    sort: str
    use: str
    funny: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Connection:
    id: str
    label: str
    kind: str
    punchline: str
    help_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_giggle(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["confusion"] < THRESHOLD:
            continue
        sig = ("giggle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["giggle"] += 1
        out.append("__giggle__")
    return out


CAUSAL_RULES = [Rule("giggle", "social", _r_giggle)]


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


def predict_connection(world: World, clue_id: str, conn_id: str) -> dict:
    sim = world.copy()
    _try_clue(sim, sim.get(clue_id), CONNECTIONS[conn_id], narrate=False)
    return {
        "confused": sim.get(clue_id).meters["confusion"] >= THRESHOLD,
        "smile": sim.get(clue_id).memes["smile"] >= THRESHOLD,
    }


def _try_clue(world: World, clue: Entity, connection: Connection, narrate: bool = True) -> None:
    clue.meters["confusion"] += 1
    clue.memes["hope"] += 1
    if narrate:
        world.say(connection.punchline)
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, place: Place) -> None:
    a.memes["curious"] += 1
    b.memes["curious"] += 1
    world.say(
        f"At {place.label}, {a.id} and {b.id} were busy being animals with too much time "
        f"and not enough manners. {place.props}"
    )
    world.say(
        f"The place sounded like {place.noises}, which made the whole day feel bouncy."
    )


def definition_joke(world: World, a: Entity, b: Entity, clue: Clue) -> None:
    a.memes["pride"] += 1
    world.say(
        f'{a.id} pointed at a chalk mark and said, "That is the definition of '
        f'{clue.label}!"'
    )
    world.say(
        f"{b.id} blinked. \"That sounds like a very serious answer for something "
        f"that smells like {clue.funny}.\""
    )


def argue(world: World, a: Entity, b: Entity, clue: Clue) -> None:
    a.meters["confusion"] += 1
    b.meters["confusion"] += 1
    world.say(
        f"They both leaned over the clue and argued for a moment, each sure the other "
        f"was making a funny mistake."
    )
    world.say(
        f"Then {b.id} said, \"Maybe the word needs a better definition than that.\""
    )


def reveal_connection(world: World, b: Entity, a: Entity, conn: Connection) -> None:
    b.memes["delight"] += 1
    world.say(
        f'{b.id} suddenly gasped. "Wait! There is a connection!"'
    )
    world.say(
        f"{b.id} explained that {conn.help_text}, and now the clue looked less silly and "
        f"more clever."
    )


def laugh_turn(world: World, a: Entity, b: Entity, conn: Connection) -> None:
    a.memes["laugh"] += 1
    b.memes["laugh"] += 1
    world.say(
        f"They looked at each other and laughed so hard that even the {conn.kind} "
        f"seemed to wobble."
    )
    world.say(
        f"In the end, their big discovery was simple: a weird definition can still "
        f"lead to a good connection."
    )


def ending(world: World, place: Place, a: Entity, b: Entity, conn: Connection) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"{place.label} felt warm and friendly now, and {a.id} and {b.id} went off "
        f"together, still giggling about {conn.label}."
    )


def tell(place: Place, clue: Clue, connection: Connection,
         first: str = "Milo", first_type: str = "fox",
         second: str = "Tia", second_type: str = "rabbit") -> World:
    world = World()
    a = world.add(Entity(id=first, kind="character", type=first_type, role="speaker"))
    b = world.add(Entity(id=second, kind="character", type=second_type, role="listener"))

    setup(world, a, b, place)
    world.para()
    definition_joke(world, a, b, clue)
    argue(world, a, b, clue)
    world.para()
    pred = predict_connection(world, "clue", connection.id)
    world.facts["pred"] = pred
    world.facts["clue"] = clue
    world.facts["connection"] = connection
    world.facts["place"] = place
    world.facts["first"] = a
    world.facts["second"] = b
    _try_clue(world, world.get("clue"), connection)
    reveal_connection(world, b, a, connection)
    laugh_turn(world, a, b, connection)
    ending(world, place, a, b, connection)
    world.facts["outcome"] = "humor"
    return world


PLACES = {
    "barnyard": Place(
        "barnyard",
        "the barnyard",
        "busy",
        "The chickens pecked at the dust, the cow chewed slowly, and the pig snorted like a tiny trumpet.",
        "cluck-clucks, oinks, and a slow moo-moo beat",
    ),
    "pond": Place(
        "pond",
        "the pond",
        "shiny",
        "The ducks bobbed like little boats and the reeds nodded in the wind.",
        "splashes, quacks, and soft reed whispers",
    ),
    "orchard": Place(
        "orchard",
        "the orchard",
        "sweet",
        "The apples hung like red lanterns and the bees buzzed from tree to tree.",
        "buzzes, thumps, and happy squirrel chatter",
    ),
}

CLUES = {
    "mud": Clue(
        "mud",
        "mud",
        "messy dirt",
        "stick to a hoof, a paw, or a nose",
        "the kind of dirt that thinks it is a coat",
        tags={"mud", "dirty"},
    ),
    "wheel": Clue(
        "wheel",
        "wheel",
        "a round thing",
        "roll away before anyone can catch it",
        "a circle with a hurry",
        tags={"wheel", "round"},
    ),
    "shadow": Clue(
        "shadow",
        "shadow",
        "a dark shape",
        "follow behind a barn or a tree",
        "a shape that copies you without asking",
        tags={"shadow", "dark"},
    ),
}

CONNECTIONS = {
    "footprint": Connection(
        "footprint",
        "footprint",
        "track",
        "the muddy marks led from the puddle to the hay pile",
        "the marks matched the animals' feet",
        tags={"track", "mud"},
    ),
    "nonsense": Connection(
        "nonsense",
        "nonsense",
        "surprise",
        "the answer was funny because it sounded serious but did a silly job",
        "the mistake made the others laugh",
        tags={"funny", "silly"},
    ),
    "trick": Connection(
        "trick",
        "trick",
        "shortcut",
        "the clue only made sense when they noticed the hidden path",
        "the hidden path connected the two places",
        tags={"hidden", "path"},
    ),
}

NAMES = ["Milo", "Tia", "Pip", "Penny", "Bram", "Nina", "Otis", "Ruby"]


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    connection: str
    first: str
    first_type: str
    second: str
    second_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            for k in CONNECTIONS:
                combos.append((p, c, k))
    return combos


ASP_RULES = r"""
valid(P, C, K) :- place(P), clue(C), connection(K).
confused(C) :- chosen_clue(C).
smile(K) :- chosen_connection(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for kid in CONNECTIONS:
        lines.append(asp.fact("connection", kid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos.")
        rc = 1
    params = resolve_params(argparse.Namespace(place=None, clue=None, connection=None,
                                               first=None, first_type=None, second=None,
                                               second_type=None), random.Random(7))
    sample = generate(params)
    if not sample.story.strip():
        print("MISMATCH: empty story")
        rc = 1
    else:
        print("OK: smoke-test generation produced a story.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Humorous animal story about a definition and a connection."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--connection", choices=CONNECTIONS)
    ap.add_argument("--first")
    ap.add_argument("--first-type", choices=["fox", "rabbit", "bear", "owl", "cat", "dog"])
    ap.add_argument("--second")
    ap.add_argument("--second-type", choices=["fox", "rabbit", "bear", "owl", "cat", "dog"])
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
    place = args.place or rng.choice(sorted(PLACES))
    clue = args.clue or rng.choice(sorted(CLUES))
    connection = args.connection or rng.choice(sorted(CONNECTIONS))
    first = args.first or rng.choice(NAMES)
    second = args.second or rng.choice([n for n in NAMES if n != first])
    first_type = args.first_type or rng.choice(["fox", "cat", "bear"])
    second_type = args.second_type or rng.choice(["rabbit", "owl", "dog"])
    return StoryParams(place, clue, connection, first, first_type, second, second_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], CONNECTIONS[params.connection],
                 params.first, params.first_type, params.second, params.second_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    clue: Clue = f["clue"]
    conn: Connection = f["connection"]
    a: Entity = f["first"]
    b: Entity = f["second"]
    return [
        f'Write a funny animal story for a young child that includes the word "definition" and takes place at {place.label}.',
        f'Write a playful story where {a.id} gives a silly definition of {clue.label}, but {b.id} finds a better connection and they both laugh.',
        f'Create a short animal story that includes the words "definition" and "connection" and ends with friends giggling together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a: Entity = f["first"]
    b: Entity = f["second"]
    clue: Clue = f["clue"]
    conn: Connection = f["connection"]
    place: Place = f["place"]
    pred = f.get("pred", {})
    return [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two animals having a funny day at {place.label}."),
        ("What word did they argue about?",
         f"They argued about the word {clue.label}, and {a.id} tried to give it a definition. That led to a silly mix-up before they found the connection."),
        ("What did they discover in the end?",
         f"They discovered a connection that made the clue make sense, and then they laughed together. The joke turned into a happy friendship moment."),
        ("Why did the story feel funny?",
         f"It was funny because the first idea sounded serious, but it described something in a silly way. Then the connection was so surprising that both animals had to laugh."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue: Clue = f["clue"]
    conn: Connection = f["connection"]
    place: Place = f["place"]
    out = [
        ("What is a definition?",
         "A definition is a sentence or two that explains what a word means. It helps people understand the word better."),
        ("What is a connection?",
         "A connection is a link between two things. Sometimes a clue and an answer are connected in a surprising way."),
    ]
    if clue.id == "mud":
        out.append(("What is mud?",
                    "Mud is wet dirt. It can stick to paws, hooves, and shoes."))
    if conn.id == "footprint":
        out.append(("What is a footprint?",
                    "A footprint is a mark left behind by a foot in soft ground. It can show who passed by."))
    if place.id == "pond":
        out.append(("What animals like ponds?",
                    "Ducks and frogs often like ponds because they can splash and swim there."))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if bits:
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("barnyard", "mud", "footprint", "Milo", "fox", "Tia", "rabbit"),
    StoryParams("pond", "shadow", "nonsense", "Pip", "owl", "Ruby", "cat"),
    StoryParams("orchard", "wheel", "trick", "Bram", "bear", "Nina", "rabbit"),
]


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    clue: Clue = f["clue"]
    conn: Connection = f["connection"]
    a: Entity = f["first"]
    b: Entity = f["second"]
    return [
        f'Write a funny animal story for a young child that includes the word "definition" and takes place at {place.label}.',
        f'Write a playful story where {a.id} gives a silly definition of {clue.label}, but {b.id} finds a better connection and they both laugh.',
        f'Create a short animal story that includes the words "definition" and "connection" and ends with friends giggling together.',
    ]


if __name__ == "__main__":
    main()
