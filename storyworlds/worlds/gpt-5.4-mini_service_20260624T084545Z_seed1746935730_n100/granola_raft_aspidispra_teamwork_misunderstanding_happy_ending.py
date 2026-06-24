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

SETTINGS = {
    "pond": "the pond",
    "creek": "the creek",
    "lake": "the little lake",
}

CHILD_NAMES = ["Mina", "Owen", "Lina", "Toby", "Nia", "Eli"]
HELPER_NAMES = ["Pip", "Rae", "Juno", "Sage", "Bea", "Nell"]


@dataclass
class StoryParams:
    setting: str
    child: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    child: Entity
    helper: Entity
    aspidispra: Entity
    raft: Entity
    granola: Entity
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming teamwork storyworld about a granola raft and an aspidispra.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
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


def _reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("The setting must be a real watery place the raft can float in.")
    if params.child and params.helper and params.child == params.helper:
        raise StoryError("The child and helper must be different characters for the teamwork story.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    params = StoryParams(setting=setting, child=child, helper=helper)
    _reasonableness_gate(params)
    return params


def _make_world(params: StoryParams) -> World:
    child = Entity("child", "character", params.child, "child")
    helper = Entity("helper", "character", params.helper, "helper")
    aspidispra = Entity("aspidispra", "character", "an aspidispra", "creature")
    raft = Entity("raft", "thing", "a small raft", "raft", meters={"float": 1.0}, memes={"safe": 0.0})
    granola = Entity("granola", "thing", "a bowl of granola", "food", meters={"crunch": 1.0})
    return World(settings:=params.setting, child=child, helper=helper, aspidispra=aspidispra, raft=raft, granola=granola)


def generate_story(world: World) -> None:
    c, h, a, r, g = world.child, world.helper, world.aspidispra, world.raft, world.granola
    place = SETTINGS[world.setting]

    c.memes["curious"] = 1
    h.memes["kind"] = 1
    a.memes["shy"] = 1

    world.say(f"On a warm day at {place}, {c.label} and {h.label} found a little raft by the water.")
    world.say(f"Beside it sat {g.label}, because {c.label} had brought a snack for the outing.")
    world.say(f"A tiny {a.type} peeked out and looked at the raft with wide, worried eyes.")

    world.para()
    c.memes["misunderstanding"] = 1
    world.say(f"{c.label} thought the {a.type} wanted to steal the raft, so {c.label} held it close.")
    world.say(f"But the {a.type} was really trying to help push the raft away from a snag of reeds.")
    h.memes["understanding"] = 0.5
    world.say(f"{h.label} noticed the reeds and said, 'Let's all work together and see what is happening.'")

    world.para()
    c.memes["teamwork"] = 1
    h.memes["teamwork"] = 1
    a.memes["teamwork"] = 1
    r.meters["waterline"] = 1.0
    world.say(f"{c.label} moved to one side, {h.label} to the other, and the {a.type} nudged from the back.")
    world.say(f"Together they freed the raft, and the little boat floated straight and happy on the water.")
    g.meters["eaten"] = 1.0
    world.say(f"Afterward they shared the granola, and the crunchy snack tasted even sweeter because everyone had helped.")

    world.para()
    c.memes["joy"] = 1.0
    h.memes["joy"] = 1.0
    a.memes["joy"] = 1.0
    r.memes["safe"] = 1.0
    world.say(f"The {a.type} smiled, because it had never meant any harm.")
    world.say(f"{c.label} smiled back, now understanding the mistake.")
    world.say(f"By the end, the raft was safe, the misunderstanding was gone, and all three friends waved at the shining water together.")

    world.facts.update(setting=world.setting, child=c, helper=h, aspidispra=a, raft=r, granola=g)


def story_text(world: World) -> str:
    return world.render()


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, h, a = f["child"], f["helper"], f["aspidispra"]
    place = SETTINGS[f["setting"]]
    return [
        QAItem(
            question=f"Who helped {c.label} at {place}?",
            answer=f"{h.label} helped {c.label}, and the tiny {a.type} helped too."
        ),
        QAItem(
            question=f"What did {c.label} think at first?",
            answer=f"At first {c.label} thought the {a.type} wanted to steal the raft."
        ),
        QAItem(
            question="What fixed the misunderstanding?",
            answer="They talked kindly and worked together to free the raft from the reeds."
        ),
        QAItem(
            question="What snack was part of the story?",
            answer="A bowl of granola was part of the outing, and they shared it after the raft was freed."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other to do something together."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks the wrong thing because they do not know the full story."
        ),
        QAItem(
            question="What is a raft?",
            answer="A raft is a flat floating thing that can carry people on water."
        ),
    ]


ASP_RULES = r"""
setting(pond).
setting(creek).
setting(lake).

can_float(raft).
has_snack(granola).
is_creature(aspidispra).

teamwork(X) :- child(X), helper(X).
happy_ending :- raft_safe, misunderstanding_resolved.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    lines.append(asp.fact("can_float", "raft"))
    lines.append(asp.fact("has_snack", "granola"))
    lines.append(asp.fact("is_creature", "aspidispra"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_helpers():
    import asp
    return asp


def asp_verify() -> int:
    asp = _asp_helpers()
    model = asp.one_model(asp_program("#show setting/1."))
    found = set(asp.atoms(model, "setting"))
    expected = {(s,) for s in SETTINGS}
    if found == expected:
        print(f"OK: ASP parity verified for {len(expected)} settings.")
        return 0
    print("MISMATCH between ASP and Python registry facts.")
    print("only in ASP:", sorted(found - expected))
    print("only in Python:", sorted(expected - found))
    return 1


def asp_list() -> None:
    asp = _asp_helpers()
    model = asp.one_model(asp_program("#show setting/1. #show can_float/1. #show has_snack/1. #show is_creature/1."))
    for atom in model:
        print(atom)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about {f["child"].label}, {f["helper"].label}, a raft, and an aspidispra.',
        f'Tell a gentle tale where a misunderstanding about a raft is solved by teamwork and a shared granola snack.',
        f'Write a child-friendly story that ends happily with the word "granola" in it.',
    ]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    generate_story(world)
    sample = StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )
    return sample


def dump_trace(world: World) -> str:
    bits = ["--- world model state ---"]
    for e in [world.child, world.helper, world.aspidispra, world.raft, world.granola]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits.append(f"{e.id:11} kind={e.kind:9} label={e.label:18} meters={meters} memes={memes}")
    return "\n".join(bits)


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
    StoryParams(setting="pond", child="Mina", helper="Pip"),
    StoryParams(setting="creek", child="Owen", helper="Rae"),
    StoryParams(setting="lake", child="Lina", helper="Juno"),
]


def resolve_by_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    return params


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        child=args.child or rng.choice(CHILD_NAMES),
        helper=args.helper or rng.choice([n for n in HELPER_NAMES if n != (args.child or "")]),
    )
    _reasonableness_gate(params)
    return params


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1. #show can_float/1. #show has_snack/1. #show is_creature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} at {p.setting} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
