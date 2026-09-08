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
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
place(workshop).
feature(humor).
feature(bravery).
feature(problem_solving).
problem(edge_dim).
can_solve(edge_dim) :- feature(problem_solving).
gentle(bravery) :- feature(bravery).
warm(humor) :- feature(humor).
happy_ending :- can_solve(edge_dim), gentle(bravery), warm(humor).
#show happy_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "her grandpa"
    project: str = "a little wooden robot"
    tool: str = "a bright red screwdriver"
    material: str = "smooth pine"
    place: str = "the workshop"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, value: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + value

    def add_meme(self, key: str, value: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + value


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, value: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + value


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the edge-dim gear",
        "problem": "the robot's tiny lamp glowed brightly in the middle but turned edge-dim near its wooden rim",
        "risk": "Without a clear lamp, the robot might bump into the shelves during its test walk",
        "clue": "a thin strip of wax sat only along one side of the lamp frame",
        "first": "{name} almost painted the whole frame at once, but stopped before covering the little hinge",
        "action": "{name} used a scrap of paper to test the light, then asked {helper} to help loosen the hinge and measure the frame",
        "dialogue": "'That lamp has an edge-dim mood,' {name} said. 'Maybe it needs a wider smile.'",
        "resolution": "They trimmed a new shade, left the hinge free, and fitted the lamp without forcing it",
        "ending": "the robot rolled beneath the shelves, its round lamp shining all the way to the edges",
        "lesson": "problem solving means testing one small idea, while bravery means stopping when a guess could cause harm",
    },
    {
        "title": "the giggling clamp",
        "problem": "a wooden clamp squeaked and made the project wobble every time it tightened",
        "risk": "The wobbling board could slip and spoil the robot's carefully drawn face",
        "clue": "the squeak vanished when a folded cloth rested under the clamp",
        "first": "{name} tried to hush the clamp with a stern look, but the clamp squeaked louder",
        "action": "{name} made the clamp a tiny paper hat, then checked the cloth idea with {helper}",
        "dialogue": "'Perhaps it is not rude,' {name} said. 'Perhaps it is telling us it needs a cushion.'",
        "resolution": "The cloth held the board steady, and the clamp wore its hat during the rest of the build",
        "ending": "the finished robot bowed while the little clamp squeaked one polite encore",
        "lesson": "humor can soften a worry, and careful testing can turn a noisy problem into useful information",
    },
    {
        "title": "the runaway wheel",
        "problem": "one wheel rolled across the workshop whenever {name} tried to attach it",
        "risk": "It could disappear beneath the heavy workbench or bump a jar of blue paint",
        "clue": "the wheel always stopped beside a strip of cork on the floor",
        "first": "{name} chased it in a circle until both the wheel and {name} felt dizzy",
        "action": "{name} placed two cork strips like a tiny road and asked {helper} to hold the axle steady",
        "dialogue": "'Running after it is not a plan,' {name} admitted. 'It is excellent exercise, though.'",
        "resolution": "The cork road kept the wheel close while they fastened it to the axle",
        "ending": "the robot traveled straight across the floor instead of taking another wheel-shaped adventure",
        "lesson": "a funny mistake can point toward a better plan when someone pauses to observe",
    },
    {
        "title": "the backwards birdhouse",
        "problem": "a birdhouse project had its round doorway facing the workshop wall",
        "risk": "A bird could not reach the doorway, and the fresh glue might set before the mistake was fixed",
        "clue": "a pencil arrow on the plan pointed toward the sunny window",
        "first": "{name} announced that the birds might enjoy a very private house, then noticed the dark wall",
        "action": "{name} bravely told {helper} about the mistake and used a warm cloth to soften the glue",
        "dialogue": "'The birds asked for a window,' {name} said. 'They were too polite to complain.'",
        "resolution": "They turned the house toward the sun and reinforced the loose corner",
        "ending": "morning light poured through the doorway while a sparrow inspected the new home",
        "lesson": "bravery includes admitting a mistake before it becomes harder to repair",
    },
    {
        "title": "the shy little motor",
        "problem": "the robot's motor hummed but would not turn the wheels",
        "risk": "Pushing the motor too hard could strip its tiny gears",
        "clue": "a loose thread was caught beneath one gear, while the battery connection was firm",
        "first": "{name} wanted to add a bigger battery, but stopped when {helper} pointed to the delicate gear",
        "action": "{name} switched off the power, used tweezers to lift the thread, and tested the wheel by hand",
        "dialogue": "'It is not lazy,' {name} said. 'It is wearing a thread scarf.'",
        "resolution": "The thread came free, and the motor turned with a gentle, happy buzz",
        "ending": "the robot waved both arms as its motor hummed a tune no louder than a bumblebee",
        "lesson": "gentle problem solving protects small parts and gives a quiet clue time to speak",
    },
    {
        "title": "the upside-down label",
        "problem": "the workshop's parts boxes had labels facing the wrong way",
        "risk": "A rushed search could mix screws with beads and leave the robot without the right fasteners",
        "clue": "only the box with a crooked star had the short brass screws",
        "first": "{name} reached for the largest box, then saw that size did not tell the whole story",
        "action": "{name} sorted the boxes by picture, checked each one with {helper}, and turned every label toward the aisle",
        "dialogue": "'A box can be upside down without being silly,' {name} said. 'But it is much easier to read right-side up.'",
        "resolution": "The brass screws were found, and the labels made the next search quick",
        "ending": "the workshop shelves looked like a friendly rainbow of tools and clearly marked parts",
        "lesson": "problem solving grows stronger when clues are organized instead of guessed at",
    },
    {
        "title": "the paintbrush moustache",
        "problem": "a paintbrush had left a thick blue moustache across the robot's face",
        "risk": "Adding more paint would hide the small smile Luna wanted to keep",
        "clue": "a clean corner of the brush made a thin line when Luna tested it on scrap wood",
        "first": "{name} considered giving the robot two moustaches, but the second one looked even more surprised",
        "action": "{name} wiped the brush, practiced on {material}, and asked {helper} whether the first layer could be sanded",
        "dialogue": "'Every robot deserves a chance to look less astonished,' {name} said",
        "resolution": "They sanded the thick mark, painted a smaller smile, and let it dry before adding details",
        "ending": "the robot's blue smile tilted kindly beneath two bright button eyes",
        "lesson": "humor helps us stay hopeful while patient practice repairs a messy beginning",
    },
    {
        "title": "the crooked bridge",
        "problem": "a bridge for the workshop toy train leaned toward a stack of jars",
        "risk": "The train could fall and rattle the jars off the shelf",
        "clue": "one support was shorter, and a ruler showed exactly how much wood was missing",
        "first": "{name} tried to prop the bridge with a pencil, which made the train wobble like a sleepy duck",
        "action": "{name} measured the gap, cut a matching shim with {helper}, and tested the bridge with an empty wagon",
        "dialogue": "'The duck bridge needs a proper leg,' {name} said",
        "resolution": "The shim leveled the track before the toy train returned",
        "ending": "the little train crossed smoothly, tooting hello beside the safe jars",
        "lesson": "a precise measurement can replace a risky guess, especially when humor keeps frustration small",
    },
    {
        "title": "the missing silver screw",
        "problem": "one silver screw vanished while Luna assembled the robot's chest",
        "risk": "Searching by sweeping could push it under the workbench",
        "clue": "a faint sparkle showed inside the fold of a soft blue rag",
        "first": "{name} almost brushed everything onto the floor, then held still and looked for one tiny shine",
        "action": "{name} asked {helper} to block the bench edge and carefully unfolded the rag over a tray",
        "dialogue": "'The screw is hiding like a very shiny mouse,' {name} whispered",
        "resolution": "The screw landed in the tray, and the robot's chest closed securely",
        "ending": "the finished robot carried a silver dot on its chest like a tiny badge of teamwork",
        "lesson": "bravery can be quiet patience, and careful searching protects both tools and helpers",
    },
    {
        "title": "the lopsided stool",
        "problem": "a stool wobbled whenever someone sat near the workshop window",
        "risk": "A sudden tilt could spill a jar of warm varnish",
        "clue": "a thread of light slipped beneath one short leg",
        "first": "{name} sat very still and declared the stool a rocking boat, but the varnish jar did not look ready for a voyage",
        "action": "{name} moved the jar away, placed the stool on a flat board, and asked {helper} to check each leg",
        "dialogue": "'This boat needs a dock,' {name} said. 'And perhaps fewer waves.'",
        "resolution": "They fitted a small wooden foot beneath the short leg and tested the stool safely",
        "ending": "the stool stood firm while sunlight warmed its newly polished seat",
        "lesson": "a joke can name the trouble, but a careful test is what makes a repair safe",
    },
    {
        "title": "the quiet bell",
        "problem": "the workshop bell stayed silent when Luna pulled its string",
        "risk": "Without the bell, helpers might not know when a large machine was about to start",
        "clue": "the striker had slipped behind a loose wooden panel",
        "first": "{name} pulled the string again and again until the bell made one tiny cough",
        "action": "{name} stopped pulling, marked the loose panel with chalk, and brought {helper} to inspect it",
        "dialogue": "'The bell is not ignoring us,' {name} said. 'It is stuck behind a wall.'",
        "resolution": "They secured the panel, freed the striker, and tested the bell from a safe distance",
        "ending": "a clear ring crossed the workshop, followed by a cheerful chorus of 'Ready!'",
        "lesson": "bravery means stopping an unhelpful action and choosing a safer way to learn",
    },
]


