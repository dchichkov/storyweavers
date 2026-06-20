#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/toe_pl_paw_icing_curiosity_mystery_to.py
========================================================================

A standalone story world for a small adventure mystery about curious kids, a
paw-shaped clue, and a cake icing mix-up. The domain keeps a gentle, child-facing
tone with a clear beginning, a state-driven middle turn, and a happy ending.

The story premise is:

- a child notices something strange in the kitchen/bakery,
- curiosity leads them to follow paw marks and a mysterious toe-pl,
- the clue trail explains a missing icing decoration,
- a helper fixes the mistake and the ending proves what changed.

Seed words and instruments included in the domain:
- toe-pl
- paw
- icing

Style target:
- Adventure
- Curiosity
- Mystery to Solve
- Happy Ending

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- StoryParams, build_parser, resolve_params, generate, emit, main
- --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate and inline ASP twin
- state-driven stories with QA grounded in world facts
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    id: str
    name: str
    dark_spot: str
    cozy_detail: str

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
class ClueItem:
    id: str
    label: str
    fits: set[str] = field(default_factory=set)
    makes_mess: bool = False
    safe: bool = True

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
class Mystery:
    id: str
    strange_sound: str
    clue_phrase: str
    reveal: str
    ending_image: str
    clue_kind: str
    solution_kind: str

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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

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
@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    mystery: str
    clue: str
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


PLACES = {
    "bakery": Place("bakery", "the bakery", "the flour room", "the warm smell of bread"),
    "kitchen": Place("kitchen", "the kitchen", "the back counter", "the shine of clean bowls"),
    "cafe": Place("cafe", "the tiny cafe", "the pastry shelf", "the hum of morning chatter"),
}

MYSTERIES = {
    "missing_icing": Mystery(
        "missing_icing",
        strange_sound="a soft plip-plip on the floor",
        clue_phrase="a little paw print",
        reveal="the frosting had slid from the tray when the door bumped open",
        ending_image="the cake stood tall again, wearing a bright swirl of icing",
        clue_kind="paw",
        solution_kind="icing",
    ),
    "mystery_toe_pl": Mystery(
        "mystery_toe_pl",
        strange_sound="a tiny toe-pl tap by the table leg",
        clue_phrase="a toe-pl mark on the tile",
        reveal="a tipped bowl had dripped icing in a neat little trail",
        ending_image="the cupcakes shone with fresh icing and the mystery was solved",
        clue_kind="toe-pl",
        solution_kind="icing",
    ),
}

CLUES = {
    "paw": ClueItem("paw", "paw", fits={"paw"}, makes_mess=False, safe=True),
    "toe_pl": ClueItem("toe_pl", "toe-pl", fits={"toe-pl"}, makes_mess=False, safe=True),
    "icing": ClueItem("icing", "icing", fits={"icing"}, makes_mess=True, safe=True),
    "spoon": ClueItem("spoon", "spoon", fits=set(), makes_mess=False, safe=True),
}

