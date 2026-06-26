#!/usr/bin/env python3
"""
storyworlds/worlds/escalator_observe_caper_repetition_sound_effects_heartwarming.py
===================================================================================

A small heartwarming story world about an escalator, an observant child, and a
tiny caper that turns into a kind, repeated rescue with sound effects.

Premise:
- A child rides an escalator with a grown-up.
- The child notices a small caper: a toy, snack, or item is lost or stuck.
- Repetition helps: looking, calling, and reaching again and again.
- Sound effects make the scene vivid: buzz, whoosh, clack, tap, beep.

The world models physical meters and emotional memes. The prose is generated from
state changes, not from a fixed paragraph template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the mall"
    affords: set[str] = field(default_factory=set)


@dataclass
class Scenario:
    id: str
    item: str
    item_phrase: str
    issue: str
    sound_effect: str
    repeated_action: str
    observed_thing: str
    caper_label: str
    resolution_action: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    scenario: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "mall": Setting("the mall", {"escalator"}),
    "station": Setting("the station", {"escalator"}),
    "museum": Setting("the museum", {"escalator"}),
    "library": Setting("the library", {"escalator"}),
}

SCENARIOS = {
    "toy": Scenario(
        id="toy",
        item="toy train",
        item_phrase="a tiny red toy train",
        issue="slipped through a handrail gap",
        sound_effect="clack-clack, whoosh",
        repeated_action="peeked again and again",
        observed_thing="the toy train flashing on the step below",
        caper_label="the little caper of the runaway train",
        resolution_action="carefully reached down with a long scarf",
        ending_image="the toy train was back in warm hands",
        tags={"escalator", "observe", "caper", "repetition", "sound"},
    ),
    "snack": Scenario(
        id="snack",
        item="cookie",
        item_phrase="a paper bag with one cookie inside",
        issue="tipped sideways on the moving step",
        sound_effect="bump-bump, ding",
        repeated_action="looked twice",
        observed_thing="the cookie bag wobbling near the edge",
        caper_label="the snack caper",
        resolution_action="held the bag steady with both hands",
        ending_image="the cookie stayed safe and still",
        tags={"escalator", "observe", "caper", "repetition", "sound"},
    ),
    "hat": Scenario(
        id="hat",
        item="hat",
        item_phrase="a blue hat with a yellow star",
        issue="blew close to the side panel",
        sound_effect="tap-tap, whoop",
        repeated_action="watched the step, then watched it again",
        observed_thing="the hat skimming along like a little boat",
        caper_label="the hat caper",
        resolution_action="caught the hat with a quick mitt",
        ending_image="the hat sat snug and happy on its head again",
        tags={"escalator", "observe", "caper", "repetition", "sound"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nina", "Ruby", "Tara", "June", "Ada", "Ivy"]
BOY_NAMES = ["Ben", "Owen", "Leo", "Ezra", "Noah", "Milo", "Finn", "Theo"]
TRAITS = ["curious", "gentle", "bright-eyed", "careful", "kind", "cheerful"]


def sound_word(s: Scenario) -> str:
    return s.sound_effect


def _act_observe(world: World, child: Entity, scenario: Scenario) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.meters["attention"] = child.meters.get("attention", 0.0) + 1
    world.say(
        f"{child.id} leaned near the escalator rail and {scenario.repeated_action}."
    )
    world.say(
        f"{sound_word(scenario)} went the escalator, and {child.id} noticed {scenario.observed_thing}."
    )


def _act_caper(world: World, child: Entity, grownup: Entity, scenario: Scenario) -> None:
    child.memes["concern"] = child.memes.get("concern", 0.0) + 1
    grownup.memes["alert"] = grownup.memes.get("alert", 0.0) + 1
    world.say(
        f"That was the start of {scenario.caper_label}, and {child.id} pointed at it at once."
    )
    world.say(
        f"{child.id} said, 'Look, look, look!' and {grownup.id} said, 'I see it, I see it.'"
    )
    world.say(
        f"The escalator kept moving: whoosh, whoosh, whoosh."
    )


def _act_repeat(world: World, child: Entity, grownup: Entity, scenario: Scenario) -> None:
    child.meters["tries"] = child.meters.get("tries", 0.0) + 1
    grownup.meters["tries"] = grownup.meters.get("tries", 0.0) + 1
    world.say(
        f"Again and again, {child.id} watched the edge while {grownup.id} reached and waited."
    )
    world.say(
        f"Tap, tap, tap went {grownup.id}'s fingers as they kept the little plan going."
    )


def _act_resolve(world: World, child: Entity, grownup: Entity, scenario: Scenario) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    grownup.memes["joy"] = grownup.memes.get("joy", 0.0) + 1
    world.say(
        f"At last, {grownup.id} {scenario.resolution_action}, and {child.id} helped hold the way clear."
    )
    world.say(
        f"{child.id} grinned as {scenario.ending_image}."
    )
    world.say(
        f"They rode the rest of the way together, quiet and smiling, with the escalator humming softly."
    )


def tell(setting: Setting, scenario: Scenario, name: str, gender: str, companion: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=trait))
    grownup = world.add(Entity(id=companion, kind="character", type="adult", label="grown-up"))
    item = world.add(Entity(id="item", type=scenario.item, label=scenario.item, phrase=scenario.item_phrase, owner=child.id))
    world.facts.update(child=child, grownup=grownup, item=item, scenario=scenario, setting=setting)

    world.say(f"{child.id} was a {trait} {gender} who loved to ride the escalator with {grownup.id}.")
    world.say(f"One day at {setting.place}, {child.id} was carrying {scenario.item_phrase}.")
    world.say(f"{child.id} liked to {scenario.repeated_action} because {sound_word(scenario)} made the ride feel like a game.")
    world.para()
    world.say(f"Then {child.id} noticed {scenario.observed_thing} and gasped, 'Oh!'")
    _act_observe(world, child, scenario)
    _act_caper(world, child, grownup, scenario)
    world.para()
    _act_repeat(world, child, grownup, scenario)
    _act_resolve(world, child, grownup, scenario)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    s: Scenario = f["scenario"]
    return [
        f'Write a heartwarming short story for a young child that includes an escalator, a caper, and the sound "{s.sound_effect}".',
        f"Tell a gentle story where {c.id} notices a small problem on an escalator and keeps looking again and again until it is fixed.",
        f"Write a simple story about {c.id}, {s.caper_label}, and a kind grown-up helping with a tiny rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    scenario: Scenario = f["scenario"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {child.id} notice the caper?",
            answer=f"{child.id} noticed it on the escalator at {setting.place}.",
        ),
        QAItem(
            question=f"What did {child.id} keep doing to help?",
            answer=f"{child.id} kept looking again and again and stayed focused until the problem was solved.",
        ),
        QAItem(
            question=f"What sound helped make the ride feel lively?",
            answer=f"The escalator sound and {scenario.sound_effect} helped make the moment feel lively and clear.",
        ),
        QAItem(
            question=f"How did the story end for {scenario.item}?",
            answer=f"It ended happily, with {scenario.ending_image}.",
        ),
        QAItem(
            question=f"Who helped {child.id} with the caper?",
            answer=f"{grownup.id} helped by staying calm, watching closely, and solving it together with {child.id}.",
        ),
    ]


KNOWLEDGE = {
    "escalator": [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a moving staircase that carries people up or down while they stand on it.",
        ),
        QAItem(
            question="Why do people hold the handrail on an escalator?",
            answer="People hold the handrail to help keep their balance and stay safe while the steps move.",
        ),
    ],
    "observe": [
        QAItem(
            question="What does it mean to observe something?",
            answer="To observe something means to look carefully and notice details about it.",
        ),
    ],
    "caper": [
        QAItem(
            question="What is a caper?",
            answer="A caper is a playful little adventure or a small, funny problem that needs attention.",
        ),
    ],
    "repetition": [
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something more than once, like looking again and again.",
        ),
    ],
    "sound": [
        QAItem(
            question="Why do sound effects make stories fun?",
            answer="Sound effects help readers imagine what things feel like and make the scene more vivid.",
        ),
    ],
    "heartwarming": [
        QAItem(
            question="What makes a story heartwarming?",
            answer="A heartwarming story leaves you with a cozy, caring feeling because people help each other kindly.",
        ),
    ],
}


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["scenario"].tags)
    tags.add("heartwarming")
    out: list[QAItem] = []
    for key in ["escalator", "observe", "caper", "repetition", "sound", "heartwarming"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(Setting, Scenario, Gender) :- setting(Setting), scenario(Scenario), allowed_gender(Scenario, Gender).
observe_event(Scenario) :- scenario(Scenario).
caper_event(Scenario) :- scenario(Scenario).
repeat_event(Scenario) :- scenario(Scenario).
sound_event(Scenario) :- scenario(Scenario).
heartwarming_story(Setting, Scenario, Gender) :- valid(Setting, Scenario, Gender),
    observe_event(Scenario), caper_event(Scenario), repeat_event(Scenario), sound_event(Scenario).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, sc in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        for g in ["girl", "boy"]:
            lines.append(asp.fact("allowed_gender", sid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    expected = {(s, sc, g) for s in SETTINGS for sc in SCENARIOS for g in ("girl", "boy")}
    actual = set(asp_valid())
    if actual == expected:
        print(f"OK: ASP gate matches Python registry ({len(actual)} combos).")
        return 0
    print("MISMATCH between ASP and Python registries:")
    print("only in ASP:", sorted(actual - expected))
    print("only in Python:", sorted(expected - actual))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, sc, g) for s in SETTINGS for sc in SCENARIOS for g in ("girl", "boy")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming escalator story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.scenario:
        combos = [c for c in combos if c[1] == args.scenario]
    if args.gender:
        combos = [c for c in combos if c[2] == args.gender]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, scenario, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["mother", "father", "grandma", "grandpa"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, scenario=scenario, name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SCENARIOS[params.scenario], params.name, params.gender, params.companion, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(setting="mall", scenario="toy", name="Mia", gender="girl", companion="mother", trait="curious"),
    StoryParams(setting="station", scenario="snack", name="Ben", gender="boy", companion="father", trait="careful"),
    StoryParams(setting="museum", scenario="hat", name="Ruby", gender="girl", companion="grandma", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for s, sc, g in combos:
            print(f"  {s:8} {sc:8} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.scenario} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
