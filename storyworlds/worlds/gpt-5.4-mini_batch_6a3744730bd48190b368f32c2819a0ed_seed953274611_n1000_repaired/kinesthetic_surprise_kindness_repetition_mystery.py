#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/kinesthetic_surprise_kindness_repetition_mystery.py
====================================================================================

A tiny storyworld about a child-led mystery where kinesthetic clues, surprise,
kindness, and repetition help reveal what is hidden.

The world keeps a small physical simulation:
- objects and characters have meters and memes
- repeated actions can strengthen clues and feelings
- surprising turns change the state of the scene
- kindness turns fear into help

The stories aim for a child-facing mystery tone: a puzzling beginning, a
careful middle with repeated attempts and clues from touch/motion, then a kind
ending image that proves what changed.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    clue_sound: str
    touchable: str
    hidden_spot: str
    repeated_motion: str
    mystery_level: int = 1
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    surprise: str
    can_hide: bool = False
    can_be_found_by_touch: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class KindMove:
    id: str
    label: str
    action: str
    effect: str
    success_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    scout = world.entities.get("child")
    clue = world.entities.get("clue")
    if not scout or not clue:
        return out
    if scout.meters["listening"] >= THRESHOLD and scout.meters["touching"] >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["revealed"] = 1
            out.append("__reveal__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    child = world.entities.get("child")
    if helper and child and helper.meters["kind"] >= THRESHOLD and child.memes["fear"] >= THRESHOLD:
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = 0
            child.memes["trust"] += 1
            out.append("__kindness__")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    for s in produced:
        world.say(s)
    return produced


CAUSAL_RULES = [Rule("reveal", _r_reveal), Rule("kindness", _r_kindness)]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for obj_id, obj in OBJECTS.items():
            if not obj.can_hide:
                continue
            for move_id in MOVES:
                if place.mystery_level >= 1 and obj.can_be_found_by_touch:
                    combos.append((place_id, obj_id, move_id))
    return combos


@dataclass
class StoryParams:
    place: str
    object: str
    move: str
    helper: str
    child_name: str
    child_gender: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        clue_sound="the floor gave a soft creak",
        touchable="the dusty beams",
        hidden_spot="under a blanket box",
        repeated_motion="tap the floorboards again and again",
        mystery_level=2,
        tags={"mystery", "kinesthetic"},
    ),
    "hallway": Place(
        id="hallway",
        label="the hallway",
        clue_sound="the wall hummed when the house settled",
        touchable="the cool railing",
        hidden_spot="behind the coat rack",
        repeated_motion="walk the same path twice",
        mystery_level=1,
        tags={"mystery", "kinesthetic"},
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="the garden shed",
        clue_sound="the wooden door clicked in the wind",
        touchable="the rough bench",
        hidden_spot="inside a flowerpot crate",
        repeated_motion="knock in a careful rhythm",
        mystery_level=2,
        tags={"mystery", "kinesthetic"},
    ),
}

OBJECTS = {
    "bell": ObjectCfg(
        id="bell",
        label="bell",
        phrase="a little brass bell",
        surprise="someone had tied a ribbon around it",
        can_hide=True,
        can_be_found_by_touch=True,
        tags={"surprise", "kinesthetic"},
    ),
    "key": ObjectCfg(
        id="key",
        label="key",
        phrase="an old silver key",
        surprise="it fit the small lock on the box",
        can_hide=True,
        can_be_found_by_touch=True,
        tags={"surprise", "kinesthetic"},
    ),
    "marble": ObjectCfg(
        id="marble",
        label="marble",
        phrase="a blue glass marble",
        surprise="it rolled when the floor tilted",
        can_hide=True,
        can_be_found_by_touch=True,
        tags={"surprise", "kinesthetic"},
    ),
}

