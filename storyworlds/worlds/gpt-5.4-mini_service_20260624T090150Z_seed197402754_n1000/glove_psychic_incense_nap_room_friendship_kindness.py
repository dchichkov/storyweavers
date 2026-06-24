#!/usr/bin/env python3
"""
A small ghost-story-style storyworld set in a nap room.

Premise:
- A child in a nap room notices a spooky feeling around a glove, a psychic,
  and a stick of incense.
- The tension comes from a soft, mysterious ghost that keeps hiding the nap mat.
- Friendship and kindness turn the spooky feeling into a gentle helper story.

This script is self-contained and follows the Storyweavers world contract.
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
    kind: str = "thing"  # character | thing | spirit
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "spirit":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the nap room"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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


@dataclass
class Rule:
    name: str


def _incense_calms(world: World) -> list[str]:
    out: list[str] = []
    incense = world.entities.get("incense")
    spirit = world.entities.get("ghost")
    if not incense or not spirit:
        return out
    if incense.meters.get("lit", 0.0) < THRESHOLD:
        return out
    if spirit.memes.get("fear", 0.0) < THRESHOLD:
        return out
    sig = "incense_calms"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spirit.memes["fear"] = 0.0
    spirit.memes["calm"] = spirit.memes.get("calm", 0.0) + 1.0
    out.append("The spooky air softened, as if the room had taken one slow breath.")
    return out


def _glove_guides(world: World) -> list[str]:
    out: list[str] = []
    glove = world.entities.get("glove")
    child = world.entities.get("child")
    if not glove or not child:
        return out
    if glove.carried_by != child.id:
        return out
    sig = "glove_guides"
    if sig in world.fired:
        return out
    if child.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1.0
    out.append("The glove felt warm in the child's hand, like a tiny promise.")
    return out


def _friendship_resolves(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    psychic = world.entities.get("psychic")
    ghost = world.entities.get("ghost")
    if not child or not psychic or not ghost:
        return out
    if child.memes.get("friendship", 0.0) < THRESHOLD:
        return out
    if psychic.memes.get("understanding", 0.0) < THRESHOLD:
        return out
    if ghost.memes.get("fear", 0.0) >= THRESHOLD:
        return out
    sig = "friendship_resolves"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["friendliness"] = 1.0
    out.append("The ghost was not mean at all. It only wanted someone to notice it kindly.")
    return out


CAUSAL_RULES = [
    Rule("incense_calms"),
    Rule("glove_guides"),
    Rule("friendship_resolves"),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.name == "incense_calms":
                sents = _incense_calms(world)
            elif rule.name == "glove_guides":
                sents = _glove_guides(world)
            else:
                sents = _friendship_resolves(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_nap_room_story(world: World) -> None:
    child = world.get("child")
    parent = world.get("parent")
    psychic = world.get("psychic")
    glove = world.get("glove")
    incense = world.get("incense")
    ghost = world.get("ghost")

    world.say(
        f"In the nap room, {child.id} liked the quiet rows of little beds and the sleepy air."
    )
    world.say(
        f"{child.pronoun().capitalize()} had found a soft glove and held it like a treasure."
    )
    world.say(
        f"{parent.pronoun().capitalize()} said the glove had been left there for a reason, "
        f"and the room felt a little strange."
    )

    world.para()
    world.say(
        f"Then a psychic came in with a calm voice and a careful smile."
    )
    psychic.memes["understanding"] = 1.0
    child.memes["friendship"] = child.memes.get("friendship", 0.0) + 1.0
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1.0
    ghost.memes["fear"] = 1.0
    world.say(
        f"The psychic pointed to the little curl of incense and said, "
        f'"We can make the room gentle, not scary."'
    )

    world.para()
    incense.meters["lit"] = 1.0
    world.say(
        f"So {parent.id} lit the incense, and the room filled with a sweet, slow smell."
    )
    propagate(world, narrate=True)

    world.say(
        f"{child.id} slipped on the glove and walked closer to the shadow by the nap mats."
    )
    world.say(
        f"Instead of hiding, the ghost bobbed up like a shy pillow and waited."
    )

    world.para()
    world.say(
        f"{child.id} used a soft voice and shared a blanket corner, showing kindness first."
    )
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1.0
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1.0
    propagate(world, narrate=True)

    world.say(
        f"At last, the ghost stopped feeling spooky. It helped tuck the blanket smooth, "
        f"and the nap room became quiet again."
    )
    world.say(
        f"{child.id} kept the glove, the incense smell drifted softly away, and everyone "
        f"rested in a room that felt friendly."
    )

    world.facts.update(
        child=child,
        parent=parent,
        psychic=psychic,
        glove=glove,
        incense=incense,
        ghost=ghost,
        setting=world.setting,
    )


def valid_story() -> bool:
    return True


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "nap_room"),
        asp.fact("item", "glove"),
        asp.fact("item", "incense"),
        asp.fact("character", "psychic"),
        asp.fact("character", "child"),
        asp.fact("relationship", "friendship"),
        asp.fact("value", "kindness"),
        asp.fact("place", "nap_room"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
needs_calm(nap_room).
can_help(psychic, ghost) :- character(psychic), character(ghost).
can_help(child, ghost) :- relationship(friendship), value(kindness).
friendly_end :- needs_calm(nap_room), can_help(psychic, ghost), can_help(child, ghost).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show friendly_end/0."))
    asp_ok = bool(model)
    py_ok = valid_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


NAMES = ["Mia", "Lily", "Noah", "Eli", "Ava", "Zoe"]
TRAITS = ["gentle", "curious", "brave", "quiet", "kind"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story-style world set in a nap room.")
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
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(Setting())
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        traits=["little", params.trait],
        memes={"friendship": 0.0, "kindness": 0.0, "brave": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        memes={"care": 1.0},
    ))
    psychic = world.add(Entity(
        id="psychic",
        kind="character",
        type="person",
        label="the psychic",
        traits=["calm", "knowing"],
        memes={"understanding": 0.0},
    ))
    glove = world.add(Entity(
        id="glove",
        kind="thing",
        type="glove",
        label="glove",
        phrase="a soft glove",
        owner=child.id,
        carried_by=child.id,
        meters={"held": 1.0},
    ))
    incense = world.add(Entity(
        id="incense",
        kind="thing",
        type="incense",
        label="incense",
        phrase="a stick of incense",
        owner=parent.id,
        meters={"lit": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="spirit",
        type="ghost",
        label="ghost",
        phrase="a shy ghost",
        meters={"seen": 0.0},
        memes={"fear": 0.0, "friendliness": 0.0},
    ))
    world.facts["setting"] = world.setting
    build_nap_room_story(world)

    story = world.render()
    prompts = [
        'Write a gentle ghost story set in a nap room where a child, a psychic, '
        'and a little bit of incense help a shy spirit feel safe.',
        f"Tell a child-friendly story about {params.name} finding a glove in the nap room "
        f"and learning kindness with help from a psychic.",
        "Write a cozy spooky story that ends with friendship instead of fright.",
    ]
    story_qa = [
        QAItem(
            question=f"Where did {params.name} find the glove?",
            answer=f"{params.name} found the glove in the nap room, where the beds and blankets were waiting for rest.",
        ),
        QAItem(
            question="Who helped make the room feel less spooky?",
            answer="The psychic helped, and so did the child, the parent, and the gentle smell of incense.",
        ),
        QAItem(
            question="What changed the ghost at the end?",
            answer="Kindness and friendship changed the ghost from scary-looking into a shy helper who wanted to be noticed kindly.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is incense used for in a room?",
            answer="Incense is used to give a room a strong, gentle smell that can make the air feel calm or special.",
        ),
        QAItem(
            question="What does a psychic do in a ghost story?",
            answer="A psychic is a character who notices mysterious feelings and helps people understand what a spirit might need.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means using gentle words and helpful actions so someone feels safe and cared for.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people trust each other, share time together, and try to help one another feel happy.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print()
        print("== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print()
        print("== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show friendly_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show friendly_end/0."))
        print("friendly_end" if model else "no friendly end")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", parent="mother", trait="gentle"),
            StoryParams(name="Noah", gender="boy", parent="father", trait="curious"),
            StoryParams(name="Ava", gender="girl", parent="mother", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
