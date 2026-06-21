#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fascinator_rowdy_concern_foreshadowing_detective_story.py
=========================================================================================

A standalone story world for a small detective tale with foreshadowing:
a child detective notices a rowdy scene, feels concern, spots planted clues,
and follows them to recover a missing fascinator.

The seed words are woven into the simulated world:
- fascinator
- rowdy
- concern

Style:
- Detective story
- Child-facing
- State-driven, with foreshadowing as a first-class narrative instrument
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    label: str
    detail: str
    indoors: bool = True

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
class Clue:
    id: str
    label: str
    hint: str
    reveal: str
    leads_to: str

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
class Item:
    id: str
    label: str
    phrase: str
    special: str = ""
    plural: bool = False
    misplaced_in: str = ""

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
class Suspect:
    id: str
    label: str
    rowdy_level: int
    innocence: int
    clue: str
    method: str

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_rowdy(world: World) -> list[str]:
    out: list[str] = []
    crowd = world.get("crowd")
    if crowd.meters["rowdy"] < THRESHOLD:
        return out
    sig = ("rowdy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("detective", "owner"):
        world.get(eid).memes["concern"] += 1
    crowd.meters["noise"] += 1
    out.append("__rowdy__")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("ribbon")
    if clue.meters["noticed"] < THRESHOLD:
        return out
    sig = ("foreshadow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("detective").memes["certainty"] += 1
    out.append("__foreshadow__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    hat = world.get("fascinator")
    if hat.meters["found"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("rowdy", "social", _r_rowdy),
    Rule("foreshadow", "clue", _r_foreshadow),
    Rule("reveal", "plot", _r_reveal),
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


def predict_missing(world: World) -> dict:
    sim = world.copy()
    sim.get("fascinator").meters["hidden"] = 1.0
    sim.get("ribbon").meters["noticed"] = 1.0
    propagate(sim, narrate=False)
    return {
        "found": bool(sim.get("fascinator").meters["found"] >= THRESHOLD),
        "concern": sim.get("detective").memes["concern"],
    }


def setup(world: World, detective: Entity, owner: Entity, place: Place) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"On a bright morning at {place.label}, {detective.id} arrived with a notebook "
        f"and a careful look in {detective.pronoun('possessive')} eyes. "
        f"{place.detail}"
    )
    world.say(
        f"{owner.id} stood nearby, trying to keep the room calm, but there was already a "
        f"little concern in the air."
    )


def introduce_case(world: World, fascinator: Item, suspect: Suspect) -> None:
    world.say(
        f"The case was a small one, but important: a {fascinator.label} had gone missing. "
        f"It had glittered on the table just a moment ago, and then the rowdy crowd jostled "
        f"past."
    )
    world.say(
        f"{suspect.label} was the loudest of them all, bumping chairs, laughing too hard, "
        f"and leaving everyone with the feeling that something had gone wrong."
    )


def foreshadow_clue(world: World, clue: Clue) -> None:
    world.get(clue.id).meters["noticed"] += 1
    world.say(
        f"Near the table, {clue.hint}. {clue.reveal}"
    )
    world.say(
        f"{world.get('detective').id} wrote it down at once. The clue pointed toward "
        f"{clue.leads_to}, and that made {world.get('detective').pronoun('possessive')} "
        f"thoughts very sharp."
    )


def suspect_noise(world: World, suspect: Suspect) -> None:
    world.get("crowd").meters["rowdy"] += suspect.rowdy_level
    world.say(
        f"{suspect.label} had been rowdy all morning, so rowdy that even the teacups seemed "
        f"to tremble."
    )


def search(world: World, detective: Entity, clue: Clue, item: Item) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} followed the ribbon's hint first, then moved to {clue.leads_to}. "
        f"There, tucked where the sunlight landed, was a tiny sparkle."
    )
    item.meters["found"] += 1
    world.say(
        f"It was the missing {item.label}, resting exactly where the clue had promised."
    )


def explain(world: World, owner: Entity, detective: Entity, item: Item) -> None:
    owner.memes["relief"] += 1
    world.say(
        f"{owner.id} gasped with relief, then smiled at {detective.id}. "
        f'"You noticed the clues before anyone else," {owner.pronoun()} said. '
        f'"That is exactly what a good detective does."'
    )
    world.say(
        f"{detective.id} placed the {item.label} back where it belonged, and the room "
        f"grew calm again."
    )


def ending(world: World, detective: Entity, owner: Entity, item: Item, place: Place) -> None:
    detective.memes["pride"] += 1
    world.say(
        f"By the end, the rowdy noise had faded, the concern had melted away, and the "
        f"{item.label} was safe again."
    )
    world.say(
        f"At {place.label}, {detective.id} closed {detective.pronoun('possessive')} notebook "
        f"beside the recovered {item.label}, and the case was finished with a neat little smile."
    )


def tell(place: Place, fascinator: Item, clue: Clue, suspect: Suspect,
         detective_name: str = "Nina", detective_gender: str = "girl",
         owner_name: str = "Mrs. Bell", owner_gender: str = "woman") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender,
                                 role="detective", traits=["careful", "sharp"]))
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender,
                             role="owner", traits=["worried"]))
    crowd = world.add(Entity(id="crowd", kind="thing", type="crowd", label="the crowd"))
    world.add(Entity(id="fascinator", kind="thing", type="item", label=fascinator.label))
    world.add(Entity(id="ribbon", kind="thing", type="clue", label="a ribbon scrap"))
    world.facts["place"] = place
    world.facts["fascinator"] = fascinator
    world.facts["clue"] = clue
    world.facts["suspect"] = suspect
    world.facts["detective"] = detective
    world.facts["owner"] = owner

    setup(world, detective, owner, place)
    world.para()
    introduce_case(world, fascinator, suspect)
    suspect_noise(world, suspect)
    foreshadow_clue(world, clue)
    world.para()
    search(world, detective, clue, fascinator)
    explain(world, owner, detective, fascinator)
    ending(world, detective, owner, fascinator, place)

    world.facts.update(
        crowd=crowd,
        found=fascinator.meters["found"] >= THRESHOLD,
        concern=detective.memes["concern"],
    )
    return world


