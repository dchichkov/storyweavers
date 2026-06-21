#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/visit_intense_bed_lesson_learned_bedtime_story.py
=================================================================================

A tiny standalone storyworld for a bedtime-style tale about a visit that feels
intense, a bed that becomes important, and a lesson learned by the end.

Premise
-------
A child goes to visit a cozy place, the feeling gets intense as bedtime nears,
and a wise helper guides the child toward a calmer choice and a softer ending.
The story must naturally include the words "visit", "intense", and "bed", and
should end with a clear lesson learned.

The world is small on purpose:
- typed entities with physical meters and emotional memes
- one forward-chained causal engine
- a reasonableness gate over allowed combinations
- a Python/ASP twin for parity checking
- three QA sets generated from simulated world state, not by parsing prose

This script is self-contained except for the shared result containers and ASP
helper modules from the Storyweavers repo.
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
CALM_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
class Setting:
    id: str
    place: str
    mood: str
    detail: str
    afford: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    worry: str
    zone: set[str]
    intense: int
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
class Bed:
    id: str
    label: str
    phrase: str
    comfort: str
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
class Guide:
    id: str
    label: str
    suggestion: str
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


def _r_intense(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["intensity"] < THRESHOLD:
            continue
        sig = ("intense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child = world.entities.get("child")
        if child is not None:
            child.memes["overwhelm"] += 1
        out.append("__intense__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    guide = world.entities.get("guide")
    if child is None or guide is None:
        return out
    if child.memes["calm"] < THRESHOLD or child.memes["lesson"] < THRESHOLD:
        return out
    sig = ("calm", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["rest"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("intense", "emotional", _r_intense),
    Rule("calm", "emotional", _r_calm),
]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            if aid not in setting.afford:
                continue
            for gid, bed in BEDS.items():
                if act.zone & bed.tags:
                    combos.append((sid, aid, gid))
    return combos


def reasonableness(setting: Setting, activity: Activity, bed: Bed) -> bool:
    return activity.id in setting.afford and bool(activity.zone & bed.tags)


def would_settle(activity: Activity, guide: Guide) -> bool:
    return activity.intense <= guide_threshold(guide)


def guide_threshold(guide: Guide) -> int:
    return 2 if "gentle" in guide.tags else 3


def predict(world: World, activity: Activity) -> dict:
    sim = world.copy()
    sim.get("child").memes["intensity"] += activity.intense
    propagate(sim, narrate=False)
    return {
        "overwhelm": sim.get("child").memes["overwhelm"],
        "rest": sim.get("child").meters["rest"],
    }


def start_visit(world: World, child: Entity, host: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} went to visit {host.id} at {setting.place}. "
        f"{setting.detail}"
    )


def build_tension(world: World, child: Entity, activity: Activity, bed: Bed) -> None:
    child.memes["intensity"] += activity.intense
    world.say(
        f"At first, the evening felt {setting_descriptor(world)}. "
        f"{child.id} wanted one more look around, and everything seemed {activity.worry}."
    )
    world.say(
        f"Then {child.id} noticed the {bed.label} waiting nearby, soft and quiet."
    )


def setting_descriptor(world: World) -> str:
    return world.facts["setting"].mood


def warn(world: World, guide: Entity, child: Entity, activity: Activity, bed: Bed, host: Entity) -> None:
    pred = predict(world, activity)
    child.memes["worry"] += 1
    world.facts["predicted_overwhelm"] = pred["overwhelm"]
    world.say(
        f"{guide.id} smiled softly and said, "
        f'"It is getting late. Let’s keep this visit calm, because the {bed.label} '
        f'is for rest, not rushing."'
    )
    if pred["overwhelm"] >= THRESHOLD:
        world.say(
            f"{host.label_word.capitalize()} nodded too, and reminded {child.id} that "
            f"tired feelings can get intense when bedtime is near."
        )


def defy(world: World, child: Entity, activity: Activity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} tried to make the moment louder and more intense, even though "
        f"the room was supposed to be winding down."
    )


def choose_bed(world: World, child: Entity, bed: Bed, guide: Entity) -> None:
    child.memes["calm"] += 1
    world.say(
        f"Then {guide.id} led {child.id} to the {bed.label}. "
        f"{bed.comfort}"
    )


def lesson(world: World, child: Entity, guide: Entity, bed: Bed, activity: Activity) -> None:
    child.memes["lesson"] += 1
    child.memes["worry"] = 0.0
    child.memes["overwhelm"] = 0.0
    world.say(
        f"{child.id} took a slow breath and curled up on the {bed.label}. "
        f'"I learned something," {child.id} whispered. "When a visit feels intense, '
        f'it helps to get quiet and choose rest."'
    )
    world.say(
        f"{guide.id} tucked the blanket in and smiled. The lesson learned made the "
        f"whole room softer, and the {bed.label} looked warm and safe."
    )


def tell(setting: Setting, activity: Activity, bed: Bed, guide: Guide,
         child_name: str = "Mia", child_gender: str = "girl",
         host_name: str = "Grandma", host_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child"))
    host = world.add(Entity(id=host_name, kind="character", type=host_gender,
                            role="host", label="the host"))
    helper = world.add(Entity(id=guide.id, kind="character", type="woman",
                              role="guide", label=guide.label))
    world.facts["setting"] = setting
    world.facts["activity"] = activity
    world.facts["bed"] = bed
    world.facts["guide"] = guide

    start_visit(world, child, host, setting)
    world.para()
    build_tension(world, child, activity, bed)
    warn(world, helper, child, activity, bed, host)
    defy(world, child, activity)
    world.para()
    choose_bed(world, child, bed, helper)
    lesson(world, child, helper, bed, activity)

    world.facts.update(
        child=child, host=host, guide=helper, outcome="lesson_learned",
        intense=activity.intense, rested=child.meters["rest"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "visit_home": Setting(
        id="visit_home",
        place="Grandma's house",
        mood="cozy but intense",
        detail="The hallway was dim, and the clock was ticking toward bedtime.",
        afford={"visit"},
    ),
    "visit_room": Setting(
        id="visit_room",
        place="Auntie's quiet room",
        mood="soft and serious",
        detail="The little lamp made the shadows small, but the feelings were still big.",
        afford={"visit"},
    ),
}

ACTIVITIES = {
    "visit": Activity(
        id="visit",
        verb="visit",
        worry="full of big thoughts",
        zone={"torso"},
        intense=2,
        tags={"visit"},
    ),
    "intense_visit": Activity(
        id="intense_visit",
        verb="visit again",
        worry="so intense it made the air feel tight",
        zone={"torso"},
        intense=3,
        tags={"visit", "intense"},
    ),
}

BEDS = {
    "bed": Bed(
        id="bed",
        label="bed",
        phrase="the bed",
        comfort="The quilt was smooth, the pillow was plump, and the room finally felt like a lullaby.",
        tags={"bed"},
    ),
    "tall_bed": Bed(
        id="tall_bed",
        label="bed",
        phrase="the high bed",
        comfort="The mattress gave a tiny bounce, then settled down like a sleepy cloud.",
        tags={"bed"},
    ),
}

GUIDES = {
    "lesson_guide": Guide(
        id="guide",
        label="a gentle grown-up",
        suggestion="slow down and rest",
        lesson="A lesson learned is safest when it is simple and kind.",
        tags={"gentle", "lesson"},
    ),
}

@dataclass
class StoryParams:
    theme: str
    activity: str
    bed: str
    guide: str
    child_name: str = "Mia"
    child_gender: str = "girl"
    host_name: str = "Grandma"
    host_gender: str = "woman"
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
    StoryParams(theme="visit_home", activity="visit", bed="bed", guide="lesson_guide",
                child_name="Mia", child_gender="girl", host_name="Grandma", host_gender="woman", seed=7),
    StoryParams(theme="visit_room", activity="intense_visit", bed="tall_bed", guide="lesson_guide",
                child_name="Noah", child_gender="boy", host_name="Auntie", host_gender="woman", seed=8),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "visit", "intense", and "bed".',
        f"Tell a gentle story where {f['child'].id} goes on a visit, the feeling becomes intense, "
        f"and a kind helper guides the child back to the bed.",
        f"Write a small bedtime story with a lesson learned at the end, using a bed as the calm place.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, host, guide, setting, bed, activity = (
        f["child"], f["host"], f["guide"], f["setting"], f["bed"], f["activity"]
    )
    return [
        ("Who went on the visit?",
         f"{child.id} went on the visit to {setting.place}. The story follows the child as the evening grows more intense and bedtime gets closer."),
        ("What helped calm the story down?",
         f"The {bed.label} helped calm everything down. {guide.id} guided {child.id} there so the feelings could settle and the lesson could be learned."),
        ("What did the child learn?",
         f"{child.id} learned that when a visit feels intense, it helps to slow down and choose rest. The bed became the quiet ending that proved the change."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bed for?",
         "A bed is a soft place where people rest and sleep. It helps the body and mind slow down at bedtime."),
        ("What does visit mean?",
         "To visit means to go see someone for a little while. A visit can be happy, quiet, or exciting."),
        ("What does intense mean?",
         "Intense means very strong or powerful. A feeling can be intense when it is hard to ignore."),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_setting_keys() -> list[str]:
    return list(SETTINGS.keys())


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.theme and args.theme not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.bed and args.bed not in BEDS:
        raise StoryError("Unknown bed.")
    if args.guide and args.guide not in GUIDES:
        raise StoryError("Unknown guide.")

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.activity is None or c[1] == args.activity)
        and (args.bed is None or c[2] == args.bed)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, activity, bed = rng.choice(sorted(combos))
    guide = args.guide or "lesson_guide"
    child_name = rng.choice(["Mia", "Noah", "Lily", "Eli", "Ava"])
    child_gender = rng.choice(["girl", "boy"])
    host_name = rng.choice(["Grandma", "Auntie", "Uncle Ben", "Papa"])
    host_gender = "woman" if host_name in {"Grandma", "Auntie"} else "man"
    return StoryParams(
        theme=theme,
        activity=activity,
        bed=bed,
        guide=guide,
        child_name=child_name,
        child_gender=child_gender,
        host_name=host_name,
        host_gender=host_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in SETTINGS:
        raise StoryError("Invalid theme.")
    if params.activity not in ACTIVITIES:
        raise StoryError("Invalid activity.")
    if params.bed not in BEDS:
        raise StoryError("Invalid bed.")
    if params.guide not in GUIDES:
        raise StoryError("Invalid guide.")
    setting = SETTINGS[params.theme]
    activity = ACTIVITIES[params.activity]
    bed = BEDS[params.bed]
    guide = GUIDES[params.guide]
    if not reasonableness(setting, activity, bed):
        raise StoryError("This combination does not make a plausible bedtime story.")
    world = tell(setting, activity, bed, guide, params.child_name, params.child_gender, params.host_name, params.host_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a visit, an intense feeling, a bed, and a lesson learned.")
    ap.add_argument("--theme", choices=list(SETTINGS.keys()))
    ap.add_argument("--activity", choices=list(ACTIVITIES.keys()))
    ap.add_argument("--bed", choices=list(BEDS.keys()))
    ap.add_argument("--guide", choices=list(GUIDES.keys()))
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for bid in BEDS:
        lines.append(asp.fact("bed", bid))
    for sid, setting in SETTINGS.items():
        for aid in setting.afford:
            lines.append(asp.fact("affords", sid, aid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("intense", aid, act.intense))
        for z in sorted(act.zone):
            lines.append(asp.fact("zone", aid, z))
    for bid, bed in BEDS.items():
        for t in sorted(bed.tags):
            lines.append(asp.fact("bed_tag", bid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,B) :- affords(S,A), zone(A,Z), bed_tag(B,Z).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.theme} / {p.activity} / {p.bed}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
