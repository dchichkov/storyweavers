#!/usr/bin/env python3
"""
A heartwarming parade story about a sailor, an infantry drummer, and a twist
that turns a missed celebration into a shared welcome.
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
    setting: str = "the harbor square"
    sailor: str = "Mara"
    infantry: str = "Jon"
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
    "the harbor square": {
        "tags": {"parade", "harbor", "community"},
        "mood": "bright with flags and sea wind",
    },
    "the lighthouse road": {
        "tags": {"parade", "coast", "lanterns"},
        "mood": "golden beneath the lighthouse beam",
    },
    "the riverside avenue": {
        "tags": {"parade", "river", "music"},
        "mood": "shimmering beside the water",
    },
}


@dataclass(frozen=True)
class ParadeArc:
    title: str
    premise: str
    problem: str
    twist: str
    action: str
    result: str
    ending: str
    problem_answer: str
    twist_answer: str
    result_answer: str


ARCS = [
    ParadeArc(
        title="The Parade That Turned Around",
        premise="The town had planned a grand parade to welcome a sailor home after a long voyage.",
        problem="When the drums began, the sailor was nowhere to be seen, and the infantry line marched toward an empty pier.",
        twist="Then the harbor bell rang from behind them: the sailor had arrived quietly by a small fishing boat and was leading the oldest dock workers toward the square.",
        action="The infantry stopped, turned their drums around, and joined the dock workers instead of pretending nothing had gone wrong.",
        result="The parade became a welcome for everyone who had kept the harbor alive, not just for one returning sailor.",
        ending="the sailor and the infantry drummer shared the first dance while flags fluttered above the smiling dock workers",
        problem_answer="The welcome parade could not find the returning sailor and marched toward an empty pier.",
        twist_answer="The sailor had already arrived in a small fishing boat and was bringing the oldest dock workers to the celebration.",
        result_answer="The infantry turned the parade around and welcomed the dock workers along with the sailor.",
    ),
    ParadeArc(
        title="The Quiet Drum",
        premise="An infantry drummer had practiced one shining rhythm for the sailor's homecoming parade.",
        problem="On the morning of the parade, the drumhead tore, and the drummer feared the whole celebration would fall silent.",
        twist="The sailor noticed that the drum's wooden shell still made a warm, gentle sound when tapped with a spoon.",
        action="She invited children, cooks, and boat builders to tap cups, pans, oars, and buckets in the same rhythm.",
        result="The broken drum became the beginning of a whole street of music.",
        ending="the repaired drum rested beside a row of kitchen pans, each still holding a little shining rhythm",
        problem_answer="The infantry drummer's drumhead tore just before the sailor's homecoming parade.",
        twist_answer="The sailor discovered that the drum's wooden shell could still make music with a spoon.",
        result_answer="Everyone added household sounds, turning the broken drum into a joyful street orchestra.",
    ),
    ParadeArc(
        title="The Flag at the Window",
        premise="A sailor returned on parade day, hoping to see the blue flag her little brother had promised to wave.",
        problem="The boy was sick in an upstairs room and could not reach the crowded street.",
        twist="Instead of passing his window, the parade quietly changed its route and climbed the hill toward his house.",
        action="The infantry carried their flags slowly, while the sailor stood below the window and told her brother about every place the sea had taken her.",
        result="The boy waved from his bed, and every neighbor learned that a parade could travel toward one person who needed it.",
        ending="a blue flag hung from the sickroom window, bright against the evening sky",
        problem_answer="The sailor's sick little brother could not come outside to see the parade or wave his blue flag.",
        twist_answer="The parade changed its route and went uphill to the boy's window.",
        result_answer="The boy got to join the celebration from bed, and the neighborhood made the parade personal and kind.",
    ),
    ParadeArc(
        title="The Extra Place",
        premise="The harbor prepared a parade supper for the sailor and the marching infantry.",
        problem="A storm delayed several families, leaving one long table with empty chairs and untouched bowls.",
        twist="The sailor remembered that the lighthouse keeper and night fishermen were still working beyond the breakwater.",
        action="She and the infantry carried the supper in covered baskets, following the lighthouse keeper's lantern through the rain.",
        result="The empty chairs became invitations, and the workers returned carrying warm bread for everyone.",
        ending="the parade table glowed with lanterns while wet coats hung around it like bright flags",
        problem_answer="A storm delayed families from the parade supper, leaving empty chairs and untouched bowls.",
        twist_answer="The sailor realized that lighthouse keepers and night fishermen were still working nearby.",
        result_answer="The sailor and infantry brought supper to the workers, who later joined the celebration with bread.",
    ),
    ParadeArc(
        title="The Sailor's Backward March",
        premise="The town asked a sailor and an infantry company to lead its proudest parade.",
        problem="The sailor kept walking backward because she wanted to watch the smallest children safely cross the street.",
        twist="The infantry captain first thought she had forgotten the route, but then saw that her backward steps made her the perfect guardian of the children.",
        action="The captain placed the drummer beside her and taught the whole company to slow the parade whenever a child needed help.",
        result="The march lost its hurry and gained many small companions.",
        ending="children marched between the sailor and the infantry, keeping time with tiny wooden spoons",
        problem_answer="The sailor walked backward during the parade, making the infantry think she had forgotten the route.",
        twist_answer="She was walking backward so she could watch and protect the smallest children.",
        result_answer="The infantry slowed down and made room for children to join the parade safely.",
    ),
    ParadeArc(
        title="The Bell Beneath the Banner",
        premise="A sailor carried a little brass bell from a faraway island at the front of the parade.",
        problem="The bell fell into a crack beneath the town's largest banner and could not be reached.",
        twist="An infantry scout heard the bell ringing below and realized the banner pole had marked an old rain tunnel.",
        action="The sailor lowered a rope while the infantry lifted the banner carefully, and neighbors passed the bell hand to hand.",
        result="The parade discovered a hidden spring under the square and used its clear water to fill every waiting cup.",
        ending="the brass bell hung beside the spring, ringing whenever a child took a drink",
        problem_answer="The sailor's island bell fell into a crack beneath the largest parade banner.",
        twist_answer="An infantry scout realized the crack led to an old rain tunnel and a hidden spring.",
        result_answer="The community rescued the bell and found clean water for everyone in the square.",
    ),
    ParadeArc(
        title="The Parade of Small Boats",
        premise="A sailor returned to a town where the parade had always been made for people on land.",
        problem="Many families who lived on houseboats could see the flags but could not reach the crowded avenue.",
        twist="The sailor tied bright ribbons to little boats and asked the infantry band to play from the riverbank.",
        action="Boat after boat joined the water beside the marching route, carrying lanterns, flowers, and waving children.",
        result="The parade became two parades, one on the road and one on the river, traveling together.",
        ending="lantern boats followed the marching infantry like a second string of stars",
        problem_answer="Houseboat families could see the parade but could not reach the crowded avenue.",
        twist_answer="The sailor created a water parade with ribboned boats and music from the riverbank.",
        result_answer="The road parade and river parade traveled together, including the houseboat families.",
    ),
    ParadeArc(
        title="The Missing Trumpet",
        premise="The infantry prepared a bright trumpet call for a sailor who had crossed three seas to come home.",
        problem="The trumpet vanished just before the parade, and the young musician felt certain she had ruined the day.",
        twist="The sailor found the trumpet tucked inside a market basket, where an old fruit seller had hidden it to keep it dry from a sudden shower.",
        action="The musician thanked the seller, then asked him to walk at the front and choose the first note.",
        result="The missing trumpet brought an old friend into the parade and gave the homecoming a new beginning.",
        ending="the fruit seller's first trumpet note floated over apples, uniforms, and the sailor's grateful smile",
        problem_answer="The infantry musician's trumpet disappeared before the sailor's homecoming parade.",
        twist_answer="The trumpet was safe in a fruit seller's basket, where he had hidden it from the rain.",
        result_answer="The musician invited the fruit seller to choose the first note, making him part of the parade.",
    ),
    ParadeArc(
        title="The Map in the Drumcase",
        premise="A sailor brought a map of distant waters to show the infantry children after the parade.",
        problem="The map was lost among the flags, and the sailor could remember the sea routes but not the names of the little islands.",
        twist="The infantry drummer opened an old drumcase and found that its lining was sewn from the sailor's missing map.",
        action="They carefully unfolded the cloth, then asked the children to draw the islands again from the sailor's stories.",
        result="The map became larger and more colorful than before, holding both memory and imagination.",
        ending="the new map covered the parade table while children pointed to islands they hoped to visit",
        problem_answer="The sailor lost her map and could not remember all the names of its small islands.",
        twist_answer="The map had been sewn into the lining of the infantry drummer's old drumcase.",
        result_answer="The sailor and children rebuilt the map together from stories and drawings.",
    ),
    ParadeArc(
        title="The Last Ribbon",
        premise="A sailor had one scarlet ribbon left for the parade's final flag.",
        problem="The infantry standard had torn, and every other ribbon had already been used.",
        twist="The sailor offered her own voyage ribbon, which had been tied to her coat since the day she left.",
        action="The infantry mended the standard with careful stitches, leaving one small scarlet piece visible as a reminder of the voyage.",
        result="The flag no longer showed only military pride; it carried the sailor's journey and the town's welcome.",
        ending="the scarlet patch shone on the flag as the sailor saluted the people who had waited",
        problem_answer="The infantry standard tore when the parade had no ribbon left to repair it.",
        twist_answer="The sailor offered the scarlet ribbon she had worn throughout her voyage.",
        result_answer="The infantry repaired the flag with the sailor's ribbon, giving it a shared story.",
    ),
]


OPENINGS = [
    "On the morning of the parade, sea wind carried music through {setting}.",
    "Everyone in {setting} knew the parade was coming because the flags began dancing before the drums.",
    "When the sailor returned, the people of {setting} polished the streets and hung bright ribbons from every window.",
    "The infantry gathered beneath the morning sun while {sailor} watched the harbor for a familiar shore.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.sailor, params.infantry))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _lower(text: str) -> str:
    return text[:1].lower() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: ParadeArc = f["arc"]
    opening = _fill(OPENINGS[f["opening_variant"]], f)
    premise = _fill(arc.premise, f)
    problem = _fill(arc.problem, f)
    twist = _fill(arc.twist, f)
    action = _fill(arc.action, f)
    result = _fill(arc.result, f)
    ending = _fill(arc.ending, f)
    sailor = f["sailor"]
    infantry = f["infantry"]

    structures = [
        [
            f"{opening} This is the story of \"{arc.title}.\"",
            f"{premise} {problem}",
            f"\"We can still make this a welcome,\" said {sailor}. The {infantry} listened.",
            twist,
            action,
            f"{result} \"A parade is not just a path,\" said the infantry drummer. \"It is a way to make room.\"",
            f"At sunset, {ending}.",
        ],
        [
            opening,
            f"\"Where should we go?\" asked the infantry drummer. {premise}",
            _cap(problem),
            f"{sailor} looked toward the flags. \"Then let us notice what the day is asking for.\" {twist}",
            f"The sailor and the infantry worked together. {_cap(_lower(action))}",
            f"The surprise changed everything: {_lower(result)}",
            f"That evening, {ending}. The town remembered the parade as a lesson in welcome.",
        ],
        [
            f"The old people of {f['setting']} still tell \"{arc.title}\" when flags appear.",
            f"They begin with this: {opening}",
            f"The celebration seemed ready, but {problem[0].lower() + problem[1:]}",
            f"\"We do not have to hide the mistake,\" said {sailor}. \"We can follow it.\" {twist}",
            f"{_cap(_lower(action))} The music grew softer, then warmer.",
            f"{_cap(_lower(result))}",
            f"Long after the last drumbeat, {ending}.",
        ],
        [
            f"{opening} Yet the parade did not unfold as planned.",
            f"{_cap(problem)}",
            f"The infantry drummer lowered the instrument. \"Should we turn back?\" he asked.",
            f"\"We should look again,\" answered {sailor}. {twist}",
            action,
            f"{result} Even the people who had been waiting quietly began to smile.",
            f"The final picture was simple: {ending}.",
        ],
        [
            f"Before the parade, {sailor} told the infantry, \"A welcome belongs to the person who needs it most.\"",
            f"The words mattered because {premise[0].lower() + premise[1:]}",
            f"Then trouble came. {problem}",
            f"\"Listen,\" said {sailor}. {twist}",
            action,
            f"{result} The drummer answered, \"Then this is the right parade after all.\"",
            f"Under the evening stars, {ending}.",
        ],
    ]
    return structures[f["structure_variant"]]


ASP_RULES = r"""
setting(harbor_square).
setting(lighthouse_road).
setting(riverside_avenue).

