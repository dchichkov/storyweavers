#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py
=========================================================

A standalone storyworld for a playful mythic tale about a child who makes a
showy bid for glory with a market product, ignores a warning to heed the old
rule, startles a sacred being, and learns a calmer way to ask for wonder.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate over which products can trouble which sacred targets
- a deterministic outcome model (averted / soothed / blustered)
- prose driven by simulated state, not by slot-swapping
- an inline ASP twin for parity checks

The stories keep a myth-like voice, but with warm humor: winds snatch hats,
geese honk from clouds, melons wobble downhill, and the lesson lands gently.

Run it
------
    python storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py
    python storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py --product thunder_whistle --target cloud_geese
    python storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py --target stone_lion
    python storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py --all
    python storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py --json
    python storyworlds/worlds/gpt-5.4/product_heed_bid_humor_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
SENSE_MIN = 2
BOLDNESS_INIT = 6.0
CAREFUL_TRAITS = {"careful", "wise", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    sensitive_to: set[str] = field(default_factory=set)
    sacred: bool = False
    # Physical/emotional axes.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "priestess", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "priestess": "priestess",
            "priest": "priest",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
class Festival:
    id: str
    place: str
    opening: str
    crowd_detail: str
    shrine: str
    closing: str
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
class Product:
    id: str
    label: str
    phrase: str
    boast: str
    sound_tag: str
    noise: int
    wake_word: str
    sales_line: str
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
class Target:
    id: str
    label: str
    the: str
    rest_place: str
    nuisance: str
    severity: int
    sensitive_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in ("boaster", "cautioner")]

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


