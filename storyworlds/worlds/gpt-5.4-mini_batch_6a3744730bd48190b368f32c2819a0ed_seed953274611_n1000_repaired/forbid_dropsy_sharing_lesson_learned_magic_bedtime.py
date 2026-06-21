#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/forbid_dropsy_sharing_lesson_learned_magic_bedtime.py
=====================================================================================

A small bedtime storyworld about a child, a magical object, a sharing dispute,
a wobbly mistake, and a lesson learned.

The seed asks for the words "forbid" and "dropsy" plus the features
Sharing, Lesson Learned, and Magic in a bedtime-story style. This world
turns that into a tiny simulation: a child and a sibling or friend want to
share a magic bedtime glow, someone tries to forbid the sharing, the object
gets a "dropsy" wobble when handled clumsily, and a grown-up helps turn the
moment into a calm lesson.

The script follows the shared StorySample / QAItem contract and includes a
Python reasonableness gate plus an inline ASP twin.
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
BRIGHT = 1.0
WOBBLE = 1.0


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
    magical: bool = False
    shareable: bool = False
    forbid_unsafe: bool = False
    can_wobble: bool = False

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
    hush: str
    bedtime: str
    cozy: str
    share_scene: str
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
class MagicThing:
    id: str
    label: str
    glow: str
    touch: str
    share_use: str
    fragile: bool = False
    shareable: bool = True
    can_wobble: bool = True
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
class Interruption:
    id: str
    label: str
    sense: int
    effect: int
    text: str
    lesson: str
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
class StoryParams:
    setting: str
    magic: str
    interruption: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    relation: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("wobble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "lamp" in world.entities:
            world.get("lamp").meters["dim"] += 1
        for kid in world.characters():
            if kid.role in {"child1", "child2"}:
                kid.memes["unease"] += 1
        out.append("__wobble__")
    return out


CAUSAL_RULES = [Rule("wobble", "physical", _r_wobble)]


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


def bedtime_reasonable(setting: Setting, magic: MagicThing, interruption: Interruption) -> bool:
    return magic.shareable and interruption.sense >= 2 and magic.magical


def safe_fix_candidates() -> list[Interruption]:
    return [i for i in INTERRUPTIONS.values() if i.sense >= 2]


def preferred_fix() -> Interruption:
    return max(INTERRUPTIONS.values(), key=lambda x: x.sense)


def act_share(world: World, a: Entity, b: Entity, magic: MagicThing) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At bedtime, {a.id} and {b.id} shared {magic.label} in the soft glow of the room. "
        f"{magic.share_use}."
    )


def act_forbid(world: World, a: Entity, parent: Entity, magic: MagicThing) -> None:
    a.memes["hurt"] += 1
    world.say(
        f"{a.id} tried to share, but {parent.label_word} said it was safe to {parent.pronoun('object')} "
        f"to forbid the mean little tug of grabbing."
    )


def act_drop(world: World, a: Entity, magic_ent: Entity, magic: MagicThing) -> None:
    a.memes["careless"] += 1
    magic_ent.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {a.id}'s fingers went dropsy and the magic {magic.label} wobbled in {a.pronoun('possessive')} hands. "
        f"{magic.touch}."
    )


def act_alarm(world: World, b: Entity, a: Entity, parent: Entity, magic: MagicThing) -> None:
    world.say(
        f"{b.id} whispered, '{a.id}, be gentle.' When the wobble grew, {b.id} called, "
        f"\"{parent.label_word.capitalize()}!\""
    )


def act_fix(world: World, parent: Entity, fix: Interruption, magic_ent: Entity, magic: MagicThing) -> None:
    magic_ent.meters["wobble"] = 0.0
    world.get("lamp").meters["dim"] = 0.0
    for kid in world.characters():
        if kid.role in {"child1", "child2"}:
            kid.memes["unease"] = 0.0
            kid.memes["love"] += 1
    body = fix.text.replace("{magic}", magic.label)
    world.say(f"{parent.label_word.capitalize()} came in and {body}.")
    world.say(f"The room grew calm again, and the little glow waited quietly for sharing.")


