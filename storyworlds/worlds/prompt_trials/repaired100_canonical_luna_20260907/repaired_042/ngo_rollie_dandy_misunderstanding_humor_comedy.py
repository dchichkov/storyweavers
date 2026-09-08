#!/usr/bin/env python3
"""
A small comedy storyworld about Ngo, Rollie, Dandy, and a very silly
misunderstanding.
"""

from __future__ import annotations

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
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    ngo_name: str = "Ngo"
    rollie_name: str = "Rollie"
    dandy_name: str = "Dandy"
    scenario_id: int = 0
    telling_mode: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SCENARIOS = [
    {
        "object": "a tall purple hat",
        "message": "Bring the hat to the parade",
        "mistake": "Rollie heard, Bring the cat to the parade",
        "cat": "a sleepy orange cat",
        "clue": "the hat had a feather, while the cat had whiskers",
        "action": "Ngo put the hat on the cat",
        "repair": "Dandy read the note aloud and pointed to the feather drawing",
        "ending": "the cat wore a tiny ribbon while the hat sat proudly on Rollie's head",
        "lesson": "listen carefully before acting on a surprising message",
    },
    {
        "object": "a sack of flour",
        "message": "Put the flour by the bakery door",
        "mistake": "Dandy heard, Pour the floor by the bakery door",
        "cat": "a shiny blue watering can",
        "clue": "the sack was dusty, but the floor was already quite full of itself",
        "action": "Dandy sprinkled flour across the clean tiles",
        "repair": "Ngo swept the flour into a bowl and explained the missing word",
        "ending": "the bakery smelled warm, and the floor looked less like a snowstorm",
        "lesson": "ask a question when a sentence sounds strange",
    },
    {
        "object": "a basket of lemons",
        "message": "Roll the lemons to the picnic",
        "mistake": "Rollie heard, Rollie, lemon to the picnic",
        "cat": "a round yellow balloon",
        "clue": "the lemons could roll, but Rollie was the person carrying the basket",
        "action": "Rollie climbed into the basket and waited",
        "repair": "Ngo laughed kindly and showed Rollie the comma on the card",
        "ending": "the lemons rolled into lemonade while Rollie carried the basket properly",
        "lesson": "punctuation can change who is meant to do a job",
    },
    {
        "object": "a silver trumpet",
        "message": "Polish the trumpet for the concert",
        "mistake": "Ngo heard, Polish the trumpet for the concert, and searched for Poland",
        "cat": "a postcard with a red-and-white flag",
        "clue": "the trumpet needed a cloth, not a passport",
        "action": "Ngo packed the trumpet beside a suitcase",
        "repair": "Dandy found a polishing cloth and explained that polish could mean make shiny",
        "ending": "the trumpet gleamed so brightly that Rollie saw his grin in it",
        "lesson": "one word can have more than one meaning",
    },
    {
        "object": "a tiny stage curtain",
        "message": "Raise the curtain at noon",
        "mistake": "Rollie heard, Raise the curtain and noon",
        "cat": "a sleepy clock",
        "clue": "noon could arrive, but it could not be lifted above a stage",
        "action": "Rollie tried to raise the clock",
        "repair": "Ngo showed the stage rope and Dandy pointed at the clock's hands",
        "ending": "the curtain rose at noon, and the clock received a polite bow",
        "lesson": "separate the things in an instruction before rushing",
    },
    {
        "object": "a box of party crackers",
        "message": "Set the crackers on the table",
        "mistake": "Dandy heard, Set the table on the crackers",
        "cat": "a wobbly wooden table",
        "clue": "the table was much too large to balance on a little box",
        "action": "Dandy tried to lift the table onto the crackers",
        "repair": "Rollie stopped the wobble and read the words from left to right",
        "ending": "the crackers popped safely, and the table held every party plate",
        "lesson": "the order of words matters",
    },
    {
        "object": "a jar of strawberry jam",
        "message": "Share the jam with Dandy",
        "mistake": "Dandy heard, Share Dandy with the jam",
        "cat": "a very sticky spoon",
        "clue": "Dandy was a friend, not a slice of toast",
        "action": "Dandy sat on a plate and waited nervously",
        "repair": "Ngo handed Dandy a spoon and Rollie passed the bread",
        "ending": "Dandy enjoyed toast with jam and climbed off the plate",
        "lesson": "check what a sentence is describing before taking it literally",
    },
    {
        "object": "a red umbrella",
        "message": "Open the umbrella by the pond",
        "mistake": "Ngo heard, Open the pond by the umbrella",
        "cat": "a blue rain boot",
        "clue": "the pond had no handle, but the umbrella did",
        "action": "Ngo searched for a zipper on the pond",
        "repair": "Rollie pointed to the umbrella's folded ribs and opened them",
        "ending": "the red umbrella kept everyone dry while the pond stayed gloriously unzipped",
        "lesson": "use the nearby clues to decide what an action belongs to",
    },
]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a misunderstanding?",
        answer="A misunderstanding happens when someone understands words or actions differently from what was intended.",
    ),
    QAItem(
        question="Why can misunderstandings be funny?",
        answer="They can be funny when a harmless mistake leads to a surprising picture, such as a person trying to put a table on crackers.",
    ),
    QAItem(
        question="What is comedy?",
        answer="Comedy is storytelling that uses playful surprises, mistakes, and amusing situations to make people laugh.",
    ),
]


