#!/usr/bin/env python3
"""
clocktower_search.py
====================

Seed:

    Words: bell, candle, rope
    Features: Cautionary, Problem Solving
    Style: Mystery

A child loses a small bell at a busy clocktower district. The remembered sound becomes
the clue, and recovery only succeeds when the chosen search action matches what the
scene can safely support.
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

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Venue:
    key: str
    phrase: str
    supported_spots: tuple[str, ...]
    atmosphere: str


@dataclass(frozen=True)
class LostToken:
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
    flashback: str
    hazard: str = "dry"


@dataclass(frozen=True)
class SearchMethod:
    key: str
    phrase: str
    action: str
    solves: tuple[str, ...]
    unsafe: bool = False


@dataclass
class StoryParams:
    venue: str
    token: str
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
    tags: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)


@dataclass
class World:
    params: StoryParams
    venue: Venue
    token: LostToken
    spot: SearchSpot
    method: SearchMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for name, ent in self.entities.items():
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            meters = f" meters={ent.meters}" if ent.meters else ""
            memes = f" memes={ent.memes}" if ent.memes else ""
            suffix = f" {tags}" if tags else ""
            rows.append(f"  {name:<9} ({ent.kind:<11}){suffix}{meters}{memes}")
        fact_text = ", ".join(f"{k}={v}" for k, v in sorted(self.facts.items()))
        rows.append(f"  facts: {fact_text}")
        rows.append(f"  fired rules: {self.fired}")
        return "\n".join(rows)


VENUES: dict[str, Venue] = {
    "clocktower": Venue(
        "clocktower",
        "the old clocktower square",
        ("rope_ring", "rope_box", "bell_balcony", "copper_stairs"),
        "ringing bells, warm lantern light, and fast footsteps",
    ),
    "pier": Venue(
        "pier",
        "the sea pier platform",
        ("signal_hole", "net_basket", "wind_post"),
        "salt air, gull calls, and shifting wooden planks",
    ),
    "schoolyard": Venue(
        "schoolyard",
        "the schoolyard gym hall",
        ("stage_ledge", "tool_locker", "flag_hoop"),
        "bright paint, chalk marks, and many children passing by",
    ),
    "orchard": Venue(
        "orchard",
        "the orchard lane",
        ("rope_swing", "crate_stack", "hay_bale"),
        "soft grass, tall trees, and a patient evening wind",
    ),
}


LOST_TOKENS: dict[str, LostToken] = {
    "paper_bell": LostToken("paper_bell", "paper bell", "paper", False, "the morning bell game"),
    "tin_bell": LostToken("tin_bell", "tin bell", "tin", True, "the candle parade"),
    "felt_ribbon": LostToken("felt_ribbon", "felt ribbon", "felt", False, "the bell ribbon reward"),
    "glass_bell": LostToken("glass_bell", "glass bell", "glass", False, "a quiet bedtime ceremony"),
}


SPOTS: dict[str, SearchSpot] = {
    "rope_ring": SearchSpot(
        "rope_ring",
        "behind the rope ring",
        "reach",
        "a sharp wooden clap against rope",
        "the bell had struck and bounced toward the old rope rig",
        "dry",
    ),
    "rope_box": SearchSpot(
        "rope_box",
        "inside the rope-box latch",
        "key",
        "a small key click that vanished",
        "the helper had unlocked the box before anyone noticed the bell drop",
        "locked",
    ),
    "bell_balcony": SearchSpot(
        "bell_balcony",
        "near the high clock balcony",
        "height",
        "a hollow ring rolling down from up high",
        "the bell rolled off a handrail edge as the crowd clapped",
        "height",
    ),
    "copper_stairs": SearchSpot(
        "copper_stairs",
        "under the copper stairs",
        "reach",
        "a tiny rattle from below",
        "someone stepped hard and the bell bounced into a lower shadow",
        "dry",
    ),
    "signal_hole": SearchSpot(
        "signal_hole",
        "inside the signal marker hole",
        "key",
        "a whispering click like a locked lid",
        "the hatch had been opened, then closed too fast",
        "locked",
    ),
    "net_basket": SearchSpot(
        "net_basket",
        "inside the old net basket",
        "net",
        "a soft splash-drag against coarse rope weave",
        "the basket dipped with the tide as the wind shifted",
        "water",
    ),
    "wind_post": SearchSpot(
        "wind_post",
        "beside the wind post",
        "net",
        "a rope hiss against rope",
        "a gust pulled a loop downward near the post",
        "wind",
    ),
    "stage_ledge": SearchSpot(
        "stage_ledge",
        "on the stage ledge",
        "height",
        "a gentle tap from a lantern-shifted shadow",
        "the bell rolled toward the ledge edge and sat behind a drape",
        "height",
    ),
    "tool_locker": SearchSpot(
        "tool_locker",
        "behind the tool locker",
        "key",
        "a quiet metal rattle in the dark slot",
        "the slot got open for a moment and then shut",
        "locked",
    ),
    "flag_hoop": SearchSpot(
        "flag_hoop",
        "near the flag hoop",
        "dark",
        "a weak glow blinking from the hoop ring",
        "the rope lamp nearby shifted, and the shadow moved toward the dark side",
        "dark",
    ),
    "rope_swing": SearchSpot(
        "rope_swing",
        "under the rope swing",
        "reach",
        "a hush of fabric and rope against wood",
        "the child stepped back and the rope swung over the small object",
        "dry",
    ),
    "crate_stack": SearchSpot(
        "crate_stack",
        "between two painted crates",
        "reach",
        "a soft thud inside the gap",
        "the bell was nudged by a crate edge into a narrow gap",
        "dry",
    ),
    "hay_bale": SearchSpot(
        "hay_bale",
        "inside the hay bale stack",
        "reach",
        "a muffled clink inside the hay",
        "the object dropped while everyone moved toward the lantern line",
        "dry",
    ),
}


METHODS: dict[str, SearchMethod] = {
    "careful_reach": SearchMethod(
        "careful_reach",
        "a careful reach",
        "reached slowly and slid hands under the edge",
        ("reach",),
    ),
    "borrowed_key": SearchMethod(
        "borrowed_key",
        "a borrowed key",
        "opened the place with the correct key and checked slowly",
        ("key",),
    ),
    "steady_ladder": SearchMethod(
        "steady_ladder",
        "a steady ladder",
        "stood on the ladder and reached up carefully",
        ("height",),
    ),
    "candle_light": SearchMethod(
        "candle_light",
        "a small candle-light check",
        "let the candle light guide a slow check around shadowed edges",
        ("dark",),
    ),
    "net_pull": SearchMethod(
        "net_pull",
        "a long-handled net",
        "used a net pull to check corners from a distance",
        ("net",),
    ),
    "panic_run": SearchMethod(
        "panic_run",
        "a panic run",
        "rushed through the place, touching everything quickly",
        ("reach", "key", "dark", "height", "net"),
        unsafe=True,
    ),
}


HEROES = {
    "girl": ("Mina", "Lena", "Nova", "Sasha", "Tia"),
    "boy": ("Nico", "Leo", "Kai", "Rory", "Theo"),
}

HELPERS = ("mother", "grandmother", "uncle", "older_sister", "park_guard")


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def valid_combo(venue: str, token: str, spot: str, method: str) -> bool:
    if venue not in VENUES or token not in LOST_TOKENS or spot not in SPOTS or method not in METHODS:
        return False
    v = VENUES[venue]
    t = LOST_TOKENS[token]
    s = SPOTS[spot]
    m = METHODS[method]
    if m.unsafe:
        return False
    if spot not in v.supported_spots:
        return False
    if s.need not in m.solves:
        return False
    if s.hazard == "water" and not t.water_safe:
        return False
    return True


def explain_rejection(venue: str, token: str, spot: str, method: str) -> str:
    if venue not in VENUES:
        return f"No story: unknown venue {venue!r}."
    if token not in LOST_TOKENS:
        return f"No story: unknown lost token {token!r}."
    if spot not in SPOTS:
        return f"No story: unknown search spot {spot!r}."
    if method not in METHODS:
        return f"No story: unknown method {method!r}."
    if METHODS[method].unsafe:
        return "No story: panic can make small objects and children unsafe here."
    if spot not in VENUES[venue].supported_spots:
        return f"No story: {SPOTS[spot].phrase} is not in {VENUES[venue].phrase}."
    if SPOTS[spot].need not in METHODS[method].solves:
        return f"No story: {METHODS[method].phrase} cannot solve a {SPOTS[spot].need} check for {SPOTS[spot].phrase}."
    if SPOTS[spot].hazard == "water" and not LOST_TOKENS[token].water_safe:
        return f"No story: a {LOST_TOKENS[token].material} token would be ruined by water."
    return "No story: this setup is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue in VENUES:
        for token in LOST_TOKENS:
            for spot in SPOTS:
                for method in METHODS:
                    if valid_combo(venue, token, spot, method):
                        combos.append((venue, token, spot, method))
    return combos


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.venue, params.token, params.spot, params.method):
        raise StoryError(explain_rejection(params.venue, params.token, params.spot, params.method))
    return World(
        params=params,
        venue=VENUES[params.venue],
        token=LOST_TOKENS[params.token],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
        entities={},
    )


def _rule_lost(world: World) -> None:
    hero = world.entities["Hero"]
    token = world.entities["Token"]
    hero.add_meme("searching", 1.0)
    token.add_meme("missing", 1.0)
    world.facts["problem"] = f"lost {world.token.phrase} at {world.venue.phrase}"
    world.facts["clue"] = world.spot.clue
    world.facts["flashback"] = world.spot.flashback
    world.facts["tone"] = "sudden urgency"
    world.fired.append("lost_token")


def _rule_investigate(world: World) -> None:
    hero = world.entities["Hero"]
    world.entities["Venue"].add_meter("noise", 0.6)
    world.facts["atmosphere"] = world.venue.atmosphere
    world.facts["need"] = world.spot.need
    hero.add_meme("focus", 1.1)
    world.fired.append("investigation")


def _rule_recovered(world: World) -> None:
    hero = world.entities["Hero"]
    token = world.entities["Token"]
    helper = world.entities["Helper"]
    token.add_meme("restored", 1.0)
    token.tags["status"] = "found"
    token.tags["found_at"] = world.spot.key
    helper.add_meme("helpfulness", 0.7)
    hero.add_meme("relief", 1.2)
    world.facts["method"] = world.method.phrase
    world.facts["found_by"] = world.params.helper
    world.fired.append("found_token")


def _rule_hazard_warning(world: World) -> None:
    if world.spot.hazard == "locked":
        world.facts["hazard_warning"] = "locked spaces need the right key, not force."
    elif world.spot.hazard == "height":
        world.facts["hazard_warning"] = "height can be unstable without support."
    elif world.spot.hazard == "water":
        world.facts["hazard_warning"] = "water can pull a small token out of reach fast."
    elif world.spot.hazard == "dark":
        world.facts["hazard_warning"] = "dark corners hide small objects and feet."
    else:
        world.facts["hazard_warning"] = "crowded spaces can turn a careful search into a risky one."


def apply_rules(world: World) -> None:
    hero = world.params.hero
    helper = world.params.helper.replace("_", " ").title()
    world.entities["Hero"] = Entity(hero, "child", {"mood": "worried"})
    world.entities["Token"] = Entity(world.token.phrase, "artifact", {"material": world.token.material})
    world.entities["Spot"] = Entity(world.spot.key, "place", {"clue": world.spot.clue})
    world.entities["Venue"] = Entity(world.venue.key, "place", {"atmosphere": world.venue.atmosphere})
    world.entities["Helper"] = Entity(helper, "person", {"role": "support"})
    _rule_lost(world)
    _rule_investigate(world)
    _rule_recovered(world)
    _rule_hazard_warning(world)


def predict_risk(world: World) -> str:
    if world.spot.hazard == "locked":
        return "A locked place needs a correct key and patient hands"
    if world.spot.hazard == "height":
        return "A child could lose balance without a stable step"
    if world.spot.hazard == "water":
        return "Water can tug a small object from safe reach"
    if world.spot.hazard == "dark":
        return "Dim places can hide the bell and make footing unsure"
    return "crowds and movement can hide quiet sounds and small objects"


def tokenized_flashback(world: World) -> str:
    return world.spot.flashback.replace("bell", world.token.phrase).replace("object", world.token.phrase)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    apply_rules(world)
    subject, possessive, _ = pronouns(params.gender)
    helper = params.helper.replace("_", " ").title()

    opening = (
        f"{params.hero} stood at {world.venue.phrase} as evening bells rang. "
        f"{params.hero} carried {possessive} {world.token.phrase} while {subject} kept watch on the crowd."
    )
    disappearance = (
        f"When one final tone rang, {params.hero} looked down and found the {world.token.phrase} missing. "
        f"In memory, {params.hero} heard this sound: \"{world.spot.clue}\"."
    )
    helper_line = (
        f'\"{helper},\" {params.hero} said, \"we can still find it.\" '
        f'{helper} smiled and pointed out the flashback: {tokenized_flashback(world)}.'
    )
    search = (
        f"They used {world.method.phrase}. {params.hero} {world.method.action}. "
        f"{predict_risk(world)}. {params.hero} found the {world.token.phrase} {world.spot.phrase}."
    )
    ending = (
        f"{params.hero} held {possessive} {world.token.phrase} and set it on the table. "
        f"The lesson was simple: {params.hero} learned to pause, follow clues, and match each method to the place."
    )

    sample = StorySample(
        params=params,
        story="\n\n".join([opening, disappearance, helper_line, search, ending]),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a mystery story using the words "bell", "candle", and "rope".',
        f"Create a careful-search story where {world.params.hero} loses {world.token.phrase} in {world.venue.phrase}.",
        f"Explain how {world.params.hero} found the missing item using {world.method.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What was the missing item?", f"The story says the lost item was {world.token.phrase}."),
        QAItem("What started the investigation?", f"The first clue remembered was '{world.spot.clue}'."),
        QAItem("Why was the chosen method safe?", f"The scene required a {world.spot.need} search and they used a method for that need."),
        QAItem("How was the missing item found?", f"They used {world.method.phrase}, which was suitable for {world.spot.need}, and found it {world.spot.phrase}."),
        QAItem("What did the child learn?", "The child learned that safe methods and calm planning recover things better than rushing."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    qas = [
        QAItem("Why can crowds make searching harder?", "Crowds can hide small objects and make careful movement difficult."),
        QAItem("Why is helper support useful?", "A helper can cover an angle the main searcher cannot reach and keep the search safer."),
    ]
    if world.spot.hazard == "locked":
        qas.append(QAItem("Why does a key matter in this scene?", "Locked places need the correct key so the search remains safe and controlled."))
    if world.spot.hazard == "height":
        qas.append(QAItem("Why avoid standing on unstable edges?", "Unstable edges can cause a child to lose balance."))
    if world.spot.hazard == "water":
        qas.append(QAItem("Why avoid wet corners for fragile items?", "Water can pull or damage objects that should stay dry and can shift footing."))
    if world.spot.hazard == "dark":
        qas.append(QAItem("Why did they use candle light?", "A small light helps locate objects in dark spots without forcing movement."))
    if world.token.material in ("paper", "felt", "glass"):
        qas.append(QAItem(
            "What can happen to fragile materials?",
            f"A {world.token.material} token can be damaged by wetness, pressure, or hard movement.",
        ))
    return qas


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate clocktower-search storyworld samples.")
    parser.add_argument("--venue", choices=sorted(VENUES))
    parser.add_argument("--token", choices=sorted(LOST_TOKENS))
    parser.add_argument("--spot", choices=sorted(SPOTS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    combos = []
    for combo in valid_combos():
        venue, token, spot, method = combo
        if args.venue and args.venue != venue:
            continue
        if args.token and args.token != token:
            continue
        if args.spot and args.spot != spot:
            continue
        if args.method and args.method != method:
            continue
        combos.append(combo)
    return combos


def _make_params(args: argparse.Namespace, rng: random.Random, combo: tuple[str, str, str, str], seed: int | None) -> StoryParams:
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice(HELPERS)
    venue, token, spot, method = combo
    return StoryParams(venue, token, spot, method, hero, gender, helper, seed)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = _matching_combos(args)
    if not combos:
        raise StoryError(explain_rejection(args.venue or "clocktower", args.token or "tin_bell", args.spot or "rope_ring", args.method or "careful_reach"))
    seed = getattr(rng, "story_seed", None)
    return _make_params(args, rng, rng.choice(combos), seed)


def format_qa(sample: StorySample) -> str:
    lines = ["", "== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
        print(format_qa(sample))


def _json_dump(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
    else:
        print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))


ASP_RULES = r"""
water_bad(T,S) :- lost_token(T), hazard(S,water), not water_safe(T).

