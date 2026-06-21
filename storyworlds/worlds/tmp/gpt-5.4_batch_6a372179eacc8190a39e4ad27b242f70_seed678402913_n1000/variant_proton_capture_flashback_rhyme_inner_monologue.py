#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/variant_proton_capture_flashback_rhyme_inner_monologue.py
====================================================================================

A standalone story world about a child building a tiny atom craft, watching a
red proton piece roll toward trouble, and remembering the calm way to capture it.

Seed requirements folded into the world model:
- includes the words "variant", "proton", and "capture"
- uses Flashback
- uses Inner Monologue
- keeps the prose in a gentle Rhyming Story style

Run it
------
python storyworlds/worlds/gpt-5.4/variant_proton_capture_flashback_rhyme_inner_monologue.py
python storyworlds/worlds/gpt-5.4/variant_proton_capture_flashback_rhyme_inner_monologue.py --place porch --route drain --tool cup
python storyworlds/worlds/gpt-5.4/variant_proton_capture_flashback_rhyme_inner_monologue.py --tool hand
python storyworlds/worlds/gpt-5.4/variant_proton_capture_flashback_rhyme_inner_monologue.py --all
python storyworlds/worlds/gpt-5.4/variant_proton_capture_flashback_rhyme_inner_monologue.py --qa --json
python storyworlds/worlds/gpt-5.4/variant_proton_capture_flashback_rhyme_inner_monologue.py --verify
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
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    afford_routes: set[str] = field(default_factory=set)
    helper_type: str = "mother"
    detail: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class VariantCfg:
    id: str
    label: str
    bounce: int = 0
    opening: str = ""
    ending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    speed: int = 1
    risky: bool = True
    toward: str = ""
    loss_text: str = ""
    saved_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sense: int = 2
    power: int = 1
    method: str = ""
    fail: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    variant: str
    route: str
    tool: str
    child_name: str
    child_gender: str
    helper: str
    delay: int = 0
    seed: Optional[int] = None


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
        clone = World(self.setting)
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


def _r_roll_alarm(world: World) -> list[str]:
    proton = world.entities.get("proton")
    child = world.entities.get("child")
    route = world.entities.get("route")
    if not proton or not child or not route:
        return []
    if proton.meters["rolling"] < THRESHOLD:
        return []
    sig = ("roll_alarm", route.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    route.meters["danger"] += 1
    return []


def _r_captured_relief(world: World) -> list[str]:
    proton = world.entities.get("proton")
    child = world.entities.get("child")
    if not proton or not child:
        return []
    if proton.meters["captured"] < THRESHOLD:
        return []
    sig = ("captured_relief", proton.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    return []


def _r_lost_sadness(world: World) -> list[str]:
    proton = world.entities.get("proton")
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not proton or not child or not helper:
        return []
    if proton.meters["lost"] < THRESHOLD:
        return []
    sig = ("lost_sadness", proton.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["sadness"] += 1
    helper.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="roll_alarm", tag="physical", apply=_r_roll_alarm),
    Rule(name="captured_relief", tag="emotional", apply=_r_captured_relief),
    Rule(name="lost_sadness", tag="emotional", apply=_r_lost_sadness),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) > before:
                changed = True


def place_supports(setting: Setting, route: Route) -> bool:
    return route.id in setting.afford_routes


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def severity(variant: VariantCfg, route: Route, delay: int) -> int:
    return variant.bounce + route.speed + delay


def is_captured(variant: VariantCfg, route: Route, tool: Tool, delay: int) -> bool:
    return tool.power >= severity(variant, route, delay)


def predict_outcome(variant: VariantCfg, route: Route, tool: Tool, delay: int) -> dict:
    return {
        "severity": severity(variant, route, delay),
        "captured": is_captured(variant, route, tool, delay),
    }


def introduce(world: World, child: Entity, helper: Entity, variant: VariantCfg) -> None:
    child.memes["joy"] += 1
    world.say(
        f"At {world.setting.place}, {child.id} worked beside {child.pronoun('possessive')} "
        f"{helper.label_word} and built {variant.opening}."
    )
    world.say(
        f"It was a bright little atom craft, a happy variant with paper rings in a swing and a string."
    )
    world.say(
        f"In the middle sat a small red proton bead, round as a berry and shiny with speed."
    )


def admire(world: World, child: Entity, variant: VariantCfg) -> None:
    world.say(
        f'{child.id} tipped {child.pronoun("possessive")} head and whispered, '
        f'"This {variant.label} looks right tonight; it glows so small, and still so bright."'
    )


def wobble(world: World, child: Entity, proton: Entity, route_cfg: Route) -> None:
    proton.meters["rolling"] += 1
    proton.meters["near_loss"] += 1
    propagate(world)
    world.say(
        f"Then the tray gave a tiny slide, and the proton began to glide."
    )
    world.say(
        f"It skipped and clicked and rolled {route_cfg.toward}, quick as a bead in a drum-drum ride."
    )


def inner_monologue(world: World, child: Entity, route_cfg: Route, tool: Tool, variant: VariantCfg) -> None:
    child.memes["worry"] += 1
    outlook = predict_outcome(variant, route_cfg, tool, world.facts["delay"])
    if outlook["captured"]:
        tail = f"If I stay low and steady, maybe {tool.label} is ready."
    else:
        tail = f"If I rush with {tool.label}, that bead may still wriggle free."
    world.say(
        f'Inside {child.id} came a quick small song: "Oh no, oh no, don\'t roll along. '
        f'{tail}"'
    )


def flashback(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.memes["memory"] += 1
    world.say(
        f"A flashback fluttered through {child.id}'s mind like a ribbon in rewind."
    )
    world.say(
        f"Yesterday, {helper.label_word} had tipped {tool.phrase} low and said, "
        f'"Do not swat when little things scoot. Scoop slow, stay near, and give them room to root."'
    )


def reach(world: World, child: Entity, tool: Tool) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} reached for {tool.phrase} and bent down low, slow as snow."
    )


