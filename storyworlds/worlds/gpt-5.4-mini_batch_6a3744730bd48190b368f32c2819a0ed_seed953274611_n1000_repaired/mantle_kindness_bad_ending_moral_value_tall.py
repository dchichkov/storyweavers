#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mantle_kindness_bad_ending_moral_value_tall.py
===============================================================================

A small standalone storyworld for a tall-tale-style moral story about
kindness, a fireplace mantle, and a bad ending that teaches caution.

Premise
-------
A child notices a weary traveler on a stormy night and wants to help.
The child offers warmth and shelter near the mantle, but kindness without
care becomes trouble. The ending is sad: something precious is lost, yet the
moral is clear -- kindness matters, and so does thinking first.

This world intentionally supports a *bad ending* branch. It is not a bug:
the point is to tell a complete story where a good heart meets a poor choice
and the consequence becomes the lesson.

The script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven narration
- Python reasonableness gate plus inline ASP twin
- prompts, story QA, and world QA from simulated state
- --verify runs parity checks and a smoke story generation
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MIN_KINDNESS = 1


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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    weather: str
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
    kind: str
    safe: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Risk:
    id: str
    label: str
    phrase: str
    can_break: bool = True
    can_smoke: bool = False
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    safe: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    charm: str
    risk: str
    remedy: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "storm": Setting("storm", "a lonely cabin by the road", "windy", "fierce"),
    "snow": Setting("snow", "a pine cabin under the drifts", "snowy", "bright"),
    "prairie": Setting("prairie", "a little ranch house", "dry", "wide"),
}

CHARMS = {
    "candle": Charm("candle", "candle", "a little candle", "light"),
    "tea": Charm("tea", "tea kettle", "a steaming kettle of tea", "warmth"),
    "quilt": Charm("quilt", "quilt", "a patched quilt", "warmth"),
}

RISKS = {
    "mantle": Risk("mantle", "mantle", "the mantle above the hearth", can_break=True, can_smoke=False),
    "glass": Risk("glass", "glass lamp", "the glass lamp by the wall", can_break=True, can_smoke=True),
    "bread": Risk("bread", "bread loaf", "the bread loaf cooling nearby", can_break=False, can_smoke=True),
}

REMEDIES = {
    "wait": Remedy("wait", "wait", "waited for the fire to calm", power=0, sense=3),
    "cover": Remedy("cover", "cover", "covered the lamp with a tin pan", power=2, sense=3),
    "snuff": Remedy("snuff", "snuff", "snuffed the candle at once", power=4, sense=4),
    "water": Remedy("water", "water", "dashed water over the flames", power=1, sense=1),
}

GIRL_NAMES = ["Mabel", "June", "Ruby", "Ivy", "Nell", "Sadie"]
BOY_NAMES = ["Rufus", "Eli", "Beck", "Hank", "Owen", "Bo"]
HELPER_NAMES = ["Mina", "Clint", "Tess", "Wade", "Nora", "Jeb"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CHARMS:
            for r in RISKS:
                if c == "candle" and r == "mantle":
                    out.append((s, c, r))
                elif c in {"tea", "quilt"} and r in {"mantle", "glass"}:
                    out.append((s, c, r))
    return out


def reasonableness_gate(charm: Charm, risk: Risk) -> bool:
    return (charm.id == "candle" and risk.id == "mantle") or (charm.id in {"tea", "quilt"} and risk.id in {"mantle", "glass"})


def recommended_remedy(risk: Risk) -> Remedy:
    return REMEDIES["snuff"] if risk.id == "mantle" else REMEDIES["cover"]


def fire_after_delay(risk: Risk, delay: int) -> int:
    base = 3 if risk.id == "mantle" else 2
    return base + delay


def can_contain(remedy: Remedy, risk: Risk, delay: int) -> bool:
    return remedy.power >= fire_after_delay(risk, delay)


def _r_soot(world: World) -> list[str]:
    out = []
    if world.get("risk").meters["smoke"] < THRESHOLD:
        return out
    if ("soot",) in world.fired:
        return out
    world.fired.add(("soot",))
    world.get("child").memes["fear"] += 1
    world.get("helper").memes["worry"] += 1
    out.append("__smoke__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _r_soot(world):
            changed = True
            if not s.startswith("__"):
                out.append(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_badness(world: World, charm: Charm, risk: Risk) -> dict:
    sim = world.copy()
    simulate_choice(sim, charm, risk, narrate=False)
    return {"smoke": sim.get("risk").meters["smoke"], "breaks": sim.get("risk").meters["broken"]}


def setup(world: World, child: Entity, helper: Entity, parent: Entity, charm: Charm, risk: Risk) -> None:
    child.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"On a night when the wind could whistle a tune through a keyhole, {child.id} and {helper.id} lived in {world.setting.place}. "
        f"{world.setting.place.capitalize()} was so small the shadows seemed to sit down and warm their boots."
    )
    world.say(
        f"{child.id} loved {charm.phrase}, and on the mantle sat {risk.phrase}, looking as important as a sheriff's badge."
    )


def temptation(world: World, child: Entity, charm: Charm, helper: Entity, risk: Risk) -> None:
    pred = predict_badness(world, charm, risk)
    world.facts["predicted_smoke"] = pred["smoke"]
    world.facts["predicted_breaks"] = pred["breaks"]
    world.say(
        f"When the storm began to rattle the windows, {child.id} noticed the dark above the hearth. "
        f'"We ought to put {charm.label} by the mantle," {child.id} said, "so the room feels kinder."'
    )
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} scratched {helper.pronoun("possessive")} chin. "{child.id}, that may seem kind, but {risk.label} is a fool to trust near heat."'
    )


