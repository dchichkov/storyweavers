#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/doofus_twist_tall_tale.py
====================================================

A standalone storyworld for a tiny Tall Tale domain with a clear twist:
someone laughs and says "doofus" when a child hero brings a tiny helper to face
a giant town-sized problem, but the smallest helper turns out to be exactly the
right one.

The world model is constraint-checked:

- each setting only affords some giant troubles
- each trouble has one hidden weak spot
- only a helper with the matching knack can plausibly solve it
- the delay before the helper acts changes whether the town is saved neatly or
  only after a comic bit of damage

Run it
------
python storyworlds/worlds/gpt-5.4/doofus_twist_tall_tale.py
python storyworlds/worlds/gpt-5.4/doofus_twist_tall_tale.py --setting prairie --trouble runaway_wagon --helper ferret
python storyworlds/worlds/gpt-5.4/doofus_twist_tall_tale.py --trouble floodgate --helper mouse
python storyworlds/worlds/gpt-5.4/doofus_twist_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/doofus_twist_tall_tale.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    boasts: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    start: str
    threat: str
    weak_spot: str
    need: str
    risk: int
    saved: str
    messy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    type: str
    knack: str
    power: int
    entrance: str
    action: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_panic(world: World) -> list[str]:
    trouble = world.get("trouble")
    if trouble.meters["raging"] < THRESHOLD:
        return []
    sig = ("panic",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("town").memes["worry"] += 1
    world.get("hero").memes["resolve"] += 1
    world.get("helper").memes["bravery"] += 1
    return []


def _r_fix(world: World) -> list[str]:
    trouble = world.get("trouble")
    helper = world.get("helper")
    if trouble.meters["raging"] < THRESHOLD or helper.meters["at_weak_spot"] < THRESHOLD:
        return []
    sig = ("fix",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trouble.meters["raging"] = 0.0
    trouble.meters["stopped"] += 1
    world.get("town").memes["relief"] += 1
    world.get("hero").memes["pride"] += 1
    world.get("teaser").memes["shame"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="panic", tag="social", apply=_r_panic),
    Rule(name="fix", tag="physical", apply=_r_fix),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="a prairie town where the grass was said to comb itself",
        sky="The sky looked so wide it could have worn ten sunsets at once.",
        boasts="Folks there bragged that even the shadows stretched their legs before breakfast.",
        affords={"runaway_wagon", "tangled_windmill"},
        tags={"prairie"},
    ),
    "riverbend": Setting(
        id="riverbend",
        place="a river town curled around a silver bend",
        sky="The water flashed so bright it looked as if the sun had dropped a pocketful of coins.",
        boasts="People said the river could rinse a barn clean just by blinking at it.",
        affords={"floodgate", "runaway_wagon"},
        tags={"river"},
    ),
    "mesa": Setting(
        id="mesa",
        place="a red-rock mesa town perched above the wind",
        sky="The cliffs stood so tall they seemed to keep spare clouds on their shoulders.",
        boasts="The old-timers swore the wind there could whistle two tunes at once.",
        affords={"tangled_windmill", "floodgate"},
        tags={"mesa", "wind"},
    ),
}

