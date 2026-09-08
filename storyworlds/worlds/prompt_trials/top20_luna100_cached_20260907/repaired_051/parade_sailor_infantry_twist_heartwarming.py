#!/usr/bin/env python3
"""
A heartwarming parade storyworld about a sailor, an infantry drummer, and a
small twist that changes who leads the celebration.
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
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "balance": 0.0,
            "volume": 0.0,
            "warmth": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "joy": 0.0,
            "relief": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "Harbor Lantern Square"


@dataclass
class StoryParams:
    sailor: str
    sailor_type: str
    infantry: str
    infantry_type: str
    child: str
    child_type: str
    parade_name: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


SCENARIOS = [
    {
        "route": "the spring harbor parade",
        "problem": "A strong sea wind tore the parade's bright banner from its pole and carried it toward the old lighthouse steps.",
        "first_try": "The sailor pulled hard on the loose rope, but the banner wrapped tighter around the rail.",
        "clue": "The infantry drummer noticed that the banner moved whenever the small harbor bell rang.",
        "action": "The sailor timed a gentle tug with the bell, while the infantry formed a safe line and the child guided the cloth with a broom.",
        "twist": "When the banner came free, everyone saw a tiny painted anchor on its back, made by children who had once welcomed the sailor home.",
        "result": "The parade turned toward the lighthouse, where the sailor held the banner high and the infantry played a slower, warmer march.",
        "lesson": "a celebration belongs to the people who fill it with care",
        "image": "the banner floated above the square, its hidden anchor shining in the sunset",
    },
    {
        "route": "the moonlit return parade",
        "problem": "The parade drum lost its deep voice just before the sailors and infantry reached the town gate.",
        "first_try": "The infantry drummer struck harder, but the cracked drumhead answered with a small and lonely pop.",
        "clue": "The sailor heard a steady tapping from a basket beside the soup tent.",
        "action": "They discovered a cook tapping two wooden spoons, then matched the spoons to the drummer's soft beat.",
        "twist": "The missing drum sound had not been needed at all; the whole town had been waiting for a quieter rhythm so sleeping babies would not wake.",
        "result": "The parade crossed the gate to a gentle beat, and families stepped outside carrying warm cups of soup.",
        "lesson": "listening can reveal the welcome that people truly need",
        "image": "wooden spoons and drumsticks rested together beside the glowing soup tent",
    },
    {
        "route": "the first-rain neighborhood parade",
        "problem": "Rain began just as the sailor's little boat cart reached the narrowest street.",
        "first_try": "The infantry tried to shield the cart with their coats, but the wind turned the coats into flapping sails.",
        "clue": "A child pointed to strings of old umbrellas hanging above the bakery lane.",
        "action": "The neighbors lowered the umbrellas, the infantry held them in a row, and the sailor rolled the cart beneath their bright roof.",
        "twist": "The boat cart was not carrying medals, as everyone had guessed; it held letters from sailors to families who had missed them.",
        "result": "The parade stopped at every doorway so each letter could reach the right pair of hands.",
        "lesson": "the most precious cargo may be a message meant for someone else",
        "image": "rain drummed on a roof of umbrellas while families read letters in the warm doorway light",
    },
    {
        "route": "the lantern parade around the village hill",
        "problem": "The lead lantern went dark, leaving the parade unsure which path was safe.",
        "first_try": "The sailor lit a match, but the wind snuffed it out before it touched the wick.",
        "clue": "The infantry captain saw fireflies glowing beside the old stone wall.",
        "action": "The friends followed the fireflies to a covered alcove, relit the lantern there, and placed it on a high cart.",
        "twist": "The lantern had been designed by the town's oldest resident, who could no longer walk in parades but had watched every one from her window.",
        "result": "The parade carried her lantern past her window, and she waved from her chair as if she were marching with them.",
        "lesson": "including someone can make a path feel brighter for everyone",
        "image": "the old resident's lantern glowed in the window long after the parade passed",
    },
    {
        "route": "the welcome-home parade along the pebble beach",
        "problem": "The sailor's flagstaff snapped when the parade reached the shore.",
        "first_try": "The infantry tied it to a heavy crate, but the next wave pulled the crate toward the water.",
        "clue": "A child found a long piece of driftwood shaped like a mast.",
        "action": "The sailor sanded its rough edge, the infantry wrapped it with spare cord, and the child tied the flag at the top.",
        "twist": "The flag was not meant to honor one sailor; its stitched names belonged to everyone who had helped keep the harbor safe.",
        "result": "The whole parade held the cord together while the shared flag rose above the beach.",
        "lesson": "thanks grow stronger when no helper is left out",
        "image": "many stitched names fluttered together over the bright, foamy water",
    },
]


SAILOR_NAMES = ["Mara", "Jonah", "Anika", "Theo", "Lina"]
SAILOR_TYPES = ["sailor", "deckhand", "harbor sailor"]
INFANTRY_NAMES = ["Corporal Reed", "Drummer Vale", "Sergeant Rowan", "Private June"]
INFANTRY_TYPES = ["infantry drummer", "infantry captain", "infantry guide"]
CHILD_NAMES = ["Pip", "Nell", "Sam", "Tavi", "Rosa"]
CHILD_TYPES = ["child", "young helper", "harbor child"]
PARADE_NAMES = ["the Harbor Parade", "the Lantern Parade", "the Welcome Parade"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

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
        return "\n\n".join(" ".join(group) for group in self.paragraphs if group)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade story about a sailor and infantry helpers."
    )
    parser.add_argument("--sailor")
    parser.add_argument("--sailor-type")
    parser.add_argument("--infantry")
    parser.add_argument("--infantry-type")
    parser.add_argument("--child")
    parser.add_argument("--child-type")
    parser.add_argument("--parade")
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
    return StoryParams(
        sailor=args.sailor or rng.choice(SAILOR_NAMES),
        sailor_type=args.sailor_type or rng.choice(SAILOR_TYPES),
        infantry=args.infantry or rng.choice(INFANTRY_NAMES),
        infantry_type=args.infantry_type or rng.choice(INFANTRY_TYPES),
        child=args.child or rng.choice(CHILD_NAMES),
        child_type=args.child_type or rng.choice(CHILD_TYPES),
        parade_name=args.parade or rng.choice(PARADE_NAMES),
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def _choose(items: list[str], variant: int, offset: int) -> str:
    return items[(variant + offset) % len(items)]


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    world = World(Setting())

    sailor = world.add(
        Entity("sailor", "person", params.sailor_type, params.sailor)
    )
    infantry = world.add(
        Entity("infantry", "person", params.infantry_type, params.infantry)
    )
    child = world.add(Entity("child", "person", params.child_type, params.child))
    banner = world.add(Entity("parade_banner", "thing", "banner", "the parade banner"))
    parade = world.add(
        Entity("parade", "event", "parade", params.parade_name)
    )

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        child=child,
        banner=banner,
        parade=parade,
        scenario=scenario,
    )

    sailor.memes["courage"] = 1.0
    infantry.memes["trust"] = 1.0
    child.memes["joy"] = 1.0

    openings = [
        f"On the morning of {scenario['route']}, {sailor.label} the {sailor.type} polished a brass button beside {world.setting.place}.",
        f"When {scenario['route']} began, {sailor.label} the {sailor.type} stood at the front of the bright line in {world.setting.place}.",
        f"The bells of {world.setting.place} rang for {scenario['route']}, and {sailor.label} the {sailor.type} lifted a smiling hand.",
    ]
    world.say(_choose(openings, params.detail_variant, 0))
    world.say(
        f"{infantry.label}, a {infantry.type}, marched nearby while {child.label}, a {child.type}, carried a little ribbon for the parade."
    )
    world.say(
        f"They were proud to lead {params.parade_name}, because the parade was meant to welcome every neighbor home."
    )
    world.para()

    sailor.meters["distance"] = 1.0
    banner.meters["balance"] = 0.2
    sailor.memes["worry"] = 1.0
    world.say(scenario["problem"])
    world.say(
        f'"We must keep the parade together," {infantry.label} said. "{sailor.label}, what can we do?"'
    )
    world.say(
        f'"We can try one careful plan," {sailor.label} replied, though worry made the sailor grip the rope too tightly.'
    )
    world.say(scenario["first_try"])
    world.para()

    banner.meters["balance"] = 0.4
    world.say(scenario["clue"])
    world.say(
        f'"Look there," {child.label} said. "The parade can help if we listen to what the place is telling us."'
    )
    world.say(
        f'"Then we will use every helpful hand," {sailor.label} answered. The words changed the plan from a struggle into a team effort.'
    )
    child.memes["courage"] = 1.0
    infantry.memes["trust"] = 2.0
    world.para()

    banner.meters["balance"] = 1.0
    banner.meters["warmth"] = 1.0
    parade.meters["volume"] = 0.7
    sailor.memes["worry"] = 0.0
    sailor.memes["relief"] = 1.0
    infantry.memes["joy"] = 1.0
    child.memes["joy"] = 2.0

    world.say(scenario["action"])
    world.say(scenario["twist"])
    world.say(scenario["result"])
    world.para()

    world.say(
        f'{sailor.label} looked at {infantry.label} and {child.label}. "This is the kind of parade I will remember," the sailor said.'
    )
    world.say(
        f'The parade continued, not because one person had saved it, but because {sailor.label}, {infantry.label}, and {child.label} had trusted one another.'
    )
    world.say(f'They understood that {scenario["lesson"]}.')
    world.say(f'At sunset, {scenario["image"]}.')
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("banner_balance=1.0")
    world.log("parade_complete=true")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    sailor: Entity = world.facts["sailor"]  # type: ignore[assignment]
    infantry: Entity = world.facts["infantry"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about {sailor.label} the sailor leading a parade with {infantry.label} and {child.label}.",
        f"Tell a child-friendly parade story where a sailor, an infantry helper, and a young friend solve this problem: {scenario['problem']}",
        f"Include a gentle twist showing that the parade means more than the characters first expected.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    sailor: Entity = world.facts["sailor"]  # type: ignore[assignment]
    infantry: Entity = world.facts["infantry"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem interrupted {sailor.label}'s parade?",
            answer=f"{scenario['problem']} The parade had to pause so the group could protect its important banner or parade object.",
        ),
        QAItem(
            question=f"What did {infantry.label} notice or discover?",
            answer=f"{scenario['clue']} This clue helped the sailor, the infantry helper, and {child.label} choose a calmer plan.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"{scenario['twist']} The discovery showed that the parade carried a loving meaning the characters had not understood at first.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"{scenario['action']} Their shared effort allowed the parade to continue safely.",
        ),
        QAItem(
            question="What did the characters learn?",
            answer=f"They learned that {scenario['lesson']}. The finished parade proved that every helpful person mattered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people move together through a street or public place, often with music, flags, or decorations.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and ships, helping travel safely on water and caring for the vessel and its crew.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who serve and move on foot. In this gentle storyworld, the infantry characters are helpers in a community parade.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change or discovery that makes an earlier event mean something new.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        details = [f"type={entity.type}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(sailor).
entity(infantry).
entity(child).
entity(banner).
entity(parade).

safe_banner :- banner_found, team_helps, parade_stays_together.
parade_complete :- safe_banner, twist_revealed.
heartwarming_end :- parade_complete.

#show safe_banner/0.
#show parade_complete/0.
#show heartwarming_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("banner_found"),
            asp.fact("team_helps"),
            asp.fact("parade_stays_together"),
            asp.fact("twist_revealed"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show safe_banner/0. #show parade_complete/0. "
            "#show heartwarming_end/0."
        )
    )
    found = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"safe_banner/0", "parade_complete/0", "heartwarming_end/0"}
    if found != expected:
        print(f"MISMATCH: {sorted(found)} != {sorted(expected)}")
        return 1

    rng = random.Random(17)
    for _ in range(5):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        required = [params.sailor, params.infantry, params.child]
        if any(word not in sample.story for word in required):
            print("MISMATCH: generated story omitted a named character")
            return 1
        if "parade" not in sample.story.lower():
            print("MISMATCH: generated story omitted parade")
            return 1

    print("OK: ASP parity check and story exercise passed.")
    return 0


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        sailor="Mara",
        sailor_type="sailor",
        infantry="Corporal Reed",
        infantry_type="infantry drummer",
        child="Pip",
        child_type="child",
        parade_name="the Harbor Parade",
        scenario_index=0,
        detail_variant=2,
    ),
    StoryParams(
        sailor="Jonah",
        sailor_type="deckhand",
        infantry="Drummer Vale",
        infantry_type="infantry guide",
        child="Nell",
        child_type="young helper",
        parade_name="the Lantern Parade",
        scenario_index=2,
        detail_variant=5,
    ),
    StoryParams(
        sailor="Anika",
        sailor_type="harbor sailor",
        infantry="Sergeant Rowan",
        infantry_type="infantry captain",
        child="Rosa",
        child_type="harbor child",
        parade_name="the Welcome Parade",
        scenario_index=4,
        detail_variant=8,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show safe_banner/0. #show parade_complete/0. "
                "#show heartwarming_end/0."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show safe_banner/0. #show parade_complete/0. "
                "#show heartwarming_end/0."
            )
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n:
            if attempts >= max(args.n * 30, 30):
                raise StoryError("could not create enough distinct stories")
            rng = random.Random(base_seed + attempts)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempts
            attempts += 1
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
