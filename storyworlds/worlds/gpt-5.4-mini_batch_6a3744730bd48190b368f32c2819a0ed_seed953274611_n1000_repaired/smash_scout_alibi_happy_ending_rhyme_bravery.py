#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smash_scout_alibi_happy_ending_rhyme_bravery.py
================================================================================

A small TinyStories-style storyworld with a pirate-tale feel.

Premise:
- Two children play as daring little pirates.
- One child wants to smash a prop to find a "secret" clue.
- The other scouts ahead, notices the risk, and offers a better alibi-like plan:
  they can explain what happened honestly and use a safe substitute.
- Bravery matters: the brave choice is not smashing first; it is telling the truth,
  calling for help, and trying a safe fix.
- The ending is always happy, with a short rhyming flourish.

This script is self-contained and follows the Storyweavers world contract.
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
    scene: str
    place: str
    dark_spot: str
    treasure_word: str
    ending_image: str
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
    phrase: str
    kind: str
    risky: bool = False
    flammable: bool = False
    makes_noise: bool = False
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
class ResponseCfg:
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


@dataclass
class StoryParams:
    setting: str
    scout: str
    scout_gender: str
    brave: str
    brave_gender: str
    adult: str
    object_id: str
    response: str
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


def _r_smash(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["broken"] < THRESHOLD:
            continue
        sig = ("smash", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["mess"] += 1
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["startle"] += 1
        out.append("__smash__")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("alibi_told") and not world.facts.get("truth_told"):
        sig = ("truth",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__truth__")
    return out


CAUSAL_RULES = [Rule("smash", _r_smash), Rule("truth", _r_truth)]


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


def hazard_at_risk(obj: ObjectCfg) -> bool:
    return obj.risky or obj.flammable or obj.makes_noise


def sensible_responses() -> list[ResponseCfg]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for oid, obj in OBJECTS.items():
            for rid, resp in RESPONSES.items():
                if hazard_at_risk(obj) and resp.sense >= 2:
                    combos.append((sid, oid, rid))
    return combos


def resolve_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def predict_smash(world: World, obj_id: str, delay: int) -> dict:
    sim = world.copy()
    sim.get(obj_id).meters["broken"] += 1
    if delay > 0:
        sim.get("room").meters["mess"] += delay
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("room").meters["mess"],
        "broken": sim.get(obj_id).meters["broken"] >= THRESHOLD,
    }


def _do_smash(world: World, obj: Entity, narrate: bool = True) -> None:
    obj.meters["broken"] += 1
    world.facts["smash_happened"] = True
    propagate(world, narrate=narrate)


def tell(world_cfg: Setting, obj_cfg: ObjectCfg, response: ResponseCfg,
         scout: Entity, brave: Entity, adult: Entity, delay: int) -> World:
    world = World()
    room = world.add(Entity(id="room", type="room", label=world_cfg.place))
    _ = room
    prop = world.add(Entity(id="prop", type="thing", label=obj_cfg.label))
    safe_prop = world.add(Entity(id="safe_prop", type="thing", label="a wooden practice barrel"))
    scout.memes["caution"] += 1
    brave.memes["bravery"] += 1

    world.say(
        f"On a bright deck of make-believe, {scout.id} and {brave.id} turned "
        f"{world_cfg.place} into a pirate ship. {world_cfg.scene}"
    )
    world.say(
        f'{brave.id} pointed at {obj_cfg.phrase}. "{obj_cfg.label.capitalize()}!" '
        f'{brave.id} said. "Maybe we can smash it and find treasure!"'
    )
    world.say(
        f'{scout.id} climbed higher to scout ahead. "Wait," {scout.id} called, '
        f'"we should not smash that."'
    )

    pred = predict_smash(world, prop.id, delay)
    if obj_cfg.risky:
        world.facts["predicted_risk"] = True
    world.facts["predicted_mess"] = pred["mess"]

    if response.sense < 2:
        raise StoryError("This response is too weak for a brave pirate story.")

    world.para()
    if delay <= 0:
        world.say(
            f'"We can be brave and honest," {scout.id} said. "Here is our alibi: '
            f'we were scouting the ship, not wrecking it."'
        )
        world.say(
            f"{adult.label_word.capitalize()} smiled at the honest alibi and handed "
            f"over a safe practice target instead."
        )
        world.say(
            f'{brave.id} nodded. "A smart plan can still be bold," {brave.id} said.'
        )
        world.para()
        world.say(
            f"{response.text.replace('{target}', 'the practice barrel').capitalize()}. "
            f"{scout.id} and {brave.id} took turns with safe taps and loud cheers."
        )
        world.say(
            f"At the end, {world_cfg.ending_image}, and the treasure stayed tucked away, "
            f"safe and sound."
        )
        world.say("Brave hearts won the day; no smash, no crash, hooray.")
        outcome = "happy"
    else:
        _do_smash(world, prop, narrate=False)
        world.say(
            f'{brave.id} took one step too fast. Then there was a loud smash, and '
            f"the pirate game went still."
        )
        world.say(
            f"{adult.label_word.capitalize()} came running, but the honest alibi "
            f"arrived first: {scout.id} pointed to the lookout rope and told the truth."
        )
        world.say(
            f"{response.fail.replace('{target}', obj_cfg.label).capitalize()}. "
            f"Still, everyone stayed safe, and the broken bit was only a prop."
        )
        world.para()
        world.say(
            f"{scout.id} and {brave.id} helped clean up, then chose the safe practice "
            f"barrel. By sunset, {world_cfg.ending_image}, and they laughed "
            f"like little pirates in a rhyme."
        )
        world.say("A brave truth, a safer route, and a happy end astern.")
        outcome = "repaired"

    world.facts.update(
        scout=scout,
        brave=brave,
        adult=adult,
        setting=world_cfg,
        object_cfg=obj_cfg,
        response=response,
        outcome=outcome,
        delay=delay,
        alibi_told=True,
        truth_told=True,
    )
    return world


SETTINGS = {
    "deck": Setting(
        id="deck",
        scene="The crate was their ship, the broom was their mast, and a chalk map led to the gold.",
        place="the deck",
        dark_spot="the cargo corner",
        treasure_word="gold",
        ending_image="the chalk map still showed the way to the gold",
    ),
    "cove": Setting(
        id="cove",
        scene="The bench became a boat, the bucket became a drum, and a ribbon map pointed to the cave.",
        place="the cove",
        dark_spot="the shadowy cove nook",
        treasure_word="pearls",
        ending_image="the ribbon map fluttered in the warm breeze",
    ),
    "harbor": Setting(
        id="harbor",
        scene="The stools were lookout towers, a ladle was a spyglass, and a shell map promised a secret chest.",
        place="the harbor",
        dark_spot="the dock-side crate pile",
        treasure_word="shells",
        ending_image="the shell map lay flat and bright",
    ),
}

OBJECTS = {
    "crate": ObjectCfg(
        id="crate",
        label="crate",
        phrase="the old crate",
        kind="thing",
        risky=True,
        makes_noise=True,
        tags={"smash"},
    ),
    "coconut": ObjectCfg(
        id="coconut",
        label="coconut",
        phrase="the coconut",
        kind="thing",
        risky=True,
        tags={"smash"},
    ),
    "shell_box": ObjectCfg(
        id="shell_box",
        label="shell box",
        phrase="the shell box",
        kind="thing",
        risky=True,
        tags={"smash", "alibi"},
    ),
}

RESPONSES = {
    "shield": ResponseCfg(
        id="shield",
        sense=3,
        power=3,
        text="picked up the safe practice barrel and set it down as a new target",
        fail="could not stop the mess from spreading to the deck",
        qa_text="set out the safe practice barrel",
        tags={"safe", "brave"},
    ),
    "tell_truth": ResponseCfg(
        id="tell_truth",
        sense=3,
        power=3,
        text="told the truth and asked for help instead of hiding the problem",
        fail="wanted to help, but the problem was already too big",
        qa_text="told the truth and asked for help",
        tags={"alibi", "truth"},
    ),
    "stomp": ResponseCfg(
        id="stomp",
        sense=2,
        power=1,
        text="stomped hard and carefully on the loose bits until they settled",
        fail="stomped, but the splinters still skittered away",
        qa_text="stomped the loose bits still",
        tags={"brave"},
    ),
}


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Eli"]
TRAITS = ["brave", "curious", "quick", "bold", "cheery"]


@dataclass
class StoryHint:
    prompt_words: list[str] = field(default_factory=list)
    rhyme_tags: list[str] = field(default_factory=list)
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


HINTS = StoryHint(prompt_words=["smash", "scout", "alibi"], rhyme_tags=["brave", "wave", "cave"])


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-tale story for a small child that includes the words '
        f'"smash", "scout", and "alibi".',
        f"Tell a brave little pirate story where {f['scout'].id} scouts ahead, "
        f"{f['brave'].id} wants to smash a prop, and they choose an honest alibi "
        f"and a safer plan.",
        f'Write a happy ending story with a rhyme or two, where bravery means '
        f"telling the truth and choosing a safe substitute instead of a smash.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scout, brave, adult = f["scout"], f["brave"], f["adult"]
    obj = f["object_cfg"]
    resp = f["response"]
    qa = [
        (
            "Who were the story's little pirates?",
            f"The story was about {scout.id} and {brave.id}. {scout.id} scouted ahead, "
            f"and {brave.id} was the one who wanted to smash the prop.",
        ),
        (
            f"Why did {scout.id} stop the smash plan?",
            f"{scout.id} saw that {obj.label} could make a mess and ruin the game. "
            f"{scout.id} chose bravery by warning everyone and telling the truth.",
        ),
        (
            "What was the alibi in the story?",
            f"The alibi was simple and honest: {scout.id} and {brave.id} were only scouting "
            f"the ship, not wrecking it. That gave {adult.label_word} a true story to hear.",
        ),
    ]
    if f["outcome"] == "happy":
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with a safe practice target, a smiling grown-up, and "
                f"a brave rhyme about choosing the right way. The dangerous smash never happened.",
            )
        )
    else:
        qa.append(
            (
                "How did the story still stay happy?",
                f"The prop broke, but everyone stayed safe and told the truth. Then they cleaned up, "
                f"picked a safer game, and finished with smiles instead of trouble.",
            )
        )
    qa.append(
        (
            f"What did {resp.id} do in the ending?",
            f"{resp.qa_text.capitalize()}, which fit the brave pirate mood because it solved the problem "
            f"without making things worse.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    obj = f["object_cfg"]
    resp = f["response"]
    topics: list[tuple[str, str]] = []
    if "smash" in obj.tags:
        topics.append(("What does smash mean?", "To smash something means to hit it hard so it can break or split apart."))
    if "alibi" in resp.tags:
        topics.append(("What is an alibi?", "An alibi is an explanation of where someone was, so people can understand what really happened."))
    topics.append(("What does a scout do?", "A scout looks ahead, notices danger, and brings back useful information."))
    topics.append(("What does bravery mean?", "Bravery means doing the right thing even when it feels scary."))
    topics.append(("Why is telling the truth brave?", "Telling the truth can be hard, but it helps fix problems and keeps everyone safe."))
    return topics


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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="deck", scout="Lily", scout_gender="girl", brave="Tom", brave_gender="boy", adult="mother", object_id="crate", response="tell_truth", delay=0),
    StoryParams(setting="cove", scout="Mia", scout_gender="girl", brave="Ben", brave_gender="boy", adult="father", object_id="coconut", response="shield", delay=1),
    StoryParams(setting="harbor", scout="Nora", scout_gender="girl", brave="Eli", brave_gender="boy", adult="mother", object_id="shell_box", response="stomp", delay=0),
]


