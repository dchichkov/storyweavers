#!/usr/bin/env python3
"""
A small Animal-Story-style world about a rhyme session that goes wrong when
something rotten starts a conflict, then turns into a gentler twist.

The child-facing premise:
- A group of animals gather for a rhyme session.
- One animal brings a rotten treat, which causes a smell and a squabble.
- A helper notices the problem, switches the plan, and the group ends happily
  with a new rhyme and a fresh snack.

This script follows the Storyweavers world contract:
- standalone stdlib script
- shared results containers imported eagerly
- ASP helpers imported lazily inside ASP helpers
- generate / emit / main interface
- reasoning gate plus inline ASP_RULES twin
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("smell", "mess", "noise", "freshness"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "conflict", "shame", "curiosity", "kindness"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.species


@dataclass
class Place:
    name: str = "the meadow"
    indoor: bool = False


@dataclass
class Event:
    id: str
    title: str
    rhyme_line: str
    twist_line: str
    conflict_line: str
    fix_line: str
    snack: str
    mess_source: str
    atmosphere: str


@dataclass(frozen=True)
class Incident:
    id: str
    premise: str
    rotten_item: str
    warning: str
    conflict: str
    mistaken_action: str
    clue: str
    helpful_action: str
    twist: str
    resolution: str
    ending: str
    replacement: str
    lesson: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": Place("the meadow", indoor=False),
    "porch": Place("the porch", indoor=False),
    "den": Place("the den", indoor=True),
}

EVENTS = {
    "rotten_rhyme": Event(
        id="rotten_rhyme",
        title="rotten rhyme session",
        rhyme_line="They wanted to rhyme in a bright little ring, and every voice was ready to sing.",
        twist_line="Then one basket tipped, and a rotten smell rose up like a cloud.",
        conflict_line="The bad smell made the animals wrinkle their noses, and they began to argue over who should leave.",
        fix_line="A small helper swapped in fresh berries, opened the windows, and turned the quarrel into a new rhyme game.",
        snack="fresh berries",
        mess_source="rot",
        atmosphere="warm and bouncy",
    )
}

ANIMALS = {
    "bunny": {"species": "bunny", "label": "bunny", "trait": "bouncy"},
    "fox": {"species": "fox", "label": "fox", "trait": "clever"},
    "mouse": {"species": "mouse", "label": "mouse", "trait": "tiny"},
    "bear": {"species": "bear", "label": "bear", "trait": "steady"},
}

NAMES = ["Pip", "Milo", "Tia", "Nina", "Bram", "Wren", "Sage", "Clover"]

INCIDENTS = [
    Incident(
        "echoing_apple", "planned a call-and-answer rhyme for the shy field mice",
        "a rotten apple hidden beneath the rhythm cards",
        "a sour smell drifted up whenever the chorus stamped",
        "each animal blamed the neighbor whose paw was closest to the cards",
        "shook every card into the air, making the clues harder to follow",
        "one card had a damp, apple-shaped stain",
        "sorted the cards by smell and followed the stain to its source",
        "the loudest accuser had packed the apple days ago and simply forgotten it",
        "apologized, composted the apple, and rebuilt the chorus one careful line at a time",
        "Field mice tapped clean cards while an apple tree rustled above the final rhyme.",
        "crisp apple slices", "A mistake is easier to mend when friends inspect clues instead of blaming.",
    ),
    Incident(
        "drum_gourd", "gathered seedpod drums for a rain-rhyme rehearsal",
        "a rotten gourd wedged inside the biggest drum",
        "every boom puffed a musty smell across the circle",
        "the drummers argued that someone was ruining the beat on purpose",
        "beat the drum harder, splitting its old vine handle",
        "tiny fruit flies slipped through a crack in the drumhead",
        "untied the drumhead, found the gourd, and repaired the handle together",
        "the supposed saboteur had actually heard the gourd rolling and tried to warn everyone",
        "listened to the warning, carried the gourd to the compost heap, and restarted softly",
        "Three gentle drumbeats rolled through the clean air as raindrops winked on the leaves.",
        "sunflower-seed cakes", "Listening closely can turn a quarrel into useful teamwork.",
    ),
    Incident(
        "buried_pear", "invented treasure-map rhymes along a row of painted stones",
        "a rotten pear buried under the stone marked X",
        "the final clue smelled far less sweet than its verse promised",
        "the treasure hunters accused one another of replacing the prize",
        "dug three wild holes before checking the map symbols",
        "a trail of pear seeds led directly to the marked stone",
        "matched every seed to the map and lifted the correct stone together",
        "the rotten pear was an old practice treasure, while the real prize waited nearby",
        "filled the stray holes, composted the pear, and shared the unopened prize",
        "A silver map weight held down their new rhyme while the filled earth lay smooth again.",
        "oat-and-berry biscuits", "Careful evidence beats hurried guesses.",
    ),
    Incident(
        "moldy_reed", "practiced a river rhyme with reed whistles",
        "a rotten reed bundle left in a wet basket",
        "one whistle wheezed and released a swampy odor",
        "the musicians quarreled over who had played the rude-sounding note",
        "blew into every wet reed at once and made the smell worse",
        "a dark waterline showed which bundle had never dried",
        "set the spoiled reeds aside and laid the sound reeds in the sun",
        "the ugly note came from trapped water, not from anyone playing a trick",
        "said sorry, cleaned the basket, and performed the rhyme with safe dry whistles",
        "Dry reeds chimed over the stream, and their reflections trembled like golden pencils.",
        "cucumber boats", "When something goes wrong, test the object before judging the player.",
    ),
    Incident(
        "turnip_crown", "prepared a royal rhyme in which each animal would wear a vegetable crown",
        "a rotten turnip sewn into the first crown",
        "the crown sagged and left a brown drip on the rhyme rug",
        "two performers argued about who had spoiled the royal costume",
        "hid the crown behind a cushion, where the smell spread",
        "a loose gold thread matched the thread on the costume basket",
        "traced the thread, found the crown, and fetched cleaning cloths",
        "the turnip had been a stage prop from last season, not today's snack",
        "cleaned the rug, remade the crown from paper leaves, and let both performers lead",
        "Two paper crowns bobbed beneath the moon while the spotless rug framed their bow.",
        "carrot ribbons", "Owning an awkward problem kindly keeps it from growing.",
    ),
    Incident(
        "cheese_bell", "built a bell-rhyme game from cups hanging on a low branch",
        "a rotten cheese rind tucked inside the lowest cup",
        "the cup rang with a sticky clunk and smelled sharp",
        "the ringers disputed whose turn had spoiled the melody",
        "pulled all the cords at once, tangling them around the branch",
        "greasy crumbs clung only to the lowest cord",
        "loosened the cords one by one and inspected the matching cup",
        "a magpie had cached the rind there before the rhyme session began",
        "removed the rind, washed the cup, and invited the magpie to ring a clean bell",
        "Five bright notes floated from the branch while the washed cup spun in the breeze.",
        "melon cubes", "A surprising cause can appear once everyone stops tugging and looks.",
    ),
    Incident(
        "pumpkin_boat", "launched leaf boats carrying rhyming couplets across a shallow pond",
        "a rotten pumpkin used as the starting buoy",
        "the buoy split and sent orange pulp drifting toward the boats",
        "the racers blamed one another for bumping the buoy",
        "splashed after the boats and pushed the pulp into a wider patch",
        "the pumpkin's underside was already soft and cracked",
        "used broad leaves to skim the pulp and guided every boat back with a stick",
        "the slowest boat carried a verse explaining how to clean the pond",
        "followed that verse, composted the pulp, and held a fair second race",
        "Leaf boats crossed clear water as frogs answered the winners with one deep croak.",
        "pea-pod sandwiches", "A fair restart includes repairing the shared place first.",
    ),
    Incident(
        "plum_puppet", "staged a rhyming puppet show behind a fern curtain",
        "a rotten plum lodged inside the fox puppet",
        "the puppet's mouth opened and a purple, sour drop fell out",
        "the actors accused the puppeteer of playing a mean joke",
        "snatched at the puppet and tore one sleeve seam",
        "purple juice marked the inside of the puppet but not the puppeteer's paws",
        "opened the lining, removed the plum, and stitched the seam",
        "a squirrel had hidden the plum in the puppet during an earlier picnic",
        "accepted the explanation and rewrote the villain as a forgetful fruit collector",
        "The mended puppet bowed under fern-frond curtains with one neat patch shining on its sleeve.",
        "blueberry muffins", "Checking what happened protects a friend from an unfair accusation.",
    ),
    Incident(
        "onion_parcel", "passed sealed parcels while rhyming about what might be inside",
        "a rotten onion wrapped in the brightest parcel",
        "the paper grew damp and the guesses turned into groans",
        "the guessers fought over who must open the smelly parcel",
        "rolled it downhill, where it nearly struck a nest",
        "a faded label said 'compost lesson' beneath the bow",
        "stopped the parcel, moved it away from the nest, and read the label aloud",
        "the parcel was meant for tomorrow's garden lesson, not today's guessing game",
        "delivered it safely to the compost bin and made new parcels from clean pinecones",
        "Bright parcels circled the nest at a safe distance as the last pinecone clicked into place.",
        "pear pinwheels", "Reading instructions before acting can keep others safe.",
    ),
    Incident(
        "banana_banner", "painted a long banner whose pictures completed each rhyme",
        "a rotten banana rolled inside the banner tube",
        "a brown smear appeared each time the banner was unrolled",
        "the painters accused one another of using muddy brushes",
        "scrubbed the painted side and blurred two carefully drawn stars",
        "the smear began at the hollow tube rather than at any paint pot",
        "opened the tube, removed the banana, and blotted the paper from behind",
        "the blurred stars became perfect fuzzy comets for the closing verse",
        "repainted the rhyme together and hung the clean banner between two trees",
        "Two fuzzy comets glowed on the banner while the empty tube rested beside the compost pail.",
        "strawberry spirals", "Cooperation can transform a mishap without hiding it.",
    ),
    Incident(
        "tomato_tracks", "followed paw-print cards through a rhyming woodland trail",
        "a rotten tomato squashed beneath the first clue box",
        "red tracks crossed the path and smelled much worse than paint",
        "the trackers argued about which animal had made the messy prints",
        "followed the red marks into a bramble without checking their direction",
        "each print grew fainter away from the clue box, proving the trail began there",
        "walked backward along the marks and lifted the box together",
        "a hedgehog had rolled the tomato under the box while seeking shade",
        "freed the hedgehog, cleared the path, and replaced the stained cards",
        "Clean paw-print cards curved home while the rescued hedgehog slept beneath a dry leaf.",
        "corn cakes", "The direction of a clue matters as much as its color.",
    ),
    Incident(
        "peach_lantern", "arranged lanterns so their shadows would act out a moon rhyme",
        "a rotten peach resting in the base of one lantern",
        "the warm lantern made the peach smell stronger and its shadow wobble",
        "the shadow makers argued that someone kept moving the lantern",
        "held the lantern still with a heavy stone, trapping more heat around the fruit",
        "a trickle of peach juice, not a paw print, curved under the base",
        "put out the light, waited for it to cool, and opened the base safely",
        "the wobbling shadow had warned them about the hidden peach before it leaked farther",
        "cleaned and dried the lantern, then thanked the watcher who noticed the wobble",
        "A steady rabbit-shaped shadow danced on the wall beside a bowl of cool fruit slices.",
        "cool peach slices", "A strange detail may be a useful warning rather than a nuisance.",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A rhyme session is reasonable when there is a place, a group, and a way to
% turn the rotten conflict into a fresh ending.
reason(P) :- place(P).

rotten_event(rotten_rhyme).
has_conflict(E) :- event(E), conflict(E).
has_fix(E) :- event(E), fix(E), fresh_snack(E).

valid_story(P, E) :- reason(P), event(E), has_conflict(E), has_fix(E).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("conflict", eid))
        lines.append(asp.fact("fix", eid))
        lines.append(asp.fact("fresh_snack", eid))
        lines.append(asp.fact("mess_source", eid, ev.mess_source))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    event: str
    hero: str
    hero_kind: str
    helper: str
    helper_kind: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The chosen place is not in this small animal world.")
    if params.event not in EVENTS:
        raise StoryError("The chosen event is not in this small animal world.")
    if params.hero_kind not in ANIMALS:
        raise StoryError("Unknown hero animal type.")
    if params.helper_kind not in ANIMALS:
        raise StoryError("Unknown helper animal type.")
    if params.hero_kind == params.helper_kind and params.hero == params.helper:
        raise StoryError("Hero and helper should not be the exact same character.")


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = PLACES[params.place]
    ev = EVENTS[params.event]
    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = "|".join((params.place, params.event, params.hero, params.hero_kind,
                                params.helper, params.helper_kind))
    rng = random.Random(stable_seed)
    incident = rng.choice(INCIDENTS)
    world = World(place)

    hero_info = ANIMALS[params.hero_kind]
    helper_info = ANIMALS[params.helper_kind]

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        species=hero_info["species"],
        label=params.hero,
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        species=helper_info["species"],
        label=params.helper,
    ))
    snack = world.add(Entity(
        id="snack",
        kind="thing",
        species="food",
        label=incident.replacement,
        phrase=f"a plate of {incident.replacement}",
        owner=hero.id,
    ))
    rotten_snack = world.add(Entity(
        id="rotten_snack",
        kind="thing",
        species="spoiled food",
        label=incident.rotten_item,
        phrase=incident.rotten_item,
        owner=hero.id,
    ))

    # Setup
    openings = [
        f"At {place.name}, {hero.id} the {hero_info['label']} called the animals together for a rhyme session.",
        f"The day's animal story began at {place.name}, where {hero.id} the {hero_info['label']} rang a tiny bell for rhyme-session time.",
        f"Morning light reached {place.name} just as {hero.id} the {hero_info['label']} welcomed everyone to a rhyme session.",
        f"A circle of expectant animals formed at {place.name} around {hero.id} the {hero_info['label']}.",
        f"{hero.id} the {hero_info['label']} had promised the animals at {place.name} a rhyme session with a surprise ending.",
        f"At {place.name}, every animal hushed when {hero.id} the {hero_info['label']} lifted the first rhyme card.",
        f"{place.name.capitalize()} was busy with paws and tails because {hero.id} the {hero_info['label']} was hosting a rhyme session.",
        f"One clear afternoon, {hero.id} the {hero_info['label']} prepared {place.name} for an animal rhyme session.",
    ]
    world.say(rng.choice(openings))
    world.say(f"{helper.id} the {helper_info['label']} came to help with the animal rhyme session, and together they {incident.premise}.")
    setup_details = [
        "They tested the first verse twice, leaving room for every small voice.",
        "The opening words bounced neatly around the circle.",
        "They agreed that anyone could pause the game if something seemed wrong.",
        "Soon paws tapped the beat and whiskers twitched in time.",
        "A basket of clean props waited beside the rhyme cards.",
        "Even the quietest listeners leaned closer for the first refrain.",
    ]
    world.say(rng.choice(setup_details))
    world.para()

    # Turn
    turn_leads = ["Then the cheerful rhythm broke.", "On the next beat, the plan went crooked.",
                  "Halfway through a verse, every nose lifted.", "That was when the rotten surprise appeared.",
                  "Just before the chorus, the trouble announced itself.", "The next sound did not belong in the song."]
    world.say(f"{rng.choice(turn_leads)} They discovered {incident.rotten_item}; {incident.warning}.")
    hero.meters["smell"] += 1
    hero.memes["curiosity"] += 1
    rotten_snack.meters["smell"] += 3
    rotten_snack.meters["mess"] += 2
    world.para()

    # Conflict
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.say(f"A conflict flared: {incident.conflict}.")
    objections = [
        f'"We cannot rhyme over that rotten problem," said {helper.id}. "First we learn what happened."',
        f'"Nobody meant to spoil our session," {helper.id} said. "Let us slow down and look."',
        f'"Stop blaming and start noticing," said {helper.id}. "The clues are still here."',
        f'"A sour smell is not proof against a friend," {helper.id} reminded the group.',
        f'"Let every animal speak once," said {helper.id}. "Then we will test the clues."',
        f'"We need a safe fix, not the fastest guess," {helper.id} said.',
        f'"Our rhyme can wait," said {helper.id}. "Kindness and evidence come first."',
        f'"The mess is real, but the accusation may be wrong," {helper.id} said.',
    ]
    world.say(rng.choice(objections))
    world.say(f"At first, {hero.id} {incident.mistaken_action}.")
    world.say(f"But {helper.id} noticed that {incident.clue}.")
    world.para()

    # Resolution / twist
    helper.memes["kindness"] += 1
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0
    helper.memes["conflict"] = 0
    snack.meters["freshness"] += 3
    investigation_leads = ["They followed that clue instead of their hunches.",
                           "The circle grew quiet enough to think.",
                           "They compared the clue with everything they had seen.",
                           "Working side by side made the next step clear.",
                           "A careful second look changed the whole problem.",
                           "They took turns observing, asking, and checking."]
    world.say(f"{rng.choice(investigation_leads)} {hero.id} and {helper.id} {incident.helpful_action}.")
    world.say(f"The twist was that {incident.twist}.")
    world.say(f"{hero.id} and {helper.id} {incident.resolution}.")
    world.say(f"They shared {snack.phrase}, then made a new rhyme about what they had learned: {incident.lesson}")
    closing_leads = ["When the last word landed,", "At the final soft beat,", "As the session ended,",
                     "Their repaired chorus ended with a picture:", "After one last happy refrain,",
                     "The new rhyme left everyone with this picture:"]
    ending = incident.ending[0].lower() + incident.ending[1:]
    world.say(f"{rng.choice(closing_leads)} {ending}")

    world.facts.update(
        place=params.place,
        event=params.event,
        hero=params.hero,
        helper=params.helper,
        hero_kind=params.hero_kind,
        helper_kind=params.helper_kind,
        incident=incident.id,
        premise=incident.premise,
        rotten_item=incident.rotten_item,
        warning=incident.warning,
        conflict_detail=incident.conflict,
        clue=incident.clue,
        helpful_action=incident.helpful_action,
        twist=incident.twist,
        resolution=incident.resolution,
        snack=incident.replacement,
        lesson=incident.lesson,
        ending=incident.ending,
        rotten=True,
        conflict=True,
        resolved=True,
    )
    return world


def valid_pairs() -> list[tuple[str, str]]:
    return [(place, event) for place in PLACES for event in EVENTS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Animal Story about a {f["hero_kind"]} named {f["hero"]} whose rhyme session at {PLACES[f["place"]].name} is interrupted by {f["rotten_item"]}.',
        f"Tell a gentle story where {f['hero']} and {f['helper']} resolve a conflict by noticing that {f['clue']}.",
        f"Write a child-friendly story with rhyme, a rotten surprise, and the twist that {f['twist']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['hero']} and {f['helper']} hold the rhyme session?",
            answer=f"They held it at {PLACES[f['place']].name}.",
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer=f"The conflict began after the animals found {f['rotten_item']}; {f['conflict_detail']}.",
        ),
        QAItem(
            question=f"What clue did {f['helper']} notice?",
            answer=f"{f['helper']} noticed that {f['clue']}.",
        ),
        QAItem(
            question="What was the twist in this rhyme-session story?",
            answer=f"The twist was that {f['twist']}.",
        ),
        QAItem(
            question=f"How did {f['hero']} and {f['helper']} resolve the problem?",
            answer=f"They {f['resolution']}.",
        ),
        QAItem(
            question="What lesson did the animals put into their new rhyme?",
            answer=f"They learned this: {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does rotten food mean?",
            answer="Rotten food is spoiled food that smells bad and should not be eaten.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound similar at the end, like cat and hat.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem or disagreement between characters.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that surprises the reader and turns the story in a new direction.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

HERO_KINDS = sorted(ANIMALS.keys())
HELPER_KINDS = sorted(ANIMALS.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: rhyme, twist, conflict, and a rotten surprise.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--event", choices=sorted(EVENTS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=HERO_KINDS)
    ap.add_argument("--helper")
    ap.add_argument("--helper-kind", choices=HELPER_KINDS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    event = args.event or rng.choice(sorted(EVENTS))
    hero_kind = args.hero_kind or rng.choice(HERO_KINDS)
    helper_kind = args.helper_kind or rng.choice([k for k in HELPER_KINDS if k != hero_kind])
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(
        place=place,
        event=event,
        hero=hero,
        hero_kind=hero_kind,
        helper=helper,
        helper_kind=helper_kind,
    )
    reasonableness_gate(params)
    return params


CURATED = [
    StoryParams(place="meadow", event="rotten_rhyme", hero="Pip", hero_kind="bunny", helper="Wren", helper_kind="fox"),
    StoryParams(place="porch", event="rotten_rhyme", hero="Milo", hero_kind="mouse", helper="Sage", helper_kind="bear"),
    StoryParams(place="den", event="rotten_rhyme", hero="Tia", hero_kind="fox", helper="Clover", helper_kind="bunny"),
]


def asp_verify() -> int:
    import asp

    # Minimal parity check: the ASP twin should at least enumerate the same
    # event/place shape as the Python registry.
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_story"))
    expected = set((place, "rotten_rhyme") for place in PLACES)
    if atoms != expected:
        print("MISMATCH between ASP and Python registry gate.")
        print("ASP:", sorted(atoms))
        print("PY :", sorted(expected))
        return 1
    print(f"OK: ASP gate matches Python registry gate ({len(atoms)} combinations).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story shapes:")
        for place, event in vals:
            print(f"  {place} / {event}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero} / {p.helper} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
