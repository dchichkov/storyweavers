#!/usr/bin/env python3
"""
A fairy-tale storyworld about a shared treat, a jar of kefir, and a hyacinth
that causes a misunderstanding before teamwork sets it right.
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
    hero: str = "Mira"
    helper: str = "Pip"
    elder: str = "Grandmother"
    creature: str = "mischievous sprite"
    place: str = "the cottage garden"
    treat: str = "honey cake"
    drink: str = "kefir"
    flower: str = "hyacinth"
    task: str = "make a treat for the spring feast"


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amt: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amt

    def add_meme(self, key: str, amt: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amt


@dataclass
class World:
    params: StoryParams
    hero: Entity
    helper: Entity
    elder: Entity
    creature: Entity
    place: str
    treat_ready: bool = False
    misunderstanding: bool = False
    teamwork: bool = False
    flower_used: bool = False
    kefir_spilled: bool = False
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world of treat, kefir, and hyacinth.")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
    ap.add_argument("--creature")
    ap.add_argument("--place")
    ap.add_argument("--treat")
    ap.add_argument("--kefir")
    ap.add_argument("--flower")
    ap.add_argument("--task")
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(["Mira", "Nina", "Tara", "Lena"]),
        helper=args.helper or rng.choice(["Pip", "Nico", "Bram", "Sera"]),
        elder=args.elder or rng.choice(["Grandmother", "Old Rowan", "Queen Elin", "the baker"]),
        creature=args.creature or rng.choice(["mischievous sprite", "small goblin", "young dragon"]),
        place=args.place or rng.choice(["the cottage garden", "the mossy well", "the moonlit kitchen"]),
        treat=args.treat or rng.choice(["honey cake", "berry tart", "sweet bun"]),
        drink=args.kefir or "kefir",
        flower=args.flower or "hyacinth",
        task=args.task or "make a treat for the spring feast",
    )


def _maybe_raise_invalid(params: StoryParams) -> None:
    bad_words = {"forbidden", "poison", "broken"}
    if params.treat.lower() in bad_words or params.drink.lower() in bad_words:
        raise StoryError("The fairy tale needs a gentle treat and a wholesome drink.")
    if not params.flower:
        raise StoryError("A hyacinth must be present for the misunderstanding to bloom.")


def _setup(world: World) -> None:
    p = world.params
    world.say(
        f"Once upon a time, {p.hero} and {p.helper} lived near {p.place}, where every "
        f"morning smelled of warm bread and clean rain."
    )
    world.say(
        f"To help {p.elder}, they wished to {p.task}, with {p.drink} and a bright {p.flower} "
        f"set upon the table."
    )
    world.say(
        f"{p.hero} loved the idea of a {p.treat}, and {p.helper} loved working side by side, "
        f"because two careful hands could do the work of four."
    )


def _misunderstanding(world: World) -> None:
    p = world.params
    world.para()
    world.misunderstanding = True
    world.creature.add_meme("curiosity", 1)
    world.elder.add_meme("worry", 1)
    world.hero.add_meme("hope", 1)
    world.say(
        f"When {p.creature} peeked through the window, it saw the {p.flower} beside the bowl "
        f"of {p.drink} and thought the special treat was for it alone."
    )
    world.say(
        f"The little creature whisked away the flower, leaving a pale spot on the cloth, and "
        f"{p.hero} feared the feast had been ruined."
    )
    world.say(
        f"{p.elder} frowned, for the missing {p.flower} looked like a sign of trouble, not a gift."
    )


def _teamwork(world: World) -> None:
    p = world.params
    world.para()
    world.teamwork = True
    world.hero.add_meme("resolve", 1)
    world.helper.add_meme("resolve", 1)
    world.say(
        f"Then {p.hero} said, '{p.helper}, let us not quarrel with guesses. We shall look, "
        f"measure, and mend together.'"
    )
    world.say(
        f"{p.helper} found the flower, {p.hero} stirred the kefir gently, and together they "
        f"wove the petals into a sweet glaze for the {p.treat}."
    )
    world.say(
        f"The creature, ashamed, helped carry nuts from the pantry, so every part of the feast "
        f"was finished by many hands instead of one."
    )


def _resolution(world: World) -> None:
    p = world.params
    world.para()
    world.treat_ready = True
    world.flower_used = True
    world.kefir_spilled = False
    world.say(
        f"By sunset, the {p.treat} shone like a tiny golden moon, jeweled with lilac {p.flower} "
        f"and softened by {p.drink}."
    )
    world.say(
        f"{p.elder} smiled, the creature bowed, and {p.hero} and {p.helper} shared the first slice "
        f"while the lanterns blinked awake."
    )
    world.say(
        f"So the misunderstanding turned into a feast, and the best part of the story was that "
        f"everyone had helped make it."
    )


def tell(params: StoryParams) -> World:
    _maybe_raise_invalid(params)
    hero = Entity(params.hero, "hero")
    helper = Entity(params.helper, "helper")
    elder = Entity(params.elder, "elder")
    creature = Entity(params.creature, "creature")
    world = World(params=params, hero=hero, helper=helper, elder=elder, creature=creature, place=params.place)
    _setup(world)
    _misunderstanding(world)
    _teamwork(world)
    _resolution(world)
    world.facts = {
        "hero": hero,
        "helper": helper,
        "elder": elder,
        "creature": creature,
        "place": params.place,
        "treat": params.treat,
        "drink": params.drink,
        "flower": params.flower,
        "misunderstanding": world.misunderstanding,
        "teamwork": world.teamwork,
        "resolved": world.treat_ready,
    }
    return world


ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
misunderstanding :- sees(creature, flower, kefir), not knows_shared_treat(creature).
teamwork :- asks_help(hero), helps(helper), mends_treat(hero, helper).
resolved :- teamwork, misunderstanding.
#show misunderstanding/0.
#show teamwork/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero_name", "Mira"),
        asp.fact("helper_name", "Pip"),
        asp.fact("sees", "creature", "flower", "kefir"),
        asp.fact("asks_help", "hero"),
        asp.fact("helps", "helper"),
        asp.fact("mends_treat", "hero", "helper"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception:
        print("ASP verification unavailable: clingo helper not installed.")
        return 1
    model = asp.one_model(asp_program("#show misunderstanding/0.\n#show teamwork/0.\n#show resolved/0."))
    atoms = {str(a) for a in model}
    expected = {"misunderstanding", "teamwork", "resolved"}
    if atoms >= expected:
        print("OK: ASP twin produces the expected fairy-tale state.")
        return 0
    print("MISMATCH: ASP twin did not reach the expected state.")
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short fairy tale about {p.hero}, {p.helper}, and a shared {p.treat}.",
        f"Tell a gentle story where {p.drink} and a {p.flower} lead to a misunderstanding, then teamwork fixes it.",
        f"Write a child-friendly story set near {p.place} that ends with everyone sharing the treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"What did {p.hero} and {p.helper} want to make?",
            answer=f"They wanted to make a {p.treat} for {p.elder}'s spring feast.",
        ),
        QAItem(
            question=f"Why did the little creature get confused?",
            answer=f"It saw the {p.flower} beside the {p.drink} and thought the special treat was only for it.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.helper} fix the trouble?",
            answer=f"They worked together, found the flower, and used it to finish the {p.treat} in a kinder way.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The misunderstanding ended, the {p.treat} was ready, and everyone shared the feast together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to do a job that is easier or better with help.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing and gets confused.",
        ),
        QAItem(
            question=f"What is kefir?",
            answer=f"Kefir is a tangy, drinkable dairy food that people can use in recipes or drink cold.",
        ),
        QAItem(
            question=f"What is a hyacinth?",
            answer=f"A hyacinth is a fragrant flower with clustered blooms, often purple, pink, or blue.",
        ),
        QAItem(
            question=f"What is a treat?",
            answer=f"A treat is a special food that feels joyful or festive, like a sweet {p.treat}.",
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
    for ent in [world.hero, world.helper, world.elder, world.creature]:
        lines.append(f"{ent.kind}: {ent.name} meters={ent.meters} memes={ent.memes}")
    lines.append(f"state: misunderstanding={world.misunderstanding} teamwork={world.teamwork} resolved={world.treat_ready}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="Mira", helper="Pip", elder="Grandmother", creature="small goblin", place="the cottage garden", treat="honey cake", drink="kefir", flower="hyacinth"),
    StoryParams(hero="Lena", helper="Bram", elder="Old Rowan", creature="mischievous sprite", place="the moonlit kitchen", treat="berry tart", drink="kefir", flower="hyacinth"),
]


def asp_verify_available() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


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
        print(asp_program("#show misunderstanding/0.\n#show teamwork/0.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        if not asp_verify_available():
            print("ASP mode unavailable: clingo is not installed.")
            return
        import asp
        model = asp.one_model(asp_program("#show misunderstanding/0.\n#show teamwork/0.\n#show resolved/0."))
        print("ASP model:", ", ".join(sorted(str(a) for a in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
