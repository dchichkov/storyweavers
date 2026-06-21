#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stockade_ingenious_splutter_problem_solving_tall_tale.py
===================================================================================

A standalone storyworld for tall-tale problem solving on a giant frontier patch.

Seed requirements carried into every sample:
- the story includes the words "stockade", "ingenious", and "splutter"
- the domain centers on Problem Solving
- the tone leans into cheerful Tall Tale exaggeration

Premise
-------
A child tends an oversized crop behind a stockade on the edge of a boastful
frontier town. On a blazing day, the water pump begins to splutter. The child
studies the trouble, chooses a fix, and either saves the crop in time or learns
that even an ingenious plan can arrive late if the sun gets too much of a head
start.

Reasonableness constraint
-------------------------
Not every fix fits every problem. A split pipe needs sealing, a clogged nozzle
needs clearing, and a slipping drive chain needs a new way to pull the pump.
The world refuses mismatched combinations.

Run it
------
    python storyworlds/worlds/gpt-5.4/stockade_ingenious_splutter_problem_solving_tall_tale.py
    python storyworlds/worlds/gpt-5.4/stockade_ingenious_splutter_problem_solving_tall_tale.py --problem leak --fix stockade_patch
    python storyworlds/worlds/gpt-5.4/stockade_ingenious_splutter_problem_solving_tall_tale.py --problem clog --fix stockade_patch
    python storyworlds/worlds/gpt-5.4/stockade_ingenious_splutter_problem_solving_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/stockade_ingenious_splutter_problem_solving_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "aunt", "mother"}
        male = {"boy", "man", "grandpa", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    brag: str
    sky: str
    stockade: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Crop:
    id: str
    label: str
    phrase: str
    boast: str
    drink_line: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    symptom: str
    cause: str
    need: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    does: set[str]
    power: int
    action: str
    success: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    title: str
    type: str
    advice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    crop: str
    problem: str
    fix: str
    helper: str
    hero_name: str
    hero_gender: str
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


def _r_droop(world: World) -> list[str]:
    crop = world.entities.get("crop")
    pump = world.entities.get("pump")
    if crop is None or pump is None:
        return []
    if pump.meters["flow"] >= THRESHOLD or crop.meters["thirst"] < THRESHOLD:
        return []
    sig = ("droop",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["droop"] += 1
    crop.memes["worry"] += 1
    hero = world.entities.get("hero")
    if hero is not None:
        hero.memes["worry"] += 1
    return ["__droop__"]


def _r_revive(world: World) -> list[str]:
    crop = world.entities.get("crop")
    pump = world.entities.get("pump")
    if crop is None or pump is None:
        return []
    if pump.meters["flow"] < THRESHOLD or crop.meters["droop"] < THRESHOLD:
        return []
    sig = ("revive",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["revived"] += 1
    crop.memes["relief"] += 1
    hero = world.entities.get("hero")
    if hero is not None:
        hero.memes["hope"] += 1
    return ["__revive__"]


CAUSAL_RULES = [
    Rule(name="droop", tag="physical", apply=_r_droop),
    Rule(name="revive", tag="physical", apply=_r_revive),
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
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the prairie edge",
        brag="where the wind could slick a pony's ears flat from twenty fields away",
        sky="The sky was so broad it looked as if it had elbowed every other sky aside.",
        stockade="an old cottonwood stockade around the patch",
        tags={"prairie", "sun"},
    ),
    "canyon": Setting(
        id="canyon",
        place="the red canyon bend",
        brag="where even echoes wore boots and came back for supper",
        sky="The cliffs held the heat like giant brick ovens with opinions.",
        stockade="a juniper stockade braced against the canyon gusts",
        tags={"canyon", "sun"},
    ),
    "riverside": Setting(
        id="riverside",
        place="the riverside flats",
        brag="where the river bragged louder than the townsfolk and still lost",
        sky="The afternoon shimmered so hard that fence posts looked half melted.",
        stockade="a willow stockade beside the water-meadow",
        tags={"river", "sun"},
    ),
}

CROPS = {
    "beans": Crop(
        id="beans",
        label="beans",
        phrase="towering beans",
        boast="The bean vines had climbed so high that passing clouds snagged on them like sheep on briars.",
        drink_line="Those beans drank faster than six mules after a parade.",
        ending="By sundown the beans were standing straight again, tickling the low clouds.",
        tags={"beans", "plants"},
    ),
    "pumpkins": Crop(
        id="pumpkins",
        label="pumpkins",
        phrase="wagon-round pumpkins",
        boast="The pumpkins were so big that one of them could have served as a schoolhouse for very polite mice.",
        drink_line="Those pumpkins liked a deep drink before the sun could toast their orange cheeks.",
        ending="By sundown the pumpkins sat bright and smug, round as harvest moons.",
        tags={"pumpkins", "plants"},
    ),
    "corn": Crop(
        id="corn",
        label="corn",
        phrase="flagpole-tall corn",
        boast="The corn stood so high and straight that crows had to rest halfway up before reaching the tassels.",
        drink_line="That corn slurped water with the steady seriousness of a brass band on payday.",
        ending="By sundown the corn was rattling in the breeze like a row of green trumpets.",
        tags={"corn", "plants"},
    ),
}

PROBLEMS = {
    "leak": Problem(
        id="leak",
        label="split pipe",
        symptom="a bright side-stream whipping out of the pipe",
        cause="a pipe seam had split and was throwing half the water into the dust",
        need="seal",
        severity=1,
        tags={"leak", "pump"},
    ),
    "clog": Problem(
        id="clog",
        label="choked nozzle",
        symptom="muddy coughs from the nozzle",
        cause="seed fluff and silt had packed the nozzle tight",
        need="clear",
        severity=1,
        tags={"clog", "pump"},
    ),
    "chain": Problem(
        id="chain",
        label="slipping drive chain",
        symptom="the chain skipping with a sad clack",
        cause="the drive chain had gone slack and would not keep the pump pulling",
        need="drive",
        severity=2,
        tags={"chain", "pump"},
    ),
}

FIXES = {
    "stockade_patch": Fix(
        id="stockade_patch",
        label="a stockade slat patch",
        does={"seal"},
        power=2,
        action="pulled a smooth slat from the stockade, wrapped it over the split with twine, and cinched the pipe tight",
        success="The side-stream stopped at once, and the water drove forward where it belonged.",
        fail="The patch slowed the spray, but the noon heat had already taken too much of the crop's strength.",
        qa_text="used a stockade slat and twine to seal the split pipe",
        tags={"stockade", "seal"},
    ),
    "reed_pick": Fix(
        id="reed_pick",
        label="a river-reed pick",
        does={"clear"},
        power=2,
        action="cut a tough reed, poked out the packed nozzle, and rinsed the clump clear",
        success="The nozzle quit coughing and sent out a clean shining arc.",
        fail="The clog came free, but the thirsty patch had already bowed under the hard sun.",
        qa_text="used a stiff reed to clear the clogged nozzle",
        tags={"reed", "clear"},
    ),
    "mule_loop": Fix(
        id="mule_loop",
        label="a mule-loop pull",
        does={"drive"},
        power=3,
        action="ran a rope from the wheel to old Junebug the mule and had him walk a neat circle until the chain bit again",
        success="The chain caught, the wheel turned true, and the pump began to thump like a drum in a parade.",
        fail="The chain finally caught, but it took long enough for the field to lose some of its brag.",
        qa_text="used a rope and a patient mule to pull the chain back into motion",
        tags={"mule", "drive"},
    ),
}

HELPERS = {
    "grandpa": Helper(
        id="grandpa",
        title="Grandpa Reed",
        type="grandpa",
        advice="measured twice with his eyes before saying a word",
        tags={"elder"},
    ),
    "aunt": Helper(
        id="aunt",
        title="Aunt May",
        type="aunt",
        advice="could hear a loose bolt complain from across a field",
        tags={"elder"},
    ),
    "marshal": Helper(
        id="marshal",
        title="Marshal Jo",
        type="man",
        advice="believed every hard problem ought to be looked square in the face",
        tags={"elder"},
    ),
}

GIRL_NAMES = ["Molly", "Clara", "Nell", "Sadie", "Ivy", "Pearl"]
BOY_NAMES = ["Eli", "Beau", "Jesse", "Cal", "Hank", "Toby"]


def valid_fix(problem: Problem, fix: Fix) -> bool:
    return problem.need in fix.does


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for sid in SETTINGS:
        for cid in CROPS:
            for pid, problem in PROBLEMS.items():
                for fid, fix in FIXES.items():
                    if valid_fix(problem, fix):
                        out.append((sid, cid, pid, fid))
    return out


def severity_total(problem: Problem, delay: int) -> int:
    return problem.severity + delay


def saved_in_time(problem: Problem, fix: Fix, delay: int) -> bool:
    return fix.power >= severity_total(problem, delay)


def outcome_of(params: StoryParams) -> str:
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    if not valid_fix(problem, fix):
        return "invalid"
    return "saved" if saved_in_time(problem, fix, params.delay) else "wilted"


def explain_rejection(problem: Problem, fix: Fix) -> str:
    if problem.need == "seal":
        need = "something that seals a split pipe"
    elif problem.need == "clear":
        need = "something that clears a packed nozzle"
    else:
        need = "something that pulls the pump drive again"
    return (
        f"(No story: {problem.label} needs {need}, but {fix.label} does not fit that job. "
        f"This world only tells fixes that honestly match the trouble.)"
    )


def intro(world: World, setting: Setting, crop: Crop, hero: Entity, helper: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} kept a patch at {setting.place}, {setting.brag}. "
        f"Around it stood {setting.stockade}, stout enough to make coyotes mind their manners."
    )
    world.say(setting.sky)
    world.say(
        f"Inside that stockade grew {crop.phrase}. {crop.boast} "
        f"{helper.label} said that on a good day the patch could shade half the county fair."
    )


def rising_need(world: World, crop: Crop, hero: Entity) -> None:
    crop_ent = world.get("crop")
    crop_ent.meters["thirst"] += 1
    hero.memes["care"] += 1
    world.say(
        f"By noon the sun was stamping on the ground like a giant boot. "
        f"{crop.drink_line}"
    )


def pump_trouble(world: World, problem: Problem, helper: Entity) -> None:
    pump = world.get("pump")
    pump.meters["flow"] = 0.0
    pump.meters[problem.id] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {helper.label} reached for the pump lever, the machine gave a tired splutter. "
        f"Instead of its usual gush, there came only {problem.symptom}."
    )
    world.say(f"In one blink, {problem.cause}.")
    if world.get("crop").meters["droop"] >= THRESHOLD:
        world.say(
            "The nearest leaves tipped downward as if the whole patch had suddenly remembered how hot noon could be."
        )


