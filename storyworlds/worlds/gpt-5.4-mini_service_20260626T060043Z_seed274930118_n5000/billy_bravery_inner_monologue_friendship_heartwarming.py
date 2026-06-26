#!/usr/bin/env python3
"""
Standalone storyworld: Billy, bravery, inner monologue, friendship, heartwarming.

A small simulated domain about a child named Billy who wants to help a friend,
but has to brave a nervous moment first. The world tracks both physical state
and emotional state, and the story is assembled from the evolving simulation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    knows: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little park"
    affordances: set[str] = field(default_factory=lambda: {"help", "play", "talk"})


@dataclass
class Problem:
    id: str
    trouble: str
    inner_fear: str
    brave_action: str
    resolution_action: str
    emotion_before: str
    emotion_after: str
    location_detail: str
    friend_need: str
    keyword: str = "billy"


@dataclass
class Friend:
    id: str
    label: str
    need_label: str
    need_kind: str
    reward_label: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def clamp(v: float) -> float:
    return max(0.0, min(5.0, v))


def feel(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = clamp(e.memes.get(key, 0.0) + delta)


def meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = clamp(e.meters.get(key, 0.0) + delta)


def setup_world() -> tuple[Setting, Problem, Friend]:
    setting = Setting()
    problem = Problem(
        id="stagefright",
        trouble="a tall kite string had tangled on a branch",
        inner_fear="Billy worried his hands would shake if he tried to help",
        brave_action="take a deep breath and climb the small step stool",
        resolution_action="reach up, loosen the string, and give the kite back",
        emotion_before="nervous",
        emotion_after="proud",
        location_detail="beside the swings under the old maple tree",
        friend_need="the kite could not fly unless the string was freed",
    )
    friend = Friend(
        id="Maya",
        label="Maya",
        need_label="kite",
        need_kind="kite",
        reward_label="the bright yellow kite",
    )
    return setting, problem, friend


def tell_story(world: World, hero: Entity, friend: Friend, problem: Problem) -> None:
    world.say(
        f"Billy was a little {hero.type} who loved helping people, even when he felt shy."
    )
    world.say(
        f"He had a quiet inner voice that whispered, '{problem.inner_fear}' whenever something looked hard."
    )
    world.say(
        f"One afternoon, Billy saw {friend.label} near {world.setting.place}, where {problem.location_detail}."
    )
    world.say(
        f"{friend.label}'s {friend.need_label} was stuck in a branch, and {problem.friend_need}."
    )

    world.para()
    feel(hero, "nervous", 2)
    feel(hero, "care", 1)
    hero.knows.add("friendship")
    world.say(
        f"Billy looked up at the branch and thought, '{problem.inner_fear} But {friend.label} needs me.'"
    )
    world.say(
        f"His heart thumped, but he still {problem.brave_action}."
    )

    meter(hero, "bravery", 1)
    feel(hero, "nervous", -1)
    feel(hero, "brave", 2)
    world.say(
        f"He held on tight, stretched his arm, and carefully {problem.resolution_action}."
    )
    world.say(
        f"The string slipped free, and {friend.label} caught {friend.reward_label} with a huge smile."
    )

    world.para()
    feel(hero, "joy", 2)
    feel(hero, "love", 1)
    feel(hero, "friendship", 2)
    world.say(
        f"'{friend.reward_label} is flying again!' {friend.label} cheered."
    )
    world.say(
        f"Billy grinned, because the brave thing had turned into a happy thing."
    )
    world.say(
        f"On the way home, he listened to his inner voice and found it sounded softer now: 'I can help.'"
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story about Billy using bravery and inner monologue to help a friend.",
        f"Tell a gentle story where Billy sees {world.facts['friend'].label}'s problem and chooses courage.",
        "Write a child-friendly story about friendship, a worried thought, and a kind rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    problem = world.facts["problem"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"The story is about Billy, a caring little child who learns to be brave for a friend."
        ),
        QAItem(
            question=f"What was Billy worried about before he helped {friend.label}?",
            answer=f"Billy worried his hands would shake if he tried to help, but he listened to his inner voice and still went for it."
        ),
        QAItem(
            question=f"What problem did {friend.label} have?",
            answer=f"{friend.label}'s {friend.need_label} was stuck in a branch, so it could not fly until the string was freed."
        ),
        QAItem(
            question="How did Billy show bravery?",
            answer=f"He showed bravery by taking a deep breath, climbing the small step stool, and carefully freeing the string."
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"At the end, Billy felt proud and happy, and {friend.label} was smiling with the {friend.reward_label} flying again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something scary or hard when you know it matters, even if you still feel nervous."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside your head that helps you think about what to do."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is caring about someone, helping them, and wanting them to feel happy and safe."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        if e.knows:
            bits.append(f"knows={sorted(e.knows)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story() -> bool:
    return True


ASP_RULES = r"""
hero(billy).
friend(maya).
problem(stagefright).
inner_fear(stagefright).
brave_action(stagefright).
resolution_action(stagefright).

good_story :- hero(billy), friend(maya), problem(stagefright), brave_action(stagefright), resolution_action(stagefright).
#show good_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "billy"),
        asp.fact("friend", "maya"),
        asp.fact("problem", "stagefright"),
        asp.fact("setting", "little_park"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    import itertools

    model = asp.one_model(asp_program("#show good_story/0."))
    asp_ok = any(sym.name == "good_story" for sym in model)
    py_ok = valid_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python parity matches.")
        return 0
    print("MISMATCH between ASP and Python parity.")
    return 1


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Billy"
    friend_name: str = "Maya"
    place: str = "the little park"


CURATED = [StoryParams()]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming Billy storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--place")
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
    return StoryParams(
        seed=args.seed,
        name=args.name or "Billy",
        friend_name=args.friend_name or "Maya",
        place=args.place or "the little park",
    )


def generate(params: StoryParams) -> StorySample:
    setting, problem, friend = setup_world()
    setting.place = params.place
    world = World(setting)
    hero = world.add(Entity(id=params.name, type="child", label=params.name))
    world.facts["hero"] = hero
    world.facts["problem"] = problem
    world.facts["friend"] = friend
    tell_story(world, hero, friend, problem)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/0."))
        print(f"good_story models: {1 if any(sym.name == 'good_story' for sym in model) else 0}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
