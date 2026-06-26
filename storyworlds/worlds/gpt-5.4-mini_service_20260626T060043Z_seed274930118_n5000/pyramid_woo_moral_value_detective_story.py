#!/usr/bin/env python3
"""
pyramid_woo_moral_value_detective_story.py
==========================================

A small standalone storyworld in a detective-story style.

Premise:
- A young detective follows clues around a pyramid.
- The case turns on a moral value: honesty.
- A helper says "woo!" when a clue is found, giving the story a cheerful beat.

The simulated world tracks:
- Physical meters: clue counts, distance, hiddenness, certainty.
- Emotional memes: curiosity, worry, pride, relief, honesty, trust.

The story is generated from the live world state, not from a frozen template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = {}
        if self.memes is None:
            self.memes = {}

    def meter(self, key: str) -> float:
        return float(self.meters.get(key, 0.0))

    def meme(self, key: str) -> float:
        return float(self.memes.get(key, 0.0))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the pyramid"
    time: str = "night"
    mood: str = "quiet"


@dataclass
class Clue:
    id: str
    label: str
    hidden: bool = True
    truthful: bool = True
    value: str = "honesty"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

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

        other = World(self.scene)
        other.entities = _copy.deepcopy(self.entities)
        other.clues = _copy.deepcopy(self.clues)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


def _r_discover_clue(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    clue = world.clues["truth_note"]
    if detective.meter("search") < THRESHOLD:
        return out
    if clue.hidden:
        sig = ("discover", clue.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        clue.hidden = False
        detective.meters["certainty"] = detective.meter("certainty") + 1.0
        out.append("A small note appeared from behind a stone, and the mystery felt closer.")
    return out


def _r_worry_fades(world: World) -> list[str]:
    detective = world.get("detective")
    sidekick = world.get("sidekick")
    if detective.meme("honesty") >= THRESHOLD and not world.clues["truth_note"].hidden:
        sig = ("worry_fades",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        detective.memes["worry"] = 0.0
        sidekick.memes["worry"] = 0.0
        detective.memes["relief"] = detective.meme("relief") + 1.0
        sidekick.memes["relief"] = sidekick.meme("relief") + 1.0
        return ["The worry melted away."]
    return []


def _r_pride(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.meme("honesty") >= THRESHOLD and detective.meme("relief") >= THRESHOLD:
        sig = ("pride",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        detective.memes["pride"] = detective.meme("pride") + 1.0
        return ["The detective stood a little taller."]
    return []


CAUSAL_RULES = [_r_discover_clue, _r_worry_fades, _r_pride]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(place: str, hero_name: str, sidekick_name: str) -> World:
    world = World(Scene(place=place, time="night", mood="quiet"))
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type="girl",
        label=hero_name,
        meters={"search": 0.0, "distance": 0.0, "certainty": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "honesty": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type="boy",
        label=sidekick_name,
        meters={"search": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "trust": 1.0, "relief": 0.0},
    ))
    world.add_clue(Clue(id="truth_note", label="a truth note", hidden=True, truthful=True, value="honesty"))
    world.facts.update(detective=detective, sidekick=sidekick, clue=world.clues["truth_note"], place=place)
    return world


def opening(world: World) -> None:
    d = world.get("detective")
    s = world.get("sidekick")
    world.say(
        f"{d.label} was a little detective who loved hard cases and bright answers."
    )
    world.say(
        f"{s.label} followed along, whispering, \"woo!\" whenever a clue seemed near."
    )


def case_setup(world: World) -> None:
    d = world.get("detective")
    s = world.get("sidekick")
    place = world.scene.place
    world.para()
    world.say(
        f"One quiet night, they went to {place}, where the stones stood like old secrets."
    )
    world.say(
        f"{d.label} wanted to find the missing truth, but the path felt long and shadowy."
    )
    d.meters["search"] = 1.0
    d.memes["curiosity"] += 1.0
    d.memes["worry"] += 1.0
    s.meters["search"] = 1.0
    s.memes["curiosity"] += 1.0
    propagate(world, narrate=True)


def turn(world: World) -> None:
    d = world.get("detective")
    s = world.get("sidekick")
    clue = world.clues["truth_note"]
    world.para()
    if clue.hidden:
        world.say(
            f"Near the base of the pyramid, {s.label} spotted a tiny edge of paper."
        )
        world.say(
            f'"Woo!" {s.label} said, and {d.label} knelt down to look.'
        )
    d.memes["honesty"] += 1.0
    d.meters["search"] = d.meter("search") + 1.0
    d.meters["distance"] = d.meter("distance") + 1.0
    propagate(world, narrate=True)


def resolution(world: World) -> None:
    d = world.get("detective")
    s = world.get("sidekick")
    clue = world.clues["truth_note"]
    world.para()
    if not clue.hidden:
        world.say(
            f"The note said the answer was not a trick at all; it was honesty."
        )
        world.say(
            f"{d.label} smiled, because telling the truth made the case simple and kind."
        )
        world.say(
            f"{s.label} grinned and gave one more happy \"woo!\""
        )
    else:
        raise StoryError("The story ended before the truth clue was found.")
    if d.meme("pride") >= THRESHOLD:
        world.say(
            f"At the foot of the pyramid, {d.label} held the note carefully, and the night felt safe again."
        )


def tell(place: str, hero_name: str, sidekick_name: str) -> World:
    world = build_world(place, hero_name, sidekick_name)
    opening(world)
    case_setup(world)
    turn(world)
    resolution(world)
    return world


def reasonableness_gate(place: str) -> None:
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place!r}")


def generation_prompts(world: World) -> list[str]:
    d = world.get("detective")
    s = world.get("sidekick")
    place = world.scene.place
    return [
        f"Write a short detective story for a young child set at {place} with a pyramid, a clue, and the word 'woo'.",
        f"Tell a gentle mystery story where {d.label} and {s.label} search the pyramid and learn that honesty matters.",
        f"Write a small story about finding a missing truth near a pyramid, ending with a happy 'woo!'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.get("detective")
    s = world.get("sidekick")
    clue = world.clues["truth_note"]
    place = world.scene.place
    return [
        QAItem(
            question=f"Where did {d.label} and {s.label} go to solve the mystery?",
            answer=f"They went to {place}, where the pyramid stood in the quiet night.",
        ),
        QAItem(
            question="What kind of value did the clue point to?",
            answer="The clue pointed to honesty, which meant telling the truth.",
        ),
        QAItem(
            question=f"What did {s.label} say when a clue showed up?",
            answer=f'{s.label} said "woo!" because the clue made the mystery feel exciting.',
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The hidden note was found, the truth was clear, and the worry faded away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the truth instead of hiding it or making things up.",
        ),
        QAItem(
            question="What is a pyramid?",
            answer="A pyramid is a large building with sloping sides that come to a point at the top.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} label={e.label!r}"
        )
    for clue in world.clues.values():
        lines.append(f"clue {clue.id}: hidden={clue.hidden} value={clue.value}")
    return "\n".join(lines)


PLACES = {
    "pyramid": "the pyramid",
    "desert": "the desert museum",
    "museum": "the museum hall",
}


@dataclass
class SimpleAspRegistry:
    places: list[str]
    values: list[str]


ASP_RULES = r"""
place(pyramid).
place(desert).
place(museum).

