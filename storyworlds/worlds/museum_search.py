#!/usr/bin/env python3
"""
museum_search.py
================

Seed-inspired standalone sketch:

    Words: mask, map, lantern
    Features: Mystery, Kindness, Safety
    Style: Indoor Adventure

A child misplaces a valued object in a museum-like market and can recover it only
by matching the right search action to the place's requirement.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

STORYWORLDS = Path(__file__).resolve().parents[1]
if str(STORYWORLDS) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Venue:
    key: str
    phrase: str
    supported_spots: tuple[str, ...]
    atmosphere: str


@dataclass(frozen=True)
class LostObject:
    key: str
    phrase: str
    material: str
    water_safe: bool
    loved_for: str


@dataclass(frozen=True)
class Spot:
    key: str
    phrase: str
    need: str
    clue: str
    memory: str
    hazard: str


@dataclass(frozen=True)
class Method:
    key: str
    phrase: str
    action: str
    solves: tuple[str, ...]
    unsafe: bool = False


@dataclass
class StoryParams:
    venue: str
    lost_object: str
    spot: str
    method: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    role: str
    notes: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    venue: Venue
    lost_object: LostObject
    spot: Spot
    method: Method
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)
    story: str = ""

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for key, ent in self.entities.items():
            details = ", ".join(f"{k}={v}" for k, v in sorted(ent.notes.items()))
            lines.append(f"  {key}: {ent.role} ({details})")
        if self.facts:
            lines.append(f"  facts: {self.facts}")
        lines.append(f"  fired: {self.fired}")
        return "\n".join(lines)


VENUES: dict[str, Venue] = {
    "museum_hall": Venue(
        "museum_hall",
        "the old city museum hall",
        ("gallery_arch", "display_box", "statue_corner", "catwalk"),
        "murmur of feet, cool glass, and label cards",
    ),
    "planetarium": Venue(
        "planetarium",
        "the dome planetarium",
        ("control_ladder", "dark_seat", "ticket_board", "projection_box"),
        "soft projector hum and drifting light beams",
    ),
    "reading_room": Venue(
        "reading_room",
        "the quiet reading room",
        ("shelf_gap", "locked_cabinet", "desk_drawer", "window_niche"),
        "low voices, old paper scent, and careful footsteps",
    ),
}

LOST_OBJECTS: dict[str, LostObject] = {
    "ticket": LostObject("ticket", "mini museum ticket", "paper", True, "their favorite treasure day"),
    "mask": LostObject("mask", "paper festival mask", "paper", False, "the costume game"),
    "coin_box": LostObject("coin_box", "small puzzle coin box", "wood", False, "the treasure challenge"),
    "flash": LostObject("flash", "tiny flashlight", "plastic", True, "checking dark spots"),
}

SPOTS: dict[str, Spot] = {
    "gallery_arch": Spot(
        "gallery_arch",
        "behind a gallery arch",
        "reach",
        "a faint rustle like cloth brushing plaster",
        "the object slipped behind a frame when people passed closely",
        "crowd",
    ),
    "display_box": Spot(
        "display_box",
        "under a glass display box",
        "ask",
        "a whisper that someone had seen a small object there",
        "a helper had shifted the cardboard guard while cleaning",
        "locked",
    ),
    "statue_corner": Spot(
        "statue_corner",
        "next to a tall statue corner",
        "height",
        "a soft tap from above",
        "the statue's shadow moved as someone looked up and looked down",
        "height",
    ),
    "catwalk": Spot(
        "catwalk",
        "under a maintenance catwalk",
        "reach",
        "a thin metallic vibration",
        "a draft moved the hanging cloth toward a gap",
        "height",
    ),
    "control_ladder": Spot(
        "control_ladder",
        "near a side ladder",
        "height",
        "the gentle click of a safety strap",
        "the child reached too far once and the object fell behind the frame",
        "height",
    ),
    "dark_seat": Spot(
        "dark_seat",
        "behind dark seats",
        "dark",
        "a glow like a distant star",
        "the emergency light flickered and the object drifted into shadow",
        "dark",
    ),
    "ticket_board": Spot(
        "ticket_board",
        "behind a ticket board",
        "key",
        "a clean click like a small latch",
        "a staff member closed the board for a moment",
        "locked",
    ),
    "projection_box": Spot(
        "projection_box",
        "inside the projection box",
        "key",
        "a soft electronic chirp",
        "the box opened briefly for a test then closed",
        "locked",
    ),
    "shelf_gap": Spot(
        "shelf_gap",
        "between tall shelves",
        "reach",
        "a paper-like brush and tiny scrape",
        "the gap tightened and the paper dropped into a side slot",
        "crowd",
    ),
    "locked_cabinet": Spot(
        "locked_cabinet",
        "inside a locked cabinet",
        "key",
        "a soft key-turn whisper",
        "the cabinet stayed locked just as attention moved away",
        "locked",
    ),
    "desk_drawer": Spot(
        "desk_drawer",
        "in a top drawer",
        "ask",
        "a creaking drawer and a low assistant voice",
        "a careful attendant opened the drawer partway to help",
        "locked",
    ),
    "window_niche": Spot(
        "window_niche",
        "in a window niche",
        "dark",
        "a little glow from the stained-glass edge",
        "the object slid toward the cool window shadow",
        "dark",
    ),
}

METHODS: dict[str, Method] = {
    "careful_reach": Method(
        "careful_reach",
        "a careful reach",
        "made a gentle reach and avoided jostling shelves",
        ("reach",),
    ),
    "ask_staff": Method(
        "ask_staff",
        "a polite ask",
        "asked a staff member to check safely first",
        ("ask", "key"),
    ),
    "lantern_lens": Method(
        "lantern_lens",
        "a narrow torch beam",
        "lit a focused beam and scanned the dark edges",
        ("dark",),
    ),
    "use_key": Method(
        "use_key",
        "careful permission",
        "waited for the right person to open the lock",
        ("key",),
    ),
    "guided_step": Method(
        "guided_step",
        "an adult-guided step",
        "climbed with an adult hold and no sudden movement",
        ("height",),
    ),
    "rushed_sprint": Method(
        "rushed_sprint",
        "a rushed sprint",
        "ran quickly between displays",
        ("reach", "ask", "key", "dark", "height"),
        unsafe=True,
    ),
}

HERO_NAMES = {
    "girl": ("Maya", "Lina", "Sana", "Ivy", "Tara"),
    "boy": ("Ezio", "Noam", "Ravi", "Leo", "Nico"),
}

HELPERS = ("curator", "librarian", "guard", "parent", "older_brother")

WORLD_KNOWLEDGE = {
    "ticket": [
        QAItem("Why can paper items fail near moisture?", "Paper softens and tears when wet, so water should be avoided. A careful search protects the object as well as finding it."),
    ],
    "mask": [
        QAItem("Why can paper masks be fragile in crowds?", "Paper masks crease or tear if pulled quickly by movement. That is why the search method should avoid jostling people or displays."),
    ],
    "coin_box": [
        QAItem("Why can a small wood box be hard to recover?", "A small rigid object can fall into cracks and become hard to spot. The finder needs a method that matches the hiding place rather than a fast grab."),
    ],
    "flash": [
        QAItem("Why is good lighting useful in dark spots?", "Focused light makes small items easier to spot without feeling around blindly. It keeps the search safe because hands do not have to sweep through unknown spaces."),
    ],
}



def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return "he", "his", "him"
    return "she", "her", "her"


def helper_phrase(helper: str) -> str:
    words = helper.replace("_", " ")
    family = {"parent", "older brother"}
    if words in family:
        return words
    return f"the {words}"


def sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text += "."
    return text


def spot_where(phrase: str) -> str:
    first = phrase.split()[0]
    if first in {"inside", "under", "behind", "next", "near", "on", "in", "at", "between", "beside", "through", "within", "outside"}:
        return phrase
    return f"in {phrase}"

def explain_rejection(venue: str, lost_object: str, spot: str, method: str) -> str:
    if venue not in VENUES:
        return f"No story: unknown venue {venue!r}."
    if lost_object not in LOST_OBJECTS:
        return f"No story: unknown object {lost_object!r}."
    if spot not in SPOTS:
        return f"No story: unknown spot {spot!r}."
    if method not in METHODS:
        return f"No story: unknown method {method!r}."
    if METHODS[method].unsafe:
        return "No story: this method is unsafe for a child in this setting."
    if spot not in VENUES[venue].supported_spots:
        return f"No story: {SPOTS[spot].phrase} is not in {VENUES[venue].phrase}."
    if SPOTS[spot].need not in METHODS[method].solves:
        return f"No story: this method does not match a {SPOTS[spot].need} requirement."
    if SPOTS[spot].hazard == "water" and not LOST_OBJECTS[lost_object].water_safe:
        return "No story: this object is not safe with the spot's hazard."
    return "No story: this setup is not a reasonable museum search."


def valid_combo(venue: str, lost_object: str, spot: str, method: str) -> bool:
    if venue not in VENUES or lost_object not in LOST_OBJECTS or spot not in SPOTS or method not in METHODS:
        return False
    if METHODS[method].unsafe:
        return False
    if spot not in VENUES[venue].supported_spots:
        return False
    if SPOTS[spot].need not in METHODS[method].solves:
        return False
    if SPOTS[spot].hazard == "water" and not LOST_OBJECTS[lost_object].water_safe:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for venue_key in VENUES:
        for obj in LOST_OBJECTS:
            for spot in SPOTS:
                for method in METHODS:
                    if valid_combo(venue_key, obj, spot, method):
                        out.append((venue_key, obj, spot, method))
    return out


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.venue, params.lost_object, params.spot, params.method):
        raise StoryError(explain_rejection(params.venue, params.lost_object, params.spot, params.method))
    return World(
        params=params,
        venue=VENUES[params.venue],
        lost_object=LOST_OBJECTS[params.lost_object],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
    )


def apply_rules(world: World) -> None:
    world.entities["Hero"] = Entity(world.params.hero, "child", {
        "name": world.params.hero,
        "gender": world.params.gender,
        "goal": "retrieve object",
    })
    world.entities["Item"] = Entity(world.lost_object.phrase, "thing", {
        "material": world.lost_object.material,
        "location": world.spot.key,
    })
    world.entities["Spot"] = Entity("spot", "place", {
        "hazard": world.spot.hazard,
        "need": world.spot.need,
    })
    world.entities["Venue"] = Entity("venue", "place", {
        "label": world.venue.phrase,
        "atmosphere": world.venue.atmosphere,
    })
    world.entities["Helper"] = Entity(world.params.helper, "person", {"role": "helper"})

    world.fired.extend(("sensed_clue", "checked_spot", "found_item"))
    world.facts["clue"] = world.spot.clue
    world.facts["memory"] = world.spot.memory
    world.facts["method"] = world.method.phrase
    world.facts["hazard"] = world.spot.hazard
    world.facts["need"] = world.spot.need

    if world.spot.hazard == "locked":
        world.facts["hazard_warning"] = "locked places need permission and patience"
    elif world.spot.hazard == "height":
        world.facts["hazard_warning"] = "moving near high edges needs stable adult guidance"
    elif world.spot.hazard == "dark":
        world.facts["hazard_warning"] = "low light can hide small shapes"
    else:
        world.facts["hazard_warning"] = "quiet movement helps in crowded places"


def predict_reason(world: World) -> str:
    return {
        "crowd": "The room is crowded, so quick hands could drop things out of sight.",
        "height": "A high or raised place can cause slips if climbed without a hand.",
        "dark": "In dark spots it is easy to miss small things unless there is focused light.",
        "locked": "Some parts are locked, so asking first keeps everything safe.",
    }.get(world.spot.hazard, "The layout changes often, so care is needed.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    apply_rules(world)
    subject, poss, obj_pron = _pronouns(params.gender)
    helper = helper_phrase(params.helper)
    helper_subject = helper.capitalize()
    spot_location = spot_where(world.spot.phrase)

    child_intro = "a girl" if params.gender == "girl" else "a boy"
    story_lines = [
        f"Once upon a time, there was {child_intro} named {params.hero}.",
        f"{params.hero} treasured {poss} {world.lost_object.phrase} because it reminded {obj_pron} of {world.lost_object.loved_for}.",
        f"One visit to {world.venue.phrase}, {params.hero} noticed the room smelled of {world.venue.atmosphere}.",
    ]

    story_lines.append(
        f"Then {spot_location}, the {world.lost_object.phrase} was gone. "
        f"{subject.capitalize()} remembered: {world.spot.clue}."
    )
    story_lines.append(
        f"{subject.capitalize()} said quietly, \"Let's stay calm and do this the safe way.\" {helper_subject} agreed "
        f"and explained that {spot_location} needed a {world.spot.need} approach."
    )

    para_two = [
        f"They went slowly and used {world.method.phrase}.",
        f"{subject.capitalize()} {world.method.action}.",
        predict_reason(world),
    ]

    para_three = [
        f"In a moment, {subject} found the {world.lost_object.phrase} {spot_location}.",
        f"{helper_subject} smiled, and {params.hero} learned to match method and place, especially when things {subject} loves matter most.",
    ]

    world.story = "\n\n".join([" ".join(story_lines), " ".join(para_two), " ".join(para_three)])
    world.facts["resolved"] = True

    prompts = [
        f'Write a mystery-style story that includes the words "mask", "map", and "lantern".',
        f"Create a safe indoor search where {params.hero} misplaces a {world.lost_object.key}.",
        f"Show how a careful helper method solves a place-specific search problem.",
    ]

    story_qa = [
        QAItem(
            "What was lost?",
            f"{params.hero} lost the {world.lost_object.phrase}. It mattered because the object reminded {obj_pron} of {world.lost_object.loved_for}, so the search had emotional weight as well as a practical goal.",
        ),
        QAItem(
            "Where was the search location?",
            f"The search happened in {world.venue.phrase}, specifically {spot_location}. That spot had a {world.spot.hazard} hazard, so the scene needed more care than simply looking around.",
        ),
        QAItem(
            "Which method was used?",
            f"They used {world.method.phrase}, because the spot needed a {world.spot.need} approach. The method is grounded in the world trace as the action that can solve this kind of place-specific problem.",
        ),
        QAItem(
            "Why was this method safe?",
            f"{sentence(world.facts['hazard_warning'])} It kept the search matched to the hazard instead of letting worry turn into rushing.",
        ),
        QAItem(
            "What lesson is shown?",
            "The story shows that asking for help and using the right method for a place helps keep the search safe and calm. It also shows that caring about a lost object does not mean ignoring the room's rules.",
        ),
    ]

    world_qa = list(WORLD_KNOWLEDGE[params.lost_object])
    world_qa.append(
        QAItem("Why can a crowd make quiet work hard?", "A lot of people makes small objects harder to track and increases sudden movement. Slow, quiet searching protects both the child and the exhibits.")
    )

    return StorySample(
        params=params,
        story=world.story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story/world trace ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child-level checks ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("\n")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Museum search world sketch.")
    ap.add_argument("--venue", choices=sorted(VENUES))
    ap.add_argument("--lost-object", dest="lost_object", choices=sorted(LOST_OBJECTS))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=sorted(HERO_NAMES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    combos = [combo for combo in valid_combos()
              if (args.venue is None or combo[0] == args.venue)
              and (args.lost_object is None or combo[1] == args.lost_object)
              and (args.spot is None or combo[2] == args.spot)
              and (args.method is None or combo[3] == args.method)]
    if not combos:
        raise StoryError(explain_rejection(
            args.venue or "museum_hall",
            args.lost_object or "ticket",
            args.spot or "gallery_arch",
            args.method or "careful_reach",
        ))
    venue, lost_object, spot, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(venue, lost_object, spot, method, hero, gender, helper)


ASP_RULES = r"""
place_spot(V,S) :- venue(V), in_place(V,S).

