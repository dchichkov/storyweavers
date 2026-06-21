#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ignite_graze_bad_ending_transformation_nursery_rhyme.py
========================================================================================

A small nursery-rhyme storyworld about a forbidden spark, a graze of danger,
and a transformation that ends badly.

Seed words: ignite, graze
Style: Nursery Rhyme
Features: Bad Ending, Transformation

The storyworld is intentionally tiny and classical:
- a child and a small helper
- a forbidden flame source
- a nearby flammable place or object
- a grown-up response that may come too late
- a bad ending where the scene transforms into soot and loss

The prose aims for a sing-song, child-facing feel, while the world model keeps
the story state-driven rather than frozen.
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
    flammable: bool = False
    makes_flame: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma",
                "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    play: str
    title_child: str
    title_helper: str
    dark_place: str
    sendoff: str


@dataclass
class FlameTool:
    id: str
    label: str
    phrase: str
    where: str
    makes_flame: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class FlammableThing:
    id: str
    label: str
    the: str
    near: str
    drape: str
    spread: int = 2
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    forbidden: str
    target: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_type: str
    delay: int = 0
    seed: Optional[int] = None


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    if world.get("target").meters["burning"] < THRESHOLD:
        return out
    sig = ("spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["danger"] += 1
    world.get("child").memes["fear"] += 1
    world.get("helper").memes["fear"] += 1
    out.append("__fire__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(tool: FlameTool, target: FlammableThing) -> bool:
    return tool.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: FlammableThing, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: FlammableThing, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def _ignite(world: World, target: Entity) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=False)


def predict(world: World, target_id: str) -> dict:
    sim = world.copy()
    _ignite(sim, sim.get(target_id))
    return {
        "ignites": sim.get(target_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def start(world: World, child: Entity, helper: Entity, theme: Theme) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Under a nursery moon, {child.id} and {helper.id} made a little play. "
        f"{theme.play}"
    )
    world.say(
        f'"{theme.title_child} {child.id} and {theme.title_helper} {helper.id}!" '
        f"{child.id} sang. " +
        f'"Let us seek {theme.dark_place}!"'
    )


def need_light(world: World, helper: Entity, theme: Theme, target: FlammableThing) -> None:
    world.say(
        f"But the little nook -- {theme.dark_place}, {target.drape} -- was dim and deep."
    )
    world.say(f'"We need a light," said {helper.id}, soft as sleep.')


def tempt(world: World, child: Entity, tool: FlameTool) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} lifted a chin. "I know! {tool.label.capitalize()}!" '
        f"{tool.phrase} sat {tool.where}."
    )


def warn(world: World, helper: Entity, child: Entity, tool: FlameTool, target: FlammableThing) -> None:
    pred = predict(world, "target")
    helper.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{helper.id} bit {helper.pronoun("possessive")} lip. "{child.id}, no, no, '
        f"{tool.label} can make a real flame, and {target.the} can catch."
        f'"'
    )


def defy(world: World, child: Entity, tool: FlameTool) -> None:
    child.memes["defiance"] += 1
    world.say(f'{"But"} {child.id} would not wait, and ran to get {tool.label}.')


def ignite_scene(world: World, tool: FlameTool, target: FlammableThing) -> None:
    _ignite(world, world.get("target"))
    world.say(
        f"{tool.label.capitalize()} did ignite. It flashed like a star, then grazed "
        f"{target.near}, and a thin gold line began to climb."
    )


