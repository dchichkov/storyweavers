#!/usr/bin/env python3
"""
insect_trim_fuzz_dance_studio_bad_ending.py
===========================================

A small rhyming, cautionary storyworld about an insect, a strip of trim,
and soft fuzz in a dance studio. A selfish choice makes a bad ending,
while sharing offers the safer path.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    material: str
    color: str
    use: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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


SETTINGS = {
    "studio": Setting(place="the dance studio", affords={"dance", "sharing"}),
}

DANCES = {
    "dance": {
        "name": "fuzz-foot dance",
        "verb": "twirl",
        "gerund": "twirling",
        "risk": "a loose decoration could trip a dancer",
    }
}

PROPS = {
    "trim": Prop(
        id="trim",
        label="silver trim",
        material="shiny cloth",
        color="silver",
        use="outline the practice stage",
    ),
    "fuzz": Prop(
        id="fuzz",
        label="soft blue fuzz",
        material="cottony fluff",
        color="blue",
        use="make a gentle tail for a costume",
    ),
}

INSECT_TYPES = ["beetle", "moth", "cricket", "ladybug", "firefly"]
NAMES = ["Luna", "Mina", "Pip", "Nori", "Tavi", "Bram"]
HELPERS = ["Moth", "Cricket", "Beetle", "Rae"]
TRAITS = ["eager", "bouncy", "careful", "proud", "curious"]

SCENARIOS = [
    {
        "id": "stolen_trim",
        "premise": "The dancers found one bright strip of trim beside the mirror.",
        "temptation": "Luna wanted to keep the trim for her own grand costume.",
        "choice": "snatched the strip before the group could use it",
        "clue": "the loose edge curling across the floor",
        "dialogue": '"Please share it," said Moth. "The whole class needs a safe border."',
        "repair": "returned the trim and helped tape it flat around the practice stage",
        "ending": "But the torn costume sagged, and the final dance ended in a quiet, crooked flop.",
        "lesson": "a pretty prize is not worth making a shared place unsafe",
    },
    {
        "id": "fuzz_cloud",
        "premise": "A bag of soft blue fuzz waited beside the studio sewing table.",
        "temptation": "Luna imagined a fluffy crown and pulled the whole bag toward herself.",
        "choice": "grabbed the fuzz and scattered tufts with a swish",
        "clue": "blue fuzz floating near the dancers' noses",
        "dialogue": '"Stop and breathe," said Cricket. "We can make one costume for everyone to enjoy."',
        "repair": "shared the fuzz, gathered the loose tufts, and placed them in a clean basket",
        "ending": "The dancers coughed through the finale, and the once-bright studio was left in a fuzzy mess.",
        "lesson": "sharing materials also means sharing care for the air and floor",
    },
    {
        "id": "insect_spotlight",
        "premise": "A tiny insect landed beneath the warm spotlight before rehearsal.",
        "temptation": "Luna wanted the brightest center spot and waved the insect away with a trim ribbon.",
        "choice": "danced too close to the insect and knocked over the ribbon stand",
        "clue": "the insect hiding beside the stage trim",
        "dialogue": '"Let it rest," said Beetle. "Make room, and the dance will be better."',
        "repair": "moved back, shared the center, and guided the insect safely toward the open window",
        "ending": "The stand leaned crookedly, the spotlight shut off, and the grand solo became a dim stumble.",
        "lesson": "a careful dancer leaves room for small neighbors",
    },
    {
        "id": "costume_race",
        "premise": "The class held a costume race across the polished studio floor.",
        "temptation": "Luna tucked silver trim and blue fuzz into her belt so she could look fastest.",
        "choice": "raced before checking whether the decorations were secure",
        "clue": "a bright strand dragging behind her foot",
        "dialogue": '"Wait for us," said Moth. "A shared dance needs a shared pace."',
        "repair": "stopped, divided the decorations, and tied each piece firmly with a friend",
        "ending": "The trim tangled her ankles, and the race finished with a loud, embarrassing thump.",
        "lesson": "hurrying for praise can turn a dance into a fall",
    },
]

OPENINGS = [
    "In the dance studio, Luna the {species} heard the beat: tap, tap, tune!",
    "Beneath the round studio lights, Luna the {species} practiced a bright little tune.",
    "The dance studio floor shone like a moon as Luna the {species} came to dance.",
    "At rehearsal time, Luna the {species} bounced in twice and bowed once.",
]

BAD_ENDINGS = [
    "The music stopped with a clack, and the dancers stared at the mess.",
    "The final bell rang, but nobody cheered for the lopsided end.",
    "The curtain drooped, the floor was untidy, and the bright plan was done.",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for activity in sorted(setting.affords):
            for prop in PROPS:
                combos.append((place, activity, prop))
    return combos


ASP_RULES = r"""
place(studio).
affords(studio,dance).
affords(studio,sharing).
prop(trim).
prop(fuzz).
valid(Place,Activity,Prop) :- place(Place), affords(Place,Activity), prop(Prop).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for activity in sorted(setting.affords):
            lines.append(asp.fact("affords", place, activity))
    for prop in PROPS:
        lines.append(asp.fact("prop", prop))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_rows = set(asp_valid_combos())
    if py == clingo_rows:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - clingo_rows))
    print("  only in clingo:", sorted(clingo_rows - py))
    return 1


