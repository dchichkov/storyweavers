#!/usr/bin/env python3
"""
A small rhyming storyworld about Luna, a funny little magician, whose repeated
spell helps repair a moonlit surprise and bring a happy ending.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
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
    id: str
    place: str
    affordance: str


@dataclass
class Spell:
    id: str
    phrase: str
    effect: str
    rhyme: str


@dataclass
class World:
    setting: Setting
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


SETTINGS = {
    "moon_garden": Setting(
        id="moon_garden",
        place="the moon garden",
        affordance="a silver gate, a round pond, and a little stage",
    ),
}

SPELLS = {
    "mend_and_bend": Spell(
        id="mend_and_bend",
        phrase="Mend and bend, shine and send!",
        effect="repairs a broken magical moon",
        rhyme="bend and send",
    ),
    "twinkle_tangle": Spell(
        id="twinkle_tangle",
        phrase="Twinkle, tangle, stars now dangle!",
        effect="untangles magical star ribbons",
        rhyme="tangle and dangle",
    ),
    "hop_and_pop": Spell(
        id="hop_and_pop",
        phrase="Hop and pop, do not stop!",
        effect="makes a stuck parade of moon-mice move again",
        rhyme="hop and pop",
    ),
}

HEROES = [
    ("Luna", "rabbit"),
    ("Pip", "mouse"),
    ("Mira", "fox"),
    ("Toby", "squirrel"),
]

TRAITS = ["bouncy", "goofy", "curious", "jolly", "wobbly"]

SCENARIOS = {
    "cracked_moon": {
        "opening": "Luna planned a moonlight show, but the paper moon had cracked with a quiet clack.",
        "danger": "Without the moon, the garden would lose its glow and the sleepy fireflies would miss the show.",
        "clue": "A tiny silver thread still shone across the crack, showing that the moon could be mended instead of tossed away.",
        "first_idea": "Luna tried to fix it with a carrot, a sock, and one very serious wiggle.",
        "adult": "The garden keeper brought safe glue and held the moon steady while Luna cast the spell.",
        "proof": "The moon rose round and bright, and its silly crack became a smiling silver grin.",
        "ending": "Everyone danced below it, even the fireflies, who blinked in a cheerful row.",
        "lesson": "A patient repeat can turn a cracked surprise into a bright reprise.",
    },
    "tangled_ribbons": {
        "opening": "At the garden party, magical star ribbons tied themselves into a knotty, naughty knot.",
        "danger": "The knot dragged the lanterns low, so guests had to duck, tuck, and scoot.",
        "clue": "One loose blue ribbon slipped free whenever Luna repeated the same gentle words.",
        "first_idea": "Luna pulled once, pulled twice, then pulled so hard that her hat flew into a pie.",
        "adult": "The keeper lowered the lantern pole while Luna loosened the knot with a small repeated charm.",
        "proof": "The ribbons floated high again and made a sparkling path over the party.",
        "ending": "Luna got her hat back, though it smelled like blueberry pie.",
        "lesson": "Soft words, said again, can loosen a tangle without a tug or a strain.",
    },
    "stuck_moon_mice": {
        "opening": "A line of moon-mice froze beside the pond, each one stuck in a shiny puddle of moonbeam.",
        "danger": "The little parade could not reach the picnic, and the cheese sandwiches were getting lonely.",
        "clue": "The mice twitched their whiskers whenever Luna said the same bouncy spell.",
        "first_idea": "Luna pushed the first mouse with a spoon, but the spoon began marching too.",
        "adult": "The keeper placed soft stepping stones while Luna repeated the magic words at a gentle pace.",
        "proof": "The moon-mice hopped free and marched in a neat, squeaky line.",
        "ending": "They shared the sandwiches and gave Luna the marching spoon.",
        "lesson": "Repeating a kind spell can help a stuck friend move well.",
    },
}

TELLINGS = ["moon_first", "dialogue_first", "clue_first", "silly_first", "quiet_first"]


@dataclass
class StoryParams:
    setting: str
    hero: str
    animal: str
    trait: str
    spell: str
    scenario: str
    telling: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Funny rhyming magic storyworld.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--animal", choices=[animal for _, animal in HEROES])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--spell", choices=SPELLS)
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--telling", choices=TELLINGS)
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
    if args.setting and args.setting != "moon_garden":
        raise StoryError("This funny magic story takes place in the moon garden.")
    if args.hero is None and args.animal is None:
        hero, animal = rng.choice(HEROES)
    elif args.hero is not None and args.animal is None:
        hero = args.hero
        animal = next((kind for name, kind in HEROES if name == hero), "rabbit")
    elif args.hero is None:
        animal = args.animal
        hero = next((name for name, kind in HEROES if kind == animal), "Luna")
    else:
        hero, animal = args.hero, args.animal
    return StoryParams(
        setting="moon_garden",
        hero=hero,
        animal=animal,
        trait=args.trait or rng.choice(TRAITS),
        spell=args.spell or rng.choice(sorted(SPELLS)),
        scenario=args.scenario or rng.choice(sorted(SCENARIOS)),
        telling=args.telling or rng.choice(TELLINGS),
    )


def _rhyming_line(hero: str, spell: Spell) -> str:
    return f'"{spell.phrase}" called {hero}, with a bounce and a pounce.'


def tell(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.setting]
    scenario = SCENARIOS[params.scenario]
    spell = SPELLS[params.spell]
    world = World(setting)

    hero = world.add(Entity(params.hero, "character", params.animal, params.hero))
    friend = world.add(Entity("keeper", "character", "garden_keeper", "the garden keeper"))
    magic = world.add(Entity("moon_magic", "thing", "magic", "moon magic"))
    trouble = world.add(Entity("trouble", "thing", "problem", "the funny problem"))

    hero.memes.update(funny=1.0, brave=1.0, repetition=1.0)
    magic.meters["strength"] = 1.0
    trouble.meters["repaired"] = 0.0
    world.facts.update(
        hero=hero,
        friend=friend,
        magic=magic,
        trouble=trouble,
        spell=spell,
        scenario=scenario,
        repeated=0,
        resolved=False,
    )

    openings = {
        "moon_first": f"Above {setting.place}, the moon winked at {hero.label}, a {params.trait} {params.animal}.",
        "dialogue_first": f'"Is the moon supposed to wobble?" asked {hero.label}, a {params.trait} {params.animal}.',
        "clue_first": f"A silver sparkle skipped across {setting.place}, and {hero.label}, a {params.trait} {params.animal}, followed it.",
        "silly_first": f"{hero.label} wore two hats, one shoe, and a spoon as a badge in {setting.place}.",
        "quiet_first": f"Night settled softly over {setting.place}, where {hero.label}, a {params.trait} {params.animal}, listened.",
    }
    world.say(openings[params.telling])
    world.say("It was a funny night, but not every funny thing felt fine.")
    world.say(scenario["opening"])
    world.para()

    world.say(scenario["danger"])
    world.say(scenario["clue"])
    world.say(f"The clue made {hero.label} pause instead of pounce.")
    world.para()

    world.say(scenario["first_idea"])
    world.say(f'"Maybe I need a spell with a little more swell," said {hero.label}.')
    world.say(f'"Try the same spell slowly," said the garden keeper. "Magic likes a steady beat."')
    world.say(_rhyming_line(hero.label, spell))
    world.facts["repeated"] = 1
    world.para()

    world.say(scenario["adult"])
    for count in range(2):
        world.say(f"{hero.label} repeated, {_rhyming_line(hero.label, spell).lower()}")
        world.facts["repeated"] = int(world.facts["repeated"]) + 1
    world.say(f"On the third try, the magic began to {spell.effect}.")
    trouble.meters["repaired"] = 1.0
    world.facts["resolved"] = True
    world.para()

    world.say(scenario["proof"])
    world.say(scenario["ending"])
    world.say(f"{hero.label} laughed and said, 'Funny, happy, and bright—repetition made the night just right!'")
    world.say(f"Everyone joined the rhyme: '{scenario['lesson']}'")
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.spell not in SPELLS:
        raise StoryError("Unknown spell.")
    if params.scenario not in SCENARIOS:
        raise StoryError("Unknown scenario.")
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.hero + params.scenario)
    world = tell(params, random.Random(seed ^ 0xA91F))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a funny rhyming story about {params.hero} using magic repetition.",
            "Include a clear problem, a spoken exchange, a repeated spell, and a happy ending.",
            "Show how a small clue changes the hero's plan.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    scenario = world.facts["scenario"]
    spell = world.facts["spell"]
    return [
        QAItem(
            question=f"What problem did {hero.label} discover?",
            answer=scenario["danger"],
        ),
        QAItem(
            question=f"What clue changed {hero.label}'s first plan?",
            answer=scenario["clue"],
        ),
        QAItem(
            question="What did the garden keeper tell the hero about magic?",
            answer="The garden keeper said to try the same spell slowly because magic likes a steady beat.",
        ),
        QAItem(
            question="What spell did the hero repeat?",
            answer=f'{spell.phrase} The hero repeated it three times with a steady beat.',
        ),
        QAItem(
            question="How did the story end?",
            answer=scenario["proof"] + " " + scenario["ending"],
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again and again, often to help it work or to help someone remember.",
        ),
        QAItem(
            question="What is magic in this storyworld?",
            answer="Magic is a playful story force that responds to a careful, repeated spell.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the problem is safely resolved and leaves the characters with a joyful final image.",
        ),
        QAItem(
            question="What does funny mean?",
            answer="Funny means amusing or silly in a way that makes people smile or laugh.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} type={entity.type:14} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  repeated={world.facts.get('repeated')}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
magic_problem(S) :- spell(S).
repeated(S) :- spell(S), repetition.
resolved(P) :- magic_problem(P), repeated(P), safe.
happy :- resolved(P).
#show magic_problem/1.
#show repeated/1.
#show resolved/1.
#show happy/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "moon_garden"),
        asp.fact("spell", "mend_and_bend"),
        asp.fact("repetition"),
        asp.fact("safe"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        names = {symbol.name for symbol in model}
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    required = {"magic_problem", "repeated", "resolved", "happy"}
    if required.issubset(names):
        print("OK: ASP magic, repetition, resolution, and happy ending agree.")
        return 0
    print("MISMATCH: ASP did not derive the complete happy ending.")
    return 1


CURATED = [
    StoryParams("moon_garden", "Luna", "rabbit", "bouncy", "mend_and_bend", "cracked_moon", "dialogue_first", 101),
    StoryParams("moon_garden", "Pip", "mouse", "goofy", "twinkle_tangle", "tangled_ribbons", "clue_first", 202),
    StoryParams("moon_garden", "Mira", "fox", "curious", "hop_and_pop", "stuck_moon_mice", "silly_first", 303),
]


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

    if args.verify:
        raise SystemExit(asp_verify())

    if args.show_asp:
        print(asp_program())
        return

    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(item) for item in CURATED]
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
