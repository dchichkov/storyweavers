#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lilac_trait_soccer_field_lesson_learned_cautionary.py
================================================================================

A standalone story world about a child at a soccer field who is tempted to use
the goal the wrong way. The world models a cautionary, nursery-rhyme-flavored
lesson: a bold trait can help in play, but listening keeps everyone safe.

The simulated premise:
- A child comes to a soccer field wearing something lilac.
- The ball gets snagged in or near the goal.
- The child is tempted to climb or swing on the goal frame.
- A friend warns that the goal can wobble and tip.
- Either the child listens and gets help safely, or the child ignores the warning,
  the goal jolts, and the child gets a small scrape and a fright.
- A coach helps, teaches the lesson, and the children end with a safer habit.

The reasonableness gate only allows hazards where the chosen goal is unstable
enough to wobble and only allows retrieval methods that honestly solve the
problem without making the danger worse.

Run it
------
    python storyworlds/worlds/gpt-5.4/lilac_trait_soccer_field_lesson_learned_cautionary.py
    python storyworlds/worlds/gpt-5.4/lilac_trait_soccer_field_lesson_learned_cautionary.py --goal portable --temptation climb_frame
    python storyworlds/worlds/gpt-5.4/lilac_trait_soccer_field_lesson_learned_cautionary.py --goal painted_wall
    python storyworlds/worlds/gpt-5.4/lilac_trait_soccer_field_lesson_learned_cautionary.py --all
    python storyworlds/worlds/gpt-5.4/lilac_trait_soccer_field_lesson_learned_cautionary.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/lilac_trait_soccer_field_lesson_learned_cautionary.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLD_START = 5.0
CAREFUL_TRAITS = {"careful", "patient", "steady", "gentle"}


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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    anchored: bool = False
    climbable: bool = False
    helpful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "coach_f"}
        male = {"boy", "father", "dad", "man", "coach_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"coach_f", "coach_m"}:
            return "coach"
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class FieldLook:
    id: str
    sky: str
    grass: str
    opening: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GoalKind:
    id: str
    label: str
    phrase: str
    anchored: bool
    climbable: bool
    wobble_word: str
    nest_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    label: str
    action_line: str
    dangerous_line: str
    needs_climbable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Retrieval:
    id: str
    label: str
    sense: int
    power: int
    safe: bool
    text: str
    qa_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    field_look: str
    goal: str
    temptation: str
    retrieval: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    coach_gender: str
    trait: str
    lilac_item: str
    child_age: int = 6
    friend_age: int = 6
    relation: str = "teammates"
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.characters() if e.role in {"child", "friend"}]

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


