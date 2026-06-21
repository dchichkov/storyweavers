#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aquarium_bog_cautionary_surprise_fairy_tale.py
===============================================================================

A tiny standalone storyworld: a fairy-tale cautionary surprise set around an
aquarium and a bog. A child or young caretaker is tempted to bring a bog-crown
(or muddy reed charm) to a shimmering aquarium festival, a kindly warning is
ignored, a surprising mishap happens, and a thoughtful grown-up fixes things
with calm care and a better plan.

The world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes
- state-driven narration
- a Python reasonableness gate plus inline ASP twin
- three QA sets from world state
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp

It is intentionally small and classical: one premise, one turn, one resolution.
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
    flammable: bool = False
    wettable: bool = False
    magical: bool = False
    safe_alternative: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    tone: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    label: str
    phrase: str
    where: str
    mischief: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    kind: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    pond = world.entities.get("aquarium")
    bog = world.entities.get("bog_item")
    if pond is None or bog is None:
        return out
    if pond.meters["cloudy"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if bog.meters["mud"] < THRESHOLD:
        bog.meters["mud"] += 1
    if "fish" in world.entities:
        world.get("fish").memes["startled"] += 1
    out.append("__spill__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None or child.memes["warning"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("worry", "social", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(temptation: Temptation, hazard: Hazard) -> bool:
    return temptation.mischief == "mud" and hazard.risky


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def weather_the_surprise(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def predict_mishap(world: World, temptation: Temptation, hazard: Hazard) -> dict:
    sim = world.copy()
    _do_tempt(sim, sim.get("child"), temptation, hazard, narrate=False)
    return {
        "cloudy": sim.get("aquarium").meters["cloudy"],
        "muddy": sim.get("bog_item").meters["mud"],
    }


def _do_tempt(world: World, child: Entity, temptation: Temptation, hazard: Hazard, narrate: bool = True) -> None:
    world.get("aquarium").meters["cloudy"] += 1
    world.get("bog_item").meters["mud"] += 1
    child.memes["impulse"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, elder: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    elder.memes["care"] += 1
    world.say(
        f"Once in a fairy-tale town by a silver pond, {child.id} and {elder.id} "
        f"came to the {setting.place}. {setting.detail}"
    )
    world.say(
        f"The air felt {setting.tone}, and the little castle bell rang softly over the water."
    )


def desire(world: World, child: Entity, temptation: Temptation) -> None:
    world.say(
        f"{child.id} found {temptation.phrase} {temptation.where} and thought it looked like a charm."
    )
    world.say(
        f'"I want to use {temptation.label}," {child.id} said. "It would make my game feel grand."'
    )


def warn(world: World, elder: Entity, child: Entity, temptation: Temptation, hazard: Hazard) -> None:
    elder.memes["warning"] += 1
    pred = predict_mishap(world, temptation, hazard)
    world.facts["prediction"] = pred
    world.say(
        f'{elder.id} shook {elder.pronoun("possessive")} head. '
        f'"Careful now," {elder.id} said. "That belongs to the bog, not the aquarium. '
        f"It can make the water cloudy and trouble the little fish.""
    )


def defy(world: World, child: Entity, temptation: Temptation) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} loved the idea too much. {child.id} slipped the charm closer to the shining tank."
    )


def surprise(world: World, child: Entity, temptation: Temptation, hazard: Hazard) -> None:
    _do_tempt(world, child, temptation, hazard)
    world.say(
        f"Then, with a sudden splash of mischief, the {temptation.label} turned the water cloudy."
    )
    world.say(
        f"The fish swirled in surprise, and the aquarium lamp blinked over the muddy shimmer."
    )


def alarm(world: World, elder: Entity) -> None:
    world.say(
        f'"Oh!" {child_name(world)} cried. {elder.id} hurried close at once.'
    )


def calm_fix(world: World, elder: Entity, response: Response, delay: int) -> None:
    aquarium = world.get("aquarium")
    bog_item = world.get("bog_item")
    if weather_the_surprise(response, delay):
        aquarium.meters["cloudy"] = 0
        bog_item.meters["mud"] = 0
        world.say(
            f"{elder.id} came gently running and {response.text}."
        )
        world.say(
            "The cloudy water cleared, and the fish floated safely in a bright little circle of glass."
        )
    else:
        aquarium.meters["cloudy"] += 1
        world.say(
            f"{elder.id} came gently running and {response.fail}."
        )
        world.say("The surprise stayed too big, and the little aquarium still looked dim.")


def lesson(world: World, child: Entity, elder: Entity, temptation: Temptation) -> None:
    child.memes["lesson"] += 1
    child.memes["worry"] = 0
    child.memes["joy"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {elder.id} knelt down and said, "
        f'"The bog is for muddy things, but the aquarium is for quiet, clean water. '
        f'You were brave to call me, and now we choose a safer way."'
    )
    world.say(
        f'{child.id} nodded and promised never to mix {temptation.label} with the aquarium again.'
    )


def gift(world: World, child: Entity, elder: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"The next morning, {elder.id} gave {child.id} a tiny glass lantern with no flame at all."
    )
    world.say(
        f'"Now you can keep watch over the aquarium," {elder.id} smiled, "and let the bog keep its mud."'
    )
    world.say(
        f"{child.id} held the lantern up beside the tank, and the water shone clear as a spell."
    )


def child_name(world: World) -> str:
    return world.facts.get("child_name", "the child")


def tell(setting: Setting, temptation: Temptation, hazard: Hazard, response: Response,
         child_name_: str = "Mina", child_gender: str = "girl",
         elder_name: str = "Aunt Rowan", elder_gender: str = "woman",
         delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name_, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name_, kind="character", type=elder_gender, role="elder"))
    aquarium = world.add(Entity(id="aquarium", label="aquarium", flammable=False))
    bog_item = world.add(Entity(id="bog_item", label="bog charm", wettable=True))
    fish = world.add(Entity(id="fish", label="little fish", kind="character", type="thing"))

    world.facts["child_name"] = child_name_
    opening(world, child, elder, setting)
    world.para()
    desire(world, child, temptation)
    warn(world, elder, child, temptation, hazard)
    defy(world, child, temptation)
    world.para()
    surprise(world, child, temptation, hazard)
    calm_fix(world, elder, response, delay)
    lesson(world, child, elder, temptation)
    world.para()
    gift(world, child, elder)
    world.facts.update(
        child=child, elder=elder, aquarium=aquarium, bog_item=bog_item, fish=fish,
        temptation=temptation, hazard=hazard, response=response, delay=delay,
        outcome="contained" if weather_the_surprise(response, delay) else "unclear",
    )
    return world


SETTINGS = {
    "moonlit_fountain": Setting(
        id="moonlit_fountain",
        place="the moonlit aquarium hall",
        detail="At its center stood a round aquarium like a crystal well, and beyond the garden gate lay a marshy bog.",
        tone="cool and silvery",
        affords={"bog", "aquarium"},
    ),
    "castle_gallery": Setting(
        id="castle_gallery",
        place="the castle gallery",
        detail="There was a noble aquarium in the corner, and in the royal courtyard a bog where reeds grew thick.",
        tone="gentle and echoing",
        affords={"bog", "aquarium"},
    ),
}

TEMPTATIONS = {
    "bog_mud": Temptation(
        id="bog_mud",
        label="bog-mud",
        phrase="a spoonful of bog mud in a willow cup",
        where="beside the reeds",
        mischief="mud",
        tags={"bog", "mud"},
    ),
    "bog_reed": Temptation(
        id="bog_reed",
        label="bog reeds",
        phrase="a braid of bog reeds",
        where="near the lantern path",
        mischief="mud",
        tags={"bog", "reed"},
    ),
}

HAZARDS = {
    "aquarium": Hazard(
        id="aquarium",
        label="aquarium",
        phrase="the aquarium water",
        kind="water",
        risky=True,
        tags={"aquarium", "fish"},
    ),
    "fish": Hazard(
        id="fish",
        label="fish",
        phrase="the little fish",
        kind="creature",
        risky=True,
        tags={"aquarium", "fish"},
    ),
}

RESPONSES = {
    "net_and_towel": Response(
        id="net_and_towel",
        sense=3,
        power=2,
        text="lifted the muddy charm away with a soft net and wiped the rim with a clean towel until the water cleared",
        fail="tried to scoop it out, but the mud had already swirled through the whole tank",
        qa_text="lifted the muddy charm away with a soft net and wiped the rim clean",
        tags={"clean", "help"},
    ),
    "drain_and_refill": Response(
        id="drain_and_refill",
        sense=3,
        power=3,
        text="poured the cloudy water out, refilled the aquarium with fresh water, and calmed the fish with a steady hand",
        fail="poured and poured, but the muddiness still clung to the glass",
        qa_text="drained the cloudy water and refilled the aquarium with fresh water",
        tags={"clean", "help"},
    ),
    "water_bucket": Response(
        id="water_bucket",
        sense=1,
        power=1,
        text="splashed more water at the mess",
        fail="splashed more water, which only made everything wobble and blur",
        qa_text="splashed more water at the mess",
        tags={"weak"},
    ),
}

CHILD_NAMES = ["Mina", "Luna", "Toby", "Owen", "Iris", "Rowan"]
ELDER_NAMES = ["Aunt Rowan", "Old Elia", "Queen Mae", "Sir Bram"]
TRAITS = ["curious", "gentle", "bright", "careful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid in TEMPTATIONS:
            for hid in HAZARDS:
                if reasonable_combo(TEMPTATIONS[tid], HAZARDS[hid]):
                    combos.append((sid, tid, hid))
    return combos


@dataclass
class StoryParams:
    setting: str
    temptation: str
    hazard: str
    response: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale cautionary surprise story that includes the words "{f["setting"].place}" and "bog".',
        f"Tell a gentle story where {f['child_name']} is tempted by something from the bog, but an elder warns them before the aquarium is spoiled.",
        "Write a child-facing fairy tale with a surprise mishap in an aquarium, a calm fix, and a lesson about keeping bog mud away from clean water.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    temptation = f["temptation"]
    response = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {elder.id}, who come to the aquarium hall and notice a bog charm. The story follows what happens when curiosity meets caution."),
        ("What did the child want to use?",
         f"{child.id} wanted to use {temptation.label}, a thing from the bog. The elder worried because muddy bog things do not belong near clean aquarium water."),
        ("What happened as a surprise?",
         f"The aquarium water turned cloudy, and the little fish swirled in surprise. The mud from the bog spread faster than the child expected, so the warning turned out to be right."),
    ]
    if f["response"].sense >= SENSE_MIN:
        qa.append((
            "How was the problem fixed?",
            f"{elder.id} used {response.qa_text}. That cleared the tank and brought calm back to the fish."
        ))
    else:
        qa.append((
            "How was the problem fixed?",
            f"{elder.id} tried a weaker idea, but it was not enough to clear the water. The tank stayed cloudy until a better plan could be found."
        ))
    qa.append((
        "What lesson did the child learn?",
        f"{child.id} learned that the bog is for muddy things and the aquarium is for clean water. After that, {child.id} promised to ask first whenever something risky felt exciting."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["temptation"].tags) | set(f["hazard"].tags) | set(f["response"].tags)
    out = []
    knowledge = {
        "aquarium": [("What is an aquarium?", "An aquarium is a glass home for fish and water plants. It needs clean water and gentle care.")],
        "bog": [("What is a bog?", "A bog is a wet, muddy place where reeds and moss grow. It is not a place for clean glass bowls or fish tanks.")],
        "mud": [("Why can mud be a problem in clean water?", "Mud makes water cloudy and can hide food, dirt, and little pieces that do not belong there. Clean water needs to stay clear for fish.")],
        "fish": [("What do fish need in a tank?", "Fish need clean water, room to swim, and calm care. Loud splashes and dirt can upset them.")],
        "clean": [("Why do people clean an aquarium?", "People clean an aquarium to keep the water clear and the fish healthy. A clean tank helps everyone see the little fish shine.")],
    }
    for key in ["aquarium", "bog", "mud", "fish", "clean"]:
        if key in tags and key in knowledge:
            out.extend(knowledge[key])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="moonlit_fountain", temptation="bog_mud", hazard="aquarium", response="net_and_towel", child_name="Mina", child_gender="girl", elder_name="Aunt Rowan", elder_gender="woman", trait="curious", delay=0),
    StoryParams(setting="castle_gallery", temptation="bog_reed", hazard="fish", response="drain_and_refill", child_name="Toby", child_gender="boy", elder_name="Old Elia", elder_gender="woman", trait="bright", delay=0),
]


