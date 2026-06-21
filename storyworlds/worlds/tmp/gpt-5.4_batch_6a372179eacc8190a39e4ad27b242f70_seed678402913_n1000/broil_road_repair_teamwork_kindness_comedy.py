#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/broil_road_repair_teamwork_kindness_comedy.py
========================================================================

A small standalone storyworld about a cheerful road-repair crew on a very hot
day. The crew is fixing a problem in the street when the heat makes the fresh
repair start to broil and slump. A kind pause to help someone nearby changes
the social state of the scene, and that help comes back as exactly the clue or
tool the crew needs. The result is a comedy of sticky boots, polite neighbors,
and teamwork that turns a wobbly patch into a safe road.

The world model is deliberately small and classical:

* typed entities share one representation with physical meters and emotional memes
* a forward-chaining rule engine turns heat + fresh mix into a broiling mess
* kindness changes who is willing to help, which changes what fix is available
* the story text is driven by simulated state rather than noun swapping
* a Python reasonableness gate and inline ASP twin stay in parity

Run it
------
    python storyworlds/worlds/gpt-5.4/broil_road_repair_teamwork_kindness_comedy.py
    python storyworlds/worlds/gpt-5.4/broil_road_repair_teamwork_kindness_comedy.py --damage pothole --mix quickset --helper vendor --fix shade_tarp
    python storyworlds/worlds/gpt-5.4/broil_road_repair_teamwork_kindness_comedy.py --mix gravel
    python storyworlds/worlds/gpt-5.4/broil_road_repair_teamwork_kindness_comedy.py --all
    python storyworlds/worlds/gpt-5.4/broil_road_repair_teamwork_kindness_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/broil_road_repair_teamwork_kindness_comedy.py --verify
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
HEAT_LEVEL = 3
HELP_MIN = 1


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
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Damage:
    id: str
    label: str
    phrase: str
    lane: str
    depth: int
    needed_mix: str
    needs_rake: bool
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mix:
    id: str
    label: str
    phrase: str
    strength: int
    heat_softness: int
    spread_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    arrival: str
    need: str
    thanks: str
    return_gift: str
    clue: str
    gift_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    needs_gift: str
    power: int
    funny: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    damage: str
    mix: str
    helper: str
    fix: str
    foreman: str
    rookie: str
    roller: str
    foreman_gender: str
    rookie_gender: str
    roller_gender: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_broil(world: World) -> list[str]:
    out: list[str] = []
    patch = world.get("patch")
    if patch.meters["fresh"] < THRESHOLD:
        return out
    if patch.meters["heat"] < HEAT_LEVEL:
        return out
    if patch.meters["softening"] >= THRESHOLD:
        return out
    sig = ("broil",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patch.meters["softening"] += 1
    patch.meters["messy"] += 1
    for eid in ("foreman", "rookie", "roller"):
        world.get(eid).memes["worry"] += 1
    out.append("__broil__")
    return out


def _r_sag(world: World) -> list[str]:
    out: list[str] = []
    patch = world.get("patch")
    if patch.meters["softening"] < THRESHOLD:
        return out
    if patch.meters["supported"] >= THRESHOLD:
        return out
    sig = ("sag",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patch.meters["sagging"] += 1
    world.get("street").meters["risk"] += 1
    out.append("__sag__")
    return out


RULES = [
    Rule(name="broil", tag="physical", apply=_r_broil),
    Rule(name="sag", tag="physical", apply=_r_sag),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


DAMAGES = {
    "pothole": Damage(
        id="pothole",
        label="pothole",
        phrase="a round pothole right in the middle of Maple Street",
        lane="middle",
        depth=2,
        needed_mix="quickset",
        needs_rake=True,
        danger="bumped bicycle wheels",
        tags={"pothole", "road"},
    ),
    "crack": Damage(
        id="crack",
        label="long crack",
        phrase="a long crack zigzagging across the slow lane",
        lane="slow lane",
        depth=1,
        needed_mix="sealant",
        needs_rake=False,
        danger="snagged scooter wheels",
        tags={"crack", "road"},
    ),
    "dip": Damage(
        id="dip",
        label="sunken patch",
        phrase="a little sunken patch near the bus stop",
        lane="curbside",
        depth=2,
        needed_mix="quickset",
        needs_rake=True,
        danger="splashed bus-stop puddles onto shoes",
        tags={"dip", "road"},
    ),
    "grate": Damage(
        id="grate",
        label="wobbly grate edge",
        phrase="a wobbly grate edge beside the corner drain",
        lane="corner",
        depth=1,
        needed_mix="sealant",
        needs_rake=False,
        danger="rattled every passing cart",
        tags={"grate", "road"},
    ),
}

MIXES = {
    "quickset": Mix(
        id="quickset",
        label="quick-set patch mix",
        phrase="a fresh mound of quick-set patch mix",
        strength=3,
        heat_softness=1,
        spread_word="slumped like warm cake frosting",
        tags={"asphalt", "repair"},
    ),
    "sealant": Mix(
        id="sealant",
        label="rubbery road sealant",
        phrase="a shiny stripe of road sealant",
        strength=2,
        heat_softness=0,
        spread_word="wiggled into a shiny ribbon",
        tags={"sealant", "repair"},
    ),
    "coldpatch": Mix(
        id="coldpatch",
        label="cold patch mix",
        phrase="a lumpy scoop of cold patch",
        strength=1,
        heat_softness=2,
        spread_word="oozed sideways like a sleepy brownie",
        tags={"asphalt", "repair"},
    ),
    "gravel": Mix(
        id="gravel",
        label="loose gravel",
        phrase="a pile of loose gravel",
        strength=0,
        heat_softness=2,
        spread_word="skittered away in every direction",
        tags={"gravel"},
    ),
}

HELPERS = {
    "vendor": HelperKind(
        id="vendor",
        label="popsicle cart lady",
        arrival="a popsicle cart lady rang her little bell beside the cones",
        need="her cart wheel had snagged at the cone line",
        thanks="She laughed when the crew freed it and said they had saved both her cart and her cherry pops.",
        return_gift="From under the cart she pulled out a folded striped shade tarp.",
        clue="The tarp was meant to protect her popsicles from melting.",
        gift_kind="shade",
        tags={"vendor", "kindness", "shade"},
    ),
    "cyclist": HelperKind(
        id="cyclist",
        label="wobbly cyclist",
        arrival="a cyclist stopped with one sandal twisted around a pedal strap",
        need="the strap had wrapped itself into a stubborn knot",
        thanks="The rider grinned when the crew untangled it and said that was the kindest pit stop in town.",
        return_gift="From a basket the cyclist handed over a spring clamp and a bright umbrella strap.",
        clue="The rider said, with a wink, that sunny days were sneaky.",
        gift_kind="shade",
        tags={"cyclist", "kindness", "shade"},
    ),
    "gardener": HelperKind(
        id="gardener",
        label="watering gardener",
        arrival="a gardener from the corner lot hurried over with a hose that had kinked itself into a pretzel",
        need="the hose would not reach the thirsty tomatoes",
        thanks="When the kink popped free, the gardener bowed as if the crew had rescued royalty.",
        return_gift="From the truck bed the gardener lent them two sturdy wooden boards.",
        clue="The boards were usually used to make a little path over soft dirt.",
        gift_kind="support",
        tags={"gardener", "kindness", "support"},
    ),
    "mail": HelperKind(
        id="mail",
        label="mail carrier",
        arrival="a mail carrier paused with a bag strap slipping off one shoulder",
        need="the strap buckle had jammed shut",
        thanks="The carrier chuckled when the buckle clicked free and said no letter had ever looked so relieved.",
        return_gift="From the satchel came a neat roll of caution twine and a pair of wooden stakes.",
        clue="The carrier said tidy lines make everybody behave better.",
        gift_kind="support",
        tags={"mail", "kindness", "support"},
    ),
}

FIXES = {
    "shade_tarp": Fix(
        id="shade_tarp",
        label="shade tarp",
        phrase="hold a shade tarp over the patch while the others worked",
        needs_gift="shade",
        power=2,
        funny="The tarp snapped and fluttered so hard that the cones looked like they were applauding.",
        qa_text="They held a shade tarp over the hot repair so the mix would stop broiling in the sun.",
        tags={"shade", "teamwork"},
    ),
    "umbrella_parade": Fix(
        id="umbrella_parade",
        label="umbrella parade",
        phrase="clip a bright umbrella over the patch and march around it to block the sun",
        needs_gift="shade",
        power=1,
        funny="For one minute the crew looked less like road workers and more like a parade that had misplaced its music.",
        qa_text="They shaded the patch with an umbrella and worked together around it.",
        tags={"shade", "teamwork", "comedy"},
    ),
    "board_bridge": Fix(
        id="board_bridge",
        label="board bridge",
        phrase="lay two boards beside the soft spot so nobody stepped into it while it settled",
        needs_gift="support",
        power=2,
        funny="Even the rookie's boot finally stopped making kissy sounds in the tar.",
        qa_text="They laid boards to support the edges and keep feet and wheels off the soft repair.",
        tags={"support", "teamwork"},
    ),
    "twine_corral": Fix(
        id="twine_corral",
        label="twine corral",
        phrase="string a tidy little corral around the patch so it could rest untouched",
        needs_gift="support",
        power=1,
        funny="The tiny fence made the patch look as if it had been grounded for bad manners.",
        qa_text="They tied a small safety corral around the patch so it could settle without being disturbed.",
        tags={"support", "teamwork", "comedy"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Ava", "Nora", "Ruby", "Lena", "Ivy", "Ella"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Sam", "Jack", "Owen", "Theo"]


def damage_works_with_mix(damage: Damage, mix: Mix) -> bool:
    return damage.needed_mix == mix.id and mix.strength >= damage.depth


def fix_matches_helper(helper: HelperKind, fix: Fix) -> bool:
    return helper.gift_kind == fix.needs_gift


def fix_contains_problem(damage: Damage, mix: Mix, fix: Fix) -> bool:
    heat = HEAT_LEVEL + mix.heat_softness
    severity = 1 if heat >= HEAT_LEVEL + 1 else 0
    if damage.depth >= 2:
        severity += 1
    return fix.power >= severity


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for damage_id, damage in DAMAGES.items():
        for mix_id, mix in MIXES.items():
            if not damage_works_with_mix(damage, mix):
                continue
            for helper_id, helper in HELPERS.items():
                for fix_id, fix in FIXES.items():
                    if fix_matches_helper(helper, fix) and fix_contains_problem(damage, mix, fix):
                        combos.append((damage_id, mix_id, helper_id, fix_id))
    return sorted(combos)


def explain_mix_rejection(damage: Damage, mix: Mix) -> str:
    if damage.needed_mix != mix.id:
        return (
            f"(No story: {damage.label} needs {damage.needed_mix}, not {mix.label}. "
            f"The crew should use the right road material for the job.)"
        )
    if mix.strength < damage.depth:
        return (
            f"(No story: {mix.label} is too weak for {damage.label}. "
            f"A deeper road problem needs a stronger patch.)"
        )
    return "(No story: that road material is not a reasonable match.)"


def explain_fix_rejection(helper: HelperKind, fix: Fix, damage: Damage, mix: Mix) -> str:
    if not fix_matches_helper(helper, fix):
        return (
            f"(No story: {helper.label} would bring a {helper.gift_kind} kind of help, "
            f"but {fix.label} needs {fix.needs_gift}. Kindness should return in a believable way.)"
        )
    if not fix_contains_problem(damage, mix, fix):
        return (
            f"(No story: {fix.label} is too weak once the {mix.label} starts to broil. "
            f"The fix has to truly steady the repair.)"
        )
    return "(No story: that helper and fix do not fit together.)"


def predict_broil(world: World) -> dict:
    sim = world.copy()
    patch = sim.get("patch")
    patch.meters["fresh"] += 1
    patch.meters["heat"] = HEAT_LEVEL + sim.facts["mix"].heat_softness
    propagate(sim, narrate=False)
    return {
        "broils": patch.meters["softening"] >= THRESHOLD,
        "sags": patch.meters["sagging"] >= THRESHOLD,
        "risk": sim.get("street").meters["risk"],
    }


def introduce(world: World, foreman: Entity, rookie: Entity, roller: Entity, damage: Damage) -> None:
    for worker in (foreman, rookie, roller):
        worker.memes["cheer"] += 1
    world.say(
        f"By ten o'clock, the sun had turned Maple Street into a bright griddle, and "
        f"{foreman.id}, {rookie.id}, and {roller.id} were out to fix {damage.phrase}."
    )
    world.say(
        f"{foreman.id} pointed with a shovel, {roller.id} steered the little roller into place, "
        f"and {rookie.id} carried the cone stack so high that only {rookie.pronoun('possessive')} nose showed."
    )


def inspect(world: World, foreman: Entity, damage: Damage) -> None:
    world.say(
        f'"This one has been trouble all week," {foreman.id} said. '
        f'"It has already {damage.danger}."'
    )


def prep_patch(world: World, rookie: Entity, mix: Mix, damage: Damage) -> None:
    patch = world.get("patch")
    patch.meters["fresh"] += 1
    patch.meters["heat"] = HEAT_LEVEL + mix.heat_softness
    patch.meters["strength"] = mix.strength
    world.say(
        f"They swept, scooped, and patted until the street held {mix.phrase} inside the {damage.label}."
    )
    if damage.needs_rake:
        world.say(
            f"{rookie.id} raked the top smooth, though every time {rookie.pronoun()} stepped back, "
            f"{rookie.pronoun('possessive')} boot made a sticky little schlup."
        )


def warn_heat(world: World, foreman: Entity) -> None:
    pred = predict_broil(world)
    world.facts["predicted_broils"] = pred["broils"]
    world.facts["predicted_risk"] = pred["risk"]
    if pred["broils"]:
        world.say(
            f'{foreman.id} squinted at the shimmer over the road. "If we do not mind the heat," '
            f'{foreman.pronoun()} said, "this patch could broil before it settles."'
        )


def kindness_arrives(world: World, helper_cfg: HelperKind) -> None:
    world.say(helper_cfg.arrival + ".")
    world.say(f"It turned out {helper_cfg.need}.")


def help_neighbor(world: World, foreman: Entity, rookie: Entity, roller: Entity, helper_cfg: HelperKind) -> None:
    for worker in (foreman, rookie, roller):
        worker.memes["kindness"] += 1
        worker.memes["teamwork"] += 1
    world.facts["helped"] = True
    world.say(
        f"{foreman.id} steadied the cones, {roller.id} held the awkward part, and {rookie.id} used both hands to fix the little trouble."
    )
    world.say(helper_cfg.thanks)


def trouble_hits(world: World, mix: Mix) -> None:
    propagate(world, narrate=False)
    patch = world.get("patch")
    if patch.meters["softening"] >= THRESHOLD:
        world.say(
            f"But the sun was bossy. The fresh repair began to broil and {mix.spread_word}."
        )
    if patch.meters["sagging"] >= THRESHOLD:
        world.say(
            "The neat edge sagged in one corner, and everybody made the same worried face at once."
        )


def gift_returns(world: World, helper_cfg: HelperKind) -> None:
    world.say(helper_cfg.return_gift)
    world.say(helper_cfg.clue)
    world.facts["gift_kind"] = helper_cfg.gift_kind


def solve(world: World, foreman: Entity, rookie: Entity, roller: Entity, fix: Fix, damage: Damage) -> None:
    patch = world.get("patch")
    patch.meters["supported"] += 1
    patch.meters["softening"] = 0.0
    patch.meters["sagging"] = 0.0
    world.get("street").meters["risk"] = 0.0
    for worker in (foreman, rookie, roller):
        worker.memes["relief"] += 1
        worker.memes["teamwork"] += 1
    world.say(
        f'"Everybody grab a side," {foreman.id} said, and they moved fast to {fix.phrase}.'
    )
    world.say(fix.funny)
    if damage.needs_rake:
        world.say(
            f"{rookie.id} smoothed the patch again while {roller.id} counted slowly and {foreman.id} checked the edges."
        )
    else:
        world.say(
            f"{roller.id} gave the repair a careful pass while {foreman.id} watched the seam and {rookie.id} guarded the cones like a very serious goose."
        )


def ending(world: World, foreman: Entity, rookie: Entity, roller: Entity, helper_cfg: HelperKind, damage: Damage) -> None:
    patch = world.get("patch")
    patch.meters["set"] += 1
    world.say(
        f"When the crew finally stepped back, the {damage.label} sat flat and proper, and not a single wheel wobbled over it."
    )
    world.say(
        f'{helper_cfg.label.capitalize()} waved from down the block. "{foreman.id} was right," {rookie.id} said. '
        f'"A kind stop did not ruin the job. It saved it."'
    )
    world.say(
        f"{roller.id} tapped the roller handle and grinned. "
        f'"Next time the road tries comedy," {roller.pronoun()} said, "we bring better shade and fewer sticky boots."'
    )


def tell(
    damage: Damage,
    mix: Mix,
    helper_cfg: HelperKind,
    fix: Fix,
    foreman_name: str,
    rookie_name: str,
    roller_name: str,
    foreman_gender: str,
    rookie_gender: str,
    roller_gender: str,
) -> World:
    world = World()
    foreman = world.add(Entity(id="foreman", kind="character", type=foreman_gender, label=foreman_name, role="foreman"))
    rookie = world.add(Entity(id="rookie", kind="character", type=rookie_gender, label=rookie_name, role="rookie"))
    roller = world.add(Entity(id="roller", kind="character", type=roller_gender, label=roller_name, role="roller"))
    street = world.add(Entity(id="street", kind="thing", type="street", label="Maple Street"))
    patch = world.add(Entity(id="patch", kind="thing", type="patch", label="the patch"))
    helper = world.add(Entity(id="helper", kind="character", type="person", label=helper_cfg.label, role="helper"))

    world.facts.update(
        damage=damage,
        mix=mix,
        helper_cfg=helper_cfg,
        fix=fix,
        foreman=foreman,
        rookie=rookie,
        roller=roller,
        helper=helper,
        helped=False,
        gift_kind="",
    )

    introduce(world, foreman, rookie, roller, damage)
    inspect(world, foreman, damage)
    world.para()
    prep_patch(world, rookie, mix, damage)
    warn_heat(world, foreman)
    kindness_arrives(world, helper_cfg)
    help_neighbor(world, foreman, rookie, roller, helper_cfg)
    world.para()
    trouble_hits(world, mix)
    gift_returns(world, helper_cfg)
    solve(world, foreman, rookie, roller, fix, damage)
    world.para()
    ending(world, foreman, rookie, roller, helper_cfg, damage)
    return world


def generation_prompts(world: World) -> list[str]:
    damage = world.facts["damage"]
    mix = world.facts["mix"]
    helper_cfg = world.facts["helper_cfg"]
    foreman = world.facts["foreman"]
    rookie = world.facts["rookie"]
    return [
        'Write a funny story for a 3-to-5-year-old set at road repair that includes the word "broil".',
        f"Tell a comedy where a road crew is fixing {damage.phrase}, the hot sun makes {mix.label} start to broil, and a kind pause to help a neighbor turns into the answer.",
        f"Write a teamwork-and-kindness story where {foreman.label} and {rookie.label} help {helper_cfg.label}, and that good turn comes back to save the repair job.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    damage = world.facts["damage"]
    mix = world.facts["mix"]
    helper_cfg = world.facts["helper_cfg"]
    fix = world.facts["fix"]
    foreman = world.facts["foreman"]
    rookie = world.facts["rookie"]
    roller = world.facts["roller"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about three road workers, {foreman.label}, {rookie.label}, and {roller.label}. They were trying to fix {damage.phrase}.",
        ),
        (
            "What problem were they fixing?",
            f"They were fixing {damage.phrase}. It was a real problem because it had already {damage.danger}.",
        ),
        (
            'What did the foreman mean by saying the patch could "broil"?',
            f"{foreman.label} meant the hot sun could overheat the fresh {mix.label} and make it soften. If that happened, the repair could slump before it finished setting.",
        ),
        (
            "How did kindness change the story?",
            f"The crew stopped to help {helper_cfg.label} with a small problem. Because they were kind first, that person gladly shared something useful when the patch began to fail.",
        ),
        (
            "How did the crew solve the repair problem?",
            f"{fix.qa_text} They worked as a team, so one person could hold, one could smooth, and one could watch the edges.",
        ),
        (
            "Why is teamwork important in this story?",
            f"No one worker could do every part at once once the repair softened. The fix only worked because the crew shared the job and moved together quickly.",
        ),
        (
            "How did the story end?",
            f"The road sat flat and safe at the end, and the crew was laughing again. The ending shows that kindness and teamwork changed a sticky mess into a finished repair.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "road": [
        (
            "What does a road repair crew do?",
            "A road repair crew fixes broken parts of streets so cars, bikes, and people can travel safely. They fill holes, smooth rough spots, and keep the road strong.",
        )
    ],
    "pothole": [
        (
            "What is a pothole?",
            "A pothole is a hole in the road where the surface has broken away. Wheels can bump into it and make travel rough or unsafe.",
        )
    ],
    "crack": [
        (
            "Why is a crack in the road a problem?",
            "A crack can let water in and make the road weaker over time. It can also catch small wheels and make a ride bumpy.",
        )
    ],
    "asphalt": [
        (
            "Why can hot road mix get soft in the sun?",
            "Road mix can soften when it gets very hot because heat makes it squishier for a while. That is why workers watch fresh repairs carefully on sunny days.",
        )
    ],
    "shade": [
        (
            "Why does shade help on a hot day?",
            "Shade blocks some of the sun's heat, so things underneath stay cooler. That can help people and even some materials from getting too hot too fast.",
        )
    ],
    "support": [
        (
            "Why do workers keep feet and wheels off a fresh repair?",
            "A fresh repair needs time to settle and firm up. If people step on it too soon, the surface can bend, sink, or get messy again.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people share a job and help one another do it well. A hard task gets easier when everyone does one part together.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is helping someone in a caring way, even when you are busy. A kind act can make another person feel safe, grateful, and ready to help too.",
        )
    ],
}
KNOWLEDGE_ORDER = ["road", "pothole", "crack", "asphalt", "shade", "support", "teamwork", "kindness"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"road", "teamwork", "kindness"}
    damage = world.facts["damage"]
    mix = world.facts["mix"]
    fix = world.facts["fix"]
    tags |= set(damage.tags)
    tags |= set(mix.tags)
    tags |= set(fix.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        damage="pothole",
        mix="quickset",
        helper="vendor",
        fix="shade_tarp",
        foreman="Mia",
        rookie="Ben",
        roller="Zoe",
        foreman_gender="girl",
        rookie_gender="boy",
        roller_gender="girl",
    ),
    StoryParams(
        damage="crack",
        mix="sealant",
        helper="cyclist",
        fix="umbrella_parade",
        foreman="Leo",
        rookie="Ava",
        roller="Finn",
        foreman_gender="boy",
        rookie_gender="girl",
        roller_gender="boy",
    ),
    StoryParams(
        damage="dip",
        mix="quickset",
        helper="gardener",
        fix="board_bridge",
        foreman="Nora",
        rookie="Sam",
        roller="Ruby",
        foreman_gender="girl",
        rookie_gender="boy",
        roller_gender="girl",
    ),
    StoryParams(
        damage="grate",
        mix="sealant",
        helper="mail",
        fix="twine_corral",
        foreman="Max",
        rookie="Ella",
        roller="Theo",
        foreman_gender="boy",
        rookie_gender="girl",
        roller_gender="boy",
    ),
]


ASP_RULES = r"""
works_with_mix(D, M) :- damage(D), mix(M), needed_mix(D, M), strength(M, S), depth(D, Need), S >= Need.
gift_match(H, F) :- helper(H), fix(F), gift_kind(H, G), needs_gift(F, G).

heat_value(M, V) :- mix(M), heat_softness(M, H), base_heat(B), V = B + H.
severity(D, M, 1) :- works_with_mix(D, M), heat_value(M, V), V >= 4, depth(D, 1).
severity(D, M, 2) :- works_with_mix(D, M), heat_value(M, V), V >= 4, depth(D, 2).
severity(D, M, 0) :- works_with_mix(D, M), heat_value(M, V), V < 4, depth(D, 1).
severity(D, M, 1) :- works_with_mix(D, M), heat_value(M, V), V < 4, depth(D, 2).

contains_problem(D, M, F) :- severity(D, M, Need), fix(F), power(F, P), P >= Need.
valid(D, M, H, F) :- damage(D), mix(M), helper(H), fix(F), works_with_mix(D, M), gift_match(H, F), contains_problem(D, M, F).

chosen_valid :- chosen_damage(D), chosen_mix(M), chosen_helper(H), chosen_fix(F), valid(D, M, H, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("base_heat", HEAT_LEVEL)]
    for damage_id, damage in DAMAGES.items():
        lines.append(asp.fact("damage", damage_id))
        lines.append(asp.fact("depth", damage_id, damage.depth))
        lines.append(asp.fact("needed_mix", damage_id, damage.needed_mix))
    for mix_id, mix in MIXES.items():
        lines.append(asp.fact("mix", mix_id))
        lines.append(asp.fact("strength", mix_id, mix.strength))
        lines.append(asp.fact("heat_softness", mix_id, mix.heat_softness))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("gift_kind", helper_id, helper.gift_kind))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("needs_gift", fix_id, fix.needs_gift))
        lines.append(asp.fact("power", fix_id, fix.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify_combo(params: StoryParams) -> bool:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_damage", params.damage),
            asp.fact("chosen_mix", params.mix),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show chosen_valid/0."))
    return bool(getattr(model, "symbols", None)) or ("chosen_valid" in str(model))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a hot road repair, a kind detour, and a funny teamwork save."
    )
    ap.add_argument("--damage", choices=sorted(DAMAGES))
    ap.add_argument("--mix", choices=sorted(MIXES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name not in avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.damage and args.mix:
        damage = DAMAGES[args.damage]
        mix = MIXES[args.mix]
        if not damage_works_with_mix(damage, mix):
            raise StoryError(explain_mix_rejection(damage, mix))
    if args.helper and args.fix:
        helper = HELPERS[args.helper]
        fix = FIXES[args.fix]
        damage = DAMAGES[args.damage] if args.damage else next(iter(DAMAGES.values()))
        mix = MIXES[args.mix] if args.mix else next(iter(MIXES.values()))
        if not (fix_matches_helper(helper, fix) and fix_contains_problem(damage, mix, fix)):
            raise StoryError(explain_fix_rejection(helper, fix, damage, mix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.damage is None or combo[0] == args.damage)
        and (args.mix is None or combo[1] == args.mix)
        and (args.helper is None or combo[2] == args.helper)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    damage_id, mix_id, helper_id, fix_id = rng.choice(combos)
    used: set[str] = set()
    foreman, fg = _pick_name(rng, used)
    used.add(foreman)
    rookie, rg = _pick_name(rng, used)
    used.add(rookie)
    roller, kg = _pick_name(rng, used)
    return StoryParams(
        damage=damage_id,
        mix=mix_id,
        helper=helper_id,
        fix=fix_id,
        foreman=foreman,
        rookie=rookie,
        roller=roller,
        foreman_gender=fg,
        rookie_gender=rg,
        roller_gender=kg,
    )


def generate(params: StoryParams) -> StorySample:
    if params.damage not in DAMAGES:
        raise StoryError(f"(Unknown damage '{params.damage}')")
    if params.mix not in MIXES:
        raise StoryError(f"(Unknown mix '{params.mix}')")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}')")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix '{params.fix}')")

    damage = DAMAGES[params.damage]
    mix = MIXES[params.mix]
    helper_cfg = HELPERS[params.helper]
    fix = FIXES[params.fix]

    if not damage_works_with_mix(damage, mix):
        raise StoryError(explain_mix_rejection(damage, mix))
    if not fix_matches_helper(helper_cfg, fix) or not fix_contains_problem(damage, mix, fix):
        raise StoryError(explain_fix_rejection(helper_cfg, fix, damage, mix))

    world = tell(
        damage=damage,
        mix=mix,
        helper_cfg=helper_cfg,
        fix=fix,
        foreman_name=params.foreman,
        rookie_name=params.rookie,
        roller_name=params.roller,
        foreman_gender=params.foreman_gender,
        rookie_gender=params.rookie_gender,
        roller_gender=params.roller_gender,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    smoke_cases = list(CURATED)
    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print("SMOKE resolve failed:", err)
            break

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header=f"### smoke {idx}")
        except Exception as err:
            rc = 1
            print(f"SMOKE generation failed for {params}: {err}")
            break
        try:
            if not asp_verify_combo(params):
                rc = 1
                print(f"ASP scenario check failed for {params}")
                break
        except Exception as err:
            rc = 1
            print(f"ASP scenario execution failed for {params}: {err}")
            break

    if rc == 0:
        print("OK: smoke tests passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (damage, mix, helper, fix) combos:\n")
        for damage, mix, helper, fix in combos:
            print(f"  {damage:8} {mix:10} {helper:8} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.damage} with {p.mix} ({p.helper} -> {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
