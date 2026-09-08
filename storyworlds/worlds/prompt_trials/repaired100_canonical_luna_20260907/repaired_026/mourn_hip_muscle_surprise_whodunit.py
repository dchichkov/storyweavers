#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
while _root and not os.path.exists(os.path.join(_root, "results.py")):
    parent = os.path.dirname(_root)
    if parent == _root:
        break
    _root = parent
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: str | None = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    seed: int | None = None
    detective: str = "Luna"
    partner: str = "Milo"
    coach: str = "Coach Fern"
    place: str = "the moonlit gym"
    object_name: str = "the silver victory pin"


DETECTIVES = ["Luna", "Mira", "Nell", "Pia", "Sora"]
PARTNERS = ["Milo", "Theo", "Jun", "Pip", "Ash"]
COACHES = ["Coach Fern", "Coach Rowan", "Coach Hazel", "Coach Briar"]
PLACES = [
    "the moonlit gym",
    "the old dance hall",
    "the riverside training room",
]
OBJECTS = [
    "the silver victory pin",
    "the blue champion badge",
    "the little gold whistle",
]
CASES = [
    {
        "title": "the vanished warm-up medal",
        "clue": "a crescent of chalk dust beside the bench",
        "suspect": "the quiet trophy cat",
        "muscle": "a sore hip muscle",
        "surprise": "the missing medal was tucked inside the cat's hollow toy drum",
        "truth": "The cat had knocked it there while chasing a ribbon, and a draft had rolled the drum under the bench.",
        "ending": "the medal returned to the notice board, shining above a row of honest names",
    },
    {
        "title": "the silent whistle",
        "clue": "a faint peppermint smell near the equipment shelf",
        "suspect": "the new groundskeeper",
        "muscle": "a tired hip muscle",
        "surprise": "the whistle was hidden in a warm-up basket beneath a folded towel",
        "truth": "The groundskeeper had moved it to stop a puppy from chewing the cord, then forgot to tell anyone.",
        "ending": "the whistle gave one bright peep as everyone laughed at the harmless mystery",
    },
    {
        "title": "the badge behind the mirror",
        "clue": "a clean oval mark on the dusty floor",
        "suspect": "the visiting drummer",
        "muscle": "a tight hip muscle",
        "surprise": "the badge was balanced behind the tall practice mirror",
        "truth": "A sweeping mop had pushed it there, while the drummer had only borrowed the mirror to find a lost feather.",
        "ending": "the badge rested safely in its velvet box beside the mirror",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A Surprise-style whodunit about mourn, hip, and muscle.")
    parser.add_argument("--detective")
    parser.add_argument("--partner")
    parser.add_argument("--coach")
    parser.add_argument("--place")
    parser.add_argument("--object-name")
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
    detective = args.detective or rng.choice(DETECTIVES)
    partner = args.partner or rng.choice([p for p in PARTNERS if p != detective])
    place = args.place or rng.choice(PLACES)
    if not place.strip():
        raise StoryError("place must not be empty")
    if detective == partner:
        raise StoryError("detective and partner must be different people")
    return StoryParams(
        seed=args.seed,
        detective=detective,
        partner=partner,
        coach=args.coach or rng.choice(COACHES),
        place=place,
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    world.add(Entity("detective", "person", params.detective,
                     meters={"alertness": 0.8, "distance": 0.0},
                     memes={"curiosity": 0.9, "courage": 0.7}))
    world.add(Entity("partner", "person", params.partner,
                     meters={"alertness": 0.7, "distance": 0.0},
                     memes={"worry": 0.5, "trust": 0.6}))
    world.add(Entity("coach", "person", params.coach,
                     meters={"distance": 1.0},
                     memes={"concern": 0.8, "relief": 0.0}))
    world.add(Entity("treasure", "object", params.object_name,
                     meters={"visibility": 0.0, "safety": 0.3},
                     memes={"importance": 0.9},
                     owner="coach"))
    world.add(Entity("bench", "place", "the wooden bench",
                     meters={"distance": 0.4}))
    return world


def tell(params: StoryParams) -> World:
    rng = random.Random((params.seed or 0) ^ 0xC0FFEE)
    case = rng.choice(CASES)
    world = make_world(params)
    detective = params.detective
    partner = params.partner
    coach = params.coach
    treasure = params.object_name

    world.facts.update(case=case, clue=case["clue"], suspect=case["suspect"],
                       muscle=case["muscle"], surprise=case["surprise"],
                       truth=case["truth"], ending=case["ending"],
                       detective=detective, partner=partner, coach=coach,
                       treasure=treasure, solved=False)

    world.say(f"At {params.place}, {coach} began the evening practice and placed {treasure} on the trophy table.")
    world.say(f"Then the lights flickered. When they came back, {treasure} had vanished.")
    world.para()
    world.say(f"{coach} looked ready to mourn the lost prize. “Who could have taken it?” {coach} asked.")
    world.say(f"{detective} bent carefully near the bench and noticed {case['clue']}.")
    world.say(f"“That clue tells us where to look, not whom to blame,” {detective} said. “Let us ask questions first.”")
    world.say(f"{partner} whispered, “Could it be {case['suspect']}?”")
    world.say(f"“Maybe,” said {detective}, “but a mystery needs proof.”")
    world.para()
    world.say(f"While searching, {detective} felt {case['muscle']} after crouching beside the equipment shelf.")
    world.say(f"{partner} offered an arm. “Rest your hip muscle for a moment,” {partner} said.")
    world.say(f"{detective} nodded. “Good detectives protect their muscles and their facts.”")
    world.say(f"Together they followed the chalk and peppermint trail toward the bench.")
    world.say(f"Suddenly, there was a Surprise: {case['surprise']}.")
    world.say(f"{detective} lifted the object and discovered the truth. {case['truth']}")
    world.para()
    world.say(f"{coach} hurried over. “Was it stolen?”")
    world.say(f"“No,” {detective} replied. “It was misplaced. The clue led us here, but careful questions solved the case.”")
    world.say(f"{partner} smiled. “Then we need not mourn after all.”")
    world.say(f"{coach} thanked them and carefully returned {treasure} to its place.")
    world.say(f"By bedtime, {case['ending']}.")
    world.facts["solved"] = True
    world.entities["treasure"].meters.update(visibility=1.0, safety=1.0)
    world.entities["coach"].memes["relief"] = 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly Whodunit about {f['detective']} solving the disappearance of {f['treasure']} at {world.place}.",
        f"Include the words mourn, hip, and muscle, plus a Surprise that changes the case.",
        f"Show {f['detective']} refusing to blame {f['suspect']} without evidence and discovering the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"Why did {f['coach']} begin to mourn?",
            f"{f['coach']} began to mourn because {f['treasure']} disappeared from the trophy table.",
        ),
        QAItem(
            f"What clue did {f['detective']} notice?",
            f"{f['detective']} noticed {f['clue']}.",
        ),
        QAItem(
            "What happened to the detective's hip muscle?",
            f"The detective felt {f['muscle']} while crouching and rested it before continuing the search.",
        ),
        QAItem(
            "What was the Surprise?",
            f"The Surprise was that {f['surprise']}.",
        ),
        QAItem(
            "How was the mystery solved?",
            f"The detectives followed the clue, asked questions, and learned that {f['truth']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a whodunit?", "A whodunit is a mystery story in which people gather clues to discover who caused an event."),
        QAItem("What is a muscle?", "A muscle is body tissue that helps a person move."),
        QAItem("What does mourn mean?", "To mourn means to feel and show sadness after a loss."),
        QAItem("What is a hip?", "A hip is the joint where the upper leg connects to the body."),
        QAItem("What is a surprise?", "A surprise is something unexpected that suddenly changes what someone knows or feels."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}, label={entity.label}, "
            f"meters={entity.meters}, memes={entity.memes}, owner={entity.owner}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
visible(T) :- treasure(T), found(T).
safe(T) :- treasure(T), returned(T).
solved :- safe(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("treasure", "treasure"),
        asp.fact("found", "treasure"),
        asp.fact("returned", "treasure"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show visible/1. #show safe/1. #show solved/0."))
    names = {str(symbol) for symbol in model}
    expected = {"visible(treasure)", "safe(treasure)", "solved"}
    if expected.issubset(names):
        print("OK: ASP parity matches the solved Python world.")
        return 0
    print("MISMATCH between ASP and Python assumptions.")
    print("got:", sorted(names))
    print("expected:", sorted(expected))
    return 1


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(detective="Luna", partner="Milo", coach="Coach Fern", place="the moonlit gym", object_name="the silver victory pin"),
    StoryParams(detective="Mira", partner="Theo", coach="Coach Rowan", place="the old dance hall", object_name="the blue champion badge"),
    StoryParams(detective="Nell", partner="Jun", coach="Coach Hazel", place="the riverside training room", object_name="the little gold whistle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show visible/1. #show safe/1. #show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show visible/1. #show safe/1. #show solved/0."))
        print("ASP atoms:")
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
