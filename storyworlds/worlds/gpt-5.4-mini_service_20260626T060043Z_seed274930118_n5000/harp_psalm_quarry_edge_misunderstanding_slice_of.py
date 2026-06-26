#!/usr/bin/env python3
"""
Standalone storyworld: quarry-edge misunderstanding with a harp and a psalm.

A small slice-of-life domain where a child or young helper sees a harp and hears
a psalm at the quarry edge, misunderstands what is happening, and then learns
the gentler truth.

The simulated world tracks both physical meters and emotional memes. The story
is generated from world state rather than from a fixed paragraph template.
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

QUARRY_EDGE = "the quarry edge"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = QUARRY_EDGE
    echoes: bool = True
    has_harp: bool = True
    has_psalm: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    observer_role: str
    singer_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        other = World(self.scene)
        import copy

        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _rule_worry(world: World) -> list[str]:
    out: list[str] = []
    for observer in world.characters():
        if observer.memes.get("misunderstanding", 0.0) < THRESHOLD:
            continue
        sig = ("worry", observer.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(observer, "worry", 1.0)
        out.append(f"{observer.id} felt a little worried and looked toward the sound.")
    return out


def _rule_relief(world: World) -> list[str]:
    out: list[str] = []
    for observer in world.characters():
        if observer.memes.get("understanding", 0.0) < THRESHOLD:
            continue
        sig = ("relief", observer.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(observer, "relief", 1.0)
        out.append(f"{observer.id} relaxed at once, because the truth was kinder than the guess.")
    return out


RULES = [_rule_worry, _rule_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            produced = rule(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class CatalogItem:
    id: str
    label: str
    phrase: str
    kind: str


PEOPLE = {
    "girl": ["Mina", "Lena", "Tia", "Nora", "Elsie"],
    "boy": ["Owen", "Theo", "Ben", "Eli", "Sam"],
}

ROLES = {
    "worker": "worker",
    "neighbor": "neighbor",
    "grandparent": "grandparent",
    "singer": "singer",
}

TRAITS = ["careful", "quiet", "gentle", "curious", "steady"]


HARP = CatalogItem(
    id="harp",
    label="harp",
    phrase="a small harp with bright strings",
    kind="instrument",
)

PSALM = CatalogItem(
    id="psalm",
    label="psalm",
    phrase="a soft psalm sung in a low voice",
    kind="song",
)


def valid_combos() -> list[tuple[str, str]]:
    return [("quarry_edge", "harp_psalm")]


def explain_rejection(place: str, feature: str) -> str:
    return f"(No story: this world is built for the quarry edge and the harp-psalm misunderstanding.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life quarry-edge misunderstanding storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--observer-role", choices=list(ROLES))
    ap.add_argument("--singer-role", choices=list(ROLES))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(PEOPLE[gender])
    observer_role = args.observer_role or rng.choice(["worker", "neighbor", "grandparent"])
    singer_role = args.singer_role or rng.choice(["worker", "neighbor", "grandparent", "singer"])
    if observer_role == singer_role:
        singer_role = "singer" if observer_role != "singer" else "worker"
    return StoryParams(name=name, gender=gender, observer_role=observer_role, singer_role=singer_role)


def _choose_singer_role(role: str) -> str:
    return ROLES.get(role, role)


def generate(params: StoryParams) -> StorySample:
    world = World(Scene())
    observer = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "curious"]))
    singer_name = {
        "worker": "Jory",
        "neighbor": "Mara",
        "grandparent": "Grandpa Sol",
        "singer": "Iris",
    }[params.singer_role]
    singer_type = "man" if params.singer_role in {"worker", "grandparent"} else "woman"
    singer = world.add(Entity(id=singer_name, kind="character", type=singer_type, traits=["quiet", "gentle"]))
    harp = world.add(Entity(id="harp", type="instrument", label="harp", phrase=HARP.phrase, owner=singer.id))
    psalm = world.add(Entity(id="psalm", type="song", label="psalm", phrase=PSALM.phrase, owner=singer.id))

    world.say(
        f"{observer.id} went to {QUARRY_EDGE} with a tin cup and found {singer.id} sitting on a flat stone."
    )
    world.say(
        f"Beside {singer.pronoun('object')}, a harp rested in the dust, and a psalm drifted out over the rocks."
    )
    _add_meme(observer, "curiosity", 1.0)
    _add_meme(observer, "misunderstanding", 1.0)
    world.say(
        f"{observer.id} frowned, because the music sounded so serious that {observer.pronoun()} thought something was wrong."
    )

    world.para()
    _add_meter(observer, "steps", 1.0)
    _add_meme(observer, "helpfulness", 1.0)
    world.say(
        f"{observer.id} hurried closer and asked if {singer.pronoun('subject')} was hurt, tired, or looking for a missing tool."
    )
    world.say(
        f"{singer.id} blinked, then laughed softly. {singer.pronoun().capitalize()} said the psalm was just for morning comfort, and the harp was only for practice."
    )
    _add_meme(observer, "understanding", 1.0)
    _add_meme(singer, "warmth", 1.0)
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{observer.id} sat on a warm block of stone and listened until the last note faded between the quarry walls."
    )
    world.say(
        f"Then {observer.pronoun()} sipped the tin cup dry while {singer.id} played one more gentle chorus, and the edge of the quarry felt almost like a porch at home."
    )

    world.facts.update(
        observer=observer,
        singer=singer,
        harp=harp,
        psalm=psalm,
        scene=world.scene,
        params=params,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    observer = f["observer"]
    singer = f["singer"]
    return [
        "Write a short slice-of-life story about a child at the quarry edge who misreads a harp and a psalm, then learns the truth.",
        f"Tell a gentle story where {observer.id} sees {singer.id} with a harp at the quarry edge and has a misunderstanding.",
        "Write a small, concrete story with music, dust, and a kind correction.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    observer = f["observer"]
    singer = f["singer"]
    return [
        QAItem(
            question=f"Where did {observer.id} go in the story?",
            answer=f"{observer.id} went to the quarry edge, where the stones were warm and the air carried sound far away.",
        ),
        QAItem(
            question=f"What did {observer.id} first misunderstand about {singer.id}?",
            answer=f"{observer.id} thought something was wrong because the harp and the psalm sounded serious, but {singer.id} was only practicing.",
        ),
        QAItem(
            question=f"What changed after {singer.id} explained the music?",
            answer=f"{observer.id} stopped worrying, understood the psalm was for comfort, and sat down to listen instead.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a harp?",
            answer="A harp is a stringed musical instrument that makes clear, ringing notes when someone plucks its strings.",
        ),
        QAItem(
            question="What is a psalm?",
            answer="A psalm is a sacred song or poem that people may sing or recite quietly.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what is happening, and then learns the truth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(quarry_edge).
feature(harp_psalm).

valid_story(P, F) :- place(P), feature(F).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", "quarry_edge"), asp.fact("feature", "harp_psalm")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


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
    StoryParams(name="Mina", gender="girl", observer_role="worker", singer_role="grandparent"),
    StoryParams(name="Theo", gender="boy", observer_role="neighbor", singer_role="worker"),
    StoryParams(name="Elsie", gender="girl", observer_role="grandparent", singer_role="neighbor"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} ({p.gender})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
