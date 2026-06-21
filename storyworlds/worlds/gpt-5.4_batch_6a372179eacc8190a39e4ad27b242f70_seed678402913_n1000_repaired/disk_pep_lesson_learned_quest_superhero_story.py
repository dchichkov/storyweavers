#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/disk_pep_lesson_learned_quest_superhero_story.py

A small superhero storyworld about a child hero on a quest to recover a missing
disk. The hero starts with lots of pep and an unsafe idea, then learns that real
heroes use teamwork and the right tool.

Run examples
------------
python storyworlds/worlds/gpt-5.4/disk_pep_lesson_learned_quest_superhero_story.py
python storyworlds/worlds/gpt-5.4/disk_pep_lesson_learned_quest_superhero_story.py --quest beacon --place gutter --helper ladder_team
python storyworlds/worlds/gpt-5.4/disk_pep_lesson_learned_quest_superhero_story.py --helper magnet_line --place gutter
python storyworlds/worlds/gpt-5.4/disk_pep_lesson_learned_quest_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/disk_pep_lesson_learned_quest_superhero_story.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Quest:
    id: str
    disk_label: str
    disk_phrase: str
    mission: str
    need_line: str
    ending_image: str
    material: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PlaceCfg:
    id: str
    label: str
    phrase: str
    height: int
    open_access: bool
    narrow: bool
    below_grate: bool
    edge: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    max_height: int
    needs_open: bool
    works_narrow: bool
    works_below: bool
    metal_only: bool
    team: bool
    action: str
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


def _r_notice_risk(world: World) -> list[str]:
    hero = world.get("hero")
    disk = world.get("disk")
    place = world.get("place")
    out: list[str] = []
    if disk.meters["lost"] >= THRESHOLD and place.meters["danger"] >= THRESHOLD:
        sig = ("risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append("__risk__")
    return out


def _r_recover(world: World) -> list[str]:
    disk = world.get("disk")
    helper = world.get("helper")
    out: list[str] = []
    if helper.meters["reaching"] >= THRESHOLD and disk.meters["reachable"] >= THRESHOLD:
        sig = ("recover",)
        if sig not in world.fired:
            world.fired.add(sig)
            disk.meters["lost"] = 0.0
            disk.meters["home"] += 1
            world.get("place").meters["danger"] = 0.0
            world.get("hero").memes["relief"] += 1
            world.get("sidekick").memes["relief"] += 1
            out.append("__recover__")
    return out


CAUSAL_RULES = [
    Rule(name="notice_risk", tag="emotional", apply=_r_notice_risk),
    Rule(name="recover", tag="physical", apply=_r_recover),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def helper_fits(quest: Quest, place: PlaceCfg, helper: HelperCfg) -> bool:
    if place.height > helper.max_height:
        return False
    if helper.needs_open and not place.open_access:
        return False
    if place.narrow and not helper.works_narrow:
        return False
    if place.below_grate and not helper.works_below:
        return False
    if helper.metal_only and quest.material != "metal":
        return False
    return True


def explain_rejection(quest: Quest, place: PlaceCfg, helper: HelperCfg) -> str:
    if place.height > helper.max_height:
        return (
            f"(No story: {helper.label} cannot reach {place.phrase}. "
            f"It only works up to height {helper.max_height}, but this spot is {place.height}.)"
        )
    if helper.needs_open and not place.open_access:
        return (
            f"(No story: {helper.label} needs an open angle, but {place.phrase} is cramped.)"
        )
    if place.narrow and not helper.works_narrow:
        return (
            f"(No story: {helper.label} is too clumsy for the narrow space at {place.phrase}.)"
        )
    if place.below_grate and not helper.works_below:
        return (
            f"(No story: {helper.label} cannot slip under the grate at {place.phrase}.)"
        )
    if helper.metal_only and quest.material != "metal":
        return (
            f"(No story: {helper.label} only works on metal, but the {quest.disk_label} is {quest.material}.)"
        )
    return "(No story: this helper does not fit this quest.)"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for qid, quest in QUESTS.items():
        for pid, place in PLACES.items():
            for hid, helper in HELPERS.items():
                if helper_fits(quest, place, helper):
                    combos.append((qid, pid, hid))
    return combos


def predict_rush(world: World, place: PlaceCfg) -> dict:
    sim = world.copy()
    sim.get("hero").memes["rush"] += 1
    sim.get("place").meters["danger"] = float(1 + place.height)
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("place").meters["danger"],
        "worry": sim.get("hero").memes["worry"],
    }


def introduce(world: World, hero: Entity, sidekick: Entity, quest: Quest) -> None:
    hero.memes["pep"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"In Brightblock City, {hero.id} was a little superhero with a cape, quick feet, "
        f"and lots of pep. {sidekick.id}, {hero.pronoun('possessive')} faithful sidekick, "
        f"liked plans almost as much as adventures."
    )
    world.say(
        f"That afternoon, a new quest zoomed in on the clubhouse alarm screen: {quest.need_line}"
    )


def discover_loss(world: World, hero: Entity, sidekick: Entity, quest: Quest, place: PlaceCfg) -> None:
    disk = world.get("disk")
    disk.meters["lost"] += 1
    world.get("place").meters["danger"] = float(1 + place.height)
    propagate(world, narrate=False)
    world.say(
        f"The {quest.disk_label} was missing from its stand. A silver arrow on the screen "
        f"pointed to {place.phrase}, where the disk had landed."
    )
    world.say(
        f'"Quest time!" cried {hero.id}. "{quest.mission}!" {sidekick.id} nodded, but leaned '
        f"closer to see how tricky the spot looked."
    )


def rush_idea(world: World, hero: Entity, place: PlaceCfg) -> None:
    hero.memes["rush"] += 1
    world.say(
        f"{hero.id} bounced on {hero.pronoun('possessive')} toes. "
        f'"I can just scramble up and grab it from {place.label}!" {hero.pronoun()} said.'
    )


def sidekick_warning(world: World, hero: Entity, sidekick: Entity, place: PlaceCfg) -> None:
    pred = predict_rush(world, place)
    sidekick.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{sidekick.id} put a hand on the cape. "Slow down," {sidekick.pronoun()} said. '
        f'"That spot is too tricky for a jump. If you rush, the quest gets harder, not easier."'
    )