def capture_success(world: World, child: Entity, helper: Entity, proton: Entity, route_cfg: Route, tool: Tool, variant: VariantCfg) -> None:
    proton.meters["captured"] += 1
    proton.meters["rolling"] = 0.0
    world.get("route").meters["danger"] = 0.0
    propagate(world)
    world.say(
        f"{tool.method} {route_cfg.saved_text}"
    )
    world.say(
        f'"I made the capture!" {child.id} cheered. The red proton rested safe and near.'
    )
    world.say(
        f"Soon the craft was whole again, and {variant.ending}"
    )


def capture_fail(world: World, child: Entity, helper: Entity, proton: Entity, route_cfg: Route, tool: Tool, variant: VariantCfg) -> None:
    proton.meters["lost"] += 1
    proton.meters["rolling"] = 0.0
    propagate(world)
    world.say(
        f"{tool.fail} {route_cfg.loss_text}"
    )
    world.say(
        f"{child.id}'s shoulders sank a little low. 'I tried,' {child.pronoun()} said, soft as snow."
    )
    world.say(
        f"But {helper.label_word} knelt by {child.pronoun('object')} with a gentle grin. "
        f'"We can make one more and begin again."'
    )
    world.say(
        f"Together they rolled a new red bead, slower this time, with patient heed. "
        f"By sunset the craft still sang {variant.ending}"
    )


def ending_image(world: World, child: Entity, helper: Entity, variant: VariantCfg, captured: bool) -> None:
    if captured:
        world.say(
            f"{child.id} held the little model high. It bobbed but did not say goodbye."
        )
    else:
        world.say(
            f"{child.id} held the rebuilt model high. This time the proton stayed nearby."
        )
    world.say(
        f"{helper.label_word.capitalize()} smiled, and the rings turned light, making a soft small moonlit sight."
    )


