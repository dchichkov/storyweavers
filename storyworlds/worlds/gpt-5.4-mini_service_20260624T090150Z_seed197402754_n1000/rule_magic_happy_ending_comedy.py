#!/usr/bin/env python3
"""
A small comedy storyworld about a magic rule that causes a silly problem and a
happy ending.

Seed premise:
- A child wants to use magic.
- A grown-up worries about a rule.
- A tiny mistake leads to a funny mess.
- They follow the rule in a smarter way and end happy.

The simulated model tracks:
- physical meters: sparkles, mess, tidy, noise
- emotional memes: delight, worry, embarrassment, relief, pride
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the kitchen"
    afford_magic: bool = True
    afford_baking: bool = True


@dataclass
class MagicAction:
    id: str
    verb: str
    gerund: str
    mess: str
    delight: str
    sparkly: bool = True


@dataclass
class Rule:
    id: str
    text: str
    check: str


@dataclass
class StoryParams:
    setting: str
    action: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting("the kitchen"),
    "stage": Setting("the little stage"),
    "garden": Setting("the garden"),
}

ACTIONS = {
    "cookies": MagicAction(
        id="cookies",
        verb="make cookies dance",
        gerund="making cookies dance",
        mess="flour",
        delight="the cookies spun like tiny ballerinas",
    ),
    "bubbles": MagicAction(
        id="bubbles",
        verb="fill the room with bubbles",
        gerund="blowing bubble spells",
        mess="foam",
        delight="the bubbles popped like cheerful rain",
    ),
    "confetti": MagicAction(
        id="confetti",
        verb="make confetti rain from the ceiling",
        gerund="casting confetti spells",
        mess="paper bits",
        delight="the colors fluttered like happy birds",
    ),
}

HELPERS = {
    "cat": "the cat",
    "hat": "the hat",
    "spoon": "the spoon",
}

RULES = [
    Rule(
        id="rule",
        text="Magic may be used only if the room is tidy and the helper is not on the floor.",
        check="tidy_and_safe",
    )
]

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Finn", "Theo", "Sam"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when magic is allowed in the setting and the chosen
% action has a tidy ending path.
allowed(S) :- setting(S), magic_ok(S).
valid_story(S, A, H) :- setting(S), action(A), helper(H), allowed(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_magic:
            lines.append(asp.fact("magic_ok", sid))
        if s.afford_baking:
            lines.append(asp.fact("baking_ok", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set((s, a, h) for s in SETTINGS for a in ACTIONS for h in HELPERS if SETTINGS[s].afford_magic)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(setting: Setting, action: MagicAction) -> bool:
    return setting.afford_magic and bool(action.verb)


def predict_mess(world: World, child: Entity, action: MagicAction) -> dict[str, object]:
    sim = world.copy()
    child2 = sim.get(child.id)
    child2.meters["sparkles"] = child2.meters.get("sparkles", 0) + 1
    if action.mess:
        child2.meters[action.mess] = child2.meters.get(action.mess, 0) + 1
    return {
        "messy": child2.meters.get(action.mess, 0) > 0,
        "sparkles": child2.meters.get("sparkles", 0),
    }


def tell(setting: Setting, action: MagicAction, name: str, gender: str, helper_id: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    grownup = world.add(Entity(id="grownup", kind="character", type="mother", label="Mom"))
    helper = world.add(Entity(id=helper_id, kind="thing", type=helper_id, label=HELPERS[helper_id]))
    helper.owner = child.id

    child.memes["delight"] = 1
    world.say(f"{name} was a little {gender} who loved magic tricks and funny surprises.")
    world.say(f"{child.pronoun('subject').capitalize()} wanted to {action.verb}, because {action.delight}.")
    world.say(f"But Mom had one rule: “{RULES[0].text}”")

    world.para()
    world.say(f"One day, {name} and {helper.ref()} went to {setting.place}.")
    child.memes["worry"] = 0
    world.say(f"{name} whispered the spell, and suddenly {action.gerund} got a lot messier than expected.")
    child.meters["sparkles"] = 1
    child.meters[action.mess] = 1
    child.memes["embarrassment"] = 1
    world.say(f"There were {action.mess} everywhere, and {name} made a very round silly face.")

    world.para()
    world.say(f"Mom looked at the mess, then at the rule, and nodded instead of frowning.")
    world.say(f"“Let's use the rule in a clever way,” she said. “First we tidy up, then we try again.”")
    child.meters[action.mess] = 0
    child.meters["tidy"] = 1
    child.memes["relief"] = 1
    child.memes["pride"] = 1
    world.say(f"{name} helped wipe the floor, and {helper.ref()} balanced on the table like a tiny statue.")
    world.say(f"After that, the spell worked beautifully, and {action.delight}.")

    world.para()
    world.say(f"In the end, {name} was laughing, Mom was laughing, and the room was tidy again.")
    world.say(f"The rule had not ruined the fun; it had saved the fun.")
    world.facts.update(
        child=child,
        grownup=grownup,
        helper=helper,
        action=action,
        setting=setting,
        rule=RULES[0],
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    action: MagicAction = f["action"]
    helper: Entity = f["helper"]
    return [
        f'Write a short comedy story for a child named {child.id} who wants to {action.verb} but must follow a magic rule.',
        f"Tell a funny story where {child.id} and {helper.ref()} make a messy spell, then fix it and end happily.",
        f'Write a gentle magic story that includes the word "rule" and ends with everyone laughing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    grownup: Entity = f["grownup"]
    helper: Entity = f["helper"]
    action: MagicAction = f["action"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at the beginning of the story?",
            answer=f"{child.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"What rule did Mom say they had to follow?",
            answer=f"Mom said magic could be used only if the room was tidy and the helper was not on the floor.",
        ),
        QAItem(
            question=f"How did the story end after the mess was cleaned up?",
            answer=f"It ended happily, with {child.id}, Mom, and {helper.ref()} all laughing in a tidy room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rule?",
            answer="A rule is a direction that tells people what is allowed or what they should do.",
        ),
        QAItem(
            question="Why do people tidy up after making a mess?",
            answer="People tidy up so the floor and table are safe, clean, and nice to use again.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something surprising that makes impossible things happen.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    out.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Magic comedy storyworld with a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    if not reasonableness_gate(SETTINGS[setting], ACTIONS[action]):
        raise StoryError("This magic action is not reasonable in the chosen setting.")
    return StoryParams(setting=setting, action=action, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], params.name, params.gender, params.helper)
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
    StoryParams(setting="kitchen", action="cookies", name="Mia", gender="girl", helper="cat"),
    StoryParams(setting="stage", action="bubbles", name="Leo", gender="boy", helper="hat"),
    StoryParams(setting="garden", action="confetti", name="Nora", gender="girl", helper="spoon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid_stories()
        print(f"{len(model)} compatible stories:")
        for s, a, h in model:
            print(f"  {s:8} {a:10} {h}")
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
            header = f"### {p.name}: {p.action} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
