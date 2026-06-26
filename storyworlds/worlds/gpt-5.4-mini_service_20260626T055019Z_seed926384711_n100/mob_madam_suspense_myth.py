#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/mob_madam_suspense_myth.py
========================================================================================================

A tiny mythic suspense storyworld built from the seed words "mob" and "madam".

Premise:
- A small village mob gathers in the dusk.
- A calm madam keeps a lantern, a key, and a secret reason for moving slowly.
- Suspense comes from the crowd's fear of the dark gate and the missing moon charm.
- The turn is a reveal: the madam has been protecting the charm from the night wind.
- The resolution is a shared, gentle ritual that sends the mob home transformed.

The story model uses:
- Physical meters: distance, light, noise, fear, safety, chill, hunger, trust
- Emotional memes: worry, courage, suspicion, wonder, relief, reverence

The narrative is authored from state changes rather than from a frozen paragraph.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key in ["distance", "light", "noise", "fear", "safety", "chill", "hunger", "trust"]:
            self.meters.setdefault(key, 0.0)
        for key in ["worry", "courage", "suspicion", "wonder", "relief", "reverence", "patience"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"madam", "woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("distance", 0.0)
        self.meters.setdefault("light", 0.0)
        self.meters.setdefault("noise", 0.0)
        self.meters.setdefault("safety", 0.0)
        self.meters.setdefault("chill", 0.0)
        self.memes.setdefault("wonder", 0.0)
        self.memes.setdefault("reverence", 0.0)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(place=_copy.deepcopy(self.place))
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    crowd: str = "village mob"
    madam: str = "madam"
    charm: str = "moon charm"
    place: str = "the old gate"
    weather: str = "fog"
    tone: str = "suspense"


CROWD_WORDS = {
    "village mob": ("village mob", True),
    "market mob": ("market mob", True),
    "little mob": ("little mob", True),
}

MADAM_NAMES = {
    "madam": "madam",
    "Madam Ivy": "Madam Ivy",
    "Madam Noor": "Madam Noor",
    "Madam Sol": "Madam Sol",
}

PLACES = {
    "the old gate": "the old gate",
    "the hill path": "the hill path",
    "the stone well": "the stone well",
}

CHARMS = {
    "moon charm": "moon charm",
    "silver charm": "silver charm",
    "bright charm": "bright charm",
}

WEATHERS = {
    "fog": "fog",
    "night wind": "night wind",
    "cold dusk": "cold dusk",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
crowd(C) :- crowd_name(C).
madam(M) :- madam_name(M).
charm(T) :- charm_name(T).

suspense(C, M, T, P) :- crowd(C), madam(M), charm(T), place(P).

resolved(C, M, T, P) :- suspense(C, M, T, P), calm_path(P), safe_keep(T), shared_light(C, M).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for k in CROWD_WORDS:
        lines.append(asp.fact("crowd_name", k))
    for k in MADAM_NAMES:
        lines.append(asp.fact("madam_name", k))
    for k in CHARMS:
        lines.append(asp.fact("charm_name", k))
    for k in PLACES:
        lines.append(asp.fact("place", k))
    for k in ["the old gate", "the hill path", "the stone well"]:
        lines.append(asp.fact("calm_path", k))
    lines.append(asp.fact("safe_keep", "moon charm"))
    lines.append(asp.fact("shared_light", "village mob", "madam"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/4."))
    asp_set = set(asp.atoms(model, "resolved"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for crowd in CROWD_WORDS:
        for madam in MADAM_NAMES:
            for charm in CHARMS:
                for place in PLACES:
                    combos.append((crowd, madam, charm, place))
    return combos


def explain_invalid() -> str:
    return "(No story: the mob, madam, charm, and place must all be chosen from the registries.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    place = Place(name=PLACES[params.place])
    world = World(place=place)

    mob = world.add(Entity(
        id="mob",
        kind="character",
        type="mob",
        label=params.crowd,
        plural=True,
        meters={"distance": 6.0, "noise": 4.0, "fear": 2.0, "trust": 1.0, "safety": 1.0},
        memes={"worry": 2.0, "suspicion": 2.0, "wonder": 1.0},
    ))
    madam = world.add(Entity(
        id="madam",
        kind="character",
        type="madam",
        label=params.madam,
        meters={"distance": 1.0, "light": 2.0, "noise": 0.0, "safety": 3.0, "trust": 3.0},
        memes={"patience": 3.0, "reverence": 2.0, "wonder": 1.0},
    ))
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type="charm",
        label=params.charm,
        phrase=f"a small {params.charm}",
        owner="madam",
        carried_by="madam",
        hidden=True,
        meters={"light": 2.0, "safety": 1.0},
        memes={"wonder": 2.0},
    ))

    world.facts.update(params=params, mob=mob, madam=madam, charm=charm, place=place)
    return world


def forecast_danger(world: World) -> bool:
    mob = world.get("mob")
    madam = world.get("madam")
    charm = world.get("charm")
    return mob.memes["suspicion"] >= 1.0 and charm.hidden and madam.carried_by != "mob"


def opening(world: World) -> None:
    mob = world.get("mob")
    madam = world.get("madam")
    place = world.place.name
    world.say(
        f"At {place}, a small {mob.label} gathered under the dim sky."
    )
    world.say(
        f"Near the gate stood {madam.label}, calm as a candle, holding a secret the crowd could not yet see."
    )


def suspense_beats(world: World) -> None:
    mob = world.get("mob")
    madam = world.get("madam")
    charm = world.get("charm")

    mob.memes["suspicion"] += 1.0
    mob.memes["worry"] += 1.0
    mob.meters["noise"] += 1.0
    world.place.meters["chill"] += 1.0
    world.say(
        f"The {mob.label} whispered and shuffled closer, for the fog made every shadow look like a warning."
    )
    world.say(
        f"Some feared {madam.label} had hidden the {charm.label} away."
    )

    if forecast_danger(world):
        mob.memes["wonder"] += 1.0
        world.say(
            f"But {madam.label} did not flinch; she only lifted her lantern and asked the crowd to look before they judged."
        )
        world.say(
            f"Her steady voice made the waiting feel even sharper, as if the night itself had paused to listen."
        )


def reveal(world: World) -> None:
    mob = world.get("mob")
    madam = world.get("madam")
    charm = world.get("charm")

    charm.hidden = False
    charm.carried_by = None
    world.place.meters["light"] += 2.0
    mob.memes["suspicion"] -= 1.5
    mob.memes["wonder"] += 1.5
    madam.memes["reverence"] += 1.0
    world.say(
        f"At last, {madam.label} opened her palm, and there lay the {charm.label}, safe from the night wind."
    )
    world.say(
        f"She had kept it close so the little glow would not be swallowed before dawn."
    )


def shared_ritual(world: World) -> None:
    mob = world.get("mob")
    madam = world.get("madam")
    charm = world.get("charm")

    mob.memes["courage"] += 1.5
    mob.memes["relief"] += 2.0
    mob.meters["fear"] = max(0.0, mob.meters["fear"] - 1.5)
    mob.meters["trust"] += 2.0
    world.place.meters["safety"] += 2.0
    world.say(
        f"Then the {mob.label} formed a soft ring around {madam.label}, and together they carried the glow across the path."
    )
    world.say(
        f"The {charm.label} shone on the stones, and the crowd learned that patience can guard what fear cannot understand."
    )


def ending_image(world: World) -> None:
    mob = world.get("mob")
    madam = world.get("madam")
    charm = world.get("charm")
    world.para()
    world.say(
        f"When the story ended, the {mob.label} went home quieter than before, and {madam.label} walked beside them with the {charm.label} shining like a tiny moon."
    )


def build_story(world: World) -> None:
    opening(world)
    world.para()
    suspense_beats(world)
    world.para()
    reveal(world)
    shared_ritual(world)
    ending_image(world)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short myth-like story about a {p.crowd} and {p.madam} at {p.place} during {p.weather}.",
        f"Tell a suspenseful, child-friendly tale where {p.madam} protects the {p.charm} from the night.",
        f"Write a gentle myth in which a crowd learns why a {p.madam} kept a glowing charm hidden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Where did the {p.crowd} gather?",
            answer=f"The {p.crowd} gathered at {p.place}, where the air felt still and the sky looked dim.",
        ),
        QAItem(
            question=f"Why were some of the crowd afraid of {p.madam}?",
            answer=f"Some of the crowd suspected {p.madam} had hidden the {p.charm}, so they worried before they understood her reason.",
        ),
        QAItem(
            question=f"What did {p.madam} do with the {p.charm} in the end?",
            answer=f"{p.madam} opened her palm and showed the {p.charm}, revealing that she had kept it safe from the night wind.",
        ),
        QAItem(
            question="How did the story end for the crowd?",
            answer="The crowd calmed down, shared the light, and went home wiser and quieter than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What is a mob?",
            answer="A mob is a crowd of many people gathered closely together, often because they are excited, worried, or angry.",
        ),
        QAItem(
            question="What is a madam?",
            answer="A madam is a respectful word for a woman, often someone who seems wise, formal, or important in a story.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important is about to happen, so the reader wants to know what will come next.",
        ),
        QAItem(
            question="Why might a charm be kept safe?",
            answer="A charm might be kept safe because it is special, fragile, or important to the people who care for it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(crowd="village mob", madam="madam", charm="moon charm", place="the old gate", weather="fog", tone="suspense"),
    StoryParams(crowd="market mob", madam="Madam Ivy", charm="silver charm", place="the hill path", weather="night wind", tone="suspense"),
    StoryParams(crowd="little mob", madam="Madam Noor", charm="bright charm", place="the stone well", weather="cold dusk", tone="suspense"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    crowd = args.crowd or rng.choice(list(CROWD_WORDS))
    madam = args.madam or rng.choice(list(MADAM_NAMES))
    charm = args.charm or rng.choice(list(CHARMS))
    place = args.place or rng.choice(list(PLACES))
    weather = args.weather or rng.choice(list(WEATHERS))
    tone = "suspense"
    if crowd not in CROWD_WORDS or madam not in MADAM_NAMES or charm not in CHARMS or place not in PLACES:
        raise StoryError(explain_invalid())
    return StoryParams(seed=None, crowd=crowd, madam=madam, charm=charm, place=place, weather=weather, tone=tone)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    build_story(world)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.name}")
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id}: {', '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic suspense storyworld about a mob and a madam.")
    ap.add_argument("--crowd", choices=list(CROWD_WORDS))
    ap.add_argument("--madam", choices=list(MADAM_NAMES))
    ap.add_argument("--charm", choices=list(CHARMS))
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--weather", choices=list(WEATHERS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show resolved/4."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combinations:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
