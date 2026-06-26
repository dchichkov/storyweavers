#!/usr/bin/env python3
"""
A tiny fairy-tale story world with a lesson learned:
a child, a magic rod, a nervous spaz, and a change of mode.

This standalone script follows the storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven narration
- Python reasonableness gate plus inline ASP twin
- generate / emit / main interface
"""

from __future__ import annotations

import argparse
import copy
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
    wielded_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    helps: set[str]
    mode: str


@dataclass
class HeroConfig:
    name: str
    type: str
    trait: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.mode: str = "kind"

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.mode = self.mode
        return clone


def _get(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _set_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = amount


def _hero_title(hero: Entity) -> str:
    return hero.type


def _mode_name(mode: str) -> str:
    return {"kind": "kind mode", "stern": "stern mode", "quiet": "quiet mode"}.get(mode, mode)


def reasonableness_gate(hero: Entity, rod: Entity, spaz: Entity, tool: Tool) -> None:
    if not tool.kind == "lesson":
        raise StoryError("This world only tells stories where the lesson-tool can change the mode.")
    if rod.owner != hero.id:
        raise StoryError("The rod must belong to the hero.")
    if spaz.kind != "character":
        raise StoryError("Spaz must be a character in the tale.")
    if tool.mode not in {"kind", "stern", "quiet"}:
        raise StoryError("Unsupported mode for this fairy tale.")


def predict_loss(world: World, hero: Entity, rod: Entity, spaz: Entity, tool: Tool) -> bool:
    sim = world.copy()
    _do_scene(sim, sim.get(hero.id), sim.get(rod.id), sim.get(spaz.id), tool, narrate=False)
    return bool(sim.get(rod.id).meters.get("cracked", 0.0) >= THRESHOLD)


def _do_scene(world: World, hero: Entity, rod: Entity, spaz: Entity, tool: Tool, narrate: bool = True) -> None:
    _add_meme(hero, "curiosity")
    _add_meme(spaz, "nervous")
    world.mode = "kind"
    if narrate:
        world.say(
            f"In a small fairy-tale castle, {hero.id} carried a slender rod that glimmered like moonlight."
        )
        world.say(
            f"Near the hall, {spaz.id} kept fidgeting, for {spaz.id} was a spaz when every eye looked their way."
        )
    if _mem(spaz, "nervous") >= THRESHOLD:
        _add_meter(spaz, "tremble", 1.0)
    if narrate:
        world.say(
            f"{hero.id} wanted the rod to fix everything at once, but the rod only worked well in {_mode_name(world.mode)}."
        )

    world.mode = "stern"
    if narrate:
        world.say(
            f"Then {hero.id} tried stern mode, and the room felt tight and prickly."
        )
    _add_meme(hero, "frustration")
    _add_meme(spaz, "fear")
    if _mem(hero, "frustration") >= THRESHOLD and _mem(spaz, "fear") >= THRESHOLD:
        _add_meter(rod, "shaken", 1.0)

    if predict_loss(world, hero, rod, spaz, tool):
        pass

    if narrate:
        world.say(
            f"{hero.id} noticed the rod was getting shaken, and {spaz.id} looked ready to cry."
        )

    world.mode = tool.mode
    if narrate:
        world.say(
            f"At last, {hero.id} remembered the lesson learned: a gentle heart makes a better mode than a sharp one."
        )
    _add_meme(hero, "wisdom", 1.0)
    _add_meme(spaz, "relief", 1.0)
    _set_meme(hero, "frustration", 0.0)
    _set_meme(spaz, "fear", 0.0)
    _add_meter(rod, "cracked", 0.0)
    if narrate:
        world.say(
            f"{hero.id} lowered the rod, spoke softly, and the hall grew calm again."
        )


def tell(hero_cfg: HeroConfig, setting: Setting, tool: Tool) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_cfg.name, kind="character", type=hero_cfg.type))
    spaz = world.add(Entity(id="Spaz", kind="character", type="child"))
    rod = world.add(Entity(
        id="rod",
        kind="thing",
        type="rod",
        label="rod",
        phrase="a slender silver rod",
        owner=hero.id,
        caretaker=hero.id,
    ))
    hero.meters["calm"] = 0.0
    hero.memes["curiosity"] = 0.0
    spaz.memes["nervous"] = 0.0
    reasonableness_gate(hero, rod, spaz, tool)

    world.say(
        f"Once in a fairy-tale castle, {hero.id} found {rod.phrase}, a rod that could help when the mode was right."
    )
    world.say(
        f"{spaz.id} had a habit of turning spaz-like whenever the court grew loud, and that made the air wobble."
    )
    world.para()
    _do_scene(world, hero, rod, spaz, tool, narrate=True)
    world.para()
    if tool.mode == "kind":
        world.say(
            f"In the end, the lesson learned was simple: kind mode kept the rod safe, {spaz.id} calm, and the castle bright."
        )
    elif tool.mode == "stern":
        world.say(
            f"In the end, the lesson learned was still plain: stern words only worked after they were softened by kindness."
        )
    else:
        world.say(
            f"In the end, the lesson learned was quiet and clear: sometimes the best mode is the one that lets everyone breathe."
        )

    world.facts.update(hero=hero, spaz=spaz, rod=rod, tool=tool, setting=setting, mode=tool.mode)
    return world


