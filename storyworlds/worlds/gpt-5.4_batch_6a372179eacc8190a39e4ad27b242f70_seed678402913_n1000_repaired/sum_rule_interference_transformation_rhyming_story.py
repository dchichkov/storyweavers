#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sum_rule_interference_transformation_rhyming_story.py
================================================================================

A standalone storyworld for tiny rhyming math tales about a child building a
sum, meeting some interference, and solving the problem through a sensible
transformation of the materials.

The core world idea:
- A child and a friend make a visible sum with some physical math display.
- A simple counting rule gives the activity shape.
- An interference disturbs the display in a way the world model can track.
- A helper transforms the display into a steadier form that still shows the same sum.
- The ending image proves what changed: the numbers stay put, the rule still works,
  and the children can finish with confidence.

Run it
------
    python storyworlds/worlds/gpt-5.4/sum_rule_interference_transformation_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/sum_rule_interference_transformation_rhyming_story.py --display chalk_sum --interference wind
    python storyworlds/worlds/gpt-5.4/sum_rule_interference_transformation_rhyming_story.py --display block_sum --interference drip
    python storyworlds/worlds/gpt-5.4/sum_rule_interference_transformation_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/sum_rule_interference_transformation_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sum_rule_interference_transformation_rhyming_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
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
class Display:
    id: str
    label: str
    phrase: str
    place: str
    material: str
    item_word: str
    intro_line: str
    vulnerable_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Interference:
    id: str
    label: str
    phrase: str
    effect: str
    arrival: str
    damage: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    phrase: str
    accepts: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
    action: str = ""
    ending: str = ""
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


def _r_worry_from_mess(world: World) -> list[str]:
    display = world.entities.get("display")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not display or not hero or not friend:
        return []
    if display.meters["disturbed"] < THRESHOLD:
        return []
    sig = ("worry", "display")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    return []


def _r_relief_from_restore(world: World) -> list[str]:
    display = world.entities.get("display")
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    helper = world.entities.get("helper")
    if not display or not hero or not friend or not helper:
        return []
    if display.meters["stable"] < THRESHOLD or display.meters["sum_clear"] < THRESHOLD:
        return []
    sig = ("relief", "display")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    helper.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="worry_from_mess", tag="emotional", apply=_r_worry_from_mess),
    Rule(name="relief_from_restore", tag="emotional", apply=_r_relief_from_restore),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


DISPLAYS = {
    "chalk_sum": Display(
        id="chalk_sum",
        label="chalk sum",
        phrase="a bright chalk sum",
        place="beside the schoolyard slide",
        material="marks",
        item_word="chalk marks",
        intro_line="They drew little stars and numbers in a row, with pink and blue chalk in a soft afternoon glow.",
        vulnerable_to={"wind", "drip"},
        tags={"sum", "chalk"},
    ),
    "leaf_sum": Display(
        id="leaf_sum",
        label="leaf sum",
        phrase="a leaf sum",
        place="on a picnic blanket in the garden",
        material="loose",
        item_word="leaves",
        intro_line="They lined up red leaves and yellow leaves with care, making a neat little number trail there.",
        vulnerable_to={"wind", "puppy", "drip"},
        tags={"sum", "leaves"},
    ),
    "block_sum": Display(
        id="block_sum",
        label="block sum",
        phrase="a block sum",
        place="on the classroom rug",
        material="loose",
        item_word="blocks",
        intro_line="They stood up counting blocks, click-clack and square, building a tidy math tower in the bright room air.",
        vulnerable_to={"puppy"},
        tags={"sum", "blocks"},
    ),
}

INTERFERENCES = {
    "wind": Interference(
        id="wind",
        label="wind",
        phrase="a quick wind",
        effect="scatter",
        arrival="Then a quick wind skipped over the ground with a whoosh and a spin.",
        damage="The little pieces slid and twirled, and the neat line would not stay in.",
        tags={"wind", "interference"},
    ),
    "puppy": Interference(
        id="puppy",
        label="puppy tail",
        phrase="a puppy with a wagging tail",
        effect="scatter",
        arrival="Just then a puppy bounced by, all wiggle and whirl.",
        damage="One happy tail swished through the groups, and the counting line gave a curl.",
        tags={"puppy", "interference"},
    ),
    "drip": Interference(
        id="drip",
        label="rain drip",
        phrase="a fat rain drip from the eaves",
        effect="blur",
        arrival="Plip, plip, from the edge above came a fat rain drip with a silver gleam.",
        damage="The marks turned smudgy and soft at the edges, like numbers fading out of a dream.",
        tags={"rain", "interference"},
    ),
}

