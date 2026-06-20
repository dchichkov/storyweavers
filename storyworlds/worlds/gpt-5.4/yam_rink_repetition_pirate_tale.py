#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py
=============================================================

A standalone storyworld for a tiny pirate tale at a skating rink.

Premise
-------
Two children turn a rink into a shining pirate sea. One child wants to use a
real yam as pretend pirate treasure or a cannonball. On smooth ice, a hard round
yam can roll, make skaters wobble, and spoil the game. A wiser child or a calm
grown-up steers the play toward a soft, rink-safe substitute.

Why this world exists
---------------------
The seed asked for:
- the words "yam" and "rink"
- repetition
- a pirate-tale style

So this world builds a small simulation around those constraints instead of just
swapping nouns into one paragraph. The repeated chants come from state:
eager play, risky temptation, and a safer ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py --use cannonball
    python storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py --substitute foam_coin
    python storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py --response call_only
    python storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/yam_rink_repetition_pirate_tale.py --verify
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
# from a nested worlds/ subdirectory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    roundish: bool = False
    hard: bool = False
    rink_safe: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Rink:
    id: str
    place: str
    shine: str
    edge: str
    crowd_words: dict[int, str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Theme:
    id: str
    opening: str
    title_a: str
    title_b: str
    quest: str
    send_off: str


@dataclass
class Use:
    id: str
    purpose: str
    claim: str
    repeated: str
    danger: str
    roll_risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Substitute:
    id: str
    label: str
    phrase: str
    purposes: set[str]
    bounce: str
    rink_safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rolling_danger(world: World) -> list[str]:
    out: list[str] = []
    yam = world.entities.get("yam")
    if yam is None or yam.meters["rolling"] < THRESHOLD:
        return out
    sig = ("rolling_danger", "yam")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "rink" in world.entities:
        world.get("rink").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__rolling__")
    return out


CAUSAL_RULES = [
    Rule("rolling_danger", "physical", _r_rolling_danger),
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


def hazardous(use: Use) -> bool:
    return use.roll_risk > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def substitute_fits(use: Use, sub: Substitute) -> bool:
    return use.purpose in sub.purposes and sub.rink_safe


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for rink in RINKS:
        for theme in THEMES:
            for use_id, use in USES.items():
                if not hazardous(use):
                    continue
                for sub_id, sub in SUBSTITUTES.items():
                    if substitute_fits(use, sub):
                        combos.append((rink, theme, use_id, sub_id))
    return combos


def crowd_severity(use: Use, crowd: int) -> int:
    return use.roll_risk + crowd


def is_contained(response: Response, use: Use, crowd: int) -> bool:
    return response.power >= crowd_severity(use, crowd)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BOLDNESS_INIT


def predict_roll(world: World) -> dict:
    sim = world.copy()
    yam = sim.get("yam")
    yam.meters["rolling"] += 1
    propagate(sim, narrate=False)
    return {
        "rolling": yam.meters["rolling"] >= THRESHOLD,
        "danger": sim.get("rink").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, rink: Rink, theme: Theme, crowd: int) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.meters["gliding"] += 1
    crowd_text = rink.crowd_words[crowd]
    world.say(
        f"On a cold bright day, {a.id} and {b.id} stepped onto {rink.place}. "
        f"{rink.shine} Along the edge, {rink.edge}. {crowd_text}"
    )
    world.say(
        f"They decided the rink was not a rink at all but {theme.opening}. "
        f'"{theme.title_a} {a.id}! {theme.title_b} {b.id}!" {a.id} cried. '
        f'"{theme.quest}!"'
    )
    world.say('"Skate, skate, skate!" they sang as their blades whispered over the ice.')


def need_prop(world: World, b: Entity, use: Use) -> None:
    world.say(
        f"After a while, {b.id} said their pirate game still needed one more thing. "
        f"It needed {use.claim.lower()}."
    )


def tempt(world: World, a: Entity, use: Use) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"{a.id}'s eyes shone. "
        f'"I have just the thing," {a.pronoun()} said. '
        f'"A yam, a yam, a yam! {use.repeated}"'
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity, use: Use, crowd: int) -> None:
    pred = predict_roll(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    crowd_words = {0: "almost empty", 1: "busy enough", 2: "crowded"}
    extra = ""
    if crowd >= 1:
        extra = f" The rink was {crowd_words[crowd]}, so one rolling thing could bother lots of skates."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. '
        f'"No, {a.id}. A yam is hard and round, and on ice it can roll away. '
        f'{parent.label_word.capitalize()} said rink games must use soft things only."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, sub: Substitute) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["boldness"] = 0.0
    world.say(
        f'{a.id} looked at {b.id}, who was older and sounded very sure. '
        f'After one more breath, {a.pronoun()} tucked the yam back into the snack bag.'
    )
    world.say(
        f'Together they skated to the bench and showed {parent.label_word} the problem. '
        f'{parent.label_word.capitalize()} smiled and handed them {sub.phrase} instead.'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Just for one tiny sail," {a.id} said. {a.pronoun().capitalize()} balanced the yam in '
        f'{a.pronoun("possessive")} mitten and pushed away before {b.id} could stop {a.pronoun("object")}.'
    )


def drop_yam(world: World, a: Entity, use: Use) -> None:
    yam = world.get("yam")
    yam.meters["rolling"] += 1
    yam.meters["loose"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The yam slipped from {a.id}'s mitten and tapped the ice. "
        f"Roll, roll, roll -- away it went, spinning over the rink like a little brown ball."
    )
    world.say(use.danger)


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"The yam! The yam! The yam!" {b.id} shouted.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, sub: Substitute) -> None:
    yam = world.get("yam")
    yam.meters["rolling"] = 0.0
    world.get("rink").meters["danger"] = 0.0
    world.say(f"{parent.label_word.capitalize()} glided over and {response.text}.")
    world.say(
        f'"Hard things stay off the ice," {parent.pronoun()} said gently. '
        f'"But pirates may still play." Then {parent.pronoun()} offered them {sub.phrase}.'
    )


def tumble(world: World, parent: Entity, b: Entity, response: Response, sub: Substitute) -> None:
    b.meters["wobbly"] += 1
    b.meters["fallen"] += 1
    world.say(f"{parent.label_word.capitalize()} {response.fail}.")
    world.say(
        f"{b.id} sat down on the ice with a surprised little bump. "
        f"Tears sprang up, more shocked than hurt."
    )
    world.say(
        f'{parent.label_word.capitalize()} helped {b.id} stand, brushed off the knees, and rolled the yam away. '
        f'Then {parent.pronoun()} brought out {sub.phrase} for the game instead.'
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, use: Use) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} bent close so both children could hear. '
        f'"The rink is for skates and soft play props," {parent.pronoun()} said. '
        f'"A real yam can roll under someone and make a fall."'
    )
    world.say(
        f'"Pirates can be brave and careful at the same time," {parent.pronoun()} added. '
        f'"That is the best kind of captain."'
    )


