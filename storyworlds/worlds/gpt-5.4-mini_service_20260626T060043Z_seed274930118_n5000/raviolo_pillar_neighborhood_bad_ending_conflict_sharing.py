#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "queen", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "king", "god"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str = "the neighborhood"
    glow: str = "soft lamplight"


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    sacred: bool = False


@dataclass
class StoryParams:
    setting: str
    treasure: str
    name_a: str
    name_b: str
    role_a: str
    role_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("A")
    b = world.entities.get("B")
    t = world.entities.get("treasure")
    if not a or not b or not t:
        return out
    if a.memes.get("want", 0) >= 1 and b.memes.get("want", 0) >= 1:
        sig = ("tension",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["conflict"] = a.memes.get("conflict", 0) + 1
            b.memes["conflict"] = b.memes.get("conflict", 0) + 1
            out.append("The two hearts sharpened against one another like twin spears.")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    t = world.entities.get("treasure")
    if not t or t.held_by is None:
        return out
    holder = world.entities[t.held_by]
    if holder.memes.get("conflict", 0) >= 1 and holder.meters.get("shake", 0) >= 1:
        sig = ("drop",)
        if sig not in world.fired:
            world.fired.add(sig)
            t.held_by = None
            t.meters["fallen"] = 1
            out.append("The raviolo slipped from the trembling hand and fell to the stones.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out: list[str] = []
    t = world.entities.get("treasure")
    if not t or t.meters.get("fallen", 0) < 1:
        return out
    sig = ("bad_end",)
    if sig not in world.fired:
        world.fired.add(sig)
        out.append("A crow found the raviolo first, and the little feast was lost.")
    return out


RULES = [Rule("tension", _r_tension), Rule("drop", _r_drop), Rule("bad_end", _r_bad_ending)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            msgs = rule.apply(world)
            if msgs:
                changed = True
                produced.extend(msgs)
    if narrate:
        for msg in produced:
            world.say(msg)
    return produced


def predict_fall(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    t = sim.entities["treasure"]
    return t.meters.get("fallen", 0) >= 1


def build_story(setting: Setting, treasure: Treasure, params: StoryParams) -> World:
    world = World(setting)
    a = world.add(Entity(id="A", kind="character", type=params.role_a, label=params.name_a))
    b = world.add(Entity(id="B", kind="character", type=params.role_b, label=params.name_b))
    t = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=a.id,
        caretaker=b.id,
        held_by=a.id,
    ))

    world.say(f"In the {setting.name}, under {setting.glow}, {a.label} and {b.label} met beside an old pillar.")
    world.say(f"Upon the stone lay {t.phrase}, warm as a small sun and meant to be shared.")
    world.para()
    world.say(f"{a.label} reached for the raviolo and wanted it all at once.")
    world.say(f"{b.label} also reached, because the pillar had taught both of them to hunger for the same bright prize.")
    a.memes["want"] = 1
    b.memes["want"] = 1
    a.meters["shake"] = 1
    propagate(world, narrate=True)
    world.para()
    if predict_fall(world):
        world.say(f"{b.label} called for sharing, but pride was already rising like storm-cloud smoke.")
        world.say(f"{a.label} tried to hold the raviolo tighter.")
        a.meters["shake"] = 1
        propagate(world, narrate=True)
    world.para()
    world.say("In the end, the raviolo fell, the crow came, and the pillar kept only a stain and a lesson.")
    world.say(f"Neither of them ate it, and the neighborhood remembered that a gift held in quarrel can become a bad ending.")
    world.facts.update(hero_a=a, hero_b=b, treasure=t, setting=setting, treasure_cfg=treasure)
    return world


SETTINGS = {
    "neighborhood": Setting(name="the neighborhood", glow="soft lamplight"),
    "courtyard": Setting(name="the courtyard", glow="moonlit air"),
}

TREASURES = {
    "raviolo": Treasure(label="raviolo", phrase="one golden raviolo", type="raviolo", sacred=True),
}

ROLES = ["girl", "boy", "mother", "father", "child", "hermit"]
NAMES = ["Mira", "Jon", "Sela", "Tarin", "Ivo", "Nia", "Pero", "Luma"]


def valid_combos() -> list[tuple[str, str]]:
    return [("neighborhood", "raviolo"), ("courtyard", "raviolo")]


def explain_rejection(setting: str, treasure: str) -> str:
    return f"(No story: only the raviolo myth is supported here, and the chosen setting must be a small shared place.)"


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    lines.append(asp.fact("shared_place", "neighborhood"))
    lines.append(asp.fact("shared_place", "courtyard"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T) :- setting(S), treasure(T), shared_place(S).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(p - a))
    print("only in clingo:", sorted(a - p))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, t = f["hero_a"], f["hero_b"], f["treasure"]
    return [
        f'Write a short myth for a child about {a.label} and {b.label} in the {f["setting"].name}, with a shared {t.label}.',
        f"Tell a small legend where two figures disagree over a {t.label} near a pillar, then learn too late about sharing.",
        f'Write a simple myth that uses the words "raviolo", "pillar", and "neighborhood".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, t = f["hero_a"], f["hero_b"], f["treasure"]
    return [
        QAItem(
            question=f"Who were the two figures in the neighborhood myth?",
            answer=f"They were {a.label} and {b.label}, two figures standing by the pillar in the neighborhood.",
        ),
        QAItem(
            question=f"What was the shared treasure in the story?",
            answer=f"The shared treasure was {t.phrase}, a raviolo meant to be shared.",
        ),
        QAItem(
            question="What went wrong at the end?",
            answer="The two figures argued over the raviolo, it fell, a crow took it, and the ending was bad.",
        ),
        QAItem(
            question="What did the story teach about sharing?",
            answer="It taught that when sharing is replaced by quarrel, a good gift can be lost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pillar?",
            answer="A pillar is a tall stone or wooden column that can stand like a marker or support.",
        ),
        QAItem(
            question="What is a neighborhood?",
            answer="A neighborhood is a part of a town or city where people live close to one another.",
        ),
        QAItem(
            question="What is a raviolo?",
            answer="A raviolo is a pasta pocket, often filled with soft food and served as part of a meal.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person enjoy the same thing in turn or together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} held_by={e.held_by} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic neighborhood storyworld about a raviolo, a pillar, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--role-a", choices=ROLES)
    ap.add_argument("--role-b", choices=ROLES)
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
    setting = args.setting or "neighborhood"
    treasure = args.treasure or "raviolo"
    if setting not in SETTINGS or treasure not in TREASURES:
        raise StoryError("(No valid combination matches the given options.)")
    if (setting, treasure) not in valid_combos():
        raise StoryError(explain_rejection(setting, treasure))
    role_a = args.role_a or rng.choice(["girl", "boy", "child"])
    role_b = args.role_b or rng.choice(["girl", "boy", "child"])
    name_a = args.name_a or rng.choice(NAMES)
    name_b = args.name_b or rng.choice([n for n in NAMES if n != name_a])
    return StoryParams(setting=setting, treasure=treasure, name_a=name_a, name_b=name_b, role_a=role_a, role_b=role_b)


def generate(params: StoryParams) -> StorySample:
    world = build_story(SETTINGS[params.setting], TREASURES[params.treasure], params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treasure) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, (setting, treasure) in enumerate(valid_combos()):
            params = StoryParams(
                setting=setting,
                treasure=treasure,
                name_a=NAMES[i % len(NAMES)],
                name_b=NAMES[(i + 3) % len(NAMES)],
                role_a="child",
                role_b="child",
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