combo(V,O,S,M) :-
  venue(V), lost_object(O), spot(S), method(M),
  place_spot(V,S), spot_need(S,N), method_solves(M,N),
  not method_unsafe(M), not water_bad(O,S).

water_bad(O,S) :- lost_object(O), spot_hazard(S,water), not water_safe(O).

#show combo/4.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for venue in VENUES.values():
        rows.append(asp.fact("venue", venue.key))
        for spot in venue.supported_spots:
            rows.append(asp.fact("in_place", venue.key, spot))
    for key, item in LOST_OBJECTS.items():
        rows.append(asp.fact("lost_object", key))
        if item.water_safe:
            rows.append(asp.fact("water_safe", key))
    for key, spot in SPOTS.items():
        rows.append(asp.fact("spot", key))
        rows.append(asp.fact("spot_need", key, spot.need))
        rows.append(asp.fact("spot_hazard", key, spot.hazard))
    for key, method in METHODS.items():
        rows.append(asp.fact("method", key))
        if method.unsafe:
            rows.append(asp.fact("method_unsafe", key))
        for need in method.solves:
            rows.append(asp.fact("method_solves", key, need))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show combo/4."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    if py == logic:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP gate")
    if py - logic:
        print(f"  only python: {sorted(py - logic)}")
    if logic - py:
        print(f"  only asp: {sorted(logic - py)}")
    return 1


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    target = max(1, args.n)
    while len(samples) < target and i < target * 25:
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique stories from current constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    out: list[StorySample] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(*combo, hero="Maya", gender="girl", helper="curator", seed=(args.seed or 17) + i)
        out.append(generate(params))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return

    if args.all:
        samples = _sample_all(args)
    else:
        samples = _sample_n(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