TROUBLES = {
    "runaway_wagon": Trouble(
        id="runaway_wagon",
        label="runaway wagon",
        start="a runaway wagon came tearing down the main road with flour barrels bouncing in back",
        threat="If nobody stopped it, it would smash the town well flat as a pancake.",
        weak_spot="the jammed brake box under the wagon seat",
        need="squeeze",
        risk=2,
        saved="The wagon shuddered, groaned, and stopped with its front wheel kissing the hitching post instead of the town well.",
        messy="The wagon did stop, but not before it burst two flour barrels and turned the square white as winter.",
        tags={"wagon", "brake"},
    ),
    "floodgate": Trouble(
        id="floodgate",
        label="floodgate",
        start="the river floodgate stuck fast while the water rose like it meant to climb the moon",
        threat="If the gate stayed shut, the water would leap the bank and swim right through the bakery.",
        weak_spot="the little spill pipe behind the rusted gate wheel",
        need="swim",
        risk=2,
        saved="The gate coughed, lurched, and swung open, and the river went racing where it belonged.",
        messy="The gate finally opened, but not before the river sloshed over the bank and gave the bakery steps a soaking.",
        tags={"river", "gate"},
    ),
    "tangled_windmill": Trouble(
        id="tangled_windmill",
        label="tangled windmill",
        start="the town windmill tied its own sail ropes in a knot and quit turning in the hottest part of the day",
        threat="If it stayed stuck, the town pump would stop and every bucket in town would turn lonely and dry.",
        weak_spot="the hard knot high in the sail rope",
        need="gnaw",
        risk=2,
        saved="The knot snapped loose, the sails whooshed around again, and cool water came singing up the pump pipe.",
        messy="The ropes did come free, but not before the pump wheezed dry and the townsfolk had to share the last bucket of water for one sticky hour.",
        tags={"windmill", "water"},
    ),
}

HELPERS = {
    "ferret": HelperCfg(
        id="ferret",
        label="ferret",
        phrase="a skinny ferret named Flick",
        type="animal",
        knack="squeeze",
        power=3,
        entrance="Flick was so slim he could slip through a keyhole sideways.",
        action="darted into the brake box, kicked the catch loose with one sharp wiggle, and vanished out the other side before the dust could count to three",
        reveal="What looked like a silly little pet was exactly the size the brake box needed.",
        tags={"ferret", "small_helper"},
    ),
    "duck": HelperCfg(
        id="duck",
        label="duck",
        phrase="a yellow-billed duck named Paddle",
        type="animal",
        knack="swim",
        power=3,
        entrance="Paddle could dive through muddy water as neatly as a needle through cloth.",
        action="splashed into the spill pipe, paddled under the rusted gate wheel, and nudged the hidden latch free with a stout bill",
        reveal="The pipe behind the gate was far too narrow for any person, but just right for a duck that loved a current.",
        tags={"duck", "small_helper"},
    ),
    "mouse": HelperCfg(
        id="mouse",
        label="mouse",
        phrase="a field mouse named Nib",
        type="animal",
        knack="gnaw",
        power=3,
        entrance="Nib had teeth so quick folks joked he could trim a broom while it was still sweeping.",
        action="scrambled up the tower rope, reached the knot, and nibbled the stubborn strands apart with bright little teeth",
        reveal="No grown-up hand could reach the knot safely, but tiny teeth and tiny feet could.",
        tags={"mouse", "small_helper"},
    ),
}

GIRL_NAMES = ["Mae", "June", "Lula", "Wren", "Tess", "Molly", "Nell"]
BOY_NAMES = ["Bo", "Eli", "Hank", "Jude", "Otis", "Cal", "Finn"]
TEASERS = ["Mayor Bristle", "Old Chet", "Aunt Sable", "Sheriff Dot", "Miss Kettle"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    helper: str
    hero_name: str
    hero_gender: str
    teaser_name: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="prairie",
        trouble="runaway_wagon",
        helper="ferret",
        hero_name="Mae",
        hero_gender="girl",
        teaser_name="Mayor Bristle",
        delay=0,
    ),
    StoryParams(
        setting="riverbend",
        trouble="floodgate",
        helper="duck",
        hero_name="Bo",
        hero_gender="boy",
        teaser_name="Old Chet",
        delay=1,
    ),
    StoryParams(
        setting="mesa",
        trouble="tangled_windmill",
        helper="mouse",
        hero_name="June",
        hero_gender="girl",
        teaser_name="Sheriff Dot",
        delay=0,
    ),
]


def trouble_match(helper: HelperCfg, trouble: Trouble) -> bool:
    return helper.knack == trouble.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid in sorted(setting.affords):
            trouble = TROUBLES[tid]
            for hid, helper in HELPERS.items():
                if trouble_match(helper, trouble):
                    combos.append((sid, tid, hid))
    return combos


def severity(trouble: Trouble, delay: int) -> int:
    return trouble.risk + delay


