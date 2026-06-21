#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hydrocortisone_bike_understand_inner_monologue_happy_ending.py
==========================================================================================

A standalone story world about a child who wants to ride a bike on a grand day,
gets an itchy spot, does not understand hydrocortisone at first, and is helped
by a kind grown-up who explains it gently. The world rebuilds a tiny tale with
state: longing, confusion, inner monologue, explanation, waiting, relief, and a
happy ending proved by the ride itself.

The style leans toward a child-friendly tall tale: feelings are large, bicycles
feel almost legendary, and the ending shines. The simulation stays grounded by a
small reasonableness gate:

* hydrocortisone belongs in the story only for itchy skin troubles such as a
  mosquito bite or a mild rash
* it is refused for an open scrape
* the helper's explanation must be clear enough for the child to understand
* they must wait long enough for the cream to help before the big ride

Run it
------
    python storyworlds/worlds/gpt-5.4/hydrocortisone_bike_understand_inner_monologue_happy_ending.py
    python storyworlds/worlds/gpt-5.4/hydrocortisone_bike_understand_inner_monologue_happy_ending.py --ride parade --issue mosquito_bite
    python storyworlds/worlds/gpt-5.4/hydrocortisone_bike_understand_inner_monologue_happy_ending.py --issue scraped_knee
    python storyworlds/worlds/gpt-5.4/hydrocortisone_bike_understand_inner_monologue_happy_ending.py --wait 1
    python storyworlds/worlds/gpt-5.4/hydrocortisone_bike_understand_inner_monologue_happy_ending.py --all --qa
    python storyworlds/worlds/gpt-5.4/hydrocortisone_bike_understand_inner_monologue_happy_ending.py --verify
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
CLARITY_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class RidePlan:
    id: str
    opening: str
    boast: str
    course: str
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SkinIssue:
    id: str
    label: str
    place: str
    cause: str
    itchy: bool = True
    open_skin: bool = False
    relief_need: int = 2
    warning: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Explanation:
    id: str
    style: str
    metaphor: str
    clarity: int = 2
    kindness_line: str = ""
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


