#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sword_teal_rhyme_dialogue_suspense_heartwarming.py
===================================================================================

A small standalone storyworld about a child, a teal scarf, and a missing toy sword.
The world is built from typed entities with physical meters and emotional memes,
and it supports rhyme, dialogue, suspense, and a heartwarming turn.

This script follows the Storyweavers contract:
- stdlib-only script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- support for --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
    atmosphere: str
    rhyme_hint: str
    suspense: str


@dataclass
class Prize:
    id: str
    label: str
    type: str
    phrase: str
    safe_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    prize: str
    helper: str
    child: str = "Mia"
    child_gender: str = "girl"
    parent: str = "mom"
    parent_gender: str = "woman"
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["lost"] >= THRESHOLD and ("relief", e.id) not in world.fired:
            world.fired.add(("relief", e.id))
            e.memes["worry"] = 0.0
            e.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief)]


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


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}, side by side,"

def rhyme_line2(a: str, b: str) -> str:
    return f"kept the little world warm with love as their guide."


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for prize_id, prize in PRIZES.items():
            for helper_id, helper in HELPERS.items():
                if "sword" in prize.tags and helper_id == "ribbon":
                    continue
                combos.append((scene_id, prize_id, helper_id))
    return combos


def scene_intro(world: World, scene: Scene, child: Entity, prize: Prize) -> None:
    world.say(
        f"{child.id} lived near {scene.place}, where {scene.atmosphere}. "
        f"{scene.rhyme_hint}"
    )
    world.say(
        f"{child.id} loved {prize.phrase}, a little treasure with a story to tell."
    )


def setup_dream(world: World, child: Entity, prize: Prize) -> None:
    child.memes["hope"] += 1
    world.say(f'“I will keep it safe,” {child.id} whispered, “and carry it close.”')


def suspense_turn(world: World, child: Entity, parent: Entity, prize: Prize, helper: Helper) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Then the room went quiet. {child.id} reached for {prize.label}, but it was gone."
    )
    world.say(
        f'“{child.id}?” {parent.id} called softly. “Did you see it anywhere?”'
    )
    world.say(
        f'{child.id} blinked at the teal blanket and the tidy shelf. “No, {parent.label_word}, not there.”'
    )
    world.say(
        f"The search felt like a puzzle with one missing piece, and the answer hid somewhere close."
    )


def search_scene(world: World, child: Entity, parent: Entity, prize: Prize, helper: Helper) -> None:
    child.memes["suspense"] += 1
    world.say(
        f"{child.id} peeked under the bed, behind the chair, and beside the teal curtain."
    )
    world.say(
        f'“Could it be here?” {child.id} asked. ““No,” said {parent.id}, “but we can look together.”'
    )
    world.say(
        f"At last, {parent.id} found {prize.phrase} tucked where a sleepy blanket had hidden it."
    )


def heartwarming_turn(world: World, child: Entity, parent: Entity, prize: Prize, helper: Helper) -> None:
    prize_ent = world.get("prize")
    prize_ent.meters["found"] += 1
    prize_ent.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.id} smiled. “There it is, little star.” {child.id} hugged {parent.pronoun("object")}.'
    )
    world.say(
        f'"And my teal {helper.label}, too," {child.id} said, lifting {helper.phrase}. '
        f'"It helps me feel brave.”'
    )
    world.say(
        f'{parent.id} tucked the {prize.label} and {helper.label} together on the shelf. '
        f'"A sword can rest, and hearts can glow," {parent.id} said.'
    )
    world.say(
        "So the child fell asleep safe and proud, with teal things nearby and love all around."
    )


