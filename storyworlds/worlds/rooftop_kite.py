#!/usr/bin/env python3
"""
rooftop_kite.py
================

A Rooftop kite-safety sketch with constrained sampling and ASP gating.

The script models the tension between wind, launch site, kite type, and a
safety alternative that keeps the child in a safe state.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
STORYWORLDS = Path(__file__).resolve().parents[1]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Rooftop:
    key: str
    phrase: str
    description: str
    hazards: tuple[str, ...]
    forbidden_winds: tuple[str, ...]


@dataclass(frozen=True)
class Wind:
    key: str
    phrase: str
    hazards: tuple[str, ...]


@dataclass(frozen=True)
class Kite:
    key: str
    phrase: str
    allowed_winds: tuple[str, ...]
    forbidden_locations: tuple[str, ...]
    hazards: tuple[str, ...]
    tip: str


@dataclass(frozen=True)
class SafeAlternative:
    key: str
    phrase: str
    allows_flying: bool
    lesson: str
    details: str
    covers: tuple[str, ...]


@dataclass
class StoryParams:
    location: str
    wind: str
    kite: str
    alternative: str
    hero: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    role: str
    traits: list[str] = field(default_factory=list)
    state: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    location: Rooftop
    wind: Wind
    kite: Kite
    alternative: SafeAlternative
    can_fly: bool
    can_reason: str
    entities: dict[str, Entity] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    story: str = ""

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for key, ent in self.entities.items():
            traits = ", ".join(ent.traits) if ent.traits else "none"
            lines.append(f"  {key}: {ent.name} ({ent.role}), traits=[{traits}]")
        lines.append(f"  location={self.location.key}")
        lines.append(f"  wind={self.wind.key}")
        lines.append(f"  kite={self.kite.key}")
        lines.append(f"  alternative={self.alternative.key}")
        lines.append(f"  can_fly={self.can_fly}")
        lines.append(f"  can_reason={self.can_reason}")
        if self.risks:
            lines.append(f"  active_risks: {', '.join(self.risks)}")
        else:
            lines.append("  active_risks: none")
        lines.append(f"  events: {', '.join(self.events) if self.events else 'none'}")
        return "\n".join(lines)


ROOFTOPS: dict[str, Rooftop] = {
    "open_terrace": Rooftop(
        key="open_terrace",
        phrase="an open roof terrace",
        description="a wide surface with no immediate edge hazards",
        hazards=(),
        forbidden_winds=("storm",),
    ),
    "edge_patio": Rooftop(
        key="edge_patio",
        phrase="a narrow patio beside a safety rail",
        description="steeper edges with a clear drop nearby",
        hazards=("edge",),
        forbidden_winds=("storm",),
    ),
    "antenna_park": Rooftop(
        key="antenna_park",
        phrase="a roof with old antennas and hanging lines",
        description="tight spaces and exposed cabling",
        hazards=("snag", "power"),
        forbidden_winds=("gusty", "storm"),
    ),
    "water_tank_ring": Rooftop(
        key="water_tank_ring",
        phrase="a narrow ring around a rooftop water tank",
        description="low clearance and hard-to-see obstacles",
        hazards=("edge", "obstacle"),
        forbidden_winds=("storm",),
    ),
}

WINDS: dict[str, Wind] = {
    "calm": Wind(
        key="calm",
        phrase="a calm, soft breeze",
        hazards=("low_lift",),
    ),
    "steady": Wind(
        key="steady",
        phrase="a steady and predictable wind",
        hazards=(),
    ),
    "gusty": Wind(
        key="gusty",
        phrase="unexpected gusts",
        hazards=("gust", "pull"),
    ),
    "storm": Wind(
        key="storm",
        phrase="a hard storm gusting across the roof",
        hazards=("gust", "pull", "tear"),
    ),
}

KITES: dict[str, Kite] = {
    "butterfly": Kite(
        key="butterfly",
        phrase="a small butterfly kite",
        allowed_winds=("calm", "steady"),
        forbidden_locations=("antenna_park",),
        hazards=("low_lift", "snag"),
        tip="Small kites still need enough wind to stay up and can be snagged on lines.",
    ),
    "delta": Kite(
        key="delta",
        phrase="a classic delta kite",
        allowed_winds=("steady", "gusty"),
        forbidden_locations=("water_tank_ring",),
        hazards=("pull",),
        tip="Delta kites pull line tension when winds gust.",
    ),
    "foil": Kite(
        key="foil",
        phrase="a paperfoil trainer kite",
        allowed_winds=("steady", "gusty", "storm"),
        forbidden_locations=("edge_patio", "water_tank_ring"),
        hazards=("pull", "tear"),
        tip="Trainer kites can work in breezier weather, but they demand strong control.",
    ),
    "streamer": Kite(
        key="streamer",
        phrase="a colorful streamer kite",
        allowed_winds=("calm", "steady", "gusty"),
        forbidden_locations=("antenna_park",),
        hazards=("snag",),
        tip="Streamers are light and can become tangled around nearby structures.",
    ),
}

ALTERNATIVES: dict[str, SafeAlternative] = {
    "ask_adult": SafeAlternative(
        key="ask_adult",
        phrase="asked an adult to supervise every launch step",
        allows_flying=True,
        lesson="Adults can add guardrails for pull and edge-risk situations.",
        details="an adult held the line knot and stood near the edge while the child flew with guidance",
        covers=("pull", "snag", "edge", "obstacle", "low_lift"),
    ),
    "tether_plan": SafeAlternative(
        key="tether_plan",
        phrase="used a short-tether practice line close to the wall",
        allows_flying=True,
        lesson="Short lines and controlled distance reduce surprise pulls on wind changes.",
        details="the line was shortened, tested once in place, then let out only after safe clearance",
        covers=("pull", "low_lift", "snag"),
    ),
    "watch_clouds": SafeAlternative(
        key="watch_clouds",
        phrase="chose a safe indoor kite-building session and watched the clouds from the stairwell",
        allows_flying=False,
        lesson="Choosing a grounded activity is a complete safety alternative.",
        details="they built kite parts and skipped launching entirely",
        covers=("all",),
    ),
    "window_watch": SafeAlternative(
        key="window_watch",
        phrase="watched the city weather from a sheltered window and skipped launching",
        allows_flying=False,
        lesson="Good judgment is staying indoors when conditions are uncertain.",
        details="the child compared wind and roof conditions before deciding not to launch",
        covers=("all",),
    ),
}

HEROES: dict[str, tuple[str, ...]] = {
    "girl": ("Mia", "Nora", "Lena", "Sana", "Iris"),
    "boy": ("Leo", "Eli", "Noah", "Rory", "Kai"),
}


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def _article(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def active_risks(location: Rooftop, wind: Wind, kite: Kite) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for risk in location.hazards + wind.hazards + kite.hazards:
        if risk not in seen:
            seen.add(risk)
            ordered.append(risk)
    return ordered


def safe_to_fly(location: Rooftop, wind: Wind, kite: Kite) -> tuple[bool, str]:
    if wind.key not in kite.allowed_winds:
        return False, f"{kite.phrase} is not matched to {wind.phrase}"
    if wind.key in location.forbidden_winds:
        return False, f"{wind.phrase} is not safe at {location.phrase}"
    if location.key in kite.forbidden_locations:
        return False, f"{location.phrase} has hazards that do not work with {kite.phrase}"
    return True, "environment matched for a controlled launch"


def _alternative_covers(alt: SafeAlternative, risks: Iterable[str]) -> bool:
    if "all" in alt.covers:
        return True
    return all(r in alt.covers for r in risks)


def valid_combo(location_key: str, wind_key: str, kite_key: str, alternative_key: str) -> bool:
    if location_key not in ROOFTOPS or wind_key not in WINDS or kite_key not in KITES or alternative_key not in ALTERNATIVES:
        return False
    location = ROOFTOPS[location_key]
    wind = WINDS[wind_key]
    kite = KITES[kite_key]
    alternative = ALTERNATIVES[alternative_key]
    can_fly, reason = safe_to_fly(location, wind, kite)
    if not can_fly and alternative.allows_flying:
        return False
    if can_fly and not alternative.allows_flying:
        return False
    risks = active_risks(location, wind, kite)
    return _alternative_covers(alternative, risks)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for location_key in sorted(ROOFTOPS):
        for wind_key in sorted(WINDS):
            for kite_key in sorted(KITES):
                for alternative_key in sorted(ALTERNATIVES):
                    if valid_combo(location_key, wind_key, kite_key, alternative_key):
                        combos.append((location_key, wind_key, kite_key, alternative_key))
    return combos


def describe_rejection(location_key: str, wind_key: str, kite_key: str, alternative_key: str) -> str:
    if location_key not in ROOFTOPS:
        return f"No story: unknown location {location_key!r}."
    if wind_key not in WINDS:
        return f"No story: unknown wind {wind_key!r}."
    if kite_key not in KITES:
        return f"No story: unknown kite {kite_key!r}."
    if alternative_key not in ALTERNATIVES:
        return f"No story: unknown safe alternative {alternative_key!r}."
    return "No story: this setup is currently not a safe-compatible combination."


def build_world(params: StoryParams) -> World:
    location = ROOFTOPS[params.location]
    wind = WINDS[params.wind]
    kite = KITES[params.kite]
    alternative = ALTERNATIVES[params.alternative]
    can_fly, reason = safe_to_fly(location, wind, kite)
    risks = active_risks(location, wind, kite)

    world = World(
        params=params,
        location=location,
        wind=wind,
        kite=kite,
        alternative=alternative,
        can_fly=can_fly,
        can_reason=reason,
        risks=risks,
    )

    if not valid_combo(params.location, params.wind, params.kite, params.alternative):
        raise StoryError(describe_rejection(params.location, params.wind, params.kite, params.alternative))

    subject, poss, _obj = _pronouns(params.gender)
    world.entities["hero"] = Entity(params.hero, "child", [f"{params.gender} child"], {"name": params.hero, "pronoun": subject})
    world.entities["kite"] = Entity(kite.key, "object", ["kites", "line"], {"place": location.key, "weather": wind.key})

    if can_fly:
        world.events.append("selected-safe-flight-plan")
    else:
        world.events.append("selected-grounded-safe-alternative")
    world.events.append(f"risks={','.join(risks) if risks else 'none'}")
    return world


def _opening(world: World, pronoun: str, possessive: str) -> list[str]:
    hero = world.params.hero
    return [
        f"{hero} came to {world.location.phrase}, carrying {world.kite.phrase} tucked in a side bag.",
        f"The day had {world.wind.phrase}, and {possessive} friend had said this roof could be tricky.",
        f"Because the roof had {world.location.description}, {hero} checked everything before deciding to play.",
    ]


def _flight_plan(world: World, subject: str, possessive: str) -> list[str]:
    hero = world.entities["hero"].name
    return [
        f"{hero} followed the safe plan: {world.alternative.phrase}.",
        f"{world.alternative.details.capitalize()}, so the line never became a surprise.",
        f"The kite caught air, and {hero} kept a wide distance while launching.",
    ]


def _ground_plan(world: World, object_pronoun: str) -> list[str]:
    hero = world.entities["hero"].name
    details = world.alternative.details.replace("the child", hero)
    return [
        f"Because {human_reason(world.can_reason)}, {hero} did not launch a kite.",
        f"Instead, {hero} chose a safer plan: {details}.",
        f"This kept {object_pronoun} safe while the rooftop sky stayed part of the day from afar.",
    ]


def _closing(world: World) -> list[str]:
    hero = world.entities["hero"].name
    return [
        f"{world.alternative.lesson}",
        f"{hero} packed the kite carefully, already knowing to match kite choice, wind, and place before every launch.",
    ]


def human_reason(reason: str) -> str:
    return reason.replace("_", " ").replace("edge patio", "the edge patio").replace("foil kite", "paperfoil trainer kite")


def alternative_action(hero: str, alternative: SafeAlternative) -> str:
    return f"{hero} {alternative.phrase}"


def covers_text(alternative: SafeAlternative) -> str:
    if "all" in alternative.covers:
        return "all active risks"
    return ", ".join(human_reason(risk) for risk in alternative.covers)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    subject, possessive, object_pronoun = _pronouns(params.gender)
    hero_name = world.entities["hero"].name
    risks_text = ", ".join(human_reason(risk) for risk in world.risks) if world.risks else "no active roof, wind, or kite risk"

    if world.can_fly:
        middle = _flight_plan(world, subject, possessive)
    else:
        middle = _ground_plan(world, object_pronoun)

    para1 = " ".join(_opening(world, subject, possessive))
    para2 = " ".join(middle)
    para3 = " ".join(_closing(world))
    world.story = f"{para1}\n\n{para2}\n\n{para3}"

    prompts = [
        f"Write a safe rooftop story where {params.hero} uses this safety plan: {world.alternative.phrase}.",
        f"The world has {world.location.phrase}, {world.wind.phrase}, and {world.kite.phrase}.",
        "Show safe decision-making in a child-focused setting.",
    ]

    story_qa = [
        QAItem(
            "What did the child want to do at first?",
            f"{hero_name} planned to fly {world.kite.phrase}. The story treats that wish seriously, but checks it against the roof, wind, and kite before allowing action.",
        ),
        QAItem(
            "Where did this happen?",
            f"It happened at {world.location.phrase}. That place matters because it has {world.location.description}, which changes how safe a launch can be.",
        ),
        QAItem(
            "Was it safe to fly the kite in this setup?",
            "Yes. The wind, kite, and roof matched well enough for a controlled launch, so the story still required distance and a planned handoff."
            if world.can_fly
            else "No. The wind, kite, or roof did not match safely, so the child chose a grounded alternative instead of forcing a launch.",
        ),
        QAItem(
            "What safe plan was chosen?",
            f"{alternative_action(hero_name, world.alternative)}. That plan fits because it covers {covers_text(world.alternative)} while preserving a rooftop-sky activity.",
        ),
        QAItem(
            "Why was the alternative safe here?",
            f"{world.alternative.lesson} It kept the child away from the risky launch conditions while still answering the desire to play or observe.",
        ),
        QAItem(
            "What risk was explicitly identified by the decision?",
            f"The decision identified {human_reason(world.can_reason)} and active risks of {risks_text}. Naming those risks makes the safety choice specific instead of a generic warning.",
        ),
    ]

    world_qa = [
        QAItem(
            "Why can some rooftop spots be dangerous for kites?",
            "Edges and obstacles can turn wind tension into a fall or snag risk. A safe story has to reason about the place, not only whether the kite looks fun.",
        ),
        QAItem(
            "How do strong gusts affect kite play?",
            "They can create sudden pull and make line control harder. That suddenness is why gusty or stormy wind often pushes the story toward grounded alternatives.",
        ),
        QAItem(
            "What should adults do in edge-located kite situations?",
            "Adults should add distance, clear footing, and direct supervision before any launch. If those controls do not cover the active risk, the launch should be postponed.",
        ),
        QAItem(
            "What is one safe alternative when conditions are unsafe?",
            "A grounded activity such as indoor building or observing from a sheltered place can keep the kite interest alive. The important point is that the alternative must cover the same risk that stopped the launch.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts"]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.extend(["", "== (2) Story questions"])
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.extend(["", "== (3) World-knowledge questions"])
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
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rooftop kite safety world sketch.")
    parser.add_argument("--location", choices=sorted(ROOFTOPS))
    parser.add_argument("--wind", choices=sorted(WINDS))
    parser.add_argument("--kite", choices=sorted(KITES))
    parser.add_argument("--alternative", choices=sorted(ALTERNATIVES))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="render every valid combination")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="list only gate-valid combinations from clingo")
    parser.add_argument("--verify", action="store_true", help="verify inline ASP rules against Python valid_combos")
    parser.add_argument("--show-asp", action="store_true", help="print the ASP facts + rules")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.location is None or combo[0] == args.location)
        and (args.wind is None or combo[1] == args.wind)
        and (args.kite is None or combo[2] == args.kite)
        and (args.alternative is None or combo[3] == args.alternative)
    ]
    if not combos:
        raise StoryError(describe_rejection(
            args.location or "open_terrace",
            args.wind or "steady",
            args.kite or "delta",
            args.alternative or "ask_adult",
        ))

    location_key, wind_key, kite_key, alternative_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    return StoryParams(location_key, wind_key, kite_key, alternative_key, hero, gender, seed=(args.seed or 1000) + index)


ASP_RULES = r"""
% Domain atoms.
location(L) :- rooftop(L).
wind(W) :- breeze(W).
kite(K) :- kite_type(K).
alternative(A) :- safe_alt(A).

