#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/advantage_fiftieth_quest_fable.py
==================================================================

A standalone storyworld for a small fable-like quest domain.

Seed idea:
- Words to include: "advantage" and "fiftieth"
- Feature: Quest
- Style: Fable

This world tells a short quest fable about a small traveler who tries many times,
learns from a helper, and finds that patience gives the best advantage. The
world model tracks physical meters (distance, load, treasure, etc.) and emotional
memes (hope, pride, calm, shame, etc.), and the prose is driven by those states.

The ending always proves what changed: the quest is completed, the helper's
lesson is learned, and the final image shows the gained advantage.
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
TRY_MARK = 50


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
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
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
    obstacle: str
    reward: str
    opening: str
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
class Quest:
    id: str
    verb: str
    goal: str
    method: str
    risk: str
    meter: str
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
class Guide:
    id: str
    label: str
    advice: str
    advantage: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w
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


def _r_try(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    gate = world.entities.get("gate")
    if not hero or not gate:
        return out
    if hero.meters["tries"] < THRESHOLD:
        return out
    sig = ("try", int(hero.meters["tries"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gate.meters["yield"] += 1
    hero.memes["hope"] += 1
    out.append("__try__")
    return out


def _r_advantage(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    guide = world.entities.get("guide")
    if not hero or not guide:
        return out
    if hero.meters["advantage"] < THRESHOLD:
        return out
    sig = ("adv", 1)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] += 1
    out.append("__advantage__")
    return out


CAUSAL_RULES = [Rule("try", _r_try), Rule("advantage", _r_advantage)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_success(world: World, quest: Quest) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["tries"] += 1
    hero.meters["advantage"] += 1
    propagate(sim, narrate=False)
    gate = sim.get("gate")
    return {"yield": gate.meters["yield"], "advantage": hero.meters["advantage"]}


def tell(setting: Setting, quest: Quest, guide: Guide, hero_name: str, hero_type: str,
         mentor_name: str, mentor_type: str, tries: int, bold: int, patience: int) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name,
                             role="seeker", traits=["small", "brave"], attrs={"name": hero_name}))
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_type, label=mentor_name,
                              role="guide", traits=["wise"], attrs={"name": mentor_name}))
    gate = world.add(Entity(id="gate", type="thing", label=setting.obstacle, role="gate"))
    prize = world.add(Entity(id="prize", type="thing", label=setting.reward, role="reward"))

    hero.meters["tries"] = float(tries)
    hero.memes["bold"] = float(bold)
    hero.memes["patience"] = float(patience)
    mentor.memes["wisdom"] = 2.0

    world.say(
        f"Once in a little {setting.place}, there lived {hero_name}, a small {hero_type} "
        f"who wanted to {quest.verb} and win {setting.reward}."
    )
    world.say(
        f"{setting.opening} {hero_name} set out at dawn, because the old path promised a quest "
        f"that only a patient heart could finish."
    )

    world.para()
    world.say(
        f"{hero_name} reached {setting.obstacle}, and the way would not open by hurry alone."
    )
    world.say(
        f"{mentor_name} the {mentor_type} watched quietly and said, "
        f"\"A true advantage is not speed. It is knowing when to listen.\""
    )

    world.para()
    world.say(
        f"{hero_name} tried again and again, and each try made the gate tremble a little more."
    )
    if tries < TRY_MARK:
        hero.meters["tries"] = float(TRY_MARK)
        world.say(
            f"On the fiftieth try, {hero_name} stopped pushing and tried {guide.method} instead."
        )
    else:
        world.say(
            f"By the fiftieth try, {hero_name} had already learned to use {guide.method}."
        )

    hero.meters["advantage"] += 1
    propagate(world, narrate=False)
    pred = predict_success(world, quest)
    world.facts["predicted"] = pred

    world.para()
    if pred["yield"] >= THRESHOLD:
        gate.meters["open"] = 1.0
        prize.meters["claimed"] = 1.0
        hero.memes["joy"] += 2
        mentor.memes["joy"] += 1
        world.say(
            f"Then the gate opened wide, and {hero_name} found the {setting.reward} shining beyond it."
        )
        world.say(
            f"{mentor_name} smiled as the child took the treasure, for the best advantage had been patience all along."
        )
    else:
        gate.meters["open"] = 0.0
        hero.memes["worry"] += 1
        world.say(
            f"But even after the fiftieth try, the gate stayed shut, and {hero_name} had to go home wiser."
        )
        world.say(
            f"The lesson remained the same: a quest can fail for a day, but a calm mind keeps its advantage tomorrow."
        )

    world.facts.update(
        hero=hero, mentor=mentor, gate=gate, prize=prize, quest=quest, guide=guide,
        outcome="opened" if gate.meters["open"] >= THRESHOLD else "shut",
        tries=int(hero.meters["tries"]),
    )
    return world


SETTINGS = {
    "hill": Setting(
        id="hill",
        place="hill town",
        obstacle="the old stone gate",
        reward="a silver key",
        opening="At the edge of the hill town,",
        tags={"quest", "gate"},
    ),
    "forest": Setting(
        id="forest",
        place="forest village",
        obstacle="the briar arch",
        reward="a golden leaf",
        opening="Deep in the green forest,",
        tags={"quest", "gate"},
    ),
    "harbor": Setting(
        id="harbor",
        place="harbor lane",
        obstacle="the sea-wall door",
        reward="a small pearl",
        opening="By the windy harbor,",
        tags={"quest", "gate"},
    ),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        verb="finish the quest",
        goal="the hidden reward",
        method="wait, listen, and try once more",
        risk="pride",
        meter="tries",
        tags={"quest"},
    ),
}

