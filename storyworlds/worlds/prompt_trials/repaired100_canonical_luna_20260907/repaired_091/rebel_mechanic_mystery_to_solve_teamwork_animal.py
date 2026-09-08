#!/usr/bin/env python3
"""
Story world: a rebellious animal, a patient mechanic, a mystery, and teamwork.
"""

from __future__ import annotations

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
    workshop: str = "Willow Creek repair shed"
    hero: str = "Luna"
    mechanic: str = "Mara"
    animal: str = "Pip"
    seed: Optional[int] = None


SCENARIOS = (
    {
        "name": "the midnight scooter",
        "mystery": "the old delivery scooter rolled away from the shed each night",
        "clue": "small muddy paw marks crossed the floor beside the front wheel",
        "wrong": "Luna first suspected that a loose brake was sending the scooter downhill",
        "cause": "Pip the goat had been nudging the kickstand while searching for fallen apples",
        "response": "Mara fitted a bright wheel chock and moved the apples into a covered bin",
        "line": '"The marks stop where the apples used to be," Mara said',
        "change": "Pip stopped being blamed as a troublemaker and became the shed's careful bell-ringer",
        "ending": "the scooter stayed still while Pip rang the little brass bell for the morning repair crew",
        "lesson": "teamwork grows when everyone follows clues before choosing blame",
    },
    {
        "name": "the silent engine",
        "mystery": "the workshop engine refused to start whenever the barn cat slept nearby",
        "clue": "a tuft of orange fur was caught under the loose battery strap",
        "wrong": "Luna wondered whether the engine had become jealous of the cat",
        "cause": "the strap slipped against the battery terminal whenever the cat brushed the workbench",
        "response": "Mara cleaned the terminal, tightened the strap, and gave the cat a warm basket away from the tools",
        "line": '"The fur tells us where the shaking begins," Luna said",
        "change": "the cat went from suspicious visitor to welcome nap-time helper",
        "ending": "the engine purred steadily while the orange cat slept in its basket beside the sunny wall",
        "lesson": "a good team gives every clue a fair chance to speak",
    },
    {
        "name": "the vanishing wrench",
        "mystery": "the mechanic's silver wrench disappeared from the same peg every afternoon",
        "clue": "a trail of shiny scratches led beneath the wooden animal pen",
        "wrong": "Luna thought a sneaky crow was collecting tools for a nest",
        "cause": "the curious donkey had pushed the wrench through a gap while rubbing its itchy nose",
        "response": "Mara retrieved the wrench with a long grabber and repaired the gap before returning it to the peg",
        "line": '"The scratches are low, so our thief has a nose, not wings," Luna said",
        "change": "the donkey learned to rub against a safe brush instead of the tool wall",
        "ending": "the wrench hung bright on its peg while the donkey scratched happily against the new brush",
        "lesson": "solving a mystery can help friends understand a need hidden behind mischief",
    },
    {
        "name": "the blinking lantern",
        "mystery": "the shed lantern blinked whenever the rebel pony stamped its hoof",
        "clue": "the wire beside the door trembled in the same rhythm as the stamping",
        "wrong": "Everyone wondered whether the pony was sending a secret warning",
        "cause": "the pony's rope had been tied to a loose wall hook that shook the lantern switch",
        "response": "Mara moved the hook, secured the wire, and gave the pony a safer lead near the hay rack",
        "line": '"The hoofbeat moves the hook, and the hook moves the switch," Mara explained",
        "change": "the pony became calmer because its restless rope no longer tugged the wall",
        "ending": "the lantern shone steadily as the pony munched hay under the repaired hook",
        "lesson": "careful teamwork can solve a machine problem and an animal problem together",
    ),
    {
        "name": "the humming cart",
        "mystery": "a handcart hummed a low tune whenever it stood beside the rabbit hutch",
        "clue": "the tune stopped when Luna rolled the cart onto the stone path",
        "wrong": "Luna imagined that the rabbits were secretly singing to the cart",
        "cause": "one loose wheel rubbed against the wooden hutch and vibrated like a string",
        "response": "Mara tightened the wheel and moved the cart away from the animals' quiet shelter",
        "line": '"Change one place, then listen again," Luna suggested",
        "change": "the rabbits stayed peaceful, and Luna learned that a strange sound could have an ordinary source",
        "ending": "the cart rested silently on the stone path while the rabbits twitched their noses in peace",
        "lesson": "testing one small change can turn a frightening mystery into a useful answer",
    ),
    {
        "name": "the painted footprints",
        "mystery": "blue footprints appeared across the repair yard after every rain",
        "clue": "the marks had square edges and matched the color of a newly painted toolbox",
        "wrong": "Luna feared that the shelter's runaway animal had crossed the wet yard",
        "cause": "a paint tray had tipped beside a rubber boot used for checking tire tracks",
        "response": "Mara washed the boot, closed the paint shelf, and placed a sign around the wet work area",
        "line": '"Real paw pads would not make corners," Luna noticed",
        "change": "the frightened rabbit returned to its pen, and the paint crew learned to mark their tools",
        "ending": "the blue footprints faded from the yard while the rabbit rested safely beside its clean water bowl",
        "lesson": "a surprising shape is a clue to examine, not proof of danger",
    ),
    {
        "name": "the rattling trailer",
        "mystery": "the animal trailer rattled even when no animal was inside",
        "clue": "the rattle matched the bumps made by the wind against one loose gate chain",
        "wrong": "Luna thought a hidden animal might be trapped beneath the floor",
        "cause": "the chain struck the metal gate each time the wind lifted it",
        "response": "Mara padded the chain, checked the empty trailer, and latched the gate before the next storm",
        "line": '"The sound follows the chain, not the floor," Mara said",
        "change": "Luna replaced fear with confidence in careful listening",
        "ending": "the trailer stood quiet beneath the clouds while the animals watched from their dry stalls",
        "lesson": "teamwork means sharing observations until the safest explanation appears",
    ),
    {
        "name": "the warm toolbox",
        "mystery": "one toolbox felt warm every evening although the shed was cold",
        "clue": "fresh straw was tucked beneath it, and tiny feathers covered the nearby shelf",
        "wrong": "Luna wondered whether a broken battery was heating the metal",
        "cause": "a wren had built a nest against the sunny side of the closed toolbox",
        "response": "Mara moved the empty toolbox only after the bird flew out, then placed a nesting box under the eaves",
        "line": '"We must wait for the bird before moving anything," Luna said",
        "change": "the wren gained a safe home, and Luna learned that kindness belongs in repairs too",
        "ending": "the toolbox cooled in the shade while the wren sang from its new box above the door",
        "lesson": "good helpers protect small lives while solving practical problems",
    ),
)


