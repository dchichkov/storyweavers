#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jackeroo_tennis_fortunate_dialogue_animal_story.py
==============================================================================

A standalone storyworld for a tiny animal-story domain: two young animals hurry
off to play tennis, the ball gets trapped in a tricky place, and a sensible
animal-friendly solution turns the mishap into a fortunate ending.

The seed asked for the words "jackeroo", "tennis", and "fortunate", and for
dialogue in an animal-story style. This script models a few close variations of
that domain with a small, typed world model, a reasonableness gate, and an ASP
twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/jackeroo_tennis_fortunate_dialogue_animal_story.py
    python storyworlds/worlds/gpt-5.4/jackeroo_tennis_fortunate_dialogue_animal_story.py --animal kangaroo --trap thorn_bush
    python storyworlds/worlds/gpt-5.4/jackeroo_tennis_fortunate_dialogue_animal_story.py --trap sky
    python storyworlds/worlds/gpt-5.4/jackeroo_tennis_fortunate_dialogue_animal_story.py --method poke_stick
    python storyworlds/worlds/gpt-5.4/jackeroo_tennis_fortunate_dialogue_animal_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/jackeroo_tennis_fortunate_dialogue_animal_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    can_climb: bool = False
    can_reach_high: bool = False
    can_grab_delicate: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "sheep", "kangaroo_f", "koala_f", "possum_f"}
        male = {"boy", "father", "roo", "kangaroo", "wombat", "koala", "possum", "platypus", "emu"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class AnimalChoice:
    id: str
    species: str
    type: str
    starter: str
    motion: str
    court_line: str
    skill: str
    title_word: str = "jackeroo"
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendChoice:
    id: str
    species: str
    type: str
    caution_style: str
    helper_style: str
    can_climb: bool = False
    can_reach_high: bool = False
    can_grab_delicate: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class TrapChoice:
    id: str
    label: str
    place_phrase: str
    danger_line: str
    recover_line: str
    requires: str
    valid: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MethodChoice:
    id: str
    label: str
    action_text: str
    success_qa: str
    supports: set[str] = field(default_factory=set)
    sense: int = 2
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


def _r_ball_trouble(world: World) -> list[str]:
    ball = world.get("ball")
    if ball.meters["stuck"] < THRESHOLD:
        return []
    sig = ("ball_trouble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        world.get(eid).memes["worry"] += 1
    return ["__ball_trouble__"]


def _r_help_bring_relief(world: World) -> list[str]:
    helper = world.get("friend")
    ball = world.get("ball")
    if helper.meters["helped"] < THRESHOLD or ball.meters["free"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="ball_trouble", tag="social", apply=_r_ball_trouble),
    Rule(name="help_bring_relief", tag="social", apply=_r_help_bring_relief),
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


ANIMALS = {
    "kangaroo": AnimalChoice(
        id="kangaroo",
        species="young kangaroo",
        type="kangaroo",
        starter="a springy young kangaroo",
        motion="bounced",
        court_line="The flat clay court behind the gum trees looked just right for tennis.",
        skill="quick feet",
        title_word="jackeroo",
        tags={"kangaroo", "tennis"},
    ),
    "koala": AnimalChoice(
        id="koala",
        species="little koala",
        type="koala",
        starter="a little koala with bright eyes",
        motion="padded",
        court_line="The little practice court beside the gum trees looked quiet and sunny.",
        skill="careful paws",
        title_word="jackeroo",
        tags={"koala", "tennis"},
    ),
    "wombat": AnimalChoice(
        id="wombat",
        species="round little wombat",
        type="wombat",
        starter="a round little wombat with a determined face",
        motion="trotted",
        court_line="A smooth patch by the fence had been brushed into a tiny tennis court.",
        skill="steady steps",
        title_word="jackeroo",
        tags={"wombat", "tennis"},
    ),
}

FRIENDS = {
    "possum": FriendChoice(
        id="possum",
        species="possum",
        type="possum",
        caution_style="soft but quick",
        helper_style="nimble little paws",
        can_climb=True,
        can_reach_high=True,
        can_grab_delicate=True,
        tags={"possum", "friend"},
    ),
    "emu": FriendChoice(
        id="emu",
        species="emu chick",
        type="emu",
        caution_style="tall and sensible",
        helper_style="long neck and careful peck",
        can_reach_high=True,
        can_grab_delicate=False,
        tags={"emu", "friend"},
    ),
    "platypus": FriendChoice(
        id="platypus",
        species="platypus",
        type="platypus",
        caution_style="quiet and thoughtful",
        helper_style="patient little bill and paws",
        can_climb=False,
        can_reach_high=False,
        can_grab_delicate=True,
        tags={"platypus", "friend"},
    ),
}

TRAPS = {
    "thorn_bush": TrapChoice(
        id="thorn_bush",
        label="thorn bush",
        place_phrase="into a thorn bush by the fence",
        danger_line="The thorns were sharp enough to scratch a nose or a paw.",
        recover_line="A gentle pull could free the ball if someone reached carefully.",
        requires="delicate",
        valid=True,
        tags={"thorn", "careful_help"},
    ),
    "gum_branch": TrapChoice(
        id="gum_branch",
        label="gum-tree branch",
        place_phrase="up onto a low gum-tree branch",
        danger_line="It was too high for a wild jump from the ground.",
        recover_line="Someone who could reach high could tap it loose.",
        requires="high",
        valid=True,
        tags={"tree", "reach"},
    ),
    "reed_patch": TrapChoice(
        id="reed_patch",
        label="reed patch",
        place_phrase="into a patch of reeds beside the pond",
        danger_line="The mud at the edge was slippery and deep enough to soak little feet.",
        recover_line="A careful fetch from the bank would keep everyone dry.",
        requires="careful_bank",
        valid=True,
        tags={"pond", "mud", "careful_help"},
    ),
    "sky": TrapChoice(
        id="sky",
        label="sky",
        place_phrase="into the sky",
        danger_line="A ball cannot stay trapped in the sky.",
        recover_line="There is nothing there to recover it from.",
        requires="none",
        valid=False,
        tags={"invalid"},
    ),
}


METHODS = {
    "gentle_paw": MethodChoice(
        id="gentle_paw",
        label="gentle paw",
        action_text="used a gentle paw to work the ball free",
        success_qa="used a gentle paw to work the ball free",
        supports={"delicate", "careful_bank"},
        sense=3,
        tags={"help", "careful"},
    ),
    "climb_and_tap": MethodChoice(
        id="climb_and_tap",
        label="climb and tap",
        action_text="climbed up and tapped the ball down",
        success_qa="climbed up and tapped the ball down",
        supports={"high"},
        sense=3,
        tags={"tree", "help"},
    ),
    "racket_scoop": MethodChoice(
        id="racket_scoop",
        label="racket scoop",
        action_text="slid the tennis racket under the ball and scooped it back",
        success_qa="slid the tennis racket under the ball and scooped it back",
        supports={"thorn_bush", "careful_bank"},
        sense=3,
        tags={"tennis", "tool"},
    ),
    "poke_stick": MethodChoice(
        id="poke_stick",
        label="poking stick",
        action_text="jabbed at the ball with a stick",
        success_qa="jabbed at the ball with a stick",
        supports={"high"},
        sense=1,
        tags={"rough"},
    ),
}


def trap_needs(trap: TrapChoice) -> str:
    if trap.id == "thorn_bush":
        return "delicate"
    if trap.id == "gum_branch":
        return "high"
    if trap.id == "reed_patch":
        return "careful_bank"
    return trap.requires


def friend_can_help(friend: FriendChoice, trap: TrapChoice) -> bool:
    need = trap_needs(trap)
    if need == "delicate":
        return friend.can_grab_delicate
    if need == "high":
        return friend.can_reach_high or friend.can_climb
    if need == "careful_bank":
        return friend.can_grab_delicate
    return False


def method_works(method: MethodChoice, trap: TrapChoice) -> bool:
    need = trap_needs(trap)
    return need in method.supports or trap.id in method.supports


def valid_story(animal_id: str, friend_id: str, trap_id: str, method_id: str) -> bool:
    animal = ANIMALS[animal_id]
    friend = FRIENDS[friend_id]
    trap = TRAPS[trap_id]
    method = METHODS[method_id]
    _ = animal
    return trap.valid and friend_can_help(friend, trap) and method.sense >= SENSE_MIN and method_works(method, trap)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for animal_id in sorted(ANIMALS):
        for friend_id in sorted(FRIENDS):
            for trap_id in sorted(TRAPS):
                for method_id in sorted(METHODS):
                    if valid_story(animal_id, friend_id, trap_id, method_id):
                        combos.append((animal_id, friend_id, trap_id, method_id))
    return combos


@dataclass
class StoryParams:
    animal: str
    friend: str
    trap: str
    method: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        animal="kangaroo",
        friend="possum",
        trap="thorn_bush",
        method="gentle_paw",
        hero_name="Joey Jackeroo",
        friend_name="Pip",
    ),
    StoryParams(
        animal="koala",
        friend="emu",
        trap="gum_branch",
        method="climb_and_tap",
        hero_name="Moss Jackeroo",
        friend_name="Tallie",
    ),
    StoryParams(
        animal="wombat",
        friend="platypus",
        trap="reed_patch",
        method="gentle_paw",
        hero_name="Wally Jackeroo",
        friend_name="Bramble",
    ),
    StoryParams(
        animal="kangaroo",
        friend="possum",
        trap="reed_patch",
        method="racket_scoop",
        hero_name="Nip Jackeroo",
        friend_name="Pip",
    ),
]


