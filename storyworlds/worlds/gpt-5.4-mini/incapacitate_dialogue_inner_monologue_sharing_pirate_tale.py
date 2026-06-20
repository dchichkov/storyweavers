#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/incapacitate_dialogue_inner_monologue_sharing_pirate_tale.py
===========================================================================================

A standalone story world for a tiny pirate-tale domain with:
- Dialogue
- Inner monologue
- Sharing
- one key word: "incapacitate"

The premise is simple: a small pirate crew is out at sea, one child pirate becomes
too dizzy or too shaky to keep helping, the others share supplies and speak calmly,
and the crew finds a safe way to finish the little voyage.

The world is intentionally small and state-driven:
- physical meters track sickness, thirst, fear, relief, and progress
- emotional memes track worry, courage, care, and trust
- the story changes because the world state changes, not because nouns are swapped

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/incapacitate_dialogue_inner_monologue_sharing_pirate_tale.py
    python storyworlds/worlds/gpt-5.4-mini/incapacitate_dialogue_inner_monologue_sharing_pirate_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/incapacitate_dialogue_inner_monologue_sharing_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/incapacitate_dialogue_inner_monologue_sharing_pirate_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HEALTHY_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Ship:
    id: str
    name: str
    place: str
    has_bow: bool = True
    has_cabin: bool = True
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Supply:
    id: str
    label: str
    kind: str
    helps: str
    phrase: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        self.ship: Optional[Ship] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e):
        self.entities[e.id] = e
        return e

    def get(self, eid: str):
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
        c.ship = copy.deepcopy(self.ship)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


@dataclass
@dataclass
class StoryParams:
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    ship: str
    place: str
    problem: str
    supply1: str
    supply2: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


CAPTAINS = [("Lina", "girl"), ("Milo", "boy"), ("Nia", "girl"), ("Jace", "boy")]
MATES = [("Bea", "girl"), ("Oren", "boy"), ("Pip", "boy"), ("Tessa", "girl")]

SHIPS = {
    "tiny sloop": "a tiny sloop with a red sail",
    "little cutter": "a little cutter with a blue sail",
    "round skiff": "a round skiff with a striped sail",
}

PLACES = {
    "the cove": "the cove",
    "the bright harbor": "the bright harbor",
    "the quiet bay": "the quiet bay",
}

SUPPLIES = {
    "water": Supply("water", "water jug", "drink", "thirst", "a water jug"),
    "banana": Supply("banana", "banana", "snack", "hunger", "a banana"),
    "blanket": Supply("blanket", "warm blanket", "warmth", "chill", "a warm blanket"),
    "rope": Supply("rope", "soft rope", "steady", "shaking", "a soft rope"),
    "pear": Supply("pear", "pear", "snack", "hunger", "a pear"),
}

PROBLEMS = {
    "sway": "the boat swayed too hard",
    "dizzy": "the sea made one pirate dizzy",
    "thirsty": "the sun made them thirsty",
}


