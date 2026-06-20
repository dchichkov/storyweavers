#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/restrain_intimate_chandelier_problem_solving_inner_monologue.py
================================================================================================

A standalone story world about a young superhero using magic and careful thinking
to solve a chandelier emergency during a city celebration.

Seed requirements embodied here:
- includes the words "restrain", "intimate", and "chandelier"
- uses Problem Solving, Inner Monologue, and Magic
- keeps a child-facing Superhero Story tone

Domain sketch
-------------
A child hero helps prepare a special night in a grand room. There is always a
beautiful chandelier and also an intimate little corner inside the larger place:
a snug reading nook, a quiet balcony cove, or a velvet window seat. A spell goes
wrong. The chandelier begins to swing, tangle, or blaze too brightly. The hero
must first restrain the danger around other people, then choose a magical fix
that actually matches the problem. Good fixes lead to a bright superhero ending.
Weak or mismatched fixes are rejected up front, and slow/weak responses can lead
to a "show saved, chandelier lost" ending where nobody is hurt but the party has
to move to a smaller, gentler light.

Run it
------
python storyworlds/worlds/gpt-5.4/restrain_intimate_chandelier_problem_solving_inner_monologue.py
python storyworlds/worlds/gpt-5.4/restrain_intimate_chandelier_problem_solving_inner_monologue.py --all
python storyworlds/worlds/gpt-5.4/restrain_intimate_chandelier_problem_solving_inner_monologue.py --qa --json
python storyworlds/worlds/gpt-5.4/restrain_intimate_chandelier_problem_solving_inner_monologue.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
    intimate_corner: str
    crowd: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ChandelierCfg:
    id: str
    label: str
    phrase: str
    made_of: str
    weight: int
    fragile: bool
    supports: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Mishap:
    id: str
    label: str
    verb: str
    problem: str
    effect: str
    base: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    handles: set[str]
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CapeStyle:
    id: str
    label: str
    shimmer: str
    restrain_text: str
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

    def people(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_danger(world: World) -> list[str]:
    room = world.get("room")
    chandelier = world.get("chandelier")
    if chandelier.meters["unstable"] < THRESHOLD:
        return []
    sig = ("danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["danger"] += 1
    for person in world.people():
        if person.role in {"hero", "mentor"}:
            person.memes["worry"] += 1
    return ["__danger__"]


def _r_fear_clears(world: World) -> list[str]:
    room = world.get("room")
    if room.meters["restrained_zone"] < THRESHOLD or room.meters["danger"] < THRESHOLD:
        return []
    sig = ("crowd_safe",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["crowd_safe"] += 1
    return []


CAUSAL_RULES = [
    Rule("danger", "physical", _r_danger),
    Rule("crowd_safe", "social", _r_fear_clears),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def hazard_at_risk(chandelier: ChandelierCfg, mishap: Mishap) -> bool:
    return mishap.id in chandelier.supports


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_works(response: Response, mishap: Mishap) -> bool:
    return mishap.id in response.handles


def severity_of(chandelier: ChandelierCfg, mishap: Mishap, delay: int) -> int:
    bonus = 1 if chandelier.fragile and mishap.id == "swing" else 0
    return mishap.base + delay + bonus


def is_saved(response: Response, chandelier: ChandelierCfg, mishap: Mishap, delay: int) -> bool:
    if not response_works(response, mishap):
        return False
    return response.power >= severity_of(chandelier, mishap, delay)


def predict_risk(world: World, mishap: Mishap) -> dict:
    sim = world.copy()
    ch = sim.get("chandelier")
    ch.meters["unstable"] += 1
    ch.attrs["mishap"] = mishap.id
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "unstable": ch.meters["unstable"],
    }


def introduce(world: World, hero: Entity, mentor: Entity, venue: Venue, cape: CapeStyle,
              chandelier: ChandelierCfg) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {venue.place}, {hero.id} zipped in with {cape.label} fluttering behind "
        f"{hero.pronoun('object')}. Tonight was {venue.purpose}, and the whole place "
        f"waited under {chandelier.phrase}."
    )
    world.say(
        f"Off to one side was {venue.intimate_corner}, a small calm pocket inside the big bright room. "
        f"{mentor.id}, {hero.id}'s {mentor.label_word}, called it the best place for a brave hero to think."
    )


def setup_power(world: World, hero: Entity, venue: Venue) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"{hero.id} was not just any child. {hero.pronoun().capitalize()} was the kind of neighborhood hero "
        f"who listened first, then used magic second. {venue.crowd.capitalize()} would soon arrive, "
        f"and {hero.pronoun()} wanted every light to shine safely."
    )


def mishap_begins(world: World, hero: Entity, mishap: Mishap, chandelier: ChandelierCfg) -> None:
    ch = world.get("chandelier")
    ch.meters["unstable"] += 1
    ch.attrs["mishap"] = mishap.id
    propagate(world, narrate=False)
    world.say(
        f"But just as {hero.id} touched the air with a sparkle of magic, {chandelier.label} {mishap.verb}. "
        f"{mishap.effect}"
    )


def inner_monologue(world: World, hero: Entity, mishap: Mishap, mentor: Entity) -> None:
    pred = predict_risk(world, mishap)
    hero.memes["resolve"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'"Hold on," {hero.id} thought. "First I have to restrain the danger, then I can solve the spell."'
    )
    extra = " If it fell, someone could be right underneath it." if pred["danger"] >= THRESHOLD else ""
    world.say(
        f'"What is the problem really?" {hero.pronoun()} asked {hero.pronoun("object")}self. '
        f'"The chandelier is {mishap.problem}, and people need space."{extra}'
    )
    world.say(
        f"{mentor.id} saw the careful look on {hero.id}'s face and gave one quick nod."
    )


def restrain_crowd(world: World, hero: Entity, cape: CapeStyle, venue: Venue) -> None:
    room = world.get("room")
    room.meters["restrained_zone"] += 1
    hero.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At once, {hero.id} swept {cape.label} in a shining curve. {cape.restrain_text} "
        f"The magic did not trap anyone; it simply marked a safe line and gently held {venue.crowd} back."
    )


