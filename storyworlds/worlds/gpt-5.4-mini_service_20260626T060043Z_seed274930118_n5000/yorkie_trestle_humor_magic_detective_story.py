#!/usr/bin/env python3
"""
storyworlds/worlds/yorkie_trestle_humor_magic_detective_story.py
=================================================================

A small, self-contained detective storyworld about a clever yorkie, a trestle,
a dash of humor, and a little magic.

Premise:
- A tiny detective dog investigates a strange problem near a trestle.
- The case seems serious at first, but the clues are playful and magical.
- The answer should be a complete child-facing story with a clear turn and a
  satisfying resolution.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the trestle bridge"
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    clue: str
    event: str
    twist: str
    resolution: str
    weird: str
    funny: str
    magic: str
    keyword: str = "trestle"


@dataclass
class StoryParams:
    case: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("mystery", 0.0) >= THRESHOLD and ent.meters.get("magic", 0.0) >= THRESHOLD:
            sig = ("magic", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["glow"] = ent.meters.get("glow", 0.0) + 1
            out.append(f"A small spark of magic danced around {ent.label or ent.id}.")
    return out


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("amused", 0.0) >= THRESHOLD:
            sig = ("humor", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["joy"] = ent.memes.get("joy", 0.0) + 1
            out.append(f"{ent.label or ent.id} gave a tiny happy snort.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_magic, _r_humor):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "trestle": Setting(place="the trestle bridge", outdoor=True, affords={"investigate", "search"}),
    "riverbank": Setting(place="the riverbank under the trestle", outdoor=True, affords={"investigate", "search"}),
    "station": Setting(place="the little station by the tracks", outdoor=True, affords={"investigate", "search"}),
}

CASES = {
    "missing_cookie": Case(
        id="missing_cookie",
        clue="a crumb trail that kept turning into tiny paw prints",
        event="a cookie vanished from the picnic bench",
        twist="the trail led to a hat that giggled when touched",
        resolution="the hat was enchanted and hiding the cookie for a surprise",
        weird="a giggling hat",
        funny="the yorkie sneezed so hard the clue map spun like a wheel",
        magic="the hat blinked with blue sparkles",
    ),
    "vanishing_harmonica": Case(
        id="vanishing_harmonica",
        clue="a cheerful tune heard under the boards",
        event="a harmonica disappeared from a fisherman’s coat",
        twist="the tune came from a tiny lantern with a grin",
        resolution="the lantern was magical and had borrowed the harmonica to play along",
        weird="a grinning lantern",
        funny="the yorkie barked once, then twice, as if asking the mystery to please stand still",
        magic="the lantern glowed green and hummed a song",
    ),
    "sleepy_bell": Case(
        id="sleepy_bell",
        clue="a bell that rang only when nobody was looking",
        event="the bridge keeper could not find his lunch bell",
        twist="the bell had hidden inside a rubber boot and was making sleepy noises",
        resolution="a charm in the boot made the bell nap there by accident",
        weird="a sleepy boot",
        funny="the yorkie tiptoed so carefully that even the river seemed to hold its breath",
        magic="the boot softly shimmered with moonlight",
    ),
}

NAMES = ["Pip", "Milo", "Tilly", "Nell", "Daisy", "Benny", "Ruby", "Scout"]


def build_case(world: World, case: Case, name: str) -> None:
    dog = world.add(Entity(id=name, kind="animal", type="yorkie", label=f"little yorkie {name}"))
    keeper = world.add(Entity(id="keeper", kind="character", type="man", label="the bridge keeper"))
    clue = world.add(Entity(id="clue", type="thing", label="clue", phrase=case.clue))
    treasure = world.add(Entity(id="treasure", type="thing", label="lost thing", phrase=case.event, caretaker=keeper.id))
    magic_obj = world.add(Entity(id="magic_obj", type="thing", label=case.weird, phrase=case.magic))
    dog.memes["curious"] = 1
    dog.memes["mystery"] = 1
    magic_obj.meters["magic"] = 1
    magic_obj.memes["amused"] = 1
    world.facts.update(dog=dog, keeper=keeper, clue=clue, treasure=treasure, magic_obj=magic_obj, case=case)


def tell(case: Case, name: str) -> World:
    world = World(SETTINGS["trestle"])
    build_case(world, case, name)
    dog: Entity = world.facts["dog"]
    keeper: Entity = world.facts["keeper"]
    magic_obj: Entity = world.facts["magic_obj"]

    world.say(f"{dog.label.capitalize()} was a little detective who loved sniffing out strange clues.")
    world.say(f"One day, {keeper.label} had a problem: {case.event}.")
    world.say(f"{dog.pronoun().capitalize()} hurried to {world.setting.place}, where {case.clue} waited like a secret.")
    world.para()
    world.say(f"{case.funny.capitalize()}.")
    world.say(f"{dog.pronoun().capitalize()} followed the clue, but then {case.twist}.")
    dog.memes["mystery"] += 1
    dog.meters["search"] = dog.meters.get("search", 0.0) + 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"At last, {dog.label} solved the case: {case.resolution}.")
    world.say(f"The silly answer made {keeper.label} laugh, and {dog.pronoun().subject if False else 'the yorkie'} wagged with pride.")
    world.say(f"By the end, {magic_obj.label} still shone softly, and the trestle felt like the friendliest place in town.")
    dog.memes["joy"] = dog.memes.get("joy", 0.0) + 1
    keeper.memes["relief"] = keeper.memes.get("relief", 0.0) + 1
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    dog: Entity = world.facts["dog"]
    return [
        f'Write a short detective story for a child about a yorkie named {dog.id} at the trestle.',
        f"Tell a funny mystery with magic where {dog.label} follows {case.clue} and solves {case.event}.",
        f"Write a gentle detective tale that includes the word \"trestle\" and ends with a magical reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    dog: Entity = world.facts["dog"]
    keeper: Entity = world.facts["keeper"]
    magic_obj: Entity = world.facts["magic_obj"]
    return [
        QAItem(
            question=f"Who solved the mystery at the trestle?",
            answer=f"The little yorkie named {dog.id} solved it by following the clue and thinking carefully.",
        ),
        QAItem(
            question=f"What was the problem {keeper.label} needed help with?",
            answer=f"{case.event.capitalize()}. {dog.id} investigated it like a tiny detective.",
        ),
        QAItem(
            question=f"What magical thing made the case funny instead of scary?",
            answer=f"It was {magic_obj.label}, because {case.magic}. That magical clue turned the mystery into a playful surprise.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{case.resolution.capitalize()}. {keeper.label} laughed, and {dog.id} stood proudly by the trestle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trestle?",
            answer="A trestle is a bridge or support structure, often made with strong beams, that helps carry weight across water or land.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is when something unusual or impossible happens, like a charm, sparkle, or enchanted object.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_case(C) :- case(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_case/1."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    py = {(cid,) for cid in CASES}
    cl = set(asp_valid_cases())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} cases).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def valid_cases() -> list[str]:
    return list(CASES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with a yorkie, a trestle, humor, and magic.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name", choices=NAMES)
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
    case = args.case or rng.choice(sorted(CASES))
    name = args.name or rng.choice(NAMES)
    return StoryParams(case=case, name=name)


def generate(params: StoryParams) -> StorySample:
    case = CASES[params.case]
    world = tell(case, params.name)
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
    StoryParams(case="missing_cookie", name="Pip"),
    StoryParams(case="vanishing_harmonica", name="Tilly"),
    StoryParams(case="sleepy_bell", name="Scout"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_case/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_cases()
        print(f"{len(triples)} valid cases:")
        for (cid,) in triples:
            print(f"  {cid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.case}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
