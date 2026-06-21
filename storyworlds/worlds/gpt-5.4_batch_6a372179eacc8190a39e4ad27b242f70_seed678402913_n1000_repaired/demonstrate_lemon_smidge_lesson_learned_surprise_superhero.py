#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/demonstrate_lemon_smidge_lesson_learned_surprise_superhero.py
=========================================================================================

A standalone story world about a child superhero who wants to demonstrate a
small "rescue science" trick with lemon. The world prefers careful, reasonable
choices: a hard sticky gadget can be cleaned with just a smidge of lemon, while
a paper or plush target is rejected because lemon would ruin it. Some stories
stay neat; others have a small spill first, then turn into a lesson learned.

The prose is driven by simulated state:
- typed entities with physical meters and emotional memes
- a simple forward-chaining rule engine
- a Python reasonableness gate plus an ASP twin
- state-grounded prompts and Q&A
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
# from a nested world directory like storyworlds/worlds/gpt-5.4/.
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
    acid_safe: bool = False
    absorbent: bool = False
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
class Mission:
    id: str
    base: str
    opening: str
    call: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    material: str
    mess: str
    hidden: str
    reveal: str
    acid_safe: bool = False
    absorbent: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def The(self) -> str:
        return f"The {self.label}"


@dataclass
class Amount:
    id: str
    label: str
    sense: int
    drops: int
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cloth:
    id: str
    label: str
    phrase: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_reveal(world: World) -> list[str]:
    target = world.get("target")
    if target.meters["clean"] < THRESHOLD:
        return []
    sig = ("reveal", "target")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["revealed"] += 1
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    hero.memes["wonder"] += 1
    sidekick.memes["joy"] += 1
    return ["__reveal__"]


def _r_spill_feelings(world: World) -> list[str]:
    table = world.get("table")
    if table.meters["mess"] < THRESHOLD:
        return []
    sig = ("spill_feelings", "table")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    hero.memes["oops"] += 1
    sidekick.memes["concern"] += 1
    return ["__spill__"]