def solve(world: World, hero: Entity, mentor: Entity, response: Response,
          chandelier: ChandelierCfg, mishap: Mishap) -> None:
    world.say(
        f'"Now for step two," {hero.id} thought. "{response.qa_text.capitalize()}."'
    )
    world.say(
        f"{hero.id} lifted both hands, and {response.text}"
    )
    world.get("chandelier").meters["stable"] += 1
    world.get("chandelier").meters["unstable"] = 0.0
    world.get("room").meters["danger"] = 0.0
    hero.memes["relief"] += 1
    mentor.memes["pride"] += 1
    world.say(
        f"The room let out one long breath. The {chandelier.label} settled, and the superhero problem was solved."
    )


def fail_softly(world: World, hero: Entity, mentor: Entity, response: Response,
                chandelier: ChandelierCfg, mishap: Mishap, venue: Venue) -> None:
    ch = world.get("chandelier")
    room = world.get("room")
    hero.memes["sad"] += 1
    mentor.memes["care"] += 1
    ch.meters["cracked"] += 1 if chandelier.fragile else 0
    ch.meters["lowered"] += 1
    room.meters["danger"] = 0.0
    world.say(
        f"{hero.id} tried, and {response.fail}."
    )
    if chandelier.fragile:
        world.say(
            f"A few pieces chimed and cracked, but because the safe line was already in place, nobody was under the chandelier."
        )
    else:
        world.say(
            f"The big light had to be lowered early, but because the safe line was already in place, nobody was under it."
        )
    world.say(
        f'"I did not save the chandelier," {hero.id} thought, "but I did save the people."'
    )
    world.say(
        f"{mentor.id} squeezed {hero.id}'s shoulder. \"That is what real heroes do first,\" {mentor.pronoun()} said."
    )
    world.say(
        f"So the celebration moved to {venue.intimate_corner}, where smaller lanterns glowed warm and close. "
        f"It was quieter than the grand plan, but it was safe, and the night still felt magical."
    )


def celebrate(world: World, hero: Entity, mentor: Entity, venue: Venue, cape: CapeStyle) -> None:
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Soon the doors opened. {venue.crowd.capitalize()} looked up, then cheered for the young hero with the {cape.shimmer} cape."
    )
    world.say(
        f"{hero.id} only smiled. Inside, {hero.pronoun()} kept one small thought like a bright badge: "
        f'"Magic is strongest when it listens."'
    )


