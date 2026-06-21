#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hop_weensie_inner_monologue_flashback_transformation_space.py
=============================================================================================

A tiny space-adventure storyworld about a small crew, a nervous little craft,
and a brave change of shape.

Seed words: hop, weensie
Narrative instruments: inner monologue, flashback, transformation
Style: Space Adventure

This world models a child-facing mission in which a weensie scout ship must hop
between small space rocks, remember an earlier lesson, and transform into a new
shape to finish the rescue. The world state drives the story beats:
- the ship's meters track fuel, damage, and transformation
- the pilot's memes track fear, courage, memory, and relief
- a flashback is triggered by a stateful reminder
- the transformation is a concrete mechanical change that unlocks the ending

The story is intentionally small and constraint-checked. Invalid combinations
raise StoryError with a clear reason.

Run it:
    python hop_weensie_inner_monologue_flashback_transformation_space.py
    python hop_weensie_inner_monologue_flashback_transformation_space.py --all
    python hop_weensie_inner_monologue_flashback_transformation_space.py --qa --json
    python hop_weensie_inner_monologue_flashback_transformation_space.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fuel": 0.0, "damage": 0.0, "transform": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "courage": 0.0, "memory": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    sky: str
    hazard: str
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
class Ship:
    id: str
    name: str
    size: str
    can_hop: bool
    can_transform_to: str
    label: str
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
class Mission:
    id: str
    aim: str
    obstacle: str
    rescue: str
    flashback_hint: str
    inner_voice: str
    ending_image: str
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
    mission: Mission
    ship_cfg: Ship
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting, self.mission, self.ship_cfg)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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


def _r_fear(world: World) -> list[str]:
    out = []
    pilot = world.get("pilot")
    ship = world.get("ship")
    if pilot.meters.get("stuck", 0.0) >= THRESHOLD and ship.meters.get("damage", 0.0) < THRESHOLD:
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            pilot.memes["fear"] += 1
            out.append("__inner__")
    return out


def _r_flashback(world: World) -> list[str]:
    out = []
    pilot = world.get("pilot")
    if pilot.memes.get("fear", 0.0) >= THRESHOLD and pilot.memes.get("memory", 0.0) < THRESHOLD:
        sig = ("flashback",)
        if sig not in world.fired:
            world.fired.add(sig)
            pilot.memes["memory"] += 1
            out.append("__flashback__")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    ship = world.get("ship")
    if ship.meters.get("transform", 0.0) >= THRESHOLD and world.get("pilot").memes.get("memory", 0.0) >= THRESHOLD:
        sig = ("transform",)
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["wings"] = 1.0
            out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("flashback", _r_flashback), Rule("transform", _r_transform)]


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


def is_reasonable(ship: Ship, mission: Mission, setting: Setting) -> bool:
    return "space" in setting.tags and "rescue" in mission.tags and ship.can_hop and ship.can_transform_to == "wing-shape"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            for shid, ship in SHIPS.items():
                if is_reasonable(ship, mission, setting):
                    combos.append((sid, mid, shid))
    return combos


def explain_rejection(setting: Setting, mission: Mission, ship: Ship) -> str:
    return (
        f"(No story: this space tale needs a ship that can hop and later transform, "
        f"a rescue mission, and a space setting. Try a ship like {ship.name} if it "
        f"can become wing-shaped, or another valid combination.)"
    )


@dataclass
class StoryParams:
    setting: str
    mission: str
    ship: str
    pilot_name: str
    pilot_gender: str
    helper_name: str
    helper_gender: str
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
    "asteroid_belt": Setting(
        id="asteroid_belt",
        place="the bright asteroid belt",
        sky="a black sky with silver dust",
        hazard="tumbling rocks",
        tags={"space"},
    ),
    "moon_loop": Setting(
        id="moon_loop",
        place="the moon loop",
        sky="a quiet sky over a ring of moons",
        hazard="a drifting debris cloud",
        tags={"space"},
    ),
}

