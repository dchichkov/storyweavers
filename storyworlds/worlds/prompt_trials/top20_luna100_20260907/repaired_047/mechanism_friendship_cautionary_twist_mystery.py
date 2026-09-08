#!/usr/bin/env python3
"""
A standalone mystery storyworld about a small mechanism, friendship, and a
cautionary twist.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
mystery_world(W) :- setting(W), has_friendship(W), has_caution(W), has_twist(W).
safe_mechanism(M) :- mechanism(M), checked(M), guarded(M).
solved(W) :- mystery_world(W), safe_mechanism(M), uses(W,M), clue_found(W).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    friend: str
    mechanism: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    opening: str
    trouble: str
    first_clue: str
    friend_line: str
    false_answer: str
    twist: str
    repair: str
    result: str
    ending: str
    caution: str


@dataclass
class World:
    place: str = "the old observatory"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            details = []
            if entity.meters:
                details.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                details.append(f"memes={dict(entity.memes)}")
            if entity.label:
                details.append(f"label={entity.label!r}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) {' '.join(details)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


NAMES = ["Luna", "Mira", "Theo", "Nia", "Arlo", "Suri", "Juno", "Pip"]
FRIENDS = [
    "her friend Rowan",
    "her friend Bea",
    "her friend Milo",
    "her friend Kiko",
    "her friend Tavi",
]
MECHANISMS = ["brass compass", "moon-key", "clockwork bird", "star wheel"]

SCENARIOS = [
    Scenario(
        key="silent_compass",
        opening="Luna and her friend were cataloging the observatory's forgotten instruments.",
        trouble="The brass compass began spinning although every window was closed.",
        first_clue="a thread of blue dust lay beneath its glass",
        friend_line='"The dust is pointing somewhere, not merely blowing around," the friend said.',
        false_answer="Luna guessed that a hidden magnet was pulling the needle.",
        twist="When they lifted the compass, its needle pointed not north but toward a loose floor tile.",
        repair="they marked the safe path, lifted the tile with a wooden ruler, and found a tiny signal mirror below it",
        result="The mirror explained the blue flash that had been appearing on the far hill each night.",
        ending="the compass rested quietly beside the mirror while two friends watched the hill answer with one last glimmer",
        caution="a strange tool should be observed before it is forced to obey",
    ),
    Scenario(
        key="locked_telescope",
        opening="Luna and her friend were preparing the old telescope for a midnight mystery.",
        trouble="The telescope locked itself whenever they aimed it at the dark western roof.",
        first_clue="three fresh scratches curved around the brass turning ring",
        friend_line='"Those scratches look like a warning," the friend whispered.',
        false_answer="Luna tried turning the ring harder and heard a worrying click.",
        twist="A hidden catch released only when the telescope was pointed away from the roof.",
        repair="they backed away, loosened the catch with a soft brush, and examined the roof through a side mirror",
        result="The mirror revealed a nest resting over the roof hatch, where a curious owl had trapped a ribbon.",
        ending="the telescope opened again, but the friends left the owl's quiet nest undisturbed",
        caution="a locked mechanism may be protecting something rather than hiding it",
    ),
    Scenario(
        key="clockwork_message",
        opening="Luna and her friend found a clockwork bird beneath a dusty star chart.",
        trouble="The bird repeated one note and refused to open its little beak.",
        first_clue="a minute gear carried a smear of green paint",
        friend_line='"The paint matches the garden door," the friend said.',
        false_answer="Luna poked the gear with a pin, which made the bird jerk and stop.",
        twist="The green paint was not a mark from the garden; it was a trail left by a loose spring.",
        repair="they covered the bird, moved it away from the edge, and reset the spring with a blunt wooden tool",
        result="The bird opened its beak and dropped a folded map of the observatory.",
        ending="the map led them to a sunny shelf where the repaired bird sang its full little song",
        caution="a small mechanism can hold a large clue, so careless poking can destroy the message",
    ),
    Scenario(
        key="moon_key",
        opening="Luna and her friend were searching the observatory archives for a missing moon-key.",
        trouble="The key-shaped mechanism appeared inside the archive box, then vanished whenever the lid opened.",
        first_clue="a silver crescent stayed warm on the underside of the lid",
        friend_line='"Let us watch the shadow instead of chasing the key," the friend said.',
        false_answer="Luna reached quickly into the box and scattered the papers.",
        twist="The crescent was a spring-loaded mirror that made the key look invisible from one angle.",
        repair="they held the lid still, changed the lamp's position, and retrieved the key with a cloth",
        result="The key opened a narrow drawer containing the observatory's lost visitor book.",
        ending="their names joined the old book beneath a careful note about the tricky mirror",
        caution="a mystery can change when the light changes, so rushing toward an answer is risky",
    ),
    Scenario(
        key="star_wheel",
        opening="Luna and her friend were dusting a star wheel in the observatory dome.",
        trouble="The wheel clicked twelve times every hour even though its hands had stopped.",
        first_clue="one star-shaped notch was brighter than all the others",
        friend_line='"The bright notch is a doorway for the clue," the friend said.',
        false_answer="Luna pressed the notch, and a panel above them swung open.",
        twist="The panel was not a secret door but a counterweight that could make the dome roll.",
        repair="they stepped back, secured the wheel, and used a long ribbon to pull the panel closed",
        result="Behind the counterweight they found a missing brass label, not treasure.",
        ending="the star wheel ticked safely while the friends returned the label to its patient place",
        caution="a promising button may move something much larger than expected",
    ),
]

OPENINGS = [
    "Rain tapped the observatory roof when {name} entered with a small lantern.",
    "At dusk, {name} found the old observatory door standing open.",
    "The observatory had been quiet for years, until {name} heard a careful click inside.",
    "Moonlight crossed the observatory floor as {name} arrived to meet a friend.",
    "A cold wind carried one mysterious chime through the observatory.",
]

REACTIONS = [
    "{name} held up a hand. It was better to notice the pattern before touching anything else.",
    '"We can be brave without being hasty," {name} said.',
    "{name} took a slow step back and invited the friend to inspect the device too.",
    '"Every good mystery leaves a clue, but not every clue tells the whole truth," {name} murmured.',
]

PLANS = [
    "They placed the lantern on the floor, sketched what they saw, and agreed on one safe test.",
    "They kept their hands still while one friend watched the mechanism and the other watched the room.",
    "They marked the original position of every piece before trying the smallest possible change.",
    "They checked the exits, moved fragile objects away, and then compared the clues aloud.",
]

NAMES_FOR_MECHANISMS = {
    "brass compass": "compass",
    "moon-key": "key",
    "clockwork bird": "bird",
    "star wheel": "wheel",
}


def valid_mechanism_choices() -> list[str]:
    return list(MECHANISMS)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The mystery needs a named investigator.")
    if not params.friend.strip():
        raise StoryError("The investigator needs a friend to share clues with.")
    if params.mechanism not in valid_mechanism_choices():
        raise StoryError("The mechanism must be a small, harmless observatory device.")


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        friend=rng.choice(FRIENDS),
        mechanism=rng.choice(MECHANISMS),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mystery storyworld about a mechanism and friendship."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--mechanism", choices=valid_mechanism_choices())
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
    params = valid_params(rng)
    if args.name:
        params.name = args.name
    if args.friend:
        params.friend = args.friend
    if args.mechanism:
        params.mechanism = args.mechanism
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity("hero", "character", params.name))
    world.add(Entity("friend", "character", params.friend))
    world.add(Entity("mechanism", "mechanism", params.mechanism, owner="observatory"))
    world.add(Entity("lantern", "tool", "small lantern"))
    world.facts.update(
        setting="old observatory",
        friendship=True,
        caution=True,
        twist=True,
        mechanism=params.mechanism,
        uses=False,
        clue_found=False,
        checked=False,
        guarded=False,
        solved=False,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    hero = world.get("hero")
    friend = world.get("friend")
    mechanism = world.get("mechanism")
    lantern = world.get("lantern")

    hero.bump_meme("curiosity")
    friend.bump_meme("friendship")
    mechanism.bump_meter("mystery", 1)

    world.say(rng.choice(OPENINGS).format(name=hero.label))
    world.say(
        f"{scenario.opening} The {mechanism.label} waited on a stone table, "
        f"and {hero.label} invited {friend.label} to investigate it together."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(f"At first, {scenario.false_answer}")
    world.say(rng.choice(REACTIONS).format(name=hero.label))
    world.say(f"Then they noticed the first useful clue: {scenario.first_clue}.")
    world.say(scenario.friend_line)
    world.para()

    friend.bump_meme("courage")
    hero.bump_meme("trust")
    world.facts["clue_found"] = True
    world.say(rng.choice(PLANS))
    world.say(
        f"{hero.label} placed the {lantern.label} where both friends could see, "
        f"while {friend.label} watched the {mechanism.label} without touching it."
    )
    world.say(f"Together, they discovered the twist: {scenario.twist}")
    world.para()

    mechanism.bump_meter("checked", 1)
    mechanism.bump_meter("handled_carefully", 1)
    world.facts["checked"] = True
    world.say(f"With patient hands, {scenario.repair}.")
    world.facts["uses"] = True
    world.say(scenario.result)
    world.para()

    world.facts["guarded"] = True
    world.facts["solved"] = True
    hero.bump_meme("relief")
    friend.bump_meme("relief")
    world.say(
        f"{hero.label} and {friend.label} smiled, because the answer belonged to both of them."
    )
    world.say(f"They remembered that {scenario.caution}.")
    world.say(f"As the mystery ended, {scenario.ending}")
    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        first_clue=scenario.first_clue,
        false_answer=scenario.false_answer,
        twist=scenario.twist,
        repair=scenario.repair,
        result=scenario.result,
        caution=scenario.caution,
        ending=scenario.ending,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly mystery in an old observatory where {facts['hero'].label} and {facts['friend'].label} investigate a {facts['mechanism']}.",
        "Write a cautionary friendship mystery in which a mechanism gives a misleading first clue and has a surprising twist.",
        f"Tell a gentle mystery about two friends who solve a mechanism puzzle by observing carefully instead of forcing it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    friend = facts["friend"].label
    mechanism = facts["mechanism"]
    return [
        QAItem(
            question=f"What mystery did {hero} and {friend} investigate?",
            answer=f"They investigated the {mechanism}: {facts['trouble']}",
        ),
        QAItem(
            question="What was the first important clue?",
            answer=f"The first clue was that {facts['first_clue']}.",
        ),
        QAItem(
            question=f"What twist did {hero} and {friend} discover about the {mechanism}?",
            answer=f"They discovered that {facts['twist']}.",
        ),
        QAItem(
            question="How did the friends solve the mystery safely?",
            answer=f"They solved it when {facts['repair']}.",
        ),
        QAItem(
            question="What caution did the mystery teach?",
            answer=f"It taught them that {facts['caution']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a group of parts that work together to make something move or perform a task.",
        ),
        QAItem(
            question="Why is friendship useful during a mystery?",
            answer="Friendship is useful because friends can share clues, notice different details, and remind one another to stay safe.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means thinking carefully and acting safely before touching or changing something unknown.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprising change that makes an earlier clue or guess mean something different.",
        ),
    ]


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "observatory"),
            asp.fact("has_friendship", "observatory"),
            asp.fact("has_caution", "observatory"),
            asp.fact("has_twist", "observatory"),
            asp.fact("mechanism", "compass"),
            asp.fact("mechanism", "key"),
            asp.fact("mechanism", "bird"),
            asp.fact("mechanism", "wheel"),
            asp.fact("checked", "compass"),
            asp.fact("checked", "key"),
            asp.fact("checked", "bird"),
            asp.fact("checked", "wheel"),
            asp.fact("guarded", "compass"),
            asp.fact("guarded", "key"),
            asp.fact("guarded", "bird"),
            asp.fact("guarded", "wheel"),
            asp.fact("uses", "observatory", "compass"),
            asp.fact("clue_found", "observatory"),
        ]
    )


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show mystery_world/1.\n#show safe_mechanism/1.\n#show solved/1."
    )
    model = asp.one_model(program)
    actual = {
        (symbol.name, tuple(asp_value(arg) for arg in symbol.arguments))
        for symbol in model
        if symbol.name in {"mystery_world", "safe_mechanism", "solved"}
    }
    expected = {
        ("mystery_world", ("observatory",)),
        ("safe_mechanism", ("compass",)),
        ("safe_mechanism", ("key",)),
        ("safe_mechanism", ("bird",)),
        ("safe_mechanism", ("wheel",)),
        ("solved", ("observatory",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python reasonableness model.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    rng = random.Random(17)
    for _ in range(5):
        sample = generate(valid_params(rng))
        if not sample.world or not sample.world.facts["solved"]:
            print("MISMATCH: generated story did not resolve.")
            return 1
        if not sample.story or len(sample.story_qa) < 3:
            print("MISMATCH: generated story lacked required content.")
            return 1

    print("OK: ASP twin matches the Python gate and generated stories resolve.")
    return 0


def asp_value(symbol) -> object:
    import clingo

    if symbol.type == clingo.SymbolType.Number:
        return symbol.number
    if symbol.type == clingo.SymbolType.String:
        return symbol.string
    return symbol.name


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show solved/1."))
    return sorted(asp.atoms(model, "solved"))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "her friend Rowan", "brass compass", 11),
    StoryParams("Mira", "her friend Bea", "moon-key", 29),
    StoryParams("Theo", "her friend Milo", "clockwork bird", 47),
    StoryParams("Nia", "her friend Kiko", "star wheel", 71),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        print("ASP-compatible observatory mystery facts:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            attempts += 1
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