def explain_rejection(friend: FriendChoice, trap: TrapChoice) -> str:
    if not trap.valid:
        return (
            f"(No story: {trap.label} is not a real place for a lost tennis ball to stay. "
            f"Pick a trap like thorn_bush, gum_branch, or reed_patch.)"
        )
    if not friend_can_help(friend, trap):
        return (
            f"(No story: a {friend.species} is not a plausible helper for a ball stuck in "
            f"{trap.label}. Pick a helper whose body and skills fit the problem.)"
        )
    return "(No story: this helper cannot solve that trap.)"


def explain_method(method: MethodChoice, trap: TrapChoice) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it is too rough for this storyworld "
            f"(sense={method.sense} < {SENSE_MIN}). Try a gentler, more sensible rescue.)"
        )
    return (
        f"(No story: the method '{method.id}' does not really fit a ball stuck in "
        f"{trap.label}. Choose a method that matches the problem.)"
    )


def predict_trouble(world: World, trap_id: str, method_id: str) -> dict:
    sim = world.copy()
    trap = TRAPS[trap_id]
    method = METHODS[method_id]
    sim.get("ball").meters["stuck"] += 1
    sim.facts["trap"] = trap
    propagate(sim, narrate=False)
    freed = method_works(method, trap)
    if freed:
        sim.get("ball").meters["free"] += 1
        sim.get("friend").meters["helped"] += 1
        propagate(sim, narrate=False)
    return {
        "worry": sim.get("hero").memes["worry"],
        "freed": sim.get("ball").meters["free"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, animal: AnimalChoice) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the sunny bush beyond the gum trees lived {hero.id}, {animal.starter}."
    )
    world.say(
        f"His best friend was {friend.id} the {friend.attrs['species']}, and the two of them "
        f"loved tennis."
    )
    world.say(
        f'One morning {hero.id} tied on a tiny scarf and said, "Today I feel like a real '
        f'{animal.title_word} of the court."'
    )
    world.say(
        f'{friend.id} laughed. "{animal.title_word.capitalize()} or not, let us see your '
        f'{animal.skill}," {friend.pronoun()} said.'
    )
    world.say(animal.court_line)