def _r_turmoil(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["startled"] < THRESHOLD:
            continue
        sig = ("turmoil", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        room = world.get("square")
        room.meters["gusts"] += 1
        room.meters["chaos"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
            kid.memes["awe"] += 1
        out.append("__gusts__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="turmoil", tag="physical", apply=_r_turmoil),
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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(product: Product, target: Target) -> bool:
    return product.sound_tag in target.sensitive_to and product.noise >= 1


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def best_repair() -> Repair:
    return max(REPAIRS.values(), key=lambda r: r.sense)


def disturbance_severity(target: Target, delay: int) -> int:
    return target.severity + delay


def is_soothed(repair: Repair, target: Target, delay: int) -> bool:
    return repair.power >= disturbance_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, boaster_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > boaster_age
    authority = initial_caution(trait) + 1.0 + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BOLDNESS_INIT


def predict_mischief(world: World, target_id: str) -> dict:
    sim = world.copy()
    target_ent = sim.get(target_id)
    target_ent.meters["startled"] += 1
    propagate(sim, narrate=False)
    return {
        "startled": target_ent.meters["startled"] >= THRESHOLD,
        "gusts": sim.get("square").meters["gusts"],
        "chaos": sim.get("square").meters["chaos"],
    }


def play_setup(world: World, boaster: Entity, cautioner: Entity, festival: Festival) -> None:
    boaster.memes["joy"] += 1
    cautioner.memes["joy"] += 1
    world.say(
        f"In the age when the hills still listened and the small gods still gossiped, "
        f"{festival.opening} {festival.place}. {festival.crowd_detail}"
    )
    world.say(
        f"{boaster.id} and {cautioner.id} slipped through the crowd with festival cakes on "
        f"their fingers and bright plans in their heads."
    )


def show_need(world: World, boaster: Entity, festival: Festival, target: Target) -> None:
    world.say(
        f"Above them, {festival.shrine} watched over {target.rest_place}. Everyone said the sacred "
        f"creature there liked peace better than praise."
    )
    world.say(
        f"But {boaster.id} had a shining thought: if {boaster.pronoun()} could stir a wonder in front "
        f"of the whole square, {boaster.pronoun()} might become the most-talked-about child in town."
    )


def tempt(world: World, boaster: Entity, product: Product) -> None:
    boaster.memes["swagger"] += 1
    world.say(
        f"At a crooked stall, a peddler lifted {product.phrase}. "
        f'"Here is my finest product," he cried. "{product.sales_line}"'
    )
    world.say(
        f"{boaster.id}'s eyes grew round. Making a grand bid for glory suddenly seemed as easy as "
        f"blowing, clapping, or whirling one bright thing."
    )


def warn(world: World, cautioner: Entity, boaster: Entity, product: Product, target: Target, elder: Entity) -> None:
    pred = predict_mischief(world, "target")
    cautioner.memes["caution"] += 1
    world.facts["predicted_gusts"] = pred["gusts"]
    world.facts["predicted_chaos"] = pred["chaos"]
    extra = ""
    if cautioner.memes["caution"] >= 6:
        extra = f" {cautioner.pronoun().capitalize()} sounded very sure."
    world.say(
        f'{cautioner.id} tugged {boaster.pronoun("possessive")} sleeve. "Do not use {product.label} by '
        f'{target.the}," {cautioner.pronoun()} said. "You should heed {elder.label_word}\'s rule. '
        f'If {target.the} wakes the wrong way, the square will start dancing before anyone asks it to."{extra}'
    )


def defy(world: World, boaster: Entity, cautioner: Entity, product: Product) -> None:
    boaster.memes["defiance"] += 1
    older = boaster.attrs.get("relation") == "siblings" and boaster.age > cautioner.age
    if older:
        world.say(
            f'"I only want one brave moment," {boaster.id} said. Because {boaster.pronoun()} was the older '
            f"sibling, {cautioner.id} could not quite stop {boaster.pronoun('object')}. "
            f"{boaster.id} raised {product.label} with a grin too large for wisdom."
        )
    else:
        world.say(
            f'"I only want one brave moment," {boaster.id} said, and lifted {product.label} before '
            f"{cautioner.id} could pull {boaster.pronoun('object')} back."
        )


def back_down(world: World, boaster: Entity, cautioner: Entity, product: Product, elder: Entity) -> None:
    boaster.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    boaster.memes["swagger"] = 0.0
    sib = "brother" if cautioner.type == "boy" else "sister"
    world.say(
        f'{boaster.id} opened {boaster.pronoun("possessive")} mouth to answer, then saw how steady '
        f'{cautioner.id} looked. Because {cautioner.id} was {boaster.pronoun("possessive")} older {sib}, '
        f'the bold idea suddenly seemed smaller than it had a moment before.'
    )
    world.say(
        f'{boaster.id} lowered {product.label}. "All right," {boaster.pronoun()} said. '
        f'"I will heed the rule." Together they carried the noisy product straight back to the stall and '
        f"told {elder.label_word} what tempting nonsense the peddler had been selling."
    )


def awaken(world: World, boaster: Entity, product: Product, target_ent: Entity, target: Target) -> None:
    target_ent.meters["startled"] += 1
    target_ent.meters["flutter"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{product.boast} {product.wake_word} answered at once. {target.The} jerked awake in {target.rest_place}, "
        f"and the air puffed its cheeks like a child trying very hard to look important."
    )
    world.say(target.nuisance)


def alarm(world: World, cautioner: Entity, boaster: Entity, target: Target, elder: Entity) -> None:
    world.say(
        f'"{boaster.id}!" cried {cautioner.id}. "{target.The} is awake!"'
    )
    world.say(f'"{elder.label_word.capitalize()}!"')


def soothe(world: World, elder: Entity, repair: Repair, target_ent: Entity, target: Target, festival: Festival) -> None:
    target_ent.meters["startled"] = 0.0
    target_ent.meters["flutter"] = 0.0
    world.get("square").meters["gusts"] = 0.0
    world.get("square").meters["chaos"] = 0.0
    world.say(
        f"{elder.label_word.capitalize()} came hurrying from the shrine steps and {repair.text.replace('{target}', target.label)}."
    )
    world.say(
        f"Soon the wild little weather folded itself up again. Even the hats settled back on heads as if they had merely gone on a short adventure."
    )
    world.say(
        f"The people laughed, and {festival.closing}"
    )


def lesson(world: World, elder: Entity, boaster: Entity, cautioner: Entity, product: Product) -> None:
    for kid in (boaster, cautioner):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a heartbeat, nobody spoke except one very proud chicken from the market.")
    world.say(
        f'Then {elder.label_word} crouched beside them and smiled the patient smile of someone who had seen many foolish ideas wear shiny shoes. '
        f'"Wonder listens best to gentle hands," {elder.pronoun()} said. '
        f'"When an old rule tells you to heed it, heed it. A loud bid for glory can wake more than applause."'
    )
    world.say(
        f'{boaster.id} nodded so fast that {boaster.pronoun("possessive")} hair bounced. '
        f'{cautioner.id} nodded too, because being right is sweeter when everyone is safe.'
    )


def new_way(world: World, elder: Entity, boaster: Entity, cautioner: Entity, festival: Festival) -> None:
    boaster.memes["joy"] += 1
    cautioner.memes["joy"] += 1
    boaster.memes["safety"] += 1
    cautioner.memes["safety"] += 1
    world.say(
        f"A little later, {elder.label_word} showed them the proper way to ask for a blessing: a small bowl of figs, a quiet bow, and one clear song sung without showing off."
    )
    world.say(
        f"This time {boaster.id} sang beside {cautioner.id} instead of ahead of {cautioner.pronoun('object')}. "
        f"A soft breeze circled the shrine, cool as river water."
    )
    world.say(
        f"The people smiled, the bells chimed politely, and {festival.closing}"
    )


def bluster_fail(world: World, elder: Entity, repair: Repair, target_ent: Entity, target: Target) -> None:
    target_ent.meters["startled"] += 1
    world.get("square").meters["gusts"] += 1
    world.get("square").meters["chaos"] += 1
    world.say(
        f"{elder.label_word.capitalize()} {repair.fail.replace('{target}', target.label)}."
    )
    world.say(
        "The gusts grew cheekier. Hats flew, laundry sailed like flags, and three melons rolled downhill as if they had urgent business elsewhere."
    )


def loss_and_laughter(world: World, elder: Entity, boaster: Entity, cautioner: Entity) -> None:
    boaster.memes["fear"] += 1
    cautioner.memes["fear"] += 1
    world.say(
        f"There was no use pretending to be heroic. {elder.label_word.capitalize()} herded the children under the shrine awning while the villagers chased baskets, hats, and one scandalized goose."
    )
    world.say(
        f"Nobody was hurt, but the whole fair had to pause until the sacred temper tired itself out. "
        f"{boaster.id}'s grand bid for glory turned into the longest afternoon of sweeping anyone could remember."
    )


def grim_lesson(world: World, elder: Entity, boaster: Entity, cautioner: Entity, product: Product) -> None:
    for kid in (boaster, cautioner):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'At last the wind sulked away. {elder.label_word.capitalize()} wrapped both children in one shawl and said, '
        f'"You are safe, and that is good. But let this stay in your bones: if a wise warning tells you to heed it, do not laugh first and listen later."'
    )
    world.say(
        f"{boaster.id} never forgot how much sweeping followed one noisy product and one foolish moment. "
        f"After that, any bid for praise had to pass through thought before it reached {boaster.pronoun('possessive')} mouth."
    )


def tell(
    festival: Festival,
    product: Product,
    target: Target,
    repair: Repair,
    *,
    boaster_name: str = "Ivo",
    boaster_gender: str = "boy",
    cautioner_name: str = "Nia",
    cautioner_gender: str = "girl",
    elder_type: str = "priestess",
    trait: str = "careful",
    delay: int = 0,
    boaster_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    pet: str = "",
) -> World:
    world = World()
    boaster = world.add(
        Entity(
            id=boaster_name,
            kind="character",
            type=boaster_gender,
            role="boaster",
            traits=["bold"],
            age=boaster_age,
            attrs={"relation": relation},
        )
    )
    cautioner = world.add(
        Entity(
            id=cautioner_name,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation, "pet": pet},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    square = world.add(
        Entity(
            id="square",
            type="square",
            label="the market square",
        )
    )
    target_ent = world.add(
        Entity(
            id="target",
            type="sacred",
            label=target.label,
            sacred=True,
            sensitive_to=set(target.sensitive_to),
        )
    )
    item = world.add(
        Entity(
            id="product",
            type="product",
            label=product.label,
        )
    )

    boaster.memes["boldness"] = BOLDNESS_INIT
    cautioner.memes["trust"] = float(trust)
    cautioner.memes["caution"] = initial_caution(trait)
    square.meters["gusts"] = 0.0
    square.meters["chaos"] = 0.0
    target_ent.meters["startled"] = 0.0
    target_ent.meters["flutter"] = 0.0
    world.facts["pet"] = pet
    world.facts["relation"] = relation

    play_setup(world, boaster, cautioner, festival)
    show_need(world, boaster, festival, target)

    world.para()
    tempt(world, boaster, product)
    warn(world, cautioner, boaster, product, target, elder)

    averted = would_avert(relation, boaster.age, cautioner.age, trait)
    if averted:
        back_down(world, boaster, cautioner, product, elder)
        world.para()
        new_way(world, elder, boaster, cautioner, festival)
        severity = 0
        soothed = True
    else:
        defy(world, boaster, cautioner, product)
        world.para()
        awaken(world, boaster, product, target_ent, target)
        alarm(world, cautioner, boaster, target, elder)
        severity = disturbance_severity(target, delay)
        target_ent.meters["severity"] = float(severity)
        soothed = is_soothed(repair, target, delay)

        world.para()
        if soothed:
            soothe(world, elder, repair, target_ent, target, festival)
            lesson(world, elder, boaster, cautioner, product)
            world.para()
            new_way(world, elder, boaster, cautioner, festival)
        else:
            bluster_fail(world, elder, repair, target_ent, target)
            loss_and_laughter(world, elder, boaster, cautioner)
            grim_lesson(world, elder, boaster, cautioner, product)

    outcome = "averted" if averted else ("soothed" if soothed else "blustered")
    world.facts.update(
        festival=festival,
        product_cfg=product,
        target_cfg=target,
        repair=repair,
        boaster=boaster,
        cautioner=cautioner,
        elder=elder,
        target=target_ent,
        item=item,
        outcome=outcome,
        startled=target_ent.meters["severity"] >= THRESHOLD or target_ent.meters["flutter"] >= THRESHOLD,
        severity=severity,
        delay=delay,
        promised=boaster.memes["lesson"] >= THRESHOLD,
    )
    return world


FESTIVALS = {
    "windfair": Festival(
        id="windfair",
        place="in the hill town of Bell Hollow",
        opening="the Windfair was ringing",
        crowd_detail="Blue ribbons snapped from stalls, and every baker in the square claimed the gods preferred his cakes.",
        shrine="the little shrine of the listening sky",
        closing="the day felt merry instead of noisy, which in Bell Hollow counted as a miracle.",
        tags={"festival", "wind"},
    ),
    "sunsteps": Festival(
        id="sunsteps",
        place="on the warm terraces of Sunsteps",
        opening="the market of first fruit was humming",
        crowd_detail="Peddlers shouted, priests polished brass bowls, and a donkey chewed a garland with saintly calm.",
        shrine="the painted stair-shrine",
        closing="the terraces glowed gold, and even the donkey looked pleased with the ending.",
        tags={"festival", "market"},
    ),
    "rivermoon": Festival(
        id="rivermoon",
        place="beside the stone quays of Rivermoon",
        opening="the Lantern Bargain was beginning",
        crowd_detail="Paper fish bobbed on strings, fiddles squeaked merrily, and traders praised their wares as if each one had been invented by a star.",
        shrine="the river gate shrine",
        closing="the lanterns drifted out smoothly, and nobody's hat had to be fished from the water.",
        tags={"festival", "river"},
    ),
}

PRODUCTS = {
    "thunder_whistle": Product(
        id="thunder_whistle",
        label="the thunder whistle",
        phrase="a tin thunder whistle with red tassels",
        boast="Peep-PEEP!",
        sound_tag="shrill",
        noise=3,
        wake_word="A sharp cry",
        sales_line="One peep and the sky itself will look your way!",
        tags={"whistle", "sound"},
    ),
    "bronze_clapper": Product(
        id="bronze_clapper",
        label="the bronze clapper",
        phrase="a bronze clapper shaped like a smiling fish",
        boast="Clang-clang!",
        sound_tag="clang",
        noise=2,
        wake_word="A brassy knock",
        sales_line="Strike it once and even sleepy spirits will sit up straight!",
        tags={"clapper", "sound"},
    ),
    "feather_fan": Product(
        id="feather_fan",
        label="the feather fan",
        phrase="a peacock-feather fan with a silver handle",
        boast="Fwiff-fwiff!",
        sound_tag="flutter",
        noise=1,
        wake_word="A tickly rush",
        sales_line="Wave it and a breeze will rush to serve you like a little prince!",
        tags={"fan", "wind"},
    ),
}

TARGETS = {
    "cloud_geese": Target(
        id="cloud_geese",
        label="cloud geese",
        the="the cloud geese",
        rest_place="their nest of white vapor above the shrine",
        nuisance="At once they burst up honking. Their wings beat gusts through the square, snatching caps, puffing skirts, and turning prayer smoke into curly mustaches.",
        severity=3,
        sensitive_to={"shrill", "clang"},
        tags={"geese", "wind", "myth"},
    ),
    "nap_dragon": Target(
        id="nap_dragon",
        label="the nap dragon",
        the="the nap dragon",
        rest_place="a sunny coil behind the shrine wall",
        nuisance="The nap dragon sneezed itself awake. Warm puffs sent market parasols spinning, and a line of figs rolled away as if escaping taxes.",
        severity=2,
        sensitive_to={"flutter", "shrill"},
        tags={"dragon", "wind", "myth"},
    ),
    "stone_lion": Target(
        id="stone_lion",
        label="the stone lion spirit",
        the="the stone lion spirit",
        rest_place="inside the old lion statue by the gate",
        nuisance="The lion spirit gave one offended roar. Dust leapt from the paving stones, sandals skidded, and three solemn priests had to chase their own robes.",
        severity=2,
        sensitive_to={"clang"},
        tags={"lion", "statue", "myth"},
    ),
    "moon_fish": Target(
        id="moon_fish",
        label="the moon fish",
        the="the moon fish",
        rest_place="the sacred basin under the shrine eaves",
        nuisance="Silver tails slapped the water in a shining panic. The basin sprayed everyone nearby, and the nearest merchant blinked at his soggy accounts in disbelief.",
        severity=1,
        sensitive_to={"flutter"},
        tags={"fish", "water", "myth"},
    ),
}

REPAIRS = {
    "apology_song": Repair(
        id="apology_song",
        sense=3,
        power=3,
        text="began the old apology song and bowed until every note lay soft in the air",
        fail="began the old apology song, but the noise already flying about the square was too rude to listen",
        qa_text="sang the old apology song and bowed until the sacred mood calmed",
        tags={"song", "apology"},
    ),
    "fig_offering": Repair(
        id="fig_offering",
        sense=3,
        power=2,
        text="set out a dish of cut figs and honey and called for patience instead of praise",
        fail="set out figs and honey, but the startled spirit was too busy blustering to notice the treat",
        qa_text="offered figs and honey to calm the sacred being",
        tags={"offering", "figs"},
    ),
    "ribbon_bow": Repair(
        id="ribbon_bow",
        sense=2,
        power=1,
        text="tied a blue ribbon to the shrine rail and made the children bow three quiet times",
        fail="tied a blue ribbon and bowed, but the gusts only tugged the ribbon harder and laughed at manners",
        qa_text="used a blue ribbon and three quiet bows to ask for calm",
        tags={"ribbon", "apology"},
    ),
    "shout_back": Repair(
        id="shout_back",
        sense=1,
        power=1,
        text="shouted at the wind until it ran out of breath",
        fail="shouted back at the spirit, which only encouraged it",
        qa_text="shouted back at the spirit",
        tags={"noise"},
    ),
}

GIRL_NAMES = ["Nia", "Tala", "Mira", "Iris", "Leda", "Pia", "Dora", "Rhea", "Una", "Cleo"]
BOY_NAMES = ["Ivo", "Tarin", "Leo", "Milo", "Damon", "Orin", "Nico", "Cass", "Theo", "Pax"]
TRAITS = ["careful", "wise", "steady", "thoughtful", "curious", "clever"]
PETS = ["the goat", "the little dog", "the white hen", "the cat"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_repairs():
        return combos
    for festival_id in FESTIVALS:
        for product_id, product in PRODUCTS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(product, target):
                    combos.append((festival_id, product_id, target_id))
    return combos


@dataclass
class StoryParams:
    festival: str
    product: str
    target: str
    repair: str
    boaster: str
    boaster_gender: str
    cautioner: str
    cautioner_gender: str
    elder: str
    trait: str
    delay: int = 0
    boaster_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    pet: str = ""
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
    "whistle": [
        (
            "What is a whistle?",
            "A whistle is a small thing you blow to make a loud sound. Loud sounds can startle people and animals very quickly.",
        )
    ],
    "clapper": [
        (
            "What is a clapper?",
            "A clapper is something you strike to make a ringing sound. Metal sounds can travel far and feel very sudden.",
        )
    ],
    "fan": [
        (
            "What does a hand fan do?",
            "A hand fan moves air when you wave it. It can make a soft breeze, or a silly flutter if you wave it too hard.",
        )
    ],
    "wind": [
        (
            "What is a gust of wind?",
            "A gust is a quick, strong burst of moving air. It can tug hats, ruffle clothes, and push light things around.",
        )
    ],
    "geese": [
        (
            "Why are geese noisy when startled?",
            "Geese honk and flap when something surprises them. Their wings and voices make a lot of commotion in a hurry.",
        )
    ],
    "dragon": [
        (
            "What is a dragon in a myth?",
            "A dragon in a myth is a magical creature with great power. Some are fierce, and some are merely grumpy when woken from a nap.",
        )
    ],
    "statue": [
        (
            "What is a shrine statue for?",
            "A shrine statue helps people remember a spirit, a god, or a holy story. People treat it with respect and quiet manners.",
        )
    ],
    "water": [
        (
            "Why does splashing water make a mess?",
            "Water can soak clothes, papers, and shoes. That is why people try not to startle creatures near a basin or fountain.",
        )
    ],
    "song": [
        (
            "Why can a calm song help in a story?",
            "A calm song can slow people down and make everyone gentler. In stories, music often changes a mood better than shouting does.",
        )
    ],
    "offering": [
        (
            "What is an offering?",
            "An offering is a gift given with respect. In myths, people often bring food, flowers, or light to ask politely for help.",
        )
    ],
    "ribbon": [
        (
            "Why use a ribbon in a festival?",
            "A ribbon can mark a promise, a prayer, or a celebration. It is light, bright, and easy for the wind to toy with.",
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you are sorry and try to make things right. A real apology is quiet, honest, and followed by better choices.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "whistle",
    "clapper",
    "fan",
    "wind",
    "geese",
    "dragon",
    "statue",
    "water",
    "song",
    "offering",
    "ribbon",
    "apology",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    boaster, cautioner = f["boaster"], f["cautioner"]
    product, target, festival = f["product_cfg"], f["target_cfg"], f["festival"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a funny little myth for ages 3 to 5 in which a child is tempted by a shiny product at {festival.place} but learns to heed a wiser warning before trouble starts.',
            f"Tell a mythic market story where {boaster.id} makes a bid for glory with {product.label}, then listens to {cautioner.id} and chooses a quieter way to ask for wonder.",
            f'Write a warm, humorous tale that includes the words "product", "heed", and "bid", and ends with a child returning a noisy gadget instead of using it by a sacred place.',
        ]
    if outcome == "blustered":
        return [
            f'Write a humorous myth where a child ignores a warning to heed an old rule, uses {product.label}, wakes {target.the}, and turns a festival into a windy mess before learning a lesson.',
            f"Tell a cautionary but child-safe story where {boaster.id}'s bid for praise goes wrong at {festival.place}, and a sacred being causes comic chaos.",
            f'Write a mythic story with jokes, gusts, and a clear lesson: a noisy product is not the right way to win glory.',
        ]
    return [
        f'Write a funny myth for young children where a child makes a bold bid for attention with {product.label} at {festival.place}, wakes {target.the}, and a wise elder calms everything.',
        f"Tell a child-friendly myth where {boaster.id} forgets to heed {cautioner.id}, but the trouble is soothed with respect instead of anger.",
        f'Write a playful story that includes the words "product", "heed", and "bid", and ends with a calmer, proper blessing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    boaster, cautioner, elder = f["boaster"], f["cautioner"], f["elder"]
    product, target, repair, festival = f["product_cfg"], f["target_cfg"], f["repair"], f["festival"]
    pair = pair_noun(boaster, cautioner, f.get("relation", "friends"))
    ew = elder.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {boaster.id} and {cautioner.id}, at {festival.place}. It also includes {ew}, who knows the old rule for the shrine.",
        ),
        (
            f"What did {boaster.id} want to do?",
            f"{boaster.id} wanted to make a grand bid for glory by using {product.label} near {target.the}. {boaster.pronoun().capitalize()} hoped a wonder would happen in front of everyone.",
        ),
        (
            f"What warning did {cautioner.id} give?",
            f"{cautioner.id} told {boaster.id} to heed the old rule and not use {product.label} by {target.the}. The warning mattered because the sacred creature resting there could wake in a troublesome mood.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend(
            [
                (
                    f"Why did {boaster.id} change {boaster.pronoun('possessive')} mind?",
                    f"{boaster.id} saw that {cautioner.id} was serious and steady, and that made the bold idea feel foolish instead of grand. Because {cautioner.id} was the older sibling, the warning carried extra weight.",
                ),
                (
                    "How did the story end?",
                    f"It ended peacefully. The children returned the noisy product and learned a proper, quiet way to ask for a blessing instead.",
                ),
            ]
        )
    elif f["outcome"] == "soothed":
        qa.extend(
            [
                (
                    f"What happened when {boaster.id} used {product.label}?",
                    f"{target.The} woke at once and caused comic trouble in the square. Hats flew, people stumbled, and the festival became noisy because the sacred being had been startled.",
                ),
                (
                    f"How did {ew} fix the trouble?",
                    f"{ew.capitalize()} {repair.qa_text}. That respectful repair was strong enough to calm the sacred mood before the chaos grew larger.",
                ),
                (
                    f"What did {boaster.id} learn?",
                    f"{boaster.id} learned to heed wise warnings instead of making a loud bid for praise. The ending shows {boaster.pronoun('object')} singing quietly beside {cautioner.id}, not showing off in front of {cautioner.pronoun('object')}.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Could {ew} calm things right away?",
                    f"No. {ew.capitalize()} tried, but the sacred temper was already too stirred up to settle at once. The whole fair had to stop while everyone waited for the bluster to pass.",
                ),
                (
                    "Was anyone hurt?",
                    f"No one was hurt, but the festival became a great comic mess. That is why the lesson feels serious even though the story stays gentle.",
                ),
                (
                    f"What did {boaster.id} learn in the end?",
                    f"{boaster.id} learned that a noisy product and a foolish bid for glory can make much more work than wonder. After that day, {boaster.pronoun()} tried to listen before acting.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    product = f["product_cfg"]
    target = f["target_cfg"]
    repair = f["repair"]
    outcome = f["outcome"]
    tags: set[str] = set()
    tags |= set(product.tags)
    tags |= set(target.tags)
    if outcome != "averted":
        tags |= set(repair.tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.sensitive_to:
            bits.append(f"sensitive_to={sorted(e.sensitive_to)}")
        if e.sacred:
            bits.append("sacred=True")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        festival="windfair",
        product="thunder_whistle",
        target="cloud_geese",
        repair="apology_song",
        boaster="Ivo",
        boaster_gender="boy",
        cautioner="Nia",
        cautioner_gender="girl",
        elder="priestess",
        trait="careful",
        delay=0,
        boaster_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=6,
        pet="the goat",
    ),
    StoryParams(
        festival="sunsteps",
        product="feather_fan",
        target="nap_dragon",
        repair="fig_offering",
        boaster="Mira",
        boaster_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        elder="grandmother",
        trait="thoughtful",
        delay=0,
        boaster_age=6,
        cautioner_age=5,
        relation="friends",
        trust=3,
        pet="the cat",
    ),
    StoryParams(
        festival="rivermoon",
        product="bronze_clapper",
        target="stone_lion",
        repair="ribbon_bow",
        boaster="Nico",
        boaster_gender="boy",
        cautioner="Tala",
        cautioner_gender="girl",
        elder="priest",
        trait="wise",
        delay=1,
        boaster_age=7,
        cautioner_age=4,
        relation="siblings",
        trust=2,
        pet="the white hen",
    ),
    StoryParams(
        festival="windfair",
        product="feather_fan",
        target="moon_fish",
        repair="fig_offering",
        boaster="Pia",
        boaster_gender="girl",
        cautioner="Rhea",
        cautioner_gender="girl",
        elder="aunt",
        trait="careful",
        delay=0,
        boaster_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
        pet="the little dog",
    ),
    StoryParams(
        festival="sunsteps",
        product="thunder_whistle",
        target="cloud_geese",
        repair="apology_song",
        boaster="Cass",
        boaster_gender="boy",
        cautioner="Una",
        cautioner_gender="girl",
        elder="grandfather",
        trait="steady",
        delay=2,
        boaster_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=1,
        pet="the goat",
    ),
]


def explain_rejection(product: Product, target: Target) -> str:
    if product.sound_tag not in target.sensitive_to:
        return (
            f"(No story: {product.label} makes a {product.sound_tag} kind of fuss, but {target.the} does not care about that sort of disturbance. "
            f"Pick a target the product could honestly startle.)"
        )
    return "(No story: this combination does not create a plausible sacred disturbance.)"


def explain_repair(rid: str) -> str:
    repair = REPAIRS[rid]
    better = " / ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try a calmer, wiser repair such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.boaster_age, params.cautioner_age, params.trait):
        return "averted"
    return "soothed" if is_soothed(REPAIRS[params.repair], TARGETS[params.target], params.delay) else "blustered"


ASP_RULES = r"""
hazard(P, T) :- product(P), target(T), sound_of(P, S), sensitive_to(T, S), noise(P, N), N >= 1.
sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
valid(F, P, T) :- festival(F), hazard(P, T).

cautious_now(T) :- trait(T), is_careful(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), boaster_age(BA), cautioner_age(CA), CA > BA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), boldness_init(BI), A > BI.

severity(V + D) :- chosen_target(T), base_severity(T, V), delay(D).
repair_power(P) :- chosen_repair(R), power(R, P).
soothed :- repair_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(soothed) :- not averted, soothed.
outcome(blustered) :- not averted, not soothed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fid in FESTIVALS:
        lines.append(asp.fact("festival", fid))
    for pid, product in PRODUCTS.items():
        lines.append(asp.fact("product", pid))
        lines.append(asp.fact("sound_of", pid, product.sound_tag))
        lines.append(asp.fact("noise", pid, product.noise))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("base_severity", tid, target.severity))
        for sound in sorted(target.sensitive_to):
            lines.append(asp.fact("sensitive_to", tid, sound))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("power", rid, repair.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_repair", params.repair),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("boaster_age", params.boaster_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_repairs()}
    if c_sens == p_sens:
        print(f"OK: sensible repairs match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    parser = build_parser()
    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke-test ordinary generation and serialization.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        if "product" not in sample.story.lower() and "heed" not in sample.story.lower() and "bid" not in sample.story.lower():
            # Not fatal to contain all three in every exact casing, but the seed words should appear.
            raise StoryError("smoke test story did not include the seed words")
        sample.to_dict()
        buf = io.StringIO()
        saved = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = saved
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a funny little myth about a shiny market product, a warning to heed, and a bid for glory."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--product", choices=PRODUCTS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--elder", choices=["priestess", "priest", "grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument(
        "--delay",
        type=int,
        choices=[0, 1, 2],
        help="how much time passes before the elder responds; more delay makes a blustery ending more likely",
    )
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.product and args.target:
        product = PRODUCTS[args.product]
        target = TARGETS[args.target]
        if not hazard_at_risk(product, target):
            raise StoryError(explain_rejection(product, target))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        c
        for c in valid_combos()
        if (args.festival is None or c[0] == args.festival)
        and (args.product is None or c[1] == args.product)
        and (args.target is None or c[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival_id, product_id, target_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    boaster, boaster_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=boaster)
    elder = args.elder or rng.choice(["priestess", "priest", "grandmother", "grandfather", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    boaster_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    pet = rng.choice(PETS + ["", ""])

    return StoryParams(
        festival=festival_id,
        product=product_id,
        target=target_id,
        repair=repair_id,
        boaster=boaster,
        boaster_gender=boaster_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        elder=elder,
        trait=trait,
        delay=delay,
        boaster_age=boaster_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.festival not in FESTIVALS:
        raise StoryError(f"(Unknown festival: {params.festival})")
    if params.product not in PRODUCTS:
        raise StoryError(f"(Unknown product: {params.product})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if REPAIRS[params.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))
    if not hazard_at_risk(PRODUCTS[params.product], TARGETS[params.target]):
        raise StoryError(explain_rejection(PRODUCTS[params.product], TARGETS[params.target]))

    world = tell(
        FESTIVALS[params.festival],
        PRODUCTS[params.product],
        TARGETS[params.target],
        REPAIRS[params.repair],
        boaster_name=params.boaster,
        boaster_gender=params.boaster_gender,
        cautioner_name=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        elder_type=params.elder,
        trait=params.trait,
        delay=params.delay,
        boaster_age=params.boaster_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
        pet=params.pet,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (festival, product, target) combos:\n")
        for festival_id, product_id, target_id in combos:
            print(f"  {festival_id:10} {product_id:16} {target_id}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.boaster} & {p.cautioner}: {p.product} near {p.target} ({p.festival}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
