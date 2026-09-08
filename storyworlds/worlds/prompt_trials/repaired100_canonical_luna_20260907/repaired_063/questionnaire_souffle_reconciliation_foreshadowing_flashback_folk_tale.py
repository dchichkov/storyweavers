#!/usr/bin/env python3
"""
A standalone folk tale storyworld about a questionnaire, a souffle, and a
family reconciliation remembered through a flashback.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    baker_name: str
    cousin_name: str
    village_name: str
    recipe_mode: int = 0
    question_mode: int = 0
    flashback_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str = "the village bakehouse"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting()

BAKERS = ["Luna", "Mara", "Tilda", "Anwen", "Pella"]
COUSINS = ["Oren", "Bram", "Sella", "Niko", "Eda"]
VILLAGES = ["Bellflower", "Ashgrove", "Mossbridge", "Hazelford"]

RECIPES = [
    {
        "name": "the cloud souffle",
        "ingredients": "three eggs, warm milk, honey, and a pinch of salt",
        "clue": "a blue ribbon tied around the old recipe book",
        "cause": "the recipe had been changed by both cousins long ago, but each remembered only the part the other had written",
        "image": "The souffle rose like a golden hill, and two spoons rested side by side beside it.",
        "lesson": "A shared memory can mend what a proud silence has torn.",
    },
    {
        "name": "the pear souffle",
        "ingredients": "ripe pears, eggs, cinnamon, and a little brown sugar",
        "clue": "a pear-shaped mark pressed into the flour",
        "cause": "the cousins had once baked it together, each adding a different family secret before their quarrel",
        "image": "Steam curled above the pear souffle while the cousins laughed at the flour on their noses.",
        "lesson": "The sweetest recipe is sometimes made from two forgotten truths.",
    },
    {
        "name": "the hearth souffle",
        "ingredients": "eggs, cream, chives, and cheese from the hill pasture",
        "clue": "a tiny copper bell hidden beside the whisk",
        "cause": "their grandmother had rung the bell whenever both cousins worked carefully together",
        "image": "The copper bell chimed softly as the souffle settled, warm and bright on the table.",
        "lesson": "Old kindness may wait quietly until someone asks it to return.",
    },
]

QUESTIONNAIRES = [
    "Which ingredient did you add, and which ingredient did your cousin add?",
    "What do you remember about the first souffle you made together?",
    "What would you like your cousin to understand today?",
    "Which family rule helped the souffle rise?",
]

FLASHBACKS = [
    "Luna remembered a summer morning when she and Oren were small. Their grandmother had placed one bowl between them and said, \"A good dish has room for two careful hands.\"",
    "A memory returned to Luna: rain tapped the shutters while the cousins beat eggs together. Oren had held the bowl steady, and Luna had whispered, \"We make a fine team.\"",
    "Luna saw again the old festival table. Their grandmother had cut the first souffle in two and told them, \"Never let one sharp word become a wall.\"",
]

FORESHADOWS = [
    "Before the oven was lit, the copper bell gave one faint ring, though no hand touched it.",
    "A blue ribbon fluttered from the recipe book, hinting that an old promise still waited inside.",
    "The flour formed two little hills beside the bowl, as if the kitchen itself expected two helpers.",
]

ENDINGS = [
    "That evening, the village shared the souffle, and the cousins wrote a new answer beneath every old question.",
    "From that day forward, the bakehouse kept two spoons in one cup.",
    "At the next festival, Luna and Oren entered their souffle under both names, and the village cheered.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Folk tale storyworld about reconciliation and a souffle.")
    parser.add_argument("--baker-name")
    parser.add_argument("--cousin-name")
    parser.add_argument("--village-name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    baker = args.baker_name or rng.choice(BAKERS)
    cousin = args.cousin_name or rng.choice([name for name in COUSINS if name != baker])
    village = args.village_name or rng.choice(VILLAGES)
    return StoryParams(
        baker_name=baker,
        cousin_name=cousin,
        village_name=village,
        recipe_mode=rng.randrange(len(RECIPES)),
        question_mode=rng.randrange(len(QUESTIONNAIRES)),
        flashback_mode=rng.randrange(len(FLASHBACKS)),
        ending_mode=rng.randrange(len(ENDINGS)),
    )


def _build_world(params: StoryParams) -> World:
    world = World(SETTING)
    baker = world.add(Entity("baker", "young baker", params.baker_name))
    cousin = world.add(Entity("cousin", "cousin", params.cousin_name))
    souffle = world.add(Entity("souffle", "dish", RECIPES[params.recipe_mode]["name"]))
    questionnaire = world.add(Entity("questionnaire", "questionnaire", "the reconciliation questionnaire"))
    bell = world.add(Entity("bell", "keepsake", "the copper bell"))

    baker.memes.update(pride=1, hope=0)
    cousin.memes.update(pride=1, trust=0)
    souffle.meters.update(air=0, baked=0)
    questionnaire.meters.update(answered=0)
    bell.meters["memory"] = 1

    world.facts.update(
        baker=baker,
        cousin=cousin,
        souffle=souffle,
        questionnaire=questionnaire,
        bell=bell,
        recipe=RECIPES[params.recipe_mode],
        params=params,
        reconciled=False,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    params: StoryParams = facts["params"]
    baker: Entity = facts["baker"]
    cousin: Entity = facts["cousin"]
    recipe: dict[str, str] = facts["recipe"]

    world.say(
        f"In the village of {params.village_name}, {baker.label} kept the warmest bakehouse and "
        f"{cousin.label} kept the finest whisk."
    )
    world.say(
        f"Yet the cousins had not spoken kindly for many moons, because each believed the other "
        f"had forgotten how to make {recipe['name']}."
    )
    world.say(FORESHADOWS[params.flashback_mode % len(FORESHADOWS)])

    world.para()
    world.say(
        f"One morning, {baker.label} found a questionnaire beside the mixing bowl. Its first question read, "
        f"\"{QUESTIONNAIRES[params.question_mode % len(QUESTIONNAIRES)]}\""
    )
    world.say(
        f"{cousin.label} stepped into the bakehouse. \"I thought you would bake without me,\" said {cousin.label}."
    )
    world.say(
        f"\"I thought you wanted the recipe for yourself,\" answered {baker.label}. "
        f"Then {baker.label} pushed the questionnaire across the table."
    )
    world.say(
        f"{cousin.label} read the next question aloud: \"What would you like your cousin to understand today?\""
    )
    world.say(
        f"\"That I was hurt,\" said {baker.label}. \"And that I am sorry,\" said {cousin.label}."
    )

    world.para()
    world.say(FLASHBACKS[params.flashback_mode % len(FLASHBACKS)])
    world.say(
        f"The flashback showed them the clue they had missed: {recipe['clue']}. "
        f"It reminded them that {recipe['cause']}."
    )
    world.say(
        f"Together they answered the questionnaire. {baker.label} measured {recipe['ingredients']}, "
        f"while {cousin.label} folded the whites slowly, as the old family rule required."
    )
    world.say(
        f"\"Will you trust me with the bowl?\" asked {cousin.label}. "
        f"\"Yes,\" said {baker.label}. \"And will you trust me with the oven?\" "
        f"\"Yes,\" said {cousin.label}."
    )

    world.para()
    world.say(
        f"The souffle rose. The cousins watched through the oven window instead of blaming one another."
    )
    world.say(
        f"When the timer rang, they lifted out {recipe['name']}, golden and trembling but whole."
    )
    world.say(
        f"They shared a spoonful. The questionnaire was complete, and their reconciliation was no longer "
        f"just a promise but something warm they had made together."
    )
    world.say(recipe["image"])
    world.say(ENDINGS[params.ending_mode % len(ENDINGS)])
    world.say(f"The cousins remembered the lesson: {recipe['lesson']}")

    baker.memes["hope"] = 1
    cousin.memes["trust"] = 1
    souffle.meters["air"] = 1
    souffle.meters["baked"] = 1
    facts["questionnaire"].meters["answered"] = 1
    facts["reconciled"] = True


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    return [
        f"Write a child-friendly folk tale in the village of {params.village_name} about a questionnaire and a souffle.",
        f"Tell a reconciliation story between {params.baker_name} and {params.cousin_name} using a foreshadowed clue and a flashback.",
        "Write a warm folk tale in which answering questions changes what two relatives decide to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    params: StoryParams = facts["params"]
    recipe: dict[str, str] = facts["recipe"]
    return [
        QAItem(
            question=f"Why had {params.baker_name} and {params.cousin_name} stopped speaking kindly?",
            answer=f"They each believed the other had forgotten how to make {recipe['name']}.",
        ),
        QAItem(
            question="What did the questionnaire help the cousins do?",
            answer="It helped them say what had hurt them, listen to each other, and remember how they had once worked together.",
        ),
        QAItem(
            question="What did the flashback reveal?",
            answer=f"It revealed that {recipe['cause']}.",
        ),
        QAItem(
            question="What clue was foreshadowed before the baking began?",
            answer=f"The clue was {recipe['clue']}.",
        ),
        QAItem(
            question="How did the cousins make the souffle?",
            answer=f"They shared the work: one measured {recipe['ingredients']}, and the other folded the whites slowly before they baked the souffle together.",
        ),
        QAItem(
            question="How was the reconciliation shown at the end?",
            answer="The cousins trusted each other with the bowl and oven, shared the finished souffle, and kept working together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a questionnaire?",
            answer="A questionnaire is a set of questions used to gather answers, feelings, or information.",
        ),
        QAItem(
            question="What is a souffle?",
            answer="A souffle is a light baked dish that rises because air is held in its mixture.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of repairing a relationship after people have been hurt or disagreed.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint early in a story about something that will matter later.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that returns to an earlier event or memory.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id:14} ({entity.type:16}) meters={meters} memes={memes}")
    lines.append(f"  reconciled: {world.facts['reconciled']}")
    return "\n".join(lines)


ASP_RULES = r"""
answered(questionnaire) :- questionnaire_ready, conversation.
risen(souffle) :- shared_work, careful_folding.
reconciled(cousins) :- answered(questionnaire), risen(souffle), apology, trust.
good_story :- reconciled(cousins).
#show good_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("questionnaire_ready"),
            asp.fact("conversation"),
            asp.fact("shared_work"),
            asp.fact("careful_folding"),
            asp.fact("apology"),
            asp.fact("trust"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    if any(symbol.name == "good_story" for symbol in model):
        return 0
    print("MISMATCH: ASP twin did not derive a reconciled story.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
    StoryParams("Luna", "Oren", "Bellflower", 0, 0, 0, 0),
    StoryParams("Mara", "Bram", "Ashgrove", 1, 1, 1, 1),
    StoryParams("Tilda", "Sella", "Mossbridge", 2, 2, 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("good_story" if any(symbol.name == "good_story" for symbol in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
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
            header = f"### {sample.params.baker_name} and {sample.params.cousin_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
