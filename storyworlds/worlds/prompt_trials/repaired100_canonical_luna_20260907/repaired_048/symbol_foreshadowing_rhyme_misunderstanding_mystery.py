#!/usr/bin/env python3
"""
A small mystery storyworld about a hidden symbol, a warning rhyme, and a
misunderstanding that careful friends can solve.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    feature: str


@dataclass
class StoryParams:
    place: str
    detective: str
    helper: str
    symbol_name: str
    object_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    object_description: str
    missing_result: str
    rhyme: str
    mistaken_blame: str
    foreshadowing: str
    test: str
    cause: str
    repair: str
    ending: str
    lesson: str


CASES = [
    Case(
        "a small brass key with a blue thread tied to it",
        "the cabinet holding the town's storybook would not open",
        "When the silver moon is near the door, follow the star to find the floor.",
        "the quiet caretaker",
        "a pale star was scratched into the dust beneath the cabinet",
        "placed a paper star on the floor and watched how the door's shadow moved",
        "the key had slipped beneath a loose floorboard marked with the same star",
        "lifted the board, opened the cabinet, and tightened its hinge",
        "the storybook rested open beneath a bright painted star",
        "A clue should be tested before anyone is blamed.",
    ),
    Case(
        "a red ribbon carrying a tiny sun symbol",
        "the lantern for the evening walk could not be found",
        "If the little sun turns red, look where warm footsteps tread.",
        "the child who had carried the lantern last",
        "a warm patch of dust curved from the doorway toward the old bench",
        "followed the curved marks instead of searching only the shelves",
        "the ribbon had caught on a bench nail, pulling the lantern behind a curtain",
        "freed the ribbon and tied a safe loop around the lantern handle",
        "the lantern shone along the path while the red ribbon fluttered",
        "Following the whole clue can clear up a misunderstanding.",
    ),
    Case(
        "a wooden token carved with a fish symbol",
        "the harbor bell stayed silent before the boats came home",
        "A fish by the stair will show what is fair.",
        "the youngest bell helper",
        "a line of damp fish-shaped prints led toward the stair",
        "compared the token's wet edge with the prints",
        "rainwater had washed the token from its hook and wedged it under the stair",
        "dried the token, moved its hook, and checked the bell rope",
        "the harbor bell rang while the fish symbol gleamed above it",
        "A careful question is kinder than a quick accusation.",
    ),
    Case(
        "a paper badge printed with a green leaf symbol",
        "the garden gate seemed locked during the flower show",
        "Where one green leaf bends low, the hidden answer likes to grow.",
        "a visitor who had left in a hurry",
        "one leaf-shaped mark appeared below the gate latch",
        "pressed a leaf against the mark and lifted the latch gently",
        "a fallen vine had wrapped around the latch and made the gate look locked",
        "trimmed the vine and placed a small symbol sign beside the latch",
        "the gate swung open, revealing flowers bright as colored stars",
        "A strange-looking problem may have an ordinary cause.",
    ),
    Case(
        "a silver card bearing a tiny bell symbol",
        "the music room's lost-and-found box appeared empty",
        "When the small bell rings twice, seek the place where quiet hides.",
        "the music teacher",
        "two bell marks were stamped near the curtain's quiet corner",
        "rang a handbell twice and listened for a soft answer",
        "the box had rolled behind the curtain when the floor was swept",
        "put felt beneath the box and marked its shelf with the bell symbol",
        "the missing scarf lay safe behind the curtain as the bell chimed",
        "Good detectives notice what a clue predicts.",
    ),
    Case(
        "a round stone painted with a white eye symbol",
        "the museum's tiny moon model had vanished from its stand",
        "The white eye sees the night; search beneath the gentle light.",
        "the night guard",
        "the eye symbol faced a patch of moonlight on the floor",
        "shone a lamp from the symbol toward the model's stand",
        "the model had rolled into a display shadow after a visitor brushed the stand",
        "added a low rim around the stand and returned the stone",
        "the moon model glowed safely beneath the museum lamp",
        "Evidence can explain an accident without making an enemy.",
    ),
]

OPENINGS = [
    "The mystery began with one empty place where something important should have been.",
    "On a quiet morning, a small symbol appeared where no one expected it.",
    "The detective noticed the trouble because an ordinary room suddenly felt full of questions.",
    "Nothing seemed wrong until the helper found a folded rhyme beside the door.",
    "A tiny mark turned a simple search into a careful mystery.",
]

DIALOGUE = [
    '"I think someone took it," said the helper. "Let us ask what the clue tells us," replied the detective.',
    '"The rhyme sounds like a warning," said the helper. "Or a direction," said the detective. "We should test it."',
    '"You saw who was nearby," said the helper. "That does not prove who caused the trouble," answered the detective.',
    '"Could the symbol be part of the answer?" asked the helper. "It may be the first step," said the detective.',
]

CLOSINGS = [
    "They wrote the true cause beside the symbol so the next mystery would begin with a fair question.",
    "From then on, the helper looked for a full chain of clues before choosing a culprit.",
    "The symbol stayed on the repaired object, a quiet reminder to investigate kindly.",
    "Their misunderstanding faded as the room returned to its usual cheerful sounds.",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


def tell(world: World, params: StoryParams) -> None:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values().__str__())))
    rng = random.Random(seed ^ 0x91A7)
    case = rng.choice(CASES)
    opening = rng.choice(OPENINGS)
    dialogue = rng.choice(DIALOGUE)
    closing = rng.choice(CLOSINGS)

    detective = world.add(Entity("detective", "character", "child", params.detective,
                                 memes={"curiosity": 1.0, "patience": 1.0}))
    helper = world.add(Entity("helper", "character", "child", params.helper,
                              memes={"worry": 1.0, "confusion": 0.0}))
    symbol = world.add(Entity("symbol", "thing", "symbol", params.symbol_name,
                              meters={"visible": 1.0}, memes={"meaning": 1.0}))
    object_ent = world.add(Entity("object", "thing", "mystery_object", params.object_name,
                                  meters={"present": 0.0}, memes={}))

    world.say(opening)
    world.say(f"{detective.label} loved mysteries with clues that could be touched, seen, and tested.")
    world.say(f"{helper.label} kept watch over {params.place}, where {case.object_description} belonged.")
    world.para()

    world.say(f"That day, {case.missing_result}.")
    world.say(f"Beside the empty place, {helper.label} found {params.symbol_name} and read this rhyme aloud: “{case.rhyme}”")
    world.say(f"The rhyme was a piece of foreshadowing, but its meaning was not clear yet.")
    world.say(f"{helper.label} misunderstood the scene and suspected {case.mistaken_blame}.")
    world.say(dialogue)

    helper.memes["confusion"] = 1.0
    helper.memes["worry"] = 1.0
    detective.memes["curiosity"] = 2.0
    world.fired.add("misunderstanding")

    world.para()
    world.say(f"{detective.label} searched without accusing anyone. The first clue was that {case.foreshadowing}.")
    world.say(f"The detective said, “The symbol and the rhyme should point to the same place.”")
    world.say(f"Together they {case.test}.")
    world.say(f"The test revealed the answer: {case.cause}.")
    world.say(f"{helper.label} lowered their head and said, “I am sorry. I misunderstood what I saw.”")
    world.say(f"{detective.label} replied, “Now we know the truth, and no one had to be blamed.”")

    object_ent.meters["present"] = 1.0
    helper.memes["confusion"] = 0.0
    helper.memes["worry"] = 0.0
    detective.memes["pride"] = 1.0
    world.fired.add("cause_found")

    world.para()
    world.say(f"They {case.repair}.")
    world.say(case.lesson)
    world.say(f"{closing} {case.ending}.")

    world.facts.update(
        detective=detective,
        helper=helper,
        symbol=symbol,
        object=object_ent,
        case=case,
        place=params.place,
    )


PLACES = {
    "clocktower": Setting("the clock tower", "old stone stairs"),
    "museum": Setting("the little museum", "quiet display rooms"),
    "harbor": Setting("the harbor office", "wooden docks"),
    "garden": Setting("the community garden", "a vine-covered gate"),
    "music_room": Setting("the music room", "a red velvet curtain"),
}

DETECTIVES = ["Luna", "Mira", "Theo", "Niko", "Ivy", "Sam"]
HELPERS = ["Pip", "June", "Ollie", "Tess", "Rafi", "Ada"]
SYMBOLS = ["the silver star symbol", "the blue spiral symbol", "the golden key symbol", "the white moon symbol"]
OBJECTS = ["the missing key", "the lost lantern", "the hidden token", "the vanished model", "the absent badge"]


ASP_RULES = r"""
visible_symbol(S) :- symbol(S), visible(S).
mystery_ready(O) :- object(O), found(O), clue_tested(O).
resolved(O) :- mystery_ready(O), repaired(O).
#show visible_symbol/1.
#show mystery_ready/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for symbol in SYMBOLS:
        lines.append(asp.fact("symbol", symbol))
        lines.append(asp.fact("visible", symbol))
    for obj in OBJECTS:
        lines.append(asp.fact("object", obj))
        lines.append(asp.fact("found", obj))
        lines.append(asp.fact("clue_tested", obj))
        lines.append(asp.fact("repaired", obj))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about a symbol, a rhyme, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--symbol-name")
    ap.add_argument("--object-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
        place=args.place or rng.choice(list(PLACES)),
        detective=args.detective or rng.choice(DETECTIVES),
        helper=args.helper or rng.choice(HELPERS),
        symbol_name=args.symbol_name or rng.choice(SYMBOLS),
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]  # type: ignore[assignment]
    return [
        f'Write a gentle mystery for children featuring the symbol "{f["symbol"].label}".',
        f"Include foreshadowing through this rhyme: {case.rhyme}",
        f"Show how {f['helper'].label} resolves a misunderstanding by testing a clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]  # type: ignore[assignment]
    return [
        QAItem("What symbol helped guide the investigation?", f"The investigation used {f['symbol'].label}, which pointed toward the hidden clue."),
        QAItem("What did the rhyme foreshadow?", f"The rhyme foreshadowed the place or method that revealed {case.cause}."),
        QAItem("What misunderstanding did the helper have?", f"The helper mistakenly suspected {case.mistaken_blame}, even though that was not proven."),
        QAItem("How did the detective solve the mystery?", f"The detective tested the clue by {case.test}, which showed that {case.cause}."),
        QAItem("How was the problem repaired?", f"They {case.repair}."),
        QAItem("What lesson did the characters learn?", case.lesson),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a symbol?", "A symbol is a mark or picture that stands for an idea, object, or direction."),
        QAItem("What is foreshadowing?", "Foreshadowing is a clue that hints at something important that will happen later."),
        QAItem("What is a misunderstanding?", "A misunderstanding happens when someone gets the wrong meaning from what they see or hear."),
        QAItem("Why should a mystery clue be tested?", "Testing a clue helps separate what is true from what is only a guess."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(f"{entity.id}: kind={entity.kind} type={entity.type} meters={entity.meters} memes={entity.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if not params.detective or not params.helper:
        raise StoryError("A mystery needs both a detective and a helper.")
    if params.detective == params.helper:
        raise StoryError("The detective and helper must be different characters.")
    world = World(PLACES[params.place])
    tell(world, params)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n#show symbol/1.\n"))
    places = {row[0] for row in asp.atoms(model, "place")}
    symbols = {row[0] for row in asp.atoms(model, "symbol")}
    if places != set(PLACES) or symbols != set(SYMBOLS):
        print("MISMATCH: ASP and Python registries differ.")
        return 1
    for seed in range(3):
        params = resolve_params(argparse.Namespace(place=None, detective=None, helper=None,
                                                   symbol_name=None, object_name=None),
                                random.Random(seed))
        sample = generate(params)
        if "misunderstanding" not in sample.world.fired or "cause_found" not in sample.world.fired:
            print("MISMATCH: generated story did not complete its mystery.")
            return 1
    print(f"OK: ASP/Python registry parity ({len(places)} places, {len(symbols)} symbols).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show place/1.\n#show symbol/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show place/1.\n#show symbol/1.\n#show resolved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams("clocktower", "Luna", "Pip", "the silver star symbol", "the missing key", base_seed),
            StoryParams("museum", "Mira", "June", "the white moon symbol", "the vanished model", base_seed + 1),
            StoryParams("garden", "Theo", "Ada", "the green leaf symbol", "the hidden token", base_seed + 2),
        ]
        samples = [generate(p) for p in presets]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 50):
            if len(samples) >= max(args.n, 1):
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False
        ))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
