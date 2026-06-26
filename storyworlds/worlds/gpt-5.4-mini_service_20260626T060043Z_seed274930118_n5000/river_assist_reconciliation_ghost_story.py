#!/usr/bin/env python3
"""
A small ghost-story world with a river, an assist, and reconciliation.

The tale premise:
A child visits a quiet riverbank at dusk, meets a shy ghost, loses a small
treasure to the water, and learns the ghost is not there to frighten anyone.
The ghost assists, the child and ghost reconcile, and the ending proves the
change through a recovered object and a calmer night.

This world is intentionally narrow and constraint-checked: it generates a
single, coherent kind of story rather than a loose collection of spooky lines.
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
SETTINGS = {
    "riverbank": "the riverbank",
    "old_bridge": "the old bridge",
    "willow_path": "the willow path by the river",
}
MOODS = {"foggy", "twilight", "rainy"}
PRIZES = {
    "lantern": "a little red lantern",
    "boat_key": "a brass boat key",
    "scarf": "a blue scarf with silver thread",
}
CHILD_NAMES = ["Mina", "Leo", "Nia", "Owen", "Pia", "Ravi"]
GHOST_NAMES = ["Moth", "Hush", "Willow", "Bramble", "Eve", "Glim"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    haunted: bool = False
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["drift", "wet", "safe", "returned"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "trust", "hope", "relief", "lonely", "regret"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: str
    mood: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
class StoryParams:
    setting: str
    mood: str
    prize: str
    child_name: str
    child_type: str
    ghost_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: river, assist, reconciliation.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mood", choices=sorted(MOODS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name")
    ap.add_argument("--ghost")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, p) for s in SETTINGS for m in MOODS for p in PRIZES]


def reasonableness_gate(setting: str, mood: str, prize: str) -> bool:
    return setting in SETTINGS and mood in MOODS and prize in PRIZES


def explain_rejection(setting: str, mood: str, prize: str) -> str:
    return f"(No story: {setting}, {mood}, and {prize} do not form a coherent river-ghost reconciliation tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    mood = args.mood or rng.choice(sorted(MOODS))
    prize = args.prize or rng.choice(sorted(PRIZES))
    if not reasonableness_gate(setting, mood, prize):
        raise StoryError(explain_rejection(setting, mood, prize))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost or rng.choice(GHOST_NAMES)
    return StoryParams(setting=setting, mood=mood, prize=prize, child_name=child_name, child_type=child_type, ghost_name=ghost_name)


def _setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name, visible=True))
    ghost = world.add(Entity(id="ghost", kind="ghost", type="ghost", label=params.ghost_name, haunted=True, visible=False))
    prize = world.add(Entity(id="prize", kind="thing", type=params.prize, label=PRIZES[params.prize], phrase=PRIZES[params.prize], owner=child.id))
    world.facts.update(child=child, ghost=ghost, prize=prize, params=params)
    child.memes["fear"] += 1
    ghost.memes["lonely"] += 1
    world.say(f"{child.label} came to {SETTINGS[params.setting]} when the air was {params.mood} and still.")
    world.say(f"At the edge of the water, {child.label} held {prize.phrase} close and listened to the river whisper.")
    world.say(f"Then {ghost.label}, a shy ghost, floated out of the reeds like a pale breath.")
    world.para()


def _turn(world: World) -> None:
    child: Entity = world.facts["child"]
    ghost: Entity = world.facts["ghost"]
    prize: Entity = world.facts["prize"]
    child.memes["fear"] += 1
    ghost.memes["regret"] += 1
    world.say(f"{child.label} gasped and stepped back, because {ghost.label} looked spooky in the dim light.")
    world.say(f"{ghost.label} looked sorry and pointed at the river, where the current tugged at {prize.phrase}.")
    world.say(f"When {prize.phrase} slipped from {child.label}'s hands, it drifted toward the dark water.")
    world.say(f"That was when {ghost.label} decided to assist.")
    world.para()


def _assist(world: World) -> None:
    child: Entity = world.facts["child"]
    ghost: Entity = world.facts["ghost"]
    prize: Entity = world.facts["prize"]
    ghost.memes["trust"] += 1
    child.memes["hope"] += 1
    prize.meters["drift"] = 1.0
    world.say(f"{ghost.label} glided above the surface and touched the water only with a silver fingertip.")
    world.say(f"With a careful swirl of mist, {ghost.label} nudged {prize.phrase} away from a snag of roots.")
    world.say(f"Then {ghost.label} carried it back, and {child.label} reached out with both hands.")
    prize.meters["returned"] = 1.0
    child.memes["relief"] += 1
    world.para()


def _reconcile(world: World) -> None:
    child: Entity = world.facts["child"]
    ghost: Entity = world.facts["ghost"]
    prize: Entity = world.facts["prize"]
    child.memes["fear"] = 0.0
    ghost.memes["regret"] = 0.0
    ghost.memes["trust"] += 1
    child.memes["trust"] += 1
    world.say(f"{child.label} saw that {ghost.label} had helped, not hunted.")
    world.say(f'“I was scared of you,” {child.label} admitted. “But you saved my {prize.type}.”')
    world.say(f'“I only wanted to be useful,” {ghost.label} whispered. “I am glad we can be friends.”')
    world.say(f"So {child.label} smiled, and the ghost smiled too, and the river sounded gentler than before.")
    world.para()
    world.say(f"In the end, {child.label} went home with {prize.phrase}, and {ghost.label} stayed by the water no longer lonely.")
    world.say(f"The moon lay bright on the river, and even the reeds seemed to nod in peace.")


def generate_world(params: StoryParams) -> World:
    world = World(setting=params.setting, mood=params.mood)
    _setup(world, params)
    _turn(world)
    _assist(world)
    _reconcile(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a child-friendly ghost story about a river, an assist, and reconciliation.",
        f"Tell a spooky-but-kind story where {p.child_name} meets {p.ghost_name} at {SETTINGS[p.setting]} and learns the ghost is helpful.",
        f"Write a short story set by a river where a lost {p.prize} is recovered with a ghost's help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    ghost: Entity = world.facts["ghost"]
    prize: Entity = world.facts["prize"]
    return [
        QAItem(
            question=f"Who met {ghost.label} by the river?",
            answer=f"{child.label} met {ghost.label} by the riverbank in the story.",
        ),
        QAItem(
            question=f"What did the ghost assist with?",
            answer=f"{ghost.label} helped rescue {prize.phrase} from the river water.",
        ),
        QAItem(
            question=f"How did the child feel after the ghost helped?",
            answer=f"{child.label} felt relieved and trusted {ghost.label} after seeing the help.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The child and ghost reconciled, and the lost {prize.type} was safely returned.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a river?",
            answer="A river is a long moving stream of water that flows across the land.",
        ),
        QAItem(
            question="What does assist mean?",
            answer="To assist means to help someone do something or fix a problem.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and become peaceful or friendly again.",
        ),
        QAItem(
            question="Why can a ghost story still be gentle?",
            answer="A ghost story can be gentle when the ghost is shy, kind, or helpful instead of mean.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.haunted:
            parts.append("haunted=True")
        if not e.visible:
            parts.append("visible=False")
        lines.append(f"  {e.id:6} ({e.kind:9}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(riverbank).
setting(old_bridge).
setting(willow_path).

mood(foggy).
mood(twilight).
mood(rainy).

prize(lantern).
prize(boat_key).
prize(scarf).

coherent(S,M,P) :- setting(S), mood(M), prize(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MOODS:
        lines.append(asp.fact("mood", m))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show coherent/3."))
    return sorted(set(asp.atoms(model, "coherent")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


CURATED = [
    StoryParams(setting="riverbank", mood="twilight", prize="lantern", child_name="Mina", child_type="girl", ghost_name="Moth"),
    StoryParams(setting="old_bridge", mood="foggy", prize="boat_key", child_name="Leo", child_type="boy", ghost_name="Hush"),
    StoryParams(setting="willow_path", mood="rainy", prize="scarf", child_name="Nia", child_type="girl", ghost_name="Willow"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show coherent/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show coherent/3."))
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
            header = f"### {p.child_name}: {p.prize} by {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
