#!/usr/bin/env python3
"""
A child-facing cautionary mystery about a petite gardener, an ovary-shaped
seed vault, and a vote that must not disenfranchise anyone.
"""

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

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Conservatory:
    name: str
    lanterns: int
    locked: bool = False


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "moonhouse": Conservatory("the Moonhouse Conservatory", lanterns=7),
}

NAMES = ["Luna", "Mira", "Pip", "Nell", "Tavi", "Suri", "Oren", "Bee"]

CASES = [
    {
        "key": "missing_ballot",
        "premise": "the conservatory's yearly seed council was about to choose which garden would receive the moonwater",
        "object": "a petite brass ballot box shaped like an ovary",
        "clue": "a silver thread caught on the box hinge",
        "danger": "one garden might be disenfranchised if its ballot stayed hidden",
        "rhyme": "A vote in the light is a garden's right.",
        "action": "followed the silver thread beneath the potting bench",
        "resolution": "found the ballot box tucked behind a fallen tray and returned every ballot before the vote",
        "ending": "the ovary-shaped box gleamed beneath seven lanterns while every garden's card rested inside",
        "lesson": "a fair choice must make room for every voice",
    },
    {
        "key": "false_key",
        "premise": "the conservatory keeper announced a midnight vote on the safest place for the rare blue bulbs",
        "object": "a petite key with an ovary-shaped handle",
        "clue": "tiny damp footprints crossed the dust but stopped before the locked cabinet",
        "danger": "a rushed guess could disenfranchise the quiet bulb garden",
        "rhyme": "Check the track before you blame the pack.",
        "action": "held the key under a lantern and compared the footprints with the watering chart",
        "resolution": "discovered that the night moths had dragged the key ribbon, then opened the cabinet only after everyone agreed",
        "ending": "the blue bulbs shone in their safe cabinet, and the key hung where all voters could see it",
        "lesson": "evidence is kinder and safer than a hurried accusation",
    },
    {
        "key": "sealed_register",
        "premise": "each garden was meant to mark a card in the register before the storm arrived",
        "object": "a petite register clasp carved like an ovary",
        "clue": "the missing page left a clean rectangle in a layer of seed dust",
        "danger": "without the page, the smallest garden could be disenfranchised",
        "rhyme": "If a page goes astray, search the dust's trail today.",
        "action": "asked each gardener what they had seen and traced the clean rectangle to the drying rack",
        "resolution": "found the page drying beside spilled rainwater and copied the register before the ink ran",
        "ending": "the smallest garden's name stood clearly on the rescued page",
        "lesson": "protecting a small voice protects the whole community",
    },
    {
        "key": "whispering_latch",
        "premise": "a whisper came from the seed room just as the council prepared to choose a new keeper",
        "object": "a petite latch with an ovary-shaped copper plate",
        "clue": "the whisper repeated the same rhyme whenever the wind moved the roof vent",
        "danger": "the council might disenfranchise a keeper because of a frightening sound",
        "rhyme": "When hinges sing, inspect the thing.",
        "action": "stood still, listened twice, and checked the roof plan instead of opening the door in a fright",
        "resolution": "found a loose vent singing through the latch, then let every keeper speak before choosing",
        "ending": "the repaired latch clicked softly as the council welcomed its new keeper",
        "lesson": "a mystery should be investigated before it becomes a judgment",
    },
]

OPENINGS = [
    "At dusk, when the moon made silver windows on the glass,",
    "Just before the first lantern was lit,",
    "On the evening of the seed council,",
    "While rain tapped a careful rhythm on the conservatory roof,",
]

CONCERNS = [
    "Someone may be left out, and that would not be fair",
    "A quiet voice still deserves a place in the count",
    "We should solve the mystery before we choose a culprit",
    "Please let us check the clue before the vote begins",
]

REPLIES = [
    "You are right. A careful question is better than a fast guess",
    "Then we will look together and keep every garden included",
    "I nearly rushed, but the clue deserves our patience",
    "No one should lose a voice because we failed to check",
]


class World:
    def __init__(self, conservatory: Conservatory) -> None:
        self.conservatory = conservatory
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary mystery storyworld.")
    parser.add_argument("--setting", choices=SETTINGS.keys())
    parser.add_argument("--name")
    parser.add_argument("--helper")
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
    hero = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    return StoryParams(
        setting=args.setting or "moonhouse",
        hero_name=hero,
        helper_name=helper,
    )