% A flight is physically possible only when the local constraints and kite limits align.
flight_possible(L,W,K) :- location(L), wind(W), kite(K),
    wind_allows(K,W),
    not rooftop_forbid_wind(L,W),
    not kite_forbid_loc(K,L).

active_risk(L,W,K,R) :- location(L), wind(W), kite(K), location_hazard(L,R).
active_risk(L,W,K,R) :- location(L), wind(W), kite(K), wind_hazard(W,R).
active_risk(L,W,K,R) :- location(L), wind(W), kite(K), kite_hazard(K,R).

risk(R) :- location_hazard(_, R).
risk(R) :- wind_hazard(_, R).
risk(R) :- kite_hazard(_, R).

covers(A,R) :- alt_covers(A,R).
covers(A,R) :- alt_any(A), risk(R).

unsafe_combo(L,W,K,A) :- location(L), wind(W), kite(K), alternative(A), active_risk(L,W,K,R), not covers(A,R).

combo(L,W,K,A) :- location(L), wind(W), kite(K), alternative(A), flight_possible(L,W,K), alt_flight(A), not unsafe_combo(L,W,K,A).
combo(L,W,K,A) :- location(L), wind(W), kite(K), alternative(A), not flight_possible(L,W,K), alt_grounded(A), not unsafe_combo(L,W,K,A).
#show combo/4.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for rooftop in ROOFTOPS.values():
        rows.append(asp.fact("rooftop", rooftop.key))
        rows.append(asp.fact("rooftop_desc", rooftop.key, rooftop.description))
        rows.extend(asp.fact("location_hazard", rooftop.key, h) for h in rooftop.hazards)
        for wind_key in rooftop.forbidden_winds:
            rows.append(asp.fact("rooftop_forbid_wind", rooftop.key, wind_key))
    for wind in WINDS.values():
        rows.append(asp.fact("breeze", wind.key))
        rows.extend(asp.fact("wind_hazard", wind.key, h) for h in wind.hazards)
    for kite in KITES.values():
        rows.append(asp.fact("kite_type", kite.key))
        rows.extend(asp.fact("wind_allows", kite.key, wind) for wind in kite.allowed_winds)
        rows.extend(asp.fact("kite_forbid_loc", kite.key, loc) for loc in kite.forbidden_locations)
        rows.extend(asp.fact("kite_hazard", kite.key, h) for h in kite.hazards)
    for alt in ALTERNATIVES.values():
        rows.append(asp.fact("safe_alt", alt.key))
        if alt.allows_flying:
            rows.append(asp.fact("alt_flight", alt.key))
        else:
            rows.append(asp.fact("alt_grounded", alt.key))
        if "all" in alt.covers:
            rows.append(asp.fact("alt_any", alt.key))
        else:
            rows.extend(asp.fact("alt_covers", alt.key, h) for h in alt.covers)
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show combo/4."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("ASP/Python mismatch:")
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


def _emit_variants(samples: list[StorySample], args: argparse.Namespace) -> None:
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### location={p.location} wind={p.wind} kite={p.kite} alternative={p.alternative}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed or 7
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos(), start=1):
        p = StoryParams(*combo, hero=(args.hero or "Mia"), gender=(args.gender or "girl"), seed=base_seed + index)
        samples.append(generate(p))
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

    samples: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)

    try:
        if args.all:
            samples = _sample_all(args)
        else:
            seen: set[str] = set()
            i = 0
            while len(samples) < args.n and i < args.n * 50:
                params = resolve_params(args, random.Random(base_seed + i), index=i)
                sample = generate(params)
                i += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique stories with this constraint set.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
            return 0

        _emit_variants(samples, args)
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
