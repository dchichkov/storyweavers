#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/infringe_percent_sound_effects_kindness_slice_of.py
================================================================================

A standalone story world about a child planning a tiny pretend show and learning
how to use sound effects kindly.

The domain is intentionally small and slice-of-life:
- a child builds a simple home show,
- a loud sound-effect idea bumps against somebody nearby who needs quiet,
- a kind helper predicts the problem,
- the child either listens right away or makes one noisy mistake first,
- they choose a thoughtful fix and end with a show that is "100 percent kind."

The two seed words appear naturally in the stories:
- "infringe" appears in the kindness lesson about not intruding on another
  person's quiet time;
- "percent" appears in the ending sign or line about the show being "100 percent
  kind."

Run it
------
    python storyworlds/worlds/gpt-5.4/infringe_percent_sound_effects_kindness_slice_of.py
    python storyworlds/worlds/gpt-5.4/infringe_percent_sound_effects_kindness_slice_of.py --tool pot_lid
    python storyworlds/worlds/gpt-5.4/infringe_percent_sound_effects_kindness_slice_of.py --need none
    python storyworlds/worlds/gpt-5.4/infringe_percent_sound_effects_kindness_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/infringe_percent_sound_effects_kindness_slice_of.py --qa --json
    python storyworlds/worlds/gpt-5.4/infringe_percent_sound_effects_kindness_slice_of.py --verify
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
KINDNESS_MIN = 2
LISTENING_TRAITS = {"careful", "kind", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "neighbor_woman"}
        male = {"boy", "father", "man", "neighbor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    prep_area: str
    quiet_place: str
    show_place: str
    outside_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundTool:
    id: str
    label: str
    phrase: str
    sound: int
    onomat: str
    action: str
    soft_version: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuietNeed:
    id: str
    who_label: str
    who_type: str
    activity: str
    quiet_need: int
    warning: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    reduce: int = 0
    move_outside: bool = False
    kindness: int = 2
    offer_text: str = ""
    ending_text: str = ""
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_disturbance(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    quiet = world.get("quiet")
    room = world.get("room")
    if child.meters["noise"] < THRESHOLD:
        return out
    if quiet.meters["quiet_need"] < THRESHOLD:
        return out
    if child.attrs.get("location") != quiet.attrs.get("location"):
        return out
    if child.meters["noise"] <= quiet.meters["quiet_need"]:
        return out
    sig = ("disturbance", child.id, quiet.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    quiet.meters["disturbed"] += 1
    room.meters["tension"] += 1
    child.memes["alarm"] += 1
    out.append("__disturbance__")
    return out


CAUSAL_RULES = [
    Rule(name="disturbance", tag="social", apply=_r_disturbance),
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
        for sent in produced:
            world.say(sent)
    return produced


def risk_present(tool: SoundTool, need: QuietNeed) -> bool:
    return need.quiet_need > 0 and tool.sound > need.quiet_need


def fix_works(tool: SoundTool, need: QuietNeed, fix: Fix) -> bool:
    if need.quiet_need <= 0:
        return True
    if fix.move_outside:
        return True
    return max(tool.sound - fix.reduce, 0) <= need.quiet_need


def kind_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.kindness >= KINDNESS_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for tool_id, tool in TOOLS.items():
            for need_id, need in NEEDS.items():
                for fix_id, fix in FIXES.items():
                    if need_id == "none":
                        if fix_works(tool, need, fix):
                            combos.append((setting_id, tool_id, need_id, fix_id))
                    elif risk_present(tool, need) and fix.kindness >= KINDNESS_MIN and fix_works(tool, need, fix):
                        combos.append((setting_id, tool_id, need_id, fix_id))
    return combos


def would_listen(trait: str) -> bool:
    return trait in LISTENING_TRAITS


def outcome_of(params: "StoryParams") -> str:
    return "listened" if would_listen(params.trait) else "oops_then_fixed"


def predict_disturbance(world: World, tool: SoundTool) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["noise"] += tool.sound
    propagate(sim, narrate=False)
    quiet = sim.get("quiet")
    return {
        "disturbance": quiet.meters["disturbed"] >= THRESHOLD,
        "noise": child.meters["noise"],
        "need": quiet.meters["quiet_need"],
    }


def introduce(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"After school, {child.id} and {helper.id} spread paper stars, tape, and crayons across "
        f"{world.setting.prep_area}. They were making a tiny home show with a cardboard moon and a string puppet."
    )
    world.say(
        f"{child.id} wanted the show to feel real, with sound effects that could make every little scene sparkle."
    )


def mention_quiet_need(world: World, quiet: Entity) -> None:
    if quiet.meters["quiet_need"] < THRESHOLD:
        world.say(
            f"The apartment felt easy and open, and no one nearby needed the rooms to stay extra quiet."
        )
        return
    world.say(
        f"Just beyond the hall, {quiet.label} was {quiet.attrs['activity']}. The home felt softer than usual because quiet mattered right then."
    )


def choose_tool(world: World, child: Entity, tool: SoundTool) -> None:
    child.memes["excitement"] += 1
    world.say(
        f'"For the thunder part, I can use {tool.phrase}," {child.id} said. "{tool.onomat.capitalize()}! It will sound amazing."'
    )


def warn(world: World, helper: Entity, child: Entity, tool: SoundTool, quiet: Entity) -> None:
    pred = predict_disturbance(world, tool)
    world.facts["predicted_disturbance"] = pred["disturbance"]
    if quiet.meters["quiet_need"] < THRESHOLD:
        helper.memes["support"] += 1
        world.say(
            f'{helper.id} smiled. "That could be fun. Let\'s just keep it tidy so the puppet strings do not tangle."'
        )
        return
    helper.memes["kindness"] += 1
    world.say(
        f'{helper.id} glanced toward {world.setting.quiet_place} and shook {helper.pronoun("possessive")} head. '
        f'"We should not infringe on {quiet.label} while {quiet.pronoun()} is {quiet.attrs["activity"]}. '
        f'{quiet.attrs["warning"]}"'
    )


def listen_now(world: World, child: Entity, tool: SoundTool) -> None:
    child.memes["kindness"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} looked at {tool.phrase} and then toward the quiet hall. The exciting idea still glowed, but kindness felt bigger."
    )
    world.say(
        f'"You\'re right," {child.id} said softly. "I want the show to be fun, not too loud for somebody else."'
    )


def make_noise_once(world: World, child: Entity, quiet: Entity, tool: SoundTool) -> None:
    child.meters["noise"] += tool.sound
    propagate(world, narrate=False)
    world.say(
        f"Still, {child.id} wanted to hear it just once. {child.pronoun().capitalize()} {tool.action} -- {tool.onomat}!"
    )
    if quiet.meters["disturbed"] >= THRESHOLD:
        quiet.memes["startled"] += 1
        world.say(
            f"A pause rippled through the apartment. Even from {world.setting.quiet_place}, it was easy to feel that the sound had landed too hard."
        )
        child.memes["regret"] += 1
        world.say(
            f"{child.id}'s cheeks turned warm. Right away, {child.pronoun()} knew the boom had been bigger than the room could kindly hold."
        )
    else:
        world.say(
            f"The sound bounced once and faded. It did not trouble anyone, but it still felt sharper than the little show needed."
        )


def apologize(world: World, child: Entity, quiet: Entity) -> None:
    if quiet.meters["disturbed"] >= THRESHOLD:
        world.say(
            f'"I\'m sorry," {child.id} whispered toward the hall. "{quiet.label.capitalize()} needed quiet, and I forgot for a second."'
        )
        child.memes["kindness"] += 1


def offer_fix(world: World, helper: Entity, child: Entity, tool: SoundTool, fix: Fix) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f'{helper.id} stayed calm. "{fix.offer_text.format(tool=tool.label, soft=tool.soft_version, outside=world.setting.outside_place)}"'
    )


def apply_fix(world: World, child: Entity, tool: SoundTool, fix: Fix) -> None:
    if fix.move_outside:
        child.attrs["location"] = "outside"
        world.facts["final_location"] = "outside"
    else:
        child.meters["noise"] = max(tool.sound - fix.reduce, 0)
        world.facts["final_location"] = "inside"
    child.memes["joy"] += 1
    child.memes["kindness"] += 1
    child.memes["confidence"] += 1


def ending(world: World, child: Entity, helper: Entity, quiet: Entity, tool: SoundTool, fix: Fix) -> None:
    sign = world.facts.get("sign_text", "100 percent kind")
    if fix.move_outside:
        world.say(
            f"Soon they were in {world.setting.outside_place}, and the evening air had room for a bigger sound. "
            f"{fix.ending_text.format(tool=tool.label, soft=tool.soft_version)}"
        )
    else:
        world.say(
            f"Soon the puppet moon swung above the table, and the storm scene came alive in a gentler way. "
            f"{fix.ending_text.format(tool=tool.label, soft=tool.soft_version)}"
        )
    if quiet.meters["quiet_need"] >= THRESHOLD:
        world.say(
            f"In the quiet part of the home, {quiet.ending_image}."
        )
    world.say(
        f'At the edge of the stage, {child.id} taped up a small sign that said "{sign}." '
        f"{helper.id} gave a proud little clap, and the whole show felt exactly right."
    )


def tell(
    setting: Setting,
    tool: SoundTool,
    need: QuietNeed,
    fix: Fix,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_name: str = "Theo",
    helper_type: str = "boy",
    parent_type: str = "mother",
    trait: str = "kind",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["steady"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    quiet = world.add(
        Entity(
            id="quiet",
            kind="character",
            type=need.who_type,
            role="quiet_person",
            label=need.who_label,
            attrs={"activity": need.activity, "warning": need.warning, "location": "inside"},
        )
    )
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    prop = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    child.attrs["location"] = "inside"
    quiet.attrs["location"] = "inside"
    quiet.meters["quiet_need"] = float(need.quiet_need)
    world.facts["sign_text"] = "100 percent kind"

    introduce(world, child, helper)
    mention_quiet_need(world, quiet)

    world.para()
    choose_tool(world, child, tool)
    warn(world, helper, child, tool, quiet)

    world.para()
    if would_listen(trait):
        listen_now(world, child, tool)
    else:
        make_noise_once(world, child, quiet, tool)
        apologize(world, child, quiet)

    offer_fix(world, helper, child, tool, fix)
    apply_fix(world, child, tool, fix)

    world.para()
    ending(world, child, helper, quiet, tool, fix)

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        quiet=quiet,
        setting=setting,
        tool_cfg=tool,
        need_cfg=need,
        fix_cfg=fix,
        disturbed=quiet.meters["disturbed"] >= THRESHOLD,
        outcome=outcome_of(
            StoryParams(
                setting=setting.id,
                tool=tool.id,
                need=need.id,
                fix=fix.id,
                child_name=child_name,
                child_type=child_type,
                helper_name=helper_name,
                helper_type=helper_type,
                parent=parent_type,
                trait=trait,
            )
        ),
    )
    return world


SETTINGS = {
    "apartment": Setting(
        id="apartment",
        place="the apartment",
        prep_area="the kitchen table",
        quiet_place="the bedroom door",
        show_place="the little rug by the sofa",
        outside_place="the courtyard bench",
        tags={"home"},
    ),
    "duplex": Setting(
        id="duplex",
        place="the duplex",
        prep_area="the dining room floor",
        quiet_place="the hallway by the guest room",
        show_place="the patch of floor under the lamp",
        outside_place="the small front steps",
        tags={"home"},
    ),
    "house": Setting(
        id="house",
        place="the house",
        prep_area="the coffee table",
        quiet_place="the den doorway",
        show_place="the blanket fort in the living room",
        outside_place="the back porch",
        tags={"home"},
    ),
}

TOOLS = {
    "pot_lid": SoundTool(
        id="pot_lid",
        label="a pot lid and spoon",
        phrase="a pot lid and a wooden spoon",
        sound=4,
        onomat="CLANG-CLANG",
        action="tapped the spoon on the lid",
        soft_version="fingertip taps on a paper box",
        tags={"loud", "sound_effects"},
    ),
    "toy_drum": SoundTool(
        id="toy_drum",
        label="a toy drum",
        phrase="the toy drum",
        sound=3,
        onomat="BUM-BUM",
        action="patted the drum with both hands",
        soft_version="a pillow drumbeat with open palms",
        tags={"drum", "sound_effects"},
    ),
    "metal_shaker": SoundTool(
        id="metal_shaker",
        label="a metal shaker",
        phrase="the metal shaker full of beans",
        sound=3,
        onomat="SHAKA-SHAKA",
        action="shook the little tin hard",
        soft_version="a soft rice shaker wrapped in a sock",
        tags={"shaker", "sound_effects"},
    ),
    "paper_thunder": SoundTool(
        id="paper_thunder",
        label="a sheet of poster paper",
        phrase="a big sheet of poster paper",
        sound=1,
        onomat="fwump-fwish",
        action="wobbled the paper over the stage",
        soft_version="paper thunder",
        tags={"paper", "sound_effects"},
    ),
}

NEEDS = {
    "baby_nap": QuietNeed(
        id="baby_nap",
        who_label="the baby next door",
        who_type="thing",
        activity="taking a nap",
        quiet_need=1,
        warning="A loud bang could wake the baby up.",
        ending_image="the baby kept sleeping, one tiny hand still tucked under the blanket",
        tags={"baby", "quiet"},
    ),
    "grandpa_rest": QuietNeed(
        id="grandpa_rest",
        who_label="Grandpa",
        who_type="man",
        activity="resting with a cool cloth on his forehead",
        quiet_need=1,
        warning="Grandpa needs the room to stay calm while he rests.",
        ending_image="Grandpa rested easily and later smiled at the puppet moon from his chair",
        tags={"rest", "quiet"},
    ),
    "mom_call": QuietNeed(
        id="mom_call",
        who_label="Mom",
        who_type="mother",
        activity="finishing an important phone call for work",
        quiet_need=2,
        warning="If the room booms now, Mom will lose the words she is trying to hear.",
        ending_image="Mom finished the call and later gave them a grateful thumbs-up",
        tags={"call", "quiet"},
    ),
    "none": QuietNeed(
        id="none",
        who_label="nobody nearby",
        who_type="thing",
        activity="anything that needed special quiet",
        quiet_need=0,
        warning="No one needs extra quiet right now.",
        ending_image="the whole home simply felt easy and cheerful",
        tags={"easy"},
    ),
}

FIXES = {
    "paper_swap": Fix(
        id="paper_swap",
        label="paper thunder",
        reduce=3,
        move_outside=False,
        kindness=3,
        offer_text="How about we make thunder with poster paper instead of {tool}? It can still sound stormy without being so sharp.",
        ending_text="Their new thunder went fwump-fwish instead of crashing, and it made everyone lean in to listen.",
        tags={"paper", "kindness"},
    ),
    "sock_wrap": Fix(
        id="sock_wrap",
        label="sock-wrapped shaker",
        reduce=2,
        move_outside=False,
        kindness=2,
        offer_text="How about we wrap the noisy part and use a softer version, like {soft}? Then the sound can stay in the show without jumping into somebody else's quiet.",
        ending_text="The softer sound made the puppet storm feel cozy, as if rain were pattering on a window instead of banging on the room.",
        tags={"soft", "kindness"},
    ),
    "move_outside": Fix(
        id="move_outside",
        label="move the show outside",
        reduce=0,
        move_outside=True,
        kindness=3,
        offer_text="How about we carry the show to {outside}? Then you can make the big sound there and still be thoughtful inside.",
        ending_text="Out there, the sound could be bold and happy, and it no longer pressed on anybody else's quiet time.",
        tags={"outside", "kindness"},
    ),
}


GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "Lucy", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Sam", "Noah", "Eli", "Jack", "Finn", "Leo"]
TRAITS = ["kind", "careful", "thoughtful", "gentle", "impulsive", "stubborn"]


@dataclass
class StoryParams:
    setting: str
    tool: str
    need: str
    fix: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "sound_effects": [
        (
            "What are sound effects?",
            "Sound effects are extra sounds that help a story feel real, like rain noises or thunder noises. They can be loud or soft, so people choose them carefully."
        )
    ],
    "quiet": [
        (
            "Why is quiet sometimes important at home?",
            "Quiet can help people rest, think, or listen. Being quiet at the right time is one way to show kindness."
        )
    ],
    "baby": [
        (
            "Why do babies wake up easily?",
            "Babies can wake up when they hear a sudden sound because their sleep is light. A loud noise can startle them before they settle again."
        )
    ],
    "rest": [
        (
            "Why does a tired person need a calm room?",
            "A calm room helps a tired or sick person relax. Less noise can make resting easier."
        )
    ],
    "call": [
        (
            "Why can loud sounds make phone calls hard?",
            "Loud sounds cover up the words people are trying to hear. Then it becomes hard to listen and answer."
        )
    ],
    "paper": [
        (
            "How can paper make a thunder sound?",
            "If you wobble a big sheet of paper, it can make a soft stormy noise. It sounds interesting without being as sharp as metal."
        )
    ],
    "drum": [
        (
            "What does a drum do?",
            "A drum makes a beat when you tap it. You can play it loudly or softly."
        )
    ],
    "shaker": [
        (
            "What is a shaker instrument?",
            "A shaker is something with little bits inside that rattle when you move it. It can make a gentle or a noisy sound."
        )
    ],
    "kindness": [
        (
            "What does kindness sound like in a home?",
            "Kindness can sound like softer voices, patient waiting, and checking how other people feel. Sometimes kindness means changing your own plan a little."
        )
    ],
    "outside": [
        (
            "Why is it sometimes better to move a noisy game outside?",
            "Outside, sound has more room to spread out. That can make it easier to play loudly without bothering people indoors."
        )
    ],
}
KNOWLEDGE_ORDER = ["sound_effects", "quiet", "baby", "rest", "call", "paper", "drum", "shaker", "kindness", "outside"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    tool = f["tool_cfg"]
    need = f["need_cfg"]
    if need.id == "none":
        return [
            f'Write a slice-of-life story for a 3-to-5-year-old about a child making sound effects for a home show, and include the words "infringe" and "percent".',
            f"Tell a gentle story where {child.id} uses {tool.label} while planning a puppet show, and the ending says the show is 100 percent kind.",
            "Write a cozy home story with sound effects, kindness, and a small handmade stage."
        ]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old about a child planning a home show with sound effects, and include the words "infringe" and "percent".',
        f"Tell a gentle story where {child.id} wants to use {tool.label}, but someone nearby needs quiet and the children choose kindness first.",
        f"Write a simple story about making room for other people at home, with a small show, a noisy idea, and a 100 percent kind ending."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    quiet = f["quiet"]
    tool = f["tool_cfg"]
    fix = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.id}, who were making a tiny home show together. The story is also about thinking kindly about {quiet.label}."
        ),
        (
            "What did the children want to make?",
            f"They wanted to make a little puppet show with sound effects. The stage was small and homemade, which gave the story its warm slice-of-life feeling."
        ),
        (
            f"What sound idea did {child.id} have?",
            f"{child.id} wanted to use {tool.label} for a storm sound. {child.pronoun('subject').capitalize()} thought the noise would make the show feel real."
        ),
    ]
    if quiet.meters["quiet_need"] >= THRESHOLD:
        qa.append(
            (
                f"Why did {helper.id} say they should not infringe on {quiet.label}?",
                f"{helper.id} knew that {quiet.label} was {quiet.attrs['activity']}, so a loud sound could bother {quiet.pronoun('object')}. The warning was about kindness, not just rules."
            )
        )
    else:
        qa.append(
            (
                "Why did the room feel easy in this story?",
                "No one nearby needed special quiet, so the children did not have to worry about disturbing anyone. That made the planning feel relaxed and cheerful."
            )
        )
    if outcome == "listened":
        qa.append(
            (
                f"What did {child.id} do after the warning?",
                f"{child.id} listened right away and chose a gentler plan. That quick choice showed that kindness mattered more than making the biggest possible noise."
            )
        )
    else:
        qa.append(
            (
                f"What mistake did {child.id} make, and what happened next?",
                f"{child.id} tried the loud sound once before stopping. Then {child.pronoun('subject')} felt sorry, apologized, and helped choose a kinder way to finish the show."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They used {fix.label} so the show could still have sound effects without pressing on somebody else's quiet time. The fix worked because it either softened the noise or moved it to a better place."
        )
    )
    qa.append(
        (
            'Why did the sign say "100 percent kind"?',
            f'The sign showed what had changed by the end: the children were thinking about other people as well as their own fun. The ending image proves the show was not only playful, but thoughtful too.'
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sound_effects", "kindness"}
    need = f["need_cfg"]
    tool = f["tool_cfg"]
    fix = f["fix_cfg"]
    tags |= set(need.tags)
    tags |= set(tool.tags)
    tags |= set(fix.tags)
    if need.id != "none":
        tags.add("quiet")
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
    for ent in list(world.entities.values()):
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="apartment",
        tool="pot_lid",
        need="baby_nap",
        fix="paper_swap",
        child_name="Mina",
        child_type="girl",
        helper_name="Theo",
        helper_type="boy",
        parent="mother",
        trait="kind",
    ),
    StoryParams(
        setting="duplex",
        tool="toy_drum",
        need="grandpa_rest",
        fix="move_outside",
        child_name="Ben",
        child_type="boy",
        helper_name="Lucy",
        helper_type="girl",
        parent="father",
        trait="stubborn",
    ),
    StoryParams(
        setting="house",
        tool="metal_shaker",
        need="mom_call",
        fix="sock_wrap",
        child_name="Ava",
        child_type="girl",
        helper_name="Leo",
        helper_type="boy",
        parent="mother",
        trait="impulsive",
    ),
    StoryParams(
        setting="apartment",
        tool="paper_thunder",
        need="none",
        fix="paper_swap",
        child_name="Nora",
        child_type="girl",
        helper_name="Sam",
        helper_type="boy",
        parent="father",
        trait="gentle",
    ),
]


