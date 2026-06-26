#!/usr/bin/env python3
"""
Standalone story world: orchard animal story with read / reflux / participate,
featuring suspense and a happy ending.

Premise:
- A young animal in an orchard loves reading aloud.
- After a snack, a reflux-like tummy burble makes the animal worry they may not
  join the orchard play.
- Friends and a caregiver help them slow down, rest, and still participate in a
  gentle way.
- The ending shows the animal safely rejoining the group, with calm and joy.

This script follows the storyworld contract:
- self-contained stdlib script
- StoryParams, registries, parser, resolve_params, generate, emit, main
- eager results import, lazy asp import
- inline ASP twin and Python reasonableness gate
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

ORCHARD = "the orchard"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "rabbit": {"subject": "they", "object": "them", "possessive": "their"},
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "bear": {"subject": "she", "object": "her", "possessive": "her"},
            "mouse": {"subject": "she", "object": "her", "possessive": "her"},
            "owl": {"subject": "she", "object": "her", "possessive": "her"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = ORCHARD
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "orchard": Setting(place=ORCHARD, affords={"read"}),
}

ACTIVITIES = {
    "read": Activity(
        id="read",
        verb="read the orchard signs aloud",
        gerund="reading the orchard signs",
        rush="rush toward the tree row",
        mess="dizzy",
        soil="too dizzy to play safely",
        zone={"head"},
        keyword="read",
    ),
    "reflux": Activity(
        id="reflux",
        verb="sit and rest after the reflux",
        gerund="resting with a tummy burble",
        rush="hurry to join the game too soon",
        mess="uneasy",
        soil="worse tummy trouble",
        zone={"stomach"},
        keyword="reflux",
    ),
    "participate": Activity(
        id="participate",
        verb="join the orchard game",
        gerund="participating in the orchard game",
        rush="dash into the circle",
        mess="tired",
        soil="too tired to finish",
        zone={"legs", "stomach"},
        keyword="participate",
    ),
}

PRIZES = {
    "book": Prize(
        label="book",
        phrase="a picture book about apples and birds",
        type="book",
        region="paws",
    ),
    "basket": Prize(
        label="basket",
        phrase="a little apple basket",
        type="basket",
        region="paws",
        plural=False,
    ),
}

AIDS = {
    "blanket": Aid(id="blanket", label="a soft blanket", prep="wrap up in a soft blanket", tail="stayed under the blanket"),
    "water": Aid(id="water", label="cool water", prep="take small sips of cool water", tail="drank the cool water slowly"),
    "bench": Aid(id="bench", label="the bench", prep="rest on the bench for a little while", tail="sat on the bench and breathed slowly"),
}

NAMES = ["Ruby", "Pip", "Milo", "Nina", "Toby", "Mabel", "Otis", "Luna"]
KINDS = ["rabbit", "fox", "bear", "mouse", "owl"]
TRAITS = ["curious", "gentle", "brave", "cheerful", "small", "lively"]


def reason_ok(activity: Activity, prize: Prize) -> bool:
    if activity.id == "read":
        return prize.region in {"paws"}
    if activity.id == "reflux":
        return True
    if activity.id == "participate":
        return True
    return False


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.id} does not fit a {prize.label} in a way that creates a clear orchard problem.)"


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    species: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="orchard", activity="read", prize="book", name="Ruby", species="rabbit", trait="curious"),
    StoryParams(place="orchard", activity="reflux", prize="book", name="Milo", species="fox", trait="gentle"),
    StoryParams(place="orchard", activity="participate", prize="basket", name="Nina", species="bear", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story in an orchard: read, reflux, participate.")
    ap.add_argument("--place", choices=SETTINGS.keys(), default="orchard")
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--species", choices=KINDS)
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
    if args.activity and args.prize:
        if not reason_ok(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    activity = args.activity or rng.choice(list(ACTIVITIES.keys()))
    prize = args.prize or rng.choice(list(PRIZES.keys()))
    if activity == "read":
        prize = "book"
    species = args.species or rng.choice(KINDS)
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=args.place, activity=activity, prize=prize, name=name, species=species, trait=trait)


def build_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", type=params.species, traits=[params.trait, "little"]))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type="bear", label="the caregiver"))
    prize = world.add(Entity(id="Prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, owner=hero.id, caregiver=caregiver.id))
    activity = ACTIVITIES[params.activity]
    aid = AIDS["water" if params.activity == "reflux" else "blanket"]

    world.say(f"{hero.id} was a {params.trait} little {hero.type} who loved the orchard.")
    if params.activity == "read":
        world.say(f"{hero.id} liked to {activity.gerund} beside the apple trees, and {hero.pronoun('possessive')} {prize.label} stayed tucked under {hero.pronoun('possessive')} chin.")
        world.para()
        world.say(f"One bright morning, {hero.id} came to {ORCHARD} with {hero.pronoun('possessive')} {prize.label}.")
        world.say(f"{hero.id} wanted to {activity.verb}, but a crinkly sound in the grass made {hero.pronoun('object')} pause.")
        world.say(f"Then {hero.id} found a note that said, 'Follow the red ribbon to the apple cart.'")
        world.say(f"That was the suspenseful part, because the ribbon twisted between the trees and hid the path for a moment.")
        world.para()
        world.say(f"At the cart, {hero.id} listened, read the signs aloud, and helped the others find the ripe apples.")
        world.say(f"The orchard children smiled when {hero.id} finally got to participate in the counting game.")
        world.say(f"{hero.id} ended the day with {prize.it()} held safe and {hero.pronoun('possessive')} voice warm and proud.")
        world.facts.update(action=activity, hero=hero, prize=prize, aid=aid, suspense=True, happy_end=True)
        return

    if params.activity == "reflux":
        world.say(f"After snack time, {hero.id} felt a little reflux bubble up in {hero.pronoun('possessive')} tummy.")
        world.say(f"{hero.id} had been trying to participate in the apple toss, but the burble made {hero.pronoun('object')} stop and worry.")
        world.para()
        world.say(f"A sudden rustle in the orchard made everyone look up. Was something stuck in the branches, or was it only the wind?")
        world.say(f"The caregiver hurried over with {aid.label} and a calm voice, because the little animal looked pale and unsure.")
        world.say(f"{hero.id} sat still while {hero.pronoun('possessive')} belly settled.")
        world.say(f"That quiet minute was the suspense: could {hero.id} still join the fun, or would the game end without {hero.pronoun('object')}?")
        world.para()
        world.say(f"After small sips and a rest, {hero.id} felt better.")
        world.say(f"The caregiver helped {hero.id} participate by letting {hero.pronoun('object')} ring the little bell for each apple counted.")
        world.say(f"{hero.id} smiled, and the orchard game finished with laughter, soft steps, and a happy ending.")
        world.facts.update(action=activity, hero=hero, prize=prize, aid=aid, suspense=True, happy_end=True)
        return

    world.say(f"{hero.id} wanted to {activity.verb} in {ORCHARD}, but {hero.pronoun('possessive')} tummy felt heavy after lunch.")
    world.say(f"{hero.id} could still hear the others calling, and {hero.pronoun('possessive')} paws twitched to join them.")
    world.para()
    world.say(f"Then a breeze shook the branches so hard that a few apples rolled and hid in the leaves.")
    world.say(f"Everyone searched quietly, and for a moment no one knew where the missing apples had gone.")
    world.say(f"That made the orchard feel full of suspense, because the game could not continue until the apples were found.")
    world.para()
    world.say(f"{hero.id} rested with {aid.label}, then pointed to the apples near the fence.")
    world.say(f"The friends cheered and let {hero.id} participate by gathering the last apples into {hero.pronoun('possessive')} basket.")
    world.say(f"By sunset, {hero.id} was laughing again, and the orchard glowed with a happy ending.")
    world.facts.update(action=activity, hero=hero, prize=prize, aid=aid, suspense=True, happy_end=True)


def generation_prompts(world: World) -> list[str]:
    h = world.facts["hero"]
    a = world.facts["action"]
    return [
        f"Write an animal story set in an orchard where {h.id} wants to {a.verb}.",
        f"Tell a suspenseful but gentle orchard tale that includes the words read, reflux, and participate.",
        "Write a short happy-ending story about a little animal, an orchard, and a small worry in the tummy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    a = world.facts["action"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {h.id}, a little {h.type} who loves the orchard and learns to keep going gently.",
        ),
        QAItem(
            question=f"What problem made the story suspenseful?",
            answer=f"The suspense came from a small worry: {h.id} had to pause because of {a.id} feelings or a tummy upset before joining in.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {h.id} could participate safely and the orchard game finished with smiles.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an orchard?", answer="An orchard is a place where fruit trees grow, like apple trees and pear trees."),
        QAItem(question="What does it mean to participate?", answer="To participate means to take part in an activity with other people or animals."),
        QAItem(question="What is reflux?", answer="Reflux is when food or liquid comes back up a little and can make a tummy feel uncomfortable."),
        QAItem(question="What is suspense in a story?", answer="Suspense is the feeling of wondering what will happen next."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} kind={e.kind}")
    return "\n".join(out)


ASP_RULES = r"""
suspense_story(A) :- action(A), A = read.
suspense_story(A) :- action(A), A = reflux.
suspense_story(A) :- action(A), A = participate.
happy_ending(A) :- suspense_story(A).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "orchard"),
        asp.fact("action", "read"),
        asp.fact("action", "reflux"),
        asp.fact("action", "participate"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show suspense_story/1. #show happy_ending/1."))
    atoms = set(asp.atoms(model, "suspense_story")) | set(asp.atoms(model, "happy_ending"))
    py = {("read",), ("reflux",), ("participate",)}
    if {a for a in atoms if a in py}:
        print("OK: ASP program is internally consistent.")
        return 0
    print("MISMATCH")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
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


def asp_show() -> str:
    return asp_program("#show suspense_story/1. #show happy_ending/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show suspense_story/1. #show happy_ending/1."))
        print("ASP model:")
        for a in model:
            print(a)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = rng_base + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