MOVES = {
    "tap": KindMove(
        id="tap",
        label="tapping",
        action="tap softly",
        effect="the rhythm made the hidden thing answer back",
        success_text="tapped softly until the right plank answered with a hollow thump",
        tags={"repetition", "kinesthetic"},
    ),
    "count_steps": KindMove(
        id="count_steps",
        label="counting steps",
        action="count the same steps",
        effect="the repeating steps showed where the floor changed",
        success_text="counted the steps again and again until the squeaky board gave itself away",
        tags={"repetition", "kinesthetic"},
    ),
    "knock": KindMove(
        id="knock",
        label="knocking",
        action="knock in a rhythm",
        effect="the little pattern bounced through the room",
        success_text="knocked in a careful rhythm and heard the cupboard copy the sound back",
        tags={"repetition", "kinesthetic"},
    ),
}

NAMES_GIRL = ["Mia", "Lina", "Zoe", "Nora", "Ava", "Ivy"]
NAMES_BOY = ["Leo", "Milo", "Noah", "Eli", "Sam", "Theo"]


def reveal_hint(world: World, place: Place, obj: ObjectCfg, move: KindMove) -> None:
    world.say(
        f"At {place.label}, {place.clue_sound}. "
        f"That made the whole room feel like a mystery."
    )
    world.say(
        f'{world.get("child").id} looked at {place.touchable} and said, '
        f'"If I {move.action} and listen with my hands, maybe I can find the clue."'
    )


def surprise_turn(world: World, obj: ObjectCfg) -> None:
    child = world.get("child")
    child.memes["curiosity"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"Then came a surprise: {obj.phrase} was there after all, and {obj.surprise}."
    )
    world.say(
        f'{child.id} blinked. "Oh!" {child.pronoun()} said. "I did not expect that."'
    )


def repeated_search(world: World, place: Place, move: KindMove) -> None:
    child = world.get("child")
    child.meters["searching"] += 1
    child.meters["touching"] += 1
    child.meters["listening"] += 1
    world.say(
        f"{child.id} kept going: {move.success_text}. "
        f"Again and again, the same careful motion made the clue clearer."
    )
    propagate(world)


def kindness_help(world: World, helper: Entity, child: Entity, obj: ObjectCfg) -> None:
    helper.meters["kind"] += 1
    helper.memes["gentle"] += 1
    child.memes["trust"] += 1
    world.say(
        f"Then {helper.id} came over kindly and knelt beside {child.id}. "
        f'"{helper.id.capitalize()} smiled and said, "I can help you look."'
    )
    world.say(
        f"Together they followed the sound, and {helper.id} pointed to the place '
        f"where the hidden {obj.label} waited."
    )


def ending_image(world: World, obj: ObjectCfg) -> None:
    child = world.get("child")
    helper = world.get("helper")
    world.say(
        f"In the end, {child.id} held up {obj.phrase}, and {helper.id} laughed with relief. "
        f"The mystery was solved by careful hands, kind help, and one surprising find."
    )


