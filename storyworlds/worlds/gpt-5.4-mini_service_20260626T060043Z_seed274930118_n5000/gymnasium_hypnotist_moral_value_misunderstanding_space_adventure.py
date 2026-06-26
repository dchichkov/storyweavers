#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure-style tale set in a gymnasium,
featuring a hypnotist, a Moral Value, and a misunderstanding that gets resolved
through a safer, kinder choice.

The world is deliberately small and classical:
- one setting: the gymnasium
- one child hero
- one misleading hypnotist trick
- one moral value that matters
- one misunderstanding that is repaired by a better plan

The story is state-driven: physical meters and emotional memes change as the
plot unfolds, and the final image proves what changed.
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

MORAL_VALUES = {
    "honesty": "honesty",
    "kindness": "kindness",
    "patience": "patience",
    "courage": "courage",
}

MISUNDERSTANDINGS = {
    "mirror_trick": "thought the hypnotist was giving a true space mission order",
    "sleepy_signal": "thought the swaying watch meant everyone had to obey without asking",
    "silver_ring": "thought the shiny ring was a magic command instead of a stage prop",
}

NAMES = ["Ari", "Mina", "Jules", "Noa", "Tala", "Lio", "Pia", "Ravi"]
ADULT_NAMES = ["Ms. Vega", "Captain Sol", "Mr. Orbit", "Dr. Comet"]
TRAITS = ["curious", "brave", "thoughtful", "careful", "quick"]

