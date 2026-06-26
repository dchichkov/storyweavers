#!/usr/bin/env python3
"""
A standalone storyworld script for an Animal Story about neighborhood
reconciliation, kindness, and inner monologue, centered on a maraschino cherry
problem that ends in a warm repair.
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

ANIMALS = {
    "cat": {
        "species": "cat",
        "title": "cat",
        "pronouns": ("she", "her", "her"),
        "names": ["Mina", "Luna", "Pip", "Nori", "Momo", "Tessa"],
    },
    "dog": {
        "species": "dog",
        "title": "dog",
        "pronouns": ("he", "him", "his"),
        "names": ["Otis", "Benny", "Roo", "Milo", "Arlo", "Finn"],
    },
    "rabbit": {
        "species": "rabbit",
        "title": "rabbit",
        "pronouns": ("they", "them", "their"),
        "names": ["Clover", "Poppy", "Juniper", "Basil", "Iris", "Wren"],
    },
    "fox": {
        "species": "fox",
        "title": "fox",
        "pronouns": ("he", "him", "his"),
        "names": ["Red", "Sable", "Rusty", "Ash", "Taro", "Quill"],
    },
}

NEIGHBORHOODS = {
    "block": "the little neighborhood block",
    "street": "the quiet neighborhood street",
    "garden": "the shared neighborhood garden",
    "courtyard": "the brick courtyard between the homes",
}

TREATS = {
    "maraschino": {
        "label": "maraschino cherry",
        "plural": "maraschino cherries",
        "taste": "bright and sweet",
        "risk": "sticky red juice",
        "mess": "sticky",
    },
    "cookie": {
        "label": "cookie",
        "plural": "cookies",
        "taste": "crumbly and sweet",
        "risk": "crumbs",
        "mess": "crumbly",
    },
}

HELPFUL_ACTIONS = {
    "share": "share the treat fairly",
    "apologize": "say sorry and make it right",
    "return": "bring it back before anyone worries more",
}

ASP_RULES = r"""
% The compatible story exists when an animal can be in a neighborhood and the
% treat can cause a worry that kindness can fix.
story(A,N,T) :- animal(A), neighborhood(N), treat(T), risky(T), kind_fix(T).
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"dog", "fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    animal: str
    name: str
    neighbor: str
    place: str
    treat: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)

    def copy(self) -> "World":
        nw = World(self.place)
        import copy as _copy
        nw.entities = _copy.deepcopy(self.entities)
        nw.facts = _copy.deepcopy(self.facts)
        nw.lines = []
        nw.fired = set(self.fired)
        return nw


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld: neighborhood, kindness, reconciliation, inner monologue.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--name")
    ap.add_argument("--neighbor")
    ap.add_argument("--place", choices=NEIGHBORHOODS)
    ap.add_argument("--treat", choices=TREATS)
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
    animal = args.animal or rng.choice(list(ANIMALS))
    place = args.place or rng.choice(list(NEIGHBORHOODS))
    treat = args.treat or "maraschino"
    if treat not in TREATS:
        raise StoryError("Unknown treat.")
    name = args.name or rng.choice(ANIMALS[animal]["names"])
    neighbor = args.neighbor or rng.choice([n for n in ["Mrs. Wren", "Mr. Otter", "Auntie Bea", "Mr. Finch"] if n != name])
    return StoryParams(animal=animal, name=name, neighbor=neighbor, place=place, treat=treat)


def _acts_risky(treat: str) -> bool:
    return treat == "maraschino"


