#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ganache_indoor_play_cafe_misunderstanding_cautionary_suspense.py
=============================================================================================

A standalone story world for a bedtime-style cautionary tale set in an indoor
play café. Two children are playing nearby when one of them misunderstands a
grown-up word -- "ganache" -- and mistakes a warm bowl of real chocolate
ganache for something meant for play. The tension comes from that
misunderstanding and from the child edging closer to a hot, messy thing that
could spill or sting. A calm grown-up notices, stops the mistake, explains what
ganache is, and offers a safe alternative.

The world model keeps track of:
- typed entities with physical meters (warmth, spill, mess, risk)
- emotional memes (curiosity, worry, relief, trust, lesson)
- a small causal rule system: warm ganache near a reaching child creates risk;
  a spill creates mess and worry

The domain enforces a reasonableness gate:
- only some play motifs are close enough to make the misunderstanding plausible
- only some cooling stages are hot enough to make the cautionary beat matter
- only some adult responses are sensible enough to tell as the fix

It also includes an ASP twin for:
- plausible (motif, mistaken_for, cooling) combinations
- sensible responses
- outcome inference (averted / messy)

Run it
------
    python storyworlds/worlds/gpt-5.4/ganache_indoor_play_cafe_misunderstanding_cautionary_suspense.py
    python storyworlds/worlds/gpt-5.4/ganache_indoor_play_cafe_misunderstanding_cautionary_suspense.py --all
    python storyworlds/worlds/gpt-5.4/ganache_indoor_play_cafe_misunderstanding_cautionary_suspense.py --qa
    python storyworlds/worlds/gpt-5.4/ganache_indoor_play_cafe_misunderstanding_cautionary_suspense.py --trace
    python storyworlds/worlds/gpt-5.4/ganache_indoor_play_cafe_misunderstanding_cautionary_suspense.py --verify
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
    warm: bool = False
    edible: bool = False
    pretend: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "barista"}
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
class Motif:
    id: str
    scene: str
    prop_line: str
    goal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MistakenFor:
    id: str
    label: str
    phrase: str
    play_words: str
    needs_touch: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Cooling:
    id: str
    phrase: str
    warmth: int
    suspense_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    safe_alt: str
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


def _r_reach_risk(world: World) -> list[str]:
    child = world.entities.get("child")
    bowl = world.entities.get("ganache")
    room = world.entities.get("room")
    if child is None or bowl is None or room is None:
        return []
    if child.meters["reaching"] < THRESHOLD or bowl.meters["warmth"] < THRESHOLD:
        return []
    sig = ("reach_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    room.meters["risk"] += 1
    return ["__risk__"]


def _r_spill_mess(world: World) -> list[str]:
    bowl = world.entities.get("ganache")
    floor = world.entities.get("floor")
    child = world.entities.get("child")
    if bowl is None or floor is None or child is None:
        return []
    if bowl.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill_mess",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    floor.meters["mess"] += 1
    child.memes["worry"] += 1
    return ["A shiny brown puddle spread across the floor."]


CAUSAL_RULES: list[Rule] = [
    Rule(name="reach_risk", tag="physical", apply=_r_reach_risk),
    Rule(name="spill_mess", tag="physical", apply=_r_spill_mess),
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


def plausible_confusion(motif: Motif, mistaken: MistakenFor) -> bool:
    return bool(motif.tags & mistaken.tags)


def cautionary_cooling(cooling: Cooling) -> bool:
    return cooling.warmth >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def makes_mess(cooling: Cooling, delay: int) -> bool:
    return cooling.warmth + delay >= 3


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["reaching"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("room").meters["risk"],
        "warmth": sim.get("ganache").meters["warmth"],
    }


def introduce_play(world: World, child: Entity, friend: Entity, motif: Motif) -> None:
    for kid in (child, friend):
        kid.memes["joy"] += 1
    world.say(
        f"At the indoor play café, {child.id} and {friend.id} had made {motif.scene}. "
        f"{motif.prop_line}"
    )
    world.say(
        f"They whispered so the tiny plush customers would not be disturbed, and "
        f"the whole corner felt soft and important."
    )


def notice_bowl(world: World, child: Entity, barista: Entity, cooling: Cooling) -> None:
    bowl = world.get("ganache")
    bowl.meters["warmth"] = float(cooling.warmth)
    world.say(
        f"On the real café counter, {barista.label} had set down {cooling.phrase} of ganache "
        f"to rest for a moment."
    )
    world.say(cooling.suspense_line)


def misunderstand(world: World, child: Entity, mistaken: MistakenFor, motif: Motif) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} heard the word ganache and blinked. "
        f'"Ganache?" {child.pronoun().capitalize()} echoed. '
        f'To {child.pronoun("object")}, it sounded exactly like {mistaken.phrase} for {motif.goal}.'
    )
    world.say(
        f"{child.id} looked at the smooth brown shine and decided it must be {mistaken.label}. "
        f"{mistaken.play_words}"
    )