def neatly_saved(helper: HelperCfg, trouble: Trouble, delay: int) -> bool:
    return helper.power >= severity(trouble, delay)


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    trouble = TROUBLES[params.trouble]
    return "neat_save" if neatly_saved(helper, trouble, params.delay) else "messy_save"


def explain_rejection(setting_id: str, trouble_id: str, helper_id: str) -> str:
    setting = SETTINGS[setting_id]
    trouble = TROUBLES[trouble_id]
    helper = HELPERS[helper_id]
    if trouble_id not in setting.affords:
        return (
            f"(No story: {setting.place} does not host the {trouble.label} problem. "
            f"Pick a trouble that fits that place.)"
        )
    return (
        f"(No story: {helper.phrase} can {helper.knack}, but the {trouble.label} needs "
        f"someone who can {trouble.need} at {trouble.weak_spot}. The twist only works "
        f"when the tiny helper truly fits the hidden weak spot.)"
    )


def predict_fix(world: World) -> dict:
    sim = world.copy()
    helper = sim.get("helper")
    helper.meters["at_weak_spot"] += 1
    propagate(sim, narrate=False)
    trouble = sim.get("trouble")
    return {
        "stopped": trouble.meters["stopped"] >= THRESHOLD,
        "town_relief": sim.get("town").memes["relief"],
    }


def _do_trouble(world: World) -> None:
    trouble = world.get("trouble")
    trouble.meters["raging"] += 1
    propagate(world, narrate=False)


def _do_helper(world: World) -> None:
    helper = world.get("helper")
    helper.meters["at_weak_spot"] += 1
    propagate(world, narrate=False)


def open_tale(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In {setting.place}, {hero.id} was the sort of child who could hear a plan hiding inside a problem."
    )
    world.say(setting.sky)
    world.say(setting.boasts)


def trouble_arrives(world: World, trouble: Trouble) -> None:
    _do_trouble(world)
    world.say(
        f"One noon, {trouble.start}. {trouble.threat}"
    )


def crowd_fails(world: World, trouble: Trouble) -> None:
    world.say(
        "The grown-ups shoved, hollered, and waved their hats, but all that noise did not help one speck."
    )
    if trouble.id == "runaway_wagon":
        world.say(
            "Two blacksmiths yanked on the reins, yet the wagon kept charging as if it had borrowed thunder for hooves."
        )
    elif trouble.id == "floodgate":
        world.say(
            "Three farmers leaned on the gate wheel together, yet the rust only groaned and held tighter."
        )
    else:
        world.say(
            "A ladder went up, then another, but the knot sat higher than both and meaner than either."
        )


def hero_arrives(world: World, hero: Entity, helper: Entity, helper_cfg: HelperCfg) -> None:
    hero.memes["resolve"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"Then {hero.id} came running with {helper_cfg.phrase} tucked close. {helper_cfg.entrance}"
    )


def tease(world: World, teaser: Entity, hero: Entity, helper_cfg: HelperCfg, trouble: Trouble) -> None:
    teaser.memes["scorn"] += 1
    pred = predict_fix(world)
    world.facts["predicted_stop"] = pred["stopped"]
    world.say(
        f'"{hero.id}, you doofus," {teaser.id} barked. "That {helper_cfg.label} cannot stop a whole {trouble.label}!"'
    )


def explain_plan(world: World, hero: Entity, helper_cfg: HelperCfg, trouble: Trouble) -> None:
    world.say(
        f'But {hero.id} only pointed at {trouble.weak_spot} and said, '
        f'"Big hands cannot reach it. {helper_cfg.phrase} can."'
    )


def delay_beat(world: World, trouble: Trouble, delay: int) -> None:
    if delay <= 0:
        return
    if trouble.id == "runaway_wagon":
        world.say(
            "For a breath too long, flour barrels bounced like white moons in the wagon bed."
        )
    elif trouble.id == "floodgate":
        world.say(
            "For a breath too long, the river lipped over the bank and slapped the stones."
        )
    else:
        world.say(
            "For a breath too long, the windmill stood still and the pump answered with nothing but a dry cough."
        )