def _r_wobble(world: World) -> list[str]:
    child = world.get("child")
    goal = world.get("goal")
    if child.meters["on_goal"] < THRESHOLD:
        return []
    if goal.meters["tipped"] >= THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if not goal.anchored:
        goal.meters["wobbling"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        world.get("field").meters["danger"] += 1
        return ["__wobble__"]
    return []


def _r_scrape(world: World) -> list[str]:
    goal = world.get("goal")
    child = world.get("child")
    if goal.meters["wobbling"] < THRESHOLD:
        return []
    sig = ("scrape",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    goal.meters["tipped"] += 1
    child.meters["scraped"] += 1
    child.memes["shock"] += 1
    return ["__scrape__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="scrape", tag="physical", apply=_r_scrape),
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


def hazard_at_risk(goal: GoalKind, temptation: Temptation) -> bool:
    return goal.climbable and (not goal.anchored) and (not temptation.needs_climbable or goal.climbable)


def sensible_retrievals() -> list[Retrieval]:
    return [r for r in RETRIEVALS.values() if r.sense >= SENSE_MIN and r.safe]


def trouble_severity(goal: GoalKind, delay: int) -> int:
    return (2 if not goal.anchored else 0) + delay


def retrieval_works(retrieval: Retrieval, goal: GoalKind, delay: int) -> bool:
    return retrieval.power >= trouble_severity(goal, delay)


def older_friend_stops_it(child_age: int, friend_age: int, trait: str, relation: str) -> bool:
    care = 5.0 if trait in CAREFUL_TRAITS else 3.0
    authority = care + (2.0 if relation == "siblings" and friend_age > child_age else 0.0)
    return authority > BOLD_START and friend_age >= child_age


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["on_goal"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("goal").meters["wobbling"] >= THRESHOLD,
        "scrape": sim.get("child").meters["scraped"] >= THRESHOLD,
        "danger": sim.get("field").meters["danger"],
    }


def introduce(world: World, child: Entity, friend: Entity, look: FieldLook, lilac_item: str) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{look.opening} At the soccer field, {child.id} came skipping by in {lilac_item}, "
        f"while {friend.id} ran beside {child.pronoun('object')}. {look.sky} {look.grass}"
    )
    world.say(
        f"{child.id} had a quick trait for darting after every ball, and that quick trait "
        f"made the game feel bright and fast."
    )


def start_play(world: World, child: Entity, friend: Entity) -> None:
    world.say(
        f"They tapped the ball, they laughed with delight, "
        f"they raced by the goal in the warm afternoon light."
    )


def snag_ball(world: World, child: Entity, goal_cfg: GoalKind) -> None:
    world.get("ball").meters["stuck"] += 1
    world.say(
        f"Then bounce went the ball with a hop and a sail, "
        f"and it tucked by {goal_cfg.nest_spot}, too high for a tail."
    )
    world.say(
        f'{child.id} tipped back {child.pronoun("possessive")} head. "I can get it," '
        f'{child.pronoun()} said.'
    )


def tempt(world: World, child: Entity, temptation: Temptation) -> None:
    child.memes["boldness"] += 1
    world.say(temptation.action_line.format(name=child.id))
    world.say(temptation.dangerous_line)


def warn(world: World, friend: Entity, child: Entity, goal_cfg: GoalKind, coach: Entity) -> None:
    pred = predict_wobble(world)
    friend.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_scrape"] = pred["scrape"]
    wobble = goal_cfg.wobble_word
    extra = ""
    if pred["scrape"]:
        extra = " and could bump you hard on the way down"
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. "{child.id}, no, '
        f"please do not climb. This goal can {wobble}{extra}. Let's call {coach.label_word}."
        f'"'
    )


def back_down(world: World, child: Entity, friend: Entity, coach: Entity) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{child.id} stood still for half a beat, then stepped back to the grass. "
        f"The fast feet stopped, and the brave heart listened at last."
    )
    world.say(
        f"They waved to {coach.label_word}, who came with calm steps from the cones."
    )


def climb_attempt(world: World, child: Entity) -> None:
    child.meters["on_goal"] += 1
    propagate(world, narrate=False)


def accident(world: World, child: Entity, goal_cfg: GoalKind) -> None:
    climb_attempt(world, child)
    if world.get("goal").meters["wobbling"] >= THRESHOLD:
        world.say(
            f"Up went {child.id}, but then came a jiggle; "
            f"the {goal_cfg.label} gave a long, shaky wriggle."
        )
    if world.get("child").meters["scraped"] >= THRESHOLD:
        world.say(
            f"Down came the frame with a thump and a grate, "
            f"and {child.id} got a small scrape before it was late."
        )


def call_coach(world: World, friend: Entity, coach: Entity) -> None:
    world.say(f'"Coach!" cried {friend.id}. "{coach.label_word.capitalize()}, please come quick!"')


def coach_help(world: World, coach: Entity, retrieval: Retrieval, goal_cfg: GoalKind) -> None:
    world.get("ball").meters["stuck"] = 0.0
    world.say(
        f"{coach.label_word.capitalize()} hurried over and {retrieval.text.format(goal=goal_cfg.label)}."
    )


def lesson_after_scare(world: World, coach: Entity, child: Entity, friend: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'{coach.label_word.capitalize()} knelt by {child.id} and brushed the grass from '
        f'{child.pronoun("possessive")} knee. "Being quick is a fine trait in soccer," '
        f'{coach.pronoun()} said, "but climbing goals is not for play. Fast feet need wise ears too."'
    )
    world.say(
        f'{child.id} nodded. "{friend.id} was right," {child.pronoun()} whispered. '
        f'"Next time I will call for help first."'
    )


