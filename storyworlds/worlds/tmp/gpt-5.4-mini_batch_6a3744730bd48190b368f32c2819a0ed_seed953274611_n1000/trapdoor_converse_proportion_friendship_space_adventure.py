#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trapdoor_converse_proportion_friendship_space_adventure.py
==========================================================================================

A small, self-contained story world for a friendship-in-space tale.

Seed words:
- trapdoor
- converse
- proportion

Style:
- Space Adventure

Premise:
Two friends aboard a tiny starship discover a trapdoor in the cargo deck. One
friend wants to open it and go exploring; the other wants to converse first and
check whether the plan is safe. Their friendship, a simple proportion check, and
a helpful tool decide the outcome.

This script follows the storyworld contract:
- stdlib only
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    noun: str
    sound: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectItem:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
    type: str = "thing"
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    safe: bool
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_pressure(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["pressure"] < THRESHOLD:
            continue
        sig = ("pressure", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("ship").meters["alert"] += 1
        out.append("__alert__")
    return out


def _r_bond(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("A")
    b = world.entities.get("B")
    if not a or not b:
        return out
    if a.memes["trust"] >= THRESHOLD and b.memes["trust"] >= THRESHOLD:
        sig = ("bond",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["bond"] += 1
            b.memes["bond"] += 1
            out.append("__bond__")
    return out


CAUSAL_RULES = [Rule("pressure", _r_pressure), Rule("bond", _r_bond)]


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


def hazard_at_risk(act: Activity, obj: ObjectItem) -> bool:
    return obj.region in act.zone


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid, act in ACTIVITIES.items():
            if aid not in SETTINGS[sid].affords:
                continue
            for oid, obj in OBJECTS.items():
                if hazard_at_risk(act, obj):
                    combos.append((sid, aid, oid))
    return combos


def fire_severity(obj: ObjectItem, delay: int) -> int:
    return 1 + delay + (1 if obj.fragile else 0)


def is_contained(response: Response, obj: ObjectItem, delay: int) -> bool:
    return response.power >= fire_severity(obj, delay)


def predict_risk(world: World, obj_id: str) -> dict:
    sim = world.copy()
    sim.get(obj_id).meters["pressure"] += 1
    propagate(sim, narrate=False)
    return {"alert": sim.get("ship").meters["alert"], "pressure": sim.get(obj_id).meters["pressure"]}


def _do_risky(world: World, obj: Entity, narrate: bool = True) -> None:
    obj.meters["pressure"] += 1
    obj.meters["stress"] += 1
    propagate(world, narrate=narrate)


def set_scene(world: World, a: Entity, b: Entity, setting: Setting, act: Activity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On the little starship {setting.place}, {a.id} and {b.id} turned "
        f"the cargo deck into a game of {setting.mood}. {setting.detail}"
    )
    world.say(
        f'"Look," said {a.id}, "the {act.keyword} hatch is right there!" '
        f'"Let\'s see what\'s under it!"'
    )


def need_converse(world: World, b: Entity, setting: Setting, obj: ObjectItem) -> None:
    world.say(
        f"But the {setting.mood} corner felt quiet, and the trapdoor sat there "
        f"like a mystery. {b.id} peered at it. "
        f'"We should converse first," {b.pronoun()} said. "We need a plan."'
    )
    world.facts["proportion_hint"] = True
    world.say(
        f'{b.id} tapped the deck and added, "We have to keep the right '
        f'proportion between our tiny hands and that big heavy hatch."'
    )


def tempt(world: World, a: Entity, act: Activity) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"{a.id}'s eyes flashed bright. \"I know! We can open it now,\" "
        f"{a.id} said. \"It will only take a second.\""
    )
    world.say(f"The idea sounded quick and thrilling.")


def warn(world: World, b: Entity, a: Entity, obj: ObjectItem, setting: Setting) -> None:
    pred = predict_risk(world, obj.id)
    b.memes["caution"] += 1
    world.facts["predicted_alert"] = pred["alert"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, that trapdoor is '
        f"too heavy for us to rush. If it slips, it could bump the console "
        f"and make a mess in the {setting.place}."'
    )


def open_hatch(world: World, a: Entity, obj: ObjectItem, act: Activity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Maybe just a peek," {a.id} said, and {a.id} heaved at the '
        f"{obj.label}. Then the hatch gave a sharp clank and popped open."
    )


def alarm(world: World, b: Entity, a: Entity, obj: ObjectItem) -> None:
    world.say(f'"{a.id}! The {obj.label}!" {b.id} cried.')
    world.say('"Hold on!"')


def rescue(world: World, parent: Entity, response: Response, obj: ObjectItem) -> None:
    obj.meters["pressure"] = 0
    world.get("ship").meters["alert"] = 0
    body = response.text.replace("{target}", obj.label)
    world.say(f"{parent.id} came hurrying over and {body}.")
    world.say(
        f"The hatch settled closed again, and the ship went from clanging alarm "
        f"to soft, steady hum."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.id} smiled and knelt beside them. "
        f'"I like that you talked to each other," {parent.pronoun()} said. '
        f'"Friends can be brave and still check the plan first."'
    )
    world.say(
        f'{a.id} and {b.id} nodded, and the little hatch stayed shut while '
        f'they made a safer route through the {setting.place}.'
    )


def safe_end(world: World, parent: Entity, a: Entity, b: Entity, tool: Tool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next watch, {parent.id} brought out {tool.phrase}. "
        f"{a.id} clicked it on, and {b.id} grinned when the beam lit the deck."
    )
    world.say(
        f"This time they could explore together -- bright, careful, and still "
        f"good friends."
    )


def rescue_fail(world: World, parent: Entity, response: Response, obj: ObjectItem) -> None:
    world.get("ship").meters["alert"] += 1
    world.say(
        f"{parent.id} came hurrying over, but {response.fail.replace('{target}', obj.label)}."
    )
    world.say(
        f"The hatch jammed partly open, and the ship shuddered with a loud metallic groan."
    )


def ending_loss(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"{parent.id} led {a.id} and {b.id} back to the control room and shut "
        f"the corridor lights down until the ship calmed."
    )
    world.say(
        "They were safe, but the adventure had to pause until the next day."
    )


def tell(setting: Setting, activity: Activity, obj: ObjectItem, tool: Tool, response: Response,
         name_a: str, name_b: str, parent_name: str, delay: int = 0,
         trust_a: int = 2, trust_b: int = 2) -> World:
    world = World()
    a = world.add(Entity(id=name_a, kind="character", type="girl", role="friend"))
    b = world.add(Entity(id=name_b, kind="character", type="boy", role="friend"))
    parent = world.add(Entity(id=parent_name, kind="character", type="captain", role="adult", label="the captain"))
    ship = world.add(Entity(id="ship", type="ship", label="the starship"))
    hatch = world.add(Entity(id="trapdoor", type="thing", label="trapdoor"))
    a.memes["trust"] = float(trust_a)
    b.memes["trust"] = float(trust_b)

    set_scene(world, a, b, setting, activity)
    world.para()
    need_converse(world, b, setting, obj)
    tempt(world, a, activity)
    warn(world, b, a, obj, setting)

    averted = a.memes["trust"] >= 4 and b.memes["trust"] >= 4 and delay == 0
    contained = True
    severity = 0

    if averted:
        a.memes["defiance"] = 0
        b.memes["relief"] += 1
        world.say(
            f'{a.id} paused, looked at {b.id}, and said, "Okay. Let us converse '
            f"first.""
        )
        world.say(
            f"They counted their steps, checked the proportion of space around the "
            f"trapdoor, and left it shut."
        )
        world.para()
        safe_end(world, parent, a, b, tool)
        outcome = "averted"
    else:
        open_hatch(world, a, hatch, activity)
        world.para()
        alarm(world, b, a, hatch)
        severity = fire_severity(obj, delay)
        contained = is_contained(response, obj, delay)
        if contained:
            rescue(world, parent, response, obj)
            lesson(world, parent, a, b, setting)
            world.para()
            safe_end(world, parent, a, b, tool)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, obj)
            ending_loss(world, parent, a, b)
            outcome = "burned"

    world.facts.update(
        a=a, b=b, parent=parent, ship=ship, hatch=hatch, setting=setting,
        activity=activity, obj=obj, tool=tool, response=response, outcome=outcome,
        severity=severity, delay=delay, contained=contained
    )
    return world


SETTINGS = {
    "cargo_bay": Setting(
        id="cargo_bay",
        place="the cargo bay",
        detail="A few moon crates floated in neat rows, and a round window showed the blue glow of Earth.",
        mood="quiet space play",
        affords={"inspect", "listen", "converse"},
    ),
    "observation_deck": Setting(
        id="observation_deck",
        place="the observation deck",
        detail="Stars glittered beyond the glass, and a little map glowed on the wall.",
        mood="starlight play",
        affords={"inspect", "listen", "converse"},
    ),
}

ACTIVITIES = {
    "inspect": Activity(
        id="inspect",
        verb="inspect the hatch",
        noun="inspection",
        sound="clank",
        risk="pressure",
        zone={"cargo"},
        keyword="trapdoor",
        tags={"trapdoor", "space"},
    ),
    "converse": Activity(
        id="converse",
        verb="converse about the hatch",
        noun="conversation",
        sound="whisper",
        risk="pressure",
        zone={"cargo"},
        keyword="converse",
        tags={"converse", "friendship"},
    ),
    "listen": Activity(
        id="listen",
        verb="listen by the hatch",
        noun="listening",
        sound="tap",
        risk="pressure",
        zone={"cargo"},
        keyword="proportion",
        tags={"proportion", "friendship"},
    ),
}

OBJECTS = {
    "hatch": ObjectItem(
        id="hatch",
        label="trapdoor",
        phrase="the trapdoor",
        region="cargo",
        fragile=True,
        tags={"trapdoor"},
    ),
}

TOOLS = {
    "lamp": Tool(
        id="lamp",
        label="star lamp",
        phrase="a small star lamp",
        safe=True,
        effect="lights the deck",
        tags={"space"},
    ),
    "beacon": Tool(
        id="beacon",
        label="pocket beacon",
        phrase="a pocket beacon",
        safe=True,
        effect="shows the way",
        tags={"space"},
    ),
}

RESPONSES = {
    "brace": Response(
        id="brace",
        sense=3,
        power=2,
        text="braced the trapdoor with both hands and locked it shut",
        fail="tried to brace the trapdoor, but it was already stuck",
        qa_text="braced the trapdoor with both hands and locked it shut",
        tags={"trapdoor"},
    ),
    "call": Response(
        id="call",
        sense=3,
        power=3,
        text="called for the captain and kept the hatch steady until help came",
        fail="called for the captain, but the ship shuddered before help could help",
        qa_text="called for the captain and kept the hatch steady until help came",
        tags={"friendship"},
    ),
    "glue": Response(
        id="glue",
        sense=1,
        power=1,
        text="smeared quick glue over the edge of the trapdoor",
        fail="smeared quick glue over the edge, but it only made the hatch stick worse",
        qa_text="smeared quick glue over the edge of the trapdoor",
        tags={"trapdoor"},
    ),
}

SENSE_MIN = 2
TRAITS = ["brave", "careful", "curious", "gentle"]
GIRL_NAMES = ["Mina", "Lia", "Zuri", "Nia"]
BOY_NAMES = ["Tao", "Jun", "Pax", "Noel"]


def sensible_choices() -> list[str]:
    return sorted(r.id for r in sensible_responses())


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly space adventure story that includes the words "{f["activity"].keyword}", "trapdoor", and "proportion".',
        f"Tell a friendship story aboard a starship where {f['a'].id} and {f['b'].id} converse before opening a trapdoor.",
        f"Write a small space tale about friends who pause to compare the right proportion before touching a trapdoor.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["a"], f["b"], f["parent"]
    setting = f["setting"]
    obj = f["obj"]
    act = f["activity"]
    qa = [
        ("Who are the story friends?",
         f"The story is about {a.id} and {b.id}, two friends on a tiny starship. They stay close because they care about each other and want the adventure to be safe."),
        ("Why did they talk before opening the trapdoor?",
         f"They talked first because the trapdoor was heavy and could cause trouble if it slipped. Conversation helped them slow down and check the plan together."),
        ("What word about size did the story use?",
         f"It used the word proportion. They compared the right proportion of their small hands to the big hatch so they would know whether their idea was sensible."),
    ]
    if f["outcome"] == "averted":
        qa.append((
            "What happened instead of opening the trapdoor?",
            f"{a.id} listened to {b.id}, and they left the trapdoor shut. Then they chose a safer way to explore the {setting.place} together."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the friends using a safe light and staying cheerful on the ship. The trapdoor stayed closed, and their friendship helped them make a wiser choice."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            "What happened when the trapdoor opened?",
            f"The trapdoor popped open, and everyone got a scare. The captain came quickly and used the chosen response to steady it before the problem could grow."
        ))
        qa.append((
            "How did the friends feel at the end?",
            f"They felt relieved, happy, and closer as friends. The scary moment turned into a lesson about talking first and trusting each other."
        ))
    else:
        qa.append((
            "What made the ending scary?",
            f"The trapdoor jammed and the first fix was not strong enough. The captain had to calm the ship down, so the friends could only continue the adventure later."
        ))
        qa.append((
            "What did they learn?",
            f"They learned that a quick idea is not always the safest one. In space, good friendship means checking the plan and asking for help early."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["activity"].tags) | set(f["obj"].tags) | set(f["tool"].tags)
    if f["outcome"] != "averted":
        tags |= {"trapdoor"}
    out = []
    if "trapdoor" in tags:
        out.append((
            "What is a trapdoor?",
            "A trapdoor is a door in the floor or ceiling that can open to another space. It can be useful, but it can also be dangerous if you rush it."
        ))
    if "converse" in tags:
        out.append((
            "What does converse mean?",
            "To converse means to talk with someone back and forth. Friends converse when they share ideas and listen to each other."
        ))
    if "proportion" in tags:
        out.append((
            "What is proportion?",
            "Proportion means how the parts of something compare to the whole. People use it to check whether sizes seem right together."
        ))
    if "space" in tags:
        out.append((
            "Why do starships need lights?",
            "Starships often have dark corners and hidden decks, so lights help people see where they are going. A safe light is better than guessing in the dark."
        ))
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cargo_bay", activity="converse", obj="hatch", tool="lamp", response="brace",
                a_name="Mina", b_name="Tao", parent_name="Captain Sol", seed=1, a_trust=5, b_trust=5),
    StoryParams(setting="observation_deck", activity="inspect", obj="hatch", tool="beacon", response="call",
                a_name="Lia", b_name="Pax", parent_name="Captain Mira", seed=2, a_trust=3, b_trust=3),
    StoryParams(setting="cargo_bay", activity="listen", obj="hatch", tool="lamp", response="glue",
                a_name="Nia", b_name="Jun", parent_name="Captain Sol", seed=3, a_trust=2, b_trust=2),
]