def choose_kindness(world: World, child: Entity, helper: Entity, charm: Charm) -> None:
    child.memes["kindness"] += 1
    world.say(
        f"But {child.id} had a heart as big as the moon, and {child.id} decided kindness was the finest rope in the county. "
        f"{child.id} carried {charm.phrase} closer anyway."
    )


def simulate_choice(world: World, charm: Charm, risk: Risk, narrate: bool = True) -> None:
    risk_ent = world.get("risk")
    if charm.id == "candle":
        risk_ent.meters["smoke"] += 1
    else:
        risk_ent.meters["smoke"] += 0.5
    if risk.can_break:
        risk_ent.meters["broken"] += 1
    propagate(world, narrate=narrate)


def accident(world: World, parent: Entity, charm: Charm, risk: Risk) -> None:
    simulate_choice(world, charm, risk, narrate=False)
    world.say(
        f"{charm.label_word.capitalize()} light touched the {risk.label}, and the whole business turned topsy-turvy. "
        f"A lick of smoke climbed the wall like a gray cat."
    )
    world.say(f'"{parent.label_word.capitalize()}!" somebody shouted, but the trouble had already begun.')


def rescue_fail(world: World, parent: Entity, remedy: Remedy, risk: Risk) -> None:
    world.say(
        f"{parent.label_word.capitalize()} came running and {remedy.phrase}, but the flames had the upper hand."
    )
    world.say(
        f"The {risk.label} cracked, the room filled with smoke, and the mantle wore a black scar as long as a riverboat."
    )


def escape_and_lesson(world: World, parent: Entity, child: Entity, helper: Entity, charm: Charm, risk: Risk) -> None:
    child.memes["fear"] += 1
    helper.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hustled them outside into the cold, where the wind pinched their noses red. "
        f"They stood in the snow and watched the cabin cough gray smoke into the night."
    )
    world.say(
        f"For once, even the tall tale had to sit down. {child.id} learned that a kind wish can still make a bad ending if it forgets to be careful."
    )