def cry_alarm(world: World, child: Entity, helper: Entity, target: FlammableThing, parent: Entity) -> None:
    world.say(f'"{child.id}! Fire! {target.The}!" cried {helper.id}.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue_fail(world: World, parent: Entity, response: Response, target: FlammableThing) -> None:
    world.get("room").meters["burning"] += 1
    world.get("target").meters["burning"] += 1
    propagate(world, narrate=False)
    world.say(f"{parent.label_word.capitalize()} came hurrying, but {response.fail.replace('{target}', target.label)}.")
    world.say(f"The flames leapt and laughed, and the little room turned to smoke.")


def ending(world: World, child: Entity, helper: Entity, parent: Entity, theme: Theme, target: FlammableThing) -> None:
    child.memes["fear"] += 1
    helper.memes["fear"] += 1
    world.say("Then the moon looked pale, and the nursery held its breath.")
    world.say(
        f"{parent.label_word.capitalize()} held them close and said, "
        f'"Safe or sorry, little ones, fire grows bigger than a game."'
    )
    world.say(
        f"The {theme.dark_place} was never the same; the bright thing turned to soot, "
        f"and the old play transformed into a sad black frame."
    )
    world.say(
        f"They went to bed with quiet feet, and the story ended small and dim: "
        f"no treasure found, no song to sing, and no warm light came again for him."
    )


def tell(theme: Theme, tool: FlameTool, target: FlammableThing, response: Response,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Mina", helper_gender: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    tgt = world.add(Entity(id="target", type="target", label=target.label, flammable=target.flammable))
    world.facts["delay"] = delay

    start(world, child, helper, theme)
    need_light(world, helper, theme, target)
    world.para()
    tempt(world, child, tool)
    warn(world, helper, child, tool, target)
    world.para()
    defy(world, child, tool)
    ignite_scene(world, tool, target)
    cry_alarm(world, child, helper, target, parent)
    world.para()
    severity = fire_severity(target, delay)
    tgt.meters["severity"] = float(severity)
    if is_contained(response, target, delay):
        # This world is designed to lean bad, but keep the branch for completeness.
        world.say(f"{parent.label_word.capitalize()} managed to stop the fire in time.")
        world.say("The room changed back to calm, and the rhyme would have ended bright.")
    else:
        rescue_fail(world, parent, response, target)
        ending(world, child, helper, parent, theme, target)

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        theme=theme,
        tool=tool,
        target_cfg=target,
        target=tgt,
        room=room,
        response=response,
        outcome="burned" if not is_contained(response, target, delay) else "contained",
        ignited=tgt.meters["scorched"] >= THRESHOLD,
    )
    return world


THEMES = {
    "nursery": Theme(
        id="nursery",
        scene="A cradle-song was in the air, and little toys were laid with care.",
        play="A blanket fort stood by the wall, with paper stars and ribbons small.",
        title_child="Little",
        title_helper="Tiny",
        dark_place="the corner under the shelf",
        sendoff="",
    ),
    "lantern": Theme(
        id="lantern",
        scene="A bedtime bell was soft and low, and shadows swayed in gentle row.",
        play="A toy boat rocked upon the rug, and picture books sat snug and snug.",
        title_child="Little",
        title_helper="Tiny",
        dark_place="the nook behind the curtain",
        sendoff="",
    ),
}

FORBIDDEN = {
    "match": FlameTool(
        id="match",
        label="match",
        phrase="a tiny box of matches",
        where="in the drawer",
        makes_flame=True,
        tags={"match", "fire"},
    ),
    "sparkler": FlameTool(
        id="sparkler",
        label="sparkler",
        phrase="a sparkler from the cake box",
        where="on the sill",
        makes_flame=True,
        tags={"sparkler", "fire"},
    ),
    "candle": FlameTool(
        id="candle",
        label="candle",
        phrase="a candle for the night",
        where="on the shelf",
        makes_flame=True,
        tags={"candle", "fire"},
    ),
}

TARGETS = {
    "curtain": FlammableThing(
        id="curtain",
        label="curtain",
        the="the curtain",
        near="the hem of the curtain",
        drape="the curtain hung soft and wide",
        spread=3,
        flammable=True,
        tags={"curtain", "cloth"},
    ),
    "paper_star": FlammableThing(
        id="paper_star",
        label="paper star",
        the="the paper star",
        near="the edge of the paper star",
        drape="a paper star hung down from string",
        spread=2,
        flammable=True,
        tags={"paper", "star"},
    ),
    "straw_hay": FlammableThing(
        id="straw_hay",
        label="straw bundle",
        the="the straw bundle",
        near="the dry straw",
        drape="a little straw bundle sat by the shelf",
        spread=2,
        flammable=True,
        tags={"straw", "hay"},
    ),
}

RESPONSES = {
    "bucket": Response(
        id="bucket",
        sense=3,
        power=1,
        text="filled a bucket with water and splashed the fire, trying to hush it",
        fail="filled a bucket with water and splashed the fire, but the flames kept on",
        qa_text="filled a bucket with water and splashed the fire",
        tags={"water", "bucket"},
    ),
    "cloth": Response(
        id="cloth",
        sense=2,
        power=2,
        text="snatched a damp cloth and pressed it down",
        fail="snatched a damp cloth, but it was much too small",
        qa_text="pressed it down with a damp cloth",
        tags={"cloth"},
    ),
    "call": Response(
        id="call",
        sense=4,
        power=4,
        text="called for help and grabbed the blanket to smother the spark",
        fail="called for help, but the fire had already climbed too high",
        qa_text="called for help and tried to smother the spark",
        tags={"call", "blanket"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nina", "Ada", "Rose", "Tilly"]
BOY_NAMES = ["Milo", "Theo", "Ned", "Pip", "Toby", "Finn"]
TRAITS = ["gentle", "curious", "cheery", "sleepy", "bold"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for theme in THEMES:
        for forbidden in FORBIDDEN:
            for target in TARGETS:
                for response in RESPONSES:
                    if hazard_at_risk(FORBIDDEN[forbidden], TARGETS[target]):
                        combos.append((theme, forbidden, target, response))
    return combos


def explain_rejection(tool: FlameTool, target: FlammableThing) -> str:
    return (
        f"(No story: {tool.label} can make a flame, but {target.the} would not "
        f"make a meaningful fire here.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme fire storyworld: ignite, graze, transformation, bad ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.forbidden and args.target:
        if not hazard_at_risk(FORBIDDEN[args.forbidden], TARGETS[args.target]):
            raise StoryError(explain_rejection(FORBIDDEN[args.forbidden], TARGETS[args.target]))

    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, forbidden, target, response = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if gender == "boy" else "boy"
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child_name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        forbidden=forbidden,
        target=target,
        response=response,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent_type=parent,
        delay=rng.randint(1, 2),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style fire story that includes the words "ignite" and "graze".',
        f"Tell a small story where {f['child'].id} tries to use a {f['tool'].label} near {f['target_cfg'].the}, and the little scene ends in a bad transformation.",
        f"Write a child-facing rhyme where a warning is ignored, a flame ignites, and the ending turns smoky and sad.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, parent = f["child"], f["helper"], f["parent"]
    tool, target = f["tool"], f["target_cfg"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, with {parent.label_word} watching over them. The little pair are the ones who make the trouble by the dark nook."),
        ("What did the child want to do?",
         f"{child.id} wanted to use {tool.label} for light. That choice was the wrong one because it could make a real flame near {target.the}."),
        ("What happened when the flame started?",
         f"The flame ignited and then grazed {target.near}, so the fire began to climb. That small touch mattered because {target.label} is flammable and the fire could spread."),
        ("How did the story end?",
         f"It ended badly. The room changed into smoke and soot, and the little play was transformed into a sad, black mess."),
    ]
    if f.get("outcome") == "burned":
        qa.append((
            "Could the grown-up save the day in time?",
            f"No. {parent.label_word.capitalize()} came with {resp.fail.replace('{target}', target.label)}, but the flames were already too big. That is why the ending stays sad instead of bright."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tool"].tags) | set(world.facts["target_cfg"].tags) | {"fire"}
    out = []
    if "fire" in tags:
        out.append(("Why is fire dangerous?",
                    "Fire is dangerous because it gets very hot and can spread fast. It can turn toys, cloth, and paper into ash before anyone means to do it."))
    if "match" in tags:
        out.append(("What do matches do?",
                    "Matches make a small flame when they are struck. They are for grown-ups, not for child play."))
    if "sparkler" in tags:
        out.append(("What is a sparkler?",
                    "A sparkler is a stick that makes bright sparks and heat. It can burn fingers and nearby things, so it is not a toy."))
    if "curtain" in tags or "cloth" in tags:
        out.append(("Why can cloth catch fire?",
                    "Cloth can catch fire because it is dry and thin enough for flames to eat quickly. Curtains, paper, and straw all need to stay far away from fire."))
    if "paper" in tags:
        out.append(("Why is paper easy to burn?",
                    "Paper is light and dry, so fire can bite into it very fast. That is why paper stars and paper decorations must stay away from flames."))
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
        if e.flammable:
            bits.append("flammable")
        if e.makes_flame:
            bits.append("makes_flame")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(F,T) :- makes_flame(F), flammable(T).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
severity(T,D, V) :- spread(T,S), delay(D), V = S + D.
contained(R,T,D) :- power(R,P), severity(T,D,V), P >= V.
outcome(burned) :- chosen(F,T,R,D), hazard(F,T), sensible(R), not contained(R,T,D).
outcome(contained) :- chosen(F,T,R,D), hazard(F,T), sensible(R), contained(R,T,D).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, f in FORBIDDEN.items():
        lines.append(asp.fact("response_source", fid))
        if f.makes_flame:
            lines.append(asp.fact("makes_flame", fid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.flammable:
            lines.append(asp.fact("flammable", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show hazard/2.\n", "#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen", params.forbidden, params.target, params.response, params.delay),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == {(f, t) for _, f, t, _ in valid_combos()}:
        print("OK: ASP hazard gate matches Python.")
    else:
        rc = 1
        print("MISMATCH: ASP hazard gate differs from Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            theme=None, forbidden=None, target=None, response=None, parent=None,
            name=None, helper=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    cases = [StoryParams(theme="nursery", forbidden="match", target="curtain",
                         response="bucket", child_name="Milo", child_gender="boy",
                         helper_name="Mina", helper_gender="girl", parent_type="mother",
                         delay=d)
             for d in range(1, 3)]
    if all(asp_outcome(p) == ("burned" if not is_contained(RESPONSES[p.response], TARGETS[p.target], p.delay) else "contained")
           for p in cases):
        print("OK: ASP outcome matches Python on curated cases.")
    else:
        rc = 1
        print("MISMATCH: ASP outcome differs from Python.")
    return rc


CURATED = [
    StoryParams(theme="nursery", forbidden="match", target="curtain", response="bucket",
                child_name="Milo", child_gender="boy", helper_name="Mina", helper_gender="girl",
                parent_type="mother", delay=2, seed=1),
    StoryParams(theme="lantern", forbidden="sparkler", target="paper_star", response="cloth",
                child_name="Lily", child_gender="girl", helper_name="Pip", helper_gender="boy",
                parent_type="father", delay=1, seed=2),
    StoryParams(theme="nursery", forbidden="candle", target="straw_hay", response="call",
                child_name="Ned", child_gender="boy", helper_name="Tilly", helper_gender="girl",
                parent_type="mother", delay=2, seed=3),
]


def generate(params: StoryParams) -> StorySample:
    for key, mapping in (("theme", THEMES), ("forbidden", FORBIDDEN), ("target", TARGETS), ("response", RESPONSES)):
        if getattr(params, key) not in mapping:
            raise StoryError(f"invalid {key}: {getattr(params, key)!r}")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(FORBIDDEN[params.forbidden], TARGETS[params.target]):
        raise StoryError(explain_rejection(FORBIDDEN[params.forbidden], TARGETS[params.target]))
    world = tell(THEMES[params.theme], FORBIDDEN[params.forbidden], TARGETS[params.target],
                 RESPONSES[params.response], params.child_name, params.child_gender,
                 params.helper_name, params.helper_gender, params.parent_type, params.delay)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, forbidden, target, response = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if gender == "boy" else "boy"
    return StoryParams(
        theme=theme,
        forbidden=forbidden,
        target=target,
        response=response,
        child_name=args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES),
        child_gender=gender,
        helper_name=args.helper or rng.choice(GIRL_NAMES + BOY_NAMES),
        helper_gender=helper_gender,
        parent_type=args.parent or rng.choice(["mother", "father"]),
        delay=rng.randint(1, 2),
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme storyworld with ignite/graze and a bad ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show hazard/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("asp mode is available; this world focuses on story generation.")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
