#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/voodoo_repetition_pirate_tale.py
=================================================================

A standalone storyworld for a tiny pirate tale with repetition, a little
voodoo trinket, a risky mistake, and a calm repair.

Premise
-------
Two children play pirate ship indoors. One child finds a voodoo doll and tries
the same spooky trick over and over to make the pretend captain "feel" it. The
other child warns that toys are not for hurting, a parent steps in, and the game
shifts toward a safer repeated chant and a treasure-hunt ending.

The world is state-driven:
- physical meters: worry, damage, dust, courage, soot, safety, repetition
- emotional memes: delight, fear, guilt, relief, trust, pride

The story can end in two close variants:
- contained: the parent calmly stops the harm and redirects the game
- averted: the warning is enough and the children never use the doll on anyone

The seed word "voodoo" is always present; the style stays close to pirate tale.
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
BRAVERY_INIT = 5.0

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn"]


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
    voodoo: bool = False
    pirate: bool = False

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
    props: str
    repeated_chant: str
    mood: str
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
class Charm:
    id: str
    label: str
    phrase: str
    repeats: int
    spooky: bool = False
    voodoo: bool = True
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
    phrase: str
    startled: str
    harmed: bool = False
    risky: bool = True
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
class Response:
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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    inst = world.entities.get("instigator")
    tgt = world.entities.get("target")
    if not inst or not tgt:
        return out
    if inst.meters["repetition"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tgt.memes["fear"] += 1
    inst.memes["pride"] += 1
    out.append("__repeat__")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    tgt = world.entities.get("target")
    if not tgt:
        return out
    if tgt.meters["damage"] < THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("ship").meters["worry"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["worry"] += 1
    out.append("__damage__")
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("damage", _r_damage)]


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


def repetition_harm(charm: Charm, target: Target) -> bool:
    return charm.voodoo and target.risky


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    caution_bonus = 3.0 if trait in {"careful", "cautious", "sensible"} else 1.0
    older_bonus = 3.0 if relation == "siblings" and cautioner_age > instigator_age else 0.0
    return older_bonus + caution_bonus > BRAVERY_INIT


def _do_charm(world: World, charm: Charm, target_ent: Entity, narrate: bool = True) -> None:
    target_ent.meters["damage"] += 1
    target_ent.meters["repetition"] += 1
    world.get("instigator").meters["repetition"] += 1
    propagate(world, narrate=narrate)


def predict_harm(world: World, charm: Charm, target_id: str) -> dict:
    sim = world.copy()
    _do_charm(sim, sim.facts["charm_ent"], sim.get(target_id), narrate=False)
    return {
        "damaged": sim.get(target_id).meters["damage"] >= THRESHOLD,
        "worry": sim.get("ship").meters["worry"],
    }


def setup(world: World, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["delight"] += 1
    mate.memes["delight"] += 1
    world.say(
        f"On a windy afternoon, {hero.id} and {mate.id} turned the parlor into "
        f"{setting.place}. {setting.props}"
    )
    world.say(
        f"They played pirate ship again and again, and {setting.repeated_chant}."
    )


def tempt(world: World, hero: Entity, charm: Charm) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'{hero.id} found a little voodoo charm and grinned. '
        f'"Look, look," {hero.id} said. "{charm.phrase}"'
    )
    world.say("The same spooky idea came back twice, then three times, like a drumbeat.")


def warn(world: World, mate: Entity, hero: Entity, target: Target, parent: Entity) -> None:
    mate.memes["caution"] += 1
    world.say(
        f'{mate.id} frowned. "{hero.id}, that is not a toy. '
        f'{parent.label_word.capitalize()} said never to use voodoo to scare anybody, '
        f'and {target.label} could get hurt."'
    )


def defy(world: World, hero: Entity, charm: Charm) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I only mean to try it once," {hero.id} said. '
        f'But once turned into once more, and once more again.'
    )


