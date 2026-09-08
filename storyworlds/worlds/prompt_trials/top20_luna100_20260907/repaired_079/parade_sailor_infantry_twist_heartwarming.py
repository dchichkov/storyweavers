#!/usr/bin/env python3
"""
A heartwarming storyworld about a parade, a sailor, and an infantry band
whose surprising twist changes what everyone thinks a parade is for.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sailor_girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "sailor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    sailor_name: str = "Mara"
    sailor_type: str = "sailor_girl"
    infantry_name: str = "Jonah"
    infantry_type: str = "boy"
    parade_name: str = "the Harbor Lights Parade"


NAMES = ["Mara", "Jonah", "Lina", "Owen", "Pia", "Sam", "Tessa", "Ravi"]
PARADES = [
    "the Harbor Lights Parade",
    "the Lantern Parade",
    "the Spring Drum Parade",
    "the Little Victory Parade",
]

SCENES = [
    {
        "street": "a bright harbor street",
        "weather": "a soft rain",
        "problem": "the parade route had become too slippery for the heavy marching drums",
        "mistake": "the infantry line kept marching toward the grandstand because everyone believed the crowd was waiting there",
        "clue": "a small paper boat floating along the curb",
        "twist": "the sailor realized the parade was meant to bring music to the people who could not reach the grandstand",
        "action": "turned the parade toward the quiet care home beside the harbor",
        "ending": "the residents lifted their hands to the windows and tapped along with spoons",
        "lesson": "A parade is not measured by how far it travels, but by whom it reaches",
    },
    {
        "street": "a town square lined with blue ribbons",
        "weather": "a warm wind",
        "problem": "the flag ropes tangled around a statue before the parade could begin",
        "mistake": "the infantry marched past the trouble while the crowd waited for someone else to help",
        "clue": "the sailor's old knot book tucked inside a canvas pocket",
        "twist": "the sailor discovered that the parade's finest first step was stopping to help the square keeper",
        "action": "freed the ropes and invited the keeper to lead the first turn",
        "ending": "the ribbons streamed above the march as the keeper laughed at the front",
        "lesson": "The best celebration makes room for the people who hold a place together",
    },
    {
        "street": "a hill road overlooking the sea",
        "weather": "a clear golden morning",
        "problem": "the youngest drummer lost the beat whenever the road climbed steeply",
        "mistake": "the infantry tried to march faster, hoping the hill would end sooner",
        "clue": "the sailor noticed the drummer watching the lighthouse flashes",
        "twist": "the sailor changed the march into a slow lighthouse rhythm so the child could lead it",
        "action": "matched every drumbeat to a patient flash from the lighthouse",
        "ending": "even the tired soldiers smiled as the smallest drummer guided them to the top",
        "lesson": "A strong group changes its pace so everyone can belong",
    },
    {
        "street": "a narrow lane between flower stalls",
        "weather": "a cloudless afternoon",
        "problem": "the parade's bright banner snagged on a low balcony",
        "mistake": "the infantry pulled harder and nearly tore the banner in two",
        "clue": "the sailor heard a child calling from the balcony above",
        "twist": "the child was the banner maker, and the sailor asked her how the cloth wanted to be freed",
        "action": "lowered the pole, listened to the child, and gently unwound the cloth",
        "ending": "the maker walked beside the banner, holding its corner proudly",
        "lesson": "Careful listening can save what hurried strength might break",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    sailor = world.add(Entity(params.sailor_name, "character", params.sailor_type, params.sailor_name))
    infantry = world.add(Entity(params.infantry_name, "character", params.infantry_type, params.infantry_name))
    parade = world.add(Entity("parade", "thing", "parade", params.parade_name))
    drum = world.add(Entity("drum", "thing", "drum", "the marching drum"))
    banner = world.add(Entity("banner", "thing", "banner", "the parade banner"))

    sailor.meters.update(seamanship=1.0, patience=1.0)
    sailor.memes["belonging"] = 0.0
    infantry.meters["marching"] = 1.0
    infantry.memes["worry"] = 0.0
    parade.meters.update(joy=1.0, reach=0.0)
    drum.meters["rhythm"] = 1.0
    banner.meters["brightness"] = 1.0

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        parade=parade,
        drum=drum,
        banner=banner,
    )


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.sailor_name}|{params.infantry_name}|{params.parade_name}"
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    scene = SCENES[_token(params) % len(SCENES)]
    sailor = world.facts["sailor"]
    infantry = world.facts["infantry"]
    parade = world.facts["parade"]
    banner = world.facts["banner"]

    world.say(
        f"{sailor.label}, a sailor who knew how to read wind and water, marched beside "
        f"{infantry.label}, a young member of the infantry, in {parade.label}."
    )
    world.say(
        f"They traveled down {scene['street']} under {scene['weather']}, while drums beat "
        "and neighbors waved from doorways."
    )
    world.say(f"But {scene['problem'].capitalize()}.")

    world.para()
    world.say(f"At first, {scene['mistake']}.")
    world.say(
        f'"Should we keep going?" {infantry.label} asked. '
        f'"A parade should reach its grand ending."'
    )
    world.say(
        f'"Not before we understand what the street is telling us," {sailor.label} replied. '
        "The sailor watched the people instead of only watching the route."
    )
    world.say(
        f"Then {sailor.label} noticed {scene['clue']}. That small sign made the sailor stop and look again."
    )

    world.para()
    world.say(f"The twist was this: {scene['twist'].capitalize()}.")
    world.say(
        f'"Then the parade can come to them," {sailor.label} said. '
        f'"Will you help me change the plan?"'
    )
    world.say(
        f'"Yes," {infantry.label} answered. "A careful turn is still a brave march."'
    )
    world.say(f"Together, they {scene['action']}.")
    world.say(
        f"The infantry lowered its polished instruments, and {sailor.label} guided the group "
        "through the safest part of the street."
    )

    world.para()
    world.say(f"The new plan worked: {scene['ending']}.")
    world.say(
        f"{infantry.label} saw that the parade had not become smaller. It had become kinder, "
        "because the music had found listeners who needed it."
    )
    world.say(
        f'"I thought the parade was going to one special place," {infantry.label} said.'
    )
    world.say(
        f'"Today it found many special people," {sailor.label} replied.'
    )
    world.say(
        f"{scene['lesson']}. As the last drumbeat faded, {parade.label} left a bright trail "
        "of smiles behind it."
    )

    sailor.memes["belonging"] = 1.0
    infantry.memes["worry"] = 0.0
    parade.meters["reach"] = 1.0
    world.fired.update({
        ("noticed_clue", scene["clue"]),
        ("changed_route", scene["action"]),
        ("reached_people", scene["ending"]),
    })
    world.facts.update(
        params=params,
        scene=scene,
        scene_index=_token(params) % len(SCENES),
        twist=True,
        resolved=True,
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    scene = world.facts["scene"]
    return [
        f"Write a heartwarming story about {params.sailor_name}, a sailor, and {params.infantry_name}, an infantry marcher, in {params.parade_name}.",
        f"Include this parade problem: {scene['problem']}. Let a clue create a surprising twist.",
        "End with a spoken exchange and a gentle image showing that the parade reached people who needed it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    scene = world.facts["scene"]
    return [
        QAItem(
            question=f"Who marched in {params.parade_name}?",
            answer=f"{params.sailor_name}, a sailor, marched beside {params.infantry_name}, a young member of the infantry.",
        ),
        QAItem(
            question="What problem interrupted the parade?",
            answer=f"The parade was interrupted because {scene['problem']}.",
        ),
        QAItem(
            question="What did the first plan get wrong?",
            answer=f"The first plan failed because {scene['mistake']}.",
        ),
        QAItem(
            question="What clue changed the sailor's thinking?",
            answer=f"The sailor noticed {scene['clue']}, which showed that the route needed to be understood differently.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {scene['twist']}.",
        ),
        QAItem(
            question="How did the sailor and infantry fix the parade?",
            answer=f"Together, they {scene['action']}. This allowed the music to reach people who might otherwise have missed it.",
        ),
        QAItem(
            question="How did the parade end?",
            answer=f"It ended when {scene['ending']}. The parade became a kinder celebration for everyone involved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized group that moves through a public place with music, flags, or other sights for people to enjoy.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and learns how to travel safely on water by reading weather, wind, and waves.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move on foot, often working together in a coordinated group.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change or discovery that makes an earlier event mean something new.",
        ),
    ]


ASP_RULES = r"""
% The parade begins with a sailor and an infantry marcher.
has_parade_team(S) :- sailor_present(S), infantry_present(S).