OPENINGS = (
    "Morning rain tapped the roof of the repair shed when Luna noticed something strange.",
    "At the edge of the animal shelter, Luna and the mechanic Mara found a new mystery.",
    "The animals were safe in their stalls, but one machine was behaving in a very odd way.",
    "Before the first cart arrived, a small clue waited beside the workshop door.",
    "Luna liked fixing things, but she liked understanding them even more.",
    "The repair shed was quiet until an animal, a machine, and a muddy trail made a puzzle.",
)

TRANSITIONS = (
    "Instead of guessing again, Luna and Mara divided the work and watched different parts of the shed.",
    "They kept behind the safety line, compared notes, and changed only one thing at a time.",
    "Luna listened while Mara inspected the equipment, and each observation helped the other.",
    "Their first idea did not fit every clue, so the team set it aside without arguing.",
    "They asked the animal keeper for permission before touching any tool or entering any pen.",
    "The mystery became smaller when the friends matched the marks, sounds, and timing.",
)

QA_STYLES = (
    (
        "What mystery did Luna find?",
        "Which clue helped the team?",
        "What caused the trouble?",
        "How did the mechanic solve it safely?",
        "How did the animal's role change?",
        "What did the teamwork teach Luna?",
    ),
    (
        "Why did the workshop need investigating?",
        "What evidence changed the team's first guess?",
        "What had really happened?",
        "What safe repair did Mara make?",
        "What changed for the animal?",
        "What lesson completed the story?",
    ),
    (
        "What unusual event began the story?",
        "How did Luna and Mara test their idea?",
        "What was the hidden cause?",
        "How did the helpers protect the animals?",
        "What transformation followed?",
        "Why was teamwork important?",
    ),
)


