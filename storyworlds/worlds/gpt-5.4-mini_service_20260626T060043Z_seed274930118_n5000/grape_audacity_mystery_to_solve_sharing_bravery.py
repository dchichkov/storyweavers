#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a shared bowl of grapes, a gentle
mystery, and a brave choice to tell the truth.
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    eaten: bool = False
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "the kitchen"
    time: str = "afternoon"
    weather: str = "sunny"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.scene)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _name_title(gender: str) -> str:
    return {"girl": "girl", "boy": "boy"}.get(gender, "child")


def _parent_label(parent: str) -> str:
    return {"mother": "mom", "father": "dad"}.get(parent, parent)


def _friend_label(gender: str) -> str:
    return {"girl": "friend", "boy": "friend"}.get(gender, "friend")


def _mystery_reason(world: World, grape: Entity, child: Entity, friend: Entity) -> str:
    if grape.hidden:
        return f"the bowl looked one grape short, and {friend.id} had quietly tucked it behind a napkin"
    return f"the bowl looked one grape short, and no one could see where the missing grape had gone"


def _tell_if_brave(world: World, child: Entity, friend: Entity) -> None:
    child.memes["audacity"] = child.memes.get("audacity", 0.0) + 1.0
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1.0
    world.say(f"{child.id} took a breath. {child.pronoun().capitalize()} felt brave enough to ask the question out loud.")


def _share(world: World, child: Entity, friend: Entity, grapes: Entity) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1.0
    friend.memes["relief"] = friend.memes.get("relief", 0.0) + 1.0
    grapes.shared_with = [child.id, friend.id]
    grapes.eaten = True
    world.say(
        f"Then {child.id} smiled and said they could share the grapes after all. "
        f"{friend.id} offered the hidden grape back, and the two of them split the bowl."
    )
    world.say(
        f"By the end, the snack was smaller, but the kitchen felt warmer, and everyone had enough."
    )


def tell(scene: Scene, params: StoryParams) -> World:
    world = World(scene)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender))
    grapes = world.add(Entity(
        id="grapes",
        type="grapes",
        label="grapes",
        phrase="a small bowl of purple grapes",
        plural=True,
        owner=child.id,
    ))
    one_grape = world.add(Entity(
        id="one_grape",
        type="grape",
        label="grape",
        phrase="one shiny grape",
        owner=friend.id,
        hidden=True,
    ))

    world.say(
        f"In {scene.place}, {child.id} was a little {_name_title(params.gender)} with a head full of audacity "
        f"and a soft spot for grapes."
    )
    world.say(
        f"{params.name}'s {_parent_label(params.parent)} brought out {grapes.phrase} for an after-school snack, "
        f"and {params.friend_name} came over to sit nearby."
    )

    world.para()
    world.say(
        f"At first, the snack felt ordinary. Then {child.id} noticed something strange: {grapes.label} seemed to be missing one."
    )
    world.say(_mystery_reason(world, one_grape, child, friend) + ".")
    world.say(
        f"{child.id} looked at {friend.id}, then at the bowl, and wondered whether to speak up."
    )

    world.para()
    _tell_if_brave(world, child, friend)
    world.say(
        f"{child.id} asked, \"Did one of us take a grape without asking?\""
    )
    world.say(
        f"{friend.id} blushed and held out a napkin. \"I was scared you'd be upset,\" {friend.pronoun('subject')} said, "
        f"\"but I wanted to know if I could share.\""
    )
    one_grape.hidden = False
    one_grape.eaten = True

    world.para()
    _share(world, child, friend, grapes)
    world.say(
        f"{params.name}'s {_parent_label(params.parent)} nodded at the honest answer and said that sharing works best when everyone asks first."
    )

    world.facts.update(
        child=child,
        parent=parent,
        friend=friend,
        grapes=grapes,
        grape=one_grape,
        scene=scene,
    )
    return world


SETTINGS = {
    "kitchen": Scene(place="the kitchen", time="afternoon", weather="sunny"),
    "porch": Scene(place="the porch", time="late afternoon", weather="breezy"),
    "picnic": Scene(place="the picnic table", time="afternoon", weather="warm"),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ava", "Zoe", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Ben", "Max", "Leo"]


@dataclass
class StoryWorld:
    """Inline alias used nowhere; kept only to avoid accidental external coupling."""
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about grapes, mystery, sharing, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    friend_name = args.friend_name or rng.choice(
        [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != name]
    )
    if friend_name == name:
        raise StoryError("The child and the friend need different names.")
    return StoryParams(
        place=place,
        name=name,
        gender=gender,
        parent=parent,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story about {f["child"].id}, grapes, and a small mystery in {f["scene"].place}.',
        f"Tell a gentle story where {f['child'].id} uses audacity to solve a missing-grape mystery and learn to share.",
        f"Write a child-friendly story about a snack, a brave question, and a happy sharing moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, parent, grapes = f["child"], f["friend"], f["parent"], f["grapes"]
    return [
        QAItem(
            question=f"What was the mystery in {f['scene'].place}?",
            answer=f"The mystery was that one grape seemed to be missing from the bowl, and nobody knew at first where it had gone.",
        ),
        QAItem(
            question=f"How did {child.id} solve the mystery?",
            answer=f"{child.id} was brave enough to ask a careful question out loud, and that helped {friend.id} admit what happened.",
        ),
        QAItem(
            question=f"What did the children do at the end?",
            answer=f"They shared the grapes, told the truth, and ate the snack together instead of keeping the secret.",
        ),
        QAItem(
            question=f"Why did {parent.id} feel pleased?",
            answer=f"{parent.id} was pleased because the children were honest, brave, and willing to share after the mystery was solved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grape?",
            answer="A grape is a small round fruit that can be green, red, or purple and is often eaten as a snack.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or eat part of something so everyone can enjoy it too.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel nervous or shy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.shared_with:
            parts.append(f"shared_with={e.shared_with}")
        if e.eaten:
            parts.append("eaten=True")
        if e.hidden:
            parts.append("hidden=True")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}): {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_story/3.
place(kitchen).
place(porch).
place(picnic).

feature(mystery_to_solve).
feature(sharing).
feature(bravery).

valid_story(P, grape, audacity) :- place(P), feature(mystery_to_solve), feature(sharing), feature(bravery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("seed_word", "grape"))
    lines.append(asp.fact("seed_word", "audacity"))
    lines.append(asp.fact("feature", "mystery_to_solve"))
    lines.append(asp.fact("feature", "sharing"))
    lines.append(asp.fact("feature", "bravery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, "grape", "audacity") for p in SETTINGS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(cl)} stories).")
        return 0
    print("MISMATCH:")
    print(" python only:", sorted(py - cl))
    print(" clingo only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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
    StoryParams(place="kitchen", name="Mia", gender="girl", parent="mother", friend_name="Noah", friend_gender="boy"),
    StoryParams(place="porch", name="Eli", gender="boy", parent="father", friend_name="Luna", friend_gender="girl"),
    StoryParams(place="picnic", name="Ava", gender="girl", parent="mother", friend_name="Ben", friend_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, g, a in stories:
            print(f"  {p:8} {g:5} {a}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
