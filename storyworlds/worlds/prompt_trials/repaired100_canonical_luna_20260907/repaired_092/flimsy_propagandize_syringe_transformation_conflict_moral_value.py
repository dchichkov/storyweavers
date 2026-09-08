#!/usr/bin/env python3
"""A gentle rhyming story about a flimsy poster, a syringe, and moral courage."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Trial:
    key: str
    place: str
    claim: str
    tempting_action: str
    evidence: str
    repair: str
    transformation: str
    ending: str
    moral: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Milo"
    trial: str = "paper_gate"
    rhyme_mode: int = 0
    conflict_mode: int = 0
    ending_mode: int = 0


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(group) for group in self.paragraphs if group)


TRIALS = {
    "paper_gate": Trial(
        "paper_gate",
        "the village health fair",
        "A new poster claimed that one magical syringe could cure every ache.",
        "repeat the shiny claim from the stage",
        "The poster was flimsy, and the nurse explained that a syringe is useful only for the right medicine and the right patient.",
        "replace the boast with a clear sign about asking a trained health worker",
        "A weak sheet becomes a sturdy, honest guide when Luna adds facts and a wooden frame.",
        "The crowd learns to ask questions, and the fair grows calmer and wiser.",
        "Truth helps people choose safely; a loud claim is not proof.",
    ),
    "painted_cart": Trial(
        "painted_cart",
        "the market square",
        "A painted cart promised that one syringe would make everyone strong.",
        "propagandize the promise with a marching chant",
        "The cart's wheel wobbled, its canvas was flimsy, and the clinic worker said treatments must fit each person's need.",
        "wash away the boast and paint a question board beside the clinic tent",
        "The wobbly cart becomes a rolling lesson board with careful questions.",
        "Children circle the board, choosing knowledge instead of a noisy promise.",
        "Good choices grow from evidence, care, and honest questions.",
    ),
    "rain_banner": Trial(
        "rain_banner",
        "the school garden",
        "A rain-soaked banner said that every syringe was a magic key.",
        "hide the warning beneath a brighter slogan",
        "The banner tore in the wind, while the gardener showed that safe medicine needs instructions and trusted adults.",
        "turn the scraps into weatherproof cards that explain how to seek help",
        "The flimsy banner transforms into a row of sturdy cards beneath the garden roof.",
        "The children read the cards aloud while raindrops tap a truthful beat.",
        "Caring words should guide people, never pressure them.",
    ),
}

HEROES = ("Luna", "Nia", "Pip", "Tara")
HELPERS = ("Milo", "Ari", "Grandma Sol", "Nurse Bea")

OPENINGS = (
    "At dawn in the square, the fair began with a flare.",
    "By the garden gate, Luna found a curious slate.",
    "When bells rang bright, a banner caught the light.",
    "In a little town, a loud claim floated down.",
)

CONFLICTS = (
    "The speaker cried, \"Tell everyone! Make the promise ring!\"",
    "A crowd began to cheer, though the message was unclear.",
    "\"Do not question the sign! Just repeat it line by line!\"",
    "The bright words pressed like rain, but Luna stopped the train.",
)

ENDINGS = (
    "The sign stood straight and true, with room for questions too.",
    "The crowd went home to share a wiser care.",
    "The fair's loud boast grew small; honest words helped all.",
    "The new cards shone in the sun, and thoughtful work had won.",
)

ASP_RULES = r"""
item(syringe).
concept(transformation).
concept(conflict).
concept(moral_value).
claim_requires_evidence.
safe_message :- evidence_checked, no_pressure.
transformed(sign) :- flimsy(material), honest_message, repaired.
resolved(conflict) :- safe_message, honest_message.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("flimsy", "material"),
            asp.fact("tool", "syringe"),
            asp.fact("feature", "transformation"),
            asp.fact("feature", "conflict"),
            asp.fact("feature", "moral_value"),
            asp.fact("evidence_checked"),
            asp.fact("no_pressure"),
            asp.fact("honest_message"),
            asp.fact("repaired"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a rhyming story about truth and safe choices.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trial", choices=sorted(TRIALS))
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
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        trial=args.trial or rng.choice(sorted(TRIALS)),
        rhyme_mode=rng.randrange(len(OPENINGS)),
        conflict_mode=rng.randrange(len(CONFLICTS)),
        ending_mode=rng.randrange(len(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    if params.trial not in TRIALS:
        raise StoryError(f"Unknown trial: {params.trial}")
    trial = TRIALS[params.trial]
    world = World(params)
    hero = world.add(Entity(params.hero, "character", params.hero, memes={"curiosity": 1.0, "courage": 1.0}))
    helper = world.add(Entity(params.helper, "character", params.helper, memes={"care": 1.0}))
    poster = world.add(Entity("poster", "message", "the poster", meters={"strength": 0.2}))
    syringe = world.add(Entity("syringe", "medical_tool", "a syringe", meters={"purpose": 1.0}))

    world.say(OPENINGS[params.rhyme_mode])
    world.say(f"{hero.label} saw {poster.label}, thin as a feather, promising, \"{trial.claim}\"")
    world.say(f"{helper.label} stood near {syringe.label}, ready to explain that careful health choices matter more than a dazzling stare.")
    world.para()

    world.say(CONFLICTS[params.conflict_mode])
    world.say(f"{hero.label} took a breath and said, \"A claim can be loud, but how do we know it is sound?\"")
    world.say(f"{helper.label} replied, \"We ask a trained health worker, check the facts, and never pressure people around.\"")
    world.say(f"Together they discovered that {trial.evidence}")
    world.say(f"That truth changed {hero.label}'s plan: instead of trying to propagandize the crowd, {hero.label} chose to {trial.repair}.")
    world.say(f"The conflict softened as neighbors listened, compared the words, and made room for a question.")
    world.para()

    world.say(f"Then came the transformation: {trial.transformation}")
    world.say(ENDINGS[params.ending_mode])
    world.say(trial.ending)
    world.say(f"{hero.label} smiled and said, \"{trial.moral}\"")
    world.say("The syringe stayed with the trained clinic worker, while the children carried honest questions home.")

    world.facts.update(
        hero=hero,
        helper=helper,
        poster=poster,
        syringe=syringe,
        trial=trial,
        transformation=True,
        conflict_resolved=True,
        moral_value=trial.moral,
        evidence=trial.evidence,
    )
    poster.meters["strength"] = 1.0
    poster.memes["honesty"] = 2.0
    hero.memes["wisdom"] = 2.0
    world.trace.extend(
        [
            "flimsy_message_detected",
            "syringe_context_explained",
            "propaganda_refused",
            "evidence_checked",
            "message_transformed",
            "conflict_resolved",
        ]
    )
    return world


def generation_prompts(world: World) -> list[str]:
    trial: Trial = world.facts["trial"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a rhyming story about {hero.label} facing a flimsy claim involving a syringe.",
        f"Include conflict, transformation, and moral value, then reveal that {trial.evidence}",
        "Show dialogue changing a character's decision from repeating propaganda to sharing careful truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    trial: Trial = world.facts["trial"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            "What did the flimsy message claim?",
            f"It claimed that {trial.claim}",
        ),
        QAItem(
            f"How did {hero.label} and {helper.label} handle the conflict?",
            f"They checked the claim with a trusted health worker and chose to {trial.repair}.",
        ),
        QAItem(
            "What transformation happened?",
            f"{trial.transformation} The weak message became a sturdier, more honest guide.",
        ),
        QAItem(
            "Why was the syringe mentioned carefully?",
            "A syringe is a medical tool for the right medicine and patient; a trained health worker must explain and use it safely.",
        ),
        QAItem(
            "What moral value did the story show?",
            trial.moral,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should people question a loud health claim?",
            "A loud claim may still be incomplete or false. People should seek evidence and ask a trusted health professional.",
        ),
        QAItem(
            "What does propagandize mean in this story?",
            "It means trying to spread a persuasive claim widely, especially without giving enough evidence or room for questions.",
        ),
        QAItem(
            "Who should handle a syringe?",
            "A trained health worker should explain and handle a syringe safely; children should not use one themselves.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {item}" for item in world.trace)
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: meters={entity.meters}, memes={entity.memes}")
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(trial="paper_gate"),
    StoryParams(hero="Nia", helper="Nurse Bea", trial="rain_banner", rhyme_mode=2, conflict_mode=1, ending_mode=3),
    StoryParams(hero="Pip", helper="Ari", trial="painted_cart", rhyme_mode=3, conflict_mode=2, ending_mode=1),
]


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(
            asp_program(
                "#show safe_message/0.\n#show transformed/1.\n#show resolved/1.\n"
            )
        )
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if not model:
        print("ASP produced no model.")
        return 1
    atoms = {str(atom) for atom in model}
    required = {"safe_message", "transformed(sign)", "resolved(conflict)"}
    if not required.issubset(atoms):
        print("ASP parity check failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "conflict" not in sample.story.lower() or "syringe" not in sample.story.lower():
            print("Story exercise failed.")
            return 1
    print("OK: ASP parity and story exercises passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    show = "#show safe_message/0.\n#show transformed/1.\n#show resolved/1.\n"
    if args.show_asp:
        print(asp_program(show))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            print("\n".join(str(atom) for atom in asp.one_model(asp_program(show))))
        except Exception as exc:
            raise StoryError(f"ASP mode unavailable: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for offset in range(max(0, args.n)):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
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
