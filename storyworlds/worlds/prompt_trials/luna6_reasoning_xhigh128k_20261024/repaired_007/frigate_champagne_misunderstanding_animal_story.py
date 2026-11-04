#!/usr/bin/env python3
"""
A small animal-story world about a gust of wind, a frigate, and a muddled word.

Piko hears “chain” when Captain Fern asks for the champagne. The world model
tracks the mistake, the ship's movement, the characters' feelings, and the
actions that return the frigate to a safe berth.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class PlaceSpec:
    id: str
    label: str


@dataclass(frozen=True)
class MisunderstandingSpec:
    id: str
    intended_word: str
    heard_word: str
    clue: str
    safe_repair: str
    ending_image: str


@dataclass
class World:
    place: Entity
    entities: dict[str, Entity] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    fired: set[str] = field(default_factory=set)
    events: list[str] = field(default_factory=list)
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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], bool]


def _r_misunderstanding(world: World) -> bool:
    hero = world.get("hero")
    captain = world.get("captain")
    if (
        world.meters["gust"] >= 1
        and hero.memes["heard_chain"] >= 1
        and captain.memes["made_request"] >= 1
        and "misunderstanding" not in world.fired
    ):
        world.fired.add("misunderstanding")
        world.meters["confusion"] = 1
        hero.memes["worry"] += 1
        world.events.append("A gust blurred the captain's request.")
        return True
    return False


def _r_raise_anchor_chain(world: World) -> bool:
    hero = world.get("hero")
    if (
        world.meters["confusion"] >= 1
        and hero.memes["turning_capstan"] >= 1
        and "anchor_chain_raised" not in world.fired
    ):
        world.fired.add("anchor_chain_raised")
        world.get("anchor_chain").meters["raised_links"] = 2
        world.get("anchor").meters["holding"] = 0
        world.get("frigate").meters["bow_near_fenders"] = 1
        world.get("helper").memes["alert"] += 1
        world.events.append("Two anchor-chain links rose and the tide nudged the bow.")
        return True
    return False


def _r_clarify(world: World) -> bool:
    hero = world.get("hero")
    if (
        world.meters["captain_clarified"] >= 1
        and world.meters["confusion"] >= 1
        and "clarification" not in world.fired
    ):
        world.fired.add("clarification")
        world.meters["confusion"] = 0
        hero.memes["understands"] = 1
        hero.memes["worry"] = 0
        world.events.append("The crew learned that the captain meant the bottle.")
        return True
    return False


def _r_restore_berth(world: World) -> bool:
    if (
        world.get("hero").memes["understands"] >= 1
        and world.get("hero").memes["lowering_chain"] >= 1
        and world.get("helper").memes["steadying_line"] >= 1
        and world.get("captain").memes["checking_anchor"] >= 1
        and "berth_restored" not in world.fired
    ):
        world.fired.add("berth_restored")
        world.get("anchor_chain").meters["raised_links"] = 0
        world.get("anchor").meters["holding"] = 1
        world.get("frigate").meters["bow_near_fenders"] = 0
        world.get("frigate").meters["securely_moored"] = 1
        world.get("hero").memes["relief"] += 1
        world.get("helper").memes["relief"] += 1
        world.meters["safe_berth_restored"] = 1
        world.events.append("The anchor held and the frigate settled safely at her berth.")
        return True
    return False


def _r_deliver_bottle(world: World) -> bool:
    bottle = world.get("champagne")
    if (
        world.meters["safe_berth_restored"] >= 1
        and bottle.memes["carried_up"] >= 1
        and bottle.meters["sealed"] >= 1
        and "welcome_ready" not in world.fired
    ):
        world.fired.add("welcome_ready")
        bottle.meters["on_chart_table"] = 1
        world.meters["welcome_ready"] = 1
        world.events.append("The sealed champagne reached the chart table.")
        return True
    return False


CAUSAL_RULES = [
    Rule("misunderstanding", _r_misunderstanding),
    Rule("raise_anchor_chain", _r_raise_anchor_chain),
    Rule("clarify", _r_clarify),
    Rule("restore_berth", _r_restore_berth),
    Rule("deliver_bottle", _r_deliver_bottle),
]


def propagate(world: World) -> list[str]:
    before = len(world.events)
    for _ in range(len(CAUSAL_RULES) + 3):
        changed = False
        for rule in CAUSAL_RULES:
            changed = rule.apply(world) or changed
        if not changed:
            break
    return world.events[before:]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    captain_name: str = "Fern"
    hero_species: str = "parrot"
    helper_species: str = "otter"
    mixup: str = "chain"
    seed: Optional[int] = None


PLACES = {
    "old_harbor": PlaceSpec("old_harbor", "Old Harbor"),
    "beacon_quay": PlaceSpec("beacon_quay", "Beacon Quay"),
    "blue_cove": PlaceSpec("blue_cove", "Blue Cove"),
}

ANIMALS = {
    "parrot": ["Piko", "Luma", "Kiki"],
    "otter": ["Moss", "Nori", "Ollie"],
    "seal": ["Pearl", "Finn", "Bubbles"],
    "mouse": ["Pip", "Tansy", "Mallow"],
}

CAPTAIN_NAMES = ["Tilda", "Fern", "Shellby"]

MISUNDERSTANDINGS = {
    "chain": MisunderstandingSpec(
        id="chain",
        intended_word="champagne",
        heard_word="chain",
        clue="A gust makes champagne sound like chain.",
        safe_repair="Lower the anchor chain, steady the spring line, and check the anchor.",
        ending_image="The sealed bottle rests beside the chart on a safely moored frigate.",
    )
}


def reasonable(place_id: str, mixup_id: str) -> bool:
    """Python reasonableness gate, mirrored by the inline ASP rules."""
    spec = MISUNDERSTANDINGS.get(mixup_id)
    return bool(
        place_id in PLACES
        and spec
        and spec.clue
        and spec.safe_repair
        and spec.ending_image
    )


def valid_combos() -> list[tuple[str, str]]:
    return sorted(
        (place_id, mixup_id)
        for place_id in PLACES
        for mixup_id in MISUNDERSTANDINGS
        if reasonable(place_id, mixup_id)
    )


CURATED = [
    StoryParams(
        place="old_harbor",
        hero_name="Piko",
        helper_name="Moss",
        captain_name="Fern",
        hero_species="parrot",
        helper_species="otter",
    ),
    StoryParams(
        place="beacon_quay",
        hero_name="Pip",
        helper_name="Pearl",
        captain_name="Tilda",
        hero_species="mouse",
        helper_species="seal",
    ),
    StoryParams(
        place="blue_cove",
        hero_name="Finn",
        helper_name="Luma",
        captain_name="Shellby",
        hero_species="seal",
        helper_species="parrot",
    ),
]


def _validate_name(name: str, role: str) -> str:
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z'-]*", name.strip()):
        raise StoryError(f"The {role} needs a simple character name made of letters.")
    return name.strip()


def _validate_params(params: StoryParams) -> MisunderstandingSpec:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place {params.place!r}; choose a registered harbor.")
    if params.hero_species not in ANIMALS:
        raise StoryError(f"Unknown hero animal {params.hero_species!r}.")
    if params.helper_species not in ANIMALS:
        raise StoryError(f"Unknown helper animal {params.helper_species!r}.")
    if not reasonable(params.place, params.mixup):
        raise StoryError(f"The misunderstanding {params.mixup!r} has no safe, supported resolution.")
    _validate_name(params.hero_name, "hero")
    _validate_name(params.helper_name, "helper")
    _validate_name(params.captain_name, "captain")
    names = {params.hero_name.casefold(), params.helper_name.casefold(), params.captain_name.casefold()}
    if len(names) != 3:
        raise StoryError("The hero, helper, and captain must have different names.")
    return MISUNDERSTANDINGS[params.mixup]


def tell(params: StoryParams, mixup: MisunderstandingSpec) -> World:
    place_spec = PLACES[params.place]
    place = Entity(
        id="place",
        kind="place",
        type="harbor",
        label=place_spec.label,
        tags={"safe_harbor"},
    )
    world = World(place=place)
    world.add(place)
    hero = world.add(
        Entity("hero", "character", params.hero_species, params.hero_name, role="hero")
    )
    helper = world.add(
        Entity("helper", "character", params.helper_species, params.helper_name, role="helper")
    )
    captain = world.add(
        Entity("captain", "character", "tortoise", params.captain_name, role="captain")
    )
    frigate = world.add(Entity("frigate", "vessel", "frigate", "Gullwing"))
    anchor = world.add(Entity("anchor", "object", "anchor", "the anchor"))
    chain = world.add(Entity("anchor_chain", "object", "chain", "the anchor chain"))
    bottle = world.add(
        Entity("champagne", "object", "champagne", "the sealed bottle of champagne")
    )
    world.add(Entity("crate", "object", "crate", "the padded crate"))
    world.add(Entity("chart_table", "object", "table", "the chart table"))
    world.add(Entity("spring_line", "object", "line", "the spring line"))
    world.add(Entity("fenders", "object", "fenders", "the soft fenders"))

    place.meters["safe_berth"] = 1
    frigate.meters["securely_moored"] = 1
    anchor.meters["holding"] = 1
    bottle.meters["sealed"] = 1
    world.meters["gust"] = 1
    captain.memes["made_request"] = 1
    hero.memes["heard_chain"] = 1
    hero.memes["turning_capstan"] = 1

    propagate(world)
    if world.meters["confusion"] < 1 or frigate.meters["bow_near_fenders"] < 1:
        raise StoryError("The misunderstanding did not produce its expected, safely contained problem.")

    world.say(
        f"At {place.label}, {hero.label} the {hero.type} and {helper.label} the "
        f"{helper.type} helped Captain {captain.label}, a patient tortoise, prepare "
        "a welcome aboard the frigate Gullwing."
    )
    world.say(
        "Below deck, a sealed bottle of champagne waited in a padded crate for the "
        "harbor keeper's grown-up celebration."
    )
    world.para()

    world.say(
        f"Captain {captain.label} called, “Bring the champagne up from below for "
        "the harbor keeper's welcome!”"
    )
    world.say(
        f"A gust snapped the pennants. {hero.label} heard “{mixup.heard_word}” "
        "instead, turned the capstan, and lifted two links of the anchor chain."
    )
    if chain.meters["raised_links"] >= 1 and frigate.meters["bow_near_fenders"] >= 1:
        world.say(
            "The tide nudged the frigate's bow toward the quay, but the mooring line "
            "stretched safely and the soft fenders kept the hull from bumping the stones."
        )
    world.para()

    world.say(
        f"“Why are you raising the anchor?” {helper.label} called. “I thought Captain "
        f"{captain.label} said ‘chain,’” {hero.label} replied. “I said ‘champagne,’” "
        f"Captain {captain.label} answered, pointing to the crate. “The bottle is our "
        "welcome gift. The anchor chain needs to stay down.”"
    )

    world.meters["captain_clarified"] = 1
    propagate(world)
    if hero.memes["understands"] < 1:
        raise StoryError("The captain's explanation did not clear up the misunderstanding.")

    world.say(
        f"“Oh—champagne, not chain! I understand now,” said {hero.label}. "
        f"“I'll lower the links. Can you watch the line?”"
    )
    world.say(
        f"“I'll keep it clear,” {helper.label} answered. “We can bring the bottle up "
        "when the frigate is steady.”"
    )

    hero.memes["lowering_chain"] = 1
    helper.memes["steadying_line"] = 1
    captain.memes["checking_anchor"] = 1
    propagate(world)
    if world.meters["safe_berth_restored"] < 1:
        raise StoryError("The crew's repair did not restore the frigate to a safe berth.")

    world.say(
        f"Together, {hero.label} eased the two links back down while {helper.label} "
        f"watched the spring line. Captain {captain.label} checked the anchor; it "
        "caught firmly, and the frigate swung safely away from the fenders."
    )
    world.para()

    bottle.memes["carried_up"] = 1
    propagate(world)
    if world.meters["welcome_ready"] < 1:
        raise StoryError("The welcome gift could not be safely brought aboard.")

    world.say(
        f"Once the frigate was steady, {hero.label} carried up the padded crate. "
        f"Captain {captain.label} set the sealed champagne beside the chart, while "
        f"{helper.label} tied bright pennants along the rail."
    )
    ending = (
        "At sunset, the harbor keeper stepped aboard to find the frigate resting "
        "quietly, the pennants fluttering, and the sealed champagne shining beside the chart."
    )
    world.say(ending)

    world.facts.update(
        hero=hero,
        helper=helper,
        captain=captain,
        place=place,
        frigate=frigate,
        anchor=anchor,
        chain=chain,
        champagne=bottle,
        mixup=mixup,
        problem=(
            f"A gust made {hero.label} hear “chain” when Captain {captain.label} "
            "asked for the champagne."
        ),
        effect=(
            "The anchor chain rose, so the tide nudged the frigate toward its fenders; "
            "the mooring line held it safely."
        ),
        action=(
            f"{hero.label} lowered the chain while {helper.label} watched the spring "
            f"line and Captain {captain.label} checked the anchor."
        ),
        result=(
            "The anchor caught again, the frigate settled safely at her berth, and "
            "the sealed bottle reached the chart table."
        ),
        ending=ending,
        actual_word=mixup.intended_word,
        heard_word=mixup.heard_word,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    mixup = _validate_params(params)
    world = tell(params, mixup)
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
        (
            f"Write a gentle animal story aboard the frigate Gullwing at "
            f"{facts['place'].label}. Include champagne, a gust-caused misunderstanding, "
            "spoken dialogue, and a safe, visible resolution."
        ),
        (
            f"Tell how {facts['hero'].label} and {facts['helper'].label} help Captain "
            f"{facts['captain'].label} when “champagne” is mistaken for “chain.”"
        ),
        "Write a child-friendly story in which listening carefully helps animal friends solve a problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].label
    helper = facts["helper"].label
    captain = facts["captain"].label
    return [
        QAItem(
            question="What did the hero misunderstand?",
            answer=(
                f"A gust blurred Captain {captain}'s request for champagne, so {hero} "
                "heard “chain” and began raising the anchor chain instead of fetching "
                "the sealed welcome bottle."
            ),
        ),
        QAItem(
            question="Why did the frigate's bow move toward the quay?",
            answer=(
                "As the anchor chain rose, the tide nudged the frigate toward the quay. "
                "Its mooring line and soft fenders held the ship safely while the crew "
                "worked out what had happened."
            ),
        ),
        QAItem(
            question="How did the animals fix the problem?",
            answer=(
                f"{hero} lowered the anchor chain while {helper} watched the spring "
                f"line, and Captain {captain} checked that the anchor caught. The "
                "frigate returned to a steady berth before they brought up the bottle."
            ),
        ),
        QAItem(
            question="What final image showed that the welcome was ready?",
            answer=f"{facts['ending']} The safely moored ship and the bottle beside the chart showed that the mistake had been put right.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frigate?",
            answer=(
                "A frigate is a kind of ship that can travel across the sea. Anchors "
                "and mooring lines help keep a ship in place when it stops."
            ),
        ),
        QAItem(
            question="What is champagne?",
            answer=(
                "Champagne is a sparkling drink that is often saved for a celebration. "
                "In this story, the bottle stays sealed as a grown-up welcome gift."
            ),
        ),
        QAItem(
            question="How can a misunderstanding be cleared up?",
            answer=(
                "People can stop, ask what someone meant, and listen to the explanation. "
                "That can help everyone choose a safer and more helpful next step."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:14} ({entity.kind}/{entity.type}) "
            f"{' '.join(details)}"
        )
    lines.append(f"  world          meters={dict(world.meters)}")
    lines.append(f"  events         {world.events}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(P,M) :-
    place(P),
    misunderstanding(M),
    clue(M),
    safe_repair(M),
    ending_image(M).

can_resolve(M) :-
    reasonable(P,M),
    safe_repair(M),
    ending_image(M).

#show reasonable/2.
#show can_resolve/1.
"""


