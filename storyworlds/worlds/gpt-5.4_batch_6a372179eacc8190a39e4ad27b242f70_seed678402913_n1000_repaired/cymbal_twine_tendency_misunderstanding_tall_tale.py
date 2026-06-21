#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cymbal_twine_tendency_misunderstanding_tall_tale.py
==============================================================================

A standalone story world for a tall-tale misunderstanding story built around a
cymbal, a length of twine, and a child's tendency to act before asking one more
question.

Premise
-------
On a windy day in an exaggerated frontier place, a grown-up gives a simple bell
job. The wind and the hero's own tendency make the words come out wrong in the
hero's head, so the hero ties up a giant cymbal instead of helping with the
bell. The mistake turns the weather noisy enough for a tall tale, and then the
grown-up fixes the real problem the sensible way while teaching the hero to ask
what was meant.

The domain uses a small reasonableness gate:
- each task requires a particular kind of fix
- low-sense fixes are refused
- the inline ASP twin checks the same compatibility and outcome logic

Run it
------
python storyworlds/worlds/gpt-5.4/cymbal_twine_tendency_misunderstanding_tall_tale.py
python storyworlds/worlds/gpt-5.4/cymbal_twine_tendency_misunderstanding_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/cymbal_twine_tendency_misunderstanding_tall_tale.py --qa
python storyworlds/worlds/gpt-5.4/cymbal_twine_tendency_misunderstanding_tall_tale.py --verify
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    landmark: str
    wind_desc: str
    boast: str
    wind: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    ask: str
    purpose: str
    intended_object: str
    correct_action: str
    proper_result: str
    mistaken_plan: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tendency:
    id: str
    label: str
    style: str
    impulse: int
    line: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    handles: set[str]
    text: str
    qa_text: str
    ending_image: str
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


def _r_noise_spreads(world: World) -> list[str]:
    out: list[str] = []
    cymbal = world.entities.get("cymbal")
    sky = world.entities.get("sky")
    hero = world.entities.get("hero")
    elder = world.entities.get("elder")
    if cymbal is None or cymbal.meters["ringing"] < THRESHOLD:
        return out
    sig = ("noise_spreads", "cymbal")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if sky is not None:
        sky.meters["racket"] += 1
    if hero is not None:
        hero.memes["alarm"] += 1
    if elder is not None:
        elder.memes["hurry"] += 1
    out.append("__boom__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_spreads", tag="physical", apply=_r_noise_spreads),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if not bit.startswith("__"):
                world.say(bit)
    return produced


