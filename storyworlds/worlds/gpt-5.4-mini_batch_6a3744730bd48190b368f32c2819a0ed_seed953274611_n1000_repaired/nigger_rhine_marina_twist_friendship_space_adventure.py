#!/usr/bin/env python3
"""
Standalone storyworld: a tiny space-dock friendship tale with a mid-story twist.

This world follows the shared Storyweavers contract:
- stdlib-only script
- StoryParams + parser + resolve_params + generate + emit + main
- world model with meters and memes
- Python reasonableness gate plus inline ASP twin
- Q&A generated from simulated world state, not from rendered prose
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    dark_place: str
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
class Twist:
    id: str
    label: str
    reveal: str
    change: str
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
class Friendship:
    id: str
    label: str
    comfort: str
    repair: str
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
class Tool:
    id: str
    label: str
    safe: bool
    light: bool = False
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
class Hazard:
    id: str
    label: str
    risky: bool
    echoes: str
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
    theme: str
    twist: str
    friendship: str
    tool: str
    hazard: str
    captain: str
    captain_gender: str
    partner: str
    partner_gender: str
    guide: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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
    ship = world.entities.get("ship")
    if ship and ship.meters["risk"] >= THRESHOLD and ("worry", "ship") not in world.fired:
        world.fired.add(("worry", "ship"))
        for ent in list(world.entities.values()):
            if ent.role in {"captain", "partner"}:
                ent.memes["worry"] += 1
        out.append("__twist__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


CAUSAL_RULES = [Rule("worry", _r_worry)]


THEMES = {
    "space": Theme(
        id="space",
        scene="a bright space dock",
        rig="The dock lights blinked blue, a small map glowed on the table, and the window showed the stars like tiny silver seeds.",
        title_a="Captain",
        title_b="Pilot",
        goal="the old station at the edge of the Rhine route",
        dark_place="the shadowy bay under the marina lights",
        ending_image="the dock lights and the star map shining together",
    )
}

TWISTS = {
    "twist": Twist(
        id="twist",
        label="Twist",
        reveal="the route was not broken after all",
        change="the missing path was hidden behind the old marina gate",
        tags={"twist"},
    )
}

FRIENDSHIPS = {
    "friendship": Friendship(
        id="friendship",
        label="Friendship",
        comfort="they trusted each other and listened closely",
        repair="their friendship made it easy to try the safe plan together",
        tags={"friendship"},
    )
}

TOOLS = {
    "scanner": Tool(id="scanner", label="a little scanner", safe=True, light=False, tags={"scanner"}),
    "lamp": Tool(id="lamp", label="a soft lamp", safe=True, light=True, tags={"lamp", "light"}),
    "beacon": Tool(id="beacon", label="a marina beacon", safe=True, light=True, tags={"beacon", "light"}),
}

HAZARDS = {
    "storm": Hazard(id="storm", label="storm clouds", risky=True, echoes="the sky kept rolling and hiding the path", tags={"storm"}),
    "drift": Hazard(id="drift", label="drifting debris", risky=True, echoes="the floating bits made the route hard to follow", tags={"drift"}),
}

GIRL_NAMES = ["Mina", "Lina", "Nova", "Tia", "Ria"]
BOY_NAMES = ["Kian", "Arlo", "Jace", "Rin", "Tavi"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in THEMES:
        for tw in TWISTS:
            for fr in FRIENDSHIPS:
                combos.append((tid, tw, fr))
    return combos


def hazard_reasonable(hazard: Hazard) -> bool:
    return hazard.risky


def tool_reasonable(tool: Tool) -> bool:
    return tool.safe


def best_tool() -> Tool:
    return TOOLS["beacon"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny space-dock friendship storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--friendship", choices=FRIENDSHIPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not tool_reasonable(TOOLS[args.tool]):
        raise StoryError("This tool is too risky for a child-facing space-dock story.")
    if args.hazard and not hazard_reasonable(HAZARDS[args.hazard]):
        raise StoryError("That hazard is not strong enough to make a real story turn.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.twist is None or c[1] == args.twist)
              and (args.friendship is None or c[2] == args.friendship)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, twist, friendship = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(list(TOOLS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if captain_gender == "girl" else "girl")
    captain_pool = GIRL_NAMES if captain_gender == "girl" else BOY_NAMES
    partner_pool = [n for n in (GIRL_NAMES if partner_gender == "girl" else BOY_NAMES)]
    captain = args.captain or rng.choice(captain_pool)
    partner = args.partner or rng.choice([n for n in partner_pool if n != captain])
    guide = args.guide or "Marina"
    return StoryParams(theme=theme, twist=twist, friendship=friendship, tool=tool, hazard=hazard,
                       captain=captain, captain_gender=captain_gender,
                       partner=partner, partner_gender=partner_gender, guide=guide)


def _setup_world(params: StoryParams) -> World:
    world = World()
    theme = THEMES[params.theme]
    twist = TWISTS[params.twist]
    friendship = FRIENDSHIPS[params.friendship]
    tool = TOOLS[params.tool]
    hazard = HAZARDS[params.hazard]

    captain = world.add(Entity(id=params.captain, kind="character", type=params.captain_gender, role="captain"))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_gender, role="partner"))
    guide = world.add(Entity(id=params.guide, kind="character", type="woman", role="guide", label="Marina"))
    ship = world.add(Entity(id="ship", type="ship", label="the little shuttle"))
    ship.meters["risk"] = 0.0

    world.facts["theme"] = theme
    world.facts["twist"] = twist
    world.facts["friendship"] = friendship
    world.facts["tool"] = tool
    world.facts["hazard"] = hazard
    world.facts["captain"] = captain
    world.facts["partner"] = partner
    world.facts["guide"] = guide
    world.facts["ship"] = ship

    captain.memes["trust"] += 1
    partner.memes["trust"] += 1
    return world


def tell(world: World) -> None:
    f = world.facts
    theme: Theme = f["theme"]
    twist: Twist = f["twist"]
    friendship: Friendship = f["friendship"]
    tool: Tool = f["tool"]
    hazard: Hazard = f["hazard"]
    captain: Entity = f["captain"]
    partner: Entity = f["partner"]
    guide: Entity = f["guide"]
    ship: Entity = f["ship"]

    world.say(
        f"{captain.id} and {partner.id} walked onto {theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.title_a} {captain.id} and {theme.title_b} {partner.id}!" '
        f"{captain.id} called. They were chasing {theme.goal}."
    )
    world.para()
    world.say(
        f"But {hazard.label} gathered near {theme.dark_place}, and the route felt hard to trust. "
        f"{hazard.echoes}"
    )
    world.say(
        f"{partner.id} touched {tool.label} and said, \"We need a safe way to see.\" "
        f"{friendship.comfort.capitalize()}."
    )

    ship.meters["risk"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"Then {guide.label_word if guide.label else guide.id} Marina arrived with a twist. "
        f"{twist.reveal.capitalize()}."
    )
    world.say(
        f"She pointed to {twist.change} and showed them {best_tool().label} instead of a risky spark."
    )
    world.say(
        f"{friendship.repair.capitalize()}. Together they used the safe light and kept going."
    )
    world.para()
    world.say(
        f"In the end, {theme.ending_image} led them forward, and the dock looked warm and brave."
    )
    captain.memes["joy"] += 1
    partner.memes["joy"] += 1
    captain.memes["trust"] += 1
    partner.memes["trust"] += 1
    ship.meters["risk"] = 0.0
    world.facts["ending"] = "safe"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a child that includes the words "marina", "Rhine", and "Twist".',
        f"Tell a friendship story where {f['captain'].id} and {f['partner'].id} explore a space dock, then a twist helps them choose a safer path.",
        f"Write a gentle space story about a marina, a route near the Rhine, and two friends who stay brave together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain: Entity = f["captain"]
    partner: Entity = f["partner"]
    theme: Theme = f["theme"]
    twist: Twist = f["twist"]
    friendship: Friendship = f["friendship"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {captain.id} and {partner.id}, who explore a space dock together. Marina helps them when the path changes.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the route was not really lost. Marina showed them a hidden way behind the old gate, so they could keep going safely.",
        ),
        QAItem(
            question="How did friendship matter?",
            answer=f"{friendship.comfort.capitalize()} It helped them listen to each other, stay calm, and choose the safe light together.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the dock shining bright and the friends still together. The ending image proves they kept moving by safe light instead of worry.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marina?",
            answer="A marina is a place where boats or small ships can stop and rest. In a space story, it can feel like a dock with safe lights and paths.",
        ),
        QAItem(
            question="What does friendship help friends do?",
            answer="Friendship helps friends listen, share ideas, and help each other when things get confusing. It makes a hard choice feel less scary.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what the characters think is happening. It gives the story a new direction without making it confusing.",
        ),
        QAItem(
            question="Why do explorers need lights in the dark?",
            answer="Lights help explorers see where they are going and avoid danger. In space, safe light keeps the path clear without using anything risky.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    return "\n".join(lines)


ASP_RULES = r"""
valid(T,W,F) :- theme(T), twist(W), friendship(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for fid in FRIENDSHIPS:
        lines.append(asp.fact("friendship", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python combo logic.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, twist=None, friendship=None,
                                                             tool=None, hazard=None, captain=None,
                                                             captain_gender=None, partner=None,
                                                             partner_gender=None, guide=None),
                                         random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in (("theme", THEMES), ("twist", TWISTS), ("friendship", FRIENDSHIPS),
                       ("tool", TOOLS), ("hazard", HAZARDS)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    if params.tool and not TOOLS[params.tool].safe:
        raise StoryError("The chosen tool is too risky for this gentle storyworld.")
    if params.hazard and not HAZARDS[params.hazard].risky:
        raise StoryError("The chosen hazard is too weak for a real twist.")

    world = _setup_world(params)
    tell(world)
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


CURATED = [
    StoryParams(theme="space", twist="twist", friendship="friendship", tool="scanner", hazard="storm",
                captain="Mina", captain_gender="girl", partner="Rin", partner_gender="boy", guide="Marina"),
    StoryParams(theme="space", twist="twist", friendship="friendship", tool="lamp", hazard="drift",
                captain="Nova", captain_gender="girl", partner="Kian", partner_gender="boy", guide="Marina"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.twist is None or c[1] == args.twist)
              and (args.friendship is None or c[2] == args.friendship)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, twist, friendship = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(list(TOOLS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or ("boy" if captain_gender == "girl" else "girl")
    captain_pool = GIRL_NAMES if captain_gender == "girl" else BOY_NAMES
    partner_pool = GIRL_NAMES if partner_gender == "girl" else BOY_NAMES
    captain = args.captain or rng.choice(captain_pool)
    partner = args.partner or rng.choice([n for n in partner_pool if n != captain])
    guide = args.guide or "Marina"
    return StoryParams(theme=theme, twist=twist, friendship=friendship, tool=tool, hazard=hazard,
                       captain=captain, captain_gender=captain_gender,
                       partner=partner, partner_gender=partner_gender, guide=guide)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for t, w, f in asp_valid_combos():
            print(f"  {t} {w} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