def _r_understand(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.memes["explained"] < THRESHOLD:
        return []
    if hero.memes["confusion"] <= 0:
        return []
    sig = ("understand", hero.id)
    if sig in world.fired:
        return []
    if hero.memes["clarity"] >= hero.memes["confusion"]:
        world.fired.add(sig)
        hero.memes["understand"] += 1
        hero.memes["confusion"] = 0.0
        hero.memes["calm"] += 1
        return ["__understand__"]
    return []


def _r_relief(world: World) -> list[str]:
    hero = world.entities.get("hero")
    spot = world.entities.get("spot")
    if hero is None or spot is None:
        return []
    if spot.meters["cream"] < THRESHOLD:
        return []
    wait = int(world.facts.get("wait", 0))
    needed = int(world.facts.get("relief_need", 99))
    sig = ("relief", hero.id, wait)
    if sig in world.fired:
        return []
    if wait >= needed:
        world.fired.add(sig)
        spot.meters["itch"] = 0.0
        hero.memes["relief"] += 1
        hero.memes["hope"] += 1
        return ["__relief__"]
    return []


def _r_ready_to_ride(world: World) -> list[str]:
    hero = world.entities.get("hero")
    spot = world.entities.get("spot")
    if hero is None or spot is None:
        return []
    if hero.memes["understand"] < THRESHOLD:
        return []
    if hero.memes["relief"] < THRESHOLD:
        return []
    sig = ("ready", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    return ["__ready__"]


CAUSAL_RULES = [
    Rule(name="understand", tag="social", apply=_r_understand),
    Rule(name="relief", tag="physical", apply=_r_relief),
    Rule(name="ready_to_ride", tag="emotional", apply=_r_ready_to_ride),
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


RIDES = {
    "parade": RidePlan(
        id="parade",
        opening="the morning of the town's tin-bell bike parade",
        boast="The bike waiting by the porch looked big enough to roll across three counties and polite enough to ring hello to every chicken in town.",
        course="down the maple-lined street with ribbons snapping from the handlebars",
        finish="By the end, the little bike bell was singing and the whole street seemed to smile back.",
        tags={"bike", "parade"},
    ),
    "bakery": RidePlan(
        id="bakery",
        opening="the bright day of the bakery errand ride",
        boast="The bike leaned against the fence like a silver pony with two spinning pancakes for wheels.",
        course="to the bakery corner where the air smelled like warm buns and cinnamon",
        finish="At the end of the ride, the bread was warm in the basket and the hero was grinning wider than the handlebars.",
        tags={"bike", "bakery"},
    ),
    "pond": RidePlan(
        id="pond",
        opening="the breezy afternoon of the duck-pond ride",
        boast="The bike stood ready like a trusty little thunderbolt, all chrome wink and brave tires.",
        course="along the path by the pond where ducks waddled like judges in feathery coats",
        finish="When the wheels finally slowed, even the ducks looked as if they approved the grand adventure.",
        tags={"bike", "pond"},
    ),
}

ISSUES = {
    "mosquito_bite": SkinIssue(
        id="mosquito_bite",
        label="mosquito bite",
        place="ankle",
        cause="a sneaky mosquito had nibbled the hero the evening before",
        itchy=True,
        open_skin=False,
        relief_need=2,
        warning="It was not a big hurt, only a tiny itchy trouble with very loud opinions.",
        tags={"itch", "mosquito"},
    ),
    "nettle_brush": SkinIssue(
        id="nettle_brush",
        label="nettle sting",
        place="calf",
        cause="the hero had brushed past a nettle patch near the fence",
        itchy=True,
        open_skin=False,
        relief_need=2,
        warning="The sting was small, but it prickled as if a whole pocketful of ants were practicing a marching song there.",
        tags={"itch", "plant"},
    ),
    "soap_rash": SkinIssue(
        id="soap_rash",
        label="soap rash",
        place="elbow",
        cause="a new soap had made a little itchy patch",
        itchy=True,
        open_skin=False,
        relief_need=3,
        warning="It was a mild rash, red and annoying, not dangerous, just fussy as a goose with wet feet.",
        tags={"itch", "rash"},
    ),
    "scraped_knee": SkinIssue(
        id="scraped_knee",
        label="scraped knee",
        place="knee",
        cause="the hero had skidded on gravel the day before",
        itchy=False,
        open_skin=True,
        relief_need=99,
        warning="This was an open scrape, and that is not what hydrocortisone is for.",
        tags={"scrape"},
    ),
}

EXPLANATIONS = {
    "plain": Explanation(
        id="plain",
        style="plain",
        metaphor="It helps quiet itchy skin. It is not a magic racing cream, just a gentle cream for irritation.",
        clarity=2,
        kindness_line="I know the word sounds big, but I can explain it one small piece at a time.",
        tags={"hydrocortisone", "medicine"},
    ),
    "story": Explanation(
        id="story",
        style="story",
        metaphor="Hydrocortisone is like a soft librarian for itchy skin; it tells the noisy itch, 'Shhh now, settle down.'",
        clarity=3,
        kindness_line="Big words can be friendly once we get to know them.",
        tags={"hydrocortisone", "medicine"},
    ),
    "hurried": Explanation(
        id="hurried",
        style="hurried",
        metaphor="It is cream. Just hold still.",
        clarity=1,
        kindness_line="",
        tags={"hydrocortisone"},
    ),
}

HELPERS = {
    "mother": {"type": "mother", "role": "parent"},
    "grandfather": {"type": "grandfather", "role": "helper"},
    "aunt": {"type": "aunt", "role": "helper"},
}

GIRL_NAMES = ["Lula", "Mina", "Nell", "Poppy", "June", "Daisy", "Willa", "Pearl"]
BOY_NAMES = ["Otis", "Milo", "Jasper", "Beau", "Finn", "Toby", "Reed", "Cal"]
TRAITS = ["eager", "curious", "bright", "hopeful", "spirited", "thoughtful"]


def issue_treatable(issue: SkinIssue) -> bool:
    return issue.itchy and not issue.open_skin


def explanation_clear(explanation: Explanation) -> bool:
    return explanation.clarity >= CLARITY_MIN


def wait_enough(issue: SkinIssue, wait: int) -> bool:
    return wait >= issue.relief_need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for ride_id in RIDES:
        for issue_id, issue in ISSUES.items():
            for exp_id, exp in EXPLANATIONS.items():
                if issue_treatable(issue) and explanation_clear(exp):
                    combos.append((ride_id, issue_id, exp_id))
    return combos


@dataclass
class StoryParams:
    ride: str
    issue: str
    explanation: str
    helper: str
    hero_name: str
    hero_gender: str
    trait: str
    wait: int
    seed: Optional[int] = None


def opening(world: World, hero: Entity, ride: RidePlan) -> None:
    hero.memes["joy"] += 1
    hero.memes["desire"] += 1
    world.say(
        f"On {ride.opening}, {hero.id} woke with a grin so wide it could have held a sunrise on each cheek."
    )
    world.say(ride.boast)
    world.say(
        f"{hero.id} was a {hero.traits[0]} little {hero.type} who wanted to ride that bike so badly that even the shoelaces seemed ready to clap."
    )


def discover_issue(world: World, hero: Entity, issue: SkinIssue) -> None:
    spot = world.get("spot")
    world.say(
        f"But just as {hero.pronoun()} reached for the handlebars, {issue.cause}. The {issue.label} on {hero.pronoun('possessive')} {issue.place} began to itch."
    )
    world.say(issue.warning)
    world.say(
        f'{hero.id} thought, "Oh dear. If my {issue.place} keeps fussing like this, how can I ride my bike clear to glory?"'
    )


def inner_monologue(world: World, hero: Entity) -> None:
    if hero.memes["confusion"] >= THRESHOLD:
        world.say(
            f'Then {hero.id} stared at the tube on the porch step and thought, "Hydrocortisone is a mighty long word. Is it for horses? Is it for storms? How is a person supposed to understand a word with so many corners?"'
        )


def kind_explain(world: World, helper: Entity, hero: Entity, explanation: Explanation) -> None:
    hero.memes["explained"] += 1
    hero.memes["clarity"] += float(explanation.clarity)
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.label_word.capitalize()} knelt so {helper.pronoun()} was eye to eye with {hero.id}. "
        f'"{explanation.kindness_line} {explanation.metaphor}"'
    )
    propagate(world, narrate=False)
    if hero.memes["understand"] >= THRESHOLD:
        world.say(
            f'{hero.id} blinked, then nodded. "Oh! I understand. The hydrocortisone is for the itch, not for making the bike go faster."'
        )


def apply_cream(world: World, helper: Entity, hero: Entity, issue: SkinIssue) -> None:
    spot = world.get("spot")
    spot.meters["cream"] += 1
    world.say(
        f"So {helper.label_word} dabbed on a little hydrocortisone cream, gentle as a cloud touching a fence post, right on the itchy {issue.place}."
    )
    world.say(
        f"{hero.id} held very still, because being trusted to hold still felt almost as brave as riding downhill with the wind cheering."
    )


def wait_for_relief(world: World, hero: Entity, wait: int) -> None:
    world.facts["wait"] = wait
    world.say(
        f"They waited {wait} minute{'s' if wait != 1 else ''} on the porch steps, counting sparrows, clouds, and one very nosy ladybug."
    )
    propagate(world, narrate=False)
    if hero.memes["relief"] >= THRESHOLD:
        world.say(
            f"Little by little, the itch stopped acting like a brass band and settled down to a whisper."
        )


def ride_out(world: World, hero: Entity, helper: Entity, ride: RidePlan) -> None:
    world.say(
        f"Soon {hero.id} pushed off and rode {ride.course}. The wheels hummed, the breeze patted {hero.pronoun('possessive')} hair, and the day felt right-sized again."
    )
    world.say(
        f"{helper.label_word.capitalize()} waved from the porch, pleased not because the problem had been grand, but because kindness had made it small."
    )
    world.say(ride.finish)


def tell(
    ride: RidePlan,
    issue: SkinIssue,
    explanation: Explanation,
    helper_key: str,
    hero_name: str,
    hero_gender: str,
    trait: str,
    wait: int,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            traits=[trait],
        )
    )
    helper_cfg = HELPERS[helper_key]
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg["type"],
            label=helper_cfg["type"],
            phrase=helper_cfg["type"],
            role=helper_cfg["role"],
        )
    )
    spot = world.add(
        Entity(
            id="spot",
            type="skin_issue",
            label=issue.label,
            phrase=issue.label,
            attrs={"place": issue.place},
        )
    )

    hero.memes["confusion"] = 2.0
    spot.meters["itch"] = 1.0
    world.facts["relief_need"] = issue.relief_need

    opening(world, hero, ride)
    world.para()
    discover_issue(world, hero, issue)
    inner_monologue(world, hero)
    world.para()
    kind_explain(world, helper, hero, explanation)
    apply_cream(world, helper, hero, issue)
    wait_for_relief(world, hero, wait)
    world.para()
    ride_out(world, hero, helper, ride)

    world.facts.update(
        hero=hero,
        helper=helper,
        ride=ride,
        issue=issue,
        explanation=explanation,
        understood=hero.memes["understand"] >= THRESHOLD,
        relieved=hero.memes["relief"] >= THRESHOLD,
        ready=hero.memes["confidence"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "hydrocortisone": [
        (
            "What is hydrocortisone cream for?",
            "Hydrocortisone cream is a medicine cream that can help calm itchy, irritated skin. A grown-up should choose and use it the right way.",
        )
    ],
    "mosquito": [
        (
            "Why do mosquito bites itch?",
            "A mosquito bite itches because your skin reacts to the tiny bite. The body notices it and the spot can feel annoying for a while.",
        )
    ],
    "plant": [
        (
            "Why can nettles make skin sting and itch?",
            "Some plants like nettles can bother your skin when you brush against them. That can leave a stingy, itchy patch.",
        )
    ],
    "rash": [
        (
            "What is a rash?",
            "A rash is a patch of skin that looks or feels irritated. It can be red, itchy, or bumpy.",
        )
    ],
    "bike": [
        (
            "Why is it important to feel comfortable before riding a bike?",
            "When your body feels calm and comfortable, it is easier to pay attention and ride safely. Small problems are easier to solve before the ride starts.",
        )
    ],
    "medicine": [
        (
            "Why should a grown-up explain medicine in simple words?",
            "Simple words help children understand what the medicine is for and what will happen next. Understanding can make a child feel calmer and braver.",
        )
    ],
    "kindness": [
        (
            "How can kindness help when someone is worried?",
            "Kindness helps by making the worried person feel safe and listened to. When someone feels safe, it is easier to think and understand.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hydrocortisone", "mosquito", "plant", "rash", "bike", "medicine", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    ride = f["ride"]
    issue = f["issue"]
    return [
        f'Write a tall-tale style story for a 3-to-5-year-old that includes the words "hydrocortisone", "bike", and "understand".',
        f"Tell a kind story where a little {hero.type} wants to ride a bike for {ride.id}, gets an itchy {issue.label}, and a gentle {helper.label_word} explains hydrocortisone so the child can understand.",
        "Write a happy-ending story with inner monologue where a child worries about a big medicine word, then learns what it means and rides off smiling.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    ride = f["ride"]
    issue = f["issue"]
    explanation = f["explanation"]
    wait = int(world.facts.get("wait", 0))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little {hero.type} who wanted to ride a bike, and {helper.label_word}, who helped with an itchy {issue.label}.",
        ),
        (
            "What problem came before the ride?",
            f"An itchy {issue.label} on {hero.label}'s {issue.place} started bothering {hero.pronoun('object')} just as the ride was about to begin. The itch made {hero.pronoun('object')} worry that the big bike day might be spoiled.",
        ),
        (
            f"Why did {hero.label} not understand the hydrocortisone at first?",
            f"{hero.label} only heard a very big word and did not know what it was for. In {hero.pronoun('possessive')} inner monologue, the word sounded strange and confusing, so {hero.pronoun()} needed someone kind to explain it.",
        ),
        (
            f"How did {helper.label_word} help {hero.label} understand?",
            f"{helper.label_word.capitalize()} knelt down, spoke gently, and explained hydrocortisone in simple words. The explanation worked because it matched the itchy problem and made the big word feel smaller.",
        ),
        (
            "What happened after they waited?",
            f"They waited {wait} minutes, and the itch settled down. Because the cream had time to help, {hero.label} felt calm enough to ride happily.",
        ),
        (
            "How did the story end?",
            f"It ended happily with {hero.label} riding {ride.course}. The ending proves what changed: {hero.pronoun().capitalize()} understood the hydrocortisone, the itch eased, and the big day could continue.",
        ),
    ]
    if explanation.style == "story":
        qa.append(
            (
                "What kind of explanation did the helper use?",
                f"{helper.label_word.capitalize()} used a playful picture, calling hydrocortisone a soft librarian for itchy skin. That kind image helped {hero.label} understand what the cream was doing.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"bike", "kindness"} | set(world.facts["issue"].tags) | set(world.facts["explanation"].tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        ride="parade",
        issue="mosquito_bite",
        explanation="story",
        helper="grandfather",
        hero_name="June",
        hero_gender="girl",
        trait="eager",
        wait=2,
    ),
    StoryParams(
        ride="bakery",
        issue="nettle_brush",
        explanation="plain",
        helper="mother",
        hero_name="Otis",
        hero_gender="boy",
        trait="curious",
        wait=2,
    ),
    StoryParams(
        ride="pond",
        issue="soap_rash",
        explanation="story",
        helper="aunt",
        hero_name="Pearl",
        hero_gender="girl",
        trait="thoughtful",
        wait=3,
    ),
]


def explain_issue_rejection(issue: SkinIssue) -> str:
    if issue.open_skin:
        return (
            f"(No story: {issue.label} is an open skin problem, and hydrocortisone is not the sensible choice for that. "
            f"Pick an itchy irritation such as mosquito_bite, nettle_brush, or soap_rash.)"
        )
    return f"(No story: {issue.label} is not an itchy irritation that fits hydrocortisone.)"


def explain_explanation_rejection(explanation: Explanation) -> str:
    return (
        f"(No story: the '{explanation.id}' explanation is too unclear for the child to understand "
        f"(clarity={explanation.clarity} < {CLARITY_MIN}). This world requires a kind, understandable explanation.)"
    )


def explain_wait_rejection(issue: SkinIssue, wait: int) -> str:
    return (
        f"(No story: waiting {wait} minute{'s' if wait != 1 else ''} is too short for a {issue.label}. "
        f"This story needs enough time for the hydrocortisone to help before the bike ride.)"
    )


def outcome_of(params: StoryParams) -> str:
    issue = ISSUES[params.issue]
    explanation = EXPLANATIONS[params.explanation]
    if not explanation_clear(explanation):
        return "puzzled"
    if not wait_enough(issue, params.wait):
        return "still_itchy"
    return "happy"


ASP_RULES = r"""
treatable(I) :- issue(I), itchy(I), not open_skin(I).
clear(E) :- explanation(E), clarity(E, C), clarity_min(M), C >= M.
valid(R, I, E) :- ride(R), treatable(I), clear(E), issue(I), explanation(E).

happy :- chosen_issue(I), chosen_explanation(E), clear(E),
         relief_need(I, Need), wait(W), W >= Need.
puzzled :- chosen_explanation(E), not clear(E).
still_itchy :- chosen_explanation(E), clear(E),
               chosen_issue(I), relief_need(I, Need), wait(W), W < Need.

outcome(happy) :- happy.
outcome(puzzled) :- puzzled.
outcome(still_itchy) :- still_itchy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ride_id in RIDES:
        lines.append(asp.fact("ride", ride_id))
    for issue_id, issue in ISSUES.items():
        lines.append(asp.fact("issue", issue_id))
        if issue.itchy:
            lines.append(asp.fact("itchy", issue_id))
        if issue.open_skin:
            lines.append(asp.fact("open_skin", issue_id))
        lines.append(asp.fact("relief_need", issue_id, issue.relief_need))
    for exp_id, exp in EXPLANATIONS.items():
        lines.append(asp.fact("explanation", exp_id))
        lines.append(asp.fact("clarity", exp_id, exp.clarity))
    lines.append(asp.fact("clarity_min", CLARITY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_issue", params.issue),
            asp.fact("chosen_explanation", params.explanation),
            asp.fact("wait", params.wait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED) + [
        StoryParams(
            ride="parade",
            issue="mosquito_bite",
            explanation="plain",
            helper="mother",
            hero_name="Test",
            hero_gender="girl",
            trait="bright",
            wait=1,
        ),
        StoryParams(
            ride="pond",
            issue="soap_rash",
            explanation="hurried",
            helper="aunt",
            hero_name="Test",
            hero_gender="boy",
            trait="hopeful",
            wait=3,
        ),
    ]
    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp_val = asp_outcome(params)
        if py != asp_val:
            mismatches.append((params, py, asp_val))
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for params, py, asp_val in mismatches:
            print(f"  {params} python={py} asp={asp_val}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child wants a bike ride, needs help understanding hydrocortisone, and gets a happy ending."
    )
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--explanation", choices=EXPLANATIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--wait", type=int, choices=[1, 2, 3])
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
    if args.issue:
        issue = ISSUES[args.issue]
        if not issue_treatable(issue):
            raise StoryError(explain_issue_rejection(issue))
    if args.explanation:
        explanation = EXPLANATIONS[args.explanation]
        if not explanation_clear(explanation):
            raise StoryError(explain_explanation_rejection(explanation))
    if args.issue and args.wait is not None:
        issue = ISSUES[args.issue]
        if not wait_enough(issue, args.wait):
            raise StoryError(explain_wait_rejection(issue, args.wait))

    combos = [
        combo
        for combo in valid_combos()
        if (args.ride is None or combo[0] == args.ride)
        and (args.issue is None or combo[1] == args.issue)
        and (args.explanation is None or combo[2] == args.explanation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ride_id, issue_id, explanation_id = rng.choice(sorted(combos))
    issue = ISSUES[issue_id]

    helper = args.helper or rng.choice(sorted(HELPERS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
        hero_name = rng.choice(pool)
    trait = rng.choice(TRAITS)

    if args.wait is not None:
        wait = args.wait
    else:
        wait = rng.choice([w for w in [1, 2, 3] if wait_enough(issue, w)])

    return StoryParams(
        ride=ride_id,
        issue=issue_id,
        explanation=explanation_id,
        helper=helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        trait=trait,
        wait=wait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ride not in RIDES:
        raise StoryError(f"(Invalid ride: {params.ride})")
    if params.issue not in ISSUES:
        raise StoryError(f"(Invalid issue: {params.issue})")
    if params.explanation not in EXPLANATIONS:
        raise StoryError(f"(Invalid explanation: {params.explanation})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")

    issue = ISSUES[params.issue]
    explanation = EXPLANATIONS[params.explanation]
    if not issue_treatable(issue):
        raise StoryError(explain_issue_rejection(issue))
    if not explanation_clear(explanation):
        raise StoryError(explain_explanation_rejection(explanation))
    if not wait_enough(issue, params.wait):
        raise StoryError(explain_wait_rejection(issue, params.wait))

    world = tell(
        ride=RIDES[params.ride],
        issue=issue,
        explanation=explanation,
        helper_key=params.helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        trait=params.trait,
        wait=params.wait,
    )

    story_text = world.render().replace("hero", world.facts["hero"].label)
    story_text = story_text.replace("helper", world.facts["helper"].label_word)

    story_text = story_text.replace(" hero ", f" {world.facts['hero'].label} ")
    story_text = story_text.replace(" hero.", f" {world.facts['hero'].label}.")
    story_text = story_text.replace(" helper ", f" {world.facts['helper'].label_word} ")
    story_text = story_text.replace(" helper.", f" {world.facts['helper'].label_word}.")

    hero_label = world.facts["hero"].label
    helper_word = world.facts["helper"].label_word
    story_text = story_text.replace("hero's", f"{hero_label}'s")
    story_text = story_text.replace("helper's", f"{helper_word}'s")

    return StorySample(
        params=params,
        story=story_text,
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
        print(f"{len(combos)} compatible (ride, issue, explanation) combos:\n")
        for ride_id, issue_id, explanation_id in combos:
            print(f"  {ride_id:8} {issue_id:14} {explanation_id}")
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
            header = f"### {p.hero_name}: {p.issue} before the {p.ride} ride"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
