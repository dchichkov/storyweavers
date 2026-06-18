#!/usr/bin/env python3
"""
harbor_search.py
================

Seed-inspired standalone sketch:

    Words: shell, whistle, lantern
    Features: Search, Problem Solving, Kindness
    Style: Adventure

A child loses a loved object near the harbor. The clue is remembered, and a safe
method is needed for the exact place so a calm search can succeed.
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
class District:
    key: str
    phrase: str
    supported_spots: tuple[str, ...]
    atmosphere: str


@dataclass(frozen=True)
class LostItem:
    key: str
    phrase: str
    material: str
    water_safe: bool
    loved_for: str


@dataclass(frozen=True)
class SearchSpot:
    key: str
    phrase: str
    need: str
    clue: str
    memory: str
    hazard: str = "crowd"


@dataclass(frozen=True)
class SearchMethod:
    key: str
    phrase: str
    action: str
    solves: tuple[str, ...]
    unsafe: bool = False


@dataclass
class StoryParams:
    district: str
    lost_item: str
    spot: str
    method: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    notes: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    district: District
    lost_item: LostItem
    spot: SearchSpot
    method: SearchMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)
    story: str = ""

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for name, ent in self.entities.items():
            info = ", ".join(f"{k}={v}" for k, v in sorted(ent.notes.items()))
            lines.append(f"  {name}: {ent.kind} ({info})")
        if self.facts:
            lines.append(f"  facts: {self.facts}")
        lines.append(f"  fired: {self.fired}")
        return "\n".join(lines)


DISTRICTS: dict[str, District] = {
    "harbor": District(
        "harbor",
        "the harbor boardwalk",
        ("buoy_ring", "ship_ledge", "net_tuck", "watch_tower"),
        "salt wind, gulls, and rope sounds",
    ),
    "pier": District(
        "pier",
        "the busy pier",
        ("ticket_shelf", "rope_net", "ladder_step", "cargo_crate"),
        "hard wood underfoot and a chorus of footsteps",
    ),
    "boat_shop": District(
        "boat_shop",
        "the old boat shop lane",
        ("boat_calm", "oil_barrel", "dock_toolbox", "rope_spool"),
        "metal clanks, cool shadows, and stacked nets",
    ),
}

LOST_ITEMS: dict[str, LostItem] = {
    "whistle": LostItem("whistle", "tiny silver whistle", "tin", True, "the harbor song contest"),
    "shell": LostItem("shell", "small spiral shell", "shell", True, "its pretty swirl pattern"),
    "note": LostItem("note", "folded paper note", "paper", True, "the secret harbor map"),
    "lantern": LostItem("lantern", "mini teal lantern", "glass", False, "the night walk home"),
}

SPOTS: dict[str, SearchSpot] = {
    "buoy_ring": SearchSpot(
        "buoy_ring",
        "inside a buoy rope ring",
        "reach",
        "a faint hollow click from the rope ring",
        "the item had slid when the rope shifted under wind",
        "wind",
    ),
    "ship_ledge": SearchSpot(
        "ship_ledge",
        "under the old ship ledge",
        "dark",
        "a warm glimmer from behind the dark edge",
        "the last light caught there when the sea breeze blew",
        "dark",
    ),
    "net_tuck": SearchSpot(
        "net_tuck",
        "inside a crammed fishing net",
        "open",
        "a wet creak and a tiny rattle of beads",
        "the object bounced into a tight fold while someone pulled the net",
        "water",
    ),
    "watch_tower": SearchSpot(
        "watch_tower",
        "behind the watch tower stairs",
        "height",
        "a whispery scrape from high above",
        "a high wind made the tower doors shake and lift an edge",
        "height",
    ),
    "ticket_shelf": SearchSpot(
        "ticket_shelf",
        "behind the ticket shelf",
        "key",
        "a little key rattle and then a short silence",
        "a hand brushed by fast and the item slipped behind the shelf",
        "locked",
    ),
    "rope_net": SearchSpot(
        "rope_net",
        "inside a loose coiled rope",
        "net",
        "a rough tug along braided rope",
        "the old rope had shifted and held the object briefly",
        "slip",
    ),
    "ladder_step": SearchSpot(
        "ladder_step",
        "under a ladder step",
        "reach",
        "a small knock followed by a heavy pause",
        "a sudden step shifted and pushed the object into shadow",
        "height",
    ),
    "cargo_crate": SearchSpot(
        "cargo_crate",
        "under a cargo crate",
        "key",
        "a box latch clicking shut",
        "someone closed the crate while turning to wave",
        "locked",
    ),
    "boat_calm": SearchSpot(
        "boat_calm",
        "in a calm rowboat corner",
        "reach",
        "a gentle clunk, like a dropped bead",
        "the boat bobbed and the item rolled toward the gunwale",
        "water",
    ),
    "oil_barrel": SearchSpot(
        "oil_barrel",
        "near a paint-marked oil barrel",
        "ask",
        "a soft voice saying where they had seen a small thing",
        "an adult nearby heard and pointed the exact shadow",
        "crowd",
    ),
    "dock_toolbox": SearchSpot(
        "dock_toolbox",
        "inside a dock toolbox",
        "key",
        "a quiet clunk from a locked steel box",
        "a helper had opened it a moment earlier and closed it fast",
        "locked",
    ),
    "rope_spool": SearchSpot(
        "rope_spool",
        "inside a rope spool basket",
        "net",
        "the scrape of rope over rope",
        "the spool had rolled and trapped a small object briefly",
        "slip",
    ),
}

METHODS: dict[str, SearchMethod] = {
    "steady_reach": SearchMethod(
        "steady_reach",
        "a steady reach",
        "made a careful reach into the hidden place",
        ("reach",),
    ),
    "ask_guard": SearchMethod(
        "ask_guard",
        "an adult helper",
        "asked a harbor helper to check it gently",
        ("ask", "key"),
    ),
    "torch_search": SearchMethod(
        "torch_search",
        "a small torch",
        "lit a small torch and moved slowly through the shadows",
        ("dark",),
    ),
    "lock_respect": SearchMethod(
        "lock_respect",
        "a careful key request",
        "asked for the right key and opened the lid only when told",
        ("key",),
    ),
    "net_slide": SearchMethod(
        "net_slide",
        "a net-scoop",
        "used a net-scoop to check the rope folds without pulling",
        ("net",),
    ),
    "tall_hand": SearchMethod(
        "tall_hand",
        "a safe adult hand on the ladder",
        "climbed with one steady adult hold",
        ("height",),
    ),
    "risky_rush": SearchMethod(
        "risky_rush",
        "a rushed dash",
        "ran back and forth through the area",
        ("ask", "reach", "key", "dark", "height", "net"),
        unsafe=True,
    ),
}

HERO_NAMES = {
    "girl": ("Mina", "Lara", "Nora", "Ivy", "Sana"),
    "boy": ("Kai", "Noah", "Luis", "Leo", "Theo"),
}

HELPERS = ("captain", "uncle", "dock_guard", "mother", "sailor")


HUMAN_QUESTIONS = {
    "whistle": [
        ("Why can wind and water matter for a whistle?", "A silver whistle can get wet or rust over time if it is left in heavy spray."),
    ],
    "lantern": [
        ("Why can glass lanterns be risky near water?", "A glass lantern can break or lose light quickly when dropped or wet."),
    ],
    "note": [
        ("Why should papers be kept away from water?", "Paper softens and fades when wet, making the writing hard to read."),
    ],
    "shell": [
        ("Why do shells disappear when moving through crowd?", "Small objects slip between gear and cloth quickly, especially when people jostle."),
    ],
}


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return "he", "his", "him"
    return "she", "her", "her"


def helper_phrase(helper: str) -> str:
    words = helper.replace("_", " ")
    family = {"mother", "uncle"}
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

def explain_rejection(district: str, lost_item: str, spot: str, method: str) -> str:
    if district not in DISTRICTS:
        return f"No story: unknown district {district!r}."
    if lost_item not in LOST_ITEMS:
        return f"No story: unknown lost item {lost_item!r}."
    if spot not in SPOTS:
        return f"No story: unknown spot {spot!r}."
    if method not in METHODS:
        return f"No story: unknown method {method!r}."
    if METHODS[method].unsafe:
        return "No story: this method is unsafe for this setup."
    if spot not in DISTRICTS[district].supported_spots:
        return f"No story: {SPOTS[spot].phrase} is not in {DISTRICTS[district].phrase}."
    if SPOTS[spot].need not in METHODS[method].solves:
        return f"No story: {METHODS[method].phrase} does not match a {SPOTS[spot].need} search there."
    if SPOTS[spot].hazard == "water" and not LOST_ITEMS[lost_item].water_safe:
        return f"No story: a {LOST_ITEMS[lost_item].material} object would be at risk near water."
    return "No story: this setup is not a reasonable harbor-precise search."


def _valid_combo(district: str, lost_item: str, spot: str, method: str) -> bool:
    if district not in DISTRICTS or lost_item not in LOST_ITEMS or spot not in SPOTS or method not in METHODS:
        return False
    if METHODS[method].unsafe:
        return False
    if spot not in DISTRICTS[district].supported_spots:
        return False
    if SPOTS[spot].need not in METHODS[method].solves:
        return False
    if SPOTS[spot].hazard == "water" and not LOST_ITEMS[lost_item].water_safe:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for district in DISTRICTS:
        for lost_item in LOST_ITEMS:
            for spot in SPOTS:
                for method in METHODS:
                    if _valid_combo(district, lost_item, spot, method):
                        combos.append((district, lost_item, spot, method))
    return combos


def build_world(params: StoryParams) -> World:
    if not _valid_combo(params.district, params.lost_item, params.spot, params.method):
        raise StoryError(explain_rejection(params.district, params.lost_item, params.spot, params.method))
    return World(
        params=params,
        district=DISTRICTS[params.district],
        lost_item=LOST_ITEMS[params.lost_item],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
    )


def _apply_rules(world: World) -> None:
    world.entities["Hero"] = Entity(world.params.hero, "child", {
        "name": world.params.hero,
        "gender": world.params.gender,
        "object": world.lost_item.key,
    })
    world.entities["Object"] = Entity("lost item", "thing", {
        "label": world.lost_item.phrase,
        "material": world.lost_item.material,
        "location": world.spot.key,
    })
    world.entities["Spot"] = Entity("spot", "place", {
        "label": world.spot.phrase,
        "hazard": world.spot.hazard,
        "need": world.spot.need,
    })
    world.entities["District"] = Entity("district", "place", {
        "label": world.district.phrase,
        "atmosphere": world.district.atmosphere,
    })
    world.entities["Helper"] = Entity(world.params.helper, "person", {"role": "helper"})

    world.fired.append(f"noticed:{world.spot.key}")
    world.facts["clue"] = world.spot.clue
    world.facts["memory"] = world.spot.memory
    world.facts["atmosphere"] = world.district.atmosphere
    world.facts["method"] = world.method.phrase
    world.facts["hazard"] = world.spot.hazard
    world.facts["need"] = world.spot.need
    world.facts["found"] = True

    if world.spot.hazard in {"water", "wind", "height", "locked", "dark", "slip"}:
        world.facts["hazard_warning"] = {
            "water": "water can make small objects drift and footing uncertain",
            "wind": "strong wind shifts rope and shadows quickly",
            "height": "height increases the risk of dropping things too far",
            "locked": "locked spots require permission and patience",
            "dark": "dark corners hide edges and hidden gaps",
            "slip": "slippery or loose surfaces can pull you off balance",
        }[world.spot.hazard]


def predict_risk(world: World) -> str:
    if world.spot.hazard == "water":
        return "The harbor water nearby could pull the thing from the hand and make the footing unsafe."
    if world.spot.hazard == "wind":
        return "A gust could move the rope and shift the object while searching."
    if world.spot.hazard == "height":
        return "Looking up and leaning can make a child unsteady around hard edges."
    if world.spot.hazard == "locked":
        return "A locked place can frustrate a careful child and require a patient adult helper."
    if world.spot.hazard == "dark":
        return "Low light makes it harder to tell where the small object moved."
    if world.spot.hazard == "slip":
        return "Loose rope and slick surfaces can make every step risky."
    return "Crowds and movement make the scene look different every moment."


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    _apply_rules(world)
    spot_location = spot_where(world.spot.phrase)

    subject, poss, _ = _pronouns(params.gender)
    other = helper_phrase(world.params.helper)
    hero = params.hero
    item = world.lost_item.phrase
    method = world.method.phrase

    para1 = [
        f"{hero} loved the {item} for {world.lost_item.loved_for} and always kept it close. "
        f"On a bright morning, {hero} and {other} were by {world.district.phrase}.",
        f"The air smelled like {world.district.atmosphere}. It was one of {hero}'s favorite places.",
    ]

    para2 = [
        f"Then, while walking past {world.spot.phrase}, {hero} felt the weight of an absence. "
        f"{hero} had lost the {item}. {hero} remembered: {world.spot.clue}.",
        f"{subject.capitalize()} took a breath, because {world.spot.hazard} spots are tricky and a child can't solve them with hurry.",
        f'"We can do this safely," said {other}. "Use the right method for this place." {hero} nodded.',
    ]

    para3 = [
        f"So {hero} and {other} searched with {method}. {hero} {world.method.action}.",
        f"{predict_risk(world)} {subject.capitalize()} kept a calm pace and checked each place slowly.",
        f"In the end, the {item} was found {spot_location}, and everyone smiled.",
        f'"I should remember to slow down first," {hero} said. "And I should match the method to the place."',
    ]

    world.story = "\n\n".join([" ".join(para1), " ".join(para2), " ".join(para3)])
    world.facts.update(
        resolved=True,
        method=method,
        hero=hero,
        helper=other,
        subject=subject,
        pronoun_possessive=poss,
    )

    prompts = [
        f'Write a harbor search story using the words "shell", "whistle", and "lantern".',
        f'Create a calm puzzle where {hero} loses a {item} and uses a fitting method in {world.district.phrase}.',
        "Show why matching the search method to the spot's need keeps the child safe and successful.",
    ]

    qas = [
        QAItem(f"What did {hero} lose?", f"{hero} lost the {world.lost_item.phrase}."),
        QAItem("Where did the search take place?", f"The search took place in {world.district.phrase}."),
        QAItem(
            "Why was the method needed?",
            sentence(world.facts.get("hazard_warning", f"The {world.spot.hazard} made a careful method necessary.")) + " "
            f"That is why {hero} needed a {world.spot.need}-style approach instead of rushing."
        ),
        QAItem("How was the problem solved?", f"{hero} used {method} with {other}, then found the {world.lost_item.phrase} {spot_location}."),
    ]

    qas_world: list[QAItem] = [
        QAItem("Why can crowded places make searching hard?", "Crowds can hide small clues and move small objects quickly."),
        QAItem("Why do adults help in height or locked spots?", "Adults can add caution, permission, and a stable plan when reaching or opening is needed."),
    ]
    qas_world.append(
        QAItem(f"What is one risk of {world.spot.hazard} in search scenes?", sentence(world.facts["hazard_warning"]))
    )
    qas_world.extend(QAItem(q, a) for q, a in HUMAN_QUESTIONS.get(params.lost_item, []))

    return StorySample(
        params=params,
        story=world.story,
        prompts=prompts,
        story_qa=qas,
        world_qa=qas_world,
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
        print("")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Harbor search world sketch.")
    ap.add_argument("--district", choices=sorted(DISTRICTS))
    ap.add_argument("--lost-item", dest="lost_item", choices=sorted(LOST_ITEMS))
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
    ap.add_argument("--asp", action="store_true", help="list gate-valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="assert ASP and Python gates match")
    ap.add_argument("--show-asp", action="store_true", help="print ASP facts + rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [combo for combo in valid_combos()
              if (args.district is None or combo[0] == args.district)
              and (args.lost_item is None or combo[1] == args.lost_item)
              and (args.spot is None or combo[2] == args.spot)
              and (args.method is None or combo[3] == args.method)]
    if not combos:
        raise StoryError(explain_rejection(
            args.district or "harbor",
            args.lost_item or "whistle",
            args.spot or "buoy_ring",
            args.method or "steady_reach",
        ))

    district, lost_item, spot, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(district, lost_item, spot, method, hero, gender, helper, seed=None)


ASP_RULES = r"""
% District-specific spot placement.
district_spot(D,S) :- district(D), supports(D,S).

% Unsafe methods are rejected.
combo(D,I,S,M) :-
    district(D),
    lost_object(I),
    spot(S),
    method(M),
    district_spot(D,S),
    spot_need(S,N),
    method_solves(M,N),
    not method_unsafe(M),
    not water_bad(I,S).

water_bad(I,S) :- lost_object(I), spot_hazard(S,water), not water_safe(I).

#show combo/4.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for district in DISTRICTS.values():
        rows.append(asp.fact("district", district.key))
        for spot in district.supported_spots:
            rows.append(asp.fact("supports", district.key, spot))
    for key, obj in LOST_ITEMS.items():
        rows.append(asp.fact("lost_object", key))
        if obj.water_safe:
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
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("ASP/Python mismatch:")
    if py - asp_set:
        print(f"  only in python: {sorted(py - asp_set)}")
    if asp_set - py:
        print(f"  only in asp: {sorted(asp_set - py)}")
    return 1


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < args.n * 20:
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < args.n:
        raise StoryError("Could not produce enough unique stories with given constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(*combo, hero="Mina", gender="girl", helper="captain", seed=(args.seed or 7) + i)
        samples.append(generate(params))
    return samples


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
        samples = _samples_for_n(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