GUIDES = {
    "owl": Guide(
        id="owl",
        label="an old owl",
        advice="wait, listen, and try once more",
        advantage="patience",
        tags={"wisdom"},
    ),
    "grandmother": Guide(
        id="grandmother",
        label="a grandmother",
        advice="breathe, look, and try the gentle way",
        advantage="calm",
        tags={"wisdom"},
    ),
    "miller": Guide(
        id="miller",
        label="a miller",
        advice="move the latch instead of pushing the door",
        advantage="thinking",
        tags={"wisdom"},
    ),
}

HERO_NAMES = ["Milo", "Nia", "Sage", "Leah", "Tomas", "Iris", "Pip", "Rina"]
MENTOR_NAMES = ["Rowan", "Wren", "Etta", "Bram", "Oona", "Nell"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    guide: str
    hero_name: str
    hero_type: str
    mentor_name: str
    mentor_type: str
    tries: int = TRY_MARK
    bold: int = 3
    patience: int = 3
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for g in GUIDES:
                combos.append((s, q, g))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about a quest where {f["hero"].label_word} learns the word "advantage" by listening on the fiftieth try.',
        f"Tell a gentle quest story in a fable style where {f['hero'].label_word} almost gives up, but {f['mentor'].label_word} helps at the fiftieth try.",
        f'Write a child-friendly story that includes the words "advantage" and "fiftieth" and ends with a lesson about patience.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mentor, setting, guide = f["hero"], f["mentor"], f["quest"], f["guide"]
    out = [
        (
            "What was the quest about?",
            f"It was about {hero.label_word} trying to {setting.verb}. The journey led toward a hidden reward behind a stubborn gate.",
        ),
        (
            "Why did {0} keep trying?".format(hero.label_word),
            f"{hero.label_word} wanted the reward and did not want to turn back. The fiftieth try mattered because that was when {hero.label_word} finally used {guide.advice}.",
        ),
        (
            "What did the mentor teach?",
            f"{mentor.label_word} taught that the best advantage is patience. That advice helped the child stop pushing and choose the wiser way.",
        ),
    ]
    if f["outcome"] == "opened":
        out.append(
            (
                "How did the story end?",
                f"It ended with the gate opening and the reward shining in the sunlight. {hero.label_word} learned that the fiftieth try can succeed when the heart grows calm.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        (
            "What does advantage mean?",
            "An advantage is something that helps you do better or reach a goal more easily. In a fable, patience can be a quiet advantage.",
        ),
        (
            "What does fiftieth mean?",
            "Fiftieth means number fifty in order. It comes after forty-ninth and before fifty-first.",
        ),
        (
            "What is a fable?",
            "A fable is a short story that teaches a lesson, often by using animals or simple characters. The lesson is usually clear at the end.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:7} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: this quest setup cannot be made reasonable from the chosen options.)"


ASP_RULES = r"""
% A quest is successful when the hero reaches advantage and the gate opens.
needs_try(hero) :- quest(quest).
fiftieth_try(hero) :- tries(50).
advantage(hero) :- listens(hero), tries(50).
opened(hero) :- advantage(hero), gate_open(gate).
outcome(opened) :- opened(hero).
outcome(shut) :- not opened(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    lines.append(asp.fact("tries", TRY_MARK))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show outcome/1."))
        _ = asp.atoms(model, "outcome")
    except Exception as err:
        print(f"ASP smoke test failed: {err}")
        return 1

    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, quest=None, guide=None, hero_name=None, hero_type=None,
            mentor_name=None, mentor_type=None, tries=None, bold=None, patience=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"Normal generation failed: {err}")
        return 1

    print("OK: ASP smoke test and normal generation both succeeded.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small quest fable about patience and advantage.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "fox", "rabbit", "mouse"])
    ap.add_argument("--mentor-name")
    ap.add_argument("--mentor-type", choices=["owl", "woman", "man", "mouse"])
    ap.add_argument("--tries", type=int)
    ap.add_argument("--bold", type=int)
    ap.add_argument("--patience", type=int)
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection(args))
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or "quest"
    guide = args.guide or rng.choice(list(GUIDES))
    hero_type = args.hero_type or rng.choice(["girl", "boy", "fox", "rabbit", "mouse"])
    mentor_type = args.mentor_type or "owl"
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    mentor_name = args.mentor_name or rng.choice(MENTOR_NAMES)
    tries = args.tries if args.tries is not None else TRY_MARK
    bold = args.bold if args.bold is not None else rng.randint(2, 5)
    patience = args.patience if args.patience is not None else rng.randint(2, 5)
    return StoryParams(
        setting=setting,
        quest=quest,
        guide=guide,
        hero_name=hero_name,
        hero_type=hero_type,
        mentor_name=mentor_name,
        mentor_type=mentor_type,
        tries=tries,
        bold=bold,
        patience=patience,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.guide not in GUIDES:
        raise StoryError("invalid story parameters")
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        GUIDES[params.guide],
        params.hero_name,
        params.hero_type,
        params.mentor_name,
        params.mentor_type,
        params.tries,
        params.bold,
        params.patience,
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
        print(asp_program("#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show outcome/1."))
        print("ASP model:", sorted(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(
            setting="hill",
            quest="quest",
            guide="owl",
            hero_name="Milo",
            hero_type="mouse",
            mentor_name="Rowan",
            mentor_type="owl",
            tries=TRY_MARK,
            bold=4,
            patience=5,
        ),
        StoryParams(
            setting="forest",
            quest="quest",
            guide="grandmother",
            hero_name="Nia",
            hero_type="girl",
            mentor_name="Etta",
            mentor_type="woman",
            tries=TRY_MARK,
            bold=3,
            patience=4,
        ),
        StoryParams(
            setting="harbor",
            quest="quest",
            guide="miller",
            hero_name="Pip",
            hero_type="fox",
            mentor_name="Bram",
            mentor_type="man",
            tries=TRY_MARK,
            bold=5,
            patience=2,
        ),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero_name}: the fiftieth quest at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
