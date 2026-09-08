#!/usr/bin/env python3
"""
A standalone fairy-tale storyworld about dough, a surprising twist, sharing,
and a lesson learned.
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


@dataclass
class Character:
    name: str
    kind: str
    trait: str
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Kitchen:
    name: str
    warmth: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Dough:
    flour: str = "golden flour"
    shape: str = "a round loaf"
    risen: bool = False
    shared: bool = False
    ready: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class TaleArc:
    gift: str
    trouble: str
    twist: str
    clue: str
    action: str
    sharing: str
    ending: str
    lesson: str
    companion: str


@dataclass
class StoryParams:
    name: str
    kind: str
    trait: str
    kitchen: str
    flour: str
    seed: Optional[int] = None


KITCHENS = {
    "cottage": Kitchen("the little cottage kitchen", "hearth-warm"),
    "tower": Kitchen("the moonlit tower kitchen", "silver-warm"),
    "forest": Kitchen("the fern-ringed forest kitchen", "moss-warm"),
}

KINDS = ["girl", "boy", "rabbit", "fox", "mouse"]
TRAITS = ["kind", "patient", "curious", "brave", "generous"]
FLOURS = {
    "wheat": "golden wheat flour",
    "oat": "soft oat flour",
    "rye": "dark rye flour",
}
NAMES = {
    "girl": ["Luna", "Mara", "Elsa"],
    "boy": ["Finn", "Theo", "Pip"],
    "rabbit": ["Clover", "Bram", "Tilly"],
    "fox": ["Fenn", "Russet", "Mira"],
    "mouse": ["Nim", "Pella", "Moss"],
}

ARCS = [
    TaleArc(
        gift="a basket of warm rolls for the village feast",
        trouble="the dough would not rise, no matter how gently it was covered",
        twist="a tiny silver bell appeared in the middle of the dough",
        clue="the bell rang only when someone nearby felt lonely",
        action="invited the hungry forest creatures to knead the dough together",
        sharing="broke the risen loaf into a piece for every creature who had helped",
        ending="the last roll glowed softly in the hands of an old owl",
        lesson="a gift grows when lonely hearts are welcomed into its making",
        companion="an old owl",
    ),
    TaleArc(
        gift="one enormous loaf for the queen's table",
        trouble="the dough stretched toward the locked pantry instead of resting in its bowl",
        twist="it shaped itself into a golden road beneath the kitchen door",
        clue="the road stopped at every house with an empty cupboard",
        action="followed the dough and carried flour to each empty cupboard",
        sharing="cut the great loaf into warm rounds for every family",
        ending="the queen placed her crown beside the final shared crust",
        lesson="bread meant only for one table becomes smaller than bread carried to many",
        companion="the queen",
    ),
    TaleArc(
        gift="a moon-shaped cake for the village children",
        trouble="the dough turned cold and gray before it could be baked",
        twist="when Luna sang to it, the dough began to whisper names",
        clue="it whispered the names of children who had no supper",
        action="asked each named child to add one pinch of flour and one kind wish",
        sharing="served the cake in shining slices beneath the moon",
        ending="every child found a bright crumb in their palm",
        lesson="kindness can warm even a cold beginning",
        companion="a shy child from the mill",
    ),
    TaleArc(
        gift="sweet buns for a traveling baker",
        trouble="the dough divided itself into many tiny balls and rolled away",
        twist="each ball carried a different colored seed",
        clue="the seeds matched flowers growing where the baker had once helped others",
        action="gathered the dough and planted the seeds beside the road",
        sharing="gave each traveler a bun and a promise to tend one flower",
        ending="the road bloomed with flowers and crumbs",
        lesson="what we share may return as a path of beauty",
        companion="a traveling baker",
    ),
    TaleArc(
        gift="a braided loaf to mend a quarrel between two sisters",
        trouble="the dough pulled into two ropes whenever the sisters tugged at it",
        twist="the ropes braided themselves when the sisters stopped arguing",
        clue="the dough held firm only when both sisters held one end",
        action="asked the sisters to knead in the same rhythm",
        sharing="let the sisters divide the braided loaf evenly",
        ending="the sisters laughed when the final braid stayed together",
        lesson="some knots loosen when hands work together instead of pulling apart",
        companion="two quarrelling sisters",
    ),
    TaleArc(
        gift="a small loaf for a dragon who guarded the hill",
        trouble="the dough puffed up whenever anyone spoke boastfully",
        twist="it became tiny whenever someone said, 'I need no one'",
        clue="it rose highest after a quiet thank-you",
        action="invited the dragon to name the helpers who had carried water and wood",
        sharing="served the loaf around the fire, beginning with the dragon",
        ending="the dragon guarded the village oven instead of the lonely hill",
        lesson="being thankful gives a small kindness room to grow",
        companion="a young dragon",
    ),
]

OPENINGS = [
    "Once upon a gentle morning,",
    "Long ago, when ovens still listened to wishes,",
    "In a kingdom tucked between three green hills,",
    "At the edge of an enchanted wood,",
    "On a day bright enough to wake the fairies,",
]

DIALOGUES = [
    ('"The dough is telling us something," {name} said. "Let us listen before we bake."',
     '"Perhaps it is telling us to help one another," {companion} replied.'),
    ('"I thought this loaf was mine to finish," {name} admitted.',
     '"A loaf can have many hands and still have one heart," {companion} said.'),
    ('"What if the strange part is not a mistake?" {name} asked.',
     '"Then we must discover whom it is trying to help," {companion} answered.'),
    ('"I cannot solve this twist alone," {name} said.',
     '"Good," {companion} replied. "That means there is room for all of us."'),
]

CURATED = [
    StoryParams("Luna", "girl", "kind", "cottage", "wheat"),
    StoryParams("Clover", "rabbit", "generous", "forest", "oat"),
    StoryParams("Finn", "boy", "curious", "tower", "rye"),
    StoryParams("Mara", "fox", "patient", "cottage", "wheat"),
]


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.hero: Optional[Character] = None
        self.dough = Dough()
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.dough.meters = {"softness": 0.5, "warmth": 0.0, "readiness": 0.0}
        self.dough.memes = {"hope": 0.0, "belonging": 0.0, "generosity": 0.0}

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def valid_params(params: StoryParams) -> None:
    if params.kitchen not in KITCHENS:
        raise StoryError(f"Unknown kitchen: {params.kitchen}")
    if params.kind not in KINDS:
        raise StoryError(f"Unknown kind: {params.kind}")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait: {params.trait}")
    if params.flour not in FLOURS:
        raise StoryError(f"Unknown flour: {params.flour}")
    if not params.name.strip():
        raise StoryError("A story hero needs a name.")


def build_world(params: StoryParams) -> World:
    valid_params(params)
    world = World(KITCHENS[params.kitchen])
    world.hero = Character(params.name, params.kind, params.trait)
    world.dough.flour = FLOURS[params.flour]
    value = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c) for i, c in enumerate(
            f"{params.name}|{params.kind}|{params.trait}|{params.kitchen}|{params.flour}"
        )
    )
    arc = ARCS[value % len(ARCS)]
    opening = OPENINGS[(value // len(ARCS)) % len(OPENINGS)]
    dialogue = DIALOGUES[(value * 3 + value // 7) % len(DIALOGUES)]
    world.facts.update(
        arc=arc,
        opening=opening,
        dialogue=dialogue,
        resolved=False,
    )
    return world


def make_dough(world: World) -> None:
    if "make" in world.fired:
        return
    world.fired.add("make")
    hero = world.hero
    world.say(
        f"{hero.name} mixed {world.dough.flour} with clear water and a pinch of salt. "
        f"The dough felt soft beneath {hero.name}'s hands, but it carried a quiet shiver."
    )
    world.dough.meters["softness"] = 1.0
    world.dough.memes["hope"] = 0.5


def face_trouble(world: World) -> None:
    if "trouble" in world.fired:
        return
    world.fired.add("trouble")
    arc: TaleArc = world.facts["arc"]
    world.say(f"Yet {arc.trouble.capitalize()}.")
    world.dough.meters["warmth"] = 0.0


def reveal_twist(world: World) -> None:
    if "twist" in world.fired:
        return
    world.fired.add("twist")
    arc: TaleArc = world.facts["arc"]
    world.say(f"Then came the twist: {arc.twist.capitalize()}.")
    world.say(f"{arc.clue.capitalize()}.")
    world.dough.memes["belonging"] = 0.5


def share_and_solve(world: World) -> None:
    if "solve" in world.fired:
        return
    if "twist" not in world.fired:
        raise StoryError("The dough's twist must be understood before sharing.")
    world.fired.add("solve")
    hero = world.hero
    arc: TaleArc = world.facts["arc"]
    first, second = world.facts["dialogue"]
    world.say(first.format(name=hero.name, companion=arc.companion))
    world.say(second.format(name=hero.name, companion=arc.companion))
    world.say(f"So {hero.name} {arc.action}.")
    world.say(f"The dough warmed, rose, and became ready. {hero.name} {arc.sharing}.")
    world.dough.risen = True
    world.dough.ready = True
    world.dough.shared = True
    world.dough.meters["warmth"] = 1.0
    world.dough.meters["readiness"] = 1.0
    world.dough.memes["belonging"] = 1.0
    world.dough.memes["generosity"] = 1.0
    world.facts["resolved"] = True


def conclude(world: World) -> None:
    arc: TaleArc = world.facts["arc"]
    hero = world.hero
    if not world.facts["resolved"]:
        raise StoryError("A fairy tale about sharing needs a resolved sharing action.")
    world.say(
        f"When the feast was done, {arc.ending.capitalize()}. "
        f"{hero.name} remembered the lesson learned: {arc.lesson}."
    )


def tell_story(world: World) -> None:
    hero = world.hero
    arc: TaleArc = world.facts["arc"]
    world.say(
        f"{world.facts['opening']} in {world.kitchen.name} lived a {hero.trait} "
        f"{hero.kind} named {hero.name}."
    )
    world.say(
        f"One morning, {hero.name} decided to make {arc.gift}. "
        f"The hearth glimmered, and even the wooden spoon seemed eager to help."
    )
    world.para()
    make_dough(world)
    face_trouble(world)
    reveal_twist(world)
    world.para()
    share_and_solve(world)
    world.para()
    conclude(world)
    world.facts.update(
        hero=hero,
        kitchen=world.kitchen,
        flour=world.dough.flour,
        twist=arc.twist,
        clue=arc.clue,
        trouble=arc.trouble,
        sharing=arc.sharing,
        ending=arc.ending,
        lesson=arc.lesson,
        companion=arc.companion,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a fairy tale about {f['hero'].name} making dough in {f['kitchen'].name}.",
        f"Include this twist: {f['twist']}.",
        f"Show how sharing solves the trouble and ends with the lesson: {f['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            f"What trouble did {hero.name} face with the dough?",
            f"{hero.name} faced this trouble: {f['trouble']}.",
        ),
        QAItem(
            "What was the twist in the fairy tale?",
            f"The twist was that {f['twist']}. The clue was that {f['clue']}.",
        ),
        QAItem(
            f"How did {hero.name} use sharing to solve the problem?",
            f"{hero.name} {f['sharing']}. Sharing made the dough warm, ready, and full of belonging.",
        ),
        QAItem(
            "What lesson was learned?",
            f"The lesson learned was that {f['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is dough?",
            "Dough is a soft mixture, often made from flour and water, that can be shaped and baked.",
        ),
        QAItem(
            "Why does bread dough rise?",
            "Bread dough rises when trapped air or gas makes the mixture puff up before baking.",
        ),
        QAItem(
            "What does sharing mean?",
            "Sharing means giving part of what you have so that other people can enjoy or use it too.",
        ),
        QAItem(
            "What is a lesson learned in a story?",
            "A lesson learned is an understanding gained from what happened in the story.",
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
    return "\n".join(
        [
            "--- world model state ---",
            f"kitchen={world.kitchen.name}",
            f"hero={world.hero.name} ({world.hero.kind}, {world.hero.trait})",
            f"dough.flour={world.dough.flour}",
            f"dough.risen={world.dough.risen}",
            f"dough.shared={world.dough.shared}",
            f"dough.ready={world.dough.ready}",
            f"dough.meters={world.dough.meters}",
            f"dough.memes={world.dough.memes}",
            f"fired={sorted(world.fired)}",
        ]
    )


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (kitchen, kind, flour)
        for kitchen in KITCHENS
        for kind in KINDS
        for flour in FLOURS
    ]


ASP_RULES = r"""
kitchen(K) :- kitchen_name(K).
kind(K) :- kind_name(K).
flour(F) :- flour_name(F).
valid(K, T, F) :- kitchen(K), kind(T), flour(F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in KITCHENS:
        lines.append(asp.fact("kitchen_name", value))
    for value in KINDS:
        lines.append(asp.fact("kind_name", value))
    for value in FLOURS:
        lines.append(asp.fact("flour_name", value))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP.")
    print("Only in Python:", sorted(py - cl))
    print("Only in ASP:", sorted(cl - py))
    return 1


@dataclass
class _Args:
    kitchen: Optional[str] = None
    kind: Optional[str] = None
    trait: Optional[str] = None
    flour: Optional[str] = None
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy-tale storyworld about dough, sharing, and a lesson learned."
    )
    parser.add_argument("--kitchen", choices=list(KITCHENS))
    parser.add_argument("--kind", choices=KINDS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--flour", choices=list(FLOURS))
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
    kind = args.kind or rng.choice(KINDS)
    return StoryParams(
        name=args.name or rng.choice(NAMES[kind]),
        kind=kind,
        trait=args.trait or rng.choice(TRAITS),
        kitchen=args.kitchen or rng.choice(list(KITCHENS)),
        flour=args.flour or rng.choice(list(FLOURS)),
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
        sys.exit(asp_verify())
    if args.asp:
        for kitchen, kind, flour in asp_valid_combos():
            print(f"{kitchen:8} {kind:8} {flour}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
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
        params = sample.params
        header = ""
        if args.all:
            header = f"### {params.name}: dough tale in {params.kitchen}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