def inspect(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["focus"] += 1
    world.say(
        f'{hero.id} did not cry or stomp. {hero.pronoun().capitalize()} knelt beside the pump, '
        f"listened, looked, and thought while {helper.label} {helper.attrs.get('advice', 'stood nearby')}."
    )
    world.say(
        f'Soon {hero.id} had an ingenious idea. "It is not the whole pump," '
        f'{hero.pronoun()} said. "It is the {problem.label}."'
    )


def apply_fix(world: World, hero: Entity, helper: Entity, fix: Fix, crop: Crop, problem: Problem, delay: int) -> None:
    pump = world.get("pump")
    crop_ent = world.get("crop")
    hero.memes["resolve"] += 1
    world.say(
        f"Quick as a jackrabbit in a hurry, {hero.id} {fix.action}. "
        f"{helper.label} grinned and lent a steady hand."
    )
    if saved_in_time(problem, fix, delay):
        pump.meters["flow"] = 1.0
        pump.meters[problem.id] = 0.0
        crop_ent.meters["watered"] += 1
        crop_ent.meters["droop"] = 0.0
        propagate(world, narrate=False)
        world.say(fix.success)
        world.say(
            f"Water came racing down the furrows so fast it looked eager to apologize. {crop.ending}"
        )
    else:
        pump.meters["flow"] = 1.0
        pump.meters[problem.id] = 0.0
        crop_ent.meters["watered"] += 1
        crop_ent.meters["droop"] = 1.0
        world.say(fix.fail)
        world.say(
            f"The pump was running again, but one edge of the patch stayed bent and thirsty-looking. "
            f"Even in a tall tale, the sun can steal a march when it gets too much time."
        )


def ending_saved(world: World, hero: Entity, helper: Entity, crop: Crop) -> None:
    hero.memes["joy"] += 1
    hero.memes["confidence"] += 1
    world.say(
        f'{helper.label} tipped {helper.pronoun("possessive")} hat. "That was fine thinking," '
        f'{helper.pronoun()} said. {hero.id} laughed, and the whole patch seemed to stand a little taller for hearing it.'
    )
    world.say(
        f"That evening, folks said the patch behind the stockade had beaten the noon heat by sheer wit, "
        f"and nobody argued with them."
    )


def ending_wilted(world: World, hero: Entity, helper: Entity, crop: Crop) -> None:
    hero.memes["lesson"] += 1
    hero.memes["sadness"] += 1
    world.say(
        f'{helper.label} rested a hand on {hero.id}\'s shoulder. "You solved it true," '
        f'{helper.pronoun()} said, "only the sun had too much of a lead."'
    )
    world.say(
        f"{hero.id} nodded. Next morning {hero.pronoun()} mended the whole rig before breakfast, "
        f"and the patch behind the stockade drank first, not last."
    )


def tell(
    setting: Setting,
    crop: Crop,
    problem: Problem,
    fix: Fix,
    helper_cfg: Helper,
    hero_name: str,
    hero_gender: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.title,
            role="helper",
            attrs={"advice": helper_cfg.advice},
            tags=set(helper_cfg.tags),
        )
    )
    world.add(Entity(id="pump", type="pump", label="the pump", tags={"pump"}))
    world.add(Entity(id="crop", type="crop", label=crop.label, phrase=crop.phrase, tags=set(crop.tags)))
    world.add(Entity(id="stockade", type="fence", label="stockade", phrase=setting.stockade, tags={"stockade"}))

    intro(world, setting, crop, hero, helper)
    world.para()
    rising_need(world, crop, hero)
    pump_trouble(world, problem, helper)
    world.para()
    inspect(world, hero, helper, problem)
    apply_fix(world, hero, helper, fix, crop, problem, delay)
    world.para()

    outcome = "saved" if saved_in_time(problem, fix, delay) else "wilted"
    if outcome == "saved":
        ending_saved(world, hero, helper, crop)
    else:
        ending_wilted(world, hero, helper, crop)

    world.facts.update(
        setting=setting,
        crop_cfg=crop,
        problem=problem,
        fix=fix,
        helper=helper,
        hero=hero,
        delay=delay,
        outcome=outcome,
        crop_drooped=world.get("crop").meters["droop"] >= THRESHOLD,
        fixed=True,
    )
    return world


