#!/usr/bin/env python3
"""
A standalone Storyweavers world about a heartwarming parade.

A sailor and an infantry drummer prepare a town parade, but a missing
signal flag creates a problem. A gentle twist reveals that the quietest
helper has been preparing a surprise welcome, and the parade changes course
to include everyone.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "harbor parade"
SEED_WORDS = {"parade", "sailor", "infantry"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "harbor"

    def __post_init__(self) -> None:
        for key in ("distance", "wind", "weight", "brightness", "noise"):
            self.meters.setdefault(key, 0.0)
        for key in ("hope", "worry", "pride", "belonging", "kindness", "courage"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    sailor: str = "Mara"
    infantry: str = "Jonah"
    scenario: int = 0
    voice: int = 0
    twist_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    place: str
    missing: str
    obstacle: str
    clue: str
    false_lead: str
    discovery: str
    twist: str
    repair: str
    proof: str
    lesson: str
    ending: str


SCENARIOS = [
    Scenario(
        place="the bright harbor square",
        missing="the blue welcome pennant",
        obstacle="a sharp wind tore the parade's signal flag from its pole",
        clue="a trail of blue thread leading toward the old boathouse",
        false_lead="a gull carried a scrap of blue cloth toward the sea",
        discovery="found the pennant folded beneath a stack of clean sailcloth",
        twist="the pennant had not been lost at all: a shy child named Elsie had borrowed it to sew small blue stars onto a welcome banner for the returning boats",
        repair="joined the banner to the parade standard and invited Elsie to carry it at the front",
        proof="the new banner held steady, and every child on the route could see a star made by someone's careful hand",
        lesson="A parade becomes warmer when it makes room for the people who were quietly helping.",
        ending="When the boats appeared, the harbor filled with blue stars and the sound of many happy feet.",
    ),
    Scenario(
        place="the village pier",
        missing="the brass captain's ribbon",
        obstacle="the ribbon vanished just before the sailor's boat reached the pier",
        clue="a line of gold thread caught on the parade cart",
        false_lead="a shining fish scale near the water made everyone look toward the tide",
        discovery="lifted the ribbon from the cart's folded bunting",
        twist="an elderly sailor had tucked it there while mending the cart, then used its loose thread to mark a place for a surprise reunion",
        repair="turned the cart around so the waiting families could stand beside the marching group",
        proof="the cart rolled smoothly and the sailor recognized his old shipmate in the front row",
        lesson="A small delay can reveal a larger kindness waiting nearby.",
        ending="The brass ribbon gleamed between two generations of sailors as the parade moved on.",
    ),
    Scenario(
        place="the town's maple-lined road",
        missing="the infantry drum's red strap",
        obstacle="the drum could not be carried when its strap snapped during rehearsal",
        clue="red stitching on a bench beside a basket of wool",
        false_lead="a scarlet kite tugging above the rooftops",
        discovery="found the broken strap beside a basket of handmade scarves",
        twist="the scarf-maker had taken the strap to weave its strong thread into a warm sling for a young drummer who was too small to carry the drum",
        repair="made the sling wider and let the young drummer march beside the infantry band",
        proof="the drum sounded clearly while the child kept both feet steady",
        lesson="A parade is not only about marching perfectly; it is about helping everyone take part.",
        ending="The drumbeat rolled down the maple road, and the smallest drummer smiled beneath the largest red scarf.",
    ),
    Scenario(
        place="the lighthouse green",
        missing="the white lantern for the evening parade",
        obstacle="clouds covered the moon and the parade lantern would not light",
        clue="a warm glow shining through a shed window",
        false_lead="a firefly drifting over the grass",
        discovery="found the lantern beside a box of repaired batteries",
        twist="the lighthouse keeper had borrowed it to guide a lost sailor's family safely up the path, then returned it brighter than before",
        repair="walked the parade past the lighthouse and let the keeper lead the first lantern turn",
        proof="the light shone across the green and showed every face in the crowd",
        lesson="The best route is sometimes the one that first helps someone who needs it.",
        ending="Under the renewed lantern, the parade curved toward the lighthouse like a river of warm stars.",
    ),
]


@dataclass
class World:
    hero: Entity
    sailor: Entity
    infantry: Entity
    banner: Entity
    drum: Entity
    harbor: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def entity(eid: str, kind: str, type_: str, label: str, location: str = "harbor") -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, location=location)


def build_world(params: StoryParams) -> World:
    hero = entity(params.hero, "character", "child", "the young parade leader")
    sailor = entity(params.sailor, "character", "sailor", "the sailor")
    infantry = entity(params.infantry, "character", "infantry", "the infantry drummer")
    banner = entity("banner", "object", "flag", "the parade banner")
    drum = entity("drum", "object", "drum", "the infantry drum")
    harbor = entity("harbor", "place", "harbor", "the harbor square")
    return World(hero, sailor, infantry, banner, drum, harbor)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, s, i = world.hero, world.sailor, world.infantry
    scenario = SCENARIOS[params.scenario % len(SCENARIOS)]

    h.memes["hope"] = 2
    h.memes["worry"] = 1
    s.memes["pride"] = 1
    i.memes["courage"] = 1
    world.banner.meters["brightness"] = 2
    world.drum.meters["noise"] = 2

    openings = [
        f"In {scenario.place}, {h.id}, {s.id} the sailor, and {i.id} of the infantry band prepared a parade for the whole town.",
        f"Flags fluttered above {scenario.place} as {h.id} checked the route, {s.id} polished the boat bell, and {i.id} warmed up the parade drum.",
        f"The harbor woke to music. {h.id} carried the parade list while {s.id} and {i.id} gathered the sailor flags and infantry drums.",
        f"Families filled {scenario.place} before the parade began. {h.id} wanted every guest to feel welcome, especially the sailors returning that day.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"Then {scenario.obstacle}. Without it, the parade could not show the sailors where to turn.")
    world.say(f"{h.id} felt worry, but the sailor and the infantry drummer stayed close.")

    world.para()
    world.say(f"Near the empty pole, they noticed {scenario.clue}.")
    world.say(f"At the same time, {scenario.false_lead}.")
    thoughts = [
        f"'The sea is full of surprises,' {h.id} said, 'but the thread is a clue we can follow.'",
        f"{h.id} took a slow breath. 'We should test the thread before we chase the gull.'",
        f"'A bright thing can distract us,' said {h.id}. 'Let's look for what touched the missing flag.'",
        f"{h.id} pointed to the ground. 'The smallest mark may tell us where the parade's heart went.'",
    ]
    world.say(thoughts[params.voice % len(thoughts)])

    dialogue = [
        f"{s.id} said, 'I know the water, but I do not know every path on land.' 'Then we will search together,' {i.id} replied.",
        f"'Should we keep marching?' asked {i.id}. 'Not until we understand what happened,' said {h.id}.",
        f"{s.id} asked, 'What can the thread prove?' {h.id} answered, 'Only where the flag may have brushed something. We still need to check.'",
        f"'I can listen for the next clue,' said {i.id}. 'And I can watch the wind,' said {s.id}.",
    ]
    world.say(dialogue[(params.voice + params.twist_style) % len(dialogue)])
    world.say("They divided the search: the sailor watched the pier, the infantry drummer checked the carts, and the parade leader followed the blue trail.")

    world.para()
    search_lines = [
        "The gull flew away, but its scrap was not part of the pennant. The blue thread led somewhere more useful.",
        "Their first guess failed. Instead of blaming the wind or one another, they compared what each person had actually seen.",
        "The search grew quiet. Even the drum waited while the team tested the clue against the places along the route.",
        "When the clues were placed side by side, the false lead became smaller and the careful thread became stronger.",
    ]
    world.say(search_lines[params.twist_style % len(search_lines)])
    world.say(f"At last, the team {scenario.discovery}.")
    world.banner.location = "boathouse"
    world.banner.meters["distance"] = 1

    twists = [
        f"That was the twist: {scenario.twist}.",
        f"Then came a gentle surprise. {scenario.twist}.",
        f"The missing pennant held a kinder secret than anyone expected: {scenario.twist}.",
        f"What looked like a parade problem became a welcome gift. {scenario.twist}.",
    ]
    world.say(twists[params.twist_style % len(twists)])
    world.say(f"{h.id} smiled and said, 'The parade should carry that kindness with us.'")

    world.para()
    world.say(f"The sailor and the infantry drummer {scenario.repair}.")
    world.banner.location = "parade front"
    world.banner.meters["distance"] = 0
    world.banner.meters["brightness"] += 1
    h.memes["belonging"] += 2
    s.memes["kindness"] += 1
    i.memes["kindness"] += 1
    world.say(f"They tested the new plan: {scenario.proof}.")
    world.say(f"{i.id} tapped a soft opening beat, and {s.id} rang the boat bell so the whole parade could hear.")

    lessons = [
        f"{h.id} said, 'Today we learned that {scenario.lesson.lower()}'",
        f"The sailor nodded. 'A true celebration remembers that {scenario.lesson.lower()}'",
        f"The infantry drummer added, 'Our best marching step is the one that makes room for others.'",
        f"Nobody hurried past the lesson: {scenario.lesson}",
    ]
    world.say(lessons[params.ending_style % len(lessons)])

    world.para()
    endings = [
        scenario.ending,
        f"The last drumbeat faded gently. {scenario.ending}",
        f"Even the gulls seemed to listen. {scenario.ending}",
        f"At the front, the new helper lifted the banner high. {scenario.ending}",
    ]
    world.say(endings[params.ending_style % len(endings)])

    world.facts.update(
        scenario=scenario,
        hero=h,
        sailor=s,
        infantry=i,
        resolved=True,
        missing=scenario.missing,
        obstacle=scenario.obstacle,
        clue=scenario.clue,
        false_lead=scenario.false_lead,
        discovery=scenario.discovery,
        twist=scenario.twist,
        repair=scenario.repair,
        proof=scenario.proof,
        lesson=scenario.lesson,
        ending=scenario.ending,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, s, i = f["hero"], f["sailor"], f["infantry"]
    return [
        QAItem(
            question="What problem interrupted the parade?",
            answer=f"The parade was interrupted because {f['obstacle']}. The missing item was {f['missing']}.",
        ),
        QAItem(
            question=f"How did {h.id} and the others find the missing item?",
            answer=f"They followed {f['clue']} instead of trusting the false lead. Then they {f['discovery']}.",
        ),
        QAItem(
            question="What was the heartwarming twist?",
            answer=f"The twist was that {f['twist']}. The missing item had become part of a thoughtful welcome.",
        ),
        QAItem(
            question=f"How did the sailor and infantry drummer help?",
            answer=f"{s.id} and {i.id} helped when they {f['repair']}. They also helped test the new parade plan.",
        ),
        QAItem(
            question="What did the parade teach the characters?",
            answer=f"They learned that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people walk, march, play music, or carry decorations for others to watch.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and ships, helping them travel and caring for the people and equipment on board.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who travel and work on foot. In a parade, an infantry group may march together with music or flags.",
        ),
        QAItem(
            question="Why can a twist make a story interesting?",
            answer="A twist changes what the reader expected and reveals a new reason, discovery, or choice that makes earlier clues mean something different.",
        ),
        QAItem(
            question="What makes an ending heartwarming?",
            answer="A heartwarming ending shows care, belonging, or kindness, often through a concrete action that brings people closer together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming child-friendly parade story featuring a sailor and infantry drummer. Include this problem: {f['obstacle']}.",
        f"Tell a story in which characters follow this clue: {f['clue']}, then reveal a gentle twist: {f['twist']}.",
        "Create a warm parade tale where a missing object leads to a kinder, more inclusive celebration.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{n}. {prompt}" for n, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in (
        world.hero,
        world.sailor,
        world.infantry,
        world.banner,
        world.drum,
        world.harbor,
    ):
        meters = {k: v for k, v in item.meters.items() if v}
        memes = {k: v for k, v in item.memes.items() if v}
        lines.append(
            f"  {item.id:10} ({item.kind:9}) location={item.location!r} "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(harbor_parade).
has_role(harbor_parade, sailor).
has_role(harbor_parade, infantry).
has_feature(harbor_parade, twist).
has_style(harbor_parade, heartwarming).

valid_story(S) :-
    setting(S),
    has_role(S, sailor),
    has_role(S, infantry),
    has_feature(S, twist),
    has_style(S, heartwarming).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "harbor_parade"),
            asp.fact("has_role", "harbor_parade", "sailor"),
            asp.fact("has_role", "harbor_parade", "infantry"),
            asp.fact("has_feature", "harbor_parade", "twist"),
            asp.fact("has_style", "harbor_parade", "heartwarming"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = any(atom.name == "valid_story" for atom in model)
    py_ok = all(word in SEED_WORDS for word in ("parade", "sailor", "infantry"))
    if asp_ok and py_ok:
        for index in range(len(SCENARIOS)):
            params = StoryParams(scenario=index)
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("MISMATCH: generated story validation failed.")
                return 1
        print("OK: Python and ASP agree on the harbor parade domain.")
        return 0
    print("MISMATCH: ASP or Python domain validation failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming harbor parade story."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--sailor", default=None)
    parser.add_argument("--infantry", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nora", "Milo", "Ada", "Theo"])
    sailor = args.sailor or rng.choice(["Mara", "Sol", "Bea", "Rafi", "June"])
    infantry = args.infantry or rng.choice(["Jonah", "Pia", "Owen", "Nell", "Sam"])
    if len({hero, sailor, infantry}) != 3:
        raise StoryError("The hero, sailor, and infantry drummer must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        sailor=sailor,
        infantry=infantry,
        scenario=offset % len(SCENARIOS),
        voice=(offset // len(SCENARIOS)) % 4,
        twist_style=(offset // (len(SCENARIOS) * 4)) % 4,
        ending_style=(offset // (len(SCENARIOS) * 4 * 4)) % 4,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(hero="Luna", sailor="Mara", infantry="Jonah", scenario=0),
    StoryParams(hero="Nora", sailor="Sol", infantry="Pia", scenario=1),
    StoryParams(hero="Milo", sailor="Bea", infantry="Owen", scenario=2),
    StoryParams(hero="Ada", sailor="Rafi", infantry="Nell", scenario=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if not samples:
        raise StoryError("No story variants could be generated.")

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
    try:
        main()
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        sys.exit(2)
