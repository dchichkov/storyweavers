#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py
===================================================================

A standalone storyworld about a child on a space-station visit who wants to see
a wonderful place but must face one specific fear on the way there. The world
models physical state ("meters") and feelings ("memes"), uses a small
reasonableness gate so only fitting comforts are allowed, and renders stories
with child-facing inner monologue.

Run it
------
    python storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py
    python storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py --destination comet_dome
    python storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py --aid snack_pack
    python storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py --qa
    python storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py --trace
    python storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py --asp
    python storyworlds/worlds/gpt-5.4/visit_inner_monologue_space_adventure.py --verify
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
CALM_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    route: str
    wonder: str
    image: str
    need: str
    visit_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    action: str = ""
    style: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    feeling: str
    intensity: int
    inner_line: str
    body_sign: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    destination: str
    aid: str
    mood: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_type: str
    buddy_name: str
    buddy_kind: str
    favorite: str
    seed: Optional[int] = None


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


def _r_support_calms(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    route = world.entities.get("route")
    aid = world.entities.get("aid")
    if not child or not route or not aid:
        return out
    need = route.attrs.get("need")
    if aid.attrs.get("active") and need in aid.attrs.get("helps", set()):
        sig = ("calm", aid.id, need)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 2
            child.memes["courage"] += 1
            out.append("__calm__")
    return out


def _r_fear_blocks(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["fear"] >= THRESHOLD and child.memes["calm"] < CALM_MIN:
        sig = ("blocked", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["stopped"] += 1
            out.append("__blocked__")
    return out


CAUSAL_RULES = [
    Rule(name="support_calms", tag="emotion", apply=_r_support_calms),
    Rule(name="fear_blocks", tag="physical", apply=_r_fear_blocks),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


DESTINATIONS = {
    "comet_dome": Destination(
        id="comet_dome",
        label="comet dome",
        phrase="the comet dome",
        route="a glass skybridge over the stars",
        wonder="a silver comet tail sweeping past the windows",
        image="their faces shining in blue comet light",
        need="heights",
        visit_word="visit the comet dome",
        tags={"comet", "skybridge", "visit", "space_station"},
    ),
    "moon_garden": Destination(
        id="moon_garden",
        label="moon garden",
        phrase="the moon garden",
        route="a dim tunnel with glowing pipes in the walls",
        wonder="round leaves floating slowly in soft air fans",
        image="green leaves bobbing above the moon-soil beds",
        need="dark",
        visit_word="visit the moon garden",
        tags={"garden", "dark", "visit", "space_station"},
    ),
    "engine_balcony": Destination(
        id="engine_balcony",
        label="engine balcony",
        phrase="the engine balcony",
        route="a narrow humming lift that clanked as it rose",
        wonder="the giant engines pulsing like orange suns",
        image="warm engine light flickering across the rail",
        need="noise",
        visit_word="visit the engine balcony",
        tags={"engines", "noise", "visit", "space_station"},
    ),
}

AIDS = {
    "buddy_link": Aid(
        id="buddy_link",
        label="buddy link",
        phrase="a soft buddy-link strap",
        helps={"heights"},
        action="clipped the strap around both their wrists so nobody had to cross alone",
        style="together",
        qa_text="used a buddy-link strap so the child could cross with a helper",
        tags={"buddy_link", "help", "crossing"},
    ),
    "glow_map": Aid(
        id="glow_map",
        label="glow map",
        phrase="a tiny glow map",
        helps={"dark"},
        action="opened the glow map, and little arrows lit the path one by one",
        style="light",
        qa_text="used a glow map to make the dark tunnel feel clear and bright",
        tags={"glow_map", "help", "light"},
    ),
    "hush_phones": Aid(
        id="hush_phones",
        label="hush phones",
        phrase="a pair of hush phones",
        helps={"noise"},
        action="settled the hush phones over the child's ears until the big sounds turned soft",
        style="quiet",
        qa_text="used hush phones to make the loud lift quieter",
        tags={"hush_phones", "help", "quiet"},
    ),
    "snack_pack": Aid(
        id="snack_pack",
        label="snack pack",
        phrase="a little snack pack",
        helps=set(),
        action="offered a snack pack with three star crackers inside",
        style="snack",
        qa_text="offered a snack pack",
        tags={"snack", "help"},
    ),
}

MOODS = {
    "nervous": Mood(
        id="nervous",
        feeling="nervous",
        intensity=2,
        inner_line="What if my brave boots forget how to be brave?",
        body_sign="held still for one extra breath",
        tags={"feelings"},
    ),
    "shy": Mood(
        id="shy",
        feeling="shy",
        intensity=1,
        inner_line="I want to go, but maybe the stars are looking right at me.",
        body_sign="tucked one hand into a pocket",
        tags={"feelings"},
    ),
    "worried": Mood(
        id="worried",
        feeling="worried",
        intensity=2,
        inner_line="This feels bigger than I thought. What if I cannot do it?",
        body_sign="pressed lips together and peeked from the side",
        tags={"feelings"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Zoe", "Ava", "Nia", "Ivy", "Tess", "Maya"]
BOY_NAMES = ["Leo", "Max", "Owen", "Finn", "Kai", "Theo", "Eli", "Noah"]
GUIDE_NAMES = ["Captain Sol", "Guide Nova", "Pilot Rue", "Commander Pex"]
BUDDY_NAMES = ["Beep", "Pico", "Dot", "Spark"]
FAVORITES = ["star sticker", "moon patch", "tiny rocket pin", "silver map badge"]


def valid_combo(destination_id: str, aid_id: str) -> bool:
    return DESTINATIONS[destination_id].need in AIDS[aid_id].helps


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for did in DESTINATIONS:
        for aid_id in AIDS:
            if valid_combo(did, aid_id):
                combos.append((did, aid_id))
    return combos


def explain_rejection(destination: Destination, aid: Aid) -> str:
    return (
        f"(No story: {aid.phrase} does not solve the problem on the way to {destination.phrase}. "
        f"The route there asks for help with {destination.need}, so choose an aid that truly fits.)"
    )


def introduce(world: World, child: Entity, guide: Entity, buddy: Entity, destination: Destination) -> None:
    world.say(
        f"{child.id} had come to the ring-shaped space station for a special visit. "
        f"{guide.id}, the station guide, promised that today they could {destination.visit_word}."
    )
    world.say(
        f"Beside them rolled {buddy.id}, a round little helper bot with a blinking blue eye. "
        f"{child.id}'s favorite {child.attrs.get('favorite', 'badge')} shone on {child.pronoun('possessive')} shirt."
    )


def approach_route(world: World, child: Entity, destination: Destination, mood: Mood) -> None:
    route = world.get("route")
    child.memes["wonder"] += 1
    child.memes["fear"] += mood.intensity
    world.say(
        f"They followed the silver arrows until the path narrowed into {destination.route}. "
        f"Beyond it waited {destination.wonder}."
    )
    world.say(
        f"{child.id} {mood.body_sign}. Inside, {child.pronoun()} thought, "
        f'"{mood.inner_line}"'
    )
    route.meters["challenging"] += 1
    route.attrs["need"] = destination.need
    world.facts["inner_line"] = mood.inner_line


def pause_at_route(world: World, child: Entity, guide: Entity, destination: Destination) -> None:
    propagate(world, narrate=False)
    if child.meters["stopped"] >= THRESHOLD:
        world.say(
            f"{child.id} stopped at the very start of the path. "
            f"{child.pronoun('possessive').capitalize()} toes stayed planted, even though {child.pronoun()} wanted badly to keep going."
        )
    world.say(
        f'"It is all right to pause on a visit," {guide.id} said. '
        f'"Space adventures can feel big the first time."'
    )


def offer_aid(world: World, child: Entity, guide: Entity, aid: Aid) -> None:
    aid_ent = world.get("aid")
    aid_ent.attrs["active"] = True
    propagate(world, narrate=False)
    world.say(
        f"{guide.id} took out {aid.phrase} and {aid.action}."
    )
    if child.memes["calm"] >= CALM_MIN:
        world.say(
            f"{child.id} took a smaller breath, then a steadier one. Inside, {child.pronoun()} thought, "
            f'"Maybe I do not have to be fearless. Maybe I just have to take the next step."'
        )
        world.facts["second_inner_line"] = (
            "Maybe I do not have to be fearless. Maybe I just have to take the next step."
        )


def cross_route(world: World, child: Entity, guide: Entity, buddy: Entity, destination: Destination) -> None:
    if child.memes["calm"] < CALM_MIN:
        raise StoryError("(Story failure: the chosen aid did not calm the child enough to continue.)")
    child.meters["crossed"] += 1
    child.memes["courage"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"Step by step, {child.id} moved forward with {guide.id} and {buddy.id}. "
        f"The path no longer felt like a giant test. It felt like a road leading somewhere lovely."
    )
    world.say(
        f"When they reached {destination.phrase}, {destination.image} filled the whole room."
    )


def ending(world: World, child: Entity, guide: Entity, destination: Destination) -> None:
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f'{child.id} smiled so wide that {guide.id} laughed. "{destination.label.capitalize()} visitors need brave hearts," '
        f'{guide.pronoun()} said, "but brave hearts are allowed to tremble first."'
    )
    world.say(
        f"On the way back, {child.id} looked once more at the shining station hall and knew this visit had changed something. "
        f"The place was still huge, but now {child.pronoun()} felt big enough to meet it."
    )


def tell(
    destination: Destination,
    aid: Aid,
    mood: Mood,
    child_name: str,
    child_gender: str,
    guide_name: str,
    guide_type: str,
    buddy_name: str,
    buddy_kind: str,
    favorite: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"favorite": favorite},
        )
    )
    guide = world.add(
        Entity(
            id="guide",
            kind="character",
            type=guide_type,
            label=guide_name,
            role="guide",
        )
    )
    buddy = world.add(
        Entity(
            id="buddy",
            kind="thing",
            type=buddy_kind,
            label=buddy_name,
            role="buddy",
        )
    )
    route = world.add(
        Entity(
            id="route",
            kind="thing",
            type="route",
            label=destination.route,
            role="route",
            attrs={"need": destination.need},
        )
    )
    aid_ent = world.add(
        Entity(
            id="aid",
            kind="thing",
            type="aid",
            label=aid.label,
            role="aid",
            attrs={"helps": set(aid.helps), "active": False},
        )
    )

    child.id = child_name
    guide.id = guide_name
    buddy.id = buddy_name

    world.entities[child.id] = world.entities.pop("child")
    world.entities[guide.id] = world.entities.pop("guide")
    world.entities[buddy.id] = world.entities.pop("buddy")
    world.entities["route"] = route
    world.entities["aid"] = aid_ent

    introduce(world, child, guide, buddy, destination)
    world.para()
    approach_route(world, child, destination, mood)
    pause_at_route(world, child, guide, destination)
    world.para()
    offer_aid(world, child, guide, aid)
    cross_route(world, child, guide, buddy, destination)
    world.para()
    ending(world, child, guide, destination)

    world.facts.update(
        child=child,
        guide=guide,
        buddy=buddy,
        destination=destination,
        aid_cfg=aid,
        mood=mood,
        route=route,
        succeeded=child.meters["crossed"] >= THRESHOLD,
        used_aid=aid_ent.attrs.get("active", False),
    )
    return world


KNOWLEDGE = {
    "visit": [
        (
            "What does it mean to visit a place?",
            "To visit a place means you go there for a while to see it and spend time there. After the visit, you usually go back home or to where you started.",
        )
    ],
    "space_station": [
        (
            "What is a space station?",
            "A space station is a place built for people to live and work in space. It travels high above Earth and has rooms, windows, and machines inside.",
        )
    ],
    "comet": [
        (
            "What is a comet?",
            "A comet is a chunk of ice and dust that moves through space. When sunlight warms it, it can grow a bright tail.",
        )
    ],
    "garden": [
        (
            "How can a garden grow in space?",
            "Plants in space can grow in special beds with light, water, and careful air. People make the room just right so the plants can live.",
        )
    ],
    "engines": [
        (
            "What does an engine do on a spaceship or station?",
            "An engine helps a spacecraft move or adjust where it is going. Big engines can be loud because they use strong power.",
        )
    ],
    "skybridge": [
        (
            "What is a skybridge?",
            "A skybridge is a walkway that connects one place to another. If its walls are clear, it can feel high and open to someone crossing it.",
        )
    ],
    "dark": [
        (
            "Why can a dark place feel scary?",
            "A dark place can feel scary when you cannot see clearly what is around you. Light helps your brain understand the space better.",
        )
    ],
    "noise": [
        (
            "Why can loud noise feel hard to handle?",
            "Loud noise can make your body jump and your thoughts feel crowded. Softening the sound can help you feel calmer.",
        )
    ],
    "buddy_link": [
        (
            "How can holding on to someone help when you feel afraid?",
            "Being linked to a trusted helper can make your body feel safer. Then it is easier to take one step at a time.",
        )
    ],
    "glow_map": [
        (
            "How does a glowing map help in a dark place?",
            "A glowing map shows where to go, so the path stops feeling hidden. Clear steps can make a dark place feel easier.",
        )
    ],
    "hush_phones": [
        (
            "What do earmuffs or quiet headphones do?",
            "They soften loud sounds before they reach your ears. That can help a noisy place feel more gentle.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "visit",
    "space_station",
    "comet",
    "garden",
    "engines",
    "skybridge",
    "dark",
    "noise",
    "buddy_link",
    "glow_map",
    "hush_phones",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dest = f["destination"]
    mood = f["mood"]
    aid = f["aid_cfg"]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the word "visit" and uses inner monologue.',
        f"Tell a gentle story where {child.label} goes on a visit to {dest.phrase}, feels {mood.feeling} on the way, and is helped by {aid.phrase}.",
        f"Write a child-facing story set on a space station where a small fear is solved step by step, and the ending image proves the child has grown braver.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    buddy = f["buddy"]
    dest = f["destination"]
    aid = f["aid_cfg"]
    mood = f["mood"]
    route = f["route"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, who came to the space station for a visit, with {guide.label} as the guide and {buddy.label} nearby to help.",
        ),
        (
            f"Where did {child.label} want to go?",
            f"{child.label} wanted to {dest.visit_word}. The place felt special because {dest.wonder} was waiting there.",
        ),
        (
            f"Why did {child.label} stop on the way?",
            f"{child.label} stopped because the path was {route.label}, and that matched the fear that made {child.pronoun('object')} feel {mood.feeling}. The pause happened even though {child.pronoun()} still wanted to keep going.",
        ),
        (
            "What was the child's inner monologue?",
            f'{child.label} thought, "{f.get("inner_line", mood.inner_line)}" when the path first felt too big. That line shows the worry happening inside before anyone fixed it.',
        ),
        (
            f"How did {guide.label} help?",
            f"{guide.label} helped by using {aid.phrase}. {aid.qa_text.capitalize()}, which matched the exact problem on the route and let {child.label} calm down enough to move.",
        ),
        (
            f"How did the story end?",
            f"{child.label} reached {dest.phrase} at last and saw {dest.wonder}. The ending image of {dest.image} proves the visit changed from a scary moment into a proud one.",
        ),
    ]
    second = f.get("second_inner_line")
    if second:
        qa.append(
            (
                f"What changed inside {child.label} after the help?",
                f'After the help, {child.label} thought, "{second}" That shows the fear did not have to disappear completely before courage could begin.',
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"visit", "space_station"} | set(f["destination"].tags) | set(f["aid_cfg"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {}
        for k, v in e.attrs.items():
            if v:
                attrs[k] = sorted(v) if isinstance(v, set) else v
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        destination="comet_dome",
        aid="buddy_link",
        mood="nervous",
        child_name="Luna",
        child_gender="girl",
        guide_name="Captain Sol",
        guide_type="man",
        buddy_name="Beep",
        buddy_kind="robot",
        favorite="star sticker",
    ),
    StoryParams(
        destination="moon_garden",
        aid="glow_map",
        mood="worried",
        child_name="Max",
        child_gender="boy",
        guide_name="Guide Nova",
        guide_type="woman",
        buddy_name="Dot",
        buddy_kind="robot",
        favorite="moon patch",
    ),
    StoryParams(
        destination="engine_balcony",
        aid="hush_phones",
        mood="shy",
        child_name="Mira",
        child_gender="girl",
        guide_name="Pilot Rue",
        guide_type="woman",
        buddy_name="Spark",
        buddy_kind="robot",
        favorite="silver map badge",
    ),
]


ASP_RULES = r"""
fits(D, A) :- destination(D), aid(A), need(D, N), helps(A, N).
valid(D, A) :- fits(D, A).

calm_gain(2) :- chosen_destination(D), chosen_aid(A), fits(D, A).
calm_gain(0) :- chosen_destination(D), chosen_aid(A), not fits(D, A).

fear_total(F) :- chosen_mood(M), mood_fear(M, F).
crosses :- calm_gain(C), C >= 1.
blocked :- fear_total(F), F >= 1, calm_gain(C), C < 1.

outcome(success) :- crosses.
outcome(stopped) :- blocked.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did, d in DESTINATIONS.items():
        lines.append(asp.fact("destination", did))
        lines.append(asp.fact("need", did, d.need))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for need in sorted(aid.helps):
            lines.append(asp.fact("helps", aid_id, need))
    for mid, mood in MOODS.items():
        lines.append(asp.fact("mood", mid))
        lines.append(asp.fact("mood_fear", mid, mood.intensity))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_destination", params.destination),
            asp.fact("chosen_aid", params.aid),
            asp.fact("chosen_mood", params.mood),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def python_outcome(params: StoryParams) -> str:
    return "success" if valid_combo(params.destination, params.aid) else "stopped"


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
    for seed in range(30):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for p in cases:
        if asp_outcome(p) != python_outcome(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches python_outcome() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child's visit to a space station, a moment of fear, and a fitting helper."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father", "woman", "man"], help="guide type")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible destination/aid pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.destination and args.aid and not valid_combo(args.destination, args.aid):
        raise StoryError(explain_rejection(DESTINATIONS[args.destination], AIDS[args.aid]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.aid is None or combo[1] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, aid = rng.choice(sorted(combos))
    mood = args.mood or rng.choice(sorted(MOODS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide_type = args.guide or rng.choice(["woman", "man"])
    guide_name = rng.choice(GUIDE_NAMES)
    buddy_name = rng.choice(BUDDY_NAMES)
    favorite = rng.choice(FAVORITES)

    return StoryParams(
        destination=destination,
        aid=aid,
        mood=mood,
        child_name=child_name,
        child_gender=gender,
        guide_name=guide_name,
        guide_type=guide_type,
        buddy_name=buddy_name,
        buddy_kind="robot",
        favorite=favorite,
    )


def generate(params: StoryParams) -> StorySample:
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")
    if not valid_combo(params.destination, params.aid):
        raise StoryError(explain_rejection(DESTINATIONS[params.destination], AIDS[params.aid]))

    world = tell(
        destination=DESTINATIONS[params.destination],
        aid=AIDS[params.aid],
        mood=MOODS[params.mood],
        child_name=params.child_name,
        child_gender=params.child_gender,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
        buddy_name=params.buddy_name,
        buddy_kind=params.buddy_kind,
        favorite=params.favorite,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (destination, aid) combos:\n")
        for destination, aid in combos:
            print(f"  {destination:15} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.destination} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