def tell(
    setting: Setting,
    variant: VariantCfg,
    route_cfg: Route,
    tool: Tool,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, phrase=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="the helper", role="helper"))
    proton = world.add(Entity(id="proton", type="bead", label="proton", phrase="a red proton bead"))
    route = world.add(Entity(id="route", type="route", label=route_cfg.label, phrase=route_cfg.label))
    child.attrs["name"] = child_name
    world.facts["delay"] = delay

    introduce(world, child, helper, variant)
    admire(world, child, variant)

    world.para()
    wobble(world, child, proton, route_cfg)
    inner_monologue(world, child, route_cfg, tool, variant)
    flashback(world, child, helper, tool)
    reach(world, child, tool)

    world.para()
    captured = is_captured(variant, route_cfg, tool, delay)
    if captured:
        capture_success(world, child, helper, proton, route_cfg, tool, variant)
    else:
        capture_fail(world, child, helper, proton, route_cfg, tool, variant)
    ending_image(world, child, helper, variant, captured)

    world.facts.update(
        child=child,
        helper=helper,
        proton=proton,
        variant=variant,
        route_cfg=route_cfg,
        route=route,
        tool=tool,
        outcome="captured" if captured else "lost",
        severity=severity(variant, route_cfg, delay),
        captured=captured,
        flashback=True,
        inner_monologue=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen table",
        afford_routes={"crack"},
        helper_type="mother",
        detail="Sunlight made squares on the table.",
        tags={"home"},
    ),
    "classroom": Setting(
        id="classroom",
        place="the classroom art table",
        afford_routes={"crack", "vent"},
        helper_type="teacher",
        detail="Glue sticks and crayons stood in a bright row.",
        tags={"school"},
    ),
    "porch": Setting(
        id="porch",
        place="the back porch",
        afford_routes={"drain"},
        helper_type="father",
        detail="A warm wind hummed at the steps.",
        tags={"outside"},
    ),
}

VARIANTS = {
    "moon": VariantCfg(
        id="moon",
        label="moon variant",
        bounce=0,
        opening="a moon variant of the class atom",
        ending="with calm little rings that could sway and stay",
        tags={"variant"},
    ),
    "rainbow": VariantCfg(
        id="rainbow",
        label="rainbow variant",
        bounce=1,
        opening="a rainbow variant of the class atom",
        ending="with bright little rings that could sing in a swing",
        tags={"variant", "color"},
    ),
    "comet": VariantCfg(
        id="comet",
        label="comet variant",
        bounce=1,
        opening="a comet variant of the class atom",
        ending="with tails of paper that fluttered together",
        tags={"variant", "space"},
    ),
}

ROUTES = {
    "crack": Route(
        id="crack",
        label="floor crack",
        speed=1,
        risky=True,
        toward="toward a thin floor crack",
        loss_text="The bead gave one last tic-tic kick and slipped into the crack.",
        saved_text="The bead tapped the rim, bounced once, and settled inside the cup before the crack could keep it.",
        tags={"crack"},
    ),
    "drain": Route(
        id="drain",
        label="porch drain",
        speed=2,
        risky=True,
        toward="toward the porch drain",
        loss_text="The bead spun in a tiny ring and vanished down the drain.",
        saved_text="The cup slid over it just in time, and the drain got only a cold small shine.",
        tags={"drain"},
    ),
    "vent": Route(
        id="vent",
        label="heater vent",
        speed=3,
        risky=True,
        toward="toward the heater vent",
        loss_text="The bead rattled through the slats and was gone below the vent.",
        saved_text="The cup covered it with a soft quick tap, and the vent kept only dust, not the atom map.",
        tags={"vent"},
    ),
    "rug": Route(
        id="rug",
        label="soft rug edge",
        speed=0,
        risky=False,
        toward="toward the soft rug edge",
        loss_text="The bead hid in the rug fluff.",
        saved_text="The bead stopped in the rug fringe and never really escaped.",
        tags={"rug"},
    ),
}