PLACES = {
    "tea_room": Place(
        "tea_room", "the tea room",
        "The little tables were set with spoons and napkins, and a window let in a stripe of gold."
    ),
    "museum": Place(
        "museum", "the costume museum",
        "Glass cases lined the hall, and a velvet rope made the room feel important and quiet."
    ),
    "library": Place(
        "library", "the library hall",
        "Tall shelves stood like careful towers, and a reading rug made the room soft and calm."
    ),
}

FASCINATORS = {
    "blue": Item("blue", "blue fascinator", "a blue fascinator with a silver flower"),
    "pearl": Item("pearl", "pearl fascinator", "a pearl fascinator with a ribbon curl"),
    "rose": Item("rose", "rose fascinator", "a rose fascinator with tiny beads"),
}

CLUES = {
    "ribbon": Clue("ribbon", "ribbon scrap", "a ribbon scrap fluttered by the table leg",
                   "It matched the ribbon on the hatband.", "the sunny window ledge"),
    "glitter": Clue("glitter", "glitter trail", "a few glitter specks sparkled on the floor",
                    "They looked like they had fallen from something fancy.", "the display shelf"),
    "feather": Clue("feather", "feather tip", "a soft feather had snagged on a chair",
                    "It twirled exactly like the little trim on a hat.", "the coat rack"),
}

SUSPECTS = {
    "barker": Suspect("barker", "a rowdy balloon seller", 2, 3, "a balloon string trailing behind", "bumping through the crowd"),
    "kids": Suspect("kids", "some rowdy children", 3, 4, "a sock and a skipped step", "racing too fast"),
    "dog": Suspect("dog", "a rowdy little dog", 2, 5, "a wagging tail and a muddy pawprint", "darting under tables"),
}