def act_lesson(world: World, parent: Entity, a: Entity, b: Entity, magic: MagicThing, fix: Interruption) -> None:
    for kid in world.characters():
        if kid.role in {"child1", "child2"}:
            kid.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt beside them and gave the bedtime lesson: "
        f"\"Sharing can be gentle, and {magic.label} needs careful hands. {fix.lesson}\""
    )
    world.say(
        f"{a.id} nodded. {b.id} nodded too. They promised to ask before taking and to hold the glow together."
    )


def act_cozy_end(world: World, a: Entity, b: Entity, magic: MagicThing) -> None:
    a.memes["peace"] += 1
    b.memes["peace"] += 1
    world.say(
        f"After that, {a.id} and {b.id} sat side by side, passing {magic.label} back and forth like a tiny moon. "
        f"The bedtime room stayed warm, quiet, and kind."
    )


def tell(setting: Setting, magic: MagicThing, interruption: Interruption,
         child1: str = "Mia", child1_gender: str = "girl",
         child2: str = "Noah", child2_gender: str = "boy",
         parent: str = "Mom", relation: str = "siblings") -> World:
    world = World(setting)
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="child1"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="child2"))
    ptype = "mother" if parent.lower() in {"mom", "mother"} else "father"
    mom = world.add(Entity(id=parent, kind="character", type=ptype, role="parent", label="the parent"))
    lamp = world.add(Entity(id="lamp", kind="thing", type="lamp", label="the lamp"))
    mag = world.add(Entity(id="magic", kind="thing", type="magic", label=magic.label, magical=True, shareable=True, can_wobble=True))

    world.say(
        f"{a.id} and {b.id} lived in {setting.place}, where {setting.cozy}. {setting.bedtime}"
    )
    world.say(
        f"At the end of the day, they discovered {magic.label}, which gave off {magic.glow}."
    )

    world.para()
    act_share(world, a, b, magic)
    act_forbid(world, a, mom, magic)
    act_drop(world, a, mag, magic)
    act_alarm(world, b, a, mom, magic)

    world.para()
    fix = interruption
    act_fix(world, mom, fix, mag, magic)
    act_lesson(world, mom, a, b, magic, fix)

    world.para()
    act_cozy_end(world, a, b, magic)

    world.facts.update(
        child1=a, child2=b, parent=mom, setting=setting, magic=magic,
        interruption=fix, lamp=lamp, outcome="lesson"
    )
    return world


SETTINGS = {
    "moonroom": Setting(
        id="moonroom",
        place="the moonroom",
        hush="soft hush",
        bedtime="The curtains were drawn, and only a sleepy stripe of moonlight reached the rug.",
        cozy="a quilted bed, two pillows, and one teddy bear waiting for a story",
        share_scene="a little bedside table where treasures could rest",
    ),
    "treehouse": Setting(
        id="treehouse",
        place="the treehouse",
        hush="gentle hush",
        bedtime="The ladder was tucked away, and the windows were full of stars.",
        cozy="blankets, a tiny shelf, and one lantern by the pillow",
        share_scene="a narrow ledge by the window for shared treasures",
    ),
    "nursery": Setting(
        id="nursery",
        place="the nursery",
        hush="warm hush",
        bedtime="The room was ready for sleep, with blankets tucked up and a cradle rocking softly.",
        cozy="a rocking chair, a soft rug, and a basket of bedtime books",
        share_scene="a little shelf beside the crib",
    ),
}

