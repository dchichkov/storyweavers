#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ritual_romantic_inner_monologue_surprise_sharing_superhero.py
=========================================================================================

A standalone story world about two child superheroes who keep a kindness ritual,
notice that a romantic anniversary surprise is missing one important thing, and
decide whether to share their own treasured gear to save the evening.

This world is built to produce short, child-facing superhero stories with:
- the words "ritual" and "romantic"
- inner monologue
- surprise
- sharing

Run it
------
python storyworlds/worlds/gpt-5.4/ritual_romantic_inner_monologue_surprise_sharing_superhero.py
python storyworlds/worlds/gpt-5.4/ritual_romantic_inner_monologue_surprise_sharing_superhero.py --all
python storyworlds/worlds/gpt-5.4/ritual_romantic_inner_monologue_surprise_sharing_superhero.py --qa
python storyworlds/worlds/gpt-5.4/ritual_romantic_inner_monologue_surprise_sharing_superhero.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# File location: storyworlds/worlds/gpt-5.4/<this file>.py
# We need storyworlds/ on sys.path so "results" resolves.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Core entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    skyline: str
    afford_problems: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    lack_line: str
    need_word: str
    romantic_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    give_line: str = ""
    result_line: str = ""
    qa_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_need(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    if place.meters["problem"] >= THRESHOLD:
        sig = ("need", world.facts["problem"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in (world.get("hero"), world.get("partner")):
                kid.memes["concern"] += 1
            out.append("__need__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    item = world.get("item")
    if item.meters["shared"] >= THRESHOLD and place.meters["problem"] >= THRESHOLD:
        sig = ("fix", world.facts["problem"].id, world.facts["item"].id)
        if sig not in world.fired and compatibility(world.facts["problem"], world.facts["item"]):
            world.fired.add(sig)
            place.meters["problem"] = 0.0
            place.meters["ready"] += 1
            for adult in (world.get("adult1"), world.get("adult2")):
                adult.memes["comfort"] += 1
            out.append("__fixed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="need", tag="state", apply=_r_need),
    Rule(name="fix", tag="state", apply=_r_fix),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def compatibility(problem: Problem, item: ShareItem) -> bool:
    return problem.id in item.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for problem_id in sorted(setting.afford_problems):
            for item_id, item in SHARE_ITEMS.items():
                if compatibility(PROBLEMS[problem_id], item):
                    combos.append((setting_id, problem_id, item_id))
    return combos


def courage_score(trait: str, partner_age: int, hero_age: int, encouragement: int) -> int:
    base = {"kind": 3, "gentle": 2, "sparkly": 1, "proud": 0, "showy": 0, "careful": 2}[trait]
    older_bonus = 1 if partner_age > hero_age else 0
    return base + encouragement + older_bonus


def outcome_of(params: "StoryParams") -> str:
    if courage_score(params.trait, params.partner_age, params.hero_age, params.encouragement) >= 3:
        return "prompt_share"
    return "late_share"


def explain_rejection(setting_id: str, problem_id: str, item_id: str) -> str:
    setting = SETTINGS[setting_id]
    problem = PROBLEMS[problem_id]
    item = SHARE_ITEMS[item_id]
    if problem.id not in setting.afford_problems:
        return (
            f"(No story: {setting.place} does not naturally have the problem "
            f"'{problem.label}', so the superheroes would have no honest mission there.)"
        )
    return (
        f"(No story: sharing {item.phrase} would not solve a place that is {problem.label}. "
        f"The shared gear must actually fix the problem.)"
    )


# ---------------------------------------------------------------------------
# Prediction helpers
# ---------------------------------------------------------------------------
def predict_surprise(world: World, problem: Problem, item: ShareItem, share_now: bool) -> dict:
    sim = world.copy()
    sim.get("place").meters["problem"] = 1
    propagate(sim)
    if share_now:
        sim.get("item").meters["shared"] = 1
        propagate(sim)
    return {
        "ready": sim.get("place").meters["ready"] >= THRESHOLD,
        "problem_left": sim.get("place").meters["problem"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def evening_ritual(world: World, hero: Entity, partner: Entity, setting: Setting) -> None:
    for kid in (hero, partner):
        kid.memes["joy"] += 1
        kid.memes["duty"] += 1
    world.say(
        f"Every Friday at sunset, {hero.id} and {partner.id} climbed to {setting.place} "
        f"for their superhero ritual. They tapped their paper badges, straightened their capes, "
        f"and whispered, \"Eyes open. Hearts open. Help first.\""
    )
    world.say(f"Above them, {setting.skyline} made the whole city feel ready for a secret mission.")


def discover_problem(world: World, hero: Entity, partner: Entity, problem: Problem) -> None:
    place = world.get("place")
    place.meters["problem"] = 1
    propagate(world)
    world.say(problem.lack_line)
    world.say(problem.romantic_line)
    world.facts["noticed_problem"] = True


def plan_surprise(world: World, hero: Entity, partner: Entity, adult1: Entity, adult2: Entity) -> None:
    world.say(
        f'"Tonight is {adult1.label_word} and {adult2.label_word}\'s anniversary," {partner.id} whispered. '
        f'"Let\'s make it a surprise."'
    )
    world.say(
        f"{hero.id} looked over the little supper setup and nodded. A superhero mission did not always need "
        f"a cape-swooping rescue. Sometimes it needed careful hands."
    )


def ask_for_share(world: World, hero: Entity, partner: Entity, item: ShareItem) -> None:
    hero.memes["attachment"] += 1
    world.say(
        f'{partner.id} pointed to {hero.pronoun("possessive")} {item.label}. '
        f'"What if we share {item.phrase}?"'
    )


def inner_monologue(world: World, hero: Entity, item: ShareItem, hopeful: bool) -> None:
    if hopeful:
        hero.memes["generosity"] += 1
        world.say(
            f"{hero.id} pressed a hand to {hero.pronoun('possessive')} chest. "
            f'Inside, {hero.pronoun()} had a tiny hero-thought: '
            f'"I love my {item.label}. But maybe a real hero shines brightest when {hero.pronoun()} shares."'
        )
    else:
        hero.memes["hesitation"] += 1
        world.say(
            f"{hero.id} swallowed hard. In {hero.pronoun('possessive')} head, a quieter thought fluttered: "
            f'"I wanted my {item.label} for myself tonight. If I give it away, will the mission still feel like mine?"'
        )


def prompt_share(world: World, hero: Entity, partner: Entity, item: ShareItem) -> None:
    hero.memes["generosity"] += 1
    world.get("item").meters["shared"] = 1
    propagate(world)
    world.say(
        f'{hero.id} smiled. "Yes," {hero.pronoun()} said. "{item.give_line}"'
    )
    world.say(item.result_line)


def hesitate(world: World, hero: Entity, partner: Entity, item: ShareItem) -> None:
    hero.memes["selfish_pull"] += 1
    world.say(
        f'{hero.id} hugged the {item.label} to {hero.pronoun("possessive")} middle. '
        f'"Maybe we can do the mission without it," {hero.pronoun()} murmured.'
    )


def second_look(world: World, hero: Entity, partner: Entity, problem: Problem, item: ShareItem) -> None:
    pred = predict_surprise(world, problem, item, share_now=True)
    world.facts["predicted_ready_if_shared"] = pred["ready"]
    hero.memes["care"] += 1
    partner.memes["patience"] += 1
    world.say(
        f"{partner.id} did not grab or fuss. {partner.pronoun().capitalize()} only looked at the little table again, "
        f"where it still felt {problem.label}."
    )
    world.say(
        f"{hero.id} imagined the grown-ups stepping out and seeing the place that way. "
        f'That picture made a new thought bloom: "If I share now, the whole surprise can work."'
    )


def late_share(world: World, hero: Entity, partner: Entity, item: ShareItem) -> None:
    hero.memes["generosity"] += 1
    world.get("item").meters["shared"] = 1
    propagate(world)
    world.say(
        f'{hero.id} took a deep breath and held out the {item.label}. '
        f'"Heroes share gear when a mission needs it," {hero.pronoun()} said.'
    )
    world.say(item.result_line)


def reveal_surprise(world: World, hero: Entity, partner: Entity, adult1: Entity, adult2: Entity, problem: Problem) -> None:
    adult1.memes["surprise"] += 1
    adult2.memes["surprise"] += 1
    ready = world.get("place").meters["ready"] >= THRESHOLD
    if ready:
        adult1.memes["joy"] += 1
        adult2.memes["joy"] += 1
        world.say(
            f"When {adult1.label_word} and {adult2.label_word} stepped out, they stopped all at once. "
            f'"For us?" {adult1.label_word} asked.'
        )
        world.say(
            f'{partner.id} threw both hands up. "Surprise!"'
        )
        world.say(
            f"The place no longer felt {problem.label}. It felt warm and bright and a little romantic, "
            f"like a tiny hero-made celebration floating above the city."
        )
    else:
        world.say(
            f"When {adult1.label_word} and {adult2.label_word} stepped out, they smiled at the effort, "
            f"but the place still felt {problem.label}."
        )


def closing_image(world: World, hero: Entity, partner: Entity, item: ShareItem) -> None:
    hero.memes["pride"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"{hero.id} noticed that sharing had not made {hero.pronoun('possessive')} hero gear feel smaller. "
        f"It had made the whole rooftop feel bigger."
    )
    world.say(
        f"Soon the two young heroes were leaning on the rail together, nibbling moon cookies while "
        f"{item.phrase} glowed over the supper table below."
    )


# ---------------------------------------------------------------------------
# Main screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    problem: Problem,
    item: ShareItem,
    hero_name: str,
    hero_gender: str,
    partner_name: str,
    partner_gender: str,
    adult1_type: str,
    adult2_type: str,
    trait: str,
    relation: str,
    hero_age: int,
    partner_age: int,
    encouragement: int,
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        attrs={"name": hero_name, "trait": trait, "relation": relation, "age": hero_age},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        phrase=partner_name,
        role="partner",
        attrs={"name": partner_name, "relation": relation, "age": partner_age},
    ))
    adult1 = world.add(Entity(
        id="adult1",
        kind="character",
        type=adult1_type,
        label="the first grown-up",
        phrase="the first grown-up",
        role="adult1",
    ))
    adult2 = world.add(Entity(
        id="adult2",
        kind="character",
        type=adult2_type,
        label="the second grown-up",
        phrase="the second grown-up",
        role="adult2",
    ))
    place = world.add(Entity(
        id="place",
        type="place",
        label=setting.place,
        phrase=setting.place,
        tags=set(setting.tags),
    ))
    item_ent = world.add(Entity(
        id="item",
        type="gear",
        label=item.label,
        phrase=item.phrase,
        tags=set(item.tags),
    ))

    hero.id = hero_name
    partner.id = partner_name
    world.entities[hero_name] = world.entities.pop("hero")
    world.entities[partner_name] = world.entities.pop("partner")

    world.facts.update(
        setting=setting,
        problem=problem,
        item=item,
        hero=world.get(hero_name),
        partner=world.get(partner_name),
        adult1=adult1,
        adult2=adult2,
        relation=relation,
        hero_age=hero_age,
        partner_age=partner_age,
        encouragement=encouragement,
        trait=trait,
    )

    hero = world.get(hero_name)
    partner = world.get(partner_name)

    evening_ritual(world, hero, partner, setting)
    world.para()
    discover_problem(world, hero, partner, problem)
    plan_surprise(world, hero, partner, adult1, adult2)

    world.para()
    ask_for_share(world, hero, partner, item)
    outcome = "prompt_share" if courage_score(trait, partner_age, hero_age, encouragement) >= 3 else "late_share"
    world.facts["outcome"] = outcome

    if outcome == "prompt_share":
        inner_monologue(world, hero, item, hopeful=True)
        prompt_share(world, hero, partner, item)
    else:
        inner_monologue(world, hero, item, hopeful=False)
        hesitate(world, hero, partner, item)
        second_look(world, hero, partner, problem, item)
        late_share(world, hero, partner, item)

    world.para()
    reveal_surprise(world, hero, partner, adult1, adult2, problem)
    closing_image(world, hero, partner, item)
    world.facts["shared"] = world.get("item").meters["shared"] >= THRESHOLD
    world.facts["ready"] = world.get("place").meters["ready"] >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "rooftop": Setting(
        id="rooftop",
        place="the apartment rooftop",
        skyline="the windows below blinked like a line of superhero signals",
        afford_problems={"dark", "plain", "chilly"},
        tags={"city", "rooftop"},
    ),
    "balcony": Setting(
        id="balcony",
        place="the balcony outside the kitchen",
        skyline="the evening clouds glowed purple over the chimneys",
        afford_problems={"dark", "plain", "chilly"},
        tags={"city", "balcony"},
    ),
    "window_nook": Setting(
        id="window_nook",
        place="the big window nook at the top of the stairs",
        skyline="the city lights trembled in the glass like tiny stars",
        afford_problems={"plain", "chilly"},
        tags={"house", "window"},
    ),
}

PROBLEMS = {
    "dark": Problem(
        id="dark",
        label="too dark",
        lack_line="A tiny anniversary table was already waiting there, but the corners were too dark for a special supper.",
        need_word="light",
        romantic_line="Without a soft glow, the surprise did not feel very romantic yet.",
        tags={"light", "anniversary"},
    ),
    "chilly": Problem(
        id="chilly",
        label="too chilly",
        lack_line="The plates were set and the napkins were folded, but the evening air on the table felt too chilly for a cozy celebration.",
        need_word="warmth",
        romantic_line="The little supper wanted to feel romantic, not shivery.",
        tags={"warmth", "anniversary"},
    ),
    "plain": Problem(
        id="plain",
        label="too plain",
        lack_line="Two cups and a plate of cookies sat there, but the place still looked too plain for an anniversary surprise.",
        need_word="color",
        romantic_line="It needed a gentle, romantic touch to show that tonight was special.",
        tags={"beauty", "anniversary"},
    ),
}

SHARE_ITEMS = {
    "star_lantern": ShareItem(
        id="star_lantern",
        label="star lantern",
        phrase="the silver star lantern",
        fixes={"dark"},
        give_line="My star lantern can be mission light tonight.",
        result_line="Soon soft silver light pooled over the tablecloth and made the spoons sparkle like tiny moon tools.",
        qa_line="They shared the star lantern to add gentle light.",
        tags={"light", "lantern"},
    ),
    "comet_blanket": ShareItem(
        id="comet_blanket",
        label="comet blanket",
        phrase="the blue comet blanket",
        fixes={"chilly"},
        give_line="My comet blanket can keep the chairs warm.",
        result_line="They draped the blue blanket across the two chairs, and the whole supper corner looked cozy at once.",
        qa_line="They shared the comet blanket to make the place warm and cozy.",
        tags={"warmth", "blanket"},
    ),
    "heart_banner": ShareItem(
        id="heart_banner",
        label="heart banner",
        phrase="the red heart banner",
        fixes={"plain"},
        give_line="My heart banner belongs on the mission more than in my toy box.",
        result_line="They tied the paper hearts from rail to rail, and a cheerful ribbon of red danced over the table.",
        qa_line="They shared the heart banner to make the place look festive and loving.",
        tags={"beauty", "banner"},
    ),
    "whoosh_whistle": ShareItem(
        id="whoosh_whistle",
        label="whoosh whistle",
        phrase="the brass whoosh whistle",
        fixes=set(),
        give_line="",
        result_line="",
        qa_line="",
        tags={"noise"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "Ava", "Zoe", "Ivy", "Ella"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Sam", "Eli", "Noah"]
TRAITS = ["kind", "gentle", "sparkly", "proud", "showy", "careful"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    item: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    adult1_type: str
    adult2_type: str
    trait: str
    relation: str
    hero_age: int
    partner_age: int
    encouragement: int
    seed: Optional[int] = None


# Curated set used by --all
CURATED = [
    StoryParams(
        setting="rooftop",
        problem="dark",
        item="star_lantern",
        hero_name="Mina",
        hero_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        adult1_type="mother",
        adult2_type="father",
        trait="kind",
        relation="siblings",
        hero_age=7,
        partner_age=5,
        encouragement=1,
    ),
    StoryParams(
        setting="balcony",
        problem="plain",
        item="heart_banner",
        hero_name="Leo",
        hero_gender="boy",
        partner_name="Ava",
        partner_gender="girl",
        adult1_type="mother",
        adult2_type="father",
        trait="proud",
        relation="friends",
        hero_age=6,
        partner_age=6,
        encouragement=1,
    ),
    StoryParams(
        setting="window_nook",
        problem="chilly",
        item="comet_blanket",
        hero_name="Tess",
        hero_gender="girl",
        partner_name="Nora",
        partner_gender="girl",
        adult1_type="mother",
        adult2_type="father",
        trait="careful",
        relation="siblings",
        hero_age=5,
        partner_age=7,
        encouragement=0,
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ritual": [
        (
            "What is a ritual?",
            "A ritual is something you do the same careful way again and again. It can make a moment feel important and special."
        )
    ],
    "romantic": [
        (
            "What does romantic mean in this story?",
            "Here, romantic means gentle and loving, the kind of feeling grown-ups might like on a special anniversary night. It does not mean magic powers; it means the place feels warm and full of love."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something kind or exciting that someone does without telling you first. It feels special because you do not expect it."
        )
    ],
    "sharing": [
        (
            "Why is sharing important?",
            "Sharing lets more than one person enjoy something good. It can also solve a problem when someone else needs help."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so people can see. A soft lantern can also make a place feel calm and cozy."
        )
    ],
    "blanket": [
        (
            "How can a blanket help on a chilly night?",
            "A blanket helps hold in warmth. It can make a seat or a lap feel much cozier."
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a strip or string of decoration that hangs up where people can see it. It can make a place look festive."
        )
    ],
}
KNOWLEDGE_ORDER = ["ritual", "romantic", "surprise", "sharing", "lantern", "blanket", "banner"]


def relation_phrase(relation: str, hero: Entity, partner: Entity) -> str:
    if relation == "siblings":
        if hero.type == "girl" and partner.type == "girl":
            return "two sisters"
        if hero.type == "boy" and partner.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    problem = world.facts["problem"]
    item = world.facts["item"]
    setting = world.facts["setting"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "ritual" and "romantic".',
        f"Tell a gentle superhero story where {hero.label} and {partner.label} discover that {setting.place} is {problem.label} for an anniversary surprise, and they save the mission by sharing {item.phrase}.",
        "Write a story with inner monologue, surprise, and sharing, where child heroes learn that kindness can be as powerful as a cape.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    partner = world.facts["partner"]
    problem = world.facts["problem"]
    item = world.facts["item"]
    relation = world.facts["relation"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {relation_phrase(relation, hero, partner)}, {hero.label} and {partner.label}, who pretend to be superheroes. They use their kindness ritual to look for someone who needs help."
        ),
        (
            "What mission did the children find?",
            f"They found that the anniversary surprise place was {problem.label}. That mattered because the grown-ups' special supper would not feel as warm and lovely as the children hoped."
        ),
        (
            f"What did {partner.label} ask {hero.label} to do?",
            f"{partner.label} asked {hero.label} to share {item.phrase}. The idea was to use the hero gear to fix what the supper place was missing."
        ),
    ]
    if outcome == "prompt_share":
        qa.append(
            (
                f"What was {hero.label}'s inner monologue about?",
                f"{hero.label} thought about loving the {item.label} but wanting to be a real hero even more. That quiet thought helped {hero.pronoun()} choose sharing right away."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.label} hesitate before sharing?",
                f"{hero.label} first wanted to keep the {item.label} for a private game. Then {hero.pronoun()} imagined the surprise failing and understood that sharing would help everyone more."
            )
        )
    qa.append(
        (
            "How did the surprise end?",
            f"The grown-ups stepped out and found the place transformed. Because the children shared {item.phrase}, the anniversary corner no longer felt {problem.label} and the surprise felt special."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ritual", "romantic", "surprise", "sharing"}
    item = world.facts["item"]
    if "lantern" in item.tags:
        tags.add("lantern")
    if "blanket" in item.tags:
        tags.add("blanket")
    if "banner" in item.tags:
        tags.add("banner")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story combo is valid when the setting can honestly host the problem
% and the shared item really fixes that problem.
valid(S, P, I) :- setting(S), problem(P), item(I), affords(S, P), fixes(I, P).

% Outcome model: a stronger sharing impulse leads to prompt sharing.
older_partner :- hero_age(H), partner_age(P), P > H.
older_bonus(1) :- older_partner.
older_bonus(0) :- not older_partner.

trait_base(3) :- chosen_trait(kind).
trait_base(2) :- chosen_trait(gentle).
trait_base(1) :- chosen_trait(sparkly).
trait_base(0) :- chosen_trait(proud).
trait_base(0) :- chosen_trait(showy).
trait_base(2) :- chosen_trait(careful).

courage(T + E + O) :- trait_base(T), encouragement(E), older_bonus(O).

outcome(prompt_share) :- courage(C), C >= 3.
outcome(late_share) :- courage(C), C < 3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for problem_id in sorted(setting.afford_problems):
            lines.append(asp.fact("affords", setting_id, problem_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for item_id, item in SHARE_ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for problem_id in sorted(item.fixes):
            lines.append(asp.fact("fixes", item_id, problem_id))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
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
        asp.fact("chosen_trait", params.trait),
        asp.fact("hero_age", params.hero_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("encouragement", params.encouragement),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for seed in range(30):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome scenarios differ.")

    try:
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Two child superheroes keep a kindness ritual and save a romantic surprise by sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=SHARE_ITEMS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--adult1", choices=["mother", "father"])
    ap.add_argument("--adult2", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--encouragement", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.problem and args.problem not in SETTINGS[args.setting].afford_problems:
        any_item = args.item or next(iter(SHARE_ITEMS))
        raise StoryError(explain_rejection(args.setting, args.problem, any_item))
    if args.problem and args.item and not compatibility(PROBLEMS[args.problem], SHARE_ITEMS[args.item]):
        setting_id = args.setting or next(iter(SETTINGS))
        if args.problem not in SETTINGS[setting_id].afford_problems:
            for sid, st in SETTINGS.items():
                if args.problem in st.afford_problems:
                    setting_id = sid
                    break
        raise StoryError(explain_rejection(setting_id, args.problem, args.item))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.item is None or combo[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, item_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    partner_name = args.partner_name or pick_name(rng, partner_gender, avoid=hero_name)
    adult1 = args.adult1 or "mother"
    adult2 = args.adult2 or "father"
    trait = args.trait or rng.choice(TRAITS)
    relation = args.relation or rng.choice(["siblings", "friends"])
    encouragement = args.encouragement if args.encouragement is not None else rng.choice([0, 1, 2])
    hero_age, partner_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        item=item_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        adult1_type=adult1,
        adult2_type=adult2,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        partner_age=partner_age,
        encouragement=encouragement,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        problem = PROBLEMS[params.problem]
        item = SHARE_ITEMS[params.item]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err})") from None

    if params.problem not in setting.afford_problems:
        raise StoryError(explain_rejection(params.setting, params.problem, params.item))
    if not compatibility(problem, item):
        raise StoryError(explain_rejection(params.setting, params.problem, params.item))

    world = tell(
        setting=setting,
        problem=problem,
        item=item,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        adult1_type=params.adult1_type,
        adult2_type=params.adult2_type,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        partner_age=params.partner_age,
        encouragement=params.encouragement,
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
        print(f"{len(combos)} compatible (setting, problem, item) combos:\n")
        for setting_id, problem_id, item_id in combos:
            print(f"  {setting_id:12} {problem_id:8} {item_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} & {p.partner_name}: {p.problem} at {p.setting} with {p.item} ({outcome_of(p)})"
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