def safe_end(world: World, a: Entity, b: Entity, theme: Theme, sub: Substitute, crowd: int) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.meters["gliding"] += 1
    if crowd >= 2:
        tail = "Around them, the busy rink kept humming, but now their game fit the ice."
    elif crowd == 1:
        tail = "Other skaters swept past, and nobody had to dodge a rolling yam again."
    else:
        tail = "The rink felt wide and peaceful again."
    world.say(
        f"Soon {a.id} and {b.id} were gliding side by side with {sub.phrase}. "
        f"{sub.bounce} {tail}"
    )
    world.say('"Safe and steady, safe and steady, safe and steady!" they sang.')
    world.say(f"And the little pirate crew {theme.send_off} -- not wild, but wise.")


def tell(
    rink: Rink,
    theme: Theme,
    use: Use,
    sub: Substitute,
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    crowd: int = 1,
    instigator_age: int = 5,
    cautioner_age: int = 7,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator, kind="character", type=instigator_gender, role="instigator",
        age=instigator_age, traits=["bold"], attrs={"relation": relation}
    ))
    b = world.add(Entity(
        id=cautioner, kind="character", type=cautioner_gender, role="cautioner",
        age=cautioner_age, traits=[trait], attrs={"relation": relation}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent", label="the parent"
    ))
    world.add(Entity(id="rink", type="rink", label="the rink"))
    world.add(Entity(id="yam", type="yam", label="yam", roundish=True, hard=True))
    world.add(Entity(id="prop", type="prop", label=sub.label, rink_safe=True))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    play_setup(world, a, b, rink, theme, crowd)
    need_prop(world, b, use)

    world.para()
    tempt(world, a, use)
    warn(world, b, a, parent, use, crowd)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent, sub)
        world.para()
        lesson(world, parent, a, b, use)
        safe_end(world, a, b, theme, sub, crowd)
        contained = True
        outcome = "averted"
    else:
        defy(world, a, b)
        world.para()
        drop_yam(world, a, use)
        alarm(world, b, parent)
        contained = is_contained(response, use, crowd)
        world.para()
        if contained:
            rescue(world, parent, response, sub)
            lesson(world, parent, a, b, use)
        else:
            tumble(world, parent, b, response, sub)
            lesson(world, parent, a, b, use)
        world.para()
        safe_end(world, a, b, theme, sub, crowd)
        outcome = "contained" if contained else "tumbled"

    world.facts.update(
        rink=rink,
        theme=theme,
        use=use,
        substitute=sub,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        crowd=crowd,
        relation=relation,
        outcome=outcome,
        contained=contained,
        severity=crowd_severity(use, crowd) if not averted else 0,
        rolled=world.get("yam").meters["loose"] >= THRESHOLD,
    )
    return world


