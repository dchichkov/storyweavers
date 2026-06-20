#!/usr/bin/env python3
"""Slice-of-life parking lot mystery driven by a floating clue and a strange sound."""

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
    anchor_keys: tuple[str, ...]


@dataclass(frozen=True)
class FloatThing:
    key: str
    name: str
    article: str
    color: str
    texture: str
    drift_phrase: str
    settle_phrase: str
    height_m: float
    anchor_keys: tuple[str, ...]


@dataclass(frozen=True)
class Anchor:
    key: str
    name: str
    place_phrase: str
    sound_effect: str
    sound_line: str
    resolved_image: str
    venue_keys: tuple[str, ...]


@dataclass(frozen=True)
class Helper:
    key: str
    name: str
    role: str
    tool: str
    venue_keys: tuple[str, ...]


@dataclass
class StoryParams:
    venue: str
    float_thing: str
    anchor: str
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
class ParkingLotWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "wind": 0.0,
            "mystery": 0.0,
            "quiet": 0.0,
            "bustle": 0.0,
            "relief": 0.0,
        }
    )
    facts: dict[str, str | int | float | bool] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(self, event_id: str, beat: str, subject: str, text: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, beat, subject, text, target))


HEROES: dict[str, HeroProfile] = {
    "leah": HeroProfile("leah", "Leah", "she", "her", "her", "observant"),
    "mateo": HeroProfile("mateo", "Mateo", "he", "him", "his", "patient"),
    "ivy": HeroProfile("ivy", "Ivy", "she", "her", "her", "careful"),
}

VENUES: dict[str, Venue] = {
    "grocery": Venue(
        "grocery",
        "Green Basket Market",
        "after helping carry a bag of oranges out of Green Basket Market",
        "cart shadows stretched across the painted lines",
        "the cart row stood still beside the red curb",
        ("dad", "cart_clerk"),
        ("cart_corral", "signpost"),
    ),
    "library": Venue(
        "library",
        "Maple Street Library",
        "after returning three books to Maple Street Library",
        "the bike rack drew long bars of shade over the warm asphalt",
        "the book drop clicked once, and then the lot stayed calm",
        ("grandpa", "librarian"),
        ("bike_rack", "signpost"),
    ),
    "bakery": Venue(
        "bakery",
        "Pine Corner Bakery",
        "after picking up a paper bag of warm rolls from Pine Corner Bakery",
        "the air smelled like butter even out on the parking lot",
        "the bakery door swung shut behind them, and the lot sounded ordinary again",
        ("baker", "aunt"),
        ("bike_rack", "signpost"),
    ),
}

FLOAT_THINGS: dict[str, FloatThing] = {
    "ribbon": FloatThing(
        "ribbon",
        "balloon ribbon",
        "a",
        "silver",
        "slick plastic",
        "began to float in shiny curls",
        "lay in one quiet loop",
        0.9,
        ("bike_rack", "cart_corral"),
    ),
    "receipt": FloatThing(
        "receipt",
        "receipt strip",
        "a",
        "white",
        "thin paper",
        "began to float like a little fish tail",
        "rested flat against the curb",
        0.5,
        ("bike_rack", "signpost"),
    ),
    "bag": FloatThing(
        "bag",
        "produce bag",
        "a",
        "yellow",
        "puffy plastic",
        "began to float in soft puffs",
        "sagged into a harmless knot",
        0.8,
        ("cart_corral", "signpost"),
    ),
}

ANCHORS: dict[str, Anchor] = {
    "cart_corral": Anchor(
        "cart_corral",
        "cart corral",
        "at the cart corral",
        "clink-clink",
        "a bright clink-clink kept hopping across the parking lot",
        "the metal rail only flashed in the sun",
        ("grocery",),
    ),
    "bike_rack": Anchor(
        "bike_rack",
        "bike rack",
        "by the bike rack",
        "ting-ting",
        "a small ting-ting, ting-ting rang between the parked cars",
        "the rack just held its line of shadows",
        ("library", "bakery"),
    ),
    "signpost": Anchor(
        "signpost",
        "parking sign",
        "beside the parking sign",
        "flap-flap",
        "a papery flap-flap kept slapping the warm air",
        "the sign only pointed quietly toward the spaces",
        ("grocery", "library", "bakery"),
    ),
}

