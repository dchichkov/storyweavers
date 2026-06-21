#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/frost_harsh_breaking_twist_dialogue_foreshadowing_mystery.py
==============================================================================================

A small mystery storyworld about a frosty shop, a harsh message, a breaking clue,
and a twist reveal. The world keeps a simple simulation of physical evidence
and emotional pressure, then renders a child-facing mystery with dialogue and
foreshadowing.

Theme seed words: frost, harsh, breaking
Style: mystery
Features: twist, dialogue, foreshadowing
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
LEAD_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    clues: list[str] = field(default_factory=list)
    linked_to: str = ""

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
class Scene:
    place: str
    weather: str
    object_name: str
    object_label: str
    object_near: str
    object_breaks: bool = True
    frost_level: int = 1
    harsh_level: int = 1


@dataclass
class StoryParams:
    scene: str
    suspect: str
    clue: str
    twist: str
    name: str
    name_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None
    weather: str = "cold"
    tone: str = "mystery"


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_breaking(world: World) -> list[str]:
    out = []
    clue = world.get("clue")
    if clue.meters["breaking"] >= THRESHOLD and ("breaking", clue.id) not in world.fired:
        world.fired.add(("breaking", clue.id))
        world.get("detective").memes["alert"] += 1
        world.get("helper").memes["alarm"] += 1
        out.append("__breaking__")
    return out


def _r_frost(world: World) -> list[str]:
    out = []
    scene = world.get("scene")
    if scene.meters["frost"] >= THRESHOLD and ("frost", scene.id) not in world.fired:
        world.fired.add(("frost", scene.id))
        world.get("detective").memes["curious"] += 1
        out.append("A pale frost glossed the window and made the room feel even quieter.")
    return out


