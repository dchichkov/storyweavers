#!/usr/bin/env python3
"""Luna and the Storm Strap.

A small, state-driven adventure about a child, a cliff path, and a strap
that must hold before the storm reaches the lighthouse.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field, replace
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


HEROES = ("Luna", "Mara", "Tess", "Nell")
WEATHER = ("windy", "rainy")
MATERIALS = ("leather", "canvas")
HELPERS = ("goat", "raven")
VOICES = ("plain", "brisk", "playful")
DETAILS = ("compact", "normal", "rich")
MAX_ACTIONS = 20


@dataclass
class StoryParams:
    hero: str = "Luna"
    weather: str = "windy"
    material: str = "leather"
    helper: str = "goat"
    voice: str = "brisk"
    detail: str = "normal"
    world_seed: int = 2026
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    location: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    fact_events: dict[str, int] = field(default_factory=dict)
    outcome: str = ""

    def snapshot(self) -> dict:
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind: str, actor: str, *, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.fact_events]
        if missing:
            raise StoryError(f"{kind} needs facts that have not happened: {', '.join(missing)}.")
        event_id = len(self.history)
        causes = tuple(sorted({self.fact_events[fact] for fact in needs}))
        self.history.append(
            Event(
                id=event_id,
                kind=kind,
                actor=actor,
                data=data,
                facts=tuple(facts),
                causes=causes,
                state=self.snapshot(),
            )
        )
        for fact in facts:
            self.fact_events[fact] = event_id


def validate_params(p: StoryParams):
    if p.hero not in HEROES:
        raise StoryError(f"Unknown hero: {p.hero!r}.")
    if p.weather not in WEATHER:
        raise StoryError(f"Unknown weather: {p.weather!r}.")
    if p.material not in MATERIALS:
        raise StoryError(f"Unknown strap material: {p.material!r}.")
    if p.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {p.helper!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if p.detail not in DETAILS:
        raise StoryError(f"Unknown detail level: {p.detail!r}.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(params=p)
    w.entities = {
        "luna": Entity(
            "luna",
            p.hero,
            "village",
            "character",
            memes={"courage": 0.7, "attention": 0.8},
        ),
        "keeper": Entity(
            "keeper",
            "the lighthouse keeper",
            "lighthouse",
            "character",
            memes={"worry": 0.8, "trust": 0.4},
        ),
        "helper": Entity(
            "helper",
            f"the {p.helper}",
            "village",
            "animal",
            memes={"nervousness": 0.4},
        ),
        "bridge": Entity(
            "bridge",
            "the old rope bridge",
            "ravine",
            meters={"gap": 12, "loose_plank": 1, "safe": 0},
        ),
        "crate": Entity(
            "crate",
            "the supply crate",
            "far_side",
            meters={"mass": 4, "sealed": 1},
        ),
        "lantern": Entity(
            "lantern",
            "the storm lantern",
            "lighthouse",
            meters={"lit": 0, "fragile": 1},
        ),
        "strap": Entity(
            "strap",
            f"the {p.material} strap",
            "lighthouse",
            meters={"length": 5, "strength": 2.5 if p.material == "leather" else 2.0, "buckled": 0},
        ),
        "peg": Entity(
            "peg",
            "the iron peg",
            "lighthouse",
            meters={"strength": 3},
        ),
        "bell": Entity(
            "bell",
            "the warning bell",
            "lighthouse",
            meters={"ringable": 1},
        ),
    }
    w.record(
        "opening",
        "keeper",
        facts=("storm_warning", "mission_known"),
        weather=p.weather,
        helper=p.helper,
    )
    return w


def strap_ready(w: World) -> bool:
    strap = w.entities["strap"]
    return (
        strap.location == "bridge"
        and strap.meters["buckled"] == 1
        and strap.meters["strength"] >= 2
    )


def bridge_safe(w: World) -> bool:
    return bool(w.entities["bridge"].meters["safe"])


def choose_action(w: World) -> str:
    facts = w.fact_events
    if "ending" in facts:
        return "close"
    if "crate_delivered" in facts:
        return "ring_bell"
    if "crate_recovered" in facts and not bridge_safe(w):
        return "secure_bridge"
    if "strap_tied" in facts and "crossed" not in facts:
        return "cross"
    if "strap_checked" in facts and "strap_tied" not in facts:
        return "tie_strap"
    if "strap_found" in facts and "strap_checked" not in facts:
        return "check_strap"
    if "bridge_inspected" not in facts:
        return "inspect_bridge"
    if "mission_known" in facts and "bridge_inspected" in facts and "strap_found" not in facts:
        return "find_strap"
    if "mission_known" in facts and "departure" not in facts:
        return "depart"
    if "departure" in facts and "mission_known" not in facts:
        return "ask_mission"
    return "ask_mission"


def execute(w: World, action: str):
    p = w.params
    hero = w.entities["luna"]
    bridge = w.entities["bridge"]
    strap = w.entities["strap"]
    crate = w.entities["crate"]
    helper = w.entities["helper"]

    def require(condition: bool, message: str):
        if not condition:
            raise StoryError(message)

    if action == "ask_mission":
        require("mission_known" not in w.fact_events, "The mission has already been explained.")
        w.record(
            "ask_mission",
            "luna",
            facts=("mission_understood",),
            needs=("mission_known",),
            goal="bring lantern oil and signal the storm warning",
        )
        hero.memes["attention"] = 0.9

    elif action == "depart":
        require("mission_understood" in w.fact_events, "Luna must understand the mission before leaving.")
        hero.location = "ravine"
        helper.location = "ravine"
        w.record("depart", "luna", facts=("departure",), needs=("mission_understood",))

    elif action == "inspect_bridge":
        require(hero.location == "ravine", "The bridge can only be inspected at the ravine.")
        w.record(
            "inspect_bridge",
            "luna",
            facts=("bridge_inspected",),
            needs=("departure",),
            loose_plank=True,
            wind=p.weather == "windy",
        )

    elif action == "find_strap":
        require("bridge_inspected" in w.fact_events, "Inspect the bridge before choosing equipment.")
        strap.location = "ravine"
        w.record(
            "find_strap",
            "luna",
            facts=("strap_found",),
            needs=("bridge_inspected",),
            material=p.material,
        )

    elif action == "check_strap":
        require(strap.location == "ravine", "The strap must be at the ravine.")
        require(strap.meters["length"] >= 5, "The strap is too short for this bridge.")
        require(strap.meters["strength"] >= 2, "The strap is too weak for a safe crossing.")
        w.record(
            "check_strap",
            "luna",
            facts=("strap_checked",),
            needs=("strap_found",),
            strength=strap.meters["strength"],
        )

    elif action == "tie_strap":
        require("strap_checked" in w.fact_events, "Check the strap before tying it.")
        strap.meters["buckled"] = 1
        strap.location = "bridge"
        w.record(
            "tie_strap",
            "luna",
            facts=("strap_tied",),
            needs=("strap_checked",),
            anchor="iron peg",
        )

    elif action == "cross":
        require(strap_ready(w), "The strap must be buckled to a strong anchor before crossing.")
        require(hero.location == "ravine", "Luna must be at the ravine.")
        hero.location = "far_side"
        helper.location = "far_side"
        crate.location = "far_side"
        w.record(
            "cross",
            "luna",
            facts=("crossed",),
            needs=("strap_tied",),
            wind=p.weather == "windy",
        )

    elif action == "secure_bridge":
        require("crossed" in w.fact_events, "Cross the bridge before securing the far side.")
        require(helper.location == "far_side", "The helper must be across the bridge.")
        bridge.meters["safe"] = 1
        crate.location = "luna"
        w.record(
            "secure_bridge",
            "luna",
            facts=("crate_recovered", "bridge_secure"),
            needs=("crossed",),
            helper=p.helper,
        )

    elif action == "ring_bell":
        require(crate.location == "luna", "The supply crate must be recovered first.")
        crate.location = "lighthouse"
        w.entities["bell"].meters["ringable"] = 0
        w.entities["lantern"].meters["lit"] = 1
        w.outcome = "warning_given"
        w.record(
            "ring_bell",
            "luna",
            facts=("crate_delivered", "warning_given"),
            needs=("crate_recovered", "bridge_secure"),
        )

    elif action == "close":
        require(w.outcome == "warning_given", "The warning must be given before the story can end.")
        hero.location = "lighthouse"
        helper.location = "lighthouse"
        w.record(
            "close",
            "keeper",
            facts=("ending",),
            needs=("warning_given",),
            outcome=w.outcome,
        )

    else:
        raise StoryError(f"Unknown action: {action}.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "ending" in w.fact_events:
            validate_world(w)
            return w
    raise StoryError("The adventure did not reach a safe ending.")


def validate_world(w: World):
    if w.outcome != "warning_given" or "ending" not in w.fact_events:
        raise StoryError("The warning mission must be completed.")
    if not strap_ready(w):
        raise StoryError("The strap must remain buckled to the bridge.")
    if not bridge_safe(w):
        raise StoryError("The bridge must be secure at the ending.")
    if w.entities["crate"].location != "lighthouse":
        raise StoryError("The supply crate must reach the lighthouse.")
    if w.entities["lantern"].meters["lit"] != 1:
        raise StoryError("The storm lantern must be lit.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")


class Teller:
    def __init__(self, world: World):
        self.world = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.lines: list[str] = []
        self.qa: list[QAItem] = []
        self.context = {
            "hero": self.p.hero,
            "weather": self.p.weather,
            "material": self.p.material,
            "helper": self.p.helper,
        }

    def tell(self, *choices: str):
        if self.p.detail == "compact":
            choices = tuple(sorted(choices, key=len)[:2])
        elif self.p.detail == "rich":
            choices = tuple(sorted(choices, key=len)[-2:])
        self.lines.append(self.rng.choice(choices).format(**self.context))

    def dialogue(self, choices: tuple[tuple[str, str], ...]):
        for speaker, text in choices:
            name = self.context["hero"] if speaker == "hero" else "the keeper"
            self.lines.append(f'"{text.format(**self.context)}" {name} said.')

    def add_qa(self, question: str, answer: str):
        self.qa.append(QAItem(question.format(**self.context), answer.format(**self.context)))

    def render(self) -> tuple[str, list[QAItem]]:
        for event in self.world.history:
            self.render_event(event)
        return "\n\n".join(self.lines), self.qa

    def render_event(self, event: Event):
        k = event.kind
        if k == "opening":
            self.tell(
                "On a dark {weather} afternoon, {hero} found the lighthouse keeper staring toward the ravine.",
                "The wind pushed gray clouds over the cliffs when {hero} ran to the lighthouse.",
            )
            self.dialogue(
                (
                    ("hero", "Why are you watching the bridge?"),
                    ("keeper", "The storm lantern is ready, but its oil is in a crate on the far side."),
                    ("hero", "Then I will bring it back."),
                )
            )
            self.tell(
                "The old rope bridge swung above the ravine, and the first drops of rain began to strike its boards.",
                "Beyond the ravine, the supply crate waited beside the far cliff while the bridge groaned in the rising air.",
            )
            self.add_qa(
                "What danger was waiting at the beginning?",
                "A storm was approaching, and the oil needed for the lighthouse lantern was across a swinging rope bridge.",
            )

        elif k == "ask_mission":
            self.tell(
                "{hero} asked exactly what had to be done before the storm arrived.",
                "Before stepping toward the ravine, {hero} made the keeper explain the plan.",
            )
            self.dialogue(
                (
                    ("hero", "What must reach the lighthouse?"),
                    ("keeper", "The oil crate. Then ring the warning bell."),
                )
            )
            self.add_qa(
                "What was {hero}'s mission?",
                "{hero} had to bring the oil crate from the far side and ring the warning bell at the lighthouse.",
            )

        elif k == "depart":
            self.tell(
                "{hero} and the {helper} hurried toward the ravine as the clouds folded over the sea.",
                "With the {helper} close behind, {hero} left the lighthouse and followed the cliff path.",
            )

        elif k == "inspect_bridge":
            self.tell(
                "At the bridge, {hero} saw a loose plank twisting above the dark gap.",
                "The bridge creaked under the wind. One plank had lifted, and the ropes shivered around it.",
            )
            self.dialogue(
                (
                    ("hero", "We need something to hold us if the plank slips."),
                    ("keeper", "Take the strap from the gear room."),
                )
            )
            self.add_qa(
                "Why did {hero} need a strap?",
                "A loose plank and the shaking ropes made the bridge dangerous, so a strong strap could give {hero} a handhold and anchor.",
            )

        elif k == "find_strap":
            self.tell(
                "{hero} found a {material} strap hanging beside the lighthouse door and carried it to the bridge.",
                "In the gear room, {hero} pulled down the {material} strap. It was long enough to reach the iron peg.",
            )

        elif k == "check_strap":
            self.tell(
                "{hero} tugged the strap twice. It was long, sound, and strong enough for the crossing.",
                "The {material} strap had no torn stitches. {hero} tested it before trusting the ravine to it.",
            )
            self.add_qa(
                "How did {hero} test the strap?",
                "{hero} pulled it twice and checked that its length, stitches, and strength were enough for the bridge.",
            )

        elif k == "tie_strap":
            self.tell(
                "{hero} looped the strap around the bridge rope and buckled it to the iron peg.",
                "Kneeling in the wet grass, {hero} fastened the strap to the iron peg beside the bridge.",
            )
            self.dialogue(
                (
                    ("hero", "Hold the loose end, please."),
                    ("keeper", "I have it."),
                    ("hero", "If I slip, pull when I call."),
                )
            )
            self.add_qa(
                "Where did {hero} fasten the strap?",
                "{hero} buckled the strap around the bridge rope and anchored it to an iron peg.",
            )

        elif k == "cross":
            self.tell(
                "The bridge lurched. {hero} gripped the strap and stepped over the loose plank while the {helper} trotted behind.",
                "A gust swung the bridge toward the ravine wall, but the strap stayed tight. {hero} crossed one careful step at a time.",
            )
            self.dialogue(
                (
                    ("hero", "Stay close to the strap!"),
                    ("keeper", "The bridge is moving!"),
                    ("hero", "So are we. Keep going!"),
                )
            )
            self.add_qa(
                "How did {hero} cross the bridge?",
                "{hero} held the buckled strap, stepped over the loose plank, and crossed carefully while the bridge swung in the wind.",
            )

        elif k == "secure_bridge":
            self.tell(
                "On the far side, {hero} tied the crate's handle to the strap so the {helper} could help drag it back.",
                "The {helper} braced its feet while {hero} pulled the supply crate clear of the cliff edge.",
            )
            self.add_qa(
                "How did {hero} recover the crate?",
                "{hero} used the anchored strap to pull the supply crate away from the far cliff edge, with help from the {helper}.",
            )

        elif k == "ring_bell":
            self.tell(
                "{hero} brought the crate into the lighthouse and lit the storm lantern.",
                "Back at the lighthouse, {hero} delivered the oil and raised the lantern's warm flame.",
            )
            self.dialogue(
                (
                    ("hero", "The oil is here. Ring the bell!"),
                    ("keeper", "You made it back before the storm."),
                    ("hero", "The strap made the crossing possible."),
                )
            )
            self.add_qa(
                "What happened after the crate arrived?",
                "{hero} delivered the oil, lit the storm lantern, and told the keeper to ring the warning bell.",
            )

        elif k == "close":
            self.tell(
                "The warning bell rolled across the cliffs. Behind the lighthouse, the strap still held the bridge steady.",
                "As the storm broke over the sea, the bell rang and the anchored strap kept the old bridge from twisting apart.",
            )
            self.add_qa(
                "How did the story end?",
                "The warning bell rang, the lantern was lit, and the strap remained fastened so the bridge stayed secure.",
            )


ASP_RULES = """
mission.
weather(windy).
weather(rainy).
material(leather).
material(canvas).
strong(leather).
strong(canvas).
length(leather,5).
length(canvas,5).
anchor(iron_peg).
safe_crossing(M,A) :- material(M), strong(M), length(M,5), anchor(A).
deliver(M,A) :- safe_crossing(M,A).
#show safe_crossing/2.
#show deliver/2.
"""


def asp_facts() -> str:
    from asp import fact

    facts = [
        fact("mission"),
        *(fact("weather", value) for value in WEATHER),
        *(fact("material", value) for value in MATERIALS),
        fact("anchor", "iron_peg"),
    ]
    return "\n".join(facts)


def asp_cases() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "safe_crossing"))


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story, story_qa = Teller(world).render()
    return StorySample(
        params=p,
        story=story,
        prompts=[
            f"Write an adventure story about {p.hero} using a {p.material} strap to cross a stormy bridge."
        ],
        story_qa=story_qa,
        world_qa=[
            QAItem(
                "What is a strap useful for in this world?",
                "A strap can provide a handhold and anchor a person or load while crossing the old bridge.",
            )
        ],
        world=world,
    )


def verify():
    expected = {(material, "iron_peg") for material in MATERIALS}
    if asp_cases() != expected:
        raise StoryError("Python and ASP disagree about which straps can anchor a crossing.")
    count = 0
    for weather, material, helper in itertools.product(WEATHER, MATERIALS, HELPERS):
        p = StoryParams(weather=weather, material=material, helper=helper)
        world = simulate(p)
        generate(p)
        for voice in VOICES:
            altered = replace(p, voice=voice, prose_seed=99, detail="compact")
            other = simulate(altered)
            if [event.kind for event in other.history] != [event.kind for event in world.history]:
                raise StoryError("Prose settings changed the simulated event sequence.")
        count += 1
    print(f"OK: {count} configurations; ASP parity; independent prose checks.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=2026)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--weather", choices=WEATHER)
    parser.add_argument("--material", choices=MATERIALS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--voice", choices=VOICES, default="brisk")
    parser.add_argument("--detail", choices=DETAILS, default="normal")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng: random.Random, index: int = 0, *, sample: bool = False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        voice=args.voice,
        detail=args.detail,
    )
    registries = {
        "hero": HEROES,
        "weather": WEATHER,
        "material": MATERIALS,
        "helper": HELPERS,
    }
    for name, choices in registries.items():
        value = getattr(args, name)
        setattr(
            p,
            name,
            value if value is not None else rng.choice(choices) if sample else getattr(p, name),
        )
    validate_params(p)
    return p


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "world": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_cases())))
            return 0

        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for weather, material, helper in itertools.product(WEATHER, MATERIALS, HELPERS):
                if args.weather is not None and args.weather != weather:
                    continue
                if args.material is not None and args.material != material:
                    continue
                if args.helper is not None and args.helper != helper:
                    continue
                params.append(
                    replace(
                        resolve_params(args, rng),
                        weather=weather,
                        material=material,
                        helper=helper,
                    )
                )
        else:
            params = [
                resolve_params(args, rng, index, sample=args.n > 1)
                for index in range(args.n)
            ]

        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for index, p in enumerate(params):
                emit(
                    generate(p),
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(params) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