GIRL_NAMES = ["Lina", "Mina", "Pia", "Nora", "Tia", "Zoe", "Mila", "Ava"]
BOY_NAMES = ["Oli", "Ben", "Timo", "Noah", "Leo", "Finn", "Jasper", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for mystery in MYSTERIES:
            for clue in CLUES:
                if clue in {"paw", "toe_pl", "icing"}:
                    combos.append((place, mystery, clue))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.clue == "spoon":
        raise StoryError("A spoon is too ordinary for this adventure mystery.")
    if params.mystery == "missing_icing" and params.clue == "toe_pl":
        return
    if params.mystery == "mystery_toe_pl" and params.clue == "paw":
        return
    if params.clue not in {"paw", "toe_pl", "icing"}:
        raise StoryError("This world needs a paw, toe-pl, or icing clue.")


def _do_clue(world: World, clue: ClueItem) -> None:
    ent = world.add(Entity(id=clue.id, type="thing", label=clue.label))
    ent.meters["noticed"] = 1.0
    world.facts["noticed_clue"] = clue.id


def solve_mystery(world: World, mystery: Mystery, hero: Entity, helper: Entity, clue: ClueItem) -> None:
    world.say(
        f"At {world.place.name}, {hero.id} heard {mystery.strange_sound} and stopped to look."
    )
    world.say(
        f"{hero.id} pointed at {mystery.clue_phrase}. "
        f'"Look," {hero.pronoun()} said, "that clue might tell us what happened."'
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0.0) + 1
    _do_clue(world, clue)
    if clue.id == mystery.clue_kind:
        world.say(
            f"{helper.id} crouched beside {hero.pronoun('object')} and followed the clue trail carefully."
        )
        world.say(f"They found out that {mystery.reveal}.")
        world.say(
            f"Then {helper.id} fixed the icing with gentle hands, and soon {mystery.ending_image}."
        )
    else:
        world.say(
            f"Still, {helper.id} used {clue.label} to search the room until the answer came into view."
        )
        world.say(f"They finally saw that {mystery.reveal}.")
        world.say(
            f"After that, {helper.id} put the icing back in place, and {mystery.ending_image}."
        )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.facts["solved"] = True


def tell(place: Place, mystery: Mystery, clue: ClueItem, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="cake", type="thing", label="cake"))
    world.add(Entity(id="tray", type="thing", label="tray"))
    world.facts.update(place=place, mystery=mystery, clue=clue, hero=hero, helper=helper)

    world.say(
        f"{hero.id} and {helper.id} were on an adventure at {place.name}. {place.cozy_detail} made the room feel safe."
    )
    world.say(
        f"Then a mystery began. They heard {mystery.strange_sound}, and both of them wanted to know why."
    )
    world.para()
    solve_mystery(world, mystery, hero, helper, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    mystery = f["mystery"]
    clue = f["clue"]
    hero = f["hero"]
    helper = f["helper"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "{clue.label}" and ends happily.',
        f"Tell a curious mystery story where {hero.id} and {helper.id} explore {place.name}, notice a {clue.label}, and solve what happened to the icing.",
        f'Write a child-facing adventure with curiosity, a clue, and icing that ends with a bright happy image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    clue: ClueItem = f["clue"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {helper.id}, who went on a small adventure together."
        ),
        QAItem(
            question="What clue did they notice?",
            answer=f"They noticed a {clue.label}. That clue helped them look more closely at the mystery."
        ),
        QAItem(
            question=f"What did they learn happened to the icing?",
            answer=f"They learned that {mystery.reveal}. After that, the icing was put right back where it belonged."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. {mystery.ending_image.capitalize()}."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does icing do on a cake?",
            answer="Icing makes a cake sweet, smooth, and pretty. It is often spread on top in swirls or layers."
        ),
        QAItem(
            question="What is a paw print?",
            answer="A paw print is the mark an animal's paw leaves behind on the floor or ground."
        ),
        QAItem(
            question="What is a toe-pl mark?",
            answer="A toe-pl mark is a tiny made-up kind of footprint clue in this story world. It helps the characters look for answers."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
noticed_clue(C) :- clue(C).
solved(M) :- mystery(M), clue_kind(M, C), noticed_clue(C).
happy_end(M) :- solved(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("strange_sound", mid, m.strange_sound))
        lines.append(asp.fact("clue_kind", mid, m.clue_kind))
        lines.append(asp.fact("solution_kind", mid, m.solution_kind))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, hero=None, hero_type=None, helper=None, helper_type=None, mystery=None, clue=None, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"FAIL: generation smoke test failed: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny curiosity mystery adventure with icing and clue marks.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    clue = args.clue or MYSTERIES[mystery].clue_kind
    if clue not in {"paw", "toe_pl", "icing"}:
        raise StoryError("This mystery world needs a paw, toe-pl, or icing clue.")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    if hero == helper:
        helper = helper + "a"
    reasonableness_check(StoryParams(place, hero, hero_type, helper, helper_type, mystery, clue))
    return StoryParams(place, hero, hero_type, helper, helper_type, mystery, clue)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], CLUES[params.clue],
                 params.hero, params.hero_type, params.helper, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_qa(world)],
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
    StoryParams("bakery", "Lina", "girl", "Oli", "boy", "missing_icing", "paw"),
    StoryParams("kitchen", "Milo", "boy", "Mina", "girl", "mystery_toe_pl", "toe_pl"),
    StoryParams("cafe", "Ava", "girl", "Finn", "boy", "missing_icing", "icing"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
