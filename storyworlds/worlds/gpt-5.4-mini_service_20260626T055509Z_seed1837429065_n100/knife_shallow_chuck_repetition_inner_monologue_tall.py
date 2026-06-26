#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/knife_shallow_chuck_repetition_inner_monologue_tall.py
================================================================================================

A small, standalone Storyweavers world for a tall-tale-style story about a
knife, a shallow place, and Chuck.

Premise:
- Chuck is a rangy, boastful little helper with a big imagination.
- He wants to use a knife to shape a small chunk of wood by a shallow creek.
- The creek is shallow, which makes the knife easy to lose but also easy to spot.
- Repetition and inner monologue are the narrative instruments that carry the turn.

The world simulates:
- physical meters: reach, depth, sharpness, wetness, progress
- emotional memes: pride, worry, patience, relief

The story is generated from state changes, not from a frozen template paragraph.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["reach", "depth", "sharpness", "wetness", "progress"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "worry", "patience", "relief", "focus"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "cowboy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the shallow creek"
    affordance: str = "carving"


@dataclass
class StoryParams:
    name: str = "Chuck"
    helper: str = "Mabel"
    setting: str = "creek"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def repeated_phrase(word: str, count: int = 3) -> str:
    return ", ".join([word] * count)


def inner_monologue(chuck: Entity, thought: str) -> str:
    return f'Chuck thought, "{thought}"'


def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type="boy", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=params.helper))
    knife = world.add(Entity(
        id="knife",
        type="knife",
        label="knife",
        phrase="a keen little knife",
        owner=hero.id,
    ))
    wood = world.add(Entity(
        id="wood",
        type="thing",
        label="chunk of wood",
        phrase="a small chunk of cedar",
        owner=hero.id,
    ))
    creek = world.add(Entity(
        id="creek",
        type="place",
        label="shallow creek",
        phrase="a shallow creek",
    ))
    creek.meters["depth"] = 0.5
    knife.meters["sharpness"] = 1.0
    hero.memes["pride"] = 1.0
    hero.memes["focus"] = 1.0
    helper.memes["worry"] = 1.0
    world.facts.update(hero=hero, helper=helper, knife=knife, wood=wood, creek=creek)
    return world


def predict_misstep(world: World) -> bool:
    knife = world.get("knife")
    creek = world.get("creek")
    return creek.meters["depth"] < 1.0 and knife.meters["sharpness"] >= THRESHOLD


def intro(world: World) -> None:
    h = world.facts["hero"]
    world.say(
        f"Chuck was a lanky little fellow with a grin as wide as a fence rail, "
        f"and he liked to say he could make a brave day out of a plain one."
    )
    world.say(
        f"He loved his knife, because it could shave a stick, split a string, "
        f"and help a small idea grow into something useful."
    )
    world.say(
        f"By the shallow creek, the water slipped over the stones like silver ribbon, "
        f"and Chuck felt his chest puff up with tall-tale pride."
    )
    h.memes["pride"] += 1.0


def desire(world: World) -> None:
    h = world.facts["hero"]
    knife = world.facts["knife"]
    wood = world.facts["wood"]
    h.memes["focus"] += 1.0
    world.say(
        f"He wanted to carve the {wood.label} into a whistle, then into a better whistle, "
        f"then into the best whistle a creek-side boy had ever heard."
    )
    world.say(
        f'He held up the {knife.label} and whispered, "{repeated_phrase("Easy")} now."'
    )
    world.say(
        inner_monologue(h, "Easy, easy, easy. A tidy cut will make a tidy tune.")
    )