def start_play(world: World, hero: Entity, friend: Entity, animal: AnimalChoice) -> None:
    ball = world.get("ball")
    racket = world.get("racket")
    hero.memes["pride"] += 1
    ball.meters["ready"] += 1
    racket.meters["held"] += 1
    world.say(
        f"{hero.id} {animal.motion} to the line with the little racket tucked under his arm."
    )
    world.say(
        f'"Watch this serve," {hero.id} said. "{friend.id}, if it lands by the chalk, '
        f'you must call it fair."'
    )
    world.say(
        f'"Fair is fair," {friend.id} replied. "{animal.title_word.capitalize()}, send the ball over."'
    )


def mishap(world: World, hero: Entity, friend: Entity, trap: TrapChoice) -> None:
    ball = world.get("ball")
    ball.meters["stuck"] += 1
    ball.meters["lost"] += 1
    world.facts["mishap"] = trap.place_phrase
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} swung, the ball flew in a bright yellow blur, and instead of landing on the court "
        f"it bounced {trap.place_phrase}."
    )
    world.say(trap.danger_line)
    world.say(
        f'"Oh dear," {hero.id} whispered. "Our tennis ball is gone."'
    )
    world.say(
        f'"Do not rush," {friend.id} said in a voice that was {friend.attrs["caution_style"]}. '
        f'"A hurried paw can make a small problem bigger."'
    )


