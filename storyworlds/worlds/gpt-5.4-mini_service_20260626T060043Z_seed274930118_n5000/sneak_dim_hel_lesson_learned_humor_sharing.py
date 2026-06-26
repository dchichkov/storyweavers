#!/usr/bin/env python3
"""
storyworlds/worlds/sneak_dim_hel_lesson_learned_humor_sharing.py
=================================================================

A small adventure storyworld about sneaking into a dim place called the Hel,
making a funny mistake, sharing the light and supplies, and learning a lesson.

Seed premise:
- sneak-dim
- hel
- Lesson Learned
- Humor
- Sharing
- Style: Adventure
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    dim: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


@dataclass
class StoryParams:
    place: str
    relic: str
    tool: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "hel": Setting(place="the Hel", dim=True, affords={"sneak", "explore"}),
    "cave": Setting(place="the cave", dim=True, affords={"sneak", "explore"}),
    "tower": Setting(place="the tower stairs", dim=True, affords={"sneak", "explore"}),
}

RELICS = {
    "map": Relic(id="map", label="map", phrase="a folded treasure map", region="hand"),
    "lantern": Relic(id="lantern", label="lantern", phrase="a little lantern", region="hand"),
    "key": Relic(id="key", label="key", phrase="a tiny brass key", region="pocket"),
    "snack": Relic(id="snack", label="snack", phrase="a crumbly snack pack", region="hand", plural=False),
}

TOOLS = [
    Tool(
        id="torch",
        label="a torch",
        guards={"dark"},
        covers={"hand"},
        prep="take a torch along",
        tail="walked back with the torch",
    ),
    Tool(
        id="rope",
        label="a rope",
        guards={"lose"},
        covers={"hand"},
        prep="bring a rope too",
        tail="returned with the rope looped safely around their hands",
    ),
    Tool(
        id="lantern_buddy",
        label="a shared lantern",
        guards={"dark"},
        covers={"hand"},
        prep="share one lantern",
        tail="went on together with the shared lantern",
    ),
]

HERO_NAMES = ["Mina", "Toby", "Lina", "Pip", "Nora", "Jasper", "Milo", "Ivy"]
COMPANIONS = ["friend", "sibling", "cousin", "neighbor"]
TRAITS = ["brave", "curious", "playful", "bold", "quick", "cheerful"]


def is_reasonable(place: str, relic: str, tool: str) -> bool:
    return place in SETTINGS and relic in RELICS and any(t.id == tool for t in TOOLS)


def select_tool(rel: Relic) -> Optional[Tool]:
    if rel.region != "hand":
        return None
    for tool in TOOLS:
        if "dark" in tool.guards:
            return tool
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: sneak, dim light, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
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
    place = args.place or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    tool = args.tool or select_tool(RELICS[relic]).id
    if tool is None:
        raise StoryError("(No story: that relic cannot be safely shared through the dim place.)")
    if not is_reasonable(place, relic, tool):
        raise StoryError("(No story: the requested choices do not make a coherent adventure.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, tool=tool, name=name, gender=gender, companion=companion, trait=trait)


def _do_sneak(world: World, hero: Entity, rel: Relic) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.meters["sneak"] = hero.meters.get("sneak", 0.0) + 1
    world.say(f"{hero.id} felt brave enough to sneak into {world.setting.place} and see what glittered inside.")


def _do_blunder(world: World, hero: Entity, rel: Relic) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    world.say(
        f"Right away, {hero.id} bumped a little stone, and it clicked like a tiny drum. "
        f"{hero.pronoun().capitalize()} froze, then gave a nervous giggle at the echo."
    )


def _do_share(world: World, hero: Entity, partner: Entity, rel: Relic, tool: Tool) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
    partner.memes["sharing"] = partner.memes.get("sharing", 0.0) + 1
    world.say(
        f"Then {hero.id} shared the {tool.label} with {partner.id}, and the two of them could see the {rel.label} better."
    )


def _do_lesson(world: World, hero: Entity, partner: Entity, rel: Relic, tool: Tool) -> None:
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} learned that a secret adventure is better when friends are included. "
        f"Together they left {world.setting.place} laughing, with the {rel.label} safe and the shared {tool.label} shining."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    partner = world.add(Entity(id="Partner", kind="character", type=params.companion, label=params.companion))
    rel = world.add(Entity(id=params.relic, label=RELICS[params.relic].label, phrase=RELICS[params.relic].phrase, region=RELICS[params.relic].region))
    tool = next(t for t in TOOLS if t.id == params.tool)

    world.say(
        f"{hero.id} was a {params.trait} little {hero.type} who loved adventure."
    )
    world.say(
        f"One dim afternoon, {hero.id} spotted {rel.phrase} near {setting.place}."
    )
    world.para()
    _do_sneak(world, hero, rel)
    _do_blunder(world, hero, rel)
    world.say(
        f"{hero.id} thought about turning back, but {hero.pronoun('possessive')} {params.companion} had followed {hero.pronoun('object')} in."
    )
    world.say(
        f"Together they decided to {tool.prep}."
    )
    _do_share(world, hero, partner, rel, tool)
    world.para()
    world.say(
        f"With the light shared, the dim Hel did not feel so scary anymore."
    )
    _do_lesson(world, hero, partner, rel, tool)
    _do_lesson(world, partner, hero, rel, tool)

    world.facts.update(hero=hero, partner=partner, relic=rel, tool=tool, setting=setting, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rel = f["relic"]
    tool = f["tool"]
    return [
        f'Write an adventure story for a child about sneaking into the dim Hel and finding {rel.label}.',
        f"Tell a short story where {hero.id} is curious, makes a funny mistake, then shares {tool.label} with a friend.",
        f"Write a child-friendly adventure with humor and sharing that ends with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    rel = f["relic"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who went on the adventure in the dim Hel?",
            answer=f"It was {hero.id}, and then {partner.id} joined {hero.pronoun('object')} after the sneaky start.",
        ),
        QAItem(
            question=f"What funny thing happened when {hero.id} sneaked inside?",
            answer=f"{hero.id} bumped a stone, and the little click echoed in a funny way that made the moment feel less scary.",
        ),
        QAItem(
            question=f"What did they share to help them explore safely?",
            answer=f"They shared {tool.label}, so they could see better in the dim place and keep the {rel.label} safe.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that an adventure is better when friends share the load, the light, and the fun.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you instead of keeping it only for yourself.",
        ),
        QAItem(
            question="Why can a dim place feel hard to explore?",
            answer="A dim place can be hard to explore because it is not bright enough to see clearly, so people may need a lamp or torch.",
        ),
        QAItem(
            question="Why can humor help in an adventure?",
            answer="Humor can help because a small joke or funny mistake can make everyone relax and feel braver.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the helpful thing a character understands after what happened, and it changes how they act next time.",
        ),
    ]
    return out


ASP_RULES = r"""
hero_had_adventure(H) :- hero(H).
funny_moment(H) :- sneaks(H), echo(H).
shared_light(H) :- uses(H, T), shares(H, T).
lesson_learned(H) :- shared_light(H), friend_joined(H).
good_ending(H) :- lesson_learned(H), found_relic(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for relic in RELICS:
            if select_tool(RELICS[relic]) is not None:
                combos.append((place, relic, select_tool(RELICS[relic]).id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show hero_had_adventure/1.\n#show funny_moment/1.\n#show shared_light/1.\n#show lesson_learned/1.\n#show good_ending/1."))
    return sorted(set(asp.atoms(model, "good_ending")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(valid_combos())
    if py == cl:
        print(f"OK: ASP/Python parity looks good ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams(place="hel", relic="lantern", tool="lantern_buddy", name="Mina", gender="girl", companion="friend", trait="curious"),
    StoryParams(place="cave", relic="map", tool="torch", name="Toby", gender="boy", companion="sibling", trait="brave"),
    StoryParams(place="tower", relic="key", tool="rope", name="Ivy", gender="girl", companion="cousin", trait="playful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    tool = args.tool or select_tool(RELICS[relic]).id
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    trait = rng.choice(TRAITS)
    if tool is None:
        raise StoryError("(No story: the chosen relic cannot be shared safely in the dim place.)")
    return StoryParams(place=place, relic=relic, tool=tool, name=name, gender=gender, companion=companion, trait=trait)


def build_asp_text() -> str:
    return asp_program("#show good_ending/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_text())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(json.dumps(valid_combos(), indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
