#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/match_gerund_shield_mozzarella_conflict_comedy.py
===================================================================================

A small comedy storyworld about a cheese party, a forbidden match-gerund mishap,
a floppy shield, and a mozzarella conflict that gets resolved with a safer plan.

The seed words are treated as story instruments:
- match-gerund: the unsafe act of striking a match
- shield: a physical prop used in the pretend conflict
- mozzarella: the prized cheese that gets threatened by the mess

The world is intentionally tiny, child-facing, and state-driven. It simulates
characters, props, and emotional/physical meters, then renders a complete story
with a beginning, a turn, and an ending image that proves what changed.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    flammable: bool = False
    makes_flame: bool = False
    shield: bool = False
    edible: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"burning": 0.0, "messy": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "conflict": 0.0, "pride": 0.0}

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


@dataclass
class StoryParams:
    setting: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    parent: str
    line: str
    shield: str
    mozzarella: str
    response: str
    delay: int = 0
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    makes_flame: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ShieldProp:
    id: str
    label: str
    phrase: str
    cover: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cheese:
    id: str
    label: str
    phrase: str
    spread: int = 2
    flammable: bool = True
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("burning", 0.0) < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for char in world.entities.values():
            if char.kind == "character":
                char.memes["fear"] += 1
        if "room" in world.entities:
            world.get("room").meters["messy"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


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


def hazard(tool: Tool, cheese: Cheese) -> bool:
    return tool.makes_flame and cheese.flammable


def response_sensible(resp: Response) -> bool:
    return resp.sense >= SENSE_MIN


def fire_severity(cheese: Cheese, delay: int) -> int:
    return cheese.spread + delay


def is_contained(resp: Response, cheese: Cheese, delay: int) -> bool:
    return resp.power >= fire_severity(cheese, delay)


def setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a silly afternoon, {a.id} and {b.id} turned {setting.place} into "
        f"{setting.scene}."
    )
    world.say(
        f"They drew a big cartoon shield on a cardboard plate and named it "
        f"\"The Mighty Snack Shield.\""
    )


def need_plan(world: World, a: Entity, cheese: Cheese, setting: Setting) -> None:
    world.say(
        f"But {setting.dark_spot} was too dark to check the snack table, and "
        f"{a.id} wanted to see the {cheese.label} right away."
    )


def tempt(world: World, a: Entity, tool: Tool, line: str) -> None:
    a.memes["pride"] += 1
    world.say(
        f'\"I know! {line},\" {a.id} said, grinning at the {tool.label}. '
        f'\"It will be hilarious.\"'
    )


def warn(world: World, b: Entity, a: Entity, tool: Tool, cheese: Cheese, parent: Entity) -> None:
    b.memes["conflict"] += 1
    world.say(
        f"{b.id} frowned. \"Don't make a flame near the {cheese.label}. "
        f"{parent.label_word.capitalize()} said we have to keep the snack safe.\""
    )


def act_match(world: World, tool: Tool, cheese: Cheese) -> None:
    target = world.get("cheese")
    target.meters["burning"] += 1
    world.get("room").meters["messy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{tool.phrase.capitalize()} flared like a tiny dragon tongue. "
        f"The edge of the {cheese.label} warmed, then turned a little toasty."
    )


def alarm(world: World, b: Entity, parent: Entity, cheese: Cheese) -> None:
    world.say(f"\"Oops! The {cheese.label}!\" {b.id} yelped.")
    world.say(f"\"{parent.label_word.upper()}!\"")