RINKS = {
    "harbor": Rink(
        "harbor", "the town rink",
        "The ice shone like silver water under the lamps.",
        "red scarves and wool hats hung over the rail",
        {0: "Only a few skaters traced quiet loops.",
         1: "Families and children drifted here and there.",
         2: "Skaters swirled in every direction like busy fish."},
        tags={"rink", "ice"},
    ),
    "moon": Rink(
        "moon", "the moonlight rink",
        "The smooth ice gleamed pale as moonlit sea foam.",
        "mittens and boots rested on the benches nearby",
        {0: "The open space felt big enough for whispered games.",
         1: "Small groups passed in bright little clusters.",
         2: "The whole rink hummed with blades and laughter."},
        tags={"rink", "ice"},
    ),
}

THEMES = {
    "pirates": Theme(
        "pirates",
        "a glittering pirate sea",
        "Captain",
        "First Mate",
        "Let us sail for the hidden snack-island treasure",
        "sailed on toward their make-believe treasure"
    ),
    "corsairs": Theme(
        "corsairs",
        "a bright frozen ocean where brave pirates could voyage",
        "Captain",
        "Lookout",
        "Let us search for the secret cove",
        "glided after their secret cove prize"
    ),
}

USES = {
    "treasure": Use(
        "treasure",
        "treasure",
        "a pirate treasure chest",
        "This yam can be our treasure, our treasure, our treasure!",
        "One little skater nearby had to hop aside as the yam rolled past.",
        2,
        tags={"yam", "treasure", "safety"},
    ),
    "cannonball": Use(
        "cannonball",
        "cannon",
        "a pirate cannonball",
        "This yam can be our cannonball, our cannonball, our cannonball!",
        "Two skaters wobbled and spread their arms wide to keep from falling.",
        3,
        tags={"yam", "cannonball", "safety"},
    ),
}

