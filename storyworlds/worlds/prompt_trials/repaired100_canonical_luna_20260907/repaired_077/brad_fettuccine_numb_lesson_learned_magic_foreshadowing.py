#!/usr/bin/env python3
"""
A small pirate tale about Brad, a bowl of fettuccine, a numb hand,
and the magic of learning before the next voyage.
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

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    ship: str
    shore: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    ship: str
    shore: str
    fettuccine_state: str = "hot in a covered pot"
    hand_state: str = "ready"
    lesson_learned: bool = False
    magic_awake: bool = False
    foreshadowing_seen: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Brad", "Luna", "Pip", "Mara", "Toby", "Nell", "Finn", "Rook"]
SHIPS = ["the Moonlit Sardine", "the Copper Gull", "the Brave Noodle", "the Starry Kettle"]
SHORES = ["Whispering Cove", "Lantern Reef", "Bluebell Island", "the Misty Jetty"]

ADVENTURES = [
    {
        "title": "the silver fork",
        "opening": "a silver fork glimmered beside a steaming pot of fettuccine",
        "warning": "a blue spark danced on the fork's handle",
        "mistake": "Brad grabbed the fork before checking whether it was hot",
        "risk": "the fork had been resting in boiling water, so a quick grab could burn his hand",
        "numb": "his fingers tingled, then felt numb from the icy charm hidden in the handle",
        "clue": "the little blue spark appeared whenever the fork grew dangerously hot",
        "magic": "the charm cooled the fork just long enough for Brad to set it safely on a wooden board",
        "repair": "called Cook Mira, wrapped the handle in a thick cloth, and moved the pot away from the edge",
        "ending": "the fettuccine steamed safely while the silver fork shone on its wooden board",
    },
    {
        "title": "the galley bell",
        "opening": "a brass bell rang beside a covered pot of fettuccine",
        "warning": "three pale lights blinked beneath the bell",
        "mistake": "Brad lifted the lid at once because he thought supper was ready",
        "risk": "the pot still held boiling water, and lifting its lid too quickly could send a hot cloud into his face",
        "numb": "his hand went numb when the bell's cold spell touched his knuckles",
        "clue": "the lights always blinked three times before the steam became safe",
        "magic": "the bell's old magic held the lid down until the third blink",
        "repair": "waited for the lights, used a dry cloth, and asked Cook Mira to check the pot",
        "ending": "the bell fell quiet, and warm fettuccine filled every hungry pirate's bowl",
    },
    {
        "title": "the moonlit noodle",
        "opening": "one long strand of fettuccine curled like a rope across the galley floor",
        "warning": "moonlight made the noodle sparkle with tiny runes",
        "mistake": "Brad tugged it hard, thinking a sea sprite had tied the galley shut",
        "risk": "the strand led straight to a hot pot, and pulling it could tip the pot over",
        "numb": "his palm grew numb when the rune at the noodle's end flashed",
        "clue": "the sparkle pointed toward the pot instead of toward the door",
        "magic": "the enchanted noodle curled into a gentle arrow and showed him where to stop",
        "repair": "let go, warned the crew, and used tongs to lift the stray noodle from a safe distance",
        "ending": "the moonlit strand rested in the bowl while the galley floor stayed dry",
    },
    {
        "title": "the captain's supper chart",
        "opening": "a parchment chart lay beside a pot of fettuccine on the captain's table",
        "warning": "golden letters appeared whenever steam touched the page",
        "mistake": "Brad read the supper chart as a map and began following its dotted line",
        "risk": "the dotted line led around the hot pot, so reaching across it could scald him",
        "numb": "his hand felt numb after brushing the chart's chilly enchanted edge",
        "clue": "the words SAUCE, BOWL, and SPOON rose from the parchment",
        "magic": "the chart drew a glowing circle around the safe side of the pot",
        "repair": "stepped around the table, used a long spoon, and told the crew what the letters meant",
        "ending": "the chart showed a supper route, and every pirate reached the fettuccine safely",
    },
    {
        "title": "the frost coin",
        "opening": "a blue coin sat beside a pot of fettuccine bubbling in the galley",
        "warning": "frost spread from the coin in the shape of a tiny compass",
        "mistake": "Brad picked it up, believing it was a lucky treasure",
        "risk": "the coin's cold magic could numb his fingers, making it hard to notice the pot's heat",
        "numb": "his thumb and forefinger became numb as the frost climbed his hand",
        "clue": "the compass arrow pointed away from the coin and toward a pair of wooden tongs",
        "magic": "the coin whispered one clear word, 'TONGS,' through a puff of blue mist",
        "repair": "set the coin down, told the captain, and used the tongs instead of his bare hand",
        "ending": "the frost coin slept in a locked chest while fettuccine curled onto safe plates",
    },
]

OPENINGS = [
    "At sunset, aboard",
    "One windy evening on",
    "As the tide whispered beside",
    "Before the moon rose over",
    "During a quiet watch aboard",
]

REACTIONS = [
    'Brad swallowed. "I thought treasure always wanted to be picked up," he said.',
    'Brad rubbed his numb fingers. "Next time I will ask before I grab," he promised.',
    '"A pirate needs more than courage," Brad said. "A pirate needs a careful plan."',
    'Brad looked at the steaming pot. "The warning was there. I was simply too hurried to see it."',
]

CODAS = [
    "That night, Brad painted a bright warning stripe beside the galley.",
    "Before bed, he taught the youngest deckhand the safe-hand rule.",
    "The captain pinned the clue above the stove so no hurried pirate would miss it.",
    "From then on, Brad checked the magic, the heat, and the handle before touching anything.",
]

LESSONS = [
    "The lesson learned was simple: bravery means stopping to check, not grabbing first.",
    "Brad learned that a warning is a gift, especially when magic makes danger hard to see.",
    "The lesson learned was that careful pirates use tools and ask for help near hot pots.",
    "Brad learned that a small pause can protect a hand, a meal, and an entire crew.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Brad, fettuccine, and a magical pirate lesson.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--ship", choices=SHIPS)
    parser.add_argument("--shore", choices=SHORES)
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
        name=args.name or rng.choice(NAMES),
        ship=args.ship or rng.choice(SHIPS),
        shore=args.shore or rng.choice(SHORES),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError("Brad's pirate name must come from the crew registry.")
    if params.ship not in SHIPS:
        raise StoryError("That ship is not in the harbor registry.")
    if params.shore not in SHORES:
        raise StoryError("That shore is not charted in this little world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    adventure = rng.choice(ADVENTURES)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS)
    lesson = rng.choice(LESSONS)
    coda = rng.choice(CODAS)

    hero = Character(
        name=params.name,
        kind="young pirate",
        meters={"courage": 0.7, "care": 0.3, "hand_sensation": 1.0},
        memes={"curious": 1.0, "helpful": 0.8},
    )
    world = World(hero=hero, ship=params.ship, shore=params.shore)
    world.foreshadowing_seen = True
    world.facts["foreshadowing"] = adventure["warning"]
    world.facts["risk"] = adventure["risk"]
    world.facts["incident"] = adventure["title"]

    lines = [
        f"{opening} {params.ship}, Brad the young pirate kept watch over the galley.",
        f"Beyond the rail, {params.shore} glimmered, but {adventure['opening']}.",
        f"Before Brad could think, {adventure['warning']}.",
        f"{adventure['mistake']}.",
        f"At once, {adventure['numb']}. The warning he had almost missed was real: {adventure['risk']}.",
        reaction,
        f"Then Brad noticed the clue: {adventure['clue']}.",
        f"The old galley magic answered. {adventure['magic']}.",
        f"Brad breathed slowly, and {adventure['repair']}.",
    ]

    world.hand_state = "safe after the numbness passed"
    world.fettuccine_state = "cooked and served safely"
    world.lesson_learned = True
    world.magic_awake = True
    world.hero.meters["care"] = 1.0
    world.hero.meters["hand_sensation"] = 1.0
    world.facts["clue"] = adventure["clue"]
    world.facts["magic"] = adventure["magic"]
    world.facts["repair"] = adventure["repair"]
    world.facts["lesson"] = lesson
    world.facts["ending"] = adventure["ending"]

    lines.extend([
        lesson,
        coda,
        f"By moonrise, {adventure['ending']}.",
    ])
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Tell a pirate tale about Brad, fettuccine, and a numb hand aboard {params.ship}.",
        f"Write a magical story set near {params.shore} with foreshadowing, a safe repair, and a lesson learned.",
        "Show how a warning changes a pirate's choice instead of merely decorating the scene.",
    ]

    story_qa = [
        QAItem(
            question=f"What danger did Brad face in {adventure['title']}?",
            answer=f"Brad faced danger because {adventure['risk']}.",
        ),
        QAItem(
            question="Why did Brad's hand feel numb?",
            answer=f"Brad's hand felt numb because {adventure['numb']}.",
        ),
        QAItem(
            question="What foreshadowing warned Brad before the trouble?",
            answer=f"The foreshadowing was that {adventure['warning']}.",
        ),
        QAItem(
            question="How did magic help Brad?",
            answer=f"The magic helped when {adventure['magic']}.",
        ),
        QAItem(
            question="What lesson did Brad learn?",
            answer=lesson,
        ),
        QAItem(
            question="How did Brad make the galley safe?",
            answer=f"Brad made the galley safe when he {adventure['repair']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is fettuccine?",
            answer="Fettuccine is a flat pasta usually served with sauce or other toppings.",
        ),
        QAItem(
            question="What does numb mean?",
            answer="Numb means having little or no feeling in part of the body for a while.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an earlier clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is an imaginary power that can make unusual things happen according to the story's rules.",
        ),
        QAItem(
            question="What should someone do near a hot pot?",
            answer="Someone should pause, use a safe tool or thick dry cloth, and ask a responsible adult or helper when needed.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        w = sample.world
        print("\n--- trace ---")
        print(f"hero={w.hero.name}, kind={w.hero.kind}")
        print(f"meters={w.hero.meters}, memes={w.hero.memes}")
        print(f"ship={w.ship}, shore={w.shore}")
        print(
            f"fettuccine_state={w.fettuccine_state}, hand_state={w.hand_state}, "
            f"lesson_learned={w.lesson_learned}, magic_awake={w.magic_awake}, "
            f"foreshadowing_seen={w.foreshadowing_seen}"
        )
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_ship(S) :- ship(S).
valid_shore(S) :- shore(S).
safe_lesson :- lesson_learned, magic_awake, foreshadowing_seen.
#show valid_ship/1.
#show valid_shore/1.
#show safe_lesson/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("ship", ship) for ship in SHIPS]
    facts += [asp.fact("shore", shore) for shore in SHORES]
    facts += [
        asp.fact("lesson_learned"),
        asp.fact("magic_awake"),
        asp.fact("foreshadowing_seen"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_registry() -> tuple[set[tuple], set[tuple]]:
    import asp
    model = asp.one_model(asp_program("#show valid_ship/1.\n#show valid_shore/1."))
    return (
        set(asp.atoms(model, "valid_ship")),
        set(asp.atoms(model, "valid_shore")),
    )


def asp_verify() -> int:
    py_ships = {(ship,) for ship in SHIPS}
    py_shores = {(shore,) for shore in SHORES}
    cl_ships, cl_shores = asp_valid_registry()
    if py_ships != cl_ships or py_shores != cl_shores:
        print("MISMATCH between clingo and Python registries.")
        if py_ships != cl_ships:
            print("  ships:", sorted(py_ships), sorted(cl_ships))
        if py_shores != cl_shores:
            print("  shores:", sorted(py_shores), sorted(cl_shores))
        return 1

    params = StoryParams(name="Brad", ship=SHIPS[0], shore=SHORES[0], seed=77)
    sample = generate(params)
    required = ("Brad", "fettuccine", "numb", "lesson", "magic")
    if not all(word.lower() in sample.story.lower() for word in required):
        print("Generated story missed a required narrative element.")
        return 1
    print("OK: ASP registry parity and generated-story checks passed.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                name=NAMES[i % len(NAMES)],
                ship=SHIPS[i % len(SHIPS)],
                shore=SHORES[i % len(SHORES)],
            )
            for i in range(len(SHIPS) * len(SHORES))
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_ship/1.\n#show valid_shore/1.\n#show safe_lesson/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_ship/1.\n#show valid_shore/1.\n#show safe_lesson/0."))
        for name in ("valid_ship", "valid_shore", "safe_lesson"):
            for atom in asp.atoms(model, name):
                print(name, atom)
        return

    samples: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 0
    for i, params in enumerate(generation_params(args)):
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
