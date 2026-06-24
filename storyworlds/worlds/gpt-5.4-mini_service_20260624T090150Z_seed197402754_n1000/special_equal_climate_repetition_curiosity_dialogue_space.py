#!/usr/bin/env python3
"""
A small Space-Adventure storyworld about a curious child who helps a station
keep its climate equal and discovers something special along the way.

The premise:
- A child on a space station notices that one habitat is too warm and another is
  too chilly.
- A careful climate console can equalize the rooms.
- The child is curious, asks questions, and talks with a helper.
- Repetition matters: the child checks the same dials again and again until the
  climate settles into balance.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pilot-girl"}
        male = {"boy", "father", "man", "pilot-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    glow: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    kind: str
    action: str
    effect: str
    equalizes: set[str]
    target: str
    special_note: str = ""


@dataclass
class StoryParams:
    place: str
    device: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_steps: list[str] = []

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbital_hub": Setting(
        place="the orbital hub",
        glow="silver light",
        affords={"balance", "inspect", "talk"},
    ),
    "ice_ring": Setting(
        place="the ice ring",
        glow="blue light",
        affords={"balance", "inspect", "talk"},
    ),
    "sun_dock": Setting(
        place="the sun dock",
        glow="gold light",
        affords={"balance", "inspect", "talk"},
    ),
    "greenhouse_bay": Setting(
        place="the greenhouse bay",
        glow="green light",
        affords={"balance", "inspect", "talk"},
    ),
}

DEVICES = {
    "climate_wheel": Device(
        id="climate_wheel",
        label="climate wheel",
        kind="console",
        action="turn the climate wheel again and again",
        effect="equalize the air",
        equalizes={"warm", "cold"},
        target="climate",
        special_note="It is a special wheel with bright arrows.",
    ),
    "sun_shade": Device(
        id="sun_shade",
        label="sun shade panel",
        kind="panel",
        action="slide the shade panel back and forth",
        effect="make the room equal",
        equalizes={"hot", "bright"},
        target="light",
        special_note="It can keep the sun from shining too hard.",
    ),
    "mist_pipe": Device(
        id="mist_pipe",
        label="mist pipe",
        kind="pipe",
        action="tap the mist pipe twice",
        effect="balance the climate",
        equalizes={"dry", "warm"},
        target="air",
        special_note="A little mist helps the air feel fair.",
    ),
}

TRAITS = ["curious", "brave", "careful", "lively", "bright", "patient"]
NAMES_GIRL = ["Mia", "Nova", "Lina", "Zoe", "Ava", "Luna"]
NAMES_BOY = ["Kai", "Finn", "Eli", "Noah", "Leo", "Jett"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def pronoun_gender(gender: str) -> str:
    return {"girl": "girl", "boy": "boy"}[gender]


def activity_room(setting: Setting) -> str:
    return f"{setting.place} glowed with {setting.glow}."


def narrator_intro(hero: Entity) -> str:
    return f"{hero.id} was a little {hero.pronoun('possessive')} own kind of space kid, always looking up at new things."


def dialogue(a: str, b: str) -> str:
    return f'"{a}" {b}'


def is_balanced(world: World) -> bool:
    return abs(world.facts.get("warmth", 0.0) - world.facts.get("coolness", 0.0)) <= 0.25


def predict_balance(world: World, device: Device) -> bool:
    sim = world.copy()
    apply_device(sim, device, narrate=False)
    return is_balanced(sim)


def apply_device(world: World, device: Device, narrate: bool = True) -> None:
    key = ("device", device.id)
    if key in world.fired:
        return
    world.fired.add(key)

    world.facts["balance_steps"] = world.facts.get("balance_steps", 0) + 1
    if device.id == "climate_wheel":
        world.facts["warmth"] = max(0.0, world.facts.get("warmth", 0.0) - 0.5)
        world.facts["coolness"] = max(0.0, world.facts.get("coolness", 0.0) - 0.5)
        world.say("The child turned the climate wheel once, then checked the lights.")
        world.say("The child turned it again, because the rooms still did not feel equal.")
    elif device.id == "sun_shade":
        world.facts["warmth"] = max(0.0, world.facts.get("warmth", 0.0) - 0.4)
        world.facts["glare"] = max(0.0, world.facts.get("glare", 0.0) - 0.7)
        world.say("The panel slid open and shut in a neat rhythm.")
        world.say("The room grew calmer each time the shade moved.")
    elif device.id == "mist_pipe":
        world.facts["coolness"] = max(0.0, world.facts.get("coolness", 0.0) - 0.3)
        world.facts["dryness"] = max(0.0, world.facts.get("dryness", 0.0) - 0.8)
        world.say("A soft mist puffed out, thin as a cloudlet.")
        world.say("The air felt kinder after the second tap.")
    world.trace_steps.append(f"used {device.id}")
    if narrate:
        world.say("They checked the console again to see if the climate was equal.")


def set_problem(world: World, place: str) -> None:
    if place == "orbital_hub":
        world.facts.update(warmth=1.2, coolness=0.2, glare=0.6, dryness=0.3)
    elif place == "ice_ring":
        world.facts.update(warmth=0.2, coolness=1.3, glare=0.1, dryness=0.8)
    elif place == "sun_dock":
        world.facts.update(warmth=1.0, coolness=0.4, glare=1.1, dryness=0.5)
    else:
        world.facts.update(warmth=0.7, coolness=0.7, glare=0.2, dryness=0.2)


def solve_climate(world: World, hero: Entity, helper: Entity, device: Device) -> None:
    world.say(narrator_intro(hero))
    world.say(activity_room(world.setting))
    world.say(f"{hero.id} noticed that the climate was not equal in the station rooms.")
    world.para()
    world.say(f"{hero.id} wanted to know why the air felt so uneven, so {hero.pronoun()} asked {helper.id}, {dialogue('Why is one room warm and the other one cold?', f'{helper.pronoun('subject').capitalize()} said.')}")

    helper_line = {
        "girl": "Let's fix it together, one careful check at a time.",
        "boy": "Let's make it equal step by step.",
    }[helper.type if helper.type in {"girl", "boy"} else "girl"]
    world.say(f"{helper.id} smiled and said, {dialogue(helper_line, f'{helper.pronoun('subject').capitalize()} replied.')}")
    world.para()

    apply_device(world, device, narrate=True)
    if not is_balanced(world):
        world.say(f"{hero.id} frowned, because the climate was still not equal.")
        world.say(f"So {hero.id} tried the same special control again.")
        apply_device(world, device, narrate=True)

    if not is_balanced(world):
        world.say(f"{helper.id} pointed to a tiny warning light and said, {dialogue('Once more.', f'{helper.pronoun('subject').capitalize()} whispered.')}")
        apply_device(world, device, narrate=True)

    world.para()
    world.say(f"At last, the rooms felt equal and calm.")
    world.say(f"{hero.id} looked out the window and saw something special: a small star garden shining in steady light.")
    world.say(f"{hero.id} smiled at {helper.id}, and {helper.id} smiled back, because the climate stayed fair for everyone.")


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_story(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    device = DEVICES[params.device]
    world = World(setting)
    set_problem(world, params.place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        pronoun="",
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="boy" if params.gender == "girl" else "girl",
        label=params.helper,
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        device=device,
        place=setting.place,
        special_word="special",
        equal_word="equal",
        climate_word="climate",
    )

    solve_climate(world, hero, helper, device)

    story = world.render()
    prompts = generation_prompts(world)
    story_qa = make_story_qa(world)
    world_qa = make_world_qa(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    device: Device = f["device"]
    return [
        f'Write a short space adventure for a young child about "{f["special_word"]}" climate tools.',
        f"Tell a story where {hero.id} and {helper.id} try to make the climate equal using {device.label}.",
        f"Write a gentle story with curiosity, dialogue, and repetition on a space station.",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    device: Device = world.facts["device"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"What did {hero.id} notice at {place}?",
            answer=f"{hero.id} noticed that the climate was not equal, so the rooms felt different from each other.",
        ),
        QAItem(
            question=f"Who did {hero.id} ask for help?",
            answer=f"{hero.id} asked {helper.id} for help because {helper.id} knew how to use the {device.label}.",
        ),
        QAItem(
            question=f"How did the child fix the climate?",
            answer=f"{hero.id} used the {device.label} again and again until the climate became equal.",
        ),
        QAItem(
            question=f"What special thing did {hero.id} see at the end?",
            answer=f"{hero.id} saw a special star garden shining in steady light once the climate was balanced.",
        ),
    ]


def make_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does climate mean in a space station?",
            answer="Climate means the way the air feels, such as warm, cool, dry, or misty, in a room or habitat.",
        ),
        QAItem(
            question="Why do people check the same controls more than once?",
            answer="People check the same controls more than once to make sure the result is really balanced and safe.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions and learn what is going on.",
        ),
    ]


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    device: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld: special climate, equal balance, curious dialogue.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--device", choices=DEVICES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    device = args.device or rng.choice(list(DEVICES.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(NAMES_BOY if gender == "girl" else NAMES_GIRL)
    if helper == name:
        helper = (NAMES_BOY if gender == "girl" else NAMES_GIRL)[0]
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, device=device, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    lines.append(f"steps={world.trace_steps}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
device(D) :- climate_device(D).
story_ok(P,D) :- place(P), device(D), affords(P, balance), equalizes(D, climate).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for did, d in DEVICES.items():
        lines.append(asp.fact("climate_device", did))
        lines.append(asp.fact("equalizes", did, "climate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    asp_set = set(asp.atoms(model, "story_ok"))
    py_set = {(p, d) for p in SETTINGS for d in DEVICES}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python registry ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="orbital_hub", device="climate_wheel", name="Nova", gender="girl", helper="Kai", trait="curious"),
    StoryParams(place="ice_ring", device="mist_pipe", name="Leo", gender="boy", helper="Mia", trait="patient"),
    StoryParams(place="sun_dock", device="sun_shade", name="Ava", gender="girl", helper="Finn", trait="bright"),
    StoryParams(place="greenhouse_bay", device="climate_wheel", name="Jett", gender="boy", helper="Luna", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible place-device pairs:")
        for p, d in pairs:
            print(f"  {p}  {d}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} using {p.device}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
