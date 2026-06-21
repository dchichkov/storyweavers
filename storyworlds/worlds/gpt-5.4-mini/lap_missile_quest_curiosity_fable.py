#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lap_missile_quest_curiosity_fable.py
======================================================================

A small standalone storyworld for a fable-like quest about curiosity, a lap,
and a missile-shaped toy that should not be sent flying indoors.

Domain sketch
-------------
A curious child and a cautious helper are on a little quest for a missing charm.
They discover a toy missile tucked in a chest or pocket, but it is unsafe to
launch where people are sitting. The curious child nearly uses it as a game,
the helper warns them, and a grown-up shows a safer way: the quest can continue
with a map, a lantern, or a paper marker instead of a flying toy.

The world is intentionally tiny:
- typed entities with meters and memes
- a forward causal step that can make the room tense if the toy is launched
- a reasonableness gate that only allows a missile-story when the missile
  actually creates risk near a lap-bound target
- a fable tone with a clear turn and ending image

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/lap_missile_quest_curiosity_fable.py
    python storyworlds/worlds/gpt-5.4-mini/lap_missile_quest_curiosity_fable.py --all
    python storyworlds/worlds/gpt-5.4-mini/lap_missile_quest_curiosity_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/lap_missile_quest_curiosity_fable.py --verify
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
    risky: bool = False
    launches: bool = False
    safe_light: bool = False

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    detail: str
    quest_place: str
    lap_spot: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    at_risk: str
    region: str = "lap"
    fragile: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ToyMissile:
    id: str
    label: str
    phrase: str
    whirr: str
    warn: str
    power: int
    sense: int
    launches: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    method: str
    calm_words: str
    power: int
    sense: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_tension(world: World) -> list[str]:
    out = []
    missile = world.facts.get("missile_ent")
    if missile and missile.meters["launched"] >= THRESHOLD:
        sig = ("tension", missile.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.get("room").meters["tense"] += 1
        for eid in ("child", "helper"):
            world.get(eid).memes["alarm"] += 1
        out.append("__tension__")
    return out


CAUSAL_RULES = [Rule("tension", "social", _r_tension)]


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
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(missile: ToyMissile, relic: Relic) -> bool:
    return missile.launches and relic.fragile


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def quest_severity(delay: int, helper: Helper) -> int:
    return delay + helper.power


def can_contain(helper: Helper, delay: int) -> bool:
    return helper.power >= delay + 1


def _launch(world: World, missile: Entity, narrate: bool = True) -> None:
    missile.meters["launched"] += 1
    missile.meters["whirring"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {setting.place}, {child.id} and {helper.id} began a little quest. "
        f"{setting.detail}"
    )
    world.say(
        f"{child.id} loved curiosity and kept asking what hid behind each door."
    )


def quest_setup(world: World, child: Entity, relic: Relic, setting: Setting) -> None:
    world.say(
        f"The quest was for {relic.phrase}, which belonged in {setting.quest_place}. "
        f"{child.id} wanted to place it on {setting.lap_spot} and see it shine."
    )


def tempt(world: World, child: Entity, missile: ToyMissile) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} found {missile.phrase}. {missile.whirr} {missile.warn} "
        f"For one bright breath, it looked like the perfect trick for a quest."
    )


def warn(world: World, helper: Entity, child: Entity, missile: ToyMissile, relic: Relic) -> None:
    world.say(
        f'{helper.id} touched {helper.pronoun("possessive")} lap and said, '
        f'"Not that way. A {missile.label} should not fly near a lap, and '
        f'{relic.label} could be knocked away."'
    )


def launch(world: World, child: Entity, missile_ent: Entity, missile: ToyMissile) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"I only want to try once," {child.id} said, and let the {missile.label} go.'
    )
    _launch(world, missile_ent)


def hush(world: World, helper: Entity, child: Entity) -> None:
    world.say(
        f"{helper.id} rose quickly, caught the toy before it could bounce far, "
        f"and reminded {child.id} to keep the quest gentle."
    )


def rescue(world: World, helper: Entity, relic: Relic, setting: Setting) -> None:
    world.get("room").meters["tense"] = 0.0
    world.say(
        f"{helper.id} took a lantern from the shelf and set it beside "
        f"{relic.at_risk}. The glow was calm, and the lap stayed safe."
    )
    world.say(
        f"Together they found the missing charm, tucked it into {setting.lap_spot}, "
        f"and finished the quest without any flying trouble."
    )


