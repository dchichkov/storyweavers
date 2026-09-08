#!/usr/bin/env python3
"""
A standalone heartwarming parade storyworld about a sailor, infantry friends,
and a surprising twist.
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
parade_story(S) :- setting(S), has_sailor(S), has_infantry(S), has_twist(S).
kind_twist(S) :- parade_story(S), shared_care(S), happy_ending(S).
ready(S) :- parade_story(S), repaired(S).
"""

PLACE = "harbor parade"


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
    sailor: str
    infantry: str
    signal: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    beginning: str
    trouble: str
    first_try: str
    clue: str
    sailor_line: str
    twist: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    place: str = PLACE
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


SCENARIOS = [
    Scenario(
        key="quiet_drum",
        beginning="was polishing the harbor bell before the town's bright parade",
        trouble="The infantry drum lost its deep voice just as the marching line reached the pier.",
        first_try="tapping harder made only a thin rattle",
        clue="a small rope knot had slipped beneath the drum's rim",
        sailor_line='"A drum needs a steady skin and a steady friend," the sailor said.',
        twist="Then the sailor revealed that the old drum had once belonged to his own little parade band.",
        repair="held the drum steady while the infantry untied the knot and tightened the rim",
        result="Its warm boom rolled across the harbor and gave every marcher the same proud step.",
        ending="the sailor marched beside the infantry while the rescued drum welcomed the boats home",
    ),
    Scenario(
        key="missing_flag",
        beginning="was helping the town prepare flags along the sunny quay",
        trouble="The largest parade flag vanished before the infantry could lead the procession.",
        first_try="searching the storage shed uncovered only empty poles and tangled string",
        clue="a trail of blue cloth fluttered toward the sailor's small boat",
        sailor_line='"The wind may have chosen a new flag bearer," the sailor joked.',
        twist="Inside the boat they found the missing flag wrapped around a tiny rescue mast, sheltering a lost seabird.",
        repair="freed the flag gently, carried the bird to a warm basket, and fixed the cloth to its proper pole",
        result="The flag flew above the parade, while the rescued bird rested safely with the harbor keeper.",
        ending="the blue flag waved over the smiling marchers as the little bird watched from a sunny perch",
    ),
    Scenario(
        key="backward_route",
        beginning="was checking the parade route beside the old lighthouse",
        trouble="A fallen market sign blocked the turn where the sailor and infantry were meant to pass.",
        first_try="pushing from one side left the heavy sign wedged against a cart",
        clue="the sign had wheels hidden beneath its painted base",
        sailor_line='"Some things move best when we change direction," the sailor said.',
        twist="The sailor recognized the sign as the town's first parade float, saved years ago by his grandmother.",
        repair="lifted one corner, rolled the sign backward, and guided the infantry through the open lane",
        result="The old sign became a welcome arch instead of an obstacle.",
        ending="the parade passed beneath the painted arch while the sailor saluted his grandmother's memory",
    ),
    Scenario(
        key="rainy_ribbons",
        beginning="was tying cheerful ribbons to the railings before the harbor parade",
        trouble="A sudden shower soaked the ribbons and made the infantry's route look gray.",
        first_try="wringing them out left the colors drooping in the wet air",
        clue="the sailor's cabin had a row of warm brass hooks beneath its roof",
        sailor_line='"A little shelter can make bright colors brave again," the sailor said.',
        twist="The cabin's old signal cloths turned out to match the town colors perfectly.",
        repair="hung the ribbons beside the signal cloths, dried them, and shared the cabin's shelter",
        result="The parade returned with bright streamers and a new place for everyone to warm up.",
        ending="rain tapped the roof while red and gold ribbons glowed beside the sailor's signal cloths",
    ),
    Scenario(
        key="smallest_step",
        beginning="was practicing the opening march with the infantry near the harbor clock",
        trouble="A young marcher could not keep pace because one bootlace kept coming loose.",
        first_try="pulling the knot tighter made the lace pinch the child's foot",
        clue="the sailor noticed a smooth loop hidden inside the old knot",
        sailor_line='"A good march leaves room for every foot," the sailor said.',
        twist="The sailor had learned the same knot from a child who once helped him find his way home.",
        repair="retied the bootlace softly, shortened the loose end, and practiced the first steps together",
        result="The young marcher found a comfortable rhythm and led the smallest row.",
        ending="the child took the first parade step while the sailor and infantry followed with proud smiles",
    ),
    Scenario(
        key="empty_chair",
        beginning="was placing chairs for families who would watch the parade from the quay",
        trouble="One chair remained empty beside the sailor's old shipmate's name card.",
        first_try="moving the chair away made the row look neat but left a lonely space",
        clue="the infantry carried a folded blanket marked with the same name",
        sailor_line='"That chair is waiting for a story, not only a guest," the sailor said.',
        twist="The missing shipmate had asked the infantry to keep the place for the sailor's granddaughter.",
        repair="set the blanket on the chair, invited the child forward, and saved room beside the sailor",
        result="The empty place became a welcome seat filled with family memories.",
        ending="the child sat beneath the name card as the parade passed, carrying an old friendship forward",
    ),
]