def mentor_arrives(world: World, mentor: Entity) -> None:
    mentor.memes["calm"] += 1
    world.say(
        f"Just then, {mentor.label} strode over with a calm smile. "
        f'"A real superhero keeps the pep," {mentor.pronoun()} said, '
        f'"but points it in the right direction."'
    )


def choose_helper(world: World, hero: Entity, sidekick: Entity, helper: HelperCfg, place: PlaceCfg) -> None:
    helper_ent = world.get("helper")
    helper_ent.meters["ready"] += 1
    if helper.team:
        hero.memes["teamwork"] += 1
        sidekick.memes["teamwork"] += 1
        world.say(
            f"Together they grabbed {helper.phrase}. {sidekick.id} steadied the base while "
            f"{hero.id} followed the plan one careful step at a time."
        )
    else:
        hero.memes["focus"] += 1
        sidekick.memes["focus"] += 1
        world.say(
            f"{mentor_line(world)} Together they chose {helper.phrase}, the tool that actually fit "
            f"{place.label}."
        )


def mentor_line(world: World) -> str:
    mentor = world.get("mentor")
    return f'{mentor.label} handed it over and said, "Use the right helper first."'


def recover_disk(world: World, hero: Entity, sidekick: Entity, quest: Quest, helper: HelperCfg) -> None:
    helper_ent = world.get("helper")
    disk = world.get("disk")
    helper_ent.meters["reaching"] += 1
    disk.meters["reachable"] += 1
    propagate(world, narrate=False)
    world.say(helper.action.format(hero=hero.id, sidekick=sidekick.id, disk=quest.disk_label))
    world.say(
        f"In one careful moment, the {quest.disk_label} came free. It landed safely in "
        f"{hero.id}'s hands instead of bouncing into more trouble."
    )


def return_disk(world: World, hero: Entity, sidekick: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"They hurried back to the clubhouse and slid the disk into place. At once, "
        f"{quest.ending_image}."
    )


def lesson(world: World, hero: Entity, sidekick: Entity, mentor: Entity) -> None:
    hero.memes["lesson"] += 1
    sidekick.memes["lesson"] += 1
    hero.memes["rush"] = 0.0
    world.say(
        f'{mentor.label} tapped the badge on {hero.id}\'s chest. "What did this quest teach you?"'
    )
    world.say(
        f'{hero.id} grinned. "Pep is great, but not by itself. First we look, then we plan, '
        f'and then we save the day."'
    )
    world.say(
        f'{sidekick.id} laughed and bumped {hero.pronoun("possessive")} shoulder. '
        f'"That is how careful heroes shine."'
    )