TRANSFORMATIONS = {
    "tile_swap": Transformation(
        id="tile_swap",
        label="number tiles",
        phrase="snapping number tiles onto a little board",
        accepts={"marks"},
        fixes={"blur"},
        action="traded the smeary marks for number tiles that snapped into place",
        ending="The numbers clicked and stayed, bright and square for the rest of the day.",
        tags={"tiles", "transformation"},
    ),
    "clip_cards": Transformation(
        id="clip_cards",
        label="clipped number cards",
        phrase="clipping number cards to a steady string",
        accepts={"loose", "marks"},
        fixes={"blur", "scatter"},
        action="changed the old display into clipped number cards on a steady string",
        ending="The cards hung still and neat, and no small bump could spoil the beat.",
        tags={"cards", "transformation"},
    ),
    "counting_tray": Transformation(
        id="counting_tray",
        label="counting tray",
        phrase="sorting the pieces into a counting tray",
        accepts={"loose"},
        fixes={"scatter"},
        action="changed the loose pieces into two snug rows inside a counting tray",
        ending="Each group sat in its own small bay, so the sum could stay and stay.",
        tags={"tray", "transformation"},
    ),
}


@dataclass
class StoryParams:
    display: str
    interference: str
    transformation: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    helper_type: str
    addend_a: int
    addend_b: int
    seed: Optional[int] = None


GIRL_NAMES = ["Lila", "Mina", "Ruby", "Nora", "Tess", "Ella", "Maya", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Theo", "Noah", "Eli", "Ben", "Leo"]


def interference_hits(display: Display, interference: Interference) -> bool:
    return interference.id in display.vulnerable_to


def transformation_fits(display: Display, interference: Interference, transformation: Transformation) -> bool:
    return (
        display.material in transformation.accepts
        and interference.effect in transformation.fixes
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for display_id, display in DISPLAYS.items():
        for interference_id, interference in INTERFERENCES.items():
            if not interference_hits(display, interference):
                continue
            for transformation_id, transformation in TRANSFORMATIONS.items():
                if transformation_fits(display, interference, transformation):
                    combos.append((display_id, interference_id, transformation_id))
    return sorted(combos)


def explain_rejection(display: Display, interference: Interference, transformation: Optional[Transformation] = None) -> str:
    if not interference_hits(display, interference):
        return (
            f"(No story: {interference.phrase} would not make believable interference "
            f"for {display.phrase} {display.place}. Pick an interference that can really disturb it.)"
        )
    if transformation is not None and not transformation_fits(display, interference, transformation):
        return (
            f"(No story: {transformation.label} does not sensibly fix {interference.effect} "
            f"problems for a {display.material} display. The transformation must make the sum steadier.)"
        )
    return "(No story: this combination is not reasonable in this little world.)"


def predict_disturbance(world: World, interference: Interference) -> dict:
    sim = world.copy()
    display = sim.get("display")
    if interference.effect == "scatter":
        display.meters["order"] -= 1
        display.meters["visible"] -= 0.5
    else:
        display.meters["visible"] -= 1
    display.meters["disturbed"] += 1
    propagate(sim, narrate=False)
    return {
        "disturbed": display.meters["disturbed"] >= THRESHOLD,
        "visible": display.meters["visible"],
        "worry": sim.get("hero").memes["worry"],
    }


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def introduce(world: World, hero: Entity, friend: Entity, helper: Entity, display: Display) -> None:
    world.say(
        f"{hero.id} and {friend.id} sat {display.place}, bright-eyed with a counting hum."
    )
    world.say(
        f"{hero.id}'s {helper.label_word} watched nearby while the afternoon felt calm and plummy."
    )
    world.say(display.intro_line)


def build_sum(world: World, hero: Entity, friend: Entity, display: Display, a: int, b: int) -> None:
    display_ent = world.get("display")
    display_ent.meters["order"] = 1.0
    display_ent.meters["visible"] = 1.0
    display_ent.meters["sum_clear"] = 1.0
    hero.memes["pride"] += 1
    friend.memes["joy"] += 1
    total = a + b
    world.say(
        f'"{a} here and {b} there make {total} in all, that is our sum rule, clear and small," '
        f"{hero.id} sang."
    )
    world.say(
        f"{friend.id} tapped each group once and then the whole row once more. "
        f"Their rule was simple: count the parts, then count the total at the end of the score."
    )


def warn(world: World, friend: Entity, interference: Interference) -> None:
    pred = predict_disturbance(world, interference)
    world.facts["predicted_visible"] = pred["visible"]
    if interference.effect == "scatter":
        world.say(
            f'{friend.id} tilted {friend.pronoun("possessive")} head. "That looks like interference," '
            f'{friend.pronoun()} said. "If it bumps our groups apart, the rule will be hard to see."'
        )
    else:
        world.say(
            f'{friend.id} peered up. "That looks like interference," {friend.pronoun()} said. '
            f'"If the numbers blur, our sum rule may hide from us."'
        )


def disturb(world: World, display: Entity, interference: Interference) -> None:
    display.meters["disturbed"] += 1
    display.meters["sum_clear"] = 0.0
    if interference.effect == "scatter":
        display.meters["order"] -= 1
        display.meters["visible"] -= 0.5
    else:
        display.meters["visible"] -= 1
    propagate(world, narrate=False)
    world.say(interference.arrival)
    world.say(interference.damage)


def react(world: World, hero: Entity, friend: Entity, display: Display) -> None:
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id} hugged {hero.pronoun('possessive')} knees. "
            f'"Oh dear," {hero.pronoun()} whispered. "Our {display.label} was neat, and now it is not clear."'
        )
    if friend.memes["worry"] >= THRESHOLD:
        world.say(
            f"{friend.id} nodded and looked at the groups again. "
            f"The answer had not changed, but the picture had slipped out of shape."
        )


