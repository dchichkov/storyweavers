#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/roll_vessel_foreshadowing_adventure.py
=================================================================

A small storyworld for gentle adventure tales built from the seed words
"roll" and "vessel", with explicit foreshadowing.

Premise
-------
Two children set out on a small water adventure with a guide. Before they leave,
the world offers a clear sign of trouble to come: reeds bend, water curls, or a
low roll of thunder sounds in the distance. That sign is not decorative. It
predicts the kind of challenge the children will meet on the water, and the
story only allows journeys where the chosen vessel and tool genuinely fit that
risk.

Reasonableness gate
-------------------
A story is valid only when:

* the chosen route's hazard is one the vessel can handle, and
* the chosen tool is one that can help with that same hazard.

So a light coracle is refused on a windy bay, and a guide rope is refused as the
solution to thunder on open water. The world prefers fewer sensible adventures
to many weak ones.

Run it
------
    python storyworlds/worlds/gpt-5.4/roll_vessel_foreshadowing_adventure.py
    python storyworlds/worlds/gpt-5.4/roll_vessel_foreshadowing_adventure.py --route reed_channel --vessel coracle --tool guide_rope
    python storyworlds/worlds/gpt-5.4/roll_vessel_foreshadowing_adventure.py --route gull_bay --vessel coracle
    python storyworlds/worlds/gpt-5.4/roll_vessel_foreshadowing_adventure.py --all
    python storyworlds/worlds/gpt-5.4/roll_vessel_foreshadowing_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/roll_vessel_foreshadowing_adventure.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Route:
    id: str
    label: str
    water: str
    goal: str
    landing: str
    sign: str
    omen_line: str
    hazard: str
    hazard_text: str
    recovery_result: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class VesselCfg:
    id: str
    label: str
    phrase: str
    plural: bool = False
    handles: set[str] = field(default_factory=set)
    traits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works_on: set[str] = field(default_factory=set)
    warning: str = ""
    action: str = ""
    qa_action: str = ""
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


def _r_foreshadow(world: World) -> list[str]:
    route = world.get("route")
    vessel = world.get("vessel")
    out: list[str] = []
    if route.meters["omen"] >= THRESHOLD and vessel.meters["afloat"] >= THRESHOLD:
        sig = ("challenge", route.attrs["hazard"])
        if sig not in world.fired:
            world.fired.add(sig)
            vessel.meters["challenge"] += 1
            world.get("hero").memes["alert"] += 1
            world.get("friend").memes["alert"] += 1
            out.append("__challenge__")
    return out


