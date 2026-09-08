#!/usr/bin/env python3
"""
A folk tale about Ole, an exorbitant bargain, and the quiet wisdom inside one
small heart.
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
    setting: str = "the hill village"
    hero: str = "Ole"
    companion: str = "Mara"
    merchant: str = "the old peddler"
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
    "the hill village": {"mood": "sunny and wind-washed", "tags": {"village", "market"}},
    "the reed marsh": {"mood": "misty and whispering", "tags": {"marsh", "market"}},
    "the pine road": {"mood": "green and shadowed", "tags": {"forest", "road"}},
}


@dataclass(frozen=True)
class TaleArc:
    title: str
    premise: str
    problem: str
    bargain: str
    action: str
    result: str
    ending: str
    problem_answer: str
    bargain_answer: str
    result_answer: str


ARCS = [
    TaleArc(
        title="Ole and the Exorbitant Bell",
        premise="In {setting}, Ole found a little silver bell beneath a hawthorn tree.",
        problem="The bell belonged to a frightened foal, but the {merchant} demanded an exorbitant price before he would reveal where its mother had gone.",
        bargain="Ole thought, \"If I spend every coin, the bell will be mine, but the foal will still be lost.\"",
        action="He asked the villagers for help instead, and each person offered one useful thing: a lantern, a length of rope, or a handful of oats.",
        result="Together they followed the bell's clear ringing and found the mare caught behind a fallen gate.",
        ending="Ole hung the bell beside the village well, where its gentle sound called neighbors to help one another.",
        problem_answer="A foal was separated from its mother, while a merchant demanded an exorbitant price for the bell that could guide them.",
        bargain_answer="Ole refused to spend all his money and asked the villagers to share their different kinds of help.",
        result_answer="The villagers' combined help led them to the mare, who was freed from behind a fallen gate.",
    ),
    TaleArc(
        title="The Exorbitant Loaf",
        premise="Every baker in {setting} baked bread for the harvest feast except a proud stranger with one golden loaf.",
        problem="The stranger set an exorbitant price on the loaf, although the poorest children had brought no coins at all.",
        bargain="Ole thought, \"A feast that shuts out hungry children is no feast at all.\"",
        action="He offered his own basket of apples and invited every family to add whatever food it could spare.",
        result="The golden loaf was sliced thinly, but the shared table became so generous that nobody went hungry.",
        ending="the stranger learned that one loaf can taste larger when many hands pass it kindly.",
        problem_answer="A stranger charged an exorbitant price for the only golden loaf, leaving poor children unable to join the feast.",
        bargain_answer="Ole chose to share his apples and invite every family to contribute food instead of accepting an unfair price.",
        result_answer="The village shared the loaf and many other foods, so every child received a full meal.",
    ),
    TaleArc(
        title="Ole's Quiet Purse",
        premise="A talking purse appeared on the road through {setting}, promising riches to anyone brave enough to open it.",
        problem="The purse demanded an exorbitant promise: its owner must keep every coin and never help a neighbor.",
        bargain="Ole thought, \"A purse that makes my heart smaller is too costly, even if it is full.\"",
        action="He carried the purse to the village elder and asked whether a treasure could be measured by what it helped people do.",
        result="The purse opened only when Ole placed it beside the common grain chest, and its coins became seeds for every field.",
        ending="green shoots rose around the chest, while Ole's empty hands were warm from planting.",
        problem_answer="The talking purse offered riches only in exchange for a selfish and exorbitant promise never to help anyone.",
        bargain_answer="Ole rejected the purse's cruel condition and brought it to the elder to seek a fairer use for its treasure.",
        result_answer="The purse opened for the common good and changed its coins into seeds for every village field.",
    ),
    TaleArc(
        title="The Peddler's Exorbitant Shadow",
        premise="A traveling peddler sold bright cloth shadows in {setting}, claiming they could protect people from every sorrow.",
        problem="His exorbitant price left a lonely child without shade, though the child had only a torn blue scarf.",
        bargain="Ole thought, \"A shadow is meant to shelter someone, not to make someone poorer.\"",
        action="He stretched the scarf between two sticks and asked the child to decorate it with leaves and painted stars.",
        result="The little shelter became a meeting place, and soon the whole village brought scraps to make it wider.",
        ending="the peddler's costly shadows hung unused while the villagers' patched canopy danced in the breeze.",
        problem_answer="A peddler charged an exorbitant price for protective shadows, leaving a lonely child without shelter.",
        bargain_answer="Ole made a shelter from the child's scarf and invited the villagers to improve it with shared scraps.",
        result_answer="The shared canopy grew wide enough for the village and became more useful than the peddler's costly shadows.",
    ),
]


OPENINGS = [
    "In the old days, when roads were narrow and promises were wide, {hero} lived near {setting}.",
    "Long ago, the people of {setting} knew a young traveler named {hero}, whose coat had more patches than pockets.",
    "There was once, beside {setting}, a humble soul called {hero}, who listened carefully before taking a step.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.companion, params.merchant))
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _start(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    facts = world.facts
    arc: TaleArc = facts["arc"]
    opening = _fill(OPENINGS[facts["opening_variant"]], facts)
    premise = _fill(arc.premise, facts)
    problem = _fill(arc.problem, facts)
    bargain = _fill(arc.bargain, facts)
    action = _fill(arc.action, facts)
    result = _fill(arc.result, facts)
    ending = _fill(arc.ending, facts)
    hero = facts["hero"]
    companion = facts["companion"]
    merchant = facts["merchant"]

    structures = [
        [
            opening,
            f"{premise} {problem}",
            f"{companion} asked, \"What will you do, {hero}?\" {bargain}",
            action,
            f"{merchant.capitalize()} watched from the roadside. {result}",
            f"From that day onward, {ending}",
        ],
        [
            f"The tale is called \"{arc.title}.\" {opening}",
            f"At first, {problem}",
            f"\"That price is exorbitant,\" said {companion}. {bargain}",
            f"{hero} spoke aloud at last: \"Let us find a way that leaves nobody behind.\" {action}",
            result,
            f"So the old folk still say that {ending}",
        ],
        [
            opening,
            premise,
            f"Then trouble came. {problem}",
            f"{companion} whispered, \"Must you pay so much?\" {hero} answered, \"No. I must choose wisely.\" {bargain}",
            action,
            f"The choice changed everything. {result} In the evening, {ending}",
        ],
        [
            f"Whenever the elders tell \"{arc.title},\" they begin with {hero} walking through {facts['setting']}.",
            f"That was where {premise[0].lower() + premise[1:]} Soon, {problem[0].lower() + problem[1:]}",
            f"{hero} fell silent. Inside, {bargain}",
            f"Then {hero} turned to {companion} and said, \"We can make a better bargain.\" {action}",
            f"{result}",
            f"And the proof of the lesson remained: {ending}",
        ],
    ]
    return structures[facts["structure_variant"]]


ASP_RULES = r"""
setting(hill_village).
setting(reed_marsh).
setting(pine_road).
virtue(kindness).
virtue(wisdom).
can_tell_tale(S) :- setting(S), virtue(kindness), virtue(wisdom).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.extend([asp.fact("virtue", "kindness"), asp.fact("virtue", "wisdom")])
    return "\n".join(lines)


