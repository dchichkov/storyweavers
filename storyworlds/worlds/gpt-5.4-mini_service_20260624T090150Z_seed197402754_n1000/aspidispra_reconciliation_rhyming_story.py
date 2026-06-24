#!/usr/bin/env python3
"""
A small rhyming storyworld about aspidispra and reconciliation.

A seed tale:
A little aspidispra loved to sing and rhyme, but it hurt a friend's feelings by
taking the last bright ribbon without asking. The friend turned away. The little
aspidispra felt a pang, found the courage to say sorry, shared the ribbon, and
the two sang together again.

The simulated world tracks:
- a small physical item that can be taken and shared
- emotional states for hurt, regret, and peace
- a simple reconciliation turn where apology and giving back repair the bond
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

ASP_RULES = r"""
% A reconciliation is reasonable when the same story contains:
% - a hurt friend
% - an apology
% - the item being shared back
% - peace restored
hurt_friend(F) :- hurt(F).
apology_made(A) :- apologized(A).
item_returned(I) :- shared_back(I).
reconciled(A, F, I) :- apologized(A), hurt(F), shared_back(I), peace_restored.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"aspidispra", "friend"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    name: str
    friend_name: str
    item: str = "bright ribbon"
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    friend: Entity
    item: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {"meadow": "the meadow"}
PRIZES = {"ribbon": "bright ribbon"}
NAMES = ["Mira", "Nilo", "Pip", "Luna", "Tavi", "Suri"]
FRIENDS = ["Bram", "Kiki", "Rory", "Mina", "Jori", "Fenn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming reconciliation storyworld about aspidispra.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    if name == friend:
        raise StoryError("The hero and friend must have different names.")
    return StoryParams(name=name, friend_name=friend)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hurt", "friend"),
            asp.fact("apologized", "hero"),
            asp.fact("shared_back", "ribbon"),
            asp.fact("peace_restored"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciled/3."))
    atoms = set(asp.atoms(model, "reconciled"))
    expected = {("hero", "friend", "ribbon")}
    if atoms == expected:
        print("OK: ASP twin matches the reconciliation story pattern.")
        return 0
    print("MISMATCH:")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


def make_world(params: StoryParams) -> World:
    hero = Entity(id="hero", kind="character", label=params.name, type="aspidispra", meters={"joy": 0.0}, memes={"regret": 0.0})
    friend = Entity(id="friend", kind="character", label=params.friend_name, type="friend", meters={"joy": 0.0}, memes={"hurt": 0.0, "peace": 0.0})
    item = Entity(id="ribbon", kind="thing", label=params.item, type="ribbon", owner=friend.id, meters={"held": 1.0})
    w = World(hero=hero, friend=friend, item=item)

    # Act 1: rhyme and play.
    w.say(f"{hero.label} the aspidispra loved a soft little rhyme,")
    w.say(f"and danced in the meadow one sun-bright time.")
    w.say(f"{friend.label} held a {item.label}, shiny and neat,")
    w.say(f"a prize that made singing feel extra sweet.")

    # Act 2: the trouble.
    w.para()
    hero.memes["want"] = 1.0
    w.say(f"{hero.label} saw the {item.label} and reached with a tap,")
    w.say(f"then took it and tucked it inside {hero.pronoun('possessive')} lap.")
    friend.memes["hurt"] = 1.0
    friend.meters["turn_away"] = 1.0
    w.say(f"{friend.label} frowned and turned, with a teary-eyed glare,")
    w.say(f"for taking the ribbon felt not kind or fair.")

    # Act 3: reconciliation.
    w.para()
    hero.memes["regret"] = 1.0
    hero.meters["apology"] = 1.0
    w.say(f"Then {hero.label} felt sorry, with a fluttering sigh,")
    w.say(f"and spoke, “I was selfish. I know I did wrong. I’m shy — but I try.”")
    w.say(f"{hero.label} gave back the ribbon, bright as a spark,")
    w.say(f"and offered a bow with a warm, gentle mark.")
    item.owner = friend.id
    item.meters["held"] = 0.0
    friend.memes["hurt"] = 0.0
    friend.memes["peace"] = 1.0
    hero.meters["joy"] = 1.0
    friend.meters["joy"] = 1.0
    w.say(f"{friend.label} smiled again, and the air felt light;")
    w.say(f"they rhymed side by side till the stars shone bright.")
    w.say(f"The ribbon stayed shared, and the friendship grew deep,")
    w.say(f"with peace in their hearts and a happy, cozy sleep.")

    w.facts.update(hero=hero, friend=friend, item=item, reconciled=True)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about an aspidispra named {f["hero"].label} who must make things right.',
        f'Tell a gentle reconciliation story where {f["hero"].label} takes a {f["item"].label}, says sorry, and shares it back.',
        f'Write a child-friendly rhyming tale about hurt feelings, an apology, and friendship growing warm again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, fr, it = f["hero"], f["friend"], f["item"]
    return [
        QAItem(
            question=f"What did {h.label} the aspidispra do that made {fr.label} sad?",
            answer=f"{h.label} took the {it.label} without asking, and that made {fr.label} feel hurt.",
        ),
        QAItem(
            question=f"How did {h.label} fix the problem?",
            answer=f"{h.label} said sorry, gave the {it.label} back, and made things kind again.",
        ),
        QAItem(
            question=f"How did the story end for {h.label} and {fr.label}?",
            answer=f"They were smiling together, sharing the {it.label}, and their friendship felt peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an apology?",
            answer="An apology is when someone says they are sorry for a hurtful choice and tries to make it right.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop being upset and rebuild their friendship after a problem.",
        ),
        QAItem(
            question="Why can sharing help after a mistake?",
            answer="Sharing can help because it shows kindness, returns what was taken, and makes it easier to trust again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in [world.hero, world.friend, world.item]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: label={ent.label} type={ent.type} meters={meters} memes={memes} owner={ent.owner}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(name="Mira", friend_name="Bram"),
    StoryParams(name="Luna", friend_name="Kiki"),
    StoryParams(name="Tavi", friend_name="Mina"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciled/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reconciled/3."))
        print(asp.atoms(model, "reconciled"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
