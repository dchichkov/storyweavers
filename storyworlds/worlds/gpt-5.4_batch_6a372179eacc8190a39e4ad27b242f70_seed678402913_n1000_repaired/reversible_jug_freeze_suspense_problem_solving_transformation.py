#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reversible_jug_freeze_suspense_problem_solving_transformation.py
=============================================================================================

A standalone storyworld about a child, a jug, and a freezing problem told in a
gentle nursery-rhyme style. The little world models winter cold, a liquid in a
jug, a suspenseful near-freeze or full freeze, a problem-solving step using a
reversible wrap, and a transformation at the end: icy drink to flowing drink,
or a child turning worry into cheerful cleverness.

The core constraint is simple and concrete:

    route cold + jug chill + poor wrap -> the drink freezes
    route cold + good wrap             -> the drink stays pourable
    frozen drink + sensible thaw       -> the drink flows again

The world refuses combinations that make no physical sense, and it includes an
inline ASP twin for parity checking.

Run it
------
    python storyworlds/worlds/gpt-5.4/reversible_jug_freeze_suspense_problem_solving_transformation.py
    python storyworlds/worlds/gpt-5.4/reversible_jug_freeze_suspense_problem_solving_transformation.py --drink cider --route porch
    python storyworlds/worlds/gpt-5.4/reversible_jug_freeze_suspense_problem_solving_transformation.py --wrap ribbon
    python storyworlds/worlds/gpt-5.4/reversible_jug_freeze_suspense_problem_solving_transformation.py --all
    python storyworlds/worlds/gpt-5.4/reversible_jug_freeze_suspense_problem_solving_transformation.py --verify
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Drink:
    id: str
    label: str
    phrase: str
    warm_word: str
    frozen_word: str
    color: str
    starts_warm: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class JugKind:
    id: str
    label: str
    phrase: str
    chill: int
    clink: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    cold: int
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Wrap:
    id: str
    label: str
    phrase: str
    reversible: bool
    warmth_plain: int
    warmth_best: int
    best_side: str
    weak: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ThawMethod:
    id: str
    label: str
    sense: int
    power: int
    text: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_freeze(world: World) -> list[str]:
    jug = world.get("jug")
    if jug.meters["freeze_risk"] < THRESHOLD:
        return []
    if ("freeze",) in world.fired:
        return []
    world.fired.add(("freeze",))
    jug.meters["frozen"] += 1
    child = world.get("child")
    child.memes["worry"] += 1
    return ["__freeze__"]


def _r_relief(world: World) -> list[str]:
    jug = world.get("jug")
    if jug.meters["flowing"] < THRESHOLD:
        return []
    if ("relief",) in world.fired:
        return []
    world.fired.add(("relief",))
    child = world.get("child")
    helper = world.get("helper")
    child.memes["relief"] += 1
    helper.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="freeze", tag="physical", apply=_r_freeze),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


DRINKS = {
    "cider": Drink(
        id="cider",
        label="apple cider",
        phrase="a jug of warm apple cider",
        warm_word="warm cider",
        frozen_word="apple-ice slush",
        color="golden",
        tags={"cider", "warm_drink", "freeze"},
    ),
    "berry_juice": Drink(
        id="berry_juice",
        label="berry juice",
        phrase="a jug of rosy berry juice",
        warm_word="warm berry juice",
        frozen_word="berry ice",
        color="rosy",
        tags={"juice", "freeze"},
    ),
    "soup": Drink(
        id="soup",
        label="pumpkin soup",
        phrase="a jug of pumpkin soup",
        warm_word="warm soup",
        frozen_word="pumpkin slush",
        color="orange",
        tags={"soup", "freeze"},
    ),
}

JUGS = {
    "glass": JugKind(
        id="glass",
        label="glass jug",
        phrase="a clear glass jug",
        chill=2,
        clink="The glass gave a tiny clink in the cold.",
        tags={"glass", "jug"},
    ),
    "tin": JugKind(
        id="tin",
        label="tin jug",
        phrase="a bright tin jug",
        chill=3,
        clink="The tin gave a silver ping in the cold.",
        tags={"tin", "jug"},
    ),
    "stoneware": JugKind(
        id="stoneware",
        label="stoneware jug",
        phrase="a round stoneware jug",
        chill=1,
        clink="The stoneware felt heavy and still.",
        tags={"stoneware", "jug"},
    ),
}