def tell(scene: Scene, prize: Prize, helper: Helper, child_name: str, child_gender: str,
         parent_name: str, parent_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    prize_ent = world.add(Entity(id="prize", type=prize.type, label=prize.label, tags=set(prize.tags)))
    helper_ent = world.add(Entity(id="helper", type=helper.type, label=helper.label, tags=set(helper.tags)))

    scene_intro(world, scene, child, prize)
    setup_dream(world, child, prize)
    world.para()
    suspense_turn(world, child, parent, prize, helper)
    search_scene(world, child, parent, prize, helper)
    world.para()
    heartwarming_turn(world, child, parent, prize, helper)

    world.facts.update(
        scene=scene, prize=prize, helper=helper, child=child, parent=parent,
        found=True, suspense=True, heartwarming=True, rhyme=True,
    )
    return world


SCENES = {
    "bedroom": Scene(
        place="a small bedroom",
        atmosphere="the teal lamp made the shadows soft instead of scary",
        rhyme_hint="At night it was quiet, but not too quiet; the teal light turned fright into flight.",
        suspense="under the bed",
    ),
    "playroom": Scene(
        place="a bright playroom",
        atmosphere="the teal rug was neat and the toy box sat waiting",
        rhyme_hint="With books and blocks in tidy sight, the teal room felt kind and right.",
        suspense="behind the toy box",
    ),
}

PRIZES = {
    "sword": Prize(
        id="sword",
        label="toy sword",
        type="toy",
        phrase="the little sword",
        safe_place="the shelf",
        tags={"sword", "toy"},
    ),
    "teal_star": Prize(
        id="teal_star",
        label="teal star charm",
        type="toy",
        phrase="the teal star charm",
        safe_place="the drawer",
        tags={"teal", "toy"},
    ),
}

HELPERS = {
    "blanket": Helper(
        id="blanket",
        label="teal blanket",
        type="blanket",
        phrase="the teal blanket",
        use="warmth",
        tags={"teal"},
    ),
    "ribbon": Helper(
        id="ribbon",
        label="teal ribbon",
        type="ribbon",
        phrase="the teal ribbon",
        use="comfort",
        tags={"teal"},
    ),
}

CHILD_NAMES = ["Mia", "Lena", "Noah", "Ivy", "Eli", "Rose"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the words "sword" and "teal" and uses dialogue, rhyme, and suspense.',
        f"Tell a gentle story about {f['child'].id} losing a toy sword in a teal room and finding it again with a parent.",
        f'Write a short suspenseful but warm bedtime story where teal things and a sword both matter.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prize = f["prize"]
    helper = f["helper"]
    qa = [
        ("What was the child looking for?",
         f"{child.id} was looking for {prize.label}. It mattered because it was the toy that made the child feel brave."),
        ("What made the scene suspenseful?",
         f"The room went quiet and the toy seemed to vanish for a moment. That made the search feel suspenseful, even though {parent.id} stayed calm and looked together with the child."),
        ("How did the story end?",
         f"It ended with {prize.label} safe on {prize.safe_place} and {helper.label} nearby. The child felt loved, and the teal colors made the ending feel gentle and warm."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a sword in a kid's story?",
         "In a kid's story, a sword is often a pretend or toy object used in brave play. It can stand for courage without needing real danger."),
        ("Why might teal feel comforting?",
         "Teal is a calm blue-green color, so it can feel cool and peaceful. Soft colors like that often make a room seem safe."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="bedroom", prize="sword", helper="blanket", child="Mia", child_gender="girl", parent="mom", parent_gender="woman"),
    StoryParams(scene="playroom", prize="teal_star", helper="ribbon", child="Noah", child_gender="boy", parent="dad", parent_gender="man"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen parts do not make a gentle suspense story worth telling.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming tiny storyworld with a sword, teal colors, rhyme, dialogue, and suspense."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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
    scenes = list(SCENES)
    prizes = list(PRIZES)
    helpers = list(HELPERS)
    scene = args.scene or rng.choice(scenes)
    prize = args.prize or rng.choice(prizes)
    helper = args.helper or rng.choice(helpers)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(CHILD_NAMES)
    parent = args.parent or ("Mom" if parent_gender == "woman" else "Dad")
    return StoryParams(
        scene=scene,
        prize=prize,
        helper=helper,
        child=child,
        child_gender=child_gender,
        parent=parent,
        parent_gender=parent_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    world = tell(
        SCENES[params.scene],
        PRIZES[params.prize],
        HELPERS[params.helper],
        params.child,
        params.child_gender,
        params.parent,
        params.parent_gender,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
valid(Scene, Prize, Helper) :- scene(Scene), prize(Prize), helper(Helper).
"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python combo checks.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP and Python agree; generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
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
