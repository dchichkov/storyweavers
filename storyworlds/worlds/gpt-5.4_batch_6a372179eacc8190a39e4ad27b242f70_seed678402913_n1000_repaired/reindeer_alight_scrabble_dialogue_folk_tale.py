#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reindeer_alight_scrabble_dialogue_folk_tale.py
=========================================================================

A small standalone storyworld for a winter folk tale with dialogue, built around
three anchor words: reindeer, alight, and scrabble.

Premise
-------
A child walks into the winter dusk with a lantern and a small helpful thing.
In the hush of the snow, the child hears a reindeer in trouble: perhaps its
antler is caught, perhaps its hooves scrabble on ice, perhaps hunger has made
it too weak to cross the drifts. The child must choose a help that honestly fits
the trouble. If the match is reasonable, the reindeer is freed or steadied,
trust grows, and the creature leads the child to a bright ending where the
village windows stand alight.

Constraint
----------
This world refuses weak "fixes." Sand helps on ice but not with a tangled antler.
A knife cuts a willow cord but does not feed a hungry animal. Oats can hearten a
hungry reindeer but do nothing for ice. The story exists only when the setting,
the trouble, and the carried help make common sense together.

Run it
------
    python storyworlds/worlds/gpt-5.4/reindeer_alight_scrabble_dialogue_folk_tale.py
    python storyworlds/worlds/gpt-5.4/reindeer_alight_scrabble_dialogue_folk_tale.py --setting ford --trouble ice --helper sand
    python storyworlds/worlds/gpt-5.4/reindeer_alight_scrabble_dialogue_folk_tale.py --trouble hunger --helper knife
    python storyworlds/worlds/gpt-5.4/reindeer_alight_scrabble_dialogue_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/reindeer_alight_scrabble_dialogue_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/reindeer_alight_scrabble_dialogue_folk_tale.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    path: str
    winter_light: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    noun: str
    trouble_line: str
    motion_line: str
    relief_line: str
    need_tag: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    solve_tag: str
    action_line: str
    qa_line: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    child = world.get("child")
    deer = world.get("reindeer")
    if deer.meters["troubled"] < THRESHOLD:
        return []
    sig = ("fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["pity"] += 1
    child.memes["resolve"] += 1
    deer.memes["fear"] += 1
    return ["__fear__"]


def _r_trust(world: World) -> list[str]:
    deer = world.get("reindeer")
    helper = world.get("helper")
    if deer.meters["freed"] < THRESHOLD:
        return []
    sig = ("trust", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    deer.memes["trust"] += 1
    child = world.get("child")
    child.memes["wonder"] += 1
    return ["__trust__"]


CAUSAL_RULES = [
    Rule(name="fear", tag="emotion", apply=_r_fear),
    Rule(name="trust", tag="emotion", apply=_r_trust),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def trouble_fits_setting(setting: Setting, trouble: Trouble) -> bool:
    return trouble.id in setting.affords


def helper_matches(helper: Helper, trouble: Trouble) -> bool:
    return helper.solve_tag == trouble.need_tag


def valid_story(setting: Setting, trouble: Trouble, helper: Helper) -> bool:
    return trouble_fits_setting(setting, trouble) and helper_matches(helper, trouble)


def predict_help(world: World, helper_id: str) -> dict:
    sim = world.copy()
    deer = sim.get("reindeer")
    helper = sim.get(helper_id)
    trouble_cfg = sim.facts["trouble_cfg"]
    helper_cfg = sim.facts["helper_cfg"]
    if helper_matches(helper_cfg, trouble_cfg):
        deer.meters["troubled"] = 0.0
        deer.meters["freed"] += 1
    propagate(sim, narrate=False)
    return {
        "freed": deer.meters["freed"] >= THRESHOLD,
        "trust": deer.memes["trust"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, elder: Entity, helper: Helper) -> None:
    world.say(
        f"In the oldest days, when the snow remembered every footstep, {child.id} "
        f"lived at the edge of the pine wood with {child.pronoun('possessive')} "
        f"{elder.label_word}."
    )
    world.say(
        f"On the night of the winter lantern walk, {elder.label_word.capitalize()} "
        f"placed {helper.phrase} in {child.id}'s mittened hand and a small lantern "
        f"in the other."
    )
    world.say(
        f'"Walk softly," said {elder.label_word}. "Even the dark listens on a night '
        f'like this."'
    )


def send_out(world: World, child: Entity, setting: Setting) -> None:
    child.memes["duty"] += 1
    world.say(
        f"{child.id} followed {setting.path}. The air was so still that the little "
        f"flame did not shake, and {setting.winter_light}."
    )


def meet_trouble(world: World, child: Entity, deer: Entity, trouble: Trouble) -> None:
    deer.meters["troubled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from beyond a drift, came a sharp scrabble in the snow. {child.id} "
        f"lifted the lantern and saw a reindeer by the path."
    )
    world.say(trouble.trouble_line)
    world.say(
        f'"Oh, poor wanderer," whispered {child.id}. "{trouble.noun.capitalize()} '
        f'should not be your bed for the night."'
    )
    deer.memes["fear"] += 1
    world.say(trouble.motion_line)


def choose_help(world: World, child: Entity, deer: Entity, helper: Helper, trouble: Trouble) -> None:
    helper_ent = world.get("helper")
    pred = predict_help(world, helper_ent.id)
    world.facts["predicted_freed"] = pred["freed"]
    if not pred["freed"]:
        raise StoryError(
            f"(No story: {helper.label} does not sensibly solve {trouble.noun}. "
            f"Pick help that matches the trouble.)"
        )
    child.memes["courage"] += 1
    world.say(
        f'{child.id} remembered the thing in {child.pronoun("possessive")} pocket. '
        f'"Be still," {child.pronoun()} said softly. "I think I can help."'
    )
    deer.meters["troubled"] = 0.0
    deer.meters["freed"] += 1
    propagate(world, narrate=False)
    world.say(helper.action_line)
    world.say(trouble.relief_line)
    world.say(
        f'The reindeer stamped once, not in fear now but in thanks. "{child.id}," '
        f'said the child in wonder, "you understand a grateful silence better than '
        f'many people understand words."'
    )


def reward_path(world: World, child: Entity, deer: Entity, setting: Setting) -> None:
    deer.memes["guide"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Instead of bounding away, the reindeer turned and walked ahead through the "
        f"trees. Every few steps it looked back, as if asking whether {child.id} had "
        f"the courage to follow."
    )
    world.say(
        f'{child.id} followed. "Lead on, then," {child.pronoun()} said, and the little '
        f'lantern shone over a hidden, easy track in the snow.'
    )
    world.say(
        f"When they came out from the pines, the whole village lay below them, "
        f"{setting.winter_light}, and even the far windows were alight like a necklace "
        f"of warm stars."
    )


def ending(world: World, child: Entity, elder: Entity) -> None:
    child.memes["homecoming"] += 1
    world.say(
        f"At the door, {elder.label_word} saw the bright face and the snow on the hem "
        f"of {child.id}'s coat."
    )
    world.say(
        f'"Grandmother," said {child.id}' if elder.type == "grandmother"
        else f'"Grandfather," said {child.id}'
    )
    world.paragraphs[-1][-1] += ', "I did not lose my way. A reindeer showed me the kind road after I helped it."'
    world.say(
        f'{elder.label_word.capitalize()} smiled as if this explained something old. '
        f'"That is how the winter wood pays a kindness," {elder.pronoun()} said.'
    )
    world.say(
        f"And from that year on, whenever the first hard snow came, {child.id}'s "
        f"house set a little gift by the pines for passing hooves. Folk still say "
        f"that on the coldest nights you may hear a thankful reindeer breathing "
        f"there, while the village lamps burn steady and alight."
    )


def tell(
    setting: Setting,
    trouble: Trouble,
    helper: Helper,
    *,
    child_name: str = "Anya",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    child_trait: str = "gentle",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[child_trait],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
        )
    )
    deer = world.add(
        Entity(
            id="reindeer",
            kind="character",
            type="reindeer",
            label="the reindeer",
            role="helper",
            tags={"reindeer"},
        )
    )
    world.add(
        Entity(
            id="helper",
            kind="thing",
            type="helper",
            label=helper.label,
            phrase=helper.phrase,
            role="helper_item",
            tags=set(helper.tags),
        )
    )

    introduce(world, child, elder, helper)
    send_out(world, child, setting)
    world.para()
    meet_trouble(world, child, deer, trouble)
    choose_help(world, child, deer, helper, trouble)
    world.para()
    reward_path(world, child, deer, setting)
    ending(world, child, elder)

    world.facts.update(
        child=child,
        elder=elder,
        reindeer=deer,
        setting_cfg=setting,
        trouble_cfg=trouble,
        helper_cfg=helper,
        helped=deer.meters["freed"] >= THRESHOLD,
        trusted=deer.memes["trust"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "ford": Setting(
        id="ford",
        place="the frozen ford",
        path="the path that bent toward the frozen ford",
        winter_light="the snow itself seemed to hold a pale blue light",
        affords={"ice"},
        tags={"winter", "ice"},
    ),
    "thicket": Setting(
        id="thicket",
        place="the willow thicket",
        path="the narrow track beside the willow thicket",
        winter_light="the frost on the twigs glimmered like glass",
        affords={"snag"},
        tags={"winter", "willow"},
    ),
    "ridge": Setting(
        id="ridge",
        place="the wind-swept ridge",
        path="the long rise toward the wind-swept ridge",
        winter_light="the moon washed the drifts in silver",
        affords={"hunger"},
        tags={"winter", "moon"},
    ),
}

TROUBLES = {
    "ice": Trouble(
        id="ice",
        noun="a sheet of river ice",
        trouble_line="Its front hooves could not bite into the glazed bank, and they did nothing but scrabble and slide.",
        motion_line='The creature tossed its head and blew a white cloud into the air. "Easy now," said the child.',
        relief_line="Soon the hooves found their hold, and the reindeer stepped up from the river edge as lightly as a shadow.",
        need_tag="grip",
        tags={"ice", "winter"},
    ),
    "snag": Trouble(
        id="snag",
        noun="a willow cord wound around one antler",
        trouble_line="A fallen willow switch had twisted round one antler and held fast each time the animal tried to pull away.",
        motion_line='It backed and lunged, and the branches answered with another dry scrabble. "Hush," said the child.',
        relief_line="The loop parted, and the reindeer lifted its head free under the lantern glow.",
        need_tag="cut",
        tags={"willow", "forest"},
    ),
    "hunger": Trouble(
        id="hunger",
        noun="an empty belly and shaking legs",
        trouble_line="The reindeer was not caught at all, yet its sides were hollow and its legs trembled in the drift.",
        motion_line='It pawed weakly at the crusted snow in a tired scrabble. "So that is it," said the child. "You are hungry."',
        relief_line="After a few mouthfuls, strength came back into its neck and shoulders, and it stood tall again.",
        need_tag="food",
        tags={"food", "winter"},
    ),
}

HELPERS = {
    "sand": Helper(
        id="sand",
        label="sand",
        phrase="a small pouch of sand",
        solve_tag="grip",
        action_line="The child opened the pouch and scattered the sand over the ice until the shining bank turned rough and brown.",
        qa_line="The child scattered sand on the ice so the hooves could grip instead of sliding.",
        tags={"sand", "ice"},
    ),
    "knife": Helper(
        id="knife",
        label="a little knife",
        phrase="a little knife wrapped in cloth",
        solve_tag="cut",
        action_line="Very carefully, the child slid the little knife under the willow cord and cut the twisted strand without touching the antler.",
        qa_line="The child used the little knife to cut the willow cord away from the antler.",
        tags={"knife", "forest"},
    ),
    "oats": Helper(
        id="oats",
        label="oats",
        phrase="a warm pouch of oats",
        solve_tag="food",
        action_line="The child poured the oats into cupped mittens, and the reindeer ate with quick, grateful breaths.",
        qa_line="The child fed the reindeer oats, which gave it the strength to stand and walk again.",
        tags={"oats", "food"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Tala", "Ira", "Sona", "Niva", "Lina", "Runa"]
BOY_NAMES = ["Mikko", "Ivo", "Tarin", "Pavel", "Niko", "Sami", "Lev", "Oren"]
TRAITS = ["gentle", "patient", "brave", "kind", "quiet", "steadfast"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    helper: str
    child_name: str
    child_gender: str
    elder_type: str
    child_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="ford",
        trouble="ice",
        helper="sand",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="patient",
    ),
    StoryParams(
        setting="thicket",
        trouble="snag",
        helper="knife",
        child_name="Mikko",
        child_gender="boy",
        elder_type="grandfather",
        child_trait="brave",
    ),
    StoryParams(
        setting="ridge",
        trouble="hunger",
        helper="oats",
        child_name="Runa",
        child_gender="girl",
        elder_type="grandmother",
        child_trait="kind",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid, trouble in TROUBLES.items():
            for hid, helper in HELPERS.items():
                if valid_story(setting, trouble, helper):
                    combos.append((sid, tid, hid))
    return combos


KNOWLEDGE = {
    "reindeer": [
        (
            "What is a reindeer?",
            "A reindeer is a deer that lives in cold places. It has wide hooves for snow, and both walking and digging are easier for it in winter than for many animals.",
        )
    ],
    "ice": [
        (
            "Why is ice slippery?",
            "Ice is smooth, and pressure can make a thin wet layer on top of it. That makes feet and hooves slide instead of gripping.",
        )
    ],
    "sand": [
        (
            "Why does sand help on ice?",
            "Sand makes the surface rougher. That gives shoes or hooves something to catch on instead of sliding.",
        )
    ],
    "knife": [
        (
            "What is a knife used for in careful hands?",
            "A knife can cut rope, twine, or plant stems. It must be used slowly and carefully, usually with a grown-up's teaching.",
        )
    ],
    "oats": [
        (
            "What are oats?",
            "Oats are small grains that people and animals can eat. They give energy, which helps a tired body feel stronger.",
        )
    ],
    "winter": [
        (
            "Why do winter nights look bright even in the dark?",
            "Snow reflects moonlight and lamplight. That makes the world seem to glow even after sunset.",
        )
    ],
    "folk": [
        (
            "What is a folk tale?",
            "A folk tale is a story told and retold by people. It often carries an old lesson about kindness, wisdom, or courage.",
        )
    ],
}
KNOWLEDGE_ORDER = ["reindeer", "ice", "sand", "knife", "oats", "winter", "folk"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    trouble = f["trouble_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting_cfg"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "reindeer", "alight", and "scrabble".',
        f"Tell a winter folk tale with dialogue where {child.id} meets a reindeer near {setting.place} and uses {helper.label} to solve {trouble.noun}.",
        "Write a gentle old-fashioned story where kindness to an animal leads a child safely home through the snow.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    trouble = f["trouble_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child walking out on a winter errand, and a reindeer met near {setting.place}. It also includes {child.pronoun('possessive')} {elder.label_word}, who sends {child.pronoun('object')} out with a lantern.",
        ),
        (
            "What did the child hear in the snow?",
            f"{child.id} heard a sharp scrabble in the snow and followed the sound with the lantern. That is how {child.pronoun()} discovered the reindeer in trouble.",
        ),
        (
            "What trouble was the reindeer in?",
            f"The reindeer was struggling with {trouble.noun}. The danger mattered because it could not travel safely until the child helped.",
        ),
        (
            f"How did {child.id} help the reindeer?",
            f"{helper.qa_line} That worked because the help matched the problem instead of being a random guess.",
        ),
        (
            "What changed after the help worked?",
            f"After the reindeer was safe, it trusted the child and guided {child.pronoun('object')} along a hidden good path. The ending proves the change because the child reaches home with the village windows alight below.",
        ),
        (
            "What lesson does the story teach?",
            f"It teaches that careful kindness can turn fear into friendship. When {child.id} stopped to help instead of hurrying past, the winter wood answered with help in return.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"reindeer", "winter", "folk"} | set(world.facts["trouble_cfg"].tags) | set(world.facts["helper_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, trouble: Trouble, helper: Helper) -> str:
    if not trouble_fits_setting(setting, trouble):
        return (
            f"(No story: {trouble.noun} does not belong at {setting.place}. "
            f"Pick a trouble that fits the setting.)"
        )
    return (
        f"(No story: {helper.label} does not sensibly solve {trouble.noun}. "
        f"Choose help that matches the problem.)"
    )


ASP_RULES = r"""
fits(S, T) :- setting(S), trouble(T), affords(S, T).
matches(H, T) :- helper(H), trouble(T), solves(H, Need), needs(T, Need).
valid(S, T, H) :- fits(S, T), matches(H, T).

chosen_valid :- chosen_setting(S), chosen_trouble(T), chosen_helper(H), valid(S, T, H).
outcome(helped) :- chosen_valid.
outcome(impossible) :- not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, tid))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("needs", tid, trouble.need_tag))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("solves", hid, helper.solve_tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_trouble", params.trouble),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    helper = HELPERS[params.helper]
    return "helped" if valid_story(setting, trouble, helper) else "impossible"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a winter folk tale of a child, a reindeer, and the one honest help that fits."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.trouble and args.helper:
        setting = SETTINGS[args.setting]
        trouble = TROUBLES[args.trouble]
        helper = HELPERS[args.helper]
        if not valid_story(setting, trouble, helper):
            raise StoryError(explain_rejection(setting, trouble, helper))
    if args.setting and args.trouble and not trouble_fits_setting(SETTINGS[args.setting], TROUBLES[args.trouble]):
        helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
        raise StoryError(explain_rejection(SETTINGS[args.setting], TROUBLES[args.trouble], helper))
    if args.trouble and args.helper and args.setting is None:
        possible = [
            sid for sid, setting in SETTINGS.items()
            if valid_story(setting, TROUBLES[args.trouble], HELPERS[args.helper])
        ]
        if not possible:
            setting = next(iter(SETTINGS.values()))
            raise StoryError(explain_rejection(setting, TROUBLES[args.trouble], HELPERS[args.helper]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trouble_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    child_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        trouble=trouble_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.trouble not in TROUBLES or params.helper not in HELPERS:
        raise StoryError("(Invalid params: unknown setting, trouble, or helper key.)")
    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    helper = HELPERS[params.helper]
    if not valid_story(setting, trouble, helper):
        raise StoryError(explain_rejection(setting, trouble, helper))

    world = tell(
        setting=setting,
        trouble=trouble,
        helper=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, trouble, helper) combos:\n")
        for setting, trouble, helper in combos:
            print(f"  {setting:8} {trouble:8} {helper}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.trouble} at {p.setting} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