ROUTES = {
    "porch": Route(
        id="porch",
        label="porch",
        phrase="across the porch to the little table",
        cold=2,
        detail="Moon-cold boards creaked under small feet.",
        tags={"porch", "winter"},
    ),
    "yard": Route(
        id="yard",
        label="yard",
        phrase="through the yard to the gate",
        cold=3,
        detail="The yard wind came sniffing through the snow.",
        tags={"yard", "winter"},
    ),
    "pantry": Route(
        id="pantry",
        label="pantry",
        phrase="down the short pantry hall",
        cold=1,
        detail="The pantry hall was cool, but not biting cold.",
        tags={"pantry"},
    ),
}

WRAPS = {
    "reversible_cozy": Wrap(
        id="reversible_cozy",
        label="reversible cozy",
        phrase="a reversible cozy with a quilt side and a wool side",
        reversible=True,
        warmth_plain=1,
        warmth_best=3,
        best_side="wool side out",
        tags={"reversible", "wrap", "wool"},
    ),
    "tea_towel": Wrap(
        id="tea_towel",
        label="tea towel",
        phrase="a striped tea towel",
        reversible=False,
        warmth_plain=1,
        warmth_best=1,
        best_side="wrapped snugly",
        tags={"towel", "wrap"},
    ),
    "ribbon": Wrap(
        id="ribbon",
        label="ribbon",
        phrase="a shiny ribbon",
        reversible=False,
        warmth_plain=0,
        warmth_best=0,
        best_side="tied in a bow",
        weak=True,
        tags={"ribbon"},
    ),
}

THAWS = {
    "warm_water_bath": ThawMethod(
        id="warm_water_bath",
        label="warm water bath",
        sense=3,
        power=3,
        text="set the jug in a bowl of warm water and turned it slowly until the icy hush softened",
        qa_text="They thawed it by setting the jug in warm water and turning it slowly.",
        tags={"warm_water", "thaw"},
    ),
    "hearth_stool": ThawMethod(
        id="hearth_stool",
        label="hearth stool",
        sense=2,
        power=2,
        text="set the jug on the little stool by the hearth and waited while the cold knot melted loose",
        qa_text="They thawed it by warming the jug on a stool near the hearth.",
        tags={"hearth", "thaw"},
    ),
    "windowsill": ThawMethod(
        id="windowsill",
        label="windowsill",
        sense=1,
        power=0,
        text="set the jug on the frosty sill, which only made the cold sit tighter",
        qa_text="They put it on the frosty windowsill, which was not a good way to thaw it.",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "curious", "merry", "thoughtful", "gentle", "clever"]


def freeze_score(jug: JugKind, route: Route, wrap: Wrap, use_best_side: bool) -> int:
    warmth = wrap.warmth_best if use_best_side else wrap.warmth_plain
    return route.cold + jug.chill - warmth


def hazard_possible(jug: JugKind, route: Route) -> bool:
    return route.cold + jug.chill >= 2


def sensible_thaws() -> list[ThawMethod]:
    return [m for m in THAWS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, bool]]:
    combos: list[tuple[str, str, str, bool]] = []
    for drink_id in DRINKS:
        for jug_id, jug in JUGS.items():
            for route_id, route in ROUTES.items():
                if not hazard_possible(jug, route):
                    continue
                for wrap_id, wrap in WRAPS.items():
                    for use_best_side in ([False, True] if wrap.reversible else [False]):
                        if wrap.weak and freeze_score(jug, route, wrap, use_best_side) <= 0:
                            continue
                        combos.append((drink_id, jug_id, route_id, wrap_id if not use_best_side else f"{wrap_id}:best"))
    return combos