def tell(venue: Venue, chandelier: ChandelierCfg, mishap: Mishap, response: Response,
         cape: CapeStyle, hero_name: str = "Nova", hero_type: str = "girl",
         mentor_type: str = "mother", mentor_name: str = "Aunt Mira", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                            traits=["brave", "careful"]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_type, role="mentor",
                              label="the mentor"))
    room = world.add(Entity(id="room", type="hall", label=venue.place))
    ch = world.add(Entity(id="chandelier", type="chandelier", label=chandelier.label,
                          attrs={"made_of": chandelier.made_of}))

    introduce(world, hero, mentor, venue, cape, chandelier)
    setup_power(world, hero, venue)

    world.para()
    mishap_begins(world, hero, mishap, chandelier)
    inner_monologue(world, hero, mishap, mentor)
    restrain_crowd(world, hero, cape, venue)

    saved = is_saved(response, chandelier, mishap, delay)

    world.para()
    if saved:
        solve(world, hero, mentor, response, chandelier, mishap)
        world.para()
        celebrate(world, hero, mentor, venue, cape)
        outcome = "saved"
    else:
        fail_softly(world, hero, mentor, response, chandelier, mishap, venue)
        outcome = "moved"

    world.facts.update(
        venue=venue,
        chandelier_cfg=chandelier,
        mishap=mishap,
        response=response,
        cape=cape,
        hero=hero,
        mentor=mentor,
        delay=delay,
        outcome=outcome,
        crowd_restrained=room.meters["restrained_zone"] >= THRESHOLD,
        severity=severity_of(chandelier, mishap, delay),
        saved=saved,
    )
    return world


VENUES = {
    "library_hall": Venue(
        "library_hall",
        "the Moonbeam Library hall",
        "an intimate reading nook with two velvet chairs beneath the balcony",
        "families and sleepy-eyed readers",
        "Starlight Thank-You Night",
        tags={"library", "intimate"},
    ),
    "museum_atrium": Venue(
        "museum_atrium",
        "the City Museum atrium",
        "an intimate window seat tucked behind a marble column",
        "neighbors in bright party shoes",
        "Hero Helpers Night",
        tags={"museum", "intimate"},
    ),
    "sky_theater": Venue(
        "sky_theater",
        "the Sky Theater foyer",
        "an intimate velvet cove beside the ticket arch",
        "children wearing paper masks",
        "the Midnight Cape Parade",
        tags={"theater", "intimate"},
    ),
}

CHANDELIERS = {
    "crystal": ChandelierCfg(
        "crystal",
        "crystal chandelier",
        "a huge crystal chandelier",
        "glass and silver drops",
        weight=3,
        fragile=True,
        supports={"swing", "flare"},
        tags={"chandelier", "crystal"},
    ),
    "moonglass": ChandelierCfg(
        "moonglass",
        "moonglass chandelier",
        "a moonglass chandelier shaped like a silver moon",
        "moonglass bowls and rings",
        weight=2,
        fragile=False,
        supports={"flare", "tangle"},
        tags={"chandelier", "moonlight"},
    ),
    "vine_lantern": ChandelierCfg(
        "vine_lantern",
        "vine-lantern chandelier",
        "a vine-lantern chandelier braided with glowing leaves",
        "glowing leaves and light wood",
        weight=2,
        fragile=False,
        supports={"swing", "tangle"},
        tags={"chandelier", "vines"},
    ),
}

MISHAPS = {
    "swing": Mishap(
        "swing",
        "wild wind spell",
        "began to swing in great shining arcs",
        "swinging too hard",
        "Its chain groaned, and bright pieces flashed across the ceiling.",
        base=2,
        tags={"wind", "danger"},
    ),
    "tangle": Mishap(
        "tangle",
        "runaway vine spell",
        "sprouted loops of glowing vine that wrapped around itself",
        "tangled and pulling against its own chain",
        "The hanging loops tightened and tugged from three sides at once.",
        base=1,
        tags={"vines", "danger"},
    ),
    "flare": Mishap(
        "flare",
        "starburst spell",
        "flared so brightly that the whole room squinted",
        "glowing too fiercely",
        "Little sparks skipped from crystal to crystal like tiny jumping stars.",
        base=2,
        tags={"light", "danger"},
    ),
}