def complication(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    knife = world.facts["knife"]
    wood = world.facts["wood"]
    creek = world.facts["creek"]

    if not predict_misstep(world):
        raise StoryError("The story needs the knife to be at real risk in the shallow creek.")

    world.para()
    world.say(
        f"Chuck knelt at the bank, and the shallow water gave him just enough room "
        f"to lean too far."
    )
    world.say(
        f"He shaved the {wood.label} once, shaved it twice, and on the third shave "
        f"the {knife.label} slipped from his fingers."
    )
    knife.meters["wetness"] += 1.0
    knife.memes["worry"] += 1.0
    h.memes["worry"] += 1.0
    world.say(
        f'Chuck gasped, "Now hold on, now hold on," for the blade flashed once and '
        f'sank into the shallow water.'
    )
    world.say(
        inner_monologue(h, "Don't lose it. Not here. Not in water that shallow.")
    )
    world.say(
        f"The helper put a hand to her chin and said that a lost knife in a shallow creek "
        f"was easier to find than a lost biscuit in a hayloft, but it still needed steady eyes."
    )
    helper.memes["worry"] += 1.0


def recovery(world: World) -> None:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    knife = world.facts["knife"]
    wood = world.facts["wood"]
    creek = world.facts["creek"]

    world.para()
    world.say(
        f"Chuck took one slow breath, then another, and he peered through the clear water."
    )
    world.say(
        f'"Easy, easy, easy," he said again, because repetition was the rope he used '
        f"to pull his thoughts straight."
    )
    world.say(
        inner_monologue(h, "If the creek is shallow, the knife cannot hide forever.")
    )

    knife.meters["wetness"] = max(0.0, knife.meters["wetness"] - 1.0)
    knife.memes["worry"] = 0.0
    h.memes["patience"] += 1.0
    h.memes["worry"] = max(0.0, h.memes["worry"] - 1.0)

    world.say(
        f"He slid a flat stick under the blade, lifted it as gentle as a moth on a leaf, "
        f"and fished the {knife.label} back up."
    )
    world.say(
        f"The blade came out clean, because the creek was shallow and the water had no mind "
        f"to keep a good tool hidden."
    )

    wood.meters["progress"] += 1.0
    h.memes["relief"] += 1.0
    helper.memes["relief"] += 1.0
    world.say(
        f"Then Chuck finished the whistle with careful little cuts, and the {wood.label} "
        f"turned into a bright thing with a brave sound."
    )
    world.say(
        f'He blew once, then twice, then once more, and the tune hopped over the stones '
        f"like a grasshopper in a hurry."
    )
    world.say(
        f'The helper laughed and said, "That there was a mighty fine rescue for a mighty '
        f"small blade.""
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    desire(world)
    complication(world)
    recovery(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall-tale story about Chuck, a shallow creek, and a knife.',
        'Tell a child-friendly story where repeated words and inner thoughts help a character recover a lost knife.',
        'Write a short, lively story in a tall-tale style that ends with a whistle made from a chunk of wood.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    knife = world.facts["knife"]
    helper = world.facts["helper"]
    wood = world.facts["wood"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about Chuck, a lanky little boy who likes to make useful things with his knife.",
        ),
        QAItem(
            question="What did Chuck want to make from the chunk of wood?",
            answer=f"He wanted to carve the {wood.label} into a whistle.",
        ),
        QAItem(
            question="Why was the knife hard to keep track of?",
            answer="Because Chuck dropped it into the shallow creek, and small things can seem to vanish in water for a moment.",
        ),
        QAItem(
            question="How did Chuck get the knife back?",
            answer="He slowed down, looked carefully through the shallow water, and lifted it out with a flat stick.",
        ),
        QAItem(
            question="What did the helper do?",
            answer="She watched, worried at first, then laughed when Chuck brought the knife back and finished the whistle.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does shallow mean?",
            answer="Shallow means not very deep, so something like water does not go down very far.",
        ),
        QAItem(
            question="Why can a knife help with wood?",
            answer="A knife can shave or shape wood by cutting off tiny bits at a time.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition is when a word, phrase, or sound is used again and again to make the story stronger or more musical.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thoughts, spoken inside the story so readers can hear what the character is thinking.",
        ),
    ]


ASP_RULES = r"""
#show risky/2.
#show resolved/1.

risky(knife,creek) :- shallow(creek), knife_present(knife).
resolved(hero) :- risky(knife,creek), hears_thought(hero).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import required by contract
    return "\n".join([
        asp.fact("shallow", "creek"),
        asp.fact("knife_present", "knife"),
        asp.fact("hears_thought", "hero"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    risky = set(asp.atoms(model, "risky"))
    resolved = set(asp.atoms(model, "resolved"))
    ok = risky == {("knife", "creek")} and resolved == {("hero",)}
    if ok:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH in ASP parity.")
    print("risky:", sorted(risky))
    print("resolved:", sorted(resolved))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld of Chuck, a knife, and a shallow creek.")
    ap.add_argument("--name", default="Chuck")
    ap.add_argument("--helper", default="Mabel")
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
    return StoryParams(
        name=args.name or "Chuck",
        helper=args.helper or rng.choice(["Mabel", "Nell", "Rose"]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(name=args.name or "Chuck", helper=args.helper or "Mabel", seed=args.seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