def warn(world: World, friend: Entity, child: Entity, mistaken: MistakenFor) -> None:
    pred = predict_risk(world)
    world.facts["predicted_risk"] = pred["risk"]
    friend.memes["caution"] += 1
    extra = ""
    if pred["warmth"] >= 2:
        extra = " It looked too warm to be a toy."
    world.say(
        f'{friend.id} caught a tiny breath. "{child.id}, wait," {friend.pronoun()} said. '
        f'"That is on the real counter. It might be food, not {mistaken.label}."{extra}'
    )


def edge_closer(world: World, child: Entity, mistaken: MistakenFor) -> None:
    child.meters["reaching"] += 1
    child.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the bowl was glossy and interesting, and {child.id} took one slow step closer. "
        f'{child.pronoun().capitalize()} lifted one finger, ready to test whether ganache felt '
        f"like {mistaken.label}."
    )


def stop_in_time(world: World, barista: Entity, child: Entity, response: Response) -> None:
    child.meters["reaching"] = 0.0
    room = world.get("room")
    room.meters["risk"] = 0.0
    world.say(
        f"Just then, {barista.label} turned and saw the little hand. "
        f"{response.text}"
    )
    world.say(
        f'"This is ganache," {barista.pronoun()} said gently. '
        f'"It is real chocolate for cakes, and it can still be warm."'
    )


def small_mess(world: World, barista: Entity, child: Entity, response: Response) -> None:
    bowl = world.get("ganache")
    bowl.meters["spilled"] += 1
    bowl.meters["warmth"] = max(0.0, bowl.meters["warmth"] - 1.0)
    propagate(world, narrate=True)
    world.say(
        f"Before anyone could reach it, the bowl tipped at the edge and a little ganache slipped over the rim. "
        f"{response.text}"
    )
    world.say(
        f'"Good thing no hands were under it," {barista.pronoun()} said. '
        f'"Ganache is for eating, not for play, and warm spills can surprise you."'
    )


def explain_and_offer(world: World, barista: Entity, child: Entity, friend: Entity,
                      response: Response, mistaken: MistakenFor, motif: Motif) -> None:
    for kid in (child, friend):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"{barista.label} knelt so {child.id} and {friend.id} could see {barista.pronoun('object')} clearly. "
        f'"When you are not sure what something is in a café, you must ask first," '
        f'{barista.pronoun()} said. "Real kitchen things are not part of the game."'
    )
    world.say(
        f"Then {barista.pronoun()} smiled and brought them {response.safe_alt}. "
        f"Now they could make {mistaken.label} for {motif.goal} without touching the real counter."
    )


def calm_ending(world: World, child: Entity, friend: Entity, motif: Motif, mistaken: MistakenFor) -> None:
    for kid in (child, friend):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"Soon the two children were back in {motif.scene}, patting and stirring their safe pretend {mistaken.label}. "
        f"This time, when they heard a grown-up word, they asked what it meant before the game went on."
    )
    world.say(
        f"And the indoor play café grew cozy again, with soft cups, soft voices, and no more secret reaching."
    )