HELPERS: dict[str, Helper] = {
    "dad": Helper("dad", "Dad", "parent", "an old umbrella", ("grocery",)),
    "cart_clerk": Helper("cart_clerk", "Ms. Tori", "cart clerk", "a long grabber", ("grocery",)),
    "grandpa": Helper("grandpa", "Grandpa", "grandparent", "the curved handle of his cane", ("library",)),
    "librarian": Helper("librarian", "Mr. Hale", "librarian", "a return-bin reacher", ("library",)),
    "baker": Helper("baker", "Ms. June", "baker", "a broom handle", ("bakery",)),
    "aunt": Helper("aunt", "Aunt Rina", "aunt", "the strap of her tote bag", ("bakery",)),
}


def article_phrase(item: FloatThing) -> str:
    return f"{item.article} {item.color} {item.name}"


def indefinite_article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def anchor_cause(float_thing: FloatThing, anchor: Anchor) -> str:
    if anchor.key == "cart_corral":
        return (
            f"The {float_thing.name} had wound around the loose cart chain, "
            "and every puff of wind pulled the chain into the rail."
        )
    if anchor.key == "bike_rack":
        return (
            f"The {float_thing.name} was hooked beneath a red reflector, "
            "and each little gust flicked the reflector against the metal bar."
        )
    return (
        f"The {float_thing.name} was caught under the corner of a laminated notice, "
        "so every breeze snapped the notice back against the pole."
    )


def helper_action(hero: HeroProfile, helper: Helper, float_thing: FloatThing, anchor: Anchor) -> str:
    if helper.key == "dad":
        return (
            f"Dad held the grocery bag close and used {helper.tool} to lift the {float_thing.name} free. "
            f"{hero.name} caught it before the wind could send it flying again."
        )
    if helper.key == "cart_clerk":
        return (
            f"Ms. Tori came over with {helper.tool}, pinched the {float_thing.name}, "
            f"and let {hero.name} guide it into the store's lost-and-found bucket."
        )
    if helper.key == "grandpa":
        return (
            f"Grandpa tipped out {helper.tool}, held the rack steady, "
            f"and {hero.name} slipped the {float_thing.name} loose with careful fingers."
        )
    if helper.key == "librarian":
        return (
            f"Mr. Hale reached out with {helper.tool}, and {hero.name} pointed right where the {float_thing.name} had snagged. "
            "Together they eased it down without bending the sign or the rack."
        )
    if helper.key == "baker":
        return (
            f"Ms. June leaned out the bakery door with {helper.tool}, nudged the {float_thing.name} lower, "
            f"and {hero.name} gathered it before it could float away again."
        )
    return (
        f"Aunt Rina looped {helper.tool} over the {float_thing.name}, "
        f"and {hero.name} laughed softly when it slid down into {hero.possessive} hands at last."
    )


