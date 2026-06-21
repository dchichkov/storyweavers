#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/conk_antler_dialogue_moral_value_kindness_bedtime.py
================================================================================

A standalone bedtime-story world about a child finding a hurt forest animal and
choosing kindness over keeping a pretty thing.

Tiny domain shape:
- A child walks outside near bedtime and hears a soft conk in the bushes.
- A young deer has an antler caught or has bumped itself and is frightened.
- The child can act kindly with help from a grown-up using a gentle aid.
- The story resolves with the animal safe and the child carrying kindness into bed.

Run it
------
    python storyworlds/worlds/gpt-5.4/conk_antler_dialogue_moral_value_kindness_bedtime.py
    python storyworlds/worlds/gpt-5.4/conk_antler_dialogue_moral_value_kindness_bedtime.py --animal fawn --problem basket
    python storyworlds/worlds/gpt-5.4/conk_antler_dialogue_moral_value_kindness_bedtime.py --wish keep_antler
    python storyworlds/worlds/gpt-5.4/conk_antler_dialogue_moral_value_kindness_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/conk_antler_dialogue_moral_value_kindness_bedtime.py --verify
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

# Make shared result containers importable when this script is run directly.
_THIS = os.path.abspath(__file__)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_THIS))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
KINDNESS_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | animal | thing | place
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    sky: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalCfg:
    id: str
    label: str
    phrase: str
    baby_name: str
    coat: str
    antler_kind: str
    cry: str
    tracks: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemCfg:
    id: str
    label: str
    snag_text: str
    conk_text: str
    risk_text: str
    help_text: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class AidCfg:
    id: str
    label: str
    phrase: str
    use_text: str
    comfort_text: str
    power: int
    kindness: int
    tags: set[str] = field(default_factory=set)


@dataclass
class WishCfg:
    id: str
    want_text: str
    lesson_text: str
    selfish: bool
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


