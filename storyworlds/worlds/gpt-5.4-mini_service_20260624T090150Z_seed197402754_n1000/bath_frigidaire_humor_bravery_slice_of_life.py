#!/usr/bin/env python3
"""
storyworlds/worlds/bath_frigidaire_humor_bravery_slice_of_life.py
=================================================================

A small slice-of-life story world about bath time, a humming frigidaire,
humor, and a brave little choice.

Seed tale used to build the model:
---
A child in a cozy kitchen keeps sneaking back to the frigidaire to look for
a cold treat. It is bath time, but the child does not want to leave the warm,
funny kitchen or climb into the tub. A parent notices the sticky hands, the
bath waiting, and the child’s nervous face. The parent makes the moment lighter
with a silly joke and a brave plan: wash first, then pick a snack from the
frigidaire. The child takes a deep breath, tries the bath, and ends the evening
clean, smiling, and proud.
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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryThing:
    id: str
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryEvent:
    id: str
    verb: str
    worry: str
    reward: str
    tags: set[str]


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _narrate_metaphor(value: float) -> str:
    return "a little" if value < 2 else "a lot of"


def _rule_clammy(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    if not child:
        return out
    ent = world.get(child.id)
    if ent.meters.get("sticky", 0) >= THRESHOLD and ("clammy", child.id) not in world.fired:
        world.fired.add(("clammy", child.id))
        ent.memes["restless"] = ent.memes.get("restless", 0) + 1
        out.append(f"{child.id} kept wiggling because sticky hands never feel quite settled.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_clammy,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mia", "Luna", "Ruby", "Nora", "Ada", "Zoe"],
    "boy": ["Ben", "Theo", "Finn", "Eli", "Max", "Owen"],
}
TRAITS = ["curious", "playful", "shy", "brave", "silly", "gentle"]


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"bath", "frigidaire"}),
}


ACTIVITY = StoryEvent(
    id="bath_and_frigidaire",
    verb="take a bath",
    worry="the bath felt too big and splashy",
    reward="a tiny treat from the frigidaire",
    tags={"bath", "frigidaire", "humor", "bravery", "slice_of_life"},
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life bath and frigidaire story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS["kitchen"])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait],
        meters={"sticky": 1.0},
        memes={"bravery": 0.0, "humor": 0.0, "worry": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        memes={"patience": 1.0, "humor": 1.0},
    ))
    bath = world.add(Entity(
        id="Bath",
        type="bath",
        label="the bath",
        phrase="the warm bath",
        meters={"water": 1.0, "bubbles": 1.0},
    ))
    fridge = world.add(Entity(
        id="Frigidaire",
        type="frigidaire",
        label="the frigidaire",
        phrase="the humming frigidaire",
        meters={"cold": 1.0},
        memes={"hum": 1.0},
    ))
    world.facts.update(child=child, parent=parent, bath=bath, fridge=fridge, params=params)
    return world


def _silly_line(parent: Entity) -> str:
    return f'"The {parent.type} said the bath was not a monster, just a tub with better manners."'


def tell(world: World) -> None:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    bath: Entity = world.facts["bath"]
    fridge: Entity = world.facts["fridge"]
    params: StoryParams = world.facts["params"]

    world.say(
        f"{child.id} was a little {params.trait} {params.gender} who lived in a cozy kitchen "
        f"where the frigidaire hummed like a sleepy bee."
    )
    world.say(
        f"{child.id} liked the sound of the frigidaire and kept hoping it held something sweet."
    )

    world.para()
    world.say(
        f"That evening, {parent.label} called, \"It is bath time.\" "
        f"{child.id} made a face and glanced at {fridge.label}, not at {bath.label}."
    )
    child.memes["worry"] += 1
    child.meters["sticky"] += 0.5
    propagate(world, narrate=True)

    world.say(
        f"{child.id} wanted the cold snack first, but {parent.label} pointed at the bath and "
        f"laughed a little, because the whole kitchen was acting fussy for no reason."
    )
    world.say(_silly_line(parent))
    parent.memes["humor"] += 1
    child.memes["humor"] += 1

    world.para()
    child.memes["bravery"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)
    world.say(
        f"{child.id} took a deep breath, marched to the bathroom with small brave steps, and said, "
        f"\"I can do it.\""
    )
    world.say(
        f"The bath water was warm, the bubbles piled up like soft clouds, and the tiny duck "
        f"looked very pleased with the decision."
    )
    child.meters["sticky"] = 0.0
    child.meters["clean"] = 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0

    world.say(
        f"After the bath, {parent.label} opened the frigidaire and found a cold treat waiting there, "
        f"which made the end of the night feel funny and fair."
    )
    world.say(
        f"{child.id} grinned, proud of {child.pronoun('subject')}self for being brave, and "
        f"the frigidaire hummed on while the clean pajamas felt wonderfully fresh."
    )

    world.facts["resolved"] = True


ASP_RULES = r"""
#show compatible/0.
compatible :- bath_ok, fridge_ok.
bath_ok :- needs_bath.
fridge_ok :- has_treat.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "kitchen"),
        asp.fact("affords", "kitchen", "bath"),
        asp.fact("affords", "kitchen", "frigidaire"),
        asp.fact("thing", "bath"),
        asp.fact("thing", "frigidaire"),
        asp.fact("theme", "humor"),
        asp.fact("theme", "bravery"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/0."))
    ok = any(sym.name == "compatible" for sym in model)
    if ok:
        print("OK: ASP gate recognizes the bath/frigidaire story world.")
        return 0
    print("MISMATCH: ASP gate did not derive compatibility.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a gentle story about {p.name}, a bath, and a frigidaire, with humor and bravery.',
        f"Tell a slice-of-life story where {p.name} wants a cold treat from the frigidaire "
        f"but must finish bath time first.",
        "Write a short child-friendly story in which a parent uses a silly joke to help a child be brave about bath time.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    return [
        QAItem(
            question=f"Why did {child.id} hesitate at bath time?",
            answer=f"{child.id} hesitated because the bath felt too big and splashy, and {child.pronoun('subject')} wanted to stay near the frigidaire instead.",
        ),
        QAItem(
            question=f"What helped {child.id} be brave?",
            answer=f"A silly joke from {parent.label} and the promise of a treat from the frigidaire helped {child.id} feel brave enough to try the bath.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} was clean, smiling, and proud after the bath, and the frigidaire was still there waiting for a snack later.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bath for?",
            answer="A bath is for washing your body with water and soap so you can get clean.",
        ),
        QAItem(
            question="What is a frigidaire?",
            answer="A frigidaire is a refrigerator, a cold box that keeps food and drinks fresh.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel nervous or shy.",
        ),
        QAItem(
            question="Why can humor help?",
            answer="Humor can help because a funny joke can make a worried moment feel lighter and easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def valid_params(args: argparse.Namespace) -> None:
    if args.gender == "girl" and args.parent == "father":
        return


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/0."))
        print("compatible" if any(sym.name == "compatible" for sym in model) else "not compatible")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(name="Mia", gender="girl", parent="mother", trait="brave", seed=base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
