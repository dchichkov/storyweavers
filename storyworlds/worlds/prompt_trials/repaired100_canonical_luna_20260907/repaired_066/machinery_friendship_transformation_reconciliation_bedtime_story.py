#!/usr/bin/env python3
"""
A standalone bedtime storyworld about machinery, friendship, transformation,
and reconciliation.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)


@dataclass
class Workshop:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    machine_name: str
    machine_kind: str
    moon_gift: str
    scenario_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    action_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


CHILD_NAMES = ["Luna", "Milo", "Nia", "Theo", "Pia", "Owen", "Iris", "Sol"]
MACHINE_NAMES = ["Copper", "Whirr", "Button", "Tinker", "Moss", "Pip"]
MACHINE_KINDS = ["moon-lantern", "clockwork owl", "little music engine", "star projector"]
MOON_GIFTS = ["a silver gear", "a blue ribbon", "a warm brass bell", "a tiny glass star"]

SCENARIOS = [
    {
        "problem": "the little moon-lantern had stopped glowing before bedtime",
        "misunderstanding": "the machine no longer wanted to be Luna's friend",
        "clue": "a loose copper spring lay beneath the pillow-sized workbench",
        "machine_words": "I was trying to shine, but my spring felt lonely and loose",
        "action": "searched beneath the workbench and found the spring beside a sleepy blue thread",
        "repair": "cleaned the spring, tightened it gently, and tested the lantern one soft click at a time",
        "result": "the moon-lantern glowed again, not because it was perfect, but because its friends had listened",
        "image": "a round pool of silver light rested on the blanket while the machine hummed peacefully",
        "lesson": "friendship can change when we listen closely to what a struggling friend is trying to say",
    },
    {
        "problem": "the clockwork owl kept turning its head away whenever Luna came near",
        "misunderstanding": "the owl had decided it was tired of their friendship",
        "clue": "one wooden feather was caught between two tiny gears",
        "machine_words": "I turned away because the feather tickled my gears",
        "action": "held the owl still and freed the feather with a soft paintbrush",
        "repair": "oiled the little hinge and taught the owl a slower, gentler turn",
        "result": "the clockwork owl blinked both brass eyes and faced Luna again",
        "image": "the owl's shadow perched beside Luna's shadow on the wall",
        "lesson": "a friend may seem distant when a hidden problem is making every movement hard",
    },
    {
        "problem": "the little music engine played one gloomy note instead of a lullaby",
        "misunderstanding": "the engine was angry about being asked to sing",
        "clue": "a pebble from the garden sat inside its smallest music wheel",
        "machine_words": "I did not mean to sound cross; the pebble was stuck in my song",
        "action": "opened the safe cover and rolled the pebble out onto a cloth",
        "repair": "polished the wheel and wound the engine with a patient, even turn",
        "result": "the engine changed its gloomy note into a melody soft enough for dreams",
        "image": "the final note floated like a feather beneath the sleepy stars",
        "lesson": "reconciliation begins when blame gives way to a careful look at what went wrong",
    },
    {
        "problem": "the star projector scattered stars across the floor instead of the ceiling",
        "misunderstanding": "the projector wanted to make a mess of Luna's bedtime",
        "clue": "its round lens had slipped sideways in its velvet holder",
        "machine_words": "I wanted to show the sky, but my window had wandered",
        "action": "followed the bright dots and found the tilted lens near the rug",
        "repair": "set the lens straight and fastened its holder with a tiny golden screw",
        "result": "the stars returned to the ceiling and the scattered room became a sky again",
        "image": "one bright star rested above the machine like a promise kept",
        "lesson": "repairing a friendship can transform a mistake into a gentler beginning",
    },
    {
        "problem": "the bedtime wind-up train stopped between the bookcase and the rug",
        "misunderstanding": "the train had refused to carry Luna's goodnight wish",
        "clue": "a red thread was wrapped around its front wheel",
        "machine_words": "I was not refusing; I could not move while the thread held me",
        "action": "snipped the thread with a blunt craft tool and checked the wheel",
        "repair": "wound the train slowly and placed a clear track around the rug",
        "result": "the train carried the goodnight wish safely to the waiting shelf",
        "image": "its small lamp glimmered as it rested beside the bedtime book",
        "lesson": "when a friend is stuck, patient help can turn frustration into trust",
    },
]

OPENINGS = [
    "At the quiet edge of bedtime, {child} heard a strange little sound from the room of machinery: {problem}.",
    "The moon was high when {child} noticed that {problem}.",
    "Just before the blankets were tucked in, {child} discovered that {problem}.",
    "In the blue hush before sleep, {child} found a small mystery: {problem}.",
    "The house was nearly still, but {problem}. {child} listened carefully.",
]

DIALOGUES = [
    '"I do not want to guess," {child} whispered. "Will you tell me what happened?"',
    '"A friend deserves a question before a judgment," {helper} said softly.',
    '"We can mend this together," {child} promised.',
    '"Perhaps the machine is asking for help in its own way," {helper} said.',
    '"I am still here," {child} told the machine. "Let us look carefully."',
]

ACTIONS = [
    "{child} followed the clue with a candle-lamp and a patient heart.",
    "{child} knelt beside the machinery and examined each small part.",
    "{child} gathered a brush, a cloth, and the courage to try again.",
    "{child} moved slowly, so no gear or feeling would be hurt.",
    "{child} asked for help and made a careful plan.",
]

ENDINGS = [
    "When the repair was finished, {result}.",
    "By the time the moon crossed the window, {result}.",
    "The room grew peaceful again, and {result}.",
    "At last, {result}.",
    "Soon the last little click settled into silence, and {result}.",
]


def tell(params: StoryParams) -> Workshop:
    world = Workshop()
    child = world.add(Entity(
        params.child_name,
        "child",
        params.child_name,
        params.child_type,
        meters={"patience": 1.0, "curiosity": 1.0},
        memes={"worry": 0.0, "friendship": 1.0, "relief": 0.0},
    ))
    machine = world.add(Entity(
        "machine",
        "machinery",
        params.machine_name,
        params.machine_kind,
        owner=child.id,
        meters={"power": 1.0, "alignment": 0.5},
        memes={"loneliness": 0.5, "trust": 0.7, "hope": 0.8},
        props={"gift": params.moon_gift},
    ))
    helper = world.add(Entity(
        "helper",
        "helper",
        "the night caretaker",
        "caretaker",
        meters={"warmth": 1.0},
        memes={"wisdom": 1.0, "kindness": 1.0},
    ))
    scene = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    world.facts.update(
        child=child,
        machine=machine,
        helper=helper,
        problem=scene["problem"],
        misunderstanding=scene["misunderstanding"],
        clue=scene["clue"],
        machine_words=scene["machine_words"],
        action=scene["action"],
        repair=scene["repair"],
        result=scene["result"],
        image=scene["image"],
        lesson=scene["lesson"],
        gift=params.moon_gift,
        resolved=True,
        transformation=True,
        reconciliation=True,
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        child=params.child_name, problem=scene["problem"]
    ))
    world.say(
        f"{params.child_name} looked at {params.machine_name}, the {params.machine_kind}, "
        f"and wondered whether {scene['misunderstanding']}."
    )
    child.memes["worry"] = 1.0
    world.para()

    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        child=params.child_name, helper=helper.label
    ))
    world.say(
        f'"Were you trying to turn away from me?" {params.child_name} asked. '
        f'{params.machine_name} answered with a faint click: "{scene["machine_words"]}."'
    )
    world.say(
        f'"Then we will listen to the machinery," said {helper.label}. '
        f'"A small part can hold a very big worry."'
    )
    child.memes["friendship"] += 0.6
    world.para()

    world.say(f"The important clue was that {scene['clue']}.")
    world.say(ACTIONS[params.action_id % len(ACTIONS)].format(child=params.child_name))
    world.say(f"Together, they {scene['repair']}.")
    world.say(
        f'"I am sorry I thought you had stopped being my friend," {params.child_name} said.'
    )
    world.say(
        f'"And I am sorry my broken sound frightened you," replied {params.machine_name}.'
    )
    world.say(
        f"They placed {params.moon_gift} beside the repaired machine as a promise to begin again."
    )
    machine.meters["power"] = 1.0
    machine.meters["alignment"] = 1.0
    machine.memes["loneliness"] = 0.0
    machine.memes["trust"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["relief"] = 1.0
    world.para()

    world.say(ENDINGS[params.ending_id % len(ENDINGS)].format(result=scene["result"]))
    world.say(f"Then {scene['image']}.")
    world.say(
        f"{params.child_name} learned that {scene['lesson']} "
        f"and fell asleep while the machinery kept a gentle watch."
    )
    return world


def valid_combo(params: StoryParams) -> bool:
    if not params.child_name.strip():
        raise StoryError("child name must not be empty")
    if not params.machine_name.strip():
        raise StoryError("machine name must not be empty")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError("child type must be girl or boy")
    if params.machine_kind not in MACHINE_KINDS:
        raise StoryError("unknown machinery type")
    return True


ASP_RULES = r"""
needs_repair(machine) :- loose_part(machine).
kind_question(child) :- asks(child).
friendship_restored(child, machine) :- kind_question(child), repaired(machine).
transformed(machine) :- repaired(machine), friendship_restored(child, machine).
reconciled(child, machine) :- transformed(machine).
#show needs_repair/1.
#show friendship_restored/2.
#show transformed/1.
#show reconciled/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("loose_part", "machine"),
        asp.fact("asks", "child"),
        asp.fact("repaired", "machine"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {str(atom) for atom in model}
    needed = ["friendship_restored", "transformed", "reconciled"]
    if all(any(name in atom for atom in names) for name in needed):
        return 0
    print("MISMATCH: ASP twin did not establish the full repair arc.")
    return 1


def generation_prompts(world: Workshop) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle bedtime story about {f['machine'].label}, a piece of machinery that needs friendship and repair.",
        f"Tell how {f['child'].label} uses dialogue and a clue to transform a misunderstanding into reconciliation.",
        f"Write a child-facing bedtime tale with machinery, a concrete repair, an apology, and a peaceful ending image.",
    ]


