#!/usr/bin/env python3
"""
A tiny heartwarming storyworld about a parade, a sailor, and infantry friends.
The twist: the quiet sailor is not marching for applause, but guiding a lost
little boat-shaped lantern home to the child who made it.
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
from collections import defaultdict
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass(frozen=True)
class Arc:
    key: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    turn: tuple[str, str]
    ending: tuple[str, str]
    problem: str
    action: str
    result: str
    final_image: str


ARCS = (
    Arc(
        "lantern_wake",
        (
            "In {place}, a bright parade curled past the harbor while {sailor} marched beside the infantry band.",
            "Every drum sounded proud, and little flags danced above the shining street.",
        ),
        (
            "Then a gust lifted a small boat lantern from the children's float and sent it skittering toward the dark water.",
            '"Keep the parade moving," called the drum leader. "But that lantern belongs to someone," said {sailor}.',
        ),
        (
            "{sailor} left the marching line only long enough to reach the lantern with a boat hook.",
            '"I can carry the light," {sailor} told {soldier}, "and you can help me find its maker."',
        ),
        (
            "Together they followed the painted stars on the lantern until they found a worried child beside the float.",
            "The parade paused for one sweet cheer as the little boat returned, glowing warmly in its owner's hands.",
        ),
        "a child-made boat lantern slipped away from the parade float",
        "the sailor rescued the lantern while an infantry friend searched for the child who made it",
        "the lantern returned safely to its maker",
        "the child hugging the glowing boat while the parade cheered",
    ),
    Arc(
        "missing_ribbon",
        (
            "At {place}, the parade gathered beneath bright bunting, and {sailor} marched with the smiling infantry.",
            "A blue ribbon fluttered from every cap as the town waited for the first brave drumbeat.",
        ),
        (
            "A young child's ribbon blew beneath the parade wagon and disappeared under a wheel.",
            '"The march must go on," said {soldier}. "The march can wait one small moment," answered {sailor}.',
        ),
        (
            "{sailor} crouched beside the wagon and used a sailor's careful knot to pull the ribbon free.",
            "{soldier} held the wagon still, then placed the ribbon back in the child's waiting hand.",
        ),
        (
            "The child tied the ribbon to the front flag, where it waved higher than any other.",
            "The infantry stepped proudly, the sailor smiled, and the parade carried the child's courage down the street.",
        ),
        "a child's blue ribbon became trapped beneath a parade wagon",
        "the sailor freed it with a careful knot while an infantry friend steadied the wagon",
        "the child placed the ribbon on the lead flag",
        "the blue ribbon waving above the whole parade",
    ),
    Arc(
        "quiet_hero",
        (
            "The town parade began at {place}, with {sailor} in a sailor's cap and {soldier} marching in the infantry line.",
            "The crowd clapped for polished boots, brass buttons, and banners bright as sunrise.",
        ),
        (
            "Behind the cheering crowd, an old harbor bell had stopped ringing, so a small girl could not find her grandfather.",
            '"I hear no bell," she whispered. "Then we will make a path of sound," said {sailor}.',
        ),
        (
            "{sailor} tapped a steady signal on a little ship's drum while {soldier} asked the infantry to pass the sound along.",
            "The beat traveled from one marcher to the next, turning the noisy parade into a gentle guide.",
        ),
        (
            "The girl followed the rhythm and found her grandfather waiting beside the harbor gate.",
            "No medal shone as brightly as their relieved smiles when the parade began again.",
        ),
        "a girl could not find her grandfather because the harbor bell had stopped",
        "the sailor made a steady drum signal and the infantry passed it along",
        "the girl followed the shared rhythm to the harbor gate",
        "the girl embracing her grandfather beside the returning parade",
    ),
)


@dataclass
class StoryParams:
    place: str
    sailor_name: str
    infantry_name: str
    sailor_gender: str = "boy"
    infantry_gender: str = "girl"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


PLACES = {
    "harbor_square": Place("harbor_square", "the harbor square", {"harbor", "town"}),
    "lighthouse_road": Place("lighthouse_road", "the lighthouse road", {"harbor", "road"}),
    "market_quay": Place("market_quay", "the market quay", {"harbor", "market"}),
}

NAMES = {
    "boy": ["Theo", "Finn", "Owen", "Milo"],
    "girl": ["Luna", "Nora", "Maya", "Ada"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "sailor", "infantry") for place in PLACES]


CURATED = [
    StoryParams("harbor_square", "Finn", "Luna", "boy", "girl"),
    StoryParams("lighthouse_road", "Theo", "Nora", "boy", "girl"),
    StoryParams("market_quay", "Maya", "Owen", "girl", "boy"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming parade story with a sailor, infantry, and a twist.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--sailor")
    parser.add_argument("--infantry")
    parser.add_argument("--sailor-gender", choices=["boy", "girl"])
    parser.add_argument("--infantry-gender", choices=["boy", "girl"])
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
    sailor_gender = args.sailor_gender or rng.choice(["boy", "girl"])
    infantry_gender = args.infantry_gender or ("girl" if sailor_gender == "boy" else "boy")
    sailor = args.sailor or rng.choice(NAMES[sailor_gender])
    choices = [name for name in NAMES[infantry_gender] if name != sailor]
    infantry = args.infantry or rng.choice(choices)
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        sailor_name=sailor,
        infantry_name=infantry,
        sailor_gender=sailor_gender,
        infantry_gender=infantry_gender,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown parade setting.")
    if params.sailor_name == params.infantry_name:
        raise StoryError("The sailor and infantry marcher must have different names.")
    if params.sailor_gender not in NAMES or params.infantry_gender not in NAMES:
        raise StoryError("Invalid character gender.")

    world = World(PLACES[params.place])
    sailor = world.add(Entity("sailor", "character", "sailor", params.sailor_name, "sailor"))
    soldier = world.add(Entity("infantry", "character", "infantry", params.infantry_name, "infantry"))
    parade = world.add(Entity("parade", "event", "parade", "the parade", "parade"))
    lantern = world.add(Entity("lantern", "thing", "lantern", "the little lantern", "twist"))

    rng = random.Random(params.seed if params.seed is not None else sum(ord(c) for c in params.place + params.sailor_name))
    arc = rng.choice(ARCS)
    values = {
        "place": world.place.label,
        "sailor": params.sailor_name,
        "soldier": params.infantry_name,
    }

    parade.meters["moving"] = 1
    sailor.memes["kindness"] += 1
    soldier.memes["care"] += 1

    for line in arc.opening:
        world.say(line.format(**values))
    world.para()

    parade.meters["trouble"] = 1
    lantern.meters["lost"] = 1
    sailor.memes["concern"] += 1
    soldier.memes["concern"] += 1
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()

    sailor.meters["helped"] = 1
    soldier.meters["helped"] = 1
    lantern.meters["found"] = 1
    for line in arc.turn:
        world.say(line.format(**values))
    world.para()

    parade.meters["moving"] = 1
    parade.meters["kind"] = 1
    lantern.meters["lost"] = 0
    lantern.meters["returned"] = 1
    sailor.memes["joy"] += 1
    soldier.memes["joy"] += 1
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        sailor=sailor,
        soldier=soldier,
        parade=parade,
        lantern=lantern,
        arc=arc.key,
        problem=arc.problem,
        action=arc.action,
        result=arc.result,
        final_image=arc.final_image,
        twist="The sailor paused the parade to help someone who needed a small light or sign of hope.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a heartwarming story about a parade, a sailor, and infantry friends.",
        f"Tell a gentle parade story in which {f['sailor'].label} notices that {f['problem']}.",
        "Use a kind twist: the quiet helper matters more than applause.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What problem happened during the parade?",
            f"During the parade, {f['problem']}.",
        ),
        QAItem(
            "How did the sailor and infantry friend help?",
            f"They helped by {f['action']}. This made sure that {f['result']}.",
        ),
        QAItem(
            "What was the story's twist?",
            f"The twist was that {f['twist']}",
        ),
        QAItem(
            "What image showed that everything ended well?",
            f"The ending showed {f['final_image']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a parade?",
            "A parade is an organized procession in which people move together while music, flags, or special costumes make the event joyful.",
        ),
        QAItem(
            "What does infantry mean?",
            "Infantry are soldiers who travel and work on foot. In this gentle story, the infantry marcher is also a caring friend.",
        ),
        QAItem(
            "Why can a small act of kindness matter?",
            "A small act of kindness can matter because it helps someone feel safe, noticed, and cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id:9} ({entity.type:8}) meters={meters} memes={memes}")
    lines.append(f"  place: {world.place.label}")
    lines.append(f"  arc: {world.facts.get('arc')}")
    return "\n".join(lines)


ASP_RULES = r"""
parade_ready :- parade(parade), moving(parade).
twist(kindness) :- sailor(sailor), infantry(infantry), lost_item(item), helps(sailor,item).
resolved(item) :- found(item), returned(item).
outcome(heartwarming) :- parade_ready, twist(kindness), resolved(item).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("parade", "parade"),
        asp.fact("sailor", "sailor"),
        asp.fact("infantry", "infantry"),
        asp.fact("lost_item", "lantern"),
        asp.fact("moving", "parade"),
        asp.fact("helps", "sailor", "lantern"),
        asp.fact("found", "lantern"),
        asp.fact("returned", "lantern"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        outcomes = asp.atoms(model, "outcome")
        if ("heartwarming",) not in outcomes:
            print("ASP parity failed: heartwarming outcome was absent.")
            return 1
        sample = generate(CURATED[0])
        if not sample.story.strip() or "parade" not in sample.story.lower():
            print("Story generation smoke test failed.")
            return 1
        if not sample.story_qa:
            print("Story QA smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: Python and ASP story checks passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    return sorted(asp.atoms(model, "outcome"))


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 50):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
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
