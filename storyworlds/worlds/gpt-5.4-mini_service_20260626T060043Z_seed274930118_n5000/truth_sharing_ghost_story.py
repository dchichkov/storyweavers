#!/usr/bin/env python3
"""
A small storyworld about a shy ghost, a missing truth, and a sharing circle that
makes the room feel warm again.

The world premise:
- A child notices a ghostly presence in a quiet room.
- Someone has been hiding the truth about a small mistake.
- The ghost cannot rest until the truth is shared.
- Once the truth is spoken, the group shares what they know, repairs the harm,
  and the ghost becomes gentle instead of spooky.

The story engine models:
- characters with meters and memes
- a hidden object or broken item
- the emotional tension of secrecy
- the relief of truth-sharing and repair

This world is intentionally narrow: only truth + sharing stories that can
resolve in a child-facing, ghost-story style are generated.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"broken": 0.0, "found": 0.0, "fixed": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "guilt": 0.0, "relief": 0.0, "trust": 0.0, "spooky": 0.0}

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
class Setting:
    place: str = "the old attic"
    hush: str = "The room was quiet, with soft dust in the corners and moonlight on the floor."


@dataclass
class Secret:
    id: str
    truth: str
    broken_item: str
    repair: str
    hiding_phrase: str


@dataclass
class StoryParams:
    place: str
    secret: str
    child_name: str
    child_type: str
    child_trait: str
    ghost_name: str
    seed: Optional[int] = None


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_truth_softens(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if child.memes["guilt"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["spooky"] = max(0.0, ghost.memes["spooky"] - 1.0)
    ghost.memes["trust"] += 1.0
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    out.append("The ghost's cold feeling thinned when the truth was finally shared.")
    return out


def _r_share_repairs(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    item = world.entities.get("item")
    if not child or not item:
        return out
    if child.memes["guilt"] < THRESHOLD or item.meters["broken"] < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["fixed"] = 1.0
    item.meters["broken"] = 0.0
    child.memes["relief"] += 1.0
    out.append(f"Together, they mended the {item.label} with careful hands.")
    return out


CAUSAL_RULES = [
    Rule("truth_softens", "social", _r_truth_softens),
    Rule("share_repairs", "physical", _r_share_repairs),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "attic": Setting("the old attic", "The room was quiet, with soft dust in the corners and moonlight on the floor."),
    "hall": Setting("the candlelit hall", "The hall was still, and the candles made little gold pools of light."),
    "bedroom": Setting("the bedroom", "The bedroom was hush-soft, with blankets piled like little hills."),
}

SECRETS = {
    "vase": Secret(
        id="vase",
        truth="the child bumped the vase and it cracked on the floor",
        broken_item="vase",
        repair="glue it back together",
        hiding_phrase="hid the crack behind a towel",
    ),
    "lamp": Secret(
        id="lamp",
        truth="the child knocked the lamp and its shade bent",
        broken_item="lamp",
        repair="straighten the shade",
        hiding_phrase="pushed it close to the wall",
    ),
    "toy": Secret(
        id="toy",
        truth="the child stepped on the toy and one wheel popped off",
        broken_item="toy truck",
        repair="snap the wheel back on",
        hiding_phrase="slid it under the bed",
    ),
}

GHOST_NAMES = ["Milo", "Nell", "Pip", "Wren", "Boo", "Mara"]
CHILD_NAMES = ["Ada", "Finn", "Lily", "Noah", "Mia", "Owen", "Zoe", "Ben"]
TRAITS = ["curious", "gentle", "brave", "shy", "thoughtful", "sleepy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, secret_id) for place in SETTINGS for secret_id in SECRETS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.secret and args.secret not in SECRETS:
        raise StoryError("Unknown secret.")

    place = args.place or rng.choice(list(SETTINGS))
    secret = args.secret or rng.choice(list(SECRETS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    child_trait = args.child_trait or rng.choice(TRAITS)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(
        place=place,
        secret=secret,
        child_name=child_name,
        child_type=child_type,
        child_trait=child_trait,
        ghost_name=ghost_name,
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    secret = SECRETS[params.secret]
    world = World(setting)

    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="thing",
        label=secret.broken_item,
        phrase=secret.broken_item,
        owner=child.id,
        caretaker=child.id,
    ))

    child.memes["guilt"] = 1.0
    child.memes["fear"] = 1.0
    ghost.memes["spooky"] = 1.0

    world.say(f"{params.child_name} was a {params.child_trait} {params.child_type} who lived near {setting.place}.")
    world.say(f"At night, {params.ghost_name} the ghost drifted through the dark, but {params.ghost_name} was never cruel.")
    world.say(setting.hush)
    world.say(f"{params.child_name} kept a secret: {secret.hiding_phrase} after {secret.truth}.")
    world.say(f"That secret felt heavy, and the ghost seemed to glow brighter every time the room went still.")

    world.para()
    world.say(f"One evening, {params.ghost_name} floated close and whispered, \"Truth is lighter when it is shared.\"")
    world.say(f"{params.child_name} looked at the floor, then took a careful breath and said the truth out loud.")
    child.memes["guilt"] = 0.0
    child.memes["trust"] += 1.0
    propagate(world, narrate=True)

    world.para()
    if item.meters["fixed"] < THRESHOLD:
        world.say(f"Together they found the broken {item.label} and fixed it as best they could.")
        item.meters["fixed"] = 1.0
        item.meters["broken"] = 0.0
    world.say(f"The ghost's glow turned soft and silver, like moonlight on a clean window.")
    world.say(f"By the end, {params.child_name} felt brave, and {params.ghost_name} felt like a friend who could stay.")

    world.facts.update(
        child=child,
        ghost=ghost,
        item=item,
        secret=secret,
        setting=setting,
        params=params,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    s = f["secret"]
    return [
        f'Write a gentle ghost story about a {p.child_trait} {p.child_type} named {p.child_name} who must tell the truth about a {s.broken_item}.',
        f"Tell a short story where {p.ghost_name} the ghost helps {p.child_name} share a secret and fix what was broken.",
        f'Write a child-friendly ghost story with the word "truth" and an ending where sharing makes everyone feel better.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    s = f["secret"]
    item = f["item"]
    ghost = f["ghost"]
    child = f["child"]
    return [
        QAItem(
            question=f"What was {p.child_name} hiding in the story?",
            answer=f"{p.child_name} was hiding the truth about {s.truth}, and that made {child.pronoun('possessive')} heart feel heavy.",
        ),
        QAItem(
            question=f"Who asked {p.child_name} to share the truth?",
            answer=f"{ghost.label} the ghost asked {p.child_name} to share the truth, because honesty made the room feel softer.",
        ),
        QAItem(
            question=f"What did {p.child_name} and {ghost.label} do after the truth came out?",
            answer=f"They worked together to {s.repair} and make the {item.label} whole again.",
        ),
        QAItem(
            question=f"How did {p.child_name} feel at the end?",
            answer=f"{p.child_name} felt brave and relieved, because {child.pronoun('subject')} had shared the truth and fixed the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is truth?",
            answer="Truth means saying what really happened, even if it feels hard for a little while.",
        ),
        QAItem(
            question="Why can sharing the truth help?",
            answer="Sharing the truth can help because other people can understand the problem and help fix it.",
        ),
        QAItem(
            question="What is a ghost in a story like this?",
            answer="A ghost is a spooky-looking character in the story, but it can still be kind and helpful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
truth_shared :- guilt(child), spoken_truth.
softer_ghost :- truth_shared.
repaired :- broken(item), truth_shared, sharing_help.
#show truth_shared/0.
#show softer_ghost/0.
#show repaired/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("guilt", "child"),
        asp.fact("broken", "item"),
        asp.fact("spoken_truth"),
        asp.fact("sharing_help"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show truth_shared/0.\n#show softer_ghost/0.\n#show repaired/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"truth_shared/0", "softer_ghost/0", "repaired/0"}
    if atoms == expected:
        print("OK: ASP and Python gate agree.")
        return 0
    print("Mismatch between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world about truth and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--secret", choices=SECRETS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-trait", choices=TRAITS)
    ap.add_argument("--ghost-name")
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
    StoryParams(place="attic", secret="vase", child_name="Mia", child_type="girl", child_trait="shy", ghost_name="Boo"),
    StoryParams(place="hall", secret="lamp", child_name="Noah", child_type="boy", child_trait="thoughtful", ghost_name="Nell"),
    StoryParams(place="bedroom", secret="toy", child_name="Ada", child_type="girl", child_trait="brave", ghost_name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show truth_shared/0.\n#show softer_ghost/0.\n#show repaired/0."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        print("ASP mode available for truth-sharing parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.place} with {p.ghost_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