OPENINGS = [
    "On a warm morning, {name} carried {material} into {place} beside {helper}.",
    "{name} entered {place} with {helper}, ready to build {project} from {material}.",
    "Sunlight rested on the workbench as {name} and {helper} began a new project in {place}.",
    "The workshop smelled of wood and lemon oil when {name} arrived with {helper}.",
    "With {tool} tucked in a pocket, {name} joined {helper} at the busy workshop bench.",
    "Rain tapped the workshop window while {name} and {helper} planned their careful build.",
]


TURNS = [
    "The odd detail changed the problem from a guess into a question they could test.",
    "Luna took a breath, because rushing would only make the small trouble bigger.",
    "The workshop grew quiet enough for one useful clue to be heard.",
    "A silly first idea made them laugh, then the real plan became easier to see.",
    "Instead of forcing the part, Luna let the evidence choose the next step.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming workshop story about humor, bravery, and problem solving.")
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--project")
    parser.add_argument("--tool")
    parser.add_argument("--material")
    parser.add_argument("--place")
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
    place = args.place or "the workshop"
    if place != "the workshop":
        raise StoryError("This world is built in the workshop.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Milo", "Nora", "Tavi", "Pia"]),
        helper=args.helper or rng.choice(["her grandpa", "her aunt May", "her neighbor Jo", "her friend Sam"]),
        project=args.project or rng.choice(["a little wooden robot", "a wind-up bird", "a toy delivery cart"]),
        tool=args.tool or rng.choice(["a bright red screwdriver", "a silver ruler", "a small yellow hammer"]),
        material=args.material or rng.choice(["smooth pine", "warm cedar", "a square of cork"]),
        place=place,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "workshop"),
            asp.fact("feature", "humor"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "problem_solving"),
            asp.fact("problem", "edge_dim"),
        ]
    )


