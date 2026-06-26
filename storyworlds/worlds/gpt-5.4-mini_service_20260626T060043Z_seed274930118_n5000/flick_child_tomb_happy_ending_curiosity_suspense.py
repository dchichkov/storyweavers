#!/usr/bin/env python3
"""
storyworlds/worlds/flick_child_tomb_happy_ending_curiosity_suspense.py
=======================================================================

A small space-adventure storyworld about a curious child, a dark tomb, a
flickering light, and a safe happy ending.

Seed tale inspiration:
---
A child on a starship hears about an old tomb on a dust moon. The child is
curious, but the tomb feels spooky and full of suspense. A flickering lantern
helps the child look inside, discover the tomb is only a quiet memorial, and
bring home a gentle wonder instead of fear.
---

Design goals:
- Child-facing space-adventure prose.
- A real simulated turn: curiosity pulls the child forward, suspense rises in
  the tomb, and a careful action resolves the fear.
- Physical meters and emotional memes both matter.
- Invalid or unreasonable choices raise StoryError with clear reasons.
- Inline ASP rules mirror the Python reasonableness gate.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    located_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str
    backdrop: str
    dark: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    warns: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    tool: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_character()]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "moon_tomb": Setting(
        place="the moon tomb",
        backdrop="an old silver tomb under a glassy crater",
        dark=True,
        affords={"peek", "enter", "listen"},
    ),
    "star_cavern": Setting(
        place="the star cavern",
        backdrop="a cave full of pale stones that shine like little moons",
        dark=True,
        affords={"peek", "enter", "listen"},
    ),
    "orbital_ruins": Setting(
        place="the orbital ruins",
        backdrop="broken arches drifting beside a quiet station wall",
        dark=True,
        affords={"peek", "enter", "listen"},
    ),
}

TOOLS = {
    "flicker_lamp": Tool(
        id="flicker_lamp",
        label="a flickering lamp",
        phrase="a small flickering lamp",
        helps={"peek", "enter"},
        warns={"dark"},
    ),
    "star_torch": Tool(
        id="star_torch",
        label="a star torch",
        phrase="a bright star torch",
        helps={"peek", "enter", "listen"},
        warns={"dark"},
    ),
    "glow_panel": Tool(
        id="glow_panel",
        label="a glow panel",
        phrase="a tiny glow panel",
        helps={"peek"},
        warns={"dark"},
    ),
}

TRAITS = ["curious", "brave", "gentle", "quiet", "bright", "careful"]
GIRL_NAMES = ["Mina", "Ivy", "Luna", "Zuri", "Nia", "Pia", "Mira"]
BOY_NAMES = ["Taj", "Finn", "Ezra", "Kian", "Noel", "Ravi", "Jett"]

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def tomb_is_spooky(setting: Setting) -> bool:
    return setting.dark and "enter" in setting.affords


def tool_can_face_tomb(tool: Tool) -> bool:
    return "enter" in tool.helps or "peek" in tool.helps


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        if not tomb_is_spooky(setting):
            continue
        for tid, tool in TOOLS.items():
            if tool_can_face_tomb(tool):
                combos.append((sid, tid))
    return combos


def explain_rejection(setting: Setting, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} is not enough for {setting.place}. "
        f"The child would have no safe way to face the dark tomb, so the tale "
        f"would not have a fair suspense-and-happy-ending shape.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------


def _narrate_opening(world: World, child: Entity, guide: Entity, tool: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a big curious heart."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved space stories, and {guide.label} "
        f"kept {child.pronoun('possessive')} hands busy with {tool.phrase}."
    )


def _narrate_arrival(world: World, child: Entity, guide: Entity) -> None:
    world.para()
    world.say(
        f"One quiet night, {child.id} and {guide.label} walked to {world.setting.place}."
    )
    world.say(
        f"{world.setting.backdrop.capitalize()} waited in the dust, and even the stars "
        f"looked very still."
    )


def _narrate_curiosity(world: World, child: Entity, tool: Entity) -> None:
    child.memes["curiosity"] = child.e("curiosity") + 1
    world.say(
        f"{child.id} wanted to look inside, because the tomb felt strange and mysterious."
    )
    world.say(
        f"{child.pronoun().capitalize()} flicked {tool.pronoun('possessive')} lamp, and a shy little light jumped across the stone."
    )
    tool.meters["light"] = tool.m("light") + 1


def _narrate_suspense(world: World, child: Entity, guide: Entity) -> None:
    child.memes["suspense"] = child.e("suspense") + 1
    world.say(
        f"Inside, the air was cool and still. A tiny echo answered every step, which made {child.id} hold {child.pronoun('possessive')} breath."
    )
    world.say(
        f"{guide.label} stayed near, ready to help if the shadows felt too big."
    )


def _narrate_discovery(world: World, child: Entity) -> None:
    child.memes["wonder"] = child.e("wonder") + 1
    world.say(
        f"Then the light found a small memorial plaque and a bowl of moon flowers that had dried long ago."
    )
    world.say(
        f"The tomb was not a monster's lair at all. It was a quiet place made to remember someone who had loved the stars."
    )


def _narrate_happy_ending(world: World, child: Entity, guide: Entity, tool: Entity) -> None:
    child.memes["fear"] = 0.0
    child.memes["joy"] = child.e("joy") + 1
    world.say(
        f"{child.id} smiled, because the suspense had turned into wonder."
    )
    world.say(
        f"{guide.label} tucked the {tool.label} closer, and together they left the tomb gently, with the moon dust sparkling under their boots."
    )
    world.say(
        f"On the walk home, {child.id} carried a tiny pressed flower from the memorial, and the stars above looked warm instead of spooky."
    )


def simulate(setting: Setting, tool_cfg: Tool, name: str, gender: str, guide_type: str, trait: str) -> World:
    world = World(setting)

    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        meters={"steps": 0.0},
        memes={"curiosity": 1.0, "suspense": 0.0, "joy": 0.0, "fear": 1.0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_type,
        label=f"the {guide_type}",
        memes={"care": 1.0},
    ))
    tool = world.add(Entity(
        id=tool_cfg.id,
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        caretaker=guide.id,
        carried_by=child.id,
    ))
    tomb = world.add(Entity(
        id="tomb",
        type="place",
        label="the tomb",
        phrase=setting.place,
        located_in=setting.place,
    ))

    world.facts.update(child=child, guide=guide, tool=tool, tomb=tomb, setting=setting)

    _narrate_opening(world, child, guide, tool)
    _narrate_arrival(world, child, guide)
    _narrate_curiosity(world, child, tool)
    _narrate_suspense(world, child, guide)
    _narrate_discovery(world, child)
    _narrate_happy_ending(world, child, guide, tool)

    world.facts["ending"] = "happy"
    world.facts["trait"] = trait
    return world


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        f'Write a short space-adventure story about a curious child who carries {tool.phrase} into {setting.place}.',
        f"Tell a suspenseful but gentle tale where {child.id} goes to a tomb and the light flickers in the dark.",
        f'Write a happy-ending story that includes the words "flick", "child", and "tomb".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who went to {setting.place} in the story?",
            answer=f"{child.id} went there with {guide.label}.",
        ),
        QAItem(
            question=f"What did {child.id} flick to help look inside the tomb?",
            answer=f"{child.id} flicked {tool.phrase} so the tomb would not stay dark.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful before the ending?",
            answer=(
                f"It felt suspenseful because the tomb was dark and still, and {child.id} did not know what was inside until the light showed it."
            ),
        ),
        QAItem(
            question=f"What did {child.id} find in the tomb?",
            answer=(
                f"{child.id} found a quiet memorial plaque and moon flowers, which showed the tomb was a place for remembering, not a place for danger."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily, with {child.id} leaving the tomb calm, curious, and glad to have seen something beautiful."
            ),
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a tomb?",
        answer="A tomb is a place where people keep the memory of someone who died. It is often quiet and respectful.",
    ),
    QAItem(
        question="What does flick mean?",
        answer="To flick something means to move it with a quick small motion, like turning on a light or tapping a switch.",
    ),
    QAItem(
        question="Why do explorers carry lights in dark places?",
        answer="Explorers carry lights so they can see where they are walking and avoid bumps, holes, or other surprises.",
    ),
    QAItem(
        question="What is curiosity?",
        answer="Curiosity is the feeling that makes you want to learn about something new or unknown.",
    ),
    QAItem(
        question="What is suspense?",
        answer="Suspense is the feeling of wondering what will happen next, especially when something seems mysterious or tense.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_combo(S, T) :- setting(S), tool(T), spooky(S), helps_face(T).
spooky(S) :- dark(S), affords(S, enter).
helps_face(T) :- helps(T, enter).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dark:
            lines.append(asp.fact("dark", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
        for w in sorted(t.warns):
            lines.append(asp.fact("warns", tid, w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure storyworld: a curious child, a dark tomb, a flickering light, and a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father", "captain", "teacher"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.setting and args.tool:
        if (args.setting, args.tool) not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.setting], TOOLS[args.tool]))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    if (setting, tool) not in valid_combos():
        raise StoryError(explain_rejection(SETTINGS[setting], TOOLS[tool]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["mother", "father", "captain", "teacher"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, tool=tool, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = simulate(
        SETTINGS[params.setting],
        TOOLS[params.tool],
        params.name,
        params.gender,
        params.guide,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.located_in:
            bits.append(f"located_in={e.located_in}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


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
    StoryParams(setting="moon_tomb", tool="flicker_lamp", name="Mina", gender="girl", guide="mother", trait="curious"),
    StoryParams(setting="star_cavern", tool="star_torch", name="Jett", gender="boy", guide="father", trait="brave"),
    StoryParams(setting="orbital_ruins", tool="glow_panel", name="Luna", gender="girl", guide="captain", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/tool combos:\n")
        for s, t in combos:
            print(f"  {s:14} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