def two_names(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    c = rng.choice(CAPTAINS)
    m = rng.choice([x for x in MATES if x[0] != c[0]])
    return c, m


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for ship in SHIPS:
        for place in PLACES:
            for prob in PROBLEMS:
                combos.append((ship, place, prob))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.captain == params.mate:
        raise StoryError("The captain and mate must be different children.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.supply1 == params.supply2:
        raise StoryError("The sharing items must be different.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with dialogue, inner monologue, and sharing.")
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--supply1", choices=SUPPLIES)
    ap.add_argument("--supply2", choices=SUPPLIES)
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
    ship = args.ship or rng.choice(list(SHIPS))
    place = args.place or rng.choice(list(PLACES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    supply1 = args.supply1 or rng.choice(list(SUPPLIES))
    supply2 = args.supply2 or rng.choice([k for k in SUPPLIES if k != supply1])
    (captain, captain_gender), (mate, mate_gender) = two_names(rng)
    if args.captain:
        captain = args.captain
    if args.mate:
        mate = args.mate
    params = StoryParams(captain, captain_gender, mate, mate_gender, ship, place, problem, supply1, supply2)
    reasonableness_gate(params)
    return params


def _start(world: World, p: StoryParams) -> tuple[Entity, Entity]:
    cap = world.add(Entity(p.captain, "character", p.captain_gender, role="captain", traits=["bold"]))
    mate = world.add(Entity(p.mate, "character", p.mate_gender, role="mate", traits=["careful"]))
    ship = Ship("ship", p.ship, PLACES[p.place])
    world.ship = ship
    cap.memes["pride"] = 1
    mate.memes["care"] = 1
    world.say(
        f"On a bright day at {PLACES[p.place]}, {cap.id} and {mate.id} climbed aboard {SHIPS[p.ship]}."
    )
    world.say(
        f'They were pretending to be true pirates, looking for a small treasure and a safe way home.'
    )
    return cap, mate


def _problem(world: World, cap: Entity, mate: Entity, p: StoryParams) -> None:
    cap.memes["worry"] += 1
    mate.memes["worry"] += 1
    if p.problem == "dizzy":
        cap.meters["dizzy"] += 1
        cap.meters["incapacitated"] += 1
        world.say(
            f"Then a sudden roll of the waves made {cap.id} wobble."
        )
        world.say(
            f'{cap.id} put a hand to {proun := cap.pronoun("possessive")} forehead and thought, '
            f'"Oh no, I cannot keep climbing like this."'
        )
        world.say(
            f'{mate.id} noticed at once. "Are you all right?" {mate.id} asked.'
        )
    elif p.problem == "thirsty":
        cap.meters["thirst"] += 1
        cap.meters["incapacitated"] += 1
        world.say(f"The sun felt hot, and {cap.id}'s mouth went dry.")
        world.say(f'"I feel too tired to help," {cap.id} thought, biting {cap.pronoun("possessive")} lip.')
        world.say(f'"I need a drink," {cap.id} said softly.')
    else:
        cap.meters["sway"] += 1
        cap.meters["incapacitated"] += 1
        world.say(f"The boat pitched sideways, and {cap.id} had to grab the rail.")
        world.say(f'"I cannot do this alone," {cap.id} thought.')
        world.say(f'"Hold on," {mate.id} said. "I am right here."')


def _share(world: World, cap: Entity, mate: Entity, p: StoryParams) -> None:
    s1, s2 = SUPPLIES[p.supply1], SUPPLIES[p.supply2]
    world.say(
        f'{mate.id} opened the little chest and shared {s1.phrase} and {s2.phrase}.'
    )
    world.say(
        f'"We can help each other," {mate.id} said. "{s1.label_word if hasattr(s1, "label_word") else s1.label} first, then {s2.label}."'
    )
    if s1.kind == "drink" or s2.kind == "drink":
        cap.meters["thirst"] = max(0, cap.meters.get("thirst", 0) - 1)
    if s1.kind == "steady" or s2.kind == "steady":
        cap.meters["shaking"] = 0
        cap.meters["incapacitated"] = max(0, cap.meters.get("incapacitated", 0) - 1)
    if s1.kind == "snack" or s2.kind == "snack":
        cap.memes["hope"] += 1
    cap.memes["trust"] += 1
    mate.memes["care"] += 1
    world.say(f"{cap.id} took a careful breath and felt a little stronger.")


def _turn(world: World, cap: Entity, mate: Entity) -> None:
    if cap.meters.get("incapacitated", 0) >= THRESHOLD:
        world.say(
            f'{cap.id} was still shaky, but {mate.id} climbed the rope and tied the knot for {cap.pronoun("object")}.'
        )
        world.say(
            f'"I can share the job," {mate.id} said. "You can steer from here."'
        )
    else:
        world.say(
            f'{cap.id} stood up straighter. "I am better now," {cap.id} said.'
        )
        world.say(
            f'Inside {cap.id}\'s head, a brave little thought sparkled: "Sharing helped me.' + '"'
        )
    cap.memes["relief"] += 1
    mate.memes["relief"] += 1


def _ending(world: World, cap: Entity, mate: Entity) -> None:
    cap.meters["incapacitated"] = 0
    world.say(
        f"Together they guided the ship back to {world.ship.place}, where the water shone gold and calm."
    )
    world.say(
        f"{cap.id} kept {mate.id}'s hand for a moment, and the little pirate crew felt proud of their kind choice."
    )


def tell(params: StoryParams) -> World:
    w = World()
    cap, mate = _start(w, params)
    w.para()
    _problem(w, cap, mate, params)
    w.para()
    _share(w, cap, mate, params)
    w.para()
    _turn(w, cap, mate)
    w.para()
    _ending(w, cap, mate)
    w.facts.update(params=params, captain=cap, mate=mate, outcome="shared_help", problem=params.problem)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a pirate tale for a young child that uses the word "incapacitate" in a gentle, child-friendly way.',
        f"Tell a story where {p.captain} and {p.mate} are little pirates, one of them becomes unable to help for a moment, and they solve it by sharing supplies.",
        f"Write a pirate adventure with dialogue, an inner thought, and sharing, ending with a safe return to {PLACES[p.place]}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    cap: Entity = world.facts["captain"]
    mate: Entity = world.facts["mate"]
    return [
        QAItem(
            question="What happened to the captain?",
            answer=(
                f"{cap.id} became too shaky to keep helping for a moment, so the story says {cap.pronoun()} was incapacitated. "
                f"That meant {mate.id} had to help with the job until the captain felt better."
            ),
        ),
        QAItem(
            question="How did they help each other?",
            answer=(
                f"{mate.id} shared {SUPPLIES[p.supply1].phrase} and {SUPPLIES[p.supply2].phrase}. "
                f"Sharing gave the captain something useful right away and helped the crew keep going."
            ),
        ),
        QAItem(
            question="What did the captain think at the end?",
            answer=(
                f"{cap.id} thought that sharing had helped and that the little crew could still finish the trip. "
                f"That thought matched the ending, because the pirates reached the harbor together."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does incapacitated mean?",
            answer="It means too unwell, too shaky, or too tired to do the job for a little while.",
        ),
        QAItem(
            question="Why do pirates share supplies?",
            answer="They share supplies so everyone can stay safe, steady, and ready to keep working together.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to each other in the story.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought that the story lets us hear.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} {e.type:8} meters={meters} memes={memes} role={e.role}")
    if world.ship:
        lines.append(f"  ship       name={world.ship.name} place={world.ship.place}")
    return "\n".join(lines)


ASP_RULES = r"""
incapacitated(C) :- character(C), meter(C, incapacitated, V), V >= 1.
shared_help(C) :- character(C), character(M), shared(M, C), incapacitated(C).
outcome(shared_help) :- shared_help(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for key in SHIPS:
        lines.append(asp.fact("ship", key))
    for key in PLACES:
        lines.append(asp.fact("place", key))
    for key in PROBLEMS:
        lines.append(asp.fact("problem", key))
    for key in SUPPLIES:
        lines.append(asp.fact("supply", key))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    return sorted(set(asp.atoms(model, "outcome")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == {("shared_help",)}:
        print("OK: ASP sanity check passed.")
    else:
        rc = 1
        print("MISMATCH: ASP outcome check failed.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generation produced empty story.")
    else:
        print("OK: generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("Lina", "girl", "Bea", "girl", "tiny sloop", "the cove", "dizzy", "water", "rope"),
    StoryParams("Milo", "boy", "Oren", "boy", "little cutter", "the bright harbor", "thirsty", "banana", "water"),
    StoryParams("Nia", "girl", "Tessa", "girl", "round skiff", "the quiet bay", "sway", "blanket", "rope"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("", "#show outcome/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