def run_world(world: World, hero: Entity, helper: Entity, prop: Prop, scenario: dict) -> None:
    hero.memes["pride"] = 1
    world.facts["started"] = True
    world.say(f"{hero.id} wanted the {scenario['temptation'].split(' wanted ', 1)[-1].rstrip('.')}.")
    hero.memes["greed"] = 1
    hero.meters["risk"] = 1
    world.say(f"In a hurry, {hero.id} {scenario['choice']}.")
    world.say(scenario["dialogue"])
    helper.memes["warning"] = 1
    world.say(f"Then {hero.id} noticed {scenario['clue']}. The warning was plain: share, or the dance could go wrong.")
    hero.memes["understanding"] = 1
    world.say(f'"I should have asked first," {hero.id} admitted. "I will help now."')
    hero.memes["sharing"] = 1
    helper.memes["trust"] = 1
    world.say(f"Together, {hero.id} {scenario['repair']}.")
    world.para()
    hero.meters["bad_ending"] = 1
    world.say(scenario["ending"])
    world.say(f"{random.choice(BAD_ENDINGS)} This was a cautionary ending, not a happy one.")
    world.say(f"The lesson rang with the beat: {scenario['lesson']}.")
    world.facts.update(
        {
            "hero": hero,
            "helper": helper,
            "prop": prop,
            "scenario": scenario,
            "lesson": scenario["lesson"],
            "ending": scenario["ending"],
            "bad_ending": True,
            "cautionary": True,
            "sharing": True,
        }
    )