def tell(params: StoryParams) -> World:
    template = SETTINGS[params.setting]
    conservatory = Conservatory(template.name, template.lanterns)
    world = World(conservatory)
    rng = random.Random(params.seed or 0)
    case = rng.choice(CASES)
    opening = rng.choice(OPENINGS)
    concern = rng.choice(CONCERNS)
    reply = rng.choice(REPLIES)

    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type="mole",
            label="a petite gardener",
            traits=["careful", "curious"],
            meters={"height": 0.7, "suspense": 0.0},
            memes={"courage": 1.0, "fairness": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type="robin",
            label="a watchful helper",
            traits=["patient", "bright"],
            meters={"height": 0.2, "suspense": 0.0},
            memes={"trust": 1.0, "fairness": 1.0},
        )
    )
    vault = world.add(
        Entity(
            id="seed_vault",
            kind="object",
            type="ovary-shaped vault",
            label=case["object"],
            traits=["locked", "important"],
            meters={"security": 1.0},
            memes={"shared": 1.0},
        )
    )

    hero.meters["suspense"] = 1.0
    helper.meters["suspense"] = 1.0
    conservatory.locked = True

    world.say(
        f"{opening} {hero.id}, {hero.label}, tended herbs in {conservatory.name}. "
        f"{helper.id}, {helper.label}, carried the council lantern."
    )
    world.say(f"{case['premise']}. Beside the register waited {case['object']}.")
    world.para()

    world.say(
        f"Then the important object vanished from its marked place. "
        f"{case['danger'].capitalize()} The glass roof creaked, and the lantern flames leaned toward the dark."
    )
    world.say(f"“{concern},” {hero.id} whispered.")
    world.say(
        f"“{reply},” {helper.id} answered. “What is the first clue?”"
    )
    world.say(f"They found it: {case['clue']}.")
    world.para()

    world.say(
        f"The clue made the mystery sharper, but it also gave them a path. "
        f"{hero.id} said, “{case['rhyme']}”"
    )
    world.say(
        f"Together, they {case['action']}. They did not accuse anyone, and they did not close the register."
    )
    world.say(f"At the end of the trail, they {case['resolution']}.")
    world.para()

    hero.meters["suspense"] = 0.0
    helper.meters["suspense"] = 0.0
    hero.memes["confidence"] = 1.0
    helper.memes["trust"] = 2.0
    conservatory.locked = False

    world.say(
        f"{case['ending']}. The cautionary lesson was clear: {case['lesson']}."
    )
    world.say(
        f"Because the petite gardener kept the register open, nobody was disenfranchised, "
        f"and the mystery ended with a fair count instead of a frightened guess."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        vault=vault,
        case=case,
        concern=concern,
        reply=reply,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a child-friendly mystery in which {case['premise']}.",
        f"Use suspense and rhyme while showing why {case['danger']}.",
        f"End with the cautionary lesson that {case['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} and {helper.id} investigate?",
            answer=f"They investigated why {case['object']} had vanished during the council preparations.",
        ),
        QAItem(
            question="What danger did the mystery create?",
            answer=f"{case['danger'].capitalize()} The missing item could have kept a garden from having its voice counted.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"They noticed that {case['clue']}. This clue gave them a careful path instead of a reason to accuse someone.",
        ),
        QAItem(
            question="How did the gardeners avoid disenfranchising anyone?",
            answer="They kept the register open, checked the evidence, and returned every garden's ballot or name before the vote.",
        ),
        QAItem(
            question="What cautionary lesson did the story teach?",
            answer=f"It taught that {case['lesson']}. A fair mystery-solving process protects people as well as objects.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does disenfranchise mean?",
            answer="To disenfranchise someone means to unfairly prevent that person or group from taking part in a vote or having their voice counted.",
        ),
        QAItem(
            question="What is an ovary?",
            answer="An ovary is a part of a plant or animal that helps hold or produce reproductive cells. In this story, the ovary shape is a harmless design on a seed vault.",
        ),
        QAItem(
            question="What does petite mean?",
            answer="Petite means small in size, often in a neat or delicate way. It does not mean weak or unimportant.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next, especially when a problem may become dangerous.",
        ),
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story warns readers about a risky choice and shows a wiser way to act.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(
        f"{world.conservatory.name}: locked={world.conservatory.locked}, "
        f"lanterns={world.conservatory.lanterns}"
    )
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(moonhouse).
theme(disenfranchise).
object(ovary).
trait(petite).
feature(suspense).
feature(rhyme).
feature(cautionary).
style(mystery).
safe_choice(check_evidence).
safe_choice(include_every_voice).

fair_vote :- safe_choice(check_evidence), safe_choice(include_every_voice).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("setting", "moonhouse"),
        asp.fact("theme", "disenfranchise"),
        asp.fact("object", "ovary"),
        asp.fact("trait", "petite"),
        asp.fact("feature", "suspense"),
        asp.fact("feature", "rhyme"),
        asp.fact("feature", "cautionary"),
        asp.fact("style", "mystery"),
        asp.fact("safe_choice", "check_evidence"),
        asp.fact("safe_choice", "include_every_voice"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show fair_vote/0.\n#show feature/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    features = {item[0] for item in asp.atoms(model, "feature")}
    expected = {"suspense", "rhyme", "cautionary"}
    fair = bool(asp.atoms(model, "fair_vote"))
    if features == expected and fair:
        rng = random.Random(17)
        params = StoryParams(
            setting="moonhouse",
            hero_name="Luna",
            helper_name="Mira",
            seed=17,
        )
        sample = generate(params)
        required = ["disenfranchised", "petite", "mystery", "rhyme"]
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP/Python parity and generated-story checks passed.")
            return 0
    print("Mismatch in ASP verification.")
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print(sorted(asp.atoms(model, "feature")))
        print(bool(asp.atoms(model, "fair_vote")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, case in enumerate(CASES):
            params = StoryParams(
                setting="moonhouse",
                hero_name=NAMES[index % len(NAMES)],
                helper_name=NAMES[(index + 1) % len(NAMES)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(50, target * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