def tell(
    quest: Quest,
    place: PlaceCfg,
    helper: HelperCfg,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    sidekick_name: str = "Bolt",
    sidekick_gender: str = "boy",
    mentor_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=sidekick_gender, label=sidekick_name, role="sidekick"))
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_type, label=("Captain Mom" if mentor_type == "mother" else "Captain Dad"), role="mentor"))
    disk = world.add(Entity(id="disk", type="disk", label=quest.disk_label, phrase=quest.disk_phrase, tags=set(quest.tags)))
    place_ent = world.add(Entity(id="place", type="place", label=place.label, phrase=place.phrase, tags=set(place.tags)))
    helper_ent = world.add(Entity(id="helper", type="tool", label=helper.label, phrase=helper.phrase, tags=set(helper.tags)))

    introduce(world, hero, sidekick, quest)
    discover_loss(world, hero, sidekick, quest, place)

    world.para()
    rush_idea(world, hero, place)
    sidekick_warning(world, hero, sidekick, place)
    mentor_arrives(world, mentor)

    world.para()
    choose_helper(world, hero, sidekick, helper, place)
    recover_disk(world, hero, sidekick, quest, helper)
    return_disk(world, hero, sidekick, quest)

    world.para()
    lesson(world, hero, sidekick, mentor)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        mentor=mentor,
        quest=quest,
        place_cfg=place,
        helper_cfg=helper,
        disk=disk,
        place=place_ent,
        helper=helper_ent,
        recovered=disk.meters["home"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "beacon": Quest(
        id="beacon",
        disk_label="beacon disk",
        disk_phrase="the brass beacon disk",
        mission="We have to relight the rooftop beacon before dusk",
        need_line="The rooftop beacon could not start without its beacon disk.",
        ending_image="a warm gold light spilled over the street like a superhero sunrise",
        material="metal",
        tags={"disk", "beacon"},
    ),
    "map": Quest(
        id="map",
        disk_label="map disk",
        disk_phrase="the painted map disk",
        mission="We have to open the secret map wall before the treasure club arrives",
        need_line="The secret map wall would not turn without its map disk.",
        ending_image="the map wall clicked open and glowing paths ran across it in blue lines",
        material="cardboard",
        tags={"disk", "map"},
    ),
    "parade": Quest(
        id="parade",
        disk_label="rhythm disk",
        disk_phrase="the bright rhythm disk",
        mission="We have to start the pep parade music before the first drum beat",
        need_line="The parade speaker would not sing without its rhythm disk.",
        ending_image="music leapt into the air and the whole block clapped in time",
        material="plastic",
        tags={"disk", "music", "pep"},
    ),
}

PLACES = {
    "branch": PlaceCfg(
        id="branch",
        label="a high tree branch",
        phrase="a high tree branch over the sidewalk",
        height=2,
        open_access=True,
        narrow=False,
        below_grate=False,
        edge=False,
        tags={"tree"},
    ),
    "drain": PlaceCfg(
        id="drain",
        label="the storm drain",
        phrase="the narrow storm drain by the curb",
        height=0,
        open_access=False,
        narrow=True,
        below_grate=True,
        edge=False,
        tags={"drain"},
    ),
    "gutter": PlaceCfg(
        id="gutter",
        label="the schoolhouse gutter",
        phrase="the schoolhouse gutter near the roof edge",
        height=3,
        open_access=True,
        narrow=False,
        below_grate=False,
        edge=True,
        tags={"roof"},
    ),
}

HELPERS = {
    "grabber": HelperCfg(
        id="grabber",
        label="the long grabber claw",
        phrase="the long grabber claw",
        max_height=2,
        needs_open=True,
        works_narrow=False,
        works_below=False,
        metal_only=False,
        team=False,
        action="{hero} stretched out the grabber claw, pinched the disk gently, and drew it back inch by inch.",
        qa_text="used the long grabber claw to pinch the disk and pull it back safely",
        tags={"grabber"},
    ),
    "magnet_line": HelperCfg(
        id="magnet_line",
        label="the magnet line",
        phrase="the magnet line on a red cord",
        max_height=1,
        needs_open=False,
        works_narrow=True,
        works_below=True,
        metal_only=True,
        team=False,
        action="{hero} lowered the magnet line through the gap, and the disk clicked onto it with a tiny snap.",
        qa_text="lowered the magnet line and let the metal disk click onto it",
        tags={"magnet"},
    ),
    "ladder_team": HelperCfg(
        id="ladder_team",
        label="the rescue ladder",
        phrase="the rescue ladder",
        max_height=3,
        needs_open=True,
        works_narrow=False,
        works_below=False,
        metal_only=False,
        team=True,
        action="{sidekick} held the ladder steady while {hero} climbed just high enough to lift the disk free.",
        qa_text="used the rescue ladder together, with one child steadying it and the other lifting the disk free",
        tags={"ladder", "teamwork"},
    ),
    "hook_pole": HelperCfg(
        id="hook_pole",
        label="the hook pole",
        phrase="the hook pole with a soft loop",
        max_height=3,
        needs_open=True,
        works_narrow=False,
        works_below=False,
        metal_only=False,
        team=False,
        action="{hero} looped the hook pole around the disk and eased it away from the edge before it could slip.",
        qa_text="looped the hook pole around the disk and eased it away from the edge",
        tags={"pole"},
    ),
}