def stop_it(world: World, hero: Entity, mate: Entity, parent: Entity) -> None:
    hero.memes["fear"] += 1
    mate.memes["relief"] += 1
    world.say(
        f'But {mate.id} held up a hand and called, "{parent.label_word.capitalize()}!"'
    )
    world.say(
        f"{parent.label_word.capitalize()} came at once, put the charm away, and said the same rule twice: "
        f'"No voodoo tricks for hurting. No voodoo tricks for hurting."'
    )


def calm_fix(world: World, parent: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["damage"] = 0.0
    world.get("ship").meters["worry"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(
        f"{parent.label_word.capitalize()} {body}."
    )
    world.say(
        f"The little crack and the worried hush faded, and the ship felt safe again."
    )


def lesson(world: World, parent: Entity, hero: Entity, mate: Entity, charm: Charm) -> None:
    for kid in (hero, mate):
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f'Then {parent.label_word.capitalize()} knelt down. "Repetition can be fun in songs," '
        f'{parent.pronoun()} said softly, "but not in hurtful tricks. {charm.label} is for pretend, '
        f'not for making fear."'
    )
    world.say(f'"We promise," whispered {mate.id} and {hero.id} together.')


def safe_ending(world: World, hero: Entity, mate: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"Then they counted the boards on the pirate ship three times and sang "
        f'{setting.repeated_chant} one more time, only now it was a happy chant.'
    )
    world.say(
        f"{hero.id} wore the voodoo charm as a pretend necklace, and the pirates went on "
        f"to hunt treasure with bright eyes and empty hands."
    )


def tell(setting: Setting, charm: Charm, target: Target, response: Response,
         instigator: str = "Tom", instigator_gender: str = "boy",
         cautioner: str = "Lily", cautioner_gender: str = "girl",
         parent_type: str = "mother", trait: str = "careful",
         relation: str = "siblings", instigator_age: int = 6,
         cautioner_age: int = 7, trust: int = 6, delay: int = 0) -> World:
    world = World(setting)
    hero = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator"))
    mate = world.add(Entity(id=cautioner, kind="character", type=cautioner_gender, role="cautioner"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    ship = world.add(Entity(id="ship", label="the ship"))
    charm_ent = world.add(Entity(id="charm", label=charm.label, voodoo=True))
    tgt = world.add(Entity(id="target", label=target.label))
    hero.meters["bravery"] = BRAVERY_INIT
    mate.memes["trust"] = float(trust)
    world.facts.update(charm_ent=charm_ent)

    setup(world, hero, mate, setting)
    world.para()
    tempt(world, hero, charm)
    warn(world, mate, hero, target, parent)
    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        stop_it(world, hero, mate, parent)
        world.para()
        safe_ending(world, hero, mate, setting)
        outcome = "averted"
    else:
        defy(world, hero, charm)
        world.para()
        _do_charm(world, charm_ent, tgt)
        world.say(f'"{hero.id}! Stop!" {mate.id} cried, because the same little poke had been done again and again.')
        world.para()
        if response.power >= 1 + delay:
            calm_fix(world, parent, response, tgt, target)
            lesson(world, parent, hero, mate, charm)
            world.para()
            safe_ending(world, hero, mate, setting)
            outcome = "contained"
        else:
            world.say(
                f"{parent.label_word.capitalize()} tried to fix it, but the worry had already spread."
            )
            outcome = "burned"
    world.facts.update(
        instigator=hero, cautioner=mate, parent=parent, setting=setting,
        charm=charm, target_cfg=target, target=tgt, response=response,
        outcome=outcome, averted=averted, delayed=delay
    )
    return world


SETTINGS = {
    "pirate_ship": Setting(
        id="pirate_ship",
        place="a pirate ship made of chairs and blankets",
        props="A mop became the mast, a spoon became the spyglass, and a chest of shells sat by the rug.",
        repeated_chant="they shouted, 'Ahoy, ahoy!' again and again",
        mood="swashbuckling",
    ),
    "cabin": Setting(
        id="cabin",
        place="a tiny pirate cabin",
        props="A lantern was only pretend, a map was drawn in circles, and the floorboards creaked like old songs.",
        repeated_chant="they tapped the table and said, 'Yo-ho, yo-ho!' three times",
        mood="cozy",
    ),
}

CHARMS = {
    "voodoo_doll": Charm(
        id="voodoo_doll",
        label="a voodoo doll",
        phrase="It made the same piratey jab-jab motion over and over",
        repeats=3,
        spooky=True,
        tags={"voodoo", "repeat"},
    ),
    "rattle": Charm(
        id="rattle",
        label="a little rattle",
        phrase="It shook, shook, shook like a storm in a jar",
        repeats=3,
        spooky=False,
        tags={"repeat"},
    ),
}

TARGETS = {
    "captain_hat": Target(
        id="captain_hat",
        label="the captain's hat",
        phrase="a tall black captain's hat",
        startled="the feathers fluttered",
        tags={"hat", "pirate"},
    ),
    "parrot": Target(
        id="parrot",
        label="the parrot",
        phrase="a bright green parrot on a perch",
        startled="the parrot squawked and hopped",
        tags={"parrot", "pirate"},
    ),
}

RESPONSES = {
    "gentle_fix": Response(
        id="gentle_fix",
        sense=3,
        power=2,
        text="calmly tucked the voodoo doll into a box and wrapped the string around it until the room felt quiet",
        fail="opened the box and tried to calm things, but the fear kept bouncing around",
        qa_text="calmly tucked the voodoo doll into a box and wrapped the string around it until the room felt quiet",
        tags={"calm", "repair"},
    ),
    "song": Response(
        id="song",
        sense=2,
        power=1,
        text="made a steady pirate song and breathed until the room matched the beat again",
        fail="started a song, but the room was already too upset to match it",
        qa_text="made a steady pirate song and breathed until the room matched the beat again",
        tags={"song", "repair"},
    ),
    "sprinkle": Response(
        id="sprinkle",
        sense=1,
        power=1,
        text="sprinkled water on the rug, which did not help much at all",
        fail="sprinkled water on the rug, which did not help much at all",
        qa_text="sprinkled water on the rug, which did not help much at all",
        tags={"weak"},
    ),
}

TRAITS = ["careful", "cautious", "clever", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, charm in CHARMS.items():
            for tid, target in TARGETS.items():
                if repetition_harm(charm, target):
                    combos.append((sid, cid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    charm: str
    target: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 7
    trust: int = 6
    delay: int = 0
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


def explain_rejection(charm: Charm, target: Target) -> str:
    if not target.risky:
        return f"(No story: {target.label} is not at risk, so the voodoo trick would not matter.)"
    return f"(No story: {charm.label} only makes sense as a risky voodoo repetition near {target.label}.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': sense={r.sense} < 2. Try: {good}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale about voodoo and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    if args.charm and args.target and not repetition_harm(CHARMS[args.charm], TARGETS[args.target]):
        raise StoryError(explain_rejection(CHARMS[args.charm], TARGETS[args.target]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator = rng.choice(GIRL_NAMES + BOY_NAMES)
    cautioner = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != instigator])
    ig = "girl" if instigator in GIRL_NAMES else "boy"
    cg = "girl" if cautioner in GIRL_NAMES else "boy"
    parent = rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting, charm=charm, target=target, response=response,
        instigator=instigator, instigator_gender=ig,
        cautioner=cautioner, cautioner_gender=cg,
        parent=parent, trait=trait,
        relation=rng.choice(["siblings", "friends"]),
        instigator_age=rng.randint(5, 8),
        cautioner_age=rng.randint(5, 9),
        trust=rng.randint(0, 10),
        delay=rng.randint(0, 1),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a small child that includes the word "voodoo" and shows the same spooky trick repeated more than once.',
        f"Tell a story where {f['instigator'].id} finds {f['charm'].label} on a pirate ship and keeps repeating the same motion until a friend warns {f['instigator'].pronoun('object')}.",
        f"Write a gentle pirate story about repetition, a warning, and a safer ending with {f['setting'].repeated_chant}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate, parent = f["instigator"], f["cautioner"], f["parent"]
    charm, target = f["charm"], f["target_cfg"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id}, {mate.id}, and the parent who came to help. The two children were playing pirates when the voodoo trouble began."),
        ("What did {0} find?".format(hero.id), f"{hero.id} found {charm.label}. It made the same little pirate motion again and again, which is what made the moment feel spooky."),
        ("Why did {0} warn {1}?".format(mate.id, hero.id), f"{mate.id} warned {hero.id} because the voodoo trick was being used to bother {target.label}. The warning mattered because the same act was repeated instead of stopped."),
    ]
    if f["outcome"] == "averted":
        qa.append(("How did the story end?", f"It ended safely, because {mate.id} and the parent stopped the trick before anyone got hurt. Then the children switched to a repeated pirate chant instead."))
    elif f["outcome"] == "contained":
        qa.append(("How did the parent fix the problem?", f"The parent {f['response'].qa_text}. That calm choice stopped the damage and let the pirate game continue in a safer way."))
        qa.append(("What changed at the end?", f"The same repeated motion turned into a repeated chant. The voodoo doll stayed put, and the children hunted treasure instead of scaring anyone."))
    else:
        qa.append(("What happened when help came?", f"Help came too late to fully undo the trouble, so the room stayed upset for a while. The children were still safe, but the game had to stop and be remembered as a mistake."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["charm"].tags) | set(f["target_cfg"].tags) | set(f["response"].tags)
    if f["setting"].id:
        tags.add("repeat")
    out = []
    if "voodoo" in tags:
        out.append(("What does voodoo mean in a story like this?", "In a story like this, voodoo means a spooky pretend charm or trick. It is not for hurting people, and grown-ups should stop it if it starts to scare someone."))
    if "repeat" in tags:
        out.append(("What is repetition?", "Repetition means doing the same thing again and again. It can be fun in songs and games, but it can also make a bad choice harder to stop."))
    if "repair" in tags:
        out.append(("What does it mean to calm something down?", "To calm something down means to make it quieter, safer, and less upset. A gentle adult can do that by pausing the game and choosing a safer plan."))
    out.append(("What do pirates look for?", "Pirates often look for treasure and adventure. In stories for children, they usually shout, march, and explore rather than truly fight."))
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
        if e.voodoo:
            bits.append("voodoo=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="pirate_ship", charm="voodoo_doll", target="captain_hat", response="gentle_fix",
                instigator="Tom", instigator_gender="boy", cautioner="Lily", cautioner_gender="girl",
                parent="mother", trait="careful", relation="siblings", instigator_age=6, cautioner_age=8, trust=7),
    StoryParams(setting="cabin", charm="voodoo_doll", target="parrot", response="song",
                instigator="Mia", instigator_gender="girl", cautioner="Ben", cautioner_gender="boy",
                parent="father", trait="cautious", relation="friends", instigator_age=5, cautioner_age=6, trust=4),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.charm not in CHARMS or params.target not in TARGETS or params.response not in RESPONSES:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(
        SETTINGS[params.setting], CHARMS[params.charm], TARGETS[params.target], RESPONSES[params.response],
        params.instigator, params.instigator_gender, params.cautioner, params.cautioner_gender,
        params.parent, params.trait, params.relation, params.instigator_age, params.cautioner_age,
        params.trust, params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
repeat_trouble(H,T) :- voodoo(H), risky(T).
contains(R) :- response(R), sense(R,S), S >= 2.
outcome(averted) :- oldersib, careful_now, bravery(B), B < 6.
outcome(contained) :- not outcome(averted), contains(_).
outcome(burned) :- not outcome(averted), not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.voodoo:
            lines.append(asp.fact("voodoo", cid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.risky:
            lines.append(asp.fact("risky", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("bravery", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show repeat_trouble/2."))
    return sorted(set(asp.atoms(model, "repeat_trouble")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show contains/1."))
    return sorted(r for (r,) in asp.atoms(model, "contains"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_response", params.response)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    sample = generate(CURATED[0])
    if not sample.story:
        rc = 1
        print("MISMATCH: generate produced empty story.")
    else:
        print("OK: generate smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with voodoo repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
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
        print(asp_program("", "#show repeat_trouble/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible repeat-trouble combos:")
        for item in asp_valid_combos():
            print(" ", item)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
