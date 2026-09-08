#!/usr/bin/env python3
"""
A child-safe detective storyworld about a fry, a tavern, a misunderstanding,
and the careful problem solving that clears it up.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    opening: str
    clue: str
    misunderstanding: str
    question: str
    first_plan: str
    problem: str
    dialogue: str
    method: str
    discovery: str
    proof: str
    ending: str
    lesson: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "fry_tavern": Setting(
        place="the Lantern Fry Tavern",
        affords={"serve_fry", "solve_cases"},
    )
}

ACTIVITIES = {
    "serve_fry": "serve a hot fry",
    "solve_cases": "solve a tavern mystery",
}

PRIZES = {
    "missing_fry": "the missing golden fry",
}

DETECTIVES = [
    ("Luna", "mouse"),
    ("Milo", "sparrow"),
    ("Pip", "kitten"),
    ("Nell", "fox"),
    ("Tavi", "badger"),
]

TRAITS = ["curious", "patient", "sharp-eyed", "thoughtful", "brave"]

TELLINGS = [
    "clue_first",
    "question_turn",
    "dialogue_first",
    "quiet_build",
    "evidence_turn",
]

CASES = {
    item.id: item
    for item in [
        Case(
            id="bell_board",
            opening="At closing time, the tavern cook found one golden fry missing from a blue plate beside the bell board.",
            clue="Luna noticed a stripe of salt running from the plate toward the bell rope, but the rope itself had not moved.",
            misunderstanding="The cook thought the quiet dishwasher had taken the fry and hidden it.",
            question="Why would a thief leave a straight trail of salt and never ring the bell?",
            first_plan="Luna wanted to search the dishwasher's apron at once.",
            problem="That plan might blame an innocent helper and still miss the real trail.",
            dialogue='"I did not take it," said Bex the dishwasher. "Then show me what you noticed," Luna replied.',
            method="Luna placed clean crumbs near the plate, watched the floor from both sides, and compared the salt marks with the wheel tracks of the serving cart.",
            discovery="The cart had bumped the plate, and a small draft had carried the fry beneath the bell board.",
            proof="When Luna pulled the loose board gently, the missing fry rolled out beside a silver spoon.",
            ending="The cook apologized to Bex, then set the recovered fry on a fresh plate for the last hungry guest.",
            lesson="A good detective checks evidence before choosing someone to blame.",
        ),
        Case(
            id="red_apron",
            opening="One warm evening, the tavern owner heard that a red-aproned visitor had stolen the largest fry from the counter.",
            clue="Luna found red flour dust on the counter, but the visitor's apron was clean and folded on a chair.",
            misunderstanding="Everyone assumed the visitor had changed clothes to hide the theft.",
            question="Could the red mark have come from somewhere other than an apron?",
            first_plan="Luna began to follow the visitor toward the door.",
            problem="Following first would let the real clue grow cold.",
            dialogue='"Please wait," said Luna. "I may have the wrong idea." The visitor answered, "I saw a red parrot near the counter."',
            method="Luna measured the little red marks, checked the counter edge, and asked the kitchen helper to repeat the serving path slowly.",
            discovery="A red flour bag had brushed the counter, and the parrot had carried the fry beneath a napkin.",
            proof="The napkin lifted to reveal the fry beside three bright feathers.",
            ending="The visitor returned to the table, and the parrot received a safe seed treat instead of a salty snack.",
            lesson="A clue may point to a place, not a person.",
        ),
        Case(
            id="empty_basket",
            opening="Before supper, a basket marked FRIES stood empty in the tavern pantry.",
            clue="Luna saw that the basket's handle was greasy on one side and dusty on the other.",
            misunderstanding="The pantry keeper thought a hungry customer had carried away the whole basket.",
            question="How could a full basket leave only one kind of mark?",
            first_plan="Luna planned to question every customer in a noisy line.",
            problem="A noisy search could cover the faint marks on the floor.",
            dialogue='"Let us listen to the floor first," said Luna. "The floor cannot change its story," agreed the pantry keeper.',
            method="Luna closed the pantry, sprinkled harmless flour along the clean path, and followed the handle's turning marks.",
            discovery="A loose pantry wheel had dragged the basket behind the curtain, where the missing fry had slipped out.",
            proof="The wheel stopped beside one golden fry resting in a fold of the curtain.",
            ending="The pantry keeper fixed the wheel, and the basket returned to its shelf with a bright new label.",
            lesson="Careful questions and quiet observation solve more than a hurried crowd.",
        ),
        Case(
            id="window_shadow",
            opening="A long shadow crossed the tavern counter just as a single fry disappeared from a warm dish.",
            clue="The shadow moved upward, while the fry's paper wrapper had fallen downward.",
            misunderstanding="The guests suspected a tall customer standing near the window.",
            question="What could move the shadow and drop the wrapper in opposite directions?",
            first_plan="Luna wanted to inspect the tallest guest's coat.",
            problem="A coat could hide a wrapper, but it could not explain the moving shadow.",
            dialogue='"Look above the counter," Luna said. "There is a sign swinging there," answered the tall guest.',
            method="Luna watched the window, the sign, and the dish together while the tavern keeper opened and closed the door once.",
            discovery="The door draft swung the sign, while a small cat had nudged the dish from below.",
            proof="The cat's pawprint appeared beside the wrapper, and the fry was found under a clean stool.",
            ending="The tall guest laughed with relief, and the cat was offered a safe bowl of water.",
            lesson="When clues seem to disagree, test whether two different causes are at work.",
        ),
        Case(
            id="silent_chime",
            opening="The tavern's little service chime rang once, but no waiter stood near it when a fry vanished.",
            clue="Luna found a thread of blue wool caught under the chime's base.",
            misunderstanding="The cook suspected the blue-scarf musician who had just left.",
            question="Did the wool prove that the musician had taken the fry?",
            first_plan="Luna hurried toward the door to question the musician.",
            problem="The musician might leave for good before the rest of the evidence was checked.",
            dialogue='"The blue thread is a clue, not a verdict," Luna told the cook. "Then let us inspect the base," said the cook.',
            method="Luna lifted the chime with the cook, checked the table legs, and traced the thread without pulling it loose.",
            discovery="A blue cleaning cloth had caught on the chime, and its corner had nudged the fry onto a lower shelf.",
            proof="The fry rested on the shelf beside the cloth and a dust-free line.",
            ending="The cook sent a kind message to the musician, and the chime was moved away from the cloth basket.",
            lesson="One clue should invite another question, not end the investigation.",
        ),
        Case(
            id="two_receipts",
            opening="Two customers claimed the same last fry because each held a receipt with a matching number.",
            clue="Luna noticed that one receipt was warm and the other was folded around a cold spoon.",
            misunderstanding="The tavern keeper thought one customer had copied the other's receipt.",
            question="Why did the receipts feel different if they named the same order?",
            first_plan="Luna wanted to choose the customer who spoke first.",
            problem="Choosing by speed would turn a misunderstanding into an unfair decision.",
            dialogue='"Tell me what happened in order," Luna said. "I placed my receipt beside the spoon," said one customer.',
            method="Luna rebuilt the serving order, checked the counter bell, and matched each receipt to the time marks on the kitchen slate.",
            discovery="The bell had stuck, so one receipt was printed early while the fry remained in the kitchen.",
            proof="The kitchen slate showed that the folded receipt belonged to the next order, not the missing fry.",
            ending="The right customer received the fry, and the other received a fresh one from the next basket.",
            lesson="Fair problem solving means checking timing as well as words.",
        ),
    ]
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    trait: str
    scenario: str = ""
    telling: str = ""
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detective stories about a fry, a tavern, and a solved misunderstanding."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--prize", choices=PRIZES)
    parser.add_argument("--name")
    parser.add_argument("--animal", choices=[animal for _, animal in DETECTIVES])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--scenario", choices=CASES)
    parser.add_argument("--telling", choices=TELLINGS)
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


def _opening_text(
    world: World,
    hero: Entity,
    trait: str,
    telling: str,
    case: Case,
    rng: random.Random,
) -> None:
    openers = [
        "Rain tapped the windows of the Lantern Fry Tavern.",
        "The Lantern Fry Tavern smelled of warm potatoes and clean tables.",
        "Evening lamps glowed over the small Lantern Fry Tavern.",
        "The tavern was nearly quiet when the mystery began.",
    ]
    opener = rng.choice(openers)
    if telling == "question_turn":
        world.say(f"{opener} {hero.id}, a {trait} {hero.type}, asked, \"What happened here?\"")
    elif telling == "dialogue_first":
        world.say(f'"A fry is missing," whispered someone in the {world.setting.place}.')
        world.say(f"{opener} {hero.id}, a {trait} {hero.type}, came closer.")
    elif telling == "quiet_build":
        world.say(f"{opener} {hero.id}, a {trait} {hero.type}, watched the last customers leave.")
    elif telling == "evidence_turn":
        world.say(f"{opener} {hero.id}, a {trait} {hero.type}, noticed a tiny mark before anyone shouted.")
    else:
        world.say(f"{opener} {hero.id}, a {trait} {hero.type}, was the tavern's careful little detective.")
    world.say(case.opening)


def tell(
    params: StoryParams,
    rng: random.Random,
) -> World:
    setting = SETTINGS[params.place]
    case = CASES[params.scenario]
    world = World(setting)
    hero = world.add(Entity(params.name, "character", params.animal))
    tavern = world.add(Entity("lantern_tavern", "place", "tavern", label=setting.place))
    fry = world.add(Entity("missing_fry", "thing", "fry", label="the missing golden fry"))
    cook = world.add(Entity("cook", "character", "cook"))
    hero.memes.update(curiosity=1.0, careful_reasoning=1.0)
    fry.meters.update(missing=1.0, importance=1.0)
    tavern.meters["busy"] = 0.5

    _opening_text(world, hero, params.trait, params.telling, case, rng)
    world.facts.update(case=case, hero=hero, fry=fry, tavern=tavern, cook=cook)
    world.para()

    if params.telling in {"clue_first", "evidence_turn"}:
        world.say(case.clue)
        world.say(case.misunderstanding)
        world.say(case.question)
    else:
        world.say(case.misunderstanding)
        world.say(case.question)
        world.say(case.clue)
    world.facts["misunderstanding"] = True
    world.say(f"{hero.id} knew that a misunderstanding was not the same as proof.")
    world.para()

    world.say(case.first_plan)
    world.say(case.problem)
    world.say(case.dialogue)
    world.facts["first_plan_checked"] = True
    world.fired.add("misunderstanding_paused")
    world.para()

    world.say(f"{hero.id} began solving the problem step by step. {case.method}")
    world.say(case.discovery)
    world.facts["cause_found"] = True
    world.para()

    world.say(case.proof)
    fry.meters["missing"] = 0.0
    world.facts["resolved"] = True
    world.fired.add("fry_recovered")
    world.say(case.ending)
    world.say(f"{hero.id} carried this lesson past the tavern door: {case.lesson}")
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a child-safe detective story in a tavern where {hero.id} investigates a missing fry.",
        f"Tell a story about a misunderstanding that {hero.id} solves by checking clues instead of blaming someone.",
        f"Write a gentle problem-solving mystery using this clue: {case.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Who investigated the missing fry at the tavern?",
            f"{hero.id}, a careful {hero.type}, investigated the missing fry.",
        ),
        QAItem(
            "What misunderstanding began the case?",
            case.misunderstanding,
        ),
        QAItem(
            "What clue helped the detective question the first idea?",
            case.clue,
        ),
        QAItem(
            "How did the detective solve the problem?",
            case.method,
        ),
        QAItem(
            "What proved where the fry was?",
            case.proof,
        ),
        QAItem(
            "What lesson did the detective learn?",
            case.lesson,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a tavern?",
            "A tavern is a place where people can gather for food and drink.",
        ),
        QAItem(
            "What is a fry?",
            "A fry is a thin piece of food, often made from potato and cooked until warm and crisp.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone interprets a person or event incorrectly.",
        ),
        QAItem(
            "What is problem solving?",
            "Problem solving means noticing a difficulty, checking useful information, and choosing a careful way to improve the situation.",
        ),
        QAItem(
            "Why should a detective check evidence before blaming someone?",
            "Checking evidence helps separate what really happened from an unfair guess.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:16} ({entity.type:8}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
fry(F) :- prize(F), missing(F).
misunderstanding :- accusation, not evidence_checked.
solved(F) :- fry(F), missing(F), clue_checked, cause_found, recovered(F).
clear_case :- misunderstanding, evidence_checked, cause_found.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("setting", "fry_tavern"),
        asp.fact("affords", "fry_tavern", "serve_fry"),
        asp.fact("affords", "fry_tavern", "solve_cases"),
        asp.fact("prize", "missing_fry"),
        asp.fact("fry", "missing_fry"),
        asp.fact("missing", "missing_fry"),
        asp.fact("accusation"),
        asp.fact("clue_checked"),
        asp.fact("evidence_checked"),
        asp.fact("cause_found"),
        asp.fact("recovered", "missing_fry"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_triples() -> list[tuple[str, str, str]]:
    return [("fry_tavern", "solve_cases", "missing_fry")]


def asp_valid_results() -> list[tuple]:
    import asp

    model = asp.one_model(
        asp_program("#show solved/1.\n#show clear_case/0.")
    )
    return sorted(
        set(asp.atoms(model, "solved") + asp.atoms(model, "clear_case"))
    )


def asp_verify() -> int:
    expected = {("missing_fry",), ()}
    actual = set(asp_valid_results())
    if expected.issubset(actual) and valid_story_triples():
        print("OK: ASP and Python both describe a recoverable fry mystery.")
        return 0
    print(f"MISMATCH: expected {sorted(expected)}, got {sorted(actual)}.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "fry_tavern":
        raise StoryError("This detective world takes place only in the Lantern Fry Tavern.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("That activity is not available in the tavern.")
    if args.prize and args.prize != "missing_fry":
        raise StoryError("This world investigates the missing fry.")
    if args.name is None and args.animal is None:
        name, animal = rng.choice(DETECTIVES)
    elif args.name is not None and args.animal is None:
        name = args.name
        animal = next(
            (known_animal for known_name, known_animal in DETECTIVES if known_name == name),
            rng.choice(DETECTIVES)[1],
        )
    elif args.name is None:
        animal = args.animal
        name = next(
            (known_name for known_name, known_animal in DETECTIVES if known_animal == animal),
            rng.choice(DETECTIVES)[0],
        )
    else:
        name, animal = args.name, args.animal
    return StoryParams(
        place="fry_tavern",
        activity=args.activity or rng.choice(sorted(ACTIVITIES)),
        prize="missing_fry",
        name=name,
        animal=animal,
        trait=args.trait or rng.choice(TRAITS),
        scenario=args.scenario or rng.choice(sorted(CASES)),
        telling=args.telling or rng.choice(TELLINGS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.place}.")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {params.activity}.")
    if params.prize not in PRIZES:
        raise StoryError(f"Unknown prize: {params.prize}.")
    if params.scenario not in CASES:
        raise StoryError(f"Unknown case: {params.scenario}.")
    detail_seed = (
        params.seed
        if params.seed is not None
        else sum(ord(char) for char in f"{params.name}:{params.scenario}:{params.telling}")
    )
    world = tell(params, random.Random(detail_seed ^ 0x4F21))
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    if "missing_fry" not in sample.story and "fry" not in sample.story:
        raise StoryError("Generated story lost the fry anchor.")
    if "tavern" not in sample.story.lower():
        raise StoryError("Generated story lost the tavern setting.")
    return sample


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
        place="fry_tavern",
        activity="solve_cases",
        prize="missing_fry",
        name="Luna",
        animal="mouse",
        trait="curious",
        scenario="bell_board",
        telling="clue_first",
        seed=17,
    ),
    StoryParams(
        place="fry_tavern",
        activity="solve_cases",
        prize="missing_fry",
        name="Milo",
        animal="sparrow",
        trait="patient",
        scenario="window_shadow",
        telling="evidence_turn",
        seed=31,
    ),
    StoryParams(
        place="fry_tavern",
        activity="serve_fry",
        prize="missing_fry",
        name="Nell",
        animal="fox",
        trait="thoughtful",
        scenario="two_receipts",
        telling="dialogue_first",
        seed=43,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        result = asp_verify()
        if result == 0:
            for params in CURATED:
                generate(params)
            print("OK: curated stories generated and checked.")
        sys.exit(result)

    if args.show_asp:
        print(asp_program("#show solved/1.\n#show clear_case/0."))
        return

    if args.asp:
        print("1 compatible detective domain:")
        print("  fry_tavern solve_cases missing_fry")
        print("ASP results:", asp_valid_results())
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(20, args.n * 20):
            seed = base_seed + attempt
            attempt += 1
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
