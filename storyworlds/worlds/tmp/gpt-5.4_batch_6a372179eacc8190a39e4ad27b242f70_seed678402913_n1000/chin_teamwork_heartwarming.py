#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chin_teamwork_heartwarming.py
========================================================

A standalone storyworld about a child who wants to fly a homemade kite, finds
that one pair of hands is not enough, and learns a warm, concrete lesson about
teamwork. The generated stories stay small and child-facing: a beginning with a
hopeful plan, a middle where the kite will not rise, a turning point where
helpers choose a method that truly fits the kite, and an ending image that shows
everyone holding the sky together.

The required seed word "chin" appears naturally in the prose and in grounded Q&A.

Run it
------
    python storyworlds/worlds/gpt-5.4/chin_teamwork_heartwarming.py
    python storyworlds/worlds/gpt-5.4/chin_teamwork_heartwarming.py --kite giant --method tail_holder
    python storyworlds/worlds/gpt-5.4/chin_teamwork_heartwarming.py --kite giant --method solo
    python storyworlds/worlds/gpt-5.4/chin_teamwork_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/chin_teamwork_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/chin_teamwork_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/chin_teamwork_heartwarming.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "dad", "man", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    ground: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KiteSpec:
    id: str
    label: str
    phrase: str
    color: str
    tail: str
    pull: int
    needs_tail_hold: bool
    needs_runner: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    helpers: int
    keeps_tail_steady: bool
    gives_running_start: bool
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_tilt(world: World) -> list[str]:
    out: list[str] = []
    kite = world.get("kite")
    child = world.get("child")
    if kite.meters["unstable"] < THRESHOLD:
        return out
    sig = ("tilt", "kite")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__tilt__")
    return out


def _r_team_joy(world: World) -> list[str]:
    out: list[str] = []
    if world.get("kite").meters["flying"] < THRESHOLD:
        return out
    for ent in world.characters():
        sig = ("joy", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] += 1
    out.append("__joy__")
    return out


CAUSAL_RULES = [
    Rule(name="tilt", tag="physical", apply=_r_tilt),
    Rule(name="team_joy", tag="emotional", apply=_r_team_joy),
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


def method_works(kite: KiteSpec, method: Method) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if method.helpers < 1:
        return False
    if kite.needs_tail_hold and not method.keeps_tail_steady:
        return False
    if kite.needs_runner and not method.gives_running_start:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for kite_id, kite in KITES.items():
            for method_id, method in METHODS.items():
                if method_works(kite, method):
                    combos.append((setting_id, kite_id, method_id))
    return combos


def explain_method_rejection(kite: KiteSpec, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). A teamwork story should pick a calm, "
            f"helpful way to launch the kite.)"
        )
    reasons: list[str] = []
    if kite.needs_tail_hold and not method.keeps_tail_steady:
        reasons.append("this kite needs someone to steady the long tail")
    if kite.needs_runner and not method.gives_running_start:
        reasons.append("this kite needs a running start to catch the wind")
    if not reasons:
        reasons.append("this method does not fit the kite")
    return f"(No story: {', and '.join(reasons)}.)"


