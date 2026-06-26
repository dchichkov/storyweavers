#!/usr/bin/env python3
"""
storyworlds/worlds/repulse_barf_elevator_surprise_tall_tale.py
==============================================================

A tall-tale story world set in an elevator, where a surprising mishap,
a strong repulse reaction, and a barf scare can be resolved by quick
thinking and one very unlikely helper.

Seed tale sketch:
---
A tiny elevator in a big building was packed with riders, and every trip felt
like a little adventure. One day, a proud child rode up with a shiny snack and a
very brave grin. Then a bump, a surprise, and a sick feeling sent the ride into
a commotion. People stepped back in disgust. The child found a way to ask for
space, clean up the mess, and turn the whole thing into an enormous tale by the
time the doors opened again.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "shock": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "surprise": 0.0, "repulse": 0.0, "embarrass": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "gentleman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class PersonSpec:
    name: str
    type: str
    trait: str


@dataclass
class Setting:
    place: str = "the elevator"
    affords: set[str] = field(default_factory=lambda: {"ride", "surprise"})


@dataclass
class SnackSpec:
    label: str
    phrase: str
    type: str = "snack"


@dataclass
class EventSpec:
    id: str
    trigger: str
    response: str
    mess: str
    emotional_shift: str
    surprise_line: str


@dataclass
class StoryParams:
    person_name: str
    person_type: str
    trait: str
    helper_name: str
    helper_type: str
    snack: str
    event: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


EVENTS = {
    "barf": EventSpec(
        id="barf",
        trigger="suddenly felt sick",
        response="barfed",
        mess="mess",
        emotional_shift="shock",
        surprise_line="The elevator gave a tiny lurch, and surprise hit like a hat off a windy fence.",
    ),
}

SNACKS = {
    "pretzel": SnackSpec(label="pretzel", phrase="a salty pretzel"),
    "candy": SnackSpec(label="candy", phrase="a bright wrapped candy"),
    "cookie": SnackSpec(label="cookie", phrase="a crumbly cookie"),
    "lemonade": SnackSpec(label="lemonade", phrase="a tiny paper cup of lemonade"),
}

PEOPLE = [
    PersonSpec("Milo", "boy", "bold"),
    PersonSpec("Ada", "girl", "curious"),
    PersonSpec("Nell", "girl", "spunky"),
    PersonSpec("Otis", "boy", "lively"),
    PersonSpec("June", "girl", "cheerful"),
    PersonSpec("Bert", "boy", "brave"),
]

HELPERS = [
    PersonSpec("Mrs. Wren", "woman", "patient"),
    PersonSpec("Mr. Pike", "man", "kind"),
    PersonSpec("The Bellhop", "man", "quick"),
    PersonSpec("Aunt Tilly", "woman", "steady"),
]

TRAITS = ["bold", "curious", "spunky", "lively", "cheerful", "brave"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.event not in EVENTS:
        raise StoryError("unknown event")
    if params.snack not in SNACKS:
        raise StoryError("unknown snack")
    if params.person_type not in {"boy", "girl"}:
        raise StoryError("the rider must be a child for this tale")
    if params.helper_type not in {"man", "woman"}:
        raise StoryError("the helper must be a grown-up for this tale")


def valid_combos() -> list[tuple[str, str, str]]:
    return [("elevator", "barf", snack_id) for snack_id in SNACKS]


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "elevator"),
        asp.fact("event", "barf"),
        asp.fact("affords", "elevator", "ride"),
        asp.fact("affords", "elevator", "surprise"),
    ]
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Event, Snack) :- setting(Place), event(Event), snack(Snack), affords(Place, ride), affords(Place, surprise).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world set in an elevator.")
    ap.add_argument("--person", choices=[p.name for p in PEOPLE])
    ap.add_argument("--helper", choices=[h.name for h in HELPERS])
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
    person = next((p for p in PEOPLE if p.name == args.person), None) if args.person else rng.choice(PEOPLE)
    helper = next((h for h in HELPERS if h.name == args.helper), None) if args.helper else rng.choice(HELPERS)
    snack = args.snack or rng.choice(list(SNACKS))
    event = args.event or "barf"
    trait = args.trait or person.trait
    gender = args.gender or person.type
    helper_gender = args.helper_gender or helper.type
    if args.person and args.gender and args.gender != person.type:
        raise StoryError("the chosen person's gender does not match the selected character")
    if args.helper and args.helper_gender and args.helper_gender != helper.type:
        raise StoryError("the chosen helper gender does not match the selected helper")
    reasonableness_gate(StoryParams(person.name, gender, trait, helper.name, helper_gender, snack, event))
    return StoryParams(
        person_name=args.name or person.name,
        person_type=gender,
        trait=trait,
        helper_name=args.helper_name or helper.name,
        helper_type=helper_gender,
        snack=snack,
        event=event,
    )


def build_story(world: World, params: StoryParams) -> None:
    child = world.add(Entity(id="child", kind="character", type=params.person_type, label=params.person_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    snack = world.add(Entity(id="snack", type="snack", label=SNACKS[params.snack].label, phrase=SNACKS[params.snack].phrase, owner=child.id))

    event = EVENTS[params.event]
    child.meters["joy"] += 1
    world.say(f"{params.person_name} was a {params.trait} little {params.person_type} who lived near the top floor, where the elevator hummed like a bee in a tin hat.")
    world.say(f"{params.person_name} carried {snack.phrase} into {world.setting.place}, because a small snack in a big elevator can feel like a grand feast.")
    world.say(f"{params.person_name} smiled at {params.helper_name} and said the ride would be easy as a feather on a moonbeam.")

    world.para()
    child.memes["surprise"] += 1
    world.say(f"Then the elevator gave a tiny shiver, and {event.surprise_line}")
    world.say(f"Before anyone could blink, {params.person_name} {event.trigger}, and the whole car turned still as a storybook page.")
    child.meters["mess"] += 1
    child.memes["embarrass"] += 1
    helper.memes["repulse"] += 1
    world.say(f"{params.helper_name} stepped back in repulse, because elevator floors are poor places for a {event.response} surprise.")
    world.say(f"Even the buttons seemed to gasp, though of course buttons do not gossip.")

    world.para()
    helper.memes["care"] += 1
    child.memes["surprise"] += 1
    world.say(f"Then {params.helper_name} waved everyone calm and said, \"Let's give {params.person_name} some space and fix this fast.\"")
    world.say(f"{params.person_name} pointed to the corner, found a napkin from the snack, and cleaned up the little mess with great care.")
    child.meters["clean"] += 1
    child.memes["embarrass"] = max(0.0, child.memes["embarrass"] - 1)
    helper.memes["repulse"] = 0.0
    world.say(f"By the time the doors opened, {params.person_name} stood taller than a parade flag, and the elevator smelled like fresh courage instead of trouble.")
    world.say(f"That day became a tall tale: one tiny ride, one big surprise, one barf scare, and one brave child who left the car clean enough for the next adventure.")

    world.facts.update(child=child, helper=helper, snack=snack, event=event, params=params)


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a tall-tale story set in an elevator that includes the words "surprise" and "{p.event}".',
        f"Tell a funny, child-friendly story where {p.person_name} rides an elevator, gets a sudden {p.event}, and a grown-up helps clean up the repulse-worthy mess.",
        f"Write a short story about {p.person_name} in {world.setting.place} with a big surprise and a brave cleanup.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    snack: Entity = world.facts["snack"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was riding the elevator with {snack.label}?",
            answer=f"{p.person_name} was riding the elevator with {snack.phrase}.",
        ),
        QAItem(
            question=f"What surprised everyone in the elevator?",
            answer=f"A sudden {p.event} surprise startled everyone and made the grown-up step back in repulse.",
        ),
        QAItem(
            question=f"How did {p.person_name} fix the trouble?",
            answer=f"{p.person_name} used a napkin, cleaned up the mess, and grew brave enough to stand tall when the doors opened.",
        ),
        QAItem(
            question=f"How did {p.helper_name} help?",
            answer=f"{p.helper_name} gave space, kept calm, and helped turn the scary elevator moment into a clean ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an elevator?",
            answer="An elevator is a machine that carries people up and down in a building.",
        ),
        QAItem(
            question="What does repulse mean?",
            answer="To repulse is to make someone step back because something feels yucky, shocking, or unpleasant.",
        ),
        QAItem(
            question="Why do people clean up a mess in a shared place?",
            answer="People clean up shared spaces so everyone can use them safely and comfortably after the trouble passes.",
        ),
        QAItem(
            question="What is surprise?",
            answer="Surprise is a sudden feeling that happens when something unexpected appears or occurs.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.type:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_verify_story() -> int:
    return asp_verify()


def generate(params: StoryParams) -> StorySample:
    world = World(Setting())
    build_story(world, params)
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


CURATED = [
    StoryParams(person_name="Milo", person_type="boy", trait="bold", helper_name="Mrs. Wren", helper_type="woman", snack="pretzel", event="barf"),
    StoryParams(person_name="Ada", person_type="girl", trait="curious", helper_name="Mr. Pike", helper_type="man", snack="cookie", event="barf"),
    StoryParams(person_name="Nell", person_type="girl", trait="spunky", helper_name="The Bellhop", helper_type="man", snack="candy", event="barf"),
    StoryParams(person_name="Otis", person_type="boy", trait="lively", helper_name="Aunt Tilly", helper_type="woman", snack="lemonade", event="barf"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify_story())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, event, snack) combos:\n")
        for place, event, snack in combos:
            print(f"  {place:10} {event:8} {snack}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.person_name}: {p.event} in the elevator"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