def explain_rejection(temptation: Temptation, hazard: Hazard) -> str:
    return f"(No story: {temptation.label} can make a muddy surprise, but the chosen hazard does not make the fairy-tale aquarium trouble reasonably enough.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def outcome_of(params: StoryParams) -> str:
    return "contained" if weather_the_surprise(RESPONSES[params.response], params.delay) else "unclear"


ASP_RULES = r"""
hazard(T, H) :- temptation(T), risky(H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, T, H) :- setting(S), temptation(T), hazard_id(H), hazard_ok(T, H).
hazard_ok(T, H) :- mischief(T, mud), risky(H).
contained :- chosen_response(R), power(R, P), delay(D), P >= 1 + D.
outcome(contained) :- contained.
outcome(unclear) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", tid))
        lines.append(asp.fact("mischief", tid, t.mischief))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard_id", hid))
        lines.append(asp.fact("risky", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_response", params.response), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        print("MISMATCH in sensible responses")
        rc = 1
    else:
        print("OK: sensible responses match.")
    # normal generate smoke test
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_dict()
        print("OK: generate() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    cases = []
    for s in range(30):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad:
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
        rc = 1
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale cautionary surprise about an aquarium and a bog.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.temptation is None or c[1] == args.temptation)
              and (args.hazard is None or c[2] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, temptation, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    elder = args.elder or rng.choice(ELDER_NAMES)
    elder_gender = args.elder_gender or "woman"
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, temptation=temptation, hazard=hazard, response=response, child_name=name, child_gender=gender, elder_name=elder, elder_gender=elder_gender, trait=trait, delay=delay)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.temptation not in TEMPTATIONS or params.hazard not in HAZARDS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], TEMPTATIONS[params.temptation], HAZARDS[params.hazard], RESPONSES[params.response], params.child_name, params.child_gender, params.elder_name, params.elder_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
