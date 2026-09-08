#!/usr/bin/env python3
"""
A cautionary fairy-tale world about a runaway gate, a tiny hinge, and the
foreshadowing that helps Luna stop a rampage before the village is harmed.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    companion: str
    object_name: str
    setting: str = "the Moonlit Village"
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


NAMES = ["Luna", "Mira", "Tavi", "Nell", "Orin", "Pip"]
COMPANIONS = ["fox", "sparrow", "rabbit", "hedgehog", "mouse"]
OBJECTS = ["silver gate", "orchard gate", "moon gate", "blue iron gate"]

SCENARIOS = [
    {
        "key": "rattling_gate",
        "premise": "the old silver gate began to swing by itself whenever the north wind puffed",
        "foreshadowing": "Earlier that morning, its lower hinge had squeaked three times, and a sleepy crow had warned, 'A little creak may become a great clatter.'",
        "problem": "When the wind rose, the gate slammed open and started a rampage down the village lane, knocking over baskets and chasing geese",
        "mistake": "{name} first tried to outrun the gate, but every hurried shove made its loose hinge rattle harder",
        "clue": "the gate always lurched just after its lower hinge lifted from the stone socket",
        "dialogue": "'The hinge is the heart of this trouble,' {name} said. 'Then let us mend the heart, not wrestle the whole gate,' replied the {companion}.",
        "action": "{name} led the {companion} behind the well, fetched a wooden wedge, and asked the village smith to pin the hinge while everyone stayed clear",
        "result": "The wedge steadied the hinge long enough for the smith to fasten it, and the gate stopped its rampage before reaching the market",
        "ending": "At dusk, the repaired gate opened with one polite creak, as if bowing to the moon",
        "lesson": "small warnings deserve attention before they grow into large dangers",
    },
    {
        "key": "gooseyard_hinge",
        "premise": "a painted garden door guarded the royal geese, and its brass hinge shone like a tiny sun",
        "foreshadowing": "At breakfast, one feather had caught on the hinge, and the oldest goose had honked three times at the crooked door",
        "problem": "The hinge snapped during a gust, sending the door on a wild rampage that scattered geese toward the thorny wood",
        "mistake": "{name} waved a ribbon to make the geese follow, but the flapping ribbon made the frightened flock rush faster",
        "clue": "the geese calmed whenever the broken door stopped banging against the post",
        "dialogue": "'Quiet the hinge, and the geese may hear us,' said {name}. 'I will bring the soft blanket,' answered the {companion}.",
        "action": "{name} and the {companion} used a blanket as a gentle screen while the smith secured the door with a rope and replaced the hinge",
        "result": "The geese turned from the thorns and waddled safely into a smaller pen while the repaired door rested against its post",
        "ending": "The royal geese slept beneath moonflowers, and the brass hinge gleamed without a single clank",
        "lesson": "calm surroundings can help frightened creatures make safer choices",
    },
    {
        "key": "miller_gate",
        "premise": "the miller's red gate stood beside a rushing stream and guarded the path to the flour mill",
        "foreshadowing": "The miller had noticed a bright crack near the hinge and tied a yellow thread there as a warning",
        "problem": "The thread broke, the gate sprang loose, and its rampage sent flour sacks rolling toward the water",
        "mistake": "{name} chased the nearest sack and nearly stepped onto the slippery mill bridge",
        "clue": "the crack widened whenever the gate was pulled from the stream side",
        "dialogue": "'The yellow thread was a warning, not decoration,' {name} said. 'Then we must stand on the dry bank,' said the {companion}.",
        "action": "They stayed on the dry bank, called the miller, and used a long pole to guide the sacks away while the hinge was braced",
        "result": "The sacks were saved, the gate was chained shut, and the miller replaced the cracked hinge before reopening the path",
        "ending": "Fresh flour dusted the red gate like snow, while the stream hurried harmlessly beneath the bridge",
        "lesson": "a visible warning is useful only when people respect what it says",
    },
    {
        "key": "moon_fair",
        "premise": "the Moon Fair's tall entrance gate glittered with bells and a single crescent-shaped hinge",
        "foreshadowing": "Before the music began, the bells chimed even though no one touched them",
        "problem": "The hinge buckled, and the decorated gate began a noisy rampage through the fairground, scattering ribbons and toy crowns",
        "mistake": "{name} rang a louder bell to call everyone away, but the extra clang made the crowd hurry in the wrong direction",
        "clue": "the smallest bell fell silent whenever the hinge was held still",
        "dialogue": "'Listen for the quiet bell,' {name} said. 'It tells us where to help,' replied the {companion}.",
        "action": "The fair keeper cleared a circle, while {name} held the gate still with a folded tent pole and the smith removed the bent hinge",
        "result": "The gate stopped moving, the crowd returned safely, and the fair reopened with the entrance tied wide",
        "ending": "Children passed beneath the harmless arch as moon-shaped bells chimed softly overhead",
        "lesson": "a good clue may be quieter than the trouble it explains",
    },
    {
        "key": "castle_hinge",
        "premise": "a little castle door protected the princess's sleeping garden from a herd of enchanted pumpkins",
        "foreshadowing": "One pumpkin had rolled against the hinge at dawn, leaving a golden smear and a warning wobble",
        "problem": "The hinge bent, the door flew open, and the pumpkins began a round orange rampage across the herb beds",
        "mistake": "{name} tried to stop every pumpkin at once, which only sent them bouncing in new directions",
        "clue": "the pumpkins all turned when the loose door knocked against the same stone",
        "dialogue": "'One hinge guides the whole door,' said {name}. 'Then one steady hand may guide our plan,' said the {companion}.",
        "action": "{name} placed a cushion against the stone while the gardener built a low ramp that guided the pumpkins into a hay-lined court",
        "result": "The pumpkins rolled safely into the court, and the gardener repaired the hinge before reopening the garden",
        "ending": "By morning, the princess found golden pumpkins resting in neat rows beside the quiet door",
        "lesson": "understanding the source of a problem is better than chasing every symptom",
    },
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P, moonlit_village), companion(P, _), object(P, _).
story_ok(P) :- valid(P), hinge(P), foreshadowing(P), rampage_stopped(P), cautionary(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary fairy tale about a rampaging gate hinge.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--object-name", choices=OBJECTS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
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
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        object_name=args.object_name or rng.choice(OBJECTS),
        seed=args.seed,
    )


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("params", "p1"),
        asp.fact("setting", "p1", "moonlit_village"),
        asp.fact("companion", "p1", "fox"),
        asp.fact("object", "p1", "silver_gate"),
        asp.fact("hinge", "p1"),
        asp.fact("foreshadowing", "p1"),
        asp.fact("rampage_stopped", "p1"),
        asp.fact("cautionary", "p1"),
    ]
    return "\n".join(facts)


def aspire() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp

    model = asp.one_model(aspire())
    if ("p1",) in set(asp.atoms(model, "valid")) and ("p1",) in set(asp.atoms(model, "story_ok")):
        print("OK: ASP and Python accept the cautionary hinge tale.")
        return 0
    print("Mismatch: ASP rejected the cautionary hinge tale.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting != "the Moonlit Village":
        raise StoryError("This fairy-tale domain belongs in the Moonlit Village.")
    if not params.object_name.endswith("gate"):
        raise StoryError("The chosen object must be a gate so its hinge can drive the tale.")

    world = World(params)
    hero = world.add(Entity(params.name, "character", params.name))
    companion = world.add(Entity(params.companion, "creature", f"the {params.companion}"))
    gate = world.add(Entity("gate", "object", params.object_name))

    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in f"{params.name}|{params.companion}|{params.object_name}")
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    values = {
        "name": params.name,
        "companion": params.companion,
        "object_name": params.object_name,
    }
    detail = {
        key: value.format(**values)
        for key, value in scenario.items()
        if key != "key"
    }

    hero.memes.update(courage=1.0, patience=1.0, attentiveness=1.0)
    companion.memes["helpful"] = 1.0
    gate.meters.update(stability=1.0, danger=0.0)
    world.facts.update(
        setting="the Moonlit Village",
        scenario=scenario["key"],
        hinge="lower hinge",
        foreshadowing=detail["foreshadowing"],
        danger=detail["problem"],
        rampage_stopped=True,
        cautionary=True,
        entered_danger=False,
    )

    world.say(
        f"In the {params.setting}, {params.name} and a {params.companion} watched the {params.object_name} "
        f"beside the village path. {detail['premise']}."
    )
    world.say(
        f"That was the foreshadowing. {detail['foreshadowing']} "
        f"Nobody knew yet how important that tiny warning would become."
    )
    world.say(
        f"Then the wind woke like a dragon. {detail['problem']}. "
        f"{detail['mistake']}."
    )
    world.say(
        f"{params.name} stopped running and looked closely. The clue was simple: {detail['clue']}. "
        f"{detail['dialogue']}"
    )
    world.say(
        f"Together, they made a safer plan. {detail['action']}. "
        f"They kept away from the swinging gate and never put fingers near the hinge."
    )
    world.say(
        f"The plan changed the ending. {detail['result']}. "
        f"{params.name} understood that {detail['lesson']}."
    )
    world.say(
        f"{detail['ending']}. From then on, whenever a small hinge whispered a warning, "
        f"the villagers listened before a rampage could begin."
    )

    world.facts["outcome"] = detail["result"]
    story_qa = [
        QAItem(
            question=f"What warning did {params.name} notice before the rampage?",
            answer=f"The warning was that {detail['foreshadowing']}. It showed that the hinge needed attention before the gate became dangerous.",
        ),
        QAItem(
            question="What caused the rampage?",
            answer=f"The rampage began because {detail['problem']}. The loose hinge made the gate move unpredictably.",
        ),
        QAItem(
            question=f"What clue helped {params.name} find the cause?",
            answer=f"The clue was that {detail['clue']}. This directed attention to the hinge rather than to every object the gate disturbed.",
        ),
        QAItem(
            question="How did the characters stay safe?",
            answer=f"They stayed away from the swinging gate and hinge while {detail['action']}. Their careful distance prevented another accident.",
        ),
        QAItem(
            question="How was the rampage stopped?",
            answer=f"{detail['result']}. Repairing and steadying the hinge removed the source of the danger.",
        ),
        QAItem(
            question="What cautionary lesson does the fairy tale teach?",
            answer=f"It teaches that {detail['lesson']}. A small warning can be a gift if people pay attention to it.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a hinge?",
            answer="A hinge is a joint with moving parts that lets a door or gate swing open and closed.",
        ),
        QAItem(
            question="Why can a loose hinge be dangerous?",
            answer="A loose hinge can make a heavy door or gate swing unpredictably, so people should keep away and ask a responsible adult to repair it.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early clue that hints at something important that may happen later.",
        ),
        QAItem(
            question="What makes a fairy tale cautionary?",
            answer="A cautionary fairy tale shows a danger, the choices that make it worse or better, and a lesson about acting wisely.",
        ),
    ]
    prompts = [
        f"Tell a fairy tale about {params.name}, a {params.companion}, and a rampaging {params.object_name}.",
        "Include foreshadowing about a small hinge, a brief dialogue exchange, and a cautionary resolution.",
        "Write a child-safe fairy tale in which noticing a tiny warning prevents a much larger danger.",
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
                f"{entity.label}: kind={entity.kind}, "
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
            StoryParams("Luna", "fox", "silver gate", seed=base_seed),
            StoryParams("Mira", "rabbit", "orchard gate", seed=base_seed + 1),
            StoryParams("Tavi", "sparrow", "moon gate", seed=base_seed + 2),
        ]
    else:
        params_list = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params_list.append(
                StoryParams(
                    name=args.name or rng.choice(NAMES),
                    companion=args.companion or rng.choice(COMPANIONS),
                    object_name=args.object_name or rng.choice(OBJECTS),
                    seed=base_seed + index,
                )
            )

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