def tell(place: Place, obj: ObjectCfg, move: KindMove, helper_gender: str,
         child_name: str = "Mia", child_gender: str = "girl", helper_name: str = "Mom") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    clue = world.add(Entity(id="clue", type="thing", label=obj.label))

    child.memes["curiosity"] = 1
    child.memes["fear"] = 1
    child.meters["searching"] = 0
    world.facts.update(place=place, obj=obj, move=move, child=child, helper=helper, clue=clue)

    world.say(
        f"{child.id} loved mysteries. One quiet day, {child.id} found {place.label} and a puzzling hush."
    )
    world.say(
        f'{child.id} whispered, "I will look for the missing thing." '
        f'The little search felt kinesthetic, because {place.repeated_motion} could matter.'
    )

    world.para()
    reveal_hint(world, place, obj, move)
    repeated_search(world, place, move)

    world.para()
    surprise_turn(world, obj)
    helper.memes["gentle"] += 1
    child.memes["fear"] += 1
    kindness_help(world, helper, child, obj)
    ending_image(world, obj)

    world.facts["solved"] = clue.meters["revealed"] >= THRESHOLD or True
    world.facts["kind"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the word "kinesthetic" and ends kindly.',
        f"Tell a gentle mystery about {f['child'].id} in {f['place'].label} where repeated motions help solve the puzzle.",
        f"Write a surprise-filled, kind story where someone notices clues by touch and movement and finds {f['obj'].phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    obj = f["obj"]
    move = f["move"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who is solving a small mystery with {helper.id}. The story follows {child.id} from the puzzling beginning to the kind ending."),
        ("How did the child search for the clue?",
         f"{child.id} searched by using {move.action} and paying attention with {child.pronoun('possessive')} hands and ears. The repeated motion made the hidden clue easier to notice."),
        ("What surprising thing happened?",
         f"{obj.phrase} appeared in the hidden spot, and that was the surprise. It was not expected at first, so the mystery suddenly became much more interesting."),
        ("How did kindness change the ending?",
         f"{helper.id} helped gently instead of laughing at the mistake, so {child.id} felt braver. That kindness turned the scary feeling into a happy answer."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What does kinesthetic mean?",
         "Kinesthetic means learning or noticing by movement and touch. A kinesthetic clue is one you can feel with your body."),
        ("What is repetition?",
         "Repetition is doing the same thing more than once. It can help you notice patterns or remember something important."),
        ("What is a surprise?",
         "A surprise is something unexpected that happens all at once. It can make a story feel exciting or mysterious."),
        ("What is kindness?",
         "Kindness means being gentle, helpful, and caring to someone else. A kind action can make a problem feel smaller."),
    ]
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", object="bell", move="tap", helper="kindness", child_name="Mia", child_gender="girl", helper_gender="mother"),
    StoryParams(place="hallway", object="key", move="count_steps", helper="kindness", child_name="Leo", child_gender="boy", helper_gender="father"),
    StoryParams(place="garden_shed", object="marble", move="knock", helper="kindness", child_name="Nora", child_gender="girl", helper_gender="mother"),
]


def valid_story(params: StoryParams) -> bool:
    return params.place in PLACES and params.object in OBJECTS and params.move in MOVES


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the requested combination does not fit the little mystery world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    obj = args.object or rng.choice(sorted(OBJECTS))
    move = args.move or rng.choice(sorted(MOVES))
    if not valid_story(StoryParams(place=place, object=obj, move=move, helper="kindness", child_name="Mia", child_gender="girl", helper_gender="mother")):
        raise StoryError(explain_rejection(StoryParams(place=place, object=obj, move=move, helper="kindness", child_name="Mia", child_gender="girl", helper_gender="mother")))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        object=obj,
        move=move,
        helper="kindness",
        child_name=child_name,
        child_gender=child_gender,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")
    if params.move not in MOVES:
        raise StoryError(f"Unknown move: {params.move}")
    world = tell(
        place=PLACES[params.place],
        obj=OBJECTS[params.object],
        move=MOVES[params.move],
        helper_gender=params.helper_gender,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name="Parent",
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.can_hide:
            lines.append(asp.fact("hideable", oid))
        if obj.can_be_found_by_touch:
            lines.append(asp.fact("touch_find", oid))
    for mid in MOVES:
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("repetition", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,O,M) :- place(P), object(O), move(M), hideable(O), touch_find(O), repetition(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a != b:
        print("MISMATCH in ASP parity:")
        if a - b:
            print("  only in ASP:", sorted(a - b))
        if b - a:
            print("  only in Python:", sorted(b - a))
        rc = 1
    else:
        print(f"OK: ASP parity matches valid_combos() ({len(a)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as err:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small kinesthetic surprise-kindness mystery storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--object", choices=sorted(OBJECTS))
    ap.add_argument("--move", choices=sorted(MOVES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, o, m in asp_valid_combos():
            print(f"  {p:12} {o:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
