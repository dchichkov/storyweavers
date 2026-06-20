#!/usr/bin/env python3
"""Parking-lot comedy where kindness turns a plain warning marker into a funny helper."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class HeroProfile:
    key: str
    name: str
    subject: str
    object: str
    possessive: str
    trait: str


@dataclass(frozen=True)
class Venue:
    key: str
    business: str
    errand: str
    lot_detail: str
    ending_image: str
    helper_keys: tuple[str, ...]
    mess_keys: tuple[str, ...]
    marker_keys: tuple[str, ...]
    scrap_piece: str
    pun_line: str


@dataclass(frozen=True)
class Mess:
    key: str
    name: str
    article: str
    source: str
    texture: str
    spread_phrase: str
    cleanup_result: str
    width_m: float
    venue_keys: tuple[str, ...]


@dataclass(frozen=True)
class Marker:
    key: str
    base_name: str
    article: str
    display_name: str
    place_phrase: str
    height_m: float
    visibility_gain: float
    venue_keys: tuple[str, ...]


@dataclass(frozen=True)
class Helper:
    key: str
    name: str
    role: str
    tool: str
    reaction: str
    venue_keys: tuple[str, ...]


@dataclass
class StoryParams:
    venue: str
    mess: str
    marker: str
    helper: str
    hero: str
    seed: int = 0


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)
    state: dict[str, str | float | bool] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    beat: str
    subject: str
    text: str
    target: str | None = None


@dataclass
class ParkingLotComedyWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "bustle": 0.0,
            "worry": 0.0,
            "cheer": 0.0,
            "safety": 0.0,
            "mess": 0.0,
        }
    )
    facts: dict[str, str | float | bool] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(self, event_id: str, beat: str, subject: str, text: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, beat, subject, text, target))


HEROES: dict[str, HeroProfile] = {
    "nia": HeroProfile("nia", "Nia", "she", "her", "her", "quick-thinking"),
    "owen": HeroProfile("owen", "Owen", "he", "him", "his", "cheerful"),
    "zuri": HeroProfile("zuri", "Zuri", "she", "her", "her", "gentle"),
}

VENUES: dict[str, Venue] = {
    "donut_shop": Venue(
        "donut_shop",
        "Sunny Ring Donuts",
        "after picking up a small box of donut holes from Sunny Ring Donuts",
        "The white lines shimmered in the heat, and the lot smelled like sugar",
        "Captain Cone still stood by the dry patch, grinning under a pink paper bow",
        ("baker", "grandma"),
        ("glaze_spill",),
        ("cone", "folding_sign"),
        "a clean pink donut-box lid",
        "Donut rush. This is a caring lot.",
    ),
    "garden_center": Venue(
        "garden_center",
        "Fern Ferry Garden Center",
        "after helping choose marigolds at Fern Ferry Garden Center",
        "The parking lot smelled like warm leaves and damp bark",
        "Buddy Box kept watch beside the swept curb with a seed-packet smile on its front",
        ("gardener", "uncle"),
        ("soil_spill",),
        ("cone", "crate"),
        "a clean seed-packet sleeve",
        "Be-leaf the sign. This is a caring lot.",
    ),
    "pet_wash": Venue(
        "pet_wash",
        "Puddle Paws Pet Wash",
        "after bringing a fluffy dog towel back to Puddle Paws Pet Wash",
        "Soap bubbles popped in the sun between the parked cars",
        "Professor Slow waited by the rinsed curb while the last bubble winked away",
        ("attendant", "dad"),
        ("bubble_spill",),
        ("folding_sign", "crate"),
        "a dry sponge-wrapper card",
        "Paws and roll. This is a caring lot.",
    ),
}

MESSES: dict[str, Mess] = {
    "glaze_spill": Mess(
        "glaze_spill",
        "glaze spill",
        "a",
        "a tipped pastry tray",
        "sticky and shiny",
        "had spread in a crooked oval near the crosswalk",
        "the sugar patch dried into only a faint sweet smell",
        1.5,
        ("donut_shop",),
    ),
    "soil_spill": Mess(
        "soil_spill",
        "potting-soil spill",
        "a",
        "a split flower bag",
        "crumbly and dark",
        "had spread over two parking stripes like a muddy cloud",
        "the black crumbs were brushed back into neat planter tubs",
        1.8,
        ("garden_center",),
    ),
    "bubble_spill": Mess(
        "bubble_spill",
        "soap-bubble spill",
        "a",
        "a leaky wash bucket",
        "slippery and foamy",
        "had drifted across the curb lane in a wobbling stripe",
        "the curb shone clean instead of slippery",
        1.4,
        ("pet_wash",),
    ),
}

MARKERS: dict[str, Marker] = {
    "cone": Marker(
        "cone",
        "orange traffic cone",
        "an",
        "Captain Cone",
        "beside the mess",
        0.7,
        2.0,
        ("donut_shop", "garden_center"),
    ),
    "folding_sign": Marker(
        "folding_sign",
        "yellow folding caution sign",
        "a",
        "Professor Slow",
        "at the edge of the lane",
        0.9,
        2.2,
        ("donut_shop", "pet_wash"),
    ),
    "crate": Marker(
        "crate",
        "plastic milk crate",
        "a",
        "Buddy Box",
        "by the curb",
        0.5,
        1.8,
        ("garden_center", "pet_wash"),
    ),
}

HELPERS: dict[str, Helper] = {
    "baker": Helper("baker", "Ms. Lark", "baker", "a mop with a short blue handle", "laughed so hard she had to sniff once", ("donut_shop",)),
    "grandma": Helper("grandma", "Grandma Joy", "grandmother", "a stack of paper napkins", "groaned at the joke and then laughed anyway", ("donut_shop",)),
    "gardener": Helper("gardener", "Mr. Reed", "gardener", "a wide push broom", "shook his head and laughed into his green apron", ("garden_center",)),
    "uncle": Helper("uncle", "Uncle Toma", "uncle", "a dustpan on a long stick", "made a huge pretend gasp before he laughed", ("garden_center",)),
    "attendant": Helper("attendant", "Pia", "wash attendant", "a long squeegee", "snorted and almost dropped the towel she was carrying", ("pet_wash",)),
    "dad": Helper("dad", "Dad", "parent", "an old chamois cloth", "covered his smile with the cloth and laughed anyway", ("pet_wash",)),
}


def mess_phrase(mess: Mess) -> str:
    return f"{mess.article} {mess.name}"


def marker_phrase(marker: Marker) -> str:
    return f"{marker.article} {marker.base_name}"


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def transformation_details(world: ParkingLotComedyWorld) -> tuple[str, str]:
    venue = VENUES[world.params.venue]
    marker = MARKERS[world.params.marker]
    hero = HEROES[world.params.hero]
    if marker.key == "cone":
        action = (
            f"With permission, {hero.name} tied {venue.scrap_piece} around the top of the cone like a floppy hat "
            f"and drew two round eyes on a scrap card. In one moment the plain cone turned into {marker.display_name}."
        )
        ending = f"{marker.display_name} looked less like road equipment and more like a polite clown on duty."
        return action, ending
    if marker.key == "folding_sign":
        action = (
            f"With permission, {hero.name} clipped {venue.scrap_piece} across the front of the folding sign like a bright smile "
            f"and set it open a little wider. The dull sign suddenly became {marker.display_name}."
        )
        ending = f"{marker.display_name} looked as if it had puffed out its chest to protect the lane."
        return action, ending
    action = (
        f"With permission, {hero.name} flipped the crate upside down, taped on {venue.scrap_piece} like a grin, "
        f"and pointed it toward the wet spot. The plain crate became {marker.display_name}."
    )
    ending = f"{marker.display_name} looked sturdy and silly at the same time."
    return action, ending


def helper_cleanup_line(world: ParkingLotComedyWorld) -> str:
    helper = HELPERS[world.params.helper]
    mess = MESSES[world.params.mess]
    if mess.key == "glaze_spill":
        return (
            f"While drivers slowed down to read the sign, {helper.name} swabbed up the sticky glaze with {helper.tool} "
            "before any tires could smear it farther."
        )
    if mess.key == "soil_spill":
        return (
            f"While drivers slowed down to stare and grin, {helper.name} swept the loose soil with {helper.tool} "
            "and rescued the marigold pots from getting dusted black."
        )
    return (
        f"While drivers slowed down and gave the lane more room, {helper.name} pushed the sudsy water aside with {helper.tool} "
        "until the slippery stripe was gone."
    )


def marker_ending_image(world: ParkingLotComedyWorld) -> str:
    marker = MARKERS[world.params.marker]
    if marker.key == "cone":
        return f"{marker.display_name} still stood by the dry patch with its paper hat tipped to one side"
    if marker.key == "folding_sign":
        return f"{marker.display_name} waited in the clean lane with its bright smile clipped across the front"
    return f"{marker.display_name} kept watch by the swept curb with its cardboard grin facing the cars"


def ending_proof(world: ParkingLotComedyWorld) -> str:
    hero = HEROES[world.params.hero]
    marker = MARKERS[world.params.marker]
    mess = MESSES[world.params.mess]
    return (
        f"On the walk back to the car, {hero.name} glanced over one shoulder. "
        f"{sentence_start(marker_ending_image(world))}. {sentence_start(mess.cleanup_result)}, and the parking lot felt lighter than it had before. "
        f"{hero.name} liked that {marker.display_name} had started as a plain warning object and ended as a kind little joke."
    )


def format_qa(sample: StorySample) -> str:
    lines: list[str] = ["Prompts:"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("Story QA:")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("World QA:")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: ParkingLotComedyWorld) -> str:
    lines = ["", "TRACE", f"params={world.params}", f"world_meters={world.meters}"]
    lines.append("entities:")
    for entity_id in sorted(world.entities):
        entity = world.entities[entity_id]
        lines.append(
            f"  - {entity.id}: {entity.name} [{entity.kind}] meters={entity.meters} memes={entity.memes} state={entity.state}"
        )
    lines.append("history:")
    for event in world.history:
        lines.append(f"  - {event.beat}: {event.text}")
    return "\n".join(lines)


def generation_prompts(world: ParkingLotComedyWorld) -> list[str]:
    hero = HEROES[world.params.hero]
    venue = VENUES[world.params.venue]
    mess = MESSES[world.params.mess]
    marker = MARKERS[world.params.marker]
    return [
        f"Write a child-facing comedy set in the parking lot outside {venue.business}.",
        f"Let {hero.name}, a {hero.trait} child, notice {mess_phrase(mess)} and help transform {marker_phrase(marker)} into a funny warning helper.",
        "Include an explicit pun, keep the kindness central to the turn, and end on a concrete image that proves the lot changed.",
    ]


def story_qa(world: ParkingLotComedyWorld) -> list[tuple[str, str]]:
    hero = HEROES[world.params.hero]
    helper = HELPERS[world.params.helper]
    mess = MESSES[world.params.mess]
    marker = MARKERS[world.params.marker]
    venue = VENUES[world.params.venue]
    return [
        (
            f"What problem did {hero.name} notice in the parking lot?",
            (
                f"{hero.name} noticed {mess_phrase(mess)} caused by {mess.source}. "
                f"It mattered because the patch was {mess.texture}, and {helper.name} needed cars to see it before anyone rolled through too fast."
            ),
        ),
        (
            f"How was {marker_phrase(marker)} transformed?",
            (
                f"{hero.name} used {venue.scrap_piece} to turn the plain marker into {marker.display_name}. "
                f"The change made the warning easier to notice, and it also made the grown-up helper laugh instead of only worry."
            ),
        ),
        (
            "Why did the pun help the cleanup work?",
            (
                f"The pun gave people a reason to slow down and look twice at the lane. "
                f"Once drivers were paying attention to {marker.display_name}, {helper.name} had enough room to clean the mess safely."
            ),
        ),
    ]


def world_knowledge_qa(world: ParkingLotComedyWorld) -> list[tuple[str, str]]:
    venue = VENUES[world.params.venue]
    helper = HELPERS[world.params.helper]
    marker = MARKERS[world.params.marker]
    return [
        (
            "Where does this story take place?",
            (
                f"It takes place in the parking lot outside {venue.business}. "
                "The comedy stays in an ordinary errand spot, which makes the transformation feel small, physical, and believable."
            ),
        ),
        (
            "What act of kindness changes the mood of the story?",
            (
                f"The key kind act is that the child helps {helper.name} instead of walking away from the problem. "
                f"That help turns {marker_phrase(marker)} into a friendly warning, so the mood shifts from strained to playful."
            ),
        ),
        (
            "What proves that the ending is a real transformation and not just a joke?",
            (
                f"The proof is that the lane is safe again and the plain marker now has a new role as {marker.display_name}. "
                "The mess is gone, the helper is calmer, and the parking lot is visibly more welcoming than it was at the start."
            ),
        ),
    ]


def make_world(params: StoryParams) -> ParkingLotComedyWorld:
    hero = HEROES[params.hero]
    helper = HELPERS[params.helper]
    venue = VENUES[params.venue]
    mess = MESSES[params.mess]
    marker = MARKERS[params.marker]
    world = ParkingLotComedyWorld(params=params)
    world.add_entity(
        Entity(
            "hero",
            hero.name,
            "child",
            meters={"height_m": 1.32, "steps_m": 0.0},
            memes={"Kindness": 2, "Joy": 1, "Courage": 1},
            state={"trait": hero.trait},
        )
    )
    world.add_entity(
        Entity(
            "helper",
            helper.name,
            helper.role,
            meters={"reach_m": 1.75, "fatigue": 1.0},
            memes={"Worry": 2, "Relief": 0, "Gratitude": 0},
            state={"tool": helper.tool},
        )
    )
    world.add_entity(
        Entity(
            "lot",
            f"the parking lot outside {venue.business}",
            "place",
            meters={"safety_level": 1.0, "noise": 1.0},
            memes={"Routine": 3, "Comedy": 0, "Care": 0},
            state={"venue": venue.key},
        )
    )
    world.add_entity(
        Entity(
            "mess",
            mess_phrase(mess),
            "hazard",
            meters={"width_m": mess.width_m, "slip_risk": 2.0},
            memes={"Trouble": 2},
            state={"source": mess.source, "cleared": False},
        )
    )
    world.add_entity(
        Entity(
            "marker",
            marker_phrase(marker),
            "warning marker",
            meters={"height_m": marker.height_m, "visibility": 1.0},
            memes={"Warning": 2, "Comedy": 0, "Care": 0},
            state={"display_name": marker.display_name, "transformed": False, "place": marker.place_phrase},
        )
    )
    world.facts.update(
        {
            "pun_line": venue.pun_line,
            "scrap_piece": venue.scrap_piece,
            "venue_name": venue.business,
            "mess_result": mess.cleanup_result,
        }
    )
    return world


def arrive(world: ParkingLotComedyWorld) -> None:
    hero = HEROES[world.params.hero]
    venue = VENUES[world.params.venue]
    world.meters["bustle"] = 1.5
    world.meters["safety"] = 1.0
    world.meters["mess"] = 1.5
    world.record(
        "arrival",
        "beginning",
        "hero",
        f"{hero.name} stepped into the parking lot {venue.errand}.",
        "lot",
    )


def spot_problem(world: ParkingLotComedyWorld) -> None:
    venue = VENUES[world.params.venue]
    mess = MESSES[world.params.mess]
    helper = HELPERS[world.params.helper]
    marker = MARKERS[world.params.marker]
    world.meters["worry"] = 2.5
    world.entities["helper"].memes["Worry"] = 3
    world.entities["lot"].memes["Care"] = 0
    world.entities["mess"].meters["slip_risk"] = 2.4
    world.record(
        "problem",
        "tension",
        "helper",
        f"{sentence_start(venue.lot_detail)}, where {mess_phrase(mess)} from {mess.source} {mess.spread_phrase}. "
        f"{helper.name} was trying to guard it with only {marker_phrase(marker)} and {helper.tool}.",
        "mess",
    )


def offer_kindness(world: ParkingLotComedyWorld) -> None:
    hero = HEROES[world.params.hero]
    helper = HELPERS[world.params.helper]
    world.entities["hero"].memes["Kindness"] += 2
    world.entities["hero"].memes["Courage"] += 1
    world.entities["lot"].memes["Care"] = 2
    world.record(
        "offer",
        "turn",
        "hero",
        f"{hero.name} saw that {helper.name} needed help and did not keep walking. "
        f"{hero.subject.capitalize()} asked if the warning could be made easier to notice and kinder to look at.",
        "helper",
    )


def make_pun(world: ParkingLotComedyWorld) -> None:
    hero = HEROES[world.params.hero]
    helper = HELPERS[world.params.helper]
    world.meters["cheer"] = 1.8
    world.entities["marker"].memes["Comedy"] = 1
    world.record(
        "pun",
        "turn",
        "hero",
        f"Then {hero.name} tried a pun. \"{world.facts['pun_line']}\" {hero.subject} said. "
        f"The pun was silly, and {helper.name} {helper.reaction}.",
        "helper",
    )


def transform_marker(world: ParkingLotComedyWorld) -> None:
    marker = MARKERS[world.params.marker]
    action, ending = transformation_details(world)
    world.entities["marker"].state["transformed"] = True
    world.entities["marker"].meters["visibility"] += marker.visibility_gain
    world.entities["marker"].memes["Comedy"] += 2
    world.entities["marker"].memes["Care"] += 2
    world.entities["lot"].memes["Comedy"] = 2
    world.meters["cheer"] = 2.8
    world.record(
        "transform",
        "turn",
        "marker",
        f"{action} {ending}",
        "hero",
    )


def clean_and_slow(world: ParkingLotComedyWorld) -> None:
    helper = HELPERS[world.params.helper]
    marker = MARKERS[world.params.marker]
    world.entities["mess"].state["cleared"] = True
    world.entities["mess"].meters["slip_risk"] = 0.2
    world.entities["helper"].memes["Worry"] = 0
    world.entities["helper"].memes["Relief"] = 2
    world.entities["helper"].memes["Gratitude"] = 2
    world.entities["hero"].memes["Joy"] += 2
    world.entities["lot"].meters["safety_level"] = 3.0
    world.entities["lot"].memes["Care"] = 3
    world.meters["worry"] = 0.0
    world.meters["safety"] = 3.0
    world.meters["mess"] = 0.2
    world.meters["cheer"] = 3.0
    world.record(
        "cleanup",
        "resolution",
        "helper",
        f"{helper_cleanup_line(world)} One driver actually rolled down a window to say hello to {marker.display_name} before creeping past.",
        "marker",
    )


def settle(world: ParkingLotComedyWorld) -> None:
    world.record(
        "ending",
        "ending",
        "lot",
        ending_proof(world),
        "hero",
    )


def render_story(world: ParkingLotComedyWorld) -> str:
    hero = HEROES[world.params.hero]
    helper = HELPERS[world.params.helper]
    venue = VENUES[world.params.venue]
    mess = MESSES[world.params.mess]
    marker = MARKERS[world.params.marker]
    opening = (
        f"{hero.name} stepped into the parking lot {venue.errand}. "
        f"{sentence_start(venue.lot_detail)}. Right away {hero.subject} saw {helper.name} worrying over {mess_phrase(mess)}."
    )
    tension = (
        f"The mess was {mess.texture} and had come from {mess.source}. "
        f"{helper.name} had set out {marker_phrase(marker)}, but it looked so plain that drivers only gave it quick little glances."
    )
    turn = (
        f"{hero.name} felt sorry for {helper.name} and offered to help. "
        f"Then {hero.subject} tried a pun: \"{world.facts['pun_line']}\" "
        f"{helper.name} {helper.reaction}, which made the hard moment feel softer."
    )
    transform = transformation_details(world)[0] + " " + transformation_details(world)[1]
    resolution = (
        f"Soon {marker.display_name} was standing {marker.place_phrase}, looking funny enough to make people slow down on purpose. "
        f"{helper_cleanup_line(world)}"
    )
    ending = ending_proof(world)
    return " ".join([opening, tension, turn, transform, resolution, ending])


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.venue not in VENUES:
        return False, f"unknown venue: {params.venue}"
    if params.mess not in MESSES:
        return False, f"unknown mess: {params.mess}"
    if params.marker not in MARKERS:
        return False, f"unknown marker: {params.marker}"
    if params.helper not in HELPERS:
        return False, f"unknown helper: {params.helper}"
    if params.hero not in HEROES:
        return False, f"unknown hero: {params.hero}"
    venue = VENUES[params.venue]
    mess = MESSES[params.mess]
    marker = MARKERS[params.marker]
    helper = HELPERS[params.helper]
    if params.mess not in venue.mess_keys:
        return False, f"{mess.name} does not belong outside {venue.business}"
    if params.helper not in venue.helper_keys:
        return False, f"{helper.name} would not be the right helper outside {venue.business}"
    if params.marker not in venue.marker_keys:
        return False, f"{marker.base_name} does not fit this parking-lot setup"
    if params.venue not in mess.venue_keys:
        return False, f"{mess.name} is not reasonable in the chosen venue"
    if params.venue not in marker.venue_keys:
        return False, f"{marker.base_name} would not be available in this parking lot"
    if params.venue not in helper.venue_keys:
        return False, f"{helper.name} does not belong in this venue"
    return True, ""


def structural_valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue in VENUES:
        for mess in MESSES:
            for marker in MARKERS:
                for helper in HELPERS:
                    probe = StoryParams(venue, mess, marker, helper, hero="nia")
                    ok, _ = valid_params(probe)
                    if ok:
                        combos.append((venue, mess, marker, helper))
    return sorted(combos)


def all_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    seed = 1
    for venue, mess, marker, helper in structural_valid_combos():
        for hero in HEROES:
            out.append(StoryParams(venue, mess, marker, helper, hero, seed=seed))
            seed += 1
    return out


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    arrive(world)
    spot_problem(world)
    offer_kindness(world)
    make_pun(world)
    transform_marker(world)
    clean_and_slow(world)
    settle(world)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
venue(V) :- venue_fact(V).
mess(M) :- mess_fact(M).
marker(K) :- marker_fact(K).
helper(H) :- helper_fact(H).

combo(V,M,K,H) :-
    venue(V), mess(M), marker(K), helper(H),
    venue_mess(V,M),
    venue_marker(V,K),
    venue_helper(V,H),
    mess_venue(M,V),
    marker_venue(K,V),
    helper_venue(H,V).

#show combo/4.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for venue in VENUES.values():
        rows.append(asp.fact("venue_fact", venue.key))
        rows.extend(asp.fact("venue_mess", venue.key, mess) for mess in venue.mess_keys)
        rows.extend(asp.fact("venue_marker", venue.key, marker) for marker in venue.marker_keys)
        rows.extend(asp.fact("venue_helper", venue.key, helper) for helper in venue.helper_keys)
    for mess in MESSES.values():
        rows.append(asp.fact("mess_fact", mess.key))
        rows.extend(asp.fact("mess_venue", mess.key, venue) for venue in mess.venue_keys)
    for marker in MARKERS.values():
        rows.append(asp.fact("marker_fact", marker.key))
        rows.extend(asp.fact("marker_venue", marker.key, venue) for venue in marker.venue_keys)
    for helper in HELPERS.values():
        rows.append(asp.fact("helper_fact", helper.key))
        rows.extend(asp.fact("helper_venue", helper.key, venue) for venue in helper.venue_keys)
    return "\n".join(rows)


def asp_program(show: str = "#show combo/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show combo/4."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    python_set = set(structural_valid_combos())
    asp_set = set(asp_valid_combos())
    failed = False
    if python_set != asp_set:
        print("ASP/Python mismatch:")
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        return 1

    ordered_heroes = sorted(HEROES)
    for index, combo in enumerate(sorted(python_set), start=1):
        hero = ordered_heroes[index % len(ordered_heroes)]
        sample = generate(StoryParams(*combo, hero=hero, seed=index))
        world = sample.world
        lower_story = sample.story.lower()
        if "parking lot" not in lower_story:
            print("verify failed: story lost parking-lot setting for", combo)
            failed = True
        if "pun" not in lower_story:
            print("verify failed: story lost required word 'pun' for", combo)
            failed = True
        if "caring lot" not in lower_story:
            print("verify failed: story lost central pun beat for", combo)
            failed = True
        if world is None or not world.entities["marker"].state["transformed"]:
            print("verify failed: marker was not transformed for", combo)
            failed = True
        if world is None or not world.entities["mess"].state["cleared"]:
            print("verify failed: mess was not cleared for", combo)
            failed = True
        if len(sample.story_qa) != 3 or len(sample.world_qa) != 3:
            print("verify failed: QA count mismatch for", combo)
            failed = True
        if any(len(item.answer.split()) < 12 for item in sample.story_qa + sample.world_qa):
            print("verify failed: short QA answer for", combo)
            failed = True
    if failed:
        return 1
    print(f"OK: clingo gate matches Python ({len(python_set)} combos), and all generated samples passed sanity checks.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parking-lot kindness comedy with a transformed warning marker.")
    parser.add_argument("--venue", choices=sorted(VENUES))
    parser.add_argument("--mess", choices=sorted(MESSES))
    parser.add_argument("--marker", choices=sorted(MARKERS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo
        for combo in structural_valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.mess is None or combo[1] == args.mess)
        and (args.marker is None or combo[2] == args.marker)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("No reasonable parking-lot kindness comedy fits that combination of venue, mess, marker, and helper.")
    venue, mess, marker, helper = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(HEROES))
    seed = (args.seed or 1000) + index
    return StoryParams(venue, mess, marker, helper, hero, seed=seed)


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for index, params in enumerate(all_params(), start=1):
        hero = args.hero or params.hero
        sample_params = StoryParams(
            params.venue,
            params.mess,
            params.marker,
            params.helper,
            hero,
            seed=(args.seed or 0) + index,
        )
        samples.append(generate(sample_params))
    return samples


def main() -> int:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show combo/4."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    try:
        if args.all:
            samples = _sample_all(args)
        else:
            samples = []
            seen: set[str] = set()
            i = 0
            while len(samples) < args.n and i < max(args.n * 50, 50):
                params = resolve_params(args, random.Random(base_seed + i), index=i)
                sample = generate(params)
                i += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique parking-lot kindness comedies with those constraints.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for i, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = f"### {p.venue} / {p.mess} / {p.marker} / {p.helper} / {p.hero}"
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if i < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