SETTINGS = {
    "castle": Setting(place="the castle", kind="castle", affords={"lesson"}),
    "garden": Setting(place="the castle garden", kind="garden", affords={"lesson"}),
    "tower": Setting(place="the old tower room", kind="tower", affords={"lesson"}),
}

TOOLS = {
    "lesson": Tool(
        id="lesson",
        label="lesson learned",
        phrase="a lesson learned charm",
        kind="lesson",
        helps={"kind", "quiet", "stern"},
        mode="kind",
    )
}

HEROES = [
    HeroConfig(name="Ayla", type="princess", trait="brave"),
    HeroConfig(name="Nico", type="prince", trait="gentle"),
    HeroConfig(name="Mira", type="girl", trait="curious"),
    HeroConfig(name="Evan", type="boy", trait="thoughtful"),
]


@dataclass
class StoryParams:
    setting: str
    tool: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "princess", "prince"])
    ap.add_argument("--trait")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    tool = args.tool or "lesson"
    hero = rng.choice(HEROES)
    return StoryParams(
        setting=setting,
        tool=tool,
        hero_name=args.hero_name or hero.name,
        hero_type=args.hero_type or hero.type,
        trait=args.trait or hero.trait,
    )


def generate(params: StoryParams) -> StorySample:
    hero_cfg = HeroConfig(name=params.hero_name, type=params.hero_type, trait=params.trait)
    world = tell(hero_cfg, SETTINGS[params.setting], TOOLS[params.tool])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short fairy tale about {hero.id}, a rod, a spaz, and a lesson learned.",
        f"Tell a gentle story where {hero.id} learns that {_mode_name(f['tool'].mode)} is better than pressure.",
        "Write a child-friendly fairy tale with a clear lesson learned and a calm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, spaz, rod, tool = f["hero"], f["spaz"], f["rod"], f["tool"]
    return [
        QAItem(
            question=f"Who learned the lesson in the fairy tale?",
            answer=f"{hero.id} learned the lesson after noticing that the rod stayed safer in kind mode.",
        ),
        QAItem(
            question=f"What was {spaz.id} like at the start?",
            answer=f"{spaz.id} was nervous and spaz-like, so the room felt wobbly before the change in mode.",
        ),
        QAItem(
            question=f"What helped the story end well?",
            answer=f"The lesson learned helped {hero.id} choose kind mode, which calmed {spaz.id} and kept the rod safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rod?",
            answer="A rod is a long, thin stick or bar. In fairy tales it can be a magic tool or a symbol of power.",
        ),
        QAItem(
            question="What does it mean to switch mode?",
            answer="To switch mode means to change the way something is working or the way someone is acting.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a good idea someone understands after making a mistake or seeing what works better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"mode={world.mode}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="castle", tool="lesson", hero_name="Ayla", hero_type="princess", trait="brave"),
    StoryParams(setting="garden", tool="lesson", hero_name="Mira", hero_type="girl", trait="curious"),
    StoryParams(setting="tower", tool="lesson", hero_name="Nico", hero_type="prince", trait="gentle"),
]


ASP_RULES = r"""
hero(H).
spaz(S).
rod(R).
tool(T).
mode(kind).
mode(stern).
mode(quiet).

can_use(T, M) :- tool(T), mode(M).
good_story(H, S, R, T) :- hero(H), spaz(S), rod(R), tool(T), can_use(T, kind).
good_story(H, S, R, T) :- hero(H), spaz(S), rod(R), tool(T), can_use(T, quiet).
good_story(H, S, R, T) :- hero(H), spaz(S), rod(R), tool(T), can_use(T, stern).

#show good_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for _k, _ in SETTINGS.items():
        lines.append(asp.fact("setting", _k))
    for _k, _ in TOOLS.items():
        lines.append(asp.fact("tool", _k))
    for h in HEROES:
        lines.append(asp.fact("hero", h.name))
    lines.append(asp.fact("spaz", "Spaz"))
    lines.append(asp.fact("rod", "rod"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {("Ayla", "Spaz", "rod", "lesson"), ("Mira", "Spaz", "rod", "lesson"), ("Nico", "Spaz", "rod", "lesson"), ("Evan", "Spaz", "rod", "lesson")}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo matches Python gate ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
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
        print(asp_program("#show good_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story tuples:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
