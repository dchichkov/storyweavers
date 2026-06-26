#!/usr/bin/env python3
"""
storyworlds/worlds/barberry_magic_adventure.py
==============================================

A tiny Adventure-style story world about barberry, magic, and a small quest.

Premise:
- A young adventurer wants to reach a barberry patch.
- The patch is protected by a simple magical obstacle.
- A helpful magical object or spell provides the safe way through.
- The story ends with a concrete changed state: the berries are gathered, the
  obstacle is handled, and the hero is happier and braver.

This file is self-contained and follows the Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"tired": 0.0, "glow": 0.0, "safe": 0.0, "collected": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "joy": 0.0, "wonder": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the barberry grove"
    overgrown: bool = True
    affords: set[str] = field(default_factory=lambda: {"seek_barberry", "cast_magic"})


@dataclass
class Challenge:
    id: str
    name: str
    threat: str
    block: str
    requires_magic: bool = False


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    plural: bool = False


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    helps_against: set[str]
    covers: set[str] = field(default_factory=set)


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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "grove": Setting(place="the barberry grove", overgrown=True, affords={"seek_barberry", "cast_magic"}),
    "trail": Setting(place="the forest trail", overgrown=False, affords={"seek_barberry", "cast_magic"}),
    "cottage": Setting(place="the cottage garden", overgrown=True, affords={"seek_barberry", "cast_magic"}),
}

CHALLENGES = {
    "thorns": Challenge(
        id="thorns",
        name="thorny barberry branches",
        threat="scratched hands",
        block="the thorns made the berries hard to reach",
        requires_magic=True,
    ),
    "bramble": Challenge(
        id="bramble",
        name="a thick bramble fence",
        threat="a long detour",
        block="the bramble blocked the path to the bush",
        requires_magic=True,
    ),
    "shadow": Challenge(
        id="shadow",
        name="a sleepy patch of shadow",
        threat="a wrong turn",
        block="the shadows made the berries hard to find",
        requires_magic=True,
    ),
}

REWARDS = {
    "berries": Reward(
        id="berries",
        label="barberries",
        phrase="bright red barberries",
        plural=True,
    ),
    "jam": Reward(
        id="jam",
        label="barberry jam ingredients",
        phrase="sweet berries for jam",
        plural=True,
    ),
}

MAGIC_TOOLS = {
    "lantern": MagicTool(
        id="lantern",
        label="a magic lantern",
        phrase="a small magic lantern that shone like a star",
        helps_against={"shadow"},
    ),
    "gloves": MagicTool(
        id="gloves",
        label="glimmer gloves",
        phrase="soft glimmer gloves",
        helps_against={"thorns"},
        covers={"hands"},
    ),
    "ribbon": MagicTool(
        id="ribbon",
        label="a charm ribbon",
        phrase="a charm ribbon that pointed the way",
        helps_against={"bramble", "shadow"},
    ),
}

HERO_NAMES = ["Nina", "Toby", "Mina", "Ravi", "Lena", "Soren", "Pia", "Eli"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["brave", "curious", "gentle", "lively", "bold", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
challenge_blocks(C) :- challenge(C), requires_magic(C).
has_magic_fix(C) :- tool(T), helps(T, C).
valid_story(P, C, R) :- place(P), challenge(C), reward(R), affords(P, seek_barberry), challenge_blocks(C), has_magic_fix(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.overgrown:
            lines.append(asp.fact("overgrown", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        if c.requires_magic:
            lines.append(asp.fact("requires_magic", cid))
    for rid, r in REWARDS.items():
        lines.append(asp.fact("reward", rid))
        if r.plural:
            lines.append(asp.fact("reward_plural", rid))
    for tid, t in MAGIC_TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.helps_against):
            lines.append(asp.fact("helps", tid, c))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    got = set(asp.atoms(model, "valid_story"))
    if got == expected:
        print(f"OK: clingo gate matches valid_combos() ({len(got)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(got - expected))
    print("only in python:", sorted(expected - got))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def challenge_needs_magic(challenge: Challenge) -> bool:
    return challenge.requires_magic


def has_magic_solution(challenge: Challenge) -> bool:
    return any(challenge.id in tool.helps_against for tool in MAGIC_TOOLS.values())


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for challenge in CHALLENGES:
            for reward in REWARDS:
                if challenge_needs_magic(CHALLENGES[challenge]) and has_magic_solution(CHALLENGES[challenge]):
                    combos.append((place, challenge, reward))
    return combos


def explain_rejection(challenge: Challenge, reward: Reward) -> str:
    return (
        f"(No story: {challenge.name} needs a real magic fix, but this world has no "
        f"compatible way to solve it for {reward.label}.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _apply_magic(world: World, hero: Entity, challenge: Challenge, tool: MagicTool) -> list[str]:
    out: list[str] = []
    sig = ("magic", hero.id, challenge.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] += 1
    hero.meters["safe"] += 1
    if challenge.id in tool.helps_against:
        hero.meters["glow"] += 1
        hero.memes["wonder"] += 1
        out.append(
            f"{hero.id} lifted {tool.label} and the air shimmered with kind, steady magic."
        )
        out.append(f"The magic helped with {challenge.name}, and the path opened at last.")
    return out


def _collect_reward(world: World, hero: Entity, reward: Entity) -> list[str]:
    sig = ("collect", hero.id, reward.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    reward.meters["collected"] += 1
    hero.memes["joy"] += 1
    hero.meters["safe"] += 1
    return [f"{hero.id} gathered {reward.phrase} and tucked them carefully away."]


def tell(setting: Setting, challenge: Challenge, reward_cfg: Reward,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    reward = world.add(Entity(
        id=reward_cfg.id,
        type=reward_cfg.id,
        label=reward_cfg.label,
        phrase=reward_cfg.phrase,
        owner=hero.id,
        plural=reward_cfg.plural,
    ))

    tool = next(iter(MAGIC_TOOLS.values()))
    for t in MAGIC_TOOLS.values():
        if challenge.id in t.helps_against:
            tool = t
            break

    world.say(
        f"{hero.id} was a {trait} little {hero.type} who loved adventures near {setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had heard that the barberry bush held {reward.label}, "
        f"and {hero.pronoun('possessive')} heart beat fast at the thought of the red treasure."
    )

    world.para()
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label or parent.type} went to {setting.place}."
    )
    world.say(
        f"But {challenge.block}, so {hero.id} could not simply reach the berries."
    )
    world.say(
        f"{hero.id} wanted to keep going anyway, because the adventure felt too exciting to stop."
    )

    world.para()
    world.say(
        f"{parent.label or 'the parent'} smiled and handed over {tool.phrase}."
    )
    for line in _apply_magic(world, hero, challenge, tool):
        world.say(line)
    for line in _collect_reward(world, hero, reward):
        world.say(line)
    world.say(
        f"In the end, {hero.id} walked home with {reward.label}, a brighter smile, and a little more courage."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        reward=reward,
        challenge=challenge,
        setting=setting,
        tool=tool,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child about "{f["hero"].id}" and barberry magic.',
        f"Tell a gentle quest where {f['hero'].id} wants to gather {f['reward'].label} but needs a magical helper.",
        f"Write a child-friendly story set at {f['setting'].place} with a barberry bush and a magical turn.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    reward: Entity = f["reward"]
    challenge: Challenge = f["challenge"]
    tool: MagicTool = f["tool"]
    trait: str = f["trait"]
    place = f["setting"].place

    return [
        QAItem(
            question=f"Who went on the adventure to {place}?",
            answer=f"{hero.id} went with {parent.label or 'the parent'} on a small adventure to {place}.",
        ),
        QAItem(
            question=f"What stopped {hero.id} from reaching the barberry bush right away?",
            answer=f"{challenge.block.capitalize()}, so {hero.id} needed help before reaching the berries.",
        ),
        QAItem(
            question=f"What magical thing helped {hero.id} solve the problem?",
            answer=f"{tool.phrase} helped {hero.id} get past the trouble.",
        ),
        QAItem(
            question=f"What did {trait} {hero.id} bring home at the end?",
            answer=f"{hero.id} brought home {reward.phrase} after the magical adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is barberry?",
            answer="Barberry is a shrub with small leaves and bright red berries. People can use its berries for cooking or pick them from the bush.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic in a story is a special power that can make surprising things happen, like glowing light, helpful charms, or spells that open a path.",
        ),
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or task where someone faces a problem, tries something brave, and learns or wins something in the end.",
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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    reward: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Barberry magic adventure story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.challenge and args.reward:
        ch = CHALLENGES[args.challenge]
        if not (challenge_needs_magic(ch) and has_magic_solution(ch)):
            raise StoryError(explain_rejection(ch, REWARDS[args.reward]))
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.reward is None or c[2] == args.reward)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, reward = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, reward=reward, name=name,
                       gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CHALLENGES[params.challenge],
        REWARDS[params.reward],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_wrapper() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify_wrapper())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, challenge, reward) combos:\n")
        for place, challenge, reward in triples:
            print(f"  {place:12} {challenge:10} {reward:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("grove", "thorns", "berries", "Nina", "girl", "mother", "curious"),
            StoryParams("trail", "shadow", "jam", "Ravi", "boy", "father", "brave"),
            StoryParams("cottage", "bramble", "berries", "Mina", "girl", "mother", "gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
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
            print(json.dumps([dataclasses.asdict(s.params) | {"story": s.story,
                                                             "prompts": s.prompts,
                                                             "story_qa": [dataclasses.asdict(q) for q in s.story_qa],
                                                             "world_qa": [dataclasses.asdict(q) for q in s.world_qa]}
                              for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