MAGICS = {
    "glowstone": MagicThing(
        id="glowstone",
        label="glowstone",
        glow="a pearl-blue sparkle",
        touch="It was bright, but it needed gentle hands.",
        share_use="It liked to be passed carefully from palm to palm",
        fragile=True,
        shareable=True,
        can_wobble=True,
        tags={"magic", "share"},
    ),
    "dreambell": MagicThing(
        id="dreambell",
        label="dreambell",
        glow="a silver tingle",
        touch="It chimed when someone held it too hard.",
        share_use="It sounded sweetest when two people held it together",
        fragile=False,
        shareable=True,
        can_wobble=True,
        tags={"magic", "share"},
    ),
    "starfeather": MagicThing(
        id="starfeather",
        label="starfeather",
        glow="a golden shimmer",
        touch="It fluttered if fingers got clumsy.",
        share_use="It was made for careful sharing",
        fragile=True,
        shareable=True,
        can_wobble=True,
        tags={"magic", "share"},
    ),
}

INTERRUPTIONS = {
    "forbid": Interruption(
        id="forbid",
        label="forbid",
        sense=2,
        effect=1,
        text="softly steadied the magic between their hands",
        lesson="You do not need to grab what can be shared.",
        tags={"forbid", "lesson"},
    ),
    "lesson": Interruption(
        id="lesson",
        label="lesson learned",
        sense=3,
        effect=2,
        text="showed them how to take turns and count to three before passing {magic}",
        lesson="A shared thing stays sweeter when everyone gets a turn.",
        tags={"lesson", "share"},
    ),
    "magic_lantern": Interruption(
        id="magic lantern",
        label="magic lantern",
        sense=4,
        effect=3,
        text="lifted a small magic lantern beside them, making the room calm and bright",
        lesson="Magic feels safest when it is used with patience.",
        tags={"magic", "lesson"},
    ),
}