CAUSAL_RULES = [
    Rule(name="reveal", tag="physical", apply=_r_reveal),
    Rule(name="spill_feelings", tag="social", apply=_r_spill_feelings),
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
        for sent in produced:
            world.say(sent)
    return produced


MISSIONS = {
    "roof_watch": Mission(
        id="roof_watch",
        base="the blanket-draped couch they called Skywatch Tower",
        opening="The city below was only a row of shoes by the door and a sleepy lamp, but in their game it was a whole town waiting for heroes.",
        call="Tonight's mission was to get one sticky hero tool ready for a brave little show.",
        closing="they struck their rooftop poses and promised to save the city with careful hands",
        tags={"superhero"},
    ),
    "kitchen_lab": Mission(
        id="kitchen_lab",
        base="the kitchen table they had renamed the Citrus Command Lab",
        opening="A dish towel became a cape, a mixing bowl became a signal dish, and every chair looked like mission control.",
        call="Tonight's mission was to make one sticky gadget ready before family hero hour.",
        closing="they clicked their capes behind them and grinned like science heroes",
        tags={"superhero", "science"},
    ),
    "hallway_hq": Mission(
        id="hallway_hq",
        base="the hallway bench they called Lightning Hall",
        opening="Boots lined up under the bench like sleeping rocket ships, and the mirror at the end of the hall looked like a giant hero screen.",
        call="Tonight's mission was to shine up one messy rescue tool before the evening parade through the house.",
        closing="they marched down the hall as if the whole house were cheering",
        tags={"superhero"},
    ),
}

TARGETS = {
    "signal_button": Target(
        id="signal_button",
        label="signal button",
        phrase="a round metal signal button",
        material="metal",
        mess="jam",
        hidden="a little stuck patch of red jam",
        reveal="a bright gold lightning bolt hidden underneath",
        acid_safe=True,
        absorbent=False,
        tags={"metal", "sticky"},
    ),
    "visor": Target(
        id="visor",
        label="rescue visor",
        phrase="a clear plastic rescue visor",
        material="plastic",
        mess="syrup",
        hidden="a cloudy stripe of syrup",
        reveal="tiny rainbow sparks dancing in the clear shine",
        acid_safe=True,
        absorbent=False,
        tags={"plastic", "sticky"},
    ),
    "badge": Target(
        id="badge",
        label="hero badge",
        phrase="a silver hero badge",
        material="metal",
        mess="honey",
        hidden="a tacky smear of honey",
        reveal="a silver star so shiny it looked almost awake",
        acid_safe=True,
        absorbent=False,
        tags={"metal", "sticky"},
    ),
    "paper_map": Target(
        id="paper_map",
        label="paper rescue map",
        phrase="a paper rescue map with hand-drawn streets",
        material="paper",
        mess="jam",
        hidden="a sticky thumbprint of jam",
        reveal="the secret route to the mayor's kitten",
        acid_safe=False,
        absorbent=True,
        tags={"paper"},
    ),
    "cape_patch": Target(
        id="cape_patch",
        label="cape patch",
        phrase="a fuzzy cape patch",
        material="cloth",
        mess="syrup",
        hidden="a sticky syrup spot",
        reveal="a tiny stitched comet",
        acid_safe=False,
        absorbent=True,
        tags={"cloth"},
    ),
}

AMOUNTS = {
    "smidge": Amount(
        id="smidge",
        label="a smidge",
        sense=3,
        drops=1,
        line='only a smidge of lemon would do the job',
        tags={"lemon", "careful"},
    ),
    "drip": Amount(
        id="drip",
        label="two careful drops",
        sense=3,
        drops=2,
        line='two careful drops of lemon would be enough',
        tags={"lemon", "careful"},
    ),
    "squeeze": Amount(
        id="squeeze",
        label="a big squeeze",
        sense=2,
        drops=5,
        line='one big squeeze would look more dramatic',
        tags={"lemon", "spill"},
    ),
    "pour": Amount(
        id="pour",
        label="a full pour",
        sense=1,
        drops=8,
        line='pouring lots of lemon would make the biggest splash',
        tags={"lemon", "spill"},
    ),
}

CLOTHS = {
    "cape_corner": Cloth(
        id="cape_corner",
        label="cape corner",
        phrase="the soft corner of a clean cape",
        gentle=True,
        tags={"cloth"},
    ),
    "microcloth": Cloth(
        id="microcloth",
        label="micro-cloth",
        phrase="a tiny hero polishing cloth",
        gentle=True,
        tags={"cloth"},
    ),
    "cotton_pad": Cloth(
        id="cotton_pad",
        label="cotton pad",
        phrase="a round cotton pad",
        gentle=True,
        tags={"cloth"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Maya", "Ava", "Zoe", "Ivy", "Ruby", "Nora"]
BOY_NAMES = ["Kai", "Leo", "Max", "Finn", "Eli", "Theo", "Noah", "Sam"]
TRAITS = ["careful", "bold", "eager", "patient", "showy", "thoughtful"]


def safe_for_lemon(target: Target) -> bool:
    return target.acid_safe and not target.absorbent


def sensible_amounts() -> list[Amount]:
    return [amount for amount in AMOUNTS.values() if amount.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for target_id, target in TARGETS.items():
            if not safe_for_lemon(target):
                continue
            for amount_id, amount in AMOUNTS.items():
                if amount.sense >= SENSE_MIN:
                    combos.append((mission_id, target_id, amount_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.amount == "smidge":
        return "smooth"
    if params.amount == "drip":
        return "smooth"
    if params.amount == "squeeze":
        return "spill"
    raise StoryError(f"Invalid amount '{params.amount}' for this world.")


def explain_rejection(target: Target) -> str:
    if target.absorbent:
        return (
            f"(No story: lemon would soak into {target.the} because it is {target.material}. "
            f"The hero needs a hard, wipeable gadget for this cleaning trick.)"
        )
    return (
        f"(No story: {target.the} is not a reasonable thing to clean with lemon here.)"
    )


def explain_amount(amount_id: str) -> str:
    amount = AMOUNTS[amount_id]
    better = ", ".join(sorted(a.id for a in sensible_amounts()))
    return (
        f"(Refusing amount '{amount_id}': it scores too low on common sense "
        f"(sense={amount.sense} < {SENSE_MIN}). Try a smaller amount such as {better}.)"
    )


@dataclass
class StoryParams:
    mission: str
    target: str
    amount: str
    cloth: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def apply_lemon(world: World, target_cfg: Target, amount: Amount, narrate: bool = True) -> None:
    target = world.get("target")
    bowl = world.get("bowl")
    target.meters["lemon"] += float(amount.drops)
    if amount.drops >= 5:
        bowl.meters["mess"] += 1
        target.meters["sticky"] += 1
        if narrate:
            world.say(
                f"But {world.get('hero').id} gave {target_cfg.the} {amount.label} of lemon, "
                f"and sour drops skittered over the rim of the tray."
            )
    else:
        target.meters["sticky"] = 0.0
        target.meters["ready_to_wipe"] += 1
        if narrate:
            world.say(
                f"{world.get('hero').id} touched {target_cfg.the} with {amount.label} of lemon. "
                f"The {target_cfg.mess} loosened at once."
            )
    propagate(world, narrate=narrate)


def wipe_target(world: World, cloth: Cloth, target_cfg: Target, narrate: bool = True) -> None:
    target = world.get("target")
    if target.meters["ready_to_wipe"] < THRESHOLD and target.meters["sticky"] >= THRESHOLD:
        return
    target.meters["clean"] += 1
    if narrate:
        world.say(
            f"Using {cloth.phrase}, the two heroes wiped {target_cfg.the} in small circles."
        )
    propagate(world, narrate=narrate)


def predict_cleanup(world: World, amount: Amount) -> dict:
    sim = world.copy()
    target_cfg = sim.facts["target_cfg"]
    cloth = sim.facts["cloth_cfg"]
    apply_lemon(sim, target_cfg, amount, narrate=False)
    if sim.get("bowl").meters["mess"] < THRESHOLD:
        wipe_target(sim, cloth, target_cfg, narrate=False)
    return {
        "spill": sim.get("bowl").meters["mess"] >= THRESHOLD,
        "revealed": sim.get("target").meters["revealed"] >= THRESHOLD,
    }


def setup_scene(world: World, mission: Mission, hero: Entity, sidekick: Entity, target_cfg: Target) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"{hero.id} tied on a towel cape and climbed onto {mission.base}. {mission.opening}"
    )
    world.say(
        f'"Sidekick {sidekick.id}," {hero.id} said, "we have to demonstrate how heroes solve little problems before bedtime."'
    )
    world.say(
        f"{mission.call} On the tray between them sat {target_cfg.phrase}, marked by {target_cfg.hidden}."
    )


def explain_problem(world: World, hero: Entity, sidekick: Entity, target_cfg: Target) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'"If we clean it, the whole team can use it tonight," {hero.id} said. '
        f'{sidekick.id} leaned close and saw how the sticky spot kept the tool from shining.'
    )


def tempt_big_move(world: World, hero: Entity, amount: Amount) -> None:
    hero.memes["showoff"] += 1
    world.say(
        f"{hero.id} held up the lemon half like a glowing moon. "
        f"{hero.pronoun().capitalize()} thought {amount.line}."
    )


def sidekick_warning(world: World, hero: Entity, sidekick: Entity, target_cfg: Target) -> None:
    pred_small = predict_cleanup(world, AMOUNTS["smidge"])
    pred_big = predict_cleanup(world, AMOUNTS["squeeze"])
    world.facts["pred_small"] = pred_small
    world.facts["pred_big"] = pred_big
    sidekick.memes["caution"] += 1
    if pred_small["revealed"] and pred_big["spill"]:
        world.say(
            f'"Careful," {sidekick.id} said. "For {target_cfg.the}, just a smidge of lemon will work. '
            f'Big hero moves are fun, but little hero moves can be smarter."'
        )
    else:
        world.say(
            f'"Let\'s be gentle," {sidekick.id} said. "Heroes do not have to be loud to help."'
        )


def smooth_branch(world: World, hero: Entity, sidekick: Entity, cloth: Cloth, target_cfg: Target) -> None:
    apply_lemon(world, target_cfg, AMOUNTS["smidge"], narrate=True)
    wipe_target(world, cloth, target_cfg, narrate=True)
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    world.say(
        f'The sticky patch disappeared so neatly that {hero.id} blinked. "{sidekick.id}, you were right," {hero.pronoun()} said.'
    )
    world.say(
        f"Being careful made the job faster, not slower."
    )


def spill_branch(world: World, hero: Entity, sidekick: Entity, parent: Entity, cloth: Cloth, target_cfg: Target) -> None:
    apply_lemon(world, target_cfg, AMOUNTS["squeeze"], narrate=True)
    if world.get("bowl").meters["mess"] >= THRESHOLD:
        world.say(
            f'"Oops," {hero.id} whispered as the lemon smell jumped into the air.'
        )
        world.say(
            f"{parent.label_word.capitalize()} stepped over, not angry, just calm. "
            f'"First we wipe the puddle," {parent.pronoun()} said. "Then you can try again the careful way."'
        )
        world.get("bowl").meters["mess"] = 0.0
        hero.memes["lesson"] += 1
        hero.memes["oops"] += 1
        sidekick.memes["trust"] += 1
        world.say(
            f"{hero.id} dabbed up the spill with {cloth.phrase} and took a slower breath."
        )
    apply_lemon(world, target_cfg, AMOUNTS["smidge"], narrate=True)
    wipe_target(world, cloth, target_cfg, narrate=True)
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    world.say(
        f'"A smidge really was enough," {hero.id} said. This time {hero.pronoun()} sounded more wise than flashy.'
    )


def surprise_reveal(world: World, hero: Entity, sidekick: Entity, target_cfg: Target, mission: Mission) -> None:
    if world.get("target").meters["revealed"] < THRESHOLD:
        return
    hero.memes["lesson"] += 1
    world.say(
        f"Then came the surprise: under the last bit of stickiness was {target_cfg.reveal}."
    )
    world.say(
        f'{sidekick.id} gasped. "{hero.id}, it was hiding there all along!"'
    )
    world.say(
        f"{hero.id} held the clean tool up high. Now it was ready for the show, and {mission.closing}."
    )


def tell(
    mission: Mission,
    target_cfg: Target,
    amount_cfg: Amount,
    cloth_cfg: Cloth,
    hero_name: str,
    hero_gender: str,
    sidekick_name: str,
    sidekick_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[trait, "imaginative"],
    ))
    sidekick = world.add(Entity(
        id=sidekick_name,
        kind="character",
        type=sidekick_gender,
        role="sidekick",
        traits=["helpful", "careful"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    target = world.add(Entity(
        id="target",
        kind="thing",
        type="gadget",
        label=target_cfg.label,
        phrase=target_cfg.phrase,
        acid_safe=target_cfg.acid_safe,
        absorbent=target_cfg.absorbent,
        tags=set(target_cfg.tags),
    ))
    bowl = world.add(Entity(
        id="bowl",
        kind="thing",
        type="tray",
        label="tray",
        phrase="the hero tray",
    ))
    cloth = world.add(Entity(
        id="cloth",
        kind="thing",
        type="cloth",
        label=cloth_cfg.label,
        phrase=cloth_cfg.phrase,
        tags=set(cloth_cfg.tags),
    ))
    target.meters["sticky"] = 1.0
    world.facts.update(
        mission=mission,
        target_cfg=target_cfg,
        amount_cfg=amount_cfg,
        cloth_cfg=cloth_cfg,
        hero=hero,
        sidekick=sidekick,
        parent=parent,
    )

    setup_scene(world, mission, hero, sidekick, target_cfg)
    explain_problem(world, hero, sidekick, target_cfg)

    world.para()
    tempt_big_move(world, hero, amount_cfg)
    sidekick_warning(world, hero, sidekick, target_cfg)

    world.para()
    if amount_cfg.id in {"smidge", "drip"}:
        smooth_branch(world, hero, sidekick, cloth_cfg, target_cfg)
        outcome = "smooth"
    else:
        spill_branch(world, hero, sidekick, parent, cloth_cfg, target_cfg)
        outcome = "spill"

    world.para()
    surprise_reveal(world, hero, sidekick, target_cfg, mission)
    world.facts.update(
        outcome=outcome,
        surprise=world.get("target").meters["revealed"] >= THRESHOLD,
        spilled=outcome == "spill",
        learned=hero.memes["lesson"] >= THRESHOLD,
        target=target,
        bowl=bowl,
        cloth=cloth,
    )
    return world


KNOWLEDGE = {
    "lemon": [
        (
            "What is a lemon?",
            "A lemon is a yellow fruit with sour juice inside. People use its juice in food and sometimes for gentle cleaning."
        )
    ],
    "sticky": [
        (
            "Why is sticky stuff hard to clean?",
            "Sticky messes cling to a surface and grab dust and crumbs. That is why they often need a careful wipe instead of a wild scrub."
        )
    ],
    "metal": [
        (
            "Why can some hard tools be wiped clean?",
            "Hard surfaces like metal or plastic do not soak liquids up the way paper or cloth can. That makes them better for gentle wiping."
        )
    ],
    "paper": [
        (
            "Why should you be careful with paper and liquid?",
            "Paper drinks liquid in quickly and can wrinkle or tear. That is why a wet cleaning trick is not a good choice for it."
        )
    ],
    "cloth": [
        (
            "What does a soft cloth do when you clean something?",
            "A soft cloth lifts dirt and sticky spots without scratching. Small circles and gentle hands often work best."
        )
    ],
    "lesson": [
        (
            "What is a lesson learned?",
            "A lesson learned is something you understand better after trying, noticing, or fixing a mistake. It helps you make a wiser choice next time."
        )
    ],
    "surprise": [
        (
            "What is a surprise in a story?",
            "A surprise is something unexpected that happens and changes how the moment feels. It often makes the ending feel bright, funny, or exciting."
        )
    ],
}

KNOWLEDGE_ORDER = ["lemon", "sticky", "metal", "paper", "cloth", "lesson", "surprise"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    mission = world.facts["mission"]
    target_cfg = world.facts["target_cfg"]
    if world.facts["outcome"] == "spill":
        return [
            'Write a short superhero story for a 3-to-5-year-old that includes the words "demonstrate", "lemon", and "smidge".',
            f"Tell a gentle superhero story where {hero.id} wants to demonstrate a cleaning trick in {mission.base}, uses too much lemon at first, and learns that a smidge works better.",
            f"Write a child-facing story with a lesson learned and a surprise ending, where {sidekick.id} gives good advice and a sticky {target_cfg.label} hides something wonderful underneath.",
        ]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the words "demonstrate", "lemon", and "smidge".',
        f"Tell a superhero story where {hero.id} listens when {sidekick.id} says that a smidge of lemon is enough to clean a sticky {target_cfg.label}.",
        "Write a story with a lesson learned and a surprise reveal, where careful hands solve the problem better than a flashy move.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    parent = world.facts["parent"]
    mission = world.facts["mission"]
    target_cfg = world.facts["target_cfg"]
    cloth_cfg = world.facts["cloth_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a pretend superhero, and {sidekick.id}, the helpful sidekick. They were getting ready in {mission.base} for a little hero show."
        ),
        (
            "What did they want to do?",
            f"They wanted to demonstrate how heroes solve a small problem by cleaning {target_cfg.the}. The sticky spot was stopping the tool from shining the way it should."
        ),
        (
            f"Why did {sidekick.id} say to use only a smidge of lemon?",
            f"{sidekick.id} knew {target_cfg.the} only needed a tiny bit to loosen the sticky {target_cfg.mess}. A bigger squeeze would make extra mess instead of helping."
        ),
    ]
    if outcome == "spill":
        qa.append(
            (
                f"What happened when {hero.id} used too much lemon?",
                f"The lemon spilled onto the tray before the cleaning was finished. {parent.label_word.capitalize()} stayed calm, and that helped {hero.id} slow down and try again the careful way."
            )
        )
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero.id} learned that big actions are not always the best actions. A smidge of lemon and a gentle wipe with {cloth_cfg.phrase} worked better than showing off."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.pronoun().capitalize()} used a smidge of lemon and then wiped {target_cfg.the} with {cloth_cfg.phrase}. Because the move was small and careful, the sticky patch came off right away."
            )
        )
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero.id} learned that careful hero work can be stronger than flashy hero work. Listening to good advice made the job quick and neat."
            )
        )
    if world.facts["surprise"]:
        qa.append(
            (
                "What was the surprise at the end?",
                f"When the sticky mess was gone, they found {target_cfg.reveal}. The surprise proved that something wonderful had been hidden under the mess all along."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"lemon", "sticky", "cloth", "lesson", "surprise"}
    target_cfg = world.facts["target_cfg"]
    if target_cfg.material in {"metal", "plastic"}:
        tags.add("metal")
    if target_cfg.material == "paper":
        tags.add("paper")
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.acid_safe:
            flags.append("acid_safe")
        if ent.absorbent:
            flags.append("absorbent")
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="roof_watch",
        target="signal_button",
        amount="smidge",
        cloth="microcloth",
        hero="Nova",
        hero_gender="girl",
        sidekick="Kai",
        sidekick_gender="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        mission="kitchen_lab",
        target="visor",
        amount="squeeze",
        cloth="cotton_pad",
        hero="Leo",
        hero_gender="boy",
        sidekick="Ruby",
        sidekick_gender="girl",
        parent="father",
        trait="showy",
    ),
    StoryParams(
        mission="hallway_hq",
        target="badge",
        amount="drip",
        cloth="cape_corner",
        hero="Maya",
        hero_gender="girl",
        sidekick="Finn",
        sidekick_gender="boy",
        parent="mother",
        trait="thoughtful",
    ),
]