def predict_launch(world: World, kite_cfg: KiteSpec, method_cfg: Method) -> dict:
    sim = world.copy()
    attempt_launch(sim, kite_cfg, method_cfg, narrate=False)
    kite = sim.get("kite")
    return {
        "flying": kite.meters["flying"] >= THRESHOLD,
        "unstable": kite.meters["unstable"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper1: Entity, helper2: Entity,
              setting: Setting, kite_cfg: KiteSpec) -> None:
    child.memes["hope"] += 1
    world.say(
        f"One soft afternoon, {child.id} carried {kite_cfg.phrase} to {setting.place}. "
        f"The {setting.sky} hung over {setting.ground}, and the wind felt ready for play."
    )
    world.say(
        f"{helper1.id} and {helper2.id} came along too, because kite days were better "
        f"when everyone had something to do."
    )


def admire(world: World, child: Entity, kite_cfg: KiteSpec) -> None:
    world.say(
        f"{child.id} tilted {child.pronoun('possessive')} chin up and looked at the "
        f"{kite_cfg.color} paper. \"If it climbs high enough,\" {child.pronoun()} said, "
        f"\"it will look like a little piece of sky with a {kite_cfg.tail}.\""
    )


def prepare(world: World, child: Entity, kite_cfg: KiteSpec) -> None:
    world.say(
        f"{child.id} held the string spool carefully. The kite tugged with a "
        f"firm little pull, as if it already wanted to go."
    )
    world.get("kite").meters["pull"] = float(kite_cfg.pull)


def want_solo(world: World, child: Entity) -> None:
    child.memes["independence"] += 1
    world.say(
        f"At first, {child.id} wanted to do the important part alone. "
        f"Doing it alone made the moment seem big and brave."
    )


def warn(world: World, helper1: Entity, child: Entity, kite_cfg: KiteSpec, method_cfg: Method) -> None:
    pred = predict_launch(world, kite_cfg, method_cfg)
    world.facts["predicted_flying"] = pred["flying"]
    world.facts["predicted_unstable"] = pred["unstable"]
    if not pred["flying"]:
        helper1.memes["care"] += 1
        need = []
        if kite_cfg.needs_tail_hold:
            need.append("someone to keep the tail from twisting")
        if kite_cfg.needs_runner:
            need.append("someone to give it a good running start")
        world.say(
            f'"Wait," said {helper1.id}. "This kite is bigger than one pair of hands. '
            f'It needs {" and ".join(need)}."'
        )
    else:
        world.say(
            f'{helper1.id} smiled and said, "We can do this together and make it easy."'
        )


def attempt_launch(world: World, kite_cfg: KiteSpec, method_cfg: Method, narrate: bool = True) -> None:
    kite = world.get("kite")
    child = world.get("child")
    if method_works(kite_cfg, method_cfg):
        kite.meters["flying"] += 1
        kite.meters["stable"] += 1
        propagate(world, narrate=narrate)
        if narrate:
            world.say(method_cfg.text)
    else:
        kite.meters["unstable"] += 1
        kite.meters["droop"] += 1
        propagate(world, narrate=narrate)
        child.memes["frustration"] += 1
        if narrate:
            world.say(
                "But the kite wobbled, dipped, and dragged its tail across the grass "
                "instead of rising."
            )


def low_moment(world: World, child: Entity) -> None:
    if child.memes["worry"] >= THRESHOLD or child.memes["frustration"] >= THRESHOLD:
        world.say(
            f"{child.id} looked down for a moment. The string felt heavy in "
            f"{child.pronoun('possessive')} hands, and the brave feeling shrank."
        )


def invite_teamwork(world: World, helper1: Entity, helper2: Entity, child: Entity,
                    kite_cfg: KiteSpec, method_cfg: Method) -> None:
    child.memes["trust"] += 1
    helper1.memes["care"] += 1
    helper2.memes["care"] += 1
    lines: list[str] = []
    if method_cfg.keeps_tail_steady:
        lines.append(f"{helper2.id} could hold the tail straight")
    if method_cfg.gives_running_start:
        lines.append(f"{helper1.id} could run with {child.id} for the first few steps")
    if not lines:
        lines.append(f"{helper1.id} and {helper2.id} could stay close and help")
    world.say(
        f'"Let us help," said {helper2.id}. "{", and ".join(lines)}. '
        f'Then the wind will have a fair chance."'
    )
    world.say(
        f"{child.id} took a breath, lifted {child.pronoun('possessive')} chin again, "
        f"and nodded."
    )


def teamwork_launch(world: World, child: Entity, helper1: Entity, helper2: Entity,
                    method_cfg: Method) -> None:
    world.say(
        f"They tried again together. {method_cfg.text}"
    )
    world.say(
        f"The string grew light instead of heavy, and all three of them laughed "
        f"when the kite finally found the wind."
    )


def ending(world: World, child: Entity, helper1: Entity, helper2: Entity,
           setting: Setting, kite_cfg: KiteSpec) -> None:
    child.memes["lesson"] += 1
    helper1.memes["love"] += 1
    helper2.memes["love"] += 1
    world.say(
        f"Soon {kite_cfg.label} was high above {setting.place}, and its "
        f"{kite_cfg.tail} rippled like a ribbon in a storybook."
    )
    world.say(
        f"{child.id} leaned close to {helper1.id} and {helper2.id}. "
        f'"It flew because we did it together," {child.pronoun()} said.'
    )
    world.say(
        f"They stood shoulder to shoulder on {setting.ground}, smiling up until "
        f"the breeze brushed softly under {child.id}'s chin."
    )


def tell(setting: Setting, kite_cfg: KiteSpec, method_cfg: Method,
         child_name: str, child_gender: str,
         helper1_name: str, helper1_gender: str,
         helper2_name: str, helper2_gender: str,
         grownup_type: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name,
                             role="child", attrs={"name": child_name}))
    helper1 = world.add(Entity(id="helper1", kind="character", type=helper1_gender, label=helper1_name,
                               role="helper", attrs={"name": helper1_name}))
    helper2 = world.add(Entity(id="helper2", kind="character", type=helper2_gender, label=helper2_name,
                               role="helper", attrs={"name": helper2_name}))
    grown = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="the grown-up",
                             role="grownup"))
    kite = world.add(Entity(id="kite", kind="thing", type="kite", label=kite_cfg.label,
                            phrase=kite_cfg.phrase, tags=set(kite_cfg.tags)))
    spool = world.add(Entity(id="spool", kind="thing", type="spool", label="string spool"))

    introduce(world, child, helper1, helper2, setting, kite_cfg)
    admire(world, child, kite_cfg)
    prepare(world, child, kite_cfg)

    world.para()
    want_solo(world, child)
    warn(world, helper1, child, kite_cfg, Method(
        id="solo_check",
        label="solo",
        sense=2,
        helpers=1,
        keeps_tail_steady=False,
        gives_running_start=False,
        text="",
        qa_text="",
    ))
    attempt_launch(
        world,
        kite_cfg,
        Method(
            id="solo_attempt",
            label="solo",
            sense=2,
            helpers=1,
            keeps_tail_steady=False,
            gives_running_start=False,
            text="",
            qa_text="",
        ),
        narrate=True,
    )

    world.para()
    low_moment(world, child)
    invite_teamwork(world, helper1, helper2, child, kite_cfg, method_cfg)
    world.say(
        f"{grown.label_word.capitalize()} watched from nearby and gave them a warm nod, "
        f"glad to see everyone making room for one another."
    )

    world.para()
    attempt_launch(world, kite_cfg, method_cfg, narrate=False)
    teamwork_launch(world, child, helper1, helper2, method_cfg)
    ending(world, child, helper1, helper2, setting, kite_cfg)

    world.facts.update(
        setting=setting,
        kite_cfg=kite_cfg,
        method=method_cfg,
        child=child,
        helper1=helper1,
        helper2=helper2,
        grownup=grown,
        child_name=child_name,
        helper1_name=helper1_name,
        helper2_name=helper2_name,
        failed_solo=True,
        succeeded=world.get("kite").meters["flying"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    kite: str
    method: str
    child_name: str
    child_gender: str
    helper1_name: str
    helper1_gender: str
    helper2_name: str
    helper2_gender: str
    grownup: str
    seed: Optional[int] = None


SETTINGS = {
    "park": Setting(
        id="park",
        place="the park hill",
        sky="blue afternoon sky",
        ground="the soft grass",
        tags={"park"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the little meadow behind the barn",
        sky="pale spring sky",
        ground="the clover",
        tags={"meadow"},
    ),
    "beach": Setting(
        id="beach",
        place="the quiet beach",
        sky="bright seaside sky",
        ground="the warm sand",
        tags={"beach"},
    ),
}

KITES = {
    "diamond": KiteSpec(
        id="diamond",
        label="the diamond kite",
        phrase="a bright diamond kite",
        color="bright red",
        tail="short blue tail",
        pull=1,
        needs_tail_hold=False,
        needs_runner=True,
        tags={"kite"},
    ),
    "dragon": KiteSpec(
        id="dragon",
        label="the dragon kite",
        phrase="a painted dragon kite",
        color="green and gold",
        tail="long fluttering tail",
        pull=2,
        needs_tail_hold=True,
        needs_runner=True,
        tags={"kite", "tail"},
    ),
    "giant": KiteSpec(
        id="giant",
        label="the giant star kite",
        phrase="a giant star kite",
        color="silver and blue",
        tail="long silver streamers",
        pull=3,
        needs_tail_hold=True,
        needs_runner=True,
        tags={"kite", "tail", "wind"},
    ),
}

METHODS = {
    "run_together": Method(
        id="run_together",
        label="run together",
        sense=3,
        helpers=2,
        keeps_tail_steady=False,
        gives_running_start=True,
        text="One child held the spool while another ran beside them, and the kite gave a hopeful leap.",
        qa_text="one child held the spool while another ran beside the flyer",
        tags={"teamwork", "running"},
    ),
    "tail_holder": Method(
        id="tail_holder",
        label="tail holder and runner",
        sense=3,
        helpers=3,
        keeps_tail_steady=True,
        gives_running_start=True,
        text="One friend kept the tail straight, another ran with the string, and the last pair of hands guided the nose toward the wind.",
        qa_text="one helper steadied the tail while another gave the kite a running start",
        tags={"teamwork", "tail", "running"},
    ),
    "gentle_count": Method(
        id="gentle_count",
        label="count and lift",
        sense=2,
        helpers=2,
        keeps_tail_steady=False,
        gives_running_start=True,
        text='They counted "one, two, three," lifted together, and ran at the same happy moment.',
        qa_text='they counted together, lifted together, and ran at the same moment',
        tags={"teamwork", "counting", "running"},
    ),
    "solo": Method(
        id="solo",
        label="solo",
        sense=1,
        helpers=1,
        keeps_tail_steady=False,
        gives_running_start=False,
        text="",
        qa_text="tried to do everything alone",
        tags={"alone"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]
GROWNUPS = ["mother", "father", "grandmother", "grandfather"]


KNOWLEDGE = {
    "kite": [
        (
            "What makes a kite fly?",
            "A kite flies when the wind pushes against it and the string helps hold it at the right angle. If it is steady enough, the air lifts it up."
        )
    ],
    "tail": [
        (
            "Why does a kite have a tail?",
            "A tail helps a kite stay balanced in the wind. It can keep the kite from twisting and wobbling too much."
        )
    ],
    "running": [
        (
            "Why do people sometimes run when they launch a kite?",
            "Running helps the kite catch moving air at the start. That first pull can help lift it up into the sky."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another do something together. Each person does one part, and the job becomes easier."
        )
    ],
    "wind": [
        (
            "Can a very big kite need more help than a small kite?",
            "Yes. A big kite pulls harder and can twist more, so extra hands may help hold it steady and start it safely."
        )
    ],
    "counting": [
        (
            "Why do people count before doing something together?",
            "Counting helps everyone begin at the same time. That makes shared work smoother."
        )
    ],
}
KNOWLEDGE_ORDER = ["kite", "tail", "running", "teamwork", "wind", "counting"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    kite_cfg = f["kite_cfg"]
    setting = f["setting"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "chin" and shows teamwork while children fly a kite.',
        f"Tell a gentle story where {display_name(child)} brings {kite_cfg.phrase} to {setting.place}, struggles at first, and learns that extra hands can help good things rise.",
        f'Write a warm story about friends sharing a job in the wind, with a happy ending image and the word "chin".',
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper1 = f["helper1"]
    helper2 = f["helper2"]
    kite_cfg = f["kite_cfg"]
    method = f["method"]
    setting = f["setting"]
    child_name = display_name(child)
    helper1_name = display_name(helper1)
    helper2_name = display_name(helper2)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, {helper1_name}, and {helper2_name} on a kite day together. They all matter because the story turns on shared help."
        ),
        (
            "What did they bring to the field?",
            f"They brought {kite_cfg.phrase}. The kite is what creates both the problem and the happy ending."
        ),
        (
            f"Why did {child_name} lift {child.pronoun('possessive')} chin at the beginning?",
            f"{child_name} was looking up at the kite and imagining it high in the sky. That little chin-up moment shows hope before the trouble starts."
        ),
        (
            f"What went wrong when {child_name} tried first?",
            f"The kite wobbled and dragged across the ground instead of rising. One pair of hands was not enough to keep it steady and start it well."
        ),
        (
            f"How did the others help {child_name}?",
            f"They did the job in parts instead of leaving everything to one child. {method.qa_text.capitalize()}, which gave the kite the steady start it needed."
        ),
        (
            "Why did the teamwork work better?",
            f"It worked better because the kite needed more than one kind of help at once. Extra hands kept it straighter and gave it a better start in the wind."
        ),
        (
            "How did the story end?",
            f"The kite flew high above {setting.place}, and everyone stood together looking up. The ending proves something changed, because the child who first wanted to do it alone now says it flew because they worked together."
        ),
    ]
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["kite_cfg"].tags) | set(world.facts["method"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="park",
        kite="diamond",
        method="run_together",
        child_name="Lily",
        child_gender="girl",
        helper1_name="Ben",
        helper1_gender="boy",
        helper2_name="Maya",
        helper2_gender="girl",
        grownup="mother",
    ),
    StoryParams(
        setting="meadow",
        kite="dragon",
        method="tail_holder",
        child_name="Max",
        child_gender="boy",
        helper1_name="Zoe",
        helper1_gender="girl",
        helper2_name="Finn",
        helper2_gender="boy",
        grownup="grandfather",
    ),
    StoryParams(
        setting="beach",
        kite="giant",
        method="tail_holder",
        child_name="Ava",
        child_gender="girl",
        helper1_name="Leo",
        helper1_gender="boy",
        helper2_name="Lucy",
        helper2_gender="girl",
        grownup="father",
    ),
    StoryParams(
        setting="park",
        kite="diamond",
        method="gentle_count",
        child_name="Noah",
        child_gender="boy",
        helper1_name="Ella",
        helper1_gender="girl",
        helper2_name="Sam",
        helper2_gender="boy",
        grownup="grandmother",
    ),
]


ASP_RULES = r"""
usable_method(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.
works(K,M) :- kite(K), method(M), usable_method(M),
              not requires_tail(K), not requires_run(K).
works(K,M) :- kite(K), method(M), usable_method(M),
              requires_run(K), gives_run(M),
              not requires_tail(K).
works(K,M) :- kite(K), method(M), usable_method(M),
              requires_tail(K), keeps_tail(M),
              not requires_run(K).
works(K,M) :- kite(K), method(M), usable_method(M),
              requires_tail(K), keeps_tail(M),
              requires_run(K), gives_run(M).

valid(S,K,M) :- setting(S), kite(K), method(M), works(K,M).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for kid, kite in KITES.items():
        lines.append(asp.fact("kite", kid))
        if kite.needs_tail_hold:
            lines.append(asp.fact("requires_tail", kid))
        if kite.needs_runner:
            lines.append(asp.fact("requires_run", kid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        if method.keeps_tail_steady:
            lines.append(asp.fact("keeps_tail", mid))
        if method.gives_running_start:
            lines.append(asp.fact("gives_run", mid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming teamwork storyworld about flying a kite together."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--kite", choices=KITES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--grownup", choices=GROWNUPS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, kite, method) triples")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    if not choices:
        raise StoryError("(No unique names available for the requested cast.)")
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.kite and args.method:
        kite = KITES[args.kite]
        method = METHODS[args.method]
        if not method_works(kite, method):
            raise StoryError(explain_method_rejection(kite, method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.kite is None or combo[1] == args.kite)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, kite_id, method_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper1_gender = rng.choice(["girl", "boy"])
    helper2_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    child_name = pick_name(rng, child_gender, used)
    used.add(child_name)
    helper1_name = pick_name(rng, helper1_gender, used)
    used.add(helper1_name)
    helper2_name = pick_name(rng, helper2_gender, used)
    grownup = args.grownup or rng.choice(GROWNUPS)
    return StoryParams(
        setting=setting_id,
        kite=kite_id,
        method=method_id,
        child_name=child_name,
        child_gender=child_gender,
        helper1_name=helper1_name,
        helper1_gender=helper1_gender,
        helper2_name=helper2_name,
        helper2_gender=helper2_gender,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.kite not in KITES:
        raise StoryError(f"(Unknown kite: {params.kite})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    kite_cfg = KITES[params.kite]
    method_cfg = METHODS[params.method]
    if not method_works(kite_cfg, method_cfg):
        raise StoryError(explain_method_rejection(kite_cfg, method_cfg))

    world = tell(
        setting=SETTINGS[params.setting],
        kite_cfg=kite_cfg,
        method_cfg=method_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper1_name=params.helper1_name,
        helper1_gender=params.helper1_gender,
        helper2_name=params.helper2_name,
        helper2_gender=params.helper2_gender,
        grownup_type=params.grownup,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, kite, method) combos:\n")
        for setting_id, kite_id, method_id in combos:
            print(f"  {setting_id:8} {kite_id:8} {method_id}")
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
            header = f"### {p.child_name}: {p.kite} at {p.setting} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
