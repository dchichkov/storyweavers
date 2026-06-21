#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shame_frantic_quince_kindness_myth.py
===============================================================

A standalone storyworld in a gentle mythic style.

Premise:
A child is chosen to carry the first quince of the season to a small hill shrine.
Because the child grows frantic on the path, the quince is damaged. Shame follows.
A kind elder teaches that the gods prefer honesty and kindness to proud pretending,
and together they try a repair that may fully restore the offering or may only
make it humble but worthy.

Run it:
    python storyworlds/worlds/gpt-5.4/shame_frantic_quince_kindness_myth.py
    python storyworlds/worlds/gpt-5.4/shame_frantic_quince_kindness_myth.py --path ford --repair wash
    python storyworlds/worlds/gpt-5.4/shame_frantic_quince_kindness_myth.py --repair gild
    python storyworlds/worlds/gpt-5.4/shame_frantic_quince_kindness_myth.py --all
    python storyworlds/worlds/gpt-5.4/shame_frantic_quince_kindness_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shame_frantic_quince_kindness_myth.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "priestess"}
        male = {"boy", "man", "father", "beekeeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {"priestess": "priestess", "beekeeper": "beekeeper"}.get(self.type, self.type)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Myth:
    id: str
    deity: str
    shrine: str
    gift_line: str
    blessing: str
    ending_image: str
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
class Path:
    id: str
    place: str
    hazard_line: str
    damage: str
    severity: int
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
class Helper:
    id: str
    type: str
    label: str
    entrance: str
    comfort: str
    lesson: str
    kindness_line: str
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
class Repair:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_damage_stirs_shame(world: World) -> list[str]:
    quince = world.get("quince")
    hero = world.get("hero")
    if quince.meters["damaged"] < THRESHOLD:
        return []
    sig = ("shame",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["shame"] += 1
    hero.memes["frantic"] += 1
    return []


def _r_kindness_blesses(world: World) -> list[str]:
    hero = world.get("hero")
    shrine = world.get("shrine")
    quince = world.get("quince")
    if hero.memes["confessed"] < THRESHOLD or hero.memes["kindness"] < THRESHOLD:
        return []
    if quince.meters["restored"] < THRESHOLD and quince.meters["humble"] < THRESHOLD:
        return []
    sig = ("blessing", quince.meters["restored"] >= THRESHOLD, quince.meters["humble"] >= THRESHOLD)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shrine.meters["favor"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="damage_stirs_shame", tag="emotional", apply=_r_damage_stirs_shame),
    Rule(name="kindness_blesses", tag="mythic", apply=_r_kindness_blesses),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def damage_severity(path: Path) -> int:
    return path.severity


def repair_holds(repair: Repair, path: Path) -> bool:
    return repair.power >= damage_severity(path)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for myth_id in MYTHS:
        for path_id, path in PATHS.items():
            if not path.damage:
                continue
            for repair_id, repair in REPAIRS.items():
                if repair.sense >= SENSE_MIN:
                    combos.append((myth_id, path_id, repair_id))
    return combos


def predict_damage(world: World, path_id: str) -> dict:
    sim = world.copy()
    path = PATHS[path_id]
    apply_damage(sim, path, narrate=False)
    hero = sim.get("hero")
    quince = sim.get("quince")
    return {
        "damaged": quince.meters["damaged"] >= THRESHOLD,
        "shame": hero.memes["shame"],
        "frantic": hero.memes["frantic"],
        "kind": sim.get("helper").memes["kindness"],
    }


def introduce(world: World, myth: Myth, hero: Entity) -> None:
    world.say(
        f"In the elder days, when hills still listened, {hero.id} was chosen to carry "
        f"the first quince of autumn to {myth.shrine}. {myth.gift_line}"
    )


def charge_task(world: World, myth: Myth, hero: Entity, quince: Entity) -> None:
    hero.memes["pride"] += 1
    quince.meters["whole"] += 1
    world.say(
        f"The fruit lay in {hero.pronoun('possessive')} palms, round and gold and fragrant, "
        f"as if a little sunset had been set there to keep."
    )


def hurry(world: World, hero: Entity, path: Path) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"But {path.place} was longer than {hero.id} remembered, and the child grew afraid of being late. "
        f"Soon {hero.pronoun()} was almost running, with a frantic heart and feet that forgot to listen to the ground."
    )


def warn_self(world: World, hero: Entity, path: Path) -> None:
    pred = predict_damage(world, path.id)
    world.facts["predicted_shame"] = pred["shame"]
    world.facts["predicted_frantic"] = pred["frantic"]
    world.say(
        f"Even then, some small wise part inside {hero.id} whispered that a sacred gift should travel slowly. "
        f"But hurry spoke louder than wisdom."
    )


def apply_damage(world: World, path: Path, narrate: bool = True) -> None:
    quince = world.get("quince")
    quince.meters["whole"] = 0.0
    quince.meters[path.damage] += 1
    quince.meters["damaged"] += 1
    propagate(world, narrate=False)
    if narrate:
        detail = {
            "muddy": "Brown water splashed up and left the quince muddy to its stem.",
            "bruised": "The quince struck a stone and took on a dark bruise beneath its bright skin.",
            "split": "A sharp thorn caught the fruit, and the golden skin split with a soft tear.",
        }[path.damage]
        world.say(f"{path.hazard_line} {detail}")


def shame_beat(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} stopped all at once. Shame rose hot in the child's throat. "
        f"{hero.pronoun().capitalize()} rubbed at the fruit in a frantic way, as if quick hands could turn time backward."
    )


