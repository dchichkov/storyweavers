#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/quadruple_aim_clip_sharing_dialogue_superhero_story.py
======================================================================================

A standalone storyworld for a tiny superhero domain: one child hero, a tricky
mission, a shared tool, and a rescue that depends on dialogue, sharing, and a
well-aimed clip.

The seed words are woven into the simulation itself:
- quadruple: a four-part rescue plan
- aim: a beam, gadget, or gesture must be aimed carefully
- clip: a small fastening clip keeps the shared gear in place

The world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- forward causal rules
- a Python reasonableness gate plus an inline ASP twin
- three QA sets grounded in simulated state
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
class Mission:
    id: str
    scene: str
    base: str
    aim: str
    danger: str
    clue: str
    finale: str
    team: str

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
class Tool:
    id: str
    label: str
    phrase: str
    clip: bool = False
    can_share: bool = False
    can_aim: bool = False
    tags: set[str] = field(default_factory=set)

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
class Threat:
    id: str
    label: str
    needs: str
    risky_if_misaimed: bool = True
    tags: set[str] = field(default_factory=set)

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
class SupportMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_spotlight(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["fear"] < THRESHOLD:
            continue
        sig = ("spotlight", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["focus"] += 1
        out.append("__focus__")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    tool = world.facts.get("tool")
    if not hero or not friend or not tool:
        return out
    if not tool.attrs.get("shared"):
        return out
    if hero.memes["trust"] >= THRESHOLD and friend.memes["trust"] >= THRESHOLD:
        sig = ("sharing", tool.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] += 1
            friend.memes["joy"] += 1
            out.append("__share__")
    return out


CAUSAL_RULES = [
    Rule("spotlight", "social", _r_spotlight),
    Rule("sharing", "social", _r_sharing),
]


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


def hazard_ok(tool: Tool, threat: Threat) -> bool:
    return tool.can_aim and tool.clip and threat.risky_if_misaimed


def sensible_supports() -> list[SupportMove]:
    return [m for m in SUPPORT_MOVES.values() if m.sense >= 2]


def fire_strength(threat: Threat, delay: int) -> int:
    return 1 + delay if threat.risky_if_misaimed else delay


def can_fix(move: SupportMove, threat: Threat, delay: int) -> bool:
    return move.power >= fire_strength(threat, delay)


def dialogue_check(world: World, hero: Entity, friend: Entity, tool: Tool, threat: Threat) -> bool:
    sim = world.copy()
    _plan_mission(sim, sim.get(hero.id), sim.get(friend.id), tool, threat, narrate=False)
    return sim.get(hero.id).memes["trust"] >= THRESHOLD and sim.get(friend.id).memes["trust"] >= THRESHOLD


def _plan_mission(world: World, hero: Entity, friend: Entity, tool: Tool, threat: Threat, narrate: bool = True) -> None:
    world.say(f'{hero.id} and {friend.id} leaned over the blueprints. "{world.facts["mission"].scene}"')
    if tool.clip:
        world.say(f'"The {tool.label} can hold the cable tight," {friend.id} said.')
    if narrate:
        propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, friend: Entity, mission: Mission) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(f"{hero.id} was a small hero who loved helping in {mission.scene}.")
    world.say(f"{friend.id} carried the plans and smiled at the bright city lights.")
    world.say(f"Tonight's job was {mission.base}: to {mission.aim} before the shadow grew.")
    world.say(f"The team would need a {mission.team} of four careful moves.")


def share_clip(world: World, hero: Entity, friend: Entity, tool: Tool) -> None:
    tool.attrs["shared"] = True
    world.say(f'{hero.id} held up the {tool.label}. "{tool.phrase}," {hero.id} said. "We can share it."')
    world.say(f'{friend.id} nodded. "I will clip it on when you aim."')


def warn(world: World, friend: Entity, hero: Entity, tool: Tool, threat: Threat) -> None:
    friend.memes["trust"] += 1
    world.say(f'{friend.id} pointed at the dark coil. "If you aim wrong, {threat.label} could slip free."')
    world.say(f'"Then let us do it together," {hero.id} said.')


def defy(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["bold"] += 1
    world.say(f"{hero.id} took a breath and lifted the tool anyway, trying to act alone.")


def misfire(world: World, hero: Entity, threat: Threat) -> None:
    hero.meters["fear"] += 1
    world.say(f"The beam wobbled and the shadow jumped. For a moment, the alley felt too big.")


def rescue(world: World, move: SupportMove, hero: Entity, friend: Entity, threat: Threat, mission: Mission) -> None:
    hero.meters["fear"] = 0
    friend.meters["fear"] = 0
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(f"A helper from the roof arrived and {move.text.replace('{threat}', threat.label)}.")
    world.say(f"The danger faded, and the {mission.scene} glowed calm again.")


def ending(world: World, hero: Entity, friend: Entity, mission: Mission, tool: Tool) -> None:
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(f"{hero.id} clipped the gear in place, and {friend.id} guided the aim.")
    world.say(f"Together they finished the {mission.team}, and the city answered with a safe bright flash.")
    world.say(f"This time, the {mission.finale} proved the lesson: sharing made the rescue work.")


def tell(mission: Mission, tool: Tool, threat: Threat, move: SupportMove,
         hero_name: str = "Nova", friend_name: str = "Pip",
         hero_gender: str = "girl", friend_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, attrs={"shared": False}))
    threat_ent = world.add(Entity(id="threat", type="threat", label=threat.label))
    world.facts["mission"] = mission
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["tool"] = tool_ent
    world.facts["threat"] = threat_ent
    hero.memes["trust"] = 0.0
    friend.memes["trust"] = 0.0

    introduce(world, hero, friend, mission)
    world.para()
    share_clip(world, hero, friend, tool_ent)
    warn(world, friend, hero, tool_ent, threat_ent)
    if not dialogue_check(world, hero, friend, tool_ent, threat_ent):
        defy(world, hero, tool_ent)
    else:
        hero.memes["trust"] += 1
        friend.memes["trust"] += 1

    world.para()
    world.say(f'Then {hero.id} aimed carefully while {friend.id} clipped the tool into place.')
    if can_fix(move, threat, 0):
        rescue(world, move, hero, friend, threat_ent, mission)
        ending(world, hero, friend, mission, tool_ent)
        outcome = "contained"
    else:
        hero.meters["fear"] += 1
        friend.meters["fear"] += 1
        world.say(f"The plan shook loose, and the city had to wait for a bigger rescue.")
        outcome = "failed"

    world.facts["outcome"] = outcome
    world.facts["move"] = move
    return world


@dataclass
@dataclass
class StoryParams:
    mission: str
    tool: str
    threat: str
    move: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
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


MISSIONS = {
    "quadruple": Mission("quadruple", "the moonlit square", "the night watch", "aim the rescue beam", "the loose cable", "the rooftop signal", "the city kept smiling", "quadruple plan"),
    "alarm": Mission("alarm", "the old tower", "the watch shift", "aim the signal light", "the tangled wire", "the flashing beacon", "the street stayed safe", "quadruple plan"),
    "bridge": Mission("bridge", "the river bridge", "the bridge watch", "aim the repair light", "the slipping bolt", "the clipped beam", "the bridge held strong", "quadruple plan"),
}

TOOLS = {
    "clip": Tool("clip", "clip", "This clip will hold the cable steady.", clip=True, can_share=True, can_aim=True, tags={"clip"}),
    "visor_clip": Tool("visor_clip", "visor clip", "This visor clip helps us aim the light.", clip=True, can_share=True, can_aim=True, tags={"clip"}),
    "signal_clip": Tool("signal_clip", "signal clip", "This signal clip keeps the beam straight.", clip=True, can_share=True, can_aim=True, tags={"clip"}),
}

THREATS = {
    "shadow": Threat("shadow", "the shadow gust", "need aiming", True, tags={"aim"}),
    "coil": Threat("coil", "the loose coil", "need clipping", True, tags={"clip"}),
    "drift": Threat("drift", "the drifting spark", "need careful aim", True, tags={"aim"}),
}

SUPPORT_MOVES = {
    "steady_beam": SupportMove("steady_beam", 3, 2, "steadied the beam with a safe brace", "could not steady the beam", "steadied the beam"),
    "tight_clip": SupportMove("tight_clip", 3, 2, "clipped the cable tight so it would not swing", "the clip could not hold it", "clipped the cable tight"),
    "team_signal": SupportMove("team_signal", 2, 1, "sent a team signal that slowed the rush", "the signal came too late", "sent a team signal"),
}

GIRL_NAMES = ["Nova", "Mira", "Ada", "Zuri", "Ivy", "Lena"]
BOY_NAMES = ["Pip", "Theo", "Jax", "Noel", "Milo", "Rex"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid, mission in MISSIONS.items():
        for tid, tool in TOOLS.items():
            for thid, threat in THREATS.items():
                if hazard_ok(tool, threat):
                    combos.append((mid, tid, thid))
    return combos


def explain_rejection(tool: Tool, threat: Threat) -> str:
    return f"(No story: the {tool.label} must be a clip-and-aim tool, and {threat.label} needs that kind of help.)"


def explain_support(sid: str) -> str:
    m = SUPPORT_MOVES[sid]
    better = ", ".join(s.id for s in sensible_supports())
    return f"(Refusing move '{sid}': sense={m.sense} is too low. Try: {better}.)"


def outcome_of(params: StoryParams) -> str:
    return "contained" if can_fix(SUPPORT_MOVES[params.move], THREATS[params.threat], 0) else "failed"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld about sharing, dialogue, aiming, and a clip.")
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--move", choices=SUPPORT_MOVES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.move and SUPPORT_MOVES[args.move].sense < 2:
        raise StoryError(explain_support(args.move))
    if args.tool and args.threat and not hazard_ok(TOOLS[args.tool], THREATS[args.threat]):
        raise StoryError(explain_rejection(TOOLS[args.tool], THREATS[args.threat]))
    combos = [c for c in valid_combos()
              if (args.mission is None or c[0] == args.mission)
              and (args.tool is None or c[1] == args.tool)
              and (args.threat is None or c[2] == args.threat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mission, tool, threat = rng.choice(sorted(combos))
    move = args.move or rng.choice(sorted(s.id for s in sensible_supports()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)]
    hero = args.hero or rng.choice(hero_pool)
    friend = args.friend or rng.choice([n for n in friend_pool if n != hero] or friend_pool)
    return StoryParams(mission, tool, threat, move, hero, hero_gender, friend, friend_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m, t, th = f["mission"], f["tool"], f["threat"]
    return [
        f'Write a superhero story for a small child that includes the words "quadruple", "aim", and "clip".',
        f"Tell a story where {f['hero'].id} and {f['friend'].id} share a {t.label} and use dialogue to save {m.scene}.",
        f"Write a gentle superhero rescue story about a {m.team} that needs careful aim and a strong clip.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, mission, tool, threat = f["hero"], f["friend"], f["mission"], f["tool"], f["threat"]
    out = [
        ("Who is the story about?", f"It is about {hero.id} and {friend.id}, two small heroes working together."),
        ("What did they need to do?", f"They had to {mission.aim} before the danger could spread."),
        ("What did they share?", f"They shared the {tool.label}, because it worked best when one hero clipped it on and the other guided the aim."),
        ("Why did they talk first?", f"They talked first so they could avoid a mistake. The warning helped them keep the {threat.label} under control."),
    ]
    if f.get("outcome") == "contained":
        out.append(("How did the story end?", f"It ended safely. Their shared tool and careful aim kept everyone calm, and the city stayed bright."))
        out.append(("What was the quadruple plan?", f"It was a four-part rescue plan: share the clip, aim the light, steady the danger, and finish together."))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tool"].tags) | set(world.facts["threat"].tags)
    qas = []
    if "clip" in tags:
        qas.append(("What does a clip do?", "A clip fastens things together so they stay in place and do not slip around."))
    if "aim" in tags:
        qas.append(("What does it mean to aim?", "To aim means to point something carefully at the right place."))
    return qas


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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("quadruple", "clip", "coil", "tight_clip", "Nova", "girl", "Pip", "boy"),
    StoryParams("alarm", "visor_clip", "shadow", "steady_beam", "Mira", "girl", "Theo", "boy"),
    StoryParams("bridge", "signal_clip", "drift", "team_signal", "Ivy", "girl", "Rex", "boy"),
]


ASP_RULES = r"""
hazard(Tool, Threat) :- can_aim(Tool), has_clip(Tool), risky(Threat).
sensible(Move) :- support(Move), sense(Move, S), min_sense(Min), S >= Min.
valid(Mission, Tool, Threat) :- mission(Mission), tool(Tool), threat(Threat), hazard(Tool, Threat).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.clip:
            lines.append(asp.fact("has_clip", tid))
        if t.can_aim:
            lines.append(asp.fact("can_aim", tid))
    for thid in THREATS:
        lines.append(asp.fact("threat", thid))
        lines.append(asp.fact("risky", thid))
    for sid, s in SUPPORT_MOVES.items():
        lines.append(asp.fact("support", sid))
        lines.append(asp.fact("sense", sid, s.sense))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) != {m.id for m in sensible_supports()}:
        rc = 1
        print("MISMATCH in sensible moves.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as ex:
        return 1 if not print(ex) else 1
    return rc


def sensible_supports() -> list[SupportMove]:
    return [m for m in SUPPORT_MOVES.values() if m.sense >= 2]


def generate(params: StoryParams) -> StorySample:
    world = tell(MISSIONS[params.mission], TOOLS[params.tool], THREATS[params.threat], SUPPORT_MOVES[params.move], params.hero, params.friend, params.hero_gender, params.friend_gender)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible moves: {', '.join(asp_sensible())}")
        print()
        for mission, tool, threat in asp_valid_combos():
            print(f"  {mission:10} {tool:12} {threat}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
