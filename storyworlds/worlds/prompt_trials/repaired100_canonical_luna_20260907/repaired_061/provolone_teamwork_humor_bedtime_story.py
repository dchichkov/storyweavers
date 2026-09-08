#!/usr/bin/env python3
"""
A gentle bedtime storyworld about teamwork, humor, and a sleepy slice of provolone.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, REPO_ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Luna"
    helper: str = "Milo"
    setting: str = "the moonlit kitchen"
    snack: str = "provolone"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.teamwork = False
        self.humor = False
        self.resolved = False

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


EPISODES = [
    {
        "opening": "The kitchen clock had just whispered midnight when Luna heard a tiny squeak beneath the pantry shelf.",
        "problem": "A round piece of provolone had rolled into the narrowest corner, where even a spoon could not reach.",
        "plan": "Luna held a wooden ruler while Milo nudged it with a clean straw.",
        "joke": "Milo puffed his cheeks and said, “If the cheese rolls away again, I shall politely chase it in my sleep.”",
        "turn": "The provolone slid out at last, but it carried a lost blue button tucked beneath it.",
        "ending": "They placed the button beside the coat, shared the provolone, and dreamed of wheels that rolled only where they were invited.",
    },
    {
        "opening": "Moonlight made silver squares on the kitchen floor while Luna prepared a bedtime snack.",
        "problem": "The last slice of provolone had slipped behind a basket and was balanced on a wobbling jar.",
        "plan": "Luna steadied the basket, and Milo made a soft bridge from folded napkins.",
        "joke": "Milo whispered, “This is the fanciest cheese bridge in the whole sleepy kingdom.”",
        "turn": "When the slice crossed the bridge, it revealed a tiny silver bell hidden under the jar.",
        "ending": "They rang the bell once, ate the provolone, and let the quiet kitchen settle back into its dreams.",
    },
    {
        "opening": "Before bedtime, Luna noticed a golden smell drifting from the pantry.",
        "problem": "A packet of provolone had slid behind a stack of bowls, and the stack leaned like a tired tower.",
        "plan": "Luna counted the bowls while Milo gently pulled the packet with a ribbon.",
        "joke": "Milo bowed to the tower and said, “Please do not fall. I am wearing my brave pajamas.”",
        "turn": "The bowls stayed safe, and the ribbon also drew out a little paper star.",
        "ending": "They put the star by the window, shared the provolone, and tucked the brave pajamas into bed.",
    },
]


def build_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different characters")
    if params.snack != "provolone":
        raise StoryError("this bedtime story domain only supports provolone")
    world = World(params)
    hero = world.add(
        Entity(
            id="luna",
            kind="character",
            type="child",
            label=params.hero,
            meters={"sleepiness": 0.35},
            memes={"curiosity": 0.8, "kindness": 0.7},
        )
    )
    helper = world.add(
        Entity(
            id="milo",
            kind="character",
            type="mouse",
            label=params.helper,
            meters={"sleepiness": 0.3},
            memes={"playfulness": 0.9, "teamwork": 0.8},
        )
    )
    snack = world.add(
        Entity(
            id="provolone",
            kind="food",
            type="cheese",
            label="provolone",
            meters={"safely_reachable": 0.0},
            memes={"comfort": 0.8},
        )
    )
    episode_index = (params.seed or 0) % len(EPISODES)
    world.facts.update(
        hero=hero,
        helper=helper,
        snack=snack,
        episode=EPISODES[episode_index],
        episode_index=episode_index,
    )
    return world


def narrate(world: World) -> None:
    p = world.params
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    snack: Entity = world.facts["snack"]  # type: ignore[assignment]
    episode: dict[str, str] = world.facts["episode"]  # type: ignore[assignment]

    world.say(
        f"{episode['opening']} {hero.label}, a gentle child, blinked at the pantry. "
        f"{helper.label}, a small mouse with very large slippers, peeked around the flour tin."
    )
    world.say(
        f'"Did you hear that?" asked {hero.label}. '
        f'"I heard cheese trouble," said {helper.label}. "It is my most important kind of trouble."'
    )

    world.para()
    world.say(episode["problem"])
    world.say(
        f"{hero.label} reached once, but the corner was too tight. "
        f"{helper.label} reached twice, but his slippers squeaked and tickled the dust."
    )
    world.say(
        f'"We need both of us," said {hero.label}. '
        f'"Excellent," said {helper.label}. "I brought two paws and one excellent idea."'
    )

    world.para()
    world.teamwork = True
    hero.memes["teamwork"] = 1.0
    helper.memes["teamwork"] = 1.0
    world.say(episode["plan"])
    world.say(episode["joke"])
    world.humor = True
    hero.memes["joy"] = 0.8
    helper.memes["joy"] = 1.0
    world.say(
        f"They moved slowly, listened carefully, and changed their plan when the basket wobbled. "
        f"At last, the {snack.label} began to slide."
    )

    world.para()
    world.say(episode["turn"])
    world.say(
        f'"We found more than supper," said {hero.label}. '
        f'"And less than a dragon," said {helper.label}. "That is a very manageable adventure."'
    )
    world.resolved = True
    snack.meters["safely_reachable"] = 1.0
    hero.meters["sleepiness"] = 0.85
    helper.meters["sleepiness"] = 0.8
    world.say(episode["ending"])
    world.say(
        f"Under the soft moonlight, {hero.label} and {helper.label} closed their eyes, "
        f"grateful that teamwork had made the small mystery gentle enough for bedtime."
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle bedtime story about {p.hero} and {p.helper} solving a small problem with teamwork and humor.",
        f"Tell a cozy story set in {p.setting} where friends rescue a piece of {p.snack}.",
        "Create a sleepy children's story in which a funny line helps friends cooperate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    episode: dict[str, str] = world.facts["episode"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who worked together in the story?",
            answer=f"{p.hero} and {p.helper} worked together in {p.setting}.",
        ),
        QAItem(
            question=f"What problem did {p.hero} and {p.helper} face?",
            answer=f"{episode['problem']} They needed to reach the provolone safely.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They combined their efforts: {episode['plan']} Their careful teamwork brought the provolone out.",
        ),
        QAItem(
            question="What made the story humorous?",
            answer=f"{p.helper} joked, “{episode['joke'].split('“', 1)[-1].rstrip('”')}” The funny words made the difficult task feel cheerful.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{episode['ending']} The friends then went peacefully to sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people cooperate and combine their efforts to reach a shared goal.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something amusing that can make people smile or laugh.",
        ),
        QAItem(
            question="What is provolone?",
            answer="Provolone is a mild cheese that can be sliced and shared as a snack.",
        ),
        QAItem(
            question="Why are gentle bedtime stories comforting?",
            answer="Gentle bedtime stories use safe problems, caring friends, and peaceful endings to help listeners relax.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(
        f"episode={world.facts['episode_index']} teamwork={world.teamwork} "
        f"humor={world.humor} resolved={world.resolved}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
character(luna).
character(milo).
food(provolone).
goal(reach_provolone).
teamwork :- character(luna), character(milo), goal(reach_provolone).
humor :- teamwork.
resolved :- teamwork, humor.
good_bedtime_story :- resolved.
#show teamwork/0.
#show humor/0.
#show resolved/0.
#show good_bedtime_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("character", "luna"),
            asp.fact("character", "milo"),
            asp.fact("food", "provolone"),
            asp.fact("goal", "reach_provolone"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    python_world = generate(StoryParams(seed=0)).world
    assert python_world is not None
    expected = {"teamwork", "humor", "resolved", "good_bedtime_story"}
    if expected.issubset(names) and python_world.teamwork and python_world.humor and python_world.resolved:
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cozy provolone bedtime storyworld about teamwork and humor."
    )
    parser.add_argument("--hero", choices=["Luna", "Nora", "Pip"])
    parser.add_argument("--helper", choices=["Milo", "Toby", "Pip"])
    parser.add_argument("--setting", default=None)
    parser.add_argument("--snack", choices=["provolone"])
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


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: int
) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nora", "Pip"])
    helpers = [name for name in ["Milo", "Toby", "Pip"] if name != hero]
    helper = args.helper or rng.choice(helpers)
    if helper == hero:
        raise StoryError("hero and helper must be different characters")
    return StoryParams(
        hero=hero,
        helper=helper,
        setting=args.setting or "the moonlit kitchen",
        snack=args.snack or "provolone",
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show teamwork/0.\n#show humor/0.\n#show resolved/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program("#show good_bedtime_story/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            ("Luna", "Milo", "the moonlit kitchen"),
            ("Nora", "Toby", "the quiet breakfast room"),
            ("Pip", "Milo", "the little pantry"),
        ]
        for index, (hero, helper, setting) in enumerate(presets):
            samples.append(
                generate(
                    StoryParams(
                        hero=hero,
                        helper=helper,
                        setting=setting,
                        snack="provolone",
                        seed=base_seed + index,
                    )
                )
            )
    else:
        for index in range(max(1, args.n)):
            sample_seed = base_seed + index
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            samples.append(generate(params))

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