CURATED = [
    StoryParams(setting="moonroom", magic="glowstone", interruption="lesson", child1="Mia", child1_gender="girl", child2="Noah", child2_gender="boy", parent="Mom", relation="siblings", seed=None),
    StoryParams(setting="treehouse", magic="dreambell", interruption="forbid", child1="Ada", child1_gender="girl", child2="Ben", child2_gender="boy", parent="Dad", relation="friends", seed=None),
    StoryParams(setting="nursery", magic="starfeather", interruption="magic_lantern", child1="Ivy", child1_gender="girl", child2="Leo", child2_gender="boy", parent="Mom", relation="siblings", seed=None),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, magic in MAGICS.items():
            for iid, intr in INTERRUPTIONS.items():
                if bedtime_reasonable(setting, magic, intr):
                    combos.append((sid, mid, iid))
    return combos


def explain_rejection(setting: Setting, magic: MagicThing, intr: Interruption) -> str:
    if not magic.shareable:
        return f"(No story: {magic.label} cannot be shared, so it doesn't fit the sharing lesson.)"
    if not magic.magical:
        return f"(No story: {magic.label} is not magical enough for this bedtime world.)"
    if intr.sense < 2:
        return f"(No story: the interruption '{intr.label}' is too weak to make a clear lesson.)"
    return "(No story: this combination doesn't make a bedtime sharing story.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, magic, intr = f["child1"], f["child2"], f["magic"], f["interruption"]
    return [
        f'Write a bedtime story that includes the words "forbid" and "dropsy" and features {magic.label}.',
        f"Tell a gentle sharing story where {a.id} and {b.id} handle {magic.label}, one child says forbid, and a grown-up turns the trouble into a lesson learned.",
        f"Write a magical bedtime scene with {magic.label}, a small wobble or dropsy mistake, and a calm ending about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, magic, intr = f["child1"], f["child2"], f["parent"], f["magic"], f["interruption"]
    return [
        QAItem(
            question="What were the children trying to do?",
            answer=f"They were trying to share {magic.label} at bedtime. They wanted the glow to belong to both of them, not just one child.",
        ),
        QAItem(
            question="What happened when the sharing got clumsy?",
            answer=f"{a.id}'s fingers went dropsy and the magic {magic.label} wobbled. That wobble made the room uneasy, so they called for help.",
        ),
        QAItem(
            question=f"Why did the parent step in?",
            answer=f"The parent stepped in because one child tried to forbid the sharing and the magic needed careful hands. The grown-up calmed the wobble and turned the moment into a lesson learned.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the children sharing {magic.label} gently again. They learned that magic feels better when it is passed kindly and watched carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic = f["magic"]
    intr = f["interruption"]
    out = []
    out.append(QAItem(
        question="What does it mean to share something?",
        answer="To share means to let more than one person use or enjoy the same thing by taking turns or holding it together.",
    ))
    out.append(QAItem(
        question="What is a bedtime story?",
        answer="A bedtime story is a calm story told at night to help children feel safe, sleepy, and cozy.",
    ))
    if intr.id == "forbid":
        out.append(QAItem(
            question="What does it mean to forbid something?",
            answer="To forbid something means to say it is not allowed. It is a strong way of stopping a choice.",
        ))
    out.append(QAItem(
        question="What is magic in a story?",
        answer="Magic in a story is something special that can glow, sing, or change in a way real things usually do not.",
    ))
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
        if e.magical:
            bits.append("magical")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
shareable(magic).
magical(magic).

valid(S,M,I) :- setting(S), magic(M), interruption(I), shareable(M), magical(M), sense(I,SN), SN >= 2.
wobble_happens(M) :- magical(M), shareable(M).
lesson_happens(I) :- interruption(I), sense(I,SN), SN >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        if m.shareable:
            lines.append(asp.fact("shareable", mid))
        if m.magical:
            lines.append(asp.fact("magical", mid))
    for iid, i in INTERRUPTIONS.items():
        lines.append(asp.fact("interruption", iid))
        lines.append(asp.fact("sense", iid, i.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP gate differs from valid_combos().")
        rc = 1

    # Smoke test: ordinary generation must not crash.
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, magic=None, interruption=None, child1=None, child1_gender=None, child2=None, child2_gender=None, parent=None, relation=None), random.Random(777)))
        _ = sample.story
        _ = sample.to_json()
        print("OK: default generation smoke test succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        print(f"FAILED smoke test: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld with sharing, magic, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--interruption", choices=INTERRUPTIONS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["Mom", "Dad"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
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
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    magic_id = args.magic or rng.choice(sorted(MAGICS))
    intr_id = args.interruption or rng.choice(sorted(INTERRUPTIONS))

    if args.setting and args.magic and args.interruption:
        if not bedtime_reasonable(SETTINGS[args.setting], MAGICS[args.magic], INTERRUPTIONS[args.interruption]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], MAGICS[args.magic], INTERRUPTIONS[args.interruption]))

    if not bedtime_reasonable(SETTINGS[setting_id], MAGICS[magic_id], INTERRUPTIONS[intr_id]):
        raise StoryError(explain_rejection(SETTINGS[setting_id], MAGICS[magic_id], INTERRUPTIONS[intr_id]))

    c1_gender = args.child1_gender or rng.choice(["girl", "boy"])
    c2_gender = args.child2_gender or ("boy" if c1_gender == "girl" else "girl")
    c1 = args.child1 or rng.choice(["Mia", "Ivy", "Ava", "Nora", "Luna", "Ada"])
    c2 = args.child2 or rng.choice([n for n in ["Noah", "Ben", "Leo", "Owen", "Finn", "Eli"] if n != c1])
    parent = args.parent or rng.choice(["Mom", "Dad"])
    relation = args.relation or rng.choice(["siblings", "friends"])

    return StoryParams(
        setting=setting_id,
        magic=magic_id,
        interruption=intr_id,
        child1=c1,
        child1_gender=c1_gender,
        child2=c2,
        child2_gender=c2_gender,
        parent=parent,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.magic not in MAGICS:
        raise StoryError("Unknown magic item.")
    if params.interruption not in INTERRUPTIONS:
        raise StoryError("Unknown interruption.")
    world = tell(
        SETTINGS[params.setting],
        MAGICS[params.magic],
        INTERRUPTIONS[params.interruption],
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        parent=params.parent,
        relation=params.relation,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, m, i in combos:
            print(f"  {s:10} {m:12} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child1} & {p.child2}: {p.magic} / {p.interruption}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
