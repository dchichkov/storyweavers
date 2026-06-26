#!/usr/bin/env python3
"""
A small storyworld for a Ghost-Story-like tale built around Curiosity and a
Flashback: a child enters a secure old place, meets an arrogant ghost, and a
concerted effort turns fear into help.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    secure: bool = True
    ghostly: bool = True
    sounds: list[str] = field(default_factory=lambda: ["floorboards", "wind", "whispers"])


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    value: str
    can_secure: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    artifact: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "house": Setting(place="the old house", secure=True, ghostly=True),
    "attic": Setting(place="the attic", secure=True, ghostly=True, sounds=["dust", "creaks", "rustles"]),
    "hall": Setting(place="the quiet hall", secure=True, ghostly=True, sounds=["echoes", "footsteps"]),
}

ARTIFACTS = {
    "lantern": Artifact(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        value="secure light",
        can_secure=True,
    ),
    "ribbon": Artifact(
        id="ribbon",
        label="ribbon",
        phrase="a blue ribbon tied around a key",
        value="memory",
        can_secure=False,
    ),
    "music_box": Artifact(
        id="music_box",
        label="music box",
        phrase="a tiny music box with a silver lid",
        value="song",
        can_secure=False,
    ),
}

GHOST = Entity(
    id="Ghost",
    kind="character",
    type="ghost",
    label="ghost",
    traits=["arrogant", "concerted", "lonely"],
)

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ivy", "Ruby"],
    "boy": ["Eli", "Ben", "Theo", "Owen", "Finn"],
}


def reasonableness_ok(setting: Setting, artifact: Artifact) -> bool:
    return setting.secure and artifact.can_secure


def explain_rejection(setting: Setting, artifact: Artifact) -> str:
    return (
        f"(No story: this ghost tale needs a secure place and an object that can "
        f"actually make someone feel safe. {artifact.label} does not fit that role here.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: curiosity, flashback, and a careful rescue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    setting = SETTINGS[place]
    art = ARTIFACTS[artifact]
    if args.place and args.artifact and not reasonableness_ok(setting, art):
        raise StoryError(explain_rejection(setting, art))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, artifact=artifact)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS["house"]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["curious", "quiet"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    artifact = ARTIFACTS[params.artifact]
    obj = world.add(Entity(id=artifact.id, type=artifact.label, label=artifact.label, phrase=artifact.phrase, owner=hero.id))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="ghost", traits=["arrogant", "concerted"]))
    world.facts.update(hero=hero, parent=parent, artifact=obj, ghost=ghost, params=params, setting=setting)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    artifact: Entity = f["artifact"]  # type: ignore[assignment]
    ghost: Entity = f["ghost"]  # type: ignore[assignment]

    world.say(
        f"{hero.id} was a curious little {hero.type} who loved the quiet corners of {world.setting.place}."
    )
    world.say(
        f"One evening, {hero.id}'s {parent.label} gave {hero.pronoun('object')} {artifact.phrase}, "
        f"and {hero.id} held {artifact.pronoun('object')} like a secret."
    )
    world.para()
    world.say(
        f"In the hall, the air felt cold, and the floorboards answered with tiny creaks. "
        f"{hero.id} followed the sound because Curiosity kept tugging gently at {hero.pronoun('possessive')} sleeve."
    )
    world.say(
        f"Then a ghost drifted out of the dark, looking arrogant and tall. "
        f'"This house is mine," the ghost said, sounding proud.'
    )
    world.say(
        f"{hero.id} froze, but then {hero.id} noticed a small ribbon on the ghost's hand, and a Flashback flickered through {hero.pronoun('possessive')} mind."
    )
    world.say(
        f"{hero.id} remembered {hero.pronoun('possessive')} {parent.label} saying that the ghost had once guarded this place so no one would get lost."
    )
    world.para()
    world.say(
        f"{hero.id} took a slow breath and spoke kindly. \"You don't have to be alone,\" {hero.pronoun()} said."
    )
    world.say(
        f"Together, {hero.id}, the {parent.label}, and the ghost made a concerted plan: they lit the lantern, found the hidden key, and opened a dusty little box."
    )
    world.say(
        f"Inside was an old note saying the house was safe when the lantern stayed near the door."
    )
    world.say(
        f"The ghost's proud face softened, because now the house felt secure at last."
    )
    world.say(
        f"At the end, {hero.id} walked home with {artifact.pronoun('object')}, the lantern glowed warmly, and the arrogant ghost waved from the hall instead of hiding in the dark."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    artifact: Entity = f["artifact"]  # type: ignore[assignment]
    return [
        "Write a gentle ghost story for a young child that includes Curiosity and a Flashback.",
        f"Tell a story where {hero.id} explores a secure old house and learns something surprising about a ghost.",
        f"Write a short haunted-house tale that ends with {artifact.label} and a calm, safe feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    artifact: Entity = f["artifact"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a curious little {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} hold at the start?",
            answer=f"{hero.id} held {artifact.phrase} and treated it like a secret.",
        ),
        QAItem(
            question="Why did the ghost seem arrogant at first?",
            answer="The ghost seemed arrogant because it acted proud and said the house belonged to it.",
        ),
        QAItem(
            question="What changed after the concerted plan?",
            answer="The ghost stopped acting proud and lonely, and the house felt secure because the lantern stayed near the door.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to ask questions and find out what is hidden or unknown.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when a story briefly remembers something that happened before.",
        ),
        QAItem(
            question="What does secure mean?",
            answer="Secure means safe, steady, and not easy to lose or break.",
        ),
        QAItem(
            question="What does concerted mean?",
            answer="Concerted means done together in a careful, organized way.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
secure_place(P) :- place(P), secure(P).
good_story(P,A) :- secure_place(P), artifact(A), can_secure(A).
#show good_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.secure:
            lines.append(asp.fact("secure", pid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        if a.can_secure:
            lines.append(asp.fact("can_secure", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/2."))
    clingo_set = set(asp.atoms(model, "good_story"))
    python_set = {(pid, aid) for pid, s in SETTINGS.items() for aid, a in ARTIFACTS.items() if reasonableness_ok(s, a)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches reasonableness_ok() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show good_story/2."))
        atoms = sorted(set(asp.atoms(model, "good_story")))
        print(f"{len(atoms)} compatible secure story pairs:")
        for p in atoms:
            print(f"  {p[0]} {p[1]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", gender="girl", parent="mother", artifact="lantern"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
