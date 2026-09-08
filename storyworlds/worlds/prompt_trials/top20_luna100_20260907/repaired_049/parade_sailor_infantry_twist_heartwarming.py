#!/usr/bin/env python3
"""
A heartwarming parade storyworld about a sailor, an infantry drummer, and a
small twist that turns a missed march into a shared celebration.
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

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    obstacle: str
    twist_clue: str
    sailor_action: str
    infantry_action: str
    result: str
    change: str
    ending: str
    lesson: str
    prop: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple[str, str]] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    sailor_name: str
    infantry_name: str
    child_name: str
    scenario: str
    seed: Optional[int] = None


SETTING = Setting(
    place="the harbor square",
    affords={"parade", "music", "shore", "kindness"},
)

SAILOR_NAMES = ["Mara", "Niko", "Lina", "Oren", "Sela", "Tavi"]
INFANTRY_NAMES = ["Bram", "Iris", "Jon", "Pia", "Ruth", "Cal"]
CHILD_NAMES = ["Ada", "Milo", "Nell", "Tomas", "Bea", "Finn"]

SCENARIOS = [
    Scenario(
        id="borrowed_drum",
        opening="The town was preparing a bright parade for everyone who had helped mend the harbor wall.",
        obstacle="The infantry drum split just before the march, and the soldiers feared their row would have no steady beat.",
        twist_clue="The sailor noticed that the empty water cask beside the pier made a warm, deep sound when tapped.",
        sailor_action="rolled the cask to the parade route and held it steady",
        infantry_action="wrapped a clean sailcloth band around the crack in the drum",
        result="the cask and the mended drum made a friendly beat that guided every marcher",
        change="a spare parade drum was kept beside the harbor workshop",
        ending="At sunset, the sailor tapped the cask once, the infantry answered on the drum, and the whole square clapped in time.",
        lesson="A missing piece can sometimes reveal a new way for everyone to join in.",
        prop="a painted water cask",
    ),
    Scenario(
        id="quiet_flag",
        opening="A parade was planned to welcome sailors home after a long voyage.",
        obstacle="The strongest wind tore the infantry flag from its pole before the guests could see it.",
        twist_clue="The sailor saw small signal ribbons fluttering safely from the rail of a nearby boat.",
        sailor_action="brought the boat's spare signal ribbons to the square",
        infantry_action="braided the ribbons into a broad, bright banner",
        result="the new banner danced in the wind without hiding any marching face",
        change="every parade group received ribbons that could be shared in bad weather",
        ending="The sailor raised the banner, and the infantry marched beneath a rainbow made from many small flags.",
        lesson="Many little gifts can become one strong welcome.",
        prop="a bundle of signal ribbons",
    ),
    Scenario(
        id="lost_heel",
        opening="The harbor prepared a parade for children who had learned to swim safely.",
        obstacle="An infantry marcher lost the heel from one boot and could not keep pace on the cobbles.",
        twist_clue="The sailor found a soft coil of rope whose woven center matched the shape of the missing heel.",
        sailor_action="cut and shaped the rope with the boat knife",
        infantry_action="held the boot while a cobbler stitched the rope into place",
        result="the marcher could step gently and stay beside the smallest children",
        change="the parade stored a repair basket for feet, flags, and instruments",
        ending="The repaired boot made a soft tap beside the children's shoes all the way to the sea gate.",
        lesson="Careful help is more important than looking perfect at the start.",
        prop="a coil of bright rope",
    ),
    Scenario(
        id="hidden_guest",
        opening="The harbor square filled with music for the annual parade.",
        obstacle="A shy lighthouse keeper stood behind the crowd because she believed nobody remembered her quiet work.",
        twist_clue="The sailor saw the lighthouse keeper's lamp shining from the hill above the route.",
        sailor_action="asked the keeper to carry the lamp at the front",
        infantry_action="changed their marching turn so the light could guide them",
        result="the crowd saw the keeper and thanked her for every safe night",
        change="the parade began naming quiet helpers as well as loud leaders",
        ending="The lighthouse lamp glowed above the parade, and its keeper smiled when the infantry saluted.",
        lesson="A celebration is brightest when it makes unseen kindness visible.",
        prop="a brass lighthouse lamp",
    ),
    Scenario(
        id="rainy_rehearsal",
        opening="The sailor and the infantry practiced a welcoming parade beneath gray clouds.",
        obstacle="Rain filled the square, and the musicians worried that the celebration would have to be canceled.",
        twist_clue="The sailor heard rain drumming a cheerful rhythm on the awnings around the market.",
        sailor_action="invited families to shelter beneath the awnings",
        infantry_action="matched their drums to the rain instead of fighting its sound",
        result="the parade became a warm moving concert under a roof of striped cloth",
        change="the town marked a covered route for rainy celebrations",
        ending="Rain fell outside while the sailor waved from one awning and the infantry played from the next.",
        lesson="A changed plan can still carry the same welcome.",
        prop="striped market awnings",
    ),
    Scenario(
        id="smallest_step",
        opening="The harbor held a parade to thank workers who repaired the old pier.",
        obstacle="A little child wanted to march but could not keep up with the long infantry steps.",
        twist_clue="The sailor noticed that gulls reached the same place with many tiny steps.",
        sailor_action="invited the child to set a small marching pace",
        infantry_action="shortened their steps and followed the child's beat",
        result="the whole parade moved together without leaving anyone behind",
        change="the parade taught a small-step rhythm for young marchers",
        ending="The sailor's boots, the infantry shoes, and the child's tiny feet all arrived at the pier together.",
        lesson="A good march makes room for every pace.",
        prop="a little silver whistle",
    ),
]

DIALOGUES = [
    ("The sailor said, \"What if the parade is asking us to listen differently?\"",
     "The infantry leader answered, \"Then we will listen before we hurry.\""),
    ("The infantry leader asked, \"Can your ship's way of solving trouble help us here?\"",
     "The sailor replied, \"Only if we solve it together.\""),
    ("The sailor whispered, \"Who is missing from our welcome?\"",
     "The infantry leader said, \"Let us make room and find out.\""),
    ("The infantry leader asked, \"Should we stop the parade?\"",
     "The sailor smiled. \"Not if we can turn the problem into an invitation.\""),
]

OPENINGS = [
    "On a clear morning, the harbor square woke to flags, gulls, and the bright promise of a parade.",
    "Every spring, the town held a parade for people whose patient work kept the harbor safe.",
    "The sailors had come home, and the infantry band prepared a welcome that could be heard from the sea.",
    "At the edge of the water, a parade gathered its colors before the first drumbeat.",
]

ADJECTIVES = ["kind", "cheerful", "thoughtful", "brave", "gentle", "curious"]


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def valid_combos() -> list[tuple[str, str]]:
    return [(SETTING.place, scenario.id) for scenario in SCENARIOS]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade story about a sailor, infantry, and a twist."
    )
    parser.add_argument("--place", choices=[SETTING.place])
    parser.add_argument("--scenario", choices=[s.id for s in SCENARIOS])
    parser.add_argument("--sailor-name")
    parser.add_argument("--infantry-name")
    parser.add_argument("--child-name")
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
    place = args.place or SETTING.place
    if place != SETTING.place:
        raise StoryError("The parade must begin in the harbor square.")
    scenario = args.scenario or rng.choice([s.id for s in SCENARIOS])
    if scenario not in {s.id for s in SCENARIOS}:
        raise StoryError("That parade trouble is not part of this storyworld.")
    sailor_name = args.sailor_name or rng.choice(SAILOR_NAMES)
    infantry_name = args.infantry_name or rng.choice(INFANTRY_NAMES)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    if len({sailor_name, infantry_name, child_name}) != 3:
        raise StoryError("The sailor, infantry leader, and child need different names.")
    return StoryParams(
        place=place,
        sailor_name=sailor_name,
        infantry_name=infantry_name,
        child_name=child_name,
        scenario=scenario,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != SETTING.place:
        raise StoryError("This storyworld only supports a parade in the harbor square.")
    if params.scenario not in {s.id for s in SCENARIOS}:
        raise StoryError("The selected parade twist is unavailable.")
    if len({params.sailor_name, params.infantry_name, params.child_name}) != 3:
        raise StoryError("The three principal characters must have different names.")


def tell(world: World, params: StoryParams) -> None:
    scenario = next(s for s in SCENARIOS if s.id == params.scenario)
    sailor = world.add(Entity(params.sailor_name, "character", "sailor", "sailor"))
    infantry = world.add(
        Entity(params.infantry_name, "character", "infantry", "infantry leader")
    )
    child = world.add(Entity(params.child_name, "character", "child", "child"))
    parade = world.add(Entity("parade", "event", "parade", "parade"))
    prop = world.add(Entity("shared_prop", "thing", "prop", scenario.prop))

    add_meme(sailor, "hope", 1.0)
    add_meme(infantry, "pride", 1.0)
    add_meme(child, "belonging", 1.0)
    add_meter(parade, "readiness", 1.0)

    variant = params.seed if params.seed is not None else 0
    opening = OPENINGS[variant % len(OPENINGS)]
    dialogue = DIALOGUES[(variant // len(OPENINGS)) % len(DIALOGUES)]
    adjective = ADJECTIVES[(variant // (len(OPENINGS) * len(DIALOGUES))) % len(ADJECTIVES)]

    world.say(opening)
    world.say(
        f"{params.sailor_name}, a {adjective} sailor, stood beside "
        f"{scenario.prop} while {params.infantry_name} led the infantry band into place."
    )
    world.say(
        f"{params.child_name} watched from the front row, holding a small place in the parade for anyone who needed it."
    )
    world.para()

    world.say(scenario.opening)
    world.say(scenario.obstacle)
    add_meme(sailor, "worry", 1.0)
    add_meme(infantry, "worry", 1.0)
    world.say(dialogue[0])
    world.say(dialogue[1])
    world.say(
        f"Then the sailor noticed the twist: {scenario.twist_clue}"
    )
    add_meme(sailor, "curiosity", 1.0)
    add_meme(infantry, "trust", 1.0)
    world.para()

    add_meter(sailor, "helping", 1.0)
    add_meter(infantry, "helping", 1.0)
    world.say(
        f"{params.sailor_name} {scenario.sailor_action}, while "
        f"{params.infantry_name} {scenario.infantry_action}."
    )
    add_meter(prop, "useful", 1.0)
    world.say(
        f"{params.child_name} carried the first small sign, and soon the whole parade had a part to play."
    )
    world.say(scenario.result)
    add_meter(parade, "readiness", 1.0)
    add_meme(sailor, "joy", 1.0)
    add_meme(infantry, "joy", 1.0)

    world.para()
    world.say(
        f"After the parade, the town made a lasting change: {scenario.change}."
    )
    world.say(
        f"The heart of the day was simple: {scenario.lesson}"
    )
    world.say(scenario.ending)

    world.facts.update(
        scenario=scenario,
        sailor=sailor,
        infantry=infantry,
        child=child,
        parade=parade,
        prop=prop,
        dialogue=dialogue,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    scenario: Scenario = world.facts["scenario"]
    sailor: Entity = world.facts["sailor"]
    infantry: Entity = world.facts["infantry"]
    return [
        f"Write a heartwarming story about a sailor named {sailor.id}, an infantry leader named {infantry.id}, and a parade.",
        f"Tell a parade story in which a surprising twist turns this obstacle into kindness: {scenario.obstacle}",
        f"Write a child-friendly tale showing how {sailor.id} and {infantry.id} solve a problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario: Scenario = world.facts["scenario"]
    sailor: Entity = world.facts["sailor"]
    infantry: Entity = world.facts["infantry"]
    child: Entity = world.facts["child"]
    return [
        QAItem(
            question="Who were the two main helpers in the parade?",
            answer=f"{sailor.id}, a sailor, and {infantry.id}, the infantry leader, worked together to save the parade.",
        ),
        QAItem(
            question="What problem interrupted the parade?",
            answer=f"{scenario.obstacle} The problem threatened to spoil the town's welcome.",
        ),
        QAItem(
            question="What twist changed their plan?",
            answer=f"The twist was that {scenario.twist_clue} This gave the helpers a new idea instead of leaving them stuck.",
        ),
        QAItem(
            question="How did the sailor help?",
            answer=f"{sailor.id} {scenario.sailor_action}, making it possible for the parade to continue.",
        ),
        QAItem(
            question="How did the infantry help?",
            answer=f"{infantry.id} {scenario.infantry_action}, so the shared solution became strong enough for the march.",
        ),
        QAItem(
            question="How did the child become part of the ending?",
            answer=f"{child.id} carried the first small sign, and the whole parade made room for every helper.",
        ),
        QAItem(
            question="What changed after the parade?",
            answer=f"The town decided that {scenario.change}. The lesson lasted beyond that single celebration.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people move together, often with music, flags, or decorations.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or near a boat and helps travel, care for equipment, or keep people safe on the water.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who serve and move on foot.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change or discovery that makes the story take a new direction.",
        ),
        QAItem(
            question="Why can teamwork help during a problem?",
            answer="Teamwork helps because people can combine different skills, notice more clues, and support one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== Prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("")
    sections.append("== Story QA ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== World QA ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(
            f"{entity.id}: {entity.type} " + " ".join(details)
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(harbor_square, borrowed_drum).
valid(harbor_square, quiet_flag).
valid(harbor_square, lost_heel).
valid(harbor_square, hidden_guest).
valid(harbor_square, rainy_rehearsal).
valid(harbor_square, smallest_step).

parade_story(Place, Scenario) :- valid(Place, Scenario).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "harbor_square"),
            *(
                asp.fact("scenario", scenario.id)
                for scenario in SCENARIOS
            ),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_combos = {
        ("harbor_square", scenario_id)
        for _, scenario_id in valid_combos()
    }
    clingo_combos = set(asp_valid_combos())
    if python_combos != clingo_combos:
        print("MISMATCH")
        print(f"Python: {sorted(python_combos)}")
        print(f"ASP: {sorted(clingo_combos)}")
        return 1

    rng = random.Random(9917)
    for _ in range(8):
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = rng.randrange(100000)
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("MISMATCH: generated sample was incomplete")
            return 1
    print(f"OK: ASP matches Python ({len(python_combos)} combinations); stories generated.")
    return 0


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
    StoryParams("the harbor square", "Mara", "Bram", "Ada", "borrowed_drum"),
    StoryParams("the harbor square", "Niko", "Iris", "Milo", "hidden_guest"),
    StoryParams("the harbor square", "Lina", "Jon", "Nell", "smallest_step"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        try:
            sys.exit(asp_verify())
        except ImportError as exc:
            raise SystemExit(f"ASP verification requires clingo: {exc}")

    if args.asp:
        print(asp_program("#show valid/2."))
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(20, args.n * 30):
            current_seed = base_seed + index
            index += 1
            rng = random.Random(current_seed)
            try:
                params = resolve_params(args, rng)
                params.seed = current_seed
                sample = generate(params)
            except StoryError as exc:
                raise SystemExit(str(exc))
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise SystemExit("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.sailor_name}: parade / {params.scenario}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
