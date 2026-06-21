#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/evening_sound_effects_inner_monologue_magic_adventure.py
=======================================================================================

A small standalone storyworld for a TinyStories-style adventure set in the
evening, with sound effects, inner monologue, and a little magic.

Premise
-------
A child goes on a short evening adventure to help recover something lost,
guided by magical clues. The sound effects and inner monologue are state-driven:
the world records when things creak, whooshes, or sparkles, and the child's
thoughts shift from worry to courage to delight.

The world is intentionally compact:
- one child protagonist
- one helper or companion
- one small magical object
- one evening location
- one goal object that must be found or rescued

The prose is authored from simulated state, not from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/evening_sound_effects_inner_monologue_magic_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/evening_sound_effects_inner_monologue_magic_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/evening_sound_effects_inner_monologue_magic_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/evening_sound_effects_inner_monologue_magic_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/evening_sound_effects_inner_monologue_magic_adventure.py --verify
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
BRAVE_MIN = 4.0


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
    evening_detail: str
    sound: str
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
class Goal:
    id: str
    label: str
    phrase: str
    hidden_in: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    sound: str
    glow: str
    power: int
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
class Complication:
    id: str
    label: str
    description: str
    risky_sound: str
    risk: int
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


def _r_worry(world: World) -> list[str]:
    out = []
    kid = world.get("kid")
    if kid.memes["worry"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        kid.memes["fear"] += 1
        out.append("__thought__")
    return out


def _r_magic(world: World) -> list[str]:
    out = []
    if world.get("wand").meters["glow"] >= THRESHOLD and ("magic",) not in world.fired:
        world.fired.add(("magic",))
        world.get("trail").meters["sparkle"] += 1
        out.append("__sparkle__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("magic", _r_magic)]


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


def setting_for(setting: Setting, goal: Goal) -> bool:
    return goal.hidden_in in setting.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for gid, goal in GOALS.items():
            if not setting_for(setting, goal):
                continue
            for cid, complication in COMPLICATIONS.items():
                if complication.risk <= 0:
                    continue
                combos.append((sid, gid, cid))
    return combos


@dataclass
class StoryParams:
    setting: str
    goal: str
    complication: str
    child_name: str
    child_gender: str
    companion_name: str
    companion_gender: str
    magic_item: str
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
    "garden": Setting(
        id="garden",
        place="the garden",
        evening_detail="The evening air smelled like wet leaves and mint.",
        sound="soft crickets",
        tags={"garden", "outside", "evening", "path"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the little harbor",
        evening_detail="The water shushed against the docks under the pink evening sky.",
        sound="gentle waves",
        tags={"harbor", "outside", "evening", "dock"},
    ),
    "attic": Setting(
        id="attic",
        place="the attic",
        evening_detail="The attic was dim, with moonlight sliding through one round window.",
        sound="old floorboards",
        tags={"attic", "inside", "evening", "loft"},
    ),
}

GOALS = {
    "lantern": Goal(
        id="lantern",
        label="lantern",
        phrase="a tiny brass lantern",
        hidden_in="garden",
        tags={"garden"},
    ),
    "shell": Goal(
        id="shell",
        label="shell",
        phrase="a moon-white shell",
        hidden_in="harbor",
        tags={"harbor"},
    ),
    "key": Goal(
        id="key",
        label="key",
        phrase="an old silver key",
        hidden_in="attic",
        tags={"attic"},
    ),
}

COMPLICATIONS = {
    "wind": Complication(
        id="wind",
        label="wind",
        description="a quick gust that rattled branches and doors",
        risky_sound="whoooosh",
        risk=1,
    ),
    "shadow": Complication(
        id="shadow",
        label="shadow",
        description="a long shadow that made the path look strange",
        risky_sound="shiver-shiver",
        risk=1,
    ),
    "rattle": Complication(
        id="rattle",
        label="rattle",
        description="a loose latch that kept clacking in the dark",
        risky_sound="clack-clack",
        risk=1,
    ),
}

MAGIC_ITEMS = {
    "firefly_jar": MagicItem(
        id="firefly_jar",
        label="firefly jar",
        phrase="a little jar of firefly light",
        effect="made the dark corners shine kindly",
        sound="fizz-fizz",
        glow="glowed like a friendly star",
        power=2,
        tags={"light", "magic"},
    ),
    "whisper_stone": MagicItem(
        id="whisper_stone",
        label="whisper stone",
        phrase="a smooth whisper stone",
        effect="pointed the way when the child listened closely",
        sound="hmmmmm",
        glow="warmed in the hand",
        power=1,
        tags={"guide", "magic"},
    ),
    "moon_ribbon": MagicItem(
        id="moon_ribbon",
        label="moon ribbon",
        phrase="a silver moon ribbon",
        effect="tied the right path into a bright little ribbon",
        sound="tink-tink",
        glow="sparkled pale and bright",
        power=2,
        tags={"guide", "magic"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nina", "Ivy", "Ava"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Eli", "Jonah", "Finn"]


def predict(world: World, setting: Setting, complication: Complication) -> dict:
    sim = world.copy()
    sim.get("kid").memes["worry"] += complication.risk
    propagate(sim, narrate=False)
    return {"fear": sim.get("kid").memes["fear"], "sparkle": sim.get("trail").meters["sparkle"]}


def tell(setting: Setting, goal: Goal, complication: Complication, magic: MagicItem,
         child_name: str, child_gender: str, companion_name: str, companion_gender: str) -> World:
    world = World()
    kid = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="helper"))
    kid.memes["curiosity"] += 1
    kid.memes["worry"] += 0.5
    companion.memes["calm"] += 1

    trail = world.add(Entity(id="trail", type="place", label="the trail"))
    wand = world.add(Entity(id="wand", type="magic", label=magic.label))
    prize = world.add(Entity(id="prize", type="thing", label=goal.label))
    world.facts.update(setting=setting, goal=goal, complication=complication, magic=magic,
                       kid=kid, companion=companion, prize=prize, trail=trail, wand=wand)

    world.say(f"That evening, {kid.id} and {companion.id} set out toward {setting.place}.")
    world.say(f"{setting.evening_detail} {setting.sound} seemed to follow them along the path.")
    world.say(f"{kid.id} wanted to find {goal.phrase}, but {complication.description} made the way feel tricky.")

    world.para()
    kid.memes["worry"] += complication.risk
    world.say(f'"If I listen carefully, I can do this," {kid.id} thought.')
    world.say(f'The dark answered with {complication.risky_sound}.')
    if kid.memes["worry"] >= BRAVE_MIN:
        world.say(f'"I am a little scared," {kid.id} thought, "but the path is still there."')

    world.para()
    world.say(f'Then {companion.id} held up {magic.phrase}, and it {magic.glow}.')
    wand.meters["glow"] += 1
    trail.meters["light"] += magic.power
    propagate(world, narrate=False)
    world.say(f'It went {magic.sound}, and the magic {magic.effect}.')
    world.say(f"{kid.id} took a deep breath and followed the new bright line.")

    world.para()
    if setting.id == "attic":
        world.say("The floorboards creaked under each careful step.")
    elif setting.id == "harbor":
        world.say("The dock boards tapped softly under their shoes.")
    else:
        world.say("The garden path rustled under the bushes.")
    world.say(f"At last, {kid.id} found {goal.phrase} waiting right where the glow pointed.")
    prize.meters["found"] += 1
    kid.memes["joy"] += 2
    companion.memes["joy"] += 1
    world.say(f"{kid.id} smiled so big it felt like the whole evening had turned into an adventure.")

    world.facts["outcome"] = "found"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    goal: Goal = f["goal"]
    complication: Complication = f["complication"]
    magic: MagicItem = f["magic"]
    kid: Entity = f["kid"]
    return [
        f'Write an evening adventure story for a small child that includes the word "evening" and the sound "{complication.risky_sound}".',
        f"Tell a story where {kid.id} and a companion go through {setting.place} at evening, use {magic.label}, and find {goal.label}.",
        f"Write a child-friendly adventure with a little magic, a worried thought, and a bright ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid: Entity = f["kid"]
    companion: Entity = f["companion"]
    goal: Goal = f["goal"]
    magic: MagicItem = f["magic"]
    setting: Setting = f["setting"]
    complication: Complication = f["complication"]
    return [
        QAItem(
            question=f"What did {kid.id} and {companion.id} go looking for?",
            answer=f"They went looking for {goal.phrase}. The goal was hidden in {setting.place}, so they had to keep going until the magic showed them the way.",
        ),
        QAItem(
            question=f"Why did {kid.id} feel worried at first?",
            answer=f"{kid.id} felt worried because {complication.description} made the path seem tricky. The worry was small, but it was enough to make the child pause and think before stepping forward.",
        ),
        QAItem(
            question=f"How did the magic help?",
            answer=f"{companion.id} lifted {magic.phrase}, and it {magic.glow}. That gave them enough light and courage to follow the path and find the lost thing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic: MagicItem = f["magic"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="What does evening mean?",
            answer="Evening is the time near the end of the day, after afternoon and before night. The sky often gets dim and quiet then.",
        ),
        QAItem(
            question=f"What kind of thing is a {magic.label} in this story?",
            answer=f"It is a magical helper that gives off a glow or a guide-like feeling. In stories, magic objects often help characters find a safe path.",
        ),
        QAItem(
            question="Why do sound effects matter in adventure stories?",
            answer="Sound effects help the reader imagine what is happening. A creak, a whoosh, or a fizz can make a place feel alive and exciting.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, goal: Goal) -> str:
    return f"(No story: {goal.label} is not hidden in {setting.place}, so this adventure would not have a fair magical search.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    goal = args.goal or rng.choice(sorted(g for g in GOALS if GOALS[g].hidden_in == setting))
    complication = args.complication or rng.choice(sorted(COMPLICATIONS))
    if setting not in SETTINGS or goal not in GOALS or complication not in COMPLICATIONS:
        raise StoryError("Invalid story parameters.")
    if not setting_for(SETTINGS[setting], GOALS[goal]):
        raise StoryError(explain_rejection(SETTINGS[setting], GOALS[goal]))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion_gender = args.companion_gender or ("boy" if gender == "girl" else "girl")
    companion_name = args.companion_name or rng.choice(GIRL_NAMES if companion_gender == "girl" else BOY_NAMES)
    magic_item = args.magic_item or rng.choice(sorted(MAGIC_ITEMS))
    return StoryParams(
        setting=setting,
        goal=goal,
        complication=complication,
        child_name=child_name,
        child_gender=gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        magic_item=magic_item,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, table in (("setting", SETTINGS), ("goal", GOALS), ("complication", COMPLICATIONS), ("magic_item", MAGIC_ITEMS)):
        if getattr(params, field_name) not in table:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)}")
    if not setting_for(SETTINGS[params.setting], GOALS[params.goal]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], GOALS[params.goal]))
    world = tell(
        SETTINGS[params.setting],
        GOALS[params.goal],
        COMPLICATIONS[params.complication],
        MAGIC_ITEMS[params.magic_item],
        params.child_name,
        params.child_gender,
        params.companion_name,
        params.companion_gender,
    )
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


ASP_RULES = r"""
setting(garden). setting(harbor). setting(attic).
goal(lantern). goal(shell). goal(key).
complication(wind). complication(shadow). complication(rattle).
magic(firefly_jar). magic(whisper_stone). magic(moon_ribbon).

hidden_in(lantern, garden).
hidden_in(shell, harbor).
hidden_in(key, attic).

valid(S, G, C) :- setting(S), goal(G), complication(C), hidden_in(G, S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for g, goal in GOALS.items():
        lines.append(asp.fact("goal", g))
        lines.append(asp.fact("hidden_in", g, goal.hidden_in))
    for c in COMPLICATIONS:
        lines.append(asp.fact("complication", c))
    for m in MAGIC_ITEMS:
        lines.append(asp.fact("magic", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, goal=None, complication=None, child_name=None,
            child_gender=None, companion_name=None, companion_gender=None,
            magic_item=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An evening adventure with sound effects, inner monologue, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--complication", choices=COMPLICATIONS)
    ap.add_argument("--magic-item", choices=MAGIC_ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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


CURATED = [
    StoryParams(setting="garden", goal="lantern", complication="wind", child_name="Lina", child_gender="girl", companion_name="Owen", companion_gender="boy", magic_item="firefly_jar"),
    StoryParams(setting="harbor", goal="shell", complication="shadow", child_name="Milo", child_gender="boy", companion_name="Ivy", companion_gender="girl", magic_item="moon_ribbon"),
    StoryParams(setting="attic", goal="key", complication="rattle", child_name="Tessa", child_gender="girl", companion_name="Theo", companion_gender="boy", magic_item="whisper_stone"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.child_name} in {p.setting} ({p.goal}, {p.magic_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