ASP_RULES = r"""
safe_target(Tg) :- target(Tg), acid_safe(Tg), not absorbent(Tg).
sensible_amount(A) :- amount(A), sense(A, S), sense_min(M), S >= M.
valid(M, Tg, A) :- mission(M), safe_target(Tg), sensible_amount(A).

smooth :- chosen_amount(A), drops(A, D), D <= 2.
spill  :- chosen_amount(A), drops(A, D), D >= 5.

outcome(smooth) :- smooth.
outcome(spill)  :- spill.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.acid_safe:
            lines.append(asp.fact("acid_safe", target_id))
        if target.absorbent:
            lines.append(asp.fact("absorbent", target_id))
    for amount_id, amount in AMOUNTS.items():
        lines.append(asp.fact("amount", amount_id))
        lines.append(asp.fact("sense", amount_id, amount.sense))
        lines.append(asp.fact("drops", amount_id, amount.drops))
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

    extra = asp.fact("chosen_amount", params.amount)
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

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve at seed {seed}.")
            break

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
            asp_out = asp_outcome(params)
            if py != asp_out:
                bad += 1
        except Exception as err:
            rc = 1
            print(f"Outcome check crashed for {params}: {err}")
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"Smoke generation failed: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child superhero learns that a smidge of lemon can do a careful job."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--amount", choices=AMOUNTS)
    ap.add_argument("--cloth", choices=CLOTHS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke generation test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target:
        target = TARGETS.get(args.target)
        if target is None:
            raise StoryError(f"Unknown target '{args.target}'.")
        if not safe_for_lemon(target):
            raise StoryError(explain_rejection(target))
    if args.amount:
        amount = AMOUNTS.get(args.amount)
        if amount is None:
            raise StoryError(f"Unknown amount '{args.amount}'.")
        if amount.sense < SENSE_MIN:
            raise StoryError(explain_amount(args.amount))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.target is None or combo[1] == args.target)
        and (args.amount is None or combo[2] == args.amount)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, target_id, amount_id = rng.choice(sorted(combos))
    cloth_id = args.cloth or rng.choice(sorted(CLOTHS))
    hero_name, hero_gender = pick_kid(rng)
    sidekick_name, sidekick_gender = pick_kid(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        mission=mission_id,
        target=target_id,
        amount=amount_id,
        cloth=cloth_id,
        hero=hero_name,
        hero_gender=hero_gender,
        sidekick=sidekick_name,
        sidekick_gender=sidekick_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission '{params.mission}'.")
    if params.target not in TARGETS:
        raise StoryError(f"Unknown target '{params.target}'.")
    if params.amount not in AMOUNTS:
        raise StoryError(f"Unknown amount '{params.amount}'.")
    if params.cloth not in CLOTHS:
        raise StoryError(f"Unknown cloth '{params.cloth}'.")
    target_cfg = TARGETS[params.target]
    amount_cfg = AMOUNTS[params.amount]
    if not safe_for_lemon(target_cfg):
        raise StoryError(explain_rejection(target_cfg))
    if amount_cfg.sense < SENSE_MIN:
        raise StoryError(explain_amount(params.amount))

    world = tell(
        mission=MISSIONS[params.mission],
        target_cfg=target_cfg,
        amount_cfg=amount_cfg,
        cloth_cfg=CLOTHS[params.cloth],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick,
        sidekick_gender=params.sidekick_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (mission, target, amount) combos:\n")
        for mission_id, target_id, amount_id in combos:
            print(f"  {mission_id:12} {target_id:14} {amount_id}")
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
            header = f"### {p.hero} & {p.sidekick}: {p.mission}, {p.target}, {p.amount} ({outcome_of(p)})"
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