SUBSTITUTES = {
    "beanbag_gem": Substitute(
        "beanbag_gem",
        "gold beanbag",
        "a soft gold beanbag shaped like treasure",
        {"treasure", "cannon"},
        "It landed with a soft plop whenever they passed it between them",
        tags={"beanbag", "safe_play"},
    ),
    "foam_coin": Substitute(
        "foam_coin",
        "foam coin",
        "a big foam coin painted yellow",
        {"treasure"},
        "It skimmed lightly in a mitten and never rolled far",
        tags={"foam", "safe_play"},
    ),
    "plush_parrot": Substitute(
        "plush_parrot",
        "plush parrot",
        "a tiny plush parrot with a sewn-on gold patch",
        {"treasure"},
        "It bobbed happily on {poss} sleeve without bumping anyone",
        tags={"plush", "safe_play"},
    ),
}

RESPONSES = {
    "glide_stop": Response(
        "glide_stop", 3, 4,
        "set one skate neatly in front of the runaway yam and stopped it before anyone fell",
        "tried to cut in front of the runaway yam, but it had already reached a wobbling skater",
        "stopped the rolling yam with one careful skate",
        tags={"coach", "stop_roll"},
    ),
    "bench_swap": Response(
        "bench_swap", 3, 3,
        "guided the children to the side, trapped the yam against the rail, and tucked it back into the snack bag",
        "hurried to the rail, but the yam had already slipped between two pairs of skates",
        "caught the yam against the rail and put it away",
        tags={"coach", "bench"},
    ),
    "call_only": Response(
        "call_only", 1, 1,
        "called from the side for everyone to watch out",
        "called out from the side, but the warning came too late to stop the wobble",
        "called out a warning",
        tags={"warning_only"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "steady", "sensible", "thoughtful", "curious", "gentle"]


@dataclass
class StoryParams:
    rink: str
    theme: str
    use: str
    substitute: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    crowd: int = 1
    instigator_age: int = 5
    cautioner_age: int = 7
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "yam": [(
        "What is a yam?",
        "A yam is a hard starchy vegetable that grows in the ground. It is food, not a skating toy."
    )],
    "rink": [(
        "What is a rink?",
        "A rink is a place for skating. People glide there, so the surface needs to stay clear and safe."
    )],
    "ice": [(
        "Why do things slide on ice?",
        "Ice is very smooth, so shoes and objects do not grip it well. That is why round things can roll quickly across it."
    )],
    "safety": [(
        "Why is a hard round thing unsafe on a skating rink?",
        "A hard round thing can roll under somebody's skates or make people swerve. On a rink, even a small rolling object can cause a fall."
    )],
    "beanbag": [(
        "Why is a beanbag safer than a yam on ice?",
        "A beanbag is soft and does not roll like a hard vegetable. If it drops, it usually stops close by and is less likely to trip someone."
    )],
    "foam": [(
        "Why can foam play props be good for children?",
        "Foam play props are light and soft. They let children pretend and play without the hard bumps of real objects."
    )],
    "plush": [(
        "Why is a plush toy gentle for pretend play?",
        "A plush toy is soft and squishy. It can still feel special in a game without being hard or slippery."
    )],
    "safe_play": [(
        "Can you still play a pirate game in a safe way?",
        "Yes. You can keep the fun part of the game and swap the unsafe object for a soft one that fits the place."
    )],
    "coach": [(
        "What does a skating coach or grown-up do at a rink?",
        "A grown-up watches for safety, helps children stay calm, and fixes small problems before they become big ones."
    )],
}
KNOWLEDGE_ORDER = ["yam", "rink", "ice", "safety", "coach", "beanbag", "foam", "plush", "safe_play"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["instigator"], f["cautioner"]
    use, rink, theme, sub = f["use"], f["rink"], f["theme"], f["substitute"]
    outcome = f["outcome"]
    base = (
        f'Write a short pirate tale for a 3-to-5-year-old that includes the words '
        f'"yam" and "rink" and uses repetition. Two children are skating and pretending '
        f'the rink is {theme.opening}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {a.id} wants to use a yam as {use.claim.lower()}, "
            f"but {b.id} talks {a.pronoun('object')} out of it before anything rolls away.",
            f'Write a repetitive pirate story that ends with the children using {sub.phrase} instead of a real yam.'
        ]
    if outcome == "tumbled":
        return [
            base,
            f"Tell a cautionary but comforting story where {a.id} ignores the warning, the yam rolls across the rink, and {b.id} has a small tumble before a grown-up helps.",
            f'Write a pirate-style rink story with repetition, a rolling yam problem, and a safe soft substitute in the ending.'
        ]
    return [
        base,
        f"Tell a gentle cautionary story where {a.id} ignores the warning, the yam rolls across the rink, and a calm grown-up stops it before anyone falls.",
        f'Write a repetitive pirate tale that teaches rink safety and ends with {sub.phrase} replacing the yam.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    rink, theme, use, sub, resp = f["rink"], f["theme"], f["use"], f["substitute"], f["response"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who pretend to be pirates at {rink.place}. {a.id}'s {pw} is there to help them stay safe."
        ),
        (
            "What were the children pretending the rink was?",
            f"They imagined the rink was {theme.opening}. That pirate game is why they wanted a special prop for their quest."
        ),
        (
            f"What did {a.id} want to use the yam for?",
            f"{a.id} wanted to use the yam as {use.claim.lower()}. The idea matched the pirate game, but it did not match the slippery ice."
        ),
        (
            f"Why did {b.id} say no?",
            f"{b.id} said no because a yam is hard and round, and on a rink it can roll away under someone's skates. The warning came from noticing the danger of the place, not from trying to spoil the fun."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after {b.id} warned {a.id}?",
            f"{a.id} listened and put the yam back into the snack bag, so no one had to dodge it. Then their {pw} gave them {sub.phrase} for the pirate game instead."
        ))
    elif f["outcome"] == "contained":
        body = resp.qa_text
        qa.append((
            f"How did {a.id}'s {pw} fix the problem?",
            f"{pw.capitalize()} {body}. After that, {pw} reminded them that the rink needs soft play props and offered {sub.phrase} instead."
        ))
    else:
        qa.append((
            "Did anyone get badly hurt?",
            f"No. {b.id} had a small tumble and some tears, but {pw} helped right away and made the rink safe again. The scary part ended with comfort, a lesson, and a better pirate prop."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the children skating side by side using {sub.phrase}. Their pirate game kept going, but in a way that fit the rink safely."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["rink"].tags) | set(f["use"].tags) | set(f["response"].tags) | set(f["substitute"].tags)
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("roundish", e.roundish), ("hard", e.hard), ("rink_safe", e.rink_safe)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        "harbor", "pirates", "treasure", "foam_coin", "glide_stop",
        "Tom", "boy", "Lily", "girl", "mother", "careful",
        crowd=1, instigator_age=5, cautioner_age=7, relation="siblings", trust=5
    ),
    StoryParams(
        "moon", "pirates", "cannonball", "beanbag_gem", "bench_swap",
        "Max", "boy", "Mia", "girl", "father", "curious",
        crowd=1, instigator_age=6, cautioner_age=5, relation="friends", trust=4
    ),
    StoryParams(
        "harbor", "corsairs", "cannonball", "beanbag_gem", "bench_swap",
        "Sam", "boy", "Zoe", "girl", "mother", "steady",
        crowd=2, instigator_age=6, cautioner_age=4, relation="siblings", trust=6
    ),
    StoryParams(
        "moon", "pirates", "treasure", "plush_parrot", "glide_stop",
        "Ella", "girl", "Nora", "girl", "father", "sensible",
        crowd=0, instigator_age=4, cautioner_age=6, relation="siblings", trust=7
    ),
]


def explain_rejection(use: Use, sub: Substitute) -> str:
    if use.purpose not in sub.purposes:
        return (
            f"(No story: {sub.phrase} does not fill the same pirate job as {use.claim.lower()}. "
            f"The safer replacement must still make sense for the game.)"
        )
    if not sub.rink_safe:
        return (
            f"(No story: {sub.phrase} is not marked rink-safe, so it cannot be the sensible fix.)"
        )
    return "(No story: this combination does not make a reasonable rink-safety tale.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). A calmer, more effective rink response is needed. "
        f"Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], USES[params.use], params.crowd) else "tumbled"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(U) :- use(U), roll_risk(U, R), R > 0.
compatible(U, S) :- use(U), substitute(S), purpose(U, P), serves(S, P), rink_safe(S).
valid(R, T, U, S) :- rink(R), theme(T), hazard(U), compatible(U, S).

% --- outcome inference -----------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), boldness_init(BI), A > BI.

