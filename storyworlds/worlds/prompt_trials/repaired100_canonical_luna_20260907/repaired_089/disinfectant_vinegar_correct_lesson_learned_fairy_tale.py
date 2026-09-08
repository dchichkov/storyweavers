#!/usr/bin/env python3
"""
Storyworld: disinfectant_vinegar_correct_lesson_learned_fairy_tale

A gentle fairy tale about a little helper who learns that vinegar and
disinfectant are useful for different jobs, and that the correct choice
matters.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Creature:
    id: str
    name: str
    kind: str
    role: str
    home: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"care": 0.0, "risk": 0.0, "knowledge": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"worry": 0.0, "relief": 0.0, "pride": 0.0}
    )


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    purpose: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"cleanliness": 0.0, "safety": 0.0, "risk": 0.0}
    )


@dataclass
class StoryParams:
    hero_name: str
    fairy_name: str
    home: str
    place: str
    task: str
    object_name: str
    telling_mode: str = "moonlit"
    seed: Optional[int] = None


HERO_NAMES = ("Luna", "Pippa", "Mira", "Tilly", "Nell")
FAIRY_NAMES = ("Fennel", "Rosemary", "Clover", "Marigold", "Briar")
HOMES = ("a blue-roofed cottage", "a little tower beside the brook", "a mossy cottage")
PLACES = ("the Moonbeam Kingdom", "the Cloverwood", "the valley of Silver Bells")
TASKS = (
    "prepare the palace kitchen for the Lantern Feast",
    "restore the glass bridge before the royal parade",
    "clean the wishing well before the village children arrived",
)
OBJECTS = (
    "the silver feast table",
    "the crystal bridge rail",
    "the old wishing-well stones",
)
TELLING_MODES = (
    "moonlit",
    "warning-first",
    "question",
    "festival",
    "rainy",
    "quiet",
)
TOOLS = (
    "a soft cloth",
    "a wooden brush",
    "a little bucket of warm water",
)
INVALID_WORDS = {"bleach", "ammonia", "mix", "mixed", "mixing"}


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.creatures: dict[str, Creature] = {}
        self.things: dict[str, Thing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


def validate_params(params: StoryParams) -> None:
    if not params.hero_name.strip():
        raise StoryError("hero_name must not be empty.")
    if not params.fairy_name.strip():
        raise StoryError("fairy_name must not be empty.")
    if params.hero_name.casefold() == params.fairy_name.casefold():
        raise StoryError("hero_name and fairy_name must be different characters.")
    if any(word in params.task.casefold().split() for word in INVALID_WORDS):
        raise StoryError("The story cannot ask characters to mix unsafe cleaners.")
    if not params.place.strip():
        raise StoryError("place must not be empty.")
    if not params.object_name.strip():
        raise StoryError("object_name must not be empty.")
    if params.telling_mode not in TELLING_MODES:
        raise StoryError(f"Unknown telling_mode: {params.telling_mode}")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    hero = Creature("hero", params.hero_name, "young fairy", "eager helper", params.home)
    mentor = Creature("mentor", params.fairy_name, "elder fairy", "wise guide", params.home)
    vinegar = Thing(
        "vinegar",
        "vinegar",
        "cleaning liquid",
        "loosening mineral marks and food stains from washable surfaces",
    )
    disinfectant = Thing(
        "disinfectant",
        "disinfectant",
        "cleaning liquid",
        "killing germs on a suitable hard surface when used as its label directs",
    )
    cloth = Thing("cloth", "a soft cloth", "tool", "wiping a cleaned surface")
    target = Thing(
        "target",
        params.object_name,
        "fairy-tale surface",
        "the surface waiting to be cleaned",
    )

    world.creatures[hero.id] = hero
    world.creatures[mentor.id] = mentor
    world.things[thing.id] = thing
    world.things[disinfectant.id] = disinfectant
    world.things[cloth.id] = cloth
    world.things[target.id] = target

    openings = {
        "moonlit": (
            f"On a moonlit evening in {params.place}, {params.hero_name} lived in "
            f"{params.home} and dreamed of helping with a royal task."
        ),
        "warning-first": (
            f'"Read every label," said {params.fairy_name} beneath the stars in '
            f"{params.place}, where {params.hero_name} lived in {params.home}."
        ),
        "question": (
            f'"Can I help?" asked {params.hero_name} in {params.place}, where '
            f"the bells were calling everyone toward the evening task."
        ),
        "festival": (
            f"Before the great festival began in {params.place}, {params.hero_name} "
            f"hurried from {params.home} to offer a helping hand."
        ),
        "rainy": (
            f"Rain tapped the windows of {params.home} while, in {params.place}, "
            f"a royal cleaning task waited."
        ),
        "quiet": (
            f"In the quiet before dawn, {params.hero_name} noticed a dull mark "
            f"shining like a tiny cloud in {params.place}."
        ),
    }
    world.say(openings[params.telling_mode])
    world.say(f"The assignment was to {params.task}, and the part before {params.hero_name} was {params.object_name}.")
    world.say(
        f"A bottle of vinegar stood beside a bottle of disinfectant, while {params.fairy_name} "
        f"laid out {random.Random((params.seed or 0) ^ 17).choice(TOOLS)}."
    )
    world.say(
        f"{params.hero_name} wanted to choose quickly, for the Lantern Feast would begin when the first star appeared."
    )
    world.para()

    hero.meters["risk"] += 1.0
    hero.memes["worry"] += 1.0
    target.meters["risk"] += 1.0
    world.say(f'"I will pour the vinegar over everything," {params.hero_name} announced.')
    world.say(
        f'{params.fairy_name} gently stopped the hand. "That would not be the correct choice for every job. '
        f"Vinegar can help loosen some marks, but disinfectant has a different purpose. Never mix cleaners, "
        f'and always follow the label."'
    )
    world.say(
        f"{params.hero_name} looked closely. The dull mark was harmless mineral dust, but the places touched "
        f"by many guests needed careful disinfecting afterward."
    )
    world.say(
        f'"So the correct cleaner depends on what needs doing?" {params.hero_name} asked. '
        f'"That is the beginning of wisdom," replied {params.fairy_name}.'
    )
    hero.meters["knowledge"] += 1.0
    mentor.meters["knowledge"] += 1.0
    world.para()

    world.say(
        f"First, {params.hero_name} used a little vinegar on the washable mineral mark, waited as the label "
        f"directed, and wiped it with a soft cloth."
    )
    world.say(
        f"Then {params.fairy_name} showed the young helper how to apply disinfectant to the suitable hard "
        f"surface, giving it the label's proper time to work."
    )
    world.say(
        f"They opened a window, kept the bottles apart, and washed their hands when the cleaning was done."
    )
    world.say(
        f'"Vinegar for this mark, disinfectant for that cleanable surface, and never a secret mixture," '
        f"{params.hero_name} repeated."
    )
    hero.meters["care"] += 2.0
    mentor.meters["care"] += 1.0
    vinegar.meters["cleanliness"] += 1.0
    disinfectant.meters["safety"] += 1.0
    world.para()

    hero.memes["relief"] += 1.0
    hero.memes["pride"] += 1.0
    mentor.memes["pride"] += 1.0
    target.meters["risk"] = 0.0
    world.say(
        f"The plan worked: {params.object_name} gleamed, and the busy places were ready for the feast."
    )
    world.say(
        f"When the first lantern rose, {params.hero_name} explained the lesson to the other young fairies: "
        f"the strongest-looking bottle is not always the correct answer."
    )
    world.say(
        f'"I learned to pause, read, and choose," said {params.hero_name}. '
        f'"And to ask when I am unsure," added {params.fairy_name}.'
    )
    world.say(
        f"That night, the fairies danced beneath golden lights, while the two bottles rested safely apart "
        f"on their marked shelf."
    )
    world.say(
        f"The lesson learned in {params.place} was simple: careful knowledge makes a small helper truly brave."
    )

    world.facts.update(
        hero=hero,
        mentor=mentor,
        vinegar=vinegar,
        disinfectant=disinfectant,
        cloth=cloth,
        target=target,
        correct_choice="use vinegar only for the suitable washable mark and disinfectant only for a suitable hard surface as its label directs",
        first_mistake="pour vinegar over everything",
        clue="the dull mark was mineral dust while high-touch places needed disinfecting",
        safe_plan="read each label, keep cleaners apart, use the correct cleaner for the correct job, and ask an adult when unsure",
        result=f"{params.object_name} gleamed and the busy places were ready for the feast",
        lesson="pause, read, choose correctly, never mix cleaners, and ask when unsure",
        place=params.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Creature = f["hero"]
    return [
        f"Write a fairy tale about {hero.name} learning to choose between vinegar and disinfectant.",
        f"Tell a gentle lesson-learned story in which {hero.name} discovers that the correct cleaner depends on the job.",
        f"Write a child-facing fairy tale where cleaners are kept apart and a wise helper explains why labels matter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Creature = f["hero"]
    mentor: Creature = f["mentor"]
    target: Thing = f["target"]
    return [
        QAItem(
            question=f"What did {hero.name} first want to do?",
            answer=f"{hero.name} first wanted to {f['first_mistake']}. That was too broad a plan because different cleaners have different purposes.",
        ),
        QAItem(
            question=f"What clue helped {hero.name} choose correctly?",
            answer=f"{hero.name} noticed that {f['clue']}. This showed that the correct cleaner depended on the kind of mark and the surface.",
        ),
        QAItem(
            question=f"How were vinegar and disinfectant used?",
            answer=f"Vinegar was used for the suitable washable mineral mark, while disinfectant was used on a suitable hard surface according to its label. The bottles were never mixed.",
        ),
        QAItem(
            question=f"What did {hero.name} learn from {mentor.name}?",
            answer=f"{hero.name} learned to {f['lesson']}. The lesson made the young helper calmer and safer.",
        ),
        QAItem(
            question="What final image shows that the problem was solved?",
            answer=f"The final image shows that {target.label} gleamed and the busy places were ready for the feast, while the two bottles rested safely apart on their marked shelf.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is disinfectant?",
            answer="Disinfectant is a product intended to kill germs on suitable surfaces when it is used exactly as its label directs.",
        ),
        QAItem(
            question="What is vinegar useful for in this story?",
            answer="Vinegar is used for a suitable washable mark, such as mineral dust, when the surface and directions allow it.",
        ),
        QAItem(
            question="Why should cleaners never be mixed?",
            answer="Cleaners should never be mixed because combining products can create dangerous fumes or other unsafe reactions.",
        ),
        QAItem(
            question="What does correct mean?",
            answer="Correct means right for the particular situation, purpose, or instructions.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is an important idea someone understands after noticing what worked, what was risky, and what should be done next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    for creature in world.creatures.values():
        lines.append(
            f"{creature.id}: kind={creature.kind} role={creature.role} "
            f"meters={dict(creature.meters)} memes={dict(creature.memes)}"
        )
    for thing in world.things.values():
        lines.append(
            f"{thing.id}: label={thing.label} purpose={thing.purpose} "
            f"meters={dict(thing.meters)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% The fairy-tale lesson is complete when the helper understands purpose,
% keeps cleaners apart, and follows directions.
lesson_learned(S) :-
    story(S),
    understands_purpose(S),
    cleaners_separate(S),
    follows_label(S),
    correct_choice(S).

safe_cleaning(S) :-
    story(S),
    vinegar_for_mark(S),
    disinfectant_for_surface(S),
    cleaners_separate(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp

    return "\n".join(
        [
            asp.fact("story", "s1"),
            asp.fact("understands_purpose", "s1"),
            asp.fact("cleaners_separate", "s1"),
            asp.fact("follows_label", "s1"),
            asp.fact("correct_choice", "s1"),
            asp.fact("vinegar_for_mark", "s1"),
            asp.fact("disinfectant_for_surface", "s1"),
        ]
    )


def asp_program() -> str:
    params = StoryParams(
        hero_name="Luna",
        fairy_name="Clover",
        home="a blue-roofed cottage",
        place="the Moonbeam Kingdom",
        task="prepare the palace kitchen for the Lantern Feast",
        object_name="the silver feast table",
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show lesson_learned/1.\n#show safe_cleaning/1.\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    learned = set(asp.atoms(model, "lesson_learned"))
    safe = set(asp.atoms(model, "safe_cleaning"))
    if learned == {("s1",)} and safe == {("s1",)}:
        print("OK: ASP gate matches the lesson-learned cleaning pattern.")
        return 0
    print("MISMATCH: ASP did not recognize the safe, correct cleaning plan.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale world about vinegar, disinfectant, and choosing correctly."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--fairy-name")
    parser.add_argument("--home")
    parser.add_argument("--place")
    parser.add_argument("--task")
    parser.add_argument("--object-name")
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        fairy_name=args.fairy_name or rng.choice(FAIRY_NAMES),
        home=args.home or rng.choice(HOMES),
        place=args.place or rng.choice(PLACES),
        task=args.task or rng.choice(TASKS),
        object_name=args.object_name or rng.choice(OBJECTS),
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        hero_name="Luna",
        fairy_name="Clover",
        home="a blue-roofed cottage",
        place="the Moonbeam Kingdom",
        task="prepare the palace kitchen for the Lantern Feast",
        object_name="the silver feast table",
        telling_mode="moonlit",
    ),
    StoryParams(
        hero_name="Mira",
        fairy_name="Rosemary",
        home="a little tower beside the brook",
        place="the Cloverwood",
        task="restore the glass bridge before the royal parade",
        object_name="the crystal bridge rail",
        telling_mode="warning-first",
    ),
    StoryParams(
        hero_name="Pippa",
        fairy_name="Marigold",
        home="a mossy cottage",
        place="the valley of Silver Bells",
        task="clean the wishing well before the village children arrived",
        object_name="the old wishing-well stones",
        telling_mode="question",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        exit_code = asp_verify()
        if exit_code:
            sys.exit(exit_code)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or len(sample.story_qa) < 3:
                print("MISMATCH: generated story exercise failed.")
                sys.exit(1)
        print("OK: generated stories pass the Python exercise.")
        return

    if args.asp:
        import asp

        print(asp.one_model(asp_program()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = []
        for index, original in enumerate(CURATED):
            params = StoryParams(**vars(original))
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