@dataclass
@dataclass
class StoryParams:
    place: str
    fascinator: str
    clue: str
    suspect: str
    detective_name: str
    detective_gender: str
    owner_name: str
    owner_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in PLACES:
        for f in FASCINATORS:
            for c in CLUES:
                combos.append((p, f, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].label
    fasc = f["fascinator"].label
    clue = f["clue"].hint
    suspect = f["suspect"].label
    return [
        f'Write a detective story for a young child set at {place} where a {fasc} goes missing and a clue is foreshadowed before the reveal.',
        f"Tell a calm mystery story that includes the words 'fascinator', 'rowdy', and 'concern', and lets the detective solve the case by following {clue}.",
        f"Write a small foreshadowing story where {suspect} makes the room rowdy, the detective feels concern, and the missing hat is found in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det: Entity = f["detective"]
    owner: Entity = f["owner"]
    place: Place = f["place"]
    fasc: Item = f["fascinator"]
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    return [
        ("Who solved the mystery?",
         f"{det.id} solved it by paying attention to the clues and staying calm."),
        ("What was missing?",
         f"The missing item was {fasc.phrase}. It had been on the table before the crowd got rowdy."),
        ("Why did the detective feel concern?",
         f"{det.id} felt concern because the room was rowdy and the fascinator had vanished. The clue on the floor made the worry feel important, because it pointed to where the hat had gone."),
        ("What clue helped?",
         f"{clue.reveal} That foreshadowing clue led straight to {clue.leads_to}, where the fascinator was found."),
        ("How did the story end?",
         f"It ended happily with the fascinator back in place and the room calm again. The rowdy noise faded, and the detective closed the notebook with a smile."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a fascinator?",
         "A fascinator is a small fancy hat decoration, often worn at special events."),
        ("What does rowdy mean?",
         "Rowdy means loud, rough, and hard to keep calm."),
        ("What is concern?",
         "Concern is a worried feeling you get when something may be wrong."),
        ("What is foreshadowing?",
         "Foreshadowing is when a story gives a small hint early on about something that will matter later."),
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
rowdy :- crowd_rowdy.
foreshadow :- noticed(ribbon).
found :- clue_to(window) ; clue_to(shelf) ; clue_to(rack).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FASCINATORS:
        lines.append(asp.fact("fascinator", fid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show place/1."))
    return sorted(set(asp.atoms(model, "place")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((p,) for p, _, _ in valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} places).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, fascinator=None, clue=None, suspect=None,
            detective_name=None, detective_gender=None, owner_name=None,
            owner_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"FAILED: generate smoke test crashed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--fascinator", choices=FASCINATORS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-name")
    ap.add_argument("--owner-gender", choices=["woman", "man", "girl", "boy"])
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
    fascinator = args.fascinator or rng.choice(list(FASCINATORS))
    clue = args.clue or rng.choice(list(CLUES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    og = args.owner_gender or rng.choice(["woman", "man"])
    dn = args.detective_name or (rng.choice(["Nina", "Mila", "Ruby", "June"]) if dg == "girl" else rng.choice(["Owen", "Leo", "Eli", "Max"]))
    on = args.owner_name or (rng.choice(["Mrs. Bell", "Ms. Lane", "Aunt May"]) if og in {"woman", "girl"} else rng.choice(["Mr. Cole", "Uncle Ray"]))
    return StoryParams(place, fascinator, clue, suspect, dn, dg, on, og)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], FASCINATORS[params.fascinator],
                 CLUES[params.clue], SUSPECTS[params.suspect],
                 params.detective_name, params.detective_gender,
                 params.owner_name, params.owner_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("tea_room", "pearl", "ribbon", "barker", "Nina", "girl", "Mrs. Bell", "woman"),
    StoryParams("museum", "rose", "glitter", "dog", "Mila", "girl", "Aunt May", "woman"),
    StoryParams("library", "blue", "feather", "kids", "Owen", "boy", "Mr. Cole", "man"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} candidate story settings.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
