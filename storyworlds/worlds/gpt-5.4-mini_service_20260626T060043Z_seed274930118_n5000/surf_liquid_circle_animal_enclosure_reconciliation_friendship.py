#!/usr/bin/env python3
"""
A mythic storyworld about a small animal enclosure, a bright liquid circle,
and a tide of friendship that must be reconciled through magic.

The seed image:
- surf
- liquid
- circle

The domain:
- an animal enclosure where a sea lion, a keeper, and a shy visitor must
  reconcile after a splashy mistake
- mythic tone, child-facing, with a clear turn and ending image
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
# Registry / world constants
# ---------------------------------------------------------------------------

ANIMAL_KINDS = {
    "seal": {
        "sound": "bark",
        "habitat": "the pool edge",
        "traits": ["playful", "spry", "curious"],
    },
    "otter": {
        "sound": "chirrup",
        "habitat": "the reeds",
        "traits": ["nimble", "bright-eyed", "merry"],
    },
    "penguin": {
        "sound": "honk",
        "habitat": "the cold stone",
        "traits": ["neat", "brave", "gentle"],
    },
}

KEEPERS = {
    "keeper": {"title": "the keeper", "tone": "patient"},
    "warden": {"title": "the warden", "tone": "careful"},
}

MAGICS = {
    "moonspell": {
        "name": "moonspell",
        "gift": "silver calm",
        "effect": "made the water shine like a path",
    },
    "tidecharm": {
        "name": "tidecharm",
        "gift": "soft tides",
        "effect": "turned the splash into a gentle circle",
    },
    "starwhisper": {
        "name": "starwhisper",
        "gift": "starry peace",
        "effect": "let old hurts drift away",
    },
}

SETTINGS = {
    "animal enclosure": {
        "place": "the animal enclosure",
        "features": {"surf", "liquid", "circle"},
    }
}

# ---------------------------------------------------------------------------
# Shared result model: physical meters and emotional memes
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    name: str = ""
    species: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: str
    features: set[str]
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "World":
        import copy

        return World(
            place=self.place,
            features=set(self.features),
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
        )


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    animal: str
    keeper: str
    magic: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------


def build_world(params: StoryParams) -> World:
    cfg_a = ANIMAL_KINDS[params.animal]
    cfg_k = KEEPERS[params.keeper]
    cfg_m = MAGICS[params.magic]
    world = World(place=SETTINGS["animal enclosure"]["place"], features=set(SETTINGS["animal enclosure"]["features"]))

    animal = world.add(
        Entity(
            id="animal",
            kind="character",
            label=params.name,
            name=params.name,
            species=params.animal,
            meters={"surge": 0.0, "wet": 0.0},
            memes={"friendship": 2.0, "worry": 0.0, "joy": 0.0, "hurt": 0.0, "reconcile": 0.0},
        )
    )
    keeper = world.add(
        Entity(
            id="keeper",
            kind="character",
            label=cfg_k["title"],
            role=cfg_k["title"],
            meters={"wet": 0.0},
            memes={"friendship": 2.0, "worry": 0.0, "joy": 0.0, "reconcile": 0.0},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            label="a small visitor",
            species="child",
            meters={"wet": 0.0},
            memes={"friendship": 3.0, "fear": 0.0, "joy": 0.0},
        )
    )
    pool = world.add(
        Entity(
            id="pool",
            kind="thing",
            label="a round pool",
            meters={"liquid": 5.0, "circle": 1.0, "surf": 1.0},
        )
    )
    charm = world.add(
        Entity(
            id="charm",
            kind="thing",
            label=cfg_m["name"],
            owner="keeper",
            meters={"magic": 1.0},
            memes={"magic": 2.0},
        )
    )

    world.facts.update(
        animal=animal,
        keeper=keeper,
        friend=friend,
        pool=pool,
        charm=charm,
        magic=cfg_m,
        cfg_a=cfg_a,
        cfg_k=cfg_k,
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    animal = world.get("animal")
    keeper = world.get("keeper")
    friend = world.get("friend")
    pool = world.get("pool")
    charm = world.get("charm")
    cfg_a = world.facts["cfg_a"]
    cfg_m = world.facts["magic"]

    world.say(
        f"In the animal enclosure, {animal.label} the {animal.species} loved the round pool, "
        f"where the liquid made a shining circle and the surf licked the stone."
    )
    world.say(
        f"{keeper.label.capitalize()} watched kindly, and the little visitor came with a grin, "
        f"hoping to share the day with the bright animal."
    )

    world.para()
    animal.memes["joy"] += 1
    animal.meters["surge"] += 1
    world.say(
        f"{animal.label} darted through the surf at the edge of the pool, and the water leapt high."
    )
    friend.meters["wet"] += 1
    friend.memes["fear"] += 1
    keeper.meters["wet"] += 1
    keeper.memes["worry"] += 1
    world.say(
        f"The splash reached the visitor's sleeves, and the child stepped back, surprised."
    )
    world.say(
        f"{keeper.label.capitalize()} saw the hurt look and knew that a small shadow had fallen between new friends."
    )

    world.para()
    keeper.memes["reconcile"] += 1
    animal.memes["hurt"] += 1
    world.say(
        f"Then {keeper.label} lifted {charm.label} and whispered a {cfg_m['name']}."
    )
    world.say(
        f"The magic {cfg_m['effect']}, and the water softened into a gentle circle instead of a wild spray."
    )
    friend.memes["fear"] = 0.0
    friend.memes["joy"] += 1
    animal.memes["reconcile"] += 1
    animal.memes["friendship"] += 1
    keeper.memes["joy"] += 1

    world.para()
    world.say(
        f"{animal.label} blinked, then nudged the visitor with a warm nose, as if asking to begin again."
    )
    world.say(
        f"The child laughed and reached out a hand. The keeper smiled, and all three stood beside the pool like a tiny treaty."
    )
    world.say(
        f"By the end, the surf was only a shimmer, the liquid was calm, and the circle of water held their friendship like a mirror."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    animal = world.facts["animal"]
    keeper = world.facts["keeper"]
    return [
        'Write a short mythic story for children about surf, liquid, and a circle in an animal enclosure.',
        f"Tell a gentle myth where {animal.label} splashes too hard, {keeper.label} helps, and friendship is restored by magic.",
        "Write a tiny reconciliation tale in a zoo-like place where water makes a circle and a friendship becomes calm again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    animal = world.facts["animal"]
    keeper = world.facts["keeper"]
    friend = world.facts["friend"]
    charm = world.facts["charm"]
    return [
        QAItem(
            question=f"Where did {animal.label} play?",
            answer="They played in the animal enclosure beside a round pool of water.",
        ),
        QAItem(
            question=f"What problem happened when {animal.label} rushed through the surf?",
            answer=f"The splash wet the small visitor, and the visitor felt surprised and hurt.",
        ),
        QAItem(
            question=f"How did {keeper.label} help everyone feel better again?",
            answer=f"The keeper used the magic charm to soften the water, so the friends could forgive one another and begin again.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The splash became gentle, the hurt was mended, and friendship stayed beside the calm water.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a circle?",
            answer="A circle is a round shape with no corners.",
        ),
        QAItem(
            question="What is liquid?",
            answer="Liquid is a thing that can flow and pour, like water.",
        ),
        QAItem(
            question="What is surf?",
            answer="Surf is the moving top of water when waves break and foam.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after people or friends have been upset.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people or animals who like and help one another.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is a wondrous power that can change what happens in surprising ways.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when it keeps the mythic shape:
% an animal in an enclosure, liquid water in a circle, a splash,
% and a reconciliation through magic.

valid_place(enclosure) :- enclosure(animal_enclosure).
valid_story(A, K, M) :- animal(A), keeper(K), magic(M).

splash_event(A) :- animal(A), surf(A).
hurt_event(F) :- friend(F), wet(F).
reconcile_event(K, A, F) :- keeper(K), animal(A), friend(F), magic(M).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("enclosure", "animal_enclosure"))
    lines.append(asp.fact("animal", "seal"))
    lines.append(asp.fact("animal", "otter"))
    lines.append(asp.fact("animal", "penguin"))
    lines.append(asp.fact("keeper", "keeper"))
    lines.append(asp.fact("keeper", "warden"))
    lines.append(asp.fact("magic", "moonspell"))
    lines.append(asp.fact("magic", "tidecharm"))
    lines.append(asp.fact("magic", "starwhisper"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    try:
        _ = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP error: {exc}")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


# ---------------------------------------------------------------------------
# Params / generation / output
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic animal-enclosure storyworld.")
    ap.add_argument("--animal", choices=sorted(ANIMAL_KINDS))
    ap.add_argument("--keeper", choices=sorted(KEEPERS))
    ap.add_argument("--magic", choices=sorted(MAGICS))
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    animal = args.animal or rng.choice(sorted(ANIMAL_KINDS))
    keeper = args.keeper or rng.choice(sorted(KEEPERS))
    magic = args.magic or rng.choice(sorted(MAGICS))
    if args.name:
        name = args.name
    else:
        name = rng.choice(["Nori", "Milo", "Pip", "Sera", "Bram", "Luma"])
    return StoryParams(animal=animal, keeper=keeper, magic=magic, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(animal="seal", keeper="keeper", magic="tidecharm", name="Nori"),
    StoryParams(animal="otter", keeper="warden", magic="moonspell", name="Pip"),
    StoryParams(animal="penguin", keeper="keeper", magic="starwhisper", name="Luma"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.animal} + {p.magic} in the animal enclosure"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