def asp_facts() -> str:
    from storyworlds import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for mixup_id, spec in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mixup_id))
        if spec.clue:
            lines.append(asp.fact("clue", mixup_id))
        if spec.safe_repair:
            lines.append(asp.fact("safe_repair", mixup_id))
        if spec.ending_image:
            lines.append(asp.fact("ending_image", mixup_id))
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/2.\n#show can_resolve/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    from storyworlds import asp

    try:
        model = asp.one_model(asp_program())
        python_combos = valid_combos()
        asp_combos = sorted(set(asp.atoms(model, "reasonable")))
        if asp_combos != python_combos:
            print(f"ASP/Python parity failed: ASP={asp_combos}, Python={python_combos}")
            return 1
        resolved = set(asp.atoms(model, "can_resolve"))
        if ("chain",) not in resolved:
            print("ASP resolution check failed: the chain misunderstanding has no safe ending.")
            return 1

        for params in CURATED:
            sample = generate(params)
            if "frigate" not in sample.story.lower() or "champagne" not in sample.story.lower():
                print("A generated story omitted a required seed word.")
                return 1
            if "“" not in sample.story or "?”" not in sample.story and "?”" not in sample.story:
                # The story also contains spoken statements that do not end in a question.
                if "“" not in sample.story or "”" not in sample.story:
                    print("A generated story is missing its spoken dialogue.")
                    return 1
            if sample.world is None or sample.world.meters["welcome_ready"] < 1:
                print("A generated story did not reach its welcome-ready ending.")
                return 1
            if not sample.story_qa or not sample.world_qa:
                print("A generated story is missing a question-and-answer set.")
                return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1

    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="An animal-story world about a frigate and a champagne mix-up."
    )
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--captain")
    parser.add_argument("--hero-species", choices=list(ANIMALS))
    parser.add_argument("--helper-species", choices=list(ANIMALS))
    parser.add_argument("--mixup", choices=list(MISUNDERSTANDINGS))
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero_species = getattr(args, "hero_species", None) or rng.choice(list(ANIMALS))
    helper_species = getattr(args, "helper_species", None) or rng.choice(list(ANIMALS))

    hero_name = getattr(args, "hero", None) or rng.choice(ANIMALS[hero_species])
    helper_candidates = [name for name in ANIMALS[helper_species] if name.casefold() != hero_name.casefold()]
    if not helper_candidates:
        helper_candidates = list(ANIMALS[helper_species])
    helper_name = getattr(args, "helper", None) or rng.choice(helper_candidates)

    captain_name = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    mixup = getattr(args, "mixup", None) or rng.choice(list(MISUNDERSTANDINGS))
    return StoryParams(
        place=place,
        hero_name=hero_name,
        helper_name=helper_name,
        captain_name=captain_name,
        hero_species=hero_species,
        helper_species=helper_species,
        mixup=mixup,
        seed=getattr(args, "seed", None),
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
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    if not args.all and args.n < 1:
        parser.error("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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


if __name__ == "__main__":
    main()