@dataclass
class StoryParams:
    setting: str
    activity: str
    obj: str
    tool: str
    response: str
    a_name: str
    b_name: str
    parent_name: str
    delay: int = 0
    a_trust: int = 2
    b_trust: int = 2
    seed: Optional[int] = None


def explain_rejection(activity: Activity, obj: ObjectItem) -> str:
    return f"(No story: {activity.verb} is not a good match for {obj.label} here.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def outcome_of(params: StoryParams) -> str:
    if params.a_trust >= 4 and params.b_trust >= 4 and params.delay == 0:
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], OBJECTS[params.obj], params.delay) else "burned"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space friendship story world with a trapdoor and a careful conversation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", dest="obj", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--parent")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    setting = args.setting or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(SETTINGS[setting].affords))
    obj = args.obj or "hatch"
    if not hazard_at_risk(ACTIVITIES[activity], OBJECTS[obj]):
        raise StoryError(explain_rejection(ACTIVITIES[activity], OBJECTS[obj]))
    tool = args.tool or rng.choice(list(TOOLS))
    response = args.response or rng.choice(sensible_choices())
    a_name = args.name_a or rng.choice(GIRL_NAMES)
    b_name = args.name_b or rng.choice(BOY_NAMES)
    parent = args.parent or "Captain Sol"
    return StoryParams(setting=setting, activity=activity, obj=obj, tool=tool, response=response,
                       a_name=a_name, b_name=b_name, parent_name=parent, delay=args.delay,
                       a_trust=rng.randint(1, 5), b_trust=rng.randint(1, 5))


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.activity not in ACTIVITIES or params.obj not in OBJECTS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], OBJECTS[params.obj],
                 TOOLS[params.tool], RESPONSES[params.response], params.a_name, params.b_name,
                 params.parent_name, delay=params.delay, trust_a=params.a_trust, trust_b=params.b_trust)
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


ASP_RULES = r"""
risk(A,O) :- activity(A), object(O), zone(A,R), region(O,R).
valid(S,A,O) :- setting(S), affords(S,A), risk(A,O).
sensible(R) :- response(R), sense(R,S), min_sense(M), S >= M.
outcome(averted) :- trust_a(TA), trust_b(TB), TA >= 4, TB >= 4, delay(0).
outcome(contained) :- not outcome(averted), chosen_response(R), chosen_object(O), response(R), power(R,P), severity(O,D,V), P >= V.
outcome(burned) :- not outcome(averted), not outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in SETTINGS[sid].affords:
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in a.zone:
            lines.append(asp.fact("zone", aid, r))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region", oid, o.region))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("min_sense", SENSE_MIN))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("trust_a", params.a_trust),
        asp.fact("trust_b", params.b_trust),
        asp.fact("delay", params.delay),
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_object", params.obj),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    vals = asp.atoms(model, "outcome")
    return vals[0][0] if vals else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    if set(asp_sensible()) != set(sensible_choices()):
        print("MISMATCH in sensible responses")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    cases = CURATED[:]
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(p)
        except StoryError:
            pass
    if any(asp_outcome(p) != outcome_of(p) for p in cases):
        print("MISMATCH in outcomes")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
