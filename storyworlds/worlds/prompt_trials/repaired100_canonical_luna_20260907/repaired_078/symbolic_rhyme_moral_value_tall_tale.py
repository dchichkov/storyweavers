#!/usr/bin/env python3
"""A child-facing tall tale about a symbolic rhyme and the moral value of honesty."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))
from results import QAItem, StoryError, StorySample  # noqa: E402


TITLE = "The Rhyme That Lifted the Mountain"


@dataclass(frozen=True)
class Tale:
    name: str
    task: str
    problem: str
    clue: str
    boast: str
    consequence: str
    helper: str
    plan: str
    rhyme: str
    resolution: str
    ending: str


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    hero: str = "Luna"
    place: str = "the Bell-High Valley"
    object_name: str = "the silver gate"
    seed: Optional[int] = None


HEROES = ["Luna", "Milo", "Tessa", "Jun"]
PLACES = ["the Bell-High Valley", "the upside-down hill", "the village above the clouds"]
OBJECTS = ["the silver gate", "the moon-sized pumpkin", "the bridge of blue stone"]

TALES = [
    Tale(
        "the gate that would not budge",
        "open the valley gate before sunrise",
        "the silver gate had grown as heavy as a mountain",
        "a tiny word, TRUE, was carved beneath its giant hinge",
        "claimed, 'I can lift it with one finger!'",
        "the gate answered with a mighty creak and dropped a shower of harmless golden dust",
        "a small fox named Pepper",
        "tell the truth about the failed boast, then listen for the gate's hidden rhythm",
        "Say what is true, and see it through; honest hearts can open doors for you!",
        "Luna admitted that the gate was too heavy for one finger, and the honest words matched the gate's rhythm",
        "the gate swung open so widely that morning sunlight marched through wearing a golden hat",
    ),
    Tale(
        "the pumpkin in the sky",
        "bring a moon-sized pumpkin to the harvest feast",
        "the pumpkin floated higher whenever anyone pretended it was easy",
        "three honest scratches on its stem formed a little ladder",
        "announced, 'I have carried larger pumpkins than this!'",
        "the pumpkin floated through the roof and bumped a sleepy cloud",
        "an old crow named Clack",
        "count the true scratches, name the real weight, and pull together",
        "Count what is true, pull as two; honest work will carry you!",
        "Luna named the pumpkin's true weight and the whole team pulled at the right moment",
        "the pumpkin landed at the feast and became a lantern bright enough to tickle the stars",
    ),
    Tale(
        "the blue-stone bridge",
        "repair the bridge before the village parade",
        "one enormous stone had rolled away, leaving a gap wide enough for a whale",
        "a blue feather pointed toward a smaller stone hidden under the bridge",
        "declared, 'I know every stone in this valley!'",
        "the missing stone rolled farther whenever Luna guessed instead of looking",
        "a patient giant named Bram",
        "admit what is unknown, follow the feather, and fit the stone carefully",
        "Tell what you know, seek what is new; truthful steps will carry you!",
        "Luna admitted she did not know the bridge's secret, and the feather led them to the right stone",
        "the repaired bridge held a parade so long that its last drummer arrived next Tuesday",
    ),
]


def validate(params: StoryParams) -> None:
    if params.hero not in HEROES:
        raise StoryError(f"unknown hero {params.hero!r}; choose one of {', '.join(HEROES)}")
    if params.place not in PLACES:
        raise StoryError(f"unknown place {params.place!r}; choose one of {', '.join(PLACES)}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"unknown object {params.object_name!r}; choose one of {', '.join(OBJECTS)}")


def choose_tale(params: StoryParams) -> Tale:
    seed = params.seed if params.seed is not None else 0
    return TALES[seed % len(TALES)]


def tell(params: StoryParams) -> World:
    validate(params)
    tale = choose_tale(params)
    world = World(params.place)
    hero = world.add(Entity("hero", "character", params.hero))
    symbol = world.add(Entity("symbol", "symbolic object", params.object_name))
    helper = world.add(Entity("helper", "helper", tale.helper))
    world.facts.update(tale=tale, hero=hero, symbol=symbol, helper=helper)
    world.say(
        f"In {params.place}, {params.hero} was famous for doing things so boldly that "
        "ordinary measuring sticks packed their bags and moved away."
    )
    world.say(
        f"One bright morning, {params.hero} promised to {tale.task}. "
        f"The task involved {params.object_name}, a {tale.name} that had become the valley's greatest wonder."
    )
    world.say(
        f"But {tale.problem.capitalize()}. {tale.clue.capitalize()}. "
        "That small mark was symbolic: it stood for the honest choice the task would need."
    )
    world.para()

    world.say(
        f"{params.hero} puffed up like a parade balloon and {tale.boast} "
        f'"Watch me!" {params.hero} cried.'
    )
    world.say(
        f'"Before you watch, tell me what you truly know," said {tale.helper}. '
        f'"I know that {params.object_name} is difficult," {params.hero} replied, though the words came out slowly.'
    )
    world.say(f"{tale.consequence.capitalize()}.")
    hero.memes["boast"] = 1
    symbol.meters["blocked"] = 1
    world.fired.add("boast_caused_trouble")
    world.para()

    world.say(
        f"The helper nodded. \"A tall tale may grow tall, but its heart must stand straight.\" "
        f"{tale.helper} explained the clue and helped {params.hero} make a careful plan."
    )
    world.say(f"Together, they would {tale.plan}.")
    world.say(f"They kept their courage steady with a rhyme: \"{tale.rhyme}\"")
    world.facts.update(clue=tale.clue, plan=tale.plan, rhyme=tale.rhyme)
    world.fired.add("truthful_plan_made")
    world.para()

    hero.memes["boast"] = 0
    hero.memes["honesty"] = 1
    hero.memes["moral_value"] = 1
    symbol.meters["blocked"] = 0
    symbol.meters["helped"] = 1
    world.say(f"{tale.resolution.capitalize()}.")
    world.say(
        f'"The truth did not make me smaller," said {params.hero}. '
        f'"It made my next step strong enough."'
    )
    world.say(
        f"{tale.ending.capitalize()}. The symbolic clue remained behind as a reminder: "
        "honesty is a moral value that helps courage find the right road."
    )
    world.fired.add("mission_completed")
    return world


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    return [
        f"Write a child-friendly tall tale about {world.facts['hero'].label} in {world.place}.",
        f"Use a symbolic clue, a rhyme, and the moral value of honesty to solve {tale.name}.",
        "Make the hero's enormous mistake lead to a truthful choice and a surprising ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            "What problem did the hero face?",
            f"{hero.label} had to {tale.task}, but {tale.problem}.",
        ),
        QAItem(
            "What did the symbolic clue mean?",
            f"The clue, {tale.clue}, symbolized the need to be honest instead of pretending to know everything.",
        ),
        QAItem(
            "How did the conversation change the hero's plan?",
            f"{helper.label} asked {hero.label} to say what was truly known. Then {hero.label} stopped boasting and chose to {tale.plan}.",
        ),
        QAItem(
            "What rhyme helped the team?",
            f'They used this rhyme: "{tale.rhyme}" It reminded them to use truthful, careful steps.',
        ),
        QAItem(
            "What moral value did the story show?",
            "The story showed honesty. Telling the truth helped the hero accept help and solve the enormous problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does symbolic mean?",
            "Something symbolic stands for a larger idea, such as a carved word standing for honesty.",
        ),
        QAItem(
            "What is a rhyme?",
            "A rhyme is a group of words or lines with matching sounds that can make an idea easy to remember.",
        ),
        QAItem(
            "What is a moral value?",
            "A moral value is a principle about good choices, such as honesty, kindness, or courage.",
        ),
        QAItem(
            "What is a tall tale?",
            "A tall tale is a playful story with wild exaggeration, while its characters still face a meaningful problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:8} ({entity.type:16}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("domain", "symbolic_rhyme_moral_value")]
    for hero in HEROES:
        lines.append(asp.fact("hero", hero))
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
    lines.extend(["rhyme.", "moral_value(honesty).", "symbolic_clue.", "tall_tale."])
    return "\n".join(lines)


ASP_RULES = r"""
has_lesson :- symbolic_clue, moral_value(honesty).
has_rhyme :- rhyme.
has_tall_turn :- tall_tale, has_lesson.
good_story :- has_rhyme, has_tall_turn.
#show has_lesson/0.
#show has_rhyme/0.
#show has_tall_turn/0.
#show good_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/0."))
    if asp.atoms(model, "good_story"):
        for seed in range(len(TALES)):
            sample = generate(StoryParams(seed=seed))
            if "honesty" not in sample.story.lower() or "rhyme" not in sample.story.lower():
                print("Verification failed: generated story lost its moral instruments.")
                return 1
        print("OK: ASP twin and generated stories agree.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Symbolic rhyme moral-value tall tale StoryWorld.")
    parser.add_argument("--hero", choices=HEROES, default=None)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--object", dest="object_name", choices=OBJECTS, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        seed=args.seed,
    )


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


CURATED = [
    StoryParams(hero="Luna", place="the Bell-High Valley", object_name="the silver gate", seed=0),
    StoryParams(hero="Milo", place="the upside-down hill", object_name="the moon-sized pumpkin", seed=1),
    StoryParams(hero="Tessa", place="the village above the clouds", object_name="the bridge of blue stone", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program(
            "#show has_lesson/0. #show has_rhyme/0. #show has_tall_turn/0. #show good_story/0."
        ))
        for predicate in ("has_lesson", "has_rhyme", "has_tall_turn", "good_story"):
            print(asp.atoms(model, predicate))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            local_args = args
            params = resolve_params(local_args, random.Random(seed))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} / {sample.params.place} / {sample.params.object_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