ASP_RULES = r"""
valid_story :- named(ngo), named(rollie), named(dandy), has_misunderstanding, has_humor.
has_misunderstanding.
has_humor.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("named", "ngo"),
            asp.fact("named", "rollie"),
            asp.fact("named", "dandy"),
            asp.fact("feature", "misunderstanding"),
            asp.fact("feature", "humor"),
            asp.fact("style", "comedy"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> None:
    names = [params.ngo_name.strip(), params.rollie_name.strip(), params.dandy_name.strip()]
    if any(not name for name in names):
        raise StoryError("Ngo, Rollie, and Dandy all need names.")
    if len(set(name.lower() for name in names)) != 3:
        raise StoryError("Ngo, Rollie, and Dandy must have different names.")
    if not 0 <= params.scenario_id < len(SCENARIOS):
        raise StoryError("The selected comedy situation does not exist.")


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    scene = SCENARIOS[params.scenario_id]
    world = World()

    ngo = world.add(
        Entity(
            "ngo",
            "character",
            params.ngo_name,
            meters={"confusion": 0.0, "confidence": 0.5},
            memes={"curiosity": 1.0, "kindness": 1.0},
        )
    )
    rollie = world.add(
        Entity(
            "rollie",
            "character",
            params.rollie_name,
            meters={"confusion": 0.0, "confidence": 0.5},
            memes={"eagerness": 1.0, "kindness": 1.0},
        )
    )
    dandy = world.add(
        Entity(
            "dandy",
            "character",
            params.dandy_name,
            meters={"confusion": 0.0, "confidence": 0.5},
            memes={"eagerness": 1.0, "kindness": 1.0},
        )
    )

    openings = [
        f"On a bright morning, {ngo.label}, {rollie.label}, and {dandy.label} prepared a neighborhood comedy parade.",
        f"{ngo.label}, {rollie.label}, and {dandy.label} were arranging a very serious celebration, which was already a suspicious beginning.",
        f"In the little town square, {ngo.label}, {rollie.label}, and {dandy.label} found an instruction card tied with yellow string.",
    ]
    world.say(openings[params.telling_mode % len(openings)])
    world.say(f"The card said, “{scene['message']}.”")
    world.say(
        f"{rollie.label} blinked. “Did it really say that?” {ngo.label} asked. "
        f"{dandy.label} nodded. “I think so, unless the card has learned a new joke.”"
    )

    for person in (ngo, rollie, dandy):
        person.meters["confusion"] += 1.0
    world.para()
    world.say(f"Unfortunately, {scene['mistake']}.")
    world.say(f"Then {scene['action']}.")
    world.say(
        f"{ngo.label} stared at the scene. “That is not what I expected.” "
        f"{rollie.label} replied, “It is also not working very well.” "
        f"{dandy.label} added, “Perhaps the sentence is wearing its socks inside out.”"
    )
    world.say(f"The odd result gave them a clue: {scene['clue'].capitalize()}.")
    world.say(
        f"For one quiet moment, everyone stood still. Then {rollie.label} made a tiny snorting sound, "
        f"and the whole group burst into laughter."
    )

    for person in (ngo, rollie, dandy):
        person.meters["confusion"] = max(0.0, person.meters["confusion"] - 1.0)
        person.meters["confidence"] += 0.5
    world.para()
    world.say(scene["repair"] + ".")
    world.say(
        f"“Oh!” said {ngo.label}. “Now the instruction makes sense.” "
        f"“And the mistake makes a better story,” said {rollie.label}. "
        f"{dandy.label} bowed. “I accept this role in the comedy.”"
    )
    world.say(f"They agreed on the lesson: {scene['lesson'].capitalize()}.")
    world.say(f"At last, {scene['ending']}.")
    world.say(
        f"The parade began with three friends, one corrected instruction, and enough laughter "
        f"to make even the pigeons look as if they understood the joke."
    )

    world.facts.update(
        scene=scene,
        ngo=ngo,
        rollie=rollie,
        dandy=dandy,
        misunderstanding=True,
        humor=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        "Write a child-friendly comedy about Ngo, Rollie, and Dandy solving a funny misunderstanding.",
        f"Create a humorous story involving the instruction “{scene['message']}” and a surprising mistake.",
        "Show how a short conversation helps three friends understand one another and repair a silly problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    scene = facts["scene"]
    ngo = facts["ngo"].label
    rollie = facts["rollie"].label
    dandy = facts["dandy"].label
    return [
        QAItem(
            question=f"What misunderstanding did {ngo}, {rollie}, and {dandy} have?",
            answer=f"They misunderstood the instruction “{scene['message']}.” The mistake was that {scene['mistake'].lower()}.",
        ),
        QAItem(
            question="What clue helped them understand the correct meaning?",
            answer=f"They noticed that {scene['clue']}. That concrete clue showed what the instruction really meant.",
        ),
        QAItem(
            question="How did the friends repair the mistake?",
            answer=f"{scene['repair']}. They talked together instead of blaming one another.",
        ),
        QAItem(
            question="Why was the situation funny?",
            answer=f"It was funny because {scene['action'].lower()}, creating a harmless result that was very different from the intended task.",
        ),
        QAItem(
            question=f"What did {dandy} learn?",
            answer=f"{dandy} learned that {scene['lesson'].lower()}.",
        ),
        QAItem(
            question=f"How did {rollie} help?",
            answer=f"{rollie} helped by noticing the strange result, joining the conversation, and helping the friends test the corrected meaning.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = asp.atoms(model, "valid_story")
    if atoms == [()]:
        print("OK: ASP comedy gate matches the Python domain.")
        return 0
    print("MISMATCH: ASP comedy gate did not produce the expected valid story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comedy storyworld about Ngo, Rollie, Dandy, and a misunderstanding."
    )
    parser.add_argument("--ngo-name", default=None)
    parser.add_argument("--rollie-name", default=None)
    parser.add_argument("--dandy-name", default=None)
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
    params = StoryParams(
        seed=None,
        ngo_name=args.ngo_name or "Ngo",
        rollie_name=args.rollie_name or "Rollie",
        dandy_name=args.dandy_name or "Dandy",
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(3),
    )
    python_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    python_reasonable(params)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.label}: type={entity.type}, meters={meters}, memes={memes}"
        )
    lines.append(
        f"  resolved={world.facts.get('resolved')}, misunderstanding={world.facts.get('misunderstanding')}, humor={world.facts.get('humor')}"
    )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(scenario_id=0, telling_mode=0),
    StoryParams(scenario_id=2, telling_mode=1),
    StoryParams(scenario_id=5, telling_mode=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP valid story:", bool(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
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
