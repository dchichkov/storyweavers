#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/theater_problem_solving_comedy.py
============================================================

A standalone story world for tiny, child-facing comedy stories about a theater
problem that gets solved on the fly. Two children are helping with a small stage
show. A silly prop problem pops up just before the curtain opens, a calm helper
suggests a sensible fix, and the performance ends with laughter because the
children turn the mishap into part of the fun.

The world enforces a simple reasonableness rule: each problem has a concrete
need, and only a matching fix can solve it. A drooping cardboard moon needs
support, not glue. A sliding crown needs a tying fix, not a brace. A loose fake
mustache needs stickiness, not a ribbon. The renderer then turns the simulated
state into a complete little story with setup, tension, turn, and ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/theater_problem_solving_comedy.py
    python storyworlds/worlds/gpt-5.4/theater_problem_solving_comedy.py --problem crown_slip
    python storyworlds/worlds/gpt-5.4/theater_problem_solving_comedy.py --fix cardboard_brace
    python storyworlds/worlds/gpt-5.4/theater_problem_solving_comedy.py --all
    python storyworlds/worlds/gpt-5.4/theater_problem_solving_comedy.py --qa
    python storyworlds/worlds/gpt-5.4/theater_problem_solving_comedy.py --verify
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

# Make the shared result containers importable when this script is run directly
# from inside storyworlds/worlds/gpt-5.4/.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher", "director_f"}
        male = {"boy", "father", "man", "director_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"director_f", "director_m"}:
            return "teacher"
        return self.type


@dataclass
class PlayTheme:
    id: str
    stage_place: str
    costume_line: str
    role1: str
    role2: str
    opening_image: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    prop_label: str
    prop_phrase: str
    need: str
    mishap: str
    warning: str
    turn_line: str
    consequence: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    capability: str
    sense: int
    power: int
    apply_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_problem_spreads(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    if not prop or prop.meters["wobble"] < THRESHOLD:
        return out
    sig = ("problem_spreads", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stage = world.entities.get("stage")
    if stage:
        stage.meters["delay"] += 1
    for kid_id in ("lead", "pal"):
        if kid_id in world.entities:
            world.get(kid_id).memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_success_relief(world: World) -> list[str]:
    out: list[str] = []
    prop = world.entities.get("prop")
    if not prop or prop.meters["stable"] < THRESHOLD:
        return out
    sig = ("success_relief", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid_id in ("lead", "pal"):
        if kid_id in world.entities:
            kid = world.get(kid_id)
            kid.memes["relief"] += 1
            kid.memes["confidence"] += 1
    return out


CAUSAL_RULES = [
    Rule("problem_spreads", "physical", _r_problem_spreads),
    Rule("success_relief", "emotional", _r_success_relief),
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


def problem_matches(problem: Problem, fix: Fix) -> bool:
    return problem.need == fix.capability


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def contained(problem: Problem, fix: Fix) -> bool:
    return problem_matches(problem, fix) and fix.power >= problem.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for pid, problem in PROBLEMS.items():
            for fid, fix in FIXES.items():
                if problem_matches(problem, fix) and fix.sense >= SENSE_MIN:
                    combos.append((theme_id, pid, fid))
    return combos


def explain_rejection(problem: Problem, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (f"(No story: {fix.label} is known in the world, but it is too clumsy "
                f"for this theater problem. Pick a calmer backstage fix.)")
    return (f"(No story: {problem.prop_phrase} needs help with {problem.need.replace('_', ' ')}, "
            f"but {fix.label} solves {fix.capability.replace('_', ' ')} instead.)")


def predict_show(world: World, problem: Problem, fix: Fix) -> dict:
    sim = world.copy()
    prop = sim.get("prop")
    prop.meters["wobble"] += 1
    propagate(sim, narrate=False)
    if contained(problem, fix):
        prop.meters["stable"] += 1
        prop.meters["wobble"] = 0.0
        propagate(sim, narrate=False)
    return {
        "delay": sim.get("stage").meters["delay"],
        "solved": sim.get("prop").meters["stable"] >= THRESHOLD,
    }


def introduce(world: World, lead: Entity, pal: Entity, theme: PlayTheme) -> None:
    for kid in (lead, pal):
        kid.memes["joy"] += 1
    world.say(
        f"On Friday afternoon, {lead.id} and {pal.id} hurried into the little theater at school. "
        f"The stage had been turned into {theme.stage_place}, and {theme.opening_image}"
    )
    world.say(
        f'{lead.id} was playing {theme.role1}, and {pal.id} was playing {theme.role2}. '
        f"{theme.costume_line}"
    )


def warmup(world: World, lead: Entity, pal: Entity, helper: Entity) -> None:
    world.say(
        f'They tiptoed, bowed, and whispered their lines while {helper.label_word} '
        f"peeked out from behind the curtain with an encouraging smile."
    )
    world.say("Everything felt ready, or almost ready, which in a theater is not quite the same thing.")


def trouble_appears(world: World, lead: Entity, pal: Entity, problem: Problem) -> None:
    prop = world.get("prop")
    prop.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the silly trouble began. {problem.mishap} {problem.warning}"
    )
    world.say(
        f'{lead.id} blinked. "{problem.turn_line}" {lead.pronoun()} said.'
    )


def react(world: World, lead: Entity, pal: Entity, helper: Entity, problem: Problem, fix: Fix) -> None:
    pred = predict_show(world, problem, fix)
    world.facts["predicted_delay"] = int(pred["delay"])
    pal.memes["care"] += 1
    helper.memes["calm"] += 1
    world.say(
        f'{pal.id} pressed both hands to {pal.pronoun("possessive")} cheeks, then made a little snorty laugh '
        f"because the mishap looked so ridiculous."
    )
    world.say(
        f'"If we do nothing, the show will wobble before it even starts," said the {helper.label_word}. '
        f'"Let us think. We need something for {problem.need.replace("_", " ")}."'
    )


def bad_idea_line(world: World, lead: Entity) -> None:
    world.say(
        f'"I could hold it with my nose," {lead.id} offered. It was a funny idea, but not a useful one.'
    )


def apply_fix(world: World, helper: Entity, problem: Problem, fix: Fix) -> None:
    prop = world.get("prop")
    if contained(problem, fix):
        prop.meters["stable"] += 1
        prop.meters["wobble"] = 0.0
        propagate(world, narrate=False)
        world.say(
            f"The {helper.label_word} reached into the backstage basket and took out {fix.phrase}. "
            f"{fix.apply_text}"
        )
    else:
        prop.meters["wobble"] += 1
        world.get("stage").meters["delay"] += 1
        world.say(
            f"The {helper.label_word} tried {fix.phrase}, but {fix.fail_text}"
        )


def improvise_success(world: World, lead: Entity, pal: Entity, theme: PlayTheme, problem: Problem) -> None:
    lead.memes["brave"] += 1
    pal.memes["playful"] += 1
    audience = world.get("audience")
    audience.memes["laughter"] += 1
    world.say(
        f"When the curtain opened, {lead.id} and {pal.id} stepped out anyway. "
        f"The fix held, so they slipped one tiny joke into the scene about the mischievous prop."
    )
    world.say(
        f"The grown-ups and children in the audience laughed at the right place, not because the show was ruined, "
        f"but because the joke made the mistake feel like part of the play."
    )
    world.say(theme.ending_image)


def improvise_fail(world: World, lead: Entity, pal: Entity, helper: Entity, theme: PlayTheme, problem: Problem) -> None:
    audience = world.get("audience")
    audience.memes["laughter"] += 1
    lead.memes["brave"] += 1
    pal.memes["playful"] += 1
    world.say(
        f"When the curtain opened, {problem.consequence} For one tiny second, everyone froze."
    )
    world.say(
        f"Then {pal.id} whispered a line about the theater having naughty props, and {lead.id} answered with a grand bow. "
        f"The audience burst out laughing, and even the {helper.label_word} had to cover a smile."
    )
    world.say(
        f"The scene was wobblier than planned, but it still ended in applause. {theme.ending_image}"
    )


def closing_lesson(world: World, lead: Entity, pal: Entity, helper: Entity, problem: Problem, fix: Fix, solved: bool) -> None:
    if solved:
        world.say(
            f'Afterward, the {helper.label_word} told them, "The best theater trick is not a magic wand. '
            f'It is a calm brain." {lead.id} and {pal.id} grinned because they knew that was true.'
        )
    else:
        world.say(
            f'Afterward, the {helper.label_word} said, "Even when a plan is imperfect, calm problem solving can still save a scene." '
            f'{lead.id} and {pal.id} nodded, still laughing.'
        )
    world.facts["lesson_text"] = (
        "calm problem solving can save the scene"
        if solved else
        "calm problem solving can rescue even a wobbly scene"
    )


def tell(theme: PlayTheme, problem: Problem, fix: Fix,
         lead_name: str = "Nora", lead_gender: str = "girl",
         pal_name: str = "Ben", pal_gender: str = "boy",
         helper_type: str = "director_f") -> World:
    world = World()
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead"))
    pal = world.add(Entity(id=pal_name, kind="character", type=pal_gender, role="pal"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the teacher"))
    prop = world.add(Entity(id="prop", type="prop", label=problem.prop_label, portable=True))
    stage = world.add(Entity(id="stage", type="stage", label="stage"))
    audience = world.add(Entity(id="audience", type="crowd", label="audience"))

    introduce(world, lead, pal, theme)
    warmup(world, lead, pal, helper)

    world.para()
    trouble_appears(world, lead, pal, problem)
    react(world, lead, pal, helper, problem, fix)
    bad_idea_line(world, lead)

    world.para()
    apply_fix(world, helper, problem, fix)
    solved = world.get("prop").meters["stable"] >= THRESHOLD
    if solved:
        improvise_success(world, lead, pal, theme, problem)
    else:
        improvise_fail(world, lead, pal, helper, theme, problem)

    world.para()
    closing_lesson(world, lead, pal, helper, problem, fix, solved)

    outcome = "solved" if solved else "wobbly"
    world.facts.update(
        theme=theme,
        problem=problem,
        fix=fix,
        lead=lead,
        pal=pal,
        helper=helper,
        prop=prop,
        stage=stage,
        audience=audience,
        solved=solved,
        outcome=outcome,
    )
    return world


THEMES = {
    "castle": PlayTheme(
        "castle",
        "a cardboard castle with silver paper stars",
        "Nora wore a velvet cape, and Ben kept practicing an extra-serious royal bow.",
        "the brave princess",
        "the royal messenger",
        "a paper moon hung over the painted tower",
        "By the end, the theater felt warmer, brighter, and much funnier than it had a few minutes before.",
        tags={"theater", "stage"},
    ),
    "jungle": PlayTheme(
        "jungle",
        "a pretend jungle with painted vines and a drum made from an old box",
        "Mia wore leaf-green slippers, and Theo kept creeping like a tiger who had forgotten how to be scary.",
        "the explorer",
        "the monkey guide",
        "a cardboard sun peeped between the vines",
        "By the end, the little theater sounded full of claps, giggles, and happy feet.",
        tags={"theater", "stage"},
    ),
    "space": PlayTheme(
        "space",
        "a tiny moon base with foil rocks and a window full of paper stars",
        "Ava wore shiny boots, and Max kept saluting as if the whole theater depended on it.",
        "the captain",
        "the moon mechanic",
        "a silver rocket waited beside the curtain",
        "By the end, the theater looked less like a place for worries and more like a place for brave, silly ideas.",
        tags={"theater", "stage"},
    ),
}

PROBLEMS = {
    "crown_slip": Problem(
        "crown_slip",
        "crown",
        "the shiny paper crown",
        "tying",
        "The shiny paper crown slid over one eyebrow and then down to the tip of the nose.",
        "It made the royal scene look more like a sneezing contest.",
        "My crown is trying to escape!",
        "the crown bobbed sideways and nearly covered the princess's eyes",
        severity=2,
        tags={"crown", "costume", "theater"},
    ),
    "mustache_peel": Problem(
        "mustache_peel",
        "mustache",
        "the curly fake mustache",
        "sticking",
        "The curly fake mustache peeled loose at one end and stuck out like a sleepy caterpillar.",
        "Every time someone spoke, it wiggled.",
        "My mustache is laughing at me!",
        "the mustache curled away and bounced when the messenger talked",
        severity=2,
        tags={"mustache", "costume", "theater"},
    ),
    "moon_droop": Problem(
        "moon_droop",
        "moon",
        "the big cardboard moon",
        "supporting",
        "The big cardboard moon bent in the middle and drooped over the tower like a tired pancake.",
        "It looked ready to flop into the castle garden.",
        "The moon looks sleepy!",
        "the moon sagged lower and lower until the audience could not miss it",
        severity=3,
        tags={"moon", "backdrop", "theater"},
    ),
}

FIXES = {
    "ribbon_tie": Fix(
        "ribbon_tie",
        "a ribbon tie",
        "a soft blue ribbon",
        "tying",
        sense=3,
        power=2,
        apply_text="In two quick loops, the crown was snug again instead of sliding around like a silly hat on a windy duck.",
        fail_text="it could not help the problem at all",
        qa_text="used a ribbon to tie the crown in place",
        tags={"ribbon", "problem_solving"},
    ),
    "stage_tape": Fix(
        "stage_tape",
        "stage tape",
        "a little roll of stage tape",
        "sticking",
        sense=3,
        power=2,
        apply_text="A neat hidden strip pressed the mustache flat, and this time it stayed where a mustache ought to stay.",
        fail_text="the prop still would not stay put",
        qa_text="used stage tape to stick the mustache back on",
        tags={"tape", "problem_solving"},
    ),
    "cardboard_brace": Fix(
        "cardboard_brace",
        "a cardboard brace",
        "a stiff strip of cardboard",
        "supporting",
        sense=3,
        power=3,
        apply_text="The brace went behind the moon like a secret little backbone, and the droop stopped at once.",
        fail_text="the wobble kept spreading",
        qa_text="slid a cardboard brace behind the moon to support it",
        tags={"cardboard", "problem_solving"},
    ),
    "glue_blob": Fix(
        "glue_blob",
        "a blob of wet glue",
        "a blob of wet glue",
        "sticking",
        sense=1,
        power=1,
        apply_text="The glue made a shiny mess",
        fail_text="the wet glue only made things slipperier",
        qa_text="smeared on glue",
        tags={"glue", "problem_solving"},
    ),
}


GIRL_NAMES = ["Nora", "Mia", "Ava", "Lily", "Zoe", "Ella", "Ruby", "Clara"]
BOY_NAMES = ["Ben", "Max", "Theo", "Finn", "Sam", "Leo", "Jack", "Owen"]


@dataclass
class StoryParams:
    theme: str
    problem: str
    fix: str
    lead_name: str
    lead_gender: str
    pal_name: str
    pal_gender: str
    helper: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "theater": [
        ("What is a theater?",
         "A theater is a place where people act out stories on a stage for an audience. It often has curtains, costumes, and props.")
    ],
    "stage": [
        ("What is a stage?",
         "A stage is the raised place where actors stand and perform. The audience watches from in front of it.")
    ],
    "prop": [
        ("What is a prop in a play?",
         "A prop is an object used in a play, like a crown, a letter, or a cardboard moon. Props help the story look real or funny.")
    ],
    "problem_solving": [
        ("What does problem solving mean?",
         "Problem solving means noticing what is wrong, thinking carefully, and trying a good fix. It helps people stay calm when something unexpected happens.")
    ],
    "audience": [
        ("Who is the audience in a theater?",
         "The audience is the group of people who sit and watch the play. They clap, laugh, and listen to the story.")
    ],
    "ribbon": [
        ("What can a ribbon do besides decorate something?",
         "A ribbon can also tie something gently in place. That can help a light costume piece stop slipping.")
    ],
    "tape": [
        ("What does tape do?",
         "Tape helps hold things in place by sticking them down. In a play, grown-ups may use a little tape to fix a loose prop.")
    ],
    "cardboard": [
        ("Why is cardboard useful for making props?",
         "Cardboard is light, easy to cut, and easy to paint. It can also help support a paper prop when the prop needs a stiffer back.")
    ],
    "glue": [
        ("Why can wet glue be a poor quick fix during a show?",
         "Wet glue can stay slippery and messy before it dries. A backstage fix often needs to work right away.")
    ],
}
KNOWLEDGE_ORDER = ["theater", "stage", "prop", "problem_solving", "audience",
                   "ribbon", "tape", "cardboard", "glue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    problem = f["problem"]
    fix = f["fix"]
    outcome = f["outcome"]
    base = (
        f'Write a funny story for a 3-to-5-year-old that includes the word "theater" '
        f"and centers on children solving a backstage problem before a play begins."
    )
    if outcome == "solved":
        return [
            base,
            f"Tell a comedy story where {problem.prop_phrase} causes trouble in a small theater, "
            f"but a calm helper and two children solve it with {fix.label}.",
            f"Write a gentle problem-solving story set in {theme.stage_place}, where a silly prop mishap becomes a joke and the audience laughs happily.",
        ]
    return [
        base,
        f"Tell a comedy story where the children try to fix {problem.prop_phrase}, the fix is not perfect, "
        f"and they still save the play by staying calm and joking together.",
        "Write a child-facing theater story where a mistake becomes part of the fun because the characters keep thinking instead of panicking.",
    ]


def pair_noun(lead: Entity, pal: Entity) -> str:
    if lead.type == "girl" and pal.type == "girl":
        return "two friends"
    if lead.type == "boy" and pal.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    pal = f["pal"]
    helper = f["helper"]
    theme = f["theme"]
    problem = f["problem"]
    fix = f["fix"]
    solved = f["solved"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {pair_noun(lead, pal)}, {lead.id} and {pal.id}, helping in a little theater play with their {helper.label_word}."),
        ("Where does the story happen?",
         f"It happens in a little theater at school, where the stage has been turned into {theme.stage_place}. That setting makes the prop problem matter right before the curtain opens."),
        ("What problem happened before the play?",
         f"{problem.mishap} {problem.warning} The trouble mattered because it could spoil the scene if nobody fixed it."),
        ("Why did the children stop and think instead of rushing on?",
         f"They saw that the prop problem could delay or wobble the show. So they paused to think about what kind of help the prop really needed."),
    ]
    if solved:
        qa.append((
            f"How did they solve the problem with {problem.prop_label}?",
            f"The {helper.label_word} {fix.qa_text}. That worked because {fix.label} matched the problem: {problem.prop_phrase} needed {problem.need.replace('_', ' ')}."
        ))
        qa.append((
            "Why did the audience laugh at the end?",
            "The audience laughed because the children turned the silly mishap into a small joke inside the play. The fix kept the show going, so the laughter felt happy instead of worried."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that a calm brain can solve a theater problem. By matching the fix to the real trouble, they changed panic into confidence."
        ))
    else:
        qa.append((
            "Did the first fix work perfectly?",
            f"No. The {helper.label_word} tried {fix.label}, but it was not the right fix for that kind of trouble. The scene stayed wobbly because {problem.prop_phrase} needed {problem.need.replace('_', ' ')}, not {fix.capability.replace('_', ' ')}."
        ))
        qa.append((
            "How was the play saved anyway?",
            f"{pal.id} and {lead.id} stayed calm and made a joke when the prop acted silly onstage. Their quick thinking turned the mistake into comedy, so the audience laughed and the scene could continue."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"theater", "stage", "prop", "problem_solving", "audience"}
    if "ribbon" in f["fix"].tags:
        tags.add("ribbon")
    if "tape" in f["fix"].tags:
        tags.add("tape")
    if "cardboard" in f["fix"].tags:
        tags.add("cardboard")
    if "glue" in f["fix"].tags:
        tags.add("glue")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle", "crown_slip", "ribbon_tie", "Nora", "girl", "Ben", "boy", "director_f"),
    StoryParams("jungle", "mustache_peel", "stage_tape", "Mia", "girl", "Theo", "boy", "director_m"),
    StoryParams("space", "moon_droop", "cardboard_brace", "Ava", "girl", "Max", "boy", "director_f"),
    StoryParams("castle", "moon_droop", "cardboard_brace", "Ruby", "girl", "Leo", "boy", "director_m"),
    StoryParams("jungle", "mustache_peel", "glue_blob", "Ella", "girl", "Finn", "boy", "director_f"),
]


ASP_RULES = r"""
matches(P, F) :- need(P, N), capability(F, N).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(T, P, F) :- theme(T), problem(P), fix(F), matches(P, F), sensible(F).

contained(P, F) :- matches(P, F), severity(P, V), power(F, W), W >= V.
outcome(solved) :- chosen_problem(P), chosen_fix(F), contained(P, F), sensible(F).
outcome(wobbly) :- chosen_problem(P), chosen_fix(F), not outcome(solved).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("need", pid, problem.need))
        lines.append(asp.fact("severity", pid, problem.severity))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("capability", fid, fix.capability))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
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
    scenario = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if contained(PROBLEMS[params.problem], FIXES[params.fix]) and FIXES[params.fix].sense >= SENSE_MIN:
        return "solved"
    return "wobbly"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for s in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test failed: empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a silly theater problem, a calm fix, and a comic ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=["director_f", "director_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.fix:
        if not problem_matches(PROBLEMS[args.problem], FIXES[args.fix]) or FIXES[args.fix].sense < SENSE_MIN:
            raise StoryError(explain_rejection(PROBLEMS[args.problem], FIXES[args.fix]))

    if args.fix and FIXES[args.fix].sense < SENSE_MIN and not args.problem:
        raise StoryError(
            f"(No story: {FIXES[args.fix].label} is too messy and weak to be the chosen theater solution.)"
        )

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.problem is None or c[1] == args.problem)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, problem, fix = rng.choice(sorted(combos))
    lead_name, lead_gender = pick_kid(rng)
    pal_name, pal_gender = pick_kid(rng, avoid=lead_name)
    helper = args.helper or rng.choice(["director_f", "director_m"])
    return StoryParams(theme, problem, fix, lead_name, lead_gender, pal_name, pal_gender, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        PROBLEMS[params.problem],
        FIXES[params.fix],
        params.lead_name,
        params.lead_gender,
        params.pal_name,
        params.pal_gender,
        params.helper,
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
        print(f"{len(combos)} compatible (theme, problem, fix) triples:\n")
        for theme, problem, fix in combos:
            print(f"  {theme:8} {problem:14} {fix}")
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
            header = f"### {p.lead_name} & {p.pal_name}: {p.problem} with {p.fix} ({p.theme})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