@dataclass
class StoryParams:
    drink: str
    jug: str
    route: str
    wrap: str
    use_best_side: bool
    thaw: str
    child: str
    gender: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def predict_freeze(jug: JugKind, route: Route, wrap: Wrap, use_best_side: bool) -> bool:
    return freeze_score(jug, route, wrap, use_best_side) >= 3


def thaw_success(method: ThawMethod, jug: JugKind, route: Route, wrap: Wrap, use_best_side: bool) -> bool:
    return method.power >= max(0, freeze_score(jug, route, wrap, use_best_side) - 1)


def outcome_of(params: StoryParams) -> str:
    jug = JUGS[params.jug]
    route = ROUTES[params.route]
    wrap = WRAPS[params.wrap]
    method = THAWS[params.thaw]
    if not predict_freeze(jug, route, wrap, params.use_best_side):
        return "safe"
    return "thawed" if thaw_success(method, jug, route, wrap, params.use_best_side) else "stuck"


def intro(world: World, child: Entity, helper: Entity, drink: Drink, jug_cfg: JugKind) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} had {jug_cfg.phrase}, and in it swam {drink.color} lights of {drink.label}."
    )
    world.say(
        f"{helper.id}, {child.pronoun('possessive')} {helper.label_word}, smiled and said, "
        f'"Step soft, step slow, and mind the winter glow."'
    )


def mission(world: World, child: Entity, route: Route) -> None:
    world.say(
        f"They meant to carry the jug {route.phrase}. {route.detail}"
    )


def prepare(world: World, child: Entity, wrap: Wrap, use_best_side: bool) -> None:
    child.memes["care"] += 1
    if wrap.reversible and use_best_side:
        world.say(
            f"{child.id} found {wrap.phrase} and turned it {wrap.best_side}. "
            f'"Reversible and clever," {child.pronoun()} sang in a little rhyme.'
        )
    else:
        world.say(
            f"{child.id} wrapped the jug in {wrap.phrase} and tucked the corners close."
        )


def suspense_walk(world: World, child: Entity, jug_cfg: JugKind, route: Route, wrap: Wrap, use_best_side: bool) -> None:
    jug = world.get("jug")
    score = freeze_score(jug_cfg, route, wrap, use_best_side)
    jug.meters["coldness"] = float(route.cold + jug_cfg.chill)
    jug.meters["warmth"] = float(wrap.warmth_best if use_best_side else wrap.warmth_plain)
    if score >= 3:
        jug.meters["freeze_risk"] += 1
        propagate(world, narrate=False)
        world.say(jug_cfg.clink)
        world.say(
            "Halfway there, the jug grew quiet. The drink stopped swishing and gave only a sleepy hush."
        )
        world.say(
            f'{child.id} held the handle still. "Oh dear, oh dear, will it freeze?" {child.pronoun()} whispered.'
        )
    else:
        child.memes["confidence"] += 1
        world.say(jug_cfg.clink)
        world.say(
            "The drink sloshed softly, not too fast and not too slow, like a song keeping time."
        )


def discover_problem(world: World, child: Entity, drink: Drink) -> None:
    jug = world.get("jug")
    if jug.meters["frozen"] >= THRESHOLD:
        child.memes["worry"] += 1
        world.say(
            f"When {child.id} peeped inside, {drink.warm_word} had turned to {drink.frozen_word}."
        )
        world.say(
            "It was a true transformation, but not the one the child had hoped to see."
        )


def solve(world: World, child: Entity, helper: Entity, method: ThawMethod) -> None:
    jug = world.get("jug")
    if jug.meters["frozen"] < THRESHOLD:
        jug.meters["flowing"] += 1
        propagate(world, narrate=False)
        return
    helper.memes["calm"] += 1
    child.memes["trust"] += 1
    world.say(
        f'"Hush now," said {helper.id}. "Cold can change a drink, and kindness can change it back."'
    )
    world.say(
        f"Together they {method.text}."
    )
    if method.power >= world.facts["freeze_need"]:
        jug.meters["frozen"] = 0.0
        jug.meters["flowing"] += 1
        child.memes["wonder"] += 1
        propagate(world, narrate=False)
    else:
        child.memes["worry"] += 1


