#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Museum:
    name: str
    exhibit: str
    case_open: bool = False
    mystery_solved: bool = False
    clue_count: int = 0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    detective_name: str
    helper_name: str
    museum_name: str
    exhibit_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Theo", "Zara", "Pip", "Mara", "Finn"]
MUSEUMS = ["Bright Steps Museum", "Little Lantern Museum", "Wonder Window Museum"]
EXHIBITS = ["the Moonbeam Crown", "the Starry Shoe", "the Rainbow Robot"]


ARCS = [
    {
        "key": "crown_shadow",
        "premise": [
            "Luna loved solving tiny mysteries at Bright Steps Museum. Her friend Milo helped her visit the glowing hall where {exhibit} rested under glass.",
            "At the children's museum, {detective} wore a paper detective badge while {helper} carried a notebook. They had come to admire {exhibit}, the museum's most glamorous treasure.",
        ],
        "problem": [
            "When the lights blinked, the treasure vanished from its case. Only a silver button and a bright violet shadow remained.",
            "The glass case was empty after the morning sparkle show. A violet smear marked the velvet, and the museum guard heard a soft click near the puppet theater.",
        ],
        "dialogue": [
            "\"Someone stole it!\" cried {helper}. \"Maybe,\" said {detective}, \"but a clue can tell us more than a guess.\" Their quick exchange changed panic into careful investigation.",
            "\"I saw a purple flash,\" said {helper}. {detective} asked, \"Did it move toward the doors or the theater?\" Milo pointed to the theater, giving Luna a new direction.",
        ],
        "turn": [
            "A flashback helped them remember the last minute before the lights blinked. In it, a museum worker had rolled a mirror beside the case, making the violet shadow look like a trail.",
            "{detective} closed her eyes and replayed the scene in a flashback. The glamorous lights had made a purple scarf shine, but the scarf was attached to a costume cart.",
        ],
        "inference": [
            "They followed the silver button to the costume cart. The button matched a magician's cape, so their inference was that the treasure had been carried as a prop, not stolen.",
            "The children compared the shadow, the button, and the click. Their inference was simple: a costume trick had made the empty case look mysterious.",
        ],
        "action": [
            "{detective} and {helper} asked the theater guide to open the cart. Beneath a velvet cape, they found {exhibit safe}, waiting for the next show.",
            "\"Let's check the cart together,\" said {detective}. {helper} lifted the cape while the guide unlocked a small drawer. There was {exhibit safe}, not a thief's prize.",
        ],
        "resolution": [
            "The guide explained that a rehearsal had borrowed the treasure by mistake. The case was closed again, and the children solved the whodunit with evidence instead of blame.",
            "The mystery ended when the guide returned the treasure and apologized. Their careful inference restored the exhibit and made the museum feel bright again.",
        ],
        "ending": [
            "The violet lights shimmered on the glass, while Luna and Milo pinned a note beside the case: Look closely before you leap.",
            "Under the repaired spotlight, the treasure glittered calmly. The two young detectives walked on, searching for their next honest clue.",
        ],
        "problem_fact": "the glamorous exhibit vanished while a violet shadow and silver button remained",
        "clue_fact": "a flashback showed that a costume cart had stood beside the case",
        "inference_fact": "the children inferred that a theater rehearsal had moved the exhibit",
        "action_fact": "they checked the costume cart with the museum guide",
        "outcome_fact": "the exhibit was found safe and the mystery was solved",
    },
    {
        "key": "robot_reflection",
        "premise": [
            "At Little Lantern Museum, {detective} and {helper} explored hands-on rooms filled with buttons, mirrors, and friendly robots. The brightest display was {exhibit}.",
            "{detective} visited the children's museum with {helper}, who loved shiny things. Together they watched {exhibit} wave beneath a glamorous curtain of stars.",
        ],
        "problem": [
            "After a puppet show, the robot disappeared. A trail of glitter led to a mirror maze, but every reflection seemed to accuse someone different.",
            "The exhibit's alarm chirped, then stopped. The robot was gone, and glittery footprints ended at a mirror that showed no footprints at all.",
        ],
        "dialogue": [
            "\"The mirror says the robot went left,\" said {helper}. \"Mirrors reverse clues,\" replied {detective}. Their words changed which path they chose.",
            "\"Should we blame the puppeteer?\" asked {helper}. \"Not without proof,\" said {detective}. They decided to test the glitter trail instead of guessing.",
        ],
        "turn": [
            "In a flashback, {detective} remembered seeing the robot's blue wheel pause when the curtain fan blew. The glamour had hidden a loose ribbon beneath the display.",
            "The children replayed the last puppet-show moment in a flashback. A glitter ribbon had brushed the robot, and its wheel had turned toward the service ramp.",
        ],
        "inference": [
            "The glitter was not a trail from a thief. It had stuck to the robot's wheel, so their inference pointed toward the service ramp.",
            "They compared the wheel mark with the ribbon fibers. Their inference was that the fan had nudged the robot away during the show.",
        ],
        "action": [
            "{detective} and {helper} followed the wheel marks to the ramp and called the technician. Behind a curtain, they found {exhibit safe}.",
            "\"We need the ramp, not the mirror,\" said {detective}. {helper} fetched the technician, who moved one box and uncovered {exhibit safe}.",
        ],
        "resolution": [
            "The technician fixed the fan and returned the robot. The mirror maze had made the case look magical, but patient inference solved it.",
            "The robot rolled back into place with a cheerful beep. No one was accused, and the children learned that reflections can be glamorous but misleading.",
        ],
        "ending": [
            "The robot waved beneath its stars, and the glitter ribbon was placed in a drawer labeled Evidence.",
            "As the museum lights softened, the robot blinked a friendly blue light at the two detectives.",
        ],
        "problem_fact": "the exhibit disappeared near a glittering mirror maze",
        "clue_fact": "a flashback revealed that a fan and ribbon had nudged the exhibit",
        "inference_fact": "the glitter had stuck to the exhibit's wheel instead of marking a thief",
        "action_fact": "the children followed wheel marks to the service ramp",
        "outcome_fact": "the exhibit was returned and the fan was repaired",
    },
    {
        "key": "shoe_in_theater",
        "premise": [
            "Zara and Theo were junior detectives at Wonder Window Museum. They were admiring {exhibit} when the children's theater bell rang.",
            "The children's museum was full of curious sounds when {detective} and {helper} arrived. The glamorous centerpiece, {exhibit}, stood near the theater doors.",
        ],
        "problem": [
            "The bell rang three times, and the exhibit disappeared. A damp footprint crossed the floor, though the museum had no puddles.",
            "When the curtain opened, the case was empty. One tiny footprint led toward the play kitchen, and a blue feather rested on the lock.",
        ],
        "dialogue": [
            "\"The footprint proves a thief came in,\" said {helper}. \"Or a costume boot made it,\" answered {detective}. That answer made them inspect the print instead of chasing a person.",
            "\"I heard splashing,\" said {helper}. {detective} asked, \"Was it real water?\" They checked the play kitchen and found a clue beneath its pretend sink.",
        ],
        "turn": [
            "A flashback brought back the theater rehearsal: an actor had carried a shiny water bucket past the case. The glamour of the stage lights had hidden its painted wheels.",
            "In their flashback, the children saw a puppet dragon pull a prop wagon. Its blue feather had brushed the lock while the wagon rolled toward the kitchen.",
        ],
        "inference": [
            "The damp footprint had been painted on the wagon wheel. Their inference was that the prop wagon had carried the exhibit backstage.",
            "The feather matched the puppet dragon, and the wheel marks matched the footprint. The children inferred that the theater crew had moved the exhibit for the show.",
        ],
        "action": [
            "They asked the theater leader to pause rehearsal. Behind the puppet curtain, they found {exhibit safe} beside the painted wagon.",
            "{detective} and {helper} followed the wheel marks backstage. The theater leader opened a prop box and revealed {exhibit safe}.",
        ],
        "resolution": [
            "The crew had borrowed the exhibit for a costume scene but forgotten to tell the museum guide. The case was restored, and the mystery ended kindly.",
            "The theater leader apologized and returned the exhibit. The young detectives had solved the puzzle by connecting the footprint, feather, and flashback.",
        ],
        "ending": [
            "The bell rang once more, this time for a show everyone could enjoy beneath the steady museum lights.",
            "The painted wagon rested beside the case, while {exhibit} gleamed safely behind glass.",
        ],
        "problem_fact": "the exhibit vanished after a theater bell rang and a strange footprint appeared",
        "clue_fact": "a flashback showed a puppet wagon passing the display",
        "inference_fact": "the footprint came from a painted prop wheel",
        "action_fact": "the children followed the wagon marks backstage",
        "outcome_fact": "the borrowed exhibit was returned to its case",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    text = "|".join(
        [params.detective_name, params.helper_name, params.museum_name, params.exhibit_name]
    )
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> "World":
    rng = _rng_for(params)
    arc = ARCS[(params.seed or rng.randrange(len(ARCS))) % len(ARCS)]
    beats = ("premise", "problem", "dialogue", "turn", "inference", "action", "resolution", "ending")
    chosen = {}
    for i, beat in enumerate(beats):
        choices = arc[beat]
        chosen[beat] = choices[((params.seed or 0) // max(1, len(ARCS)) + i) % len(choices)]

    exhibit_safe = f"{params.exhibit_name}, safe and sound"
    rendered = {}
    for beat in beats:
        rendered[beat] = chosen[beat].format(
            detective=params.detective_name,
            helper=params.helper_name,
            exhibit=params.exhibit_name,
            **{"exhibit safe": exhibit_safe},
        )

    museum = Museum(params.museum_name, params.exhibit_name)
    world = World(museum)
    detective = world.add(
        Entity(
            params.detective_name,
            "character",
            "detective",
            "young detective",
            meters={"attention": 4.0, "confidence": 3.0},
            memes={"curiosity": 1.0},
        )
    )
    helper = world.add(
        Entity(
            params.helper_name,
            "character",
            "helper",
            "museum helper",
            meters={"attention": 3.0, "confidence": 2.0},
            memes={"curiosity": 1.0},
        )
    )
    treasure = world.add(
        Entity(
            "exhibit",
            "thing",
            "museum_exhibit",
            params.exhibit_name,
            phrase=params.exhibit_name,
            owner=params.museum_name,
            meters={"glamour": 1.0, "safe": 1.0},
        )
    )
    museum.case_open = True
    museum.clue_count = 3
    museum.mystery_solved = True
    museum.facts = {
        "arc": arc,
        "detective": detective,
        "helper": helper,
        "treasure": treasure,
        "rendered": rendered,
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "inference": arc["inference_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
    }
    world.paragraphs = [[rendered[beat]] for beat in beats]
    return world


class World:
    def __init__(self, museum: Museum) -> None:
        self.museum = museum
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def generate_prompts(world: World) -> list[str]:
    f = world.museum.facts
    return [
        "Write a child-friendly whodunit in a children's museum involving inference and glamour.",
        f"Tell a museum mystery where {f['detective'].id} and {f['helper'].id} use a flashback to find {f['treasure'].label}.",
        "Write a gentle mystery in which clues change a character's decision and the missing exhibit is safely recovered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.museum.facts
    return [
        QAItem(
            f"What disappeared from {world.museum.name}?",
            f"{f['treasure'].label} disappeared from its display, but it was later found safe.",
        ),
        QAItem(
            "What did the flashback reveal?",
            f["clue"],
        ),
        QAItem(
            "What inference did the young detectives make?",
            f["inference"],
        ),
        QAItem(
            "How was the mystery solved?",
            f"{f['action']} Then {f['outcome']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is inference?",
            "Inference is a conclusion made by connecting clues and what you already know.",
        ),
        QAItem(
            "What is glamour?",
            "Glamour is an attractive sparkle or special appearance that makes something seem exciting.",
        ),
        QAItem(
            "What is a flashback?",
            "A flashback is a return to an earlier moment that helps explain what is happening now.",
        ),
        QAItem(
            "What is a museum?",
            "A museum is a place where people can see, learn about, and sometimes touch or explore interesting objects.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:12} ({entity.type:16}) meters={meters} memes={memes}"
        )
    lines.extend(
        [
            f"  museum.name={world.museum.name}",
            f"  museum.exhibit={world.museum.exhibit}",
            f"  museum.case_open={world.museum.case_open}",
            f"  museum.clue_count={world.museum.clue_count}",
            f"  museum.mystery_solved={world.museum.mystery_solved}",
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    setting(childrens_museum),
    feature(flashback),
    theme(inference),
    theme(glamour),
    style(whodunit),
    resolved(mystery).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "childrens_museum"),
            asp.fact("feature", "flashback"),
            asp.fact("theme", "inference"),
            asp.fact("theme", "glamour"),
            asp.fact("style", "whodunit"),
            asp.fact("resolved", "mystery"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if any(symbol.name == "valid_story" for symbol in model):
        sample = generate(
            StoryParams("Luna", "Milo", "Bright Steps Museum", "the Moonbeam Crown", 7)
        )
        if sample.story and sample.story_qa and "flashback" in sample.story.lower():
            print("OK: Python story and ASP twin agree.")
            return 0
    print("MISMATCH: ASP or generated-story verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Children's museum whodunit with inference, glamour, and a flashback."
    )
    parser.add_argument("--detective-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--museum-name", choices=MUSEUMS)
    parser.add_argument("--exhibit-name", choices=EXHIBITS)
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
    detective = args.detective_name or rng.choice(NAMES)
    helper_choices = [name for name in NAMES if name != detective]
    return StoryParams(
        detective_name=detective,
        helper_name=args.helper_name or rng.choice(helper_choices),
        museum_name=args.museum_name or rng.choice(MUSEUMS),
        exhibit_name=args.exhibit_name or rng.choice(EXHIBITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            models = asp.solve(asp_program(), models=1)
            print("ASP model found." if models else "No ASP model found.")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Luna", "Milo", "Bright Steps Museum", "the Moonbeam Crown", 11),
            StoryParams("Zara", "Theo", "Little Lantern Museum", "the Starry Shoe", 23),
            StoryParams("Nia", "Finn", "Wonder Window Museum", "the Rainbow Robot", 37),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No valid story variants could be generated.")

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
