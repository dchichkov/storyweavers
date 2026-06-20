#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gate_yum_dim_sharing_suspense_comedy.py
=======================================================================

A tiny standalone storyworld about a child, a gate, a snack, and a funny,
suspenseful sharing problem.

Seed words:
- gate
- yum-dim

Features:
- Sharing
- Suspense

Style:
- Comedy

The world model tracks a small family picnic scene:
a child has a "yum-dim" snack box, another child wants a share, and a gate
stands between the picnic blanket and a little garden path. Suspense comes from
the snack almost getting dropped or the gate almost swinging shut; comedy comes
from the characters being dramatic about a very small problem, then solving it
kindly.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- story driven by state changes
- prompts, grounded story QA, and world-knowledge QA
- Python reasonableness gate plus inline ASP twin
- CLI with --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    traits: list[str] = field(default_factory=list)
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
class Scene:
    id: str
    place: str
    setup: str
    gate: str
    suspense: str
    ending: str


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    yum: str
    sharing: str
    plural: bool = False
    edible: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareMethod:
    id: str
    sense: int
    speed: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("suspense", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "gate" in world.entities:
            world.get("gate").meters["creak"] += 1
        out.append("__suspense__")
    return out


def _r_hungry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["hungry"] < THRESHOLD:
            continue
        sig = ("hungry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("__yum__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("hungry", "physical", _r_hungry),
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


SCENES = {
    "garden": Scene(
        "garden",
        "the garden",
        "The picnic blanket was spread under a beanpole tomato plant, and a wobbly chair guarded the lemonade.",
        "The little gate led to the path, and it creaked whenever the wind got nosy.",
        "Everyone kept glancing at the gate, as if it might do a pratfall at any second.",
        "The gate stayed open, the snack stayed shared, and the garden kept its secret laugh.",
    ),
    "backyard": Scene(
        "backyard",
        "the backyard",
        "The picnic blanket sat beside a sandbox castle, and a watering can wore a tiny red ribbon.",
        "The little gate stood near the fence, and it liked to make a dramatic squeak.",
        "Everyone watched the gate like it was the star of a very silly show.",
        "The gate stayed open, the snack was shared, and the backyard felt like applause.",
    ),
}

SNACKS = {
    "yum-dim": Snack(
        "yum-dim",
        "yum-dim",
        "a little box of yum-dim",
        "yum-dim",
        "sharing",
        plural=False,
        tags={"yum-dim", "snack", "share"},
    ),
    "apple-puff": Snack(
        "apple-puff",
        "apple-puff",
        "a paper bowl of apple-puffs",
        "apple-puff",
        "sharing",
        plural=True,
        tags={"apple", "snack", "share"},
    ),
}

METHODS = {
    "split": ShareMethod("split", 3, 3,
                         "opened the box and split the snack into two equal halves",
                         "tried to split it, but the snack tumbled onto the grass",
                         "opened the box and split the snack into two equal halves",
                         tags={"share"}),
    "offer": ShareMethod("offer", 3, 2,
                         "held the box between them and offered the first bite with a grin",
                         "held out the box, but it slipped and almost bounced under the gate",
                         "held the box between them and offered the first bite with a grin",
                         tags={"share"}),
    "plate": ShareMethod("plate", 2, 4,
                         "set the snack on a plate and handed out careful bites one by one",
                         "set the snack down, but the wind nudged the plate toward the gate",
                         "set the snack on a plate and handed out careful bites one by one",
                         tags={"share"}),
}

NAMES = ["Mia", "Lena", "Toby", "Finn", "Ava", "Noah", "Zoe", "Ben"]
TRAITS = ["dramatic", "helpful", "curious", "careful", "silly", "polite"]


@dataclass
class StoryParams:
    scene: str
    snack: str
    method: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def reasonableness_ok(scene: Scene, snack: Snack, method: ShareMethod) -> bool:
    return snack.edible and "share" in snack.tags and method.sense >= 2 and scene.id in SCENES


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, n, m) for s in SCENES for n in SNACKS for m in METHODS
            if reasonableness_ok(SCENES[s], SNACKS[n], METHODS[m])]


def outcome_of(params: StoryParams) -> str:
    return "shared"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about sharing a snack by a gate.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in NAMES if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.snack is None or c[1] == args.snack)
              and (args.method is None or c[2] == args.method)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, snack, method = rng.choice(sorted(combos))
    snack_obj = SNACKS[snack]
    method_obj = METHODS[method]
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" else "girl")
    n1 = args.name1 or _pick_name(rng, g1)
    n2 = args.name2 or _pick_name(rng, g2, avoid=n1)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(scene, snack, method, n1, g1, n2, g2, parent, trait)


