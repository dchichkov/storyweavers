#!/usr/bin/env python3
"""
A child-facing superhero story world about bacon, a brave removal, a twist,
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "Sunbeam City"
    hero: str = "Luna"
    rival: str = "Volt"
    helper: str = "Pip"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "Sunbeam City": {"tags": {"city", "sky", "heroic"}, "mood": "bright and busy"},
    "Moonbridge Harbor": {"tags": {"harbor", "night", "heroic"}, "mood": "silver and windy"},
    "Cloudtop Village": {"tags": {"village", "cloud", "heroic"}, "mood": "soft and floating"},
}


@dataclass(frozen=True)
class HeroArc:
    title: str
    premise: str
    problem: str
    twist: str
    dialogue: str
    action: str
    resolution: str
    ending: str
    problem_answer: str
    twist_answer: str
    resolution_answer: str


ARCS = [
    HeroArc(
        title="The Bacon Beacon",
        premise="Luna patrolled Sunbeam City with a cape that shimmered whenever someone needed help.",
        problem="A giant bacon-shaped beacon had jammed above the town hall, sending smoky signals that made every rescue robot rush the wrong way.",
        twist="The villain was not a villain at all: Volt had built the beacon to call for help after his tiny sister became stuck inside its control tower.",
        dialogue='"I thought you were causing the trouble," Luna said. "I was trying to stop it," Volt answered. "Then let us fix it together," said Luna.',
        action="Luna used her wind-gloves to hold the beacon steady while Volt removed the cracked signal coil and Pip guided the frightened sister down the stairs.",
        resolution="The false alarms stopped, and the beacon began shining one calm golden circle for every real emergency.",
        ending="Luna and Volt shared a warm bacon sandwich beneath the repaired beacon while the little sister waved from the safest step.",
        problem_answer="A bacon-shaped beacon sent smoky false signals, causing the city's rescue robots to rush in the wrong direction.",
        twist_answer="Volt had made the beacon to call for help because his little sister was trapped inside its tower.",
        resolution_answer="Luna and Volt reconciled, removed the cracked signal coil, rescued the sister, and repaired the beacon.",
    ),
    HeroArc(
        title="The Sidewalk Snatcher",
        premise="Luna protected Moonbridge Harbor by listening for trouble beneath the sound of bells and waves.",
        problem="A rolling machine was removing every sidewalk tile, leaving children, carts, and a bacon vendor stranded on separate bits of pavement.",
        twist="The machine belonged to Volt, who was trying to remove a hidden magnet that had trapped the harbor's rescue bridge underground.",
        dialogue='"Why are you stealing the path?" Luna asked. "I am clearing the trap," Volt said. "Next time, tell me before the tiles disappear," she replied.',
        action="Luna lifted the loose tiles one by one while Volt turned the machine gently, and together they pulled the giant magnet free.",
        resolution="The bridge rose again, the sidewalk returned, and Volt promised to ask for help before using his noisy inventions.",
        ending="the bacon vendor rolled his cart across the restored path and gave both heroes the crispiest strips.",
        problem_answer="A rolling machine removed the harbor's sidewalk tiles and stranded people on separated patches of pavement.",
        twist_answer="Volt was removing the tiles to reach a hidden magnet that had trapped the rescue bridge underground.",
        resolution_answer="The heroes removed the magnet together, restored the bridge and sidewalk, and agreed to communicate honestly.",
    ),
    HeroArc(
        title="The Cape in the Pan",
        premise="At Cloudtop Village, Luna wore a red cape and carried a pan of bacon to the morning rescue club.",
        problem="A gust lifted the pan, and its sizzling bacon flew toward the village's balloon engines.",
        twist="The gust came from Volt's new fan, but he had turned it on to push away a swarm of stinging sky-bees.",
        dialogue='"Your fan sent the bacon flying!" Luna cried. "The bees were coming," Volt explained. "We can save both the bees and breakfast," she said.',
        action="Luna guided the bacon pan behind a cloud wall while Volt slowed the fan, and Pip removed a sticky honeycomb from its spinning guard.",
        resolution="The sky-bees drifted safely toward flowers, the engines stayed clean, and the bacon landed back in the pan.",
        ending="the heroes ate breakfast beside the flower clouds and labeled the fan with a bright red safety switch.",
        problem_answer="A gust sent a pan of bacon toward the village's balloon engines.",
        twist_answer="Volt's fan caused the gust because he was trying to protect the village from stinging sky-bees.",
        resolution_answer="The heroes slowed the fan, removed the honeycomb, protected the engines, and saved both the bees and the bacon.",
    ),
    HeroArc(
        title="The Masked Breakfast Mystery",
        premise="Luna arrived at Sunbeam City's rooftop breakfast festival when the mayor's famous bacon vanished.",
        problem="Every hero blamed the quiet newcomer in a silver mask, and angry whispers began to spread through the crowd.",
        twist="The silver-masked newcomer had not stolen the bacon; he had removed it from a hot grill after noticing a dangerous spark.",
        dialogue='"Did you take the bacon?" Luna asked. "I moved it before the fire grew," said the newcomer. "Thank you for telling us," Luna answered.',
        action="Luna checked the grill, the mayor apologized, and the newcomer helped remove the broken wire while Pip carried the bacon to a cool table.",
        resolution="The crowd learned to ask questions before blaming someone, and the newcomer was welcomed as a careful hero.",
        ending="the festival resumed with a fresh platter of bacon and a silver mask hanging beside Luna's red cape.",
        problem_answer="The mayor's bacon disappeared, and the crowd blamed a quiet newcomer without asking what happened.",
        twist_answer="The newcomer removed the bacon from a dangerous grill to prevent a fire.",
        resolution_answer="Luna investigated, the mayor apologized, and the newcomer helped make the festival safe.",
    ),
    HeroArc(
        title="The Bacon Bat Signal",
        premise="Each night, Luna watched over Moonbridge Harbor from a tower topped with a glowing bacon-shaped signal.",
        problem="The signal suddenly called every hero to the same empty alley, leaving the real harbor bridge without help.",
        twist="Volt had changed the signal because he felt forgotten after Luna received all the city's medals.",
        dialogue='"I changed the signal because nobody noticed me," Volt said. "I should have noticed," Luna replied. "Let us share the watch," she added.',
        action="Luna removed the false signal pattern, then invited Volt to design a second light for rescues that needed his special electric skills.",
        resolution="The signal became clear again, and both heroes took turns leading patrols.",
        ending="two lights blinked over the harbor, one red and one blue, while Luna and Volt stood together on the tower.",
        problem_answer="A bacon-shaped signal sent heroes to an empty alley while the real harbor bridge was left unguarded.",
        twist_answer="Volt changed the signal because he felt overlooked after Luna received all the medals.",
        resolution_answer="Luna listened, removed the false pattern, and shared leadership by creating a second rescue light for Volt.",
    ),
]


OPENINGS = [
    "In {setting}, where rooftops glittered after rain, {hero} flew past carrying a paper bag of bacon.",
    "Every child in {setting} knew the red cape of {hero}, the city's kindest superhero.",
    "At sunrise in {setting}, {hero} checked the rescue tower while the smell of bacon curled through the streets.",
    "The day began with a strange bacon signal above {setting}, and {hero} raced toward it in a silver streak.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.rival, params.helper))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: HeroArc = f["arc"]
    facts = {
        "setting": f["setting"],
        "hero": f["hero"],
        "rival": f["rival"],
        "helper": f["helper"],
    }
    opening = _fill(OPENINGS[f["opening_variant"]], facts)
    premise = _fill(arc.premise, facts)
    problem = _fill(arc.problem, facts)
    twist = _fill(arc.twist, facts)
    dialogue = _fill(arc.dialogue, facts)
    action = _fill(arc.action, facts)
    resolution = _fill(arc.resolution, facts)
    ending = _fill(arc.ending, facts)

    structures = [
        [
            f"{opening} This is the superhero story called \"{arc.title}.\"",
            f"{premise} {problem}",
            f"{_cap(f['rival'])} stood beside the machine. {twist}",
            dialogue,
            action,
            f"{resolution} At sunset, {ending}",
        ],
        [
            opening,
            f"\"What is going wrong?\" {f['helper']} asked. {premise}",
            _cap(problem),
            f"Then came the twist. {twist}",
            dialogue,
            f"Instead of fighting, the heroes worked side by side. {action} {resolution}",
            f"The proof was simple: {ending}",
        ],
        [
            f"People still tell \"{arc.title}\" whenever they smell bacon near a rescue tower.",
            f"{opening} {premise}",
            f"But the trouble was serious. {problem}",
            f"{twist} \"We need the truth before we choose a target,\" said {f['hero']}.",
            dialogue,
            action,
            f"After that, {resolution} {ending}",
        ],
        [
            opening,
            f"The first clue was a warm smell and a crooked signal. {problem}",
            f"{f['hero']} found {f['rival']} nearby. {twist}",
            dialogue,
            f"Together they made a new plan. {action}",
            f"When the danger passed, {resolution}",
            f"That evening, {ending}",
        ],
    ]
    return structures[f["structure_variant"]]


ASP_RULES = r"""
setting(sunbeam_city).
setting(moonbridge_harbor).
setting(cloudtop_village).