def story_qa(world: Workshop) -> list[QAItem]:
    f = world.facts
    child = f["child"].label
    machine = f["machine"].label
    return [
        QAItem(
            f"Why did {child} misunderstand {machine}?",
            f"{child} misunderstood {machine} because {f['problem']}, and first wondered whether {f['misunderstanding']}.",
        ),
        QAItem(
            "What clue changed the story?",
            f"The clue was that {f['clue']}. It showed that a physical problem, rather than unkindness, was stopping the machinery.",
        ),
        QAItem(
            f"How did {child} and {machine} repair their friendship?",
            f"{child} {f['action']} Then they {f['repair']}, apologized to each other, and placed {f['gift']} beside the machine as a promise.",
        ),
        QAItem(
            "What transformation happened?",
            f"The machinery changed from a troubled, stuck state into a working and trusted friend: {f['result']}.",
        ),
        QAItem(
            "What lesson does the ending show?",
            f"It shows that {f['lesson']} The final image is that {f['image']}.",
        ),
    ]


def world_knowledge_qa(world: Workshop) -> list[QAItem]:
    return [
        QAItem(
            "What is machinery?",
            "Machinery is a group of working parts, such as gears, springs, wheels, or lights, that help something move or work.",
        ),
        QAItem(
            "What is friendship?",
            "Friendship is a caring relationship in which people listen, help, trust, and make room for one another.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace after a disagreement by understanding what happened, apologizing when needed, and beginning again.",
        ),
        QAItem(
            "Why can a bedtime story feel peaceful?",
            "A bedtime story can feel peaceful because its gentle rhythm, caring characters, and safe ending help the listener relax.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime story about machinery and friendship.")
    parser.add_argument("--name")
    parser.add_argument("--machine")
    parser.add_argument("--machine-kind", choices=MACHINE_KINDS)
    parser.add_argument("--gift", choices=MOON_GIFTS)
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
    machine_kind = args.machine_kind or rng.choice(MACHINE_KINDS)
    gift = args.gift or rng.choice(MOON_GIFTS)
    child_type = "girl" if rng.random() < 0.5 else "boy"
    params = StoryParams(
        child_name=args.name or rng.choice(CHILD_NAMES),
        child_type=child_type,
        machine_name=args.machine or rng.choice(MACHINE_NAMES),
        machine_kind=machine_kind,
        moon_gift=gift,
        scenario_id=rng.randrange(len(SCENARIOS)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        action_id=rng.randrange(len(ACTIONS)),
        ending_id=rng.randrange(len(ENDINGS)),
        seed=args.seed,
    )
    valid_combo(params)
    return params


def generate(params: StoryParams) -> StorySample:
    valid_combo(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: Workshop) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={entity.meters}, "
            f"memes={entity.memes}, props={entity.props}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show reconciled/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print("\n".join(str(atom) for atom in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        fixed = [
            StoryParams("Luna", "girl", "Copper", "moon-lantern", "a silver gear", 0, 0, 0, 0, 0),
            StoryParams("Milo", "boy", "Whirr", "clockwork owl", "a blue ribbon", 1, 1, 1, 1, 1),
            StoryParams("Nia", "girl", "Tinker", "star projector", "a tiny glass star", 3, 2, 2, 2, 2),
        ]
        samples = [generate(p) for p in fixed]
    else:
        seen: set[str] = set()
        for index in range(max(args.n * 20, 50)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            sample = generate(resolve_params(args, rng))
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
        header = ""
        if args.all:
            header = f"### {sample.params.child_name} and {sample.params.machine_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