combo(V,T,S,M) :-
    venue(V),
    lost_token(T),
    spot(S),
    method(M),
    venue_spot(V,S),
    need(S,N),
    solves(M,N),
    not unsafe(M),
    not water_bad(T,S).

ok :- chosen(V,T,S,M), combo(V,T,S,M).

#show combo/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    rows: list[str] = []
    for key, venue in VENUES.items():
        rows.append(asp.fact("venue", key))
        for spot in venue.supported_spots:
            rows.append(asp.fact("venue_spot", key, spot))
    for key, token in LOST_TOKENS.items():
        rows.append(asp.fact("lost_token", key))
        if token.water_safe:
            rows.append(asp.fact("water_safe", key))
    for key, spot in SPOTS.items():
        rows.append(asp.fact("spot", key))
        rows.append(asp.fact("need", key, spot.need))
        rows.append(asp.fact("hazard", key, spot.hazard))
    for key, method in METHODS.items():
        rows.append(asp.fact("method", key))
        for need in method.solves:
            rows.append(asp.fact("solves", key, need))
        if method.unsafe:
            rows.append(asp.fact("unsafe", key))
    if params is not None:
        rows.append(asp.fact("chosen", params.venue, params.token, params.spot, params.method))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    import asp
    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update(asp.atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    import asp
    return bool(asp.atoms(asp.one_model(asp_program(params)), "ok"))


def verify() -> str:
    py = set(valid_combos())
    logic = asp_valid_combos()
    if py != logic:
        raise StoryError(f"ASP/Python mismatch. only_python={sorted(py - logic)} only_asp={sorted(logic - py)}")
    for venue, token, spot, method in sorted(py):
        params = StoryParams(venue, token, spot, method, "Mina", "girl", "mother", 0)
        if not asp_verify(params):
            raise StoryError(f"ASP rejected Python-valid combo: {(venue, token, spot, method)}")
    return f"OK: clingo gate matches valid_combos() ({len(py)} combos)."


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    samples = []
    combos = valid_combos()
    for i, combo in enumerate(combos):
        seed = (args.seed if args.seed is not None else 5000) + i
        rng = random.Random(seed)
        rng.story_seed = seed
        samples.append(generate(_make_params(args, rng, combo, seed)))
    return samples


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    seen: set[str] = set()
    samples: list[StorySample] = []
    i = 0
    target = max(1, args.n)
    while len(samples) < target and i < target * 25:
        story_seed = base_seed + i
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        i += 1
    return samples


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = _samples_for_all(args) if args.all else _samples_for_n(args)
        if args.json:
            _json_dump(samples)
            return 0
        for i, sample in enumerate(samples):
            header = ""
            if args.all:
                header = f"### {sample.params.hero}: {sample.params.token} in {sample.params.venue} via {sample.params.spot}"
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if i != len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