RESPONSES = {
    "moon_lasso": Response(
        "moon_lasso",
        sense=3,
        power=3,
        handles={"swing", "tangle"},
        text="a ribbon of moonlight curled upward, looped the chandelier, and drew it gently back to center",
        fail="a ribbon of moonlight curled upward, but the pull was too small to tame the runaway magic",
        qa_text="use the moon lasso to pull the chandelier back to center",
        tags={"moon_lasso", "magic"},
    ),
    "hush_charm": Response(
        "hush_charm",
        sense=3,
        power=3,
        handles={"flare"},
        text="a soft blue hush spread over the light, dimming each spark until the room could open its eyes again",
        fail="the hush charm softened the glare for a second, but the sparks kept jumping brighter than before",
        qa_text="cast a hush charm to calm the light",
        tags={"hush_charm", "magic"},
    ),
    "anchor_knots": Response(
        "anchor_knots",
        sense=2,
        power=2,
        handles={"tangle", "swing"},
        text="three glowing anchor knots leapt from finger to finger and fastened the chandelier still",
        fail="the anchor knots caught for a moment, but then slipped as the strain grew worse",
        qa_text="tie anchor knots to hold it still",
        tags={"anchor_knots", "magic"},
    ),
    "mirror_shell": Response(
        "mirror_shell",
        sense=2,
        power=2,
        handles={"flare"},
        text="a round mirror-shell opened around the light and folded the sharp brightness safely inward",
        fail="the mirror-shell formed, but the fierce light pushed right through its silver skin",
        qa_text="wrap it in a mirror shell",
        tags={"mirror_shell", "magic"},
    ),
    "blast_back": Response(
        "blast_back",
        sense=1,
        power=1,
        handles={"swing", "flare"},
        text="a hard burst of force smacked the magic away",
        fail="a hard burst of force only made the trouble bounce back twice as wild",
        qa_text="blast the magic back",
        tags={"blast_back", "magic"},
    ),
}