MISSIONS = {
    "rescue_beacon": Mission(
        id="rescue_beacon",
        aim="reach the tiny rescue beacon",
        obstacle="a gap too wide for one hop",
        rescue="bring home the lost drone",
        flashback_hint="once before, the pilot waited too long and missed a chance to help",
        inner_voice="Weensie ship, don't wobble now. One careful hop at a time.",
        ending_image="the beacon blinking safely beside the ship",
        tags={"rescue"},
    ),
    "repair_star": Mission(
        id="repair_star",
        aim="reach the broken star lamp",
        obstacle="a cold drift that kept sliding away",
        rescue="fix the lonely lamp before it went dark",
        flashback_hint="the pilot once watched a small lamp go dark and wished for a better plan",
        inner_voice="Tiny ship, big job. Hop first, think second, breathe always.",
        ending_image="the lamp shining again above the hull",
        tags={"rescue"},
    ),
}

SHIPS = {
    "weensie_hopper": Ship(
        id="weensie_hopper",
        name="Weensie Hopper",
        size="weensie",
        can_hop=True,
        can_transform_to="wing-shape",
        label="little scout ship",
        tags={"space"},
    ),
    "comet_bob": Ship(
        id="comet_bob",
        name="Comet Bob",
        size="small",
        can_hop=True,
        can_transform_to="wing-shape",
        label="small scout ship",
        tags={"space"},
    ),
}

