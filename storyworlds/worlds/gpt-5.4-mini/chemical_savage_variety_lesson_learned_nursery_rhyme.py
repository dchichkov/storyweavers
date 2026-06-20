#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chemical_savage_variety_lesson_learned_nursery_rhyme.py
=======================================================================================

A small standalone storyworld inspired by a nursery-rhyme style lesson:
two children make a playful "chemical" concoction with a savage smell,
try a variety of ingredients, and learn a gentle safety lesson when a
grown-up steers them toward a proper, harmless experiment.

The world is intentionally tiny and constraint-driven: it only generates
stories when the combination is reasonable, it keeps the prose state-driven,
and it includes a Python reasonableness gate plus an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/chemical_savage_variety_lesson_learned_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/chemical_savage_variety_lesson_learned_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/chemical_savage_variety_lesson_learned_nursery_rhyme.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/chemical_savage_variety_lesson_learned_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/chemical_savage_variety_lesson_learned_nursery_rhyme.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Setting:
    id: str
    label: str
    place: str
    safe_table: str
    song_line: str
    ending_image: str
    affords: set[str] = field(default_factory=set)

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
class Activity:
    id: str
    verb: str
    merrymaking: str
    stir: str
    mess: str
    zone: set[str]
    keyword: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool
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
class Reagent:
    id: str
    label: str
    phrase: str
    risky: bool
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
class Compromise:
    id: str
    label: str
    phrase: str
    fix: str
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