def tell(setting: Setting, charm: Charm, risk: Risk, remedy: Remedy,
         child_name: str = "Mabel", child_gender: str = "girl",
         helper_name: str = "Rufus", helper_gender: str = "boy",
         parent_type: str = "mother", delay: int = 1) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="risk", kind="thing", type=risk.id, label=risk.label))
    world.facts["setting"] = setting
    world.facts["charm"] = charm
    world.facts["risk"] = risk
    world.facts["remedy"] = remedy
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["parent"] = parent
    world.facts["delay"] = delay

    setup(world, child, helper, parent, charm, risk)
    world.para()
    temptation(world, child, charm, helper, risk)
    choose_kindness(world, child, helper, charm)
    world.para()
    accident(world, parent, charm, risk)
    rescue_fail(world, parent, remedy, risk)
    escape_and_lesson(world, parent, child, helper, charm, risk)

    world.facts["outcome"] = "bad"
    world.facts["moral"] = "kindness matters, but kindness also needs care"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale-style story for a 3-to-5-year-old that includes the word "mantle" and ends with a sad lesson about kindness.',
        f"Tell a story where {f['child'].id} tries to be kind near the mantle, but the choice goes wrong and the ending is bad.",
        f'Write a small moral story with a fireplace, a mantle, and a lesson that kindness should also be careful.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    charm: Charm = f["charm"]
    risk: Risk = f["risk"]
    remedy: Remedy = f["remedy"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and {parent.label_word}. They are the ones who face the storm and the mantle trouble."),
        ("What did {0} want to do?".format(child.id),
         f"{child.id} wanted to be kind and put {charm.phrase} near the mantle so the room would feel warmer and nicer."),
        ("Why did the helper warn {0}?".format(child.id),
         f"{helper.id} warned {child.id} because {risk.phrase} was sitting too near the heat. A kind idea can still turn unsafe when it gets too close to the fire."),
        ("How did the story end?",
         f"It ended badly: smoke filled the cabin, the mantle was marked black, and the family had to hurry outside into the cold."),
        ("What moral did the story teach?",
         "The moral is that kindness matters, but kindness also needs care. A good heart should still think before acting.")
    ]
    if f["outcome"] == "bad":
        qa.append((
            "Could the grown-up fix everything in time?",
            f"No. {parent.label_word.capitalize()} came running with {remedy.phrase}, but it was too late to save the room from smoke and damage."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What is a mantle?",
         "A mantle is the shelf or ledge above a fireplace. People sometimes set things on it, but it should stay away from heat."),
        ("Why is smoke dangerous?",
         "Smoke can make it hard to breathe and can fill a room very fast. That is why people try to get outside and call for help."),
        ("What does kindness mean?",
         "Kindness means caring about someone and trying to help them. It is good, but it should still be thoughtful and safe."),
    ]


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="storm", charm="candle", risk="mantle", remedy="water", child="Mabel", child_gender="girl", helper="Rufus", helper_gender="boy", parent="mother", seed=1),
    StoryParams(setting="snow", charm="quilt", risk="glass", remedy="cover", child="Bo", child_gender="boy", helper="Nora", helper_gender="girl", parent="father", seed=2),
]


def explain_rejection(charm: Charm, risk: Risk) -> str:
    return f"(No story: {charm.label} near {risk.label} does not make a fitting tall-tale trouble.)"


def outcome_of(params: StoryParams) -> str:
    return "bad"


def valid_story_params(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.charm in CHARMS and params.risk in RISKS and params.remedy in REMEDIES


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.safe:
            lines.append(asp.fact("safe_charm", cid))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if r.can_break:
            lines.append(asp.fact("breakable", rid))
    for mid, m in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("power", mid, m.power))
    lines.append(asp.fact("min_kindness", MIN_KINDNESS))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,R) :- setting(S), charm(C), risk(R).
bad(C,R) :- charm(C), risk(R), C = candle, R = mantle.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combos gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, charm=None, risk=None, remedy=None, child=None, child_gender=None, helper=None, helper_gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke story generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale moral storyworld about kindness, a mantle, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    charm = args.charm or rng.choice(list(CHARMS))
    risk = args.risk or rng.choice(list(RISKS))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    if not valid_story_params(StoryParams(setting=setting, charm=charm, risk=risk, remedy=remedy, child="x", child_gender="girl", helper="y", helper_gender="boy", parent="mother")):
        raise StoryError("Invalid params.")
    if not reasonableness_gate(CHARMS[charm], RISKS[risk]):
        raise StoryError(explain_rejection(CHARMS[charm], RISKS[risk]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    helper_pool = [n for n in HELPER_NAMES if n not in child_pool]
    return StoryParams(
        setting=setting,
        charm=charm,
        risk=risk,
        remedy=remedy,
        child=args.child or rng.choice(child_pool),
        child_gender=child_gender,
        helper=args.helper or rng.choice(helper_pool),
        helper_gender=helper_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.charm not in CHARMS or params.risk not in RISKS or params.remedy not in REMEDIES:
        raise StoryError("Unknown params.")
    if not reasonableness_gate(CHARMS[params.charm], RISKS[params.risk]):
        raise StoryError(explain_rejection(CHARMS[params.charm], RISKS[params.risk]))
    world = tell(SETTINGS[params.setting], CHARMS[params.charm], RISKS[params.risk], REMEDIES[params.remedy], params.child, params.child_gender, params.helper, params.helper_gender, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
