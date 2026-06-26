#!/usr/bin/env python3
"""
storyworlds/worlds/qrx_peony_mistaken_foreshadowing_happy_ending_rhyming.py
===========================================================================

A tiny standalone story world: a child, a peony, a mistaken guess, a gentle
warning, and a happy ending. The prose is written in a light rhyming style, and
the simulated state drives the turn from mistaken action to a safer choice.

Seed tale idea:
- Qrx is a small child in a flower garden.
- Qrx spots a peony and mistakes it for a fluffy plaything or a prize to pluck.
- A parent notices foreshadowing signs: a buzzing bee, a tight bud, and the
  risk of bruising the bloom.
- They pause, correct the mistake, and choose a kinder action.
- The story ends happily with the peony safe and Qrx content.

The world uses two numeric dimensions on entities:
- meters: physical state (fresh, bent, bruised, wet, clean)
- memes: emotional state (joy, worry, mistaken, relief, love)
"""

from __future__ import annotations

import argparse
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
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    mistake: str
    risk: str
    weather: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeChoice:
    id: str
    label: str
    prep: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("qrx")
    peony = world.get("peony")
    if child.memes.get("reach", 0) >= THRESHOLD and world.facts.get("act_id") == "pluck":
        sig = ("bump",)
        if sig not in world.fired:
            world.fired.add(sig)
            peony.meters["bent"] = peony.meters.get("bent", 0) + 1
            out.append("The peony bent a bit, and the petals shivered.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("qrx")
    peony = world.get("peony")
    if peony.meters.get("bent", 0) >= THRESHOLD and not world.facts.get("resolved"):
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = child.memes.get("worry", 0) + 1
            out.append("That little bend looked like a warning in the wind.")
    return out


CAUSAL_RULES = [_r_bump, _r_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                all_out.extend(sents)
    if narrate:
        for s in all_out:
            world.say(s)
    return all_out


def predict_risk(world: World, action: Action) -> bool:
    sim = world.copy()
    sim.get("qrx").memes["reach"] = 1.0
    sim.facts["act_id"] = action.id
    propagate(sim, narrate=False)
    return sim.get("peony").meters.get("bent", 0) >= THRESHOLD


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place} was warm and still."
    return f"The {setting.place} was bright, with soft grass and a little path."


def introduce(world: World, child: Entity) -> None:
    world.say(f"Qrx was a small child with curious feet and a bright little grin.")
    world.say(f"{setting_detail(world.setting)}")


def foreshadow(world: World, action: Action) -> None:
    world.say("A bee did a loop, and the peony stayed tight and sweet.")
    world.say("Its rosy buds were closed up close, like a secret with a seat.")
    world.facts["foreshadow"] = True
    world.facts["act_id"] = action.id


def want(world: World, action: Action) -> None:
    child = world.get("qrx")
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["reach"] = 1.0
    world.say(f"Qrx wanted to {action.verb}, with a grin so wide and neat.")
    world.say(f"But wanted things can wander wrong, like slippers off a seat.")


def warn(world: World, parent: Entity, action: Action) -> bool:
    if not predict_risk(world, action):
        return False
    child = world.get("qrx")
    peony = world.get("peony")
    child.memes["mistaken"] = child.memes.get("mistaken", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(f'"Careful, Qrx," {parent.label} said, "that peony is not a toy to tote.')
    world.say(f"It can bruise if we grab too fast, and flowers like a softer note.")
    return True


def correct_mistake(world: World, action: Action) -> None:
    child = world.get("qrx")
    child.memes["reach"] = 0.0
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.say("Qrx blinked and looked again, and the mistake came clear.")
    world.say("That fluffy bloom was not a ball, but a flower loved and dear.")


def choose_safe(world: World, choice: SafeChoice) -> None:
    child = world.get("qrx")
    peony = world.get("peony")
    world.facts["resolved"] = True
    peony.meters["fresh"] = peony.meters.get("fresh", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["love"] = child.memes.get("love", 0) + 1
    child.memes["mistaken"] = 0.0
    world.say(f"So Qrx chose to {choice.prep}, which made the moment feel right.")
    world.say(f"They {choice.ending}, and the peony stayed safe and bright.")


def happy_end(world: World) -> None:
    child = world.get("qrx")
    peony = world.get("peony")
    world.say("Qrx smiled at the peony glow, then waved and took a bow.")
    world.say("The flower stood up tall and pink, and everyone felt proud somehow.")
    world.say("A mistaken start had turned to care, with kindness in the air.")
    world.say("And that is how the little bloom and Qrx made a happy pair.")


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"pluck", "admire"}),
    "porch": Setting(place="the porch", indoor=False, affords={"admire"}),
}

