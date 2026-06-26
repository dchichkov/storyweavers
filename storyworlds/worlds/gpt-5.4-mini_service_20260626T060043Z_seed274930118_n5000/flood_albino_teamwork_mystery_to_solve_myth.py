#!/usr/bin/env python3
"""
storyworlds/worlds/flood_albino_teamwork_mystery_to_solve_myth.py
==================================================================

A small mythic story world about a flood, an albino sign-bearer, teamwork,
and a mystery to solve.

Premise:
- A river-people village is threatened by a flood.
- An albino white heron/fox/etc. is treated as an omen and becomes a helper.
- The mystery is why the water rose so fast.
- The answer is physical and causal: an upstream rootwall trapped the stream,
  and the villagers must work together to open a safe channel.

The simulation keeps two kinds of state:
- physical meters: water level, barrier strength, rescue progress, clarity
- emotional memes: fear, trust, hope, wonder, unity

The prose is state-driven; the ending image proves what changed.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "sister", "priestess"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "brother", "chief"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    river: str
    floodplain: bool
    features: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    omen: str
    hero: str
    role: str
    helper: str
    seed: Optional[int] = None


@dataclass
class StoryWorld:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "StoryWorld":
        import copy as _copy
        clone = StoryWorld(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = _copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "riverbend": Place(
        name="Riverbend",
        river="the silver river",
        floodplain=True,
        features=["reed beds", "stone steps", "old willow roots"],
    ),
    "moonford": Place(
        name="Moonford",
        river="the bright river",
        floodplain=True,
        features=["a ford", "hanging lanterns", "root tunnels"],
    ),
    "sunharbor": Place(
        name="Sunharbor",
        river="the old river",
        floodplain=True,
        features=["a quay", "sandbags", "a watch hill"],
    ),
}

OMENS = {
    "albino heron": {
        "type": "bird",
        "label": "albino heron",
        "phrase": "a white heron with pale eyes",
        "name": "White-Feather",
    },
    "albino fox": {
        "type": "fox",
        "label": "albino fox",
        "phrase": "a white fox with a silver tail",
        "name": "Milk-Tail",
    },
    "albino deer": {
        "type": "deer",
        "label": "albino deer",
        "phrase": "a white deer that moved like mist",
        "name": "Mist-Hoof",
    },
}

HEROES = {
    "girl": ["Asha", "Mira", "Ira", "Nala", "Tia"],
    "boy": ["Kian", "Rafi", "Eli", "Soren", "Taro"],
    "woman": ["Lina", "Mara", "Sera", "Nira", "Vela"],
    "man": ["Orin", "Daro", "Pavel", "Ivo", "Neru"],
}

HELPERS = {
    "fisher": "fisher",
    "potter": "potter",
    "child": "child",
    "priestess": "priestess",
    "chief": "chief",
}

TRAITS = ["brave", "quiet", "patient", "curious", "steady"]


class World(StoryWorld):
    pass


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.role,
        label=params.hero,
        helper=False,
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        helper=True,
    ))
    omen_def = OMENS[params.omen]
    omen = world.add(Entity(
        id="Omen",
        kind="character",
        type=omen_def["type"],
        label=omen_def["label"],
        phrase=omen_def["phrase"],
        helper=True,
    ))

    river = world.add(Entity(
        id="River",
        kind="thing",
        type="river",
        label=place.river,
        meters={"water": 2.5, "flow": 2.0, "blocked": 0.0, "clarity": 0.2},
    ))
    village = world.add(Entity(
        id="Village",
        kind="thing",
        type="village",
        label=place.name,
        meters={"safe": 0.2, "damage": 0.0, "rescue": 0.0},
        memes={"fear": 0.0, "hope": 0.2, "trust": 0.2, "wonder": 0.5, "unity": 0.0},
    ))
    roots = world.add(Entity(
        id="Roots",
        kind="thing",
        type="barrier",
        label="a tangle of willow roots",
        meters={"strength": 2.0, "hidden": 1.0},
    ))
    tools = world.add(Entity(
        id="Tools",
        kind="thing",
        type="tools",
        label="ropes and poles",
        plural=True,
        meters={"available": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, omen=omen, river=river, village=village, roots=roots, tools=tools)
    return world


def flood_rises(world: World) -> None:
    river = world.get("River")
    village = world.get("Village")
    roots = world.get("Roots")
    if ("flood",) not in world.fired:
        world.fired.add(("flood",))
        river.meters["water"] += 1.5
        river.meters["blocked"] += 1.0
        village.meters["safe"] -= 0.4
        village.memes["fear"] += 1.0
        village.memes["wonder"] += 0.5
        world.say(
            f"One dusk, the silver river rose against the banks, and the folk of {world.place.name} "
            f"heard the first hard rush of floodwater."
        )
        world.say(
            f"Under the willow roots, something held the current back, and the trapped water grew wild."
        )


def omen_arrives(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    omen = world.get("Omen")
    village = world.get("Village")
    if ("omen",) not in world.fired:
        world.fired.add(("omen",))
        village.memes["wonder"] += 0.5
        world.say(
            f"In the pale light came {omen.phrase}, and the people whispered that the old signs had returned."
        )
        world.say(
            f"{hero.id} did not turn away. {hero.pronoun().capitalize()} watched the white creature and felt there must be a reason for its coming."
        )


def call_team(world: World) -> None:
    helper = world.get("Helper")
    village = world.get("Village")
    if ("team",) not in world.fired:
        world.fired.add(("team",))
        village.memes["trust"] += 0.7
        village.memes["unity"] += 1.0
        world.say(
            f"The {helper.type} called the neighbors to gather with ropes, baskets, and strong hands."
        )
        world.say(
            f"No single pair of arms could hold back the flood, so they stood together like one body."
        )


def investigate(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    omen = world.get("Omen")
    roots = world.get("Roots")
    river = world.get("River")
    village = world.get("Village")
    if ("mystery",) not in world.fired:
        world.fired.add(("mystery",))
        village.memes["fear"] += 0.3
        world.say(
            f"{hero.id} followed {omen.pronoun('object')} to the willow bank, where the water spun in a circle."
        )
        world.say(
            f"There they found the secret: the roots had caught driftwood and stones, and the river could not breathe."
        )
        world.say(
            f"That was why the flood had climbed so fast."
        )
        world.facts["mystery_solved"] = True
        roots.meters["hidden"] = 0.0
        river.meters["clarity"] += 0.6


def work_together(world: World) -> None:
    village = world.get("Village")
    river = world.get("River")
    roots = world.get("Roots")
    if ("work",) not in world.fired:
        world.fired.add(("work",))
        river.meters["blocked"] = 0.0
        river.meters["water"] = max(0.5, river.meters["water"] - 1.6)
        village.meters["safe"] += 1.2
        village.meters["rescue"] += 1.0
        village.memes["fear"] = max(0.0, village.memes["fear"] - 0.8)
        village.memes["hope"] += 1.0
        village.memes["unity"] += 1.0
        world.say(
            f"Then all together they pulled the driftwood free, lifted stones from the choke, and opened a narrow path for the river."
        )
        world.say(
            f"The flood loosened, rushed onward, and the bank stopped shaking."
        )


def ending_image(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    omen = world.get("Omen")
    village = world.get("Village")
    river = world.get("River")
    if ("end",) not in world.fired:
        world.fired.add(("end",))
        village.memes["trust"] += 0.4
        world.say(
            f"By morning the water lay calm again. {hero.id}, the white {omen.type}, and the whole village stood together on the wet stones."
        )
        world.say(
            f"Where fear had stood, there was only mud, shining reeds, and the memory of many hands making one rescue."
        )


def tell_story(world: World) -> World:
    flood_rises(world)
    world.para()
    omen_arrives(world)
    investigate(world)
    world.para()
    call_team(world)
    work_together(world)
    ending_image(world)
    return world


def story_quality_gate(world: World) -> None:
    village = world.get("Village")
    river = world.get("River")
    if world.facts.get("mystery_solved") is not True:
        raise StoryError("The mystery was not solved.")
    if village.meters["safe"] < THRESHOLD:
        raise StoryError("The village did not become safe enough for a complete story.")
    if river.meters["blocked"] > 0.1:
        raise StoryError("The river remained blocked; teamwork did not resolve the flood.")


def valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for place in PLACES:
        for omen in OMENS:
            pairs.append((place, omen))
    return pairs


def aspire_reasonable(params: StoryParams) -> bool:
    return params.place in PLACES and params.omen in OMENS and params.role in HEROES and params.helper in HELPERS


ASP_RULES = r"""
place(P) :- setting(P).
omen(O) :- omen_kind(O).
role(R) :- hero_role(R).
helper(H) :- helper_kind(H).