def _has_kind_fix(treat: str) -> bool:
    return treat in {"maraschino", "cookie"}


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for n in NEIGHBORHOODS:
        lines.append(asp.fact("neighborhood", n))
    for t in TREATS:
        lines.append(asp.fact("treat", t))
        if _acts_risky(t):
            lines.append(asp.fact("risky", t))
        if _has_kind_fix(t):
            lines.append(asp.fact("kind_fix", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story/3."))
    clingo_set = set(asp.atoms(model, "story"))
    py_set = set((a, n, t) for a in ANIMALS for n in NEIGHBORHOODS for t in TREATS if _acts_risky(t) and _has_kind_fix(t))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def generate_story(world: World, params: StoryParams) -> None:
    info = ANIMALS[params.animal]
    treat = TREATS[params.treat]
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, label=params.name))
    neighbor = world.add(Entity(id="neighbor", kind="character", type="neighbor", label=params.neighbor))
    snack = world.add(Entity(id="snack", kind="thing", type=params.treat, label=treat["label"], phrase=f"a shiny {treat['label']}"))
    snack.owner = neighbor.id

    inner_voice = (
        f"{hero.name if hasattr(hero, 'name') else params.name} thought, "
        f"'I only wanted one little bite, but now {params.neighbor} might feel hurt.'"
    )

    hero.meters["want"] = 1
    hero.memes["guilt"] = 1
    world.facts.update(hero=hero, neighbor=neighbor, snack=snack, params=params, treat=treat)

    world.say(
        f"In {NEIGHBORHOODS[params.place]}, {params.name} the {info['title']} noticed {params.neighbor}'s "
        f"{treat['label']} sitting on a low wall by the path."
    )
    world.say(
        f"{params.name} loved how maraschino bright the treat looked, but the sweet smell made it hard to think of anything else."
    )
    world.say(inner_voice)

    if params.treat == "maraschino":
        world.say(
            f"When no one was looking, {params.name} took the maraschino cherry and gave it a quick nibble, "
            f"leaving sticky red juice on a paw."
        )
        hero.meters["sticky"] = 1
        hero.memes["worry"] = 1
        neighbor.memes["hurt"] = 1
        world.say(
            f"Then {params.name} heard tiny footsteps and saw {params.neighbor}'s face fall."
        )
        world.say(
            f"{params.name}'s stomach sank. 'That was unkind,' {params.name} thought, 'and I can still fix it.'"
        )
        world.say(
            f"{params.name} carried the half-eaten cherry back and said, 'I'm sorry. I should have asked first.'"
        )
        hero.memes["kindness"] = 1
        neighbor.memes["hurt"] = 0
        neighbor.memes["warmth"] = 1
        world.say(
            f"{params.neighbor} blinked, then smiled a little. 'Thank you for bringing it back,' {params.neighbor} said, "
            f"and the two neighbors sat together on the wall."
        )
        world.say(
            f"By the end, they split a fresh treat and shared the quiet air of the neighborhood, with no sticky feeling left between them."
        )
    else:
        world.say(
            f"{params.name} asked politely for a bite of the cookie, and {params.neighbor} nodded at once."
        )
        world.say(
            f"They ate it together and laughed at the crumbs, which made the neighborhood feel friendly and easy."
        )
        hero.memes["joy"] = 1
        neighbor.memes["warmth"] = 1

    world.facts["resolved"] = True
    world.facts["inner_monologue"] = True


def story_text(params: StoryParams) -> str:
    world = World(params.place)
    generate_story(world, params)
    return world.render()


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a short Animal Story about a neighborhood mistake that is repaired with kindness.",
        f"Tell a gentle story where {p.name} the {p.animal} thinks aloud, feels sorry, and makes peace with {p.neighbor}.",
        "Write a child-friendly story that includes a maraschino cherry, an apology, and a friendly ending in the neighborhood.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a {p.animal}, in {NEIGHBORHOODS[p.place]} with {p.neighbor}.",
        ),
        QAItem(
            question=f"What did {p.name} want at first?",
            answer=f"{p.name} wanted the maraschino cherry because it looked bright and sweet.",
        ),
        QAItem(
            question=f"How did the problem get fixed?",
            answer=f"{p.name} brought the treat back, apologized, and shared the moment kindly with {p.neighbor}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a maraschino cherry?",
            answer="A maraschino cherry is a bright red sweet cherry often used as a small treat or decoration.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, share, or speak gently so another creature feels cared for.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in a character's thoughts that helps them decide what to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params.place)
    generate_story(world, params)
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
    StoryParams(animal="cat", name="Mina", neighbor="Mrs. Wren", place="garden", treat="maraschino"),
    StoryParams(animal="dog", name="Otis", neighbor="Mr. Finch", place="block", treat="maraschino"),
    StoryParams(animal="rabbit", name="Clover", neighbor="Auntie Bea", place="courtyard", treat="maraschino"),
]


def resolve_valid(args: argparse.Namespace) -> None:
    if args.treat and args.treat != "maraschino":
        raise StoryError("This world is built around a maraschino cherry conflict.")
    return None


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story/3."))
        stories = sorted(set(asp.atoms(model, "story")))
        print(f"{len(stories)} compatible stories:")
        for a, n, t in stories:
            print(f"  {a} {n} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                resolve_valid(args)
                params = resolve_params(args, rng)
                params.seed = seed
            except StoryError as e:
                print(e)
                return
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