TOOLS = {
    "cup": Tool(
        id="cup",
        label="cup",
        phrase="a clear plastic cup",
        sense=3,
        power=4,
        method="The cup came down in a quiet swoop, not a slap but a careful scoop.",
        fail="The cup chased after the bead, but the roll was too fast and the reach too late.",
        qa_text="used a clear plastic cup to scoop over the bead",
        tags={"cup", "capture"},
    ),
    "lid": Tool(
        id="lid",
        label="jar lid",
        phrase="a wide jar lid",
        sense=3,
        power=2,
        method="The jar lid skimmed low like a little boat, and the bead bumped in with a bright red note.",
        fail="The jar lid scraped close, but the bead hopped off its edge and kept going.",
        qa_text="slid a wide jar lid low to trap the bead",
        tags={"lid", "capture"},
    ),
    "net": Tool(
        id="net",
        label="small net",
        phrase="a small toy net",
        sense=2,
        power=2,
        method="The net dipped gently, and the bead landed in its cloth nest.",
        fail="The net waved overhead, but the bead stayed low and slipped underneath.",
        qa_text="dipped a small net down to catch the bead",
        tags={"net", "capture"},
    ),
    "hand": Tool(
        id="hand",
        label="bare hand",
        phrase="a bare hand",
        sense=1,
        power=1,
        method="The hand closed fast around the bead.",
        fail="The fingers poked too sharply, and the bead shot ahead even faster.",
        qa_text="grabbed with a bare hand",
        tags={"hand"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "June", "Ruby", "Ella", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Finn", "Jude", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for variant_id in VARIANTS:
            for route_id, route in ROUTES.items():
                if route.risky and place_supports(setting, route):
                    combos.append((place_id, variant_id, route_id))
    return combos


KNOWLEDGE = {
    "proton": [
        (
            "What is a proton?",
            "A proton is a tiny part inside the middle of an atom. In this story, the child used a red bead to stand for one."
        )
    ],
    "variant": [
        (
            "What is a variant?",
            "A variant is one version of something that can come in different versions. It is still the same kind of thing, just made a little differently."
        )
    ],
    "capture": [
        (
            "What does capture mean?",
            "Capture can mean gently catching something so it does not get away. In this story, it means stopping the bead before it rolled into trouble."
        )
    ],
    "drain": [
        (
            "Why can a drain make a small toy or bead hard to get back?",
            "A drain has holes or a pipe below it, so a tiny object can slip down where hands cannot easily reach. That is why people try to stop little things before they fall in."
        )
    ],
    "vent": [
        (
            "Why can a floor vent be tricky for tiny objects?",
            "A vent has slats and open space below them, so a small bead can slip through. Once it drops inside, it can be hard to find."
        )
    ],
    "crack": [
        (
            "Why can a floor crack swallow a bead?",
            "A crack is a narrow opening, and small round things can roll into it. Their shape makes them move easily."
        )
    ],
    "cup": [
        (
            "Why is a cup a good tool for catching a rolling bead?",
            "A cup can cover the bead from above and stop its path. It works best when you move slowly and place it low."
        )
    ],
    "lid": [
        (
            "How can a lid help catch something small?",
            "A wide lid can slide in front of a bead and make a small wall. If the bead is not too fast, the lid can trap it."
        )
    ],
    "net": [
        (
            "What does a small net do?",
            "A small net gives a soft place for something to land. It works best when the moving thing pops up enough to fall into it."
        )
    ],
}

KNOWLEDGE_ORDER = ["variant", "proton", "capture", "drain", "vent", "crack", "cup", "lid", "net"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    variant = f["variant"]
    route_cfg = f["route_cfg"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that uses the words "variant", "proton", and "capture".',
        f"Tell a gentle story where a child named {child.attrs['name']} builds a {variant.label}, then a red proton bead rolls toward a {route_cfg.label}. Include an inner monologue and a flashback.",
        "Write a small science-flavored bedtime story in rhyme where a careful memory helps a child solve a sudden problem."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    variant = f["variant"]
    route_cfg = f["route_cfg"]
    tool = f["tool"]
    outcome = f["outcome"]
    child_name = child.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, who was making a {variant.label}, and {child.pronoun('possessive')} {helper.label_word}, who stayed close by. They were working together on a tiny atom craft."
        ),
        (
            "What was the red bead supposed to be?",
            "The red bead was the proton in the child's atom craft. It was a pretend model piece for something very tiny."
        ),
        (
            "Why did the child get scared?",
            f"{child_name} got scared because the proton bead began rolling {route_cfg.toward}. If it reached the {route_cfg.label}, it could be lost."
        ),
        (
            "What was the flashback about?",
            f"The flashback was about {helper.label_word} showing how to scoop low and slowly with {tool.phrase}. That memory gave {child_name} a calmer plan."
        ),
        (
            "What was the child's inner monologue doing in the story?",
            f"It let us hear {child_name}'s quick worried thoughts while the bead was rolling. The little thought-song showed fear first, then a careful choice."
        ),
    ]
    if outcome == "captured":
        qa.append(
            (
                f"How did {child_name} solve the problem?",
                f"{child_name} {tool.qa_text}. The slow, low move stopped the bead before it could reach the {route_cfg.label}."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the proton safe and the atom craft whole again. The final image showed the model bobbing gently instead of losing its middle piece."
            )
        )
    else:
        qa.append(
            (
                f"Did {child_name} capture the proton in time?",
                f"No. {tool.fail} and the bead was lost in the {route_cfg.label}. After that, {helper.label_word} kindly helped make another red bead so the craft could be finished anyway."
            )
        )
        qa.append(
            (
                "How did the story still end with hope?",
                f"The first proton was lost, but the child was not left alone with that sad feeling. Together they made a new bead and finished the model more carefully."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"variant", "proton", "capture"} | set(f["route_cfg"].tags) | set(f["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        variant="moon",
        route="crack",
        tool="lid",
        child_name="Mina",
        child_gender="girl",
        helper="mother",
        delay=0,
    ),
    StoryParams(
        place="porch",
        variant="rainbow",
        route="drain",
        tool="cup",
        child_name="Owen",
        child_gender="boy",
        helper="father",
        delay=0,
    ),
    StoryParams(
        place="classroom",
        variant="comet",
        route="vent",
        tool="net",
        child_name="Lila",
        child_gender="girl",
        helper="teacher",
        delay=1,
    ),
    StoryParams(
        place="classroom",
        variant="rainbow",
        route="vent",
        tool="cup",
        child_name="Theo",
        child_gender="boy",
        helper="teacher",
        delay=0,
    ),
]


def explain_rejection(place: str, route: Route) -> str:
    if not route.risky:
        return (
            f"(No story: {route.label} is not a real losing hazard here, so there is no strong need for a rescue or capture beat. "
            f"Pick a route like crack, drain, or vent.)"
        )
    return (
        f"(No story: {route.label} does not fit {SETTINGS[place].place}. "
        f"Pick a route that could really be there.)"
    )


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense "
        f"(sense={tool.sense} < {SENSE_MIN}). A careful capture should use something steadier. Try: {better}.)"
    )


ASP_RULES = r"""
sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
valid(P, V, R) :- setting(P), variant(V), route(R), affords(P, R), risky(R).

severity(SP + B + D) :- chosen_route(R), speed(R, SP),
                        chosen_variant(V), bounce(V, B),
                        delay(D).
captured :- chosen_tool(T), power(T, P), severity(S), P >= S.
outcome(captured) :- captured.
outcome(lost) :- not captured.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for route_id in sorted(setting.afford_routes):
            lines.append(asp.fact("affords", place_id, route_id))
    for variant_id, variant in VARIANTS.items():
        lines.append(asp.fact("variant", variant_id))
        lines.append(asp.fact("bounce", variant_id, variant.bounce))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("speed", route_id, route.speed))
        if route.risky:
            lines.append(asp.fact("risky", route_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_variant", params.variant),
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_tool", params.tool),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    variant = VARIANTS[params.variant]
    route = ROUTES[params.route]
    tool = TOOLS[params.tool]
    return "captured" if is_captured(variant, route, tool, params.delay) else "lost"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_tools = set(asp_sensible())
    python_tools = {t.id for t in sensible_tools()}
    if clingo_tools == python_tools:
        print(f"OK: sensible tools match ({sorted(clingo_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(clingo_tools)} python={sorted(python_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a rolling proton bead, a remembered lesson, and a careful capture."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--variant", choices=VARIANTS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=["mother", "father", "teacher"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much of a head start the rolling bead gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    if args.place and args.route:
        route = ROUTES[args.route]
        if not place_supports(SETTINGS[args.place], route) or not route.risky:
            raise StoryError(explain_rejection(args.place, route))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.variant is None or combo[1] == args.variant)
        and (args.route is None or combo[2] == args.route)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, variant, route = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(t.id for t in sensible_tools()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or SETTINGS[place].helper_type
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place,
        variant=variant,
        route=route,
        tool=tool,
        child_name=name,
        child_gender=gender,
        helper=helper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.variant not in VARIANTS:
        raise StoryError(f"(Unknown variant: {params.variant})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if TOOLS[params.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))
    if not place_supports(SETTINGS[params.place], ROUTES[params.route]) or not ROUTES[params.route].risky:
        raise StoryError(explain_rejection(params.place, ROUTES[params.route]))

    world = tell(
        setting=SETTINGS[params.place],
        variant=VARIANTS[params.variant],
        route_cfg=ROUTES[params.route],
        tool=TOOLS[params.tool],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
        delay=params.delay,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, variant, route) combos:\n")
        for place, variant, route in combos:
            print(f"  {place:10} {variant:8} {route}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.variant} at {p.place} ({p.route}, {p.tool}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
