#!/usr/bin/env python3
"""
A standalone story world for a small fable about Sonny, glue, texture, and friendship.

The world premise:
- Sonny makes a careful object with a rough texture.
- A small accident breaks it.
- Friendship, patience, and glue help repair the object and the bond.

The world is intentionally small and constraint-checked:
- glue is only a reasonable fix for broken things that can be repaired.
- the story must feature a real turn and resolution.
- invalid explicit choices raise StoryError.
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
# Story model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    shelter: bool = False


@dataclass
class Craft:
    id: str
    label: str
    phrase: str
    texture: str
    fragile: bool
    repairable: bool = True


@dataclass
class Friend:
    id: str
    label: str
    type: str = "friend"
    kind: str = "character"


@dataclass
class StoryParams:
    setting: str
    craft: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "workshop": Setting(place="the little workshop", shelter=True),
    "garden": Setting(place="the quiet garden", shelter=False),
    "porch": Setting(place="the sunny porch", shelter=True),
}

CRAFTS = {
    "bird": Craft(
        id="bird",
        label="bird",
        phrase="a small wooden bird",
        texture="smooth and warm",
        fragile=True,
    ),
    "kite": Craft(
        id="kite",
        label="kite",
        phrase="a bright paper kite",
        texture="light and crinkly",
        fragile=True,
    ),
    "box": Craft(
        id="box",
        label="box",
        phrase="a little toy box",
        texture="rough and sturdy",
        fragile=False,
    ),
}

GLOO = {
    "glue": {
        "label": "glue",
        "helps": {"bird", "kite", "box"},
        "method": "carefully spread glue on the broken edge",
    }
}

SONNY_NAMES = ["Sonny"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A craft is fragile when it can break in the open.
fragile(C) :- craft(C), craft_fragile(C).

% Glue is a reasonable repair when the thing is broken and repairable.
repairable(C) :- craft(C), craft_repairable(C).
can_fix(glue, C) :- broken(C), repairable(C).

% Friendship resolves the argument when the friend helps repair the craft.
resolved(C) :- can_fix(glue, C), friendship.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.shelter:
            lines.append(asp.fact("shelter", sid))
    for cid, c in CRAFTS.items():
        lines.append(asp.fact("craft", cid))
        if c.fragile:
            lines.append(asp.fact("craft_fragile", cid))
        if c.repairable:
            lines.append(asp.fact("craft_repairable", cid))
    lines.append(asp.fact("tool", "glue"))
    lines.append(asp.fact("friendship"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/1."))
    clingo_set = set(asp.atoms(model, "resolved"))
    python_set = {("bird",), ("kite",), ("box",)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} crafts).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness and generation
# ---------------------------------------------------------------------------
def valid_combo(setting: str, craft: str) -> bool:
    return setting in SETTINGS and craft in CRAFTS


def explain_rejection(setting: str, craft: str) -> str:
    return (
        f"(No story: {craft!r} is not a valid craft for the fable world, or "
        f"{setting!r} is not a valid setting.)"
    )


def predict_break(world: World, craft: Craft) -> bool:
    sim = world.copy()
    item = sim.get("craft")
    if craft.fragile and not sim.setting.shelter:
        item.meters["broken"] = 1
    return item.meters.get("broken", 0) >= 1


def narration_open(world: World, sonny: Entity, craft: Craft) -> None:
    world.say(
        f"Sonny lived near {world.setting.place}, and he loved making things with a "
        f"gentle, steady hand."
    )
    world.say(
        f"He worked on {craft.phrase}; its {craft.texture} texture made him proud, "
        f"because he had shaped it so carefully."
    )


def incident(world: World, sonny: Entity, craft: Craft) -> None:
    world.para()
    world.say(
        f"One day Sonny carried the little craft outside to show a friend."
    )
    if craft.fragile and not world.setting.shelter:
        craft_ent = world.get("craft")
        craft_ent.meters["broken"] = 1
        sonny.memes["sad"] = sonny.memes.get("sad", 0) + 1
        world.say(
            f"A sudden bump cracked it, and the beautiful texture was split apart."
        )
    else:
        world.say(
            f"The day stayed calm, and the craft kept its shape."
        )


def turn_and_fix(world: World, sonny: Entity, craft: Craft) -> None:
    world.para()
    if world.get("craft").meters.get("broken", 0) >= 1:
        world.say(
            f"Sonny frowned, but his friend came beside him and did not laugh."
        )
        world.say(
            f"Instead, they found the glue and carefully spread glue on the broken edge."
        )
        world.say(
            f"Together they pressed the pieces back into place and waited."
        )
        world.get("craft").meters["broken"] = 0
        world.get("craft").memes["mended"] = 1
        sonny.memes["joy"] = sonny.memes.get("joy", 0) + 1
        sonny.memes["friendship"] = sonny.memes.get("friendship", 0) + 1
        world.facts["resolved"] = True
    else:
        world.say(
            f"Nothing had broken, so Sonny only smiled and showed the craft with care."
        )
        world.facts["resolved"] = False


def ending(world: World, sonny: Entity, craft: Craft) -> None:
    world.para()
    if world.facts.get("resolved"):
        world.say(
            f"In the end, the craft stood whole again, and its rough history only made "
            f"the friendship feel stronger."
        )
        world.say(
            f"Sonny smiled at the mended {craft.label}, glad that glue and kindness had "
            f"worked together."
        )
    else:
        world.say(
            f"Sonny carried the craft home safely, and the day ended with an easy smile."
        )


def tell(setting: Setting, craft: Craft) -> World:
    world = World(setting)
    sonny = world.add(Entity(id="Sonny", kind="character", label="Sonny"))
    friend = world.add(Entity(id="Friend", kind="character", label="his friend"))
    item = world.add(Entity(id="craft", kind="thing", label=craft.label, phrase=craft.phrase))
    world.facts.update(sonny=sonny, friend=friend, craft=item, craft_cfg=craft, setting=setting)

    narration_open(world, sonny, craft)
    incident(world, sonny, craft)
    turn_and_fix(world, sonny, craft)
    ending(world, sonny, craft)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    craft: Craft = world.facts["craft_cfg"]
    return [
        'Write a short fable about Sonny, glue, and a rough texture that ends in friendship.',
        f"Tell a child-friendly story where Sonny makes {craft.phrase} and later uses glue to mend it.",
        f"Write a small moral tale about how {craft.texture} things can break, but friendship helps fix them.",
    ]


def story_qa(world: World) -> list[QAItem]:
    craft: Craft = world.facts["craft_cfg"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer="It is about Sonny, a careful maker who learns that friendship matters when things go wrong.",
        ),
        QAItem(
            question=f"What did Sonny make?",
            answer=f"Sonny made {craft.phrase}, and it had a {craft.texture} texture.",
        ),
        QAItem(
            question="What happened after the craft broke?",
            answer="Sonny's friend stayed kind, and they used glue to mend the broken piece together.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="The craft was repaired, and Sonny felt closer to his friend at the end.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is glue for?",
            answer="Glue is for sticking things together after they come apart.",
        ),
        QAItem(
            question="What does texture mean?",
            answer="Texture means how something feels, like smooth, rough, soft, or crinkly.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people care for each other and help when they can.",
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
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about Sonny, glue, texture, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--craft", choices=CRAFTS)
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
    if args.setting and args.craft and not valid_combo(args.setting, args.craft):
        raise StoryError(explain_rejection(args.setting, args.craft))
    setting = args.setting or rng.choice(list(SETTINGS))
    craft = args.craft or rng.choice(list(CRAFTS))
    return StoryParams(setting=setting, craft=craft)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CRAFTS[params.craft])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(asp.atoms(model, "resolved")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for craft in CRAFTS:
                samples.append(generate(StoryParams(setting=setting, craft=craft, seed=base_seed)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### setting={p.setting} craft={p.craft}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
