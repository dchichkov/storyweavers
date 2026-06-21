#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fielder_year_probation_inner_monologue_comedy.py
============================================================================

A standalone storyworld about a child baseball fielder starting a new year while
on silly-team probation. The world models a simple comedy premise with inner
monologue: a child wants to prove they can focus, a goofy temptation returns, a
play goes wobbly, and the child fixes the mess by choosing honesty and teamwork.

Run it
------
    python storyworlds/worlds/gpt-5.4/fielder_year_probation_inner_monologue_comedy.py
    python storyworlds/worlds/gpt-5.4/fielder_year_probation_inner_monologue_comedy.py --reason mascot_hat
    python storyworlds/worlds/gpt-5.4/fielder_year_probation_inner_monologue_comedy.py --challenge fly_ball
    python storyworlds/worlds/gpt-5.4/fielder_year_probation_inner_monologue_comedy.py --all
    python storyworlds/worlds/gpt-5.4/fielder_year_probation_inner_monologue_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fielder_year_probation_inner_monologue_comedy.py --verify
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
RESPONSIBLE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "coach_f"}
        male = {"boy", "father", "man", "coach_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Reason:
    id: str
    label: str
    what: str
    memory: str
    ban: str
    temptation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    action: str
    mishap: str
    recover: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    text: str
    qa_text: str
    responsible: int
    power: int
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


def _r_distraction(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["bobble"] < THRESHOLD:
        return []
    sig = ("distraction", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["panic"] += 1
    hero.memes["embarrassment"] += 1
    world.get("coach").memes["concern"] += 1
    return ["__bobble__"]


def _r_honesty(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["honesty"] < THRESHOLD:
        return []
    sig = ("honesty", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    world.get("coach").memes["trust"] += 1
    hero.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="distraction", tag="social", apply=_r_distraction),
    Rule(name="honesty", tag="social", apply=_r_honesty),
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
        for sent in produced:
            world.say(sent)
    return produced


def responsible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.responsible >= RESPONSIBLE_MIN]


def challenge_needs_fix(challenge: Challenge, fix: Fix) -> bool:
    return fix.power >= challenge.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for role_id in ROLES:
        for reason_id in REASONS:
            for challenge_id, challenge in CHALLENGES.items():
                if any(challenge_needs_fix(challenge, fix) for fix in responsible_fixes()):
                    combos.append((role_id, reason_id, challenge_id))
    return combos


def explain_fix_rejection(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in responsible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it is too irresponsible for this world "
        f"(responsible={fix.responsible} < {RESPONSIBLE_MIN}). "
        f"Try one of: {better}.)"
    )


def explain_combo_rejection() -> str:
    return "(No valid combination matches the given options.)"


def prediction(world: World, challenge: Challenge) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["bobble"] += 1
    sim.get("play").meters["severity"] = float(challenge.severity)
    propagate(sim, narrate=False)
    return {
        "panic": hero.memes["panic"],
        "bobble": hero.meters["bobble"],
    }


def intro(world: World, role_name: str, year_word: str) -> None:
    hero = world.get("hero")
    coach = world.get("coach")
    team = world.facts["team"]
    world.say(
        f"This year, {hero.id} trotted onto the little baseball field as {team} team's "
        f"{role_name}. {coach.id} called {hero.pronoun('object')} a brave little fielder, "
        f"which made {hero.id}'s sneakers feel suddenly much bigger."
    )
    world.say(
        f'Inside {hero.pronoun("possessive")} head, a tiny drum started to tap: '
        f'"New {year_word}, new me. Please let my glove act like a glove and not a lunch tray."'
    )


def memory(world: World, reason: Reason) -> None:
    hero = world.get("hero")
    coach = world.get("coach")
    hero.memes["embarrassment"] += 1
    world.say(
        f"Last season, {reason.memory} So {coach.id} had put {hero.pronoun('object')} on "
        f"{reason.ban} probation for the first game."
    )
    world.say(
        f'Inside {hero.pronoun("possessive")} head, another voice groaned, '
        f'"Yes, yes, I remember. Comedy and baseball are not always best friends."'
    )


def setup_temptation(world: World, reason: Reason) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["tempted"] += 1
    world.say(
        f"Even before warm-ups finished, {helper.id} wiggled {reason.what} at the fence and grinned. "
        f'"Want it back?" {helper.pronoun()} whispered. "{reason.temptation}"'
    )
    world.say(
        f'Inside {hero.pronoun("possessive")} head: "No. Absolutely not. Maybe a tiny no with sparkles on it. '
        f'But still no."'
    )


def warn(world: World, challenge: Challenge) -> None:
    hero = world.get("hero")
    coach = world.get("coach")
    pred = prediction(world, challenge)
    world.facts["predicted_panic"] = pred["panic"]
    world.say(
        f'{coach.id} pointed to the grass. "Eyes up, knees bent, ready hands," {coach.pronoun()} said. '
        f'{hero.id} nodded hard enough to wobble {hero.pronoun("possessive")} cap.'
    )
    if pred["panic"] >= THRESHOLD:
        world.say(
            f'Inside {hero.pronoun("possessive")} head: "Good plan. Very normal plan. '
            f'Nothing silly will happen now, which is exactly when silly things usually happen."'
        )


def mishap(world: World, challenge: Challenge, reason: Reason) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    play = world.get("play")
    hero.meters["bobble"] += 1
    play.meters["severity"] = float(challenge.severity)
    propagate(world, narrate=False)
    world.say(
        f"Then came {challenge.label}. {challenge.action}"
    )
    world.say(
        f"{hero.id} took one proud step, glanced at {helper.id}'s silly {reason.what}, and {challenge.mishap}"
    )
    world.say(
        f'Inside {hero.pronoun("possessive")} head: "Oh, wonderful. My body has turned into a bag of noodles in cleats."'
    )


def fix_scene(world: World, challenge: Challenge, fix: Fix) -> bool:
    hero = world.get("hero")
    coach = world.get("coach")
    play = world.get("play")
    enough = challenge_needs_fix(challenge, fix)
    if fix.id == "admit_and_hustle":
        hero.memes["honesty"] += 1
        propagate(world, narrate=False)
    if enough:
        play.meters["saved"] += 1
        world.say(
            f"But then {fix.text} {challenge.recover}"
        )
        world.say(
            f'{coach.id} blinked once, then laughed. "That is the kind of rescue I like," '
            f'{coach.pronoun()} said.'
        )
    else:
        play.meters["missed"] += 1
        world.say(
            f"{fix.text} But it was not enough, and the runners kept going while everyone chased the ball."
        )
        world.say(
            f'{hero.id} stood with hot cheeks, thinking, "Well. That was a parade of bad ideas."'
        )
    return enough


def resolution(world: World, reason: Reason, fix: Fix, success: bool) -> None:
    hero = world.get("hero")
    coach = world.get("coach")
    helper = world.get("helper")
    if success:
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        hero.memes["lesson"] += 1
        world.say(
            f"After the inning, {hero.id} walked over and handed {reason.what} back to {helper.id}. "
            f'"Keep it off the field," {hero.pronoun()} said, sounding almost as tall as the backstop.'
        )
        world.say(
            f'{coach.id} tapped the brim of {hero.pronoun("possessive")} cap. '
            f'"Probation over," {coach.pronoun()} said. "You made one bobble, then one smart choice."'
        )
        world.say(
            f'Inside {hero.pronoun("possessive")} head: "Probation over! I would like to thank my glove, '
            f'my legs, and the excellent idea of not being ridiculous."'
        )
    else:
        hero.memes["lesson"] += 1
        world.say(
            f"After the inning, {coach.id} knelt beside {hero.id}. "
            f'"Tomorrow is another day to be a steadier fielder," {coach.pronoun()} said gently.'
        )
        world.say(
            f"{hero.id} sniffed, handed {reason.what} back to {helper.id}, and nodded. "
            f"{hero.pronoun().capitalize()} did not feel grand, but {hero.pronoun()} did feel wiser."
        )
        world.say(
            f'Inside {hero.pronoun("possessive")} head: "Next time I will keep my eyes on the ball '
            f'and my comedy in my pocket."'
        )
    world.facts["probation_over"] = success
    world.facts["used_fix"] = fix


def tell(
    role_id: str,
    reason: Reason,
    challenge: Challenge,
    fix: Fix,
    hero_name: str,
    hero_type: str,
    coach_name: str,
    coach_type: str,
    helper_name: str,
    helper_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    coach = world.add(Entity(id=coach_name, kind="character", type=coach_type, role="coach"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="play", kind="thing", type="play", label="the play"))

    hero.memes["hope"] = 1
    hero.memes["trust"] = 1
    world.facts["team"] = ROLES[role_id]["team"]
    world.facts["role_label"] = ROLES[role_id]["label"]
    world.facts["year_word"] = ROLES[role_id]["year_word"]
    world.facts["reason"] = reason
    world.facts["challenge"] = challenge
    world.facts["fix"] = fix
    world.facts["hero"] = hero
    world.facts["coach"] = coach
    world.facts["helper"] = helper

    intro(world, ROLES[role_id]["label"], ROLES[role_id]["year_word"])
    memory(world, reason)

    world.para()
    setup_temptation(world, reason)
    warn(world, challenge)

    world.para()
    mishap(world, challenge, reason)

    world.para()
    success = fix_scene(world, challenge, fix)
    resolution(world, reason, fix, success)

    world.facts["success"] = success
    world.facts["bobble"] = hero.meters["bobble"] >= THRESHOLD
    world.facts["honest"] = hero.memes["honesty"] >= THRESHOLD
    return world


ROLES = {
    "left_field": {"label": "left fielder", "team": "the Pepper Pops", "year_word": "year"},
    "center_field": {"label": "center fielder", "team": "the Moon Beans", "year_word": "year"},
    "right_field": {"label": "right fielder", "team": "the Jelly Stars", "year_word": "year"},
}

REASONS = {
    "mascot_hat": Reason(
        id="mascot_hat",
        label="mascot hat",
        what="the giant chicken hat",
        memory="the hat slid over one eye and {hero} waved at a butterfly instead of the warm-up toss".replace("{hero}", "the child"),
        ban="chicken-hat",
        temptation="One tiny cluck for luck.",
        tags={"hat", "baseball", "probation"},
    ),
    "kazoo": Reason(
        id="kazoo",
        label="kazoo",
        what="the shiny kazoo",
        memory="a loud toot came out during a pitch, and three children laughed so hard that even the umpire coughed into a smile",
        ban="kazoo",
        temptation="Just one heroic parade note.",
        tags={"kazoo", "music", "probation"},
    ),
    "sunflower": Reason(
        id="sunflower",
        label="sunflower seeds",
        what="the striped bag of sunflower seeds",
        memory="the child tried to spit shells into a cup, missed badly, and turned the bench into crunchy confetti",
        ban="snack-bench",
        temptation="Only one thoughtful seed. A planning seed.",
        tags={"snack", "seeds", "probation"},
    ),
}

CHALLENGES = {
    "fly_ball": Challenge(
        id="fly_ball",
        label="a high fly ball",
        action="The batter popped the ball so high that it seemed to stop and read the clouds.",
        mishap="the ball kissed the top of the glove and bounced away into the grass",
        recover="The ball thumped into the glove at last, and the runners froze long enough for the team to laugh and clap.",
        severity=2,
        tags={"fly_ball", "catch"},
    ),
    "grounder": Challenge(
        id="grounder",
        label="a skittering grounder",
        action="The batter chopped the ball low, and it came hopping like a very rude rabbit.",
        mishap="the ball squeezed under one shoe and shot behind the snack cooler",
        recover="The throw wobbled, but it reached first base in time by the width of a shoelace.",
        severity=1,
        tags={"grounder", "throw"},
    ),
    "relay": Challenge(
        id="relay",
        label="a long relay play",
        action="A runner tore around the bases while the ball rolled all the way to the fence.",
        mishap="the pickup fumbled once, then twice, and the cap spun clear around",
        recover="The relay finally zipped home, and the runner stopped at third instead of dancing home.",
        severity=3,
        tags={"relay", "teamwork"},
    ),
}

FIXES = {
    "call_partner": Fix(
        id="call_partner",
        label="call to teammate",
        text='{hero} cupped both hands and shouted, "Backup!"'.replace("{hero}", "The child"),
        qa_text="called to a teammate for backup and kept the play alive",
        responsible=2,
        power=1,
        tags={"help", "teamwork"},
    ),
    "admit_and_hustle": Fix(
        id="admit_and_hustle",
        label="admit and hustle",
        text='{hero} blurted, "My fault!" and sprinted after the ball instead of pretending nothing happened.'.replace("{hero}", "The child"),
        qa_text="admitted the mistake and hustled after the ball",
        responsible=3,
        power=3,
        tags={"honesty", "hustle"},
    ),
    "coach_signal": Fix(
        id="coach_signal",
        label="listen for coach",
        text='{hero} heard the coach yell, "Set your feet!" and obeyed at once.'.replace("{hero}", "The child"),
        qa_text="listened to the coach and set their feet before throwing",
        responsible=2,
        power=2,
        tags={"coach", "focus"},
    ),
    "joke_bow": Fix(
        id="joke_bow",
        label="take a joke bow",
        text="The child made a grand bow to the crowd, which sadly did not make the baseball easier to catch.",
        qa_text="took a silly bow instead of fixing the play",
        responsible=1,
        power=0,
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Eli", "Theo"]
COACH_NAMES = {
    "coach_f": ["Coach May", "Coach Nina", "Coach June"],
    "coach_m": ["Coach Ray", "Coach Ben", "Coach Tom"],
}
HELPER_NAMES = ["Pip", "Tess", "Milo", "June", "Kit", "Ruby"]


@dataclass
class StoryParams:
    role: str
    reason: str
    challenge: str
    fix: str
    hero_name: str
    hero_type: str
    coach_name: str
    coach_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "baseball": [
        ("What does a fielder do in baseball?",
         "A fielder watches the ball, runs to it, and helps stop runners by catching or throwing. Fielders need ready hands and careful eyes.")
    ],
    "probation": [
        ("What does probation mean in this story?",
         "Here, probation means a short time when the child has to prove they can follow the rules. It is a chance to do better, not a forever punishment.")
    ],
    "fly_ball": [
        ("What is a fly ball?",
         "A fly ball is a baseball hit high into the air. A fielder has to look up, move under it, and catch it if they can.")
    ],
    "grounder": [
        ("What is a grounder?",
         "A grounder is a ball that bounces or rolls along the ground. It can hop in funny ways, so fielders have to stay low and ready.")
    ],
    "relay": [
        ("What is a relay play?",
         "A relay play is when teammates pass the ball from one player to another to move it faster across the field. It works best when everyone pays attention.")
    ],
    "honesty": [
        ("Why is it good to admit a mistake in a game?",
         "Admitting a mistake helps everyone fix the problem faster. It also shows you can be trusted, even after something goes wrong.")
    ],
    "teamwork": [
        ("Why do teammates call for backup?",
         "They call for backup so someone else can help when a ball gets away. Teamwork gives the team another chance to stop the play.")
    ],
    "focus": [
        ("Why does focus matter in sports?",
         "Focus helps your eyes, hands, and feet work together. When your mind wanders, even an easy play can turn tricky.")
    ],
}
KNOWLEDGE_ORDER = ["baseball", "probation", "fly_ball", "grounder", "relay", "honesty", "teamwork", "focus"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    reason = f["reason"]
    return [
        'Write a short comedy for a 3-to-5-year-old about a baseball fielder starting a new year on probation, and include funny inner monologue.',
        f"Tell a gentle sports story where {hero.id} is on {reason.label} probation, faces {challenge.label}, and learns that a smart choice can fix a wobbly moment.",
        'Write a child-facing story that includes the words "fielder", "year", and "probation", uses inner thoughts, and ends with a warm laugh.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    coach = f["coach"]
    helper = f["helper"]
    challenge = f["challenge"]
    reason = f["reason"]
    fix = f["used_fix"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {hero.id}, a little baseball fielder, along with {coach.id} and {helper.id}. {hero.id} wants to start the year well even though probation is hanging over the first game."),
        ("Why was the child on probation?",
         f"{hero.id} was on probation because last season {reason.memory}. The coach wanted {hero.pronoun('object')} to show better focus before the silly thing came back onto the field."),
        ("What went wrong during the game?",
         f"{challenge.action} Then {hero.id} got distracted and {challenge.mishap}. The trouble came from letting the silly temptation pull {hero.pronoun('possessive')} eyes away from the play."),
    ]
    if f["success"]:
        qa.append((
            "How did the child fix the problem?",
            f"{hero.id} {fix.qa_text}. That choice worked because it turned panic into action and helped the team finish the play."
        ))
        qa.append((
            "Why did the coach end probation?",
            f"{coach.id} ended probation because {hero.id} made a mistake but then handled it responsibly. The coach cared more about honesty and recovery than about being perfect."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with laughter and relief. {hero.id} felt proud because the silly object went away, the play got saved, and probation was over."
        ))
    else:
        qa.append((
            "Did the child solve the problem right away?",
            f"No. {hero.id} tried {fix.qa_text}, but it did not fix the play. Even so, the child learned to keep eyes on the ball and save the jokes for later."
        ))
        qa.append((
            "How did the story end?",
            f"It ended gently, not perfectly. {coach.id} reminded {hero.id} that tomorrow is another day to be a steadier fielder, so the lesson still mattered."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"baseball", "probation", "focus"}
    challenge = world.facts["challenge"]
    fix = world.facts["used_fix"]
    if challenge.id in {"fly_ball", "grounder", "relay"}:
        tags.add(challenge.id)
    if "honesty" in fix.tags:
        tags.add("honesty")
    if "teamwork" in fix.tags or "help" in fix.tags:
        tags.add("teamwork")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        role="left_field",
        reason="mascot_hat",
        challenge="fly_ball",
        fix="admit_and_hustle",
        hero_name="Lily",
        hero_type="girl",
        coach_name="Coach May",
        coach_type="coach_f",
        helper_name="Pip",
        helper_type="boy",
    ),
    StoryParams(
        role="center_field",
        reason="kazoo",
        challenge="grounder",
        fix="coach_signal",
        hero_name="Ben",
        hero_type="boy",
        coach_name="Coach Ray",
        coach_type="coach_m",
        helper_name="Tess",
        helper_type="girl",
    ),
    StoryParams(
        role="right_field",
        reason="sunflower",
        challenge="relay",
        fix="admit_and_hustle",
        hero_name="Zoe",
        hero_type="girl",
        coach_name="Coach Nina",
        coach_type="coach_f",
        helper_name="Milo",
        helper_type="boy",
    ),
    StoryParams(
        role="left_field",
        reason="kazoo",
        challenge="fly_ball",
        fix="call_partner",
        hero_name="Max",
        hero_type="boy",
        coach_name="Coach Tom",
        coach_type="coach_m",
        helper_name="Ruby",
        helper_type="girl",
    ),
]


ASP_RULES = r"""
% valid story ingredients
valid(Role, Reason, Challenge) :-
    role(Role), reason(Reason), challenge(Challenge), some_responsible_fix.

some_responsible_fix :- fix(F), responsible(F, R), responsible_min(M), R >= M.

sensible_fix(F) :- fix(F), responsible(F, R), responsible_min(M), R >= M.
strong_enough(F, C) :- sensible_fix(F), fix_power(F, P), severity(C, S), P >= S.

outcome(contained) :- chosen_fix(F), chosen_challenge(C), strong_enough(F, C).
outcome(bobble_only) :- chosen_fix(F), chosen_challenge(C), not strong_enough(F, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for role_id in ROLES:
        lines.append(asp.fact("role", role_id))
    for reason_id in REASONS:
        lines.append(asp.fact("reason", reason_id))
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        lines.append(asp.fact("severity", challenge_id, challenge.severity))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("responsible", fix_id, fix.responsible))
        lines.append(asp.fact("fix_power", fix_id, fix.power))
    lines.append(asp.fact("responsible_min", RESPONSIBLE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_challenge", params.challenge),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    fix = FIXES[params.fix]
    challenge = CHALLENGES[params.challenge]
    return "contained" if challenge_needs_fix(challenge, fix) else "bobble_only"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "fielder" not in sample.story or "probation" not in sample.story:
        raise StoryError("Smoke test failed: generated story was empty or missed seed words.")
    emit(sample, trace=False, qa=False, header="")


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

    python_fixes = {f.id for f in responsible_fixes()}
    clingo_fixes = set(asp_sensible_fixes())
    if python_fixes == clingo_fixes:
        print(f"OK: sensible fixes match ({sorted(python_fixes)}).")
    else:
        rc = 1
        print("MISMATCH in sensible fixes:")
        print("  clingo:", sorted(clingo_fixes))
        print("  python:", sorted(python_fixes))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy storyworld about a little baseball fielder on probation. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--reason", choices=REASONS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix is not None and FIXES[args.fix].responsible < RESPONSIBLE_MIN:
        raise StoryError(explain_fix_rejection(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.role is None or combo[0] == args.role)
        and (args.reason is None or combo[1] == args.reason)
        and (args.challenge is None or combo[2] == args.challenge)
    ]
    if not combos:
        raise StoryError(explain_combo_rejection())

    role_id, reason_id, challenge_id = rng.choice(sorted(combos))
    challenge = CHALLENGES[challenge_id]

    if args.fix is None:
        options = [fix_id for fix_id, fix in FIXES.items()
                   if fix.responsible >= RESPONSIBLE_MIN]
        fitting = [fix_id for fix_id in options if challenge_needs_fix(challenge, FIXES[fix_id])]
        fix_id = rng.choice(sorted(fitting if fitting else options))
    else:
        fix_id = args.fix

    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    coach_type = rng.choice(["coach_f", "coach_m"])
    coach_name = rng.choice(COACH_NAMES[coach_type])
    helper_type = "boy" if hero_type == "girl" else "girl"
    helper_name = rng.choice(HELPER_NAMES)

    return StoryParams(
        role=role_id,
        reason=reason_id,
        challenge=challenge_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_type=hero_type,
        coach_name=coach_name,
        coach_type=coach_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.role not in ROLES:
        raise StoryError(f"(Unknown role: {params.role})")
    if params.reason not in REASONS:
        raise StoryError(f"(Unknown reason: {params.reason})")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(Unknown challenge: {params.challenge})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if FIXES[params.fix].responsible < RESPONSIBLE_MIN:
        raise StoryError(explain_fix_rejection(params.fix))

    world = tell(
        role_id=params.role,
        reason=REASONS[params.reason],
        challenge=CHALLENGES[params.challenge],
        fix=FIXES[params.fix],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        coach_name=params.coach_name,
        coach_type=params.coach_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (role, reason, challenge) combos:\n")
        for role_id, reason_id, challenge_id in combos:
            print(f"  {role_id:12} {reason_id:12} {challenge_id}")
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
            header = f"### {p.hero_name}: {p.reason} / {p.challenge} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
