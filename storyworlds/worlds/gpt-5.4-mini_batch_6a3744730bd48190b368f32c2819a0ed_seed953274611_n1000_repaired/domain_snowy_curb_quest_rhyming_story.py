#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/domain_snowy_curb_quest_rhyming_story.py
=========================================================================

A standalone storyworld for a tiny rhyming quest set on a snowy curb.

Premise:
A child and a helper set off on a small quest at a snowy curb to find a lost
item before the cold makes the game sad. The world advances through physical
state (meters) and emotional state (memes), and the ending proves what changed.

This world keeps the prose child-facing and lightly rhymed, with a clear quest
shape: call, search, snag, solve, and a warm finish.
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
JOY_MIN = 1.0


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
    carries: str = ""

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
class Place:
    id: str
    label: str
    snow: str
    curb: str
    quest_word: str = "quest"
    domain_word: str = "domain"
    cold: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class QuestItem:
    id: str
    label: str
    phrase: str
    lost_in: str
    can_fit: bool = True
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
class HelperKit:
    id: str
    label: str
    phrase: str
    warm: str
    use: str
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
class QuestPlan:
    id: str
    goal: str
    rhyme: str
    finish: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_cold(world: World) -> list[str]:
    out = []
    if world.place.cold and world.place.meters["wind"] >= THRESHOLD:
        sig = ("cold",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.place.meters["cold"] += 1
            for e in list(world.entities.values()):
                if e.kind == "character":
                    e.memes["shiver"] += 1
            out.append("__cold__")
    return out


def _r_find(world: World) -> list[str]:
    out = []
    scout = world.entities.get("child")
    item = world.entities.get("item")
    if not scout or not item:
        return out
    if scout.meters["search"] >= THRESHOLD and item.meters["found"] < THRESHOLD:
        sig = ("find",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        item.meters["found"] += 1
        out.append("__found__")
    return out


def _r_warm(world: World) -> list[str]:
    out = []
    if world.entities["child"].memes["joy"] >= JOY_MIN and world.entities["helper"].memes["joy"] >= JOY_MIN:
        sig = ("warm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.place.meters["warmth"] += 1
            out.append("__warm__")
    return out


CAUSAL_RULES = [Rule("cold", _r_cold), Rule("find", _r_find), Rule("warm", _r_warm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_at_risk(item: QuestItem, place: Place) -> bool:
    return item.lost_in == place.id and place.cold


def sensible_helper(plan: QuestPlan) -> bool:
    return plan.id in QUESTS and len(plan.finish) > 0


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            for qid, q in QUESTS.items():
                if quest_at_risk(item, place) and sensible_helper(q):
                    combos.append((pid, iid, qid))
    return combos


def quest_energy(plan: QuestPlan, delay: int) -> int:
    return 1 + delay


def is_success(plan: QuestPlan, delay: int) -> bool:
    return quest_energy(plan, delay) <= 2


def tell(place: Place, item: QuestItem, kit: HelperKit, quest: QuestPlan,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Nina", helper_gender: str = "girl",
         delay: int = 0) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="quester"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    lost = world.add(Entity(id="item", kind="thing", type="thing", label=item.label))
    child.carries = ""
    helper.carries = kit.label

    child.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At the snowy curb, {child.label} began a little quest. "
        f"The {place.domain_word} looked white and bright, all sparkling in sight."
    )
    world.say(
        f'{child.label} said, "I lost my {item.label}, oh no, oh dear. '
        f'If we do not find it, the day turns drear."'
    )
    world.say(
        f"{helper.label} came with {kit.phrase}, all snug and warm. "
        f"'{quest.rhyme}'"
    )

    world.para()
    child.meters["search"] += 1
    place.meters["wind"] += 1
    propagate(world, narrate=False)

    if item.lost_in == place.id:
        world.say(
            f"They searched by the curb where the snowflakes swirled. "
            f"{child.label} looked left and right, round and round in the world."
        )
        if delay == 0:
            world.say(
                f"Then under a snowy ridge, with a tiny bright gleam, "
                f"they spotted the {item.label} like a star in a dream."
            )
            item.meters["found"] += 1
            child.memes["joy"] += 1
            helper.memes["joy"] += 1
            world.say(
                f"{helper.label} brushed it free, and {child.label} gave a cheer. "
                f"The lost little treasure was finally here."
            )
        else:
            child.meters["search"] += 1
            item.meters["found"] += 1
            child.memes["joy"] += 1
            helper.memes["joy"] += 1
            world.say(
                f"They followed a tiny track, one print then another, "
                f"and found the {item.label} tucked near a curbside cover."
            )
    else:
        raise StoryError("The quest item must be lost on the snowy curb for this world.")

    world.para()
    if is_success(quest, delay):
        world.say(
            f"Then {helper.label} smiled and wrapped the {kit.label} tight. "
            f"{kit.warm} made the chilly air feel right."
        )
        world.say(
            f"{child.label} held the {item.label} and laughed with a grin. "
            f"The quest was complete; the warm day moved in."
        )
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
    else:
        world.say(
            f"The wind still nipped, but their search stayed brave. "
            f"They reached the {item.label} before the snow could cave."
        )
        child.memes["relief"] += 1
        helper.memes["relief"] += 1

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        item=item,
        kit=kit,
        quest=quest,
        delay=delay,
        success=is_success(quest, delay),
        found=item.meters["found"] >= THRESHOLD,
    )
    return world


PLACES = {
    "snowy_curb": Place(
        id="snowy_curb",
        label="snowy curb",
        snow="snowy curb",
        curb="curb",
        quest_word="quest",
        domain_word="domain",
        cold=True,
    ),
}

ITEMS = {
    "mitten": QuestItem(
        id="mitten",
        label="mitten",
        phrase="a blue mitten",
        lost_in="snowy_curb",
        can_fit=True,
        tags={"winter", "lost"},
    ),
    "sled_key": QuestItem(
        id="sled_key",
        label="sled key",
        phrase="a tiny sled key",
        lost_in="snowy_curb",
        can_fit=True,
        tags={"winter", "lost"},
    ),
}

KITS = {
    "thermos": HelperKit(
        id="thermos",
        label="thermos",
        phrase="a warm thermos",
        warm="The cocoa inside was warm and sweet",
        use="sip",
        tags={"warm"},
    ),
    "scarf": HelperKit(
        id="scarf",
        label="scarf",
        phrase="a soft scarf",
        warm="The scarf kept the chill away",
        use="wrap",
        tags={"warm"},
    ),
}

QUESTS = {
    "find_mitten": QuestPlan(
        id="find_mitten",
        goal="find the mitten",
        rhyme="Let's seek the peek of the white curb streak!",
        finish="home again",
        tags={"quest", "winter"},
    ),
    "find_key": QuestPlan(
        id="find_key",
        goal="find the sled key",
        rhyme="Let's peer and cheer for the missing gear!",
        finish="play again",
        tags={"quest", "winter"},
    ),
}

GIRL_NAMES = ["Nina", "Maya", "Luna", "Ivy", "Zoe"]
BOY_NAMES = ["Milo", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    place: str
    item: str
    kit: str
    quest: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


CURATED = [
    StoryParams(
        place="snowy_curb",
        item="mitten",
        kit="thermos",
        quest="find_mitten",
        child_name="Milo",
        child_gender="boy",
        helper_name="Nina",
        helper_gender="girl",
        delay=0,
    ),
    StoryParams(
        place="snowy_curb",
        item="sled_key",
        kit="scarf",
        quest="find_key",
        child_name="Luna",
        child_gender="girl",
        helper_name="Eli",
        helper_gender="boy",
        delay=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming quest on a snowy curb.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.item and args.place and not quest_at_risk(ITEMS[args.item], PLACES[args.place]):
        raise StoryError("No story: the chosen item is not really at risk on the snowy curb.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, quest = rng.choice(sorted(combos))
    kit = args.kit or rng.choice(sorted(KITS))
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    cg = args.child_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or ("boy" if cg == "girl" else "girl")
    cn = args.child_name or rng.choice(GIRL_NAMES if cg == "girl" else BOY_NAMES)
    hn = args.helper_name or rng.choice(GIRL_NAMES if hg == "girl" else BOY_NAMES)
    return StoryParams(place=place, item=item, kit=kit, quest=quest,
                       child_name=cn, child_gender=cg,
                       helper_name=hn, helper_gender=hg, delay=delay)


def generate(params: StoryParams) -> StorySample:
    for field_name in ("place", "item", "kit", "quest"):
        if getattr(params, field_name) not in globals()[field_name.upper() + "S"]:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)}")
    world = tell(PLACES[params.place], ITEMS[params.item], KITS[params.kit], QUESTS[params.quest],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender,
                 params.delay)
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
        "Write a rhyming story about a child quest on a snowy curb, and include the word domain.",
        f"Tell a small quest story where {f['child'].label} and {f['helper'].label} search the snowy curb for a lost item.",
        f"Write a child-friendly rhyming tale set at a snowy curb where the word domain appears naturally.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    kit = f["kit"]
    q = f["quest"]
    answers = [
        ("Who went on the quest?",
         f"{child.label} and {helper.label} went on the quest together. They worked as a little team at the snowy curb."),
        ("What were they looking for?",
         f"They were looking for the {item.label}. It was lost on the snowy curb, so they searched until they found it."),
        ("What helped them stay warm?",
         f"The {kit.label} helped them stay warm. That made the cold curb feel less chilly while they searched."),
        ("How did the story end?",
         f"It ended happily, with the lost thing found and the quest finished. The snowy curb turned from chilly trouble into a warm little victory."),
    ]
    if f.get("success"):
        answers.append((
            "What changed by the end?",
            f"By the end, the search was over and everyone felt relieved. The child had the {item.label} again, and the helper's warmth made the ending cozy."
        ))
    return answers


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["item"].id, world.facts["kit"].id, "quest", "snow"}
    out = []
    if "quest" in tags:
        out.append(("What is a quest?", "A quest is a search or mission to find something or solve a problem. In stories, it often means setting off with a goal and not giving up."))
    if "snow" in tags:
        out.append(("What is snow?", "Snow is frozen water that falls like soft white flakes. It can make the ground cold, bright, and slippery."))
    if world.facts["kit"].id == "thermos":
        out.append(("What is a thermos?", "A thermos is a container that helps keep drinks warm or cold for longer."))
    if world.facts["kit"].id == "scarf":
        out.append(("What does a scarf do?", "A scarf wraps around your neck to help keep you warm when the air is cold."))
    if world.facts["item"].id == "mitten":
        out.append(("What is a mitten?", "A mitten is a warm hand covering, and it keeps fingers cozy together in the cold."))
    if world.facts["item"].id == "sled_key":
        out.append(("What is a sled key?", "A sled key is a tiny piece that can help a sled or sled toy work."))
    return out


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
        if e.carries:
            bits.append(f"carries={e.carries}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.can_fit:
            lines.append(asp.fact("fit", iid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, I, Q) :- place(P), item(I), quest(Q), fit(I).
outcome(success) :- valid(_, _, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(_: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


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
        print(asp_program("#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid quest combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