def explain_rejection(obj: ObjectCfg) -> str:
    return f"(No story: the chosen object '{obj.label}' is not a good small hazard for this brave pirate tale.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < 2).)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate storyworld about smash, scout, and alibi.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--scout")
    ap.add_argument("--brave")
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.object_id and not hazard_at_risk(OBJECTS[args.object_id]):
        raise StoryError(explain_rejection(OBJECTS[args.object_id]))
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object_id is None or c[1] == args.object_id)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, object_id, response = rng.choice(sorted(combos))
    scout = args.scout or rng.choice(GIRL_NAMES + BOY_NAMES)
    brave = args.brave or resolve_name(rng, GIRL_NAMES + BOY_NAMES, avoid=scout)
    scout_gender = "girl" if scout in GIRL_NAMES else "boy"
    brave_gender = "girl" if brave in GIRL_NAMES else "boy"
    adult = args.adult or rng.choice(["mother", "father"])
    delay = rng.randint(0, 1)
    return StoryParams(setting=setting, scout=scout, scout_gender=scout_gender,
                        brave=brave, brave_gender=brave_gender, adult=adult,
                        object_id=object_id, response=response, delay=delay)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object_id not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object_id}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    world_cfg = SETTINGS[params.setting]
    obj_cfg = OBJECTS[params.object_id]
    resp_cfg = RESPONSES[params.response]
    scout = Entity(id=params.scout, kind="character", type=params.scout_gender, role="scout")
    brave = Entity(id=params.brave, kind="character", type=params.brave_gender, role="brave")
    adult = Entity(id="Adult", kind="character", type=params.adult, role="adult", label="the grown-up")
    world = tell(world_cfg, obj_cfg, resp_cfg, scout, brave, adult, params.delay)
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
valid(S,O,R) :- setting(S), object(O), response(R), risky(O), sense(R,M), M >= min_sense.
smash_happens(O) :- object(O), risky(O).
happy_end(R) :- response(R), sense(R,M), M >= min_sense.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.risky:
            lines.append(asp.fact("risky", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object_id=None, response=None, scout=None, brave=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for sid, oid, rid in combos:
            print(f"  {sid:8} {oid:10} {rid}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