def helper_arrives(world: World, helper: Entity, helper_cfg: Helper) -> None:
    helper.memes["kindness"] = 1.0
    world.say(helper_cfg.entrance)
    world.say(
        f'''{helper.id} saw the child's face and spoke softly. "{helper_cfg.comfort}'''
    )


def confess(world: World, hero: Entity, helper: Entity, helper_cfg: Helper, path: Path) -> None:
    hero.memes["confessed"] += 1
    hero.memes["courage"] += 1
    world.say(
        f'"I hurried," {hero.id} said, and the words came out shaking. "Now the quince is {path.damage}, '
        f'and I have brought shame instead of honor."'
    )
    world.say(
        f'{helper.id} knelt beside {hero.pronoun("object")}. "{helper_cfg.kindness_line}"'
    )


def repair_attempt(world: World, repair: Repair, path: Path) -> None:
    quince = world.get("quince")
    body = repair.text.format(damage=path.damage)
    world.say(body)
    if repair_holds(repair, path):
        quince.meters["restored"] += 1
        quince.meters["damaged"] = 0.0
        quince.meters[path.damage] = 0.0
        world.say(
            "The child watched closely. The fruit was no longer proud and perfect, yet it looked cared for, ready to be carried honestly."
        )
    else:
        quince.meters["humble"] += 1
        world.say(repair.fail.format(damage=path.damage))


def offer(world: World, myth: Myth, hero: Entity, helper: Entity, helper_cfg: Helper) -> None:
    shrine = world.get("shrine")
    propagate(world, narrate=False)
    world.say(
        f"Together they climbed the last stones to {myth.shrine}, and {hero.id} laid the quince down with both hands."
    )
    if shrine.meters["favor"] >= THRESHOLD and world.get("quince").meters["restored"] >= THRESHOLD:
        hero.memes["relief"] += 1
        world.say(
            f"At once the air turned sweet. {myth.blessing} The shame left {hero.id} like mist leaving a field."
        )
        world.say(
            f'{helper.id} smiled. "{helper_cfg.lesson}"'
        )
        outcome = "blessed"
    else:
        hero.memes["relief"] += 1
        world.say(
            "No thunder spoke, and no gold fire leapt from the altar. Yet the lamp by the stone door burned steady and gentle, as if the shrine itself approved the truth."
        )
        world.say(
            f'{helper.id} touched the child\'s shoulder. "{helper_cfg.lesson}"'
        )
        outcome = "humble"
    world.say(myth.ending_image)
    world.facts["outcome"] = outcome