@dataclass
class StoryParams:
    place: str
    activity: str
    prop: str
    name: str
    species: str
    helper: str
    trait: str
    scenario: str = "stolen_trim"
    seed: Optional[int] = None
    telling: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rhyming Story world: an insect, trim, and fuzz in a dance studio."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--activity", choices=["dance", "sharing"])
    parser.add_argument("--prop", choices=PROPS)
    parser.add_argument("--name")
    parser.add_argument("--species", choices=INSECT_TYPES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
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
    combos = [
        combo
        for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.activity is None or combo[1] == args.activity
        if args.prop is None or combo[2] == args.prop
    ]
    if not combos:
        raise StoryError("No valid dance-studio combination matches the requested options.")
    place, activity, prop = rng.choice(combos)
    return StoryParams(
        place=place,
        activity=activity,
        prop=prop,
        name=args.name or rng.choice(NAMES),
        species=args.species or rng.choice(INSECT_TYPES),
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
        scenario=rng.choice(SCENARIOS)["id"],
        telling=rng.randrange(1_000_000),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.prop not in PROPS:
        raise StoryError(f"Unknown prop: {params.prop}")
    scenario = next((item for item in SCENARIOS if item["id"] == params.scenario), None)
    if scenario is None:
        raise StoryError(f"Unknown scenario: {params.scenario}")

    world = World(SETTINGS[params.place])
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.species,
            label=f"{params.trait} {params.species}",
        )
    )
    helper = world.add(Entity(id=params.helper, kind="character", type="insect", label=params.helper))
    world.add(Entity(id="stage", type="place", label="practice stage"))
    prop = PROPS[params.prop]

    rng = random.Random(params.telling)
    opening = rng.choice(OPENINGS).format(species=params.species)
    extra = rng.choice(
        [
            "The tiny insect tapped a toe, and the floor answered: beat, beat, boom!",
            "Silver trim gleamed while blue fuzz bobbed like clouds in a tune.",
            "Every little wing and foot kept time beneath the studio moon.",
        ]
    )

    world.say(opening)
    world.say(extra)
    world.say(scenario["premise"])
    world.para()
    world.say(scenario["temptation"])
    world.say(f"With a {params.trait} grin, {hero.id} {scenario['choice']}.")
    world.say(scenario["dialogue"])
    world.para()
    run_world(world, hero, helper, prop, scenario)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        "Write a child-friendly rhyming story set in a dance studio.",
        f"Tell a cautionary tale about {facts['hero'].id}, an insect, and a shared piece of {facts['prop'].label}.",
        "Include trim, fuzz, sharing, and a clear bad ending caused by a selfish choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    prop = facts["prop"]
    scenario = facts["scenario"]
    return [
        QAItem(
            question=f"Where did {hero.id}'s story happen?",
            answer=f"It happened in the dance studio, where {hero.id} and {helper.id} were preparing a group dance.",
        ),
        QAItem(
            question=f"What did {hero.id} want?",
            answer=f"{hero.id} wanted to use the {prop.label} for a special costume or dance moment instead of sharing it at first.",
        ),
        QAItem(
            question=f"What warning did {helper.id} give?",
            answer=f"{helper.id} warned that {scenario['clue']}. The clue showed that the selfish choice could make the studio or dance unsafe.",
        ),
        QAItem(
            question=f"How did {hero.id} try to repair the trouble?",
            answer=f"{hero.id} chose sharing and helped {scenario['repair']}.",
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=f"The ending was bad because {scenario['ending']} The cautionary result showed that sharing should have happened before the trouble began.",
        ),
        QAItem(
            question="What lesson does the story teach?",
            answer=f"It teaches that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an insect?",
            answer="An insect is a small animal with six legs, a body in three main parts, and usually antennae.",
        ),
        QAItem(
            question="What is trim?",
            answer="Trim is a narrow decorative strip used to finish or brighten the edge of clothing, fabric, or a stage.",
        ),
        QAItem(
            question="What is fuzz?",
            answer="Fuzz is a soft mass of tiny fibers or hairs.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, enjoy, or receive part of something instead of keeping it all for yourself.",
        ),
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story shows trouble caused by a poor choice so readers can learn to choose more carefully.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is an ending where the problem is not fully made happy or safe, often because a warning was ignored.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {item}" for item in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: {entity.type} {' '.join(details)}")
    lines.append(f"facts: bad_ending={world.facts.get('bad_ending')} sharing={world.facts.get('sharing')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        place="studio",
        activity="dance",
        prop="trim",
        name="Luna",
        species="moth",
        helper="Cricket",
        trait="eager",
        scenario="stolen_trim",
        telling=101,
    ),
    StoryParams(
        place="studio",
        activity="sharing",
        prop="fuzz",
        name="Mina",
        species="beetle",
        helper="Moth",
        trait="proud",
        scenario="fuzz_cloud",
        telling=202,
    ),
    StoryParams(
        place="studio",
        activity="dance",
        prop="trim",
        name="Pip",
        species="firefly",
        helper="Beetle",
        trait="curious",
        scenario="insect_spotlight",
        telling=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        rows = asp_valid_combos()
        print(f"{len(rows)} compatible combos:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 30, 30):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
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
