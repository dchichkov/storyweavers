#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/noise_dim_orangeade_transformation_magic_suspense_bedtime.py
=============================================================================================

A standalone bedtime-style storyworld for a small magical domain: a child hears
a noise in a dim room, discovers an orangeade charm, and uses a gentle spell to
transform a worry into something safe and sleepy.

This world keeps the story in a classical shape:
- a quiet setup,
- a suspense beat when something feels strange,
- a magical transformation,
- and a calm ending image that proves the change.

The words "noise-dim" and "orangeade" are intentionally included in the domain
and in the generated prose.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Room:
    id: str
    scene: str
    darkness: str
    comfort: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    glimmer: str
    transforms_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spell:
    id: str
    title: str
    incantation: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(copy.deepcopy(self.room))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise_grows(world: World) -> list[str]:
    out: list[str] = []
    if world.room.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.room.memes["suspense"] += 1
    for ent in world.entities.values():
        if ent.role == "child":
            ent.memes["worry"] += 1
    out.append("__noise__")
    return out


def _r_magic_brightens(world: World) -> list[str]:
    out: list[str] = []
    if world.room.memes["suspense"] < THRESHOLD:
        return out
    sig = ("magic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.room.meters["glow"] += 1
    out.append("__magic__")
    return out


CAUSAL_RULES = [
    Rule("noise", "social", _r_noise_grows),
    Rule("magic", "physical", _r_magic_brightens),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spook(world: World) -> dict:
    sim = world.copy()
    sim.room.meters["noise"] += 1
    propagate(sim, narrate=False)
    return {
        "suspense": sim.room.memes["suspense"],
        "glow": sim.room.meters["glow"],
    }


def setup(world: World, child: Entity, parent: Entity) -> None:
    child.memes["sleepy"] += 1
    parent.memes["calm"] += 1
    world.say(
        f"At bedtime, {child.id} curled up in the quiet room. The lamp made the "
        f"walls soft and the blankets looked like little hills."
    )
    world.say(
        f"{child.id} and {parent.id} were whispering good-night stories when the "
        f"room turned especially noise-dim."
    )


def suspense_beat(world: World, child: Entity, parent: Entity) -> None:
    world.room.meters["noise"] += 1
    prop = predict_spook(world)
    child.memes["suspense"] += 1
    world.facts["predicted_suspense"] = prop["suspense"]
    world.say(
        f"Then came a tiny bump from the corner, like a thimble tapping wood. "
        f"{child.id} held {child.pronoun('possessive')} breath and looked at "
        f"{parent.id}."
    )
    world.say(
        f'"Did you hear that?" {child.id} whispered. "{parent.id}, is the dark '
        f"doing something?"'
    )


def reveal_charm(world: World, child: Entity, charm: Charm) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On the bedside shelf sat {charm.phrase}. It gave off {charm.glimmer}, "
        f"and {child.id} noticed that the bottle looked almost like a tiny sunset."
    )


def magic_transform(world: World, child: Entity, charm: Charm, spell: Spell) -> None:
    world.room.meters["noise"] = 0.0
    world.room.memes["suspense"] = 0.0
    world.room.meters["glow"] += spell.power
    child.memes["joy"] += 1
    child.memes["brave"] += 1
    world.say(
        f'{child.id} took a deep breath and said, "{spell.incantation}" '
        f"{spell.effect}."
    )
    world.say(
        f"The little charm warmed, shimmered, and changed into {charm.transforms_to}. "
        f"The room answered with a gentle orange glow."
    )


def ending(world: World, child: Entity, parent: Entity, charm: Charm) -> None:
    world.say(
        f"The bump was only the window branch knocking at the glass. "
        f"{child.id} smiled and tucked {child.pronoun('possessive')} blanket under "
        f"{child.pronoun('possessive')} chin."
    )
    world.say(
        f"{parent.id} kissed {child.pronoun('object')} on the forehead and said, "
        f'"Now the room has its own sleepy lantern."'
    )
    world.say(
        f"And so {child.id} fell asleep beside the little orangeade charm, with "
        f"the night feeling calm, warm, and safe."
    )


def tell(room: Room, child_name: str = "Mira", child_type: str = "girl",
         parent_name: str = "Mom", parent_type: str = "mother") -> World:
    world = World(room)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="parent"))
    charm = Charm(
        id="orangeade",
        label="orangeade",
        phrase="a glass bottle of orangeade on the shelf",
        glimmer="a faint gold sparkle",
        transforms_to="a sleepy lantern of warm light",
        tags={"orangeade", "magic"},
    )
    spell = Spell(
        id="transform",
        title="Transformation",
        incantation="Orangeade, turn the worry round",
        effect="and the dimness folded into a kinder shape",
        power=2,
        tags={"transformation", "magic", "suspense"},
    )

    setup(world, child, parent)
    world.para()
    suspense_beat(world, child, parent)
    reveal_charm(world, child, charm)
    world.para()
    magic_transform(world, child, charm, spell)
    ending(world, child, parent, charm)

    world.facts.update(
        child=child,
        parent=parent,
        charm=charm,
        spell=spell,
        room=room,
        outcome="transformed",
        suspense=world.room.memes["suspense"],
        glow=world.room.meters["glow"],
        noise=world.room.meters["noise"],
    )
    return world


