#!/usr/bin/env python3
"""
A child-friendly tall tale on a forest trail: an Afghan blanket, a loud
misunderstanding, and a careful conversation turn a spooky rumor into a warm
campfire discovery.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    companion: str
    object_name: str = "afghan"
    setting: str = "forest trail"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NAMES = ["Luna", "Milo", "Nora", "Pia", "Tariq", "Ivy", "Owen", "June"]
COMPANIONS = ["badger", "raven", "fox", "goat", "squirrel"]

SCENARIOS = [
    {
        "key": "whistling_cloak",
        "premise": "a blue Afghan lay across a stump, its loose fringe fluttering like a tiny flag",
        "problem": "A gust made the fringe whistle, and everyone thought a giant hidden in the trees was calling",
        "mistake": "{name} announced that the forest giant must be wearing a blanket cape and hurried toward the sound",
        "clue": "the whistle stopped whenever the fringe was tucked under the blanket",
        "dialogue": "'The giant answers to the wind, not to us,' {name} said. 'Let's ask before we leap.'",
        "action": "The companion held a lantern while an adult checked the stump, and {name} folded the Afghan away from the path",
        "result": "The trail became quiet, and the supposed giant turned out to be a harmless blanket edge",
        "ending": "The Afghan rested in a picnic basket while the trees gave one last polite rustle",
        "lesson": "a strange sound deserves a calm test before a grand conclusion",
    },
    {
        "key": "sleeping_beast",
        "premise": "an Afghan blanket covered a mound beside the trail, with one corner rising and falling",
        "problem": "The moving corner looked exactly like the breathing back of a sleeping forest beast",
        "mistake": "{name} whispered that the beast was large enough to snore clouds and began planning a heroic rescue",
        "clue": "the mound rose only when the breeze puffed beneath the blanket",
        "dialogue": "'A real animal would not fold into square corners,' {name} said. 'We should look from far away.'",
        "action": "They stayed on the marked trail while an adult used a long stick to lift one corner from a safe distance",
        "result": "A basket of pinecones appeared, and the blanket was returned to the family who had left it there",
        "ending": "The pinecones rolled like little brown marbles as the empty Afghan warmed a bench",
        "lesson": "careful observation can shrink a frightening guess into an ordinary answer",
    },
    {
        "key": "echoed_warning",
        "premise": "a red Afghan was tied between two trees to mark a rest spot",
        "problem": "A hiker's warning bounced between the trunks and sounded like the blanket itself shouting",
        "mistake": "{name} claimed the Afghan had learned every trail rule and was scolding travelers",
        "clue": "the same words echoed again when the adult spoke toward the trees without touching the blanket",
        "dialogue": "'The trees are repeating the voice,' {name} said. 'The Afghan is only listening.'",
        "action": "The group moved to the signed rest area, lowered their voices, and untied the blanket after checking that nobody needed the marker",
        "result": "The warning became clear, and hikers stopped crowding a muddy part of the trail",
        "ending": "The Afghan folded into a bright square while the forest kept the last echo like a secret",
        "lesson": "a repeated message should be checked at its source",
    },
    {
        "key": "moonlit_map",
        "premise": "an Afghan patterned with silver diamonds glimmered under moonlight beside a fork in the trail",
        "problem": "The diamonds looked like a map of a secret path, and the companions disagreed about which way the blanket pointed",
        "mistake": "{name} picked the biggest diamond and declared it the route to a legendary hilltop",
        "clue": "a real trail marker stood beside the blanket and pointed in a different direction",
        "dialogue": "'The pattern is pretty, but the wooden sign knows the way,' {name} admitted",
        "action": "They stayed together, followed the marked trail, and carried the Afghan to the ranger station",
        "result": "The ranger explained that the blanket belonged to campers and thanked them for not wandering off-trail",
        "ending": "Moonlight silvered the proper sign while the Afghan became a cozy seat at the station",
        "lesson": "a vivid pattern is not always an instruction",
    },
    {
        "key": "raven_rumor",
        "premise": "a raven tugged at an Afghan corner near a ferny bend",
        "problem": "Its croak and the flapping cloth sounded like a quarrel between two invisible travelers",
        "mistake": "{name} repeated the rumor so dramatically that the companion began looking for a second raven",
        "clue": "the raven tugged once, flew away, and returned only when the corner loosened",
        "dialogue": "'We heard one bird and one blanket,' {name} said. 'Our story grew taller than the evidence.'",
        "action": "An adult secured the Afghan in a pack, and the group watched the raven fly safely from the trail",
        "result": "The imaginary argument vanished, and the real bird found a quiet branch",
        "ending": "The raven clicked from above as the folded Afghan rode home without a complaint",
        "lesson": "a rumor can grow wings, so check what actually happened",
    },
    {
        "key": "giant_shadow",
        "premise": "an Afghan hung from a low branch, throwing a huge shadow across the trail",
        "problem": "The shadow stretched over the ferns and seemed to belong to a giant with six long arms",
        "mistake": "{name} raised a pinecone as a shield and promised to negotiate with the enormous stranger",
        "clue": "when the lantern moved, the giant shadow moved in exactly the same way",
        "dialogue": "'The giant follows the lantern because it is only a shadow,' {name} explained",
        "action": "They stepped back, lowered the lantern, and asked an adult to remove the blanket from the branch",
        "result": "The shadow shrank into an ordinary cloth shape, and the trail was clear again",
        "ending": "The Afghan folded small enough for one arm while the moon made the ferns look friendly",
        "lesson": "matching movements can reveal what a shadow really is",
    },
    {
        "key": "hidden_campfire",
        "premise": "an Afghan covered a low bundle near a cold fire ring",
        "problem": "A warm smell beneath it made everyone think a sleeping dragon was hiding under the cloth",
        "mistake": "{name} offered the dragon a pinecone crown and prepared to ask for a ride above the treetops",
        "clue": "the smell came from a sealed picnic pot sitting beside the bundle",
        "dialogue": "'The dragon has a cooking pot beside it,' {name} said. 'That sounds more like campers.'",
        "action": "They kept their distance and called a ranger, who checked the cold fire ring and moved the food safely",
        "result": "The dragon became a covered picnic basket, and the campsite was left clean",
        "ending": "The Afghan became a blanket for the ranger's bench while the forest settled into its tall, dark hush",
        "lesson": "a sensible question can cool a hot imagination",
    },
    {
        "key": "talking_trail",
        "premise": "a striped Afghan was snagged on a branch above a narrow part of the trail",
        "problem": "Each passing breeze made the cloth slap the branch, sounding like someone saying, 'Turn back!'",
        "mistake": "{name} obeyed the blanket and told everyone the trail had learned to give advice",
        "clue": "the slapping happened only when the wind came through the gap between two trees",
        "dialogue": "'The gap is speaking through the cloth,' {name} said. 'The trail sign still gives the real advice.'",
        "action": "They used the wider marked path and asked an adult to retrieve the Afghan with a pole",
        "result": "Nobody crossed the narrow muddy patch, and the blanket was returned without a tear",
        "ending": "The cloth was quiet in the pack, while the wide trail curled safely toward home",
        "lesson": "listen to warnings, but make sure you know who is giving them",
    },
    {
        "key": "lost_owner",
        "premise": "a green Afghan sat neatly on a trail bench with no one nearby",
        "problem": "The companion thought the blanket was a sleeping traveler and guarded it with a fierce growl",
        "mistake": "{name} agreed that the quiet bundle must be a very patient forest person",
        "clue": "a name tag sewn inside the Afghan matched a family registered at the visitor center",
        "dialogue": "'It has an owner's name, so we should help the blanket go home,' {name} said",
        "action": "They left the Afghan on the bench, told a ranger, and waited away from the trail edge",
        "result": "The family returned, thanked them, and explained that the blanket had blown from their picnic basket",
        "ending": "The green Afghan wrapped around a tired child as the family waved goodbye",
        "lesson": "ownership clues can solve a mystery without taking what is not yours",
    },
    {
        "key": "storm_dragon",
        "premise": "an Afghan snapped in a sudden breeze just as thunder rolled beyond the ridge",
        "problem": "The crack of cloth and the thunder together sounded like a dragon beating enormous wings",
        "mistake": "{name} promised to lead the dragon to a quieter cave before the next boom",
        "clue": "the cloth snapped before each small gust, while the thunder arrived later from the ridge",
        "dialogue": "'The blanket is first and the thunder is second,' {name} said. 'They only sound like one monster.'",
        "action": "The group followed the safety signs to the shelter and packed the Afghan under an adult's arm",
        "result": "Everyone reached cover before the rain, and the dragon rumor dissolved into weather and cloth",
        "ending": "Inside the shelter, the Afghan made a warm roof over their knees while rain drummed outside",
        "lesson": "separating events by time can untangle a confusing sound",
    },
    {
        "key": "fox_den",
        "premise": "an Afghan was draped beside a hollow log where a fox kit peeked from the ferns",
        "problem": "The cloth's fringe waved over the hollow, and the companion thought the Afghan was inviting the fox out",
        "mistake": "{name} waved back and announced that the blanket spoke fluent fox",
        "clue": "the fox moved away whenever the fringe came near but relaxed when the cloth was still",
        "dialogue": "'The fox wants space, not conversation,' {name} said, stepping back",
        "action": "They stayed quiet, kept the companion close, and asked a ranger to move the Afghan away from the den",
        "result": "The fox returned to the ferns, and the blanket was placed well away from the animal's home",
        "ending": "The Afghan warmed the ranger's shoulders while the fox's nose vanished into the green",
        "lesson": "understanding an animal may mean giving it room",
    },
    {
        "key": "ranger_flag",
        "premise": "a yellow Afghan was tied to a post near a washed-out section of forest trail",
        "problem": "Its bright squares looked like a festival flag inviting everyone to cross",
        "mistake": "{name} called the muddy gap a secret shortcut and began telling a tall story about racing deer across it",
        "clue": "a smaller sign beside the Afghan clearly said TRAIL CLOSED",
        "dialogue": "'The big cloth catches our eyes, but the little sign tells the truth,' {name} said",
        "action": "They turned around, followed the detour arrows, and reported the loose blanket to a ranger",
        "result": "The group stayed dry, and the ranger secured the warning marker",
        "ending": "The yellow Afghan fluttered beside the safe detour like a cheerful sun",
        "lesson": "read every sign before choosing a path",
    },
]


ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P, forest_trail), object(P, afghan), feature(P, misunderstanding).

story_ok(P) :- valid(P), dialogue(P), clue(P), safe_action(P), resolved(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tall Tale world: an Afghan misunderstanding on a forest trail."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--object-name", default="afghan")
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
    object_name = (args.object_name or "afghan").strip().lower()
    if object_name != "afghan":
        raise StoryError("This forest-trail world requires the object name 'afghan'.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        object_name=object_name,
        seed=args.seed,
    )


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("params", "p1"),
        asp.fact("setting", "p1", "forest_trail"),
        asp.fact("object", "p1", "afghan"),
        asp.fact("feature", "p1", "misunderstanding"),
        asp.fact("dialogue", "p1"),
        asp.fact("clue", "p1"),
        asp.fact("safe_action", "p1"),
        asp.fact("resolved", "p1"),
    ]
    return "\n".join(facts)


def aspire() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp

    model = asp.one_model(aspire())
    valid = set(asp.atoms(model, "valid"))
    accepted = set(asp.atoms(model, "story_ok"))
    if ("p1",) not in valid or ("p1",) not in accepted:
        print("Mismatch: ASP did not accept the forest-trail story.")
        return 1
    sample = generate(StoryParams(name="Luna", companion="raven", seed=7))
    required = ("afghan", "forest trail", "misunderstanding")
    if not all(word in sample.story.lower() for word in required):
        print("Mismatch: generated story lost a required world feature.")
        return 1
    if "said" not in sample.story.lower():
        print("Mismatch: generated story lacks spoken dialogue.")
        return 1
    print("OK: Python and ASP accept the forest-trail misunderstanding story.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.setting != "forest trail":
        raise StoryError("This story must take place on a forest trail.")
    if params.object_name != "afghan":
        raise StoryError("The story object must be an afghan.")
    if not params.name or not params.companion:
        raise StoryError("A named traveler and companion are required.")

    world = World(params)
    traveler = world.add(Entity(params.name, "character", params.name))
    companion = world.add(Entity(params.companion, "companion", f"the {params.companion}"))
    afghan = world.add(Entity("afghan", "object", "an Afghan"))

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(ord(ch) for ch in f"{params.name}|{params.companion}|{params.object_name}")
    scenario = SCENARIOS[stable_seed % len(SCENARIOS)]
    values = {"name": params.name, "companion": params.companion}
    detail = {
        key: value.format(**values)
        for key, value in scenario.items()
        if key != "key"
    }

    traveler.memes.update(curious=1.0, imaginative=1.0, careful=1.0)
    companion.memes["alert"] = 1.0
    afghan.meters.update(safe=1.0, visible=1.0)
    world.facts.update(
        setting="forest trail",
        feature="misunderstanding",
        scenario=scenario["key"],
        clue=detail["clue"],
        safe_action=detail["action"],
        resolved=True,
        dialogue=True,
        traveler=traveler,
        companion=companion,
        afghan=afghan,
    )

    world.say(
        f"On a bright morning, {params.name} and the {params.companion} followed a forest trail "
        f"where the ferns brushed their boots. Ahead, {detail['premise']}. "
        f"It looked so important that {params.name} began a tall tale before anyone had asked a question."
    )
    world.say(
        f"The misunderstanding grew quickly. {detail['problem']}. "
        f"{detail['mistake']}. The {params.companion} made a worried sound, and the trail suddenly felt much bigger."
    )
    world.say(
        f"Then {params.name} stopped at a safe distance and studied the scene. "
        f"The useful clue was simple: {detail['clue']}. "
        f"{detail['dialogue']} The words changed the plan from rushing ahead to checking together."
    )
    world.say(
        f"{detail['action']}. No one grabbed the Afghan, chased an animal, or left the marked trail. "
        f"The forest had room for a mystery, but it did not need anyone to make the mystery dangerous."
    )
    world.say(
        f"The careful choice fixed the misunderstanding. {detail['result']}. "
        f"{params.name} laughed softly and admitted that the first story had been much taller than the truth."
    )
    world.say(
        f"By late afternoon, {detail['ending']}. "
        f"The forest trail went on beneath the trees, and {params.name} remembered that {detail['lesson']}.")

    story_qa = [
        QAItem(
            question=f"What did {params.name} misunderstand on the forest trail?",
            answer=f"{params.name} misunderstood the Afghan scene because {detail['problem'].lower()}.",
        ),
        QAItem(
            question="What clue corrected the misunderstanding?",
            answer=f"The clue was that {detail['clue']}. That observation showed what was really happening.",
        ),
        QAItem(
            question=f"What did {params.name} say to the {params.companion}?",
            answer=f"{detail['dialogue']}. The exchange changed the group’s decision from guessing to checking safely.",
        ),
        QAItem(
            question="How did the travelers act safely?",
            answer=f"They stayed on the marked trail and followed this careful plan: {detail['action']}.",
        ),
        QAItem(
            question="What happened after the truth was discovered?",
            answer=f"{detail['result']}. The result showed that the frightening story had been a misunderstanding.",
        ),
        QAItem(
            question="What lesson did the tall tale teach?",
            answer=f"It taught that {detail['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is an Afghan?",
            answer="An Afghan is a warm, often knitted or crocheted blanket made from connected squares or other patterned pieces.",
        ),
        QAItem(
            question="What is a forest trail?",
            answer="A forest trail is a marked path through trees and plants that helps people travel without wandering into unsafe places.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone understands a sound, sight, or message incorrectly.",
        ),
        QAItem(
            question="Why should hikers stay on marked trails?",
            answer="Marked trails help hikers avoid hazards, protect plants and animals, and find their way safely.",
        ),
    ]
    prompts = [
        f"Tell a Tall Tale about {params.name} and a {params.companion} meeting an Afghan on a forest trail.",
        f"Write a child-friendly misunderstanding story in which an Afghan seems mysterious until {params.name} finds a clue.",
        "Create a forest-trail adventure with spoken dialogue, a mistaken guess, a safe investigation, and a warm ending.",
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
        print("\n--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
        print(f"facts: {sample.world.facts}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(aspire())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(aspire())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "raven", seed=11),
            StoryParams("Milo", "badger", seed=23),
            StoryParams("Nora", "fox", seed=37),
            StoryParams("Tariq", "goat", seed=41),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