def _r_alarm(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["spill"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in list(world.entities.values()):
            if c.kind == "character":
                c.memes["concern"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def reasonableness_gate(reagent: Reagent, prize: Prize, activity: Activity) -> bool:
    return reagent.risky and prize.region in activity.zone and prize.fragile


def best_compromise() -> Compromise:
    return max(COMPROMISES.values(), key=lambda c: len(c.fix))


def would_learn(relation: str, helper_age: int, maker_age: int) -> bool:
    return relation == "siblings" and helper_age > maker_age


def predict_spill(world: World, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(prize_id).meters["spill"] += 1
    propagate(sim, narrate=False)
    return sim.get(prize_id).meters["spill"] >= THRESHOLD


def _do_mix(world: World, maker: Entity, reagent: Reagent, prize: Entity) -> None:
    maker.meters["spill"] += 1
    prize.meters["spill"] += 1
    propagate(world, narrate=False)


def intro(world: World, maker: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"Under the {setting.label}, {maker.id} and {helper.id} began to sing, "
        f"while the kettle ticked and the sunlight blinked awake."
    )
    world.say(
        f'"{setting.song_line}" {maker.id} hummed, and {helper.id} laughed along.'
    )


def desire(world: World, maker: Entity, activity: Activity, reagent: Reagent) -> None:
    maker.memes["want"] += 1
    world.say(
        f"{maker.id} wanted a {activity.keyword} game with a {reagent.label} surprise, "
        f"for a little chemical show can look quite bright."
    )


def warn(world: World, helper: Entity, maker: Entity, reagent: Reagent, prize: Prize) -> None:
    maker.memes["bravado"] += 1
    world.say(
        f"{helper.id} wrinkled {helper.pronoun('possessive')} nose and said, "
        f'"No, no, dear {maker.id}, that can be savage for the room. '
        f'Keep the {reagent.label} away from the {prize.label}."'
    )


def defy(world: World, maker: Entity, reagent: Reagent) -> None:
    world.say(
        f'"But I want a variety," {maker.id} said, and {maker.id} stirred anyway, '
        f"as if a tiny storm were in the spoon."
    )
    maker.memes["defiance"] += 1
    maker.meters["spill"] += 1


def spill(world: World, maker: Entity, helper: Entity, prize: Prize) -> None:
    maker.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"Then whoosh went the bowl, and a splash leapt to the {prize.label}."
    )
    world.say(
        f"{helper.id} clapped a hand to {helper.pronoun('possessive')} mouth. "
        f'"The {prize.label} is getting ruined!"'
    )


def grownup_fix(world: World, grownup: Entity, compromise: Compromise, prize: Prize) -> None:
    prize.meters["spill"] = 0.0
    world.get("room").meters["mess"] = 0.0
    world.say(
        f"{grownup.label_word.capitalize()} came in, calm as a lullaby, and "
        f"{compromise.fix}."
    )
    world.say(
        f"The splash quieted at once, and the room smelled like soap instead of trouble."
    )


def lesson(world: World, grownup: Entity, maker: Entity, helper: Entity, reagent: Reagent) -> None:
    maker.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    maker.memes["fear"] = 0.0
    helper.memes["fear"] = 0.0
    world.say(
        f"{grownup.label_word.capitalize()} knelt by the table and said, "
        f'"The lesson learned is simple: {reagent.label} is not for wild mixing, '
        f"and grown-ups must help with chemicals."
    )
    world.say(
        f"{maker.id} nodded slow and small, and {helper.id} nodded too."
    )


def happy_finish(world: World, setting: Setting, maker: Entity, helper: Entity, compromise: Compromise) -> None:
    maker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, they chose a {compromise.label} game instead, and the table "
        f"was only full of safe bubbles and giggles."
    )
    world.say(
        f"By evening, {setting.ending_image}, and the little pair sang on."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, reagent: Reagent,
         compromise: Compromise, maker_name: str = "Milly", maker_type: str = "girl",
         helper_name: str = "Benny", helper_type: str = "boy",
         grownup_type: str = "mother", relation: str = "siblings",
         maker_age: int = 4, helper_age: int = 6) -> World:
    world = World(setting)
    maker = world.add(Entity(id=maker_name, kind="character", type=maker_type, role="maker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    grownup = world.add(Entity(id="Grownup", kind="character", type=grownup_type, role="grownup"))
    world.add(Entity(id="room", type="room", label="the room"))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label))
    maker.memes["curiosity"] = 1
    helper.memes["care"] = 1
    world.facts["relation"] = relation
    world.facts["maker_age"] = maker_age
    world.facts["helper_age"] = helper_age

    intro(world, maker, helper, setting)
    world.para()
    desire(world, maker, activity, reagent)
    warn(world, helper, maker, reagent, prize_cfg)
    can_learn = would_learn(relation, helper_age, maker_age)
    if not can_learn:
        raise StoryError("This storyworld prefers an older helper in the lesson-learned role.")

    defy(world, maker, reagent)
    world.para()
    spill(world, maker, helper, prize)
    world.para()
    grownup_fix(world, grownup, compromise, prize)
    lesson(world, grownup, maker, helper, reagent)
    world.para()
    happy_finish(world, setting, maker, helper, compromise)

    world.facts.update(
        maker=maker, helper=helper, grownup=grownup, prize=prize,
        activity=activity, reagent=reagent, compromise=compromise,
        outcome="lesson"
    )
    return world


SETTINGS = {
    "nursery": Setting(
        "nursery", "the nursery", "the nursery",
        "Little ducks on the wallpaper went quack, quack, quack",
        "the lamp glowed warm and the moon looked on",
        {"mixing", "bubbles"}
    ),
    "kitchen": Setting(
        "kitchen", "the kitchen", "the kitchen",
        "Little spoons on the counter went ting, ting, ting",
        "the window shone gold and the sink sang soft",
        {"mixing", "bubbles"}
    ),
    "sunroom": Setting(
        "sunroom", "the sunroom", "the sunroom",
        "Little kites in the curtains went swish, swish, swish",
        "the glass was bright and the shadows grew small",
        {"mixing", "bubbles"}
    ),
}

ACTIVITIES = {
    "mixing": Activity("mixing", "mix a potion", "mixing and singing", "stirred and swirled", "spill", {"torso"}, "mixing", {"chemical"}),
    "bubbles": Activity("bubbles", "make bubbles", "blowing bubbles", "swished and swooshed", "spill", {"torso"}, "bubbles", {"safe"}),
}

PRIZES = {
    "cloth": Prize("cloth", "bright cloth", "bright cloth", "torso", fragile=True, tags={"cloth"}),
    "ribbon": Prize("ribbon", "a ribbon garland", "a ribbon garland", "torso", fragile=True, tags={"ribbon"}),
}

REAGENTS = {
    "vinegar": Reagent("vinegar", "vinegar", "a cup of vinegar", risky=True, tags={"chemical"}),
    "soap": Reagent("soap", "soap", "a swirl of soap", risky=False, tags={"safe"}),
    "powder": Reagent("powder", "powder", "a spoon of powder", risky=True, tags={"chemical"}),
}

COMPROMISES = {
    "safe_potion": Compromise("safe_potion", "safe potion", "a safe potion", "whisked up a bowl of soap bubbles", tags={"safe"}),
    "rhyme": Compromise("rhyme", "rhyme game", "a rhyme game", "began a gentle rhyme with wooden spoons", tags={"safe"}),
}

GIRL_NAMES = ["Milly", "Tilly", "Rosie", "Luna", "Daisy"]
BOY_NAMES = ["Benny", "Toby", "Ned", "Pip", "Ollie"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            if aid not in setting.affords:
                continue
            for pid, prize in PRIZES.items():
                if not prize.fragile:
                    continue
                for rid, reagent in REAGENTS.items():
                    if reasonableness_gate(reagent, prize, act):
                        combos.append((sid, aid, pid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    reagent: str
    compromise: str
    maker: str
    maker_gender: str
    helper: str
    helper_gender: str
    grownup: str
    relation: str
    maker_age: int = 4
    helper_age: int = 6
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


KNOWLEDGE = {
    "chemical": [("What does chemical mean?", "Chemical means a substance or material that can mix or react with other substances. Some chemicals are safe, and some need careful handling.")],
    "variety": [("What does variety mean?", "Variety means having different kinds of things instead of just one kind.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is a good idea you remember after something happens, so you can make a safer choice next time.")],
    "safe": [("Why is safe important?", "Safe means not likely to hurt anyone or cause trouble. Safe choices help everyone keep playing.")],
    "mixing": [("What happens when you stir a mixture?", "Stirring helps things blend together. Some mixtures are harmless, and some should only be handled by grown-ups.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story for a young child that includes the words "chemical", "savage", and "variety".',
        f"Tell a gentle story where {f['maker'].id} wants to make a {f['activity'].keyword} with {f['reagent'].label}, but {f['helper'].id} worries and a grown-up teaches a lesson learned.",
        f"Write a sing-song story in which a small spill leads to a calm fix, a lesson learned, and a happy ending in {f['setting'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maker, helper, grownup = f["maker"], f["helper"], f["grownup"]
    prize, reagent, compromise, setting = f["prize"], f["reagent"], f["compromise"], f["setting"]
    return [
        QAItem(
            question="What were the children trying to do?",
            answer=f"They were trying to make a little chemical mixture and give it some variety. The idea felt exciting, but it also needed careful help."
        ),
        QAItem(
            question=f"Why did {helper.id} warn {maker.id}?",
            answer=f"{helper.id} warned {maker.id} because the {reagent.label} could be savage for the room if it spilled near the {prize.label}. That warning gave the grown-up time to step in with a safer choice."
        ),
        QAItem(
            question="How did the problem get fixed?",
            answer=f"{grownup.label_word.capitalize()} came in and {compromise.fix}. That calm choice stopped the mess and turned the trouble into a lesson learned."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | set(world.facts["reagent"].tags) | set(world.facts["compromise"].tags)
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags or key == "lesson" and world.facts.get("outcome") == "lesson":
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("nursery", "mixing", "cloth", "vinegar", "safe_potion", "Milly", "girl", "Benny", "boy", "mother", "siblings"),
    StoryParams("kitchen", "mixing", "ribbon", "powder", "rhyme", "Tilly", "girl", "Toby", "boy", "father", "siblings"),
]


def explain_rejection(reagent: Reagent, prize: Prize, activity: Activity) -> str:
    if not reasonableness_gate(reagent, prize, activity):
        return "(No story: this combination is too small to create the needed trouble and lesson.)"
    return "(No story: invalid combination.)"


def outcome_of(params: StoryParams) -> str:
    return "lesson"


ASP_RULES = r"""
reasonably_valid(S, A, P, R) :- setting(S), activity(A), prize(P), reagent(R),
    risky(R), fragile(P), zone(A, Z), region(P, Z).
outcome(lesson) :- reasonably_valid(_, _, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(act.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, prize.region))
        if prize.fragile:
            lines.append(asp.fact("fragile", pid))
    for rid, reagent in REAGENTS.items():
        lines.append(asp.fact("reagent", rid))
        if reagent.risky:
            lines.append(asp.fact("risky", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonably_valid/4."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP valid combos.")
    sample = generate(CURATED[0])
    if not sample.story:
        rc = 1
        print("MISMATCH: generation produced empty story.")
    else:
        print("OK: smoke test generate() produced a story.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a chemical lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--reagent", choices=REAGENTS)
    ap.add_argument("--compromise", choices=COMPROMISES)
    ap.add_argument("--maker")
    ap.add_argument("--maker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings"])
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
    if args.activity and args.reagent and args.prize:
        if not reasonableness_gate(REAGENTS[args.reagent], PRIZES[args.prize], ACTIVITIES[args.activity]):
            raise StoryError(explain_rejection(REAGENTS[args.reagent], PRIZES[args.prize], ACTIVITIES[args.activity]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.reagent is None or c[3] == args.reagent)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize, reagent = rng.choice(sorted(combos))
    compromise = args.compromise or rng.choice(sorted(COMPROMISES))
    maker_gender = args.maker_gender or "girl"
    helper_gender = args.helper_gender or "boy"
    maker = args.maker or rng.choice(GIRL_NAMES if maker_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    if helper == maker:
        helper = "Benny" if maker != "Benny" else "Toby"
    grownup = args.grownup or rng.choice(["mother", "father"])
    relation = args.relation or "siblings"
    return StoryParams(setting, activity, prize, reagent, compromise, maker, maker_gender, helper, helper_gender, grownup, relation)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize],
        REAGENTS[params.reagent], COMPROMISES[params.compromise],
        params.maker, params.maker_gender, params.helper, params.helper_gender,
        params.grownup, params.relation, params.maker_age, params.helper_age
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
        print(asp_program("", "#show reasonably_valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
