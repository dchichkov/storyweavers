#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tart_problem_solving_inner_monologue_bad_ending.py
===================================================================================

A standalone story world about a small space-station snack problem: a child wants
to eat a tart during a tiny mission, thinks through a fix, tries one sensible
plan, and still ends up with a bad ending when the problem beats them anyway.

The domain is intentionally small and classical:
- a child, a helper, a station room, a tart, a spill/crumb hazard, and a simple fix
- state changes are physical (meters) and emotional (memes)
- the story is driven from world state rather than rendered as a frozen paragraph
- the narration includes inner monologue, problem solving, and a bad ending

The story is child-facing, concrete, and space-adventure flavored.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
    place: str
    airlock: str
    view: str
    dark_spot: str
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
class Tart:
    id: str
    label: str
    phrase: str
    smell: str
    spill: str
    crumbly: bool = True
    edible: bool = True
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
class Fix:
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
    tart: str
    fix: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None
    delay: int = 1
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    if not ship:
        return out
    for e in list(world.entities.values()):
        if e.meters["sticky"] >= THRESHOLD and ("sticky", e.id) not in world.fired:
            world.fired.add(("sticky", e.id))
            ship.meters["mess"] += 1
            out.append("__mess__")
    return out


def _r_sad(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["sticky"] >= THRESHOLD and e.role == "child":
            if ("sad", e.id) not in world.fired:
                world.fired.add(("sad", e.id))
                e.memes["worry"] += 1
                e.memes["hope"] += 1
                out.append("__sad__")
    return out


CAUSAL_RULES = [Rule("sticky", "physical", _r_sticky), Rule("sad", "social", _r_sad)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, tart in TARTS.items():
            for fid, fix in FIXES.items():
                if tart.crumbly and fix.sense >= SENSE_MIN:
                    combos.append((sid, tid, fid))
    return combos


def hazard_at_risk(tart: Tart) -> bool:
    return tart.crumbly


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def is_contained(fix: Fix, delay: int) -> bool:
    return fix.power >= 2 + delay


def outcome_of(params: StoryParams) -> str:
    return "bad"  # this world intentionally always ends badly


def _inner_thought(child: Entity, tart: Tart, setting: Setting) -> str:
    return (
        f'{child.id} thought, "If I carry {tart.phrase} through the '
        f'{setting.airlock}, maybe I can keep it steady."'
    )


def _plan(child: Entity, helper: Entity, fix: Fix, tart: Tart) -> str:
    return (
        f'{child.id} blinked at {helper.id} and thought of a plan: '
        f'{fix.qa_text.replace("{target}", tart.label)}.'
    )


def tell(setting: Setting, tart: Tart, fix: Fix, child: str, child_gender: str,
         helper: str, helper_gender: str, delay: int) -> World:
    world = World()
    kid = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    pal = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    ship = world.add(Entity(id="ship", kind="thing", type="room", label="the ship"))
    snack = world.add(Entity(id="tart", kind="thing", type="thing", label=tart.label))
    ship.attrs.update(setting=setting.id, place=setting.place)

    kid.memes["hope"] += 1
    pal.memes["care"] += 1
    snack.meters["fresh"] += 1

    world.say(
        f"On the little starship {child} and {helper} drifted through {setting.place}. "
        f"Outside the window, stars blinked over the blue edge of the planet."
    )
    world.say(
        f"{child} had a {tart.phrase} tucked in a shiny box, and it smelled like "
        f"{tart.smell}."
    )

    world.para()
    world.say(
        f"They reached {setting.dark_spot}, where the lights were dim and the deck "
        f"felt quiet."
    )
    world.say(_inner_thought(kid, tart, setting))
    world.say(
        f'{helper} frowned and whispered, "Careful. {tart.label.capitalize()} can '
        f'make a sticky mess if it slips."'
    )

    kid.memes["resolve"] += 1
    world.para()
    world.say(
        f'{child} took a breath. "I can fix this," {kid.pronoun()} thought. '
        f"{_plan(kid, pal, fix, tart)}"
    )
    world.say(
        f'{child} tried {fix.text.replace("{target}", tart.label)}.'
    )
    snack.meters["sticky"] += 1
    propagate(world, narrate=False)

    if not is_contained(fix, delay):
        world.para()
        world.say(
            f"But the plan was too slow. The tart wobbled, slipped, and landed '
            f'by the console."
        )
        world.say(
            f'{tart.label.capitalize()} smeared across the panel, and the ship gave '
            f'an unhappy beep.'
        )
        ship.meters["mess"] += 1
        kid.memes["worry"] += 1
        pal.memes["worry"] += 1

    world.para()
    world.say(
        f"{helper} helped clean up what they could, but the snack was ruined. "
        f"Their mission snack had turned into a sad, sticky splat."
    )
    world.say(
        f"{child} stared at the dark window and thought, "
        f'"Next time, I should ask for a tray before I bring a tart on a space trip."'
    )
    world.say(
        f"The stars kept shining, but the little cabin smelled like {tart.smell} "
        f"and old disappointment."
    )

    world.facts.update(
        child=kid,
        helper=pal,
        setting=setting,
        tart=tart,
        fix=fix,
        delay=delay,
        mess=ship.meters["mess"],
        ruined=True,
        bad=True,
    )
    return world


SETTINGS = {
    "orbit_room": Setting(
        id="orbit_room",
        place="the orbit room",
        airlock="airlock hatch",
        view="a round window with Earth glowing below",
        dark_spot="the corner by the control panel",
    ),
    "cargo_bay": Setting(
        id="cargo_bay",
        place="the cargo bay",
        airlock="cargo door",
        view="stacked crates and a silver ramp",
        dark_spot="the space between two tall crates",
    ),
    "moon_kitchen": Setting(
        id="moon_kitchen",
        place="the moon kitchen",
        airlock="moon hatch",
        view="dusty floor tiles and a tiny flag",
        dark_spot="the shadow under the table",
    ),
}

TARTS = {
    "berry": Tart(
        id="berry",
        label="berry tart",
        phrase="a berry tart",
        smell="sweet berries and warm sugar",
        spill="purple jam",
    ),
    "apple": Tart(
        id="apple",
        label="apple tart",
        phrase="an apple tart",
        smell="baked apples and cinnamon",
        spill="gooey apple filling",
    ),
    "lemon": Tart(
        id="lemon",
        label="lemon tart",
        phrase="a lemon tart",
        smell="bright lemon and crust",
        spill="sticky yellow cream",
    ),
}

FIXES = {
    "tray": Fix(
        id="tray",
        sense=3,
        power=2,
        text="set the tart on a flat tray and carried it with both hands",
        fail="set the tart on a flat tray, but the tray slid anyway",
        qa_text="set the tart on a flat tray and carried it carefully",
        tags={"tray"},
    ),
    "napkin": Fix(
        id="napkin",
        sense=2,
        power=1,
        text="wrapped the tart in a napkin and held it close",
        fail="wrapped the tart in a napkin, but that did not stop the slip",
        qa_text="wrapped the tart in a napkin and tried to hold it steady",
        tags={"napkin"},
    ),
    "slow_steps": Fix(
        id="slow_steps",
        sense=2,
        power=1,
        text="walked as slowly as a moon snail and counted each step",
        fail="walked slowly, but the tart still tipped in the low gravity",
        qa_text="walked as slowly as a moon snail",
        tags={"slow"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Tia", "Nora", "Zia"]
BOY_NAMES = ["Kip", "Oren", "Milo", "Joss", "Rian"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space snack story world with a tart.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tart", choices=TARTS)
    ap.add_argument("--fix", choices=FIXES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tart is None or c[1] == args.tart)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tart, fix = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES + BOY_NAMES) if n != child]
    helper = args.helper or rng.choice(helper_pool)
    return StoryParams(
        setting=setting,
        tart=tart,
        fix=fix,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        delay=1,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small space-adventure story that includes the word "{f["tart"].label}" and an inner monologue.',
        f"Tell a story about {f['child'].id} on a starship who tries to solve a tart problem, but the ending should be bad.",
        f"Write a child-friendly problem-solving story in space where a tart causes trouble and the plan does not fully work.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    tart: Tart = f["tart"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id} and {helper.id} on a small starship. {child.id} is the one thinking through the tart problem.",
        ),
        QAItem(
            question=f"What problem did {child.id} try to solve?",
            answer=f"{child.id} wanted to carry {tart.phrase} through {setting.place} without making a mess. {child.id} tried to use a careful plan, but it was not enough.",
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer=f"The tart slipped and made a sticky mess on the ship. Their idea was too slow for the problem, so the snack was ruined even though they tried to be careful.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tart: Tart = f["tart"]
    setting: Setting = f["setting"]
    out = [
        QAItem(
            question="What is a tart?",
            answer="A tart is a small baked dessert with a crust and a filling. It can be sweet and tasty, but it can also get messy if it tips over.",
        ),
        QAItem(
            question="What is an airlock?",
            answer=f"An airlock is a special door on a spaceship that helps keep air inside. It lets people move between the ship and space without opening everything at once.",
        ),
        QAItem(
            question="What should a person do if a snack might spill in space?",
            answer="They should slow down, use a tray, and ask for help before the snack slides. Careful tools and careful hands help stop a mess.",
        ),
    ]
    return out


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="orbit_room", tart="berry", fix="tray", child="Mina", child_gender="girl", helper="Oren", helper_gender="boy", delay=1),
    StoryParams(setting="cargo_bay", tart="apple", fix="napkin", child="Kip", child_gender="boy", helper="Lina", helper_gender="girl", delay=2),
    StoryParams(setting="moon_kitchen", tart="lemon", fix="slow_steps", child="Tia", child_gender="girl", helper="Joss", helper_gender="boy", delay=1),
]


def explain_rejection() -> str:
    return "(No story: this world needs a crumbly tart and a sensible but too-weak plan.)"


def sensible_fix_ids() -> list[str]:
    return [f.id for f in sensible_fixes()]


ASP_RULES = r"""
% A tart is risky when it is crumbly.
risky(T) :- tart(T), crumbly(T).

% A fix is sensible if its sense score reaches the minimum.
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.

% The ending is bad in this world whenever the tart is risky and the fix is not
% powerful enough for the delay. The story is intentionally a bad ending.
fails(F) :- fix(F), power(F, P), delay(D), needed(N), N = 2 + D, P < N.
outcome(bad) :- risky(T), tart(T), fix(F), fails(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TARTS.items():
        lines.append(asp.fact("tart", tid))
        if t.crumbly:
            lines.append(asp.fact("crumbly", tid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("delay", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(sensible_fix_ids())
    cl = set(asp_sensible())
    if py != cl:
        print("MISMATCH in sensible fixes:")
        print(" python:", sorted(py))
        print(" clingo:", sorted(cl))
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, tart=None, fix=None, child=None, child_gender=None,
            helper=None, helper_gender=None
        ), random.Random(7)))
        assert sample.story
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_smoke_args() -> argparse.Namespace:
    return argparse.Namespace(
        setting=None, tart=None, fix=None, child=None, child_gender=None,
        helper=None, helper_gender=None
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.tart not in TARTS or params.fix not in FIXES:
        raise StoryError("(Invalid params: unknown setting, tart, or fix.)")
    world = tell(
        SETTINGS[params.setting],
        TARTS[params.tart],
        FIXES[params.fix],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
        params.delay,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible fixes:", ", ".join(asp_sensible()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child} and {p.helper} with {p.tart} ({p.setting}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