NAMES = ["Luna", "Mira", "Theo", "Nell", "Arlo", "Pia", "Sam", "Iris"]
SAILORS = ["Captain Rowan", "Sailor Bea", "Mateo", "Sailor June", "Captain Sol"]
INFANTRY = ["the harbor infantry", "the young infantry", "the visiting infantry"]
SIGNALS = ["blue pennant", "brass bell", "red ribbon", "harbor lantern"]

OPENINGS = [
    "At sunrise, {name} reached the harbor while gulls circled above the parade route.",
    "The quay smelled of salt and warm bread when {name} arrived for the parade.",
    "Flags flickered over the harbor as {name} hurried toward the waiting marchers.",
    "Before the first parade drum sounded, {name} found a small job beside the water.",
    "The whole town seemed to lean toward the harbor when {name} stepped onto the quay.",
]

REACTIONS = [
    "{name} wanted to fix everything quickly, but stopped to listen first.",
    '"We can make room for everyone while we solve this," {name} promised.',
    "{name} took a careful breath and asked who had noticed the trouble earliest.",
    '"Let us look for the cause, not just cover the worry," {name} said.',
    "The sailor, the infantry, and {name} formed a small circle around the problem.",
]

PLANS = [
    "They divided the work so one person watched the fragile part while the others moved carefully.",
    "They cleared a safe space, named one gentle step, and agreed to test it before the parade began.",
    "The sailor shared a harbor trick, and the infantry added their patient strength.",
    "They listened to every suggestion before choosing the smallest useful repair.",
]

CELEBRATIONS = [
    "Nobody claimed the fix alone; each helper had added one important piece.",
    "The relief in everyone's faces felt brighter than the parade flags.",
    "The sailor thanked the infantry, and the infantry thanked {name} for noticing the quiet clue.",
    "They shared a warm laugh because the best answer had surprised them all.",
]