def tell(scene: Scene, snack: Snack, method: ShareMethod, p: StoryParams) -> World:
    world = World()
    a = world.add(Entity(p.child1, kind="character", type=p.child1_gender, role="shareer",
                         traits=[p.trait]))
    b = world.add(Entity(p.child2, kind="character", type=p.child2_gender, role="guest",
                         traits=["hungry"]))
    parent = world.add(Entity("Parent", kind="character", type=p.parent, role="parent", label="the parent"))
    gate = world.add(Entity("gate", type="gate", label="the gate"))
    snack_ent = world.add(Entity("snack", type="snack", label=snack.label))
    a.memes["joy"] += 1
    b.meters["hungry"] += 1
    world.say(f"One afternoon, {a.id} and {b.id} set up a picnic in {scene.place}. {scene.setup}")
    world.say(f'{a.id} patted the box and said, "{snack.yum}! I saved a {snack.label} for us."')
    world.para()
    world.say(f'But the gate by the path made a silly little squeak. {scene.gate}')
    world.say(f'{b.id} peered over the blanket and whispered, "What if the gate slams? That would be a tiny disaster."')
    a.memes["worry"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f'{a.id} gasped in a huge, pretend-hero voice: "Then we must share before the gate can stage its show!"')
    world.say(f'{b.id} nodded so hard the lemonade almost wobbled. "{snack.sharing} is my favorite emergency."')
    body = method.text
    if method.id == "plate":
        body += " and kept one eye on the gate like a very serious squirrel."
    world.say(f'Together, they {body}.')
    snack_ent.meters["shared"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.para()
    world.say(f'Then the gate gave one final creak, as if it wanted a bite too. Everyone laughed, because it was only a gate, and it could not eat yum-dim.')
    world.say(f'{scene.ending}')
    world.facts.update(scene=scene, snack=snack, method=method, a=a, b=b, parent=parent, gate=gate,
                       outcome="shared", shared=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny sharing story for a young child that includes the words "gate" and "{f["snack"].label}".',
        f"Tell a suspenseful but gentle comedy where {f['a'].id} and {f['b'].id} worry about a squeaky gate and decide to share a snack before anything goes wrong.",
        f'Write a child-friendly story where a gate makes everyone nervous, but the characters solve it by sharing and laughing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, scene, snack = f["a"], f["b"], f["scene"], f["snack"]
    return [
        QAItem(
            question="What made the children act so dramatically?",
            answer=f"The little gate kept making a squeaky sound, so they treated it like a big suspenseful moment. That silly worry pushed them to share the snack right away."
        ),
        QAItem(
            question=f"What did {a.id} and {b.id} do with the {snack.label}?",
            answer=f"They shared it together. {a.id} opened it first, and then both children laughed when the gate tried to steal the scene."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the gate still open, the snack shared, and everyone laughing in {scene.place}. The tiny problem turned into a funny little picnic instead of a real disaster."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gate?",
            answer="A gate is a swinging door in a fence or wall. It can open and close to let people through."
        ),
        QAItem(
            question="What does it mean to share?",
            answer="Sharing means letting someone else have some of what you have. It is a kind way to make sure everybody gets a turn."
        ),
        QAItem(
            question="Why can suspense be funny in a story?",
            answer="Suspense makes you wonder what will happen next. In a comedy, the worry is small and the ending is safe, so the tension turns into a laugh."
        ),
        QAItem(
            question="What does yum mean in this story?",
            answer="Yum is a word people say when food tastes very good. Here it helps the snack sound extra appealing."
        ),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "yum-dim", "split", "Mia", "girl", "Toby", "boy", "mother", "dramatic"),
    StoryParams("backyard", "apple-puff", "offer", "Lena", "girl", "Finn", "boy", "father", "silly"),
]


def explain_response(rid: str) -> str:
    r = METHODS[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense}).)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.edible:
            lines.append(asp.fact("edible", sid))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, m.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, N, M) :- scene(S), snack(N), method(M), edible(N), sense(M, X), X >= 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, snack=None, method=None, parent=None, name1=None, name2=None, gender1=None, gender2=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], SNACKS[params.snack], METHODS[params.method], params)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
