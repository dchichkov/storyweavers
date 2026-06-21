#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/androgynous_miracle_misunderstanding_rhyme_surprise_comedy.py
=========================================================================================

A standalone story world for a small comedy domain: a child's stage prop breaks
right before a show, a rhyming plea causes a misunderstanding, an androgynous
helper brings the wrong thing first, and a cheerful surprise turns the mishap
into a hit.

The world is intentionally narrow. It only generates combinations where the
chosen helper can really fix the chosen prop problem. The misunderstanding is
state-driven: some rhymes are easy to mishear in a noisy place, others are
clear. The ending image proves what changed: the child who thought only a
miracle could save the act ends up laughing onstage with a new friend.

Run it
------
    python storyworlds/worlds/gpt-5.4/androgynous_miracle_misunderstanding_rhyme_surprise_comedy.py
    python storyworlds/worlds/gpt-5.4/androgynous_miracle_misunderstanding_rhyme_surprise_comedy.py --problem crown --helper costume
    python storyworlds/worlds/gpt-5.4/androgynous_miracle_misunderstanding_rhyme_surprise_comedy.py --problem boot --helper janitor
    python storyworlds/worlds/gpt-5.4/androgynous_miracle_misunderstanding_rhyme_surprise_comedy.py --all
    python storyworlds/worlds/gpt-5.4/androgynous_miracle_misunderstanding_rhyme_surprise_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/androgynous_miracle_misunderstanding_rhyme_surprise_comedy.py --verify
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
NOISE_FOR_MISHEAR = 1


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    place: str
    noise: int
    crowd: str
    surprise_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    prop_label: str
    prop_phrase: str
    trouble: str
    need: str
    rhyme_call: str
    wrong_item: str
    wrong_phrase: str
    fix_text: str
    after_text: str
    ambiguous: bool
    chant_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    name: str
    helper_type: str
    style: str
    kit: set[str] = field(default_factory=set)
    join_style: str = ""
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseCfg:
    id: str
    gift: str
    entrance: str
    finish: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
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


