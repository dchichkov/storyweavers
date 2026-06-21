#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/moss_big_tote_sharing_tall_tale.py
===================================================================

A standalone story world for a tiny Tall Tale about sharing a marvelous find:
a child brings home a big tote full of moss, someone wants to keep it all, and a
calm helper turns the moment into a fair share with a bright ending image.

The world is built around:
- typed entities with physical meters and emotional memes
- a small causal simulation
- a reasonableness gate
- an inline ASP twin
- story-grounded QA and world-knowledge QA
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
    lush: bool = False
    homey: bool = False
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
class Treasure:
    id: str
    label: str
    phrase: str
    source: str
    shareable: bool = True
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
class ShareMethod:
    id: str
    sense: int
    text: str
    success: str
    fail: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    moss = world.entities.get("moss")
    if moss and moss.meters["split"] >= THRESHOLD:
        sig = ("soften",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in list(world.entities.values()):
                if kid.kind == "character":
                    kid.memes["wonder"] += 1
            out.append("__wonder__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


CAUSAL_RULES = [Rule("soften", "social", _r_soften)]


def use_share_method(method: ShareMethod) -> bool:
    return method.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for treasure_id, treasure in TREASURES.items():
            for method_id, method in METHODS.items():
                if place.lush and treasure.shareable and use_share_method(method):
                    combos.append((place_id, treasure_id, method_id))
    return combos


def story_setting(place: Place, treasure: Treasure) -> bool:
    return place.lush and treasure.shareable


def build_world(place: Place, treasure: Treasure, method: ShareMethod,
                big_tote: str, giver: str, sharer: str, helper: str,
                giver_gender: str, sharer_gender: str, helper_gender: str,
                seed: Optional[int] = None) -> World:
    world = World()
    giver_ent = world.add(Entity(id=giver, kind="character", type=giver_gender, role="giver"))
    sharer_ent = world.add(Entity(id=sharer, kind="character", type=sharer_gender, role="sharer"))
    helper_ent = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    moss_ent = world.add(Entity(id="moss", type="thing", label="moss"))
    tote_ent = world.add(Entity(id="tote", type="thing", label="big tote"))
    world.facts.update(
        place=place, treasure=treasure, method=method,
        big_tote=big_tote, giver=giver_ent, sharer=sharer_ent, helper=helper_ent,
        moss=moss_ent, tote=tote_ent, seed=seed,
    )

    giver_ent.memes["pride"] += 1
    sharer_ent.memes["want"] += 1
    helper_ent.memes["kindness"] += 1
    moss_ent.meters["bundle"] += 1
    tote_ent.meters["full"] += 1

    world.say(
        f"On a day so wide it seemed to stretch from one sunrise to the next, "
        f"{giver} came trotting home with a {big_tote} full of moss from {place.label}."
    )
    world.say(
        f"The moss was green as a song and soft as a cloud's underside. "
        f"{giver} laughed, lifted the tote high, and told the tale of where it came from."
    )
    world.para()
    world.say(
        f"But {sharer} wanted the whole heap for {sharer_ent.pronoun('possessive')} own little wonder-corner."
    )
    world.say(
        f'"That moss is mine!" {sharer} cried, hugging the tote as if it were a treasure chest.'
    )
    world.say(
        f"{helper} raised a hand gentle as rain. {helper_ent.pronoun().capitalize()} said, "
        f'"A thing this fine grows fairer when it is shared."'
    )

    world.para()
    if not use_share_method(method):
        world.say("The way they tried would not have been fair or wise.")
        return world

    sharer_ent.memes["stingy"] += 1
    world.say(
        f'At last, {helper} showed them {method.text}.'
    )
    moss_ent.meters["split"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With {method.text}, the big tote was opened like a book, and the moss was parted into two soft pillows."
    )
    world.say(
        f"{method.success}."
    )
    world.say(
        f"{giver} kept one little nest, {sharer} kept the other, and the two children smiled as if the moon had nodded at them."
    )
    world.para()
    world.say(
        f"By sunset, the {big_tote} stood by the porch like a great green boat, "
        f"and the moss sat in two neat mounds, one for each hand."
    )

    world.facts["outcome"] = "shared"
    world.facts["shared"] = True
    return world


def make_story(world: World) -> str:
    return world.render()


@dataclass
class StoryParams:
    place: str
    treasure: str
    method: str
    giver: str
    giver_gender: str
    sharer: str
    sharer_gender: str
    helper: str
    helper_gender: str
    big_tote: str = "big tote"
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
    "woods": Place(id="woods", label="the mossy woods", lush=True, tags={"moss", "woods"}),
    "brook": Place(id="brook", label="the brook bank", lush=True, tags={"moss", "water"}),
    "hill": Place(id="hill", label="the green hill", lush=True, tags={"moss", "hill"}),
}

TREASURES = {
    "moss_patch": Treasure(id="moss_patch", label="moss", phrase="a patch of moss", source="woods", tags={"moss"}),
    "moss_bundle": Treasure(id="moss_bundle", label="moss", phrase="a great bundle of moss", source="brook", tags={"moss"}),
}

METHODS = {
    "share_by_handfuls": ShareMethod(id="share_by_handfuls", sense=3, text="they took turns scooping handfuls into each palm", success="They shared it fair and square", fail="They could not sort the share at all", tags={"sharing"}),
    "share_by_halves": ShareMethod(id="share_by_halves", sense=4, text="they split the heap down the middle with a twig and a kind word", success="Each child got an even half", fail="The split went crooked and the sharing failed", tags={"sharing"}),
    "share_with_bowls": ShareMethod(id="share_with_bowls", sense=2, text="they used two little bowls and measured out an equal scoop to each", success="The bowls made the sharing plain to see", fail="The bowls were too small for the task", tags={"sharing"}),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Zoe", "Ava", "Ivy"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Finn", "Theo", "Max"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story for a child that includes the words "moss", "big", and "tote" and teaches sharing.',
        f"Tell a whimsical story where {f['giver'].id} brings home a big tote full of moss and {f['sharer'].id} wants to keep it all, but a helper makes sharing feel fair.",
        f'Create a gentle, folksy story about sharing a big tote of moss, with a bright ending that shows how the moss was divided.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    giver, sharer, helper = f["giver"], f["sharer"], f["helper"]
    qa = [
        QAItem(
            question="What did the children find?",
            answer="They found a big tote full of moss. It was a soft, green treasure from the woods, and it was so fine that both children wanted a part of it.",
        ),
        QAItem(
            question="Why did they need to share?",
            answer=f"{sharer.id} wanted the whole heap, but {helper.id} reminded everyone that a thing this fine grows fairer when it is shared. That turned the moment from a tug-of-war into a calm plan.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the moss split into two neat portions. Each child got a share, the big tote rested by the porch, and the day closed like a lantern being set down easy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is moss?",
            answer="Moss is a soft, green plant that often grows in damp, shady places. It feels springy and can make a patch of ground look like a little carpet.",
        ),
        QAItem(
            question="What is a tote?",
            answer="A tote is a bag or carrier with room for carrying things. A big tote can hold a surprising load, like moss gathered from a green bank.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use or enjoy something. When children share, everybody gets a fair turn or a fair piece, and the fun lasts longer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: Place, treasure: Treasure) -> str:
    return f"(No story: {place.label} does not fit a fair sharing tale for {treasure.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place or rng.choice(sorted(PLACES))
    treasure_id = args.treasure or rng.choice(sorted(TREASURES))
    method_id = args.method or rng.choice(sorted(METHODS))
    place = PLACES[place_id]
    treasure = TREASURES[treasure_id]
    method = METHODS[method_id]
    if not story_setting(place, treasure):
        raise StoryError(explain_rejection(place, treasure))
    if not use_share_method(method):
        raise StoryError("(No story: that sharing method is not reasonable enough.)")
    giver_gender = args.giver_gender or rng.choice(["girl", "boy"])
    sharer_gender = args.sharer_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    giver = args.giver or rng.choice(GIRL_NAMES if giver_gender == "girl" else BOY_NAMES)
    sharer = args.sharer or rng.choice([n for n in (GIRL_NAMES if sharer_gender == "girl" else BOY_NAMES) if n != giver])
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n not in {giver, sharer}])
    return StoryParams(
        place=place_id, treasure=treasure_id, method=method_id,
        giver=giver, giver_gender=giver_gender,
        sharer=sharer, sharer_gender=sharer_gender,
        helper=helper, helper_gender=helper_gender,
        big_tote=args.big_tote or "big tote",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.treasure not in TREASURES or params.method not in METHODS:
        raise StoryError("Invalid parameters.")
    world = build_world(
        PLACES[params.place], TREASURES[params.treasure], METHODS[params.method],
        params.big_tote, params.giver, params.sharer, params.helper,
        params.giver_gender, params.sharer_gender, params.helper_gender, params.seed,
    )
    return StorySample(
        params=params,
        story=make_story(world),
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


ASP_RULES = r"""
shareable(T) :- treasure(T), shareable_treasure(T).
good_place(P) :- place(P), lush(P).
reasonable(M) :- method(M), sense(M,S), sense_min(N), S >= N.
valid(P,T,M) :- good_place(P), shareable(T), reasonable(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.lush:
            lines.append(asp.fact("lush", pid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.shareable:
            lines.append(asp.fact("shareable_treasure", tid))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, m.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        import asp
        _ = asp_valid_combos()
    except Exception as exc:
        print(f"ASP failure: {exc}")
        return 1
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        print("MISMATCH between Python and ASP gate.")
        print("python-only:", sorted(py - clingo))
        print("asp-only:", sorted(clingo - py))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, treasure=None, method=None,
            giver_gender=None, sharer_gender=None, helper_gender=None,
            giver=None, sharer=None, helper=None, big_tote="big tote",
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    print(f"OK: {len(py)} valid combos; generation smoke test passed.")
    return 0


@dataclass
class StoryParams:
    place: str
    treasure: str
    method: str
    giver: str
    giver_gender: str
    sharer: str
    sharer_gender: str
    helper: str
    helper_gender: str
    big_tote: str = "big tote"
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


CURATED = [
    StoryParams(place="woods", treasure="moss_patch", method="share_by_halves", giver="Tom", giver_gender="boy", sharer="Maya", sharer_gender="girl", helper="Nora", helper_gender="girl", big_tote="big tote", seed=1),
    StoryParams(place="brook", treasure="moss_bundle", method="share_with_bowls", giver="Ava", giver_gender="girl", sharer="Leo", sharer_gender="boy", helper="Ben", helper_gender="boy", big_tote="big tote", seed=2),
    StoryParams(place="hill", treasure="moss_patch", method="share_by_handfuls", giver="Finn", giver_gender="boy", sharer="Ivy", sharer_gender="girl", helper="Zoe", helper_gender="girl", big_tote="big tote", seed=3),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale sharing story world about moss and a big tote.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--giver")
    ap.add_argument("--giver-gender", dest="giver_gender", choices=["girl", "boy"])
    ap.add_argument("--sharer")
    ap.add_argument("--sharer-gender", dest="sharer_gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["girl", "boy"])
    ap.add_argument("--big-tote", dest="big_tote", default="big tote")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for p, t, m in asp_valid_combos():
            print(f"  {p} {t} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.giver}, {p.sharer}, and the {p.method} of moss"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
