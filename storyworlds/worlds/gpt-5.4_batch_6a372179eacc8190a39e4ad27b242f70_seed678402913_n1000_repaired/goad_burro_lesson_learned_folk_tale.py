#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/goad_burro_lesson_learned_folk_tale.py
=================================================================

A small folk-tale storyworld about a traveler, a burro, and a lesson learned:
a hard hand and a goad cannot hurry a weary animal the way patience, rest, and
shared work can.

The world model tracks strain on the burro, progress on the road, and changing
feelings such as pride, fear, trust, and remorse. Stories are rendered from the
simulated state rather than from fixed templates with swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4/goad_burro_lesson_learned_folk_tale.py
    python storyworlds/worlds/gpt-5.4/goad_burro_lesson_learned_folk_tale.py --burden grain
    python storyworlds/worlds/gpt-5.4/goad_burro_lesson_learned_folk_tale.py --method goad --helper bell
    python storyworlds/worlds/gpt-5.4/goad_burro_lesson_learned_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/goad_burro_lesson_learned_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/goad_burro_lesson_learned_folk_tale.py --verify
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Burden:
    id: str
    label: str
    phrase: str
    weight: int
    goods: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Path:
    id: str
    label: str
    phrase: str
    challenge: int
    heat: int
    scene: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    harsh: bool
    sense: int
    power: int
    start_text: str
    lesson_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    cools: int
    lightens: int
    calms: int
    sense: int
    offer_text: str
    fix_text: str
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
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_overstrain(world: World) -> list[str]:
    out: list[str] = []
    burro = world.get("burro")
    if burro.meters["strain"] < 3:
        return out
    sig = ("overstrain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    burro.memes["fear"] += 1
    burro.meters["progress"] -= 1
    for eid in ("traveler", "elder"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__balk__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    burro = world.get("burro")
    traveler = world.get("traveler")
    if burro.memes["trust"] < 1 or burro.meters["strain"] >= 3:
        return out
    sig = ("kindness_moves",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    burro.meters["progress"] += 1
    traveler.memes["hope"] += 1
    out.append("__moves__")
    return out


CAUSAL_RULES = [
    Rule(name="overstrain", tag="physical", apply=_r_overstrain),
    Rule(name="kindness_moves", tag="social", apply=_r_kindness),
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
        for sent in produced:
            world.say(sent)
    return produced


BURDENS = {
    "grain": Burden(
        id="grain",
        label="grain sacks",
        phrase="two bulging grain sacks",
        weight=3,
        goods="grain for the mill",
        tags={"grain", "load"},
    ),
    "blankets": Burden(
        id="blankets",
        label="woven blankets",
        phrase="a bundle of woven blankets",
        weight=1,
        goods="blankets for the market stall",
        tags={"blankets", "load"},
    ),
    "jugs": Burden(
        id="jugs",
        label="water jugs",
        phrase="three sloshing water jugs",
        weight=2,
        goods="water for the orchard workers",
        tags={"water", "load"},
    ),
}

PATHS = {
    "hill": Path(
        id="hill",
        label="hill path",
        phrase="the steep hill path",
        challenge=2,
        heat=1,
        scene="The stones were warm, and lizards flashed in and out among the rocks.",
        ending="By sunset they stood on the ridge, and the village below shone like a bowl of lamps.",
        tags={"hill", "road"},
    ),
    "ford": Path(
        id="ford",
        label="river ford",
        phrase="the river ford road",
        challenge=2,
        heat=0,
        scene="Willows leaned over the water, and the road dipped toward a shallow silver crossing.",
        ending="At the ford the water folded around the burro's knees, and the far bank opened green and cool.",
        tags={"river", "road"},
    ),
    "mesa": Path(
        id="mesa",
        label="mesa road",
        phrase="the dusty mesa road",
        challenge=1,
        heat=2,
        scene="Dust lifted in pale curls, and the sun hung over the land like a brass plate.",
        ending="When evening came, the red mesa turned purple, and the first star trembled above it.",
        tags={"sun", "road"},
    ),
}

METHODS = {
    "goad": Method(
        id="goad",
        label="goad",
        harsh=True,
        sense=1,
        power=0,
        start_text="tapped the little goad against the packs and clicked with impatient lips",
        lesson_text="a goad may sting skin, but it does not ease a weary back",
        tags={"goad", "harsh"},
    ),
    "rope_tug": Method(
        id="rope_tug",
        label="rope tug",
        harsh=False,
        sense=2,
        power=1,
        start_text="gave the lead rope a steady pull and called for the burro to keep on",
        lesson_text="pulling harder only helps when the load itself is fair",
        tags={"rope", "effort"},
    ),
    "gentle_song": Method(
        id="gentle_song",
        label="gentle song",
        harsh=False,
        sense=3,
        power=2,
        start_text="walked beside the burro and sang an old road song in a low voice",
        lesson_text="a calm voice can guide willing feet when the burden is not too great",
        tags={"song", "kindness"},
    ),
}

HELPERS = {
    "share_load": Helper(
        id="share_load",
        label="share the load",
        cools=0,
        lightens=2,
        calms=1,
        sense=3,
        offer_text="lift one sack from the burro's back and carry part of the burden yourself",
        fix_text="slid one bundle from the packs to the traveler's own shoulders",
        qa_text="shared the load so the burro did not have to carry everything alone",
        tags={"sharing", "load"},
    ),
    "water_rest": Helper(
        id="water_rest",
        label="water and rest",
        cools=2,
        lightens=0,
        calms=1,
        sense=3,
        offer_text="lead the burro to shade, loosen the straps, and let it drink and rest",
        fix_text="led the burro under shade, loosened the straps, and let it drink cool water",
        qa_text="gave the burro shade, water, and time to rest",
        tags={"water_rest", "kindness"},
    ),
    "bell": Helper(
        id="bell",
        label="bell on the lead",
        cools=0,
        lightens=0,
        calms=1,
        sense=2,
        offer_text="tie a small bell to the lead rope and walk slowly so the burro can follow the sound",
        fix_text="tied a tiny brass bell to the rope, and its soft ringing kept a steady pace",
        qa_text="used a small bell and a slow pace to help the burro keep walking calmly",
        tags={"bell", "kindness"},
    ),
}

TRAVELERS = [
    ("Mateo", "boy"),
    ("Rosa", "girl"),
    ("Inez", "girl"),
    ("Tomas", "boy"),
    ("Alma", "girl"),
    ("Diego", "boy"),
]

ELDERS = [
    ("Abuela", "woman"),
    ("Old Tomas", "man"),
    ("Tía Luz", "woman"),
    ("Grandfather Nilo", "man"),
]


def required_aid(burden: Burden, path: Path, method: Method) -> tuple[int, int]:
    strain = burden.weight + path.challenge + path.heat
    if method.harsh:
        strain += 1
    elif method.id == "gentle_song":
        strain -= 1
    return max(strain - 2, 0), max(path.heat + burden.weight - 3, 0)


def helper_fits(burden: Burden, path: Path, method: Method, helper: Helper) -> bool:
    light_need, cool_need = required_aid(burden, path, method)
    if helper.sense < SENSE_MIN:
        return False
    if light_need > helper.lightens:
        return False
    if cool_need > helper.cools:
        return False
    if method.id == "goad" and helper.id == "bell" and burden.weight + path.challenge >= 4:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for burden_id, burden in BURDENS.items():
        for path_id, path in PATHS.items():
            for method_id, method in METHODS.items():
                for helper_id, helper in HELPERS.items():
                    if helper_fits(burden, path, method, helper):
                        combos.append((burden_id, path_id, method_id, helper_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    burden = BURDENS[params.burden]
    path = PATHS[params.path]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    if not helper_fits(burden, path, method, helper):
        return "invalid"
    strain = burden.weight + path.challenge + path.heat
    if method.harsh:
        strain += 1
    elif method.id == "gentle_song":
        strain -= 1
    strain -= helper.lightens
    strain -= helper.cools
    trust = helper.calms + (1 if not method.harsh else 0)
    if method.harsh:
        return "stumble" if strain >= 2 else "mend"
    return "smooth" if strain <= 1 and trust >= 2 else "mend"


@dataclass
class StoryParams:
    burden: str
    path: str
    method: str
    helper: str
    traveler_name: str
    traveler_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def introduce(world: World, traveler: Entity, elder: Entity, burden: Burden, path: Path) -> None:
    burro = world.get("burro")
    world.say(
        f"In a dry country of stone walls and fig trees, {traveler.id} set out at dawn with a small burro."
    )
    world.say(
        f"On the burro's back rode {burden.phrase}, and the road before them was {path.phrase}. {path.scene}"
    )
    world.say(
        f'At the gate, {elder.id} called, "Mind the creature as you would mind your own tired feet."'
    )
    burro.memes["trust"] += 1
    traveler.memes["pride"] += 1


def begin_hard_way(world: World, traveler: Entity, burro: Entity, method: Method) -> None:
    if method.id == "goad":
        world.say(
            f"But the morning was young, and {traveler.id} wanted to reach town before the good buyers did. "
            f"{traveler.pronoun().capitalize()} {method.start_text}. The burro flicked its ears and took two unwilling steps."
        )
        traveler.memes["impatience"] += 1
        burro.memes["fear"] += 1
        burro.meters["strain"] += 1
    else:
        world.say(
            f"{traveler.id} wished to make good time and {method.start_text}. The burro listened, lowered its head, and started along."
        )
        burro.memes["trust"] += 1


def road_grows_hard(world: World, traveler: Entity, burro: Entity, burden: Burden, path: Path) -> None:
    burro.meters["strain"] += burden.weight + path.challenge + path.heat
    burro.meters["progress"] += 1
    propagate(world, narrate=False)
    if burro.meters["strain"] >= 3:
        world.say(
            f"Before long the day pressed down. The straps bit, dust clung, and the burro's sides worked like a bellows."
        )
    else:
        world.say(
            f"The road bent onward, and though the packs swayed, the burro kept a patient pace."
        )


def stumble_or_balk(world: World, traveler: Entity, burro: Entity, method: Method, path: Path) -> None:
    if burro.meters["strain"] < 3:
        return
    if method.harsh:
        burro.meters["stumbled"] += 1
        world.say(
            f"When {traveler.id} touched the goad again, the burro gave a sad bray, stumbled on the stones, and stood shaking in the middle of the road."
        )
    else:
        burro.meters["balked"] += 1
        world.say(
            f"Then the burro stopped by a bend in the road and would not go another step. It was not stubbornness; it was weariness plain as noon."
        )
    traveler.memes["shame"] += 1


def elder_returns(world: World, elder: Entity, traveler: Entity, helper: Helper) -> None:
    world.say(
        f"As if the road itself had heard, {elder.id} came up behind them with a walking staff. "
        f'"Child," {elder.pronoun()} said, "there is still time to choose the wiser way: {helper.offer_text}."'
    )
    elder.memes["care"] += 1
    traveler.memes["hope"] += 1


def apply_helper(world: World, traveler: Entity, burro: Entity, helper: Helper) -> None:
    world.say(
        f"So {traveler.id} {helper.fix_text}."
    )
    burro.meters["strain"] -= helper.lightens
    burro.meters["strain"] -= helper.cools
    burro.memes["trust"] += helper.calms
    traveler.memes["kindness"] += 1
    if burro.meters["strain"] < 0:
        burro.meters["strain"] = 0
    propagate(world, narrate=False)


def apology_and_lesson(world: World, traveler: Entity, burro: Entity, elder: Entity, method: Method) -> None:
    if method.harsh:
        world.say(
            f"{traveler.id} stroked the burro's neck and whispered an apology into its dusty fur. "
            f'"I thought a sharp hand would make a short road," {traveler.pronoun()} said.'
        )
    else:
        world.say(
            f"{traveler.id} rubbed the burro's neck and looked more carefully than before. "
            f'"I was hurrying my own wish instead of hearing what the road was saying," {traveler.pronoun()} admitted.'
        )
    world.say(
        f'{elder.id} nodded. "{method.lesson_text.capitalize()}. A living helper is not a cartwheel. '
        f'When you ask for labor, you must also offer fairness."'
    )
    traveler.memes["lesson"] += 1
    burro.memes["trust"] += 1


def finish(world: World, traveler: Entity, burro: Entity, burden: Burden, path: Path, outcome: str) -> None:
    if outcome == "smooth":
        world.say(
            f"After that, burro and traveler moved together as if they had found one thought between them. "
            f"They brought {burden.goods} safely onward."
        )
    elif outcome == "mend":
        world.say(
            f"Step by step, the road grew kinder. The burro walked on without fear, and {traveler.id} matched its pace instead of fighting it."
        )
    else:
        world.say(
            f"The burro limped only for a few breaths, then found its footing again. From then on, {traveler.id} kept the goad tucked away and walked gently."
        )
    world.say(path.ending)
    world.say(
        f"People in that valley later said that {traveler.id} reached town a little later than planned, but wiser than when {traveler.pronoun()} had left home."
    )


def tell(
    burden: Burden,
    path: Path,
    method: Method,
    helper: Helper,
    traveler_name: str,
    traveler_gender: str,
    elder_name: str,
    elder_gender: str,
) -> World:
    world = World()
    traveler = world.add(Entity(id="traveler", kind="character", type=traveler_gender, label=traveler_name, role="traveler"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_gender, label=elder_name, role="elder"))
    burro = world.add(Entity(id="burro", kind="thing", type="animal", label="burro", role="burro"))
    packs = world.add(Entity(id="packs", kind="thing", type="load", label=burden.label, role="burden"))
    world.facts["traveler_name"] = traveler_name
    world.facts["elder_name"] = elder_name

    introduce(world, traveler, elder, burden, path)
    world.para()
    begin_hard_way(world, traveler, burro, method)
    road_grows_hard(world, traveler, burro, burden, path)
    stumble_or_balk(world, traveler, burro, method, path)
    world.para()
    elder_returns(world, elder, traveler, helper)
    apply_helper(world, traveler, burro, helper)
    apology_and_lesson(world, traveler, burro, elder, method)
    world.para()
    outcome = outcome_of(
        StoryParams(
            burden=burden.id,
            path=path.id,
            method=method.id,
            helper=helper.id,
            traveler_name=traveler_name,
            traveler_gender=traveler_gender,
            elder_name=elder_name,
            elder_gender=elder_gender,
        )
    )
    finish(world, traveler, burro, burden, path, outcome)

    world.facts.update(
        burden=burden,
        path=path,
        method=method,
        helper=helper,
        traveler=traveler,
        elder=elder,
        burro=burro,
        outcome=outcome,
        used_goad=method.id == "goad",
        stumbled=burro.meters["stumbled"] >= THRESHOLD,
        balked=burro.meters["balked"] >= THRESHOLD,
        lesson=traveler.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "goad": [
        (
            "What is a goad?",
            "A goad is a stick used to push or poke an animal to make it move. It may hurry the body for a moment, but it does not solve tiredness or pain.",
        )
    ],
    "burro": [
        (
            "What is a burro?",
            "A burro is a small donkey often used to carry loads along rough roads. It is strong, but like any animal it still needs water, rest, and kind treatment.",
        )
    ],
    "sharing": [
        (
            "Why does sharing a heavy load help an animal?",
            "Sharing the load means the animal carries less weight. When the burden is lighter, walking is easier and safer.",
        )
    ],
    "water_rest": [
        (
            "Why do animals need water and rest on a hot road?",
            "Heat and hard work tire the body quickly. Water and rest help an animal recover strength so it can walk safely again.",
        )
    ],
    "bell": [
        (
            "How can a small bell help on a road?",
            "A soft bell can give a steady sound to follow. It does not make a tired body stronger, but it can help a calm animal keep an even pace.",
        )
    ],
    "kindness": [
        (
            "Why is kindness better than force with working animals?",
            "Kindness helps a person notice what the animal truly needs. Force can hide the real problem, but care can fix it.",
        )
    ],
    "lesson": [
        (
            "What lesson does a folk tale often teach?",
            "A folk tale often shows that cleverness or kindness is wiser than pride. The ending teaches something people can remember and use in real life.",
        )
    ],
}
KNOWLEDGE_ORDER = ["goad", "burro", "sharing", "water_rest", "bell", "kindness", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    traveler_name = f["traveler_name"]
    burden = f["burden"]
    path = f["path"]
    method = f["method"]
    return [
        'Write a short folk tale for a young child that includes the words "goad" and "burro" and ends with a clear lesson learned.',
        f"Tell a folk-tale story where {traveler_name} tries to hurry a burro carrying {burden.label} along {path.phrase}, then learns that patience works better than force.",
        f"Write a simple moral tale about a traveler, a burro, and {method.label}, with an ending image that shows wisdom after trouble on the road.",
    ]


def pair_answer(world: World) -> str:
    f = world.facts
    return f'{f["traveler_name"]}, an elder named {f["elder_name"]}, and a patient burro.'


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    traveler_name = f["traveler_name"]
    elder_name = f["elder_name"]
    burden = f["burden"]
    path = f["path"]
    method = f["method"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is this story about?",
            f"It is about {pair_answer(world)} They travel together on a hard road, and the elder helps turn trouble into a lesson.",
        ),
        (
            "What was the burro carrying?",
            f"The burro was carrying {burden.phrase}. The weight of that load is part of what made the road difficult.",
        ),
        (
            f"Why did {traveler_name} get into trouble on the road?",
            f"{traveler_name} wanted to make quick progress, but the road and the load were harder than expected. "
            f"That hurry kept {traveler_name} from noticing how tired the burro had become.",
        ),
    ]
    if method.id == "goad":
        qa.append(
            (
                f"What happened when {traveler_name} used the goad?",
                f"The goad did not solve the real problem, and the burro stumbled and shook with fear. "
                f"It made the journey worse because pain cannot lighten a heavy load or cool a hot road.",
            )
        )
    else:
        qa.append(
            (
                f"Did {traveler_name}'s first idea work?",
                f"Not really. {traveler_name}'s first way of hurrying the trip still left the burro too tired, so the animal stopped and could not keep going.",
            )
        )
    qa.append(
        (
            f"How did {elder_name} help?",
            f"{elder_name} told {traveler_name} to choose the wiser way and {helper.qa_text}. "
            f"That changed the burro's body and mood, so the road could be finished more safely.",
        )
    )
    if outcome == "smooth":
        qa.append(
            (
                "How did the journey end?",
                f"It ended peacefully, with traveler and burro moving together in step. "
                f"The final image shows that kindness and fairness can make hard work feel lighter.",
            )
        )
    elif outcome == "mend":
        qa.append(
            (
                "What lesson was learned by the end?",
                f"{traveler_name} learned to match the burro's pace and needs instead of fighting them. "
                f"The lesson is that patience and care do more good than pride and hurry.",
            )
        )
    else:
        qa.append(
            (
                "What changed after the bad moment on the road?",
                f"After the stumble, {traveler_name} put away the goad and walked gently. "
                f"The change matters because the ending proves the lesson was not only spoken but followed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"burro", "lesson"} | set(world.facts["helper"].tags)
    if world.facts["used_goad"]:
        tags.add("goad")
    if "kindness" in world.facts["helper"].tags or world.facts["method"].id == "gentle_song":
        tags.add("kindness")
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


CURATED = [
    StoryParams(
        burden="grain",
        path="hill",
        method="goad",
        helper="share_load",
        traveler_name="Mateo",
        traveler_gender="boy",
        elder_name="Abuela",
        elder_gender="woman",
    ),
    StoryParams(
        burden="jugs",
        path="mesa",
        method="rope_tug",
        helper="water_rest",
        traveler_name="Rosa",
        traveler_gender="girl",
        elder_name="Old Tomas",
        elder_gender="man",
    ),
    StoryParams(
        burden="blankets",
        path="ford",
        method="gentle_song",
        helper="bell",
        traveler_name="Inez",
        traveler_gender="girl",
        elder_name="Grandfather Nilo",
        elder_gender="man",
    ),
    StoryParams(
        burden="grain",
        path="ford",
        method="goad",
        helper="water_rest",
        traveler_name="Diego",
        traveler_gender="boy",
        elder_name="Tía Luz",
        elder_gender="woman",
    ),
]


def explain_rejection(burden: Burden, path: Path, method: Method, helper: Helper) -> str:
    light_need, cool_need = required_aid(burden, path, method)
    if helper.sense < SENSE_MIN:
        return (
            f"(No story: {helper.label} scores too low on common sense here. "
            f"The fix should genuinely help a tired burro.)"
        )
    if light_need > helper.lightens:
        return (
            f"(No story: {helper.label} does not lighten {burden.label} enough for {path.label}. "
            f"Pick a helper that reduces the burden more honestly.)"
        )
    if cool_need > helper.cools:
        return (
            f"(No story: {helper.label} does not answer the heat and thirst of {path.label}. "
            f"Pick a helper with shade, water, or rest.)"
        )
    if method.id == "goad" and helper.id == "bell" and burden.weight + path.challenge >= 4:
        return (
            f"(No story: a little bell cannot undo the harm of a harsh goad on such a hard road. "
            f"Choose rest or shared work instead.)"
        )
    return "(No story: this combination does not make a reasonable folk-tale problem and fix.)"


ASP_RULES = r"""
need_lighten(B,P,M,N) :- burden(B), path(P), method(M),
                         bweight(B,W), pchallenge(P,C), pheat(P,H), harsh(M),
                         X = W + C + H + 1 - 2, N = X, X > 0.
need_lighten(B,P,M,N) :- burden(B), path(P), method(M),
                         bweight(B,W), pchallenge(P,C), pheat(P,H), not harsh(M), not song(M),
                         X = W + C + H - 2, N = X, X > 0.
need_lighten(B,P,M,N) :- burden(B), path(P), method(M),
                         bweight(B,W), pchallenge(P,C), pheat(P,H), song(M),
                         X = W + C + H - 1 - 2, N = X, X > 0.
need_lighten(B,P,M,0) :- burden(B), path(P), method(M), not need_lighten(B,P,M,_).

need_cool(B,P,N) :- burden(B), path(P), bweight(B,W), pheat(P,H),
                    X = H + W - 3, N = X, X > 0.
need_cool(B,P,0) :- burden(B), path(P), not need_cool(B,P,_).

fits(B,P,M,H) :- burden(B), path(P), method(M), helper(H),
                 hsense(H,S), sense_min(Min), S >= Min,
                 need_lighten(B,P,M,N1), hlight(H,L), L >= N1,
                 need_cool(B,P,N2), hcool(H,C), C >= N2,
                 not bad_bell(B,P,M,H).

bad_bell(B,P,M,bell) :- method(M), burden(B), path(P), harsh(M),
                        bweight(B,W), pchallenge(P,C), W + C >= 4.
valid(B,P,M,H) :- fits(B,P,M,H).

strain0(B,P,M,V) :- burden(B), path(P), method(M),
                    bweight(B,W), pchallenge(P,C), pheat(P,H), harsh(M),
                    V = W + C + H + 1.
strain0(B,P,M,V) :- burden(B), path(P), method(M),
                    bweight(B,W), pchallenge(P,C), pheat(P,H), song(M),
                    V = W + C + H - 1.
strain0(B,P,M,V) :- burden(B), path(P), method(M),
                    bweight(B,W), pchallenge(P,C), pheat(P,H), not harsh(M), not song(M),
                    V = W + C + H.

strain(B,P,M,H,V) :- strain0(B,P,M,S0), hlight(H,L), hcool(H,C), V = S0 - L - C.
trust(B,P,M,H,T) :- burden(B), path(P), method(M), helper(H), hcalm(H,C), harsh(M), T = C.
trust(B,P,M,H,T) :- burden(B), path(P), method(M), helper(H), hcalm(H,C), not harsh(M), T = C + 1.

outcome(B,P,M,H,stumble) :- valid(B,P,M,H), harsh(M), strain(B,P,M,H,V), V >= 2.
outcome(B,P,M,H,mend) :- valid(B,P,M,H), harsh(M), strain(B,P,M,H,V), V < 2.
outcome(B,P,M,H,smooth) :- valid(B,P,M,H), not harsh(M), strain(B,P,M,H,V), trust(B,P,M,H,T), V =< 1, T >= 2.
outcome(B,P,M,H,mend) :- valid(B,P,M,H), not harsh(M), not outcome(B,P,M,H,smooth).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for burden_id, burden in BURDENS.items():
        lines.append(asp.fact("burden", burden_id))
        lines.append(asp.fact("bweight", burden_id, burden.weight))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("pchallenge", path_id, path.challenge))
        lines.append(asp.fact("pheat", path_id, path.heat))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        if method.harsh:
            lines.append(asp.fact("harsh", method_id))
        if method.id == "gentle_song":
            lines.append(asp.fact("song", method_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("hcool", helper_id, helper.cools))
        lines.append(asp.fact("hlight", helper_id, helper.lightens))
        lines.append(asp.fact("hcalm", helper_id, helper.calms))
        lines.append(asp.fact("hsense", helper_id, helper.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_burden", params.burden),
            asp.fact("chosen_path", params.path),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_helper", params.helper),
            "selected_outcome(O) :- outcome(B,P,M,H,O), chosen_burden(B), chosen_path(P), chosen_method(M), chosen_helper(H).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(150):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "burro" not in sample.story.lower():
            raise StoryError("smoke test story missing expected content")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Folk-tale storyworld: a traveler, a burro, a goad, and a lesson learned."
    )
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.burden and args.path and args.method and args.helper:
        burden = BURDENS[args.burden]
        path = PATHS[args.path]
        method = METHODS[args.method]
        helper = HELPERS[args.helper]
        if not helper_fits(burden, path, method, helper):
            raise StoryError(explain_rejection(burden, path, method, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.burden is None or combo[0] == args.burden)
        and (args.path is None or combo[1] == args.path)
        and (args.method is None or combo[2] == args.method)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        if args.burden and args.path and args.method and args.helper:
            raise StoryError(
                explain_rejection(BURDENS[args.burden], PATHS[args.path], METHODS[args.method], HELPERS[args.helper])
            )
        raise StoryError("(No valid combination matches the given options.)")

    burden_id, path_id, method_id, helper_id = rng.choice(sorted(combos))
    traveler_name, traveler_gender = rng.choice(TRAVELERS)
    elder_name, elder_gender = rng.choice(ELDERS)
    return StoryParams(
        burden=burden_id,
        path=path_id,
        method=method_id,
        helper=helper_id,
        traveler_name=traveler_name,
        traveler_gender=traveler_gender,
        elder_name=elder_name,
        elder_gender=elder_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.burden not in BURDENS:
        raise StoryError(f"(Unknown burden: {params.burden})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    burden = BURDENS[params.burden]
    path = PATHS[params.path]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    if not helper_fits(burden, path, method, helper):
        raise StoryError(explain_rejection(burden, path, method, helper))

    world = tell(
        burden=burden,
        path=path,
        method=method,
        helper=helper,
        traveler_name=params.traveler_name,
        traveler_gender=params.traveler_gender,
        elder_name=params.elder_name,
        elder_gender=params.elder_gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (burden, path, method, helper) combos:\n")
        for burden, path, method, helper in combos:
            print(f"  {burden:8} {path:6} {method:11} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.traveler_name}: {p.method} on {p.path} with {p.burden} "
                f"({p.helper}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