% A twist occurs when the team notices a clue and changes the route.
twist(S) :- has_parade_team(S), clue_noticed(S), route_changed(S).

% The heartwarming resolution reaches people who could not reach the main stop.
heartwarming(S) :- twist(S), people_reached(S).

valid_story(S) :- has_parade_team(S), twist(S), heartwarming(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("sailor_present", "story1"),
        asp.fact("infantry_present", "story1"),
        asp.fact("clue_noticed", "story1"),
        asp.fact("route_changed", "story1"),
        asp.fact("people_reached", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if found == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(found))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade storyworld with a sailor, infantry, and a twist."
    )
    parser.add_argument("--sailor-name", choices=NAMES)
    parser.add_argument("--infantry-name", choices=NAMES)
    parser.add_argument("--parade-name", choices=PARADES)
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
    sailor = args.sailor_name or rng.choice(NAMES)
    infantry_choices = [name for name in NAMES if name != sailor]
    infantry = args.infantry_name or rng.choice(infantry_choices)
    parade = args.parade_name or rng.choice(PARADES)
    sailor_type = "sailor_girl" if sailor in {"Mara", "Lina", "Pia", "Tessa"} else "sailor"
    infantry_type = "girl" if infantry in {"Mara", "Lina", "Pia", "Tessa"} else "boy"
    return StoryParams(
        sailor_name=sailor,
        sailor_type=sailor_type,
        infantry_name=infantry,
        infantry_type=infantry_type,
        parade_name=parade,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


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


CURATED = [
    StoryParams(sailor_name="Mara", sailor_type="sailor_girl", infantry_name="Jonah", infantry_type="boy", parade_name="the Harbor Lights Parade"),
    StoryParams(sailor_name="Owen", sailor_type="sailor", infantry_name="Lina", infantry_type="girl", parade_name="the Lantern Parade"),
    StoryParams(sailor_name="Tessa", sailor_type="sailor_girl", infantry_name="Ravi", infantry_type="boy", parade_name="the Spring Drum Parade"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

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
