#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035344Z_seed1855084837_n10/solid_trumpet_copper_sound_effects_cautionary_fable.py
===================================================================================================================================

A small standalone storyworld for a cautionary fable with sound effects.

Premise:
A proud young hare finds a solid copper trumpet and wants to use it to sound
important. A cautious tortoise warns that loud trumpet calls near the beehive
will wake the bees and scare the meadow. The hare ignores the warning, blows
the trumpet, and the bees swarm. A grown-up badger helps calm the meadow, and
the hare learns to save loud sounds for the open hill.

This world models:
- typed entities with meters and memes
- a simple forward-chaining consequence system
- a reasonableness gate with an ASP twin
- story-grounded QA and world-knowledge QA
- a cautionary, child-facing fable style with onomatopoeia
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
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

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

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: _deep_entity(v) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = [dict(item) for item in self.history]
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _deep_entity(e: Entity) -> Entity:
    import copy
    return copy.deepcopy(e)


@dataclass
class StoryParams:
    setting: str
    hero: str
    lesson: str
    tool: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    label: str
    place: str
    sound_zone: set[str] = field(default_factory=set)
    warning: str = ""


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sound: str
    material: str
    solid: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    phrase: str
    alarm: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        label="the meadow",
        place="the meadow",
        sound_zone={"beehive", "field"},
        warning="The meadow was bright, but the beehive near the path was sleepy.",
    ),
    "orchard": Setting(
        id="orchard",
        label="the orchard",
        place="the orchard",
        sound_zone={"beehive", "tree"},
        warning="The orchard was sweet with apples, and a beehive hung in one tree.",
    ),
}

TOOLS = {
    "trumpet": Tool(
        id="trumpet",
        label="trumpet",
        phrase="a solid copper trumpet",
        sound="TOOT! TOOT!",
        material="copper",
        solid=True,
        tags={"trumpet", "copper", "solid", "sound"},
    ),
    "horn": Tool(
        id="horn",
        label="horn",
        phrase="a solid copper horn",
        sound="HONK!",
        material="copper",
        solid=True,
        tags={"copper", "solid", "sound"},
    ),
}

RISKS = {
    "beehive": Risk(
        id="beehive",
        label="beehive",
        phrase="the beehive",
        alarm="buzz-buzz-buzz",
        tags={"bees", "buzz", "hive"},
    )
}

HEROES = {
    "hare": {"type": "boy", "label": "hare", "name": "Pip"},
    "foal": {"type": "boy", "label": "foal", "name": "Rook"},
    "rabbit": {"type": "girl", "label": "rabbit", "name": "Mira"},
}

TRAITS = ["proud", "curious", "vain", "hasty", "cheerful"]

