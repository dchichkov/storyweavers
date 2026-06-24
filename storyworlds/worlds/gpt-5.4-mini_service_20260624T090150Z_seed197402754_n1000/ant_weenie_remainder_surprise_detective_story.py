#!/usr/bin/env python3
"""
A small storyworld for a tiny detective tale with an ant, a weenie, a remainder,
and a surprise reveal.
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
class StoryParams:
    seed: Optional[int] = None
    place: str = "kitchen"
    suspect: str = "mouse"
    container: str = "basket"
    weenie_count: int = 3


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = value

    def add_meter(self, key: str, value: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + value

    def add_meme(self, key: str, value: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + value


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            lines.append(f"  {e.name:10} ({e.kind:8}) {' '.join(bits)}")
        lines.append(f"  facts={self.facts}")
        return "\n".join(lines)


PLACES = {
    "kitchen": {
        "detail": "The kitchen was quiet, except for a tiny tap near the floor.",
        "afford": "search",
    },
    "garden": {
        "detail": "The garden had soft dirt, leaves, and one bent stepping stone.",
        "afford": "search",
    },
    "garage": {
        "detail": "The garage smelled like old boxes and dust, with a bright beam of light.",
        "afford": "search",
    },
}

SUSPECTS = {
    "mouse": {
        "clue": "small nibble marks",
        "motion": "scurried",
        "usual": "likes crumbs",
    },
    "bird": {
        "clue": "tiny shell bits",
        "motion": "hopped",
        "usual": "likes shiny things",
    },
    "cat": {
        "clue": "tufts of fur",
        "motion": "slunk",
        "usual": "likes warm spots",
    },
}

WEENIE = {
    "name": "weenie",
    "label": "a tiny weenie",
    "smell": "savory smell",
    "shape": "long little link",
}

REMAINDER = {
    "name": "remainder",
    "label": "the remainder",
    "meaning": "what is left after the first part is gone",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective storyworld about an ant, a weenie, and a surprise remainder.")
    ap.add_argument("--place", choices=sorted(PLACES), default=None)
    ap.add_argument("--suspect", choices=sorted(SUSPECTS), default=None)
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
    place = args.place or rng.choice(sorted(PLACES))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    return StoryParams(seed=args.seed, place=place, suspect=suspect, weenie_count=rng.choice([2, 3, 4]))


def reasonableness_gate(params: StoryParams) -> None:
    if params.weenie_count < 1:
        raise StoryError("The detective case needs at least one weenie.")
    if params.place == "kitchen" and params.suspect == "bird":
        raise StoryError("A bird is not a good kitchen culprit for this tiny case.")
    if params.place == "garage" and params.suspect == "mouse" and params.weenie_count < 2:
        raise StoryError("This garage case needs at least two weenie clues to make sense.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    w = World(params)
    detective = w.add(Entity("ant", "character", "a careful ant"))
    weenie = w.add(Entity("weenie", "object", WEENIE["label"]))
    remainder = w.add(Entity("remainder", "object", REMAINDER["label"]))
    suspect = w.add(Entity(params.suspect, "character", f"a sneaky {params.suspect}"))

    detective.add_meme("curiosity", 1)
    detective.add_meme("focus", 1)
    weenie.set_meter("count", float(params.weenie_count))
    remainder.set_meter("count", 1.0)
    suspect.add_meme("nervous", 1)

    w.facts.update(place=params.place, suspect=params.suspect, weenie_count=params.weenie_count)
    w.say(f"The ant was a little detective with a serious nose for clues.")
    w.say(f"One morning, the ant found a weenie with one missing bite and felt a surprise in the air.")
    w.say(f"In the {params.place}, there was also a remainder: just enough left to make the case strange.")
    w.para()
    w.say(PLACES[params.place]["detail"])
    w.say(f"The ant looked at the {WEENIE['shape']} and saw {params.weenie_count} pieces in all, except for the remainder.")
    w.say(f"That was the first clue, and it made the ant think someone had been there before.")
    w.para()
    clue = SUSPECTS[params.suspect]["clue"]
    motion = SUSPECTS[params.suspect]["motion"]
    w.say(f"The ant followed {clue} across the floor and into the {params.place}.")
    w.say(f"Near a corner, the {params.suspect} {motion}, trying to look innocent.")
    suspect.add_meme("suspicion", 1)
    weenie.add_meter("missing", 1.0)
    remainder.add_meme("mystery", 1)
    w.para()
    w.say(f"Then came the surprise: the ant found a tiny note tucked under the plate.")
    w.say(f"It said the {params.suspect} had not stolen the weenie at all; it had only moved the remainder aside to hide a crumb trail.")
    w.say(f"The ant smiled, because the whole case suddenly made sense.")
    suspect.memes["nervous"] = 0.0
    suspect.add_meme("relief", 1)
    detective.add_meme("joy", 1)
    w.facts["surprise"] = True
    return w


ASP_RULES = r"""
place(kitchen; garden; garage).
suspect(mouse; bird; cat).

case(P,S) :- place(P), suspect(S).
surprise(P,S) :- case(P,S).

#show case/2.
#show surprise/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show case/2."))
    return sorted(set(asp.atoms(model, "case")))


def asp_verify() -> int:
    py = {(p, s) for p in PLACES for s in SUSPECTS}
    cl = set(asp_cases())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} cases).")
        return 0
    print("MISMATCH between ASP and Python.")
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    if py - cl:
        print(" only in Python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f'Write a short detective story for a child that includes the words "ant", "weenie", and "remainder".',
        f"Tell a surprise detective story where an ant follows clues in the {p.place} and learns what happened to the weenie remainder.",
        f"Write a gentle mystery about a tiny ant detective, a suspicious {p.suspect}, and a leftover remainder.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    suspect = p.suspect
    place = p.place
    return [
        QAItem(
            question="Who was the detective in the story?",
            answer="The detective was the ant, who carefully followed the clues.",
        ),
        QAItem(
            question=f"What did the ant find in the {place}?",
            answer=f"The ant found a weenie with a remainder left behind, which made the case feel strange.",
        ),
        QAItem(
            question=f"Why did the ant think the {suspect} might be involved?",
            answer=f"The ant saw the clue trail in the {place} and noticed the {suspect} nearby, which made the {suspect} look suspicious at first.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The surprise was that the {suspect} had not stolen the weenie; it had only moved the remainder to hide a crumb trail.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a remainder?",
            answer="A remainder is what is left after the first part is gone or used up.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues to solve a mystery.",
        ),
        QAItem(
            question="What does surprise mean in a story?",
            answer="A surprise is something unexpected that changes what the characters thought was true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    return world.trace()


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in PLACES for s in SUSPECTS]


CURATED = [
    StoryParams(place="kitchen", suspect="mouse", weenie_count=3),
    StoryParams(place="garden", suspect="cat", weenie_count=4),
    StoryParams(place="garage", suspect="mouse", weenie_count=2),
]


def build_asp_program(show: str) -> str:
    return asp_program(show)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(build_asp_program("#show case/2."))
    return sorted(set(asp.atoms(model, "case")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_program("#show case/2.\n#show surprise/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for p, s in combos:
            print(f"{p:8} {s}")
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
            header = f"### {p.place} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
