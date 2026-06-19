#!/usr/bin/env python3
"""
crown_quest.py
==============

Seed:

    Words: ride, knock, crown
    Features: Quest, Flashback
    Style: Mystery

A child loses a crown on a ride. A remembered knock becomes the clue, but the
story only proceeds when the chosen search method is safe and actually matches
where the crown could be hidden.
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
class Ride:
    key: str
    phrase: str
    seats: str
    supported_spots: tuple[str, ...]
    safe_wait: str


@dataclass(frozen=True)
class Crown:
    key: str
    phrase: str
    material: str
    water_safe: bool
    loved_for: str


@dataclass(frozen=True)
class HidingSpot:
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
    ride: str
    crown: str
    spot: str
    method: str
    hero: str
    gender: str
    companion: str
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
    ride: Ride
    crown: Crown
    spot: HidingSpot
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
            rows.append(f"  {name:<9} ({ent.kind:<10}){suffix}{meters}{memes}")
        fact_text = ", ".join(f"{k}={v}" for k, v in sorted(self.facts.items()))
        rows.append(f"  facts: {fact_text}")
        rows.append(f"  fired rules: {self.fired}")
        return "\n".join(rows)


RIDES: dict[str, Ride] = {
    "carousel": Ride(
        "carousel",
        "the old carousel",
        "painted horses",
        ("under_saddle", "music_panel", "top_mirror"),
        "wait until the painted horses stop",
    ),
    "garden_train": Ride(
        "garden_train",
        "the garden train ride",
        "tiny green benches",
        ("under_bench", "ticket_box", "dark_tunnel"),
        "wait until the little train reaches the station",
    ),
    "duck_boats": Ride(
        "duck_boats",
        "the duck boat ride",
        "yellow boats",
        ("water_channel", "under_seat", "dock_bell"),
        "wait until the boat bumps the dock",
    ),
    "mini_ferris": Ride(
        "mini_ferris",
        "the little ferris wheel",
        "swinging baskets",
        ("basket_floor", "operator_booth", "top_lamp"),
        "wait until the wheel clicks still",
    ),
}

CROWNS: dict[str, Crown] = {
    "paper": Crown("paper", "gold paper crown", "paper", False, "a birthday parade"),
    "tin": Crown("tin", "tiny tin crown", "tin", True, "royal dress-up"),
    "flower": Crown("flower", "daisy crown", "flowers", True, "a garden parade"),
    "felt": Crown("felt", "soft felt crown", "felt", False, "a pretend coronation"),
}

SPOTS: dict[str, HidingSpot] = {
    "under_saddle": HidingSpot("under_saddle", "under a painted saddle", "reach", "a wooden knock", "the horse bumped once when the crown slipped"),
    "music_panel": HidingSpot("music_panel", "behind the music-box panel", "operator", "a tinny knock", "the music box clicked just after the crown vanished"),
    "top_mirror": HidingSpot("top_mirror", "near the high mirror", "height", "a bright knock", "the mirror flashed and knocked against the pole"),
    "under_bench": HidingSpot("under_bench", "under a green bench", "reach", "a bench knock", "the bench knocked when the train turned"),
    "ticket_box": HidingSpot("ticket_box", "inside the little ticket box", "key", "a small boxed knock", "the ticket lid tapped shut behind them"),
    "dark_tunnel": HidingSpot("dark_tunnel", "beside the pretend tunnel", "dark", "a cave-like knock", "the tunnel echoed when the crown rolled away"),
    "water_channel": HidingSpot("water_channel", "beside the shallow water channel", "net", "a splashy knock", "the boat knocked the crown toward the water", "water"),
    "under_seat": HidingSpot("under_seat", "under the boat seat", "reach", "a hollow knock", "the seat knocked as the crown slid below it"),
    "dock_bell": HidingSpot("dock_bell", "beside the dock bell", "height", "a bell knock", "the bell knocked softly after the boat docked"),
    "basket_floor": HidingSpot("basket_floor", "on the basket floor", "reach", "a basket knock", "the basket knocked when the wheel rocked"),
    "operator_booth": HidingSpot("operator_booth", "by the operator booth", "operator", "a window knock", "the booth window tapped as something rolled near it"),
    "top_lamp": HidingSpot("top_lamp", "near the top lamp", "height", "a glassy knock", "the lamp knocked once high above them"),
}

METHODS: dict[str, SearchMethod] = {
    "careful_reach": SearchMethod("careful_reach", "a careful reach", "knelt and reached only after everything was still", ("reach",)),
    "ask_operator": SearchMethod("ask_operator", "help from the ride operator", "asked the operator to open the safe little door", ("operator", "key")),
    "long_net": SearchMethod("long_net", "a long-handled net", "scooped slowly with a long-handled net", ("net",)),
    "flashlight": SearchMethod("flashlight", "a small flashlight", "shone a small flashlight into the shadow", ("dark",)),
    "adult_lift": SearchMethod("adult_lift", "an adult's careful lift", "let a grown-up lift the crown down", ("height",)),
    "run_after": SearchMethod("run_after", "running after the moving ride", "ran after the moving ride", ("reach", "height", "net", "dark", "operator", "key"), True),
}

HEROES = {
    "girl": ("Mira", "Lina", "Nora", "June", "Rose"),
    "boy": ("Theo", "Finn", "Sam", "Eli", "Ben"),
}

COMPANIONS = ("grandmother", "uncle", "aunt", "father", "mother")


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def valid_combo(ride: str, crown: str, spot: str, method: str) -> bool:
    if ride not in RIDES or crown not in CROWNS or spot not in SPOTS or method not in METHODS:
        return False
    r = RIDES[ride]
    c = CROWNS[crown]
    s = SPOTS[spot]
    m = METHODS[method]
    if m.unsafe:
        return False
    if spot not in r.supported_spots:
        return False
    if s.need not in m.solves:
        return False
    if s.hazard == "water" and not c.water_safe:
        return False
    return True


def explain_rejection(ride: str, crown: str, spot: str, method: str) -> str:
    if ride not in RIDES:
        return f"No story: unknown ride {ride!r}."
    if crown not in CROWNS:
        return f"No story: unknown crown {crown!r}."
    if spot not in SPOTS:
        return f"No story: unknown hiding spot {spot!r}."
    if method not in METHODS:
        return f"No story: unknown search method {method!r}."
    if METHODS[method].unsafe:
        return "No story: running after a moving ride is unsafe, so the quest must pause and use a calmer method."
    if spot not in RIDES[ride].supported_spots:
        return f"No story: {RIDES[ride].phrase} does not have {SPOTS[spot].phrase}."
    if SPOTS[spot].need not in METHODS[method].solves:
        return f"No story: {METHODS[method].phrase} cannot solve a {SPOTS[spot].need} search."
    if SPOTS[spot].hazard == "water" and not CROWNS[crown].water_safe:
        return f"No story: a {CROWNS[crown].material} crown would be ruined by the water channel."
    return "No story: the crown quest is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for ride in RIDES:
        for crown in CROWNS:
            for spot in SPOTS:
                for method in METHODS:
                    if valid_combo(ride, crown, spot, method):
                        out.append((ride, crown, spot, method))
    return out


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.ride, params.crown, params.spot, params.method):
        raise StoryError(explain_rejection(params.ride, params.crown, params.spot, params.method))
    world = World(
        params=params,
        ride=RIDES[params.ride],
        crown=CROWNS[params.crown],
        spot=SPOTS[params.spot],
        method=METHODS[params.method],
    )
    world.entities["Hero"] = Entity(params.hero, params.gender, {"role": "quester"})
    world.entities["Companion"] = Entity(params.companion.title(), params.companion, {"role": "safe witness"})
    world.entities["Crown"] = Entity("crown", "treasure", {"material": world.crown.material, "status": "missing"})
    world.entities["Ride"] = Entity(world.ride.key, "ride", {"state": "moving"})
    return world


def _rule_crown_missing(world: World) -> None:
    hero = world.entities["Hero"]
    crown = world.entities["Crown"]
    hero.add_meme("mystery", 1.0)
    hero.add_meme("quest", 1.0)
    crown.add_meter("lost", 1.0)
    world.facts["problem"] = f"the {world.crown.phrase} vanished on {world.ride.phrase}"
    world.fired.append("crown_missing")


def _rule_flashback_clue(world: World) -> None:
    hero = world.entities["Hero"]
    hero.add_meme("remembering", 1.0)
    world.facts["clue"] = world.spot.clue
    world.facts["flashback"] = world.spot.flashback
    world.fired.append("flashback_clue")


def _rule_safe_recovery(world: World) -> None:
    hero = world.entities["Hero"]
    crown = world.entities["Crown"]
    ride = world.entities["Ride"]
    hero.add_meme("patience", 0.8)
    hero.add_meme("relief", 1.0)
    crown.tags["status"] = "found"
    crown.tags["found_at"] = world.spot.key
    crown.meters["lost"] = 0.0
    ride.tags["state"] = "stopped"
    world.facts["method"] = world.method.phrase
    world.facts["found_at"] = world.spot.phrase
    world.fired.append("safe_recovery")


def predict_risk(world: World) -> str:
    if world.spot.hazard == "water" and not world.crown.water_safe:
        return f"the {world.crown.phrase} could be spoiled by water"
    if world.spot.need == "height":
        return "someone could reach too high and fall"
    if world.spot.need in ("operator", "key"):
        return "a locked part of the ride could be pulled the wrong way"
    if world.spot.need == "dark":
        return "the crown could be pushed deeper into the dark"
    return "small fingers could get pinched by the moving ride"


def apply_rules(world: World) -> None:
    _rule_crown_missing(world)
    _rule_flashback_clue(world)
    _rule_safe_recovery(world)


def render_story(world: World) -> str:
    p = world.params
    she, her, him = pronouns(p.gender)
    risk = predict_risk(world)
    companion = p.companion
    apply_rules(world)

    opening = (
        f"{p.hero} wore {her} {world.crown.phrase} on {world.ride.phrase}, "
        f"because it made {him} feel ready for {world.crown.loved_for}. "
        f"The ride began to turn, hum, and sparkle."
    )
    mystery = (
        f"When the ride stopped, the crown was gone. {p.hero} heard only one strange thing in memory: "
        f"{world.spot.clue}. \"This is a quest,\" {she} whispered, trying not to cry."
    )
    flashback = (
        f"{her.title()} {companion} asked {p.hero} to stand still and think backward. "
        f"In a flashback, {p.hero} remembered that {world.spot.flashback}. "
        f"\"If we chase it now, {risk},\" said {her} {companion}."
    )
    recovery = (
        f"So they followed the clue and used {world.method.phrase}. {p.hero} {world.method.action}, "
        f"and there was the crown, waiting {world.spot.phrase}."
    )
    ending = (
        f"{p.hero} put the crown back on, but more gently this time. The mystery had been solved by "
        f"remembering, not rushing, and the ride seemed to knock once more as if it approved."
    )
    return "\n\n".join([opening, mystery, flashback, recovery, ending])


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a mystery quest for children using the words "ride", "knock", and "crown".',
        f"Tell a flashback story where {world.params.hero} solves where the {world.crown.phrase} went on {world.ride.phrase}.",
        f"Write a safe amusement-ride mystery where a clue points {world.spot.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    _she, her, _ = pronouns(p.gender)
    return [
        QAItem("Who is the quest about?", f"It is about {p.hero}, {her} {p.companion}, and the missing {world.crown.phrase}. Their quest begins because the crown matters to the child's pretend game."),
        QAItem("What clue started the mystery?", f"The clue was {world.spot.clue}. In the flashback, {p.hero} remembered that {world.spot.flashback}."),
        QAItem("Why did the companion tell the child to wait?", f"{p.companion.title()} predicted that if they chased the crown, {predict_risk(world)}. Waiting kept the quest safe."),
        QAItem("How was the crown found?", f"They used {world.method.phrase} because it matched a {world.spot.need} search. The crown was recovered {world.spot.phrase} after the ride was safe."),
        QAItem("What lesson did the mystery teach?", "It taught that remembering carefully can solve a quest better than rushing. The crown came back because the child followed evidence calmly and waited for the ride to be safe."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    items = [
        QAItem("Why is it safer to wait for a ride to stop?", "Moving ride parts can pinch, bump, or trap fingers. Waiting lets an adult check safely."),
        QAItem("How can a flashback help solve a mystery?", "A flashback is a remembered moment. Thinking backward can reveal a clue that was easy to miss at first."),
    ]
    if world.spot.need == "height":
        items.append(QAItem("Why should a child ask for help with high places?", "High places can cause falls. A steady adult or operator can reach without climbing dangerously."))
    if world.spot.need in ("operator", "key"):
        items.append(QAItem("Why should only an operator open ride panels?", "Operators know which parts are safe to touch. Locked panels can hide moving or delicate mechanisms."))
    if world.spot.need == "net":
        items.append(QAItem("Why is a net useful near water?", "A net can reach into shallow water without leaning too far. It keeps the helper safer and drier."))
    if world.crown.material in ("paper", "felt"):
        items.append(QAItem("Why should paper or felt stay out of water?", "Paper and felt can sag, tear, or lose shape when soaked. Keeping them dry protects the object."))
    return items


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
water_bad(C,S) :- crown(C), hazard(S,water), not water_safe(C).

combo(R,C,S,M) :-
    ride(R),
    crown(C),
    spot(S),
    method(M),
    ride_spot(R,S),
    need(S,N),
    solves(M,N),
    not unsafe(M),
    not water_bad(C,S).

ok :- chosen(R,C,S,M), combo(R,C,S,M).

#show combo/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    rows = []
    for key, ride in RIDES.items():
        rows.append(asp.fact("ride", key))
        for spot in ride.supported_spots:
            rows.append(asp.fact("ride_spot", key, spot))
    for key, crown in CROWNS.items():
        rows.append(asp.fact("crown", key))
        if crown.water_safe:
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
        rows.append(asp.fact("chosen", params.ride, params.crown, params.spot, params.method))
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
    for ride, crown, spot, method in sorted(py):
        params = StoryParams(ride, crown, spot, method, "Mira", "girl", "mother", 0)
        if not asp_verify(params):
            raise StoryError(f"ASP rejected Python-valid combo: {(ride, crown, spot, method)}")
    return f"OK: clingo gate matches valid_combos() ({len(py)} combos)."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate crown quest storyworld samples.")
    parser.add_argument("--ride", choices=sorted(RIDES))
    parser.add_argument("--crown", choices=sorted(CROWNS))
    parser.add_argument("--spot", choices=sorted(SPOTS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("--companion", choices=COMPANIONS)
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
        ride, crown, spot, method = combo
        if args.ride and args.ride != ride:
            continue
        if args.crown and args.crown != crown:
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
    companion = args.companion or rng.choice(COMPANIONS)
    ride, crown, spot, method = combo
    return StoryParams(ride, crown, spot, method, hero, gender, companion, seed)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = _matching_combos(args)
    if not combos:
        ride = args.ride or next(iter(RIDES))
        crown = args.crown or next(iter(CROWNS))
        spot = args.spot or next(iter(SPOTS))
        method = args.method or next(iter(METHODS))
        raise StoryError(explain_rejection(ride, crown, spot, method))
    seed = getattr(rng, "story_seed", None)
    return _make_params(args, rng, rng.choice(combos), seed)


def format_qa(sample: StorySample) -> str:
    lines = ["", "== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story details ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    samples = []
    for i, combo in enumerate(valid_combos()):
        seed = (args.seed if args.seed is not None else 1000) + i
        rng = random.Random(seed)
        rng.story_seed = seed
        samples.append(generate(_make_params(args, rng, combo, seed)))
    return samples


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    target = max(1, args.n)
    while len(samples) < target and i < target * 20:
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
                header = f"### {sample.params.hero}: {sample.params.crown} crown on {sample.params.ride} at {sample.params.spot}"
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