story_ok(P,O,R,H) :- place(P), omen(O), role(R), helper(H).
#show story_ok/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for o in OMENS:
        lines.append(asp.fact("omen_kind", o))
    for r in HEROES:
        lines.append(asp.fact("hero_role", r))
    for h in HELPERS:
        lines.append(asp.fact("helper_kind", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/4."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = {(a, b) for (a, b, c, d) in asp_valid_combos()}
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} story setups.")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic flood story world with an albino omen and teamwork.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--omen", choices=sorted(OMENS))
    ap.add_argument("--role", choices=sorted(HEROES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    omen = args.omen or rng.choice(sorted(OMENS))
    role = args.role or rng.choice(sorted(HEROES))
    helper = args.helper or rng.choice(sorted(HELPERS))
    if args.name:
        hero = args.name
    else:
        hero = rng.choice(HEROES[role])
    if not aspire_reasonable(StoryParams(place=place, omen=omen, hero=hero, role=role, helper=helper)):
        raise StoryError("The chosen story ingredients do not fit this mythic flood world.")
    return StoryParams(place=place, omen=omen, hero=hero, role=role, helper=helper)


def story_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a mythic story about a flood in {params.place} and an {params.omen} who helps solve a mystery.",
        f"Tell a child-friendly legend where {params.hero} and the villagers use teamwork to understand why the river rose.",
        f"Make a short myth about a flood, an albino sign-bearer, and a secret hidden in the riverbank roots.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    omen = world.facts["omen"]
    village = world.facts["village"]
    return [
        QAItem(
            question=f"Who helped {hero.id} look into the flood mystery?",
            answer=f"{hero.id} was helped by {omen.label} and the {helper.type} who gathered the village together.",
        ),
        QAItem(
            question=f"What caused the flood to rise so fast in {world.place.name}?",
            answer="The water was trapped by a tangle of willow roots and driftwood, so it could not flow freely.",
        ),
        QAItem(
            question=f"How did the people of {world.place.name} solve the problem?",
            answer="They worked together to pull the blockage free and open a safe path for the river.",
        ),
        QAItem(
            question=f"What changed in the village by the end of the story?",
            answer="The flood eased, fear fell away, and the people stood in safety with more trust and unity than before.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flood?",
            answer="A flood is when too much water covers land that is usually dry.",
        ),
        QAItem(
            question="What does albino mean?",
            answer="Albino means an animal or person is born with very little color in its skin, fur, feathers, or eyes.",
        ),
        QAItem(
            question="Why is teamwork important when a flood comes?",
            answer="Teamwork lets many people use their strength together, which can help solve a big problem that one person cannot fix alone.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzling thing that needs clues and careful thinking before anyone understands it.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    story_quality_gate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbend", omen="albino heron", hero="Asha", role="girl", helper="fisher"),
    StoryParams(place="moonford", omen="albino fox", hero="Kian", role="boy", helper="priestess"),
    StoryParams(place="sunharbor", omen="albino deer", hero="Mara", role="woman", helper="chief"),
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


def asp_program_for_verify() -> str:
    return asp_program("#show story_ok/4.")


def asp_main_list() -> None:
    import asp
    model = asp.one_model(asp_program("#show story_ok/4."))
    combos = sorted(set(asp.atoms(model, "story_ok")))
    print(f"{len(combos)} story setups:")
    for combo in combos:
        print("  ", combo)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_for_verify())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_main_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
