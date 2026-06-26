#!/usr/bin/env python3
"""
A small storyworld: a junior space crew learns that a good theory must be tested,
especially when a crocodile-shaped mystery is drifting near the ship.

Premise:
- A child crew member loves space adventures and has a new theory about a strange
  glowing "crocodile" in orbit.
- A warning says the thing may be a real hazard, and the crew must decide whether
  to chase it, measure it, or trust a guess.

Turn:
- The theory is challenged by careful observation. The crew discovers the "crocodile"
  is a patch of space debris with a green emergency tarp, not a live creature.

Resolution:
- The child learns that theories are useful when they are checked against evidence.
  The crew uses a small tool, records the result, and brings home a lesson learned
  along with a safe ship.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    view: str
    pressure_safe: bool = True


@dataclass
class Theory:
    id: str
    claim: str
    test_verb: str
    evidence_tool: str
    risk: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    theory: str
    hero_name: str
    hero_gender: str
    captain_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

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


SETTINGS = {
    "orbit": Setting(place="the quiet orbit ring", view="Earth below"),
    "moonbase": Setting(place="the moonbase window bay", view="the dusty moon outside"),
    "dock": Setting(place="the docking tunnel", view="the silver ship lights"),
}

THEORIES = {
    "glow": Theory(
        id="glow",
        claim="the glow is a live space crocodile",
        test_verb="measure the glow",
        evidence_tool="a scanner",
        risk="chasing it without checking could waste fuel",
        lesson="a theory should be tested before anyone believes it",
    ),
    "shadow": Theory(
        id="shadow",
        claim="the shadow is a sneaky crocodile in the dark",
        test_verb="shine a lamp on the shadow",
        evidence_tool="a flashlight",
        risk="jumping at shadows can scare the crew for no reason",
        lesson="a story can be exciting and still need evidence",
    ),
    "scratch": Theory(
        id="scratch",
        claim="the scratch marks came from a crocodile claw",
        test_verb="inspect the scratch marks",
        evidence_tool="a magnifier",
        risk="guessing too fast can hide the real cause",
        lesson="careful looking makes a better answer than a quick guess",
    ),
}

HERO_NAMES = ["Mina", "Leo", "Tari", "Nico", "Ari", "Juno", "Pia", "Sami"]
CAPTAIN_NAMES = ["Captain Sol", "Captain Mira", "Captain Vega"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in THEORIES]


def explain_rejection(place: str, theory_id: str) -> str:
    return f"(No story: the place {place!r} and theory {theory_id!r} do not make a good space mystery.)"


def pick_pronoun(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    theory = THEORIES[params.theory]
    world = World(setting)

    hero_type = "girl" if params.hero_gender == "girl" else "boy"
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=params.hero_name))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=params.captain_name))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        type="crocodile",
        label="crocodile",
        phrase="a glowing crocodile shape",
        owner=None,
        caretaker=hero.id,
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=theory.evidence_tool,
        phrase=theory.evidence_tool,
        owner=hero.id,
        caretaker=hero.id,
        wearable=False,
    ))
    log = world.add(Entity(
        id="log",
        kind="thing",
        type="log",
        label="field log",
        phrase="a neat field log",
        owner=hero.id,
        caretaker=hero.id,
    ))

    # Act 1: wonder and theory.
    world.say(
        f"{hero.label} was a small space explorer who loved looking out at {world.setting.view}."
    )
    world.say(
        f"One day, {hero.label} noticed a strange shape drifting near {world.setting.place}: "
        f"{theory.claim}."
    )
    world.say(
        f"{hero.label} had a theory, and {hero.pronoun('possessive')} heart felt very excited about it."
    )

    world.para()

    # Act 2: concern and test.
    world.say(
        f"But {theory.risk}, so {params.captain_name} asked {hero.label} to slow down and test the idea."
    )
    world.say(
        f"{hero.label} brought out {theory.evidence_tool} to {theory.test_verb}."
    )
    world.say(
        f"The little crew floated closer and found green tarp fibers, broken tape, and a blinking tag."
    )
    world.say(
        f"It was not a live crocodile at all. It was old cargo wrapped in a slippery emergency cover."
    )

    world.para()

    # Act 3: lesson learned.
    hero.memes["pride"] = 1.0
    hero.memes["calm"] = 1.0
    hero.memes["lesson_learned"] = 1.0
    mystery.meters["sorted"] = 1.0
    log.meters["written"] = 1.0

    world.say(
        f"{hero.label} wrote down the result in {hero.pronoun('possessive')} field log: "
        f"{theory.lesson}."
    )
    world.say(
        f"{params.captain_name} smiled, and the two of them sent the harmless cargo back to the ship bay."
    )
    world.say(
        f"Later, {hero.label} looked at {world.setting.view} and grinned, because the best space adventures end with a lesson learned."
    )

    world.facts = {
        "hero": hero,
        "captain": captain,
        "mystery": mystery,
        "tool": tool,
        "log": log,
        "theory": theory,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theory: Theory = f["theory"]
    hero: Entity = f["hero"]
    return [
        f'Write a short space adventure story for children that includes a theory about a crocodile.',
        f"Tell a story where {hero.label} thinks {theory.claim} and learns to check it carefully.",
        f"Write a gentle story about a mystery in space, a test, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    theory: Theory = f["theory"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.label} think the strange shape was?",
            answer=f"{hero.label} thought it was {theory.claim}.",
        ),
        QAItem(
            question=f"Why did {params_human_name(hero)} need to test the idea instead of just guessing?",
            answer=f"{captain.label} wanted careful checking because {theory.risk}.",
        ),
        QAItem(
            question=f"What did {hero.label} use to check the mystery?",
            answer=f"{hero.label} used {theory.evidence_tool} to test the idea.",
        ),
        QAItem(
            question=f"What did {hero.label} learn by the end of the story?",
            answer=f"{hero.label} learned that {theory.lesson}.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened near {setting.place} with {setting.view} outside.",
        ),
    ]


def params_human_name(hero: Entity) -> str:
    return hero.label


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a theory?",
            answer="A theory is an idea someone thinks might be true and then checks with evidence.",
        ),
        QAItem(
            question="Why should people test a theory?",
            answer="People test a theory so they can see if it matches what really happens.",
        ),
        QAItem(
            question="What is a crocodile?",
            answer="A crocodile is a big reptile with a long snout and strong teeth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: type={ent.type} label={ent.label!r} meters={meters} memes={memes}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for theory_id in THEORIES:
        lines.append(asp.fact("theory", theory_id))
    for place, theory_id in valid_combos():
        lines.append(asp.fact("valid_combo", place, theory_id))
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(P, T) :- place(P), theory(T).
#show valid_combo/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a crocodile theory and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--theory", choices=THEORIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
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
    combos = valid_combos()
    if args.place and args.theory and (args.place, args.theory) not in combos:
        raise StoryError(explain_rejection(args.place, args.theory))
    place = args.place or rng.choice(list(SETTINGS.keys()))
    theory = args.theory or rng.choice(list(THEORIES.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    return StoryParams(place=place, theory=theory, hero_name=name, hero_gender=gender, captain_name=captain)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(place="orbit", theory="glow", hero_name="Mina", hero_gender="girl", captain_name="Captain Sol"),
    StoryParams(place="moonbase", theory="shadow", hero_name="Leo", hero_gender="boy", captain_name="Captain Mira"),
    StoryParams(place="dock", theory="scratch", hero_name="Tari", hero_gender="girl", captain_name="Captain Vega"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
