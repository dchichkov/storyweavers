#!/usr/bin/env python3
"""
A small Storyweavers world about animal crew members aboard a frigate.

A noisy call about a sealed crate of champagne is mistaken for an order about
the safety chain. The Python simulation tracks the misunderstanding, blocked
gangway, conversation, and repair; an inline ASP twin checks the same outcome.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_REPO_ROOT: Optional[Path] = None
for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        _REPO_ROOT = _parent
        sys.path.insert(0, str(_parent / "storyworlds"))
        sys.path.insert(0, str(_parent))
        break

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class AnimalSpec:
    id: str
    name: str
    species: str
    crew_member: bool = True


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    pennant_color: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


@dataclass
class StoryParams:
    harbor: str
    frigate: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


PLACES = {
    "saltglass_harbor": Place("saltglass_harbor", "Saltglass Harbor", "blue"),
    "moonwake_bay": Place("moonwake_bay", "Moonwake Bay", "silver"),
    "reedlight_cove": Place("reedlight_cove", "Reedlight Cove", "yellow"),
}

FRIGATES = {
    "brightwing": "Brightwing",
    "swift_petrel": "Swift Petrel",
    "north_star": "North Star",
}

ANIMALS = {
    "nori": AnimalSpec("nori", "Nori", "otter"),
    "pip": AnimalSpec("pip", "Pip", "puffin"),
    "mara": AnimalSpec("mara", "Mara", "seal"),
    "tavi": AnimalSpec("tavi", "Tavi", "tern"),
    "bram": AnimalSpec("bram", "Bram", "turtle"),
    "lark": AnimalSpec("lark", "Lark", "gull"),
    "kelp": AnimalSpec("kelp", "Kelp", "crab"),
    "wren": AnimalSpec("wren", "Wren", "pelican"),
    "captain_fern": AnimalSpec(
        "captain_fern", "Captain Fern", "albatross", crew_member=False
    ),
}
CREW_IDS = tuple(key for key, animal in ANIMALS.items() if animal.crew_member)
ANIMAL_BY_NAME = {animal.name: animal for animal in ANIMALS.values()}

DECK_NOISES = (
    "A gust snapped the canvas overhead, rattling the captain's words.",
    "The harbor bell clanged just as the captain called across the deck.",
    "A flock of gulls cried above the rigging and covered part of the call.",
)
DECK_DETAILS = (
    "A blue pennant fluttered above the wheel.",
    "Sunlight laid bright ladders across the water.",
    "A wooden gull weather vane pointed toward the pier.",
    "Two coils of rope rested neatly beside the mast.",
    "A silver bell shone beside the captain's wheel.",
    "The harbor's little waves tapped softly against the hull.",
    "A paper map was spread beneath a smooth shell.",
    "The frigate's polished rail caught the early light.",
)


@dataclass(frozen=True)
class DeckScene:
    noise: str
    detail: str


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.harbor}:{params.frigate}:{params.hero_name}:{params.helper_name}"
    return sum((i + 1) * ord(char) for i, char in enumerate(text))


def _animal_for_name(name: str) -> AnimalSpec:
    animal = ANIMAL_BY_NAME.get(name)
    if animal is None or not animal.crew_member:
        raise StoryError(f"Unknown crew animal {name!r}; choose a listed animal name.")
    return animal


def reasonableness_gate(params: StoryParams) -> None:
    """Reject setups that do not describe a plausible, supported story."""
    if params.harbor not in PLACES:
        raise StoryError(f"Unknown harbor {params.harbor!r}.")
    if params.frigate not in FRIGATES:
        raise StoryError(f"Unknown frigate {params.frigate!r}.")
    hero = _animal_for_name(params.hero_name)
    helper = _animal_for_name(params.helper_name)
    if hero.id == helper.id:
        raise StoryError("The hero and helper must be two different animals.")
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("The seed must be an integer.")


def valid_combos() -> list[tuple[str, str, str, str]]:
    """Return registered harbor, crew-pair, and frigate combinations."""
    return [
        (harbor_id, hero_id, helper_id, frigate_id)
        for harbor_id in PLACES
        for hero_id in CREW_IDS
        for helper_id in CREW_IDS
        if hero_id != helper_id
        for frigate_id in FRIGATES
    ]


def _python_causal_outcome(
    *,
    intended: str,
    heard: str,
    chain_unhooked: bool,
    conversation_checked: bool,
    chain_restored: bool,
    crate_delivered: bool,
) -> bool:
    misunderstood = intended == "champagne" and heard == "chain"
    path_blocked = misunderstood and chain_unhooked
    repaired = path_blocked and conversation_checked and chain_restored
    return repaired and crate_delivered


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = PLACES[params.harbor]
    hero_spec = _animal_for_name(params.hero_name)
    helper_spec = _animal_for_name(params.helper_name)
    captain_spec = ANIMALS["captain_fern"]
    rng = random.Random(_stable_seed(params))
    scene = DeckScene(
        noise=rng.choice(DECK_NOISES),
        detail=rng.choice(DECK_DETAILS),
    )

    world = World(place=place)
    hero = world.add(
        Entity(hero_spec.id, "character", hero_spec.species, hero_spec.name, "hero")
    )
    helper = world.add(
        Entity(
            helper_spec.id,
            "character",
            helper_spec.species,
            helper_spec.name,
            "helper",
        )
    )
    captain = world.add(
        Entity(
            captain_spec.id,
            "character",
            captain_spec.species,
            captain_spec.name,
            "captain",
        )
    )
    frigate = world.add(
        Entity(
            params.frigate,
            "vessel",
            "frigate",
            FRIGATES[params.frigate],
            "ship",
        )
    )
    crate = world.add(
        Entity("champagne_crate", "cargo", "crate", "sealed champagne crate")
    )
    chain = world.add(
        Entity("safety_chain", "equipment", "chain", "light safety chain")
    )
    gangway = world.add(
        Entity("gangway", "place", "gangway", "ship's gangway")
    )

    crate.meters["on_deck"] = 1.0
    crate.meters["sealed"] = 1.0
    chain.meters["secured_on_hooks"] = 1.0
    gangway.meters["clear"] = 1.0
    world.meters["crate_delivered"] = 0.0
    world.meters["misunderstanding"] = 0.0
    world.memes["crew_worry"] = 0.0

    world.say(
        f"At {place.label}, dawn laid a peach-colored path across the water. "
        f"The frigate {frigate.label} rocked gently beside the pier, where "
        f"{scene.detail}"
    )
    world.say(
        f"On deck, {hero.label} the {hero.type} and {helper.label} the "
        f"{helper.type} were preparing a sealed crate of champagne for the "
        "grown-ups' harbor welcome. The bottles were packed safely in straw, "
        "and the crate was meant to go ashore."
    )
    world.para()

    captain.memes["calling"] += 1.0
    world.say(
        f"Captain Fern called, “Carry the champagne crate to the pier, please!” "
        f"{scene.noise} {helper.label} heard, “Carry the chain, please!”"
    )

    # The mistaken interpretation changes the physical layout of the deck.
    helper.memes["certainty"] += 1.0
    helper.memes["confusion"] += 1.0
    helper.meters["unhooked_chain"] += 1.0
    chain.meters["secured_on_hooks"] = 0.0
    chain.meters["across_gangway"] = 1.0
    gangway.meters["clear"] = 0.0
    crate.meters["blocked"] = 1.0
    world.meters["misunderstanding"] = 1.0
    world.meters["path_blocked"] = 1.0
    world.memes["crew_worry"] += 1.0

    world.say(
        f"Thinking the captain wanted the safety chain, {helper.label} pulled it "
        "from its hooks. The loose chain looped across the gangway, so the crate "
        "could not pass."
    )
    world.para()

    hero.memes["concern"] += 1.0
    world.say(
        f"{hero.label} stopped before the loop. “Why is the safety chain across "
        f"the gangway? I heard Captain Fern say champagne.”"
    )
    world.say(
        f"“I heard ‘chain, please,’” said {helper.label}. “Let’s read the crate "
        "and ask before we move anything else.”"
    )
    world.say(
        "Together they read CHAMPAGNE on the gold label and called to the captain."
    )
    world.say(
        "“Champagne, not chain!” called Captain Fern. “That sealed crate is for "
        "the pier. Put the safety chain back on its hooks, then carry the crate "
        "together.”"
    )
    world.para()

    # The conversation changes what the helper believes and what the crew does.
    helper.memes["confusion"] = 0.0
    helper.memes["understanding"] += 1.0
    hero.memes["helpfulness"] += 1.0
    world.meters["conversation_checked"] = 1.0
    chain.meters["secured_on_hooks"] = 1.0
    chain.meters["across_gangway"] = 0.0
    gangway.meters["clear"] = 1.0
    crate.meters["blocked"] = 0.0
    helper.meters["rehung_chain"] += 1.0
    world.meters["path_blocked"] = 0.0
    world.memes["crew_worry"] = 0.0

    world.say(
        f"{helper.label} rehung the chain while {hero.label} steadied the crate. "
        "When the gangway was clear, they lifted the crate by its side handles "
        "and carried it carefully to the pier."
    )
    crate.meters["on_deck"] = 0.0
    crate.meters["delivered"] = 1.0
    crate.meters["sealed"] = 1.0
    world.meters["crate_delivered"] = 1.0
    hero.memes["pride"] += 1.0
    helper.memes["relief"] += 1.0
    world.memes["crew_joy"] += 1.0

    world.say(
        f"They set the sealed crate on the dry welcome table beneath a "
        f"{place.pennant_color} pennant. Behind them, the safety chain hung "
        "neatly on its hooks, and the frigate's gangway lay clear."
    )

    resolved = _python_causal_outcome(
        intended="champagne",
        heard="chain",
        chain_unhooked=helper.meters["unhooked_chain"] >= 1.0,
        conversation_checked=world.meters["conversation_checked"] >= 1.0,
        chain_restored=chain.meters["secured_on_hooks"] >= 1.0,
        crate_delivered=crate.meters["delivered"] >= 1.0,
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        captain=captain,
        frigate=frigate,
        crate=crate,
        chain=chain,
        gangway=gangway,
        place=place,
        scene=scene,
        intended_word="champagne",
        heard_word="chain",
        misunderstanding=True,
        path_blocked=False,
        delivered=crate.meters["delivered"] >= 1.0,
        resolved=resolved,
        problem=(
            "The helper mistook “champagne” for “chain, please,” and the loose "
            "safety chain blocked the gangway."
        ),
        action=(
            "The animals checked the crate label, asked the captain, rehung the "
            "chain, and carried the sealed crate together."
        ),
        result=(
            "The crate reached the pier, and the safety chain was back on its "
            "hooks so the gangway was clear."
        ),
        ending=(
            f"The sealed crate rested beneath a {place.pennant_color} pennant, "
            "while the chain hung neatly on its hooks behind it."
        ),
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        "Write a gentle animal story about a misunderstanding aboard a frigate.",
        (
            f"Tell how {facts['hero'].label} and {facts['helper'].label} "
            f"cleared up the mix-up over the champagne crate at "
            f"{facts['place'].label}."
        ),
        (
            "Show how listening, checking a label, and talking together can "
            "help animals fix a small problem."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question="What caused the problem on the frigate?",
            answer=(
                f"{facts['helper'].label} heard “chain, please” instead of "
                "“champagne.” The helper pulled the safety chain loose, and it "
                "looped across the gangway."
            ),
        ),
        QAItem(
            question="How did the animals fix the misunderstanding?",
            answer=(
                f"{facts['hero'].label} and {facts['helper'].label} checked the "
                "crate's label and asked Captain Fern what was meant. They rehung "
                "the chain, then carried the sealed champagne crate together."
            ),
        ),
        QAItem(
            question="What showed that everything was all right at the end?",
            answer=(
                f"{facts['ending']} The gangway was clear, and the crate had "
                "reached its welcome table."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frigate?",
            answer=(
                "A frigate is a kind of ship. In this story, the frigate is a "
                "sailing vessel with a deck, rigging, and a gangway."
            ),
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer=(
                "A misunderstanding happens when someone hears or understands "
                "something differently from what another person meant. Asking a "
                "question can help clear it up."
            ),
        ),
        QAItem(
            question="What was the champagne doing in the story?",
            answer=(
                "The champagne was packed in sealed bottles inside a crate for "
                "the grown-ups' harbor welcome. The animals carried the crate "
                "ashore without opening it."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(
        f"place={world.place.label!r} meters="
        f"{dict((k, v) for k, v in world.meters.items() if v)} "
        f"memes={dict((k, v) for k, v in world.memes.items() if v)}"
    )
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.label:22} ({entity.kind}/{entity.type}) "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(H,A,B,S) :- harbor(H), crew(A), crew(B), frigate(S), A != B.
misunderstood :- heard(chain), intended(champagne).
path_blocked :- misunderstood, chain_unhooked.
repaired :- path_blocked, ask_and_check, chain_restored.
resolved :- repaired, crate_delivered, cargo(champagne).
outcome(resolved) :- resolved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for harbor_id in PLACES:
        lines.append(asp.fact("harbor", harbor_id))
    for animal in ANIMALS.values():
        lines.append(asp.fact("animal", animal.id, animal.species))
        if animal.crew_member:
            lines.append(asp.fact("crew", animal.id))
    for frigate_id in FRIGATES:
        lines.append(asp.fact("frigate", frigate_id))

    # These facts encode the causal event simulated in tell().
    lines.extend(
        [
            asp.fact("intended", "champagne"),
            asp.fact("heard", "chain"),
            asp.fact("chain_unhooked"),
            asp.fact("ask_and_check"),
            asp.fact("chain_restored"),
            asp.fact("crate_delivered"),
            asp.fact("cargo", "champagne"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def _asp_outcome() -> bool:
    import asp

    model = asp.one_model(asp_program("#show outcome/1."))
    return ("resolved",) in set(asp.atoms(model, "outcome"))


def asp_verify() -> int:
    try:
        python_combos = sorted(valid_combos())
        solver_combos = asp_valid_combos()
        if solver_combos != python_combos:
            print("ASP/Python registry parity failed for valid story combinations.")
            return 1

        python_resolved = _python_causal_outcome(
            intended="champagne",
            heard="chain",
            chain_unhooked=True,
            conversation_checked=True,
            chain_restored=True,
            crate_delivered=True,
        )
        solver_resolved = _asp_outcome()
        if solver_resolved != python_resolved:
            print("ASP/Python causal outcome parity failed.")
            return 1

        for params in CURATED:
            sample = generate(params)
            if not sample.story.strip():
                raise RuntimeError("A generated story was empty.")
            if not sample.world.facts.get("resolved"):
                raise RuntimeError("A generated story did not resolve its problem.")
            if "champagne" not in sample.story.lower() or "frigate" not in sample.story.lower():
                raise RuntimeError("A generated story omitted a seed word.")
            if not any("“" in sentence and "”" in sentence for sentence in sample.story.split()):
                raise RuntimeError("A generated story omitted spoken dialogue.")
            if not sample.story_qa or not sample.world_qa:
                raise RuntimeError("A generated story is missing a Q&A set.")

        print(
            "OK: ASP/Python registry and causal parity passed; "
            "generated stories passed their smoke tests."
        )
        return 0
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1


CURATED = [
    StoryParams("saltglass_harbor", "brightwing", "Nori", "Pip", 1),
    StoryParams("moonwake_bay", "swift_petrel", "Mara", "Tavi", 7),
    StoryParams("reedlight_cove", "north_star", "Bram", "Lark", 11),
    StoryParams("saltglass_harbor", "north_star", "Kelp", "Wren", 14),
    StoryParams("moonwake_bay", "brightwing", "Pip", "Mara", 2),
    StoryParams("reedlight_cove", "swift_petrel", "Wren", "Nori", 5),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal stories about a champagne-and-chain misunderstanding aboard a frigate."
    )
    parser.add_argument("--harbor")
    parser.add_argument("--frigate", help="Registered frigate name (for example, brightwing).")
    parser.add_argument("--hero", help="Crew animal name.")
    parser.add_argument("--helper", help="A different crew animal name.")
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
    harbor = args.harbor or rng.choice(list(PLACES))
    frigate = args.frigate or rng.choice(list(FRIGATES))

    if args.hero:
        hero = _animal_for_name(args.hero)
    else:
        hero = ANIMALS[rng.choice(CREW_IDS)]

    if args.helper:
        helper = _animal_for_name(args.helper)
    else:
        helper_ids = [animal_id for animal_id in CREW_IDS if animal_id != hero.id]
        helper = ANIMALS[rng.choice(helper_ids)]

    return StoryParams(
        harbor=harbor,
        frigate=frigate,
        hero_name=hero.name,
        helper_name=helper.name,
        seed=args.seed,
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

    try:
        if args.show_asp:
            print(asp_program("#show valid_combo/4.\n#show outcome/1."))
            return
        if args.verify:
            raise SystemExit(asp_verify())
        if args.asp:
            print(asp_valid_combos())
            return
        if args.n < 1 and not args.all:
            raise StoryError("The number of requested stories must be at least one.")

        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            base_seed = args.seed if args.seed is not None else random.randrange(2**31)
            samples: list[StorySample] = []
            seen: set[str] = set()
            attempts = 0
            limit = max(100, args.n * 100)
            while len(samples) < args.n and attempts < limit:
                seed = base_seed + attempts
                attempts += 1
                params = resolve_params(args, random.Random(seed))
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
            header = f"### variant {index + 1}" if len(samples) > 1 else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