CURATED = [
    StoryParams(setting="meadow", hero="hare", lesson="listen_first", tool="trumpet"),
    StoryParams(setting="orchard", hero="rabbit", lesson="save_sound", tool="horn"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for h in HEROES:
            for t in TOOLS:
                combos.append((s, h, t))
    return combos


def explain_rejection() -> str:
    return "(No story: this fable needs a solid copper trumpet or horn in a place where loud sound can cause trouble.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary sound-effects fable world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--lesson", choices=["listen_first", "save_sound"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hero is None or c[1] == args.hero)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hero, tool = rng.choice(sorted(combos))
    lesson = args.lesson or ("listen_first" if rng.random() < 0.5 else "save_sound")
    return StoryParams(setting=setting, hero=hero, lesson=lesson, tool=tool)


def clamp(x: float) -> float:
    return max(0.0, x)


def tell(setting: Setting, hero_key: str, lesson: str, tool: Tool) -> World:
    world = World()
    hero_cfg = HEROES[hero_key]
    hero = world.add(Entity(
        id=hero_cfg["name"],
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        traits=[rng_trait(hero_key)],
    ))
    cautioner = world.add(Entity(
        id="Tess",
        kind="character",
        type="girl",
        label="the tortoise",
        role="cautioner",
        traits=["wise", "slow"],
    ))
    grownup = world.add(Entity(
        id="Badger",
        kind="character",
        type="man",
        label="the badger",
        role="grownup",
    ))
    risk = world.add(Entity(
        id=RISKS["beehive"].id,
        type="thing",
        label=RISKS["beehive"].label,
        phrase=RISKS["beehive"].phrase,
        tags=set(RISKS["beehive"].tags),
    ))
    world.facts["setting"] = setting
    world.facts["hero"] = hero
    world.facts["cautioner"] = cautioner
    world.facts["grownup"] = grownup
    world.facts["risk"] = risk
    world.facts["tool"] = tool
    world.facts["lesson"] = lesson
    world.facts["setting_key"] = setting.id

    hero.memes["pride"] += 1
    hero.memes["desire"] += 1
    cautioner.memes["worry"] += 1

    world.say(f"One warm day in {setting.place}, {hero.id} found {tool.phrase}.")
    world.say(f"{setting.warning}")
    world.say(f"{hero.id} wanted to look grand, and the {tool.label} gleamed like new copper in the grass.")
    world.para()
    world.say(f'"{tool.sound}" went the {tool.label}, and the sound hopped over the grass like a bright stone.')
    world.say(f'Tess lifted a hand. "{hero.id}, be careful. Loud sound near {risk.phrase} can wake more trouble than you expect."')
    if lesson == "listen_first":
        hero.memes["pride"] += 0.5
        hero.memes["calm"] += 1
        world.say(f"{hero.id} paused, lowered the {tool.label}, and listened.")
        world.say(f'Then {hero.id} walked to the open hill, where the sound could travel safely: "{tool.sound}"')
        world.say(f"The meadow stayed quiet by the beehive, and the trumpet sang only to the wind.")
        hero.memes["wisdom"] += 1
        world.facts["ended_safely"] = True
    else:
        hero.memes["stubborn"] += 1
        world.say(f"{hero.id} laughed and blew harder. {tool.sound} {tool.sound}")
        risk.meters["wake"] += 1
        world.event("noise", source=hero.id, tool=tool.id)
        propagate(world, risk)
        world.say(f"The beehive answered with a furious {RISKS['beehive'].alarm}, and bees rose like pepper in the air.")
        world.para()
        world.say(f'Badger came running. "Enough," he said, and he guided {hero.id} behind a stone wall until the bees settled.')
        hero.memes["shame"] += 1
        hero.memes["wisdom"] += 1
        world.facts["ended_safely"] = True
    world.para()
    world.say(f"After that, {hero.id} kept the solid copper {tool.label} for the open hill, where a loud note could do no harm.")
    world.say(f"The little fable ended with the trumpet resting safe and bright, as solid as a stone and quiet as dusk.")
    return world


def rng_trait(hero_key: str) -> str:
    return {"hare": "proud", "foal": "curious", "rabbit": "hasty"}[hero_key]


def propagate(world: World, risk: Entity) -> None:
    sig = ("wake", risk.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.get("Tess").memes["worry"] += 1
    world.get("Badger").memes["alert"] += 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        f'Write a short fable for a young child that includes the words "solid", "trumpet", and "copper".',
        f"Tell a cautionary animal story about {hero.id} in {setting.place} and a {tool.material} trumpet that makes too much noise.",
        f"Write a sound-effects fable where a proud little animal learns to use a trumpet more wisely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    tool: Tool = f["tool"]
    setting: Setting = f["setting"]
    risk: Entity = f["risk"]
    qa = [
        QAItem(
            question=f"Who found the solid copper trumpet in {setting.place}?",
            answer=f"{hero.id} found it in {setting.place}. The trumpet was solid, copper, and shiny, so it looked important right away.",
        ),
        QAItem(
            question=f"Why did Tess warn {hero.id} about the trumpet near {risk.phrase}?",
            answer=f"She warned {hero.id} because loud sound can wake the bees and make the meadow unsafe. The trumpet was not the problem by itself; blowing it too near the beehive was.",
        ),
    ]
    if f.get("ended_safely"):
        qa.append(QAItem(
            question=f"What changed after {hero.id} listened to the warning?",
            answer=f"{hero.id} moved to the open hill and used the trumpet there instead. The sound stayed loud, but the bees were left alone and the meadow stayed calm.",
        ))
    else:
        qa.append(QAItem(
            question=f"What happened when {hero.id} blew the trumpet too hard?",
            answer=f"The bees woke up and rushed out of the beehive. Badger had to help calm things down, which taught {hero.id} to be more careful.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool: Tool = f["tool"]
    out = [
        QAItem(
            question="What does solid mean?",
            answer="Solid means something keeps its shape and does not spill or wobble like water.",
        ),
        QAItem(
            question="What is copper?",
            answer="Copper is a reddish-brown metal. It can be made into tools and instruments like a trumpet.",
        ),
        QAItem(
            question="Why do trumpets make such a big sound?",
            answer="A trumpet makes a big sound because air blows through it and the metal shape helps the note travel far.",
        ),
    ]
    if tool.material == "copper":
        out.append(QAItem(
            question="Why might a copper trumpet feel heavy?",
            answer="Copper is a metal, and metal can feel heavy in a small child's hands. That is one reason it should be handled carefully.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,H,T) :- setting(S), hero(H), tool(T).
careful(T) :- tool(T), solid_tool(T), copper_tool(T).
risky(S,T) :- setting(S), tool(T), sound_tool(T), beehive_near(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.id))
        if "beehive" in s.sound_zone:
            lines.append(asp.fact("beehive_near", s.id))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        if t.solid:
            lines.append(asp.fact("solid_tool", t.id))
        if t.material == "copper":
            lines.append(asp.fact("copper_tool", t.id))
        lines.append(asp.fact("sound_tool", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP valid combos")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        ok = False
        print("FAILED: generate/emit smoke test produced empty story")
    else:
        print("OK: generate smoke test succeeded")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hero not in HEROES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], params.hero, params.lesson, TOOLS[params.tool])
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.setting} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