def tell(motif: Motif, mistaken: MistakenFor, cooling: Cooling, response: Response,
         child_name: str = "Lila", child_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         barista_type: str = "mother", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    barista = world.add(Entity(
        id="Barista",
        kind="character",
        type=barista_type,
        role="barista",
        label="the café helper",
    ))
    world.add(Entity(id="room", type="room", label="the café"))
    world.add(Entity(id="floor", type="floor", label="the floor"))
    bowl = world.add(Entity(
        id="ganache",
        type="food",
        label="ganache",
        phrase="a bowl of ganache",
        warm=True,
        edible=True,
        movable=True,
        tags={"ganache", "cafe", "food"},
    ))

    introduce_play(world, child, friend, motif)
    notice_bowl(world, child, barista, cooling)

    world.para()
    misunderstand(world, child, mistaken, motif)
    warn(world, friend, child, mistaken)
    edge_closer(world, child, mistaken)

    world.para()
    outcome = "averted"
    if makes_mess(cooling, delay):
        outcome = "messy"
        small_mess(world, barista, child, response)
    else:
        stop_in_time(world, barista, child, response)

    world.para()
    explain_and_offer(world, barista, child, friend, response, mistaken, motif)
    calm_ending(world, child, friend, motif, mistaken)

    world.facts.update(
        motif=motif,
        mistaken=mistaken,
        cooling=cooling,
        response=response,
        child=child,
        friend=friend,
        barista=barista,
        bowl=bowl,
        delay=delay,
        outcome=outcome,
        asked_first=child.memes["lesson"] >= THRESHOLD,
        messy=outcome == "messy",
    )
    return world


MOTIFS = {
    "bakery": Motif(
        id="bakery",
        scene="a pretend bakery under the climbing ramp",
        prop_line="A stack of felt cookies was their window display, a tray of foam cakes was cooling on a bench, and a bell made from a bottle cap rang whenever a new customer arrived.",
        goal="their bakery",
        tags={"frosting", "sauce", "mix"},
    ),
    "tea_party": Motif(
        id="tea_party",
        scene="a tiny tea room beside the book nook",
        prop_line="Plastic cups sat in a neat circle, two plush rabbits waited for buns, and a paper menu promised cocoa, soup, and moon cakes.",
        goal="their tea party",
        tags={"soup", "sauce", "mix"},
    ),
    "mud_kitchen": Motif(
        id="mud_kitchen",
        scene="an indoor mud kitchen made of felt bowls and wooden spoons",
        prop_line="The children had named the brown pom-poms beans, the beige cloth squares crackers, and the soft blocks little ovens for imaginary pies.",
        goal="their mud kitchen",
        tags={"mud", "sauce", "mix"},
    ),
}

MISTAKEN = {
    "frosting": MistakenFor(
        id="frosting",
        label="pretend frosting",
        phrase="pretend frosting",
        play_words="Maybe it belonged on the toy cupcakes after all.",
        tags={"frosting", "mix"},
    ),
    "soup": MistakenFor(
        id="soup",
        label="pretend soup",
        phrase="pretend soup",
        play_words="Maybe it was the special chocolate soup from the paper menu.",
        tags={"soup", "sauce"},
    ),
    "mud": MistakenFor(
        id="mud",
        label="pretend mud sauce",
        phrase="pretend mud sauce",
        play_words="Maybe it was the rich brown sauce for their make-believe pies.",
        tags={"mud", "sauce"},
    ),
}

COOLING = {
    "very_warm": Cooling(
        id="very_warm",
        phrase="a very warm silver bowl",
        warmth=2,
        suspense_line="A little thread of steam still curled above it, thin as a whisper.",
        tags={"hot", "cafe"},
    ),
    "warm": Cooling(
        id="warm",
        phrase="a warm bowl",
        warmth=1,
        suspense_line="The bowl no longer steamed, but it still looked fresh and glossy, as if it had only just been stirred.",
        tags={"warm", "cafe"},
    ),
    "cooling": Cooling(
        id="cooling",
        phrase="a bowl that was nearly cool",
        warmth=0,
        suspense_line="It sat very still and shiny, more mysterious than dangerous.",
        tags={"cool", "cafe"},
    ),
}

RESPONSES = {
    "lift_and_explain": Response(
        id="lift_and_explain",
        sense=3,
        power=3,
        text="In one smooth motion, the helper lifted the bowl higher onto a back shelf and guided the child a careful step away.",
        qa_text="lifted the bowl away and guided the child back",
        safe_alt="a tray of brown play dough and a blunt little spatula",
        tags={"ask_first", "play_dough", "ganache"},
    ),
    "block_and_name": Response(
        id="block_and_name",
        sense=3,
        power=2,
        text="The helper slid a tray between the bowl and the children, then set a steady hand on the counter so no one would lean farther in.",
        qa_text="blocked the bowl with a tray and stopped the reaching",
        safe_alt="a dish of cocoa-colored foam and toy spoons",
        tags={"ask_first", "foam", "ganache"},
    ),
    "call_from_across_room": Response(
        id="call_from_across_room",
        sense=1,
        power=1,
        text="The helper called, 'Careful!' from across the room and hoped the children would stop on their own.",
        qa_text="called a warning from far away",
        safe_alt="a bowl of play dough",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Ella", "Lucy", "Sana", "Ruby"]
BOY_NAMES = ["Ben", "Theo", "Max", "Leo", "Sam", "Noah", "Finn", "Eli"]
TRAITS = ["careful", "curious", "gentle", "eager", "thoughtful"]


@dataclass
class StoryParams:
    motif: str
    mistaken_for: str
    cooling: str
    response: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    helper_type: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for motif_id, motif in MOTIFS.items():
        for mistaken_id, mistaken in MISTAKEN.items():
            for cooling_id, cooling in COOLING.items():
                if plausible_confusion(motif, mistaken) and cautionary_cooling(cooling):
                    combos.append((motif_id, mistaken_id, cooling_id))
    return combos


KNOWLEDGE = {
    "ganache": [(
        "What is ganache?",
        "Ganache is a smooth chocolate mixture, often made with chocolate and warm cream. Grown-ups use it for cakes and other treats."
    )],
    "ask_first": [(
        "What should a child do if they are not sure what something is in a café?",
        "They should stop and ask a grown-up first. Real kitchen things may be hot, sharp, or meant only for food."
    )],
    "play_dough": [(
        "Why is play dough safer than real kitchen food for pretend play?",
        "Play dough is made for hands and make-believe games. Real kitchen food can be hot, messy, or not meant to be touched while someone is cooking."
    )],
    "foam": [(
        "Why do some play cafés use foam or toy food in the play area?",
        "Foam and toy food are light and safe for pretending. They let children copy real life without touching real kitchen tools or hot food."
    )],
    "cafe": [(
        "What is an indoor play café?",
        "An indoor play café is a place where children can play while grown-ups sit nearby. It often has a play corner and a real food counter, so some things are for games and some are not."
    )],
}
KNOWLEDGE_ORDER = ["cafe", "ganache", "ask_first", "play_dough", "foam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    mistaken = f["mistaken"]
    motif = f["motif"]
    outcome = f["outcome"]
    if outcome == "messy":
        return [
            'Write a bedtime-style story set in an indoor play café that includes the word "ganache" and a misunderstanding.',
            f"Tell a gentle suspense story where {child.id} mistakes real ganache for {mistaken.label} in {motif.goal}, and a grown-up stops things after a small spill.",
            "Write a cautionary story for very young children about asking first when something in a café might be real food instead of part of the game.",
        ]
    return [
        'Write a bedtime-style story set in an indoor play café that includes the word "ganache" and a misunderstanding.',
        f"Tell a soft suspense story where {child.id} moves toward real ganache, {friend.id} warns {child.pronoun('object')}, and a calm helper stops the mistake in time.",
        "Write a cautionary story for very young children about hearing a new word, misunderstanding it, and learning to ask before touching something on a café counter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    barista = f["barista"]
    motif = f["motif"]
    mistaken = f["mistaken"]
    cooling = f["cooling"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {friend.id} playing in an indoor play café, and the café helper who kept them safe. The story follows a misunderstanding about the word ganache."
        ),
        (
            "What misunderstanding started the trouble?",
            f"{child.id} heard the word ganache and thought it meant {mistaken.label} for {motif.goal}. The shiny brown bowl looked close enough to the game that the mistake felt real."
        ),
        (
            "Why did the moment feel suspenseful?",
            f"It felt suspenseful because {child.id} edged closer with a hand ready to touch the bowl. {friend.id} worried it might be real food on the counter, and {cooling.phrase} could still be warm."
        ),
    ]
    if outcome == "messy":
        qa.append((
            "What happened before the helper fully stopped the mistake?",
            f"A little ganache spilled over the rim and made a brown mess on the floor. That showed why the counter was not part of the game and why warm food must be treated carefully."
        ))
    else:
        qa.append((
            "How did the helper keep the children safe?",
            f"The helper {response.qa_text}. The danger ended because the real bowl was moved away before any spill or touch could happen."
        ))
    qa.append((
        "What lesson did the children learn?",
        f"They learned to ask first when they are not sure what something is in a café. Real kitchen things are different from play things, even when they look like part of the game."
    ))
    qa.append((
        "How did the story end?",
        f"It ended calmly, with a safe pretend substitute and the children back at play. The cozy ending proves that asking first changed the game from risky guessing to safe make-believe."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ganache", "cafe"} | set(f["response"].tags)
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
        flags = [name for name, on in (("warm", e.warm), ("edible", e.edible), ("pretend", e.pretend)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        motif="bakery",
        mistaken_for="frosting",
        cooling="warm",
        response="lift_and_explain",
        child_name="Lila",
        child_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper_type="mother",
        delay=0,
    ),
    StoryParams(
        motif="tea_party",
        mistaken_for="soup",
        cooling="very_warm",
        response="block_and_name",
        child_name="Mia",
        child_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        helper_type="father",
        delay=0,
    ),
    StoryParams(
        motif="mud_kitchen",
        mistaken_for="mud",
        cooling="very_warm",
        response="lift_and_explain",
        child_name="Nora",
        child_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        helper_type="mother",
        delay=1,
    ),
]


def explain_rejection(motif: Motif, mistaken: MistakenFor, cooling: Cooling) -> str:
    if not plausible_confusion(motif, mistaken):
        return (
            f"(No story: in {motif.goal}, ganache would not naturally be mistaken for {mistaken.label}. "
            f"The misunderstanding must be plausible enough for a child to make.)"
        )
    if not cautionary_cooling(cooling):
        return (
            f"(No story: {cooling.phrase} is not warm enough to create a cautionary moment. "
            f"Pick a warm or very warm bowl so the warning matters.)"
        )
    return "(No story: this combination does not create a strong misunderstanding.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    cooling = COOLING[params.cooling]
    return "messy" if makes_mess(cooling, params.delay) else "averted"


ASP_RULES = r"""
plausible(M, X) :- motif_tag(M, T), mistaken_tag(X, T).
cautionary(C) :- cooling(C), warmth(C, W), W >= 1.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(M, X, C) :- motif(M), mistaken(X), cooling(C), plausible(M, X), cautionary(C).

messy :- chosen_cooling(C), warmth(C, W), delay(D), W + D >= 3.
outcome(messy) :- messy.
outcome(averted) :- not messy.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, motif in MOTIFS.items():
        lines.append(asp.fact("motif", mid))
        for tag in sorted(motif.tags):
            lines.append(asp.fact("motif_tag", mid, tag))
    for xid, mistaken in MISTAKEN.items():
        lines.append(asp.fact("mistaken", xid))
        for tag in sorted(mistaken.tags):
            lines.append(asp.fact("mistaken_tag", xid, tag))
    for cid, cooling in COOLING.items():
        lines.append(asp.fact("cooling", cid))
        lines.append(asp.fact("warmth", cid, cooling.warmth))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_cooling", params.cooling),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: ganache, misunderstanding, and a calm caution in an indoor play café."
    )
    ap.add_argument("--motif", choices=MOTIFS)
    ap.add_argument("--mistaken-for", choices=MISTAKEN, dest="mistaken_for")
    ap.add_argument("--cooling", choices=COOLING)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra beat before the helper reaches the bowl")
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.motif and args.mistaken_for and args.cooling:
        motif = MOTIFS[args.motif]
        mistaken = MISTAKEN[args.mistaken_for]
        cooling = COOLING[args.cooling]
        if not (plausible_confusion(motif, mistaken) and cautionary_cooling(cooling)):
            raise StoryError(explain_rejection(motif, mistaken, cooling))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.motif is None or c[0] == args.motif)
        and (args.mistaken_for is None or c[1] == args.mistaken_for)
        and (args.cooling is None or c[2] == args.cooling)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    motif_id, mistaken_id, cooling_id = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=child_name)
    helper = args.helper or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    return StoryParams(
        motif=motif_id,
        mistaken_for=mistaken_id,
        cooling=cooling_id,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_type=helper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.motif not in MOTIFS:
        raise StoryError(f"Unknown motif: {params.motif}")
    if params.mistaken_for not in MISTAKEN:
        raise StoryError(f"Unknown mistaken_for: {params.mistaken_for}")
    if params.cooling not in COOLING:
        raise StoryError(f"Unknown cooling: {params.cooling}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    motif = MOTIFS[params.motif]
    mistaken = MISTAKEN[params.mistaken_for]
    cooling = COOLING[params.cooling]
    response = RESPONSES[params.response]
    if not plausible_confusion(motif, mistaken) or not cautionary_cooling(cooling):
        raise StoryError(explain_rejection(motif, mistaken, cooling))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        motif=motif,
        mistaken=mistaken,
        cooling=cooling,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        barista_type=params.helper_type,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (motif, mistaken_for, cooling) combos:\n")
        for motif, mistaken, cooling in combos:
            print(f"  {motif:10} {mistaken:10} {cooling}")
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
                f"### {p.child_name} & {p.friend_name}: ganache mistaken for "
                f"{p.mistaken_for} ({p.motif}, {p.cooling}, {outcome_of(p)})"
            )
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