def explain_rejection(tool: SoundTool, need: QuietNeed, fix: Optional[Fix] = None) -> str:
    if need.id != "none" and not risk_present(tool, need):
        return (
            f"(No story: {tool.label} is not loud enough to create a real kindness problem for "
            f"{need.who_label} while {need.activity}. Pick a louder tool or a stricter quiet need.)"
        )
    if fix is not None and fix.kindness < KINDNESS_MIN:
        return (
            f"(No story: fix '{fix.id}' is known, but it scores too low on kindness for this world. "
            f"Choose a fix that protects someone else's quiet more thoughtfully.)"
        )
    if fix is not None and not fix_works(tool, need, fix):
        return (
            f"(No story: {fix.label} would not solve the noise problem from {tool.label} for "
            f"{need.who_label}. The solution must really soften or relocate the sound.)"
        )
    return "(No story: this combination does not form a reasonable kindness problem and fix.)"


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
risk(Tool, Need) :- tool(Tool), need(Need), loudness(Tool, L), quiet_need(Need, Q), Q > 0, L > Q.
kind_fix(Fix)    :- fix(Fix), kindness(Fix, K), kindness_min(M), K >= M.
works(Tool, Need, Fix) :- move_outside(Fix), tool(Tool), need(Need).
works(Tool, Need, Fix) :- tool(Tool), need(Need), fix(Fix),
                          loudness(Tool, L), quiet_need(Need, Q), reduce(Fix, R),
                          L - R <= Q.