feature(parade).
feature(sailor).
feature(infantry).
feature(twist).
style(heartwarming).

can_tell_story(S) :-
    setting(S),
    feature(parade),
    feature(sailor),
    feature(infantry),
    feature(twist),
    style(heartwarming).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    for feature in ("parade", "sailor", "infantry", "twist"):
        lines.append(asp.fact("feature", feature))
    lines.append(asp.fact("style", "heartwarming"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade story about a sailor and infantry."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--sailor")
    parser.add_argument("--infantry")
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
    sailor = args.sailor or rng.choice(["Mara", "Nell", "Pia", "Sana", "Tess"])
    infantry = args.infantry or rng.choice(["the infantry drummer", "the infantry scout", "the infantry captain"])
    if sailor.lower() == infantry.lower():
        raise StoryError("The sailor and infantry companion must be different characters.")
    if not sailor.strip():
        raise StoryError("The sailor's name cannot be empty.")
    if not infantry.strip():
        raise StoryError("The infantry role cannot be empty.")
    return StoryParams(setting=setting, sailor=sailor, infantry=infantry)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if not params.sailor.strip():
        raise StoryError("The sailor's name cannot be empty.")
    if not params.infantry.strip():
        raise StoryError("The infantry role cannot be empty.")
    if params.sailor.lower() == params.infantry.lower():
        raise StoryError("The sailor and infantry companion must be different characters.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    sailor = world.add(
        Entity(
            name=params.sailor,
            kind="sailor",
            meters={"distance_traveled": 1.0, "belonging": 0.45},
            memes={"courage": 0.9, "care": 0.9},
        )
    )
    infantry = world.add(
        Entity(
            name=params.infantry,
            kind="infantry",
            meters={"marching_strength": 0.9, "rhythm": 0.8},
            memes={"duty": 0.9, "welcome": 0.55},
        )
    )
    world.add(
        Entity(
            name="the parade",
            kind="celebration",
            meters={"route_progress": 0.2, "shared_joy": 0.45},
            memes={"welcome": 0.7, "surprise": 0.8},
        )
    )
    world.add(
        Entity(
            name="the harbor bell",
            kind="signal",
            meters={"sound": 0.7},
            memes={"memory": 0.8},
        )
    )

    sailor.meters["belonging"] = 1.0
    infantry.meters["marching_strength"] = 1.0
    world.facts.update(
        sailor=sailor.name,
        infantry=infantry.name,
        setting=params.setting,
        arc=arc,
        opening_variant=(seed // len(ARCS)) % len(OPENINGS),
        structure_variant=(seed // (len(ARCS) * len(OPENINGS))) % 5,
        problem=_fill(
            arc.problem,
            {"sailor": sailor.name, "infantry": infantry.name, "setting": params.setting},
        ),
        twist=_fill(
            arc.twist,
            {"sailor": sailor.name, "infantry": infantry.name, "setting": params.setting},
        ),
        causal_action=_fill(
            arc.action,
            {"sailor": sailor.name, "infantry": infantry.name, "setting": params.setting},
        ),
        resolution=_fill(
            arc.result,
            {"sailor": sailor.name, "infantry": infantry.name, "setting": params.setting},
        ),
        ending_image=_fill(
            arc.ending,
            {"sailor": sailor.name, "infantry": infantry.name, "setting": params.setting},
        ),
        theme="parade, sailor, infantry, twist, and heartwarming welcome",
    )

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a heartwarming parade story about sailor {params.sailor} and {params.infantry} in {params.setting}.",
        "Include a gentle twist that changes what the parade is really for.",
        "Show how a sailor and infantry companion turn a problem into a welcome for someone else.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.sailor} and {params.infantry} face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="What twist changed the meaning or direction of the parade?",
            answer=arc.twist_answer,
        ),
        QAItem(
            question=f"What changed because {params.sailor} and the infantry acted together?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What final image closes \"{arc.title}\"?",
            answer=f"The story ends with {world.facts['ending_image']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people walk, play music, and celebrate together."
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or travels by ship, caring for the vessel and helping it move safely."
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move on foot."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change that makes earlier events look different or sends the story in a new direction."
        ),
        QAItem(
            question="What makes a story heartwarming?",
            answer="A heartwarming story shows care, hope, or generosity bringing people closer."
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
        print()
        print("== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(setting.replace("the ", "").replace(" ", "_") for setting in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tell_story/1."))
    return sorted(set(asp.atoms(model, "can_tell_story")))


def asp_verify() -> int:
    py = {(setting,) for setting in _valid_python()}
    clingo_result = set(_asp_valid())
    if py != clingo_result:
        print("MISMATCH between clingo and python:")
        print("python only:", sorted(py - clingo_result))
        print("clingo only:", sorted(clingo_result - py))
        return 1

    for index, setting in enumerate(SETTING_REGISTRY):
        sample = generate(
            StoryParams(
                setting=setting,
                sailor="Mara",
                infantry="the infantry drummer",
                seed=index,
            )
        )
        if not sample.story.strip() or "parade" not in sample.story.lower():
            print("Generation check failed.")
            return 1

    print(f"OK: clingo gate matches python ({len(py)} settings); generation checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tell_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(SETTING_REGISTRY):
            samples.append(
                generate(
                    StoryParams(
                        setting=setting,
                        sailor="Mara",
                        infantry="the infantry drummer",
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
