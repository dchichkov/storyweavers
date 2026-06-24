#!/usr/bin/env python3
"""
Storyworld: ask, nap room magic, dialogue, folk-tale tone.

A small child in a nap room asks for one more bit of magic before sleep.
The world model tracks tiredness, wonder, and the state of a tiny charm.
A gentle helper uses dialogue and a folk-tale style turn to lead the child
from restless asking to a magical nap and a warm ending image.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Room:
    place: str = "the nap room"
    name: str = "nap room"
    affords: set[str] = field(default_factory=lambda: {"ask", "magic", "dialogue"})


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    magic_kind: str
    gentle: bool = True


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.magic_glow = 0.0
        self.nap_ended = False

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.magic_glow = self.magic_glow
        clone.nap_ended = self.nap_ended
        return clone


def _restless(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("restless", 0.0) < THRESHOLD:
            continue
        if ("restless", actor.id) in world.fired:
            continue
        world.fired.add(("restless", actor.id))
        actor.memes["tired"] = actor.memes.get("tired", 0.0) + 0.5
        out.append(f"The little room grew quieter as {actor.id} fidgeted less.")
    return out


def _magic_settle(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if world.magic_glow < THRESHOLD or actor.memes.get("wonder", 0.0) < THRESHOLD:
            continue
        sig = ("settle", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["restless"] = max(0.0, actor.memes.get("restless", 0.0) - 1.0)
        actor.memes["sleepy"] = actor.memes.get("sleepy", 0.0) + 1.0
        out.append(f"The magic made {actor.id} grow quiet and sleepy.")
    return out


def _nap_end(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("sleepy", 0.0) < THRESHOLD:
            continue
        sig = ("nap", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.nap_ended = True
        out.append(f"{actor.id} rested at last.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_restless, _magic_settle, _nap_end):
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
    child_name: str
    child_gender: str
    helper_name: str
    charm: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mira", "Lina", "Tara", "Nina", "Sora", "Elin"],
    "boy": ["Owen", "Jasper", "Milo", "Ari", "Bram", "Tobin"],
}
HELPERS = ["grandmother", "grandfather", "old aunt", "wise uncle"]
CHILD_TRAITS = ["curious", "gentle", "restless", "bright-eyed", "little"]
CHARMS = {
    "lantern": Charm(id="lantern", label="a lantern", phrase="a tiny lantern with a silver wick", magic_kind="glow"),
    "bell": Charm(id="bell", label="a bell", phrase="a round bell that rang like a raindrop", magic_kind="song"),
    "blanket": Charm(id="blanket", label="a blanket", phrase="a soft blanket stitched with stars", magic_kind="warmth"),
}
SETTING = Room()


class AskWorld:
    pass


def ask_story(world: World, child: Entity, helper: Entity, charm: Charm) -> None:
    child.memes["wonder"] += 1
    child.memes["restless"] += 1
    world.say(f"Once in the nap room, little {child.id} could not quite close {child.pronoun('possessive')} eyes.")
    world.say(f'{child.id} looked at {helper.id} and asked, "May I ask for one more bit of magic?"')
    world.say(f'{helper.id} smiled and answered, "A story may be a kind of spell, child dear."')
    world.say(f"They held up {charm.phrase}, and the air felt kind as old bread and morning milk.")
    world.magic_glow += 1.0
    propagate(world, narrate=True)


def turn_story(world: World, child: Entity, helper: Entity, charm: Charm) -> None:
    world.para()
    world.say(f'{child.id} whispered, "Will the magic stay if I shut my eyes?"')
    world.say(f'{helper.id} said, "It will stay as long as you keep the tale in your heart."')
    world.say(f"Then {helper.id} tapped {charm.label} once, and a soft glow slipped over the blanket and pillow.")
    world.magic_glow += 1.0
    child.memes["wonder"] += 1
    child.memes["sleepy"] += 1
    propagate(world, narrate=True)


def ending_story(world: World, child: Entity, helper: Entity, charm: Charm) -> None:
    world.para()
    if world.nap_ended:
        world.say(f"{child.id} yawned, curled up, and drifted into a nap while the little glow watched like a star.")
    else:
        world.say(f"{child.id} lay still at last, listening to the hush that followed the spell.")
    world.say(f"{helper.id} tucked the blanket smooth, and {charm.label} shone quietly beside the bed.")
    world.say(f"In the nap room, the magic did not dance loudly; it stayed gentle, and that was enough.")


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.child_name, kind="character", type=params.child_gender,
        traits=["little", "curious"],
        memes={"wonder": 0.0, "restless": 0.0, "sleepy": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name, kind="character", type="adult",
        label=params.helper_name, traits=["wise", "gentle"],
    ))
    charm = CHARMS[params.charm]

    ask_story(world, child, helper, charm)
    turn_story(world, child, helper, charm)
    ending_story(world, child, helper, charm)

    world.facts.update(child=child, helper=helper, charm=charm, room=world.room)
    return world


ASP_RULES = r"""
child_restless(C) :- restless(C).
magic_glow :- charm_present.
sleepy(C) :- child_restless(C), magic_glow.
nap_ended(C) :- sleepy(C).
valid_story(Room, Charm, Gender) :- room(Room), charm(Charm), child_gender(Gender), valid_combo(Room, Charm, Gender).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("room", "nap_room"))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("charm_present"))
        lines.append(asp.fact("magic_kind", cid, charm.magic_kind))
    for g in ("girl", "boy"):
        lines.append(asp.fact("child_gender", g))
    lines.append(asp.fact("valid_combo", "nap_room", "lantern", "girl"))
    lines.append(asp.fact("valid_combo", "nap_room", "lantern", "boy"))
    lines.append(asp.fact("valid_combo", "nap_room", "bell", "girl"))
    lines.append(asp.fact("valid_combo", "nap_room", "bell", "boy"))
    lines.append(asp.fact("valid_combo", "nap_room", "blanket", "girl"))
    lines.append(asp.fact("valid_combo", "nap_room", "blanket", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale nap room story with ask, magic, and dialogue.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--charm", choices=CHARMS)
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
    child_name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    charm = args.charm or rng.choice(list(CHARMS))
    return StoryParams(child_name=child_name, child_gender=gender, helper_name=helper, charm=charm)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    charm = f["charm"]
    return [
        f'Write a short folk tale in a nap room with the word "ask" and the charm {charm.label}.',
        f"Tell a gentle story where {child.id} asks {helper.id} for magic before nap time and they speak kindly.",
        f"Write a child-facing tale with dialogue, magic, and a sleepy ending in the nap room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"What did {child.id} ask for in the nap room?",
            answer=f"{child.id} asked {helper.id} for one more bit of magic before sleeping.",
        ),
        QAItem(
            question=f"How did {helper.id} answer {child.id}?",
            answer=f"{helper.id} answered kindly and said a story could be a kind of spell.",
        ),
        QAItem(
            question=f"What happened to the magic by the end of the story?",
            answer=f"The magic grew soft and gentle, and it helped {child.id} become sleepy enough for a nap.",
        ),
        QAItem(
            question=f"What was special about {charm.label}?",
            answer=f"{charm.phrase} made the nap room feel warm, calm, and a little enchanted.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nap room for?",
            answer="A nap room is a quiet place where children rest, get sleepy, and take naps.",
        ),
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to one another using words inside quotation marks.",
        ),
        QAItem(
            question="What does magic mean in a folk tale?",
            answer="In a folk tale, magic is an amazing thing that can make ordinary moments feel enchanted or special.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  magic_glow={world.magic_glow}")
    lines.append(f"  nap_ended={world.nap_ended}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {
        ("nap_room", "lantern", "girl"),
        ("nap_room", "lantern", "boy"),
        ("nap_room", "bell", "girl"),
        ("nap_room", "bell", "boy"),
        ("nap_room", "blanket", "girl"),
        ("nap_room", "blanket", "boy"),
    }
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches Python gate ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


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
    StoryParams(child_name="Mira", child_gender="girl", helper_name="wise uncle", charm="lantern"),
    StoryParams(child_name="Owen", child_gender="boy", helper_name="grandmother", charm="blanket"),
    StoryParams(child_name="Lina", child_gender="girl", helper_name="old aunt", charm="bell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
