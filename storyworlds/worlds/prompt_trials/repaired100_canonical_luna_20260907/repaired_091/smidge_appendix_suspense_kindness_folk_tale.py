#!/usr/bin/env python3
"""
A folk tale about a smidge, an appendix, suspense, and kindness.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    village: str = "Willowmere"
    hero: str = "Luna"
    companion: str = "Pip"
    keeper: str = "Aunt Sella"
    seed: Optional[int] = None


TALES = (
    {
        "title": "The Appendix in the Bell Tower",
        "problem": "the village bell had lost its final page, called the appendix, and no one knew when the storm warning should end",
        "clue": "a smidge of red wax clung to the bell rope",
        "wrong": "Some villagers feared that a goblin had hidden the page in the rafters",
        "cause": "a gust had blown the appendix into a crack behind the bell's wooden frame",
        "response": "Luna tied a lantern to a long pole, while Pip steadied it from the stair",
        "turn": "the missing page was found behind the frame, safe but dusty",
        "change": "the villagers learned that a tiny clue could guide a brave search",
        "ending": "the bell rang its full message while the recovered appendix rested beneath a smooth stone",
        "lesson": "kindness makes courage easier to carry",
    },
    {
        "title": "The Smidge Beneath the Millstone",
        "problem": "the miller's old book said that one smidge of silver flour must remain in the grain chest, yet the silver mark had vanished",
        "clue": "a pale smidge glittered beneath the edge of the millstone",
        "wrong": "The miller suspected a greedy fox had stolen the measure",
        "cause": "the book's appendix had been copied wrongly, and the mark belonged beside the millstone, not inside the chest",
        "response": "Luna asked the miller to lift the stone with his safe wooden lever while Pip kept everyone behind the line",
        "turn": "the silver dust matched the mark in the appendix",
        "change": "a frightening accusation became a shared correction",
        "ending": "the mill turned softly, and a smidge of silver flour shone beside the true measure",
        "lesson": "kind words give mistakes room to become wisdom",
    },
    {
        "title": "The Lantern at Fox Bridge",
        "problem": "the bridge keeper's appendix warned travelers to follow one lantern, but the lantern vanished when the river mist rose",
        "clue": "one smidge of warm wax glowed on the north rail",
        "wrong": "People whispered that the river spirit had carried the lantern away",
        "cause": "the lantern had swung behind a folded warning board",
        "response": "Luna spoke gently to the frightened travelers while Pip fetched the bridge keeper",
        "turn": "the keeper moved the board and found the lantern still burning",
        "change": "the travelers changed from panic to patience",
        "ending": "one golden lantern led the way, and the appendix was read aloud before anyone crossed",
        "lesson": "when fear grows large, kindness helps everyone look closely",
    },
    {
        "title": "The Baker's Last Smidge",
        "problem": "the baker's appendix promised a final smidge of cinnamon for the winter loaf, but the jar seemed empty",
        "clue": "a sweet brown smidge marked the sleeve of the recipe book",
        "wrong": "The baker thought her apprentice had used the last spice without asking",
        "cause": "the cinnamon had settled in a narrow fold beneath the jar's paper lining",
        "response": "Luna listened to the apprentice before anyone blamed him, and Pip helped loosen the lining with a spoon",
        "turn": "the hidden cinnamon tumbled out",
        "change": "the apprentice's worry changed into relief, and the baker apologized",
        "ending": "the winter loaf wore its final cinnamon smidge like a warm brown star",
        "lesson": "kindness should arrive before judgment",
    },
    {
        "title": "The Quiet Orchard Path",
        "problem": "the orchard map's appendix promised a safe path home, but its last direction had disappeared",
        "clue": "a smidge of blue thread hung from the oldest apple tree",
        "wrong": "The children feared the path had been swallowed by the dark",
        "cause": "the missing direction was stitched into a cloth bookmark caught on the branch",
        "response": "Luna held the lantern low while Pip called for the orchard keeper instead of wandering farther",
        "turn": "the keeper recognized the thread and unfolded the lost appendix line",
        "change": "the children became careful helpers instead of frightened runners",
        "ending": "the blue thread marked the safe turn, and every child reached the village before moonrise",
        "lesson": "asking for help is a kind form of courage",
    },
    {
        "title": "The Sparrow's Little Addition",
        "problem": "the school scroll's appendix required one final kindness each morning, but the teacher could not find the small wooden token",
        "clue": "a smidge of straw rested inside the token box",
        "wrong": "The class suspected that a careless student had thrown the token away",
        "cause": "a sparrow had carried the token to its nest to strengthen a loose twig",
        "response": "Luna placed seed near the nest, and Pip asked the teacher to wait until the sparrow flew off",
        "turn": "the token was returned without disturbing the nest",
        "change": "the class learned to protect a small bird while repairing its own mistake",
        "ending": "the token returned to the box, and the appendix gained a new line about gentle hands",
        "lesson": "kindness can make room for every small creature",
    },
)


OPENINGS = (
    "Long ago, when the moon was a silver sickle, a small mystery came to Willowmere.",
    "In the old days, the people of Willowmere trusted bells, books, and one another.",
    "At dusk, when the village roofs turned purple, Luna noticed that something was not as it should be.",
    "There was once a village where even a smidge of a clue was worth following.",
    "Before the winter stars appeared, a quiet worry slipped through Willowmere.",
)


@dataclass
class World:
    village: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed if params.seed is not None else 0)
    tale = TALES[rng.randrange(len(TALES))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]

    if not params.hero.strip() or not params.companion.strip():
        raise StoryError("hero and companion names must not be empty")
    if params.hero.strip().lower() == params.companion.strip().lower():
        raise StoryError("hero and companion must have different names")

    world = World(params.village)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="girl",
            label=params.hero,
            memes={"curiosity": 1, "kindness": 1, "courage": 0},
        )
    )
    companion = world.add(
        Entity(
            id="companion",
            kind="character",
            type="boy",
            label=params.companion,
            memes={"kindness": 1, "trust": 1, "courage": 0},
        )
    )
    keeper = world.add(
        Entity(
            id="keeper",
            kind="character",
            type="woman",
            label=params.keeper,
            memes={"patience": 1},
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="evidence",
            label=tale["clue"],
            meters={"size": 0.1},
        )
    )
    appendix = world.add(
        Entity(
            id="appendix",
            kind="document",
            label="the appendix",
            meters={"present": 0, "recovered": 0},
        )
    )

    world.facts = {
        "title": tale["title"],
        "problem": tale["problem"],
        "clue": tale["clue"],
        "wrong": tale["wrong"],
        "cause": tale["cause"],
        "response": tale["response"],
        "turn": tale["turn"],
        "change": tale["change"],
        "ending": tale["ending"],
        "lesson": tale["lesson"],
        "hero": hero.label,
        "companion": companion.label,
        "keeper": keeper.label,
        "village": params.village,
    }

    world.say(opening)
    world.say(
        f"In {params.village}, {hero.label} and {companion.label} helped "
        f"{params.keeper} care for the village records. One record had a special appendix, "
        "a little ending added after the main writing."
    )
    world.say(f"That evening, {tale['problem']}.")
    world.para()

    world.say(f"{tale['wrong']}.")
    world.say(
        f"Then {hero.label} noticed the clue: {tale['clue']}. "
        f'"Look," {hero.label} said. "Even a smidge can point to a larger truth."'
    )
    world.say(
        f'"Should we search alone?" {companion.label} asked. '
        f'"No," answered {hero.label}. "We can be brave and kind by asking for help."'
    )
    world.say(
        f"{params.keeper} listened carefully and brought a safe lantern. "
        f"{companion.label} held the door, and {hero.label} watched the clue."
    )
    world.para()

    world.say(f"The search grew suspenseful as the last light slipped away. {tale['cause']}.")
    world.say(f"At last, {tale['turn']}.")
    world.say(
        f'"We found it because we listened instead of blaming," {hero.label} said. '
        f'"And because everyone helped," {companion.label} replied.'
    )
    appendix.meters["present"] = 1
    appendix.meters["recovered"] = 1
    hero.memes["courage"] = 1
    companion.memes["courage"] = 1
    world.para()

    world.say(f"To finish the work, {tale['response']}.")
    world.say(f"{tale['change']}.")
    world.say(
        f"{hero.label} thanked {companion.label}, and {companion.label} thanked "
        f"{params.keeper}. The village's fear softened into gratitude."
    )
    world.say(f"The lesson was simple: {tale['lesson']}.")
    world.say(f"By moonrise, {tale['ending']}.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Tell a child-friendly folk tale in {f['village']} involving a smidge and an appendix.",
        f"Build suspense around this clue: {f['clue']}.",
        f"Resolve the mystery through kindness, ending with this image: {f['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What problem began the tale?",
            answer=f"The problem was that {f['problem']}.",
        ),
        QAItem(
            question="What small clue helped the friends?",
            answer=f"They noticed that {f['clue']}. The tiny smidge gave them a useful direction.",
        ),
        QAItem(
            question="What did people wrongly suspect?",
            answer=f"{f['wrong']}. That guess changed when the friends examined the evidence.",
        ),
        QAItem(
            question="What was the real cause?",
            answer=f"They discovered that {f['cause']}.",
        ),
        QAItem(
            question="How did kindness help?",
            answer=f"{f['response']}. The friends listened, shared the work, and avoided blaming anyone.",
        ),
        QAItem(
            question="What lesson did the village learn?",
            answer=f"The village learned that {f['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an appendix?",
            answer="An appendix is an extra section added to the end of a book, record, or piece of writing.",
        ),
        QAItem(
            question="What does smidge mean?",
            answer="A smidge means a very small amount.",
        ),
        QAItem(
            question="Why can kindness help during suspense?",
            answer="Kindness helps people listen, share work, and make careful choices instead of blaming one another in fear.",
        ),
    ]


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
kind(X) :- character(X).
has_clue(X) :- character(X), clue(smidge).
seeks_appendix(X) :- character(X), has_clue(X).
safe_search(X) :- seeks_appendix(X), kind(X).
recovered(appendix) :- safe_search(X).
resolved :- recovered(appendix).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("hero", "luna"),
            asp.fact("companion", "pip"),
            asp.fact("clue", "smidge"),
            asp.fact("appendix", "appendix"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program(
            "#show safe_search/1.\n"
            "#show recovered/1.\n"
            "#show resolved/0.\n"
        )
    )
    names = {(symbol.name, len(symbol.arguments)) for symbol in model}
    needed = {("safe_search", 1), ("recovered", 1), ("resolved", 0)}
    if names >= needed:
        print("OK: ASP rules agree with the kindness-led recovery.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected recovery facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale about a smidge, an appendix, suspense, and kindness."
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
    parser.add_argument("--village", default="Willowmere")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--companion", default=None)
    parser.add_argument("--keeper", default=None)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        village=args.village,
        hero=args.hero or rng.choice(["Luna", "Mara", "Iris", "Nell"]),
        companion=args.companion or rng.choice(["Pip", "Tomas", "Finn", "Oren"]),
        keeper=args.keeper or rng.choice(["Aunt Sella", "Grandmother Vale", "Uncle Rowan"]),
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
            f"{entity.id}: type={entity.type} "
            f"meters={entity.meters} memes={entity.memes}"
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
                "#show safe_search/1.\n"
                "#show recovered/1.\n"
                "#show resolved/0.\n"
            )
        )
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show safe_search/1.\n"
                "#show recovered/1.\n"
                "#show resolved/0.\n"
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = max(1, args.n)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        count = len(TALES)

    for index in range(count):
        trial_seed = base_seed + index
        rng = random.Random(trial_seed)
        params = resolve_params(args, rng)
        params.seed = trial_seed
        sample = generate(params)
        if args.all or sample.story not in seen:
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
