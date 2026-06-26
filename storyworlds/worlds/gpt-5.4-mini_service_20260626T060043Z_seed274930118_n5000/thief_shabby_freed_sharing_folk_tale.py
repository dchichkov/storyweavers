#!/usr/bin/env python3
"""
A small folk-tale storyworld about a shabby thief, a freed burden, and the
surprising power of sharing.

Premise:
- A thief in shabby clothes keeps taking from a village.
- The villagers grow poorer and less trusting.
- A child notices the thief is not bold, only hungry and ashamed.
- Sharing food, cloth, and work gives the thief a way to change.

The world model tracks:
- physical meters: hunger, cold, wear, carried_goods, shared_food, mended_cloth
- emotional memes: shame, fear, trust, relief, generosity, belonging

The story resolves when the thief is freed from the need to steal and joins the
folk as a helper.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"child", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "thief"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def init_meter(self, key: str, value: float) -> None:
        self.meters[key] = value

    def init_meme(self, key: str, value: float) -> None:
        self.memes[key] = value


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "village_green"
    hero: str = "child"
    thief_name: str = "Moss"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.place)
        clone.entities = dataclasses.replace(self.entities) if False else {}
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village_green": Place("village_green", "the village green", {"folk", "sharing"}),
    "mill_lane": Place("mill_lane", "the mill lane", {"folk", "sharing"}),
    "market_square": Place("market_square", "the market square", {"folk", "sharing"}),
}

HERO_TYPES = {
    "child": "child",
    "girl": "girl",
    "boy": "boy",
}

NAMES = [
    "Moss", "Pip", "Nell", "Tob", "Wren", "Ivy", "Huck", "Bram", "Lark", "Della"
]

TRAITS = ["kind", "brave", "quiet", "gentle", "curious", "small"]

ASP_RULES = r"""
% The thief is at risk of being changed when the village shares with them.
at_risk(T) :- thief(T), hungry(T), shabby(T), not welcomed(T).

% Sharing can free the thief from stealing when it reduces hunger and shame.
freed(T) :- thief(T), shared_with(T), not hungry(T), not ashamed(T).

