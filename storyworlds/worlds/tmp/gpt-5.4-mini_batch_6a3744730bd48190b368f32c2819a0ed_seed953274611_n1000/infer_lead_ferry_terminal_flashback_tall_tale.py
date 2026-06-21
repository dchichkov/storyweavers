#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/infer_lead_ferry_terminal_flashback_tall_tale.py
===============================================================================

A standalone storyworld for a tall-tale style ferry-terminal flashback.

Premise:
- A child at a ferry terminal hears a boastful old sailor's tale.
- The story uses a flashback to explain how they learned to infer the tide and
  lead the ferry safely through a tricky channel.
- The ending proves the change in the world: the terminal clears, the ferry
  departs safely, and the child can now read the harbor signs like a map.

This world follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- a Python reasonableness gate with an inline ASP twin
- three QA sets grounded in simulated world state
- stdlib-only runtime unless ASP mode is used
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Weather:
    id: str
    label: str
    tide: str
    sky: str
    channel: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    method: str
    sens: int
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Ferry:
    id: str
    label: str
    route: str
    cargo: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("storm") and not world.facts.get("harbor_alarm"):
        world.facts["harbor_alarm"] = True
        world.get("terminal").meters["hustle"] += 1
        out.append("The terminal woke up and hurried like a goose in a gale.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("flashback_started") and not world.facts.get("flashback_set"):
        world.facts["flashback_set"] = True
        world.get("child").memes["wonder"] += 1
        out.append("__flashback__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm), Rule("flashback", _r_flashback)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(observed: Weather, guide: Guide, ferry: Ferry) -> bool:
    return guide.sens >= SENSE_MIN and observed.tide in {"low", "ebb", "turning"} and ferry.id in FERRIES


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (w.id, g.id, f.id)
        for w in WEATHER.values()
        for g in GUIDES.values()
        for f in FERRIES.values()
        if reasonableness_ok(w, g, f)
    ]


def predict(world: World) -> dict:
    sim = world.copy()
    sim.facts["flashback_started"] = True
    propagate(sim, narrate=False)
    return {
        "terminal_hustle": sim.get("terminal").meters["hustle"],
        "child_wonder": sim.get("child").memes["wonder"],
    }


def tell(weather: Weather, guide: Guide, ferry: Ferry, child_name: str, child_type: str,
         narrator_name: str, narrator_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    elder = world.add(Entity(id=narrator_name, kind="character", type=narrator_type, role="narrator"))
    terminal = world.add(Entity(id="terminal", kind="place", type="terminal", label="the ferry terminal"))
    water = world.add(Entity(id="water", kind="place", type="water", label="the harbor water"))

    child.memes["curiosity"] = 2
    elder.memes["pride"] = 2
    world.facts.update(weather=weather, guide=guide, ferry=ferry, child=child, elder=elder)

    world.say(
        f"At the ferry terminal, where the harbor water shone like a blue coin, "
        f"{child.id} listened to {elder.id}, an old sailor with a voice as big as a bell buoy."
    )
    world.say(
        f'"I can infer the weather by the tide," {elder.id} boomed. '
        f'"And I can lead a ferry through a fog so thick it could hide a whale."'
    )
    world.para()
    world.say(
        f"{child.id} laughed, because the words sounded like a map made of thunder. "
        f"Then {child.pronoun()} saw the ferry {ferry.route}, its ropes tugging like nervous reins."
    )
    child.memes["guessing"] += 1
    world.facts["flashback_started"] = True
    propagate(world, narrate=True)
    world.para()
    if weather.tide == "turning":
        world.say(
            f"That pulled a flashback from the air. Years before, the harbor had gone still and sly, "
            f"and a storm had pushed the water into a sneaky twist."
        )
    else:
        world.say(
            f"That pulled a flashback from the air. Years before, the harbor had been swallowed by fog, "
            f"and the tide had whispered clues only a careful eye could read."
        )
    world.say(
        f"In that memory, {elder.id} watched the foam, felt the wind, and {guide.method} "
        f"until the ferry found the channel and the travelers reached shore."
    )
    child.memes["wonder"] += 2
    child.memes["respect"] += 1
    world.para()
    world.say(
        f"{child.id} looked back at the real terminal, and now {child.pronoun()} could infer the tide too. "
        f"{child.id} pointed at the water and told the dockhands when the current would lead the ferry safe."
    )
    world.say(
        f"The captain followed the warning, the ferry slid out easy as a gull on the wind, "
        f"and the terminal emptied under a sky bright with salt and brass."
    )
    world.say(
        f"By the end, {child.id} stood taller than a mast-head, with a flashback in {child.pronoun('possessive')} mind "
        f"and a new lead in {child.pronoun('possessive')} step."
    )

    world.facts.update(
        terminal=terminal,
        water=water,
        harbor_alarm=bool(world.facts.get("harbor_alarm")),
        flashback_set=bool(world.facts.get("flashback_set")),
        ending="safe_departure",
        forecasted=guide.method,
    )
    return world


WEATHERS = {
    "fog_low_tide": Weather(
        id="fog_low_tide",
        label="a foggy low tide",
        tide="low",
        sky="fog",
        channel="clear",
        tags={"fog", "tide", "flashback"},
    ),
    "storm_turning": Weather(
        id="storm_turning",
        label="a storm at the turning tide",
        tide="turning",
        sky="storm",
        channel="narrow",
        tags={"storm", "tide", "flashback"},
    ),
    "breezy_ebb": Weather(
        id="breezy_ebb",
        label="a breezy ebb tide",
        tide="ebb",
        sky="breezy",
        channel="open",
        tags={"ebb", "tide", "flashback"},
    ),
}

GUIDES = {
    "foam": Guide(
        id="foam",
        label="foam-reading",
        phrase="read the foam like lines on a page",
        method="read the foam like lines on a page",
        sens=3,
        power=3,
        tags={"infer", "lead", "flashback"},
    ),
    "wind": Guide(
        id="wind",
        label="wind-reading",
        phrase="listen to the wind like a barn owl listens",
        method="listen to the wind like a barn owl listens",
        sens=2,
        power=2,
        tags={"infer", "lead", "flashback"},
    ),
    "stars": Guide(
        id="stars",
        label="star-guiding",
        phrase="follow the stars as if they were lanterns",
        method="follow the stars as if they were lanterns",
        sens=3,
        power=3,
        tags={"infer", "lead", "flashback"},
    ),
}

FERRIES = {
    "iron_ferry": Ferry(
        id="iron_ferry",
        label="the iron ferry",
        route="toward the far quay",
        cargo="mail and milk",
        tags={"ferry", "terminal"},
    ),
    "red_ferry": Ferry(
        id="red_ferry",
        label="the red ferry",
        route="out to the island dock",
        cargo="apples and boots",
        tags={"ferry", "terminal"},
    ),
    "white_ferry": Ferry(
        id="white_ferry",
        label="the white ferry",
        route="across the bay",
        cargo="lanterns and crates",
        tags={"ferry", "terminal"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Tom", "Finn", "Eli", "Noah", "Sam"]


@dataclass
class StoryParams:
    weather: str
    guide: str
    ferry: str
    child_name: str
    child_gender: str
    narrator_name: str
    narrator_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(weather="fog_low_tide", guide="foam", ferry="white_ferry",
                child_name="Maya", child_gender="girl",
                narrator_name="Old Marlow", narrator_gender="man"),
    StoryParams(weather="storm_turning", guide="wind", ferry="iron_ferry",
                child_name="Tom", child_gender="boy",
                narrator_name="Captain Rook", narrator_gender="man"),
    StoryParams(weather="breezy_ebb", guide="stars", ferry="red_ferry",
                child_name="Nora", child_gender="girl",
                narrator_name="Aunt Sal", narrator_gender="woman"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    w: Weather = f["weather"]
    g: Guide = f["guide"]
    ferry: Ferry = f["ferry"]
    return [
        f'Write a tall tale set at a ferry terminal that uses the words "infer" and "lead".',
        f"Tell a story where {f['child'].id} learns how to infer the tide and lead {ferry.label} safely through the harbor.",
        f"Write a flashback story at the ferry terminal where an old sailor explains {g.phrase} and a child remembers it later.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    weather: Weather = f["weather"]
    guide: Guide = f["guide"]
    ferry: Ferry = f["ferry"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {elder.id} at the ferry terminal. The old sailor tells a tall tale that becomes a lesson."
        ),
        QAItem(
            question="Why was the flashback important?",
            answer=f"The flashback showed how {elder.id} learned {guide.phrase} in rough harbor weather. That memory helped {child.id} infer what the tide would do and lead the ferry safely."
        ),
        QAItem(
            question=f"What did {child.id} do at the end?",
            answer=f"{child.id} pointed at the water, inferred the tide, and helped lead {ferry.label} out of the terminal. The ferry left safely, so the story ends with a clear harbor and a proud child."
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"At the start, the ferry terminal felt tricky and hard to read. By the end, the child could read the signs of the harbor and lead the ferry with confidence."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    weather: Weather = f["weather"]
    guide: Guide = f["guide"]
    out = [
        QAItem(
            question="What does it mean to infer something?",
            answer="To infer means to figure out an answer from clues. You look at what you can see, hear, or feel, and then make a careful guess."
        ),
        QAItem(
            question="What does it mean to lead something?",
            answer="To lead means to go first and show the way. A person who leads helps others move in the right direction."
        ),
        QAItem(
            question="What is a ferry terminal?",
            answer="A ferry terminal is a place where people wait for ferries. It usually has docks, ropes, and signs telling travelers where to go."
        ),
    ]
    if "fog" in weather.tags or "flashback" in weather.tags:
        out.append(QAItem(
            question="Why can a flashback help in a story?",
            answer="A flashback lets the story go back to an earlier time. It can explain how a character learned something useful before the present moment."
        ))
    if "infer" in guide.tags:
        out.append(QAItem(
            question="Why do sailors watch the tide?",
            answer="Sailors watch the tide because moving water can help or hinder a boat. If they infer the tide correctly, they can choose a safer path."
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(k for k in world.facts.keys() if k not in {'weather', 'guide', 'ferry', 'child', 'elder'})}")
    return "\n".join(lines)


ASP_RULES = r"""
sens_ok(G) :- guide(G), sens(G,S), sense_min(M), S >= M.
hazard(W) :- weather(W), tide(W,T), (T = low; T = ebb; T = turning).
valid(W,G,F) :- weather(W), guide(G), ferry(F), sens_ok(G), hazard(W).
flashback_ready :- weather(W), guide(G), ferry(F), valid(W,G,F).
outcome(safe_departure) :- flashback_ready.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for wid, w in WEATHER.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("tide", wid, w.tide))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("sens", gid, g.sens))
    for fid in FERRIES:
        lines.append(asp.fact("ferry", fid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("weather", params.weather),
        asp.fact("guide", params.guide),
        asp.fact("ferry", params.ferry),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def valid_story_combo(params: StoryParams) -> bool:
    return (params.weather in WEATHER and params.guide in GUIDES and params.ferry in FERRIES
            and GUIDES[params.guide].sens >= SENSE_MIN and WEATHER[params.weather].tide in {"low", "ebb", "turning"})


def asp_verify() -> int:
    import itertools
    rc = 0
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: gate matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" python-only:", sorted(p - a))
        print(" asp-only:", sorted(a - p))
    # Smoke-test generation
    try:
        sample = generate(resolve_params(argparse.Namespace(
            weather=None, guide=None, ferry=None, child_name=None, child_gender=None,
            narrator_name=None, narrator_gender=None, n=1, seed=None, all=False,
            trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as ex:
        rc = 1
        print(f"FAIL: generate() smoke test crashed: {ex}")
    # Check ASP outcome on curated and random valid cases.
    cases = list(CURATED)
    rng = random.Random(777)
    for _ in range(20):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), rng))
        except StoryError:
            pass
    mism = 0
    for c in cases:
        if asp_outcome(c) != "safe_departure":
            mism += 1
    if mism == 0:
        print(f"OK: ASP outcome agrees on {len(cases)} cases.")
    else:
        rc = 1
        print(f"MISMATCH: {mism} outcome cases differed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale ferry terminal flashback storyworld.")
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--ferry", choices=FERRIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--narrator-name")
    ap.add_argument("--narrator-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        (w, g, f)
        for w in WEATHERS
        for g in GUIDES
        for f in FERRIES
        if valid_story_combo(StoryParams(weather=w, guide=g, ferry=f,
                                         child_name="x", child_gender="girl",
                                         narrator_name="y", narrator_gender="man"))
        and (args.weather is None or args.weather == w)
        and (args.guide is None or args.guide == g)
        and (args.ferry is None or args.ferry == f)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    weather, guide, ferry = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    narrator_gender = args.narrator_gender or rng.choice(["woman", "man"])
    narrator_name = args.narrator_name or rng.choice(["Old Marlow", "Captain Rook", "Aunt Sal", "Uncle Drift"])
    return StoryParams(
        weather=weather,
        guide=guide,
        ferry=ferry,
        child_name=child_name,
        child_gender=child_gender,
        narrator_name=narrator_name,
        narrator_gender=narrator_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.weather not in WEATHERS:
        raise StoryError("Unknown weather choice.")
    if params.guide not in GUIDES:
        raise StoryError("Unknown guide choice.")
    if params.ferry not in FERRIES:
        raise StoryError("Unknown ferry choice.")
    if not valid_story_combo(params):
        raise StoryError("That combination is not a reasonable ferry-terminal story.")
    world = tell(
        WEATHERS[params.weather],
        GUIDES[params.guide],
        FERRIES[params.ferry],
        params.child_name,
        params.child_gender,
        params.narrator_name,
        params.narrator_gender,
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for w, g, f in combos:
            print(f"  {w:14} {g:8} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            header = f"### {p.child_name} at {p.weather} / {p.guide} / {p.ferry}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