GIRL_NAMES = ["Mina", "Tali", "Nova", "Lina", "Ria"]
BOY_NAMES = ["Finn", "Jory", "Pax", "Arlo", "Beau"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny space adventure storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--pilot")
    ap.add_argument("--pilot-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mission and args.ship:
        setting, mission, ship = SETTINGS[args.setting], MISSIONS[args.mission], SHIPS[args.ship]
        if not is_reasonable(ship, mission, setting):
            raise StoryError(explain_rejection(setting, mission, ship))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mission is None or c[1] == args.mission)
              and (args.ship is None or c[2] == args.ship)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mission, ship = rng.choice(sorted(combos))
    pilot_gender = args.pilot_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if pilot_gender == "girl" else "girl")
    pilot = args.pilot or _pick_name(rng, pilot_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    return StoryParams(
        setting=setting,
        mission=mission,
        ship=ship,
        pilot_name=pilot,
        pilot_gender=pilot_gender,
        helper_name=helper,
        helper_gender=helper_gender,
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mission = MISSIONS[params.mission]
    ship_cfg = SHIPS[params.ship]
    world = World(setting, mission, ship_cfg)
    pilot = world.add(Entity(id=params.pilot_name, kind="character", type=params.pilot_gender, role="pilot"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label=ship_cfg.label, role="ship"))
    beac = world.add(Entity(id="beacon", kind="thing", type="object", label="the beacon"))
    lamp = world.add(Entity(id="lamp", kind="thing", type="object", label="the lamp"))
    target = beac if params.mission == "rescue_beacon" else lamp

    pilot.meters["stuck"] += 1
    pilot.memes["courage"] += 1
    world.say(
        f"{pilot.id} climbed into {ship_cfg.name}, a {ship_cfg.size} little ship with a round nose and bright buttons. "
        f"{helper.id} waved from the dock as the ship drifted into {setting.place}."
    )
    world.say(
        f"The mission was to {mission.aim}, but {mission.obstacle} kept hanging in front of them. "
        f"{mission.inner_voice}"
    )

    world.para()
    world.say(
        f"In {pilot.id}'s head, a small inner monologue whispered: \"I can do this. {ship_cfg.name} is weensie, "
        f"but it is mine, and the stars are not as big as they look.\""
    )
    pilot.memes["fear"] += 1
    if "weensie" in ship_cfg.size:
        pilot.memes["courage"] += 1

    world.para()
    world.say(
        f"Then came a flashback. {mission.flashback_hint}. That memory flickered like a tiny blue window, "
        f"and {pilot.id} remembered to breathe."
    )
    pilot.memes["memory"] += 1
    ship.meters["transform"] += 1
    ship.meters["fuel"] += 1

    world.para()
    world.say(
        f"{helper.id} called, \"Hop now!\" So the little ship made a brave hop, then another. "
        f"It skimmed past the rocks, nearly snagged on the drift, and wobbled right up to the target."
    )
    propagate(world, narrate=False)

    world.para()
    ship.meters["transform"] += 1
    ship.meters["fuel"] -= 0.5
    world.say(
        f"At the edge of the obstacle, {pilot.id} pressed the silver latch. The {ship_cfg.name} began to transform. "
        f"Its sides unfolded into long wings, and its belly stretched flat and sleek like a gliding comet."
    )
    world.say(
        f"\"Now I know,\" {pilot.id} thought. \"I was not too small. I just needed the right shape.\""
    )
    world.say(
        f"With the new wing-shape, the ship slipped through the last gap and reached {target.label}, "
        f"where the rescue could finally begin."
    )
    ship.meters["damage"] = 0.0
    pilot.memes["relief"] += 1

    world.para()
    world.say(
        f"By the end, {mission.rescue}, and the final picture was {mission.ending_image}. "
        f"{pilot.id} and {helper.id} looked out at the stars as if they had grown a little bigger themselves."
    )

    world.facts.update(
        pilot=pilot,
        helper=helper,
        ship=ship,
        target=target,
        setting=setting,
        mission=mission,
        ship_cfg=ship_cfg,
        transformed=ship.meters.get("transform", 0.0) >= THRESHOLD,
        flashed=pilot.memes.get("memory", 0.0) >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story for a young child that includes the words "hop" and "weensie".',
        f"Tell a story where {f['pilot'].id} flies a {f['ship_cfg'].name}, remembers an older lesson in a flashback, and transforms the ship to finish the mission.",
        f"Write a small, brave story about a tiny ship that has an inner monologue, a flashback, and a transformation in space.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pilot: Entity = f["pilot"]
    helper: Entity = f["helper"]
    ship: Entity = f["ship"]
    mission: Mission = f["mission"]
    target: Entity = f["target"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {pilot.id} and {helper.id}, who rode a tiny ship through space to finish a rescue mission. The ship and the people work together to make the ending happen.",
        ),
        QAItem(
            question="Why did the pilot think so hard before the hop?",
            answer=f"{pilot.id} was worried because the ship was weensie and the gap looked too wide. The inner voice helped {pilot.pronoun('object')} stay calm and make the next hop anyway.",
        ),
        QAItem(
            question="What happened in the flashback?",
            answer=f"{pilot.id} remembered an earlier moment when waiting too long caused a chance to slip away. That flashback gave the pilot a better plan for this mission.",
        ),
    ]
    if f.get("transformed"):
        answers.append(
            QAItem(
                question="How did the ship change?",
                answer=f"The ship transformed into a wing-shape, with long sides that spread out like comet wings. That new shape let it glide through the last gap and reach {target.label}.",
            )
        )
    answers.append(
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {mission.ending_image}. The rescue was complete, and the small crew could look at the stars feeling proud and safe.",
        )
    )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to hop in space?",
            answer="To hop in space means to make short, careful jumps from one place to another. A small ship may hop between rocks or platforms when it cannot fly straight through.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory of something that happened earlier. Stories use it when a character remembers a past moment that helps with the present one.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation means something changes shape or becomes something new. In a space story, a ship might unfold into a different form to solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="asteroid_belt", mission="rescue_beacon", ship="weensie_hopper", pilot_name="Mina", pilot_gender="girl", helper_name="Finn", helper_gender="boy"),
    StoryParams(setting="moon_loop", mission="repair_star", ship="comet_bob", pilot_name="Nova", pilot_gender="girl", helper_name="Pax", helper_gender="boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("space_setting", sid))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("rescue_mission", mid))
    for shid, ship in SHIPS.items():
        lines.append(asp.fact("ship", shid))
        if ship.can_hop:
            lines.append(asp.fact("can_hop", shid))
        lines.append(asp.fact("transform_to", shid, ship.can_transform_to))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, Sh) :- setting(S), mission(M), ship(Sh), space_setting(S), rescue_mission(M), can_hop(Sh), transform_to(Sh, wing-shape).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python gate:")
        if a - p:
            print("  only in clingo:", sorted(a - p))
        if p - a:
            print("  only in python:", sorted(p - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mission=None, ship=None, pilot=None, pilot_gender=None, helper=None, helper_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print("MISMATCH: generation smoke test failed:", e)
    return rc


def resolve_params_for_smoke() -> StoryParams:
    return CURATED[0]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mission not in MISSIONS or params.ship not in SHIPS:
        raise StoryError("Invalid params: unknown setting, mission, or ship.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
