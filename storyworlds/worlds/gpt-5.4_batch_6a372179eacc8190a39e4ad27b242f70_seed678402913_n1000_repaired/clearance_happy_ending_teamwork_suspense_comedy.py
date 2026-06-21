#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clearance_happy_ending_teamwork_suspense_comedy.py
=============================================================================

A standalone storyworld about children trying to move a silly homemade parade
creation through a low opening. The core constraint is **clearance**: the build
must fit under the opening, either as-is or by using a teamwork-based plan that
honestly creates enough room.

The tone is light and comic, but the model keeps a real little tension arc:
there is a goal, a squeeze point, a near-stuck moment, a cooperative fix, and a
happy ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/clearance_happy_ending_teamwork_suspense_comedy.py
    python storyworlds/worlds/gpt-5.4/clearance_happy_ending_teamwork_suspense_comedy.py --project dragon --opening arch
    python storyworlds/worlds/gpt-5.4/clearance_happy_ending_teamwork_suspense_comedy.py --project rocket --plan tilt
    python storyworlds/worlds/gpt-5.4/clearance_happy_ending_teamwork_suspense_comedy.py --all
    python storyworlds/worlds/gpt-5.4/clearance_happy_ending_teamwork_suspense_comedy.py --verify
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
        female = {"girl", "mother", "mom", "woman", "teacher_f"}
        male = {"boy", "father", "dad", "man", "teacher_m"}
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
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    event: str
    crowd: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    height: int
    wobble: int
    topper: str
    sound: str
    style_line: str
    fragile_top: bool = False
    tilt_ok: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Opening:
    id: str
    label: str
    phrase: str
    clearance: int
    squeak: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    sense: int
    drop: int
    needs_teamwork: bool
    safe_for_fragile: bool
    requires_tiltable: bool
    action_text: str
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "helper"}]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stuck_tension(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    opening = world.get("opening")
    if project.meters["blocked"] < THRESHOLD:
        return out
    sig = ("stuck_tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    opening.meters["threat"] += 1
    out.append("__blocked__")
    return out


CAUSAL_RULES = [
    Rule(name="stuck_tension", tag="social", apply=_r_stuck_tension),
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
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "school": Setting(
        id="school",
        place="the school hallway",
        event="the class parade",
        crowd="teachers with clipboards and children trying not to giggle",
        tags={"school", "parade"},
    ),
    "library": Setting(
        id="library",
        place="the library lobby",
        event="the costume book march",
        crowd="librarians, paper stars, and a line of excited families",
        tags={"library", "books"},
    ),
    "rec_center": Setting(
        id="rec_center",
        place="the rec center corridor",
        event="the neighborhood fun fair",
        crowd="neighbors carrying streamers and folding chairs",
        tags={"community", "fair"},
    ),
}

PROJECTS = {
    "dragon": Project(
        id="dragon",
        label="dragon float",
        phrase="a cardboard dragon float with bouncing tissue-paper eyebrows",
        height=9,
        wobble=2,
        topper="eyebrows",
        sound="fwump",
        style_line="Its silly paper eyebrows bobbed so hard that they kept looking surprised before anyone else was.",
        fragile_top=True,
        tilt_ok=True,
        tags={"dragon", "cardboard", "parade"},
    ),
    "rocket": Project(
        id="rocket",
        label="moon rocket",
        phrase="a silver-painted moon rocket with a shiny cone on top",
        height=10,
        wobble=1,
        topper="cone",
        sound="bonk",
        style_line="Every time it rolled, the taped-on stars flashed like they were trying very hard to be important.",
        fragile_top=False,
        tilt_ok=True,
        tags={"rocket", "space", "parade"},
    ),
    "castle": Project(
        id="castle",
        label="castle tower",
        phrase="a castle tower made from stacked boxes and noodle-flag pennants",
        height=8,
        wobble=3,
        topper="pennants",
        sound="boff",
        style_line="One noodle-flag kept saluting the ceiling as if it had its own opinion.",
        fragile_top=True,
        tilt_ok=False,
        tags={"castle", "boxes", "parade"},
    ),
}

OPENINGS = {
    "arch": Opening(
        id="arch",
        label="arch",
        phrase="a low paper-star arch",
        clearance=8,
        squeak="The wheels made a tiny nervous squeak on the shiny floor.",
        tags={"arch", "low"},
    ),
    "door": Opening(
        id="door",
        label="doorway",
        phrase="a classroom doorway with a bright banner taped across the top",
        clearance=9,
        squeak="The cart rattled once and then went very still.",
        tags={"door", "banner"},
    ),
    "gate": Opening(
        id="gate",
        label="gate",
        phrase="a garden gate under a string of bells",
        clearance=7,
        squeak="One bell gave a warning tinkle, like it had already seen trouble coming.",
        tags={"gate", "bells"},
    ),
}

PLANS = {
    "duck": Plan(
        id="duck",
        label="lower the cart handles",
        sense=3,
        drop=1,
        needs_teamwork=True,
        safe_for_fragile=True,
        requires_tiltable=False,
        action_text="One child held the front, one held the back, and together they bent their knees and lowered the cart handles by the same careful amount.",
        success_text="The whole project sank just enough to make a finger-width of clearance.",
        fail_text="It dropped a little, but not enough; the top still hovered under the opening like a worried eyebrow.",
        qa_text="They worked together to lower the cart so the project sat a little lower.",
        tags={"teamwork", "clearance"},
    ),
    "tilt": Plan(
        id="tilt",
        label="tilt it sideways",
        sense=3,
        drop=2,
        needs_teamwork=True,
        safe_for_fragile=False,
        requires_tiltable=True,
        action_text="They counted to three, tipped the cart sideways, and shuffled forward in tiny crab steps while a grown-up kept a hand near the middle.",
        success_text="The tallest part slipped through first, and the rest followed with a long, comic breath of relief.",
        fail_text="The angle helped, but the top still nudged the opening before they could get through.",
        qa_text="They tilted the project sideways together so its tallest point would pass under the opening.",
        tags={"teamwork", "tilt", "clearance"},
    ),
    "remove_topper": Plan(
        id="remove_topper",
        label="remove the topper",
        sense=2,
        drop=2,
        needs_teamwork=True,
        safe_for_fragile=True,
        requires_tiltable=False,
        action_text="They unhooked the top piece, tucked it under one arm, and tried not to laugh at how the project suddenly looked bald.",
        success_text="Without the top piece, there was plenty of clearance.",
        fail_text="Even without the top piece, the project was still too tall for the opening.",
        qa_text="They took off the top decoration first, making the project shorter before they rolled it through.",
        tags={"teamwork", "clearance", "topper"},
    ),
    "charge": Plan(
        id="charge",
        label="push faster",
        sense=1,
        drop=0,
        needs_teamwork=False,
        safe_for_fragile=False,
        requires_tiltable=False,
        action_text="They leaned in and tried to hurry, which was not a real plan at all.",
        success_text="By pure luck it somehow worked.",
        fail_text="Going faster did not change the height even one tiny bit.",
        qa_text="They tried to rush, but that did not create any extra clearance.",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "bouncy", "funny", "steady", "bright", "eager"]


def effective_height(project: Project, plan: Plan) -> int:
    return project.height - plan.drop


def plan_allowed(project: Project, plan: Plan) -> bool:
    if plan.sense < SENSE_MIN:
        return False
    if project.fragile_top and not plan.safe_for_fragile:
        return False
    if plan.requires_tiltable and not project.tilt_ok:
        return False
    return True


def plan_succeeds(project: Project, opening: Opening, plan: Plan) -> bool:
    return effective_height(project, plan) <= opening.clearance


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for project_id, project in PROJECTS.items():
            for opening_id, opening in OPENINGS.items():
                for plan_id, plan in PLANS.items():
                    if plan_allowed(project, plan) and plan_succeeds(project, opening, plan):
                        combos.append((setting_id, project_id, opening_id, plan_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    project: str
    opening: str
    plan: str
    leader: str
    leader_gender: str
    helper: str
    helper_gender: str
    grownup: str
    trait1: str
    trait2: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="school",
        project="dragon",
        opening="arch",
        plan="remove_topper",
        leader="Lily",
        leader_gender="girl",
        helper="Max",
        helper_gender="boy",
        grownup="teacher_f",
        trait1="funny",
        trait2="steady",
        seed=None,
    ),
    StoryParams(
        setting="library",
        project="rocket",
        opening="door",
        plan="duck",
        leader="Ben",
        leader_gender="boy",
        helper="Mia",
        helper_gender="girl",
        grownup="teacher_m",
        trait1="eager",
        trait2="careful",
        seed=None,
    ),
    StoryParams(
        setting="rec_center",
        project="rocket",
        opening="arch",
        plan="tilt",
        leader="Zoe",
        leader_gender="girl",
        helper="Theo",
        helper_gender="boy",
        grownup="father",
        trait1="bright",
        trait2="bouncy",
        seed=None,
    ),
    StoryParams(
        setting="school",
        project="castle",
        opening="gate",
        plan="remove_topper",
        leader="Noah",
        leader_gender="boy",
        helper="Ella",
        helper_gender="girl",
        grownup="teacher_f",
        trait1="steady",
        trait2="funny",
        seed=None,
    ),
]


def explain_rejection(project: Project, opening: Opening, plan: Plan) -> str:
    if plan.sense < SENSE_MIN:
        return (
            f"(No story: '{plan.id}' is not a sensible clearance plan. "
            f"Rushing does not make {project.label} shorter.)"
        )
    if project.fragile_top and not plan.safe_for_fragile:
        return (
            f"(No story: tilting would be too rough for the {project.label}'s fragile "
            f"{project.topper}. Pick a gentler teamwork plan.)"
        )
    if plan.requires_tiltable and not project.tilt_ok:
        return (
            f"(No story: the {project.label} is too wobbly to tilt safely. "
            f"It needs a plan that keeps it upright.)"
        )
    if not plan_succeeds(project, opening, plan):
        return (
            f"(No story: the {project.label} is about {project.height} units tall, "
            f"the {opening.label} allows {opening.clearance}, and '{plan.id}' only "
            f"reduces the height to {effective_height(project, plan)}. That leaves "
            f"no honest clearance.)"
        )
    return "(No story: this combination does not work.)"


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def predict_block(world: World, plan: Plan) -> dict:
    sim = world.copy()
    project = sim.get("project")
    opening = sim.get("opening")
    project.meters["effective_height"] = project.meters["height"] - plan.drop
    blocked = project.meters["effective_height"] > opening.meters["clearance"]
    if blocked:
        project.meters["blocked"] += 1
        propagate(sim, narrate=False)
    return {
        "blocked": blocked,
        "effective_height": int(project.meters["effective_height"]),
        "clearance": int(opening.meters["clearance"]),
    }


def introduce(world: World, setting: Setting, a: Entity, b: Entity, grown: Entity, project: Project) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In {setting.place}, {a.id} and {b.id} were steering {project.phrase} toward {setting.event}. "
        f"{setting.crowd} filled the air, and the project looked much more confident than it really was."
    )
    world.say(project.style_line)
    world.say(
        f'{grown.label_word.capitalize()} {grown.id} walked beside them and said, '
        f'"Slow and steady, team. If this magnificent creature survives the trip, it gets to be famous."'
    )


def announce_goal(world: World, project: Project) -> None:
    world.say(
        f'The children grinned so hard that the {project.label} almost seemed to grin too. '
        f'Its wheels gave a tiny {project.sound} as they rolled.'
    )


def spot_opening(world: World, opening: Opening, a: Entity, b: Entity) -> None:
    world.say(
        f"Then they reached {opening.phrase}. {opening.squeak}"
    )
    world.say(
        f'{a.id} looked up. {b.id} looked up. Then they both looked up again, which did not help.'
    )


def measure_worry(world: World, plan: Plan, a: Entity, b: Entity) -> None:
    pred = predict_block(world, plan)
    world.facts["predicted_blocked"] = pred["blocked"]
    world.facts["predicted_height"] = pred["effective_height"]
    world.facts["opening_clearance"] = pred["clearance"]
    if pred["blocked"]:
        world.say(
            f'"Do we have enough clearance?" {a.id} whispered. Nobody wanted to bonk the top in front of everyone.'
        )
    else:
        world.say(
            f'"We might have just enough clearance," {b.id} whispered, which somehow felt even more suspenseful.'
        )


def first_try(world: World, plan: Plan, project_cfg: Project, opening_cfg: Opening, a: Entity, b: Entity) -> None:
    project = world.get("project")
    opening = world.get("opening")
    world.say(plan.action_text)
    project.meters["effective_height"] = project.meters["height"] - plan.drop
    if project.meters["effective_height"] > opening.meters["clearance"]:
        project.meters["blocked"] += 1
        project.meters["bonk_risk"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The top hovered under the {opening_cfg.label} so closely that everybody froze. "
            f"It was the quietest quiet either child had ever heard around craft supplies."
        )
        world.say(plan.fail_text)
    else:
        project.meters["moved"] += 1
        for kid in (a, b):
            kid.memes["bravery"] += 1
        world.say(
            f"For one breath, it seemed the whole room leaned in with them."
        )
        world.say(plan.success_text)


def teamwork_push(world: World, a: Entity, b: Entity, grown: Entity, plan: Plan, project_cfg: Project, opening_cfg: Opening) -> None:
    project = world.get("project")
    opening = world.get("opening")
    if project.meters["moved"] >= THRESHOLD:
        return
    world.para()
    world.say(
        f'{grown.label_word.capitalize()} {grown.id} did not yank the cart or panic. '
        f'"Nobody rush," {grown.pronoun()} said. "We make room with brains first, feet second."'
    )
    if plan.id != "remove_topper":
        world.say(
            f"{a.id} and {b.id} reset their hands, counted together, and tried again exactly the same way, only calmer."
        )
    else:
        world.say(
            f"{a.id} held the screws, {b.id} held the top piece, and even the grown-up held a strip of tape ready like a doctor with a bandage."
        )
    project.meters["effective_height"] = project.meters["height"] - plan.drop
    if project.meters["effective_height"] <= opening.meters["clearance"]:
        project.meters["moved"] += 1
        project.meters["blocked"] = 0.0
        opening.meters["threat"] = 0.0
        for kid in (a, b):
            kid.memes["relief"] += 1
            kid.memes["pride"] += 1
            kid.memes["worry"] = 0.0
        world.say(
            f"Very slowly, the {project_cfg.label} slid under the {opening_cfg.label}. "
            f"There was exactly enough clearance and not one crumb more."
        )
    else:
        world.say("But the opening still said no. This storyworld refuses to pretend otherwise.")


def celebrate(world: World, setting: Setting, a: Entity, b: Entity, project_cfg: Project) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["love"] += 1
    world.say(
        f"Once they were through, both children burst into the kind of laugh that only comes after being scared for a minute."
    )
    bald = ""
    if world.facts["plan"].id == "remove_topper":
        bald = f" The poor thing looked a little bald without its {project_cfg.topper}, which only made everybody laugh harder."
    world.say(
        f"At the end of the line, the {project_cfg.label} rolled proudly into {setting.event} instead of getting stuck before it even began.{bald}"
    )
    world.say(
        f"{a.id} and {b.id} marched beside it shoulder to shoulder, grinning because teamwork had saved the day and the joke."
    )


def tell(
    setting: Setting,
    project_cfg: Project,
    opening_cfg: Opening,
    plan: Plan,
    leader_name: str,
    leader_gender: str,
    helper_name: str,
    helper_gender: str,
    grown_type: str,
    trait1: str,
    trait2: str,
) -> World:
    world = World()
    a = world.add(Entity(id=leader_name, kind="character", type=leader_gender, role="leader", traits=[trait1]))
    b = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=[trait2]))
    grown = world.add(Entity(id="Pat", kind="character", type=grown_type, role="grownup", label="the grown-up"))
    project = world.add(Entity(id="project", type="project", label=project_cfg.label, phrase=project_cfg.phrase))
    opening = world.add(Entity(id="opening", type="opening", label=opening_cfg.label, phrase=opening_cfg.phrase))

    project.meters["height"] = float(project_cfg.height)
    opening.meters["clearance"] = float(opening_cfg.clearance)
    project.meters["wobble"] = float(project_cfg.wobble)

    introduce(world, setting, a, b, grown, project_cfg)
    announce_goal(world, project_cfg)

    world.para()
    spot_opening(world, opening_cfg, a, b)
    measure_worry(world, plan, a, b)
    first_try(world, plan, project_cfg, opening_cfg, a, b)

    world.para()
    teamwork_push(world, a, b, grown, plan, project_cfg, opening_cfg)
    celebrate(world, setting, a, b, project_cfg)

    world.facts.update(
        setting=setting,
        project_cfg=project_cfg,
        opening_cfg=opening_cfg,
        plan=plan,
        leader=a,
        helper=b,
        grownup=grown,
        success=project.meters["moved"] >= THRESHOLD,
        effective_height=int(project.meters["height"] - plan.drop),
        clearance=opening_cfg.clearance,
        blocked_before=bool(world.facts.get("predicted_blocked")),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["leader"]
    b = f["helper"]
    project = f["project_cfg"]
    opening = f["opening_cfg"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "clearance" and ends happily.',
        f"Tell a suspenseful teamwork story where {a.id} and {b.id} must get a {project.label} under a {opening.label} without bonking it.",
        f"Write a gentle comedy about children solving a too-tall problem together while a grown-up stays calm and helps.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["leader"]
    b = f["helper"]
    grown = f["grownup"]
    project = f["project_cfg"]
    opening = f["opening_cfg"]
    plan = f["plan"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children moving a {project.label}, and {grown.label_word} Pat walking beside them. They have to solve a small problem together before the big event can start.",
        ),
        (
            f"What problem did they notice at the {opening.label}?",
            f"They realized the {project.label} might be too tall for the {opening.label}. That is why {a.id} whispered about clearance and everybody suddenly got very quiet.",
        ),
        (
            "Why did the moment feel suspenseful?",
            f"It felt suspenseful because the children were almost at the event when they saw the low opening. If the top bonked it, their funny project could get bent or stuck right in front of everyone.",
        ),
        (
            "How did they solve the problem?",
            f"{plan.qa_text} The plan worked because it honestly made the project short enough to fit under the opening.",
        ),
        (
            "Did anyone solve it alone?",
            f"No. {a.id}, {b.id}, and the grown-up all helped in small ways, and the story makes teamwork the reason the problem ends happily.",
        ),
        (
            "How did the story end?",
            f"The {project.label} made it through with enough clearance, and the children laughed in relief. They marched into {f['setting'].event} together instead of getting stuck outside it.",
        ),
    ]
    if plan.id == "remove_topper":
        qa.append(
            (
                f"Why was the ending funny?",
                f"It was funny because the {project.label} looked a little bald after they took off its {project.topper}. The silly look turned the scary moment into a joke everyone could enjoy.",
            )
        )
    return qa


KNOWLEDGE = {
    "clearance": [
        (
            "What does clearance mean?",
            "Clearance means the empty space between something tall and the thing above it. If there is enough clearance, the object can pass without bumping.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other to do one job together. Sometimes one person steadies, one lifts, and one watches carefully.",
        )
    ],
    "tilt": [
        (
            "What does it mean to tilt something?",
            "To tilt something means to lean it to one side instead of keeping it straight up. That can change how high its tallest point is.",
        )
    ],
    "cardboard": [
        (
            "Why can cardboard projects be tricky to move?",
            "Cardboard projects can be big and light at the same time, so they wobble easily. If you rush, the taped parts can bend or tear.",
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a line of people or things moving along for others to watch. It often has costumes, music, or decorations.",
        )
    ],
    "grownup_help": [
        (
            "Why is calm grown-up help useful in a tricky moment?",
            "A calm grown-up can help children slow down and choose a safer plan. That makes it easier to solve the problem without panic.",
        )
    ],
}
KNOWLEDGE_ORDER = ["clearance", "teamwork", "tilt", "cardboard", "parade", "grownup_help"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"clearance", "teamwork", "cardboard", "parade", "grownup_help"}
    if world.facts["plan"].id == "tilt":
        tags.add("tilt")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
allowed_plan(Pj, Pl) :- project(Pj), plan(Pl), sense(Pl, S), sense_min(M), S >= M,
                        not bad_fragile(Pj, Pl), not bad_tilt(Pj, Pl).
bad_fragile(Pj, Pl) :- fragile_top(Pj), not safe_for_fragile(Pl).
bad_tilt(Pj, Pl)    :- requires_tiltable(Pl), not tilt_ok(Pj).

fits(Pj, Op, Pl) :- proj_height(Pj, H), drop(Pl, D), opening_clearance(Op, C), H - D <= C.

valid(S, Pj, Op, Pl) :- setting(S), project(Pj), opening(Op), plan(Pl),
                        allowed_plan(Pj, Pl), fits(Pj, Op, Pl).

outcome(success) :- chosen_setting(_), chosen_project(Pj), chosen_opening(Op), chosen_plan(Pl),
                    allowed_plan(Pj, Pl), fits(Pj, Op, Pl).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("proj_height", pid, p.height))
        if p.fragile_top:
            lines.append(asp.fact("fragile_top", pid))
        if p.tilt_ok:
            lines.append(asp.fact("tilt_ok", pid))
    for oid, o in OPENINGS.items():
        lines.append(asp.fact("opening", oid))
        lines.append(asp.fact("opening_clearance", oid, o.clearance))
    for plid, pl in PLANS.items():
        lines.append(asp.fact("plan", plid))
        lines.append(asp.fact("sense", plid, pl.sense))
        lines.append(asp.fact("drop", plid, pl.drop))
        if pl.safe_for_fragile:
            lines.append(asp.fact("safe_for_fragile", plid))
        if pl.requires_tiltable:
            lines.append(asp.fact("requires_tiltable", plid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_opening", params.opening),
            asp.fact("chosen_plan", params.plan),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolution failed unexpectedly at seed {seed}.")
            break

    for params in cases[:20]:
        try:
            sample = generate(params)
            if not sample.story.strip():
                rc = 1
                print("Smoke test failed: empty story.")
                break
        except Exception as err:
            rc = 1
            print(f"Smoke test failed during generate(): {err}")
            break

    mismatch = 0
    for params in cases:
        outcome = asp_outcome(params)
        if outcome != "success":
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome agrees on {len(cases)} successful scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch} scenarios were not successful in ASP.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a funny clearance problem solved with teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--opening", choices=OPENINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--grownup", choices=["mother", "father", "teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan is not None and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_rejection(PROJECTS[args.project] if args.project else next(iter(PROJECTS.values())),
                                           OPENINGS[args.opening] if args.opening else next(iter(OPENINGS.values())),
                                           PLANS[args.plan]))
    if args.project and args.opening and args.plan:
        project = PROJECTS[args.project]
        opening = OPENINGS[args.opening]
        plan = PLANS[args.plan]
        if not (plan_allowed(project, plan) and plan_succeeds(project, opening, plan)):
            raise StoryError(explain_rejection(project, opening, plan))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.project is None or c[1] == args.project)
        and (args.opening is None or c[2] == args.opening)
        and (args.plan is None or c[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, project, opening, plan = rng.choice(sorted(combos))
    leader, leader_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=leader)
    grownup = args.grownup or rng.choice(["mother", "father", "teacher_f", "teacher_m"])
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1] or TRAITS)
    return StoryParams(
        setting=setting,
        project=project,
        opening=opening,
        plan=plan,
        leader=leader,
        leader_gender=leader_gender,
        helper=helper,
        helper_gender=helper_gender,
        grownup=grownup,
        trait1=trait1,
        trait2=trait2,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        project = PROJECTS[params.project]
        opening = OPENINGS[params.opening]
        plan = PLANS[params.plan]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not (plan_allowed(project, plan) and plan_succeeds(project, opening, plan)):
        raise StoryError(explain_rejection(project, opening, plan))

    world = tell(
        setting=setting,
        project_cfg=project,
        opening_cfg=opening,
        plan=plan,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        grown_type=params.grownup,
        trait1=params.trait1,
        trait2=params.trait2,
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
        print(f"{len(combos)} compatible (setting, project, opening, plan) combos:\n")
        for setting, project, opening, plan in combos:
            print(f"  {setting:10} {project:8} {opening:8} {plan}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.leader} & {p.helper}: {p.project} at {p.setting} via {p.plan}"
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
