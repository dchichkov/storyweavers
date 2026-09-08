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
place(parade_ground).
role(sailor).
role(infantry).
feature(twist).
feature(heartwarming).

ready(parade) :- place(parade_ground), role(sailor), role(infantry).
kind_twist :- feature(twist), ready(parade).
happy_ending :- kind_twist, feature(heartwarming).
#show happy_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    sailor: str = "Sailor Theo"
    infantry: str = "Corporal June"
    object_name: str = "a bright blue ribbon"
    place: str = "the town parade ground"
    time: str = "morning"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.trace.append(line)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the quiet drum",
        "premise": "the parade drum stopped beating just before the march began",
        "obstacle": "The infantry could not hear the pace, and the sailors were unsure when to step",
        "clue": "a tiny sparrow had tucked straw beneath the drum's loose leather skin",
        "twist": "The missing beat was not a broken drum at all; it was a nest sheltering three warm eggs",
        "action": "Luna showed the straw to Sailor Theo and Corporal June, then helped carry a spare drum to the front of the parade",
        "dialogue": "'A parade can make room for a small family,' Luna said. 'We can march gently.' 'And we can keep the rhythm,' said Theo",
        "resolution": "The spare drum led the march while the quiet drum stayed safely beside the nest",
        "ending": "when the parade passed, the sparrow lifted its head above the drum and chirped along",
        "lesson": "a kind solution can keep a celebration joyful without disturbing a smaller neighbor",
    },
    {
        "title": "the upside-down pennant",
        "premise": "the harbor pennant hung upside down above the parade route",
        "obstacle": "The sailor band thought the signal meant they should turn back, while the infantry waited in the wrong square",
        "clue": "the rope's red knot was caught behind the flagpole hook",
        "twist": "The strange signal had been made by a gust chasing a child's paper kite, not by an official warning",
        "action": "Luna pointed out the knot, and Sailor Theo and Corporal June cleared the route before asking the harbor keeper to fix the rope",
        "dialogue": "'Let's check before we worry,' said Luna. 'Good eyes,' said June. 'Good teamwork,' added Theo",
        "resolution": "The pennant rose the right way, and the parade formed a bright line from the harbor to the square",
        "ending": "the rescued kite flew above the flags with a new tail made from parade ribbons",
        "lesson": "careful attention can turn a confusing moment into a shared celebration",
    },
    {
        "title": "the empty front row",
        "premise": "one front-row chair at the parade stood empty beneath a yellow sunshade",
        "obstacle": "The town's oldest veteran had planned to lead the salute but had not arrived",
        "clue": "a walking stick and a folded program rested beside the chair",
        "twist": "The veteran was not late from forgetfulness; he was helping a lost child find her grandmother behind the bandstand",
        "action": "Luna told the sailor and infantry leaders, who paused the salute and sent a gentle search party",
        "dialogue": "'We should wait for the person, not only the program,' Luna said. 'That is a fine order,' said June",
        "resolution": "The veteran returned holding the child's hand, and the whole parade welcomed them together",
        "ending": "the empty chair became a shared seat beneath the sunshade",
        "lesson": "a warm welcome matters more than keeping a ceremony perfectly on time",
    },
    {
        "title": "the runaway banner",
        "premise": "a long parade banner slipped from its pole and sailed toward the fountain",
        "obstacle": "Its heavy gold fringe could tangle the marching sailors and infantry",
        "clue": "the banner moved toward a low hedge whenever the wind softened",
        "twist": "The banner's loose cloth had wrapped around a little wagon carrying a shy drummer",
        "action": "Luna called for a pause, while Theo held the pole and June guided the wagon safely behind the hedge",
        "dialogue": "'Stop the steps, not the smiles,' Luna called. 'We can do both,' Theo replied",
        "resolution": "The banner was freed, and the shy drummer was invited to lead the next song",
        "ending": "the gold fringe shimmered beside the wagon as the smallest drummer tapped proudly",
        "lesson": "stopping at the right moment can help everyone join the joy",
    },
    {
        "title": "the mystery of the missing medals",
        "premise": "the parade medals vanished from the table before the award ceremony",
        "obstacle": "The sailors and infantry feared that the children who earned them would go home disappointed",
        "clue": "a trail of silver dust led from the table to the community garden",
        "twist": "The medals had been carried away by a friendly dog whose collar had caught the display cloth",
        "action": "Luna followed the trail with Theo and June, then traded a biscuit for the dog's gentle return",
        "dialogue": "'The medals were traveling with a helper,' Luna said. 'Then let us thank the helper,' said Theo",
        "resolution": "The medals were polished, and the dog received a ribbon of its own",
        "ending": "children raised their medals while the dog wagged beneath a tiny silver bow",
        "lesson": "a mistake can become a kindness when everyone chooses patience",
    },
    {
        "title": "the silent whistle",
        "premise": "the parade whistle made no sound when the first marching group gathered",
        "obstacle": "Nobody knew when to begin, so the sailor line and infantry line stood waiting in the sunshine",
        "clue": "a drop of honey glistened inside the whistle",
        "twist": "The whistle had been borrowed by a hummingbird, which used its bright metal shine to find its nest",
        "action": "Luna told Theo and June, who replaced the whistle with a hand bell and set the shiny whistle beside the garden flowers",
        "dialogue": "'A new signal can start the parade,' Luna said. 'And the bird can keep its safe landmark,' said June",
        "resolution": "The bell rang clearly, and the hummingbird returned to its nest",
        "ending": "the parade moved to the bell's warm sound while tiny wings flashed above the flowers",
        "lesson": "when a plan changes, kindness can help invent a better one",
    },
]