def closing_sentence(world: ParkingLotWorld) -> str:
    hero = HEROES[world.params.hero]
    venue = VENUES[world.params.venue]
    anchor = ANCHORS[world.params.anchor]
    float_thing = FLOAT_THINGS[world.params.float_thing]
    if world.meters["quiet"] >= 3.0:
        return (
            f"On the way to the car, {hero.name} looked back once more. "
            f"{sentence_start(anchor.resolved_image)}. "
            f"The {float_thing.name} {float_thing.settle_phrase}, and {venue.ending_image}. "
            f"{hero.name} smiled because the little mystery had turned into an ordinary, peaceful afternoon again."
        )
    return (
        f"{hero.name} kept listening on the way to the car, but the sound never came back. "
        f"{venue.ending_image}."
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


def dump_trace(world: ParkingLotWorld) -> str:
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


def generation_prompts(world: ParkingLotWorld) -> list[str]:
    hero = HEROES[world.params.hero]
    venue = VENUES[world.params.venue]
    anchor = ANCHORS[world.params.anchor]
    float_thing = FLOAT_THINGS[world.params.float_thing]
    return [
        f"Write a small slice-of-life story set in the parking lot outside {venue.business}.",
        f"Let {hero.name}, {indefinite_article(hero.trait)} {hero.trait} child, hear {anchor.sound_effect} and solve the mystery by following {article_phrase(float_thing)} that starts to float.",
        f"End with a concrete quiet image that proves the parking lot changed after the problem was fixed.",
    ]


def story_qa(world: ParkingLotWorld) -> list[tuple[str, str]]:
    hero = HEROES[world.params.hero]
    helper = HELPERS[world.params.helper]
    float_thing = FLOAT_THINGS[world.params.float_thing]
    anchor = ANCHORS[world.params.anchor]
    return [
        (
            f"What mystery did {hero.name} solve in the parking lot?",
            (
                f"{hero.name} figured out what was making the {anchor.sound_effect} sound in the parking lot. "
                f"The mystery turned out to be {article_phrase(float_thing)} caught {anchor.place_phrase}, where the wind kept jerking it against something hard."
            ),
        ),
        (
            f"Why did the sound keep repeating {anchor.place_phrase}?",
            (
                f"It kept repeating because the breeze never stopped tugging at the {float_thing.name}. "
                f"{anchor_cause(float_thing, anchor)}"
            ),
        ),
        (
            f"How did {helper.name} help {hero.name} finish the job?",
            (
                f"{helper.name} helped by using {helper.tool} so the snag could be reached safely. "
                f"That gave {hero.name} the last bit of help needed to free the {float_thing.name} and quiet the lot."
            ),
        ),
    ]


def world_knowledge_qa(world: ParkingLotWorld) -> list[tuple[str, str]]:
    venue = VENUES[world.params.venue]
    anchor = ANCHORS[world.params.anchor]
    float_thing = FLOAT_THINGS[world.params.float_thing]
    helper = HELPERS[world.params.helper]
    return [
        (
            "Where does this story take place?",
            (
                f"It takes place in the parking lot outside {venue.business}. "
                "The whole mystery stays grounded in an ordinary errand-time moment instead of a magical place."
            ),
        ),
        (
            f"What made {article_phrase(float_thing)} noticeable enough to become a clue?",
            (
                f"It was light enough to float and flutter whenever the breeze moved through the parked cars. "
                f"That motion drew attention to the spot {anchor.place_phrase}, where the real cause of the noise was hiding."
            ),
        ),
        (
            "What changed by the end of the story?",
            (
                f"The parking lot changed from a noisy, puzzling place into a quiet one again. "
                f"After {helper.name} helped and the snag was fixed, the sound stopped and the ordinary afternoon returned."
            ),
        ),
    ]


def make_world(params: StoryParams) -> ParkingLotWorld:
    hero = HEROES[params.hero]
    helper = HELPERS[params.helper]
    venue = VENUES[params.venue]
    float_thing = FLOAT_THINGS[params.float_thing]
    anchor = ANCHORS[params.anchor]
    world = ParkingLotWorld(params=params)
    world.add_entity(
        Entity(
            "hero",
            hero.name,
            "child",
            meters={"height_m": 1.3, "steps_m": 0.0},
            memes={"Curiosity": 2, "Calm": 2, "Care": 1},
            state={"trait": hero.trait},
        )
    )
    world.add_entity(
        Entity(
            "helper",
            helper.name,
            helper.role,
            meters={"reach_m": 1.8},
            memes={"Care": 2, "Patience": 1},
            state={"tool": helper.tool},
        )
    )
    world.add_entity(
        Entity(
            "lot",
            f"the parking lot outside {venue.business}",
            "place",
            meters={"wind_mps": 2.0, "quiet_level": 0.0},
            memes={"Routine": 3, "Mystery": 0},
            state={"venue": venue.key},
        )
    )
    world.add_entity(
        Entity(
            "float",
            article_phrase(float_thing),
            "physical clue",
            meters={"height_m": float_thing.height_m, "tension": 0.0},
            memes={"Lightness": 2, "Nuisance": 1},
            state={"texture": float_thing.texture, "free": False},
        )
    )
    world.add_entity(
        Entity(
            "anchor",
            anchor.name,
            "physical anchor",
            meters={"rattle": 0.0},
            memes={"Noise": 2},
            state={"place": anchor.place_phrase, "sound": anchor.sound_effect},
        )
    )
    world.facts.update(
        {
            "business": venue.business,
            "sound_effect": anchor.sound_effect,
            "float_phrase": article_phrase(float_thing),
            "cause_sentence": anchor_cause(float_thing, anchor),
        }
    )
    return world


def arrive(world: ParkingLotWorld) -> None:
    hero = HEROES[world.params.hero]
    venue = VENUES[world.params.venue]
    world.meters["bustle"] = 1.0
    world.meters["quiet"] = 0.5
    world.entities["lot"].meters["quiet_level"] = 0.5
    world.record(
        "arrival",
        "beginning",
        "hero",
        f"{hero.name} reached the parking lot {venue.errand}.",
    )


def hear_mystery(world: ParkingLotWorld) -> None:
    hero = HEROES[world.params.hero]
    anchor = ANCHORS[world.params.anchor]
    world.meters["mystery"] = 2.0
    world.meters["wind"] = 1.5
    world.entities["hero"].memes["Curiosity"] += 1
    world.entities["lot"].memes["Mystery"] = 2
    world.entities["anchor"].meters["rattle"] = 1.2
    world.record(
        "sound",
        "tension",
        "anchor",
        f"{anchor.sound_line}, and {hero.name} stopped to listen.",
        "hero",
    )


def follow_clue(world: ParkingLotWorld) -> None:
    float_thing = FLOAT_THINGS[world.params.float_thing]
    anchor = ANCHORS[world.params.anchor]
    hero = HEROES[world.params.hero]
    world.entities["float"].meters["height_m"] = float_thing.height_m
    world.entities["float"].meters["tension"] = 1.0
    world.entities["hero"].meters["steps_m"] += 6.0
    world.record(
        "clue",
        "turn",
        "float",
        f"{sentence_start(article_phrase(float_thing))} {float_thing.drift_phrase} {anchor.place_phrase}, and {hero.name} followed it with narrowed eyes.",
        "hero",
    )


def inspect_cause(world: ParkingLotWorld) -> None:
    hero = HEROES[world.params.hero]
    world.entities["hero"].memes["Curiosity"] += 1
    world.entities["hero"].memes["Calm"] -= 1
    world.record(
        "cause",
        "turn",
        "hero",
        f"{hero.name} knelt beside the sound and finally saw the answer. {world.facts['cause_sentence']}",
        "anchor",
    )


def solve_mystery(world: ParkingLotWorld) -> None:
    hero = HEROES[world.params.hero]
    helper = HELPERS[world.params.helper]
    float_thing = FLOAT_THINGS[world.params.float_thing]
    world.entities["float"].state["free"] = True
    world.entities["float"].meters["tension"] = 0.0
    world.entities["anchor"].meters["rattle"] = 0.0
    world.entities["lot"].meters["quiet_level"] = 3.0
    world.entities["hero"].memes["Calm"] += 2
    world.entities["hero"].memes["Care"] += 1
    world.entities["helper"].memes["Care"] += 1
    world.meters["mystery"] = 0.0
    world.meters["quiet"] = 3.0
    world.meters["relief"] = 2.0
    world.record(
        "solve",
        "resolution",
        "helper",
        helper_action(hero, helper, float_thing, ANCHORS[world.params.anchor]),
        "float",
    )


def settle(world: ParkingLotWorld) -> None:
    world.record(
        "settle",
        "ending",
        "lot",
        closing_sentence(world),
        "hero",
    )


def render_story(world: ParkingLotWorld) -> str:
    hero = HEROES[world.params.hero]
    venue = VENUES[world.params.venue]
    anchor = ANCHORS[world.params.anchor]
    float_thing = FLOAT_THINGS[world.params.float_thing]
    helper = HELPERS[world.params.helper]
    mystery_feel = "curious" if world.entities["hero"].memes["Curiosity"] >= 4 else "careful"
    opening = (
        f"{hero.name} was in the parking lot {venue.errand} when {hero.subject} heard something odd. "
        f"{sentence_start(venue.lot_detail)}, but {anchor.sound_line}."
    )
    middle = (
        f"{hero.name} stood still and listened again. Then {article_phrase(float_thing)} {float_thing.drift_phrase} "
        f"{anchor.place_phrase}, as if it wanted someone to notice it. "
        f"Because {hero.subject} was a {mystery_feel} child, {hero.name} walked closer instead of hurrying to the car."
    )
    turn = (
        f"When {hero.subject} crouched beside the noise, the answer was suddenly plain. "
        f"{world.facts['cause_sentence']} The sound was not spooky at all, only busy and trapped."
    )
    resolution = (
        f"{helper_action(hero, helper, float_thing, anchor)} "
        f"At once the {anchor.sound_effect} stopped, and the quiet felt bigger than before."
    )
    ending = closing_sentence(world)
    return " ".join([opening, middle, turn, resolution, ending])


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.venue not in VENUES:
        return False, f"unknown venue: {params.venue}"
    if params.float_thing not in FLOAT_THINGS:
        return False, f"unknown float thing: {params.float_thing}"
    if params.anchor not in ANCHORS:
        return False, f"unknown anchor: {params.anchor}"
    if params.helper not in HELPERS:
        return False, f"unknown helper: {params.helper}"
    if params.hero not in HEROES:
        return False, f"unknown hero: {params.hero}"
    venue = VENUES[params.venue]
    float_thing = FLOAT_THINGS[params.float_thing]
    anchor = ANCHORS[params.anchor]
    helper = HELPERS[params.helper]
    if params.helper not in venue.helper_keys:
        return False, f"{helper.name} does not fit an errand at {venue.business}"
    if params.anchor not in venue.anchor_keys:
        return False, f"{anchor.name} is not part of the parking lot scene outside {venue.business}"
    if params.anchor not in float_thing.anchor_keys:
        return False, f"{article_phrase(float_thing)} cannot plausibly snag on the {anchor.name}"
    if params.venue not in anchor.venue_keys:
        return False, f"{anchor.name} does not belong in the chosen parking lot"
    if params.venue not in helper.venue_keys:
        return False, f"{helper.name} would not be around to help in this parking lot"
    return True, ""


def structural_valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue in VENUES:
        for float_key in FLOAT_THINGS:
            for anchor in ANCHORS:
                for helper in HELPERS:
                    probe = StoryParams(venue, float_key, anchor, helper, hero="leah")
                    ok, _ = valid_params(probe)
                    if ok:
                        combos.append((venue, float_key, anchor, helper))
    return sorted(combos)


def all_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    seed = 1
    for venue, float_key, anchor, helper in structural_valid_combos():
        for hero in HEROES:
            out.append(StoryParams(venue, float_key, anchor, helper, hero, seed=seed))
            seed += 1
    return out


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    arrive(world)
    hear_mystery(world)
    follow_clue(world)
    inspect_cause(world)
    solve_mystery(world)
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
float_thing(F) :- float_fact(F).
anchor(A) :- anchor_fact(A).
helper(H) :- helper_fact(H).

combo(V,F,A,H) :-
    venue(V), float_thing(F), anchor(A), helper(H),
    venue_anchor(V,A),
    float_anchor(F,A),
    venue_helper(V,H),
    anchor_venue(A,V),
    helper_venue(H,V).

#show combo/4.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for venue in VENUES.values():
        rows.append(asp.fact("venue_fact", venue.key))
        rows.extend(asp.fact("venue_anchor", venue.key, anchor) for anchor in venue.anchor_keys)
        rows.extend(asp.fact("venue_helper", venue.key, helper) for helper in venue.helper_keys)
    for float_thing in FLOAT_THINGS.values():
        rows.append(asp.fact("float_fact", float_thing.key))
        rows.extend(asp.fact("float_anchor", float_thing.key, anchor) for anchor in float_thing.anchor_keys)
    for anchor in ANCHORS.values():
        rows.append(asp.fact("anchor_fact", anchor.key))
        rows.extend(asp.fact("anchor_venue", anchor.key, venue) for venue in anchor.venue_keys)
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

    for index, combo in enumerate(sorted(python_set), start=1):
        hero = sorted(HEROES)[index % len(HEROES)]
        sample = generate(StoryParams(*combo, hero=hero, seed=index))
        lower_story = sample.story.lower()
        if "parking lot" not in lower_story:
            print("verify failed: story lost parking-lot setting for", combo)
            failed = True
        if "float" not in lower_story:
            print("verify failed: story lost required word 'float' for", combo)
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
    parser = argparse.ArgumentParser(description="Floating-clue parking-lot mystery world.")
    parser.add_argument("--venue", choices=sorted(VENUES))
    parser.add_argument("--float-thing", dest="float_thing", choices=sorted(FLOAT_THINGS))
    parser.add_argument("--anchor", choices=sorted(ANCHORS))
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
        and (args.float_thing is None or combo[1] == args.float_thing)
        and (args.anchor is None or combo[2] == args.anchor)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError(
            "No reasonable parking-lot mystery fits that combination of venue, floating clue, anchor, and helper."
        )
    venue, float_key, anchor, helper = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(sorted(HEROES))
    seed = (args.seed or 1000) + index
    return StoryParams(venue, float_key, anchor, helper, hero, seed=seed)


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for index, params in enumerate(all_params(), start=1):
        hero = args.hero or params.hero
        sample_params = StoryParams(
            params.venue,
            params.float_thing,
            params.anchor,
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
            samples: list[StorySample] = []
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
                raise StoryError("Could not generate enough unique parking-lot mysteries with those constraints.")

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
                header = f"### {p.venue} / {p.float_thing} / {p.anchor} / {p.helper} / {p.hero}"
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
