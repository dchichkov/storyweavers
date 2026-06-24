#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the sandbox"
    affords: set[str] = field(default_factory=lambda: {"build", "dig", "pour"})


@dataclass
class ActorCfg:
    type: str
    name: str
    trait: str


@dataclass
class StoryParams:
    place: str
    activity: str
    mystery: str
    twist: str
    hero: str
    helper: str
    sibling: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


ACTIVITIES = {
    "build": {
        "verb": "build a tall sand tower",
        "gerund": "building a tall sand tower",
        "rush": "dash over to the tower",
        "mess": "crumbled",
    },
    "dig": {
        "verb": "dig a deep tunnel",
        "gerund": "digging a deep tunnel",
        "rush": "scramble down to the tunnel",
        "mess": "collapsed",
    },
    "pour": {
        "verb": "pour water into a moat",
        "gerund": "pouring water into a moat",
        "rush": "run to the water cup",
        "mess": "soggy",
    },
}

MYSTERIES = {
    "missing_tool": {
        "title": "a missing red bucket",
        "problem": "the red bucket was nowhere near the sandbox",
    },
    "mystery_tracks": {
        "title": "curvy tracks in the sand",
        "problem": "a curvy trail kept showing up beside the castle",
    },
    "toppled_tower": {
        "title": "a toppled sand tower",
        "problem": "the tower kept falling before anyone touched it",
    },
}

TWISTS = {
    "caster_wheel": {
        "reveal": "a loose caster wheel from the little cart",
        "why": "it rolled into the sandbox whenever the cart was moved",
    },
    "bucket_shadow": {
        "reveal": "the shadow of the bright bucket lid",
        "why": "the lid had been hiding under the bench the whole time",
    },
    "windy_corner": {
        "reveal": "a windy corner of the sandbox",
        "why": "the breeze kept nudging the soft sand just enough to spill it",
    },
}

PEOPLE = {
    "Mia": ActorCfg(type="girl", name="Mia", trait="careful"),
    "Noah": ActorCfg(type="boy", name="Noah", trait="lively"),
    "Ava": ActorCfg(type="girl", name="Ava", trait="gentle"),
    "Leo": ActorCfg(type="boy", name="Leo", trait="curious"),
    "Nora": ActorCfg(type="girl", name="Nora", trait="patient"),
    "Finn": ActorCfg(type="boy", name="Finn", trait="stubborn"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life sandbox storyworld with a mystery, a twist, and reconciliation.")
    ap.add_argument("--place", choices=["sandbox"], default="sandbox")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero", choices=PEOPLE)
    ap.add_argument("--helper", choices=PEOPLE)
    ap.add_argument("--sibling", choices=PEOPLE)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, m) for p in ["sandbox"] for a in ACTIVITIES for m in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("Unknown twist.")

    hero = args.hero or rng.choice(list(PEOPLE))
    helper = args.helper or rng.choice([n for n in PEOPLE if n != hero])
    sibling = args.sibling or rng.choice([n for n in PEOPLE if n not in {hero, helper}])

    activity = args.activity or rng.choice(list(ACTIVITIES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    twist = args.twist or rng.choice(list(TWISTS))
    return StoryParams(place="sandbox", activity=activity, mystery=mystery, twist=twist, hero=hero, helper=helper, sibling=sibling)


def generate(params: StoryParams) -> StorySample:
    world = World(Setting())
    hero = world.add(Entity(id=params.hero, kind="character", type=PEOPLE[params.hero].type, label=params.hero, memes={"curiosity": 1.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type=PEOPLE[params.helper].type, label=params.helper))
    sibling = world.add(Entity(id=params.sibling, kind="character", type=PEOPLE[params.sibling].type, label=params.sibling))

    act = ACTIVITIES[params.activity]
    mys = MYSTERIES[params.mystery]
    tw = TWISTS[params.twist]

    world.facts.update(hero=hero, helper=helper, sibling=sibling, act=act, mys=mys, tw=tw, params=params)

    world.say(f"On a quiet afternoon in the sandbox, {hero.id} was {PEOPLE[hero.id].trait} and ready for {act['gerund']}.")
    world.say(f"{sibling.id} was there too, and the two of them had been trying to solve {mys['title']} together.")
    world.say(f"The problem was simple: {mys['problem']}.")
    world.para()
    world.say(f"While they worked, {hero.id} noticed something odd near the sand pile.")
    world.say(f"{hero.id} wanted to {act['verb']}, but the odd little mark kept pulling {hero.pronoun('possessive')} eyes away.")
    world.say(f"{helper.id} knelt down and looked closely, because {helper.id} liked solving small puzzles.")
    world.para()
    world.say(f"Then came the twist: it was {tw['reveal']}.")
    world.say(f"That explained why {tw['why']}, and why the sand had been acting so strangely.")
    world.say(f"{hero.id} laughed first, then looked at {sibling.id} and said sorry for blaming {sibling.pronoun('object')} earlier.")
    world.say(f"{sibling.id} smiled back, and soon the three of them were back to {act['gerund']}, now with the mystery solved and everyone working together.")
    world.say(f"By the end, the sandbox looked neat again, and {hero.id}'s little grin said the day had turned out just right.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f'Write a gentle slice-of-life story for a young child set in a sandbox that includes the word "caster".',
        f"Tell a story where {p.hero} and {p.sibling} solve {f['mys']['title']} and then make up after a small misunderstanding.",
        f"Write a short sandbox story with a mystery to solve, a twist, and a happy reconciliation between children.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    act = world.facts["act"]
    mys = world.facts["mys"]
    tw = world.facts["tw"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    sibling = world.facts["sibling"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do in the sandbox?",
            answer=f"{hero.id} was trying to {act['verb']}.",
        ),
        QAItem(
            question=f"What mystery were the children trying to solve?",
            answer=f"They were trying to solve {mys['title']}.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the problem came from {tw['reveal']}.",
        ),
        QAItem(
            question=f"Why did {hero.id} apologize to {sibling.id}?",
            answer=f"{hero.id} apologized because {hero.id} had blamed {sibling.id} before the real answer was found.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}, {helper.id}, and {sibling.id}?",
            answer=f"They solved the mystery, made up, and went back to {act['gerund']} together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sandbox?",
            answer="A sandbox is a small place filled with sand where children can dig, build, and play.",
        ),
        QAItem(
            question="What is a caster wheel?",
            answer="A caster wheel is a small wheel that lets a cart or chair roll smoothly.",
        ),
        QAItem(
            question="Why do children sometimes solve small problems together?",
            answer="They do it so everyone can play happily again after a mix-up or a broken plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,M) :- setting(P), activity(A), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "sandbox")]
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p, a, m) for p, a, m in valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("Mismatch between clingo and python.")
    return 1


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid stories:")
        for t in atoms:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for a in ACTIVITIES:
            for m in MYSTERIES:
                for t in TWISTS:
                    params = StoryParams(place="sandbox", activity=a, mystery=m, twist=t, hero="Mia", helper="Noah", sibling="Ava")
                    samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