def worry_and_plan(world: World, hero: Entity, friend: Entity, trap: TrapChoice, method: MethodChoice) -> None:
    pred = predict_trouble(world, trap.id, method.id)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{hero.id} peered at the trap and said, "I only wanted a game of tennis. This does not feel '
        f'very fortunate."'
    )
    world.say(
        f'{friend.id} tilted {friend.pronoun("possessive")} head. "{trap.recover_line} Let me think."'
    )


def rescue(world: World, hero: Entity, friend: Entity, trap: TrapChoice, method: MethodChoice) -> None:
    ball = world.get("ball")
    friend.meters["helped"] += 1
    ball.meters["free"] += 1
    ball.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Then {friend.id}, with {friend.attrs['helper_style']}, {method.action_text}."
    )
    world.say(
        f'The ball popped free and rolled back across the clay. "{friend.id}!" cried {hero.id}. '
        f'"You saved our game."'
    )
    world.say(
        f'"And you learned not to leap first," {friend.id} said, smiling.'
    )


def resolution(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f'{hero.id} hugged the ball to his chest. "How fortunate that I have a friend who thinks before '
        f'jumping," he said.'
    )
    world.say(
        f'"How fortunate that you know how to say thank you," {friend.id} answered.'
    )
    world.say(
        "They moved a little farther from the fence, tapped the ball gently back and forth, and the game "
        "went on under the warm trees until even the birds seemed to cheer."
    )


