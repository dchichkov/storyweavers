#!/usr/bin/env python3
"""
A small mythic circus mystery about a wedged cruller, careful listening,
and a hidden kindness beneath the striped tent.
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
    prize: str
    setting: str = "Moonwheel Circus"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)


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


NAMES = ["Luna", "Milo", "Tavi", "Nia", "Orin", "Pip", "Sela", "Jun"]
COMPANIONS = ["fox", "raven", "goat", "mouse", "pony"]
PRIZES = ["cruller", "sugar cruller", "golden cruller"]

SCENARIOS = [
    {
        "key": "bell_rope",
        "premise": "the circus's oldest bell rang once, though no hand touched its rope",
        "problem": "the ringmaster could not open the evening show because the bell rope was wed in a brass pulley above the tent",
        "clue": "a faint cinnamon smell rose from the pulley, and crumbs rested on the bell platform",
        "dialogue": "'The bell is not haunted,' said {name}. 'Something sweet has caught its rope.'",
        "action": "they followed the crumbs to a cruller wed between the pulley wheel and its wooden guard",
        "result": "an adult lowered the rope, freed the cruller with a padded hook, and left the pulley turning smoothly",
        "ending": "When the moon climbed over the tent, the bell rang three clear notes, and the rescued cruller was shared at the workers' table",
        "lesson": "a strange sound may have an ordinary cause waiting for a patient eye",
    },
    {
        "key": "vanishing_ticket",
        "premise": "a silver admission ticket kept appearing beneath different circus seats",
        "problem": "the ticket seller feared that the ticket was a spirit choosing who could enter",
        "clue": "each seat carried the same sticky sugar mark, shaped like a little wheel",
        "dialogue": "'A ghost would not leave pastry crumbs,' {name} whispered. 'Let us inspect the trail.'",
        "action": "they lifted the seat cushions one at a time and found a cruller wed in the folding bench",
        "result": "the ticket was freed from a sugar-slick hinge, and the seller learned that a gust had been moving it along the row",
        "ending": "The silver ticket opened the gate for a child who had been waiting quietly, while the cruller became a snack for the tired usher",
        "lesson": "following small evidence can turn a frightening tale into a helpful truth",
    },
    {
        "key": "sleeping_trumpet",
        "premise": "the circus trumpet played one sleepy note whenever the clown bowed",
        "problem": "the musicians thought the instrument had forgotten the mythic song that summoned the stars",
        "clue": "the trumpet's bell held a warm sugary scent and a single curl of golden paper",
        "dialogue": "'Perhaps the stars are not silent,' said {name}. 'Perhaps the trumpet has a full mouth.'",
        "action": "the band leader gently shook out a cruller wed in the trumpet's wide bell",
        "result": "the trumpet sang again, and the musicians changed their grand spell into a laughing march",
        "ending": "The stars seemed to wink above the striped roof as the clean trumpet called every performer into the ring",
        "lesson": "before blaming lost magic, make room to discover what is blocking it",
    },
    {
        "key": "lion_shadow",
        "premise": "a huge lion shadow prowled behind the circus wagon after sunset",
        "problem": "the stable animals grew frightened, and no one wanted to carry hay past the wagon",
        "clue": "the shadow's mane bobbed whenever the wagon wheel squeaked",
        "dialogue": "'A real lion breathes,' said {name}. 'This one is following a wheel.'",
        "action": "they asked the lantern keeper to brighten the path and found a cruller wed behind the wagon's spoke guard",
        "result": "the cruller had been holding a painted pennant in the wheel, making the pennant's shadow look like a roaming beast",
        "ending": "The wagon rolled freely, the false lion shrank into a fluttering flag, and the animals munched hay under calm stars",
        "lesson": "a moving shadow becomes less mighty when its source is brought into the light",
    },
    {
        "key": "drummer_secret",
        "premise": "the great drum refused to boom during the circus's moon rite",
        "problem": "the drummer believed the drum had lost its thunder and prepared to cancel the finale",
        "clue": "a soft crunch sounded inside whenever the drum tilted toward the east",
        "dialogue": "'Thunder can hide in a small thing,' {name} said. 'Let us listen before we mourn it.'",
        "action": "the drummer opened the safe lower panel and removed a cruller wed beside the drum's inner brace",
        "result": "the drum boomed so deeply that dust danced from the tent ropes, and the final act returned",
        "ending": "The moon rite ended with a thunderous beat, while the cruller sat on a napkin beside the drummer's water cup",
        "lesson": "careful listening can protect a good plan from a hasty ending",
    },
    {
        "key": "missing_crown",
        "premise": "the acrobat queen's paper crown vanished before her high-wire entrance",
        "problem": "the troupe suspected that the circus's invisible trickster had stolen the crown",
        "clue": "a trail of sugar dust crossed the costume chest and stopped at the silk curtain",
        "dialogue": "'The trickster leaves no crumbs,' said {name}. 'Let us ask what the dust touched.'",
        "action": "they drew back the curtain and found the crown wed beneath a cruller in a prop basket",
        "result": "the queen brushed off the crown, thanked the hungry stagehand who had set down the pastry, and climbed safely only after the rigging was checked",
        "ending": "Her crown flashed in the lamplight, and the audience cheered the ordinary mystery that had saved the grand entrance",
        "lesson": "solving a mystery also means caring for the people who stood near it",
    },
    {
        "key": "wandering_wagon",
        "premise": "a little blue wagon rolled by itself toward the dark edge of the circus field",
        "problem": "the performers feared that the wagon carried a sleeping spell and might disappear beyond the lanterns",
        "clue": "one wheel turned faster than the others, and its axle smelled of warm spice",
        "dialogue": "'The wagon has no spell,' {name} called. 'It has a pastry in its wheel.'",
        "action": "an adult stopped the wagon with a wooden block and pulled out a cruller wed in the axle",
        "result": "the wheel stopped wobbling, and the wagon was tied safely beside the supply tent",
        "ending": "The blue wagon rested under a moon-painted tarp, no longer wandering, while the cruller was divided among its helpers",
        "lesson": "a safe pause gives a mystery time to reveal its true shape",
    },
    {
        "key": "mirror_maze",
        "premise": "the mirror maze showed a seventh reflection where only six children stood",
        "problem": "the extra figure made the children think a forgotten circus giant was trapped behind the glass",
        "clue": "the seventh reflection had a round brown hat and never blinked",
        "dialogue": "'It is not a giant,' said {name}. 'It is wearing the shape of something round.'",
        "action": "the guide switched on the overhead lantern and found a cruller wed on a ledge behind a tilted mirror",
        "result": "the pastry's reflection had looked like a mysterious visitor, and the guide straightened the mirror before reopening the maze",
        "ending": "Six children waved at six reflections, then ate the cruller outside where every face was easy to see",
        "lesson": "clear light and honest counting can untangle a surprising picture",
    },
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P, moonwheel_circus), object(P, cruller), mystery(P).
story_ok(P) :- valid(P), clue(P), dialogue(P), safe_action(P), resolved(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic circus mystery world.")
    parser.add_argument("--name")
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--prize", choices=PRIZES)
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
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    prize = args.prize or rng.choice(PRIZES)
    if "cruller" not in prize:
        raise StoryError("This circus mystery requires a cruller.")
    return StoryParams(name=name, companion=companion, prize=prize, seed=args.seed)


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("params", "p1"),
        asp.fact("setting", "p1", "moonwheel_circus"),
        asp.fact("object", "p1", "cruller"),
        asp.fact("mystery", "p1"),
        asp.fact("clue", "p1"),
        asp.fact("dialogue", "p1"),
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
    solved = set(asp.atoms(model, "story_ok"))
    if ("p1",) in valid and ("p1",) in solved:
        print("OK: ASP and Python story gates agree.")
        return 0
    print("Mismatch: ASP did not accept the circus mystery.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if "cruller" not in params.prize:
        raise StoryError("A valid story must include a cruller.")
    if params.setting != "Moonwheel Circus":
        raise StoryError("This mythic mystery belongs at the Moonwheel Circus.")

    world = World(params)
    child = world.add(Entity(params.name, "character", params.name))
    companion = world.add(Entity(params.companion, "companion", f"the {params.companion}"))
    cruller = world.add(Entity("cruller", "food", params.prize))

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(ord(ch) for ch in f"{params.name}|{params.companion}|{params.prize}")
    scenario = SCENARIOS[stable_seed % len(SCENARIOS)]
    values = {
        "name": params.name,
        "companion": params.companion,
        "prize": params.prize,
    }
    detail = {
        key: value.format(**values)
        for key, value in scenario.items()
        if key != "key"
    }

    child.memes.update(curiosity=1.0, courage=1.0, kindness=1.0)
    companion.memes["alert"] = 1.0
    cruller.meters["wedged"] = 1.0
    cruller.memes["shared"] = 1.0

    world.facts.update(
        setting="Moonwheel Circus",
        mystery=scenario["key"],
        clue=detail["clue"],
        safe_action=detail["action"],
        resolution=detail["result"],
        entered_danger=False,
        mystery_solved=True,
        dialogue_used=True,
    )

    world.say(
        f"On the night when the moon wore a silver crown, {params.name} and the {params.companion} "
        f"entered the Moonwheel Circus. {detail['premise']}. Even the striped tent seemed to hold its breath."
    )
    world.say(
        f"The odd event became a mystery to solve: {detail['problem']}. "
        f"{params.name} did not rush beneath the rigging or disturb the performers. "
        f"Instead, the {params.companion} lifted its nose and listened."
    )
    world.say(
        f"The clue was small but bright as a star: {detail['clue']}. "
        f"'{detail['dialogue'].split(\"'\", 2)[1]}' "
        f"{params.name} said, and the {params.companion} gave a thoughtful little chirp."
    )
    world.say(
        f"An adult came with a lantern and checked the circus equipment before anyone reached toward it. "
        f"Then {detail['action']}. The {params.companion} watched from the safe side of the rope."
    )
    world.say(
        f"The mystery opened like a flower. {detail['result']}. "
        f"{params.name} understood that {detail['lesson']}."
    )
    world.say(
        f"At last, the circus music began. {detail['ending']}. "
        f"The old myth of the Moonwheel Circus gained a new line that night: "
        f"even a humble cruller may hide the key to a wonder, if someone looks kindly and carefully."
    )

    world.facts.update(child=child, companion=companion, cruller=cruller)

    story_qa = [
        QAItem(
            question=f"What mystery did {params.name} try to solve?",
            answer=f"{params.name} tried to solve the mystery of why {detail['premise']}. The problem involved {detail['problem']}.",
        ),
        QAItem(
            question="What clue helped solve the circus mystery?",
            answer=f"The important clue was that {detail['clue']}. It led the characters toward the real cause instead of a magical guess.",
        ),
        QAItem(
            question=f"What did {params.name} say to the {params.companion}?",
            answer=f"{params.name} said, \"{detail['dialogue'].split(\"'\", 2)[1]}\" The words helped the characters inspect the mystery calmly.",
        ),
        QAItem(
            question="How did the characters stay safe?",
            answer=f"They stayed behind the safety boundary and involved an adult before touching circus equipment. Then {detail['action']}.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"{detail['result']}. The circus could continue, and the cruller became part of a kind, shared ending.",
        ),
        QAItem(
            question="What lesson did the myth teach?",
            answer=f"It taught that {detail['lesson']}. Patience and evidence revealed the truth.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a circus?",
            answer="A circus is a show where performers may use music, costumes, juggling, acrobatics, animals, or other acts to entertain an audience.",
        ),
        QAItem(
            question="What is a cruller?",
            answer="A cruller is a light, twisted pastry that is often fried and covered with sugar or glaze.",
        ),
        QAItem(
            question="What does it mean for something to be wedged?",
            answer="Something is wedged when it is tightly stuck between other objects and cannot move freely.",
        ),
        QAItem(
            question="Why should people inspect a mystery carefully?",
            answer="Careful inspection can reveal ordinary evidence, prevent unsafe guesses, and help people choose a useful solution.",
        ),
    ]
    prompts = [
        f"Tell a mythic circus mystery in which {params.name} discovers why a cruller became wedged.",
        f"Write a child-safe story about {params.name}, a {params.companion}, and a strange event at the Moonwheel Circus.",
        "Create a mystery to solve with a concrete clue, brief dialogue, a safe adult-supported action, and a changed final image.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(aspire())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        for atom in asp.one_model(aspire()):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "fox", "cruller", seed=base_seed),
            StoryParams("Milo", "raven", "golden cruller", seed=base_seed + 1),
            StoryParams("Nia", "goat", "sugar cruller", seed=base_seed + 2),
        ]
    else:
        params_list = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]

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
