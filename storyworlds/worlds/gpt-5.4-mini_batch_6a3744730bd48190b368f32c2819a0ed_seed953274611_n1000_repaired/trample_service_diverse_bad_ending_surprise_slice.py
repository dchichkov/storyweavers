#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trample_service_diverse_bad_ending_surprise_slice.py
===================================================================================

A small slice-of-life storyworld about a community service day, a diverse group
of helpers, a surprise, and one bad ending where something important gets trampled.

The seed words are intentionally central:
- trample
- service
- diverse

The story premise is simple and child-facing:
people set up a neighborhood service table, enjoy a calm afternoon, a surprise
changes the mood, and an unsafe rush causes a precious display to be trampled.
The ending is deliberately bad, but still complete and readable.

The world model tracks physical meters and emotional memes through a few typed
entities. Story text is driven from state changes, not from a frozen paragraph.
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
    diverse: bool = False
    serviceable: bool = False
    fragile: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    service: str
    surprise: str
    crowd_sound: str
    nice_detail: str
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
class ServiceTask:
    id: str
    title: str
    table_text: str
    gentle_action: str
    success_text: str
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
class Surprise:
    id: str
    title: str
    reveal_text: str
    attention_shift: str
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
class FragileItem:
    id: str
    label: str
    noun_phrase: str
    surface: str
    can_trample: bool = True
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
        clone.facts = dict(self.facts)
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