GIRL_NAMES = ["Nova", "Skye", "Mira", "Luna", "Ava", "Zuri"]
BOY_NAMES = ["Bolt", "Dash", "Milo", "Finn", "Kai", "Leo"]


@dataclass
class StoryParams:
    quest: str
    place: str
    helper: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    mentor: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        quest="beacon",
        place="gutter",
        helper="ladder_team",
        hero_name="Nova",
        hero_gender="girl",
        sidekick_name="Bolt",
        sidekick_gender="boy",
        mentor="mother",
    ),
    StoryParams(
        quest="map",
        place="branch",
        helper="grabber",
        hero_name="Mira",
        hero_gender="girl",
        sidekick_name="Finn",
        sidekick_gender="boy",
        mentor="father",
    ),
    StoryParams(
        quest="beacon",
        place="drain",
        helper="magnet_line",
        hero_name="Skye",
        hero_gender="girl",
        sidekick_name="Dash",
        sidekick_gender="boy",
        mentor="mother",
    ),
    StoryParams(
        quest="parade",
        place="gutter",
        helper="hook_pole",
        hero_name="Luna",
        hero_gender="girl",
        sidekick_name="Kai",
        sidekick_gender="boy",
        mentor="father",
    ),
]


KNOWLEDGE = {
    "disk": [(
        "What is a disk?",
        "A disk is a flat, round object. Some disks can be part of a machine or a game, and if one goes missing, the whole job may stop."
    )],
    "pep": [(
        "What does pep mean?",
        "Pep means lively energy and spirit. Pep can help you start a job, but you still need to think carefully."
    )],
    "magnet": [(
        "What does a magnet do?",
        "A magnet pulls on some kinds of metal. That is why a magnet can help pick up a metal object without using your hands."
    )],
    "ladder": [(
        "Why should a ladder be steady?",
        "A ladder should be steady so it does not wobble or slip. When someone holds it and the climber goes slowly, it is much safer."
    )],
    "teamwork": [(
        "Why is teamwork helpful on a quest?",
        "Teamwork helps because one person can notice danger while another person does the reaching. Working together makes hard jobs safer and smarter."
    )],
    "beacon": [(
        "What is a beacon?",
        "A beacon is a bright light that helps people notice where something is. It can guide people or signal that it is time to begin."
    )],
    "map": [(
        "Why are maps useful?",
        "Maps show where things are and how to get there. A good map helps you choose a path instead of guessing."
    )],
    "music": [(
        "Why can music help a parade?",
        "Music gives people a beat to follow. It makes marching and cheering feel lively and together."
    )],
}
KNOWLEDGE_ORDER = ["disk", "pep", "magnet", "ladder", "teamwork", "beacon", "map", "music"]


