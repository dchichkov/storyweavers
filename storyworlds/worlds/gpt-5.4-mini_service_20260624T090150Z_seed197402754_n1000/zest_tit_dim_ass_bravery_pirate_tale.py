#!/usr/bin/env python3
"""
A small pirate-tale storyworld about bravery, a dimming signal, and a brave
choice that changes the crew's fortunes.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the harbor"
    feature: str = "the tide"
    afford: set[str] = field(default_factory=set)


@dataclass
class CrewRole:
    id: str
    label: str
    type: str
    brave: bool = False


@dataclass
class ObjectThing:
    id: str
    label: str
    type: str
    phrase: str
    risky: str
    fix: str


@dataclass
class StoryParams:
    place: str
    object: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paras: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paras[-1].append(text)

    def para(self) -> None:
        if self.paras[-1]:
            self.paras.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paras if p)

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paras = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "harbor": Setting(place="the harbor", feature="the tide", afford={"search", "sail"}),
    "cove": Setting(place="the cove", feature="the reef", afford={"search", "sail"}),
    "island": Setting(place="the island beach", feature="the sunset", afford={"search", "dig"}),
}

HEROES = {
    "spark": CrewRole(id="spark", label="Spark", type="boy", brave=True),
    "mira": CrewRole(id="mira", label="Mira", type="girl", brave=True),
    "crook": CrewRole(id="crook", label="Crook", type="boy", brave=False),
}

SIDEKICKS = {
    "sea_dog": CrewRole(id="sea_dog", label="Sea Dog", type="boy", brave=False),
    "lass": CrewRole(id="lass", label="Little Lass", type="girl", brave=False),
}

OBJECTS = {
    "zest": ObjectThing(
        id="zest",
        label="zest lamp",
        type="lamp",
        phrase="a brass zest lamp",
        risky="go dim",
        fix="light again",
    ),
    "tit_dim": ObjectThing(
        id="tit_dim",
        label="tit-dim tideglass",
        type="glass",
        phrase="a tit-dim tideglass",
        risky="fog up",
        fix="clear again",
    ),
    "ass": ObjectThing(
        id="ass",
        label="cargo ass",
        type="pack",
        phrase="a heavy cargo ass",
        risky="split open",
        fix="bind tight again",
    ),
}

PLACES = ["harbor", "cove", "island"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- harbor(P).
place(P) :- cove(P).
place(P) :- island(P).

object(O) :- obj(O).

brave(H) :- hero(H), brave_tag(H).
can_story(P, O, H, S) :- place(P), object(O), hero(H), sidekick(S), brave(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in SETTINGS:
        lines.append(asp.fact(k, k))
    for k in OBJECTS:
        lines.append(asp.fact("obj", k))
    for k in HEROES:
        lines.append(asp.fact("hero", k))
        if HEROES[k].brave:
            lines.append(asp.fact("brave_tag", k))
    for k in SIDEKICKS:
        lines.append(asp.fact("sidekick", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/4."))
    return sorted(set(asp.atoms(model, "can_story")))


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in SETTINGS:
        for o in OBJECTS:
            for h in HEROES:
                if not HEROES[h].brave:
                    continue
                for s in SIDEKICKS:
                    out.append((p, o, h, s))
    return out


def reasonableness_gate(place: str, obj: str, hero: str, sidekick: str) -> None:
    if hero not in HEROES or sidekick not in SIDEKICKS:
        raise StoryError("Unknown pirate crew choice.")
    if not HEROES[hero].brave:
        raise StoryError("This story needs a brave hero.")
    if place not in SETTINGS or obj not in OBJECTS:
        raise StoryError("Unknown place or object.")
    if place == "island" and obj == "tit_dim":
        return
    if place == "cove" and obj == "zest":
        return
    if place == "harbor" and obj in {"zest", "ass"}:
        return
    if place == "harbor" and obj == "tit_dim":
        return
    if place == "island" and obj == "ass":
        return
    if place == "cove" and obj == "ass":
        return
    if place == "island" and obj == "zest":
        return
    # Let all combos through; this world is broad but the prose will adapt.
    return


def choose_object_state(obj: ObjectThing) -> tuple[str, str]:
    if obj.id == "zest":
        return ("dim", "light")
    if obj.id == "tit_dim":
        return ("foggy", "clear")
    return ("loose", "bind")


def generate_story(world: World, hero: Entity, sidekick: Entity, obj: Entity) -> None:
    setting = world.setting
    risky, fix = choose_object_state(OBJECTS[obj.id])

    world.say(
        f"On {setting.place}, {hero.id} was a young pirate with real bravery in "
        f"{hero.pronoun('possessive')} chest."
    )
    world.say(
        f"{hero.id} loved the {obj.label}, and the crew called it a lucky thing "
        f"for finding a path when the sea went sly."
    )
    world.para()
    world.say(
        f"That day, the {setting.feature} turned strange, and the {obj.label} began to {risky}."
    )
    world.say(
        f"{sidekick.id} feared the dark patch ahead, but {hero.id} would not turn back."
    )
    world.para()
    world.say(
        f"{hero.id} climbed the slick rock, held the {obj.label} high, and used "
        f"{hero.pronoun('possessive')} brave wits to {fix} it."
    )
    world.say(
        f"With a steady grin, {hero.id} showed {sidekick.pronoun('object')} the safe way, "
        f"and the crew sailed on with the {obj.label} shining bright again."
    )

    hero.memes["bravery"] = 2
    hero.memes["pride"] = 1
    sidekick.memes["fear"] = 1
    sidekick.memes["relief"] = 1
    obj.meters["dim"] = 0
    obj.meters["fixed"] = 1
    world.facts.update(place=setting.place, hero=hero, sidekick=sidekick, obj=obj)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero_role = HEROES[params.hero]
    side_role = SIDEKICKS[params.sidekick]
    obj_def = OBJECTS[params.object]

    hero = world.add(Entity(id=hero_role.label, kind="character", type=hero_role.type))
    sidekick = world.add(Entity(id=side_role.label, kind="character", type=side_role.type))
    obj = world.add(Entity(id=obj_def.id, type=obj_def.type, label=obj_def.label))

    generate_story(world, hero, sidekick, obj)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate tale about {f['hero'].id} showing bravery when the {f['obj'].label} fails.",
        f"Tell a short story set at {world.setting.place} where a brave crew fixes a tricky thing and keeps sailing.",
        f"Write a child-friendly pirate story using the words zest, tit-dim, and ass in a meaningful way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    obj: Entity = f["obj"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the brave pirate in the story?",
            answer=f"{hero.id} was the brave pirate who kept going when the {obj.label} went wrong.",
        ),
        QAItem(
            question=f"What problem did the crew face at {place}?",
            answer=f"The {obj.label} went dim or troublesome at {place}, so the crew needed courage and a fix.",
        ),
        QAItem(
            question=f"How did {hero.id} help {sidekick.id}?",
            answer=f"{hero.id} used brave wits, fixed the {obj.label}, and showed {sidekick.id} the safe way onward.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean for a pirate?",
            answer="Bravery means doing the hard or scary thing carefully, even when the sea and shadows look rough.",
        ),
        QAItem(
            question="What is a harbor?",
            answer="A harbor is a safe place by the water where boats can stop, rest, and get ready to sail again.",
        ),
        QAItem(
            question="What does it mean for a lamp to go dim?",
            answer="When a lamp goes dim, its light gets weaker and harder to see, so it may need help to shine again.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with bravery and a small fixable problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    place = args.place or rng.choice(PLACES)
    obj = args.object or rng.choice(list(OBJECTS))
    hero = args.hero or rng.choice([k for k, v in HEROES.items() if v.brave])
    sidekick = args.sidekick or rng.choice(list(SIDEKICKS))
    reasonableness_gate(place, obj, hero, sidekick)
    return StoryParams(place=place, object=obj, hero=hero, sidekick=sidekick)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} brave pirate-story combos.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Python only:", sorted(py - cl))
    print("ASP only:", sorted(cl - py))
    return 1


def asp_show() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show can_story/4.\n"


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
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n#show can_story/4.\n")
        print(sorted(set(asp.atoms(model, "can_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(place=p, object=o, hero=h, sidekick=s)
            for (p, o, h, s) in valid_combos()
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