def asp_program(show: str = "#show can_tell_tale/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale about Ole and an exorbitant bargain."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--merchant")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Ole", "Nils", "Tora", "Edda"])
    companion = args.companion or rng.choice(["Mara", "Birk", "Anja", "Sven"])
    merchant = args.merchant or rng.choice(
        ["the old peddler", "the bridge merchant", "the velvet seller"]
    )
    if hero == companion:
        raise StoryError("The hero and companion must have different names.")
    if not hero.strip() or not companion.strip():
        raise StoryError("Character names must not be empty.")
    return StoryParams(
        setting=setting,
        hero=hero,
        companion=companion,
        merchant=merchant,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero == params.companion:
        raise StoryError("The hero and companion must be different characters.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            name=params.hero,
            kind="traveler",
            meters={"coins": 3.0, "energy": 1.0},
            memes={"wisdom": 1.0, "kindness": 1.0},
        )
    )
    companion = world.add(
        Entity(
            name=params.companion,
            kind="helper",
            meters={"energy": 1.0},
            memes={"care": 1.0},
        )
    )
    merchant = world.add(
        Entity(
            name=params.merchant,
            kind="merchant",
            meters={"goods": 1.0},
            memes={"greed": 1.0},
        )
    )
    world.add(
        Entity(
            name="the exorbitant bargain",
            kind="choice",
            meters={"cost": 10.0},
            memes={"unfairness": 1.0},
        )
    )
    world.add(
        Entity(
            name="the village commons",
            kind="place",
            meters={"help": 0.0},
            memes={"belonging": 1.0},
        )
    )

    facts = {
        "hero": hero.name,
        "companion": companion.name,
        "merchant": merchant.name,
        "setting": params.setting,
        "arc": arc,
        "opening_variant": (seed // len(ARCS)) % len(OPENINGS),
        "structure_variant": (seed // (len(ARCS) * len(OPENINGS))) % 4,
    }
    facts["problem"] = _fill(arc.problem, facts)
    facts["inner_choice"] = _fill(arc.bargain, facts)
    facts["action"] = _fill(arc.action, facts)
    facts["result"] = _fill(arc.result, facts)
    facts["ending"] = _fill(arc.ending, facts)
    world.facts.update(facts)

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a folk tale about {params.hero} facing an exorbitant bargain in {params.setting}.",
        "Use an inner monologue to show a kind character choosing wisdom over greed.",
        "Write a child-facing folk tale with a spoken exchange and a changed ending image.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question=f"What did {params.hero} decide when the bargain became exorbitant?",
            answer=arc.bargain_answer,
        ),
        QAItem(
            question=f"How did {params.hero}'s choice change the situation?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What final image proves that the tale has changed?",
            answer=f"The ending shows that {facts['ending']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does exorbitant mean?",
            answer="Exorbitant means far more costly or excessive than is fair or reasonable."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thought a character has inside their mind."
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a traditional-style story often told to share a lesson about life."
        ),
        QAItem(
            question="Why can a fair bargain matter?",
            answer="A fair bargain matters because each person should receive reasonable value without being tricked or harmed."
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


def _python_valid_settings() -> list[str]:
    return sorted(setting.replace("the ", "").replace(" ", "_") for setting in SETTING_REGISTRY)


def _asp_valid_settings() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "can_tell_tale")))


def asp_verify() -> int:
    python_values = {(setting,) for setting in _python_valid_settings()}
    asp_values = set(_asp_valid_settings())
    if python_values != asp_values:
        print("MISMATCH between clingo and python:")
        print("python only:", sorted(python_values - asp_values))
        print("clingo only:", sorted(asp_values - python_values))
        return 1

    for index, setting in enumerate(SETTING_REGISTRY):
        sample = generate(
            StoryParams(
                setting=setting,
                hero="Ole",
                companion="Mara",
                merchant="the old peddler",
                seed=index,
            )
        )
        if not sample.story or "Ole" not in sample.story:
            print("MISMATCH: generated story exercise failed.")
            return 1

    print(f"OK: clingo gate matches python ({len(python_values)} settings).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for setting in _asp_valid_settings():
            print(setting[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        hero="Ole",
                        companion="Mara",
                        merchant="the old peddler",
                        seed=base_seed + len(samples),
                    )
                )
            )
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 100):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