def transform(world: World, helper: Entity, display: Entity, transformation: Transformation) -> None:
    display.attrs["transformed_into"] = transformation.id
    display.meters["stable"] = 1.0
    display.meters["visible"] = 1.0
    display.meters["order"] = 1.0
    display.meters["sum_clear"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} knelt beside them and smiled a quiet smile. "
        f"{helper.pronoun().capitalize()} did not change the answer. "
        f"{helper.pronoun().capitalize()} {transformation.action}."
    )
    world.say(
        f'"A good transformation keeps the same sum but gives it a steadier home," '
        f"{helper.pronoun()} said."
    )


def finish(world: World, hero: Entity, friend: Entity, helper: Entity,
           transformation: Transformation, a: int, b: int) -> None:
    total = a + b
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Then {hero.id} counted {a}, {friend.id} counted {b}, and together they counted {total} with a happy thumb."
    )
    world.say(
        f'{hero.id} laughed. "The interference made a muddle, but the rule still led us through."'
    )
    world.say(
        f"{transformation.ending} Beside them, {helper.label_word} nodded, and the little math song felt new."
    )


def tell(params: StoryParams) -> World:
    display_cfg = DISPLAYS[params.display]
    interference_cfg = INTERFERENCES[params.interference]
    transformation_cfg = TRANSFORMATIONS[params.transformation]

    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        role="hero",
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        role="friend",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label="the helper",
        role="helper",
    ))
    display = world.add(Entity(
        id="display",
        kind="thing",
        type="display",
        label=display_cfg.label,
        phrase=display_cfg.phrase,
        role="display",
        attrs={"material": display_cfg.material},
        tags=set(display_cfg.tags),
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        display_cfg=display_cfg,
        interference_cfg=interference_cfg,
        transformation_cfg=transformation_cfg,
        addend_a=params.addend_a,
        addend_b=params.addend_b,
        total=params.addend_a + params.addend_b,
    )

    introduce(world, hero, friend, helper, display_cfg)
    build_sum(world, hero, friend, display_cfg, params.addend_a, params.addend_b)

    world.para()
    warn(world, friend, interference_cfg)
    disturb(world, display, interference_cfg)
    react(world, hero, friend, display_cfg)

    world.para()
    transform(world, helper, display, transformation_cfg)
    finish(world, hero, friend, helper, transformation_cfg, params.addend_a, params.addend_b)

    world.facts.update(
        disturbed=display.meters["disturbed"] >= THRESHOLD,
        restored=display.meters["stable"] >= THRESHOLD and display.meters["sum_clear"] >= THRESHOLD,
        transformed_into=display.attrs.get("transformed_into", ""),
    )
    return world


KNOWLEDGE = {
    "sum": [
        (
            "What is a sum?",
            "A sum is the total you get when you add numbers together. If you have two things and then three more things, the sum is five."
        )
    ],
    "rule": [
        (
            "What is a rule in a math game?",
            "A rule is a small plan you follow the same way each time. In a counting game, a rule can help you keep numbers neat and easy to check."
        )
    ],
    "interference": [
        (
            "What does interference mean?",
            "Interference means something gets in the way of what you are trying to do. It can make a neat job harder until you fix the problem."
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is a change from one form into another form. In this story, the math idea stayed the same even when the display changed."
        )
    ],
    "wind": [
        (
            "How can wind change little objects?",
            "Wind can push light things and scatter them around. That is why small loose pieces can slide out of place."
        )
    ],
    "puppy": [
        (
            "Why can a puppy make a counting game messy?",
            "A playful puppy can bump things with paws or a wagging tail. That kind of happy movement can jumble a careful arrangement."
        )
    ],
    "rain": [
        (
            "What happens when rain drips on chalk?",
            "Rain can make chalk soft and smudgy. Then the numbers are harder to see clearly."
        )
    ],
    "tiles": [
        (
            "Why are number tiles easy to read?",
            "Number tiles have firm shapes that do not smear like chalk. They stay clear when they are snapped into place."
        )
    ],
    "cards": [
        (
            "Why do clipped cards stay tidy?",
            "Clips hold the cards where they belong. That helps the groups stay in order even when something bumps nearby."
        )
    ],
    "tray": [
        (
            "Why does a counting tray help?",
            "A counting tray gives each group its own little space. That keeps the pieces from sliding into each other."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sum",
    "rule",
    "interference",
    "transformation",
    "wind",
    "puppy",
    "rain",
    "tiles",
    "cards",
    "tray",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    display = f["display_cfg"]
    interference = f["interference_cfg"]
    transformation = f["transformation_cfg"]
    total = f["total"]
    hero = f["hero"]
    return [
        (
            f'Write a short rhyming story for a 3-to-5-year-old that uses the words '
            f'"sum," "rule," and "interference," and includes a helpful transformation.'
        ),
        (
            f"Tell a gentle math story where {hero.label} builds {display.phrase} and "
            f"{interference.phrase} causes interference, but a grown-up transforms the display into "
            f"{transformation.label} so the sum still comes out to {total}."
        ),
        (
            f"Write a child-facing rhyming story about a counting problem that is not solved by arguing, "
            f"but by changing the materials into a steadier form."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    display = f["display_cfg"]
    interference = f["interference_cfg"]
    transformation = f["transformation_cfg"]
    a = f["addend_a"]
    b = f["addend_b"]
    total = f["total"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label}, who were making {display.phrase}, and {hero.pronoun('possessive')} {helper.label_word} who helped them. They were trying to show a math idea in a clear, happy way."
        ),
        (
            "What was the sum in the story?",
            f"The children were adding {a} and {b}, and the sum was {total}. They used a counting rule to keep the two groups clear before counting the whole amount."
        ),
        (
            "What was the rule they followed?",
            f"They counted one group, then the other group, and then counted the whole set to find the sum. That rule helped them check the answer in an orderly way."
        ),
        (
            "What caused the interference?",
            f"The interference came from {interference.phrase}. It disturbed the display, so the answer stayed the same but the picture was harder to read."
        ),
    ]
    if f.get("restored"):
        qa.append(
            (
                "How did they solve the problem?",
                f"{hero.pronoun('possessive').capitalize()} {helper.label_word} used a transformation and changed the math display into {transformation.label}. The form changed, but the same sum still showed clearly, so the children could finish with confidence."
            )
        )
        qa.append(
            (
                "Did the answer change after the transformation?",
                f"No, the answer did not change. The transformation only changed how the sum was shown, which made it easier to see after the interference."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the numbers steady and clear again, and the children counting all the way to {total}. The final image shows that the transformed display could hold the rule in place."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sum", "rule", "interference", "transformation"}
    tags |= set(f["interference_cfg"].tags)
    tags |= set(f["transformation_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        display="chalk_sum",
        interference="drip",
        transformation="tile_swap",
        hero_name="Lila",
        hero_type="girl",
        friend_name="Milo",
        friend_type="boy",
        helper_type="mother",
        addend_a=2,
        addend_b=3,
    ),
    StoryParams(
        display="leaf_sum",
        interference="wind",
        transformation="counting_tray",
        hero_name="Owen",
        hero_type="boy",
        friend_name="Ruby",
        friend_type="girl",
        helper_type="father",
        addend_a=4,
        addend_b=1,
    ),
    StoryParams(
        display="leaf_sum",
        interference="puppy",
        transformation="clip_cards",
        hero_name="Mina",
        hero_type="girl",
        friend_name="Ben",
        friend_type="boy",
        helper_type="mother",
        addend_a=3,
        addend_b=2,
    ),
    StoryParams(
        display="chalk_sum",
        interference="wind",
        transformation="clip_cards",
        hero_name="Theo",
        hero_type="boy",
        friend_name="Ivy",
        friend_type="girl",
        helper_type="teacher",
        addend_a=1,
        addend_b=5,
    ),
    StoryParams(
        display="block_sum",
        interference="puppy",
        transformation="counting_tray",
        hero_name="Nora",
        hero_type="girl",
        friend_name="Finn",
        friend_type="boy",
        helper_type="teacher",
        addend_a=2,
        addend_b=4,
    ),
]


ASP_RULES = r"""
interference_hits(D, I) :- vulnerable(D, I).
transformation_fits(D, I, T) :- display(D), interference(I), transformation(T),
                                material(D, M), accepts(T, M),
                                effect(I, E), fixes(T, E).
valid(D, I, T) :- interference_hits(D, I), transformation_fits(D, I, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for display_id, display in DISPLAYS.items():
        lines.append(asp.fact("display", display_id))
        lines.append(asp.fact("material", display_id, display.material))
        for interference_id in sorted(display.vulnerable_to):
            lines.append(asp.fact("vulnerable", display_id, interference_id))
    for interference_id, interference in INTERFERENCES.items():
        lines.append(asp.fact("interference", interference_id))
        lines.append(asp.fact("effect", interference_id, interference.effect))
    for transformation_id, transformation in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", transformation_id))
        for material in sorted(transformation.accepts):
            lines.append(asp.fact("accepts", transformation_id, material))
        for effect in sorted(transformation.fixes):
            lines.append(asp.fact("fixes", transformation_id, effect))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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

    smoke_cases = list(CURATED[:3])
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(11))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: could not resolve default params: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            lower = sample.story.lower()
            for word in ("sum", "rule", "interference"):
                if word not in lower:
                    raise StoryError(f"story missing required word '{word}'")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL on case {idx}: {err}")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a child builds a sum, interference arrives, and a transformation saves the day."
    )
    ap.add_argument("--display", choices=sorted(DISPLAYS))
    ap.add_argument("--interference", choices=sorted(INTERFERENCES))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "teacher"])
    ap.add_argument("--addend-a", type=int, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--addend-b", type=int, choices=[1, 2, 3, 4, 5])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.display and args.interference:
        display = DISPLAYS[args.display]
        interference = INTERFERENCES[args.interference]
        if not interference_hits(display, interference):
            raise StoryError(explain_rejection(display, interference))
    if args.display and args.interference and args.transformation:
        display = DISPLAYS[args.display]
        interference = INTERFERENCES[args.interference]
        transformation = TRANSFORMATIONS[args.transformation]
        if not transformation_fits(display, interference, transformation):
            raise StoryError(explain_rejection(display, interference, transformation))

    combos = [
        combo for combo in valid_combos()
        if (args.display is None or combo[0] == args.display)
        and (args.interference is None or combo[1] == args.interference)
        and (args.transformation is None or combo[2] == args.transformation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    display_id, interference_id, transformation_id = rng.choice(combos)

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type, avoid=hero_name)
    helper_type = args.helper or rng.choice(["mother", "father", "teacher"])
    addend_a = args.addend_a if args.addend_a is not None else rng.randint(1, 5)
    addend_b = args.addend_b if args.addend_b is not None else rng.randint(1, 5)

    return StoryParams(
        display=display_id,
        interference=interference_id,
        transformation=transformation_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        helper_type=helper_type,
        addend_a=addend_a,
        addend_b=addend_b,
    )


def generate(params: StoryParams) -> StorySample:
    if params.display not in DISPLAYS:
        raise StoryError(f"(Unknown display: {params.display})")
    if params.interference not in INTERFERENCES:
        raise StoryError(f"(Unknown interference: {params.interference})")
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError(f"(Unknown transformation: {params.transformation})")

    display = DISPLAYS[params.display]
    interference = INTERFERENCES[params.interference]
    transformation = TRANSFORMATIONS[params.transformation]

    if not interference_hits(display, interference):
        raise StoryError(explain_rejection(display, interference))
    if not transformation_fits(display, interference, transformation):
        raise StoryError(explain_rejection(display, interference, transformation))

    world = tell(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (display, interference, transformation) combos:\n")
        for display, interference, transformation in combos:
            print(f"  {display:12} {interference:12} {transformation}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.display} + {p.interference} -> {p.transformation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
