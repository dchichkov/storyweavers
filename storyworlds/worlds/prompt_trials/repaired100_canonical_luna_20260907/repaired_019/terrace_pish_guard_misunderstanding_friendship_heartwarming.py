#!/usr/bin/env python3
"""
A standalone heartwarming storyworld about a terrace guard, a small pish, and
a misunderstanding that becomes friendship.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Terrace:
    name: str
    plant: str
    light: str


@dataclass(frozen=True)
class Guard:
    name: str
    kind: str
    trait: str


@dataclass(frozen=True)
class Pish:
    name: str
    color: str
    habit: str


@dataclass(frozen=True)
class Arc:
    misunderstanding: str
    clue: str
    guard_action: str
    pish_action: str
    truth: str
    repair: str
    ending: str
    object: str


@dataclass
class StoryParams:
    guard_name: str
    guard_kind: str
    trait: str
    terrace: str
    pish_color: str
    seed: Optional[int] = None


TERRACES = {
    "sunny": Terrace("the sunny terrace", "marigolds", "golden"),
    "rainy": Terrace("the rain-washed terrace", "mint", "silver"),
    "moonlit": Terrace("the moonlit terrace", "jasmine", "blue"),
}

GUARD_KINDS = ["sparrow", "hedgehog", "rabbit", "cat", "turtle"]
TRAITS = ["careful", "watchful", "patient", "brave", "kind"]
PISH_COLORS = ["blue", "green", "yellow", "red", "violet"]

NAMES = {
    "sparrow": ["Luna", "Pip", "Mara"],
    "hedgehog": ["Brindle", "Nell", "Moss"],
    "rabbit": ["Luna", "Clover", "Tavi"],
    "cat": ["Mira", "Soot", "Pella"],
    "turtle": ["Luna", "Pebble", "Orrin"],
}

ARCS = [
    Arc(
        "Luna thought the pish was sneaking past the flower pots to steal the terrace bell",
        "a trail of damp footprints curved away from the bell and toward a cracked watering cup",
        "blocked the gate and called, “Stop there, little pish!”",
        "hid beneath a fern and made a tiny, worried “pish”",
        "the pish was carrying drops of water to a thirsty sparrow chick hidden behind the pots",
        "set a shallow dish beside the fern and moved the bell where it could be seen",
        "the pish drank from the new dish while Luna watched the flowers sparkle",
        "a little copper bell",
    ),
    Arc(
        "Luna believed the pish had tangled the terrace lantern cord on purpose",
        "one green thread led from the cord to a nest of fallen leaves beneath the bench",
        "held up a wing and asked the pish to wait",
        "pointed at the cord, then at the leaves, and shivered",
        "the pish had tried to pull the cord away from a cold nestling",
        "untangled the cord and tied a soft ribbon around the dangerous loop",
        "the lantern glowed above the nest, and the pish sat beside Luna in its warm circle",
        "a paper lantern",
    ),
    Arc(
        "Luna feared the pish was hiding the terrace keys",
        "three bright keys rested inside a pot of thyme, next to a line of crumbs",
        "searched the path but stopped before opening the pish’s tiny basket",
        "nudged the basket toward Luna and chirped twice",
        "the pish had carried the keys away from the drain where rainwater was rushing",
        "thanked the pish, dried the keys, and placed a safe key hook beside the door",
        "the pish helped hang the keys, and neither friend worried about them again",
        "a ring of silver keys",
    ),
    Arc(
        "Luna thought the pish was making the terrace gate squeak to frighten visitors",
        "soft bits of wool were caught in the gate hinge",
        "stood guard beside the hinge and spoke in a firm voice",
        "pulled one wool thread free, then pointed beneath the gate",
        "the pish had been trying to rescue a kitten’s scarf trapped in the hinge",
        "lifted the gate, freed the scarf, and oiled the hinge",
        "the gate opened quietly while the pish and Luna carried the scarf home together",
        "a striped scarf",
    ),
    Arc(
        "Luna suspected the pish had scattered the seed packets",
        "the packets lay in a neat trail from the shelf to a hole beneath the railing",
        "gathered the packets and asked who had moved them",
        "rolled one packet back and forth until its label faced Luna",
        "the pish had been showing Luna that rain was leaking through the shelf",
        "moved the seeds to a dry box and placed a small roof over the shelf",
        "new sprouts later filled the boxes, and Luna saved a corner for the pish’s favorite seeds",
        "three paper seed packets",
    ),
    Arc(
        "Luna thought the pish was refusing to obey the terrace rules",
        "the pish always stopped at the painted line but never crossed it",
        "knelt down and read the faded sign aloud",
        "tapped the sign where a missing word should have been",
        "the pish had not broken the rule; the rain had washed away the word “welcome”",
        "painted the missing word and added a picture of a friendly open gate",
        "the pish crossed the line, bowed, and became Luna’s cheerful afternoon helper",
        "a blue rule sign",
    ),
]

LESSONS = [
    "A guard protects best when a question comes before a judgment.",
    "Friendship can begin when two careful listeners discover the same truth.",
    "A small frightened sound may be asking for help, not causing trouble.",
    "Kindness leaves room for someone else’s story.",
]

OPENINGS = [
    "Every morning, Luna walked the terrace before the first kettle sang.",
    "The terrace was small, but Luna treated it like a whole little kingdom.",
    "At the edge of the building, flowers leaned over the terrace rail like curious neighbors.",
    "Luna loved the terrace because every pot, pebble, and railing had a place.",
]

DIALOGUES = [
    '"I thought you were causing trouble," {guard} said. "What were you trying to tell me?"',
    '"Pish," said the little creature. Luna softened. "I hear you now."',
    '"Wait," said {guard}. "Let us look together before we decide."',
    '"Are you guarding this place too?" {guard} asked. The pish gave a hopeful chirp.',
]


class World:
    def __init__(self, terrace: Terrace) -> None:
        self.terrace = terrace
        self.guard: Optional[Guard] = None
        self.pish: Optional[Pish] = None
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.meters = {"trust": 0.0, "tension": 0.0, "friendship": 0.0}
        self.memes = {"misunderstanding": 1.0, "belonging": 0.0, "relief": 0.0}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    if params.terrace not in TERRACES:
        raise StoryError(f"Unknown terrace: {params.terrace}")
    if params.guard_kind not in GUARD_KINDS:
        raise StoryError(f"Unknown guard kind: {params.guard_kind}")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait: {params.trait}")
    if params.pish_color not in PISH_COLORS:
        raise StoryError(f"Unknown pish color: {params.pish_color}")

    world = World(TERRACES[params.terrace])
    world.guard = Guard(params.guard_name, params.guard_kind, params.trait)
    world.pish = Pish(
        "Pish",
        params.pish_color,
        "a small creature with bright, listening eyes",
    )
    key = "|".join(
        [params.guard_name, params.guard_kind, params.trait, params.terrace, params.pish_color]
    )
    choice = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c) for i, c in enumerate(key)
    )
    world.facts["arc"] = ARCS[choice % len(ARCS)]
    world.facts["opening"] = OPENINGS[(choice // len(ARCS)) % len(OPENINGS)]
    world.facts["lesson"] = LESSONS[(choice // (len(ARCS) * len(OPENINGS))) % len(LESSONS)]
    world.facts["dialogue"] = DIALOGUES[(choice * 3 + choice // 7) % len(DIALOGUES)].format(
        guard=params.guard_name
    )
    return world


def notice_misunderstanding(world: World) -> None:
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    world.facts["problem"] = arc.misunderstanding
    world.meters["tension"] = 1.0
    world.say(f"{world.guard.name} noticed that {arc.misunderstanding}.")
    world.say(f"That seemed serious, but {arc.clue}.")
    world.memes["misunderstanding"] = 1.0


def guard_speaks(world: World) -> None:
    if "speak" in world.fired:
        return
    world.fired.add("speak")
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    world.say(arc.guard_action)
    world.say(world.facts["dialogue"])


def listen(world: World) -> None:
    if "listen" in world.fired:
        return
    world.fired.add("listen")
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    world.say(f"The pish {arc.pish_action}.")
    world.meters["trust"] += 1.0
    world.memes["misunderstanding"] = 0.0
    world.facts["heard"] = True


def discover_truth(world: World) -> None:
    if not world.facts.get("heard"):
        raise StoryError("The truth cannot be discovered before the guard listens.")
    if "truth" in world.fired:
        return
    world.fired.add("truth")
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    world.say(f"Then the truth became clear: {arc.truth}.")
    world.facts["truth"] = arc.truth


def make_repair(world: World) -> None:
    if not world.facts.get("truth"):
        raise StoryError("A friendship repair requires the truth to be understood.")
    if "repair" in world.fired:
        return
    world.fired.add("repair")
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    world.say(f"{world.guard.name} smiled and {arc.repair}.")
    world.meters["friendship"] = 1.0
    world.memes["belonging"] = 1.0
    world.memes["relief"] = 1.0


def conclude(world: World) -> None:
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    world.say(
        f"By sunset, {arc.ending}. {world.guard.name} and the pish had become friends, "
        f"not because they had never misunderstood one another, but because they had "
        f"taken time to listen."
    )
    world.say(world.facts["lesson"])


def tell_story(world: World) -> None:
    guard = world.guard
    pish = world.pish
    assert guard is not None and pish is not None
    terrace = world.terrace

    world.say(
        f"{world.facts['opening']} There lived a {guard.trait} {guard.kind} named "
        f"{guard.name}, who served as guard of {terrace.name}."
    )
    world.say(
        f"The terrace glowed {terrace.light} around its pots of {terrace.plant}. "
        f"A little {pish.color} pish often visited, though nobody knew why."
    )

    world.para()
    notice_misunderstanding(world)
    guard_speaks(world)

    world.para()
    listen(world)
    discover_truth(world)
    make_repair(world)

    world.para()
    conclude(world)

    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    world.facts.update(
        guard=guard,
        pish=pish,
        terrace=terrace,
        object=arc.object,
        ending=arc.ending,
        friendship=True,
    )


def generation_prompts(world: World) -> list[str]:
    guard: Guard = world.facts["guard"]  # type: ignore[assignment]
    pish: Pish = world.facts["pish"]  # type: ignore[assignment]
    terrace: Terrace = world.facts["terrace"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about {guard.name}, a terrace guard, and a {pish.color} pish.",
        f"Tell a child-friendly misunderstanding story on {terrace.name} that becomes a friendship.",
        f"Write a gentle tale where a guard listens to a pish before deciding what happened.",
    ]


def story_qa(world: World) -> list[QAItem]:
    guard: Guard = world.facts["guard"]  # type: ignore[assignment]
    terrace: Terrace = world.facts["terrace"]  # type: ignore[assignment]
    arc: Arc = world.facts["arc"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What misunderstanding did {guard.name} have on {terrace.name}?",
            f"{guard.name} thought that {arc.misunderstanding}. The clue was that {arc.clue}.",
        ),
        QAItem(
            f"What did {guard.name} learn by listening to the pish?",
            f"{guard.name} learned that {arc.truth}. Listening changed the guard's first judgment.",
        ),
        QAItem(
            f"How did the misunderstanding become friendship?",
            f"{guard.name} repaired the problem when {arc.repair}. After that, {arc.ending}.",
        ),
        QAItem(
            "What object helped show what changed?",
            f"The important object was {arc.object}. At the end, it was part of a safer, kinder terrace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a terrace?",
            "A terrace is an outdoor platform or balcony where people can walk, rest, or grow plants.",
        ),
        QAItem(
            "What does a guard do?",
            "A guard watches over a place and helps keep it safe.",
        ),
        QAItem(
            "Why can misunderstandings happen?",
            "Misunderstandings happen when someone does not yet know the full reason behind another person's actions.",
        ),
        QAItem(
            "How can friendship grow after a misunderstanding?",
            "Friendship can grow when people speak kindly, listen carefully, learn the truth, and make things right together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    guard = world.guard
    pish = world.pish
    return "\n".join(
        [
            "--- world model state ---",
            f"terrace={world.terrace.name}",
            f"guard={guard.name} ({guard.kind}, {guard.trait})",
            f"pish={pish.name} ({pish.color})",
            f"misunderstanding={world.memes['misunderstanding']}",
            f"trust={world.meters['trust']}",
            f"friendship={world.meters['friendship']}",
            f"truth={world.facts.get('truth')}",
            f"fired={sorted(world.fired)}",
        ]
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (terrace, kind, trait, color)
        for terrace in TERRACES
        for kind in GUARD_KINDS
        for trait in TRAITS
        for color in PISH_COLORS
    ]


ASP_RULES = r"""
terrace(T) :- terrace_name(T).
guard_kind(K) :- guard_kind_name(K).
trait(R) :- trait_name(R).
pish_color(C) :- pish_color_name(C).
valid(T,K,R,C) :- terrace(T), guard_kind(K), trait(R), pish_color(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.extend(asp.fact("terrace_name", value) for value in TERRACES)
    lines.extend(asp.fact("guard_kind_name", value) for value in GUARD_KINDS)
    lines.extend(asp.fact("trait_name", value) for value in TRAITS)
    lines.extend(asp.fact("pish_color_name", value) for value in PISH_COLORS)
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP valid combinations.")
    return 1


@dataclass
class _Args:
    terrace: Optional[str] = None
    kind: Optional[str] = None
    trait: Optional[str] = None
    color: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


CURATED = [
    StoryParams("Luna", "sparrow", "careful", "sunny", "blue"),
    StoryParams("Mira", "cat", "patient", "rainy", "green"),
    StoryParams("Clover", "rabbit", "kind", "moonlit", "yellow"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming terrace story about a guard, a pish, and friendship."
    )
    parser.add_argument("--terrace", choices=list(TERRACES))
    parser.add_argument("--kind", choices=GUARD_KINDS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--color", choices=PISH_COLORS)
    parser.add_argument("--name")
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
    kind = args.kind or rng.choice(GUARD_KINDS)
    return StoryParams(
        guard_name=args.name or rng.choice(NAMES[kind]),
        guard_kind=kind,
        trait=args.trait or rng.choice(TRAITS),
        terrace=args.terrace or rng.choice(list(TERRACES)),
        pish_color=args.color or rng.choice(PISH_COLORS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:\n")
        for combo in combos:
            print("  " + " ".join(str(part) for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < target * 100:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            params = sample.params
            header = (
                f"### {params.guard_name}: {params.guard_kind} guarding "
                f"{params.terrace} terrace"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