@dataclass
class World:
    workshop: str
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    if not params.hero.strip() or not params.mechanic.strip() or not params.animal.strip():
        raise StoryError("hero, mechanic, and animal names must not be empty")
    if params.hero.strip().lower() == params.mechanic.strip().lower():
        raise StoryError("the hero and mechanic must have different names")
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = SCENARIOS[rng.randrange(len(SCENARIOS))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    transition = TRANSITIONS[rng.randrange(len(TRANSITIONS))]
    qa_style = rng.randrange(len(QA_STYLES))
    order = rng.randrange(3)

    world = World(params.workshop)
    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="girl",
        label=params.hero,
        traits=["curious", "kind"],
        memes={"curiosity": 1.0, "teamwork": 1.0},
    ))
    mechanic = world.add(Entity(
        id=params.mechanic,
        kind="character",
        type="woman",
        label=params.mechanic,
        traits=["patient", "skilled"],
        memes={"patience": 1.0, "teamwork": 1.0},
    ))
    animal = world.add(Entity(
        id=params.animal,
        kind="animal",
        type="animal",
        label=params.animal,
        traits=["rebel", "clever"],
        meters={"safety": 1.0, "calm": 0.0, "transformed": 0.0},
        memes={"trust": 0.0},
    ))

    world.facts = {
        "hero": hero.label,
        "mechanic": mechanic.label,
        "animal": animal.label,
        "scenario": scenario["name"],
        "mystery": scenario["mystery"],
        "clue": scenario["clue"],
        "wrong": scenario["wrong"],
        "cause": scenario["cause"],
        "response": scenario["response"],
        "line": scenario["line"].replace("Luna", hero.label).replace("Mara", mechanic.label),
        "change": scenario["change"].replace("Luna", hero.label).replace("Mara", mechanic.label),
        "ending": scenario["ending"].replace("Luna", hero.label).replace("Mara", mechanic.label),
        "lesson": scenario["lesson"],
        "qa_style": qa_style,
    }

    world.say(opening)
    world.say(
        f"At the {world.workshop}, {hero.label} watched {mechanic.label}, a careful mechanic, "
        f"look after the animals and their machines. {animal.label} was a clever rebel who often wandered "
        "where no one expected, though the animals always stayed in safe pens or supervised spaces."
    )
    world.say(f"That day, the mystery was this: {scenario['mystery']}.")
    world.para()

    observations = [
        f"{scenario['wrong']}.",
        f"{hero.label} found the important clue: {scenario['clue']}.",
        f"{world.facts['line']}.",
        transition,
    ]
    if order == 1:
        observations[0], observations[1] = observations[1], observations[0]
    elif order == 2:
        observations[1], observations[2] = observations[2], observations[1]
    for sentence in observations:
        world.say(sentence)

    world.say(
        f'"Could you check the machine while I watch the animal?" {hero.label} asked. '
        f'"Yes," said {mechanic.label}. "You watch carefully, and I will repair carefully."'
    )
    world.para()
    world.say(f"The clues revealed the cause: {scenario['cause']}.")
    world.say(f"Together, they solved the problem safely: {scenario['response']}.")
    animal.meters["calm"] = 1.0
    animal.meters["transformed"] = 1.0
    animal.memes["trust"] = 1.0
    hero.memes["mystery_solved"] = 1.0
    mechanic.memes["mystery_solved"] = 1.0
    world.say(f"The change was clear: {world.facts['change']}.")
    world.say(
        f'"We made a good team," said {hero.label}. '
        f'"We did," replied {mechanic.label}, "because we listened to the clues and to each other."'
    )
    world.para()
    world.say(f"They remembered that {scenario['lesson']}.")
    world.say(f"By sunset, {world.facts['ending']}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an animal story about {f['animal']}, a rebel, and {f['mechanic']}, a mechanic, solving {f['mystery']}.",
        f"Include teamwork based on this clue: {f['clue']}.",
        f"End with this changed image: {f['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    questions = QA_STYLES[f["qa_style"]]
    return [
        QAItem(questions[0], f"{f['hero']} discovered that {f['mystery']}."),
        QAItem(questions[1], f"The useful clue was that {f['clue']}. It fit the final explanation better than the first guess."),
        QAItem(questions[2], f"The real cause was that {f['cause']}."),
        QAItem(questions[3], f"{f['mechanic']} handled the repair while {f['hero']} watched carefully and everyone kept the animal safe. Then {f['response']}."),
        QAItem(questions[4], f"{f['change']}. The animal also became calmer and more trusting."),
        QAItem(questions[5], f"They learned that {f['lesson']}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does a mechanic do?",
            "A mechanic examines and repairs machines, tools, and vehicles.",
        ),
        QAItem(
            "What does rebel mean in this animal story?",
            "A rebel is someone who does not simply follow the usual path. In this story, the animal is curious and independent, but still must be kept safe.",
        ),
        QAItem(
            "Why is teamwork useful for a mystery?",
            "Teamwork lets people compare observations, divide safe tasks, and test an explanation together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = r"""
character(H) :- hero(H).
animal(A) :- rebel(A).
mystery_solved(H) :- hero(H), clue_seen(H), mechanic_helped.
safe(A) :- animal(A), repair_done.
teamwork(H,M) :- hero(H), mechanic(M), clue_seen(H), mechanic_helped.
transformed(A) :- safe(A), animal_calm(A).
#show mystery_solved/1.
#show safe/1.
#show teamwork/2.
#show transformed/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("hero", "luna"),
            asp.fact("mechanic", "mara"),
            asp.fact("rebel", "pip"),
            asp.fact("clue_seen", "luna"),
            asp.fact("mechanic_helped"),
            asp.fact("repair_done"),
            asp.fact("animal_calm"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    names = {(symbol.name, len(symbol.arguments)) for symbol in model}
    expected = {
        ("mystery_solved", 1),
        ("safe", 1),
        ("teamwork", 2),
        ("transformed", 1),
    }
    if not expected.issubset(names):
        print("MISMATCH: ASP rules did not produce expected facts.")
        return 1
    for seed in range(5):
        sample = generate(StoryParams(seed=seed))
        if not sample.story or len(sample.story_qa) < 3:
            print("MISMATCH: generated story verification failed.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An animal mystery about a rebel, a mechanic, and teamwork."
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
    parser.add_argument("--workshop", default="Willow Creek repair shed")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--mechanic", default=None)
    parser.add_argument("--animal", default=None)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        workshop=args.workshop,
        hero=args.hero or rng.choice(["Luna", "Nia", "Ivy", "Mina"]),
        mechanic=args.mechanic or rng.choice(["Mara", "Jo", "Rae", "Tessa"]),
        animal=args.animal or rng.choice(["Pip", "Clover", "Moss", "Pepper"]),
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = max(1, args.n)
    samples: list[StorySample] = []

    if args.all:
        for index, scenario in enumerate(SCENARIOS):
            params = StoryParams(
                workshop=args.workshop,
                hero=args.hero or "Luna",
                mechanic=args.mechanic or "Mara",
                animal=args.animal or scenario["name"].split()[-1].title(),
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < count and index < max(50, count * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
