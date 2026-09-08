#!/usr/bin/env python3
"""
A standalone adventure storyworld about a manner dispute, teamwork, and a
small bottle of augmentin used responsibly.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
setting(adventure_camp).
has_moral_value(adventure_camp).
has_teamwork(adventure_camp).
medicine(augmentin).
safe_use(augmentin) :- trusted_adult, labeled_medicine, no_dispute_over_dose.
good_adventure(adventure_camp) :- has_moral_value(adventure_camp),
    has_teamwork(adventure_camp), safe_use(augmentin), resolved_dispute(adventure_camp).
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    teammate: str
    trail: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    trouble: str
    failed_try: str
    clue: str
    dialogue: str
    plan: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            lines.append(
                f"  {entity.id:10} ({entity.kind:10}) "
                f"meters={entity.meters} memes={entity.memes} label={entity.label!r}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


SCENARIOS = [
    Scenario(
        trouble="A disagreement broke out when a thorn scratched the guide's hand beside the old stone bridge.",
        failed_try="Rafi wanted to hurry onward, while Nia insisted that the little wound needed proper care first.",
        clue="the camp medic's card said to clean the scratch and ask an adult before using any medicine",
        dialogue='"An adventure is not a race," Nia said. "And we must never guess with medicine." Rafi looked at the card and replied, "You are right. Let us ask together."',
        plan="They agreed that Rafi would guard the trail while Nia brought the card and called the camp leader.",
        repair="cleaned the scratch with water, showed the labeled augmentin to the trusted adult, and followed only the instructions they were given",
        result="The leader approved the safe next step, and the group could continue without turning a small scrape into a larger danger.",
        ending="At sunset, the friends crossed the bridge together, carrying the medicine safely and speaking to one another with respect.",
    ),
    Scenario(
        trouble="Their map tore during a gust near a steep ravine, and each explorer blamed the other for holding it poorly.",
        failed_try="pulling both halves at once made the tear longer and sent pebbles skittering toward the edge.",
        clue="the map's dotted line matched a row of red trail flags below them",
        dialogue='"Let us stop blaming and compare what we can see," said Nia. "The flags can guide us." Rafi nodded. "I will hold the safe side while you read."',
        plan="They made a calm team: one stayed well back from the ravine while the other matched the flags to the map.",
        repair="taped the map only after reaching a flat clearing, checked the labeled augmentin in the first-aid pouch, and asked the leader to inspect the supplies",
        result="The route became clear, and the medicine remained unopened and properly supervised.",
        ending="The repaired map led them to a bright overlook where both explorers shared the first view.",
    ),
    Scenario(
        trouble="A sudden rainstorm flooded the narrow path to the watchtower, and a sharp dispute filled the shelter.",
        failed_try="shouting different directions made the younger hikers more frightened and confused.",
        clue="the old ranger's bell rang from the dry path behind the shelter",
        dialogue='"A kind manner helps people listen," Rafi said. "Then let us use the bell as our guide." Nia answered, "Together, and beside the ranger."',
        plan="They formed a line, counted every hiker, and waited for the ranger before moving.",
        repair="checked the first-aid pouch with the ranger, left the augmentin sealed and labeled, and followed the dry route one careful step at a time",
        result="Everyone reached the warm lodge, and the dispute faded when the team saw how much safer cooperation was.",
        ending="Rain drummed on the roof while the explorers shared hot cocoa and thanked one another for their patient manner.",
    ),
    Scenario(
        trouble="A bridge rope loosened above a ravine just as the group prepared to cross, and two friends argued over who should fix it.",
        failed_try="one friend tugged alone, making the bridge swing harder.",
        clue="the knots were sound at one end but loose where the rope met a wooden post",
        dialogue='"No one should work alone above a ravine," Nia warned. Rafi answered, "Then we will call the guide and steady the bridge together."',
        plan="They stepped back, warned the others, and let the guide choose the safe repair.",
        repair="watched the guide secure the rope, checked the labeled augmentin with the adult, and kept the first-aid pouch dry",
        result="The bridge became safe again, and the group crossed only after the guide gave permission.",
        ending="On the far bank, the friends marked the repaired knot with a bright strip of cloth.",
    ),
]


NAMES = ["Luna", "Mara", "Tomas", "Ari", "Jo"]
TEAMMATES = ["Nia", "Rafi", "Milo", "Sana", "Pip"]
TRAILS = ["the canyon trail", "the forest trail", "the mountain trail", "the river trail"]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The adventurer needs a name.")
    if not params.teammate.strip():
        raise StoryError("An adventure needs a teammate.")
    if params.trail not in TRAILS:
        raise StoryError("Choose a named trail from the safe adventure routes.")


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "adventure_camp"),
            asp.fact("has_moral_value", "adventure_camp"),
            asp.fact("has_teamwork", "adventure_camp"),
            asp.fact("medicine", "augmentin"),
            asp.fact("trusted_adult"),
            asp.fact("labeled_medicine"),
            asp.fact("no_dispute_over_dose"),
            asp.fact("resolved_dispute", "adventure_camp"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld about teamwork and a manner dispute.")
    parser.add_argument("--name")
    parser.add_argument("--teammate")
    parser.add_argument("--trail", choices=TRAILS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        name=args.name or rng.choice(NAMES),
        teammate=args.teammate or rng.choice(TEAMMATES),
        trail=args.trail or rng.choice(TRAILS),
        seed=rng.randrange(2**31),
    )
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity("hero", "character", params.name))
    world.add(Entity("teammate", "character", params.teammate))
    world.add(Entity("medicine", "medicine", "augmentin"))
    world.add(Entity("trail", "place", params.trail))
    world.facts.update(
        setting="adventure camp",
        moral_value=True,
        teamwork=True,
        manner="respectful",
        dispute=True,
        trusted_adult=True,
        labeled_medicine=True,
        no_dispute_over_dose=True,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed or 0)
    scenario = rng.choice(SCENARIOS)
    hero = world.get("hero")
    teammate = world.get("teammate")
    medicine = world.get("medicine")

    hero.meme("courage")
    teammate.meme("fairness")

    world.say(
        f"At dawn, {hero.label} and {teammate.label} set out along {params.trail}. "
        f"They carried water, a map, and a first-aid pouch containing labeled {medicine.label}."
    )
    world.say("Their adventure began with bright hopes, but the trail soon tested their manner.")
    world.paragraph()

    world.say(scenario.trouble)
    world.say(f"At first, {scenario.failed_try}")
    world.say("The friends paused instead of letting the dispute grow.")
    world.paragraph()

    world.say(f"Then they noticed that {scenario.clue}.")
    world.say(scenario.dialogue)
    hero.meme("patience")
    teammate.meme("listening")
    world.paragraph()

    world.say(scenario.plan)
    world.say(f"With teamwork, they {scenario.repair}.")
    medicine.meter("safe_handling")
    world.say(scenario.result)
    world.paragraph()

    hero.meme("wisdom")
    teammate.meme("trust")
    world.say(scenario.ending)
    world.say(
        f"They learned that a good moral value is not merely winning an argument: "
        f"it is using a respectful manner, careful teamwork, and asking for help when safety matters."
    )
    world.facts.update(
        scenario=scenario,
        trouble=scenario.trouble,
        clue=scenario.clue,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        resolved_dispute=True,
        safe_augmentin=True,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero").label
    teammate = world.get("teammate").label
    trail = world.get("trail").label
    return [
        f"Write an adventure story about {hero} and {teammate} exploring {trail}.",
        "Include the words augmentin, manner, and dispute in a child-friendly story.",
        "Show Moral Value and Teamwork solving a dangerous disagreement safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get("hero").label
    teammate = world.get("teammate").label
    medicine = world.get("medicine").label
    scenario: Scenario = f["scenario"]  # type: ignore[assignment]
    return [
        QAItem("What caused the dispute?", f"{scenario.trouble}"),
        QAItem(
            f"What did {hero} and {teammate} notice?",
            f"They noticed that {scenario.clue}.",
        ),
        QAItem(
            f"How did {hero} and {teammate} use teamwork?",
            f"They agreed on a safe plan, and {scenario.repair}.",
        ),
        QAItem(
            f"How was {medicine} handled?",
            f"The friends kept the labeled {medicine} under trusted adult supervision and followed safe instructions instead of guessing.",
        ),
        QAItem("What changed by the end?", f"{scenario.result} {scenario.ending}"),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is teamwork?",
            "Teamwork is cooperating, listening, and sharing useful jobs to reach a safe goal together.",
        ),
        QAItem(
            "What is a respectful manner?",
            "A respectful manner means speaking and acting kindly, even when people disagree.",
        ),
        QAItem(
            "Why should medicine such as augmentin be used only with proper guidance?",
            "Medicine should be used only as directed by a trusted adult or health professional because the correct treatment and amount depend on the person and the illness.",
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


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_adventure/1."))
    found = set(asp.atoms(model, "good_adventure"))
    expected = {("adventure_camp",)}
    if found == expected:
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(found))
    print("PY :", sorted(expected))
    return 1


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Nia", "the canyon trail", 11),
    StoryParams("Mara", "Rafi", "the forest trail", 29),
    StoryParams("Tomas", "Sana", "the river trail", 47),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_adventure/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show good_adventure/1."))
        for item in asp.atoms(model, "good_adventure"):
            print(item)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        while len(samples) < max(1, args.n):
            sample = generate(resolve_params(args, random.Random(rng.randrange(2**31))))
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
