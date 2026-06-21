#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lasso_dogie_constant_bravery_surprise_friendship_pirate.py
=========================================================================================

A small pirate-tale storyworld about a brave child, a surprise, a friendly dogie,
and a lasso used for a sensible rescue.

The seed words are woven into the world:
- lasso
- dogie
- constant

The story beats are:
- a pirate-play setup
- a surprise problem
- bravery + friendship leading to a rescue
- a bright ending image proving what changed
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_START = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    rig: str
    goal: str
    dark_spot: str
    ending_image: str
    pirate_word: str
    helpers: str


@dataclass
class Hazard:
    id: str
    label: str
    source: str
    risk: str
    makes_trouble: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
    power: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    hazard: str
    rescue: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


SCENES = {
    "deck": Scene(
        id="deck",
        place="the ship deck",
        rig="The sail snapped overhead, the barrel held pretend treasure, and a mop became a mast.",
        goal="the hidden cave in the hold",
        dark_spot="the shadowy hatch",
        ending_image="their lantern and rope swung bright in the sea wind",
        pirate_word="pirate",
        helpers="the gulls overhead",
    ),
    "island": Scene(
        id="island",
        place="the sandy shore",
        rig="The driftwood made a fort, the shell pile was treasure, and a stick became a mast.",
        goal="the sea cave",
        dark_spot="the crabby rock tunnel",
        ending_image="the rope coiled neatly beside their safe lantern",
        pirate_word="buccaneer",
        helpers="the waves and gulls",
    ),
    "harbor": Scene(
        id="harbor",
        place="the little harbor dock",
        rig="The crates were a ship, a bucket became a helm, and a ragged flag danced in the wind.",
        goal="the dark boathouse",
        dark_spot="the shaded boardwalk corner",
        ending_image="the dock glowed warm under their steady light",
        pirate_word="sailor",
        helpers="the water slapping gently below",
    ),
}

HAZARDS = {
    "kite": Hazard("kite", "kite string", "a bright kite line", "can tangle and drag", tags={"string", "surprise"}),
    "net": Hazard("net", "fish net", "a loose fish net", "can snag little feet", tags={"string", "surprise"}),
    "rope": Hazard("rope", "knotty rope", "a coiled rope", "can slip and snare", tags={"string", "surprise"}),
}

RESCUES = {
    "lasso": Rescue(
        id="lasso",
        label="the lasso",
        power=3,
        text="spun the lasso and hooked the snag cleanly, then pulled the line free",
        qa_text="spun the lasso and hooked the snag cleanly, then pulled the line free",
        tags={"lasso", "bravery"},
    ),
    "cut_free": Rescue(
        id="cut_free",
        label="a small knife",
        power=2,
        text="used a small knife to cut the snag loose",
        qa_text="used a small knife to cut the snag loose",
        tags={"bravery"},
    ),
    "pull_line": Rescue(
        id="pull_line",
        label="two hands",
        power=1,
        text="pulled with two hands, but the snag held tight",
        qa_text="pulled with two hands, but the snag held tight",
        tags={"friendship"},
    ),
}

NAMES_GIRL = ["Lila", "Mira", "Nora", "Ava", "Suri"]
NAMES_BOY = ["Toby", "Milo", "Jace", "Noah", "Eli"]


def hazard_requires_bravery(h: Hazard) -> bool:
    return h.makes_trouble


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for h in HAZARDS:
            for r in RESCUES:
                if hazard_requires_bravery(HAZARDS[h]):
                    combos.append((s, h, r))
    return combos


def story_scene(world: World, scene: Scene, child: Entity, friend: Entity, parent: Entity) -> None:
    world.say(
        f"On {scene.place}, {child.id} and {friend.id} played like little {scene.pirate_word}s. "
        f"{scene.rig}"
    )
    world.say(
        f'They had a constant rule: stay together and tell the truth. {friend.id} grinned, '
        f'and {child.id} gave {friend.id} a brave nod.'
    )


def surprise_turn(world: World, scene: Scene, child: Entity, friend: Entity, hazard: Hazard) -> None:
    child.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    world.say(
        f"Then came a surprise at {scene.dark_spot}: {hazard.source} snagged the toy boat line."
    )
    world.say(
        f'"That could tangle us up," {friend.id} said, and both children looked at each other.'
    )


def choose_bravery(world: World, child: Entity, friend: Entity) -> None:
    child.memes["bravery"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'{child.id} took a breath. "I can do it," {child.id} said, and {friend.id} stayed close.'
    )


def rescue(world: World, scene: Scene, child: Entity, friend: Entity, parent: Entity,
           hazard: Hazard, rescue: Rescue) -> None:
    if rescue.id == "lasso":
        world.say(
            f"{child.id} used {rescue.label} with careful hands and {rescue.text}."
        )
    else:
        world.say(f"{child.id} {rescue.text}.")
    world.say(
        f"{friend.id} cheered, and {parent.label_word.capitalize()} smiled from the side of the deck."
    )
    world.say(
        f"At the end, {scene.ending_image}, and the two friends sailed on together."
    )


