#!/usr/bin/env python3
"""Slice-of-life parking-lot mystery with a floating clue and everyday sound effects."""

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
class ChildProfile:
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
    lot_image: str
    ending_image: str
    anchor_keys: tuple[str, ...]
    helper_keys: tuple[str, ...]


@dataclass(frozen=True)
class FloatClue:
    key: str
    name: str
    article: str
    color: str
    texture: str
    float_line: str
    resting_line: str
    height_m: float
    anchor_keys: tuple[str, ...]


@dataclass(frozen=True)
class Anchor:
    key: str
    name: str
    place_phrase: str
    sound_effect: str
    sound_line: str
    quiet_image: str
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
    float_clue: str
    anchor: str
    helper: str
    child: str
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
            "breeze": 0.0,
            "mystery": 0.0,
            "calm": 0.0,
            "relief": 0.0,
            "attention": 0.0,
        }
    )
    facts: dict[str, str | int | float | bool] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(self, event_id: str, beat: str, subject: str, text: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, beat, subject, text, target))


CHILDREN: dict[str, ChildProfile] = {
    "nora": ChildProfile("nora", "Nora", "she", "her", "her", "patient"),
    "eli": ChildProfile("eli", "Eli", "he", "him", "his", "careful"),
    "maya": ChildProfile("maya", "Maya", "she", "her", "her", "curious"),
}

VENUES: dict[str, Venue] = {
    "pharmacy": Venue(
        "pharmacy",
        "Sunny Corner Pharmacy",
        "after picking up cough drops at Sunny Corner Pharmacy",
        "Painted arrows shone on the warm parking lot after a quick sweep of sunlight.",
        "the receipt bin by the door sat still, and the afternoon felt normal again",
        ("drain_grate", "scooter_rack"),
        ("mom", "clerk"),
    ),
    "flower_shop": Venue(
        "flower_shop",
        "Petal Porch Flowers",
        "after helping carry a paper sleeve of daisies out of Petal Porch Flowers",
        "The parking lot smelled faintly sweet, even near the bumpers and white lines.",
        "the flower sleeve rustled once, then even the open spaces felt soft and settled",
        ("signpost", "drain_grate"),
        ("owner", "aunt"),
    ),
    "laundromat": Venue(
        "laundromat",
        "Spin Time Laundry",
        "after folding two warm towels at Spin Time Laundry",
        "Coins chimed behind the glass door, but out on the parking lot the air felt roomy and plain.",
        "the dryer carts inside kept rolling, while outside the lot held its breath in a peaceful way",
        ("signpost", "scooter_rack"),
        ("janitor", "grandpa"),
    ),
}

FLOAT_CLUES: dict[str, FloatClue] = {
    "ribbon": FloatClue(
        "ribbon",
        "gift ribbon",
        "a",
        "blue",
        "silky plastic",
        "began to float in light loops over the painted stripe",
        "curled into one quiet ring by the curb",
        0.9,
        ("signpost", "scooter_rack"),
    ),
    "bag": FloatClue(
        "bag",
        "produce bag",
        "a",
        "clear",
        "thin plastic",
        "started to float like a small jellyfish in the breeze",
        "drooped into a harmless knot by the curb",
        0.8,
        ("drain_grate", "signpost"),
    ),
    "coupon": FloatClue(
        "coupon",
        "coupon strip",
        "a",
        "pink",
        "glossy paper",
        "rose, seemed to float for a moment, and then dipped back down",
        "lay flat against the yellow wheel stop",
        0.5,
        ("drain_grate", "scooter_rack"),
    ),
}

ANCHORS: dict[str, Anchor] = {
    "drain_grate": Anchor(
        "drain_grate",
        "storm drain grate",
        "near the storm drain grate",
        "frip-frip",
        "A papery frip-frip kept flicking up from the far side of the parked cars.",
        "The dark grate just held a little shadow and no noise at all.",
        ("pharmacy", "flower_shop"),
    ),
    "signpost": Anchor(
        "signpost",
        "parking sign",
        "beside the parking sign",
        "tap-tap",
        "A neat tap-tap, tap-tap kept ticking against the warm air.",
        "The sign only pointed over the empty spaces and stayed still.",
        ("flower_shop", "laundromat"),
    ),
    "scooter_rack": Anchor(
        "scooter_rack",
        "scooter rack",
        "by the scooter rack",
        "ting-ting",
        "A quick ting-ting bounced between the cars and came back again.",
        "The rack held its row of tiny wheels without another sound.",
        ("pharmacy", "laundromat"),
    ),
}

