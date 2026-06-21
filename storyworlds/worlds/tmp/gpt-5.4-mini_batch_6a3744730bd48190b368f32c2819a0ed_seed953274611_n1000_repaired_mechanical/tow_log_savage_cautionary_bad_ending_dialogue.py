#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tow_log_savage_cautionary_bad_ending_dialogue.py
================================================================================

A standalone story world for a tiny mythic domain built from the seed words
tow, log, and savage, with a cautionary tone, dialogue, and a bad ending.

Premise
-------
A young river-helper tries to tow a heavy log across a mythic ford while the
wild savage wakes of the wood grow angry. A warning is ignored, the current
wins, and the ending image proves the loss.

This script follows the shared Storyweavers contract:
- typed entities with physical meters and emotional memes
- forward-simulated world state that drives the prose
- three Q&A sets generated from world state, not rendered English
- a Python reasonableness gate plus inline ASP twin
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
RECKLESS_MIN = 4.0


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
        female = {"girl", "woman", "mother", "queen", "nymph"}
        male = {"boy", "man", "father", "king", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    name: str
    scene: str
    water: str
    bank: str
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
class ObjectCfg:
    id: str
    label: str
    weight: int
    floats: bool
    sacred: bool = False
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
class ResponseCfg:
    id: str
    sense: int
    power: int
    text: str
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


def _r_current(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["dragged"] < THRESHOLD:
            continue
        sig = ("current", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("river").meters["anger"] += 1
        for k in ("hero", "witness"):
            if k in world.entities:
                world.get(k).memes["fear"] += 1
        out.append("__current__")
    return out


def _r_wreck(world: World) -> list[str]:
    out: list[str] = []
    log = world.entities.get("log")
    if not log or log.meters["sunk"] < THRESHOLD:
        return out
    sig = ("wreck", "log")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("bridge").meters["broken"] += 1
    out.append("The old crossing shuddered and broke.")
    return out


CAUSAL_RULES = [Rule("current", _r_current), Rule("wreck", _r_wreck)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def safe_responses() -> list[ResponseCfg]:
    return [r for r in RESPONSES.values() if r.sense >= 3]


def hazard_ok(towable: ObjectCfg) -> bool:
    return towable.floats and towable.weight >= 2


def response_contained(response: ResponseCfg, towable: ObjectCfg, delay: int) -> bool:
    return response.power >= towable.weight + delay


def predict_fall(world: World, towable_id: str) -> dict:
    sim = world.copy()
    _drag_log(sim, sim.get(towable_id), narrate=False)
    return {
        "sunk": sim.get(towable_id).meters["sunk"] >= THRESHOLD,
        "anger": sim.get("river").meters["anger"],
    }


def _drag_log(world: World, towable: Entity, narrate: bool = True) -> None:
    towable.meters["dragged"] += 1
    towable.meters["wetted"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, witness: Entity, setting: Setting, log_cfg: ObjectCfg) -> None:
    world.say(
        f"At {setting.name}, beneath a sky old as thunder, {hero.id} and {witness.id} "
        f"stood by {setting.water}. {setting.scene}"
    )
    world.say(
        f'They looked upon the {log_cfg.label} and whispered, "If we can tow it '
        f'home, we can raise it into a roof against the storm."'
    )


def warn(world: World, witness: Entity, hero: Entity, log_cfg: ObjectCfg, setting: Setting) -> None:
    witness.memes["worry"] += 1
    world.say(
        f'"Do not tow the {log_cfg.label} over {setting.bank}," {witness.id} said. '
        f'"The river is savage tonight."'
    )
    world.say(
        f'"It is only water," {hero.id} said. "And the log is only wood."'
    )


def defy(world: World, hero: Entity, log_cfg: ObjectCfg) -> None:
    hero.memes["reckless"] += 1
    world.say(
        f'"I have tied the rope," {hero.id} said. "Hold fast, and help me tow it '
        f'once more."'
    )
    world.say(
        f'But {hero.id} pulled with all {hero.pronoun("possessive")} stubborn breath.'
    )


def struggle(world: World, hero: Entity, witness: Entity, log_cfg: ObjectCfg, delay: int) -> None:
    world.say(
        f"The {log_cfg.label} lurched, heavy as a sleeping giant, while the current "
        f"snapped at the rope."
    )
    if delay > 0:
        world.say(
            f"By the time the children found their footing, the savage water had already "
            f"found a way under the bark."
        )
    _drag_log(world, world.get("log"))
    world.say(
        f'"It is moving wrong!" {witness.id} cried. "The river is dragging it!"'
    )
    world.say(f'"Then pull harder!" {hero.id} shouted, though fear had begun to rise.')


def alarm(world: World, witness: Entity, hero: Entity) -> None:
    world.say(
        f'"Stop!" {witness.id} shouted. "The current is too strong, and the log is "
        f"turning sideways!"'
    )
    world.say(f'"No, no," {hero.id} answered, and kept hold of the rope.')


def collapse(world: World, hero: Entity, witness: Entity, log_cfg: ObjectCfg) -> None:
    world.say(
        f"The rope snapped with a bitter crack. The {log_cfg.label} spun away, and "
        f"{hero.id} lost {hero.pronoun('possessive')} grip."
    )
    world.say(
        f"{witness.id} reached for {hero.id}, but the savage water hurled spray between "
        f"them like broken glass."
    )


def ending(world: World, setting: Setting, hero: Entity, witness: Entity, log_cfg: ObjectCfg) -> None:
    world.say(
        f"At dawn, the bank was empty. The log was gone, the rope was gone, and the "
        f"little tow they had trusted had become a sad trail of reeds."
    )
    world.say(
        f"{hero.id} and {witness.id} stood with wet sleeves and silent faces, and the "
        f"river went on speaking to itself below them."
    )


def tell(setting: Setting, log_cfg: ObjectCfg, response: ResponseCfg, delay: int,
         hero_name: str = "Ari", witness_name: str = "Nia",
         hero_type: str = "boy", witness_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    witness = world.add(Entity(id=witness_name, kind="character", type=witness_type, role="witness"))
    river = world.add(Entity(id="river", type="river", label="the river"))
    bridge = world.add(Entity(id="bridge", type="bridge", label="the crossing"))

    hero.memes["bold"] = 5
    witness.memes["care"] = 4
    world.facts["delay"] = delay

    introduce(world, hero, witness, setting, log_cfg)
    world.para()
    warn(world, witness, hero, log_cfg, setting)
    defy(world, hero, log_cfg)
    struggle(world, hero, witness, log_cfg, delay)
    alarm(world, witness, hero)

    contained = response_contained(response, log_cfg, delay)
    world.facts["contained"] = contained

    world.para()
    if contained:
        world.say(
            f"{response.text.replace('{log}', log_cfg.label).capitalize()}."
        )
        world.say(
            f"The river raged, but the children escaped with their skins and their names."
        )
        world.say(
            f"Even so, the old crossing cracked and groaned, and the lesson came hard."
        )
    else:
        world.say(
            f"{response.fail.replace('{log}', log_cfg.label).capitalize()}."
        )
        collapse(world, hero, witness, log_cfg)
        ending(world, setting, hero, witness, log_cfg)

    world.facts.update(
        hero=hero, witness=witness, river=river, bridge=bridge,
        setting=setting, log_cfg=log_cfg, response=response,
        outcome="contained" if contained else "bad",
        sunk=not contained,
    )
    return world


SETTINGS = {
    "ford": Setting(
        id="ford",
        name="the ford",
        scene="The reeds bowed low, and the moon made a silver road on the water.",
        water="the moonlit ford",
        bank="the muddy bank",
    ),
    "wharf": Setting(
        id="wharf",
        name="the old wharf",
        scene="Creaking posts leaned over black water like tired giants.",
        water="the black river",
        bank="the split boards",
    ),
    "valley": Setting(
        id="valley",
        name="the valley crossing",
        scene="Hills watched in silence, and the stream ran narrow but fierce.",
        water="the narrow stream",
        bank="the rocky ledge",
    ),
}

OBJECTS = {
    "oak_log": ObjectCfg(id="oak_log", label="oak log", weight=5, floats=True, tags={"log", "wood"}),
    "pine_log": ObjectCfg(id="pine_log", label="pine log", weight=4, floats=True, tags={"log", "wood"}),
    "sacred_log": ObjectCfg(id="sacred_log", label="sacred log", weight=6, floats=True, sacred=True, tags={"log", "sacred"}),
}

RESPONSES = {
    "pull_back": ResponseCfg(
        id="pull_back",
        sense=4,
        power=5,
        text="they braced their feet and pulled the rope back before the log could vanish",
        fail="they pulled, but the rope only sang and slipped through their hands",
        tags={"rope", "warning"},
    ),
    "cut_rope": ResponseCfg(
        id="cut_rope",
        sense=3,
        power=4,
        text="they cut the rope and let the log go before the current dragged them under",
        fail="they cut late, and the log was already spinning away",
        tags={"rope", "warning"},
    ),
    "shout_for_help": ResponseCfg(
        id="shout_for_help",
        sense=5,
        power=6,
        text="they shouted for the river-keepers, and strong arms came running from the dark",
        fail="their cries were too small, and the river swallowed the sound",
        tags={"help", "warning"},
    ),
    "keep_towing": ResponseCfg(
        id="keep_towing",
        sense=1,
        power=1,
        text="they kept towing until the old log lay where they wanted it",
        fail="they kept towing, and the savage water answered by taking the log and the rope",
        tags={"reckless"},
    ),
}

GIRL_NAMES = ["Nia", "Mira", "Eda", "Luna", "Rhea", "Tala"]
BOY_NAMES = ["Ari", "Bren", "Cai", "Orin", "Joss", "Pax"]


@dataclass
class StoryParams:
    setting: str
    log: str
    response: str
    delay: int
    hero: str
    hero_type: str
    witness: str
    witness_type: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for log_id in setting.__dict__.get("allowed", []):
            pass
    for sid in SETTINGS:
        for log_id in OBJECTS:
            if hazard_ok(OBJECTS[log_id]):
                combos.append((sid, log_id))
    return combos


def explain_rejection(log_cfg: ObjectCfg) -> str:
    if not log_cfg.floats:
        return f"(No story: {log_cfg.label} will not float, so there is no tow and no river lesson.)"
    return f"(No story: the tale needs a floating log to tow.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    allowed = ", ".join(sorted(x.id for x in safe_responses()))
    return f"(Refusing response '{rid}': sense={r.sense} is too low for a cautionary myth. Try: {allowed}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: tow, log, savage, caution, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--log", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--witness")
    ap.add_argument("--witness-type", choices=["girl", "boy"])
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
    if args.response and RESPONSES[args.response].sense < 3:
        raise StoryError(explain_response(args.response))
    setting = args.setting or rng.choice(list(SETTINGS))
    log_id = args.log or rng.choice(list(OBJECTS))
    log_cfg = OBJECTS[log_id]
    if not hazard_ok(log_cfg):
        raise StoryError(explain_rejection(log_cfg))
    response = args.response or rng.choice([r.id for r in safe_responses()])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    witness_type = args.witness_type or ("girl" if hero_type == "boy" else "boy")
    hero = args.hero or (rng.choice(BOY_NAMES) if hero_type == "boy" else rng.choice(GIRL_NAMES))
    witness = args.witness or (rng.choice(GIRL_NAMES) if witness_type == "girl" else rng.choice(BOY_NAMES))
    if witness == hero:
        witness = witness + "a"
    return StoryParams(
        setting=setting, log=log_id, response=response, delay=delay,
        hero=hero, hero_type=hero_type, witness=witness, witness_type=witness_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.log not in OBJECTS or params.response not in RESPONSES:
        raise StoryError("invalid params")
    world = tell(SETTINGS[params.setting], OBJECTS[params.log], RESPONSES[params.response], params.delay,
                 params.hero, params.witness, params.hero_type, params.witness_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a cautionary myth about a child who tries to tow a log across a savage river and is warned not to.",
        f"Tell a mythic tale that uses the words tow, log, and savage, and ends badly when the warning is ignored in {f['setting'].name}.",
        "Write a dialogue-driven story where a warning is spoken, refused, and the river wins.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, witness = f["hero"], f["witness"]
    log_cfg, setting, response = f["log_cfg"], f["setting"], f["response"]
    qa = [
        ("Who tried to tow the log?",
         f"{hero.id} tried to tow the {log_cfg.label}, even after being warned." ),
        ("What did the witness say about the river?",
         f"{witness.id} said the river was savage tonight, which was a warning to stop and think."),
        ("How did the story end?",
         "It ended badly. The rope snapped, the log was lost, and the children were left with a hard lesson."),
        ("Why was the warning wise?",
         f"The {setting.name} was dangerous, and the river's pull was stronger than the children expected."),
    ]
    if f["outcome"] == "bad":
        qa.append((
            "What happened when the children kept towing?",
            f"They kept towing, but the current dragged the log away and broke the crossing's peace."
        ))
    else:
        qa.append((
            "What happened when help came?",
            f"Help arrived in time, but the crossing still suffered, and the lesson stayed stern."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["log_cfg"].tags) | {"warning", "rope"}
    if world.facts["outcome"] == "bad":
        tags.add("river")
    if "log" in tags:
        out.append(("What is a log?",
                     "A log is a long piece of cut wood from a tree. It is heavy and can float in water." ))
    if "river" in tags:
        out.append(("What is a river?",
                     "A river is moving water that flows along a path. Strong rivers can pull and push hard." ))
    if "rope" in tags:
        out.append(("What is rope for?",
                     "Rope is used to tie, pull, and tow things. It must be held firmly when something is heavy." ))
    if "warning" in tags:
        out.append(("Why should you listen to a warning?",
                     "A warning tells you about danger before it hurts you. Listening can keep a story from becoming a tragedy." ))
    out.append(("What does savage mean in a myth?",
                 "In a myth, savage means wild, fierce, and hard to control. It often describes a force that does not listen to people."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_response(R) :- response(R), sense(R,S), sense_min(M), S >= M.
bad_ending :- chosen_response(R), response(R), sense(R,S), sense_min(M), S < M.
dangerous :- has_log(L), has_setting(S).
outcome(bad) :- dangerous, chosen_response(R), response(R), safe_response(R), not rescued.
outcome(bad) :- dangerous.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("log", oid))
        if obj.floats:
            lines.append(asp.fact("floats", oid))
        lines.append(asp.fact("weight", oid, obj.weight))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show safe_response/1.\n#show outcome/1."))
    safe = {x[0] for x in asp.atoms(model, "safe_response")}
    if safe != {r.id for r in safe_responses()}:
        print("MISMATCH in safe responses")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def build_parser_extra() -> None:
    return None


def asp_valids() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show safe_response/1."))
    return sorted(set(asp.atoms(model, "safe_response")))


def valid_story_configs() -> list[tuple[str, str]]:
    return valid_combos()


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for oid, obj in OBJECTS.items():
            if hazard_ok(obj):
                combos.append((sid, oid))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show safe_response/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show safe_response/1."))
        vals = [x[0] for x in asp.atoms(model, "safe_response")]
        print("safe responses:", ", ".join(sorted(vals)))
        print("valid combos:")
        for sid, oid in valid_combos():
            print(f"  {sid:8} {oid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="ford", log="oak_log", response="keep_towing", delay=2, hero="Ari", hero_type="boy", witness="Nia", witness_type="girl"),
            StoryParams(setting="wharf", log="pine_log", response="pull_back", delay=1, hero="Mira", hero_type="girl", witness="Pax", witness_type="boy"),
            StoryParams(setting="valley", log="sacred_log", response="shout_for_help", delay=2, hero="Orin", hero_type="boy", witness="Tala", witness_type="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