CAUSAL_RULES = [Rule("breaking", _r_breaking), Rule("frost", _r_frost)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if not s.startswith("__"):
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def scene_cfg(scene_id: str) -> Scene:
    try:
        return SCENES[scene_id]
    except KeyError as e:
        raise StoryError(f"Unknown scene: {scene_id}") from e


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.scene not in SCENES:
        raise StoryError("Unknown scene choice.")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect choice.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue choice.")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("Unknown twist choice.")

    scene = args.scene or rng.choice(list(SCENES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    clue = args.clue or rng.choice(list(CLUES))
    twist = args.twist or rng.choice(list(TWISTS))
    name_gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if name_gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper_gender = rng.choice(["girl", "boy"])
    helper_pool = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    helper = args.helper or rng.choice([n for n in helper_pool if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        scene=scene,
        suspect=suspect,
        clue=clue,
        twist=twist,
        name=name,
        name_gender=name_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        weather="cold",
        tone="mystery",
    )


def is_reasonable(params: StoryParams) -> bool:
    scene = SCENES[params.scene]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    return scene.object_breaks and clue.kind == "evidence" and suspect.kind == "person"


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SCENES:
        for su in SUSPECTS:
            for c in CLUES:
                for t in TWISTS:
                    p = StoryParams(scene=s, suspect=su, clue=c, twist=t, name="Ava", name_gender="girl", helper="Mia", helper_gender="girl", parent="mother")
                    if is_reasonable(p):
                        out.append((s, su, c, t))
    return out


def infer_twist(world: World, params: StoryParams) -> str:
    if params.twist == "mirror":
        return "The broken clue was not stolen at all; it had been a mirror shard, and the old owner had hidden it so no one would get cut."
    if params.twist == "pet":
        return "The suspect was not a thief. The real culprit was a frightened cat that knocked the clue down during the frost."
    return "The harsh note was a warning, not a threat: someone had tried to protect the clue from the cold all along."


def tell(params: StoryParams) -> World:
    if not is_reasonable(params):
        raise StoryError("This combination does not form a believable mystery.")
    world = World()
    detective = world.add(Entity(id="detective", kind="character", type=params.name_gender, label=params.name, role="detective", traits=["curious"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper, role="helper", traits=["careful"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="the parent"))
    scene = world.add(Entity(id="scene", type="place", label=SCENES[params.scene].place))
    clue = world.add(Entity(id="clue", type="thing", label=CLUES[params.clue].label, linked_to=params.suspect))
    suspect = world.add(Entity(id="suspect", type="person", label=SUSPECTS[params.suspect].label))
    detective.memes["curious"] += 1
    helper.memes["worry"] += 1

    world.say(f"On a cold evening, {detective.label} and {helper.label} crept into {scene.label}.")
    world.say(f"The air carried {scene_cfg(params.scene).weather} frost, and everything felt quiet enough to hear a pin drop.")
    world.say(f"Then {detective.label} spotted {clue.label} near {SCENES[params.scene].object_near}.")
    world.say(f'"That is a harsh little clue," {helper.label} whispered. "And look — it is {params.suspect}\'s."')

    world.para()
    clue.meters["breaking"] += 1
    scene.meters["frost"] += 1
    world.say(f"As {detective.label} picked it up, there was a breaking sound from the next room.")
    propagate(world, narrate=True)
    world.say(f'"Did you hear that?" {detective.label} said.')
    world.say(f'"Yes," {helper.label} said. "It sounded like someone was trying to warn us."')

    world.para()
    world.say(f"They followed the trail, and the twist made sense at last.")
    world.say(infer_twist(world, params))
    world.say(f'The harsh note at the table was really a message for {params.suspect}, not a threat to {detective.label}.')
    world.say(f'In the end, {detective.label} closed the case, the frost stayed on the windows, and the breaking clue led them to the truth.')

    world.facts.update(
        detective=detective,
        helper=helper,
        parent=parent,
        scene=scene,
        clue=clue,
        suspect=suspect,
        params=params,
        twist=params.twist,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a child-friendly mystery story that includes the words "frost", "harsh", and "breaking".',
        f'Tell a mystery with dialogue and a twist where {p.name} follows a harsh clue through the frost and learns the truth.',
        f'Write a short foreshadowing mystery about a breaking sound, a cold scene, and a final twist.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p = world.facts["params"]
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    clue = world.facts["clue"]
    suspect = world.facts["suspect"]
    qas = [
        ("Who is the story about?", f"It is about {detective.label} and {helper.label}, who search for the truth together. They follow a clue and keep asking careful questions."),
        ("What did they find?", f'They found {clue.label}. It looked harsh and strange at first, but it helped point toward {suspect.label}.'),
        ("What does the breaking sound mean in the story?", f"It was a sign that something important was happening nearby. The sound also foreshadowed that the clue would lead them to a bigger truth."),
        ("What was the twist?", infer_twist(world, p)),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is frost?", "Frost is a thin layer of ice crystals that forms when the air is very cold. It can sparkle on windows and grass."),
        ("What does a harsh voice sound like?", "A harsh voice sounds rough or sharp. It may feel unfriendly, even if the speaker has a good reason."),
        ("What can a breaking sound make you think?", "A breaking sound can make you think something cracked, fell, or snapped. In a mystery, it can be a clue that something changed."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.clues:
            bits.append(f"clues={e.clues}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


SCENES = {
    "station": Scene(place="the old train station", weather="frosty", object_name="bench", object_label="a cracked bench", object_near="the ticket window", object_breaks=True, frost_level=2, harsh_level=2),
    "museum": Scene(place="the little museum hall", weather="cold", object_name="case", object_label="a glass case", object_near="the display table", object_breaks=True, frost_level=1, harsh_level=1),
    "library": Scene(place="the quiet library room", weather="wintery", object_name="lamp", object_label="a lamp stand", object_near="the reading nook", object_breaks=True, frost_level=1, harsh_level=2),
}

SUSPECTS = {
    "caretaker": Entity(id="caretaker_cfg", type="person", label="the caretaker"),
    "uncle": Entity(id="uncle_cfg", type="person", label="the uncle"),
    "neighbor": Entity(id="neighbor_cfg", type="person", label="the neighbor"),
}

CLUES = {
    "note": Entity(id="note_cfg", type="thing", label="a harsh note", attrs={"kind": "evidence"}),
    "key": Entity(id="key_cfg", type="thing", label="a small brass key", attrs={"kind": "evidence"}),
    "glove": Entity(id="glove_cfg", type="thing", label="a single glove", attrs={"kind": "evidence"}),
}

TWISTS = {
    "mirror": "mirror",
    "pet": "pet",
    "warning": "warning",
}

GIRL_NAMES = ["Ava", "Mia", "Nora", "Lily", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Theo", "Sam", "Leo"]


@dataclass
class ASPConfig:
    pass


ASP_RULES = r"""
is_reasonable(Scene, Suspect, Clue, Twist) :- scene(Scene), suspect(Suspect), clue(Clue), twist(Twist), breaking_clue(Clue), person(Suspect), breakable_scene(Scene).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SCENES:
        lines.append(asp.fact("scene", s))
        lines.append(asp.fact("breakable_scene", s))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
        lines.append(asp.fact("person", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
        lines.append(asp.fact("breaking_clue", c))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show is_reasonable/4."))
    return sorted(set(asp.atoms(model, "is_reasonable")))


def asp_verify() -> int:
    import tempfile
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combo gates differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, suspect=None, clue=None, twist=None, name=None, gender=None, helper=None, helper_gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with frost, harsh clues, and a breaking twist.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(scene="station", suspect="caretaker", clue="note", twist="warning", name="Ava", name_gender="girl", helper="Mia", helper_gender="girl", parent="mother"),
    StoryParams(scene="museum", suspect="uncle", clue="key", twist="mirror", name="Noah", name_gender="boy", helper="Eli", helper_gender="boy", parent="father"),
    StoryParams(scene="library", suspect="neighbor", clue="glove", twist="pet", name="Lily", name_gender="girl", helper="Sam", helper_gender="boy", parent="mother"),
]


def resolve_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.scene not in SCENES:
        raise StoryError("Unknown scene choice.")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect choice.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue choice.")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("Unknown twist choice.")
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show is_reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
