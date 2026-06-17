#!/usr/bin/env python3
"""Story world sketch: teamwork around a lost theater prop.

A child and a teammate realize a key prop is missing before rehearsal and must
adapt together with a suitable replacement. The script models the domain with
simple causal rules, reasonableness constraints, and a clingo twin.
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

# Make shared result containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"  # girl, boy, director, child, friend, prop
    label: str = ""
    role: str = ""
    owner: Optional[str] = None
    plural: bool = False
    traits: list[str] = field(default_factory=list)
    caretaker: Optional[str] = None
    covers: set[str] = field(default_factory=set)
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "director", "mom", "mother"}
        male = {"boy", "man", "dad", "father", "director"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Venue:
    id: str
    name: str
    indoor: bool
    supports: set[str] = field(default_factory=set)
    replacement_access: set[str] = field(default_factory=set)


@dataclass
class Play:
    id: str
    title: str
    hero_role: str
    required_tag: str
    setting: str
    hook: str
    stakes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostProp:
    id: str
    label: str
    tag: str
    line: str
    noun: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Replacement:
    id: str
    label: str
    tag: str
    line: str
    praise: str
    source: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, venue: Venue, play: Play, prop: LostProp) -> None:
        self.venue = venue
        self.play = play
        self.prop = prop
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.replacement_found = False
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def by_role(self, role: str) -> Entity:
        for ent in self.entities.values():
            if ent.kind == "character" and ent.role == role:
                return ent
        raise KeyError(role)

    @property
    def hero_ent(self) -> Entity:
        return self.by_role("hero")

    @property
    def director_ent(self) -> Entity:
        return self.by_role("director")

    @property
    def friend_ent(self) -> Entity:
        return self.by_role("teammate")

    def characters(self) -> list[Entity]:
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
        clone = World(self.venue, self.play, self.prop)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.replacement_found = self.replacement_found
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_panic(world: World) -> list[str]:
    hero = world.hero_ent
    if hero.memes["prop_missing"] < THRESHOLD or world.replacement_found:
        return []
    sig = ("panic", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1.0
    director = world.director_ent
    director.memes["concern"] += 1.0
    return [
        f"A wave of nerves moved through the room."
    ]


def _r_team_cooperation(world: World) -> list[str]:
    director = world.director_ent
    hero = world.hero_ent
    if director.memes["concern"] < THRESHOLD or hero.memes["worry"] < THRESHOLD:
        return []
    if world.replacement_found:
        return []
    sig = ("team", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in world.entities.values():
        if ent.role == "teammate":
            ent.memes["helping"] += 1.0
            break
    hero.memes["team_ready"] += 1.0
    return []


def _r_rehearsal_done(world: World) -> list[str]:
    hero = world.hero_ent
    if not world.replacement_found or hero.memes["team_ready"] < THRESHOLD:
        return []
    sig = ("resolved", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1.0
    hero.memes["worry"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("missing", "social", _r_missing_panic),
    Rule("team", "social", _r_team_cooperation),
    Rule("resolve", "social", _r_rehearsal_done),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def select_replacement(play: Play, lost: LostProp, venue: Venue) -> Optional[Replacement]:
    for repl in REPLACEMENTS:
        if repl.tag == lost.tag and repl.id in venue.replacement_access:
            return repl
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id, venue in VENUES.items():
        for play_id, play in PLAYS.items():
            for lost_id, lost in LOST_PROPS.items():
                if play.required_tag != lost.tag:
                    continue
                if not select_replacement(play, lost, venue):
                    continue
                combos.append((venue_id, play_id, lost_id))
    return combos


def explain_invalid(play: Play, lost: LostProp) -> str:
    if play.required_tag != lost.tag:
        return (
            f"(No story: {play.title} needs a prop for {play.required_tag}, "
            f"but {lost.label} is a {lost.tag}-type prop.)"
        )
    return "(No story: this lost prop cannot be sensibly replaced here.)"


def explain_lost(play: Play, lost: LostProp, venue: Venue) -> str:
    return (
        f"(No story: in {venue.name}, no safe replacement for '{lost.label}' "
        f"matches the role it plays in {play.title}."
        f"Try a venue that stores a {play.required_tag}-style prop.)"
    )


# ---------------------------------------------------------------------------
# Prediction helpers
# ---------------------------------------------------------------------------
def predict_rehearsal(world: World, hero: Entity, play: Play, lost: LostProp,
                      replacement: Optional[Replacement]) -> dict:
    sim = world.copy()
    if replacement is None:
        sim.memes_no_fix = True
        return {"at_risk": True}
    sim.replacement_found = True
    sim.get("hero").memes["prop_missing"] += 1.0
    propagate(sim)
    return {
        "at_risk": False,
        "resolved": sim.hero_ent.memes.get("confidence", 0.0) >= THRESHOLD,
    }


def introduce(world: World, hero: Entity) -> None:
    hero_desc = " and ".join(hero.traits) if hero.traits else ""
    if hero_desc:
        world.say(f"Once upon a time, there was a {hero_desc} {hero.type} named {hero.id}.")
    else:
        world.say(f"There was a performer named {hero.id}.")


def setup_cast(world: World, hero: Entity, director: Entity, friend: Entity) -> None:
    world.say(
        f"The school had prepared a big production of {world.play.title} in "
        f"the {world.venue.name}."
    )
    world.say(
        f"{hero.id} was playing {hero.pronoun('possessive')} role as "
        f"{world.play.hero_role}."
    )


def setup_stage(world: World, hero: Entity, lost: LostProp) -> None:
    world.say(
        f"Before rehearsal, {hero.pronoun('possessive')} team made the {lost.label} "
        f"the star prop for the scene."
    )


def discover_missing(world: World, hero: Entity, lost_ent: Entity) -> None:
    hero.memes["prop_missing"] += 1.0
    world.say(f"Then {hero.id} opened the prop box and found their {lost_ent.label} was gone.")
    propagate(world)


def warn_about_stakes(world: World, hero: Entity, director: Entity, lost: LostProp) -> None:
    pred = predict_rehearsal(world, hero, world.play, lost, None)
    if not pred["at_risk"]:
        return
    world.say(
        f"{director.id} said, \"If that prop stays missing, the audience may not "
        f"understand our story.\"")
    world.facts["predicted_at_risk"] = True


def search_and_find_replacement(world: World, hero: Entity, friend: Entity,
                              replacement: Optional[Replacement]) -> bool:
    if replacement is None:
        return False
    world.facts["replacement_used"] = replacement
    repl_ent = world.add(Entity(
        id=replacement.id,
        kind="thing",
        type="prop",
        label=replacement.label,
        owner=hero.id,
        plural=replacement.id.endswith("s"),
    ))
    friend.memes["helping"] += 1.0
    world.say(
        f"{friend.id} called out, \"I found a {replacement.label} in {replacement.source}.\" "
        f"{hero.id} and {friend.id} made it work as the stand-in.")
    world.replacement_found = True
    propagate(world)
    world.say(replacement.line)
    world.say(f"{hero.id} felt steadier and replied, \"Great teamwork!\"")
    world.say(replacement.praise)
    return True


def perform_show(world: World, hero: Entity, friend: Entity, director: Entity,
                replacement: Optional[Replacement]) -> None:
    if not world.replacement_found:
        world.say(
            f"The rehearsal had to pause for the first scene because {hero.id} "
            f"could not present the required moment."
        )
        return
    hero.memes["confidence"] += 1.0
    world.say(
        f"Later that evening, {hero.id}, {friend.id}, and the rest of the class "
        f"performed the scene together."
    )
    world.say(
        f"The missing-prop panic passed, and everyone clapped when they finished "
        f"with applause for the teamwork.")
    world.facts.update(result="resolved", outcome="resolved")


def tell(venue: Venue, play: Play, lost: LostProp,
         hero_name: str, hero_gender: str,
         friend_name: str, director_name: str) -> World:
    world = World(venue, play, lost)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["brave", "kind"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type="friend",
        role="teammate",
    ))
    director = world.add(Entity(
        id=director_name,
        kind="character",
        type="director",
        role="director",
    ))
    lost_ent = world.add(Entity(
        id="lost_prop",
        kind="thing",
        type="prop",
        label=lost.label,
        owner=hero.id,
        plural=lost.id.endswith("s"),
    ))

    introduce(world, hero)
    setup_cast(world, hero, director, friend)
    setup_stage(world, hero, lost_ent)

    world.para()
    discover_missing(world, hero, lost_ent)
    warn_about_stakes(world, hero, director, lost)

    world.para()
    replacement = select_replacement(play, lost, venue)
    found = search_and_find_replacement(world, hero, friend, replacement)
    if not found:
        world.facts["outcome"] = "unresolved"
        world.facts["replacement_used"] = None
        world.say(f"They could not find a safe substitute and the rehearsal was delayed.")
    else:
        world.facts["outcome"] = "resolved"
    perform_show(world, hero, friend, director, replacement)

    world.facts.update(
        venue=venue,
        play=play,
        lost=lost,
        hero=hero,
        friend=friend,
        director=director,
        replacement=world.facts.get("replacement_used"),
        resolved=world.facts.get("outcome") == "resolved",
    )
    return world


# ---------------------------------------------------------------------------
# Domain tables
# ---------------------------------------------------------------------------
VENUES = {
    "school_auditorium": Venue(
        "school_auditorium", "school auditorium", True,
        replacement_access={"foam_crown", "paper_wand", "flashlight"},
        supports={"royal", "magical", "cave"},
    ),
    "community_theater": Venue(
        "community_theater", "community theater", True,
        replacement_access={"foam_crown", "fabric_map", "flashlight", "signal_bell"},
        supports={"royal", "adventure", "rescue"},
    ),
    "church_basement": Venue(
        "church_basement", "church basement stage", False,
        replacement_access={"paper_wand", "cloth_cape", "fabric_map"},
        supports={"magical", "adventure"},
    ),
}

PLAYS = {
    "royal_journey": Play(
        "royal_journey",
        "The Royal Journey",
        "the prince",
        "headwear",
        "a grand hall of a kingdom",
        "The cast needs a symbol of command in this act.",
        "The crown keeps the scene understandable to the audience.",
        tags={"royal", "leadership", "audience"},
    ),
    "cave_explorers": Play(
        "cave_explorers",
        "The Cave Explorers",
        "the explorer",
        "navigation",
        "a dark cave of wonders",
        "The map keeps the crew from getting lost.",
        "A route is needed so the team can move safely and stay together.",
        tags={"adventure", "teamwork"},
    ),
    "magic_show": Play(
        "magic_show",
        "The Magic Show",
        "the magician",
        "light",
        "a sparkling stage of tricks",
        "The light prop keeps the audience focused.",
        "The cue has to be clear for timing and safety.",
        tags={"magical", "performance"},
    ),
}

LOST_PROPS = {
    "crown": LostProp("crown", "sparkly crown", "headwear", "the crown looked too important to risk being wrong"),
    "treasure_map": LostProp("treasure_map", "folded map", "navigation", "the map needed to stay readable"),
    "magic_torch": LostProp("magic_torch", "magic lantern", "light", "the lantern was the cue for the reveal"),
}

REPLACEMENTS = [
    Replacement(
        id="foam_crown",
        label="foam crown",
        tag="headwear",
        line="They tied the foam crown over the hero's old ribbon and gave it a proud glow.",
        praise="The team laughed, and the scene still looked magical enough for the crowd.",
        source="a basket near the stage door",
        tags={"royal"},
    ),
    Replacement(
        id="paper_wand",
        label="paper wand",
        tag="light",
        line="They rewound a paper wand with foil to keep the cue visible.",
        praise="Their focus stayed high as they practiced the cue.",
        source="the props table",
        tags={"magical"},
    ),
    Replacement(
        id="fabric_map",
        label="fabric map",
        tag="navigation",
        line="They painted a bold fabric map together and clipped it to the wall.",
        praise="The audience could read every route and follow the scene clearly.",
        source="the costume trunk",
        tags={"adventure"},
    ),
    Replacement(
        id="flashlight",
        label="small flashlight",
        tag="light",
        line="They turned the small flashlight into a steady cue for the reveal.",
        praise="The timing stayed smooth and everyone moved in step.",
        source="the first-aid corner",
        tags={"safety"},
    ),
    Replacement(
        id="signal_bell",
        label="kitchen bell",
        tag="navigation",
        line="They used a kitchen bell rhythm to mark each route change.",
        praise="A shared beat anchored the whole performance.",
        source="the backstage shelf",
        tags={"teamwork"},
    ),
]

NAMES_GIRL = ["Lena", "Mia", "Sofia", "Ella", "Nora"]
NAMES_BOY = ["Noah", "Leo", "Sam", "Kai", "Tom"]
DIRECTORS = ["Ms. Carter", "Mr. Diaz", "Ms. Reed", "Mr. Cole"]
FRIENDS = ["Maya", "Jordan", "Noel", "Aria", "Theo", "Liam"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a child-friendly story about teamwork in a community play involving a "{world.play.required_tag}" prop.',
        f"Write a story where a child actor must solve a missing-prop problem at a {world.venue.name}.",
        f"Tell a three-beat theatre rehearsal story that includes a lost {world.facts['lost'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    director = world.facts["director"]
    play = world.facts["play"]
    lost = world.facts["lost"]
    replacement = world.facts.get("replacement")
    replaced = world.facts.get("resolved", False)
    pron = hero.pronoun("possessive")

    qa: list[tuple[str, str]] = [
        (f"Who is the main character of this story?",
         f"The story is about {hero.id}, a {hero.type} who played {play.hero_role} in {play.title}."),
        (f"What was the important prop in this story?",
         f"The key prop was {pron} {lost.label}, which mattered for the scene's plot."),
    ]

    if world.facts.get("predicted_at_risk"):
        qa.append((
            f"Why was {director.id} worried at first?",
            f"The director saw that without a {lost.label}, the audience would miss why "
            f"the scene mattered, so the team needed a real replacement before rehearsal."
        ))

    if replaced and replacement:
        qa.append((
            f"How did {hero.id} and {friend.id} solve the problem?",
            f"They searched together through the venue and used a {replacement.label} as a stand-in, "
            f"then rehearsed the line so the scene stayed coherent."
        ))
        qa.append((
            "What made this a teamwork moment?",
            f"{hero.id} and {friend.id} took different tasks: one searched and one prepared the replacement, "
            f"then both practiced the cue with the full cast."
        ))
    else:
        qa.append((
            f"What happened at the end of rehearsal?",
            f"They could not find a replacement, so rehearsal was delayed and the scene had to be reset."
        ))

    return qa


KNOWLEDGE = {
    "royal": [
        ("What makes a crown important in a play?",
         "A crown is a visual symbol of leadership, so it helps the audience identify who leads a story moment."),
    ],
    "adventure": [
        ("Why do teams use a map in a rescue or journey scene?",
         "A map helps everyone agree on the route and prevents confusion when the action moves quickly."),
    ],
    "headwear": [
        ("Why does a prop belong to a specific role?",
         "Some props carry meaning for a role, so they cue identity and make the scene easier to follow."),
    ],
    "navigation": [
        ("Why is coordination important during a scene with stage directions?",
         "Coordination keeps entrances, exits, and actions in the right order so the story stays clear."),
    ],
    "light": [
        ("What is a rehearsal cue for?",
         "A cue tells actors when to speak, move, or pause, so timing and focus stay synchronized."),
    ],
    "teamwork": [
        ("What is theater teamwork?",
         "It is actors, directors, and classmates sharing responsibility to solve problems and keep the show safe and clear."),
    ],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.play.tags)
    tags.add(world.play.required_tag)
    tags.add("teamwork")
    out: list[tuple[str, str]] = []
    for tag in ("royal", "adventure", "headwear", "navigation", "light", "teamwork"):
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story-grounded Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.role:
            bits.append(f"role={ent.role}")
        out.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    out.append(f"  replacement_found={world.replacement_found}")
    return "\n".join(out)


@dataclass
class StoryParams:
    venue: str
    play: str
    lost: str
    hero: str
    hero_gender: str
    friend: str
    director: str
    seed: Optional[int] = None


# Curated set for --all
CURATED = [
    StoryParams("school_auditorium", "royal_journey", "crown", "Lena", "girl", "Maya", "Ms. Carter"),
    StoryParams("community_theater", "cave_explorers", "treasure_map", "Noah", "boy", "Theo", "Mr. Diaz"),
    StoryParams("church_basement", "magic_show", "magic_torch", "Sofia", "girl", "Liam", "Ms. Reed"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A play needs a replacement when its required prop tag can be met.
valid(Venue, Play, Lost) :- play_tag(Play, Tag), lost_tag(Lost, Tag), replacement(Venue, Play, Lost).
replacement(Venue, Play, Lost) :- venue(Venue), play(Play), lost(Lost), has_replacement(Venue, Lost).
has_replacement(Venue, Lost) :- replace_for(Repl, Tag), lost_tag(Lost, Tag), located(Venue, Repl).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for vid, venue in VENUES.items():
        lines.append(asp.fact("venue", vid))
        for repl in sorted(venue.replacement_access):
            lines.append(asp.fact("located", vid, repl))

    for pid, play in PLAYS.items():
        lines.append(asp.fact("play", pid))
        lines.append(asp.fact("play_tag", pid, play.required_tag))

    for lid, lost in LOST_PROPS.items():
        lines.append(asp.fact("lost", lid))
        lines.append(asp.fact("lost_tag", lid, lost.tag))

    for repl in REPLACEMENTS:
        lines.append(asp.fact("replace_for", repl.id, repl.tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py_set = set(valid_combos())
    as_set = set(asp_valid_combos())
    if py_set == as_set:
        print(f"OK: ASP and Python gate agree on {len(py_set)} combos.")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if as_set - py_set:
        print("  only in ASP:", sorted(as_set - py_set))
    if py_set - as_set:
        print("  only in Python:", sorted(py_set - as_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Story world sketch: theater rehearsal, lost prop, and teamwork "
            "that recovers the scene safely."
        )
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--play", choices=PLAYS)
    ap.add_argument("--lost", dest="lost", choices=LOST_PROPS)
    ap.add_argument("--hero", help="hero name")
    ap.add_argument("--gender", choices=["girl", "boy"], dest="hero_gender")
    ap.add_argument("--friend", help="teammate name")
    ap.add_argument("--director", help="director name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render curated stories")
    ap.add_argument("--trace", action="store_true", help="dump world model state")
    ap.add_argument("--qa", action="store_true", help="emit three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON payload")
    ap.add_argument("--asp", action="store_true", help="list valid (venue, play, lost) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP twin matches Python gate")
    ap.add_argument("--show-asp", action="store_true", help="print inline ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.play and args.lost:
        play = PLAYS[args.play]
        lost = LOST_PROPS[args.lost]
        if play.required_tag != lost.tag:
            raise StoryError(explain_invalid(play, lost))
    if args.venue and args.play and args.lost:
        venue = VENUES[args.venue]
        play = PLAYS[args.play]
        lost = LOST_PROPS[args.lost]
        if not select_replacement(play, lost, venue):
            raise StoryError(explain_lost(play, lost, venue))

    candidates = [c for c in valid_combos()
                  if (args.venue is None or c[0] == args.venue)
                  and (args.play is None or c[1] == args.play)
                  and (args.lost is None or c[2] == args.lost)]
    if not candidates:
        raise StoryError("(No valid combination matches the requested constraints.)")

    venue_id, play_id, lost_id = sorted(candidates)[0] if len(candidates) == 1 else rng.choice(sorted(candidates))
    venue = VENUES[venue_id]
    play = PLAYS[play_id]

    # Pick a random replacement-compatible lost prop when explicit flags are not given.
    if args.play and args.lost:
        lost = LOST_PROPS[lost_id]
    else:
        lost = LOST_PROPS[lost_id]

    if lost.tag != play.required_tag:
        raise StoryError(explain_invalid(play, lost))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero:
        hero = args.hero
    elif hero_gender == "girl":
        hero = rng.choice(NAMES_GIRL)
    else:
        hero = rng.choice(NAMES_BOY)

    friend = args.friend or rng.choice(FRIENDS)
    director = args.director or rng.choice(DIRECTORS)

    return StoryParams(venue_id, play_id, lost_id, hero, hero_gender, friend, director)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        VENUES[params.venue],
        PLAYS[params.play],
        LOST_PROPS[params.lost],
        params.hero,
        params.hero_gender,
        params.friend,
        params.director,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n" + dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (venue, play, lost) combinations:")
        for venue_id, play_id, lost_id in triples:
            print(f"  {venue_id:18} {play_id:16} {lost_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} rehearses {p.play} at {p.venue} (lost {p.lost})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
