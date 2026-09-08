#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about a bargain, a caramel stand, and cheerful problem solving.
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
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"energy": 1.0, "worry": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"cleverness": 0.0, "humor": 0.0, "kindness": 0.0})
    inventory: list[str] = field(default_factory=list)


@dataclass
class Caramel:
    pieces: int
    flavor: str = "golden"
    wrapped: bool = True
    shared: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"sweetness": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"fairness": 0.0})


@dataclass
class Stand:
    name: str
    place: str
    sign: str
    sturdy: bool = True
    open: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"safety": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"welcome": 1.0})


@dataclass
class StoryParams:
    place: str = "the dappled village lane"
    hero_name: str = "Luna"
    hero_kind: str = "little mouse"
    friend_name: str = "Pip"
    friend_kind: str = "small duck"
    scenario_id: int = 0
    rhyme_mode: int = 0
    joke_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    opening: str
    problem: str
    attempt: str
    clue: str
    solution: str
    bargain: str
    ending: str
    lesson: str


SCENARIOS = (
    Scenario(
        opening="Luna and Pip rolled a tiny caramel stand into the lane for the market-day crowd.",
        problem="A gust flipped the bargain sign upside down, so every shopper thought five buttons bought one caramel and one caramel bought five buttons.",
        attempt="Luna tried to hold the sign straight with her tail, but the sign wiggled like a pancake in a storm",
        clue="Pip noticed that the stand's spare spoon could slide through two holes in the signboard",
        solution="They tied the sign to the spoon and used a ribbon as a bright arrow pointing to the true prices.",
        bargain="The bargain became clear: one button bought one caramel, while three buttons bought four small pieces to share.",
        ending="the sign stood proudly, and the arrow pointed down instead of up",
        lesson="a fair bargain needs a clear sign and a calm look",
    ),
    Scenario(
        opening="At sunrise, Luna arranged caramel squares on a little stand beneath a striped umbrella.",
        problem="The umbrella leaned over the sweets, and its shadow made the bargain list look like a row of sleepy worms.",
        attempt="Pip poked the umbrella and said, 'Wake up!' but the umbrella only drooped farther",
        clue="Luna saw a crate beside the stand with two matching wooden blocks",
        solution="They placed one block under each back leg, then checked the stand from a shopper's height.",
        bargain="Now the bargain was easy to read: two buttons for a caramel, or five buttons for three pieces.",
        ending="the umbrella stood tall while the caramel gleamed like little suns",
        lesson="checking a problem from another person's view can reveal the best fix",
    ),
    Scenario(
        opening="Luna and Pip opened their caramel stand beside the village pond, where frogs wore their finest hats.",
        problem="A frog hopped onto the bargain basket and mixed the large pieces with the small ones.",
        attempt="Luna sorted the pieces by size, but one frog mistook her sorting hat for a caramel bowl",
        clue="Pip heard the frogs croak in two different rhythms",
        solution="They made two picture cards: a big caramel for three buttons and a small caramel for one button.",
        bargain="The new bargain was fair because everyone could see which piece matched which price.",
        ending="the frogs applauded with their feet, making the pond ripple",
        lesson="pictures and simple choices help a bargain make sense",
    ),
    Scenario(
        opening="On a breezy afternoon, Luna painted a cheerful caramel stand with a yellow door.",
        problem="The door stuck whenever someone asked for a bargain, so shoppers had to squeeze through like noodles.",
        attempt="Pip pulled the door with both wings and accidentally spun around like a teacup",
        clue="Luna found a caramel wrapper caught under the lower hinge",
        solution="They lifted the door gently, removed the wrapper, and rubbed the hinge with a little safe oil.",
        bargain="They offered a kind bargain to the waiting crowd: the first three shoppers received one extra small piece.",
        ending="the door swung wide, and Pip bowed so low that his hat fell into a basket",
        lesson="small causes can make big trouble, and careful looking can solve it",
    ),
    Scenario(
        opening="Luna set up a caramel stand at the end of a lane lined with lavender.",
        problem="A cheeky breeze carried the bargain cards away one by one.",
        attempt="Pip chased the cards, but he ran in circles and returned holding a recipe for turnip soup",
        clue="Luna saw clothespins clipped to a nearby washing line",
        solution="They clipped each bargain card to a short string and anchored the strings with smooth stones.",
        bargain="The customers could choose a neat bargain without chasing a single card.",
        ending="the cards fluttered politely while Pip sold one caramel to a very serious beetle",
        lesson="good tools make a tricky job lighter and funnier",
    ),
    Scenario(
        opening="Before the noon bell, Luna placed warm caramel on her stand and polished the little bell.",
        problem="The bell would not ring when a bargain was made, so shoppers did not know whose turn it was.",
        attempt="Pip shouted 'Ding!' so loudly that a sleepy crow dropped its feather",
        clue="Luna noticed that the bell clapper was resting against a soft ribbon",
        solution="They moved the ribbon aside and tied it to the stand post instead of the bell.",
        bargain="Each fair bargain ended with one gentle ding and one grateful smile.",
        ending="the bell rang clearly, and the crow wore the feather as a mustache",
        lesson="a quiet adjustment can solve what a loud fuss cannot",
    ),
)


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, value: object) -> object:
        self.entities[eid] = value
        return value

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("Character names must not be empty.")
    if params.hero_name.strip().lower() == params.friend_name.strip().lower():
        raise StoryError("The hero and friend need different names.")
    if not 0 <= params.scenario_id < len(SCENARIOS):
        raise StoryError("scenario_id must select a known caramel-stand problem.")

    scenario = SCENARIOS[params.scenario_id]
    world = World(params.place)
    hero = world.add("hero", Character(params.hero_name, params.hero_kind))
    friend = world.add("friend", Character(params.friend_name, params.friend_kind))
    candy = world.add("caramel", Caramel(pieces=12))
    stand = world.add(
        "stand",
        Stand("caramel stand", params.place, "BARGAIN! FAIR CARAMEL HERE")
    )

    hero.memes["cleverness"] = 0.4
    friend.memes["humor"] = 0.5
    hero.meters["worry"] = 0.2

    world.say(f"At {params.place}, {scenario.opening}")
    world.say(
        f"'{params.hero_name}, a bargain should be easy to see,' said {params.friend_name}. "
        f"'Yes,' said {params.hero_name}, 'unless the sign has learned to dance.'"
    )

    world.para()
    world.say(scenario.problem)
    world.say(f"At first, {params.hero_name} {scenario.attempt}.")
    world.say(
        f"'{params.friend_name}, can you spot a clue?' asked {params.hero_name}. "
        f"'{params.hero_name}, I can spot three,' said {params.friend_name}, 'but one is wearing a hat.'"
    )
    world.say(f"The useful clue was this: {scenario.clue}.")
    world.say(
        f"That clue helped {params.hero_name} and {params.friend_name} understand that "
        f"the problem needed a careful fix, not a wild guess."
    )

    world.para()
    world.say(f"Together, they solved it. {scenario.solution}")
    world.say(
        f"Then {params.hero_name} announced, 'Our bargain is ready!' "
        f"{params.friend_name} replied, 'And this time the sign will not sell the stand by mistake.'"
    )
    world.say(scenario.bargain)

    stand.open = True
    candy.shared = True
    candy.memes["fairness"] = 1.0
    hero.memes["cleverness"] = 1.0
    hero.memes["kindness"] = 1.0
    friend.memes["humor"] = 1.0
    hero.meters["worry"] = 0.0
    hero.meters["energy"] -= 0.2
    friend.meters["energy"] -= 0.2
    world.events.extend(["problem_seen", "clue_found", "solution_made", "fair_bargain"])
    world.say(scenario.ending)

    world.para()
    if params.rhyme_mode % 3 == 0:
        world.say(
            f"So sing, little lane, of {params.hero_name} and {params.friend_name}: "
            f"they looked, they thought, and they solved it again."
        )
    elif params.rhyme_mode % 3 == 1:
        world.say(
            f"Look, look, what a sight: the caramel stand was fair and bright. "
            f"{params.hero_name} smiled, and {params.friend_name} bowed just right."
        )
    else:
        world.say(
            f"No muddle, no fuss, no grumble or fright; "
            f"the fair little bargain made everyone light."
        )
    world.say(f"Their lesson was simple: {scenario.lesson}.")

    world.facts.update(
        hero=hero,
        friend=friend,
        caramel=candy,
        stand=stand,
        problem=scenario.problem,
        clue=scenario.clue,
        solution=scenario.solution,
        bargain=scenario.bargain,
        ending=scenario.ending,
        lesson=scenario.lesson,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    return [
        f"Write a nursery-rhyme story about {hero.name} and {friend.name} solving this caramel-stand problem: {f['problem']}",
        f"Show how a clue changes the bargain at the caramel stand: {f['clue']}",
        f"Use gentle humor and problem solving to tell how {hero.name} and {friend.name} make a fair bargain.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    friend: Character = f["friend"]
    return [
        QAItem(
            question=f"What problem did {hero.name} and {friend.name} face at the caramel stand?",
            answer=f"They faced this problem: {f['problem']}"
        ),
        QAItem(
            question="What clue helped them solve the problem?",
            answer=f"The clue was that {f['clue']}. It pointed them toward a careful solution."
        ),
        QAItem(
            question="How did they fix the stand's trouble?",
            answer=f"They fixed it this way: {f['solution']}"
        ),
        QAItem(
            question="What was the final bargain?",
            answer=f"The final bargain was: {f['bargain']}"
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, {f['ending']}. The friends learned that {f['lesson']}"
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bargain?",
            answer="A bargain is an agreement in which something is exchanged for a fair price or useful promise."
        ),
        QAItem(
            question="What is caramel?",
            answer="Caramel is a sweet treat made by heating sugar until it becomes golden and soft or firm."
        ),
        QAItem(
            question="Why is problem solving useful?",
            answer="Problem solving helps people notice what is wrong, find clues, and choose a safe way to make things better."
        ),
        QAItem(
            question="What makes a good joke in a nursery rhyme?",
            answer="A good nursery-rhyme joke is gentle, surprising, and easy to picture without making anyone feel hurt."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_entity(H).
friend(F) :- friend_entity(F).
caramel(C) :- caramel_entity(C).
stand(S) :- stand_entity(S).
open_stand(S) :- stand(S), opened(S).
fair_bargain(B) :- bargain(B), solved.
served(C) :- caramel(C), fair_bargain(_).
happy(H) :- hero(H), solved.
happy(F) :- friend(F), solved.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero_entity", "hero"),
            asp.fact("friend_entity", "friend"),
            asp.fact("caramel_entity", "caramel"),
            asp.fact("stand_entity", "stand"),
            asp.fact("opened", "stand"),
            asp.fact("bargain", "clear_bargain"),
            asp.fact("solved"),
        ]
    )


def asp_program(show: str = "#show fair_bargain/1. #show happy/1. #show served/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery-rhyme caramel stand storyworld."
    )
    parser.add_argument("--place", default=None)
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
        place=args.place or rng.choice(
            ["the dappled village lane", "the pond-side path", "the lavender square"]
        ),
        hero_name=rng.choice(["Luna", "Mabel", "Nell", "Tilly", "Poppy"]),
        hero_kind=rng.choice(["little mouse", "small rabbit", "young fox", "tiny badger"]),
        friend_name=rng.choice(["Pip", "Boo", "Doodle", "Wren", "Bunny"]),
        friend_kind=rng.choice(["small duck", "cheerful mole", "bluebird", "round hedgehog"]),
        scenario_id=rng.randrange(len(SCENARIOS)),
        rhyme_mode=rng.randrange(9),
        joke_mode=rng.randrange(6),
        ending_mode=rng.randrange(4),
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


def dump_trace(world: World) -> str:
    hero: Character = world.entities["hero"]
    friend: Character = world.entities["friend"]
    caramel: Caramel = world.entities["caramel"]
    stand: Stand = world.entities["stand"]
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.setting}",
            f"hero: {hero.name} ({hero.kind}) meters={hero.meters} memes={hero.memes}",
            f"friend: {friend.name} ({friend.kind}) meters={friend.meters} memes={friend.memes}",
            f"caramel: pieces={caramel.pieces} shared={caramel.shared} memes={caramel.memes}",
            f"stand: open={stand.open} sturdy={stand.sturdy} sign={stand.sign!r}",
            f"events: {world.events}",
        ]
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


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    fair = asp.atoms(model, "fair_bargain")
    served = asp.atoms(model, "served")
    happy = asp.atoms(model, "happy")
    if ("clear_bargain",) not in fair:
        print("MISMATCH: ASP did not derive the fair bargain.")
        return 1
    if ("caramel",) not in served:
        print("MISMATCH: ASP did not derive served caramel.")
        return 1
    if ("hero",) not in happy or ("friend",) not in happy:
        print("MISMATCH: ASP did not derive happy characters.")
        return 1
    sample = generate(StoryParams())
    if not sample.story.strip() or "caramel" not in sample.story.lower():
        print("MISMATCH: generated story is incomplete.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        model = asp.one_model(asp_program())
        print("fair_bargain:", asp.atoms(model, "fair_bargain"))
        print("served:", asp.atoms(model, "served"))
        print("happy:", asp.atoms(model, "happy"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(
                place="the dappled village lane",
                hero_name="Luna",
                hero_kind="little mouse",
                friend_name="Pip",
                friend_kind="small duck",
                scenario_id=i,
                rhyme_mode=i,
                joke_mode=i,
                ending_mode=i,
            )
            for i in range(len(SCENARIOS))
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = [
            generate(resolve_params(args, random.Random(base_seed + i)))
            for i in range(max(0, args.n))
        ]

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