valid(S, T, N, F) :- setting(S), tool(T), need(N), fix(F), N = none, works(T, N, F).
valid(S, T, N, F) :- setting(S), tool(T), need(N), fix(F), risk(T, N), kind_fix(F), works(T, N, F).

% --- outcome model ----------------------------------------------------------
listened :- trait(T), listening_trait(T).
outcome(listened) :- listened.
outcome(oops_then_fixed) :- not listened.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("loudness", tid, tool.sound))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("quiet_need", nid, need.quiet_need))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("reduce", fid, fix.reduce))
        lines.append(asp.fact("kindness", fid, fix.kindness))
        if fix.move_outside:
            lines.append(asp.fact("move_outside", fid))
    for tr in sorted(LISTENING_TRAITS):
        lines.append(asp.fact("listening_trait", tr))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("trait", params.trait)
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
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "100 percent kind" not in smoke.story:
            raise StoryError("smoke story missing expected ending marker")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a small home show, sound effects, and kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.need:
        tool = TOOLS[args.tool]
        need = NEEDS[args.need]
        if need.id != "none" and not risk_present(tool, need):
            raise StoryError(explain_rejection(tool, need))
    if args.fix:
        fix = FIXES[args.fix]
        if args.tool and args.need:
            tool = TOOLS[args.tool]
            need = NEEDS[args.need]
            if fix.kindness < KINDNESS_MIN or not fix_works(tool, need, fix):
                raise StoryError(explain_rejection(tool, need, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.tool is None or combo[1] == args.tool)
        and (args.need is None or combo[2] == args.need)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, tool_id, need_id, fix_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_type)
    helper_name = args.helper_name or _pick_name(rng, helper_type, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        tool=tool_id,
        need=need_id,
        fix=fix_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    setting = SETTINGS[params.setting]
    tool = TOOLS[params.tool]
    need = NEEDS[params.need]
    fix = FIXES[params.fix]

    if need.id != "none" and not risk_present(tool, need):
        raise StoryError(explain_rejection(tool, need))
    if fix.kindness < KINDNESS_MIN or not fix_works(tool, need, fix):
        raise StoryError(explain_rejection(tool, need, fix))

    world = tell(
        setting=setting,
        tool=tool,
        need=need,
        fix=fix,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, tool, need, fix) combos:\n")
        for setting_id, tool_id, need_id, fix_id in combos:
            print(f"  {setting_id:10} {tool_id:14} {need_id:12} {fix_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} & {p.helper_name}: {p.tool}, {p.need}, {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
