#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ache_sandbox_bad_ending_misunderstanding_superhero_story.py
================================================================================

A standalone storyworld for a tiny superhero tale in a sandbox: a child hero,
a misunderstanding, an ache, and a bad ending that still resolves into a clear
final image. The world is small on purpose: one place, a few meaningful objects,
and a causal chain that drives the prose.

The seed premise:
- In a sandbox, a little superhero-like child wants to keep building.
- A misunderstanding turns the play into conflict.
- An ache appears as the body and feelings react to the tension.
- The ending is bad in the sense that the friendship does not fully recover;
  the final image shows what changed anyway.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sandbox"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    worn_on: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "sandbox": Setting(place="the sandbox", affords={"dig", "build", "race"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig",
        verb="dig a tunnel",
        gerund="digging tunnels",
        rush="scrape through the sand faster",
        mess="sandy",
        soil="all sandy",
        keyword="sand",
        tags={"sand", "sandbox"},
    ),
    "build": Activity(
        id="build",
        verb="build a tall sandcastle",
        gerund="building sandcastles",
        rush="pack the sand harder",
        mess="sandy",
        soil="full of sand",
        keyword="castle",
        tags={"sand", "castle"},
    ),
    "race": Activity(
        id="race",
        verb="race toy cars through the sand",
        gerund="racing toy cars",
        rush="zoom the cars around",
        mess="sandy",
        soil="dusty with sand",
        keyword="cars",
        tags={"sand", "cars"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", worn_on="torso"),
    "mask": Prize(label="mask", phrase="a shiny blue mask", type="mask", worn_on="face"),
    "gloves": Prize(label="gloves", phrase="a pair of hero gloves", type="gloves", worn_on="hands", plural=True),
}

HERO_NAMES = ["Nova", "Pip", "Milo", "Zara", "Theo", "Iris"]
FRIEND_NAMES = ["Bean", "Tala", "Jax", "Luna", "Rex", "Mina"]
TRAITS = ["brave", "bouncy", "curious", "spirited", "playful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    friend_name: str
    hero_trait: str
    seed: Optional[int] = None


class StoryWorld(World):
    pass


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                out.append((place, act, prize))
    return out


def explain_invalid(message: str) -> str:
    return f"(No story: {message})"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny superhero sandbox story with an ache, a misunderstanding, and a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_invalid("no valid combination matches the given options"))
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        hero_name=args.name or rng.choice(HERO_NAMES),
        friend_name=args.friend or rng.choice(FRIEND_NAMES),
        hero_trait=args.trait or rng.choice(TRAITS),
    )


def _do_activity(world: StoryWorld, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, friend_name: str, hero_trait: str) -> StoryWorld:
    world = StoryWorld(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="girl", label=friend_name))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    hero.memes["love"] = 1.0
    hero.memes["pride"] = 1.0
    prize.worn_by = hero.id

    world.say(
        f"{hero.id} was a {hero_trait} little superhero who loved {activity.gerund} in {setting.place}."
    )
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like it was part of the costume."
    )

    world.para()
    world.say(
        f"One warm day, {hero.id} and {friend.id} met in {setting.place}, where the sand waited in little hills."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, and {friend.id} wanted to help."
    )

    world.para()
    world.say(
        f"Then {friend.id} reached for the {prize.label} and said, \"I need the hero thing for the game.\""
    )
    hero.memes["misunderstanding"] = hero.memes.get("misunderstanding", 0.0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1
    hero.meters["ache"] = hero.meters.get("ache", 0.0) + 1
    world.say(
        f"{hero.id} heard that wrong and thought {friend.id} was taking it away for good."
    )
    world.say(
        f"A dull ache pinched {hero.id}'s chest, and the sandy air suddenly felt heavy."
    )

    world.para()
    _do_activity(world, hero, activity)
    world.say(
        f"{hero.id} stomped off and tried to {activity.rush}, but the sand kept slipping under {hero.pronoun('possessive')} boots."
    )
    world.say(
        f"{friend.id} called after {hero.id}, yet the words came too late."
    )
    hero.memes["conflict"] = 1.0
    friend.memes["confused"] = 1.0
    world.say(
        f"In the end, the misunderstanding stayed bigger than the joke, and the sandbox stayed quiet around them."
    )
    world.say(
        f"{hero.id} sat beside a half-built castle with {hero.pronoun('possessive')} {prize.label} dusty and the ache still there."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        setting=setting,
        activity=activity,
        hero_trait=hero_trait,
    )
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short superhero story set in a sandbox where {hero.id} wants to {act.verb} and a misunderstanding causes trouble.',
        f'Tell a child-friendly story about {hero.id}, {friend.id}, and {prize.phrase}, with an ache and a bad ending.',
        f'Write a simple story that uses the word "{act.keyword}" and ends with a sad but clear final image.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    act = f["activity"]
    trait = f["hero_trait"]
    return [
        QAItem(
            question=f"Who was the superhero child in the sandbox?",
            answer=f"The superhero child was {hero.id}, and {hero.id} was {trait}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the sandbox?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the trouble start with {friend.id} and the {prize.label}?",
            answer=f"The trouble started because {friend.id} reached for the {prize.label}, and {hero.id} misunderstood what that meant.",
        ),
        QAItem(
            question=f"What happened to {hero.id} when the misunderstanding grew?",
            answer=f"{hero.id} felt an ache in the chest and ended up sitting beside the sandbox with the {prize.label} dusty.",
        ),
    ]


KNOWLEDGE = {
    "sand": [
        QAItem(
            question="What is sand?",
            answer="Sand is made of tiny bits of rock. It feels grainy and can slip through your fingers.",
        )
    ],
    "castle": [
        QAItem(
            question="What is a sandcastle?",
            answer="A sandcastle is a little castle built from packed sand, often at a beach or in a sandbox.",
        )
    ],
    "cars": [
        QAItem(
            question="Why do toy cars roll easily?",
            answer="Toy cars roll easily because their wheels are hard and round, so they can move over the ground.",
        )
    ],
}


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ("sand", "castle", "cars"):
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P).
valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero_name, params.friend_name, params.hero_trait)
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
    StoryParams(place="sandbox", activity="build", prize="cape", hero_name="Nova", friend_name="Bean", hero_trait="brave"),
    StoryParams(place="sandbox", activity="dig", prize="mask", hero_name="Iris", friend_name="Tala", hero_trait="curious"),
    StoryParams(place="sandbox", activity="race", prize="gloves", hero_name="Pip", friend_name="Jax", hero_trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.hero_name}: {p.activity} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
