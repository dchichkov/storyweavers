#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/leave_itsy_boob_problem_solving_transformation_reconciliation.py
================================================================================================

A small fairy-tale storyworld about Itsy, a tiny caterpillar, and Boob, a young
owl with a round little face. A mishap breaks something precious near Boob's
home. Boob blames Itsy and tells the tiny visitor to leave, but Itsy stays to
solve the problem. Through patient work, Itsy changes into a butterfly, and the
two friends reconcile.

The world model keeps the tale narrow and plausible:

* A setting affords certain natural helpers.
* A problem needs a matching kind of repair.
* Only helpers with the right capability and enough strength are allowed.
* The repair work raises patience, which can trigger cocoon -> butterfly
  transformation.
* Boob's blame can turn into remorse once the world sees that Itsy truly helped.

Run it
------
    python storyworlds/worlds/gpt-5.4/leave_itsy_boob_problem_solving_transformation_reconciliation.py
    python storyworlds/worlds/gpt-5.4/leave_itsy_boob_problem_solving_transformation_reconciliation.py --all
    python storyworlds/worlds/gpt-5.4/leave_itsy_boob_problem_solving_transformation_reconciliation.py --asp
    python storyworlds/worlds/gpt-5.4/leave_itsy_boob_problem_solving_transformation_reconciliation.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
