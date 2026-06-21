#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sheath_upper_perfection_sharing_lesson_learned_nursery.py
=========================================================================================

A small nursery-rhyme storyworld about sharing a treasured costume piece.

Seed idea:
- A child loves a toy blade with a sheath stored on the upper shelf.
- Another child asks to share it.
- A small conflict turns into a lesson learned.
- The story must include the words: sheath, upper, perfection.

The world is built to produce a few closely related stories, all grounded in a
simple simulation with typed entities, physical meters, and emotional memes.
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
from typing import Optional

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
class Setting:
    id: str
    place: str
    tune: str
    shadow: str
    allowed: set[str] = field(default_factory=set)
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    resting_place: str
    precious: str
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
class ShareItem:
    id: str
    label: str
    phrase: str
    can_share: bool = True
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
class LessonPlan:
    id: str
    promise: str
    lesson: str
    fix: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    treasure: str
    share_item: str
    lesson: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    parent: str
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


SETTINGS = {
    "nursery": Setting(
        id="nursery",
        place="the nursery room",
        tune="soft little hums and bright little toys",
        shadow="the upper shelf",
        allowed={"shelf", "sharing"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        tune="tiny drums and woolly bears",
        shadow="the upper shelf",
        allowed={"shelf", "sharing"},
    ),
}

TREASURES = {
    "sheath": Treasure(
        id="sheath",
        label="a bright toy sheath",
        phrase="a bright toy sheath",
        resting_place="on the upper shelf",
        precious="perfect for the pretend sword",
        tags={"sheath", "upper"},
    ),
    "upper": Treasure(
        id="upper",
        label="the upper shelf treasure",
        phrase="the upper ribbon",
        resting_place="on the upper shelf",
        precious="kept high and neat",
        tags={"upper"},
    ),
    "perfection": Treasure(
        id="perfection",
        label="a little star of perfection",
        phrase="a little star of perfection",
        resting_place="on the upper shelf",
        precious="too special to rush",
        tags={"perfection"},
    ),
}

SHARE_ITEMS = {
    "toy_sword": ShareItem(
        id="toy_sword",
        label="the toy sword",
        phrase="the toy sword and its sheath",
        can_share=True,
        tags={"sharing", "sheath"},
    ),
    "crown": ShareItem(
        id="crown",
        label="the paper crown",
        phrase="the paper crown",
        can_share=True,
        tags={"sharing", "perfection"},
    ),
    "blocks": ShareItem(
        id="blocks",
        label="the little blocks",
        phrase="the little blocks",
        can_share=True,
        tags={"sharing"},
    ),
}

LESSONS = {
    "share_kindly": LessonPlan(
        id="share_kindly",
        promise="share it kindly",
        lesson="sharing makes the play feel bigger",
        fix="handed it over with a smile",
        tags={"sharing"},
    ),
    "take_turns": LessonPlan(
        id="take_turns",
        promise="take turns",
        lesson="turns can keep everyone happy",
        fix="set a little timer and took turns",
        tags={"sharing"},
    ),
    "gentle_words": LessonPlan(
        id="gentle_words",
        promise="use gentle words",
        lesson="gentle words keep the mood sweet",
        fix="spoke softly and passed it along",
        tags={"sharing"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella", "Rose"]
BOY_NAMES = ["Theo", "Finn", "Max", "Owen", "Ben", "Leo"]
TRAITS = ["gentle", "cheery", "patient", "curious", "sweet"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for sid in SETTINGS:
        for tid in TREASURES:
            for iid in SHARE_ITEMS:
                for lid in LESSONS:
                    out.append((sid, tid, iid, lid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about sharing and lessons learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--share-item", choices=SHARE_ITEMS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name-a")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    share_item = args.share_item or rng.choice(list(SHARE_ITEMS))
    lesson = args.lesson or rng.choice(list(LESSONS))
    ga = args.gender_a or rng.choice(["girl", "boy"])
    gb = args.gender_b or ("boy" if ga == "girl" else "girl")
    name_a = args.name_a or rng.choice(GIRL_NAMES if ga == "girl" else BOY_NAMES)
    pool_b = [n for n in (GIRL_NAMES if gb == "girl" else BOY_NAMES) if n != name_a]
    name_b = args.name_b or rng.choice(pool_b)
    parent = args.parent or rng.choice(["mother", "father"])
    if share_item not in SHARE_ITEMS:
        raise StoryError("unknown share item")
    return StoryParams(
        setting=setting,
        treasure=treasure,
        share_item=share_item,
        lesson=lesson,
        child_a=name_a,
        child_a_gender=ga,
        child_b=name_b,
        child_b_gender=gb,
        parent=parent,
    )


def _setup(world: World, a: Entity, b: Entity, parent: Entity, item: ShareItem, treasure: Treasure) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In the {world.setting.id} they played so light, with lullaby steps and voices bright. "
        f"{a.id} and {b.id} found {item.phrase}, and near it a {treasure.label} on {treasure.resting_place}."
    )
    world.say(
        f"\"Oh, look,\" said {a.id}, \"the thing is neat; a little bit of shine, a little treat.\""
    )


def _ask_share(world: World, a: Entity, b: Entity, item: ShareItem, lesson: LessonPlan) -> None:
    a.memes["want"] += 1
    b.memes["want"] += 1
    world.para()
    world.say(
        f"Then {b.id} asked, so soft and fair, \"May I have a turn? May I please share?\" "
        f"{a.id} held tight, with a furrowed brow, for {item.label} felt like perfect now."
    )
    world.say(
        f"But {a.id} remembered {lesson.promise}, and the nursery hummed its sleepy song."
    )


def _turn(world: World, a: Entity, b: Entity, parent: Entity, lesson: LessonPlan, item: ShareItem) -> None:
    a.memes["stubborn"] += 1
    if lesson.id == "take_turns":
        world.say(
            f"Yet {a.id} took a breath, as calm as dew, and counted, \"One and two and three for you.\""
        )
        world.say(
            f"{b.id} waited kindly, with feet together, and soon the two both smiled together."
        )
    elif lesson.id == "gentle_words":
        world.say(
            f"Then {parent.label_word} came near and spoke so sweet, \"Gentle words make kinder feet.\""
        )
        world.say(
            f"{a.id} softened quick, like morning bread, and passed {item.label} ahead."
        )
    else:
        world.say(
            f"{a.id} finally gave a small new grin, and shared {item.label} from within."
        )


def _resolution(world: World, a: Entity, b: Entity, parent: Entity, lesson: LessonPlan, treasure: Treasure) -> None:
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.para()
    world.say(
        f"At last the room was merry and light; the upper shelf shone, the toys felt right. "
        f"{parent.label_word.capitalize()} smiled and said, \"You learned today: {lesson.lesson}.\""
    )
    world.say(
        f"And there, by the shelf with its little glow, the {treasure.label} looked proud below."
    )


def tell(setting: Setting, treasure: Treasure, item: ShareItem, lesson: LessonPlan,
         child_a: str, child_a_gender: str, child_b: str, child_b_gender: str,
         parent_type: str) -> World:
    world = World(setting)
    a = world.add(Entity(id=child_a, kind="character", type=child_a_gender, role="sharer"))
    b = world.add(Entity(id=child_b, kind="character", type=child_b_gender, role="asker"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.facts["item"] = item
    world.facts["lesson"] = lesson
    world.facts["treasure"] = treasure
    world.facts["parent"] = parent
    _setup(world, a, b, parent, item, treasure)
    _ask_share(world, a, b, item, lesson)
    _turn(world, a, b, parent, lesson, item)
    _resolution(world, a, b, parent, lesson, treasure)
    world.facts.update(a=a, b=b, outcome="shared")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "sheath", "upper", and "perfection", and shows sharing in a gentle way.',
        f"Tell a little song-like story where {f['a'].id} and {f['b'].id} share {f['item'].label} and learn a lesson together.",
        f"Write a soft, rhyming story for young children about the upper shelf, a shared treasure, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["a"], f["b"]
    item: ShareItem = f["item"]
    lesson: LessonPlan = f["lesson"]
    treasure: Treasure = f["treasure"]
    return [
        QAItem(
            question="What did the children want to do?",
            answer=f"They wanted to play with {item.phrase} and keep the fun going together. The story turns on whether they can share it kindly."
        ),
        QAItem(
            question=f"What lesson did {a.id} learn?",
            answer=f"{a.id} learned that {lesson.lesson}. That is why {a.id} finally let the play become shared instead of held tight."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with smiles, a kind promise, and the {treasure.label} shining on the upper shelf. The room felt calm because everyone shared and learned together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sheath?",
            answer="A sheath is a cover that helps keep a pretend sword or a sharp tool safe when it is not being used."
        ),
        QAItem(
            question="What does upper mean?",
            answer="Upper means higher up. If something is on the upper shelf, it is placed above the lower things."
        ),
        QAItem(
            question="What does perfection mean?",
            answer="Perfection means something seems just right or wonderfully finished. People sometimes use the word when something feels especially neat or lovely."
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
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="nursery", treasure="sheath", share_item="toy_sword", lesson="share_kindly",
                child_a="Mia", child_a_gender="girl", child_b="Theo", child_b_gender="boy",
                parent="mother"),
    StoryParams(setting="playroom", treasure="perfection", share_item="crown", lesson="take_turns",
                child_a="Lily", child_a_gender="girl", child_b="Ben", child_b_gender="boy",
                parent="father"),
    StoryParams(setting="nursery", treasure="upper", share_item="blocks", lesson="gentle_words",
                child_a="Nora", child_a_gender="girl", child_b="Max", child_b_gender="boy",
                parent="mother"),
]


ASP_RULES = r"""
shared(A,B) :- wants(B), shares(A).
lesson_learned(A) :- shared(A,_).
story_ok(S,T,I,L) :- setting(S), treasure(T), item(I), lesson(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for i in SHARE_ITEMS:
        lines.append(asp.fact("item", i))
    for l in LESSONS:
        lines.append(asp.fact("lesson", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/4."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    ok = clingo_set == python_set
    rc = 0
    if ok:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos().")
        print(" only in clingo:", sorted(clingo_set - python_set))
        print(" only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("treasure", TREASURES), ("share_item", SHARE_ITEMS), ("lesson", LESSONS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    world = tell(
        SETTINGS[params.setting],
        TREASURES[params.treasure],
        SHARE_ITEMS[params.share_item],
        LESSONS[params.lesson],
        params.child_a,
        params.child_a_gender,
        params.child_b,
        params.child_b_gender,
        params.parent,
    )
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    share_item = args.share_item or rng.choice(list(SHARE_ITEMS))
    lesson = args.lesson or rng.choice(list(LESSONS))
    ga = args.gender_a or rng.choice(["girl", "boy"])
    gb = args.gender_b or rng.choice(["girl", "boy"])
    a = args.name_a or rng.choice(GIRL_NAMES if ga == "girl" else BOY_NAMES)
    b_pool = [n for n in (GIRL_NAMES if gb == "girl" else BOY_NAMES) if n != a]
    b = args.name_b or rng.choice(b_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        treasure=treasure,
        share_item=share_item,
        lesson=lesson,
        child_a=a,
        child_a_gender=ga,
        child_b=b,
        child_b_gender=gb,
        parent=parent,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_a} & {p.child_b}: {p.treasure}, {p.share_item}, {p.lesson}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