ACTIONS = {
    "pluck": Action(
        id="pluck",
        verb="pluck the peony",
        gerund="plucking peonies",
        mistake="picked it like a toy",
        risk="the petals could bend",
        weather="breezy",
        tags={"peony", "mistaken"},
    ),
    "admire": Action(
        id="admire",
        verb="admire the peony",
        gerund="admiring peonies",
        mistake="looked, not touched",
        risk="nothing at all",
        weather="calm",
        tags={"peony"},
    ),
}

SAFE_CHOICES = {
    "water": SafeChoice(
        id="water",
        label="a watering can",
        prep="fetch a little watering can",
        ending="gave the peony a gentle drink",
        tags={"peony"},
    ),
    "draw": SafeChoice(
        id="draw",
        label="crayons and paper",
        prep="draw the peony instead",
        ending="made a round pink copy on the page",
        tags={"peony"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nora", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Noah", "Theo"]
TRAITS = ["curious", "gentle", "spry", "bright", "bold"]


@dataclass
class StoryParams:
    place: str
    action: str
    safe_choice: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with foreshadowing and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--safe-choice", choices=SAFE_CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            for choice in SAFE_CHOICES:
                combos.append((place, action, choice))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.safe_choice is None or c[2] == args.safe_choice)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, action, safe_choice = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, safe_choice=safe_choice, name=name, gender=gender, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="qrx", kind="character", label=params.name, type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", label="parent", type="parent"))
    peony = world.add(Entity(id="peony", label="peony", type="flower"))
    world.facts.update(child=child, parent=parent, peony=peony, action=ACTIONS[params.action], choice=SAFE_CHOICES[params.safe_choice])

    action = ACTIONS[params.action]
    choice = SAFE_CHOICES[params.safe_choice]

    introduce(world, child)
    foreshadow(world, action)
    world.para()
    want(world, action)
    warn(world, parent, action)
    if action.id == "pluck":
        world.say("The thought was mistaken, and the bloom was almost taken.")
    correct_mistake(world, action)
    world.para()
    choose_safe(world, choice)
    happy_end(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    action: Action = p["action"]  # type: ignore[assignment]
    choice: SafeChoice = p["choice"]  # type: ignore[assignment]
    return [
        'Write a short rhyming story about qrx, a peony, and a mistaken choice, with a kind ending.',
        f"Tell a foreshadowing-filled story where Qrx wants to {action.verb} but learns a safer way.",
        f"Write a gentle children's story that includes the word 'mistaken' and ends happily with {choice.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    action: Action = world.facts["action"]  # type: ignore[assignment]
    choice: SafeChoice = world.facts["choice"]  # type: ignore[assignment]
    peony = world.facts["peony"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about Qrx, a small child, and the peony in the garden.",
        ),
        QAItem(
            question="What did Qrx first want to do?",
            answer=f"Qrx wanted to {action.verb}, even though that was a mistaken idea.",
        ),
        QAItem(
            question="What did the parent worry about?",
            answer="The parent worried that the peony could get bent or bruised if Qrx grabbed it too quickly.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with Qrx choosing to {choice.prep} and the peony staying safe and fresh.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a peony?",
            answer="A peony is a flower with big, soft petals and a sweet look.",
        ),
        QAItem(
            question="What does mistaken mean?",
            answer="Mistaken means someone thought one thing was true, but it was not.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A peony is at risk when a child reaches to pluck it.
risk(pluck, peony).

% Safe choices are compatible alternatives that avoid the risky action.
safe_choice(water).
safe_choice(draw).

valid_story(Place, Action, Choice) :-
    affords(Place, Action),
    risk(Action, peony),
    safe_choice(Choice).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.indoor:
            lines.append(asp.fact("indoor", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for c in SAFE_CHOICES:
        lines.append(asp.fact("choice", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="garden", action="pluck", safe_choice="draw", name="Qrx", gender="girl", trait="curious"),
            StoryParams(place="garden", action="pluck", safe_choice="water", name="Qrx", gender="boy", trait="gentle"),
            StoryParams(place="porch", action="admire", safe_choice="draw", name="Qrx", gender="girl", trait="bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
