#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a missing macaroon, quiet inner thoughts,
teamwork, and a little act of bravery.

The world is designed as a classical simulation:
- physical meters: e.g. carried, hidden, warm, sleepy
- emotional memes: e.g. worry, courage, teamwork, relief
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


@dataclass
class Person:
    name: str
    role: str  # child, sibling, parent, grandparent
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def say_name(self) -> str:
        return self.name


@dataclass
class ObjectThing:
    name: str
    label: str
    owner: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    parent_name: str
    setting: str
    treat: str
    seed: Optional[int] = None


@dataclass
class StoryWorld:
    child: Person
    helper: Person
    parent: Person
    treat: ObjectThing
    setting: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def snapshot(self) -> str:
        lines = ["--- world model state ---"]
        for person in [self.child, self.helper, self.parent]:
            meters = {k: v for k, v in person.meters.items() if v}
            memes = {k: v for k, v in person.memes.items() if v}
            lines.append(f"  {person.name:10} ({person.role:9}) meters={meters} memes={memes}")
        lines.append(f"  treat      ({self.treat.label}) meters={ {k:v for k,v in self.treat.meters.items() if v} }")
        return "\n".join(lines)


NAMES = ["Mina", "Luna", "Nora", "Toby", "Milo", "Iris", "Benny", "Sage", "Ada", "Pip"]
SETTINGS = {
    "bedtime": "the cozy bedroom at bedtime",
    "storybook_corner": "the soft storybook corner",
    "nursery": "the sleepy nursery",
}
TREATES = {
    "macaroon": "one small almond macaroon",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about macaroon, teamwork, bravery, and inner monologue.")
    ap.add_argument("--child-name", choices=NAMES)
    ap.add_argument("--helper-name", choices=NAMES)
    ap.add_argument("--parent-name", choices=NAMES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATEDS if False else list(TREATES), help=argparse.SUPPRESS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    treat = args.treat or "macaroon"
    child = args.child_name or rng.choice(NAMES)
    helper = args.helper_name or rng.choice([n for n in NAMES if n != child])
    parent = args.parent_name or rng.choice([n for n in NAMES if n not in {child, helper}])
    return StoryParams(
        child_name=child,
        helper_name=helper,
        parent_name=parent,
        setting=setting,
        treat=treat,
    )


def _make_world(params: StoryParams) -> StoryWorld:
    child = Person(params.child_name, "child", "she", "her", "her")
    helper = Person(params.helper_name, "sibling", "he", "him", "his")
    parent = Person(params.parent_name, "parent", "she", "her", "her")
    treat = ObjectThing(params.treat, params.treat, owner=parent.name)
    return StoryWorld(child=child, helper=helper, parent=parent, treat=treat, setting=SETTINGS[params.setting])


def _init_state(world: StoryWorld) -> None:
    world.child.meters.update({"sleepy": 1.0, "near_bed": 1.0})
    world.child.memes.update({"worry": 0.0, "courage": 0.0, "lonely": 0.0, "relief": 0.0, "teamwork": 0.0})
    world.helper.meters.update({"awake": 1.0, "near_bed": 1.0})
    world.helper.memes.update({"kindness": 1.0, "teamwork": 0.0, "courage": 0.0})
    world.parent.meters.update({"near_bed": 1.0, "holding_plate": 1.0})
    world.parent.memes.update({"care": 1.0, "patience": 1.0})
    world.treat.meters.update({"hidden": 1.0, "warm": 0.0, "shared": 0.0})


def _narrate_setup(world: StoryWorld) -> None:
    c, h, p, t = world.child, world.helper, world.parent, world.treat
    world.say(f"It was bedtime in {world.setting}, and {c.name} was getting sleepy.")
    world.say(f"{p.name} had saved a little {t.label} for after the stories, tucked safely under a plate.")
    world.say(f"{c.name} noticed it and felt a tiny flutter in {c.pronoun_possessive} tummy.")


def _inner_monologue(world: StoryWorld) -> None:
    c = world.child
    c.memes["worry"] += 1
    c.memes["lonely"] += 1
    world.say(f'Inside {c.name}\'s quiet thoughts, a voice whispered, "I want the {world.treat.label}, but I do not want to be rude."')
    world.say(f'{c.name} breathed slowly and thought, "Maybe I can ask kindly. Maybe I can be brave."')


def _teamwork_offer(world: StoryWorld) -> None:
    c, h, p = world.child, world.helper, world.parent
    c.memes["teamwork"] += 1
    h.memes["teamwork"] += 1
    world.say(f"{h.name} saw the little pause and walked over with a gentle smile.")
    world.say(f'"We can do this together," {h.name} whispered. "{h.name} can ask, and I can help carry the plate."')
    world.say(f"{p.name} nodded, because bedtime was smoother when everyone helped.")


def _brave_request(world: StoryWorld) -> None:
    c, p = world.child, world.parent
    c.memes["courage"] += 1
    world.say(f"{c.name} stood up a little straighter, even though {c.pronoun_subject} was still sleepy.")
    world.say(f'With a brave little voice, {c.name} asked, "{p.name}, may I please have a macaroon after I help set the book aside?"')
    world.say(f"{p.name} smiled at the honest question. That was the kind of bravery that fit right into a bedtime song.")


def _shared_treat(world: StoryWorld) -> None:
    c, h, p, t = world.child, world.helper, world.parent, world.treat
    t.meters["hidden"] = 0.0
    t.meters["shared"] = 1.0
    t.meters["warm"] = 1.0
    c.memes["worry"] = 0.0
    c.memes["relief"] += 1
    c.memes["teamwork"] += 1
    world.say(f"{p.name} lifted the plate and broke the little {t.label} into three neat pieces.")
    world.say(f"{c.name}, {h.name}, and {p.name} shared the sweet crumbs together, like a tiny moon divided among friends.")
    world.say(f"Then they snuggled back into the pillows, and the room felt soft and safe again.")


def tell_story(world: StoryWorld) -> None:
    _init_state(world)
    _narrate_setup(world)
    world.para()
    _inner_monologue(world)
    _teamwork_offer(world)
    world.para()
    _brave_request(world)
    _shared_treat(world)
    world.facts = {
        "child": world.child.name,
        "helper": world.helper.name,
        "parent": world.parent.name,
        "setting": world.setting,
        "treat": world.treat.label,
    }


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story about {f["child"]}, {f["helper"]}, and a hidden {f["treat"]}.',
        f"Tell a calm story where {f['child']} has an inner monologue, {f['helper']} helps, and {f['parent']} rewards brave asking.",
        f"Write a small bedtime tale in {f['setting']} about teamwork, bravery, and sharing a {f['treat']}.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    c, h, p, t = world.child, world.helper, world.parent, world.treat
    return [
        QAItem(
            question=f"Who asked for the macaroon in the story?",
            answer=f"{c.name} asked politely after thinking hard about what was kind and brave.",
        ),
        QAItem(
            question=f"How did {h.name} help in the story?",
            answer=f"{h.name} helped by staying close, speaking gently, and making the moment feel like teamwork.",
        ),
        QAItem(
            question=f"What happened to the macaroon at the end?",
            answer=f"The {t.label} was shared into three pieces, so everyone could enjoy it together.",
        ),
        QAItem(
            question=f"Why did {c.name} feel brave?",
            answer=f"{c.name} felt brave because {c.pronoun_subject} asked honestly even though it was bedtime and {c.pronoun_subject} felt sleepy.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a macaroon?",
            answer="A macaroon is a small sweet cookie, often made with coconut or almond and baked until it is lightly crisp.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do something together instead of trying to do it alone.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something that feels a little scary or hard, even while your heart is fluttering.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking voice inside your head that helps you sort out your feelings and choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


ASP_RULES = r"""
child(C) :- child_name(C).
helper(H) :- helper_name(H).
parent(P) :- parent_name(P).
treat(T) :- treat_name(T).

inner_monologue(C) :- child(C).
teamwork(C,H) :- child(C), helper(H), C != H.
brave_request(C) :- child(C).
shared_treat(T) :- treat(T).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("child_name", name) for name in NAMES
    ] + [
        asp.fact("helper_name", name) for name in NAMES
    ] + [
        asp.fact("parent_name", name) for name in NAMES
    ] + [
        asp.fact("treat_name", "macaroon")
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show teamwork/2. #show inner_monologue/1. #show brave_request/1. #show shared_treat/1."))
    atoms = set((a.name, tuple((x.name if hasattr(x, 'name') else x) for x in a.arguments)) for a in model)
    ok = ("shared_treat", ("macaroon",)) in atoms
    if ok:
        print("OK: ASP twin emits the bedtime-story predicates.")
        return 0
    print("MISMATCH: ASP twin did not emit expected predicates.")
    return 1


def dump_trace(world: StoryWorld) -> str:
    return world.snapshot()


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    tell_story(world)
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
    StoryParams(child_name="Mina", helper_name="Luna", parent_name="Nora", setting="bedtime", treat="macaroon"),
    StoryParams(child_name="Toby", helper_name="Milo", parent_name="Iris", setting="storybook_corner", treat="macaroon"),
    StoryParams(child_name="Ada", helper_name="Pip", parent_name="Sage", setting="nursery", treat="macaroon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shared_treat/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.setting} with a {p.treat}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