def tell(scene: Scene, hazard: Hazard, rescue: Rescue, child_name: str, child_gender: str,
         friend_name: str, friend_gender: str, parent_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero",
                             traits=["brave"], tags={"friendship", "bravery"}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend",
                              traits=["loyal"], tags={"friendship"}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent",
                              label="the parent"))

    child.memes["bravery"] = BRAVERY_START
    friend.memes["friendship"] = 2.0

    story_scene(world, scene, child, friend, parent)
    world.para()
    surprise_turn(world, scene, child, friend, hazard)
    choose_bravery(world, child, friend)
    world.para()
    if rescue.power < 1:
        raise StoryError("Rescue choice is unreasonable for this world.")
    rescue(world, scene, child, friend, parent, hazard, rescue)
    world.facts.update(scene=scene, hazard=hazard, rescue=rescue, child=child, friend=friend, parent=parent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    hazard: Hazard = f["hazard"]
    return [
        f"Write a pirate tale for a young child that includes the words lasso, dogie, and constant on {scene.place}.",
        f"Tell a brave friendship story where {f['child'].id} and {f['friend'].id} face a surprise at {scene.dark_spot} and use a lasso to help.",
        f"Write a short pirate adventure with surprise, bravery, and friendship, and make sure the dogie helps at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene: Scene = f["scene"]
    hazard: Hazard = f["hazard"]
    rescue: Rescue = f["rescue"]
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question=f"What surprised {child.id} and {friend.id}?",
            answer=(
                f"A snag at {scene.dark_spot} surprised them when {hazard.source} got in the way. "
                f"It turned the game into a problem that needed courage and quick thinking."
            ),
        ),
        QAItem(
            question=f"How did {child.id} show bravery?",
            answer=(
                f"{child.id} stayed calm and used the lasso to help. "
                f"That brave choice solved the surprise without giving up the friendship."
            ),
        ),
        QAItem(
            question="What made the ending feel happy?",
            answer=(
                f"The friends solved the problem together, and {parent.label_word} saw them work as a team. "
                f"That left them safe, proud, and still playing like pirates."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lasso?",
            answer="A lasso is a rope loop used to catch or pull something from a distance.",
        ),
        QAItem(
            question="What does friendship mean here?",
            answer="Friendship means the two children help each other and stay kind even when something goes wrong.",
        ),
        QAItem(
            question="Why is surprise important in a pirate tale?",
            answer="Surprise makes the adventure feel sudden, and it gives the brave characters a problem to solve.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(scene="deck", hazard="kite", rescue="lasso", child="Maya", child_gender="girl",
                friend="Toby", friend_gender="boy", parent="mother"),
    StoryParams(scene="island", hazard="net", rescue="lasso", child="Eli", child_gender="boy",
                friend="Nora", friend_gender="girl", parent="father"),
    StoryParams(scene="harbor", hazard="rope", rescue="cut_free", child="Lila", child_gender="girl",
                friend="Milo", friend_gender="boy", parent="mother"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if args.hazard and args.hazard not in HAZARDS:
        raise StoryError("Unknown hazard.")
    if args.rescue and args.rescue not in RESCUES:
        raise StoryError("Unknown rescue.")
    scenes = [args.scene] if args.scene else list(SCENES)
    hazards = [args.hazard] if args.hazard else list(HAZARDS)
    rescues = [args.rescue] if args.rescue else list(RESCUES)
    combos = [(s, h, r) for s in scenes for h in hazards for r in rescues]
    if not combos:
        raise StoryError("No valid combinations.")
    s, h, r = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    friend = args.friend or rng.choice(NAMES_BOY if friend_gender == "boy" else NAMES_GIRL)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        scene=s, hazard=h, rescue=r, child=child, child_gender=child_gender,
        friend=friend, friend_gender=friend_gender, parent=parent
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Invalid scene.")
    if params.hazard not in HAZARDS:
        raise StoryError("Invalid hazard.")
    if params.rescue not in RESCUES:
        raise StoryError("Invalid rescue.")
    world = tell(
        SCENES[params.scene], HAZARDS[params.hazard], RESCUES[params.rescue],
        params.child, params.child_gender, params.friend, params.friend_gender, params.parent
    )
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


ASP_RULES = r"""
hazard(H) :- hazard_id(H).
brave(C) :- child(C).
friendly(F) :- friend(F).
valid(S,H,R) :- scene_id(S), hazard_id(H), rescue_id(R), hazard(H), rescue_id(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SCENES:
        lines.append(asp.fact("scene_id", s))
    for h in HAZARDS:
        lines.append(asp.fact("hazard_id", h))
    for r in RESCUES:
        lines.append(asp.fact("rescue_id", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH between Python and ASP combos")
    else:
        print(f"OK: {len(py)} combos match")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: generate smoke test passed")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with lasso, dogie, and constant.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