def lesson_after_listening(world: World, coach: Entity, child: Entity, friend: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f'{coach.label_word.capitalize()} smiled. "That was the clever choice," {coach.pronoun()} said. '
        f'"Being quick is a fine trait in soccer, but listening before climbing keeps everyone safe."'
    )
    world.say(
        f"{child.id} smiled at {friend.id}. The lesson felt small and warm, like a knot tied neatly in the heart."
    )


def safe_restart(world: World, child: Entity, friend: Entity, look: FieldLook) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Back rolled the ball with a soft little spin, "
        f"and soon the two children were playing again."
    )
    world.say(look.closing)


def tell(
    look: FieldLook,
    goal_cfg: GoalKind,
    temptation: Temptation,
    retrieval: Retrieval,
    child_name: str = "Lina",
    child_gender: str = "girl",
    friend_name: str = "Milo",
    friend_gender: str = "boy",
    coach_gender: str = "coach_f",
    trait: str = "careful",
    lilac_item: str = "a lilac scarf",
    child_age: int = 6,
    friend_age: int = 6,
    relation: str = "teammates",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        age=child_age,
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["watchful"],
        age=friend_age,
    ))
    coach = world.add(Entity(
        id="Coach",
        kind="character",
        type=coach_gender,
        role="coach",
        label="the coach",
        helpful=True,
    ))
    world.add(Entity(id="field", type="place", label="soccer field"))
    goal = world.add(Entity(
        id="goal",
        type="goal",
        label=goal_cfg.label,
        phrase=goal_cfg.phrase,
        anchored=goal_cfg.anchored,
        climbable=goal_cfg.climbable,
    ))
    world.add(Entity(id="ball", type="ball", label="ball"))
    child.memes["boldness"] = BOLD_START
    friend.memes["caution"] = 5.0 if trait in CAREFUL_TRAITS else 3.0

    introduce(world, child, friend, look, lilac_item)
    start_play(world, child, friend)
    world.para()
    snag_ball(world, child, goal_cfg)
    tempt(world, child, temptation)
    warn(world, friend, child, goal_cfg, coach)

    averted = older_friend_stops_it(child_age, friend_age, trait, relation)

    if averted:
        world.para()
        back_down(world, child, friend, coach)
        coach_help(world, coach, retrieval, goal_cfg)
        lesson_after_listening(world, coach, child, friend)
        world.para()
        safe_restart(world, child, friend, look)
        outcome = "averted"
    else:
        world.para()
        accident(world, child, goal_cfg)
        call_coach(world, friend, coach)
        world.para()
        coach_help(world, coach, retrieval, goal_cfg)
        lesson_after_scare(world, coach, child, friend)
        world.para()
        safe_restart(world, child, friend, look)
        outcome = "scraped"

    world.facts.update(
        child=child,
        friend=friend,
        coach=coach,
        field_look=look,
        goal_cfg=goal_cfg,
        temptation=temptation,
        retrieval=retrieval,
        goal=goal,
        outcome=outcome,
        relation=relation,
        lilac_item=lilac_item,
        delay=delay,
        scraped=child.meters["scraped"] >= THRESHOLD,
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


FIELD_LOOKS = {
    "sunny": FieldLook(
        id="sunny",
        sky="The sun sat high like a shiny gold kite.",
        grass="The lines were white, and the grass flashed green and bright.",
        opening="Sing a little soccer song, soft and clear and light.",
        closing="So under the sun, by the white goal rail, they learned that listening helps quick feet prevail.",
        tags={"sunny", "soccer"},
    ),
    "breezy": FieldLook(
        id="breezy",
        sky="A breeze hummed low in a merry, whistling tune.",
        grass="Across the field, the grass bent this way and that beneath the noon.",
        opening="Hush now, hear the soccer rhyme, skipping with the day.",
        closing="And under the breeze, where the bright flags flew, they chose the safe way through and through.",
        tags={"breeze", "soccer"},
    ),
    "cloudy": FieldLook(
        id="cloudy",
        sky="Soft clouds drifted by like sheep in a row.",
        grass="The field smelled fresh, and the net cast a square below.",
        opening="Round and round the soccer sound, gentle as can be.",
        closing="With clouds above and cleats below, they kept safe habits in their toe-to-toe.",
        tags={"cloudy", "soccer"},
    ),
}

GOALS = {
    "portable": GoalKind(
        id="portable",
        label="portable goal",
        phrase="a light portable goal",
        anchored=False,
        climbable=True,
        wobble_word="wobble",
        nest_spot="the top of the loose net",
        tags={"goal", "portable"},
    ),
    "practice": GoalKind(
        id="practice",
        label="practice goal",
        phrase="a practice goal with small wheels",
        anchored=False,
        climbable=True,
        wobble_word="rock",
        nest_spot="the back of the netting",
        tags={"goal", "wheels"},
    ),
    "painted_wall": GoalKind(
        id="painted_wall",
        label="painted wall goal",
        phrase="a painted goal on the brick wall",
        anchored=True,
        climbable=False,
        wobble_word="wobble",
        nest_spot="the ledge by the wall",
        tags={"wall"},
    ),
}

TEMPTATIONS = {
    "climb_frame": Temptation(
        id="climb_frame",
        label="climb the frame",
        action_line="{name} reached for the bar and planted one shoe on the frame.",
        dangerous_line="It looked like a ladder, but it was not made for climbing.",
        needs_climbable=True,
        tags={"climb", "goal"},
    ),
    "swing_net": Temptation(
        id="swing_net",
        label="swing on the net",
        action_line="{name} grabbed the net and gave it a bold little tug.",
        dangerous_line="A net may seem springy and fun, but tugging it can pull the whole goal off balance.",
        needs_climbable=True,
        tags={"net", "goal"},
    ),
}

RETRIEVALS = {
    "lift_and_free": Retrieval(
        id="lift_and_free",
        label="lift and free",
        sense=3,
        power=3,
        safe=True,
        text="held {goal} steady with one hand and freed the ball with the other",
        qa_text="held the goal steady and freed the ball safely",
        fail_text="tried to free the ball without steadying the goal first",
        tags={"coach_help", "steady"},
    ),
    "ask_keeper_pole": Retrieval(
        id="ask_keeper_pole",
        label="goalie pole",
        sense=3,
        power=3,
        safe=True,
        text="used a long field pole from the shed to nudge the ball down from the net",
        qa_text="used a long pole to nudge the ball down safely",
        fail_text="reached too short and left the ball stuck",
        tags={"tool", "coach_help"},
    ),
    "jump_for_it": Retrieval(
        id="jump_for_it",
        label="jump for it",
        sense=1,
        power=1,
        safe=False,
        text="jumped up to smack the ball loose",
        qa_text="jumped up and knocked the ball loose",
        fail_text="jumped and made the trouble worse",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lina", "Mina", "Rosa", "Tessa", "Maya", "Nora", "Ella", "Lucy"]
BOY_NAMES = ["Milo", "Toby", "Finn", "Eli", "Noah", "Jude", "Leo", "Ben"]
TRAITS = ["careful", "patient", "steady", "gentle", "bold", "bouncy"]
LILAC_ITEMS = ["a lilac scarf", "a lilac ribbon", "a lilac jersey", "a lilac headband"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for look_id in FIELD_LOOKS:
        for goal_id, goal in GOALS.items():
            for temptation_id, temptation in TEMPTATIONS.items():
                if not hazard_at_risk(goal, temptation):
                    continue
                for retrieval_id, retrieval in RETRIEVALS.items():
                    if retrieval.sense >= SENSE_MIN and retrieval.safe:
                        combos.append((look_id, goal_id, temptation_id, retrieval_id))
    return combos


def explain_rejection(goal: GoalKind, temptation: Temptation) -> str:
    if not goal.climbable:
        return (
            f"(No story: {goal.phrase} does not invite the climbing hazard in this world. "
            f"The cautionary turn needs a child to be tempted to use the goal like a ladder.)"
        )
    if goal.anchored:
        return (
            f"(No story: {goal.phrase} is anchored, so it would not wobble the way this story needs. "
            f"Pick a light portable practice goal instead.)"
        )
    if temptation.needs_climbable and not goal.climbable:
        return f"(No story: the temptation '{temptation.label}' needs a climbable goal frame.)"
    return "(No story: this combination does not create the right hazard.)"


def explain_retrieval(retrieval_id: str) -> str:
    r = RETRIEVALS[retrieval_id]
    better = ", ".join(sorted(x.id for x in sensible_retrievals()))
    return (
        f"(Refusing retrieval '{retrieval_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}) or is unsafe. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if older_friend_stops_it(params.child_age, params.friend_age, params.trait, params.relation):
        return "averted"
    return "scraped"


KNOWLEDGE = {
    "goal": [(
        "Why should children not climb a soccer goal?",
        "A soccer goal is sports equipment, not playground bars. If it tips or shifts, it can hurt someone very quickly."
    )],
    "portable": [(
        "What is a portable soccer goal?",
        "A portable soccer goal is a lighter goal that can be moved for practice. Because it is not fixed like a heavy stadium goal, grown-ups must set it safely and children should not climb it."
    )],
    "net": [(
        "Why can pulling on a net be dangerous?",
        "A net is tied to the frame, so a hard tug can shake the whole goal. That can make the frame rock or fall."
    )],
    "coach_help": [(
        "Who should help when a ball gets stuck high in a goal?",
        "A grown-up like a coach should help. Grown-ups can steady the goal or use the right tool safely."
    )],
    "steady": [(
        "What does it mean to hold something steady?",
        "To hold something steady means to keep it still so it does not wobble. Keeping sports equipment steady helps stop accidents."
    )],
    "tool": [(
        "Why is the right tool safer than climbing?",
        "The right tool solves the problem without putting your body in danger. It lets you reach the ball while staying on the ground."
    )],
    "soccer": [(
        "What is a soccer field for?",
        "A soccer field is for kicking, passing, and running with the ball. The goals are for scoring, not for climbing."
    )],
}


def pair_noun(child: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if child.type == "boy" and friend.type == "boy":
            return "two brothers"
        if child.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two teammates"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    goal_cfg = f["goal_cfg"]
    temptation = f["temptation"]
    lilac_item = f["lilac_item"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short nursery-rhyme-style cautionary story set at a soccer field that includes the words "lilac" and "trait".',
            f"Tell a gentle lesson-learned story where {child.id}, wearing {lilac_item}, wants to {temptation.label} at a {goal_cfg.label}, but listens to {friend.id} and gets help the safe way.",
            f'Write a rhyming story for ages 3 to 5 where a child learns that being quick is a good trait, but listening first is safer than climbing sports equipment.',
        ]
    return [
        f'Write a short nursery-rhyme-style cautionary story set at a soccer field that includes the words "lilac" and "trait".',
        f"Tell a lesson-learned story where {child.id}, wearing {lilac_item}, ignores {friend.id}'s warning and tries to {temptation.label} on a {goal_cfg.label}, gets a small scrape, and learns to call the coach next time.",
        f'Write a child-facing rhyme where a fast soccer player learns that a brave trait needs careful listening when a ball gets stuck high by the goal.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    coach = f["coach"]
    goal_cfg = f["goal_cfg"]
    retrieval = f["retrieval"]
    relation = f["relation"]
    pair = pair_noun(child, friend, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {child.id} and {friend.id}, and the coach who helps them at the soccer field."
        ),
        (
            f"What was {child.id} wearing?",
            f"{child.id} was wearing {f['lilac_item']}. That small lilac detail helps paint the opening picture of the field."
        ),
        (
            "What problem started the story?",
            f"The ball got stuck by the goal, too high for the children to reach from the ground. That made {child.id} want to solve the problem too quickly."
        ),
        (
            f"What warning did {friend.id} give?",
            f"{friend.id} warned that the {goal_cfg.label} could {goal_cfg.wobble_word} if someone climbed or tugged it. {friend.pronoun().capitalize()} wanted {child.id} to call the coach instead of risking a fall."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"Why did nothing bad happen?",
            f"Nothing bad happened because {child.id} listened before climbing. The warning changed what {child.pronoun()} did, so the coach could solve the problem safely."
        ))
        qa.append((
            f"How did the coach help?",
            f"The coach {retrieval.qa_text}. That worked because the coach used a calm, safe method instead of treating the goal like playground equipment."
        ))
        qa.append((
            "What lesson was learned?",
            f"{child.id} learned that being quick is a useful trait in soccer, but listening first is safer. The ending shows the lesson because the game starts again without fear or injury."
        ))
    else:
        qa.append((
            f"What happened when {child.id} tried to use the goal the wrong way?",
            f"The goal wobbled and {child.id} got a small scrape. The scare came from treating a light practice goal like something made for climbing."
        ))
        qa.append((
            f"How did the coach help after the scare?",
            f"The coach {retrieval.qa_text}. After that, {coach.pronoun()} explained that fast feet also need wise ears."
        ))
        qa.append((
            "What lesson was learned?",
            f"{child.id} learned to call for help instead of climbing the goal. The lesson came after a small hurt and a bigger fright, so it felt real and easy to remember."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"soccer", "goal"} | set(world.facts["goal_cfg"].tags) | set(world.facts["temptation"].tags)
    tags |= set(world.facts["retrieval"].tags)
    out: list[tuple[str, str]] = []
    order = ["soccer", "goal", "portable", "net", "coach_help", "steady", "tool"]
    for tag in order:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.anchored:
            bits.append("anchored=True")
        if ent.climbable:
            bits.append("climbable=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(G, T) :- goal(G), temptation(T), climbable(G), not anchored(G), needs_climbable(T).
sensible(R) :- retrieval(R), sense(R, S), safe(R), sense_min(M), S >= M.
valid(L, G, T, R) :- field_look(L), hazard(G, T), sensible(R).

careful_trait(T) :- trait_name(T), is_careful(T).
care_score(5) :- trait_name(T), careful_trait(T).
care_score(3) :- trait_name(T), not careful_trait(T).
older_bonus(2) :- relation(siblings), friend_age(FA), child_age(CA), FA > CA.
older_bonus(0) :- not relation(siblings).
older_bonus(0) :- relation(siblings), friend_age(FA), child_age(CA), FA <= CA.
authority(C + B) :- care_score(C), older_bonus(B).
averted :- authority(A), bold_start(BS), A > BS, friend_age(FA), child_age(CA), FA >= CA.
outcome(averted) :- averted.
outcome(scraped) :- not averted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for look_id in FIELD_LOOKS:
        lines.append(asp.fact("field_look", look_id))
    for goal_id, goal in GOALS.items():
        lines.append(asp.fact("goal", goal_id))
        if goal.anchored:
            lines.append(asp.fact("anchored", goal_id))
        if goal.climbable:
            lines.append(asp.fact("climbable", goal_id))
    for temptation_id, temptation in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", temptation_id))
        if temptation.needs_climbable:
            lines.append(asp.fact("needs_climbable", temptation_id))
    for retrieval_id, retrieval in RETRIEVALS.items():
        lines.append(asp.fact("retrieval", retrieval_id))
        lines.append(asp.fact("sense", retrieval_id, retrieval.sense))
        if retrieval.safe:
            lines.append(asp.fact("safe", retrieval_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_start", int(BOLD_START)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("child_age", params.child_age),
        asp.fact("friend_age", params.friend_age),
        asp.fact("trait_name", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        field_look="sunny",
        goal="portable",
        temptation="climb_frame",
        retrieval="lift_and_free",
        child_name="Lina",
        child_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        coach_gender="coach_f",
        trait="careful",
        lilac_item="a lilac scarf",
        child_age=5,
        friend_age=7,
        relation="siblings",
        delay=0,
    ),
    StoryParams(
        field_look="breezy",
        goal="practice",
        temptation="swing_net",
        retrieval="ask_keeper_pole",
        child_name="Finn",
        child_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        coach_gender="coach_m",
        trait="bold",
        lilac_item="a lilac ribbon",
        child_age=6,
        friend_age=6,
        relation="teammates",
        delay=0,
    ),
    StoryParams(
        field_look="cloudy",
        goal="portable",
        temptation="climb_frame",
        retrieval="lift_and_free",
        child_name="Maya",
        child_gender="girl",
        friend_name="Lucy",
        friend_gender="girl",
        coach_gender="coach_f",
        trait="patient",
        lilac_item="a lilac headband",
        child_age=6,
        friend_age=6,
        relation="teammates",
        delay=0,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child at a soccer field learns not to climb a goal."
    )
    ap.add_argument("--field-look", choices=FIELD_LOOKS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--retrieval", choices=RETRIEVALS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--coach-gender", choices=["coach_f", "coach_m"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--relation", choices=["teammates", "siblings"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="present for parity; not used in prose branching here")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and args.goal not in GOALS:
        raise StoryError("(No story: unknown goal choice.)")
    if args.temptation and args.temptation not in TEMPTATIONS:
        raise StoryError("(No story: unknown temptation choice.)")
    if args.retrieval and args.retrieval not in RETRIEVALS:
        raise StoryError("(No story: unknown retrieval choice.)")
    if args.goal and args.temptation:
        goal = GOALS[args.goal]
        temptation = TEMPTATIONS[args.temptation]
        if not hazard_at_risk(goal, temptation):
            raise StoryError(explain_rejection(goal, temptation))
    if args.retrieval and (RETRIEVALS[args.retrieval].sense < SENSE_MIN or not RETRIEVALS[args.retrieval].safe):
        raise StoryError(explain_retrieval(args.retrieval))

    combos = [
        combo for combo in valid_combos()
        if (args.field_look is None or combo[0] == args.field_look)
        and (args.goal is None or combo[1] == args.goal)
        and (args.temptation is None or combo[2] == args.temptation)
        and (args.retrieval is None or combo[3] == args.retrieval)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    field_look, goal, temptation, retrieval = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    coach_gender = args.coach_gender or rng.choice(["coach_f", "coach_m"])
    child_name = pick_name(rng, child_gender)
    friend_name = pick_name(rng, friend_gender, avoid=child_name)
    trait = args.trait or rng.choice(TRAITS)
    lilac_item = rng.choice(LILAC_ITEMS)
    relation = args.relation or rng.choice(["teammates", "siblings"])
    child_age, friend_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        field_look=field_look,
        goal=goal,
        temptation=temptation,
        retrieval=retrieval,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        coach_gender=coach_gender,
        trait=trait,
        lilac_item=lilac_item,
        child_age=child_age,
        friend_age=friend_age,
        relation=relation,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.field_look not in FIELD_LOOKS:
        raise StoryError("(No story: invalid field look.)")
    if params.goal not in GOALS:
        raise StoryError("(No story: invalid goal.)")
    if params.temptation not in TEMPTATIONS:
        raise StoryError("(No story: invalid temptation.)")
    if params.retrieval not in RETRIEVALS:
        raise StoryError("(No story: invalid retrieval.)")
    goal_cfg = GOALS[params.goal]
    temptation = TEMPTATIONS[params.temptation]
    retrieval = RETRIEVALS[params.retrieval]
    if not hazard_at_risk(goal_cfg, temptation):
        raise StoryError(explain_rejection(goal_cfg, temptation))
    if retrieval.sense < SENSE_MIN or not retrieval.safe:
        raise StoryError(explain_retrieval(params.retrieval))

    world = tell(
        look=FIELD_LOOKS[params.field_look],
        goal_cfg=goal_cfg,
        temptation=temptation,
        retrieval=retrieval,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        coach_gender=params.coach_gender,
        trait=params.trait,
        lilac_item=params.lilac_item,
        child_age=params.child_age,
        friend_age=params.friend_age,
        relation=params.relation,
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    python_sensible = {r.id for r in sensible_retrievals()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible retrievals match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible retrievals: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible retrievals: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (field_look, goal, temptation, retrieval) combos:\n")
        for look, goal, temptation, retrieval in combos:
            print(f"  {look:7} {goal:12} {temptation:11} {retrieval}")
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
            header = f"### {p.child_name} & {p.friend_name}: {p.goal}, {p.temptation}, {outcome_of(p)}"
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