ASP_RULES = r"""
#show valid_story/3.

place(gymnasium).
hero(child).
adult(hypnotist).
value(honesty).
value(kindness).
value(patience).
value(courage).

misunderstanding(mirror_trick).
misunderstanding(sleepy_signal).
misunderstanding(silver_ring).

% A story is valid when the gymnasium contains a hypnotist, one moral value,
% and one misunderstanding that can be repaired by a clear explanation.
valid_story(gymnasium, V, M) :- value(V), misunderstanding(M).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    adult: str
    value: str
    misunderstanding: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str = "the gymnasium"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        w = World(place=self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def is_valid_combo(value: str, misunderstanding: str) -> bool:
    return value in MORAL_VALUES and misunderstanding in MISUNDERSTANDINGS


def choose_reasonable_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    values = [args.value] if getattr(args, "value", None) else list(MORAL_VALUES)
    mis = [args.misunderstanding] if getattr(args, "misunderstanding", None) else list(MISUNDERSTANDINGS)
    combos = [(v, m) for v in values for m in mis if is_valid_combo(v, m)]
    if not combos:
        raise StoryError("No valid Moral Value / Misunderstanding combination matches the given options.")
    return rng.choice(sorted(combos))


def explain_rejection(value: str, misunderstanding: str) -> str:
    return (
        f"(No story: {value} and {misunderstanding} cannot make a clear Space Adventure "
        f"story in the gymnasium.)"
    )


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        traits=["little", params.trait],
    ))
    hypnotist = world.add(Entity(
        id="hypnotist",
        kind="character",
        type="adult",
        label=params.adult,
        traits=["calm", "mysterious"],
    ))
    value_obj = world.add(Entity(
        id=params.value,
        type="moral_value",
        label=params.value,
        phrase=params.value,
        owner=hero.id,
    ))
    trick = world.add(Entity(
        id=params.misunderstanding,
        type="misunderstanding",
        label=params.misunderstanding,
        phrase=MISUNDERSTANDINGS[params.misunderstanding],
    ))
    world.facts.update(hero=hero, hypnotist=hypnotist, value=value_obj, trick=trick)
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    hypnotist: Entity = f["hypnotist"]
    value: Entity = f["value"]
    trick: Entity = f["trick"]

    hero.memes["curiosity"] = 1
    hero.memes["wonder"] = 1

    world.say(
        f"{hero.id} was a little {hero.traits[-1]} {hero.type} who loved the gymnasium "
        f"because it felt like a tiny space station full of echoes and bright lights."
    )
    world.say(
        f"On the practice floor, {hero.id} noticed {hypnotist.label} with a shiny prop and a slow, "
        f"swaying voice."
    )

    world.para()
    world.say(
        f"{hero.id} listened too closely and {trick.phrase}, so {hero.pronoun()} started to feel "
        f"unsure."
    )
    hero.memes["misunderstood"] = 1
    hero.memes["fear"] = 1
    world.say(
        f"That could have made a bad choice, because the shiny prop was only for a stage trick, "
        f"not a real command from space."
    )

    world.para()
    world.say(
        f"{hypnotist.label} saw the worry and spoke plainly: 'No one has to obey a trick. "
        f"We tell the truth here, and we choose kindly.'"
    )
    hero.memes["misunderstanding"] = 0
    hero.memes["trust"] = 1
    hero.memes["moral_strength"] = 1
    value.meters["bright"] = 1

    world.say(
        f"{hero.id} remembered {value.label} and asked a careful question instead of following the "
        f"swaying prop."
    )
    world.say(
        f"{hypnotist.label} smiled and explained the trick, and the gymnasium stopped feeling strange."
    )

    world.para()
    hero.memes["relief"] = 1
    hero.memes["pride"] = 1
    world.say(
        f"In the end, {hero.id} stood beside {hypnotist.label} in the gymnasium, holding {value.label} "
        f"like a tiny star badge, glad to have chosen the honest path."
    )
    world.say(
        f"The shiny prop was just a prop after all, and the real adventure was {hero.id} learning to "
        f"pause, ask, and do what was right."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    value: Entity = f["value"]
    trick: Entity = f["trick"]
    return [
        f'Write a Space Adventure-style story set in a gymnasium where {hero.id} meets a hypnotist and learns about {value.label}.',
        f"Tell a child-friendly story in the gymnasium where a misunderstanding makes {hero.id} unsure, but honesty helps.",
        f'Write a short story about a hypnotist, a shiny trick, and the moral value "{value.label}" in a gymnasium.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    hypnotist: Entity = f["hypnotist"]
    value: Entity = f["value"]
    trick: Entity = f["trick"]
    return [
        QAItem(
            question=f"Where did {hero.id} meet {hypnotist.label}?",
            answer="They met in the gymnasium, which felt like a little space station because of the bright lights and echoes.",
        ),
        QAItem(
            question=f"What misunderstanding did {hero.id} have about the hypnotist's trick?",
            answer=f"{hero.id} {MISUNDERSTANDINGS[trick.id]} before the adult explained that it was only a stage trick.",
        ),
        QAItem(
            question=f"What moral value helped {hero.id} choose well?",
            answer=f"{value.label} helped {hero.id} pause, ask a question, and choose the honest path.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} ended the story feeling calm and proud, standing in the gymnasium with the truth made clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypnotist?",
            answer="A hypnotist is a performer or helper who uses calm words, attention, and suggestion as part of a trick or demonstration.",
        ),
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the truth and not pretending something false is real.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what is really going on.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "gymnasium"), asp.fact("character", "hypnotist")]
    for v in MORAL_VALUES:
        lines.append(asp.fact("value", v))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("gymnasium", v, m) for v in MORAL_VALUES for m in MISUNDERSTANDINGS if is_valid_combo(v, m)}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python ({len(clingo_set)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld in a gymnasium with a hypnotist.")
    ap.add_argument("--value", choices=sorted(MORAL_VALUES))
    ap.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--adult", choices=ADULT_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    value, misunderstanding = choose_reasonable_combo(args, rng)
    if args.value and args.misunderstanding and not is_valid_combo(args.value, args.misunderstanding):
        raise StoryError(explain_rejection(args.value, args.misunderstanding))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        name=name,
        gender=gender,
        trait=trait,
        adult=adult,
        value=value,
        misunderstanding=misunderstanding,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
    StoryParams(name="Ari", gender="boy", trait="curious", adult="Captain Sol", value="honesty", misunderstanding="mirror_trick"),
    StoryParams(name="Mina", gender="girl", trait="careful", adult="Ms. Vega", value="kindness", misunderstanding="sleepy_signal"),
    StoryParams(name="Tala", gender="girl", trait="brave", adult="Dr. Comet", value="patience", misunderstanding="silver_ring"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, value, misunderstanding in stories:
            print(f"  {place:10} {value:10} {misunderstanding}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {p.name}: {p.value} / {p.misunderstanding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