def ending(world: World, child: Entity, helper: Entity, drink: Drink, wrap: Wrap, use_best_side: bool) -> None:
    jug = world.get("jug")
    if jug.meters["flowing"] >= THRESHOLD:
        if wrap.reversible and use_best_side:
            world.say(
                f"Soon the {drink.label} ran loose again, bright and smooth. {child.id} laughed, "
                f"for the reversible wrap had helped, and the warm trick had finished the job."
            )
        else:
            world.say(
                f"Soon the {drink.label} ran loose again, bright and smooth, and the room felt brave instead of cold."
            )
        world.say(
            f"So {child.id} poured a little cup for {helper.id}, and the jug that feared freeze now sang with steam."
        )
    else:
        world.say(
            f"The icy drink would not yet pour, so {child.id} and {helper.id} set it safely by and waited for more warmth."
        )
        world.say(
            "Even then, the child learned this winter thing: a pretty bow is not the same as a useful wrap."
        )


def tell(
    drink: Drink,
    jug_cfg: JugKind,
    route: Route,
    wrap: Wrap,
    thaw: ThawMethod,
    use_best_side: bool,
    child_name: str,
    gender: str,
    helper_name: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=gender, label=child_name, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name, role="helper"))
    jug = world.add(Entity(id="jug", type="jug", label=jug_cfg.label, phrase=jug_cfg.phrase))
    child.attrs["trait"] = trait

    intro(world, child, helper, drink, jug_cfg)
    mission(world, child, route)

    world.para()
    prepare(world, child, wrap, use_best_side)
    suspense_walk(world, child, jug_cfg, route, wrap, use_best_side)

    world.para()
    discover_problem(world, child, drink)
    need = max(0, freeze_score(jug_cfg, route, wrap, use_best_side) - 1)
    world.facts["freeze_need"] = need
    solve(world, child, helper, thaw)
    ending(world, child, helper, drink, wrap, use_best_side)

    world.facts.update(
        child=child,
        helper=helper,
        drink=drink,
        jug_cfg=jug_cfg,
        route=route,
        wrap=wrap,
        thaw=thaw,
        use_best_side=use_best_side,
        outcome="safe" if jug.meters["frozen"] < THRESHOLD and need == 0 else ("thawed" if jug.meters["flowing"] >= THRESHOLD else "stuck"),
        froze=need > 0,
    )
    return world