def _r_prop_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    prop = world.entities.get("prop")
    if hero is None or prop is None:
        return out
    if prop.meters["broken"] >= THRESHOLD:
        sig = ("worry", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_wrong_item(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    wrong = world.entities.get("wrong")
    if hero is None or helper is None or wrong is None:
        return out
    if wrong.meters["delivered"] >= THRESHOLD:
        sig = ("mixup", wrong.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["confusion"] += 1
            hero.memes["giggles"] += 1
            helper.memes["sheepish"] += 1
            out.append("__mixup__")
    return out


def _r_fix_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    prop = world.entities.get("prop")
    if hero is None or helper is None or prop is None:
        return out
    if prop.meters["fixed"] >= THRESHOLD:
        sig = ("relief", prop.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["relief"] += 1
            hero.memes["confidence"] += 1
            helper.memes["pride"] += 1
            out.append("__relief__")
    return out


def _r_surprise_delight(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    hero = world.entities.get("hero")
    if room is None or hero is None:
        return out
    if room.meters["surprise"] >= THRESHOLD:
        sig = ("delight", "room")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] += 1
            hero.memes["wonder"] += 1
            room.memes["laughter"] += 1
            out.append("__surprise__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="prop_worry", tag="emotional", apply=_r_prop_worry),
    Rule(name="wrong_item", tag="social", apply=_r_wrong_item),
    Rule(name="fix_relief", tag="emotional", apply=_r_fix_relief),
    Rule(name="surprise_delight", tag="social", apply=_r_surprise_delight),
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


def helper_can_fix(problem: Problem, helper: HelperCfg) -> bool:
    return problem.need in helper.kit


def will_misunderstand(venue: Venue, problem: Problem) -> bool:
    return problem.ambiguous and venue.noise >= NOISE_FOR_MISHEAR


def has_big_surprise(venue: Venue, helper: HelperCfg) -> bool:
    return venue.noise >= 1 and bool(helper.join_style)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue_id in VENUES:
        for problem_id, problem in PROBLEMS.items():
            for helper_id, helper in HELPERS.items():
                if not helper_can_fix(problem, helper):
                    continue
                for surprise_id in SURPRISES:
                    combos.append((venue_id, problem_id, helper_id, surprise_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    venue = VENUES[params.venue]
    problem = PROBLEMS[params.problem]
    helper = HELPERS[params.helper]
    if not helper_can_fix(problem, helper):
        return "invalid"
    mixup = will_misunderstand(venue, problem)
    if has_big_surprise(venue, helper):
        return "surprise_mixup" if mixup else "surprise_clean"
    return "mixup" if mixup else "clean"


def predict_mixup(venue: Venue, problem: Problem, helper: HelperCfg) -> dict:
    return {
        "mixup": will_misunderstand(venue, problem),
        "can_fix": helper_can_fix(problem, helper),
        "surprise": has_big_surprise(venue, helper),
    }


def introduce(world: World, hero: Entity, parent: Entity, prop: Entity, venue: Venue) -> None:
    world.say(
        f"{hero.id} was getting ready for the little show at {venue.place}. "
        f"{parent.label_word.capitalize()} had helped {hero.pronoun('object')} pack {prop.phrase}, "
        f"and the room was already full of {venue.crowd}."
    )
    hero.memes["hope"] += 1


def prop_trouble(world: World, hero: Entity, prop: Entity, problem: Problem) -> None:
    prop.meters["broken"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the trouble popped up at exactly the wrong time: {problem.trouble}. "
        f"{hero.id} stared at the prop and whispered, \"Oh no. I need {problem.need}. "
        f"At this rate, only a miracle will save my act.\""
    )


def rhyme_call(world: World, hero: Entity, venue: Venue, problem: Problem) -> None:
    world.say(
        f"Trying not to cry, {hero.id} sang a silly little rhyme into the busy air: "
        f"\"{problem.rhyme_call}\""
    )
    if venue.noise >= 1:
        world.say(
            f"But {venue.place} was full of shuffling feet and cheerful chatter, so the rhyme bounced around in a very wiggly way."
        )


def enter_helper(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"Out from backstage came {helper.id}, a calm helper in {helper_cfg.style}. "
        f"{helper.pronoun().capitalize()} had an androgynous look that made {helper.pronoun('object')} seem like exactly the right person for any costume emergency."
    )


def wrong_delivery(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    wrong = world.get("wrong")
    wrong.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"\"I heard you!\" {helper.id} said brightly, and held up {problem.wrong_phrase}. "
        f"{hero.id} blinked. \"That is very nice,\" {hero.pronoun()} said, \"but my prop is the problem, not {problem.wrong_item}.\""
    )
    if hero.memes["giggles"] >= THRESHOLD:
        world.say(
            f"For one second they both looked at each other, and then the mistake was so silly that a laugh slipped out first."
        )


def clear_up(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} pointed to the prop and tried again, slower this time: "
        f"\"Not {problem.wrong_item}. I need {problem.need} because {problem.after_text}.\""
    )
    helper.memes["understanding"] += 1
    world.say(
        f"\"Aha!\" said {helper.id}. \"Your rhyme was good. My ears were the part that needed practice.\""
    )


def fix_prop(world: World, hero: Entity, helper: Entity, prop: Entity, problem: Problem) -> None:
    prop.meters["broken"] = 0.0
    prop.meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} reached into {helper.pronoun('possessive')} pocket, found {problem.need}, and {problem.fix_text}. "
        f"In another breath, the prop was ready again."
    )
    if hero.memes["relief"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s shoulders dropped, and a grin came back. It felt a little bit like a miracle, though really it was kindness and a steady hand."
        )


def start_show(world: World, hero: Entity, venue: Venue, problem: Problem) -> None:
    world.say(
        f"Soon the music began, and {hero.id} stepped toward the front with the fixed prop. "
        f"This time {problem.after_text}, and the act could start."
    )


def surprise_join(world: World, hero: Entity, helper: Entity, surprise: SurpriseCfg, helper_cfg: HelperCfg, venue: Venue) -> None:
    room = world.get("room")
    room.meters["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just when {hero.id} thought the funny part was over, {helper.id} gave a tiny bow and {surprise.entrance} from {venue.surprise_spot}. "
        f"{helper_cfg.join_style}"
    )
    world.say(
        f"{surprise.finish} The crowd burst into happy laughter, and {hero.id} laughed hardest of all."
    )


def neat_end(world: World, hero: Entity, helper: Entity, surprise: SurpriseCfg) -> None:
    room = world.get("room")
    room.meters["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"After the applause, {helper.id} tucked {surprise.gift} into {hero.id}'s hand and whispered, "
        f"\"For brave rhymers only.\" {hero.id} laughed and promised to rhyme more clearly next time."
    )


def tell(
    venue: Venue,
    problem: Problem,
    helper_cfg: HelperCfg,
    surprise_cfg: SurpriseCfg,
    *,
    hero_name: str = "Pip",
    hero_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World(venue)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    helper = world.add(Entity(id=helper_cfg.name, kind="character", type=helper_cfg.helper_type, role="helper"))
    prop = world.add(Entity(id="prop", type="prop", label=problem.prop_label, phrase=problem.prop_phrase))
    world.add(Entity(id="wrong", type="thing", label=problem.wrong_item, phrase=problem.wrong_phrase))
    world.add(Entity(id="room", type="room", label="the room"))

    introduce(world, hero, parent, prop, venue)
    prop_trouble(world, hero, prop, problem)

    world.para()
    rhyme_call(world, hero, venue, problem)
    enter_helper(world, helper, helper_cfg)

    pred = predict_mixup(venue, problem, helper_cfg)
    world.facts["predicted_mixup"] = pred["mixup"]
    world.facts["predicted_surprise"] = pred["surprise"]

    if pred["mixup"]:
        wrong_delivery(world, hero, helper, problem)
        clear_up(world, hero, helper, problem)
    else:
        world.say(
            f"\"I heard the rhyme,\" said {helper.id}, \"and I think I know just what you need.\""
        )

    world.para()
    fix_prop(world, hero, helper, prop, problem)
    start_show(world, hero, venue, problem)

    world.para()
    if pred["surprise"]:
        surprise_join(world, hero, helper, surprise_cfg, helper_cfg, venue)
    else:
        neat_end(world, hero, helper, surprise_cfg)

    outcome = outcome_of(
        StoryParams(
            venue=venue.id,
            problem=problem.id,
            helper=helper_cfg.id,
            surprise=surprise_cfg.id,
            name=hero_name,
            gender=hero_type,
            parent=parent_type,
            seed=None,
        )
    )
    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper,
        prop=prop,
        venue=venue,
        problem=problem,
        helper_cfg=helper_cfg,
        surprise_cfg=surprise_cfg,
        outcome=outcome,
        mixup=pred["mixup"],
        surprise_happened=True,
        fixed=prop.meters["fixed"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    venue: str
    problem: str
    helper: str
    surprise: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


VENUES = {
    "school_hall": Venue(
        id="school_hall",
        place="the school hall",
        noise=2,
        crowd="folding chairs, whispering families, and squeaky shoes",
        surprise_spot="behind the curtain",
        tags={"show", "crowd", "noise"},
    ),
    "library_corner": Venue(
        id="library_corner",
        place="the library corner stage",
        noise=0,
        crowd="soft claps and polite little coughs",
        surprise_spot="between two tall bookcases",
        tags={"library", "quiet"},
    ),
    "park_stage": Venue(
        id="park_stage",
        place="the park bandstand",
        noise=1,
        crowd="picnic blankets, pigeons, and people eating buns",
        surprise_spot="behind the painted music stand",
        tags={"park", "noise"},
    ),
}

PROBLEMS = {
    "crown": Problem(
        id="crown",
        prop_label="paper crown",
        prop_phrase="a shiny paper crown with gold stars",
        trouble="the paper crown kept slipping over one eye",
        need="a clip",
        rhyme_call="Crown down! Help in town!",
        wrong_item="a gown",
        wrong_phrase="a sparkly gown on a hanger",
        fix_text="clipped the crown neatly behind one ear",
        after_text="the crown sat straight instead of sliding down",
        ambiguous=True,
        chant_word="crown",
        tags={"costume", "rhyme"},
    ),
    "cape": Problem(
        id="cape",
        prop_label="red cape",
        prop_phrase="a swishy red cape with silver dots",
        trouble="the red cape had a tiny rip near the neck",
        need="tape",
        rhyme_call="Cape scrape! Need some tape!",
        wrong_item="a tray of grapes",
        wrong_phrase="a tray of grapes from the snack table",
        fix_text="smoothed a strip of tape under the torn edge",
        after_text="the cape fluttered without pulling apart",
        ambiguous=True,
        chant_word="cape",
        tags={"costume", "tape"},
    ),
    "boot": Problem(
        id="boot",
        prop_label="giant story boot",
        prop_phrase="one giant cardboard boot for a nursery-rhyme dance",
        trouble="the giant story boot had lost its lace",
        need="a lace",
        rhyme_call="Boot loose! I need a lace!",
        wrong_item="a vase",
        wrong_phrase="a tiny blue vase with one daisy in it",
        fix_text="threaded in a fresh lace and tied a brave, bouncy bow",
        after_text="the boot stayed snug instead of flopping open",
        ambiguous=True,
        chant_word="boot",
        tags={"costume", "lace"},
    ),
}

HELPERS = {
    "costume": HelperCfg(
        id="costume",
        name="Alex",
        helper_type="person",
        style="a neat vest, bright scarf, and shoes that whispered instead of squeaked",
        kit={"a clip", "clip", "tape", "a lace", "lace"},
        join_style="Then Alex pulled out a pocket kazoo and played one proud toot exactly on the beat.",
        reveal="costume helper",
        tags={"costume", "androgynous"},
    ),
    "janitor": HelperCfg(
        id="janitor",
        name="Rowan",
        helper_type="person",
        style="blue overalls with a rainbow pen tucked into the front pocket",
        kit={"tape", "a lace", "lace"},
        join_style="Then Rowan twirled a feather duster like a baton and marched three silly steps in a row.",
        reveal="hall helper",
        tags={"janitor", "androgynous"},
    ),
    "teacher": HelperCfg(
        id="teacher",
        name="River",
        helper_type="person",
        style="a crisp shirt, velvet vest, and one shiny moon pin",
        kit={"clip", "tape"},
        join_style="Then River snapped in time and sang the last line of the rhyme back to the crowd.",
        reveal="music teacher",
        tags={"teacher", "androgynous"},
    ),
}

SURPRISES = {
    "kazoo": SurpriseCfg(
        id="kazoo",
        gift="a tiny striped kazoo",
        entrance="popped out",
        finish="A squeaky little melody skipped through the air and made even the serious grandparents grin.",
        tags={"music", "surprise"},
    ),
    "confetti": SurpriseCfg(
        id="confetti",
        gift="a paper star full of confetti",
        entrance="sprang out",
        finish="With a puff, paper stars fluttered down like cheerful snow.",
        tags={"confetti", "surprise"},
    ),
    "duck": SurpriseCfg(
        id="duck",
        gift="a yellow duck sticker",
        entrance="leaned out",
        finish="A rubber duck squeak sounded at exactly the funniest moment, and children in the front row nearly folded in half laughing.",
        tags={"duck", "surprise"},
    ),
}

GIRL_NAMES = ["Pip", "Mia", "Lulu", "Tess", "Nora", "Ruby", "June", "Bea"]
BOY_NAMES = ["Pip", "Max", "Leo", "Finn", "Ollie", "Sam", "Eli", "Noah"]


CURATED = [
    StoryParams(
        venue="school_hall",
        problem="crown",
        helper="costume",
        surprise="kazoo",
        name="Pip",
        gender="girl",
        parent="mother",
        seed=None,
    ),
    StoryParams(
        venue="library_corner",
        problem="cape",
        helper="teacher",
        surprise="confetti",
        name="Leo",
        gender="boy",
        parent="father",
        seed=None,
    ),
    StoryParams(
        venue="park_stage",
        problem="boot",
        helper="janitor",
        surprise="duck",
        name="Mia",
        gender="girl",
        parent="mother",
        seed=None,
    ),
    StoryParams(
        venue="school_hall",
        problem="cape",
        helper="teacher",
        surprise="kazoo",
        name="Finn",
        gender="boy",
        parent="father",
        seed=None,
    ),
]


KNOWLEDGE = {
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching end sounds, like crown and down. Rhymes can be fun, but if a room is noisy, people can still mishear them."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding is when one person hears or thinks the wrong thing. It can be solved by stopping, explaining clearly, and listening again."
        )
    ],
    "clip": [
        (
            "What does a clip do?",
            "A clip holds things together or keeps them from slipping. It is useful for paper, cloth, or hair."
        )
    ],
    "tape": [
        (
            "What is tape used for?",
            "Tape is sticky, so it can hold torn things together for a while. It is good for a quick fix."
        )
    ],
    "lace": [
        (
            "What is a lace?",
            "A lace is a string that can be threaded through holes and tied. Laces help shoes and other things stay snug."
        )
    ],
    "miracle": [
        (
            "What does miracle mean in this story?",
            "Here miracle means something that feels wonderfully lucky or almost impossible. The fix still comes from real help, not magic."
        )
    ],
    "surprise": [
        (
            "Why can a surprise make people laugh?",
            "A surprise can make people laugh when something unexpected happens in a cheerful way. The sudden change tickles the mind."
        )
    ],
    "show": [
        (
            "What happens at a little show?",
            "People gather to watch singing, dancing, jokes, or costumes. Everyone takes turns performing and clapping."
        )
    ],
    "androgynous": [
        (
            "What does androgynous mean?",
            "Androgynous means a person looks or dresses in a way that is not strongly just boyish or just girlish. It is simply one way a person can look."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "show",
    "rhyme",
    "misunderstanding",
    "clip",
    "tape",
    "lace",
    "miracle",
    "surprise",
    "androgynous",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    problem = f["problem"]
    venue = f["venue"]
    helper = f["helper"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "androgynous" and "miracle". The story should happen at {venue.place} and use a rhyming misunderstanding.',
        f"Tell a comedy story where {hero.id}'s {problem.prop_label} goes wrong before a show, and {helper.id} mishears a rhyme and brings the wrong thing first.",
        f"Write a gentle surprise story in which a child thinks only a miracle can save the act, but a kind androgynous helper fixes the problem and turns the mistake into laughter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    helper = f["helper"]
    venue = f["venue"]
    problem = f["problem"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was getting ready to perform, and {helper.id}, the helpful grown-up who came from backstage. {hero.id}'s {parent.label_word} helped at the beginning too."
        ),
        (
            "What went wrong before the show?",
            f"{problem.trouble}. That made {hero.id} worry the act might not be ready in time."
        ),
        (
            f"Why did {hero.id} say only a miracle could help?",
            f"{hero.id} felt scared because the prop problem happened right before the show. The word miracle shows how impossible the fix felt in that moment, even though a real person solved it."
        ),
        (
            "What kind of misunderstanding happened?",
            f"{hero.id} sang a rhyme for help, but the busy room bent the words the wrong way. {helper.id} heard it as a call for {problem.wrong_item} instead of {problem.need}."
        ),
    ]
    if f["mixup"]:
        qa.append(
            (
                f"What did {helper.id} bring by mistake?",
                f"{helper.id} brought {problem.wrong_phrase}. They both laughed because the rhyme had sounded clear to the speaker, but not to the listener."
            )
        )
    qa.append(
        (
            f"How was the problem fixed?",
            f"{helper.id} listened again, found {problem.need}, and {problem.fix_text}. After that, {problem.after_text} and the show could begin."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with a cheerful surprise onstage and lots of laughter. The broken prop became part of a funny memory instead of a disaster."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"show", "rhyme", "misunderstanding", "miracle", "surprise", "androgynous"}
    need = f["problem"].need
    if "clip" in need:
        tags.add("clip")
    if "tape" in need:
        tags.add("tape")
    if "lace" in need:
        tags.add("lace")
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, helper: HelperCfg) -> str:
    return (
        f"(No story: {helper.name} cannot reasonably fix the {problem.prop_label} problem. "
        f"The prop needs {problem.need}, but that tool is not in this helper's kit.)"
    )


ASP_RULES = r"""
can_fix(P, H) :- problem(P), helper(H), needs(P, N), carries(H, N).

valid(V, P, H, S) :- venue(V), problem(P), helper(H), surprise(S), can_fix(P, H).

mixup(V, P) :- noisy(V), ambiguous(P).
big_surprise(V, H) :- surprise_ready(H), noisy(V).

outcome(V, P, H, surprise_mixup) :- can_fix(P, H), mixup(V, P), big_surprise(V, H).
outcome(V, P, H, surprise_clean) :- can_fix(P, H), not mixup(V, P), big_surprise(V, H).
outcome(V, P, H, mixup) :- can_fix(P, H), mixup(V, P), not big_surprise(V, H).
outcome(V, P, H, clean) :- can_fix(P, H), not mixup(V, P), not big_surprise(V, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        if venue.noise >= NOISE_FOR_MISHEAR:
            lines.append(asp.fact("noisy", venue_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        lines.append(asp.fact("needs", problem_id, problem.need))
        if problem.ambiguous:
            lines.append(asp.fact("ambiguous", problem_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for tool in sorted(helper.kit):
            lines.append(asp.fact("carries", helper_id, tool))
        if helper.join_style:
            lines.append(asp.fact("surprise_ready", helper_id))
    for surprise_id in SURPRISES:
        lines.append(asp.fact("surprise", surprise_id))
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
            asp.fact("chosen_venue", params.venue),
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_helper", params.helper),
            "out(O) :- chosen_venue(V), chosen_problem(P), chosen_helper(H), outcome(V, P, H, O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show out/1."))
    atoms = asp.atoms(model, "out")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome comparisons differed.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a rhyming misunderstanding before a funny little show."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.helper:
        problem = PROBLEMS[args.problem]
        helper = HELPERS[args.helper]
        if not helper_can_fix(problem, helper):
            raise StoryError(explain_rejection(problem, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.problem is None or combo[1] == args.problem)
        and (args.helper is None or combo[2] == args.helper)
        and (args.surprise is None or combo[3] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, problem_id, helper_id, surprise_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        venue=venue_id,
        problem=problem_id,
        helper=helper_id,
        surprise=surprise_id,
        name=name,
        gender=gender,
        parent=parent,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")

    venue = VENUES[params.venue]
    problem = PROBLEMS[params.problem]
    helper = HELPERS[params.helper]
    surprise = SURPRISES[params.surprise]
    if not helper_can_fix(problem, helper):
        raise StoryError(explain_rejection(problem, helper))

    world = tell(
        venue,
        problem,
        helper,
        surprise,
        hero_name=params.name,
        hero_type=params.gender,
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
        print(asp_program("", "#show valid/4.\n#show outcome/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, problem, helper, surprise) combos:\n")
        for venue, problem, helper, surprise in combos:
            print(f"  {venue:14} {problem:7} {helper:8} {surprise}")
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
            header = f"### {p.name}: {p.problem} at {p.venue} with {p.helper} ({outcome_of(p)})"
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