def lesson(world: World, child: Entity, helper: Entity, missile: ToyMissile) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{helper.id} smiled and said, 'Curiosity is good when it listens. "
        f"{missile.label} are for rolling, not for indoor quests.'"
    )
    world.say(
        f"{child.id} nodded, hugged the lantern, and promised to ask before "
        f"any toy started to soar."
    )


def tell(setting: Setting, relic: Relic, missile: ToyMissile, helper: Helper,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_gender: str = "boy", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    guide = world.add(Entity(id=helper.id, kind="character", type=helper_gender, role="helper"))
    room = world.add(Entity(id="room", kind="thing", type="room", label="the room"))
    missile_ent = world.add(Entity(id="missile", kind="thing", type="toy", label=missile.label, launches=True))
    relic_ent = world.add(Entity(id="relic", kind="thing", type="relic", label=relic.label, risky=relic.fragile))
    lantern = world.add(Entity(id="lantern", kind="thing", type="tool", label="lantern", safe_light=True))

    intro(world, child, guide, setting)
    quest_setup(world, child, relic, setting)
    world.para()
    tempt(world, child, missile)
    warn(world, guide, child, missile, relic)

    if delay == 0:
        world.say(f"{child.id} paused.")
        rescue(world, guide, relic, setting)
    else:
        launch(world, child, missile_ent, missile)
        world.para()
        hush(world, guide, child)
        rescue(world, guide, relic, setting)
        lesson(world, child, guide, missile)

    world.facts.update(
        child=child, helper=guide, room=room, missile_ent=missile_ent,
        relic_ent=relic_ent, lantern=lantern, setting=setting, relic=relic,
        missile=missile, helper_cfg=helper, delay=delay,
        outcome="contained" if delay else "averted",
    )
    return world


SETTINGS = {
    "hall": Setting("hall", "the old hall", "Dusty banners hung high, and the floor shone like calm water.", "the map niche", "a soft lap"),
    "library": Setting("library", "the little library", "Tall shelves made a quiet maze for whispered questions.", "the atlas shelf", "a reading lap"),
    "garden": Setting("garden", "the moon garden", "Moonflowers opened like tiny cups, and every path felt secret.", "the stone bench", "a warm lap"),
}

RELICS = {
    "key": Relic("key", "a silver key", "a silver key", "the lap"),
    "pebble": Relic("pebble", "a bright pebble", "a bright pebble", "the lap"),
    "note": Relic("note", "a folded note", "a folded note", "the lap"),
}

MISSILES = {
    "toy": ToyMissile("toy", "toy missile", "a toy missile", "Whirr!", "It buzzed with silly bravado.", 2, 3),
    "cork": ToyMissile("cork", "cork missile", "a cork missile", "Zip!", "It wanted to zip somewhere fast.", 1, 2),
}

HELPERS = {
    "quester": Helper("Quest", "Quest", "Quest", "guide the search", "Stay calm", 2, 3),
    "curious": Helper("Curiosity", "Curiosity", "Curiosity", "slow the step", "Ask first", 1, 3),
    "fable": Helper("Fable", "Fable", "Fable", "tell the lesson", "Softly now", 2, 3),
}

GIRL_NAMES = ["Mina", "Luna", "Tia", "Ivy", "Nora", "Lena"]
BOY_NAMES = ["Owen", "Ezra", "Noah", "Milo", "Finn", "Jace"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for rid, r in RELICS.items():
            for mid, m in MISSILES.items():
                for hid, h in HELPERS.items():
                    if hazard_at_risk(m, r):
                        combos.append((sid, rid, mid, hid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    relic: str
    missile: str
    helper: str
    child_name: str
    child_gender: str
    helper_gender: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "curiosity": [("What is curiosity?", "Curiosity is the wish to learn and find out new things. It helps you ask questions and explore safely.")],
    "quest": [("What is a quest?", "A quest is a special search for something important. In stories, a quest often has a goal and a lesson.")],
    "lap": [("What is a lap?", "A lap is the top of your legs when you are sitting down. It is a cozy place for reading or holding something safely.")],
    "missile": [("What is a missile?", "A missile is something made to fly fast. A toy with that shape is not a good choice near people or furniture.")],
    "lantern": [("What is a lantern?", "A lantern gives light without needing to fly or spark. It helps people see in the dark safely.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story for a young child that includes the words "lap" and "missile" and features Quest and Curiosity.',
        f"Tell a short quest story where {f['child'].id} and {f['helper'].id} search for {f['relic'].label}, but Curiosity tempts them to use a missile-shaped toy near a lap.",
        f"Write a gentle fable about a child whose curiosity is guided into a safer choice during a quest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, relic, missile = f["child"], f["helper"], f["relic"], f["missile"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who went on a little quest together. {child.id} was the curious one, and {helper.id} helped keep the quest safe."),
        ("What were they searching for?", f"They were searching for {relic.label}. The quest mattered because the missing thing belonged back in its place."),
        ("Why did the helper warn about the toy?", f"{helper.id} warned because a {missile.label} can fly fast and should not be used near a lap. That kind of toy can knock things over and turn a quiet search into a scary moment."),
    ]
    if f["outcome"] == "averted":
        qa.append(("How did the story end?", f"It ended safely, with no toy launch at all. The child paused, listened, and the quest continued with a lantern and a calm lap instead."))
    else:
        qa.append(("How did the story end?", f"It ended safely after a small scare. The toy launched once, but the helper caught the moment, and then they finished the quest with a lantern and a gentle lesson."))
        qa.append(("What did the child learn?", f"{child.id} learned that curiosity is good when it listens first. The child also learned that a missile-shaped toy is for careful play, not for indoor quests."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity", "quest", "lap", "missile", "lantern"}
    out = []
    for k in ["curiosity", "quest", "lap", "missile", "lantern"]:
        out.extend(KNOWLEDGE[k])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.safe_light:
            bits.append("safe_light=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hall", "key", "toy", "quester", "Mina", "girl", "boy", 1),
    StoryParams("library", "note", "cork", "curious", "Owen", "boy", "girl", 1),
    StoryParams("garden", "pebble", "toy", "fable", "Luna", "girl", "boy", 0),
]


def explain_rejection(missile: ToyMissile, relic: Relic) -> str:
    if not hazard_at_risk(missile, relic):
        return "(No story: this toy and relic do not create a believable lap-safety problem.)"
    return "(No story: the storyworld needs a real risk near a lap so the quest can turn into a clear lesson.)"


def outcome_of(params: StoryParams) -> str:
    return "averted" if params.delay == 0 else "contained"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("fragile", rid))
    for mid, m in MISSILES.items():
        lines.append(asp.fact("missile", mid))
        if m.launches:
            lines.append(asp.fact("launches", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, HELPERS[hid].sense))
        lines.append(asp.fact("power", hid, HELPERS[hid].power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(M, R) :- missile(M), launches(M), relic(R), fragile(R).
sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
valid(S, R, M, H) :- setting(S), relic(R), missile(M), helper(H), hazard(M, R).
"""

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) == {k for k, v in HELPERS.items() if v.sense >= SENSE_MIN}:
        print("OK: sensible helpers match.")
    else:
        rc = 1
        print("MISMATCH in sensible helpers.")
    # smoke test normal generation
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, relic=None, missile=None, helper=None,
            child_name=None, child_gender=None, helper_gender=None, delay=None
        ), random.Random(7)))
        assert sample.story.strip()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like quest storyworld with curiosity, a lap, and a missile.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--missile", choices=MISSILES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.relic is None or c[1] == args.relic)
              and (args.missile is None or c[2] == args.missile)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, rid, mid, hid = rng.choice(sorted(combos))
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    if args.missile and args.relic and not hazard_at_risk(MISSILES[args.missile], RELICS[args.relic]):
        raise StoryError(explain_rejection(MISSILES[args.missile], RELICS[args.relic]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    return StoryParams(sid, rid, mid, hid, child_name, child_gender, helper_gender, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], RELICS[params.relic], MISSILES[params.missile], HELPERS[params.helper],
                 params.child_name, params.child_gender, params.helper_gender, params.delay)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible helpers: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.helper} and {p.missile} in {p.setting} ({outcome_of(p)})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