OPENINGS = [
    "On a bright morning, {name} hurried to {place} with {object_name} tucked in a pocket.",
    "The town was polishing its flags when {name} reached {place} for the morning parade.",
    "{name} arrived early at {place}, where sailors, infantry, and families were gathering.",
    "Music floated over {place} as {name} carried {object_name} toward the waiting parade.",
    "At morning's first golden bell, {name} joined the crowd beside {place}.",
]


TURNS = [
    "Luna took one slow breath and looked again.",
    "The puzzle changed when Luna noticed that the smallest detail had a story of its own.",
    "Instead of rushing into the parade, Luna listened for what the quiet moment was saying.",
    "The surprising clue made everyone pause, and pausing gave them room to choose kindly.",
    "Luna realized that the best parade step might be a careful step backward.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade story about a sailor, infantry, and a gentle twist."
    )
    parser.add_argument("--name")
    parser.add_argument("--sailor")
    parser.add_argument("--infantry")
    parser.add_argument("--object-name")
    parser.add_argument("--place")
    parser.add_argument("--time")
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
    name = args.name or rng.choice(["Luna", "Milo", "Asha", "Pip", "Nora"])
    sailor = args.sailor or rng.choice(["Sailor Theo", "Sailor Bea", "Sailor Arun"])
    infantry = args.infantry or rng.choice(["Corporal June", "Corporal Sam", "Corporal Mae"])
    object_name = args.object_name or rng.choice(
        ["a bright blue ribbon", "a paper star", "a little brass bell"]
    )
    place = args.place or "the town parade ground"
    time = args.time or "morning"
    if place != "the town parade ground":
        raise StoryError("This parade world is built around the town parade ground.")
    if time != "morning":
        raise StoryError("This parade world begins in the morning.")
    return StoryParams(
        seed=None,
        name=name,
        sailor=sailor,
        infantry=infantry,
        object_name=object_name,
        place=place,
        time=time,
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "parade_ground"),
            asp.fact("role", "sailor"),
            asp.fact("role", "infantry"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "heartwarming"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show happy_ending/0."))
    asp_ok = bool(asp.atoms(model, "happy_ending"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the heartwarming parade gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    params = world.params
    seed = params.seed if params.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(seed // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]
    values = {
        "name": params.name,
        "sailor": params.sailor,
        "infantry": params.infantry,
        "object_name": params.object_name,
        "place": params.place,
    }

    child = world.add_character(Character(params.name, "child observer"))
    sailor = world.add_character(Character(params.sailor, "sailor"))
    infantry = world.add_character(Character(params.infantry, "infantry"))
    ribbon = world.add_object(ObjectThing(params.object_name, "parade keepsake"))

    child.add_meme("curiosity", 1.0)
    child.add_meme("kindness", 0.5)
    sailor.add_meme("patience", 0.5)
    infantry.add_meme("care", 0.5)

    world.say(opening.format(**values))
    world.say(
        f"{params.sailor} stood beside {params.infantry}, ready to guide the parade. "
        f"{params.name} held {params.object_name} and watched the flags tremble."
    )
    world.say(f"Then came the trouble: {scenario['premise'].capitalize()}.")
    world.say(f"{scenario['obstacle']}. {scenario['clue'].capitalize()}.")
    child.add_meter("careful_steps", 3)
    world.say(f"{turn} {scenario['twist']}.")
    world.say(f"{scenario['action']}. {scenario['dialogue']}.")
    child.add_meme("bravery", 1.0)
    child.add_meme("kindness", 1.0)
    sailor.add_meme("teamwork", 1.0)
    infantry.add_meme("teamwork", 1.0)
    ribbon.add_meter("shared_joy", 1.0)
    world.say(f"{scenario['resolution']}. Everyone made room for the changed plan.")
    world.say(
        f"{params.name} understood that {scenario['lesson']}. "
        "The parade felt stronger because nobody had been left behind."
    )
    world.say(
        f"It was a heartwarming ending at {params.place}: {scenario['ending']}. "
        f"{params.sailor} smiled at {params.infantry}, and {params.name} tied {params.object_name} "
        "to the nearest flag so its bright color could wave for everyone."
    )

    world.facts = {
        "scenario": scenario["title"],
        "premise": scenario["premise"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "twist": scenario["twist"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What problem did {p.name} notice at the parade?",
            answer=f"{f['premise'].capitalize()} The trouble mattered because {f['obstacle'].lower()}.",
        ),
        QAItem(
            question="What clue helped the group understand the problem?",
            answer=f"{f['clue'].capitalize()} That detail encouraged everyone to investigate instead of guessing.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=f"{f['twist'].capitalize()} The twist changed the plan while keeping the people and animals safe.",
        ),
        QAItem(
            question=f"How did {p.name}, the sailor, and the infantry help?",
            answer=f"{f['action']}. They solved the trouble through teamwork and patience.",
        ),
        QAItem(
            question="What image proves the ending was heartwarming?",
            answer=f"{f['ending'].capitalize()} It shows that the parade became a shared celebration.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people walk, play music, carry flags, or celebrate together.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on a boat or ship and learns to cooperate carefully with a crew.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who travel and work on foot, often helping one another as a team.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals the situation is different from what readers first expected.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a heartwarming story about {p.name} at {p.place} with {p.sailor} and {p.infantry}.",
        f"Build the middle around this clue: {f['clue']}. Include this gentle twist: {f['twist']}.",
        f"End with a concrete joyful image: {f['ending']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"  {character.name} ({character.role}) "
            f"meters={character.meters} memes={character.memes}"
        )
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show happy_ending/0."))
        print("happy_ending" if asp.atoms(model, "happy_ending") else "(no happy_ending)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            sailor=args.sailor or "Sailor Theo",
            infantry=args.infantry or "Corporal June",
            object_name=args.object_name or "a bright blue ribbon",
            place="the town parade ground",
            time="morning",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 50, 50):
            seed = base_seed + attempt
            attempt += 1
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