def compatible_fix(task: Task, fix: Fix) -> bool:
    return task.correct_action in fix.handles and fix.sense >= SENSE_MIN


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for task_id, task in TASKS.items():
            for fix_id, fix in FIXES.items():
                if compatible_fix(task, fix):
                    combos.append((setting_id, task_id, fix_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    setting = SETTINGS[params.setting]
    tendency = TENDENCIES[params.tendency]
    gust = setting.wind + tendency.impulse
    return "booming" if gust >= 5 else "caught_early"


def predict_racket(world: World, setting: Setting, tendency: Tendency) -> dict:
    sim = world.copy()
    cymbal = sim.get("cymbal")
    cymbal.meters["tied_high"] += 1
    gust = setting.wind + tendency.impulse
    if gust >= 5:
        cymbal.meters["ringing"] += 1
        propagate(sim, narrate=False)
    return {
        "rings": cymbal.meters["ringing"] >= THRESHOLD,
        "racket": sim.get("sky").meters["racket"],
    }


def tell(
    setting: Setting,
    task: Task,
    tendency: Tendency,
    fix: Fix,
    hero_name: str = "Cora",
    hero_type: str = "girl",
    elder_type: str = "aunt",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[tendency.label],
        attrs={"display_name": hero_name},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    bell = world.add(Entity(
        id="bell",
        type="bell",
        label="supper bell",
        phrase="the supper bell",
        tags={"bell"},
    ))
    cymbal = world.add(Entity(
        id="cymbal",
        type="cymbal",
        label="cymbal",
        phrase="a brass parade cymbal",
        tags={"cymbal"},
    ))
    twine = world.add(Entity(
        id="twine",
        type="twine",
        label="twine",
        phrase="a roll of twine",
        tags={"twine"},
    ))
    sky = world.add(Entity(
        id="sky",
        type="sky",
        label="sky",
        phrase="the windy sky",
        tags={"wind"},
    ))

    world.facts["display_name"] = hero_name
    world.facts["setting"] = setting
    world.facts["task"] = task
    world.facts["tendency_cfg"] = tendency
    world.facts["fix"] = fix

    hero.memes["confidence"] = 1
    hero.memes["tendency"] = float(tendency.impulse)
    elder.memes["trust"] = 1

    world.say(
        f"In {setting.place}, the wind was so lively that {setting.boast}. "
        f"{hero_name} had a {tendency.label} tendency: {tendency.style}."
    )
    world.say(
        f"{hero_name}'s {elder.label_word} kept the camp running from {setting.landmark}, "
        f"where the supper bell watched over the whole place."
    )

    world.para()
    world.say(
        f'One gusty afternoon, {elder.label_word} called, "{task.ask}"'
    )
    pred = predict_racket(world, setting, tendency)
    world.facts["predicted_rings"] = pred["rings"]
    world.facts["predicted_racket"] = pred["racket"]
    world.say(
        f"But the wind came whistling through the boards, and in {hero_name}'s ears "
        f"the word bell turned bright and brassy, almost like cymbal."
    )
    world.say(
        f"{hero_name} grabbed {twine.phrase} and spotted {cymbal.phrase} leaning by a wagon. "
        f"{tendency.line}"
    )

    world.para()
    cymbal.meters["tied_high"] += 1
    twine.meters["used"] += 1
    hero.memes["mistaken"] += 1
    world.say(
        f"Before anyone could blink twice, {hero_name} {task.mistaken_plan}. "
        f"The twine stretched from knot to knot until the cymbal hung high and proud."
    )

    booming = outcome_of(StoryParams(
        setting=setting.id,
        task=task.id,
        tendency=tendency.id,
        fix=fix.id,
        hero_name=hero_name,
        hero_gender=hero_type,
        elder=elder_type,
        seed=None,
    )) == "booming"

    if booming:
        cymbal.meters["ringing"] += 1
        propagate(world, narrate=False)
        hero.memes["alarm"] += 1
        world.say(
            f"Then {setting.wind_desc}. The cymbal boomed so hard that dust hopped off rails, "
            f"chickens forgot their own names, and even the clouds seemed to listen."
        )
        world.say(
            f"{hero_name} froze with both hands in the air, suddenly knowing that a mistake "
            f"could grow as fast as a tall-tale wind."
        )
    else:
        hero.memes["doubt"] += 1
        world.say(
            f"{hero_name} stepped back to admire the job, then blinked. "
            f"The supper bell still sat exactly where it had always sat."
        )
        world.say(
            f"That was when the mistake showed its own shadow: the cymbal was tied up nicely, "
            f"but the bell work had not been done at all."
        )

    world.para()
    bell.meters["fixed"] += 1
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    elder.memes["calm"] += 1
    world.say(
        f"{elder.label_word.capitalize()} came striding over, looked once at the cymbal, and "
        f"understood everything."
    )
    world.say(
        f"{elder.pronoun().capitalize()} smiled instead of scolding and said, "
        f'"I said bell, not cymbal. Your ears were racing faster than my words."'
    )
    world.say(
        fix.text.format(
            hero=hero_name,
            elder=elder.label_word,
            purpose=task.purpose,
            result=task.proper_result,
        )
    )
    world.say(
        f"{hero_name} helped with the right knots this time and learned that {tendency.lesson}"
    )

    world.para()
    world.say(
        f"By supper, {fix.ending_image.format(place=setting.place, landmark=setting.landmark)} "
        f"The old cymbal rested quietly by the wagon, the twine sat in a neat loop, and "
        f"{hero_name} asked one careful question before touching a single thing."
    )

    world.facts.update(
        hero=hero,
        elder=elder,
        bell=bell,
        cymbal=cymbal,
        twine=twine,
        sky=sky,
        booming=booming,
        outcome="booming" if booming else "caught_early",
        mistaken=True,
    )
    return world


KNOWLEDGE = {
    "cymbal": [(
        "What is a cymbal?",
        "A cymbal is a round metal instrument that makes a loud crashing sound when it is hit. It belongs in music, not in place of a bell rope."
    )],
    "twine": [(
        "What is twine?",
        "Twine is a thin, strong string used for tying things together. It is useful when you tie the right thing in the right place."
    )],
    "tendency": [(
        "What does tendency mean?",
        "A tendency is something you often do or the way you often act. A hasty tendency means someone may move before thinking things through."
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone hears or understands something the wrong way. Asking a question can fix it before the problem grows."
    )],
    "bell": [(
        "What is a bell for?",
        "A bell is used to ring a signal, like calling people to supper or warning them of something. It works best when it is set up the way people mean it to be."
    )],
    "wind": [(
        "Why can wind make noise problems bigger?",
        "Wind can shake, swing, or bang loose things. That means a small mistake can become a loud one very quickly."
    )],
}
KNOWLEDGE_ORDER = ["cymbal", "twine", "tendency", "misunderstanding", "bell", "wind"]


SETTINGS = {
    "mesa_ranch": Setting(
        id="mesa_ranch",
        place="a ranch on the red mesa",
        landmark="the cook shack porch",
        wind_desc="a mesa gust came racing down like it had been late all day",
        boast="hats had to introduce themselves twice before staying on heads",
        wind=3,
        tags={"wind"},
    ),
    "river_fair": Setting(
        id="river_fair",
        place="the river fairground",
        landmark="the pie tent platform",
        wind_desc="a river breeze skipped between tents and slapped every loose flap awake",
        boast="the bunting along the booths snapped like a line of tiny flags learning to dance",
        wind=2,
        tags={"wind"},
    ),
    "apple_hill": Setting(
        id="apple_hill",
        place="the orchard on Apple Hill",
        landmark="the cider shed steps",
        wind_desc="an apple-sweet breeze rolled downhill and stirred every leaf at once",
        boast="even the scarecrow leaned into the weather as if listening for news",
        wind=1,
        tags={"wind"},
    ),
}

TASKS = {
    "quiet_bell": Task(
        id="quiet_bell",
        ask="Take this twine and tie the supper bell's clapper still so the wind will quit clanging it.",
        purpose="keep the supper bell quiet until mealtime",
        intended_object="bell clapper",
        correct_action="tie_clapper",
        proper_result="the bell stayed still and quiet until somebody rang it on purpose",
        mistaken_plan="marched to the wagon and tied the giant cymbal high beside the porch, sure that the biggest ringing thing must be the right one",
        tags={"bell", "misunderstanding"},
    ),
    "lower_rope": Task(
        id="lower_rope",
        ask="Tie this twine onto the supper bell rope so the cooks can reach it from the porch.",
        purpose="make the bell easy for the cooks to ring",
        intended_object="bell rope",
        correct_action="lower_rope",
        proper_result="the bell rope hung low enough for the cooks to tug with one easy pull",
        mistaken_plan="looped the twine through the cymbal straps and hoisted the shiny thing up where everyone could see it, certain a grand signal needed a grander instrument",
        tags={"bell", "misunderstanding"},
    ),
}

TENDENCIES = {
    "hasty": Tendency(
        id="hasty",
        label="hasty",
        style="when an idea flashed, it usually reached her boots before it reached her thoughts",
        impulse=3,
        line='"If it shines and rings, that must be it," she said, and off she flew.',
        lesson="a quick pair of hands still needs a slower pair of ears.",
        tags={"tendency", "misunderstanding"},
    ),
    "boastful": Tendency(
        id="boastful",
        label="boastful",
        style="he always believed the biggest answer in sight must be the best one",
        impulse=2,
        line='"I will fix it so fine folks will hear supper from three counties away," he declared.',
        lesson="big talk sounds better after a small question.",
        tags={"tendency", "misunderstanding"},
    ),
    "dreamy": Tendency(
        id="dreamy",
        label="dreamy",
        style="their mind liked to skip ahead and paint the job larger than life",
        impulse=1,
        line='"A regular parade call to supper would be splendid," they murmured.',
        lesson="wonderful ideas work best after you check what was actually asked.",
        tags={"tendency", "misunderstanding"},
    ),
}

FIXES = {
    "tie_clapper": Fix(
        id="tie_clapper",
        sense=3,
        handles={"tie_clapper"},
        text="{elder} untied the cymbal, then looped the twine around the bell's clapper so {purpose}. In a breath, {result}.",
        qa_text="untied the mistaken cymbal and tied the bell's clapper still",
        ending_image="the supper bell waited quietly above {landmark}, ready for the real ring later",
        tags={"twine", "bell"},
    ),
    "lower_rope": Fix(
        id="lower_rope",
        sense=3,
        handles={"lower_rope"},
        text="{elder} loosened the cymbal, tied the twine onto the true bell rope, and let it down where a cook could grab it. Soon {result}.",
        qa_text="took down the cymbal and used the twine to lower the real bell rope",
        ending_image="the bell rope swayed neatly beside {landmark}, just low enough for a cook's hand",
        tags={"twine", "bell"},
    ),
    "shout_louder": Fix(
        id="shout_louder",
        sense=1,
        handles=set(),
        text="{elder} tried to out-yell the wind, which was not much of a fix at all.",
        qa_text="tried to shout over the noise",
        ending_image="everyone had sore throats and no proper bell setup",
        tags={"wind"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    task: str
    tendency: str
    fix: str
    hero_name: str
    hero_gender: str
    elder: str
    seed: Optional[int] = None


GIRL_NAMES = ["Cora", "Mabel", "June", "Lila", "Pearl", "Ada"]
BOY_NAMES = ["Beau", "Eli", "Hank", "Jesse", "Otis", "Cal"]
NEUTRAL_NAMES = ["Sunny", "Rowan", "Wren", "Sage"]
ELDERS = ["aunt", "uncle", "mother", "father"]


CURATED = [
    StoryParams(
        setting="mesa_ranch",
        task="quiet_bell",
        tendency="hasty",
        fix="tie_clapper",
        hero_name="Cora",
        hero_gender="girl",
        elder="aunt",
        seed=11,
    ),
    StoryParams(
        setting="river_fair",
        task="lower_rope",
        tendency="boastful",
        fix="lower_rope",
        hero_name="Beau",
        hero_gender="boy",
        elder="uncle",
        seed=22,
    ),
    StoryParams(
        setting="apple_hill",
        task="quiet_bell",
        tendency="dreamy",
        fix="tie_clapper",
        hero_name="Rowan",
        hero_gender="child",
        elder="mother",
        seed=33,
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero_name = world.facts["display_name"]
    setting = world.facts["setting"]
    task = world.facts["task"]
    tendency = world.facts["tendency_cfg"]
    outcome = world.facts["outcome"]
    closer = "a huge windy racket" if outcome == "booming" else "an almost-mistake caught in time"
    return [
        f'Write a child-facing tall tale that uses the words "cymbal", "twine", and "tendency".',
        f"Tell a tall-tale misunderstanding story set in {setting.place} where {hero_name}'s {tendency.label} tendency turns a bell job into a cymbal mix-up.",
        f"Write a story where a windy misunderstanding leads to {closer}, and a calm grown-up helps fix the real bell problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    task = world.facts["task"]
    setting = world.facts["setting"]
    tendency = world.facts["tendency_cfg"]
    fix = world.facts["fix"]
    hero_name = world.facts["display_name"]
    elder_word = elder.label_word
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, {hero.pronoun('possessive')} {elder_word}, and a bell job that went wrong in {setting.place}. The mistake began because {hero_name} heard the task the wrong way."
        ),
        (
            f"What was {hero_name} asked to do?",
            f"{elder_word.capitalize()} asked {hero.pronoun('object')} to help with the supper bell. The real job was to {task.correct_action.replace('_', ' ')} so {task.purpose}."
        ),
        (
            f"Why did {hero_name} use the cymbal?",
            f"{hero_name} misunderstood the words in the wind and thought the shiny cymbal must be the thing meant for the job. {hero.pronoun('Possessive') if False else hero.pronoun('possessive').capitalize()} {tendency.label} tendency made {hero.pronoun('object')} act before asking what {elder_word} meant."
        ),
    ]

    if outcome == "booming":
        qa.append((
            "What happened when the cymbal was tied up?",
            f"The wind caught it and made it boom across the whole place. The noise grew because the mistake was hanging high where the gusts could strike it."
        ))
    else:
        qa.append((
            "How did the mistake show up before the big noise started?",
            f"{hero_name} stepped back and saw that the cymbal had been tied up, but the supper bell was still unchanged. That made the misunderstanding clear before the wind could turn it into a giant racket."
        ))

    qa.append((
        f"How did {hero_name}'s {elder_word} fix the problem?",
        f"{elder_word.capitalize()} {fix.qa_text}. Then the bell could do the real job that had been asked for in the first place."
    ))
    qa.append((
        "What did the story teach?",
        f"It taught that a tendency to hurry, boast, or drift into big ideas can cause a misunderstanding. Asking one careful question can keep a small mistake from growing tall as a tall tale."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"cymbal", "twine", "tendency", "misunderstanding", "bell", "wind"}
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_fix_rejection(fix_id: str) -> str:
    fix = FIXES[fix_id]
    if fix.sense < SENSE_MIN:
        better = ", ".join(sorted(f.id for f in sensible_fixes()))
        return (
            f"(Refusing fix '{fix_id}': it scores too low on common sense "
            f"(sense={fix.sense} < {SENSE_MIN}). Try one of these sensible fixes: {better}.)"
        )
    return f"(Refusing fix '{fix_id}': it does not actually solve the requested bell task.)"


def explain_combo_rejection(task: Task, fix: Fix) -> str:
    return (
        f"(No story: the task needs a fix that can {task.correct_action.replace('_', ' ')}, "
        f"but '{fix.id}' does not do that. The grown-up must solve the real bell problem, not a different one.)"
    )


ASP_RULES = r"""
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
compatible(Task, Fix) :- task(Task), fix(Fix), needs(Task, A), handles(Fix, A), sensible_fix(Fix).
valid(Setting, Task, Fix) :- setting(Setting), compatible(Task, Fix).

booming :- chosen_setting(S), wind(S, W), chosen_tendency(T), impulse(T, I), W + I >= 5.
caught_early :- chosen_setting(S), wind(S, W), chosen_tendency(T), impulse(T, I), W + I < 5.

outcome(booming) :- booming.
outcome(caught_early) :- caught_early.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("wind", setting_id, setting.wind))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("needs", task_id, task.correct_action))
    for tendency_id, tendency in TENDENCIES.items():
        lines.append(asp.fact("tendency", tendency_id))
        lines.append(asp.fact("impulse", tendency_id, tendency.impulse))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for handle in sorted(fix.handles):
            lines.append(asp.fact("handles", fix_id, handle))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_tendency", params.tendency),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale misunderstanding world: a cymbal, some twine, and a child's tendency to hear the wrong thing in the wind."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tendency", choices=TENDENCIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy", "child"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
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
    if args.fix:
        if FIXES[args.fix].sense < SENSE_MIN:
            raise StoryError(explain_fix_rejection(args.fix))
    if args.task and args.fix:
        task = TASKS[args.task]
        fix = FIXES[args.fix]
        if not compatible_fix(task, fix):
            raise StoryError(explain_combo_rejection(task, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.task is None or combo[1] == args.task)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, task_id, fix_id = rng.choice(sorted(combos))
    tendency_id = args.tendency or rng.choice(sorted(TENDENCIES))
    gender = args.gender or rng.choice(["girl", "boy", "child"])

    if args.name:
        name = args.name
    elif gender == "girl":
        name = rng.choice(GIRL_NAMES)
    elif gender == "boy":
        name = rng.choice(BOY_NAMES)
    else:
        name = rng.choice(NEUTRAL_NAMES)

    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(
        setting=setting_id,
        task=task_id,
        tendency=tendency_id,
        fix=fix_id,
        hero_name=name,
        hero_gender=gender,
        elder=elder,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        task = TASKS[params.task]
        tendency = TENDENCIES[params.tendency]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not compatible_fix(task, fix):
        raise StoryError(explain_combo_rejection(task, fix))

    world = tell(
        setting=setting,
        task=task,
        tendency=tendency,
        fix=fix,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        elder_type=params.elder,
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
        print(f"{len(combos)} compatible (setting, task, fix) combos:\n")
        for setting, task, fix in combos:
            print(f"  {setting:11} {task:11} {fix}")
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
            header = f"### {p.hero_name}: {p.tendency} at {p.setting} ({p.task}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