def _r_recover(world: World) -> list[str]:
    vessel = world.get("vessel")
    tool = world.get("tool")
    route = world.get("route")
    out: list[str] = []
    if vessel.meters["challenge"] >= THRESHOLD and route.attrs["hazard"] in tool.attrs.get("works_on", set()):
        sig = ("recover", tool.id)
        if sig not in world.fired:
            world.fired.add(sig)
            vessel.meters["steady"] += 1
            vessel.meters["challenge"] = 0.0
            world.get("hero").memes["courage"] += 1
            world.get("friend").memes["courage"] += 1
            out.append("__recovered__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("foreshadow_to_challenge", "physical", _r_foreshadow),
    Rule("recovery", "physical", _r_recover),
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
                produced.extend(out)
    return produced


ROUTES = {
    "gull_bay": Route(
        "gull_bay",
        "Gull Bay",
        "the wide blue bay",
        "carry a brass bell to the little watch island",
        "the stone jetty on the watch island",
        "the cattails were all leaning in one direction",
        "Even before the children climbed in, the cattails were all leaning in one direction, as if the bay were whispering that the wind had not finished with the morning.",
        "wind",
        "Halfway across, a sharp gust shoved the vessel sideways and made it roll under their knees.",
        "Soon the bow pointed true again, and the bay that had seemed bossy a moment before opened into a shining path.",
        "They stepped onto the jetty, hung the bell where the little island keeper could find it, and listened to it ring in the bright air.",
        tags={"wind", "bay", "adventure"},
    ),
    "reed_channel": Route(
        "reed_channel",
        "Reed Channel",
        "the narrow green channel",
        "bring a satchel of seed cakes to the duck house",
        "the little plank beside the duck house",
        "the water kept curling hard around the old posts",
        "At the landing, the water kept curling hard around the old posts, and the guide tapped one with a finger as if to say, remember that pull.",
        "current",
        "In the middle of the reeds, the current tugged the vessel toward the stems and made it roll with a worried wobble.",
        "The pull of the water stopped bossing them around, and the reeds slid past in neat green rows.",
        "They tied up beside the duck house and set down the seed cakes while the ducks paddled close, hopeful and proud.",
        tags={"current", "reeds", "adventure"},
    ),
    "echo_reach": Route(
        "echo_reach",
        "Echo Reach",
        "the dark silver reach below the cliffs",
        "take a wrapped map to the old lookout hut",
        "the sheltered cove below the lookout hut",
        "a low roll of thunder moved behind the cliffs",
        "As they checked the bundles, a low roll of thunder moved behind the cliffs, not loud yet, but large enough to make everyone look at the sky twice.",
        "thunder",
        "Near the cliffs, another roll of thunder crossed the water and a sprinkle began to sting the vessel's rim.",
        "The map stayed dry, their breaths grew easy again, and the reach carried them into the sheltered cove instead of into trouble.",
        "They climbed into the cove with the wrapped map safe in hand, and the lookout flag snapped above them like the last line of a brave song.",
        tags={"thunder", "storm", "adventure"},
    ),
}

VESSELS = {
    "rowboat": VesselCfg(
        "rowboat",
        "rowboat",
        "a red rowboat",
        handles={"wind", "current"},
        traits={"steady"},
        tags={"boat", "oars"},
    ),
    "coracle": VesselCfg(
        "coracle",
        "coracle",
        "a round wicker coracle",
        handles={"current"},
        traits={"light"},
        tags={"boat", "coracle"},
    ),
    "launch": VesselCfg(
        "launch",
        "launch",
        "a little harbor launch with a snug hood",
        handles={"wind", "current", "thunder"},
        traits={"steady", "covered"},
        tags={"boat", "launch"},
    ),
}

TOOLS = {
    "spare_oar": Tool(
        "spare_oar",
        "spare oar",
        "a spare oar tucked along the side",
        works_on={"wind"},
        warning="If the gust comes broadside, we will need another oar to keep the bow from wandering.",
        action="The guide slid the spare oar into the water, and together they bit into the gust until the little vessel stopped skidding sideways.",
        qa_action="used the spare oar to pull against the wind and keep the bow straight",
        tags={"oar", "wind"},
    ),
    "guide_rope": Tool(
        "guide_rope",
        "guide rope",
        "a guide rope looped through the bow ring",
        works_on={"current"},
        warning="If the channel starts pulling, this rope will let us hold the safe line.",
        action="The guide braced both feet, took the guide rope tight, and drew the vessel back to the calm lane between the reeds.",
        qa_action="used the guide rope to pull the vessel back onto the safe line",
        tags={"rope", "current"},
    ),
    "oilcloth": Tool(
        "oilcloth",
        "oilcloth",
        "a square of oilcloth folded over the packs",
        works_on={"thunder"},
        warning="If the sky speaks again, we will cover the map and keep to the sheltered side.",
        action="The guide snapped the oilcloth over the map and steered the vessel close under the cliff until the shower slipped by.",
        qa_action="covered the map with oilcloth and steered into shelter when the thunder came nearer",
        tags={"storm", "shelter"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tess", "Ava", "June", "Nora", "Elsie", "Ruby"]
BOY_NAMES = ["Finn", "Otis", "Milo", "Ben", "Leo", "Arlo", "Toby", "Sam"]
TRAITS = ["eager", "brave", "careful", "curious", "steady", "hopeful"]


def valid_combo(route: Route, vessel: VesselCfg, tool: Tool) -> bool:
    return route.hazard in vessel.handles and route.hazard in tool.works_on


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for route_id, route in ROUTES.items():
        for vessel_id, vessel in VESSELS.items():
            for tool_id, tool in TOOLS.items():
                if valid_combo(route, vessel, tool):
                    out.append((route_id, vessel_id, tool_id))
    return out


def explain_rejection(route: Route, vessel: VesselCfg, tool: Tool) -> str:
    if route.hazard not in vessel.handles:
        return (
            f"(No story: {vessel.phrase} is not a sensible vessel for {route.label}, "
            f"because it cannot handle {route.hazard}. Pick a vessel that suits the water and the warning sign.)"
        )
    if route.hazard not in tool.works_on:
        return (
            f"(No story: {tool.label} does not solve the danger on {route.label}. "
            f"The foreshadowed risk there is {route.hazard}, so the tool must help with that exact problem.)"
        )
    return "(No story: this combination does not make a reasonable adventure.)"


def predict_challenge(world: World) -> dict:
    sim = world.copy()
    sim.get("route").meters["omen"] += 1
    sim.get("vessel").meters["afloat"] += 1
    propagate(sim, narrate=False)
    return {
        "challenge": sim.get("vessel").meters["challenge"] >= THRESHOLD,
        "hazard": sim.get("route").attrs["hazard"],
    }


def introduce(world: World, hero: Entity, friend: Entity, route: Route) -> None:
    hero.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {friend.id} had been waiting all week for a real adventure on {route.water}. "
        f"Today, they were allowed to help {route.goal}."
    )


def show_vessel(world: World, guide: Entity, vessel_cfg: VesselCfg, tool: Tool) -> None:
    vessel = world.get("vessel")
    tool_ent = world.get("tool")
    vessel.memes["readiness"] += 1
    world.say(
        f"At the dock, their guide had already set out {vessel_cfg.phrase}. "
        f'"This little vessel is ready," {guide.pronoun()} said, "and so is {tool.phrase}."'
    )
    tool_ent.memes["purpose"] += 1


def foreshadow(world: World, guide: Entity, route: Route, tool: Tool) -> None:
    route_ent = world.get("route")
    route_ent.meters["omen"] += 1
    guide.memes["care"] += 1
    pred = predict_challenge(world)
    world.facts["predicted_hazard"] = pred["hazard"]
    world.say(route.omen_line)
    world.say(
        f'"That sign matters," {guide.pronoun()} told them. "{tool.warning}"'
    )


def launch(world: World, hero: Entity, friend: Entity, vessel_cfg: VesselCfg) -> None:
    vessel = world.get("vessel")
    vessel.meters["afloat"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"They climbed into the {vessel_cfg.label}, and for a moment the adventure felt easy. "
        f"The water made soft tapping sounds against the vessel as it slipped away from the dock."
    )


def hazard_hits(world: World, route: Route) -> None:
    world.say(route.hazard_text)
    propagate(world, narrate=False)


def recover(world: World, guide: Entity, route: Route, tool: Tool) -> None:
    world.say(tool.action)
    propagate(world, narrate=False)
    world.say(route.recovery_result)


def arrive(world: World, hero: Entity, friend: Entity, route: Route) -> None:
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"When they reached {route.landing}, the children grinned at each other with wet hair and shining eyes."
    )
    world.say(route.ending_image)


def tell(
    route: Route,
    vessel_cfg: VesselCfg,
    tool: Tool,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    friend_name: str = "Finn",
    friend_gender: str = "boy",
    guide_type: str = "father",
    hero_trait: str = "curious",
    friend_trait: str = "brave",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", attrs={"trait": hero_trait}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", attrs={"trait": friend_trait}))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, role="guide", label="the guide"))
    route_ent = world.add(Entity(id="route", type="route", label=route.label, attrs={"hazard": route.hazard}))
    vessel = world.add(Entity(id="vessel", type="vessel", label=vessel_cfg.label, attrs={"handles": set(vessel_cfg.handles)}))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label, attrs={"works_on": set(tool.works_on)}))

    introduce(world, hero, friend, route)
    show_vessel(world, guide, vessel_cfg, tool)

    world.para()
    foreshadow(world, guide, route, tool)
    launch(world, hero, friend, vessel_cfg)

    world.para()
    hazard_hits(world, route)
    recover(world, guide, route, tool)

    world.para()
    arrive(world, hero, friend, route)

    world.facts.update(
        hero=hero,
        friend=friend,
        guide=guide,
        route_cfg=route,
        vessel_cfg=vessel_cfg,
        tool_cfg=tool,
        route=route_ent,
        vessel=vessel,
        tool=tool_ent,
        success=vessel.meters["steady"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    route: str
    vessel: str
    tool: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    guide: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "wind": [(
        "What can wind do to a small boat?",
        "Wind can push a small boat sideways or turn its front away from the path. That is why rowers must keep the boat pointed where they want to go."
    )],
    "current": [(
        "What is a current in water?",
        "A current is water moving in one direction. It can tug a boat along even when the people inside did not mean to drift."
    )],
    "thunder": [(
        "What is thunder?",
        "Thunder is the big rumbling sound that can come with a storm. When you hear it far away, it can be a warning that the weather is changing."
    )],
    "foreshadowing": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is when a story shows a hint early that tells you something important may happen later. It makes the later moment feel earned instead of sudden."
    )],
    "oar": [(
        "What does an oar do?",
        "An oar pushes against the water so a boat can move or turn. A strong extra oar can help keep a boat straight in wind."
    )],
    "rope": [(
        "Why can a rope help on the water?",
        "A rope can help people hold a boat on a safe path or pull it away from danger. It is useful when moving water is trying to drag the boat somewhere else."
    )],
    "storm": [(
        "Why would people cover a map with oilcloth?",
        "Oilcloth keeps rain off something important. In wet weather, it can protect paper from turning soggy and tearing."
    )],
    "boat": [(
        "What is a vessel?",
        "A vessel is something that carries people or things on water, like a boat. It has to suit the water and the weather if the trip is to be safe."
    )],
}
KNOWLEDGE_ORDER = ["foreshadowing", "boat", "wind", "current", "thunder", "oar", "rope", "storm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route, vessel, tool = f["route_cfg"], f["vessel_cfg"], f["tool_cfg"]
    hero, friend = f["hero"], f["friend"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "roll" and "vessel". Use foreshadowing with an early sign on the water.',
        f"Tell a gentle adventure where {hero.id} and {friend.id} cross {route.water} in {vessel.phrase}, and an early warning sign later comes true.",
        f"Write a child-facing water adventure in which {tool.label} matters because the clue at the beginning foreshadows the danger in the middle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, guide = f["hero"], f["friend"], f["guide"]
    route, vessel, tool = f["route_cfg"], f["vessel_cfg"], f["tool_cfg"]
    pw = guide.label_word
    return [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children on a small water adventure, and their {pw} who guided them. Together they set out to {route.goal}."
        ),
        (
            f"What was the early warning sign?",
            f"The early sign was that {route.sign}. That clue was foreshadowing, because it hinted that {route.hazard} would matter later on the trip."
        ),
        (
            f"What happened in the middle of the journey?",
            f"{route.hazard_text} The danger matched the sign from the beginning, so the middle of the story felt like the warning coming true."
        ),
        (
            f"How did the guide help the children?",
            f"The guide {tool.qa_action}. That worked because {tool.label} fits the exact problem on {route.label}."
        ),
        (
            "How did the story end?",
            f"They reached {route.landing} safely and finished the job they had set out to do. {route.ending_image}"
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    route, vessel, tool = f["route_cfg"], f["vessel_cfg"], f["tool_cfg"]
    tags = {"foreshadowing", "boat"} | set(route.tags) | set(vessel.tags) | set(tool.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("gull_bay", "rowboat", "spare_oar", "Lina", "girl", "Finn", "boy", "father", "curious", "brave"),
    StoryParams("reed_channel", "coracle", "guide_rope", "Mira", "girl", "Otis", "boy", "mother", "eager", "careful"),
    StoryParams("echo_reach", "launch", "oilcloth", "Ruby", "girl", "Milo", "boy", "father", "hopeful", "steady"),
]


ASP_RULES = r"""
valid(Route, Vessel, Tool) :-
    route(Route), vessel(Vessel), tool(Tool),
    hazard(Route, H), handles(Vessel, H), works_on(Tool, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("hazard", rid, route.hazard))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        for h in sorted(vessel.handles):
            lines.append(asp.fact("handles", vid, h))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a foreshadowed water adventure. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.vessel and args.tool:
        route, vessel, tool = ROUTES[args.route], VESSELS[args.vessel], TOOLS[args.tool]
        if not valid_combo(route, vessel, tool):
            raise StoryError(explain_rejection(route, vessel, tool))

    combos = [
        c for c in valid_combos()
        if (args.route is None or c[0] == args.route)
        and (args.vessel is None or c[1] == args.vessel)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        if args.route and args.vessel and args.tool:
            raise StoryError(explain_rejection(ROUTES[args.route], VESSELS[args.vessel], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    route_id, vessel_id, tool_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    guide = args.guide or rng.choice(["mother", "father"])
    return StoryParams(
        route_id,
        vessel_id,
        tool_id,
        hero,
        hero_gender,
        friend,
        friend_gender,
        guide,
        rng.choice(TRAITS),
        rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ROUTES[params.route],
        VESSELS[params.vessel],
        TOOLS[params.tool],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.guide,
        params.hero_trait,
        params.friend_trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, vessel, tool) combos:\n")
        for route, vessel, tool in combos:
            print(f"  {route:13} {vessel:8} {tool}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.friend}: {p.route} by {p.vessel} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