@dataclass
class StoryParams:
    myth: str
    path: str
    helper: str
    repair: str
    hero_name: str
    hero_type: str
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


KNOWLEDGE = {
    "quince": [
        (
            "What is a quince?",
            "A quince is a yellow fruit that smells sweet and floral. People often cook it because it is hard when raw."
        )
    ],
    "shrine": [
        (
            "What is a shrine?",
            "A shrine is a special place people visit to pray, leave gifts, or remember a holy power. It is usually smaller than a temple."
        )
    ],
    "honey": [
        (
            "Why do people use honey on fruit?",
            "Honey is sweet and sticky, so it can glaze fruit and make it taste rich. In old stories it also feels like a gift of care."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to be gentle and helpful, especially when someone is upset or ashamed. It can help people tell the truth and feel brave again."
        )
    ],
    "truth": [
        (
            "Why is telling the truth important after a mistake?",
            "Telling the truth helps other people understand what really happened. It is the first step toward fixing a problem fairly and kindly."
        )
    ],
    "bruise": [
        (
            "What happens when fruit gets bruised?",
            "A bruise means the fruit was bumped hard and the flesh inside was hurt. The skin may stay on, but the soft part underneath turns dark."
        )
    ],
    "mud": [
        (
            "Why does muddy fruit need to be washed?",
            "Mud can leave grit and dirt on the fruit. Washing takes the dirt away so the fruit is clean again."
        )
    ],
    "split": [
        (
            "Why is split fruit harder to fix than muddy fruit?",
            "Split fruit is torn open, so the fruit itself is hurt, not just dirty. Washing helps dirt, but it cannot close a tear."
        )
    ],
}
KNOWLEDGE_ORDER = ["quince", "shrine", "kindness", "truth", "honey", "bruise", "mud", "split"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    myth = f["myth"]
    path = f["path"]
    hero_name = f["hero_name"]
    outcome = f.get("outcome", "blessed")
    if outcome == "blessed":
        return [
            'Write a short myth for a 3-to-5-year-old that uses the words "shame," "frantic," and "quince," and makes kindness save the day.',
            f"Tell a mythic story where {hero_name} damages a sacred quince on {path.place}, feels shame, and learns that kindness and honesty please the gods more than pride.",
            f"Write a gentle myth about a child carrying a quince to {myth.shrine}, making a frantic mistake, and ending with a blessing because truth was told."
        ]
    return [
        'Write a short myth for a 3-to-5-year-old that uses the words "shame," "frantic," and "quince," and shows kindness turning a mistake into a humble lesson.',
        f"Tell a mythic story where {hero_name} harms a sacred quince on {path.place}, confesses in shame, and finds a quiet ending through kindness instead of a bright miracle.",
        f"Write a myth where the gods value honesty more than a perfect offering after a frantic child makes a mistake."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    myth = f["myth"]
    path = f["path"]
    repair = f["repair"]
    hero_name = f["hero_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a child chosen to carry the first quince to {myth.shrine}, and {helper.label}, who helped along the way."
        ),
        (
            f"Why was {hero_name} carrying the quince?",
            f"{hero_name} was bringing the first quince of the season as an offering. In that village, people believed such a gift could bring blessing if it was carried with a clear heart."
        ),
        (
            f"What happened on {path.place}?",
            f"The child hurried too fast there, and the quince became {path.damage}. That accident is what filled {hero_name} with shame and made the child frantic."
        ),
        (
            f"Why did {hero_name} feel shame?",
            f"{hero_name} felt shame because the sacred quince had been damaged while in the child's care. The shame grew worse because the child had been hurrying in a frantic way instead of walking carefully."
        ),
        (
            f"How did {helper.label} show kindness?",
            f"{helper.label.capitalize()} spoke gently instead of scolding and helped {hero_name} tell the truth. That kindness made it easier for the child to stop hiding and start fixing what could be fixed."
        ),
    ]
    if f["outcome"] == "blessed":
        qa.append(
            (
                "How did they try to mend the problem?",
                f"They {repair.qa_text}. The repair truly matched the harm, so the offering could be brought honestly and with care."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The shrine answered with a blessing, and {hero_name}'s shame lifted. The ending shows that kindness and truth changed the mistake into something good."
            )
        )
    else:
        qa.append(
            (
                "How did they try to mend the problem?",
                f"They {repair.qa_text}. It did not make the quince fully whole again, but it let them bring a humble and truthful gift."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"There was no bright miracle, but the shrine felt peaceful and welcoming. The child still learned that kindness and truth mattered more than pretending the damage was gone."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"quince", "shrine", "kindness", "truth"}
    tags |= set(f["path"].tags)
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["repair"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in list(world.entities.values()):
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def outcome_of(params: StoryParams) -> str:
    repair = REPAIRS[params.repair]
    path = PATHS[params.path]
    return "blessed" if repair_holds(repair, path) else "humble"


def explain_repair(rid: str) -> str:
    r = REPAIRS[rid]
    better = ", ".join(sorted(x.id for x in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). A mythic story here should prefer honest care over decorative pretending. "
        f"Try one of: {better}.)"
    )


ASP_RULES = r"""
valid(M, P, R) :- myth(M), path(P), repair(R), sensible(R).

severity(P, S) :- path_damage(P, _), path_severity(P, S).
works(R, P) :- repair_power(R, RP), severity(P, S), RP >= S.
outcome(blessed) :- chosen_path(P), chosen_repair(R), works(R, P).
outcome(humble) :- chosen_path(P), chosen_repair(R), not works(R, P).

sensible(R) :- repair(R), repair_sense(R, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for myth_id in MYTHS:
        lines.append(asp.fact("myth", myth_id))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("path_damage", path_id, path.damage))
        lines.append(asp.fact("path_severity", path_id, path.severity))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("repair_sense", repair_id, repair.sense))
        lines.append(asp.fact("repair_power", repair_id, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_path", params.path),
        asp.fact("chosen_repair", params.repair),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        myth="sunwell",
        path="steps",
        helper="priestess",
        repair="leaf_cradle",
        hero_name="Iria",
        hero_type="girl",
    ),
    StoryParams(
        myth="rivermother",
        path="ford",
        helper="beekeeper",
        repair="wash",
        hero_name="Timon",
        hero_type="boy",
    ),
    StoryParams(
        myth="hearthlion",
        path="thorn_gap",
        helper="shepherdess",
        repair="slice_and_share",
        hero_name="Mela",
        hero_type="girl",
    ),
    StoryParams(
        myth="sunwell",
        path="thorn_gap",
        helper="priestess",
        repair="wash",
        hero_name="Leos",
        hero_type="boy",
    ),
    StoryParams(
        myth="rivermother",
        path="steps",
        helper="shepherdess",
        repair="slice_and_share",
        hero_name="Rhea",
        hero_type="girl",
    ),
]


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    py_sens = {r.id for r in sensible_repairs()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible repairs match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    for s in range(100):
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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child damages a sacred quince, feels shame, and learns kindness in a mythic world."
    )
    ap.add_argument("--myth", choices=MYTHS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        c for c in valid_combos()
        if (args.myth is None or c[0] == args.myth)
        and (args.path is None or c[1] == args.path)
        and (args.repair is None or c[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    myth_id, path_id, repair_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)

    return StoryParams(
        myth=myth_id,
        path=path_id,
        helper=helper_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        myth = MYTHS[params.myth]
        path = PATHS[params.path]
        helper_cfg = HELPERS[params.helper]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from None

    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        myth=myth,
        path=path,
        helper_cfg=helper_cfg,
        repair=repair,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name),
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (myth, path, repair) combos:\n")
        for myth_id, path_id, repair_id in combos:
            print(f"  {myth_id:11} {path_id:10} {repair_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.path}, {p.repair}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    myth: Myth,
    path: Path,
    helper_cfg: Helper,
    repair: Repair,
    *,
    hero_name: str = "Iria",
    hero_type: str = "girl",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_cfg.label, role="helper"))
    quince = world.add(Entity(id="quince", kind="thing", type="fruit", label="quince"))
    shrine = world.add(Entity(id="shrine", kind="thing", type="shrine", label=myth.shrine))

    hero.attrs["name"] = hero_name
    helper.attrs["cfg"] = helper_cfg.id
    world.facts["hero_name"] = hero_name
    world.facts["hero_type"] = hero_type
    world.facts["myth"] = myth
    world.facts["path"] = path
    world.facts["helper_cfg"] = helper_cfg
    world.facts["repair"] = repair

    introduce(world, myth, hero)
    charge_task(world, myth, hero, quince)

    world.para()
    hurry(world, hero, path)
    warn_self(world, hero, path)
    apply_damage(world, path, narrate=True)
    shame_beat(world, hero)

    world.para()
    helper_arrives(world, helper, helper_cfg)
    confess(world, hero, helper, helper_cfg, path)
    hero.memes["kindness"] += 1
    repair_attempt(world, repair, path)

    world.para()
    offer(world, myth, hero, helper, helper_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        quince=quince,
        shrine=shrine,
        damage=path.damage,
        severe=path.severity,
        restored=quince.meters["restored"] >= THRESHOLD,
        humble=quince.meters["humble"] >= THRESHOLD,
        confessed=hero.memes["confessed"] >= THRESHOLD,
    )
    return world


MYTHS = {
    "sunwell": Myth(
        id="sunwell",
        deity="the Well of Dawn",
        shrine="the little dawn shrine above the terraces",
        gift_line="It was said that if the first fruit was offered with a clear heart, the winter jars would never stand empty.",
        blessing="A pale beam slid over the altar, and every olive leaf on the hill flashed silver-green.",
        ending_image="When evening came, the village lamps looked less like lonely sparks and more like stars brought down among kind hands.",
        tags={"shrine", "blessing", "kindness"},
    ),
    "rivermother": Myth(
        id="rivermother",
        deity="the River Mother",
        shrine="the river shrine where reeds bowed in circles",
        gift_line="People said the River Mother remembered every generous deed and sent clear water to the orchards that remembered her.",
        blessing="From the reed shadows came the sound of easy water, and the channels below the orchards filled with bright running light.",
        ending_image="That night the irrigation ditches whispered through the dark like patient songs, and the quince trees slept with shining leaves.",
        tags={"river", "blessing", "kindness"},
    ),
    "hearthlion": Myth(
        id="hearthlion",
        deity="the Lion of the Hearth",
        shrine="the warm stone shrine beside the public oven",
        gift_line="The old ones taught that the Hearth Lion guarded homes where gifts were given gently and truthfully.",
        blessing="The oven-fire, though no one fed it, glowed deep and red, and the smell of bread drifted into the square.",
        ending_image="Afterward, every doorway in the village seemed warmer, and children carried supper home as carefully as treasure.",
        tags={"hearth", "blessing", "kindness"},
    ),
}

PATHS = {
    "ford": Path(
        id="ford",
        place="the shallow ford below the fig roots",
        hazard_line="At the ford a loose stone rolled underfoot, and the child stumbled knee-deep into the water.",
        damage="muddy",
        severity=1,
        tags={"water", "mud"},
    ),
    "steps": Path(
        id="steps",
        place="the old temple steps cut into the hill",
        hazard_line="On the steps one sandal skidded, and the quince slipped from the child's fingers before being snatched back.",
        damage="bruised",
        severity=1,
        tags={"stone", "bruise"},
    ),
    "thorn_gap": Path(
        id="thorn_gap",
        place="the narrow thorn gap between the old walls",
        hazard_line="In the thorn gap the child turned sideways too quickly, and the branch clawed at the fruit.",
        damage="split",
        severity=2,
        tags={"thorn", "split"},
    ),
}

HELPERS = {
    "beekeeper": Helper(
        id="beekeeper",
        type="beekeeper",
        label="the old beekeeper",
        entrance="Then from the shade of two cypress trees came the old beekeeper, with honey on his sleeves and slow steps that feared no lateness.",
        comfort="A fruit may be hurt without a child becoming bad.",
        lesson="The gods do not hunger for spotless gifts. They hunger for truthful hearts and for the kindness that mends what can be mended.",
        kindness_line="Tell the truth first. Kind hands can do the rest, even when they cannot make a thing perfect again.",
        tags={"honey", "kindness"},
    ),
    "priestess": Helper(
        id="priestess",
        type="priestess",
        label="the hill priestess",
        entrance="From a bend in the path came the hill priestess carrying a clay lamp that did not flicker, though the wind was moving.",
        comfort="Do not let shame make you harder than the stone you serve.",
        lesson="Kindness is a better offering than pretending. A true gift may be small and still be welcome.",
        kindness_line="Speak plainly. A shrine can bear an honest bruise better than a hidden lie.",
        tags={"lamp", "kindness"},
    ),
    "shepherdess": Helper(
        id="shepherdess",
        type="woman",
        label="the young shepherdess",
        entrance="A young shepherdess came down the slope with three white goats behind her, and she heard the small broken sound in the child's breathing.",
        comfort="You are frightened, not ruined.",
        lesson="What is given kindly grows larger on the way to the gods, even if the hands that carry it are trembling.",
        kindness_line="Let us be gentle with the fruit and with you. Both were hurt by haste.",
        tags={"goats", "kindness"},
    ),
}

REPAIRS = {
    "wash": Repair(
        id="wash",
        label="wash the fruit in spring water",
        sense=3,
        power=1,
        text="The helper carried the quince to a spring bowl and washed away the dirt with cool water and a clean linen corner.",
        fail="The fruit looked cleaner, but the hurt under the skin still showed. They chose not to hide it.",
        qa_text="washed the quince in spring water and carried it honestly",
        tags={"water", "wash"},
    ),
    "leaf_cradle": Repair(
        id="leaf_cradle",
        label="nest the fruit in bay leaves",
        sense=2,
        power=1,
        text="The helper laid the quince in a cradle of fresh bay leaves so the damaged place would rest instead of being rubbed raw.",
        fail="The leaves could hold the fruit gently, but they could not make the deepest harm vanish. They still brought it with the truth.",
        qa_text="set the quince in bay leaves so it could be carried gently",
        tags={"leaves", "care"},
    ),
    "slice_and_share": Repair(
        id="slice_and_share",
        label="trim and share the fruit with honey",
        sense=3,
        power=2,
        text="With a little knife the helper trimmed away the worst of the {damage}, glazed the slices with honey, and set them on a clean fig leaf so the offering became a gift meant to be shared.",
        fail="Even after the careful trimming, the gift was no longer splendid. So they offered it as a humble shared meal instead of a boast.",
        qa_text="trimmed the damaged part, glazed the quince with honey, and offered it as a shared gift",
        tags={"honey", "share", "care"},
    ),
    "gild": Repair(
        id="gild",
        label="cover the hurt with gold ribbon",
        sense=1,
        power=0,
        text="The child wrapped a bright ribbon around the wounded place, hoping shine might do the work of honesty.",
        fail="The ribbon only made the hidden damage look more hidden.",
        qa_text="hid the damaged place with ribbon",
        tags={"pretend"},
    ),
}

GIRL_NAMES = ["Iria", "Mela", "Thessa", "Danae", "Neris", "Elia", "Rhea", "Seli"]
BOY_NAMES = ["Timon", "Leos", "Damon", "Panos", "Aren", "Nikos", "Pheron", "Iason"]

if __name__ == "__main__":
    main()