ROOMS = {
    "bedroom": Room("bedroom", "a bedroom with a moonlit window", "noise-dim", "soft blankets"),
    "nursery": Room("nursery", "a nursery with a rocking chair", "noise-dim", "pillows and a teddy"),
    "attic": Room("attic", "a tiny attic room under the roof", "noise-dim", "a warm quilt"),
}

CHILD_NAMES = ["Mira", "Nina", "Eli", "Jun", "Lia", "Owen"]
PARENTS = [("Mom", "mother"), ("Dad", "father"), ("Mum", "mother")]
TRAITS = ["sleepy", "gentle", "curious", "brave"]


@dataclass
class StoryParams:
    room: str
    child: str
    child_type: str
    parent: str
    parent_type: str
    trait: str = "gentle"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(room, "orangeade", "transform") for room in ROOMS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime magic storyworld with noise-dim suspense and an orangeade transformation."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=[p for p, _ in PARENTS])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
    combos = [c for c in valid_combos() if (args.room is None or c[0] == args.room)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, _, _ = rng.choice(combos)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice([p for p, _ in PARENTS])
    parent_type = args.parent_type or dict(PARENTS)[parent]
    trait = rng.choice(TRAITS)
    return StoryParams(room, child, child_type, parent, parent_type, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that uses the words "noise-dim" and "orangeade".',
        f"Tell a gentle magic story where {f['child'].id} hears a small sound in a noise-dim room and uses an orangeade charm to change the feeling of the dark.",
        f"Write a suspenseful but cozy story with Transformation and Magic, ending in a warm bedtime glow.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, charm = f["child"], f["parent"], f["charm"]
    return [
        QAItem(
            question="What did the child hear in the room?",
            answer=f"{child.id} heard a tiny bump that made the room feel suspenseful. It was only a small sound, but it changed the quiet bedtime mood."
        ),
        QAItem(
            question="What did the child use to make the room feel safe again?",
            answer=f"{child.id} used the orangeade charm with a transformation spell. The charm turned into a sleepy lantern, so the dark looked warm instead of scary."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} falling asleep beside the glowing orangeade lantern. {parent.id} stayed close, and the room felt calm, cozy, and safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word orangeade usually make you think of?",
            answer="Orangeade makes you think of oranges and something bright and sunny. In this story it also became a magical object that gave off warm light."
        ),
        QAItem(
            question="What is transformation in a magic story?",
            answer="Transformation means one thing changes into another. In a magic story, a spell can make that change happen in a surprising but gentle way."
        ),
        QAItem(
            question="Why do bedtime stories often feel calm at the end?",
            answer="Bedtime stories often end calmly so children can feel safe and sleepy. The quiet ending helps the night feel gentle instead of loud or hurried."
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
    room = world.room
    lines.append(f"room: {room.scene} meters={dict((k,v) for k,v in room.meters.items() if v)} memes={dict((k,v) for k,v in room.memes.items() if v)}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "Mira", "girl", "Mom", "mother", "gentle"),
    StoryParams("nursery", "Eli", "boy", "Dad", "father", "curious"),
    StoryParams("attic", "Nina", "girl", "Mum", "mother", "brave"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("scene", rid, rid))
    lines.append(asp.fact("theme_word", "noise_dim"))
    lines.append(asp.fact("charm", "orangeade"))
    lines.append(asp.fact("spell", "transform"))
    lines.append(asp.fact("suspense_min", int(SUSPENSE_MIN)))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R) :- room(R).
outcome(transformed) :- valid(_).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == {(r,) for r in valid_combos()}:
        print("OK: ASP gate matches valid_combos().")
    else:
        print("MISMATCH: ASP gate differs from valid_combos().")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    room = copy.deepcopy(ROOMS[params.room])
    world = tell(room, params.child, params.child_type, params.parent, params.parent_type)
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
        print(asp_program("", "#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible rooms: {asp_valid_combos()}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
