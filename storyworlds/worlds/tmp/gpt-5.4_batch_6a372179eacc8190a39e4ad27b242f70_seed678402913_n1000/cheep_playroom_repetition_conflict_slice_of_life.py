#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cheep_playroom_repetition_conflict_slice_of_life.py
==============================================================================

A standalone story world for a small slice-of-life playroom tale built around a
little toy that goes "cheep, cheep." Two children both want the same toy, the
wish repeats, the conflict repeats, and the world model decides whether they
work it out themselves or need a grown-up to help them take turns.

Run it
------
    python storyworlds/worlds/gpt-5.4/cheep_playroom_repetition_conflict_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/cheep_playroom_repetition_conflict_slice_of_life.py --scene nest
    python storyworlds/worlds/gpt-5.4/cheep_playroom_repetition_conflict_slice_of_life.py --toy bell_bird
    python storyworlds/worlds/gpt-5.4/cheep_playroom_repetition_conflict_slice_of_life.py --plan grab_back
    python storyworlds/worlds/gpt-5.4/cheep_playroom_repetition_conflict_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/cheep_playroom_repetition_conflict_slice_of_life.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/cheep_playroom_repetition_conflict_slice_of_life.py --qa --json
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
EAGERNESS_INIT = 5.0
PEACEMAKER_TRAITS = {"patient", "gentle", "kind", "careful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    opening: str
    game_line: str
    goal: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    sound: str
    appeal: int
    cheeps: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    sense: int
    power: int
    offer: str
    success: str
    reset: str
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"first", "second"}]

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


