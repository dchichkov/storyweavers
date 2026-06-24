#!/usr/bin/env python3
"""
A small storyworld about a child, a mystery, and a flatter who tries to smooth
things over with too-sweet words.

Seed premise:
- A little story unfolds through dialogue.
- Someone flatters everyone, but something has gone missing.
- The clues, suspects, and ending are driven by the simulated world state.
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
    kind: str = "thing"  # "character" | "thing"
    role: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    afford: str


@dataclass
class Mystery:
    id: str
    missing: str
    hiding_places: list[str]
    clue: str
    reveal_place: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    culprit: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "library": Setting(place="the library", mood="quiet", afford="whispers"),
    "kitchen": Setting(place="the kitchen", mood="busy", afford="crumbs"),
    "garden": Setting(place="the garden", mood="windy", afford="petals"),
}

MYSTERIES = {
    "cookie": Mystery(
        id="cookie",
        missing="the last cookie",
        hiding_places=["jar", "chair", "shelf"],
        clue="a crumb trail",
        reveal_place="under the chair",
    ),
    "ribbon": Mystery(
        id="ribbon",
        missing="the blue ribbon",
        hiding_places=["book", "basket", "pillow"],
        clue="a blue thread on the floor",
        reveal_place="inside the basket",
    ),
    "key": Mystery(
        id="key",
        missing="the little brass key",
        hiding_places=["mug", "drawer", "rug"],
        clue="a tiny shine by the rug",
        reveal_place="under the rug",
    ),
}

CULPRITS = {
    "cat": "cat",
    "brother": "brother",
    "neighbor": "neighbor",
}

HELPERS = ["grandmother", "friend", "teacher", "brother"]
GIRL_NAMES = ["Mia", "Luna", "Nora", "Ava", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Owen", "Theo", "Max"]
TRAITS = ["curious", "careful", "brave", "gentle", "clever"]


def _do_mislead(world: World, flatter: Entity, suspect: Entity) -> None:
    flatter.memes["flattery"] = flatter.memes.get("flattery", 0.0) + 1
    suspect.memes["smile"] = suspect.memes.get("smile", 0.0) + 1
    world.say(
        f'"Oh, {suspect.id}, you are so smart," {flatter.id} said. '
        f'"You would never make a mess like that."'
    )


def _do_clue(world: World, mystery: Mystery, setting: Setting) -> None:
    world.say(
        f'Then {world.facts["hero"].id} noticed {mystery.clue} near {setting.place}.'
    )


def _do_search(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["search"] = hero.meters.get("search", 0.0) + 1
    world.say(f'"Let me look again," {hero.id} said.')
    world.say(f'{hero.pronoun().capitalize()} checked the {mystery.hiding_places[0]}, then the {mystery.hiding_places[1]}.')
    world.say(f'But the clue pointed somewhere else.')


def _do_reveal(world: World, hero: Entity, mystery: Mystery, culprit: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    culprit.memes["caught"] = culprit.memes.get("caught", 0.0) + 1
    world.say(
        f'"Aha," {hero.id} said. "The {mystery.missing} is {mystery.reveal_place}!"'
    )
    world.say(
        f'The {culprit.role} stared down, and the sweet words stopped sounding so helpful.'
    )


def _do_end(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f'"Thank you," {hero.id} said to {helper.id}. '
        f'"I found {mystery.missing}, and now the room feels calm again."'
    )
    world.say(
        f'{helper.id} smiled, and the little mystery ended with everything back in its place.'
    )


ASP_RULES = r"""
flatter(X) :- character(X), flattery(X).
suspect(X) :- character(X), not helper(X).
clue_seen(M) :- mystery(M), clue(M).
solved(M) :- mystery(M), clue_seen(M), reveal(M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("mood", sid, s.mood))
        lines.append(asp.fact("afford", sid, s.afford))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("reveal", mid, m.reveal_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solved/1."))
    solved = sorted(set(asp.atoms(model, "solved")))
    if solved == [(mid,) for mid in sorted(MYSTERIES)]:
        print("OK: ASP twin can derive solved/1 for the registry facts.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected facts.")
    print(solved)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small dialogue mystery with a flatter.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, culprit=culprit, name=name, gender=gender, helper=helper)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", role=params.gender))
    flatter = world.add(Entity(id="Flatter", kind="character", role="person"))
    culprit = world.add(Entity(id=params.culprit, kind="character", role=params.culprit))
    helper = world.add(Entity(id=params.helper, kind="character", role="person"))
    missing = world.add(Entity(id=mystery.id, kind="thing", label=mystery.missing, owner=culprit.id))

    world.facts.update(hero=hero, flatter=flatter, culprit=culprit, helper=helper, mystery=mystery, missing=missing)

    hero.memes["curiosity"] = 1
    world.say(f'It was a {setting.mood} morning at {setting.place}.')
    world.say(f'{hero.id} looked around and said, "{mystery.missing} was here a minute ago."')
    world.say(f'{helper.id} frowned. "{It} should not have vanished like that."'.replace("{It}", "It"))

    world.para()
    _do_mislead(world, flatter, culprit)
    world.say(f'"That sounds nice," {culprit.id} said, but the answer did not feel right.')
    world.say(f'{hero.id} squinted at the floor. "Nice words do not match missing things," {hero.id} whispered.')

    world.para()
    _do_clue(world, mystery, setting)
    _do_search(world, hero, mystery)
    _do_reveal(world, hero, mystery, culprit)
    _do_end(world, hero, helper, mystery)

    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child about {f["hero"].id} at {world.setting.place}.',
        f'Write dialogue-filled story where someone says too many flattering things, but a clue still leads to the answer.',
        f'Create a simple mystery about {f["mystery"].missing} that ends with the missing thing found again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    culprit: Entity = f["culprit"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Where did {hero.id} look for {mystery.missing} first?",
            answer=f"{hero.id} looked around at {world.setting.place} first, then checked the first hiding places while listening for clues.",
        ),
        QAItem(
            question=f"Why did the story sound suspicious when {culprit.id} got such sweet words?",
            answer=f"The sweet words sounded suspicious because {culprit.id} was being praised instead of giving a clear answer about {mystery.missing}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} at the end of the mystery?",
            answer=f"{helper.id} helped by listening, watching the clue, and staying calm until {hero.id} found the missing thing.",
        ),
        QAItem(
            question=f"What was finally discovered in the ending?",
            answer=f"{hero.id} found {mystery.missing} {mystery.reveal_place}, and the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does it mean to flatter someone?",
            answer="To flatter someone means to say very sweet things to make them feel pleased, even if the praise is too much.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind} {e.role} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(setting="library", mystery="key", culprit="cat", name="Mia", gender="girl", helper="teacher"),
    StoryParams(setting="kitchen", mystery="cookie", culprit="brother", name="Leo", gender="boy", helper="grandmother"),
    StoryParams(setting="garden", mystery="ribbon", culprit="neighbor", name="Nora", gender="girl", helper="friend"),
]


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
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.setting}/{p.mystery}/{p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
