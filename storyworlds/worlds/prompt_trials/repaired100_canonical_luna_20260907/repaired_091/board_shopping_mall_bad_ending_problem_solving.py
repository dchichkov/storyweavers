#!/usr/bin/env python3
"""
Story world: a shopping-mall adventure about a board, problem solving, and a bad ending avoided.
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

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    mall: str = "Maple Square Mall"
    hero: str = "Luna"
    companion: str = "Milo"
    board: str = "the blue adventure board"
    seed: Optional[int] = None


SCENARIOS = (
    {
        "name": "the disappearing arrow",
        "problem": "the board's arrow to the rooftop garden pointed into a locked service corridor",
        "clue": "a strip of green tape on the floor continued toward the public elevator",
        "wrong": "They almost followed the arrow anyway, hoping the corridor hid a secret shortcut",
        "cause": "a cleaning cart had bumped the board and turned its arrow while the floor was being polished",
        "fix": "a mall guide moved the cart, checked the corridor, and turned the board toward the elevator",
        "turn": "Luna realized that an exciting-looking path could still be the wrong path",
        "ending": "the corrected board led families to the rooftop garden, while the locked corridor stayed safely quiet",
        "lesson": "an adventure is better when brave explorers check whether a path is safe and true",
        "dialogue": (
            '"The tape is green like the garden sign," Milo said. '
            '"Then we should follow the marked public route, not the arrow alone," Luna replied.'
        ),
    },
    {
        "name": "the missing map corner",
        "problem": "the board was missing the corner that showed the way to the first-aid room",
        "clue": "tiny paper fibers pointed beneath a nearby display bench",
        "wrong": "They guessed the missing corner had blown outside through the main doors",
        "cause": "a child had peeled the corner off while looking for a sticker and tucked it under the bench",
        "fix": "the child returned the piece, and the information desk replaced the worn board with a clear copy",
        "turn": "Milo changed from blaming the wind to asking what people had touched",
        "ending": "the first-aid route shone clearly on the new board, ready for anyone who might need help",
        "lesson": "problem solving begins with clues and kind questions instead of quick blame",
        "dialogue": (
            '"The fibers point under the bench," Luna said. '
            '"Let us ask the desk before we accuse the wind," Milo answered.'
        ),
    },
    {
        "name": "the dark arcade sign",
        "problem": "the board sent visitors toward an arcade sign that had gone dark",
        "clue": "a working sticker on the board showed that the old sign had been replaced",
        "wrong": "They thought the dark sign marked a hidden entrance for a thrilling night mission",
        "cause": "the board had not been updated after the arcade moved to the opposite wing",
        "fix": "the manager printed a new board and placed a bright temporary arrow beside the old sign",
        "turn": "Luna learned that old information could make a real place feel mysterious and unsafe",
        "ending": "music spilled from the arcade's new doorway as the old sign was taken down",
        "lesson": "checking current information keeps an adventure from ending in confusion",
        "dialogue": (
            '"The sticker says this map is old," Milo noticed. '
            '"Then we need the newest directions before we explore," Luna said.'
        ),
    },
    {
        "name": "the rolling display",
        "problem": "a tall display board rolled across the mall walkway each time the doors opened",
        "clue": "one wheel had no rubber stopper and left a shiny curved trail",
        "wrong": "They imagined the board was chasing shoppers like a friendly monster",
        "cause": "the display's loose wheel caught the draft from the automatic doors",
        "fix": "a staff member moved it away from the doorway and locked all four wheels",
        "turn": "Milo stopped treating the moving board as a game and noticed how it could block someone",
        "ending": "the display stood firmly beside the flower shop, leaving a wide path for carts and wheelchairs",
        "lesson": "noticing a danger is useful when it leads to a careful repair",
        "dialogue": (
            '"It rolls whenever the doors breathe," Luna said. '
            '"Then we should warn the staff instead of trying to stop it ourselves," Milo replied.'
        ),
    },
    {
        "name": "the upside-down treasure trail",
        "problem": "the board's treasure-trail map showed the fountain at the beginning instead of the end",
        "clue": "the numbered stickers ran backward from five to one",
        "wrong": "They raced to the fountain and found no treasure, nearly giving up",
        "cause": "the board had been mounted upside down after a weekend craft fair",
        "fix": "the event helper turned it around and added a large START sticker",
        "turn": "Luna learned to inspect the order of clues before deciding that a promise had failed",
        "ending": "children followed the trail from the library to the fountain and found a basket of paper stars",
        "lesson": "patient explorers test the order of clues before they abandon a good plan",
        "dialogue": (
            '"Five comes before one on this board," Milo said. '
            '"That means the map is upside down, not the treasure gone," Luna answered.'
        ),
    },
    {
        "name": "the blocked board",
        "problem": "boxes hid the board that showed the safest route to the west exit",
        "clue": "the boxes had a delivery label for the toy shop and a clear space beside the fire door",
        "wrong": "They tried to squeeze between the boxes to read the board",
        "cause": "a delivery had been left in the wrong place during a busy sale",
        "fix": "a worker moved the boxes to the stockroom and checked that the exit route was open",
        "turn": "Milo understood that solving a problem sometimes meant waiting for an adult rather than forcing through",
        "ending": "the west-exit board could be read from across the open hallway",
        "lesson": "safe problem solving includes knowing when to ask a responsible helper",
        "dialogue": (
            '"The gap is too narrow," Luna warned. '
            '"Then we will call a worker and keep clear of the fire door," Milo said.'
        ),
    },
)

OPENINGS = (
    "Rain tapped the glass roof of Maple Square Mall when Luna spotted the board.",
    "The mall was bright with weekend shoppers, but one board made the adventure feel suddenly uncertain.",
    "Luna and Milo arrived at the shopping mall with a simple plan: find the rooftop garden.",
    "Near the fountain, a colorful board promised a path through the mall and a puzzle to solve.",
    "The adventure began beside the information desk, where a board pointed in two surprising directions.",
)

TRANSITIONS = (
    "They did not rush. They compared the board with the signs, the floor marks, and the people who worked nearby.",
    "Luna drew the clues in her notebook while Milo watched what changed when shoppers passed.",
    "They stayed in public areas, kept their hands off the equipment, and asked a mall worker to check their idea.",
    "Their first guess failed, so they returned to the smallest clue and tested it against the whole board.",
    "The mall seemed like a maze, but careful observations began turning it into a map.",
)

MALL_FACTS = (
    (
        "What is a shopping mall?",
        "A shopping mall is a large place with many shops and shared spaces where people can shop and meet.",
    ),
    (
        "What is a board used for?",
        "A board can display information, directions, notices, or a map for people to read.",
    ),
    (
        "Why should visitors follow mall safety signs?",
        "Safety signs show routes and warnings that help visitors move through the mall without getting hurt.",
    ),
)


@dataclass
class World:
    mall: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        return "\n\n".join(" ".join(group) for group in self.paragraphs if group)


def tell(params: StoryParams) -> World:
    if not params.mall.strip():
        raise StoryError("mall must not be empty")
    if not params.hero.strip() or not params.companion.strip():
        raise StoryError("hero and companion names must not be empty")
    if params.hero.casefold() == params.companion.casefold():
        raise StoryError("hero and companion must have different names")
    if not params.board.strip():
        raise StoryError("board must not be empty")

    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = SCENARIOS[rng.randrange(len(SCENARIOS))]
    opening = rng.choice(OPENINGS)
    transition = rng.choice(TRANSITIONS)
    variation = rng.randrange(3)

    world = World(params.mall)
    hero = world.add(
        Entity(
            id="hero",
            type="girl",
            label=params.hero,
            meters={"safe": 1.0, "confidence": 0.4},
            memes={"curiosity": 1.0, "care": 1.0},
            traits=["curious", "careful"],
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            type="boy",
            label=params.companion,
            meters={"safe": 1.0, "confidence": 0.3},
            memes={"loyalty": 1.0, "caution": 0.8},
            traits=["observant", "loyal"],
        )
    )
    board = world.add(
        Entity(
            id="board",
            type="board",
            label=params.board,
            meters={"readable": 1.0, "correct": 0.0},
            memes={"trust": 0.5, "clue": 1.0},
        )
    )
    world.facts = {
        "scenario": scenario,
        "opening": opening,
        "transition": transition,
        "variation": variation,
        "hero": hero.label,
        "companion": companion.label,
        "board": board.label,
        "mall": params.mall,
    }

    world.say(opening)
    world.say(
        f"{hero.label} and {companion.label} were visiting {params.mall} when they found "
        f"{params.board} beside the information desk. It promised an exciting route, but "
        f"the direction did not agree with the nearby mall signs."
    )
    world.say(f"The problem was this: {scenario['problem']}.")
    world.para()

    world.say(scenario["wrong"] + ".")
    world.say(scenario["dialogue"])
    world.say(f"{hero.label} and {companion.label} looked for evidence. They found {scenario['clue']}.")
    world.say(transition)
    world.para()

    if variation == 0:
        world.say(
            f"{hero.label} kept one hand on the notebook and the other at their side. "
            f"They did not climb, pull, or enter a staff-only space."
        )
    elif variation == 1:
        world.say(
            f"They compared the board with two fixed signs and asked a nearby mall worker "
            f"whether the public route had changed."
        )
    else:
        world.say(
            f"They marked the safe place where they were standing, then followed the clue "
            f"only as far as the public signs allowed."
        )

    world.say(f"The clue revealed the cause: {scenario['cause']}.")
    world.say(f"The safe solution was simple: {scenario['fix']}.")
    world.say(f"{scenario['turn']}.")
    board.meters["correct"] = 1.0
    board.memes["trust"] = 1.0
    hero.meters["confidence"] = 1.0
    companion.meters["confidence"] = 0.9
    hero.memes["problem_solved"] = 1.0
    companion.memes["problem_solved"] = 1.0
    world.para()

    if variation == 0:
        world.say(
            f'"A good adventure should not end with someone lost or hurt," {companion.label} said. '
            f'"Right," {hero.label} replied. "The best clue is the one that gets everyone home safely."'
        )
    elif variation == 1:
        world.say(
            f'"We solved it by slowing down," {hero.label} said. '
            f'"And by sharing what we noticed," {companion.label} added.'
        )
    else:
        world.say(
            f'"The board needed help, not a guess," {companion.label} said. '
            f'"And we needed help from people who knew the mall," {hero.label} answered.'
        )

    world.say(
        f"They understood how the story could have had a bad ending: they might have entered a "
        f"closed area, blocked a route, or become separated. Instead, problem solving changed "
        f"the danger into a safe adventure."
    )
    world.say(f"At last, {scenario['ending']}.")
    world.say(
        f"{hero.label} and {companion.label} left {params.mall} together, carrying the "
        f"lesson that {scenario['lesson']}."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    return [
        f"Write an adventurous shopping-mall story about {world.facts['board']} and this problem: {scenario['problem']}.",
        f"Show {world.facts['hero']} and {world.facts['companion']} solving the problem with this clue: {scenario['clue']}.",
        f"Avoid a bad ending and finish with this changed scene: {scenario['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    return [
        QAItem(
            question="What problem did the board create?",
            answer=f"The board caused confusion because {scenario['problem']}.",
        ),
        QAItem(
            question=f"What clue did {hero} and {companion} discover?",
            answer=f"They discovered that {scenario['clue']}.",
        ),
        QAItem(
            question="What was the real cause of the problem?",
            answer=f"The real cause was that {scenario['cause']}.",
        ),
        QAItem(
            question="How did the characters solve the problem safely?",
            answer=f"They solved it when {scenario['fix']}. They stayed in public areas and asked a responsible mall worker for help.",
        ),
        QAItem(
            question="How was a bad ending avoided?",
            answer=f"They avoided a bad ending by refusing to rush into danger and by checking the board against reliable clues and safety signs.",
        ),
        QAItem(
            question="What did the characters learn?",
            answer=f"They learned that {scenario['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in MALL_FACTS]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
character(X) :- hero(X).
character(X) :- companion(X).
safe_route(B) :- board(B), correct(B), public(B).
solved(H,C,B) :- hero(H), companion(C), board(B), safe_route(B), observes(H,B), asks(C).
avoided_bad_ending(H,C) :- solved(H,C,B), careful(H), careful(C).
adventure(H,C) :- solved(H,C,B), avoided_bad_ending(H,C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("hero", "luna"),
        asp.fact("companion", "milo"),
        asp.fact("board", "mall_board"),
        asp.fact("correct", "mall_board"),
        asp.fact("public", "mall_board"),
        asp.fact("observes", "luna", "mall_board"),
        asp.fact("asks", "milo"),
        asp.fact("careful", "luna"),
        asp.fact("careful", "milo"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program(
            "#show solved/3.\n"
            "#show avoided_bad_ending/2.\n"
            "#show adventure/2.\n"
        )
    )
    names = {symbol.name for symbol in model}
    required = {"solved", "avoided_bad_ending", "adventure"}
    if required.issubset(names):
        print("OK: ASP rules produce the expected problem-solving parity.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An adventurous shopping-mall story about a board, problem solving, and avoiding a bad ending."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--mall", default="Maple Square Mall")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--companion", default=None)
    parser.add_argument("--board", default="the blue adventure board")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nora", "Zoe", "Tessa"])
    companion = args.companion or rng.choice(["Milo", "Sam", "Theo", "Pip"])
    if hero.casefold() == companion.casefold():
        raise StoryError("hero and companion names must be different")
    return StoryParams(
        mall=args.mall,
        hero=hero,
        companion=companion,
        board=args.board,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


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
        print(
            asp_program(
                "#show solved/3.\n"
                "#show avoided_bad_ending/2.\n"
                "#show adventure/2.\n"
            )
        )
        return

    if args.verify:
        import storyworlds.asp as asp

        status = asp_verify()
        if status:
            raise SystemExit(status)
        sample = generate(StoryParams(seed=17))
        if not sample.story.strip() or len(sample.story_qa) < 3:
            print("MISMATCH: generated story verification failed.")
            raise SystemExit(1)
        print("OK: generated story exercises the shared result containers.")
        return

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show solved/3.\n"
                "#show avoided_bad_ending/2.\n"
                "#show adventure/2.\n"
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = max(1, args.n)
    samples: list[StorySample] = []

    if args.all:
        scenarios = list(range(len(SCENARIOS)))
        for index in scenarios:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < count and attempt < max(50, count * 20):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

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