severity(R + C) :- chosen_use(U), roll_risk(U, R), crowd(C).
resp_power(P) :- chosen_response(RS), power(RS, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(tumbled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in RINKS:
        lines.append(asp.fact("rink", rid))
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for uid, use in USES.items():
        lines.append(asp.fact("use", uid))
        lines.append(asp.fact("purpose", uid, use.purpose))
        lines.append(asp.fact("roll_risk", uid, use.roll_risk))
    for sid, sub in SUBSTITUTES.items():
        lines.append(asp.fact("substitute", sid))
        if sub.rink_safe:
            lines.append(asp.fact("rink_safe", sid))
        for purpose in sorted(sub.purposes):
            lines.append(asp.fact("serves", sid, purpose))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{sensible_response_rules()}\n{ASP_RULES}\n{extra}\n{show}\n"


def sensible_response_rules() -> str:
    return "sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M."


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
        asp.fact("chosen_use", params.use),
        asp.fact("chosen_response", params.response),
        asp.fact("crowd", params.crowd),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "yam" not in sample.story.lower() or "rink" not in sample.story.lower():
            raise StoryError("smoke test story is missing required seed words")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate play at a rink, a rolling yam, and a safer swap."
    )
    ap.add_argument("--rink", choices=RINKS)
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--use", choices=USES)
    ap.add_argument("--substitute", choices=SUBSTITUTES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--crowd", type=int, choices=[0, 1, 2],
                    help="how busy the rink is; higher values make a rolling yam harder to stop")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.use and args.substitute:
        use, sub = USES[args.use], SUBSTITUTES[args.substitute]
        if not substitute_fits(use, sub):
            raise StoryError(explain_rejection(use, sub))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [c for c in valid_combos()
              if (args.rink is None or c[0] == args.rink)
              and (args.theme is None or c[1] == args.theme)
              and (args.use is None or c[2] == args.use)
              and (args.substitute is None or c[3] == args.substitute)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    rink, theme, use, substitute = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    crowd = args.crowd if args.crowd is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        rink, theme, use, substitute, response,
        instigator, ig, cautioner, cg, parent, trait,
        crowd=crowd, instigator_age=instigator_age, cautioner_age=cautioner_age,
        relation=relation, trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        RINKS[params.rink],
        THEMES[params.theme],
        USES[params.use],
        SUBSTITUTES[params.substitute],
        RESPONSES[params.response],
        params.instigator,
        params.instigator_gender,
        params.cautioner,
        params.cautioner_gender,
        params.trait,
        params.parent,
        params.crowd,
        params.instigator_age,
        params.cautioner_age,
        params.relation,
        params.trust,
    )

    story = world.render()
    if "{poss}" in story:
        poss = world.facts["instigator"].pronoun("possessive")
        story = story.replace("{poss}", poss)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (rink, theme, use, substitute) combos:\n")
        for rink, theme, use, sub in combos:
            print(f"  {rink:8} {theme:8} {use:10} {sub}")
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.use} at {p.rink} "
                f"({p.theme}, {p.substitute}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
