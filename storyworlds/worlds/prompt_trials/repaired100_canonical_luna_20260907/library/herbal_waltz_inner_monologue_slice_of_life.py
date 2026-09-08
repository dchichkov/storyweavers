#!/usr/bin/env python3
"""A small herbal shop story about a waltz, a shy question, and a shared blend."""

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
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    helper: str = "Mara"
    herb: str = "lemon_balm"
    dance: str = "waltz"
    approach: str = "ask"
    seed: int = 777


HERBS = {
    "lemon_balm": {
        "name": "lemon balm",
        "scent": "bright lemon",
        "use": "a gentle evening tea",
        "measure": 2,
        "line": "The leaves smelled like a sunny window.",
    },
    "mint": {
        "name": "mint",
        "scent": "cool mint",
        "use": "a fresh tea for after dancing",
        "measure": 3,
        "line": "The mint leaves made the jar smell like rain.",
    },
    "chamomile": {
        "name": "chamomile",
        "scent": "warm apples",
        "use": "a calm tea before bed",
        "measure": 4,
        "line": "The little flowers looked like stars in a basket.",
    },
}

APPROACHES = ("ask", "guess")
NAMES = ("Luna", "Mara", "Ivo", "Nell", "Tavi", "Suri")
PROMPT = (
    "Write a gentle slice-of-life children's story about an herbal shop, "
    "a waltz, and a character who learns to ask for help."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity(
                "hero",
                params.hero,
                "character",
                "shop",
                memes={"nervousness": 1.0, "confidence": 0.2, "trust": 0.5},
            ),
            "helper": Entity(
                "helper",
                params.helper,
                "character",
                "shop",
                memes={"patience": 1.0, "trust": 0.5},
            ),
            "counter": Entity(
                "counter",
                "the wooden counter",
                "place",
                "shop",
                meters={"clear": 1},
            ),
            "jar": Entity(
                "jar",
                "the herb jar",
                "container",
                "counter",
                meters={"open": 0, "scoops": 0},
            ),
            "music": Entity(
                "music",
                "the old waltz record",
                "thing",
                "shop",
                meters={"playing": 0, "tempo": 3},
            ),
            "tin": Entity(
                "tin",
                "the tea tin",
                "container",
                "counter",
                meters={"filled": 0, "labelled": 0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def say(self, speaker: str, text: str) -> None:
        name = self.entities[speaker].label
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(kind="speech", text=f'"{text}" {name} {tag}.', state=self.snapshot())
        )

    def think(self, speaker: str, text: str) -> None:
        name = self.entities[speaker].label
        self.history.append(
            Event(kind="inner_monologue", text=f"{name} thought, {text}", state=self.snapshot())
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(
                    question=event.question,
                    answer=f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="What kind of place is an herbal shop?",
                    answer="It is a shop where dried plants and herbs are kept, measured, and prepared for uses such as tea.",
                ),
                QAItem(
                    question="What is a waltz?",
                    answer="A waltz is a dance with a gentle three-beat rhythm.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams) -> None:
    if params.herb not in HERBS:
        raise StoryError("Choose a known herb.")
    if params.dance != "waltz":
        raise StoryError("This story domain uses a waltz.")
    if params.approach not in APPROACHES:
        raise StoryError("Choose either ask or guess.")
    if params.hero == params.helper:
        raise StoryError("The two characters need different names.")
    for name in (params.hero, params.helper):
        if not name or not name[0].isupper() or not name.isalpha():
            raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    herb = HERBS[params.herb]
    world.entities["jar"].label = f"the jar of {herb['name']}"
    world.entities["hero"].meters["needed_scoops"] = herb["measure"]
    return world


def prepare_herb(world: World) -> None:
    hero = world.entities["hero"]
    jar = world.entities["jar"]
    tin = world.entities["tin"]
    needed = int(hero.meters["needed_scoops"])
    if jar.meters["open"] != 1:
        raise StoryError("The herb jar must be opened before measuring.")
    if jar.meters["scoops"] != needed:
        raise StoryError("The recipe needs the measured herb before the tin can be filled.")
    tin.meters["filled"] = 1
    tin.meters["labelled"] = 1
    hero.memes["nervousness"] = 0.0
    hero.memes["confidence"] = 1.0
    world.entities["helper"].memes["trust"] = 1.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    jar = world.entities["jar"]
    tin = world.entities["tin"]
    music = world.entities["music"]
    h = hero.label
    m = helper.label
    herb = HERBS[params.herb]
    world.narrate(
        "beginning",
        f"Late in the afternoon, {h} swept the floor of the little herbal shop while {m} "
        f"put {herb['name']} into glass jars. Rain tapped the window, and an old record waited "
        "beside the counter.",
    )
    world.think(
        "hero",
        f'"I know this recipe," {h} thought. "I only have to ask where the small scoop is."',
    )
    world.say("helper", "The evening tea is our last job before we dance.")
    world.say("hero", "I can make the herbal blend.")
    world.think(
        "hero",
        f'"I want to sound sure," {h} thought. "Maybe the scoop is obvious to everyone but me."',
    )
    world.narrate(
        "tension",
        f"{h} found the jar of {herb['name']} and three small tools on the wooden counter. "
        "The narrowest scoop had no label.",
        question="Why did making the tea become difficult for Luna?",
        cause=f"{h} knew which herb to use but did not know which scoop matched the recipe.",
        result="The unlabeled tools made a simple shop task uncertain.",
    )
    if params.approach == "guess":
        world.think(
            "hero",
            f'"I will choose one," {h} thought. "If I ask, I might stop the music before it starts."',
        )
        world.say("hero", "This scoop looks right.")
        jar.meters["open"] = 1
        jar.meters["scoops"] = 1
        world.narrate(
            "wrong_measure",
            f"{h} opened the jar and tried a scoop. The amount looked too small beside the recipe card.",
        )
        world.say("helper", "That scoop is for the strong winter mixture.")
        world.say("hero", "I guessed because I wanted to be ready.")
        world.think(
            "hero",
            f'"My guess did not save time," {h} thought. "It only hid the question."',
        )
    else:
        world.say("hero", "Mara, may I ask which scoop the recipe needs?")
        world.say("helper", "Of course. The middle scoop is marked by a tiny blue dot.")
        world.think(
            "hero",
            f'"The question was smaller than my worry," {h} thought. "Now I can begin."',
        )
        jar.meters["open"] = 1

    world.say("hero", "Could you show me how much {0} to measure?".format(herb["name"]))
    world.say("helper", "Two little scoops for this blend. Watch the level, not the heap.")
    jar.meters["scoops"] = herb["measure"]
    world.narrate(
        "turn",
        f"{m} pointed to the blue dot. {h} measured {herb['measure']} level scoops of "
        f"{herb['name']} into the tea tin, and the bright scent rose between them.",
        question="How did Luna learn to measure the herb correctly?",
        cause=f"{m} explained that the blue-dotted middle scoop was right and showed {h} how to keep it level.",
        result=f"{h} measured {herb['measure']} level scoops of {herb['name']}.",
    )
    music.meters["playing"] = 1
    world.say("helper", "The record is ready. Shall we try the waltz?")
    world.say("hero", "I would like to, but I may step on your toes.")
    world.say("helper", "Then we will take small steps and count together.")
    world.think(
        "hero",
        f'"Small steps," {h} thought. "That is a kind recipe for dancing too."',
    )
    world.say("hero", "One, two, three.")
    world.say("helper", "One, two, three. You are doing it.")
    tin.meters["filled"] = 1
    tin.meters["labelled"] = 1
    prepare_herb(world)
    world.narrate(
        "resolution",
        f"The tea tin was filled and labelled before the music reached its second verse. "
        f"{h} and {m} moved around the counter in a quiet {params.dance}, careful as leaves "
        "turning in a spoon.",
        question="What changed for Luna by the end of the afternoon?",
        cause=f"{h} asked for the scoop, measured the herb with {m}, and practiced the dance in small steps.",
        result=f"{h} finished the herbal tea and joined {m} in a confident waltz.",
    )
    world.say("helper", "You asked when you needed help, and you kept dancing.")
    world.say("hero", "The question helped with both jobs.")
    world.think(
        "hero",
        f'"The shop feels warmer now," {h} thought. "Maybe confidence can begin with three small beats."',
    )
    world.narrate(
        "ending",
        f"Outside, the rain softened. Inside, the labelled tin rested beside the blue-dotted scoop "
        f"while {h} and {m} finished their waltz between the shelves.",
        question="What showed that the problem was truly solved?",
        cause=f"The tea tin was filled and labelled, and {h} could dance without hiding uncertainty.",
        result="The correct herb waited on the counter while both friends moved together to the music.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    if world.entities["tin"].meters.get("filled") != 1:
        raise StoryError("The herbal tea must be prepared.")
    if world.entities["tin"].meters.get("labelled") != 1:
        raise StoryError("The tea tin must be labelled.")
    if world.entities["music"].meters.get("playing") != 1:
        raise StoryError("The waltz must happen.")
    speech = [event for event in world.history if event.kind == "speech"]
    thoughts = [event for event in world.history if event.kind == "inner_monologue"]
    if len(speech) < 10 or len(thoughts) < 3:
        raise StoryError("The story needs sustained dialogue and inner monologue.")
    if not any(event.question for event in world.history):
        raise StoryError("The story needs grounded questions.")
    if not any("ask" in event.text.lower() for event in thoughts):
        raise StoryError("The inner monologue must show the character's changing choice.")


ASP_RULES = """
usable(H) :- herb(H), scoop(H,N), N > 0.
ready(H) :- usable(H), labelled(H).
#show ready/1.
"""


def asp_facts() -> str:
    from asp import fact

    facts = []
    for key, value in HERBS.items():
        facts.append(fact("herb", key))
        facts.append(fact("scoop", key, value["measure"]))
    facts.append(fact("labelled", "lemon_balm"))
    facts.append(fact("labelled", "mint"))
    facts.append(fact("labelled", "chamomile"))
    return "\n".join(facts)


def asp_ready() -> set[tuple]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "ready"))


def verify() -> None:
    expected = {(key,) for key in HERBS}
    actual = asp_ready()
    if actual != expected:
        raise StoryError("Python and ASP disagree about ready herbal blends.")
    count = 0
    for herb in HERBS:
        for approach in APPROACHES:
            params = StoryParams(herb=herb, approach=approach, seed=17)
            check_sample(generate(params))
            count += 1
    print(f"OK: {count} story states; {len(actual)} ASP-ready herbal blends.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--herb", choices=tuple(HERBS))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != hero])
    params = StoryParams(
        hero=hero,
        helper=helper,
        herb=args.herb or rng.choice(tuple(HERBS)),
        approach=args.approach or rng.choice(APPROACHES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_ready())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            params_list = [
                StoryParams(
                    hero=args.hero or "Luna",
                    helper=args.helper or "Mara",
                    herb=herb,
                    approach=approach,
                    seed=args.seed,
                )
                for herb in HERBS
                for approach in APPROACHES
            ]
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