CAPES = {
    "comet": CapeStyle(
        "comet",
        "a comet-blue cape",
        "silver-comet shimmer",
        "A curved wall of blue light appeared like a friendly half-moon",
        tags={"cape"},
    ),
    "violet": CapeStyle(
        "violet",
        "a violet cape",
        "violet-spark shimmer",
        "A soft violet ring swept across the floor in one bright circle",
        tags={"cape"},
    ),
    "gold": CapeStyle(
        "gold",
        "a gold cape",
        "gold-thread shimmer",
        "A bright gold ribbon unrolled from the cape hem and drew a calm glowing boundary",
        tags={"cape"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Tess", "Ruby", "Skye"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Kai", "Jude"]
MENTOR_NAMES = ["Aunt Mira", "Captain Sol", "Mom", "Dad"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id in VENUES:
        for chandelier_id, chandelier in CHANDELIERS.items():
            for mishap_id, mishap in MISHAPS.items():
                if hazard_at_risk(chandelier, mishap):
                    combos.append((venue_id, chandelier_id, mishap_id))
    return combos


@dataclass
class StoryParams:
    venue: str
    chandelier: str
    mishap: str
    response: str
    cape: str
    hero_name: str
    hero_type: str
    mentor_type: str
    mentor_name: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "chandelier": [
        ("What is a chandelier?",
         "A chandelier is a hanging light that drops down from the ceiling with many arms or shining pieces.")
    ],
    "magic": [
        ("What is magic in a pretend superhero story?",
         "Magic is a special pretend power that can change light, air, or objects. A good hero still has to think carefully about how to use it.")
    ],
    "danger": [
        ("Why should people move back from a swinging ceiling light?",
         "A swinging ceiling light can fall or drop pieces. Moving back gives everyone space and keeps them safer.")
    ],
    "moon_lasso": [
        ("What does a lasso do?",
         "A lasso loops around something so you can guide or hold it. In a magic story, a moon lasso can do that with light instead of rope.")
    ],
    "hush_charm": [
        ("What does it mean to calm a bright light?",
         "It means making the light softer and steadier, so it stops hurting eyes or throwing sparks.")
    ],
    "anchor_knots": [
        ("What are anchor knots for?",
         "Anchor knots hold something in place so it does not pull loose or swing around.")
    ],
    "mirror_shell": [
        ("What is a mirror shell in a pretend story?",
         "It is a shiny magic cover that bounces or folds light inward so the light stays contained.")
    ],
    "intimate": [
        ("What does intimate mean in a place like a reading nook?",
         "It means small, close, and cozy. An intimate corner feels calm and tucked away.")
    ],
}
KNOWLEDGE_ORDER = [
    "chandelier", "magic", "danger", "moon_lasso", "hush_charm",
    "anchor_knots", "mirror_shell", "intimate"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    venue = f["venue"]
    mishap = f["mishap"]
    chandelier = f["chandelier_cfg"]
    response = f["response"]
    if f["outcome"] == "saved":
        return [
            f'Write a child-friendly superhero story that includes the words "restrain", "intimate", and "chandelier".',
            f"Tell a magical problem-solving story where {hero.id} faces a {mishap.label} in {venue.place}, thinks through the danger with an inner monologue, and saves the {chandelier.label} with {response.id}.",
            f"Write a short superhero story with careful thinking instead of smashing, where a child hero protects a crowd first and solves the magic second.",
        ]
    return [
        f'Write a child-friendly superhero story that includes the words "restrain", "intimate", and "chandelier".',
        f"Tell a magical problem-solving story where {hero.id} faces a {mishap.label} in {venue.place}, protects everyone, but cannot fully save the {chandelier.label}.",
        f"Write a superhero story with inner monologue where the hero learns that saving people matters more than saving a fancy object.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    venue = f["venue"]
    chandelier = f["chandelier_cfg"]
    mishap = f["mishap"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a young superhero named {hero.id} and {hero.pronoun('possessive')} {mentor.label_word}, {mentor.id}. "
            f"They were helping get {venue.place} ready for a special night."
        ),
        (
            "What problem started the adventure?",
            f"A {mishap.label} made the {chandelier.label} turn dangerous. "
            f"It was {mishap.problem}, so {hero.id} had to think fast before the crowd came in."
        ),
        (
            f"What did {hero.id} think first?",
            f"{hero.id} decided to restrain the danger before trying to fix the magic. "
            f"That inner monologue helped {hero.pronoun('object')} solve the problem in the right order."
        ),
    ]
    if f["crowd_restrained"]:
        qa.append((
            f"How did {hero.id} protect everyone?",
            f"{hero.id} used the cape magic to draw a safe glowing line and hold people back from the danger zone. "
            f"That meant nobody was standing under the chandelier when the trouble got bigger."
        ))
    if f["outcome"] == "saved":
        qa.append((
            f"How did {hero.id} solve the chandelier problem?",
            f"{hero.pronoun().capitalize()} used magic to {response.qa_text}. "
            f"Because that fix matched the kind of problem, the chandelier settled and the celebration could go on."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the crowd cheering in {venue.place}. "
            f"The chandelier was safe again, and {hero.id} remembered that careful thinking makes magic stronger."
        ))
    else:
        qa.append((
            f"Did {hero.id} save the chandelier?",
            f"No, not completely. {hero.pronoun().capitalize()} could not fully stop the damage, but {hero.pronoun()} did keep everyone safe by moving them back first."
        ))
        qa.append((
            "How did the story end?",
            f"The party moved to {venue.intimate_corner} and used smaller lights instead. "
            f"It was not the grand plan, but it proved that the hero cared more about people than objects."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"chandelier", "magic", "intimate"}
    tags |= set(f["mishap"].tags)
    tags |= set(f["response"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library_hall", "crystal", "swing", "moon_lasso", "comet",
                "Nova", "girl", "aunt", "Aunt Mira", 0),
    StoryParams("museum_atrium", "moonglass", "flare", "hush_charm", "violet",
                "Leo", "boy", "father", "Dad", 0),
    StoryParams("sky_theater", "vine_lantern", "tangle", "anchor_knots", "gold",
                "Skye", "girl", "mother", "Mom", 1),
    StoryParams("library_hall", "crystal", "swing", "anchor_knots", "violet",
                "Max", "boy", "aunt", "Captain Sol", 2),
]


def explain_rejection(chandelier: ChandelierCfg, mishap: Mishap) -> str:
    return (
        f"(No story: {chandelier.label} is not the kind that would reasonably face "
        f"the {mishap.label}. Pick a chandelier/mishap pair that truly creates a problem.)"
    )


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the safer fixes: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "saved" if is_saved(RESPONSES[params.response], CHANDELIERS[params.chandelier],
                               MISHAPS[params.mishap], params.delay) else "moved"


ASP_RULES = r"""
hazard(C, M) :- supports(C, M).
sensible(R)  :- response(R), sense(R, S), sense_min(Min), S >= Min.
works(R, M)  :- handles(R, M).

fragile_bonus(1) :- chosen_chandelier(C), fragile(C), chosen_mishap(swing).
fragile_bonus(0) :- not fragile_bonus(1).

severity(V) :- chosen_chandelier(_), chosen_mishap(M), base(M, B), delay(D), fragile_bonus(F), V = B + D + F.
saved :- chosen_response(R), chosen_mishap(M), works(R, M), power(R, P), severity(V), P >= V.
outcome(saved) :- saved.
outcome(moved) :- not saved.

valid(Venue, C, M) :- venue(Venue), chandelier(C), mishap(M), hazard(C, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id in VENUES:
        lines.append(asp.fact("venue", venue_id))
    for cid, chandelier in CHANDELIERS.items():
        lines.append(asp.fact("chandelier", cid))
        if chandelier.fragile:
            lines.append(asp.fact("fragile", cid))
        for m in sorted(chandelier.supports):
            lines.append(asp.fact("supports", cid, m))
    for mid, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mid))
        lines.append(asp.fact("base", mid, mishap.base))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for m in sorted(response.handles):
            lines.append(asp.fact("handles", rid, m))
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
        asp.fact("chosen_chandelier", params.chandelier),
        asp.fact("chosen_mishap", params.mishap),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
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
        print("MISMATCH in valid combos:")
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
        rng = random.Random(s)
        try:
            params = resolve_params(parser.parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty smoke-test story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a young superhero uses careful magic to solve a chandelier emergency."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--chandelier", choices=CHANDELIERS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--cape", choices=CAPES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--mentor-type", choices=["mother", "father", "aunt"])
    ap.add_argument("--mentor-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible chandelier/mishap combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.chandelier and args.mishap:
        chandelier = CHANDELIERS[args.chandelier]
        mishap = MISHAPS[args.mishap]
        if not hazard_at_risk(chandelier, mishap):
            raise StoryError(explain_rejection(chandelier, mishap))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.venue is None or c[0] == args.venue)
        and (args.chandelier is None or c[1] == args.chandelier)
        and (args.mishap is None or c[2] == args.mishap)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue, chandelier, mishap = rng.choice(sorted(combos))
    possible_responses = [
        r.id for r in sensible_responses()
        if response_works(r, MISHAPS[mishap])
    ]
    if args.response:
        response = args.response
    else:
        response = rng.choice(sorted(possible_responses))
    cape = args.cape or rng.choice(sorted(CAPES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    mentor_type = args.mentor_type or rng.choice(["mother", "father", "aunt"])
    if args.mentor_name:
        mentor_name = args.mentor_name
    else:
        mentor_name = {"mother": "Mom", "father": "Dad", "aunt": "Aunt Mira"}[mentor_type]
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])
    return StoryParams(
        venue=venue,
        chandelier=chandelier,
        mishap=mishap,
        response=response,
        cape=cape,
        hero_name=hero_name,
        hero_type=hero_type,
        mentor_type=mentor_type,
        mentor_name=mentor_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        VENUES[params.venue],
        CHANDELIERS[params.chandelier],
        MISHAPS[params.mishap],
        RESPONSES[params.response],
        CAPES[params.cape],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        mentor_type=params.mentor_type,
        mentor_name=params.mentor_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, chandelier, mishap) combos:\n")
        for venue, chandelier, mishap in combos:
            print(f"  {venue:14} {chandelier:12} {mishap}")
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
                f"### {p.hero_name}: {p.mishap} at {p.venue} "
                f"({p.chandelier}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