def helper_acts(world: World, helper_cfg: HelperCfg) -> None:
    _do_helper(world)
    world.say(
        f"{helper_cfg.phrase.capitalize()} {helper_cfg.action}."
    )


def resolution(world: World, trouble: Trouble, neat: bool) -> None:
    if neat:
        world.say(trouble.saved)
    else:
        world.say(trouble.messy)


def twist_ending(world: World, hero: Entity, teaser: Entity, helper_cfg: HelperCfg) -> None:
    teaser.memes["respect"] += 1
    world.say(
        f"{teaser.id} took off the hat that had done all the laughing. {helper_cfg.reveal}"
    )
    world.say(
        f'At last {teaser.pronoun()} said, "The doofus was me."'
    )
    world.say(
        f"From then on, whenever a job looked too big, the town remembered {hero.id} and {helper_cfg.phrase}, and looked twice for the small smart answer hiding inside it."
    )


def tell(
    setting: Setting,
    trouble_cfg: Trouble,
    helper_cfg: HelperCfg,
    hero_name: str,
    hero_gender: str,
    teaser_name: str,
    delay: int,
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    teaser_type = "man"
    if teaser_name.startswith("Aunt") or teaser_name.startswith("Miss") or teaser_name.startswith("Sheriff Dot"):
        teaser_type = "woman"
    teaser = world.add(Entity(id=teaser_name, kind="character", type=teaser_type, role="teaser", label=teaser_name))
    helper = world.add(
        Entity(
            id="helper",
            kind="thing",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            tags=set(helper_cfg.tags),
        )
    )
    trouble = world.add(
        Entity(
            id="trouble",
            kind="thing",
            type="trouble",
            role="trouble",
            label=trouble_cfg.label,
            tags=set(trouble_cfg.tags),
        )
    )
    town = world.add(Entity(id="town", kind="thing", type="town", role="town", label="the town"))

    open_tale(world, hero, setting)

    world.para()
    trouble_arrives(world, trouble_cfg)
    crowd_fails(world, trouble_cfg)

    world.para()
    hero_arrives(world, hero, helper, helper_cfg)
    tease(world, teaser, hero, helper_cfg, trouble_cfg)
    explain_plan(world, hero, helper_cfg, trouble_cfg)
    delay_beat(world, trouble_cfg, delay)

    world.para()
    helper_acts(world, helper_cfg)
    neat = neatly_saved(helper_cfg, trouble_cfg, delay)
    resolution(world, trouble_cfg, neat)

    world.para()
    twist_ending(world, hero, teaser, helper_cfg)

    world.facts.update(
        hero=hero,
        teaser=teaser,
        helper=helper,
        helper_cfg=helper_cfg,
        trouble=trouble,
        trouble_cfg=trouble_cfg,
        town=town,
        setting=setting,
        delay=delay,
        neat=neat,
        outcome="neat_save" if neat else "messy_save",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper_cfg"]
    trouble = f["trouble_cfg"]
    setting = f["setting"]
    return [
        'Write a short Tall Tale for a 3-to-5-year-old that includes the word "doofus" and ends with a twist.',
        f"Tell a tall-tale story set in {setting.place} where a child named {hero.id} brings {helper.phrase} to face a {trouble.label}, and everyone laughs before the tiny helper saves the day.",
        f'Write a twist story where the crowd thinks the hero is a doofus for trusting a small helper, but the helper is exactly right for {trouble.weak_spot}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    teaser = f["teaser"]
    helper = f["helper_cfg"]
    trouble = f["trouble_cfg"]
    setting = f["setting"]
    neat = f["neat"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child in {setting.place}, and {helper.phrase}. It also includes {teaser.id}, who laughs too soon.",
        ),
        (
            f"What big problem hit the town?",
            f"The town was in trouble because {trouble.start}. {trouble.threat}",
        ),
        (
            f"Why did {teaser.id} call {hero.id} a doofus?",
            f"{teaser.id} looked at the tiny helper and thought something so small could never stop such a huge problem. The laugh came from judging by size instead of by what the helper could really do.",
        ),
        (
            f"How did {hero.id} know the little helper could work?",
            f"{hero.id} noticed the hidden weak spot: {trouble.weak_spot}. Big people could not reach it, but {helper.phrase} could because {helper.reveal.lower()}",
        ),
    ]
    if neat:
        qa.append(
            (
                "How did the story end?",
                f"The helper reached the weak spot in time and the town was saved neatly. {trouble.saved}",
            )
        )
    else:
        qa.append(
            (
                "Did the helper still save the day even though there was a mess?",
                f"Yes. The helper fixed the hidden weak spot, but the delay let a little damage happen first. {trouble.messy}",
            )
        )
    qa.append(
        (
            "What was the twist in the story?",
            f"The twist is that the person who said 'doofus' was the one who had things backward. The tiny helper everyone laughed at turned out to be the smartest answer of all.",
        )
    )
    return qa


KNOWLEDGE = {
    "ferret": [
        (
            "Why can a ferret fit into small places?",
            "A ferret has a long, slim body, so it can squeeze through narrow spaces that people cannot reach.",
        )
    ],
    "duck": [
        (
            "Why is a duck good in water?",
            "A duck has webbed feet and a body built for paddling, so it can swim strongly through water.",
        )
    ],
    "mouse": [
        (
            "Why can a mouse chew through tough things?",
            "A mouse has sharp front teeth that keep growing, so it is very good at nibbling and gnawing.",
        )
    ],
    "wagon": [
        (
            "What does a brake do on a wagon?",
            "A brake helps slow or stop the wheels. If the brake gets stuck, a wagon can roll where nobody wants it to go.",
        )
    ],
    "gate": [
        (
            "What is a floodgate for?",
            "A floodgate helps control where water goes. Opening or closing it can keep water away from places that should stay dry.",
        )
    ],
    "windmill": [
        (
            "What does a windmill do?",
            "A windmill uses the wind to turn big sails or blades. That turning can help pump water or do work.",
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise turn near the end. It makes you see the story in a new way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ferret", "duck", "mouse", "wagon", "gate", "windmill", "twist"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["helper_cfg"].tags)
    tags |= set(f["trouble_cfg"].tags)
    tags.add("twist")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
fits(H, T) :- helper(H), trouble(T), knack(H, K), need(T, K).
valid(S, T, H) :- setting(S), trouble(T), helper(H), affords(S, T), fits(H, T).

% --- outcome model ---------------------------------------------------------
severity(V) :- chosen_trouble(T), risk(T, R), delay(D), V = R + D.
neat_save :- chosen_helper(H), power(H, P), severity(V), P >= V.
outcome(neat_save) :- neat_save.
outcome(messy_save) :- not neat_save.
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
        lines.append(asp.fact("need", tid, trouble.need))
        lines.append(asp.fact("risk", tid, trouble.risk))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("knack", hid, helper.knack))
        lines.append(asp.fact("power", hid, helper.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_trouble", params.trouble),
            asp.fact("chosen_helper", params.helper),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for seed in range(20):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcome cases differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a child, a tiny helper, a giant problem, and a twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--teaser-name", choices=TEASERS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late the helper acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.trouble and args.helper:
        if (args.setting, args.trouble, args.helper) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.setting, args.trouble, args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trouble_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    teaser_name = args.teaser_name or rng.choice(TEASERS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])

    return StoryParams(
        setting=setting_id,
        trouble=trouble_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        teaser_name=teaser_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    if (params.setting, params.trouble, params.helper) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.setting, params.trouble, params.helper))

    world = tell(
        setting=SETTINGS[params.setting],
        trouble_cfg=TROUBLES[params.trouble],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        teaser_name=params.teaser_name,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trouble, helper) combos:\n")
        for setting_id, trouble_id, helper_id in combos:
            print(f"  {setting_id:10} {trouble_id:17} {helper_id}")
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
            header = f"### {p.hero_name}: {p.trouble} in {p.setting} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