def tell(params: StoryParams) -> World:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.friend not in FRIENDS:
        raise StoryError(f"(Unknown friend: {params.friend})")
    if params.trap not in TRAPS:
        raise StoryError(f"(Unknown trap: {params.trap})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    animal = ANIMALS[params.animal]
    friend_cfg = FRIENDS[params.friend]
    trap = TRAPS[params.trap]
    method = METHODS[params.method]

    if not trap.valid:
        raise StoryError(explain_rejection(friend_cfg, trap))
    if not friend_can_help(friend_cfg, trap):
        raise StoryError(explain_rejection(friend_cfg, trap))
    if method.sense < SENSE_MIN or not method_works(method, trap):
        raise StoryError(explain_method(method, trap))

    world = World()
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=animal.type,
            label=params.hero_name,
            phrase=params.hero_name,
            role="hero",
            traits=[animal.skill],
            attrs={"species": animal.species},
            tags=set(animal.tags),
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type=friend_cfg.type,
            label=params.friend_name,
            phrase=params.friend_name,
            role="friend",
            attrs={
                "species": friend_cfg.species,
                "caution_style": friend_cfg.caution_style,
                "helper_style": friend_cfg.helper_style,
            },
            can_climb=friend_cfg.can_climb,
            can_reach_high=friend_cfg.can_reach_high,
            can_grab_delicate=friend_cfg.can_grab_delicate,
            tags=set(friend_cfg.tags),
        )
    )
    ball = world.add(
        Entity(
            id="ball",
            type="thing",
            label="tennis ball",
            phrase="a bright yellow tennis ball",
            tags={"tennis"},
        )
    )
    racket = world.add(
        Entity(
            id="racket",
            type="thing",
            label="racket",
            phrase="a little tennis racket",
            tags={"tennis"},
        )
    )

    introduce(world, hero, friend, animal)
    world.para()
    start_play(world, hero, friend, animal)
    world.para()
    mishap(world, hero, friend, trap)
    worry_and_plan(world, hero, friend, trap, method)
    world.para()
    rescue(world, hero, friend, trap, method)
    resolution(world, hero, friend)

    world.facts.update(
        animal=animal,
        friend_cfg=friend_cfg,
        trap=trap,
        method=method,
        hero=hero,
        friend=friend,
        ball=ball,
        racket=racket,
        fortunate=hero.memes["gratitude"] >= THRESHOLD,
        safe_end=ball.meters["free"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "tennis": [
        (
            "What is tennis?",
            "Tennis is a game where players hit a ball back and forth with rackets. The ball should stay in the playing area so everyone can keep the game going."
        )
    ],
    "kangaroo": [
        (
            "How does a kangaroo move?",
            "A kangaroo usually moves by hopping on strong back legs. Its tail helps it balance."
        )
    ],
    "koala": [
        (
            "Why are koalas good around trees?",
            "Koalas are good around trees because they have strong limbs and gripping paws. They spend much of their time climbing and resting in branches."
        )
    ],
    "wombat": [
        (
            "What is a wombat like?",
            "A wombat is a sturdy animal with a low, strong body. It is better at steady walking and digging than at climbing trees."
        )
    ],
    "possum": [
        (
            "Why can a possum be a careful climber?",
            "A possum can grip branches and move lightly. That helps it reach tricky places without crashing through them."
        )
    ],
    "emu": [
        (
            "Why can an emu reach high places better than a small animal on the ground?",
            "An emu is tall, so it can often reach things that are higher up. Height can help when a problem is above eye level."
        )
    ],
    "platypus": [
        (
            "What is special about a platypus?",
            "A platypus is an animal with a bill and webbed feet. It is good near water and can work carefully at the edge of a pond."
        )
    ],
    "thorn": [
        (
            "Why should animals be careful near thorns?",
            "Thorns are sharp, so they can scratch paws, noses, or fur. It is better to move slowly and use a careful touch."
        )
    ],
    "tree": [
        (
            "Why is climbing better than wild jumping when something is stuck in a branch?",
            "Climbing lets you get close in a steady way. Wild jumping can miss the branch and make the problem worse."
        )
    ],
    "pond": [
        (
            "Why can the edge of a pond be slippery?",
            "Mud and wet reeds near a pond can slide under little feet. That is why careful animals stay balanced and do not rush."
        )
    ],
    "help": [
        (
            "Why is asking a friend for help a smart idea?",
            "A friend may notice a safer way to solve the problem. Working together can stop a small trouble from becoming a bigger one."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "tennis",
    "kangaroo",
    "koala",
    "wombat",
    "possum",
    "emu",
    "platypus",
    "thorn",
    "tree",
    "pond",
    "help",
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    trap = world.facts["trap"]
    return [
        'Write a short animal story for a 3-to-5-year-old that includes the words "jackeroo", "tennis", and "fortunate".',
        f"Tell a gentle story with dialogue where {hero.id} and {friend.id} are animal friends playing tennis, the ball gets stuck in {trap.label}, and teamwork saves the game.",
        "Write a bush animal story where a playful mistake leads to worry, a calm friend helps, and the ending shows why the characters feel fortunate.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    trap = world.facts["trap"]
    method = world.facts["method"]
    animal = world.facts["animal"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {animal.species}, and {friend.id}, {friend.attrs['species']}. They are friends who love playing tennis together."
        ),
        (
            "What game did they want to play?",
            "They wanted to play tennis on their little bush court. The game is what brought out the ball, racket, and excited talk."
        ),
        (
            f"Why did the ball become a problem?",
            f"The ball bounced {trap.place_phrase} instead of landing on the court. That turned a happy serve into a small worry because the place was not easy or safe to reach."
        ),
        (
            f"How did {friend.id} help?",
            f"{friend.id} {method.success_qa}. That worked because {friend.pronoun('subject')} used a method that fit the place where the ball was stuck."
        ),
        (
            "Why did the hero say they were fortunate at the end?",
            f"{hero.id} felt fortunate because the game was saved and nobody got hurt. {friend.id}'s calm help changed the trouble into a happy ending."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["animal"].tags) | set(world.facts["friend_cfg"].tags) | set(world.facts["trap"].tags) | set(world.facts["method"].tags)
    tags.add("help")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        ability_bits = []
        if ent.can_climb:
            ability_bits.append("can_climb")
        if ent.can_reach_high:
            ability_bits.append("can_reach_high")
        if ent.can_grab_delicate:
            ability_bits.append("can_grab_delicate")
        if ability_bits:
            bits.append(f"abilities={ability_bits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_trap(T) :- trap(T), trap_ok(T).
friend_fits(F, T) :- friend(F), needs(T, delicate), friend_delicate(F).
friend_fits(F, T) :- friend(F), needs(T, high), friend_high(F).
friend_fits(F, T) :- friend(F), needs(T, careful_bank), friend_delicate(F).

method_fits(M, T) :- method(M), needs(T, Need), supports(M, Need).
method_fits(M, T) :- method(M), supports(M, T).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

valid(A, F, T, M) :- animal(A), friend(F), trap(T), method(M),
                     valid_trap(T), friend_fits(F, T), sensible(M), method_fits(M, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id in sorted(ANIMALS):
        lines.append(asp.fact("animal", animal_id))
    for friend_id, friend in sorted(FRIENDS.items()):
        lines.append(asp.fact("friend", friend_id))
        if friend.can_grab_delicate:
            lines.append(asp.fact("friend_delicate", friend_id))
        if friend.can_reach_high or friend.can_climb:
            lines.append(asp.fact("friend_high", friend_id))
    for trap_id, trap in sorted(TRAPS.items()):
        lines.append(asp.fact("trap", trap_id))
        if trap.valid:
            lines.append(asp.fact("trap_ok", trap_id))
        lines.append(asp.fact("needs", trap_id, trap_needs(trap)))
    for method_id, method in sorted(METHODS.items()):
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for support in sorted(method.supports):
            lines.append(asp.fact("supports", method_id, support))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(item[0] for item in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    asp_good = set(asp_sensible())
    py_good = {mid for mid, method in METHODS.items() if method.sense >= SENSE_MIN}
    if asp_good == py_good:
        print(f"OK: sensible methods match ({sorted(asp_good)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: asp={sorted(asp_good)} python={sorted(py_good)}")

    smoke_cases = list(CURATED)
    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a jackeroo of the tennis court, a lost ball, and a fortunate rescue."
    )
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--trap", choices=sorted(TRAPS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


HERO_NAMES = ["Joey Jackeroo", "Nip Jackeroo", "Moss Jackeroo", "Wally Jackeroo"]
FRIEND_NAMES = ["Pip", "Tallie", "Bramble", "Dot"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trap is not None and not TRAPS[args.trap].valid:
        friend = FRIENDS[args.friend] if args.friend else next(iter(FRIENDS.values()))
        raise StoryError(explain_rejection(friend, TRAPS[args.trap]))
    if args.friend is not None and args.trap is not None:
        if not friend_can_help(FRIENDS[args.friend], TRAPS[args.trap]):
            raise StoryError(explain_rejection(FRIENDS[args.friend], TRAPS[args.trap]))
    if args.method is not None:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            trap = TRAPS[args.trap] if args.trap else TRAPS["thorn_bush"]
            raise StoryError(explain_method(method, trap))
        if args.trap is not None and not method_works(method, TRAPS[args.trap]):
            raise StoryError(explain_method(method, TRAPS[args.trap]))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.friend is None or combo[1] == args.friend)
        and (args.trap is None or combo[2] == args.trap)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, friend_id, trap_id, method_id = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])

    return StoryParams(
        animal=animal_id,
        friend=friend_id,
        trap=trap_id,
        method=method_id,
        hero_name=hero_name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (animal, friend, trap, method) combos:\n")
        for animal_id, friend_id, trap_id, method_id in combos:
            print(f"  {animal_id:9} {friend_id:9} {trap_id:11} {method_id}")
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
            header = f"### {p.hero_name}: {p.animal}, {p.friend}, {p.trap}, {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