def valid_signal_choices() -> list[str]:
    return list(SIGNALS)


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The parade helper needs a name.")
    if params.sailor not in SAILORS:
        raise StoryError("The sailor must be a known harbor helper.")
    if params.infantry not in INFANTRY:
        raise StoryError("The infantry group must belong to the parade.")
    if params.signal not in SIGNALS:
        raise StoryError("The signal must be a gentle parade object.")


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        name=rng.choice(NAMES),
        sailor=rng.choice(SAILORS),
        infantry=rng.choice(INFANTRY),
        signal=rng.choice(SIGNALS),
        seed=rng.randrange(2**31),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "harbor_parade"),
            asp.fact("has_sailor", "harbor_parade"),
            asp.fact("has_infantry", "harbor_parade"),
            asp.fact("has_twist", "harbor_parade"),
            asp.fact("shared_care", "harbor_parade"),
            asp.fact("happy_ending", "harbor_parade"),
            asp.fact("repaired", "harbor_parade"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming harbor parade storyworld."
    )
    parser.add_argument("--name")
    parser.add_argument("--sailor", choices=SAILORS)
    parser.add_argument("--infantry", choices=INFANTRY)
    parser.add_argument("--signal", choices=valid_signal_choices())
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
    if args.sailor:
        params.sailor = args.sailor
    if args.infantry:
        params.infantry = args.infantry
    if args.signal:
        params.signal = args.signal
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(id="hero", kind="character", label=params.name))
    world.add(Entity(id="sailor", kind="character", label=params.sailor))
    world.add(Entity(id="infantry", kind="group", label=params.infantry))
    world.add(Entity(id="signal", kind="parade_item", label=params.signal))
    world.facts.update(
        place=PLACE,
        setting="harbor parade",
        hero=world.get("hero"),
        sailor=world.get("sailor"),
        infantry=world.get("infantry"),
        signal=world.get("signal"),
        twist=True,
        shared_care=True,
        happy_ending=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    hero = world.get("hero")
    sailor = world.get("sailor")
    infantry = world.get("infantry")
    signal = world.get("signal")

    hero.bump_meme("care")
    sailor.bump_meme("kindness")
    infantry.bump_meme("teamwork")

    world.say(rng.choice(OPENINGS).format(name=hero.label))
    world.say(
        f"{hero.label} greeted {sailor.label} and {infantry.label}, then helped "
        f"prepare the {signal.label}. {hero.label} {scenario.beginning}."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(f"At first, {scenario.first_try}.")
    world.say(rng.choice(REACTIONS).format(name=hero.label))
    world.para()

    sailor.bump_meter("guidance")
    infantry.bump_meter("patience")
    world.say(f"Together they noticed that {scenario.clue}.")
    world.say(scenario.sailor_line)
    world.say(rng.choice(PLANS))
    world.para()

    world.say(scenario.twist)
    world.say(
        f"The twist changed their plan: instead of giving up, {hero.label}, "
        f"{sailor.label}, and {infantry.label} worked side by side."
    )
    world.say(f"Then they {scenario.repair}.")
    world.say(scenario.result)
    world.para()

    hero.bump_meme("joy")
    sailor.bump_meme("belonging")
    infantry.bump_meme("pride")
    world.say(rng.choice(CELEBRATIONS).format(name=hero.label))
    world.say(
        f"The parade moved forward with a kinder rhythm, and everyone remembered "
        f"that {scenario.ending}."
    )

    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        first_try=scenario.first_try,
        clue=scenario.clue,
        sailor_line=scenario.sailor_line,
        twist=scenario.twist,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        repaired=True,
        parade_ready=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a heartwarming story about {facts['hero'].label} helping "
        f"{facts['sailor'].label} and {facts['infantry'].label} at a harbor parade.",
        "Tell a child-friendly parade story using the words sailor, infantry, and twist.",
        f"Write a gentle story where the {facts['signal'].label} helps reveal a surprising "
        "but heartwarming turn.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    sailor = facts["sailor"].label
    infantry = facts["infantry"].label
    return [
        QAItem(
            question="What trouble interrupted the parade preparations?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question=f"What clue did {hero}, {sailor}, and {infantry} notice?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=str(facts["twist"]),
        ),
        QAItem(
            question="How did the parade helpers solve the problem?",
            answer=f"Together they {facts['repair']}.",
        ),
        QAItem(
            question="What showed that the story ended happily?",
            answer=str(facts["ending"]).capitalize() + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people walk or move together for others to watch and enjoy.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or travels by a boat and learns how to care for people and things at sea.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who travel and work on foot as a group.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change that makes the story turn in a new direction.",
        ),
    ]


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


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show parade_story/1.\n#show kind_twist/1.\n#show ready/1."
    )
    model = asp.one_model(program)
    actual = {
        (symbol.name, tuple(asp_value(symbol) for symbol in symbol.arguments))
        for symbol in model
        if symbol.name in {"parade_story", "kind_twist", "ready"}
    }
    expected = {
        ("parade_story", ("harbor_parade",)),
        ("kind_twist", ("harbor_parade",)),
        ("ready", ("harbor_parade",)),
    }
    if actual != expected:
        print("MISMATCH between ASP and Python world gate.")
        print("ASP:", sorted(actual))
        print("PY :", sorted(expected))
        return 1

    for seed in range(5):
        params = StoryParams(
            name="Luna",
            sailor="Captain Rowan",
            infantry="the harbor infantry",
            signal="blue pennant",
            seed=seed,
        )
        sample = generate(params)
        if not sample.story.strip() or "parade" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1

    print("OK: ASP twin and generated stories agree.")
    return 0


def asp_value(symbol) -> object:
    if symbol.type == 1:
        return symbol.string
    if symbol.type == 2:
        return symbol.number
    return symbol.name


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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        name="Luna",
        sailor="Captain Rowan",
        infantry="the harbor infantry",
        signal="blue pennant",
        seed=17,
    ),
    StoryParams(
        name="Mira",
        sailor="Sailor Bea",
        infantry="the young infantry",
        signal="brass bell",
        seed=31,
    ),
    StoryParams(
        name="Theo",
        sailor="Captain Sol",
        infantry="the visiting infantry",
        signal="red ribbon",
        seed=59,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show parade_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show kind_twist/1.\n#show ready/1."))
        for atom in sorted(asp.atoms(model, "kind_twist") + asp.atoms(model, "ready")):
            print(atom)
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
        while len(samples) < max(0, args.n) and attempts < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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