def generation_prompts(world: World) -> list[str]:
    quest = world.facts["quest"]
    place = world.facts["place_cfg"]
    helper = world.facts["helper_cfg"]
    hero = world.facts["hero"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "disk" and "pep".',
        f"Tell a quest story where {hero.label} must recover a {quest.disk_label} from {place.label}, starts with a rushed idea, and learns to use {helper.label} instead.",
        "Write a gentle Lesson Learned story where a small hero discovers that energy is good, but planning and teamwork are better.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    mentor = world.facts["mentor"]
    quest = world.facts["quest"]
    place = world.facts["place_cfg"]
    helper = world.facts["helper_cfg"]
    pred = int(world.facts.get("predicted_danger", 0))

    return [
        (
            "Who is the story about?",
            f"It is about the little superhero {hero.label}, {hero.pronoun('possessive')} sidekick {sidekick.label}, and {mentor.label}. Together they go on a quest to get back the missing {quest.disk_label}."
        ),
        (
            f"Why was the {quest.disk_label} important?",
            f"It was important because {quest.need_line.lower()} Without it, the mission could not be finished."
        ),
        (
            f"Why did {sidekick.label} tell {hero.label} not to rush?",
            f"{sidekick.label} saw that the disk was stuck at {place.phrase}, which was a tricky place to reach. In the world model, rushing there raised the danger to {pred}, so slowing down was the safer choice."
        ),
        (
            f"How did they get the disk back?",
            f"They {helper.qa_text}. That worked because the helper matched the place instead of depending on a wild jump."
        ),
        (
            "What lesson did the hero learn?",
            f"{hero.label} learned that pep is helpful only when it is guided by a plan. The story ends with {hero.pronoun()} understanding that careful teamwork is part of being a real superhero."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"disk"}
    quest = world.facts["quest"]
    helper = world.facts["helper_cfg"]
    tags |= set(quest.tags)
    tags |= set(helper.tags)
    if world.facts["helper_cfg"].team:
        tags.add("teamwork")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(Q, P, H) :- quest(Q), place(P), helper(H),
                 place_height(P, PH), helper_height(H, HH), PH <= HH,
                 not bad_open(P,H), not bad_narrow(P,H), not bad_below(P,H), not bad_metal(Q,H).

bad_open(P,H)   :- place_open(P,0), helper_needs_open(H,1).
bad_narrow(P,H) :- place_narrow(P,1), helper_works_narrow(H,0).
bad_below(P,H)  :- place_below(P,1), helper_works_below(H,0).
bad_metal(Q,H)  :- helper_metal_only(H,1), quest_material(Q,M), M != metal.

valid(Q, P, H) :- fits(Q, P, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_material", qid, quest.material))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_height", pid, place.height))
        lines.append(asp.fact("place_open", pid, 1 if place.open_access else 0))
        lines.append(asp.fact("place_narrow", pid, 1 if place.narrow else 0))
        lines.append(asp.fact("place_below", pid, 1 if place.below_grate else 0))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_height", hid, helper.max_height))
        lines.append(asp.fact("helper_needs_open", hid, 1 if helper.needs_open else 0))
        lines.append(asp.fact("helper_works_narrow", hid, 1 if helper.works_narrow else 0))
        lines.append(asp.fact("helper_works_below", hid, 1 if helper.works_below else 0))
        lines.append(asp.fact("helper_metal_only", hid, 1 if helper.metal_only else 0))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero quest storyworld about recovering a missing disk."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest is not None and args.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {args.quest})")
    if args.place is not None and args.place not in PLACES:
        raise StoryError(f"(Unknown place: {args.place})")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")

    if args.quest and args.place and args.helper:
        quest = QUESTS[args.quest]
        place = PLACES[args.place]
        helper = HELPERS[args.helper]
        if not helper_fits(quest, place, helper):
            raise StoryError(explain_rejection(quest, place, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.place is None or combo[1] == args.place)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    qid, pid, hid = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero or _pick_name(rng, hero_gender)
    sidekick_name = args.sidekick or _pick_name(rng, sidekick_gender, avoid=hero_name)
    mentor = args.mentor or rng.choice(["mother", "father"])

    return StoryParams(
        quest=qid,
        place=pid,
        helper=hid,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        mentor=mentor,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.place not in PLACES or params.helper not in HELPERS:
        raise StoryError("(Story parameters refer to unknown registry keys.)")
    quest = QUESTS[params.quest]
    place = PLACES[params.place]
    helper = HELPERS[params.helper]
    if not helper_fits(quest, place, helper):
        raise StoryError(explain_rejection(quest, place, helper))

    world = tell(
        quest=quest,
        place=place,
        helper=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        mentor_type=params.mentor,
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
        print("MISMATCH between Python and ASP valid combos.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE resolve failed: {err}")

    for case in smoke_cases:
        try:
            sample = generate(case)
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"SMOKE generate failed for {case}: {err}")
            continue
        if not sample.story.strip():
            rc = 1
            print(f"SMOKE generate produced empty story for {case}.")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, place, helper) combos:\n")
        for qid, pid, hid in combos:
            print(f"  {qid:8} {pid:8} {hid}")
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
            header = f"### {p.hero_name}: {p.quest} at {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