KNOWLEDGE = {
    "stockade": [
        (
            "What is a stockade?",
            "A stockade is a strong fence made from upright posts or boards. People use one to mark off or protect a place."
        )
    ],
    "pump": [
        (
            "What does a water pump do?",
            "A water pump moves water from one place to another. On a farm or in a garden, it can send water through pipes to thirsty plants."
        )
    ],
    "leak": [
        (
            "What is a leak in a pipe?",
            "A leak is a crack or opening where water escapes. When water leaks out, less of it reaches the place it is supposed to go."
        )
    ],
    "clog": [
        (
            "What is a clog?",
            "A clog is a lump of dirt, fluff, or something else stuck in a narrow space. It blocks the flow until someone clears it away."
        )
    ],
    "chain": [
        (
            "Why does a loose chain cause trouble in a machine?",
            "A loose chain can slip instead of pulling properly. Then the machine loses its steady motion and cannot do its job well."
        )
    ],
    "seal": [
        (
            "Why does sealing a split pipe help?",
            "Sealing closes the gap where water is escaping. That sends the water back through the pipe so it can reach the plants."
        )
    ],
    "clear": [
        (
            "Why does clearing a nozzle help?",
            "Clearing a nozzle opens the path for water to come out. Once the blockage is gone, the water can spray the way it should."
        )
    ],
    "drive": [
        (
            "Why does a pump need a good pull or drive?",
            "A pump has to keep moving in a steady way to push water along. If the drive slips, the water slows down or stops."
        )
    ],
    "plants": [
        (
            "Why do plants droop when they get too dry?",
            "Plants need water to stay firm and healthy. Without enough water, their leaves and stems lose strength and start to sag."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    crop = f["crop_cfg"]
    problem = f["problem"]
    fix = f["fix"]
    outcome = f["outcome"]
    if outcome == "saved":
        end = "and the child fixes it in time"
    else:
        end = "and the child solves it honestly, though the sun has already cost the field a little"
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that uses the words "stockade," "ingenious," and "splutter."',
        f"Tell a frontier-style story where {hero.id} tends giant {crop.label} at {setting.place}, the pump hits a {problem.label}, and {fix.label} {end}.",
        f"Write a gentle Problem Solving story with big exaggerations, a broken pump, and an ending that proves what changed in the field.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    crop = f["crop_cfg"]
    problem = f["problem"]
    fix = f["fix"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who cared for giant {crop.label}, and {helper.label}, who helped watch the patch. They worked together at {setting.place} behind a stockade."
        ),
        (
            "What problem happened to the pump?",
            f"The pump began to splutter because {problem.cause}. That meant the crop was not getting the water it needed at the hottest part of the day."
        ),
        (
            f"Why was {hero.id} worried?",
            f"{hero.id} was worried because the sun was strong and the {crop.label} were already thirsty. With the pump failing, the patch started to droop instead of standing proud."
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} had an ingenious idea and {fix.qa_text}. The fix matched the real trouble, so it gave the water a fair chance to run again."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did the story end?",
                f"The water reached the field in time, and the giant {crop.label} perked back up. The ending shows that careful thinking changed a failing pump into a working one."
            )
        )
    else:
        qa.append(
            (
                "Did the fix work perfectly?",
                f"Not perfectly. {hero.id} solved the pump problem, but the delay let the hot sun get ahead, so part of the patch stayed droopy for a while."
            )
        )
        qa.append(
            (
                "What did they do after that?",
                f"They fixed the whole rig early the next morning so the trouble would not get another head start. The lesson came from seeing that a good plan still needs enough time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    problem = f["problem"]
    fix = f["fix"]
    tags = {"stockade", "pump", "plants"} | set(problem.tags) | set(fix.tags)
    out: list[tuple[str, str]] = []
    order = ["stockade", "pump", "leak", "clog", "chain", "seal", "clear", "drive", "plants"]
    for tag in order:
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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="prairie",
        crop="pumpkins",
        problem="leak",
        fix="stockade_patch",
        helper="grandpa",
        hero_name="Molly",
        hero_gender="girl",
        delay=0,
    ),
    StoryParams(
        setting="canyon",
        crop="beans",
        problem="clog",
        fix="reed_pick",
        helper="aunt",
        hero_name="Eli",
        hero_gender="boy",
        delay=0,
    ),
    StoryParams(
        setting="riverside",
        crop="corn",
        problem="chain",
        fix="mule_loop",
        helper="marshal",
        hero_name="Clara",
        hero_gender="girl",
        delay=0,
    ),
    StoryParams(
        setting="prairie",
        crop="beans",
        problem="chain",
        fix="mule_loop",
        helper="grandpa",
        hero_name="Beau",
        hero_gender="boy",
        delay=2,
    ),
]


ASP_RULES = r"""
compatible(P, F) :- problem(P), fix(F), needs(P, T), does(F, T).
valid(S, C, P, F) :- setting(S), crop(C), compatible(P, F).

severity_total(V) :- chosen_problem(P), severity(P, S), delay(D), V = S + D.
saved :- chosen_problem(P), chosen_fix(F), compatible(P, F), power(F, Pow), severity_total(V), Pow >= V.
outcome(saved) :- saved.
outcome(wilted) :- chosen_problem(P), chosen_fix(F), compatible(P, F), not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CROPS:
        lines.append(asp.fact("crop", cid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, problem.need))
        lines.append(asp.fact("severity", pid, problem.severity))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fix.power))
        for tag in sorted(fix.does):
            lines.append(asp.fact("does", fid, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(30):
        args = build_parser().parse_args([])
        try:
            p = resolve_params(args, random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            mismatches.append((params, py, cl))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcome cases differ.")
        for params, py, cl in mismatches[:5]:
            print(" ", params, py, cl)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old_stdout
        if "stockade" not in sample.story or "ingenious" not in sample.story or "splutter" not in sample.story:
            raise StoryError("smoke test story missed one of the required seed words")
        print("OK: smoke test story generation and emit() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a child solves a spluttering pump problem behind a stockade."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the sun gets a head start")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not valid_fix(problem, fix):
            raise StoryError(explain_rejection(problem, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.crop is None or combo[1] == args.crop)
        and (args.problem is None or combo[2] == args.problem)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, crop_id, problem_id, fix_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        crop=crop_id,
        problem=problem_id,
        fix=fix_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {params.crop})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    if not valid_fix(problem, fix):
        raise StoryError(explain_rejection(problem, fix))

    world = tell(
        setting=SETTINGS[params.setting],
        crop=CROPS[params.crop],
        problem=problem,
        fix=fix,
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, crop, problem, fix) combos:\n")
        for setting_id, crop_id, problem_id, fix_id in combos:
            print(f"  {setting_id:10} {crop_id:10} {problem_id:8} {fix_id}")
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
            header = (
                f"### {p.hero_name}: {p.problem} -> {p.fix} at {p.setting} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
