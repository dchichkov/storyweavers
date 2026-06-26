#!/usr/bin/env python3
"""
A small animal-story world with supper and a jury, built around a bad ending.

Premise:
A farm animal sneaks extra supper into a trial-like "jury supper" where the animals
are meant to share one bowl fairly. The jury notices the mess and, after a simple
decision, the greedy animal ends up with no supper at all.

The story is state-driven:
- animals have hunger, fairness, and embarrassment memes
- supper is a physical object with portions
- jury attention and verdicts change the ending
- the final image proves what changed: the bowl is empty, and the greedy animal
  is still hungry while the others are calm

This world keeps an Animal Story feel: simple animals, concrete food, clear
social judgment, and a gentle but unhappy ending.
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
    caregiver: Optional[str] = None
    eaten: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"cow", "hen", "duck", "mouse", "goat", "cat"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"dog", "fox", "pig", "bear", "rat"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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


@dataclass
class StoryParams:
    place: str
    animal: str
    juror: str
    supper: str
    name: str
    seed: Optional[int] = None


ANIMALS = {
    "pig": {"label": "pig", "type": "pig", "name": "Pip"},
    "duck": {"label": "duck", "type": "duck", "name": "Dot"},
    "fox": {"label": "fox", "type": "fox", "name": "Fin"},
    "hen": {"label": "hen", "type": "hen", "name": "Henny"},
    "cow": {"label": "cow", "type": "cow", "name": "Moo"},
}

SUPPERS = {
    "porridge": ("a warm bowl of porridge", "porridge"),
    "corn": ("a little bowl of corn", "corn"),
    "soup": ("a steaming bowl of soup", "soup"),
    "bread": ("a basket of bread rolls", "bread rolls"),
}

PLACES = {
    "barn": "the barn",
    "yard": "the yard",
    "kitchen": "the kitchen",
}

TRAITS = ["hungry", "greedy", "nervous", "cheerful", "proud"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: supper, jury, bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--juror", choices=ANIMALS)
    ap.add_argument("--supper", choices=SUPPERS)
    ap.add_argument("--name")
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
    animal = args.animal or rng.choice(list(ANIMALS))
    juror = args.juror or rng.choice([a for a in ANIMALS if a != animal])
    supper = args.supper or rng.choice(list(SUPPERS))
    name = args.name or ANIMALS[animal]["name"]
    return StoryParams(place=place, animal=animal, juror=juror, supper=supper, name=name)


def _story_title(params: StoryParams) -> str:
    return f"{params.name} and the supper jury"


def tell(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    animal_cfg = ANIMALS[params.animal]
    juror_cfg = ANIMALS[params.juror]
    supper_phrase, supper_noun = SUPPERS[params.supper]

    hero = world.add(Entity(id="hero", kind="character", type=animal_cfg["type"], label=animal_cfg["label"]))
    juror = world.add(Entity(id="juror", kind="character", type=juror_cfg["type"], label=juror_cfg["label"]))
    bowl = world.add(Entity(id="supper", kind="thing", type=params.supper, label=params.supper, phrase=supper_phrase))
    rule = world.add(Entity(id="rule", kind="thing", type="rule", label="the jury rule", phrase="one fair share each"))

    hero.meters["hunger"] = 2.0
    hero.memes["greed"] = 1.0
    juror.memes["fairness"] = 2.0

    world.say(f"{params.name} was a little {hero.label} who was always hungry at {world.place}.")
    world.say(f"One evening, the animals put out {supper_phrase} and said it was for the jury supper.")
    world.say(f"The rule was simple: {rule.phrase}, so every animal could get a fair bite.")

    world.para()
    world.say(f"But {params.name} saw the bowl and wanted more than a fair bite.")
    hero.memes["greed"] += 1.0
    hero.meters["taken"] = 1.0
    world.say(f"{params.name} shoved close to the bowl and scooped up too much.")

    world.para()
    juror.memes["watching"] = 1.0
    world.say(f"{juror.label.capitalize()} noticed right away and called the other jury animals over.")
    world.say(f'"That is not fair," said the jury. "We need a decision before supper disappears."')
    hero.memes["embarrassment"] = 1.0

    world.para()
    world.say(f"The jury looked at the emptying bowl, then at {params.name}'s sticky paws.")
    world.say(f"They gave a bad verdict: {params.name} had to give the bowl back and wait.")
    bowl.eaten = True
    hero.meters["hunger"] += 1.0
    hero.memes["sadness"] = 2.0
    world.say(f"So the supper went to the rest of the animals, and {params.name} got none at all.")

    world.para()
    world.say(f"In the end, {supper_noun} was gone, the jury was calm, and {params.name} sat very quiet and still hungry.")
    world.facts.update(hero=hero, juror=juror, bowl=bowl, rule=rule, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short Animal Story about {p.name}, a jury, and supper.',
        f"Tell a simple story where a {p.animal} named {p.name} acts unfairly at the {p.place}, and the jury gives a bad ending.",
        f"Write a child-friendly story with the words 'supper' and 'jury' that ends with the hungry animal missing supper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    juror = world.facts["juror"]
    bowl = world.facts["bowl"]
    qas = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {p.name}, a little {hero.label} who wanted too much supper.",
        ),
        QAItem(
            question=f"What did the jury notice?",
            answer=f"The jury noticed that {p.name} was taking more than a fair share of the supper.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The jury gave a bad verdict, the supper was handed back, and {p.name} ended up hungry with no supper.",
        ),
        QAItem(
            question=f"Who watched the bowl most closely?",
            answer=f"{juror.label.capitalize()} watched the bowl closely and called the other jury animals over.",
        ),
        QAItem(
            question=f"Was the bowl still full at the end?",
            answer=f"No. The bowl was gone by the end, and the supper had been shared out.",
        ),
    ]
    if bowl.eaten:
        qas.append(QAItem(question="Did the hero get extra supper?", answer=f"No. {p.name} had to give it back and wait, so {p.name} got none at all."))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is supper?",
            answer="Supper is the evening meal, usually the food animals or people eat at the end of the day.",
        ),
        QAItem(
            question="What is a jury?",
            answer="A jury is a group that listens carefully and then makes a judgment or decision together.",
        ),
        QAItem(
            question="Why is fairness important at a meal?",
            answer="Fairness matters because everyone should get a proper share instead of one animal taking too much.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_lost_supper(H) :- took_too_much(H), jury_watched, verdict(bad).
bad_ending(H) :- hero_lost_supper(H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("jury_watched"),
        asp.fact("verdict", "bad"),
        asp.fact("took_too_much", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/1."))
    atoms = set(asp.atoms(model, "bad_ending"))
    ok = atoms == {("hero",)}
    if ok:
        print("OK: ASP gate matches the bad-ending story shape.")
        return 0
    print("MISMATCH: ASP gate did not derive the expected ending.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="barn", animal="pig", juror="hen", supper="porridge", name="Pip"),
            StoryParams(place="yard", animal="duck", juror="cow", supper="corn", name="Dot"),
            StoryParams(place="kitchen", animal="fox", juror="hen", supper="soup", name="Fin"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### {sample.params.name}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