feature(twist).
feature(reconciliation).
ingredient(bacon).
action(remove).

can_tell_story(S) :-
    setting(S),
    feature(twist),
    feature(reconciliation),
    ingredient(bacon),
    action(remove).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.lower().replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.extend(
        [
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("ingredient", "bacon"),
            asp.fact("action", "remove"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero story world about bacon, removal, twists, and reconciliation."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--rival")
    parser.add_argument("--helper")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Nova", "Aster", "Ruby", "Sky"])
    rival = args.rival or rng.choice(["Volt", "Moss", "Echo", "Blaze", "Glimmer"])
    helper = args.helper or rng.choice(["Pip", "Tess", "Bram", "Jo", "Milo"])
    if len({hero, rival, helper}) != 3:
        raise StoryError("The hero, rival, and helper must be different characters.")
    return StoryParams(setting=setting, hero=hero, rival=rival, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if len({params.hero, params.rival, params.helper}) != 3:
        raise StoryError("The hero, rival, and helper must be different characters.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            name=params.hero,
            kind="superhero",
            meters={"energy": 1.0, "distance": 0.0},
            memes={"courage": 1.0, "empathy": 0.8},
        )
    )
    rival = world.add(
        Entity(
            name=params.rival,
            kind="inventor",
            meters={"energy": 0.7, "machine_risk": 0.8},
            memes={"loneliness": 0.7, "hope": 0.5},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="helper",
            meters={"energy": 0.8},
            memes={"curiosity": 1.0, "care": 0.9},
        )
    )
    bacon = world.add(
        Entity(
            name="the bacon",
            kind="food",
            meters={"warmth": 0.9, "crispness": 0.8},
            memes={"sharing": 1.0},
        )
    )
    machine = world.add(
        Entity(
            name="the troublesome device",
            kind="machine",
            meters={"danger": 0.7, "stability": 0.3},
            memes={"confusion": 0.8},
        )
    )

    world.facts.update(
        setting=params.setting,
        hero=hero.name,
        rival=rival.name,
        helper=helper.name,
        arc=arc,
        opening_variant=(seed // len(ARCS)) % len(OPENINGS),
        structure_variant=(seed // (len(ARCS) * len(OPENINGS))) % 4,
        bacon=bacon.name,
        device=machine.name,
        twist="the hidden reason became clear",
        reconciliation="the heroes listened, apologized, and worked together",
        removed="the dangerous part was removed safely",
    )

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a child-friendly superhero story about {params.hero}, bacon, and a problem in {params.setting}.",
        "Include a twist that changes how the rival is understood.",
        "Show reconciliation after a disagreement, with someone removing a dangerous object or part.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=arc.twist_answer,
        ),
        QAItem(
            question="How did the heroes reconcile and solve the problem?",
            answer=arc.resolution_answer,
        ),
        QAItem(
            question=f"What image closes the story of \"{arc.title}\"?",
            answer=f"The story closes with {arc.ending}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special abilities to protect and help others.",
        ),
        QAItem(
            question="What does it mean to remove something?",
            answer="To remove something means to take it away from a place or situation.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that reveals the situation is different from what it first seemed.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and finding a way forward.",
        ),
        QAItem(
            question="What is bacon?",
            answer="Bacon is a salty food made from pork and usually cooked until warm and crisp.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
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


def _valid_python() -> list[str]:
    return sorted(setting.lower().replace(" ", "_") for setting in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    expected = {(setting,) for setting in _valid_python()}
    actual = set(_asp_valid())
    if expected == actual:
        print(f"OK: clingo gate matches python ({len(expected)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(expected - actual))
    print("clingo only:", sorted(actual - expected))
    return 1


def verify_generation() -> int:
    for index, setting in enumerate(SETTING_REGISTRY):
        sample = generate(
            StoryParams(
                setting=setting,
                hero="Luna",
                rival="Volt",
                helper="Pip",
                seed=100 + index,
            )
        )
        if not sample.story.strip():
            print("Generated an empty story.")
            return 1
        if "bacon" not in sample.story.lower():
            print("Generated story omitted bacon.")
            return 1
        if "remove" not in sample.story.lower() and "removed" not in sample.story.lower():
            print("Generated story omitted removal.")
            return 1
        if len(sample.story_qa) < 3:
            print("Generated story omitted required questions.")
            return 1
    print("OK: Python generation checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return

    if args.verify:
        code = asp_verify()
        if code:
            sys.exit(code)
        sys.exit(verify_generation())

    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        hero="Luna",
                        rival="Volt",
                        helper="Pip",
                        seed=base_seed,
                    )
                )
            )
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