KNOWLEDGE = {
    "reversible": [
        (
            "What does reversible mean?",
            "Reversible means something can be used with either side showing. You can turn it over and use the other side."
        )
    ],
    "jug": [
        (
            "What is a jug?",
            "A jug is a container with a handle and a mouth for pouring. People use it to carry and pour drinks."
        )
    ],
    "freeze": [
        (
            "What does it mean when a drink starts to freeze?",
            "It means the cold is turning the liquid into ice or slush. The colder it gets, the harder it is to pour."
        )
    ],
    "warm_water": [
        (
            "Why can warm water help thaw something cold?",
            "Warm water gives gentle heat to the cold thing. That heat helps the ice loosen and melt."
        )
    ],
    "wool": [
        (
            "Why does a woolly wrap help in winter?",
            "A woolly wrap holds warmth in and keeps cold air out. That can help something stay warm for longer."
        )
    ],
    "winter": [
        (
            "Why can wind make things colder?",
            "Wind carries warmth away from surfaces. That makes hands, faces, and even a jug feel colder faster."
        )
    ],
}
KNOWLEDGE_ORDER = ["reversible", "jug", "freeze", "warm_water", "wool", "winter"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    drink = f["drink"]
    wrap = f["wrap"]
    route = f["route"]
    if f["outcome"] == "safe":
        return [
            f'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the words "reversible", "jug", and "freeze".',
            f"Tell a gentle suspense story where {child.id} carries {drink.label} in a jug {route.phrase}, worries it might freeze, and solves the problem before anything is lost.",
            f"Write a rhyming little winter story where a child uses {wrap.label} cleverly and ends with a warm pour and a happy sigh.",
        ]
    if f["outcome"] == "thawed":
        return [
            f'Write a nursery-rhyme style story that includes "reversible", "jug", and "freeze", and features a drink that changes and then changes back.',
            f"Tell a suspenseful winter story where {child.id}'s jug starts to freeze, but calm problem solving saves the day.",
            f"Write a child-facing rhyme tale with transformation: warm {drink.label} becomes icy, then flows again by the ending.",
        ]
    return [
        f'Write a nursery-rhyme style cautionary story that includes "reversible", "jug", and "freeze".',
        f"Tell a small winter story where {child.id} learns that a pretty wrap is not always a useful one.",
        f"Write a gentle suspense story with problem solving, but let the lesson be that some fixes take more time than a child first hopes.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    drink = f["drink"]
    route = f["route"]
    wrap = f["wrap"]
    thaw = f["thaw"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child carrying {drink.label} in a jug, and {helper.id}, the calm grown-up helper."
        ),
        (
            "Why was the walk suspenseful?",
            f"It felt suspenseful because the winter route was cold, and {child.id} could hear the jug grow quiet. The child knew the drink might freeze before it reached the table."
        ),
        (
            f"What did {child.id} use to wrap the jug?",
            f"{child.id} used {wrap.phrase}. That mattered because the wrap changed how much warmth the jug could keep."
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                "Did the drink freeze?",
                f"No. The drink stayed loose enough to swish and pour, so the danger passed before it became a real problem."
            )
        )
        qa.append(
            (
                "How was the problem solved?",
                f"The child prepared carefully before the walk, so the cold never won. Good wrapping and a short enough trip kept the jug safe."
            )
        )
    elif outcome == "thawed":
        qa.append(
            (
                "What transformation happened in the story?",
                f"The warm drink changed into icy slush when the cold won for a while. Then it changed back into a flowing drink after {child.id} and {helper.id} solved the problem."
            )
        )
        qa.append(
            (
                f"How did {helper.id} help?",
                f"{helper.id} stayed calm and chose {thaw.label}. {thaw.qa_text} That sensible step gave the frozen drink enough warmth to loosen."
            )
        )
    else:
        qa.append(
            (
                "Why did the plan not work right away?",
                f"The cold was stronger than the wrap and the thawing try. Because of that, the drink stayed icy and had to wait for more warmth."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned that winter problems need useful tools, not just pretty ones. A ribbon can look lovely on a jug, but it does not keep the cold out."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"jug", "freeze", "winter"}
    wrap = world.facts["wrap"]
    if wrap.reversible:
        tags.add("reversible")
    if "wool" in wrap.tags:
        tags.add("wool")
    if world.facts["thaw"].id == "warm_water_bath":
        tags.add("warm_water")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        drink="cider",
        jug="glass",
        route="porch",
        wrap="reversible_cozy",
        use_best_side=True,
        thaw="warm_water_bath",
        child="Lily",
        gender="girl",
        helper="Mama",
        helper_type="mother",
        trait="careful",
    ),
    StoryParams(
        drink="berry_juice",
        jug="tin",
        route="yard",
        wrap="tea_towel",
        use_best_side=False,
        thaw="warm_water_bath",
        child="Ben",
        gender="boy",
        helper="Dad",
        helper_type="father",
        trait="curious",
    ),
    StoryParams(
        drink="soup",
        jug="tin",
        route="yard",
        wrap="ribbon",
        use_best_side=False,
        thaw="hearth_stool",
        child="Mia",
        gender="girl",
        helper="Mama",
        helper_type="mother",
        trait="clever",
    ),
    StoryParams(
        drink="cider",
        jug="stoneware",
        route="pantry",
        wrap="tea_towel",
        use_best_side=False,
        thaw="hearth_stool",
        child="Theo",
        gender="boy",
        helper="Dad",
        helper_type="father",
        trait="gentle",
    ),
]


def explain_wrap(wrap_id: str) -> str:
    wrap = WRAPS[wrap_id]
    if wrap.weak:
        good = ", ".join(sorted(w.id for w in WRAPS.values() if not w.weak))
        return (
            f"(Refusing wrap '{wrap_id}': it looks nice, but it does not keep a jug warm enough for this world. "
            f"Try one of these instead: {good}.)"
        )
    return ""


def explain_thaw(thaw_id: str) -> str:
    method = THAWS[thaw_id]
    if method.sense < SENSE_MIN:
        good = ", ".join(sorted(m.id for m in sensible_thaws()))
        return (
            f"(Refusing thaw '{thaw_id}': it is not a sensible way to solve the freezing problem here. "
            f"Try: {good}.)"
        )
    return ""


ASP_RULES = r"""
hazard(J, R) :- jug(J), route(R), chill(J, C), cold(R, D), C + D >= 2.

good_wrap(W) :- wrap(W), weak(W, 0).
usable(D, J, R, W, 0) :- drink(D), jug(J), route(R), wrap(W), hazard(J, R), good_wrap(W).
usable(D, J, R, W, 1) :- drink(D), jug(J), route(R), wrap(W), hazard(J, R), reversible(W), good_wrap(W).

score(J, R, W, 0, S) :- chill(J, C), cold(R, D), warmth_plain(W, WP), S = C + D - WP.
score(J, R, W, 1, S) :- chill(J, C), cold(R, D), warmth_best(W, WB), S = C + D - WB.

freezes(J, R, W, B) :- score(J, R, W, B, S), S >= 3.

sensible_thaw(T) :- thaw(T), sense(T, S), sense_min(M), S >= M.
need(J, R, W, B, N) :- score(J, R, W, B, S), S > 1, N = S - 1.
need(J, R, W, B, 0) :- score(J, R, W, B, S), S <= 1.
thaws(T, J, R, W, B) :- thaw(T), need(J, R, W, B, N), power(T, P), P >= N.

outcome(D, J, R, W, B, safe) :- usable(D, J, R, W, B), not freezes(J, R, W, B).
outcome(D, J, R, W, B, thawed) :- usable(D, J, R, W, B), freezes(J, R, W, B), chosen_thaw(T), thaws(T, J, R, W, B).
outcome(D, J, R, W, B, stuck) :- usable(D, J, R, W, B), freezes(J, R, W, B), chosen_thaw(T), not thaws(T, J, R, W, B).

valid(D, J, R, W, B) :- usable(D, J, R, W, B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for drink_id in DRINKS:
        lines.append(asp.fact("drink", drink_id))
    for jug_id, jug in JUGS.items():
        lines.append(asp.fact("jug", jug_id))
        lines.append(asp.fact("chill", jug_id, jug.chill))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("cold", route_id, route.cold))
    for wrap_id, wrap in WRAPS.items():
        lines.append(asp.fact("wrap", wrap_id))
        lines.append(asp.fact("warmth_plain", wrap_id, wrap.warmth_plain))
        lines.append(asp.fact("warmth_best", wrap_id, wrap.warmth_best))
        lines.append(asp.fact("weak", wrap_id, 1 if wrap.weak else 0))
        if wrap.reversible:
            lines.append(asp.fact("reversible", wrap_id))
    for thaw_id, thaw in THAWS.items():
        lines.append(asp.fact("thaw", thaw_id))
        lines.append(asp.fact("sense", thaw_id, thaw.sense))
        lines.append(asp.fact("power", thaw_id, thaw.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_thaws() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_thaw/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_thaw"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_thaw", params.thaw),
            asp.fact("chosen_drink", params.drink),
            asp.fact("chosen_jug", params.jug),
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_wrap", params.wrap),
            asp.fact("chosen_best", 1 if params.use_best_side else 0),
            f"selected_outcome(O) :- outcome({params.drink}, {params.jug}, {params.route}, {params.wrap}, {1 if params.use_best_side else 0}, O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A nursery-rhyme winter storyworld about a jug that may freeze and a child who solves the problem."
    )
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--jug", choices=JUGS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--wrap", choices=WRAPS)
    ap.add_argument("--best-side", action="store_true", help="turn the reversible wrap to its warmest side when possible")
    ap.add_argument("--thaw", choices=THAWS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
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
    if args.wrap and WRAPS[args.wrap].weak:
        raise StoryError(explain_wrap(args.wrap))
    if args.thaw and THAWS[args.thaw].sense < SENSE_MIN:
        raise StoryError(explain_thaw(args.thaw))

    combos: list[tuple[str, str, str, str, bool]] = []
    for drink_id in DRINKS:
        if args.drink and drink_id != args.drink:
            continue
        for jug_id, jug in JUGS.items():
            if args.jug and jug_id != args.jug:
                continue
            for route_id, route in ROUTES.items():
                if args.route and route_id != args.route:
                    continue
                if not hazard_possible(jug, route):
                    continue
                for wrap_id, wrap in WRAPS.items():
                    if args.wrap and wrap_id != args.wrap:
                        continue
                    if wrap.weak:
                        continue
                    if wrap.reversible:
                        if args.best_side:
                            combos.append((drink_id, jug_id, route_id, wrap_id, True))
                        else:
                            combos.extend(
                                [
                                    (drink_id, jug_id, route_id, wrap_id, False),
                                    (drink_id, jug_id, route_id, wrap_id, True),
                                ]
                            )
                    else:
                        if not args.best_side:
                            combos.append((drink_id, jug_id, route_id, wrap_id, False))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    drink_id, jug_id, route_id, wrap_id, use_best_side = rng.choice(sorted(set(combos)))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    helper = "Mama" if parent_type == "mother" else "Dad"
    trait = rng.choice(TRAITS)
    thaw_choices = [m.id for m in sensible_thaws()]
    thaw_id = args.thaw or rng.choice(sorted(thaw_choices))
    return StoryParams(
        drink=drink_id,
        jug=jug_id,
        route=route_id,
        wrap=wrap_id,
        use_best_side=use_best_side,
        thaw=thaw_id,
        child=child,
        gender=gender,
        helper=helper,
        helper_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.drink not in DRINKS:
        raise StoryError(f"(Unknown drink: {params.drink})")
    if params.jug not in JUGS:
        raise StoryError(f"(Unknown jug: {params.jug})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.wrap not in WRAPS:
        raise StoryError(f"(Unknown wrap: {params.wrap})")
    if params.thaw not in THAWS:
        raise StoryError(f"(Unknown thaw method: {params.thaw})")
    if WRAPS[params.wrap].weak:
        raise StoryError(explain_wrap(params.wrap))
    if THAWS[params.thaw].sense < SENSE_MIN:
        raise StoryError(explain_thaw(params.thaw))

    world = tell(
        drink=DRINKS[params.drink],
        jug_cfg=JUGS[params.jug],
        route=ROUTES[params.route],
        wrap=WRAPS[params.wrap],
        thaw=THAWS[params.thaw],
        use_best_side=params.use_best_side and WRAPS[params.wrap].reversible,
        child_name=params.child,
        gender=params.gender,
        helper_name=params.helper,
        helper_type=params.helper_type,
        trait=params.trait,
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


def asp_verify() -> int:
    rc = 0

    python_valid = set(
        (d, j, r, w, 1 if b else 0)
        for d in DRINKS
        for j, jug in JUGS.items()
        for r, route in ROUTES.items()
        if hazard_possible(jug, route)
        for w, wrap in WRAPS.items()
        if not wrap.weak
        for b in ([False, True] if wrap.reversible else [False])
    )
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid combos ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    py_sens = {m.id for m in sensible_thaws()}
    asp_sens = set(asp_sensible_thaws())
    if py_sens == asp_sens:
        print(f"OK: sensible thaw methods match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible thaw methods: python={sorted(py_sens)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(25):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show sensible_thaw/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible thaw methods: {', '.join(asp_sensible_thaws())}\n")
        print(f"{len(combos)} compatible (drink, jug, route, wrap, best_side) combos:\n")
        for drink, jug, route, wrap, best in combos:
            print(f"  {drink:11} {jug:10} {route:8} {wrap:17} best_side={bool(best)}")
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
            header = (
                f"### {p.child}: {p.drink} in a {p.jug} jug by the {p.route} route "
                f"({p.wrap}, outcome={outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
