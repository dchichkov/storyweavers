#!/usr/bin/env python3
"""
A small storyworld for a rhyming tale of curiosity and repetition:
a child hears a shrill concert, follows a clue, and finds a quilted surprise.

This script models a tiny stateful domain where:
- curiosity rises when a child hears a strange sound or notices a hidden object
- repetition is an emotional/physical rhythm that makes the child try the same
  action again and again
- a concert can be shrill, and the child may want to inspect the source
- a quilt can hide, soften, or reveal something warm and interesting

The story is built from simulated state rather than fixed text: the child,
the sound, the hidden object, and the ending all depend on the world model.
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
    hidden_by: Optional[str] = None
    openable: bool = False
    open_state: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"shine": 0.0, "sound": 0.0, "warmth": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "repetition": 0.0, "joy": 0.0, "surprise": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    time: str
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


THRESHOLD = 1.0


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["repetition"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 0.5
    out.append("Again and again, the child listened with a grin.")
    return out


def _r_curious_open(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    quilt = world.get("quilt")
    mystery = world.get("mystery")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    if not quilt.openable or quilt.open_state:
        return out
    sig = ("open",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    quilt.open_state = True
    mystery.hidden_by = None
    child.memes["surprise"] += 1
    out.append("With a careful peek, the quilted cover opened wide.")
    return out


def _r_warm_reveal(world: World) -> list[str]:
    out: list[str] = []
    quilt = world.get("quilt")
    mystery = world.get("mystery")
    if not quilt.open_state:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mystery.meters["warmth"] += 1
    mystery.meters["shine"] += 1
    out.append("Under the quilt, a tiny glowing music box gave a gentle hum.")
    return out


CAUSAL_RULES = [_r_repeat, _r_curious_open, _r_warm_reveal]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyming_line(a: str, b: str) -> str:
    return f"{a} {b}"


def build_world() -> World:
    world = World(place="the little hall", time="evening")

    child = world.add(Entity(
        id="child",
        kind="character",
        type="girl",
        label="Mina",
        phrase="a curious little girl named Mina",
        meters={"shine": 0.0, "sound": 0.0, "warmth": 0.0},
        memes={"curiosity": 0.0, "repetition": 0.0, "joy": 0.0, "surprise": 0.0},
    ))
    concert = world.add(Entity(
        id="concert",
        kind="thing",
        label="concert",
        phrase="a shrill concert",
        type="thing",
        meters={"shine": 0.0, "sound": 2.0, "warmth": 0.0},
    ))
    quilt = world.add(Entity(
        id="quilt",
        kind="thing",
        label="quilt",
        phrase="a patchwork quilt",
        type="thing",
        openable=True,
        open_state=False,
        meters={"shine": 0.0, "sound": 0.0, "warmth": 1.0},
    ))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        label="music box",
        phrase="a small music box",
        type="thing",
        hidden_by="quilt",
        meters={"shine": 0.0, "sound": 1.0, "warmth": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type="mother",
        label="Mom",
        phrase="her mother",
    ))

    world.facts.update(child=child, concert=concert, quilt=quilt, mystery=mystery, parent=parent)
    return world


def tell(world: World) -> None:
    child: Entity = world.facts["child"]
    concert: Entity = world.facts["concert"]
    quilt: Entity = world.facts["quilt"]
    mystery: Entity = world.facts["mystery"]
    parent: Entity = world.facts["parent"]

    world.say(
        f"In the little hall at evening light, {child.phrase} walked in with a bright, bright sight."
    )
    world.say(
        f"A shrill concert rang through the room with a squeak, and {child.label} leaned near to take a peek."
    )
    child.meters["sound"] += concert.meters["sound"]
    child.memes["curiosity"] += 1
    world.say(
        f"The sound was high and thin and keen, so {child.label} thought, \"What can that music mean?\""
    )

    world.para()
    world.say(
        f"She tiptoed on, then tiptoed back; she followed the notes along the track."
    )
    child.memes["repetition"] += 1
    propagate(world, narrate=True)
    world.say(
        f"She whispered, \"One more look, one more go,\" for curious hearts like to follow the glow."
    )
    child.memes["repetition"] += 1
    propagate(world, narrate=True)

    world.para()
    if quilt.open_state:
        world.say(
            f"At last the quilt was lifted high, and under it sat a warm surprise nearby."
        )
        world.say(
            f"It was a little music box, tucked in the fold, with a gentle tune inside the gold."
        )
    else:
        world.say(
            f"The quilt stayed closed, soft and neat, but Mina still smiled from head to feet."
        )

    child.memes["joy"] += 1
    if quilt.open_state:
        child.memes["joy"] += 1
    world.say(
        f"{parent.label} smiled and said, \"A curious peek can find a sweet repeat.\""
    )
    world.say(
        f"And Mina clapped to the concert's beat, while the quilt kept the tiny box cozy and sweet."
    )

    world.facts["resolved"] = quilt.open_state


def story_text(world: World) -> str:
    return world.render()


def build_story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    concert: Entity = world.facts["concert"]
    quilt: Entity = world.facts["quilt"]
    mystery: Entity = world.facts["mystery"]
    parent: Entity = world.facts["parent"]

    qa = [
        QAItem(
            question=f"Why did {child.label} lean in and look around during the concert?",
            answer=f"{child.label} was curious, and the concert sounded shrill, so she wanted to know what was making that high sound.",
        ),
        QAItem(
            question=f"What did the quilt hide in the story?",
            answer=f"The quilt hid a small music box, and it stayed tucked under the quilt until Mina looked more closely.",
        ),
        QAItem(
            question=f"How did repetition show up in the story?",
            answer="Mina listened again and again, and she peeked more than once because she wanted one more look.",
        ),
        QAItem(
            question=f"Who helped make the ending feel happy?",
            answer=f"{parent.label} helped by smiling and praising Mina's curious peek, which made the ending warm and cheerful.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question="What changed after Mina opened the quilt?",
                answer="The quilt opened wide, the hidden music box came into view, and Mina felt happy because the mystery was solved.",
            )
        )
    return qa


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quilt?",
            answer="A quilt is a blanket made from sewn pieces of cloth. It can keep someone warm and can also cover or hide things.",
        ),
        QAItem(
            question="What does shrill mean when you hear a sound?",
            answer="Shrill means a sound is very high and sharp, like it can cut through the air and catch your attention right away.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more, look closer, and ask questions about something interesting.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same thing again and again. In stories, it can make a rhythm that feels playful and memorable.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    return [
        "Write a short rhyming story for a young child about a shrill concert, a quilt, and a curious peek.",
        f"Tell a gentle story where {child.label} follows a high sound, looks under a quilt, and finds a happy surprise.",
        "Make the story sing with repetition and rhyme, and end with a warm, cozy image.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        if e.openable:
            bits.append(f"open_state={e.open_state}")
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("character", "child"))
    lines.append(asp.fact("character", "parent"))
    lines.append(asp.fact("thing", "concert"))
    lines.append(asp.fact("thing", "quilt"))
    lines.append(asp.fact("thing", "mystery"))
    lines.append(asp.fact("shrill", "concert"))
    lines.append(asp.fact("covered_by", "mystery", "quilt"))
    lines.append(asp.fact("openable", "quilt"))
    lines.append(asp.fact("curious", "child"))
    lines.append(asp.fact("repeats", "child"))
    return "\n".join(lines)


ASP_RULES = r"""
curious_to_peek(C,Q) :- curious(C), openable(Q), covered_by(M,Q).
repeat_pattern(C) :- repeats(C).
happy_end(C,M) :- curious_to_peek(C,Q), covered_by(M,Q), repeat_pattern(C).
#show curious_to_peek/2.
#show repeat_pattern/1.
#show happy_end/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/2."))
    atoms = asp.atoms(model, "happy_end")
    expected = [("child", "mystery")]
    if atoms == expected:
        print("OK: clingo gate matches the Python world model.")
        return 0
    print("MISMATCH between clingo and Python world model:")
    print("  clingo:", atoms)
    print("  python:", expected)
    return 1


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    place: str = "the little hall"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: shrill concert, quilt, curiosity, repetition.")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name", type=str, default=None)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(["Mina", "Lily", "Ruby", "Nora", "Ella"])
    return StoryParams(seed=None, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world()
    world.facts["child"].label = params.name
    world.facts["child"].phrase = f"a curious little girl named {params.name}"
    tell(world)
    sample = StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
        world=world,
    )
    return sample


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
        print(asp_program("#show happy_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show curious_to_peek/2. #show repeat_pattern/1. #show happy_end/2."))
        print(asp.atoms(model, "curious_to_peek"))
        print(asp.atoms(model, "repeat_pattern"))
        print(asp.atoms(model, "happy_end"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(seed=base_seed + i, name=name)) for i, name in enumerate(["Mina", "Lily", "Ruby"])]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
