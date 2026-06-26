#!/usr/bin/env python3
"""
A small Storyweavers world: a daycare-room bedtime tale about a hatter,
mistletoe, a flunked performance, foreshadowing, teamwork, and a rhyme-filled
turn toward a gentle ending.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    helper: str
    parent: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy as _copy

        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


DAYCARE_ROOM = "the daycare room"


def rhyme_line(word1: str, word2: str) -> str:
    return f"{word1} with {word2}, soft as snow in a row."


def build_world(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    helper = w.add(Entity(id=params.helper, kind="character", type="boy", label=params.helper))
    parent = w.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    hatter = w.add(Entity(id="Hatter", kind="character", type="man", label="the hatter"))
    mistletoe = w.add(Entity(
        id="Mistletoe",
        kind="thing",
        label="mistletoe",
        phrase="a green sprig of mistletoe with tiny white berries",
        owner=child.id,
        caretaker=parent.id,
    ))
    ribbon = w.add(Entity(
        id="Ribbon",
        kind="thing",
        label="red ribbon",
        phrase="a red ribbon for the waiting place",
        owner=helper.id,
        caretaker=parent.id,
    ))
    songbell = w.add(Entity(
        id="Songbell",
        kind="thing",
        label="songbell",
        phrase="a little songbell for counting turns",
        owner=helper.id,
        caretaker=parent.id,
    ))
    child.memes["hope"] = 1.0
    helper.memes["eager"] = 1.0
    parent.memes["watchful"] = 1.0
    hatter.memes["foreshadow"] = 1.0
    w.facts.update(child=child, helper=helper, parent=parent, hatter=hatter, mistletoe=mistletoe, ribbon=ribbon, songbell=songbell)
    return w


def tell_story(w: World) -> None:
    c = w.facts["child"]
    h = w.facts["helper"]
    p = w.facts["parent"]
    t = w.facts["hatter"]
    m = w.facts["mistletoe"]
    r = w.facts["ribbon"]
    s = w.facts["songbell"]

    w.say(
        f"In {DAYCARE_ROOM}, {c.id} liked the sleepy corners, the picture books, and the soft lamp glow."
    )
    w.say(
        f"There was also {m.phrase}, tucked into a paper star. The hatter had left it there earlier, and {t.label} had said, "
        f"“If the little sprig appears, then soon the room will need careful feet and gentle teamwork.”"
    )
    w.say(
        f"{c.id} heard that tiny warning and looked at {m.label} again. It made a small promise in the air, like a rhyme waiting to wake up: "
        + rhyme_line("near", "dear")
    )
    w.para()
    w.say(
        f"When tidy-up time came, {c.id} wanted to hang the {m.label} on the reading nook all alone, but the loop slipped from {c.id}'s hands."
    )
    w.say(
        f"The sprig swung low, and {p.label} noticed at once. “That is our foreshadowing,” {p.pronoun()} said softly. “It means we should not rush.”"
    )
    w.say(
        f"{h.id} nodded and lifted the little bell. “One friend can hold, one friend can tie,” {h.pronoun()} sang, "
        f"“and two kind hands can make things right and bright.”"
    )
    w.para()
    w.say(
        f"So {c.id}, {h.id}, and {p.label} worked together. {c.id} held the ribbon, {h.id} steadied the sprig, and {p.pronoun()} tied it high and safe."
    )
    w.say(
        f"Then they set the {s.label} beside the books as a reminder: when trouble peeks in, teamwork can make it wink away."
    )
    w.say(
        f"{c.id} smiled, because the room felt calm again. The mistletoe stayed up, the ribbon stayed neat, and the bedtime rhyme drifted over the daycare room like warm milk and moonlight."
    )
    w.facts["resolved"] = True
    w.facts["story_line"] = "foreshadowing -> near mishap -> teamwork -> calm ending"


def generation_prompts(w: World) -> list[str]:
    return [
        'Write a bedtime story for a young child in a daycare room about a hatter, mistletoe, and a small mistake that turns into teamwork.',
        'Tell a gentle story that foreshadows a problem with mistletoe, then resolves it through teamwork and a rhyming line.',
        'Write a child-friendly bedtime tale set in a daycare room where a hatter gives a warning and everyone helps fix the plan.',
    ]


def story_qa(w: World) -> list[QAItem]:
    c = w.facts["child"]
    h = w.facts["helper"]
    p = w.facts["parent"]
    t = w.facts["hatter"]
    m = w.facts["mistletoe"]
    return [
        QAItem(
            question=f"Where did the story happen?",
            answer=f"The story happened in {DAYCARE_ROOM}, where the light was soft and the room felt ready for bedtime.",
        ),
        QAItem(
            question=f"Who warned that the mistletoe would need careful feet and gentle teamwork?",
            answer=f"The hatter warned them. {t.label.capitalize()} said the mistletoe would need careful feet and gentle teamwork.",
        ),
        QAItem(
            question=f"What almost went wrong when {c.id} tried to hang the mistletoe alone?",
            answer=f"{c.id} almost dropped the loop while trying to hang {m.label} alone, so the plan needed help before it became a bigger problem.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"{c.id}, {h.id}, and {p.label} fixed it by working together: one held, one steadied, and one tied the ribbon safely.",
        ),
        QAItem(
            question=f"Why did the story include foreshadowing?",
            answer=f"It included foreshadowing because the hatter's earlier warning hinted that the mistletoe might cause trouble if everyone rushed.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other do a job together so it becomes easier and kinder for everyone.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue or hint that tells you something important may happen later in the story.",
        ),
        QAItem(
            question="What does a rhyme do in a bedtime story?",
            answer="A rhyme can make a bedtime story sound playful, musical, and easy to remember.",
        ),
        QAItem(
            question="What is mistletoe?",
            answer="Mistletoe is a green plant with small berries that people sometimes hang up for decoration.",
        ),
    ]


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("place", "daycare_room"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "rhyme"),
        asp.fact("thing", "mistletoe"),
        asp.fact("character", "hatter"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
feature_story(ok) :- place(daycare_room), feature(foreshadowing), feature(teamwork), feature(rhyme), thing(mistletoe), character(hatter).
#show feature_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show feature_story/1."))
    ok = any(sym.name == "feature_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the daycare-room bedtime story features.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: hatter, mistletoe, and teamwork in a daycare room.")
    ap.add_argument("--name", choices=["Luna", "Milo", "Nora", "Ivy"], help="child name")
    ap.add_argument("--helper", choices=["Finn", "Owen", "Theo", "Eli"], help="helpful friend name")
    ap.add_argument("--parent", choices=["mother", "father"], help="parent type")
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
        name=args.name or rng.choice(["Luna", "Milo", "Nora", "Ivy"]),
        helper=args.helper or rng.choice(["Finn", "Owen", "Theo", "Eli"]),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.kind} " + " ".join(bits))
    lines.append(f"  facts={world.facts.get('story_line', '')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== (3) World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show feature_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams("Luna", "Finn", "mother", base_seed)),
            generate(StoryParams("Milo", "Theo", "father", base_seed + 1)),
            generate(StoryParams("Nora", "Eli", "mother", base_seed + 2)),
        ]
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