def _r_animal_fear(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    if animal is None:
        return out
    if animal.meters["stuck"] < THRESHOLD and animal.meters["hurt"] < THRESHOLD:
        return out
    sig = ("fear", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.memes["fear"] += 1
    if "child" in world.entities:
        world.get("child").memes["concern"] += 1
    out.append("__fear__")
    return out


def _r_kindness_calms(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    child = world.entities.get("child")
    if animal is None or child is None:
        return out
    if child.memes["kindness"] < THRESHOLD:
        return out
    sig = ("calm", animal.id, int(child.memes["kindness"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.memes["calm"] += 1
    if animal.memes["fear"] >= THRESHOLD:
        animal.memes["fear"] -= 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="animal_fear", tag="emotion", apply=_r_animal_fear),
    Rule(name="kindness_calms", tag="emotion", apply=_r_kindness_calms),
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
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def problem_real(animal: AnimalCfg, problem: ProblemCfg) -> bool:
    return animal.antler_kind != "no antlers yet" or problem.id == "bump"


def aid_works(aid: AidCfg, problem: ProblemCfg) -> bool:
    return aid.power >= problem.severity and aid.kindness >= KINDNESS_MIN


def sensible_wish(wish: WishCfg) -> bool:
    return not wish.selfish


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for animal_id, animal in ANIMALS.items():
            for problem_id, problem in PROBLEMS.items():
                if not problem_real(animal, problem):
                    continue
                for aid_id, aid in AIDS.items():
                    if aid_works(aid, problem):
                        combos.append((setting_id, animal_id, problem_id, aid_id))
    return combos


def explain_problem(animal: AnimalCfg, problem: ProblemCfg) -> str:
    if not problem_real(animal, problem):
        return (
            f"(No story: a {animal.baby_name} with {animal.antler_kind} cannot plausibly "
            f"have the problem '{problem.id}'. Pick another animal or a simpler bump.)"
        )
    return "(No story: the chosen animal and problem do not fit together.)"


def explain_aid(aid_id: str) -> str:
    aid = AIDS[aid_id]
    better = ", ".join(sorted(a.id for a in sensible_aids()))
    return (
        f"(Refusing aid '{aid_id}': it is not gentle or strong enough for this world "
        f"(kindness={aid.kindness}, power={aid.power}). Try: {better}.)"
    )


def sensible_aids() -> list[AidCfg]:
    return [aid for aid in AIDS.values() if aid.kindness >= KINDNESS_MIN]


def predict_help(world: World, problem: ProblemCfg, aid: AidCfg) -> dict:
    sim = world.copy()
    animal = sim.get("animal")
    child = sim.get("child")
    child.memes["kindness"] += aid.kindness
    if problem.id == "bump":
        animal.meters["hurt"] = max(0.0, animal.meters["hurt"] - aid.power)
    else:
        animal.meters["stuck"] = max(0.0, animal.meters["stuck"] - aid.power)
    propagate(sim, narrate=False)
    return {
        "freed": animal.meters["stuck"] < THRESHOLD and animal.meters["hurt"] < THRESHOLD,
        "calm": animal.memes["calm"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    world.say(
        f"It was almost bedtime when {child.id} walked with {child.pronoun('possessive')} "
        f"{parent.label_word} by {setting.place}. {setting.sky} and {setting.sound}."
    )
    world.say(
        f"{child.id} stayed close because the evening felt soft and sleepy, the kind of time "
        f"when even tiny sounds seemed important."
    )


def hear_conk(world: World, child: Entity, problem: ProblemCfg) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then there came a little conk from the bushes. It was not a loud sound, "
        f"just enough to make {child.id} stop and listen."
    )
    world.say(problem.conk_text)


def reveal_animal(world: World, child: Entity, animal: Entity, animal_cfg: AnimalCfg, problem: ProblemCfg) -> None:
    animal.meters["seen"] += 1
    if problem.id == "bump":
        animal.meters["hurt"] += 1
    else:
        animal.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Behind the leaves stood {animal_cfg.phrase}. {animal_cfg.coat} and "
        f"{problem.snag_text}"
    )
    world.say(
        f'"Oh," whispered {child.id}. "{animal_cfg.cry}"'
    )


def selfish_wish(world: World, child: Entity, wish: WishCfg, animal_cfg: AnimalCfg) -> None:
    child.memes["wanting"] += 1
    world.say(
        f"{child.id} looked at the {animal_cfg.antler_kind} and {wish.want_text}"
    )


def parent_guides(world: World, parent: Entity, child: Entity, problem: ProblemCfg, aid: AidCfg, animal_cfg: AnimalCfg) -> None:
    pred = predict_help(world, problem, aid)
    world.facts["predicted_freed"] = pred["freed"]
    world.facts["predicted_calm"] = pred["calm"]
    world.say(
        f'"We will not frighten {animal_cfg.pronoun("object") if hasattr(animal_cfg, "pronoun") else "it"}," '
        f"{parent.label_word} said softly. "
        f'"If we move gently and use {aid.phrase}, we may help."'
    )


def choose_kindness(world: World, child: Entity, wish: WishCfg, animal_cfg: AnimalCfg) -> None:
    child.memes["kindness"] += 1
    if wish.selfish:
        world.say(
            f'{child.id} took a slow breath. "I do not need to keep an antler," '
            f'{child.pronoun()} said. "{wish.lesson_text}"'
        )
    else:
        world.say(
            f'"{wish.lesson_text}" {child.id} said, already reaching out with careful hands.'
        )


def help_animal(world: World, child: Entity, parent: Entity, animal: Entity,
                animal_cfg: AnimalCfg, problem: ProblemCfg, aid: AidCfg) -> None:
    child.memes["kindness"] += aid.kindness
    world.say(
        f"{parent.label_word.capitalize()} opened {aid.phrase}, and {aid.use_text}"
    )
    world.say(aid.comfort_text.replace("{child}", child.id).replace("{animal}", animal_cfg.label))
    if problem.id == "bump":
        animal.meters["hurt"] = max(0.0, animal.meters["hurt"] - aid.power)
    else:
        animal.meters["stuck"] = max(0.0, animal.meters["stuck"] - aid.power)
    propagate(world, narrate=False)


def release(world: World, animal: Entity, animal_cfg: AnimalCfg, problem: ProblemCfg) -> None:
    freed = animal.meters["stuck"] < THRESHOLD and animal.meters["hurt"] < THRESHOLD
    animal.memes["relief"] += 1
    if freed:
        world.say(
            f"Soon the trouble was over. {problem.help_text} and the little {animal_cfg.baby_name} "
            f"stood still for one blink, as if listening to the quiet again."
        )
        world.say(
            f"Then it gave a small shake of its head, its {animal_cfg.antler_kind} clear at last, "
            f"and trotted back toward the dark trees."
        )
    else:
        world.say(
            f"The poor little creature was not fully free yet, so {animal_cfg.label}'s family stayed near "
            f"while {animal.pronoun()} rested. The gentleness still mattered, because being calm kept "
            f"the trouble from growing worse."
        )


def bedtime_close(world: World, child: Entity, parent: Entity, animal_cfg: AnimalCfg, wish: WishCfg) -> None:
    child.memes["lesson"] += 1
    child.memes["peace"] += 1
    world.say(
        f'On the way home, {child.id} slipped {child.pronoun("possessive")} hand into '
        f'{child.pronoun("possessive")} {parent.label_word}\'s and said, "Kindness feels warmer than keeping things."'
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled. "Yes," {parent.pronoun()} said. '
        f'"That is why a gentle heart makes the best bedtime story."'
    )
    world.say(
        f"That night, tucked under the blankets, {child.id} remembered the soft conk in the bushes, "
        f"the shy {animal_cfg.baby_name}, and the antler left where it belonged. Sleep came quietly, "
        f"and kindness stayed."
    )


def tell(setting: Setting, animal_cfg: AnimalCfg, problem: ProblemCfg, aid: AidCfg, wish: WishCfg,
         child_name: str = "Mila", child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    child.id = child_name
    world.entities[child_name] = world.entities.pop("child")
    child = world.get(child_name)
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    animal = world.add(Entity(id="animal", kind="animal", type=animal_cfg.id, label=animal_cfg.label, phrase=animal_cfg.phrase))
    world.add(Entity(id="path", kind="place", type="path", label=setting.place))

    introduce(world, child, parent, setting)
    world.para()
    hear_conk(world, child, problem)
    reveal_animal(world, child, animal, animal_cfg, problem)

    world.para()
    selfish_wish(world, child, wish, animal_cfg)
    parent_guides(world, parent, child, problem, aid, animal_cfg)
    choose_kindness(world, child, wish, animal_cfg)

    world.para()
    help_animal(world, child, parent, animal, animal_cfg, problem, aid)
    release(world, animal, animal_cfg, problem)

    world.para()
    bedtime_close(world, child, parent, animal_cfg, wish)

    outcome = "helped" if animal.meters["stuck"] < THRESHOLD and animal.meters["hurt"] < THRESHOLD else "comforted"
    world.facts.update(
        child=child,
        parent=parent,
        animal=animal,
        setting=setting,
        animal_cfg=animal_cfg,
        problem=problem,
        aid=aid,
        wish=wish,
        outcome=outcome,
        freed=outcome == "helped",
        lesson=child.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "pine_path": Setting(
        id="pine_path",
        place="the pine path behind the cottage",
        sky="The sky was turning dusky blue",
        sound="the branches whispered together above them",
        tags={"forest", "bedtime"},
    ),
    "moon_garden": Setting(
        id="moon_garden",
        place="the moonlit garden gate",
        sky="A round moon was climbing over the hedges",
        sound="crickets stitched a tiny song through the air",
        tags={"garden", "bedtime"},
    ),
    "brook_bank": Setting(
        id="brook_bank",
        place="the brook bank near the willow tree",
        sky="Silver evening light lay over the water",
        sound="the brook made a hush-hush sound over the stones",
        tags={"brook", "bedtime"},
    ),
}

ANIMALS = {
    "fawn": AnimalCfg(
        id="fawn",
        label="fawn",
        phrase="a young deer",
        baby_name="fawn",
        coat="Its spotted coat trembled in the dim light",
        antler_kind="tiny antler buds",
        cry="A little deer!",
        tracks="small hoofprints in the mud",
        tags={"deer", "antler"},
    ),
    "young_deer": AnimalCfg(
        id="young_deer",
        label="young deer",
        phrase="a small young deer",
        baby_name="young deer",
        coat="Its brown coat twitched with worry",
        antler_kind="one small antler",
        cry="It is only a young deer.",
        tracks="narrow tracks between fern leaves",
        tags={"deer", "antler"},
    ),
    "roe": AnimalCfg(
        id="roe",
        label="roe deer",
        phrase="a shy roe deer",
        baby_name="roe deer",
        coat="Its soft coat looked damp with evening mist",
        antler_kind="slim antlers",
        cry="Poor thing.",
        tracks="light tracks near the roots",
        tags={"deer", "antler"},
    ),
}

PROBLEMS = {
    "basket": ProblemCfg(
        id="basket",
        label="basket snag",
        snag_text="one antler was caught in the handle of an old berry basket",
        conk_text="Another tiny conk came, as if wood had bumped against wood.",
        risk_text="If it pulled harder, the handle might scrape its face.",
        help_text="The basket slipped away from the antler",
        severity=2,
        tags={"stuck", "basket", "conk"},
    ),
    "branch": ProblemCfg(
        id="branch",
        label="branch snag",
        snag_text="a forked branch had snagged around its antler",
        conk_text="The sound came again: conk, then a rustle, then stillness.",
        risk_text="The branch was not heavy, but panic could twist it tighter.",
        help_text="The branch eased off the antler",
        severity=2,
        tags={"stuck", "branch", "conk"},
    ),
    "bump": ProblemCfg(
        id="bump",
        label="head bump",
        snag_text="it had bumped its little antler against a low stump and stood blinking",
        conk_text="It sounded like a gentle conk against old wood, followed by a tiny sniff.",
        risk_text="The bump was small, but fear made the creature freeze.",
        help_text="The frightened creature settled and was ready to move again",
        severity=1,
        tags={"bump", "conk"},
    ),
}

AIDS = {
    "blanket": AidCfg(
        id="blanket",
        label="soft blanket",
        phrase="a soft blanket from the basket under the stroller",
        use_text="together they held it low like a quiet wall, so the animal would not startle",
        comfort_text="{child} whispered, \"It is all right, little {animal}. We will be gentle.\"",
        power=2,
        kindness=2,
        tags={"blanket", "gentle"},
    ),
    "lantern": AidCfg(
        id="lantern",
        label="covered lantern",
        phrase="a lantern with its shade turned low",
        use_text="they made a small pool of light instead of waving bright beams into frightened eyes",
        comfort_text="In the soft glow, {child} kept still and spoke in a nearly bedtime voice.",
        power=1,
        kindness=2,
        tags={"light", "gentle"},
    ),
    "gloves": AidCfg(
        id="gloves",
        label="garden gloves",
        phrase="a pair of old garden gloves",
        use_text="parent's careful fingers loosened the trouble a little, but not enough on their own",
        comfort_text="{child} stayed close and calm, which mattered more than hurrying.",
        power=1,
        kindness=1,
        tags={"gloves"},
    ),
    "scarf": AidCfg(
        id="scarf",
        label="wool scarf",
        phrase="a wool scarf folded into a soft loop",
        use_text="they used the loop to lift the snag away without tugging the antler itself",
        comfort_text="{child} breathed slowly so the little animal could hear only kindness nearby.",
        power=2,
        kindness=3,
        tags={"scarf", "gentle"},
    ),
}

WISHES = {
    "keep_antler": WishCfg(
        id="keep_antler",
        want_text="and for one tiny moment wished the antler might come loose so it could be taken home like a treasure.",
        lesson_text="The antler belongs to the deer, and the deer belongs to the forest.",
        selfish=True,
        tags={"sharing", "kindness"},
    ),
    "help_first": WishCfg(
        id="help_first",
        want_text="and hoped they could help before the frightened creature ran the wrong way.",
        lesson_text="Let us help first and wonder later.",
        selfish=False,
        tags={"kindness"},
    ),
    "be_gentle": WishCfg(
        id="be_gentle",
        want_text="and felt that the most important thing was not to scare it more.",
        lesson_text="Small scared things need soft choices.",
        selfish=False,
        tags={"kindness", "gentle"},
    ),
}

GIRL_NAMES = ["Mila", "Lila", "Nora", "Ella", "Ivy", "June", "Lucy", "Ada"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Noah", "Eli", "Milo", "Ben", "Theo"]


@dataclass
class StoryParams:
    setting: str
    animal: str
    problem: str
    aid: str
    wish: str
    child_name: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "deer": [
        (
            "What is an antler?",
            "An antler is a hard branching part that grows on the head of some deer. It is part of the animal, so we should not pull on it or take it just because it looks interesting.",
        )
    ],
    "conk": [
        (
            "What does conk mean in a story like this?",
            "Conk is a sound word. It means a small bumping noise, like wood or bone tapping something hard.",
        )
    ],
    "gentle": [
        (
            "Why should people move gently around a scared animal?",
            "A scared animal can panic if people rush or shout. Moving gently helps it feel safer and keeps the trouble from getting worse.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help and care for someone, even when you could think only about yourself. It often means being gentle, patient, and fair.",
        )
    ],
    "forest": [
        (
            "Why should wild animals stay in the forest?",
            "Wild animals belong in the places where they can find food, shelter, and their families. We can admire them without keeping them.",
        )
    ],
    "bedtime": [
        (
            "Why do bedtime stories often end softly?",
            "Soft endings help your mind grow calm. A peaceful last image makes it easier to rest and feel safe.",
        )
    ],
}

KNOWLEDGE_ORDER = ["conk", "deer", "gentle", "kindness", "forest", "bedtime"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    animal_cfg = f["animal_cfg"]
    problem = f["problem"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "conk" and "antler" and teaches kindness.',
        f"Tell a gentle night-time story where {child.id} hears a small conk, finds {animal_cfg.phrase}, and learns to help instead of keeping a pretty thing.",
        f"Write a calm story with dialogue, a moral about kindness, and a forest animal whose {problem.label} is solved in a soft, bedtime way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    animal_cfg = f["animal_cfg"]
    problem = f["problem"]
    aid = f["aid"]
    wish = f["wish"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and {animal_cfg.phrase} they found near bedtime. The story follows how {child.id} reacts when the little animal is in trouble.",
        ),
        (
            "What was the conk sound?",
            f"The conk was the small sound of the animal's trouble: {problem.conk_text.lower()} It mattered because it led {child.id} to stop, listen, and notice someone needed help.",
        ),
        (
            f"Why did {child.id} have to choose carefully?",
            f"{child.id} saw the antler and felt a wish of {wish.id.replace('_', ' ')}, but the animal was frightened and needed gentle help first. The choice mattered because kindness meant thinking about the scared creature instead of a treasure.",
        ),
        (
            f"How did {child.id} and {parent.label_word} help the animal?",
            f"They used {aid.phrase} and moved very slowly. That worked because gentle help calmed the animal instead of frightening it more.",
        ),
    ]
    if outcome == "helped":
        qa.append(
            (
                "How did the story end?",
                f"The little animal became free and trotted back to the trees. Later, {child.id} went to bed remembering that kindness felt warmer than keeping the antler.",
            )
        )
    else:
        qa.append(
            (
                "Did kindness still matter even before everything was fixed?",
                "Yes. Their calm voices and gentle hands kept the animal from panicking. In the story, kindness is important not only because it solves trouble, but because it makes frightened moments safer.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"conk", "kindness", "bedtime", "gentle", "forest", "deer"}
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pine_path",
        animal="young_deer",
        problem="basket",
        aid="scarf",
        wish="keep_antler",
        child_name="Mila",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        setting="moon_garden",
        animal="roe",
        problem="branch",
        aid="blanket",
        wish="be_gentle",
        child_name="Owen",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        setting="brook_bank",
        animal="fawn",
        problem="bump",
        aid="lantern",
        wish="help_first",
        child_name="Lila",
        child_gender="girl",
        parent="mother",
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
real_problem(A, P) :- animal(A), problem(P), antlers(A), P != bump.
real_problem(A, bump) :- animal(A).
good_aid(H) :- aid(H), aid_kindness(H, K), kindness_min(M), K >= M.
works(H, P) :- good_aid(H), aid_power(H, PW), problem_severity(P, PS), PW >= PS.
valid(S, A, P, H) :- setting(S), animal(A), problem(P), aid(H), real_problem(A, P), works(H, P).

% --- outcome model ---------------------------------------------------------
freed :- chosen_problem(P), chosen_aid(H), works(H, P).
outcome(helped) :- freed.
outcome(comforted) :- not freed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, cfg in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("aid_power", aid, cfg.power))
        lines.append(asp.fact("aid_kindness", aid, cfg.kindness))
    for pid, cfg in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_severity", pid, cfg.severity))
    for aid in sensible_aids():
        pass
    for aid_id, cfg in ANIMALS.items():
        lines.append(asp.fact("animal", aid_id))
        if cfg.antler_kind != "no antlers yet":
            lines.append(asp.fact("antlers", aid_id))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_aid", params.aid),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if not aid_works(AIDS[params.aid], PROBLEMS[params.problem]):
        return "comforted"
    return "helped"


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

    for params in CURATED:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header="")
        except Exception as exc:  # pragma: no cover
            rc = 1
            print(f"SMOKE TEST FAILED for curated sample: {exc}")
            break

    trials = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            trials.append(p)
        except StoryError:
            rc = 1
            print("Random resolve failed during verify.")
            break
    bad = sum(1 for p in trials if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(trials)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(trials)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a child hears a conk, finds an antlered animal in trouble, and chooses kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.problem:
        animal = ANIMALS[args.animal]
        problem = PROBLEMS[args.problem]
        if not problem_real(animal, problem):
            raise StoryError(explain_problem(animal, problem))
    if args.aid and AIDS[args.aid].kindness < KINDNESS_MIN:
        raise StoryError(explain_aid(args.aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.animal is None or combo[1] == args.animal)
        and (args.problem is None or combo[2] == args.problem)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, animal_id, problem_id, aid_id = rng.choice(sorted(combos))
    wish_id = args.wish or rng.choice(sorted(WISHES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        animal=animal_id,
        problem=problem_id,
        aid=aid_id,
        wish=wish_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.wish not in WISHES:
        raise StoryError(f"(Unknown wish: {params.wish})")
    animal = ANIMALS[params.animal]
    problem = PROBLEMS[params.problem]
    aid = AIDS[params.aid]
    if not problem_real(animal, problem):
        raise StoryError(explain_problem(animal, problem))
    if not aid_works(aid, problem):
        raise StoryError(explain_aid(params.aid))

    world = tell(
        setting=SETTINGS[params.setting],
        animal_cfg=animal,
        problem=problem,
        aid=aid,
        wish=WISHES[params.wish],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (setting, animal, problem, aid) combos:\n")
        for setting_id, animal_id, problem_id, aid_id in combos:
            print(f"  {setting_id:12} {animal_id:10} {problem_id:8} {aid_id}")
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
            header = f"### {p.child_name}: {p.problem} with {p.animal} ({p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