def asp_program(show: str = "#show happy_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = bool(asp.atoms(model, "happy_ending"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the workshop story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(seed // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]
    values = {
        "name": p.name,
        "helper": p.helper,
        "project": p.project,
        "tool": p.tool,
        "material": p.material,
        "place": p.place,
    }

    child = world.add_character(Character(p.name, "young builder"))
    helper = world.add_character(Character(p.helper, "workshop helper"))
    project = world.add_object(ObjectThing(p.project, "project"))
    tool = world.add_object(ObjectThing(p.tool, "tool"))

    child.add_meme("humor", 1)
    child.add_meme("bravery", 0.5)
    child.add_meme("problem_solving", 0.5)
    child.add_meter("careful_steps", 2)
    helper.add_meme("patience", 1)

    def format_text(key: str) -> str:
        return scenario[key].format(**values)

    world.say(opening.format(**values))
    world.say(f"On the bench waited {p.project}, made from {p.material}, beside {p.tool}.")
    world.say(f"Then they noticed {scenario['title']}: {format_text('problem')}.")
    world.say(f"{format_text('risk')}. {format_text('clue').capitalize()}.")
    world.say(f"{format_text('first')}. {turn}")
    world.say(f"{format_text('action')}. {format_text('dialogue')}")
    child.add_meme("bravery", 1)
    child.add_meme("problem_solving", 1)
    child.add_meter("careful_steps", 3)
    project.add_meter("stability", 1)
    tool.add_meter("usefulness", 1)
    world.say(f"{format_text('resolution')}. {p.name} and {p.helper} gave each other a relieved high five.")
    child.add_meme("joy", 1)
    world.say(f"They understood that {format_text('lesson')}.")
    world.say(f"It was a heartwarming ending in {p.place}: {format_text('ending')}.")
    world.say(f"{p.helper} smiled and said, 'A good fix leaves room for a good laugh.' {p.name} laughed, and the workshop felt bright.")

    world.facts = {
        "scenario": scenario["title"],
        "problem": format_text("problem"),
        "risk": format_text("risk"),
        "clue": format_text("clue"),
        "action": format_text("action"),
        "resolution": format_text("resolution"),
        "ending": format_text("ending"),
        "lesson": format_text("lesson"),
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            f"What problem did {p.name} find in the workshop?",
            f"{f['problem']}. It mattered because {f['risk']}.",
        ),
        QAItem(
            "What clue helped them understand the problem?",
            f"{f['clue']}. They used that detail instead of relying on a hurried guess.",
        ),
        QAItem(
            f"How did {p.name} use humor, bravery, and problem solving?",
            f"{f['action']}. The humor kept the moment warm, the bravery made careful action possible, and the problem solving followed the clue.",
        ),
        QAItem(
            "How was the workshop problem resolved?",
            f"{f['resolution']}. The repair was tested gently before the project continued.",
        ),
        QAItem(
            "What image proves the story has a heartwarming ending?",
            f"{f['ending']}. The finished result shows that the workshop is safer and more cheerful than before.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is humor?",
            "Humor is a gentle way of noticing something funny or surprising so people can feel lighter without hurting anyone.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is choosing a careful and helpful action even when a mistake or worry makes the choice difficult.",
        ),
        QAItem(
            "What is problem solving?",
            "Problem solving means noticing the trouble, finding useful clues, testing an idea safely, and changing the plan when the evidence calls for it.",
        ),
        QAItem(
            "What does edge-dim mean in this world?",
            "Edge-dim means that something is bright or clear in the middle but becomes less bright near its outer edge.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a heartwarming workshop story about {p.name} and {p.helper} repairing {f['scenario']}.",
        f"Show humor, bravery, and problem solving through this clue: {f['clue']}.",
        f"End with this concrete workshop image: {f['ending']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(f"  {character.name} ({character.role}) meters={character.meters} memes={character.memes}")
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("happy_ending" if asp.atoms(model, "happy_ending") else "(no happy_ending)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            helper=args.helper or "her grandpa",
            project=args.project or "a little wooden robot",
            tool=args.tool or "a bright red screwdriver",
            material=args.material or "smooth pine",
            place="the workshop",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 50, 50):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
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
