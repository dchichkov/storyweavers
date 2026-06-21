#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fond_twist_sharing_animal_story.py
===================================================================

A tiny animal story world about a fond little creature, a twist, and sharing.

Premise:
- A young animal wants to keep one lovely thing all to itself.
- A twist changes what the thing is needed for.
- A shared solution repairs the tension and ends in a warm image.

The world is intentionally small and constraint-checked:
- typed entities with physical meters and emotional memes
- a forward causal model
- a reasonableness gate
- inline ASP twin rules
- grounded QA from simulated state

Run examples:
    python storyworlds/worlds/gpt-5.4-mini/fond_twist_sharing_animal_story.py
    python storyworlds/worlds/gpt-5.4-mini/fond_twist_sharing_animal_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/fond_twist_sharing_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/fond_twist_sharing_animal_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sow"}
        male = {"boy", "father", "dad", "man", "boar"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    nook: str
    backdrop: str
    shared_space: str


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    need: str
    held_by: str = ""
    shareable: bool = True
    attrs: dict = field(default_factory=dict)


@dataclass
class Twist:
    id: str
    trigger: str
    reveal: str
    need_shift: str
    place_shift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingMove:
    id: str
    sense: int
    method: str
    effect: str
    ending: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lonely(world: World) -> list[str]:
    out: list[str] = []
    cub = world.get("cub")
    toy = world.get("toy")
    if toy.meters["wanted"] < THRESHOLD:
        return out
    sig = ("lonely",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cub.memes["fond"] += 1
    out.append("__lonely__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    if snack.meters["needed"] < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("cub").memes["surprise"] += 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [Rule("lonely", "social", _r_lonely), Rule("twist", "social", _r_twist)]


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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for setting in SETTINGS:
        for twist in TWISTS:
            if reasonableness_gate(SETTINGS[setting], TWISTS[twist]):
                out.append((setting, twist))
    return out


def reasonableness_gate(setting: Setting, twist: Twist) -> bool:
    return True if setting.shared_space and twist.trigger else False


def predict(world: World, setting: Setting, treasure: Treasure, twist: Twist) -> dict:
    sim = world.copy()
    sim.get("toy").meters["wanted"] += 1
    sim.get("snack").meters["needed"] += 1
    propagate(sim, narrate=False)
    return {
        "fond": sim.get("cub").memes["fond"] >= THRESHOLD,
        "surprise": sim.get("cub").memes["surprise"] >= THRESHOLD,
    }


def set_scene(world: World, cub: Entity, friend: Entity, setting: Setting) -> None:
    cub.memes["fond"] += 1
    friend.memes["fond"] += 1
    world.say(
        f"In {setting.place}, {cub.id} and {friend.id} made a small nest in {setting.nook}. "
        f"{setting.backdrop}"
    )
    world.say(
        f"{cub.id} was very fond of {world.get('toy').label}, and {friend.id} liked to sit close and watch."
    )


def want_keep(world: World, cub: Entity, toy: Entity) -> None:
    toy.meters["wanted"] += 1
    cub.memes["want"] += 1
    world.say(
        f'{cub.id} hugged the {toy.label} tight. "It is mine," {cub.pronoun()} said, '
        f"and {cub.pronoun('possessive')} tail curled around it."
    )


def twist_reveal(world: World, twist: Twist, snack: Entity, friend: Entity) -> None:
    snack.meters["needed"] += 1
    world.say(
        f"Then came the twist: {twist.reveal} {twist.need_shift}. "
        f"{friend.id} pointed to {snack.label} and said it should go to everyone in the den."
    )


def share(world: World, cub: Entity, friend: Entity, move: SharingMove, snack: Entity, toy: Entity) -> None:
    cub.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    snack.meters["shared"] += 1
    toy.meters["shared"] += 1
    world.say(
        f"{cub.id} looked at {friend.id}, took a breath, and chose {move.method}. "
        f"{move.effect}"
    )


def ending(world: World, cub: Entity, friend: Entity, move: SharingMove, setting: Setting, toy: Entity, snack: Entity) -> None:
    cub.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{move.ending} By the end, {cub.id} and {friend.id} sat together in {setting.shared_space}, "
        f"sharing {toy.label} and {snack.label}, both of them warm and happy."
    )


def tell(setting: Setting, twist: Twist, move: SharingMove, hero: str = "Cub", helper: str = "Pip") -> World:
    world = World()
    cub = world.add(Entity(id=hero, kind="character", type="bear", role="hero"))
    friend = world.add(Entity(id=helper, kind="character", type="rabbit", role="helper"))
    toy = world.add(Entity(id="toy", type="thing", label="berry biscuit", role="treasure"))
    snack = world.add(Entity(id="snack", type="thing", label="extra apple slice", role="snack"))
    world.add(Entity(id="den", type="place", label=setting.place))
    set_scene(world, cub, friend, setting)
    world.para()
    want_keep(world, cub, toy)
    twist_reveal(world, twist, snack, friend)
    world.para()
    share(world, cub, friend, move, snack, toy)
    ending(world, cub, friend, move, setting, toy, snack)
    world.facts.update(setting=setting, twist=twist, move=move, cub=cub, friend=friend, toy=toy, snack=snack)
    return world


SETTINGS = {
    "meadow": Setting(id="meadow", place="the meadow", nook="a round patch of clover", backdrop="The grass was soft, and the bees hummed like tiny bells.", shared_space="a sunny log"),
    "burrow": Setting(id="burrow", place="the burrow", nook="the warm tunnel by the lamp", backdrop="The burrow smelled like hay and honey.", shared_space="the blanket pile"),
    "pond": Setting(id="pond", place="the pond bank", nook="the reeds near the water", backdrop="The water glimmered, and the ducks bobbed like little toys.", shared_space="the big flat stone"),
}

TWISTS = {
    "sharing": Twist(id="sharing", trigger="sharing", reveal="A sudden little rustle showed that", need_shift="the snack had to be split", place_shift="so the friends could both nibble", tags={"sharing", "twist"}),
    "storm": Twist(id="storm", trigger="twist", reveal="A soft wind wandered in, and", need_shift="the snack could not stay alone", place_shift="so everyone had to gather close", tags={"twist"}),
    "visitor": Twist(id="visitor", trigger="sharing", reveal="A tiny visitor arrived, and", need_shift="the snack needed to be shared kindly", place_shift="before the visitor could go on", tags={"sharing", "twist"}),
}

SHARES = {
    "split": SharingMove(id="split", sense=3, method="splitting the berry biscuit in two", effect="One half went to the cub, and one half went to the helper.", ending="They smiled because both of them got a fair piece.", qa_text="split the berry biscuit in two", tags={"sharing"}),
    "pass": SharingMove(id="pass", sense=3, method="passing the apple slice around", effect="First one took a bite, then the other did, and nobody was left out.", ending="The little treats made the den feel larger.", qa_text="passed the apple slice around", tags={"sharing"}),
    "share_basket": SharingMove(id="share_basket", sense=2, method="sharing the whole basket together", effect="They made a tiny picnic right there in the grass.", ending="The basket looked smaller, but the fun felt bigger.", qa_text="shared the whole basket together", tags={"sharing"}),
}

CURATED = [
    StoryParams(setting="meadow", twist="sharing", move="split", seed=1),
    StoryParams(setting="burrow", twist="visitor", move="pass", seed=2),
    StoryParams(setting="pond", twist="storm", move="share_basket", seed=3),
]


@dataclass
class StoryParams:
    setting: str
    twist: str
    move: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An animal story world about fondness, a twist, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--move", choices=SHARES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.twist is None or c[1] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, twist = rng.choice(sorted(combos))
    move = args.move or rng.choice(sorted(SHARES))
    return StoryParams(setting=setting, twist=twist, move=move)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the word "fond" and a twist about {f["twist"].trigger}.',
        f"Tell a short animal story where {f['cub'].id} is fond of {f['toy'].label}, then learns to share after a surprise.",
        f"Write a gentle story about sharing in {f['setting'].place} with animal friends and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cub, friend, toy, snack, twist, move = f["cub"], f["friend"], f["toy"], f["snack"], f["twist"], f["move"]
    return [
        QAItem(
            question=f"What was {cub.id} fond of?",
            answer=f"{cub.id} was fond of the {toy.label}. The story shows {cub.id} holding it close before learning to share."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {twist.reveal.lower()} {twist.need_shift}. That changed the moment from keeping things to sharing them."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {move.ending.lower()} {cub.id} and {friend.id} sat together and shared the food in a happy, cozy place."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does fond mean?", answer="Fond means liking something very much, with a warm and caring feeling."),
        QAItem(question="What is sharing?", answer="Sharing means letting other people have some of what you have, so everyone can enjoy it."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise change that makes the story turn in a new direction."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.twist not in TWISTS or params.move not in SHARES:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], TWISTS[params.twist], SHARES[params.move])
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


ASP_RULES = r"""
valid(S, T, M) :- setting(S), twist(T), move(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for m in SHARES:
        lines.append(asp.fact("move", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((s, t, m) for s, t in valid_combos() for m in SHARES):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, twist=None, move=None), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
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
            sample = generate(p)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