value(honesty).

mystery(Place, honesty) :- place(Place).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("place", p) for p in PLACES]
    lines += [asp.fact("value", "honesty")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    python_set = {(p, "honesty") for p in PLACES}
    asp_set = set(asp_valid_places())
    if python_set == asp_set:
        print(f"OK: clingo parity matches Python gate ({len(python_set)} places).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld with a pyramid and honesty.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    place = args.place or rng.choice(list(PLACES))
    reasonableness_gate(place)
    hero_name = args.name or rng.choice(["Mina", "Ivy", "Nora", "Ruby", "Tess"])
    sidekick_name = args.sidekick or rng.choice(["Ollie", "Finn", "Sam", "Ben", "Theo"])
    if hero_name == sidekick_name:
        sidekick_name = sidekick_name + "y"
    return StoryParams(place=place, hero_name=hero_name, sidekick_name=sidekick_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero_name, params.sidekick_name)
    return StorySample(
        params=params,
        story=world.render(),
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


CURATED = [
    StoryParams(place="pyramid", hero_name="Mina", sidekick_name="Ollie"),
    StoryParams(place="museum", hero_name="Ivy", sidekick_name="Finn"),
    StoryParams(place="desert", hero_name="Nora", sidekick_name="Sam"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_places()
        print(f"{len(triples)} compatible mysteries:\n")
        for place, value in triples:
            print(f"  {place:8} {value}")
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
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
