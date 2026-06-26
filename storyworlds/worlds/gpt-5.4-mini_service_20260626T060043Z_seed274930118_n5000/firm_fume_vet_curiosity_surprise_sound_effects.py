#!/usr/bin/env python3
"""
A small folk-tale storyworld about a firm shop, a curious child, a vet, and a
surprising animal rescue with sound effects.
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
    hero_name: str = "Mina"
    hero_gender: str = "girl"
    hero_trait: str = "curious"
    place: str = "the market lane"
    firm_name: str = "the old candle firm"
    vet_name: str = "Dr. Reed"
    animal: str = "goat"
    sound: str = "clip-clop"
    fume_source: str = "the little kiln"


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    vet: Entity
    animal: Entity
    firm: Entity
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

    def copy(self) -> "World":
        return World(
            params=self.params,
            hero=Entity(self.hero.name, self.hero.kind, dict(self.hero.meters), dict(self.hero.memes)),
            vet=Entity(self.vet.name, self.vet.kind, dict(self.vet.meters), dict(self.vet.memes)),
            animal=Entity(self.animal.name, self.animal.kind, dict(self.animal.meters), dict(self.animal.memes)),
            firm=Entity(self.firm.name, self.firm.kind, dict(self.firm.meters), dict(self.firm.memes)),
            paragraphs=[[]],
            facts=dict(self.facts),
        )


THRESHOLD = 1.0


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world of curiosity, surprise, and sound effects.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-trait")
    ap.add_argument("--place")
    ap.add_argument("--firm-name")
    ap.add_argument("--vet-name")
    ap.add_argument("--animal")
    ap.add_argument("--sound")
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
        seed=args.seed,
        hero_name=args.hero_name or rng.choice(["Mina", "Nora", "Tobin", "Pip"]),
        hero_gender=args.hero_gender or rng.choice(["girl", "boy"]),
        hero_trait=args.hero_trait or rng.choice(["curious", "bold", "gentle"]),
        place=args.place or rng.choice(["the market lane", "the village road", "the barn path"]),
        firm_name=args.firm_name or rng.choice(["the old candle firm", "the flour firm", "the rope firm"]),
        vet_name=args.vet_name or rng.choice(["Dr. Reed", "Vet Willow", "Old Vet Bram"]),
        animal=args.animal or rng.choice(["goat", "pony", "dog"]),
        sound=args.sound or rng.choice(["clip-clop", "thump-thump", "skitter-skip"]),
        fume_source=rng.choice(["the little kiln", "the warm oven", "the soot pot"]),
    )


def build_world(params: StoryParams) -> World:
    hero = Entity(params.hero_name, "hero", memes={"curiosity": 0.0, "surprise": 0.0})
    vet = Entity(params.vet_name, "vet", meters={"kindness": 1.0})
    animal = Entity(params.animal, "animal", meters={"ache": 1.0, "soot": 1.0})
    firm = Entity(params.firm_name, "firm", meters={"stubbornness": 1.0}, memes={"pride": 1.0})
    return World(params=params, hero=hero, vet=vet, animal=animal, firm=firm)


def predict_help(world: World) -> bool:
    sim = world.copy()
    sim.animal.meters["ache"] = max(0.0, sim.animal.meters.get("ache", 0.0) - 1.0)
    sim.firm.meters["stubbornness"] = max(0.0, sim.firm.meters.get("stubbornness", 0.0) - 1.0)
    return sim.animal.meters["ache"] < THRESHOLD


def tell_story(world: World) -> None:
    p = world.params
    she, her, hers = pronouns(p.hero_gender)

    world.say(
        f"Once, in {p.place}, there lived a {p.hero_trait} child named {p.hero_name}, "
        f"who loved to ask what, why, and how."
    )
    world.say(
        f"At the end of the lane stood {p.firm_name}, and from its little chimney drifted "
        f"a sharp fume from {p.fume_source}."
    )
    world.say(
        f"One day {p.hero_name} heard {p.sound} from behind the gate and crept nearer, "
        f"for {she} was full of curiosity."
    )
    world.say(
        f"There {she} found a {p.animal} coughing under the smoke, and the poor creature "
        f"looked small and surprised."
    )
    world.para()

    world.hero.memes["curiosity"] += 1.0
    world.hero.memes["surprise"] += 1.0
    world.facts["curious"] = True
    world.facts["sound"] = p.sound
    world.facts["animal"] = p.animal

    world.say(
        f"{p.hero_name} ran to {p.vet_name} and cried, \"Please come quick! The {p.animal} "
        f"needs help, and the smoke smells strong.\""
    )
    world.say(
        f"{p.vet_name} listened at once, because a good vet knows when a small voice tells a true thing."
    )

    if predict_help(world):
        world.say(
            f"Together they went to the firm, and {p.vet_name} told the master there to stop the fume and open the doors."
        )
        world.firm.meters["stubbornness"] = 0.0
        world.animal.meters["ache"] = 0.0
        world.hero.memes["surprise"] += 1.0
        world.say(
            f"The smoke thinned like gray thread in the wind, and the {p.animal} sighed, "
            f"\"ahhh,\" as if a heavy stone had rolled from its chest."
        )
        world.say(
            f"{p.hero_name} laughed at the sound {p.sound} made when the {p.animal} trotted away, "
            f"and {she} felt braver than before."
        )
        world.say(
            f"That evening the firm burned cleaner, the lane smelled sweet again, and {p.hero_name} "
            f"walked home with {hers} heart shining."
        )
    else:
        raise StoryError("The story setup cannot resolve because the vet would not truly help the animal.")


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    she, her, hers = pronouns(p.hero_gender)
    return [
        QAItem(
            question=f"Who was the curious child in the story?",
            answer=f"The curious child was {p.hero_name}. {she.capitalize()} loved asking questions and looking closely at things.",
        ),
        QAItem(
            question=f"What was wrong near {p.firm_name}?",
            answer=f"A sharp fume drifted from {p.fume_source}, and the smoke made the {p.animal} cough.",
        ),
        QAItem(
            question=f"Who came to help the {p.animal}?",
            answer=f"{p.vet_name} came to help, because a vet cares for animals when they are hurt or unwell.",
        ),
        QAItem(
            question=f"What sound did the child hear before finding the animal?",
            answer=f"{p.hero_name} heard {p.sound} from behind the gate before seeing the {p.animal}.",
        ),
        QAItem(
            question=f"How did {p.hero_name} feel at the end?",
            answer=f"{p.hero_name} felt brave and glad, because the smoke cleared and the {p.animal} was safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a vet do?",
            answer="A vet helps animals stay healthy, treats them when they are sick, and checks what is making them feel unwell.",
        ),
        QAItem(
            question="What is a fume?",
            answer="A fume is a strong smoke or vapor that can sting the nose and make the air unpleasant to breathe.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, which makes someone ask questions and look closely at the world.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like clip-clop or thump-thump that help readers imagine a noise.",
        ),
        QAItem(
            question="What is a firm?",
            answer="A firm is a business or shop where people make or sell things together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a folk tale about {p.hero_name}, whose curiosity leads them to a {p.firm_name} with a strange fume.",
        f"Tell a child-friendly story where a vet helps an animal after a surprising sound like {p.sound} is heard.",
        f"Create a short folk tale in which a curious child notices a problem, calls a vet, and the village feels safe again.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for x in sample.prompts:
        out.append(x)
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
    return "\n".join(
        [
            "--- trace ---",
            f"hero.curiosity={world.hero.memes.get('curiosity', 0.0)}",
            f"hero.surprise={world.hero.memes.get('surprise', 0.0)}",
            f"animal.ache={world.animal.meters.get('ache', 0.0)}",
            f"firm.stubbornness={world.firm.meters.get('stubbornness', 0.0)}",
        ]
    )


ASP_RULES = r"""
curious(hero) :- fact_curiosity.
surprised(hero) :- fact_surprise.
helped_animal :- vet_arrives, smoke_clears.
safe_end :- helped_animal, curious(hero), surprised(hero).
#show safe_end/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("fact_curiosity"),
            asp.fact("fact_surprise"),
            asp.fact("vet_arrives"),
            asp.fact("smoke_clears"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    try:
        model = asp.one_model(asp_program("#show safe_end/0."))
    except Exception as exc:
        print(f"ASP unavailable or failed: {exc}")
        return 1
    ok = any(sym.name == "safe_end" for sym in model)
    if ok:
        print("OK: ASP model includes safe_end.")
        return 0
    print("MISMATCH: ASP model did not include safe_end.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show safe_end/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(resolve_params(args, random.Random(base_seed))))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