def _r_attention(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_seen") and "helper" in world.entities:
        helper = world.get("helper")
        if helper.memes["startle"] >= THRESHOLD and ("attention",) not in world.fired:
            world.fired.add(("attention",))
            helper.memes["rush"] += 1
            out.append("The surprise pulled everyone off balance.")
    return out


def _r_trample(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("rush_started"):
        return out
    fragile = world.get("display")
    if fragile.meters["trampled"] >= THRESHOLD:
        return out
    sig = ("trample", fragile.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fragile.meters["trampled"] += 1
    fragile.meters["broken"] += 1
    for c in world.characters():
        c.memes["sad"] += 1
    out.append("__trampled__")
    return out


CAUSAL_RULES = [
    Rule("attention", "social", _r_attention),
    Rule("trample", "physical", _r_trample),
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


def could_trample(task: ServiceTask, item: FragileItem) -> bool:
    return item.can_trample and "feet" in task.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, task in TASKS.items():
            for iid, item in ITEMS.items():
                if could_trample(task, item):
                    combos.append((sid, tid, iid))
    return combos


def simple_service_task() -> list[ServiceTask]:
    return list(TASKS.values())


def best_safe_task() -> ServiceTask:
    return TASKS["garden_help"]


def _family_names(rng: random.Random) -> tuple[str, str, str]:
    names = ["Ava", "Mina", "Rin", "Noah", "Eli", "Sage", "Luca", "Nia", "Ivy", "Theo"]
    hero = rng.choice(names)
    helper = rng.choice([n for n in names if n != hero])
    parent = rng.choice(["mom", "dad", "aunt"])
    return hero, helper, parent


@dataclass
class StoryParams:
    setting: str
    task: str
    item: str
    hero: str
    helper: str
    parent: str
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


SETTINGS = {
    "community_garden": Setting(
        id="community_garden",
        place="the community garden",
        service="service day",
        surprise="surprise visit",
        crowd_sound="soft voices and little footsteps",
        nice_detail="tomato vines leaned over the path like sleepy green elbows",
        tags={"service", "slice_of_life"},
    ),
    "school_hall": Setting(
        id="school_hall",
        place="the school hall",
        service="service fair",
        surprise="surprise announcement",
        crowd_sound="chairs scraping gently and happy talk",
        nice_detail="paper stars hung from the ceiling",
        tags={"service", "slice_of_life"},
    ),
}

TASKS = {
    "table_setup": ServiceTask(
        id="table_setup",
        title="setting up a service table",
        table_text="They arranged the service table with juice, napkins, and tidy signs.",
        gentle_action="carefully arrange the cups and signs",
        success_text="the table stayed neat and welcoming",
        tags={"feet"},
    ),
    "garden_help": ServiceTask(
        id="garden_help",
        title="helping in the garden",
        table_text="They carried small watering cans and lined up seedlings for visitors.",
        gentle_action="water the plants one by one",
        success_text="the little plants got help without any trouble",
        tags={"feet"},
    ),
    "snack_service": ServiceTask(
        id="snack_service",
        title="serving snacks",
        table_text="They passed out crackers and orange slices to everyone nearby.",
        gentle_action="hand out snacks slowly",
        success_text="everyone got a snack and a smile",
        tags={"feet"},
    ),
}

ITEMS = {
    "cookie_display": FragileItem(
        id="cookie_display",
        label="cookie display",
        noun_phrase="a plate of decorated cookies",
        surface="the low picnic cloth",
        can_trample=True,
        tags={"cookie", "fragile"},
    ),
    "seedlings": FragileItem(
        id="seedlings",
        label="seedlings",
        noun_phrase="three tiny seedlings in little cups",
        surface="the bottom shelf",
        can_trample=True,
        tags={"garden", "fragile"},
    ),
    "paper_crafts": FragileItem(
        id="paper_crafts",
        label="paper crafts",
        noun_phrase="a row of paper windmills",
        surface="the front table",
        can_trample=True,
        tags={"paper", "fragile"},
    ),
}

SURPRISES = {
    "balloon_popper": Surprise(
        id="balloon_popper",
        title="a balloon popped nearby",
        reveal_text="Then a balloon popped with a sharp bang!",
        attention_shift="everyone looked up at once",
        tags={"surprise"},
    ),
    "lost_puppy": Surprise(
        id="lost_puppy",
        title="a lost puppy arrived",
        reveal_text="Then a little lost puppy trotted in from the gate.",
        attention_shift="everyone turned to look and smile",
        tags={"surprise"},
    ),
}

DIVERSE_TRAITS = ["calm", "careful", "quiet", "kind", "curious", "steady"]
NAMES = ["Ava", "Mina", "Rin", "Noah", "Eli", "Sage", "Luca", "Nia", "Ivy", "Theo"]


def tell(setting: Setting, task: ServiceTask, item: FragileItem, surprise: Surprise,
         hero: str, helper: str, parent: str) -> World:
    w = World()
    h = w.add(Entity(id=hero, kind="character", type="child", role="helper", traits=["diverse", "kind"], diverse=True))
    k = w.add(Entity(id=helper, kind="character", type="child", role="helper", traits=["diverse", "careful"], diverse=True))
    p = w.add(Entity(id=parent, kind="character", type="adult", role="parent", type="mother" if parent == "mom" else "father"))
    disp = w.add(Entity(id="display", kind="thing", type="display", label=item.label_word, fragile=True))
    w.facts.update(setting=setting, task=task, item=item, surprise=surprise, hero=h, helper=k, parent=p, display=disp)

    w.say(f"On a warm afternoon at {setting.place}, {hero} and {helper} helped with {setting.service}.")
    w.say(f"The group was diverse in the happiest way: they came from different homes, but they all wanted to help.")
    w.say(setting.nice_detail + f" {task.table_text}")

    w.para()
    w.say(f"{surprise.reveal_text} {surprise.attention_shift}.")
    h.memes["startle"] += 1
    k.memes["startle"] += 1
    w.facts["surprise_seen"] = True

    w.para()
    w.say(f"{hero} tried to keep working, but the sudden noise made {hero} step too quickly.")
    w.facts["rush_started"] = True
    propagate(w, narrate=False)
    if disp.meters["trampled"] >= THRESHOLD:
        w.say(f"In the hurry, {hero}'s foot landed on {item.noun_phrase}, and it got trampled.")
        w.say(f"{helper} gasped, but it was too late to fix the mess right away.")

    w.para()
    w.say(f"{parent.pronoun().capitalize()} came over, looking surprised and sad.")
    w.say(f"The rest of the service kept going, but the special display was ruined, and the mood grew heavy.")
    w.say(f"By the end of the day, {hero} kept thinking about the trampled display and the way the surprise had turned into a bad ending.")

    w.facts["outcome"] = "bad_ending"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, task, item, surprise = f["setting"], f["task"], f["item"], f["surprise"]
    return [
        f"Write a slice-of-life story about {setting.place} and a {task.title} that includes the words trample, service, and diverse.",
        f"Tell a gentle neighborhood story where a surprise changes a service day, and something fragile gets trampled by accident.",
        f"Write a child-friendly story about diverse helpers, a service table, and a bad ending after a sudden surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting, task, item, surprise = f["setting"], f["task"], f["item"], f["surprise"]
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    disp = f["display"]
    return [
        QAItem(
            question="What kind of day was this?",
            answer=f"It was a slice-of-life service day at {setting.place}. People were doing small helpful jobs, and the story stayed close to ordinary life until the surprise arrived.",
        ),
        QAItem(
            question="What changed the mood?",
            answer=f"The surprise changed everything. When {surprise.reveal_text.lower()} {surprise.attention_shift}, everyone lost their calm for a moment.",
        ),
        QAItem(
            question=f"What happened to {item.label_word}?",
            answer=f"{item.noun_phrase} got trampled when {hero} stepped too quickly in the rush. The display was fragile, so the surprise and the hurried feet turned it into a bad ending.",
        ),
        QAItem(
            question="How did the helpers feel at the end?",
            answer=f"They felt sad and disappointed. {helper} wanted to help, but the broken display stayed broken, and {parent.label_word} looked worried as the service went on.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "service": [
        QAItem(
            question="What does service mean?",
            answer="Service means helping other people or doing useful work for a group. It can be setting up tables, carrying things, or sharing snacks.",
        )
    ],
    "diverse": [
        QAItem(
            question="What does diverse mean?",
            answer="Diverse means people are different in some ways, like where they come from, what they look like, or how they help. A diverse group can still work together kindly.",
        )
    ],
    "trample": [
        QAItem(
            question="What does trample mean?",
            answer="To trample something is to step on it heavily and hurt or flatten it. Fragile things can be ruined if someone rushes over them.",
        )
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that suddenly happens. Surprises can be happy or upsetting, depending on what follows.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"service", "diverse", "trample", "surprise"}
    out: list[QAItem] = []
    for key in ["service", "diverse", "trample", "surprise"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
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
        if e.diverse:
            bits.append("diverse=True")
        if e.serviceable:
            bits.append("serviceable=True")
        if e.fragile:
            bits.append("fragile=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
surprise_seen :- surprise(_).
rush_started :- surprise_seen.
trampled(D) :- rush_started, display(D).
outcome(bad_ending) :- trampled(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("feet_task", tid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("can_trample", iid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    # Simple parity: every Python-valid combo should be recognized by the ASP gate.
    rc = 0
    py = set(valid_combos())
    # Derive an ASP program that marks valid when task can trample item.
    extra = "\n".join([
        "valid(S,T,I) :- setting(S), task(T), item(I), feet_task(T), can_trample(I).",
        "#show valid/3.",
    ])
    model = asp.one_model(asp_program("", extra))
    cl = set(asp.atoms(model, "valid"))
    if cl != py:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  python only:", sorted(py - cl))
        print("  asp only   :", sorted(cl - py))
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")

    # Smoke test: ordinary generation must not crash.
    try:
        sample = generate(StoryParams(
            setting="community_garden",
            task="garden_help",
            item="seedlings",
            hero="Ava",
            helper="Mina",
            parent="mom",
        ))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"FAILED: generation smoke test crashed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a service day, a surprise, diverse helpers, and a trampled ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mom", "dad", "aunt"])
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
    combos = valid_combos()
    if args.setting and args.task and args.item:
        if (args.setting, args.task, args.item) not in combos:
            raise StoryError("(No valid combination matches the given options.)")
    if not combos:
        raise StoryError("(No valid combination exists.)")
    setting, task, item = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    parent = args.parent or rng.choice(["mom", "dad", "aunt"])
    return StoryParams(setting=setting, task=task, item=item, hero=hero, helper=helper, parent=parent)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("task", TASKS), ("item", ITEMS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    surprise = SURPRISES["balloon_popper"]
    world = tell(SETTINGS[params.setting], TASKS[params.task], ITEMS[params.item], surprise, params.hero, params.helper, params.parent)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible (setting, task, item) combos:\n")
        for s, t, i in valid_combos():
            print(f"  {s:18} {t:12} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams(setting="community_garden", task="garden_help", item="seedlings", hero="Ava", helper="Mina", parent="mom"),
            StoryParams(setting="school_hall", task="table_setup", item="paper_crafts", hero="Noah", helper="Sage", parent="dad"),
        ]:
            samples.append(generate(p))
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.helper}: {p.task} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