def rescue(world: World, parent: Entity, resp: Response, cheese: Cheese) -> None:
    world.get("cheese").meters["burning"] = 0.0
    world.get("room").meters["messy"] = 0.0
    body = resp.text.replace("{target}", cheese.label)
    world.say(
        f"{parent.label_word.capitalize()} came running, and in one quick swoop "
        f"{parent.pronoun()} {body}."
    )
    world.say(
        f"The tiny flame went poof, leaving only a warm cheese smell and two "
        f"very serious snack inspectors."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["fear"] += 1
    b.memes["fear"] += 1
    world.say("For a moment, everyone stared at the plate.")
    world.say(
        f"Then {parent.label_word.capitalize()} hugged them both. "
        f"\"{tool.label.capitalize()} are not toys,\" {parent.pronoun()} said. "
        f"\"If you need light, we use a safe lamp.\""
    )


def safe_end(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.meters["safe"] += 1
    b.meters["safe"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} brought a little lamp "
        f"and a paper lantern. {a.id} held the shield up like a stage prop, and "
        f"{b.id} giggled at the shadow show."
    )
    world.say(
        f"This time the {a.id} and {b.id} snack party stayed bright, safe, and "
        f"extra cheesy."
    )


def tell(setting: Setting, tool: Tool, cheese: Cheese, resp: Response,
         instigator: Entity, helper: Entity, parent: Entity, shield: ShieldProp,
         delay: int = 0) -> World:
    world = World()
    world.add(Entity(id="room", type="room", label=setting.place))
    world.add(Entity(id="tool", type="tool", label=tool.label, makes_flame=tool.makes_flame))
    world.add(Entity(id="shield", type="thing", label=shield.label, shield=True))
    world.add(Entity(id="cheese", type="food", label=cheese.label, flammable=cheese.flammable, edible=True))
    a = world.add(instigator)
    b = world.add(helper)
    p = world.add(parent)

    setup(world, a, b, setting)
    need_plan(world, a, cheese, setting)
    world.para()
    tempt(world, a, tool, world.facts.get("line", "I can make it sparkle"))
    warn(world, b, a, tool, cheese, p)

    if world.facts.get("averted"):
        world.say(
            f"{a.id} looked at {b.id}, then at the {shield.label}, and decided "
            f"not to touch the match at all."
        )
        world.say(f"They used the shield as a pretend stage prop instead.")
        world.para()
        safe_end(world, p, a, b)
    else:
        world.say(f"{a.id} went ahead anyway, because comedy and curiosity can be a loud team.")
        world.para()
        act_match(world, tool, cheese)
        alarm(world, b, p, cheese)
        contained = is_contained(resp, cheese, delay)
        world.facts["contained"] = contained
        if contained:
            world.para()
            rescue(world, p, resp, cheese)
            lesson(world, p, a, b, tool)
            world.para()
            safe_end(world, p, a, b)
        else:
            world.para()
            world.say(
                f"{parent.label_word.capitalize()} tried {resp.fail.replace('{target}', cheese.label)} "
                f"but the little fire was too lively and kept hopping."
            )
            world.say(
                f"Everyone rushed outside while the snack table puffed up in smoke, "
                f"and the shield became a very lopsided rescue sign."
            )
            world.say(
                f"Afterward, {parent.label_word.capitalize()} reminded them that "
                f"{tool.label} belong in drawers, not in joke contests."
            )

    world.facts.update(
        instigator=a,
        helper=b,
        parent=p,
        setting=setting,
        tool=tool,
        cheese=cheese,
        shield=shield,
        response=resp,
        delay=delay,
        outcome="averted" if world.facts.get("averted") else ("contained" if world.facts.get("contained") else "burned"),
    )
    return world


SETTINGS = {
    "snackroom": Setting(id="snackroom", place="the snack room", scene="a cheesy castle feast", dark_spot="the corner behind the snack table"),
    "kitchen": Setting(id="kitchen", place="the kitchen", scene="a wobbly lunch parade", dark_spot="the shadow under the counter"),
    "playroom": Setting(id="playroom", place="the playroom", scene="a pretend museum of snacks", dark_spot="the tunnel under the card table"),
}

TOOLS = {
    "match": Tool(id="match", label="match", phrase="a match", makes_flame=True, tags={"match", "fire"}),
}

SHIELDS = {
    "cardboard": ShieldProp(id="cardboard", label="cardboard shield", phrase="a cardboard shield", cover="face", tags={"shield"}),
    "tabletop": ShieldProp(id="tabletop", label="table shield", phrase="the round table shield", cover="table", tags={"shield"}),
}

CHEESES = {
    "mozzarella": Cheese(id="mozzarella", label="mozzarella", phrase="a ball of mozzarella", spread=2, flammable=True, tags={"mozzarella"}),
    "string": Cheese(id="string", label="string cheese", phrase="a string cheese stick", spread=1, flammable=True, tags={"mozzarella"}),
}

RESPONSES = {
    "fan": Response(id="fan", sense=3, power=3, text="fanned the smoke away and nudged the {target} onto a cool plate", fail="fanned at the smoke", qa_text="fanned the smoke away and moved the {target} to a cool plate", tags={"fan"}),
    "lid": Response(id="lid", sense=3, power=2, text="slid a pot lid over the {target} and pinched the spark out", fail="tried to cover the {target} with a lid", qa_text="slid a pot lid over the {target} and pinched the spark out", tags={"lid"}),
    "stomp": Response(id="stomp", sense=2, power=2, text="stomped out the spark with quick careful feet", fail="stomped at the flame", qa_text="stomped out the spark with quick careful feet", tags={"stomp"}),
    "water_bottle": Response(id="water_bottle", sense=1, power=1, text="splashed a tiny water bottle over the {target}", fail="splashed a tiny water bottle over the {target}", qa_text="splashed a tiny water bottle over the {target}", tags={"water"}),
}

NAMES = ["Mina", "Toby", "Lila", "Benji", "Nora", "Pip", "Milo", "Zuzu"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOOLS:
            for c in CHEESES:
                if hazard(TOOLS[t], CHEESES[c]) and any(r.sense >= SENSE_MIN for r in RESPONSES.values()):
                    combos.append((s, t, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a match, a shield, and mozzarella.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--cheese", choices=CHEESES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.response and not response_sensible(RESPONSES[args.response]):
        raise StoryError("(Refusing the low-sense response; the story needs a smarter rescue.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.cheese is None or c[2] == args.cheese)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, cheese = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(k for k, v in RESPONSES.items() if response_sensible(v)))
    parent = args.parent or rng.choice(["mother", "father"])
    name_a, name_b = rng.sample(NAMES, 2)
    inst = Entity(id=name_a, kind="character", type=rng.choice(["girl", "boy"]), role="instigator", traits=["curious"])
    helpr = Entity(id=name_b, kind="character", type=rng.choice(["girl", "boy"]), role="helper", traits=["wry"])
    return StoryParams(
        setting=setting,
        instigator=inst.id,
        instigator_gender=inst.type,
        helper=helpr.id,
        helper_gender=helpr.type,
        parent=parent,
        line="the match-gerund trick will make everyone laugh",
        shield=SHIELDS["cardboard"].id,
        mozzarella=cheese,
        response=response,
        delay=rng.randint(0, 2),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.mozzarella not in CHEESES:
        raise StoryError(f"Unknown mozzarella: {params.mozzarella}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if params.shield not in SHIELDS:
        raise StoryError(f"Unknown shield: {params.shield}")

    setting = SETTINGS[params.setting]
    tool = TOOLS["match"]
    cheese = CHEESES[params.mozzarella]
    resp = RESPONSES[params.response]
    shield = SHIELDS[params.shield]
    a = Entity(id=params.instigator, kind="character", type=params.instigator_gender, role="instigator", traits=["silly"])
    b = Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["careful"])
    p = Entity(id=params.parent, kind="character", type=params.parent, role="parent")
    world = tell(setting, tool, cheese, resp, a, b, p, shield, delay=params.delay)

    story_qa = [
        QAItem(
            question="Why did the helper get worried?",
            answer=f"{params.helper} got worried because the match could make a real flame near the mozzarella. That would turn a snack into a smoky joke very quickly."
        ),
        QAItem(
            question="How did the grown-up help in the happy ending?",
            answer=f"The grown-up used {resp.qa_text.replace('{target}', cheese.label)}. That stopped the tiny fire and let the children finish their silly snack game safely."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="At the start, the room was full of teasing and tension. By the end, the danger was gone, the children were laughing again, and the mozzarella stayed safe on the plate."
        ),
    ]
    if world.facts.get("contained") is False and world.facts.get("outcome") == "burned":
        story_qa.append(
            QAItem(
                question="What happened when the rescue was too late?",
                answer="The spark kept hopping, so the family had to rush out. The silly snack game ended in a smoky mess, and the shield became a rescue sign instead of a joke prop."
            )
        )

    prompts = [
        "Write a comedy story for a young child that includes match-gerund, shield, and mozzarella.",
        f"Tell a funny conflict story where {params.instigator} tries a match near mozzarella and {params.helper} warns them.",
        "Write a small, child-friendly rescue story with a silly prop shield and a safe ending."
    ]

    world_qa = [
        QAItem(question="What is mozzarella?", answer="Mozzarella is a soft cheese that is often white and stretchy. People put it on snacks and pizzas because it tastes mild and yummy."),
        QAItem(question="Why is a match dangerous near food or paper?", answer="A match makes a flame. A flame can spread to things nearby, so it should only be used by grown-ups in safe places."),
        QAItem(question="What is a shield?", answer="A shield is something you hold up to block, cover, or pretend to defend yourself in a game. In this story it is silly and cardboard, so it does not really stop fire."),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:10} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(T, C) :- makes_flame(T), flammable(C).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, T, C) :- setting(S), tool(T), cheese(C), hazard(T, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t, obj in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if obj.makes_flame:
            lines.append(asp.fact("makes_flame", t))
    for c, obj in CHEESES.items():
        lines.append(asp.fact("cheese", c))
        if obj.flammable:
            lines.append(asp.fact("flammable", c))
    for r, obj in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, obj.sense))
        lines.append(asp.fact("power", r, obj.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    else:
        print("OK: ASP gate matches Python valid_combos().")
    if set(asp_sensible()) != {k for k, v in RESPONSES.items() if response_sensible(v)}:
        rc = 1
        print("MISMATCH: ASP sensible responses differ from Python.")
    else:
        print("OK: ASP sensible responses match.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: ordinary story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams(setting="snackroom", instigator="Mina", instigator_gender="girl", helper="Toby", helper_gender="boy", parent="mother", line="the match-gerund trick will make everyone laugh", shield="cardboard", mozzarella="mozzarella", response="fan", delay=0, seed=1),
    StoryParams(setting="kitchen", instigator="Lila", instigator_gender="girl", helper="Benji", helper_gender="boy", parent="father", line="the match-gerund trick will make everyone laugh", shield="tabletop", mozzarella="string", response="lid", delay=1, seed=2),
    StoryParams(setting="playroom", instigator="Pip", instigator_gender="boy", helper="Nora", helper_gender="girl", parent="mother", line="the match-gerund trick will make everyone laugh", shield="cardboard", mozzarella="mozzarella", response="stomp", delay=0, seed=3),
]


def build_sample_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not response_sensible(RESPONSES[args.response]):
        raise StoryError("(Refusing the low-sense response.)")
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.tool:
        combos = [c for c in combos if c[1] == args.tool]
    if args.cheese:
        combos = [c for c in combos if c[2] == args.cheese]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, cheese = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(k for k, v in RESPONSES.items() if response_sensible(v)))
    parent = args.parent or rng.choice(["mother", "father"])
    inst_name = rng.choice(NAMES)
    helper_name = rng.choice([n for n in NAMES if n != inst_name])
    inst_gender = rng.choice(["girl", "boy"])
    help_gender = "boy" if inst_gender == "girl" else "girl"
    return StoryParams(
        setting=setting,
        instigator=inst_name,
        instigator_gender=inst_gender,
        helper=helper_name,
        helper_gender=help_gender,
        parent=parent,
        line="the match-gerund trick will make everyone laugh",
        shield="cardboard",
        mozzarella=cheese,
        response=response,
        delay=rng.randint(0, 2),
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
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, t, c in asp_valid_combos():
            print(f"  {s:10} {t:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} vs {p.helper}: {p.mozzarella} and the {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
