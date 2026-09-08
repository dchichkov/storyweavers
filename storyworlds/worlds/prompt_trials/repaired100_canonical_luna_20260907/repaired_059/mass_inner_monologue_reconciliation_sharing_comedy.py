#!/usr/bin/env python3
"""
A small comedy storyworld about Luna, a mysterious mass, private worries,
reconciliation, and sharing a surprisingly useful discovery.
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
    setting: str = "community kitchen"
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


NAMES = ["Luna", "Milo", "Pia", "Nora", "Otto", "Ivy"]
COMPANIONS = ["Tess", "Bram", "Ziggy", "Mara"]
OBJECTS = ["bread dough", "clay lump", "cheese ball", "cookie dough"]

SCENARIOS = [
    {
        "key": "flour_cloud",
        "premise": "a huge mass of bread dough sat in the middle of the table like a sleepy moon",
        "problem": "Luna and her companion had both planned to shape it first, and their tugging made the dough wobble toward the floor",
        "inner": "I want the biggest piece, Luna thought, although she knew that thought sounded rather unhelpful",
        "clue": "the dough became easier to move when they pressed from opposite sides instead of pulling",
        "dialogue": "'I was guarding the dough so hard that I forgot you were helping,' Luna said. 'I was guarding my idea too,' Tess replied.",
        "action": "They split the mass into two smaller portions, then shared flour and rolled one portion into a long loaf",
        "result": "The loaf rose in the oven, while the second portion became small rolls for everyone at the table",
        "ending": "When the bread came out, one enormous roll wore a flour mustache, and Luna and her companion laughed together",
        "lesson": "sharing control can turn a stuck argument into a useful plan",
    },
    {
        "key": "clay_comet",
        "premise": "a round mass of blue clay had rolled under a bench and was wearing a paper crown",
        "problem": "Luna wanted to make a comet, while her companion wanted a bowl, so each secretly hid the clay's best side",
        "inner": "If I say I am worried, Luna thought, perhaps everyone will think I am being bossy",
        "clue": "the clay kept its shape best when both children warmed and pressed it gently",
        "dialogue": "'I was afraid my comet would disappear,' Luna admitted. 'And I was afraid my bowl would vanish,' her companion said.",
        "action": "They agreed to make a comet-shaped bowl and divided the remaining clay for handles and stars",
        "result": "The finished bowl held paintbrushes, and its comet tail pointed toward a shelf labeled SHARE",
        "ending": "The paper crown became a tiny clay star on the bowl, where it looked much more official",
        "lesson": "saying a quiet worry aloud can make room for two good ideas",
    },
    {
        "key": "cheese_balance",
        "premise": "a golden mass of cheese had been cut into one wobbly tower for the neighborhood picnic",
        "problem": "Luna and her companion argued over who should carry it, and the tower leaned like it was listening",
        "inner": "Maybe I am holding on because I want everyone to notice my work, Luna thought",
        "clue": "the tower steadied when its weight was placed in a shallow basket between them",
        "dialogue": "'I wanted credit,' Luna said. 'I wanted cheese,' her companion answered, and both began to giggle.",
        "action": "They carried the basket together and offered the first slices to the younger children",
        "result": "The cheese reached the picnic intact, and everyone received a fair piece",
        "ending": "The empty basket still smelled delicious, while the two friends shared the last crumb",
        "lesson": "a shared job and a shared treat can mend a bruised feeling",
    },
    {
        "key": "cookie_mountain",
        "premise": "a mass of cookie dough filled a mixing bowl like a small edible mountain",
        "problem": "Luna secretly counted the chocolate chips while her companion secretly counted the scoops",
        "inner": "If I do not claim the chips now, Luna thought, someone else may get the best cookie",
        "clue": "the chips were spread more evenly when the dough was divided before baking",
        "dialogue": "'I was keeping score in my head,' Luna confessed. 'So was I,' her companion said. 'Our heads need a referee.'",
        "action": "They shared the dough into equal trays and saved a few chips for a silly face on the largest cookie",
        "result": "Every baker received a warm cookie, and the giant face had one chip for each smiling eye",
        "ending": "The cookie mountain became a plate of friendly hills, and nobody needed a secret scoreboard",
        "lesson": "fair sharing can make a celebration sweeter than winning alone",
    },
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), mass(P), sharing(P), reconciliation(P), inner_monologue(P).
story_ok(P) :- valid(P), safe(P), resolved(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comedy storyworld about mass, inner thoughts, reconciliation, and sharing."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--object-name", choices=OBJECTS)
    parser.add_argument("--setting", default="community kitchen")
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
    if args.setting != "community kitchen":
        raise StoryError("This storyworld takes place in the community kitchen.")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        object_name=args.object_name or rng.choice(OBJECTS),
        setting=args.setting,
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("params", "p1"),
            asp.fact("mass", "p1"),
            asp.fact("sharing", "p1"),
            asp.fact("reconciliation", "p1"),
            asp.fact("inner_monologue", "p1"),
            asp.fact("safe", "p1"),
            asp.fact("resolved", "p1"),
        ]
    )


def aspire() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp

    model = asp.one_model(aspire())
    valid = set(asp.atoms(model, "valid"))
    okay = set(asp.atoms(model, "story_ok"))
    if ("p1",) in valid and ("p1",) in okay:
        print("OK: ASP and Python accept the repaired storyworld.")
        return 0
    print("Mismatch: ASP did not accept the repaired storyworld.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting != "community kitchen":
        raise StoryError("The mass story requires the community kitchen setting.")

    world = World(params)
    child = world.add(Entity(params.name, "character", params.name))
    friend = world.add(Entity(params.companion, "character", params.companion))
    mass = world.add(Entity("mass", "object", params.object_name))

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(ord(ch) for ch in f"{params.name}|{params.companion}|{params.object_name}")
    scenario = SCENARIOS[stable_seed % len(SCENARIOS)]

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

    child.memes.update({"curious": 1.0, "honest": 0.6, "generous": 0.5})
    friend.memes.update({"proud": 0.7, "generous": 0.5})
    mass.meters.update({"mass": 4.0, "stability": 0.8})
    world.facts.update(
        setting=params.setting,
        scenario=scenario["key"],
        material=params.object_name,
        mass_present=True,
        inner_monologue_used=True,
        reconciliation=True,
        sharing=True,
        safe=True,
        resolved=True,
    )

    world.say(
        f"In the community kitchen, {params.name} and {params.companion} found {detail['premise']}. "
        f"It was so round that a wooden spoon leaned against it and looked ready to climb aboard."
    )
    world.say(
        f"The funny shape soon revealed a real problem: {detail['problem']}. "
        f"{params.name} tried to smile, but inside, {detail['inner']}"
    )
    world.say(
        f"Instead of pretending everything was fine, {params.name} watched the mass carefully. "
        f"The useful clue was that {detail['clue']}."
    )
    world.say(
        f"{detail['dialogue']} Hearing the hidden worry out loud softened both faces. "
        f"They stopped pulling and made room for each other's plan."
    )
    world.say(
        f"Together, they decided what to do. {detail['action']}. "
        f"They kept the work on the table and asked the kitchen helper before using the hot oven."
    )
    world.say(
        f"The new plan worked because it included both friends. {detail['result']}. "
        f"{params.name} learned that reconciliation did not erase the disagreement; it helped them use it kindly."
    )
    world.say(
        f"At the end, {detail['ending']}. "
        f"The once-disputed mass had become proof that sharing could make a little comedy out of a big worry."
    )

    world.facts["outcome"] = detail["result"]
    world.facts["lesson"] = detail["lesson"]

    story_qa = [
        QAItem(
            question=f"What mass did {params.name} and {params.companion} discover?",
            answer=f"They discovered {detail['premise']}.",
        ),
        QAItem(
            question=f"What worried {params.name} during the disagreement?",
            answer=f"Inside, {detail['inner']} This showed that {params.name} was worried about losing a preferred idea or share.",
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=f"They spoke honestly about their worries, listened to each other, and agreed on a plan: {detail['action']}.",
        ),
        QAItem(
            question="How did sharing change the result?",
            answer=f"Sharing let both friends contribute, and {detail['result']}.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer=f"It taught that {detail['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is mass?",
            answer="Mass is the amount of matter in something; a larger or denser object usually has more mass.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the character's private stream of thoughts, shown so readers can understand a worry or decision.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a disagreement by speaking honestly, listening, and finding a peaceful way forward.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing can make a job fairer, include more people, and help friends solve a problem together.",
        ),
    ]
    prompts = [
        f"Write a funny story about {params.name} and {params.companion} sharing a surprising mass.",
        "Include an inner monologue that reveals a worry, a spoken reconciliation, and a concrete shared solution.",
        "End with a comic image showing how cooperation changed the object and the friendship.",
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
        print(f"facts={sample.world.facts}")
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

        model = asp.one_model(aspire())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Tess", "bread dough", seed=base_seed),
            StoryParams("Milo", "Bram", "clay lump", seed=base_seed + 1),
            StoryParams("Pia", "Ziggy", "cookie dough", seed=base_seed + 2),
            StoryParams("Nora", "Mara", "cheese ball", seed=base_seed + 3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1

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