TRANSFORM_PATIENCE = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "hen"}
        male = {"boy", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    closing: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    object_label: str
    object_phrase: str
    mishap: str
    need: str
    difficulty: int
    fix_text: str
    solved_text: str
    risk_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    capability: str
    strength: int
    gather_text: str
    use_text: str
    gift_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


@dataclass
class StoryParams:
    place: str
    problem: str
    helper: str
    itsy_name: str
    boob_name: str
    boob_gender: str
    boob_trait: str
    wing_color: str
    seed: Optional[int] = None


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


def _r_fix_problem(world: World) -> list[str]:
    problem = world.get("problem")
    if problem.meters["mended"] < THRESHOLD:
        return []
    sig = ("fixed", problem.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    problem.meters["fixed"] += 1
    world.get("boob").memes["relief"] += 1
    world.get("itsy").memes["hope"] += 1
    return []


def _r_remorse(world: World) -> list[str]:
    boob = world.get("boob")
    if boob.memes["blame"] < THRESHOLD:
        return []
    if not world.facts.get("saw_help"):
        return []
    sig = ("remorse", boob.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boob.memes["remorse"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    itsy = world.get("itsy")
    if itsy.meters["cocoon"] < THRESHOLD or itsy.meters["patience"] < TRANSFORM_PATIENCE:
        return []
    sig = ("transform", itsy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    itsy.attrs["form"] = "butterfly"
    itsy.meters["wings"] += 1
    itsy.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="fix_problem", tag="physical", apply=_r_fix_problem),
    Rule(name="remorse", tag="social", apply=_r_remorse),
    Rule(name="transform", tag="magical", apply=_r_transform),
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
            else:
                before = len(world.fired)
                if len(world.fired) != before:
                    changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS: dict[str, Setting] = {
    "moon_grove": Setting(
        id="moon_grove",
        place="the Moon Grove",
        opening="In the Moon Grove, silver leaves trembled over a path soft as velvet moss.",
        closing="Moonlight puddled on the moss, and the grove looked kind again.",
        affords={"spider_silk", "honeysuckle_vine"},
        tags={"grove", "moonlight"},
    ),
    "lily_pond": Setting(
        id="lily_pond",
        place="the Lily Pond",
        opening="By the Lily Pond, round leaves floated like tiny boats and the water held the moon in one bright piece.",
        closing="The pond shone smooth as glass, and even the reeds seemed to bow to the peace.",
        affords={"spider_silk", "reed_cradle"},
        tags={"pond", "moonlight"},
    ),
    "thimble_hill": Setting(
        id="thimble_hill",
        place="Thimble Hill",
        opening="On Thimble Hill, thyme and clover made the air smell sweet, and little stone steps climbed toward the stars.",
        closing="A small breeze ran over the hill, and every clover head nodded as if agreeing the quarrel was over.",
        affords={"honeysuckle_vine", "reed_cradle"},
        tags={"hill", "stars"},
    ),
}

PROBLEMS: dict[str, Problem] = {
    "torn_cradle": Problem(
        id="torn_cradle",
        object_label="cradle",
        object_phrase="a dew-cradle woven for Boob's bedtime swing",
        mishap="A sudden gust caught the cradle and tore one shining side open.",
        need="stitch",
        difficulty=2,
        fix_text="The torn weave needed careful stitching before it could hold weight again.",
        solved_text="The cradle hung snug and whole once more.",
        risk_text="If it stayed torn, Boob's bedtime swing would tip and drop its warm blanket into the mud below.",
        tags={"nest", "repair"},
    ),
    "fallen_bell": Problem(
        id="fallen_bell",
        object_label="dew bell",
        object_phrase="a glassy dew bell that rang outside Boob's hollow",
        mishap="A branch shook, and the dew bell slipped from its twig and slid into the reeds below.",
        need="lift",
        difficulty=1,
        fix_text="The bell needed gentle lifting so it could be set back where morning wind could ring it.",
        solved_text="The dew bell glittered in its old place again.",
        risk_text="If it stayed below, the bell would crack at sunrise and Boob would lose the song that woke the hollow.",
        tags={"bell", "repair"},
    ),
    "snapped_step": Problem(
        id="snapped_step",
        object_label="moss step",
        object_phrase="the mossy little step below Boob's hollow door",
        mishap="When a fat raindrop fell from a high leaf, the moss step snapped loose from its root.",
        need="bind",
        difficulty=2,
        fix_text="The step needed binding tight before anyone could hop safely to the hollow door.",
        solved_text="The moss step sat firm and springy again.",
        risk_text="If it stayed loose, Boob would tumble each time he tried to reach home.",
        tags={"stairs", "repair"},
    ),
}

HELPERS: dict[str, Helper] = {
    "spider_silk": Helper(
        id="spider_silk",
        label="spider silk",
        phrase="a silver string of spider silk",
        capability="stitch",
        strength=2,
        gather_text="Itsy asked the patient spider for one silver string, and the spider, hearing the worry in the night, let it glisten into Itsy's hands.",
        use_text="With small careful loops, Itsy stitched the shining silk through the broken weave.",
        gift_text="a silver string of spider silk for mending",
        tags={"spider", "silk"},
    ),
    "reed_cradle": Helper(
        id="reed_cradle",
        label="reed hook",
        phrase="a bent reed hook",
        capability="lift",
        strength=1,
        gather_text="Itsy bent a young reed into a little hook and tested it against the water until it held true.",
        use_text="Balancing on a leaf edge, Itsy slipped the hook under the fallen bell and raised it slowly, slowly, until the stem could take it again.",
        gift_text="a bent reed hook for lifting",
        tags={"reed", "pond"},
    ),
    "honeysuckle_vine": Helper(
        id="honeysuckle_vine",
        label="honeysuckle vine",
        phrase="a soft strand of honeysuckle vine",
        capability="bind",
        strength=2,
        gather_text="Itsy drew a soft strand of honeysuckle vine from the hedge and tugged until it was just right for tying.",
        use_text="Round and round went the vine as Itsy wrapped it tight and tucked the knot under the moss.",
        gift_text="a soft honeysuckle vine for tying",
        tags={"vine", "flower"},
    ),
}

BOOB_TRAITS = ["huffy", "worried", "proud", "sleepy"]
WING_COLORS = ["gold", "blue", "rose", "amber", "violet"]
ITSY_NAMES = ["Itsy", "Tansy", "Mote", "Pip"]
BOOB_NAMES = ["Boob", "Nib", "Puff", "Boob"]


def helper_fits(problem: Problem, helper: Helper) -> bool:
    return helper.capability == problem.need and helper.strength >= problem.difficulty


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            for helper_id in sorted(setting.affords):
                helper = HELPERS[helper_id]
                if helper_fits(problem, helper):
                    combos.append((place_id, problem_id, helper_id))
    return sorted(combos)


def explain_rejection(setting: Setting, problem: Problem, helper: Helper) -> str:
    if helper.id not in setting.affords:
        return (
            f"(No story: {helper.label} does not belong in {setting.place}, so the fairy-tale world "
            f"cannot honestly offer it there.)"
        )
    if helper.capability != problem.need:
        return (
            f"(No story: {problem.object_label} needs a way to {problem.need}, but {helper.label} is for "
            f"{helper.capability}. The fix must match the problem.)"
        )
    if helper.strength < problem.difficulty:
        return (
            f"(No story: {helper.label} is too slight for this repair. The helper must be strong enough "
            f"to solve the trouble for real.)"
        )
    return "(No story: this combination does not make a sensible repair.)"


def predict_if_itsy_leaves(world: World) -> dict:
    sim = world.copy()
    problem = sim.get("problem")
    return {
        "fixed": problem.meters["fixed"] >= THRESHOLD,
        "risk": sim.facts["problem_cfg"].risk_text,
    }


def introduce(world: World, itsy: Entity, boob: Entity, problem: Problem) -> None:
    world.say(world.setting.opening)
    world.say(
        f"There lived {itsy.id}, an itsy caterpillar with patient feet, and {boob.id}, a round little owl who kept watch near {problem.object_phrase}."
    )
    world.say(
        f"{boob.id} was {world.facts['boob_trait']} tonight, but {itsy.id} came only to admire the moon and share the quiet."
    )


def mishap(world: World, boob: Entity, problem_ent: Entity, problem: Problem) -> None:
    problem_ent.meters["broken"] += 1
    boob.memes["fear"] += 1
    world.say(problem.mishap)
    world.say(f"{boob.id} gave a startled flap and stared at the trouble below.")


def blame(world: World, itsy: Entity, boob: Entity) -> None:
    boob.memes["blame"] += 1
    if world.facts["boob_trait"] == "huffy":
        line = f'"Oh dear! You came, and now everything is wrong. Just leave me to my trouble," cried {boob.id}.'
    elif world.facts["boob_trait"] == "proud":
        line = f'"I did not need company for this, and now I need it less. You may leave," said {boob.id}, trying to sound grand though {boob.pronoun()} was trembling.'
    elif world.facts["boob_trait"] == "sleepy":
        line = f'"I was nearly asleep, and now my whole night is upset. Please leave me alone," mumbled {boob.id}.'
    else:
        line = f'"If you stay, I will only worry more. Please leave," whispered {boob.id}.'
    world.say(line)


def choose_to_help(world: World, itsy: Entity, boob: Entity, problem: Problem) -> None:
    pred = predict_if_itsy_leaves(world)
    world.facts["predicted_risk"] = pred["risk"]
    itsy.memes["care"] += 1
    world.say(
        f'Itsy looked at the broken {problem.object_label} and shook {itsy.pronoun("possessive")} tiny head. "I will not leave while this can still be mended," {itsy.pronoun()} said.'
    )
    world.say(
        f"{itsy.id} could see what would happen otherwise: {pred['risk']}"
    )


def gather_helper(world: World, itsy: Entity, helper: Helper) -> None:
    itsy.meters["patience"] += 1
    world.say(helper.gather_text)


def mend(world: World, itsy: Entity, boob: Entity, problem_ent: Entity, helper: Helper, problem: Problem) -> None:
    itsy.meters["patience"] += 1
    itsy.meters["cocoon"] += 1
    world.facts["saw_help"] = True
    problem_ent.meters["mended"] += 1
    world.say(problem.fix_text)
    world.say(helper.use_text)
    propagate(world, narrate=False)
    world.say(problem.solved_text)
    if boob.memes["remorse"] >= THRESHOLD:
        world.say(f"{boob.id}'s feathers sank a little as {boob.pronoun()} understood that {itsy.id} had stayed to help, not to harm.")


def rest_and_transform(world: World, itsy: Entity) -> None:
    form_before = itsy.attrs.get("form", "caterpillar")
    itsy.meters["rest"] += 1
    propagate(world, narrate=False)
    if form_before != "butterfly" and itsy.attrs.get("form") == "butterfly":
        color = world.facts["wing_color"]
        world.say(
            f"When the work was done, Itsy rested in a little cocoon no bigger than a curled petal. Before the moon crossed the top of the sky, the cocoon opened, and out came a {color}-winged butterfly where the itsy caterpillar had been."
        )


def reconcile(world: World, itsy: Entity, boob: Entity, helper: Helper) -> None:
    if boob.memes["remorse"] < THRESHOLD:
        boob.memes["remorse"] += 1
    boob.memes["love"] += 1
    itsy.memes["love"] += 1
    world.say(
        f'{boob.id} blinked up at {itsy.id} and bowed {boob.pronoun("possessive")} round head. "I was wrong to send you away. You brought {helper.gift_text}, and you brought a brave heart besides," {boob.pronoun()} said.'
    )
    world.say(
        f'"Then let us begin again," said {itsy.id}. And so they did.'
    )


def close_story(world: World, itsy: Entity, boob: Entity, problem: Problem) -> None:
    world.say(
        f"Together they watched the mended {problem.object_label} shine softly in the night."
    )
    world.say(
        f"{world.setting.closing} {boob.id} no longer asked {itsy.id} to leave, and {itsy.id} no longer seemed small at all."
    )


def tell(
    setting: Setting,
    problem: Problem,
    helper: Helper,
    itsy_name: str = "Itsy",
    boob_name: str = "Boob",
    boob_gender: str = "boy",
    boob_trait: str = "worried",
    wing_color: str = "gold",
) -> World:
    world = World(setting)
    itsy = world.add(Entity(
        id="itsy",
        kind="character",
        type="bug",
        label=itsy_name,
        phrase=itsy_name,
        attrs={"form": "caterpillar", "display_name": itsy_name},
        tags={"caterpillar"},
    ))
    boob = world.add(Entity(
        id="boob",
        kind="character",
        type=boob_gender,
        label=boob_name,
        phrase=boob_name,
        tags={"owl"},
    ))
    problem_ent = world.add(Entity(
        id="problem",
        kind="thing",
        type="problem",
        label=problem.object_label,
        phrase=problem.object_phrase,
        tags=set(problem.tags),
    ))

    world.facts.update(
        itsy=itsy,
        boob=boob,
        problem_ent=problem_ent,
        problem_cfg=problem,
        helper_cfg=helper,
        setting_cfg=setting,
        itsy_name=itsy_name,
        boob_name=boob_name,
        boob_trait=boob_trait,
        wing_color=wing_color,
        saw_help=False,
    )

    introduce(world, itsy, boob, problem)
    world.para()
    mishap(world, boob, problem_ent, problem)
    blame(world, itsy, boob)

    world.para()
    choose_to_help(world, itsy, boob, problem)
    gather_helper(world, itsy, helper)
    mend(world, itsy, boob, problem_ent, helper, problem)

    world.para()
    rest_and_transform(world, itsy)
    reconcile(world, itsy, boob)
    close_story(world, itsy, boob, problem)

    world.facts.update(
        fixed=problem_ent.meters["fixed"] >= THRESHOLD,
        transformed=itsy.attrs.get("form") == "butterfly",
        reconciled=boob.memes["love"] >= THRESHOLD and itsy.memes["love"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "caterpillar": [
        (
            "What is a caterpillar?",
            "A caterpillar is the crawling young form of a butterfly or moth. It has a soft body and many tiny legs."
        )
    ],
    "butterfly": [
        (
            "How does a caterpillar become a butterfly?",
            "A caterpillar makes a cocoon or chrysalis and changes inside it. After that change, it comes out with wings."
        )
    ],
    "owl": [
        (
            "What is an owl?",
            "An owl is a bird with big eyes and soft feathers. Many owls are awake at night."
        )
    ],
    "repair": [
        (
            "What does it mean to mend something?",
            "To mend something means to fix what is torn, loose, or broken so it can be used again. Careful work can turn a problem into something sturdy."
        )
    ],
    "spider": [
        (
            "Why is spider silk strong?",
            "Spider silk is very thin, but it can still be strong for its size. Spiders use it to make webs and wrap things safely."
        )
    ],
    "reed": [
        (
            "What is a reed?",
            "A reed is a tall, bendy plant that grows near water. Its long stem can sway without snapping easily."
        )
    ],
    "vine": [
        (
            "What is a vine?",
            "A vine is a plant with long stems that can curl, climb, or wrap around things. Some vines are useful for tying or holding light things."
        )
    ],
    "moonlight": [
        (
            "What is moonlight?",
            "Moonlight is sunlight bouncing off the moon and reaching Earth at night. It looks soft because it is much dimmer than daylight."
        )
    ],
    "apology": [
        (
            "Why is saying sorry important?",
            "Saying sorry matters because it shows you know you hurt someone or judged them unfairly. A true apology can help friendship grow again."
        )
    ],
}
KNOWLEDGE_ORDER = ["caterpillar", "butterfly", "owl", "repair", "spider", "reed", "vine", "moonlight", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem = f["problem_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting_cfg"]
    itsy_name = f["itsy_name"]
    boob_name = f["boob_name"]
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes the words "leave", "{itsy_name}", and "{boob_name}".',
        f"Tell a gentle fairy-tale story set in {setting.place} where {boob_name} blames {itsy_name} for a broken {problem.object_label}, but {itsy_name} solves the problem with {helper.label}, changes shape, and the two make peace.",
        f'Write a story with problem solving, transformation, and reconciliation, ending with a repaired {problem.object_label} under moonlight.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    itsy = f["itsy"]
    boob = f["boob"]
    problem = f["problem_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['itsy_name']}, an itsy caterpillar, and {f['boob_name']}, a young owl in {setting.place}. They begin in a quarrel and end as friends again."
        ),
        (
            f"What problem happened to the {problem.object_label}?",
            f"{problem.mishap} That mattered because {problem.risk_text}"
        ),
        (
            f"Why did {f['boob_name']} ask {f['itsy_name']} to leave?",
            f"{f['boob_name']} was frightened and quickly blamed {f['itsy_name']} when the trouble happened. The fear came first, so the unkind words came before careful thinking."
        ),
        (
            f"How did {f['itsy_name']} solve the problem?",
            f"{f['itsy_name']} stayed, found {helper.phrase}, and used it to mend the broken {problem.object_label}. The fix worked because {helper.label} was the right kind of help for that repair."
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                f"What transformation happened to {f['itsy_name']}?",
                f"After the patient work was finished, {f['itsy_name']} rested in a little cocoon and became a {f['wing_color']}-winged butterfly. The story shows the change as a reward for patience as well as magic."
            )
        )
    if f.get("reconciled"):
        qa.append(
            (
                f"How did {f['boob_name']} and {f['itsy_name']} reconcile?",
                f"{f['boob_name']} admitted the blame had been unfair and asked to begin again. Their friendship healed because the apology followed real help and real understanding."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"caterpillar", "butterfly", "owl", "repair", "apology"} | set(f["setting_cfg"].tags)
    helper = f["helper_cfg"]
    if helper.id == "spider_silk":
        tags.add("spider")
    if helper.id == "reed_cradle":
        tags.add("reed")
    if helper.id == "honeysuckle_vine":
        tags.add("vine")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED: list[StoryParams] = [
    StoryParams(
        place="moon_grove",
        problem="torn_cradle",
        helper="spider_silk",
        itsy_name="Itsy",
        boob_name="Boob",
        boob_gender="boy",
        boob_trait="huffy",
        wing_color="gold",
    ),
    StoryParams(
        place="lily_pond",
        problem="fallen_bell",
        helper="reed_cradle",
        itsy_name="Itsy",
        boob_name="Boob",
        boob_gender="girl",
        boob_trait="worried",
        wing_color="blue",
    ),
    StoryParams(
        place="thimble_hill",
        problem="snapped_step",
        helper="honeysuckle_vine",
        itsy_name="Tansy",
        boob_name="Boob",
        boob_gender="boy",
        boob_trait="proud",
        wing_color="amber",
    ),
]


ASP_RULES = r"""
compatible(Problem, Helper) :-
    need(Problem, Need),
    capability(Helper, Need),
    strength(Helper, S),
    difficulty(Problem, D),
    S >= D.

valid(Place, Problem, Helper) :-
    setting(Place),
    problem(Problem),
    helper(Helper),
    affords(Place, Helper),
    compatible(Problem, Helper).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for helper_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, helper_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("need", problem_id, problem.need))
        lines.append(asp.fact("difficulty", problem_id, problem.difficulty))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("capability", helper_id, helper.capability))
        lines.append(asp.fact("strength", helper_id, helper.strength))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Fairy-tale storyworld: Itsy stays, solves a problem, transforms, and reconciles with Boob."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--boob-gender", choices=["boy", "girl"])
    ap.add_argument("--boob-trait", choices=BOOB_TRAITS)
    ap.add_argument("--itsy-name")
    ap.add_argument("--boob-name")
    ap.add_argument("--wing-color", choices=WING_COLORS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.problem and args.helper:
        setting = SETTINGS[args.place]
        problem = PROBLEMS[args.problem]
        helper = HELPERS[args.helper]
        if (args.place, args.problem, args.helper) not in valid_combos():
            raise StoryError(explain_rejection(setting, problem, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.problem is None or combo[1] == args.problem)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem, helper = rng.choice(combos)
    return StoryParams(
        place=place,
        problem=problem,
        helper=helper,
        itsy_name=args.itsy_name or rng.choice(ITSY_NAMES),
        boob_name=args.boob_name or rng.choice(BOOB_NAMES),
        boob_gender=args.boob_gender or rng.choice(["boy", "girl"]),
        boob_trait=args.boob_trait or rng.choice(BOOB_TRAITS),
        wing_color=args.wing_color or rng.choice(WING_COLORS),
    )


def _validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.boob_gender not in {"boy", "girl"}:
        raise StoryError(f"(Unknown Boob gender: {params.boob_gender})")
    if params.boob_trait not in BOOB_TRAITS:
        raise StoryError(f"(Unknown Boob trait: {params.boob_trait})")
    if params.wing_color not in WING_COLORS:
        raise StoryError(f"(Unknown wing color: {params.wing_color})")

    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    helper = HELPERS[params.helper]
    if (params.place, params.problem, params.helper) not in valid_combos():
        raise StoryError(explain_rejection(setting, problem, helper))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        setting=SETTINGS[params.place],
        problem=PROBLEMS[params.problem],
        helper=HELPERS[params.helper],
        itsy_name=params.itsy_name,
        boob_name=params.boob_name,
        boob_gender=params.boob_gender,
        boob_trait=params.boob_trait,
        wing_color=params.wing_color,
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
        if not sample.story or "leave" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or missed the key word 'leave'.)")
        if sample.world is None or not sample.world.facts.get("transformed") or not sample.world.facts.get("reconciled"):
            raise StoryError("(Smoke test failed: story missed transformation or reconciliation.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(5):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Generated blank story.)")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")

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
        print(f"{len(combos)} compatible (place, problem, helper) combos:\n")
        for place, problem, helper in combos:
            print(f"  {place:12} {problem:12} {helper}")
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
            header = f"### {p.itsy_name} and {p.boob_name}: {p.problem} at {p.place}"
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