% A good story exists only if there is a thief, a community, and a shared gift.
valid_story(P) :- place(P), thief(th), sharing_event(th), folk_help(P).
"""


# ---------------------------------------------------------------------------
# Utility / narration helpers
# ---------------------------------------------------------------------------

def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _has(e: Entity, key: str) -> bool:
    return _meter(e, key) >= 1.0 or _meme(e, key) >= 1.0


def _capitalize_name(name: str) -> str:
    return name[:1].upper() + name[1:]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def _start_state(world: World, thief: Entity, child: Entity, elders: Entity, bread: Entity, cloak: Entity) -> None:
    thief.init_meter("hunger", 1.0)
    thief.init_meter("wear", 1.0)
    thief.init_meme("shame", 1.0)
    thief.init_meme("fear", 1.0)

    child.init_meme("trust", 0.0)
    child.init_meme("curiosity", 1.0)

    elders.init_meme("worry", 1.0)
    elders.init_meme("doubt", 1.0)

    bread.init_meter("shared_food", 0.0)
    cloak.init_meter("mended_cloth", 0.0)

    world.facts.update(
        thief=thief,
        child=child,
        elders=elders,
        bread=bread,
        cloak=cloak,
    )


def _steal(world: World, thief: Entity, bread: Entity) -> None:
    sig = ("steal", thief.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    thief.meters["carried_goods"] = thief.meters.get("carried_goods", 0.0) + 1.0
    thief.memes["shame"] = thief.memes.get("shame", 0.0) + 1.0
    bread.meters["shared_food"] = 0.0
    world.say(
        f"{_capitalize_name(thief.id)} came to the {world.place.label} in shabby clothes and "
        f"snatched a little bread, because hunger had grown too sharp for patience."
    )


def _notice(world: World, child: Entity, thief: Entity) -> None:
    sig = ("notice", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"But a child saw the thief's torn sleeves and bent shoes and did not see a monster; "
        f"only someone who looked very tired."
    )


def _offer_sharing(world: World, child: Entity, elders: Entity, thief: Entity, bread: Entity, cloak: Entity) -> None:
    sig = ("share", thief.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    bread.meters["shared_food"] = 1.0
    cloak.meters["mended_cloth"] = 1.0
    thief.meters["hunger"] = 0.0
    thief.meters["wear"] = 0.0
    thief.memes["fear"] = max(0.0, thief.memes.get("fear", 0.0) - 1.0)
    thief.memes["shame"] = max(0.0, thief.memes.get("shame", 0.0) - 1.0)
    thief.memes["relief"] = thief.memes.get("relief", 0.0) + 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    elders.memes["worry"] = max(0.0, elders.memes.get("worry", 0.0) - 1.0)
    elders.memes["doubt"] = max(0.0, elders.memes.get("doubt", 0.0) - 1.0)
    elders.memes["generosity"] = elders.memes.get("generosity", 0.0) + 1.0
    thief.tags.add("freed")
    world.say(
        f"The child brought bread, and the elders brought a patched cloak, saying, "
        f'"No one must stay hungry and cold when the village can share."'
    )


def _accept_change(world: World, thief: Entity, child: Entity, elders: Entity) -> None:
    sig = ("accept", thief.id)
    if sig in world.fired:
        return
    if _meter(thief, "hunger") > 0.0:
        return
    world.fired.add(sig)
    thief.memes["belonging"] = thief.memes.get("belonging", 0.0) + 1.0
    world.say(
        f"The thief ate with both hands, then set the empty sack down and chose to help carry wood "
        f"instead of taking what was not theirs."
    )
    world.say(
        f"By sunset, the shabby one was no longer a thief in need of stealing, but a neighbor with "
        f"new trust in their chest and warm bread in their belly."
    )


def simulate(world: World) -> None:
    thief = world.get("thief")
    child = world.get("child")
    elders = world.get("elders")
    bread = world.get("bread")
    cloak = world.get("cloak")

    world.say(
        f"Long ago, at {world.place.label}, there lived a shabby thief who kept to the edges of the folk."
    )
    world.say(
        f"{_capitalize_name(child.id)} noticed that the thief always came near supper-time, looking hungry rather than bold."
    )

    world.para()
    _steal(world, thief, bread)
    world.say(
        f"The villagers frowned, because every stolen loaf made the table a little thinner and the evening a little colder."
    )
    _notice(world, child, thief)

    world.para()
    world.say(
        f"Then the child spoke gently to the elders, and the elders listened as if the wind itself had asked them to stop and think."
    )
    _offer_sharing(world, child, elders, thief, bread, cloak)
    _accept_change(world, thief, child, elders)

    world.para()
    world.say(
        f"After that, the thief no longer crept through the dark. They returned at dawn, helped knead dough, and carried water for the bakehouse."
    )
    world.say(
        f"And because the village shared, the shabby coat was mended, the table stayed full, and the once-freed thief walked openly among the folk."
    )


# ---------------------------------------------------------------------------
# ASP twin / reasonableness gate
# ---------------------------------------------------------------------------

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
    for name in NAMES:
        lines.append(asp.fact("name", name))
    for t in HERO_TYPES:
        lines.append(asp.fact("hero_type", t))
    lines.append(asp.fact("thief", "thief"))
    lines.append(asp.fact("shabby", "thief"))
    lines.append(asp.fact("freed", "thief"))
    lines.append(asp.fact("sharing_event", "thief"))
    lines.append(asp.fact("folk_help", "village_green"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable() -> bool:
    return True


def asp_reasonable() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/1.\n#show at_risk/1.\n#show freed/1."))
    return bool(asp.atoms(model, "valid_story"))


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    thief = world.facts["thief"]
    child = world.facts["child"]
    place = world.place.label
    return [
        f"Write a short folk tale about a shabby thief at {place} who is changed by sharing.",
        f"Tell a gentle story where {child.id} sees that {thief.id} is hungry, and the village helps them become free.",
        f"Write a child-friendly folk tale about stealing, kindness, and a thief who stops stealing after being shared with.",
    ]


def story_qa(world: World) -> list[QAItem]:
    thief = world.facts["thief"]
    child = world.facts["child"]
    elders = world.facts["elders"]
    bread = world.facts["bread"]
    cloak = world.facts["cloak"]

    return [
        QAItem(
            question=f"Who was the story about at {world.place.label}?",
            answer=f"It was about {thief.id}, a shabby thief, and about {child.id} and the village folk who changed what happened next.",
        ),
        QAItem(
            question=f"Why did {thief.id} steal bread at first?",
            answer=f"{thief.id} was hungry, ashamed, and afraid, so stealing seemed like the quickest way to get through the day.",
        ),
        QAItem(
            question=f"What did the child notice about {thief.id}?",
            answer=f"The child noticed that {thief.id} looked tired and poor, with torn clothes and a lonely face, not just a sneaky one.",
        ),
        QAItem(
            question=f"How did the village help {thief.id}?",
            answer=f"They shared bread and mended cloth, and that sharing let {thief.id} stop stealing and start helping.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"{thief.id} was freed from the need to steal, the bread was shared, the cloak was mended, and the village trusted them again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share?",
            answer="To share means to give some of what you have so other people can use it too.",
        ),
        QAItem(
            question="Why can sharing help a person in need?",
            answer="Sharing can help because it gives food, cloth, or comfort to someone who does not have enough.",
        ),
        QAItem(
            question="What does shabby mean?",
            answer="Shabby means old, worn, and a little ragged, as if something has been used a lot.",
        ),
        QAItem(
            question="What does it mean to be freed?",
            answer="To be freed means to no longer be trapped, stuck, or forced to keep doing the same hard thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    thief_name = args.name or rng.choice(NAMES)
    hero = args.hero or rng.choice(list(HERO_TYPES))
    if hero == "boy" and thief_name in {"Nell", "Ivy", "Wren", "Della", "Lark"}:
        pass
    return StoryParams(place=place, hero=hero, thief_name=thief_name)


def _build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    thief = world.add(Entity("thief", kind="character", label=params.thief_name, type="thief"))
    child = world.add(Entity("child", kind="character", label="the child", type=params.hero))
    elders = world.add(Entity("elders", kind="character", label="the elders", type="folk"))
    bread = world.add(Entity("bread", kind="thing", label="bread"))
    cloak = world.add(Entity("cloak", kind="thing", label="a patched cloak"))
    _start_state(world, thief, child, elders, bread, cloak)
    simulate(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(parts)}")
    lines.append(f"  place={world.place.label}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world: a shabby thief is freed by sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=list(HERO_TYPES))
    ap.add_argument("--name", choices=NAMES)
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


def asp_verify() -> int:
    py = python_reasonable()
    asp_ok = asp_reasonable()
    if py == asp_ok:
        print("OK: Python and ASP reasonableness agree.")
        return 0
    print(f"MISMATCH: python={py} asp={asp_ok}")
    return 1


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

    if args.show_asp:
        print(asp_program("#show valid_story/1.\n#show at_risk/1.\n#show freed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.seed is None:
        base_seed = random.randrange(2**31)
    else:
        base_seed = args.seed

    samples: list[StorySample] = []
    if args.all:
        for i, place in enumerate(list(PLACES)):
            params = StoryParams(place=place, hero="child", thief_name=NAMES[i % len(NAMES)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