HELPERS: dict[str, Helper] = {
    "mom": Helper("mom", "Mom", "parent", "the long strap of her shopping bag", ("pharmacy",)),
    "clerk": Helper("clerk", "Mr. Bell", "clerk", "a litter picker", ("pharmacy",)),
    "owner": Helper("owner", "Ms. Pru", "shop owner", "a wooden broom handle", ("flower_shop",)),
    "aunt": Helper("aunt", "Aunt Celia", "aunt", "her folded umbrella", ("flower_shop",)),
    "janitor": Helper("janitor", "Ms. Deena", "janitor", "a grabber stick", ("laundromat",)),
    "grandpa": Helper("grandpa", "Grandpa", "grandparent", "the hooked handle of his cane", ("laundromat",)),
}


def clue_phrase(clue: FloatClue) -> str:
    return f"{clue.article} {clue.color} {clue.name}"


def indefinite_article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def sentence_continue(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def anchor_cause(clue: FloatClue, anchor: Anchor) -> str:
    if anchor.key == "drain_grate":
        return (
            f"The {clue.name} had snagged in one corner of the grate, "
            "so each little breeze pulled it up and let it slap back down."
        )
    if anchor.key == "signpost":
        return (
            f"The {clue.name} was wrapped around the loose metal edge of the sign, "
            "and every gust made it pat the pole again."
        )
    return (
        f"The {clue.name} had hooked under a scooter bell on the rack, "
        "and the wind kept tugging the bell just enough to make it ring."
    )


def short_mystery_result(clue: FloatClue, anchor: Anchor) -> str:
    if anchor.key == "drain_grate":
        return f"The answer was {clue_phrase(clue)} caught {anchor.place_phrase}, where the breeze kept pulling it up and dropping it back."
    if anchor.key == "signpost":
        return f"The answer was {clue_phrase(clue)} caught {anchor.place_phrase}, where the breeze kept patting it against the pole."
    return f"The answer was {clue_phrase(clue)} caught {anchor.place_phrase}, where the breeze kept tugging a little bell on the rack."


def helper_action(child: ChildProfile, helper: Helper, clue: FloatClue) -> str:
    if helper.key == "mom":
        return (
            f"Mom steadied the bag with one hand and used {helper.tool} to pull the {clue.name} close. "
            f"{child.name} caught it before the breeze could lift it again."
        )
    if helper.key == "clerk":
        return (
            f"Mr. Bell stepped out with {helper.tool}, pinched the {clue.name}, "
            f"and held it still while {child.name} freed the last trapped corner."
        )
    if helper.key == "owner":
        return (
            f"Ms. Pru leaned out the shop door with {helper.tool}, nudged the {clue.name} down, "
            f"and {child.name} tucked it into the trash before it could float off again."
        )
    if helper.key == "aunt":
        return (
            f"Aunt Celia hooked {helper.tool} around the {clue.name}, "
            f"and {child.name} giggled softly when it slid into {child.possessive} waiting hands."
        )
    if helper.key == "janitor":
        return (
            f"Ms. Deena reached over with {helper.tool}, held the {clue.name} still, "
            f"and let {child.name} unwind it neatly without scraping the metal."
        )
    return (
        f"Grandpa tipped out {helper.tool}, lifted the {clue.name} just a little, "
        f"and {child.name} slipped it free with steady fingers."
    )


def closing_image(world: ParkingLotWorld) -> str:
    child = CHILDREN[world.params.child]
    venue = VENUES[world.params.venue]
    anchor = ANCHORS[world.params.anchor]
    clue = FLOAT_CLUES[world.params.float_clue]
    return (
        f"On the walk back to the car, {child.name} glanced over one more time. "
        f"{anchor.quiet_image} The {clue.name} {clue.resting_line}, and {venue.ending_image}. "
        f"{child.name} liked how a noisy puzzle could end with such an ordinary, calm picture."
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
    child = CHILDREN[world.params.child]
    venue = VENUES[world.params.venue]
    anchor = ANCHORS[world.params.anchor]
    clue = FLOAT_CLUES[world.params.float_clue]
    return [
        f"Write a slice-of-life story set in the parking lot outside {venue.business}.",
        f"Let {child.name}, {indefinite_article(child.trait)} {child.trait} child, hear {anchor.sound_effect} and solve the mystery by following {clue_phrase(clue)} when it starts to float.",
        "End with a concrete quiet image that proves the parking lot changed after the source of the sound was fixed.",
    ]


def story_qa(world: ParkingLotWorld) -> list[tuple[str, str]]:
    child = CHILDREN[world.params.child]
    anchor = ANCHORS[world.params.anchor]
    clue = FLOAT_CLUES[world.params.float_clue]
    helper = HELPERS[world.params.helper]
    return [
        (
            f"What mystery did {child.name} solve in the parking lot?",
            (
                f"{child.name} solved the mystery of what was making the {anchor.sound_effect} noise in the parking lot. "
                f"{short_mystery_result(clue, anchor)}"
            ),
        ),
        (
            f"Why did the sound keep happening {anchor.place_phrase}?",
            (
                f"It kept happening because the breeze kept pulling on the trapped {clue.name}. "
                f"{anchor_cause(clue, anchor)}"
            ),
        ),
        (
            f"How did {helper.name} help finish the problem?",
            (
                f"{helper.name} used {helper.tool} so the snag could be reached without anyone climbing or stretching too far. "
                f"That careful help let {child.name} free the {clue.name} and make the parking lot quiet again."
            ),
        ),
    ]


def world_knowledge_qa(world: ParkingLotWorld) -> list[tuple[str, str]]:
    venue = VENUES[world.params.venue]
    anchor = ANCHORS[world.params.anchor]
    clue = FLOAT_CLUES[world.params.float_clue]
    return [
        (
            "Where does this story happen?",
            (
                f"It happens in the parking lot outside {venue.business}. "
                "The setting stays ordinary on purpose, so the mystery grows out of a real errand instead of magic."
            ),
        ),
        (
            f"Why was {clue_phrase(clue)} a useful clue?",
            (
                f"It was useful because it could float and flutter whenever the breeze moved through the lot. "
                f"That motion pointed straight toward the place {anchor.place_phrase}, where the sound was really coming from."
            ),
        ),
        (
            "What changed by the end of the story?",
            (
                "The parking lot changed from a puzzling, noisy place into a calm one again. "
                f"Once the {clue.name} was freed, the {anchor.sound_effect} stopped and the ordinary afternoon could continue."
            ),
        ),
    ]


def make_world(params: StoryParams) -> ParkingLotWorld:
    child = CHILDREN[params.child]
    helper = HELPERS[params.helper]
    venue = VENUES[params.venue]
    clue = FLOAT_CLUES[params.float_clue]
    anchor = ANCHORS[params.anchor]
    world = ParkingLotWorld(params=params)
    world.add_entity(
        Entity(
            "child",
            child.name,
            "child",
            meters={"height_m": 1.28, "steps_m": 0.0},
            memes={"Calm": 2, "Curiosity": 2, "Care": 1},
            state={"trait": child.trait},
        )
    )
    world.add_entity(
        Entity(
            "helper",
            helper.name,
            helper.role,
            meters={"reach_m": 1.75},
            memes={"Care": 2, "Patience": 2},
            state={"tool": helper.tool},
        )
    )
    world.add_entity(
        Entity(
            "lot",
            f"the parking lot outside {venue.business}",
            "place",
            meters={"quiet_level": 0.0, "wind_mps": 1.8},
            memes={"Routine": 3, "Mystery": 0},
            state={"venue": venue.key},
        )
    )
    world.add_entity(
        Entity(
            "clue",
            clue_phrase(clue),
            "floating clue",
            meters={"height_m": clue.height_m, "tension": 0.0},
            memes={"Lightness": 2, "Nuisance": 1},
            state={"texture": clue.texture, "free": False},
        )
    )
    world.add_entity(
        Entity(
            "anchor",
            anchor.name,
            "sound source",
            meters={"noise": 0.0},
            memes={"Noise": 2},
            state={"place": anchor.place_phrase, "sound": anchor.sound_effect},
        )
    )
    world.facts.update(
        {
            "business": venue.business,
            "sound_effect": anchor.sound_effect,
            "clue_phrase": clue_phrase(clue),
            "cause_sentence": anchor_cause(clue, anchor),
        }
    )
    return world


def arrive(world: ParkingLotWorld) -> None:
    child = CHILDREN[world.params.child]
    venue = VENUES[world.params.venue]
    world.meters["calm"] = 1.0
    world.entities["lot"].meters["quiet_level"] = 1.0
    world.record(
        "arrival",
        "beginning",
        "child",
        f"{child.name} stepped into the parking lot {venue.errand}.",
    )


def hear_sound(world: ParkingLotWorld) -> None:
    child = CHILDREN[world.params.child]
    anchor = ANCHORS[world.params.anchor]
    world.meters["mystery"] = 2.0
    world.meters["breeze"] = 1.5
    world.meters["attention"] = 1.0
    world.entities["lot"].memes["Mystery"] = 2
    world.entities["anchor"].meters["noise"] = 1.2
    world.entities["child"].memes["Curiosity"] += 1
    world.record(
        "sound",
        "tension",
        "anchor",
        f"{anchor.sound_line} {child.name} paused with one sneaker half turned toward the car.",
        "child",
    )


def follow_float(world: ParkingLotWorld) -> None:
    child = CHILDREN[world.params.child]
    anchor = ANCHORS[world.params.anchor]
    clue = FLOAT_CLUES[world.params.float_clue]
    world.entities["child"].meters["steps_m"] += 5.0
    world.entities["clue"].meters["tension"] = 1.0
    world.record(
        "clue",
        "turn",
        "clue",
        f"{sentence_start(clue_phrase(clue))} {clue.float_line} {anchor.place_phrase}, and {child.name} followed it instead of guessing from far away.",
        "anchor",
    )


def inspect_cause(world: ParkingLotWorld) -> None:
    child = CHILDREN[world.params.child]
    world.entities["child"].memes["Curiosity"] += 1
    world.entities["child"].memes["Care"] += 1
    world.entities["child"].memes["Calm"] -= 1
    world.record(
        "inspect",
        "turn",
        "child",
        f"{child.name} crouched down and found the answer at last. {world.facts['cause_sentence']}",
        "anchor",
    )


def solve(world: ParkingLotWorld) -> None:
    helper = HELPERS[world.params.helper]
    child = CHILDREN[world.params.child]
    clue = FLOAT_CLUES[world.params.float_clue]
    world.entities["clue"].state["free"] = True
    world.entities["clue"].meters["tension"] = 0.0
    world.entities["anchor"].meters["noise"] = 0.0
    world.entities["lot"].meters["quiet_level"] = 3.0
    world.entities["child"].memes["Calm"] += 2
    world.entities["helper"].memes["Care"] += 1
    world.meters["mystery"] = 0.0
    world.meters["calm"] = 3.0
    world.meters["relief"] = 2.0
    world.record(
        "solve",
        "resolution",
        "helper",
        helper_action(child, helper, clue),
        "clue",
    )


def settle(world: ParkingLotWorld) -> None:
    world.record(
        "ending",
        "ending",
        "lot",
        closing_image(world),
        "child",
    )


def render_story(world: ParkingLotWorld) -> str:
    child = CHILDREN[world.params.child]
    venue = VENUES[world.params.venue]
    anchor = ANCHORS[world.params.anchor]
    helper = HELPERS[world.params.helper]
    clue = FLOAT_CLUES[world.params.float_clue]
    opening = (
        f"{child.name} was in the parking lot {venue.errand}. "
        f"{venue.lot_image} Then {sentence_continue(anchor.sound_line)}"
    )
    middle = (
        f"{child.name} listened twice because the sound did not belong to engines or doors. "
        f"{sentence_start(clue_phrase(clue))} {clue.float_line} {anchor.place_phrase}, as if it were showing the way. "
        f"Because {child.subject} was a {child.trait} child, {child.name} kept watching until curiosity carried {child.object} closer instead of away."
    )
    turn = (
        f"When {child.subject} bent down beside the noise, the mystery became simple and real. "
        f"{world.facts['cause_sentence']} What had seemed strange was only a small problem waiting for someone to notice it."
    )
    resolution = (
        f"{helper_action(child, helper, clue)} "
        f"The {anchor.sound_effect} stopped right away, and the whole parking lot seemed to breathe out."
    )
    ending = closing_image(world)
    return " ".join([opening, middle, turn, resolution, ending])


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.venue not in VENUES:
        return False, f"unknown venue: {params.venue}"
    if params.float_clue not in FLOAT_CLUES:
        return False, f"unknown float clue: {params.float_clue}"
    if params.anchor not in ANCHORS:
        return False, f"unknown anchor: {params.anchor}"
    if params.helper not in HELPERS:
        return False, f"unknown helper: {params.helper}"
    if params.child not in CHILDREN:
        return False, f"unknown child: {params.child}"
    venue = VENUES[params.venue]
    clue = FLOAT_CLUES[params.float_clue]
    anchor = ANCHORS[params.anchor]
    helper = HELPERS[params.helper]
    if params.anchor not in venue.anchor_keys:
        return False, f"{anchor.name} does not belong in the parking lot outside {venue.business}"
    if params.helper not in venue.helper_keys:
        return False, f"{helper.name} would not plausibly be around {venue.business}"
    if params.anchor not in clue.anchor_keys:
        return False, f"{clue_phrase(clue)} cannot plausibly snag on the {anchor.name}"
    if params.venue not in anchor.venue_keys:
        return False, f"{anchor.name} does not fit the chosen parking lot"
    if params.venue not in helper.venue_keys:
        return False, f"{helper.name} does not fit the chosen venue"
    return True, ""


def structural_valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue in VENUES:
        for clue in FLOAT_CLUES:
            for anchor in ANCHORS:
                for helper in HELPERS:
                    probe = StoryParams(venue, clue, anchor, helper, child="nora")
                    ok, _ = valid_params(probe)
                    if ok:
                        combos.append((venue, clue, anchor, helper))
    return sorted(combos)


def all_params() -> list[StoryParams]:
    items: list[StoryParams] = []
    seed = 1
    for venue, clue, anchor, helper in structural_valid_combos():
        for child in CHILDREN:
            items.append(StoryParams(venue, clue, anchor, helper, child, seed=seed))
            seed += 1
    return items


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    arrive(world)
    hear_sound(world)
    follow_float(world)
    inspect_cause(world)
    solve(world)
    settle(world)
    return StorySample(
        params=params,
        story=render_story(world),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
venue(V) :- venue_fact(V).
float_clue(F) :- float_fact(F).
anchor(A) :- anchor_fact(A).
helper(H) :- helper_fact(H).

combo(V,F,A,H) :-
    venue(V), float_clue(F), anchor(A), helper(H),
    venue_anchor(V,A),
    clue_anchor(F,A),
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
    for clue in FLOAT_CLUES.values():
        rows.append(asp.fact("float_fact", clue.key))
        rows.extend(asp.fact("clue_anchor", clue.key, anchor) for anchor in clue.anchor_keys)
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

    child_keys = sorted(CHILDREN)
    for index, combo in enumerate(sorted(python_set), start=1):
        child = child_keys[index % len(child_keys)]
        sample = generate(StoryParams(*combo, child=child, seed=index))
        story_lower = sample.story.lower()
        if "parking lot" not in story_lower:
            print("verify failed: story lost parking-lot setting for", combo)
            failed = True
        if "float" not in story_lower:
            print("verify failed: story lost required word 'float' for", combo)
            failed = True
        if len(sample.story_qa) != 3 or len(sample.world_qa) != 3:
            print("verify failed: QA count mismatch for", combo)
            failed = True
        if any(len(item.answer.split()) < 12 for item in sample.story_qa + sample.world_qa):
            print("verify failed: short QA answer for", combo)
            failed = True
        if sample.story.count("  ") > 0:
            print("verify failed: doubled whitespace for", combo)
            failed = True
    if failed:
        return 1
    print(f"OK: clingo gate matches Python ({len(python_set)} combos), and generated samples passed sanity checks.")
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
    parser.add_argument("--float-clue", dest="float_clue", choices=sorted(FLOAT_CLUES))
    parser.add_argument("--anchor", choices=sorted(ANCHORS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--child", choices=sorted(CHILDREN))
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
        and (args.float_clue is None or combo[1] == args.float_clue)
        and (args.anchor is None or combo[2] == args.anchor)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError(
            "No reasonable parking-lot mystery fits that combination of venue, floating clue, anchor, and helper."
        )
    venue, clue, anchor, helper = rng.choice(sorted(combos))
    child = args.child or rng.choice(sorted(CHILDREN))
    seed = (args.seed or 1000) + index
    return StoryParams(venue, clue, anchor, helper, child, seed=seed)


def sample_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for index, params in enumerate(all_params(), start=1):
        child = args.child or params.child
        sample_params = StoryParams(
            params.venue,
            params.float_clue,
            params.anchor,
            params.helper,
            child,
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
            samples = sample_all(args)
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
                header = f"### {p.venue} / {p.float_clue} / {p.anchor} / {p.helper} / {p.child}"
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