def _r_tug_fuss(world: World) -> list[str]:
    toy = world.get("toy")
    kids = world.kids()
    if toy.meters["tugged"] < THRESHOLD:
        return []
    sig = ("tug_fuss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in kids:
        kid.memes["frustration"] += 1
    world.get("room").meters["noise"] += 1
    return ["__fuss__"]


def _r_drop_quiet(world: World) -> list[str]:
    toy = world.get("toy")
    if toy.meters["dropped"] < THRESHOLD:
        return []
    sig = ("drop_quiet",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toy.meters["cheeping"] = 0.0
    toy.memes["resting"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__drop__"]


CAUSAL_RULES = [
    Rule(name="tug_fuss", tag="social", apply=_r_tug_fuss),
    Rule(name="drop_quiet", tag="physical", apply=_r_drop_quiet),
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


def toy_fits_story(toy: Toy) -> bool:
    return toy.cheeps


def sensible_plans() -> list[Plan]:
    return [plan for plan in PLANS.values() if plan.sense >= SENSE_MIN]


def conflict_severity(toy: Toy, delay: int) -> int:
    return toy.appeal + delay


def initial_peacemaking(trait: str) -> float:
    return 5.0 if trait in PEACEMAKER_TRAITS else 3.0


def would_self_solve(relation: str, first_age: int, second_age: int, trait: str) -> bool:
    older_second = relation == "siblings" and second_age > first_age
    authority = initial_peacemaking(trait) + 1.0 + (3.0 if older_second else 0.0)
    return older_second and authority > EAGERNESS_INIT


def plan_succeeds(plan: Plan, toy: Toy, delay: int) -> bool:
    return plan.power >= conflict_severity(toy, delay)


def predict_tug(world: World) -> dict:
    sim = world.copy()
    toy = sim.get("toy")
    toy.meters["held_by_first"] += 1
    toy.meters["held_by_second"] += 1
    toy.meters["tugged"] += 1
    if sim.facts.get("delay", 0) >= 2:
        toy.meters["dropped"] += 1
    propagate(sim, narrate=False)
    return {
        "fuss": sim.get("room").meters["noise"],
        "drop": sim.get("toy").meters["dropped"] >= THRESHOLD,
    }


def play_setup(world: World, first: Entity, second: Entity, scene: Scene, toy: Toy) -> None:
    for kid in (first, second):
        kid.memes["joy"] += 1
    world.say(
        f"In the playroom, {scene.opening} {first.id} and {second.id} sat close enough to bump knees."
    )
    world.say(scene.game_line)
    world.say(
        f"Between them waited {toy.phrase}. When {first.id} pressed it, it said "
        f'"{toy.sound}, {toy.sound}," and both children smiled.'
    )


def want_same_thing(world: World, first: Entity, second: Entity, scene: Scene, toy: Toy) -> None:
    first.memes["want"] += 1
    second.memes["want"] += 1
    world.say(
        f'Soon {first.id} wanted the {toy.label} for {scene.goal}, and {second.id} wanted it too.'
    )
    world.say(
        f'"My turn," said {first.id}. "My turn," said {second.id}. '
        f'The little toy answered, "{toy.sound}, {toy.sound}," as if it had heard them both.'
    )


def warn(world: World, helper: Entity, first: Entity, second: Entity, toy: Toy) -> None:
    pred = predict_tug(world)
    helper.memes["care"] += 1
    world.facts["predicted_fuss"] = pred["fuss"]
    world.facts["predicted_drop"] = pred["drop"]
    extra = "and it might tumble to the rug" if pred["drop"] else "and nobody will enjoy the game"
    world.say(
        f'{helper.id} looked at their hands and said, "One little {toy.label} cannot go in two directions at once. '
        f'If you both pull, the playroom will get loud, {extra}."'
    )


def repeat_grab(world: World, first: Entity, second: Entity, toy: Toy) -> None:
    toy.meters["held_by_first"] += 1
    world.say(f'{first.id} hugged the {toy.label} close. "{first.id} first," {first.pronoun()} said.')
    toy.meters["held_by_second"] += 1
    world.say(f'{second.id} reached too. "{second.id} first," {second.pronoun()} answered.')
    toy.meters["tugged"] += 1
    if world.facts.get("delay", 0) >= 2:
        toy.meters["dropped"] += 1
    propagate(world, narrate=False)
    if world.get("room").meters["noise"] >= THRESHOLD:
        world.say(
            f"Back and forth it went. 'My turn.' 'My turn.' The words kept bumping together faster than the toy could say {toy.sound}."
        )
    if toy.meters["dropped"] >= THRESHOLD:
        world.say(
            f"Then the {toy.label} slipped from both sets of fingers and plopped onto the rug. It went quiet all at once."
        )


def self_share(world: World, first: Entity, second: Entity, toy: Toy, scene: Scene) -> None:
    first.memes["relief"] += 1
    second.memes["relief"] += 1
    first.memes["fairness"] += 1
    second.memes["fairness"] += 1
    world.say(
        f"{first.id} looked at {second.id}, and the hot little feeling in {first.pronoun('possessive')} chest began to shrink."
    )
    world.say(
        f'"You can have the first cheep," said {first.id}. "{second.id} can have the next one after that."'
    )
    world.say(
        f"{second.id} nodded and scooted closer instead of pulling away. Soon the toy was passing from lap to lap, "
        f'and each turn came with the same happy sound: "{toy.sound}, {toy.sound}."'
    )
    world.say(scene.ending_image)


def guided_share(world: World, caregiver: Entity, first: Entity, second: Entity, toy: Toy, plan: Plan, scene: Scene) -> None:
    first.memes["relief"] += 1
    second.memes["relief"] += 1
    first.memes["fairness"] += 1
    second.memes["fairness"] += 1
    world.get("room").meters["noise"] = 0.0
    toy.meters["held_by_first"] = 0.0
    toy.meters["held_by_second"] = 0.0
    toy.meters["tugged"] = 0.0
    world.say(
        f"{caregiver.label_word.capitalize()} came to the rug and knelt beside them. "
        f'"{plan.offer}"'
    )
    world.say(
        f"They listened because {caregiver.label_word} kept {caregiver.pronoun('possessive')} voice soft and steady."
    )
    world.say(
        f"Soon {plan.success} Each child waited, then reached, then heard the toy answer, "
        f'"{toy.sound}, {toy.sound}," in a calmer rhythm.'
    )
    world.say(scene.ending_image)


def reset_then_share(world: World, caregiver: Entity, first: Entity, second: Entity, toy: Toy, plan: Plan, scene: Scene) -> None:
    for kid in (first, second):
        kid.memes["sadness"] += 1
        kid.memes["relief"] += 1
        kid.memes["fairness"] += 1
    world.get("room").meters["noise"] = 0.0
    toy.meters["dropped"] = 0.0
    toy.meters["tugged"] = 0.0
    toy.meters["held_by_first"] = 0.0
    toy.meters["held_by_second"] = 0.0
    toy.meters["cheeping"] = 1.0
    world.say(
        f"{caregiver.label_word.capitalize()} picked up the quiet toy and checked its little key."
    )
    world.say(
        f'"Nobody is in trouble," {caregiver.pronoun()} said. "The {toy.label} needs a tiny rest, and so do your hands."'
    )
    world.say(
        f"They took a breath together. Then {caregiver.pronoun()} {plan.reset} After that, the children tried again more gently."
    )
    world.say(
        f'The toy found its voice again: "{toy.sound}, {toy.sound}." This time the sound came after waiting, not tugging.'
    )
    world.say(scene.ending_image)


def tell(
    scene: Scene,
    toy_cfg: Toy,
    plan: Plan,
    first_name: str = "Mia",
    first_gender: str = "girl",
    second_name: str = "Ben",
    second_gender: str = "boy",
    trait: str = "patient",
    caregiver_type: str = "mother",
    delay: int = 1,
    first_age: int = 4,
    second_age: int = 6,
    relation: str = "siblings",
) -> World:
    world = World()
    first = world.add(Entity(
        id=first_name,
        kind="character",
        type=first_gender,
        role="first",
        traits=["eager"],
        age=first_age,
        attrs={"relation": relation},
    ))
    second = world.add(Entity(
        id=second_name,
        kind="character",
        type=second_gender,
        role="second",
        traits=[trait],
        age=second_age,
        attrs={"relation": relation},
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=caregiver_type,
        role="caregiver",
        label="the caregiver",
    ))
    toy = world.add(Entity(
        id="toy",
        type="toy",
        label=toy_cfg.label,
        phrase=toy_cfg.phrase,
        tags=set(toy_cfg.tags),
    ))
    room = world.add(Entity(id="room", type="room", label="the playroom"))

    first.memes["eagerness"] = EAGERNESS_INIT
    second.memes["peacemaking"] = initial_peacemaking(trait)
    toy.meters["cheeping"] = 1.0
    world.facts["delay"] = delay

    play_setup(world, first, second, scene, toy_cfg)
    world.para()
    want_same_thing(world, first, second, scene, toy_cfg)
    warn(world, second, first, second, toy_cfg)

    self_done = would_self_solve(relation, first_age, second_age, trait)
    if self_done:
        world.para()
        self_share(world, first, second, toy_cfg, scene)
        outcome = "self_share"
    else:
        repeat_grab(world, first, second, toy_cfg)
        world.para()
        if plan_succeeds(plan, toy_cfg, delay):
            guided_share(world, caregiver, first, second, toy_cfg, plan, scene)
            outcome = "guided_share"
        else:
            reset_then_share(world, caregiver, first, second, toy_cfg, plan, scene)
            outcome = "reset_then_share"

    world.facts.update(
        first=first,
        second=second,
        caregiver=caregiver,
        scene=scene,
        toy_cfg=toy_cfg,
        toy=toy,
        plan=plan,
        relation=relation,
        outcome=outcome,
        delay=delay,
        repeated_conflict=room.meters["noise"] >= THRESHOLD or toy.meters["tugged"] >= THRESHOLD,
        dropped=world.facts.get("predicted_drop", False) or toy.meters["dropped"] >= THRESHOLD,
    )
    return world


SCENES = {
    "nest": Scene(
        id="nest",
        opening="a round blanket nest had been built beside the low shelf,",
        game_line="One cushion was the nest wall, one box was the tiny barn, and the whole game was about getting a baby bird home.",
        goal="the next trip to the nest",
        ending_image="At the end, the blanket nest held both children leaning shoulder to shoulder, and the playroom felt small, busy, and peaceful again.",
        tags={"playroom", "sharing"},
    ),
    "parade": Scene(
        id="parade",
        opening="a winding road of wooden blocks curled across the floor,",
        game_line="The children had made a parade path around books, pillows, and a tower of bright cups.",
        goal="the front place in the parade",
        ending_image="At the end, the block road still curved around the room, but now the children were marching beside it together instead of arguing over it.",
        tags={"playroom", "sharing"},
    ),
    "picnic": Scene(
        id="picnic",
        opening="a pretend picnic had spread over the rug,",
        game_line="A small cloth was the picnic blanket, bottle caps were plates, and everyone in the room was invited except cross voices.",
        goal="the next hop to the picnic",
        ending_image="At the end, the pretend picnic looked fuller than before because there was room on the rug for turns and room in the game for both children.",
        tags={"playroom", "sharing"},
    ),
}

TOYS = {
    "windup_chick": Toy(
        id="windup_chick",
        label="little chick",
        phrase="a yellow wind-up chick",
        sound="cheep",
        appeal=2,
        cheeps=True,
        tags={"chick", "cheep", "windup"},
    ),
    "bell_bird": Toy(
        id="bell_bird",
        label="tin bird",
        phrase="a small tin bird with a bell inside",
        sound="cheep",
        appeal=3,
        cheeps=True,
        tags={"bird", "cheep", "bell"},
    ),
    "silent_duck": Toy(
        id="silent_duck",
        label="rubber duck",
        phrase="a rubber duck with faded paint",
        sound="squeak",
        appeal=1,
        cheeps=False,
        tags={"duck"},
    ),
}

PLANS = {
    "count_three": Plan(
        id="count_three",
        sense=3,
        power=3,
        offer="Let's count to three for each turn. When the counting is done, the chick moves kindly to the next lap.",
        success="they counted together and traded the toy every few heartbeats.",
        reset="counted slowly to three for each turn and placed the toy carefully into waiting hands",
        qa_text="used counting so each child got a clear turn",
        tags={"counting", "sharing"},
    ),
    "song_turns": Plan(
        id="song_turns",
        sense=3,
        power=4,
        offer="Let's sing one little turn-song. One song for one child, then one song for the other.",
        success="they used the short song as a turn sign, and the toy moved gently when the song ended.",
        reset="sang one tiny turn-song for each child and passed the toy only when the song was done",
        qa_text="used a short song to mark each turn",
        tags={"song", "sharing"},
    ),
    "basket_wait": Plan(
        id="basket_wait",
        sense=2,
        power=2,
        offer="Let's let the chick rest in the basket between turns, so nobody has to snatch.",
        success="the toy sat in the basket between turns, and waiting became easier to see.",
        reset="set the toy in a small basket between turns so waiting had a place",
        qa_text="put the toy in a basket between turns",
        tags={"basket", "sharing"},
    ),
    "grab_back": Plan(
        id="grab_back",
        sense=1,
        power=1,
        offer="If somebody grabs, the other child should grab harder and win it back.",
        success="they kept grabbing harder and harder.",
        reset="tried to fix things by grabbing back",
        qa_text="told them to grab harder",
        tags={"grabbing"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Nora", "Lucy", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Noah", "Jack", "Finn", "Theo"]
TRAITS = ["patient", "gentle", "kind", "careful", "curious", "bouncy"]


@dataclass
class StoryParams:
    scene: str
    toy: str
    plan: str
    first_name: str
    first_gender: str
    second_name: str
    second_gender: str
    caregiver: str
    trait: str
    delay: int = 1
    first_age: int = 4
    second_age: int = 6
    relation: str = "siblings"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for scene_id in SCENES:
        for toy_id, toy in TOYS.items():
            if toy_fits_story(toy):
                combos.append((scene_id, toy_id))
    return combos


KNOWLEDGE = {
    "chick": [(
        "What sound does a baby chick make?",
        'People often write a baby chick sound as "cheep" or "peep." It is a tiny, high sound.'
    )],
    "windup": [(
        "What is a wind-up toy?",
        "A wind-up toy is a toy with a little key or knob. When you turn it, the toy can move or make a sound for a short time."
    )],
    "sharing": [(
        "What does taking turns mean?",
        "Taking turns means one person goes first and another person waits, then they switch. It helps everyone join the play fairly."
    )],
    "counting": [(
        "How can counting help children share?",
        "Counting gives each turn a clear beginning and end. Then everyone can hear when it is time to switch."
    )],
    "song": [(
        "How can a short song help with turn-taking?",
        "A short song can be like a gentle timer. When the song ends, it is the next person's turn."
    )],
    "basket": [(
        "Why can a basket help children stop grabbing?",
        "A basket gives the toy a waiting place in the middle. Then the toy is not stuck in one person's hands while the other child waits."
    )],
}
KNOWLEDGE_ORDER = ["chick", "windup", "sharing", "counting", "song", "basket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    first = f["first"]
    second = f["second"]
    scene = f["scene"]
    toy = f["toy_cfg"]
    outcome = f["outcome"]
    asks = [
        'Write a short slice-of-life story for a 3-to-5-year-old set in a playroom and include the word "cheep."',
        f"Tell a gentle story where {first.id} and {second.id} both want the same {toy.label}, and the repeated wish causes a small conflict before the game settles.",
        f"Write a playroom story with repetition, conflict, and a calm ending image after the children learn to share during {scene.id} play.",
    ]
    if outcome == "self_share":
        asks.append(
            f"Make the turn happen because an older child speaks kindly before the argument grows too big."
        )
    elif outcome == "reset_then_share":
        asks.append(
            "Include a moment when the toy goes quiet after too much tugging, and a grown-up helps the children start again more gently."
        )
    else:
        asks.append(
            "Include a soft grown-up intervention that turns repeated grabbing into repeated turn-taking."
        )
    return asks


def pair_noun(first: Entity, second: Entity, relation: str) -> str:
    if relation == "siblings":
        if first.type == "boy" and second.type == "boy":
            return "two brothers"
        if first.type == "girl" and second.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    first = f["first"]
    second = f["second"]
    caregiver = f["caregiver"]
    scene = f["scene"]
    toy = f["toy_cfg"]
    plan = f["plan"]
    relation = f["relation"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(first, second, relation)}, {first.id} and {second.id}, in a playroom with their {caregiver.label_word}. The story stays close to one small family moment."
        ),
        (
            f"What toy did the children both want?",
            f"They both wanted the {toy.label}. It was special because it said \"{toy.sound}, {toy.sound}\" and fit right into their pretend game."
        ),
        (
            "Why did the conflict start?",
            f"The conflict started because both children wanted the same toy at the same time for {scene.goal}. The wish kept repeating until their words and hands began to bump into each other."
        ),
    ]
    if outcome == "self_share":
        qa.append((
            f"How was the problem solved?",
            f"{second.id} warned that pulling would spoil the game, and then {first.id} agreed to let the first cheep go to {second.id}. After that, they passed the toy back and forth in turns."
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly and closely, with both children still inside the game instead of outside it. The repeated sound of \"{toy.sound}, {toy.sound}\" changed from part of the quarrel into part of the play."
        ))
    elif outcome == "guided_share":
        qa.append((
            f"What did the grown-up do to help?",
            f"{caregiver.label_word.capitalize()} {plan.qa_text}. That gave the children a clear pattern, so the same repeated wish could turn into repeated turn-taking instead."
        ))
        qa.append((
            "How did the children feel at the end?",
            f"They felt relieved and included. Instead of grabbing, they could wait, listen for the cheep, and know another turn was coming."
        ))
    else:
        qa.append((
            "What happened when the children tugged too much?",
            f"The toy slipped to the rug and went quiet for a moment. That made the children stop and notice that the struggle was spoiling the play they both wanted."
        ))
        qa.append((
            f"How did the grown-up fix the moment after that?",
            f"{caregiver.label_word.capitalize()} reminded them nobody was in trouble and helped them begin again with {plan.qa_text}. The reset mattered because calmer hands let the toy and the game come back."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["toy_cfg"].tags) | {"sharing"} | set(f["plan"].tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="nest",
        toy="windup_chick",
        plan="count_three",
        first_name="Mia",
        first_gender="girl",
        second_name="Ben",
        second_gender="boy",
        caregiver="mother",
        trait="patient",
        delay=1,
        first_age=4,
        second_age=6,
        relation="siblings",
    ),
    StoryParams(
        scene="parade",
        toy="bell_bird",
        plan="song_turns",
        first_name="Leo",
        first_gender="boy",
        second_name="Ava",
        second_gender="girl",
        caregiver="father",
        trait="gentle",
        delay=1,
        first_age=5,
        second_age=5,
        relation="friends",
    ),
    StoryParams(
        scene="picnic",
        toy="windup_chick",
        plan="basket_wait",
        first_name="Nora",
        first_gender="girl",
        second_name="Sam",
        second_gender="boy",
        caregiver="mother",
        trait="curious",
        delay=2,
        first_age=5,
        second_age=5,
        relation="siblings",
    ),
]


def explain_rejection(toy: Toy) -> str:
    return (
        f"(No story: {toy.phrase} does not say \"cheep.\" This world is about a cheeping toy in the playroom, "
        f"so choose a toy like {TOYS['windup_chick'].phrase} or {TOYS['bell_bird'].phrase}.)"
    )


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    better = ", ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense "
        f"(sense={plan.sense} < {SENSE_MIN}). Choose a calmer sharing plan such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_self_solve(params.relation, params.first_age, params.second_age, params.trait):
        return "self_share"
    if plan_succeeds(PLANS[params.plan], TOYS[params.toy], params.delay):
        return "guided_share"
    return "reset_then_share"


ASP_RULES = r"""
valid(Scene, Toy) :- scene(Scene), toy(Toy), cheeps(Toy).
sensible(Plan) :- plan(Plan), sense(Plan, S), sense_min(M), S >= M.

peacemaker_now(T) :- trait(T), peacemaker_trait(T).
init_peacemaking(5) :- trait(T), peacemaker_now(T).
init_peacemaking(3) :- trait(T), not peacemaker_now(T).

older_second :- relation(siblings), first_age(A1), second_age(A2), A2 > A1.
bonus(3) :- older_second.
bonus(0) :- not older_second.
authority(C + 1 + B) :- init_peacemaking(C), bonus(B).
self_share :- older_second, authority(A), eagerness_init(E), A > E.

severity(A + D) :- chosen_toy(T), appeal(T, A), delay(D).
guided_share :- chosen_plan(P), power(P, Pw), severity(Sv), Pw >= Sv.

outcome(self_share) :- self_share.
outcome(guided_share) :- not self_share, guided_share.
outcome(reset_then_share) :- not self_share, not guided_share.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        lines.append(asp.fact("appeal", toy_id, toy.appeal))
        if toy.cheeps:
            lines.append(asp.fact("cheeps", toy_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("power", plan_id, plan.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("eagerness_init", int(EAGERNESS_INIT)))
    for trait in sorted(PEACEMAKER_TRAITS):
        lines.append(asp.fact("peacemaker_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_plans() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(plan for (plan,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_toy", params.toy),
        asp.fact("chosen_plan", params.plan),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("first_age", params.first_age),
        asp.fact("second_age", params.second_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    clingo_plans = set(asp_sensible_plans())
    python_plans = {plan.id for plan in sensible_plans()}
    if clingo_plans == python_plans:
        print(f"OK: sensible plans match ({sorted(clingo_plans)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(clingo_plans)} python={sorted(python_plans)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cheeping toy, repeated wanting, and a small playroom conflict."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [name for name in names if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.toy is not None and not toy_fits_story(TOYS[args.toy]):
        raise StoryError(explain_rejection(TOYS[args.toy]))
    if args.plan is not None and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.toy is None or combo[1] == args.toy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, toy_id = rng.choice(sorted(combos))
    plan_id = args.plan or rng.choice(sorted(plan.id for plan in sensible_plans()))
    first_name, first_gender = _pick_child(rng)
    second_name, second_gender = _pick_child(rng, avoid=first_name)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    first_age, second_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        scene=scene_id,
        toy=toy_id,
        plan=plan_id,
        first_name=first_name,
        first_gender=first_gender,
        second_name=second_name,
        second_gender=second_gender,
        caregiver=caregiver,
        trait=trait,
        delay=delay,
        first_age=first_age,
        second_age=second_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.toy not in TOYS:
        raise StoryError(f"(Unknown toy: {params.toy})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.caregiver not in {"mother", "father"}:
        raise StoryError(f"(Unknown caregiver: {params.caregiver})")
    if not toy_fits_story(TOYS[params.toy]):
        raise StoryError(explain_rejection(TOYS[params.toy]))
    if PLANS[params.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(params.plan))

    world = tell(
        scene=SCENES[params.scene],
        toy_cfg=TOYS[params.toy],
        plan=PLANS[params.plan],
        first_name=params.first_name,
        first_gender=params.first_gender,
        second_name=params.second_name,
        second_gender=params.second_gender,
        trait=params.trait,
        caregiver_type=params.caregiver,
        delay=params.delay,
        first_age=params.first_age,
        second_age=params.second_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible plans: {', '.join(asp_sensible_plans())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, toy) combos:\n")
        for scene_id, toy_id in combos:
            print(f"  {scene_id:8} {toy_id}")
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
            header = f"### {p.first_name} & {p.second_name}: {p.toy} in {p.scene} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
