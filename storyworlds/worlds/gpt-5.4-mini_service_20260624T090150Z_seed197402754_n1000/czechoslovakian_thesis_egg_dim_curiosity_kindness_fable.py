#!/usr/bin/env python3
"""
storyworlds/worlds/czechoslovakian_thesis_egg_dim_curiosity_kindness_fable.py
=============================================================================

A small fable-style story world about Curiosity and Kindness around a fragile
Czechoslovakian thesis egg.

Premise:
- A young creature finds an egg-dim thesis egg in a village garden.
- Curiosity wants to crack it open and peek inside.
- Kindness notices it belongs to a traveling scholar and keeps it safe.
- The story turns when the hero chooses care over haste, and the scholar returns.

The world tracks:
- physical meters: warmth, crack, polish, dryness, distance
- emotional memes: curiosity, kindness, worry, relief

The prose is authored from world state; the ending image proves what changed.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mouse", "fox", "hare", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "scholar", "owl", "rabbit", "boy-child"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    light: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Tale:
    id: str
    title: str
    action: str
    danger: str
    rescue: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    type: str = "relic"
    fragile: bool = True


@dataclass
class StoryParams:
    setting: str
    tale: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "village_garden": Setting(place="the village garden", light="soft morning light", afford={"observe", "guard"}),
    "school_hall": Setting(place="the old school hall", light="dusty window light", afford={"read", "guard"}),
    "plum_orchard": Setting(place="the plum orchard", light="golden dusk", afford={"observe", "guard"}),
}

TALES = {
    "czechoslovakian_thesis_egg": Tale(
        id="czechoslovakian_thesis_egg",
        title="the Czechoslovakian thesis egg",
        action="open the thesis egg to see the pages inside",
        danger="a hard tap could crack the shell and lose the careful pages",
        rescue="wait, warm it gently, and carry it to the scholar",
        keywords={"czechoslovakian", "thesis", "egg-dim", "curiosity", "kindness"},
    ),
}

RELICS = {
    "thesis_egg": Relic(
        id="thesis_egg",
        label="thesis egg",
        phrase="a tiny Czechoslovakian thesis egg with a dull golden shell",
    )
}

HEROES = [
    ("Lina", "girl"),
    ("Marek", "boy"),
    ("Toma", "boy"),
    ("Nina", "girl"),
]

TRAITS = ["curious", "kind", "careful", "bright"]


def aspiration_text(tale: Tale) -> str:
    return " ".join(sorted(tale.keywords))


def reasonableness_gate(setting: Setting, tale: Tale, relic: Relic) -> bool:
    return "guard" in setting.afford and relic.fragile and "thesis" in tale.id


def select_combo(setting_name: str, tale_name: str) -> tuple[Setting, Tale, Relic]:
    if setting_name not in SETTINGS:
        raise StoryError(f"Unknown setting: {setting_name}")
    if tale_name not in TALES:
        raise StoryError(f"Unknown tale: {tale_name}")
    setting = SETTINGS[setting_name]
    tale = TALES[tale_name]
    relic = RELICS["thesis_egg"]
    if not reasonableness_gate(setting, tale, relic):
        raise StoryError("No valid fable: the setting cannot safely guard the thesis egg.")
    return setting, tale, relic


def _do_peek(world: World, hero: Entity, relic: Entity, tale: Tale) -> None:
    if ("peek", hero.id) in world.fired:
        return
    world.fired.add(("peek", hero.id))
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    relic.meters["wobble"] = relic.meters.get("wobble", 0) + 1
    world.say(f"{hero.id} leaned close because {hero.pronoun('possessive')} curiosity was bright.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {tale.action}, but the shell looked egg-dim and fragile.")


def _do_warn(world: World, guardian: Entity, hero: Entity, relic: Entity, tale: Tale) -> None:
    if ("warn", guardian.id) in world.fired:
        return
    world.fired.add(("warn", guardian.id))
    guardian.memes["kindness"] = guardian.memes.get("kindness", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{guardian.id} saw the danger and spoke gently: "
        f'"A hard tap could crack the {relic.label}. {tale.danger}."'
    )


def _do_guard(world: World, hero: Entity, relic: Entity, tale: Tale) -> None:
    if ("guard", hero.id) in world.fired:
        return
    world.fired.add(("guard", hero.id))
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    relic.meters["safe"] = relic.meters.get("safe", 0) + 1
    relic.meters["warmth"] = relic.meters.get("warmth", 0) + 1
    hero.memes["curiosity"] = max(0.0, hero.memes.get("curiosity", 0) - 0.5)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"{hero.id} chose kindness instead of haste, and {hero.pronoun('possessive')} hands grew careful."
    )
    world.say(f"{hero.pronoun().capitalize()} tucked the {relic.label} in a soft nest of cloth and waited.")
    world.say(f"Then the air felt calmer, because {tale.rescue}.")


def tell(setting: Setting, tale: Tale, hero_name: str, hero_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guardian = world.add(Entity(id="Scholar", kind="character", type="scholar"))
    relic = world.add(Entity(
        id="Relic",
        type="relic",
        label="thesis egg",
        phrase="a tiny Czechoslovakian thesis egg with a dull golden shell",
        owner=guardian.id,
        caretaker=guardian.id,
    ))
    hero.memes["curiosity"] = 1
    hero.memes["kindness"] = 0
    relic.meters["safe"] = 1
    relic.meters["warmth"] = 0
    world.facts.update(hero=hero, guardian=guardian, relic=relic, tale=tale, setting=setting)

    world.say(f"In {setting.place}, under {setting.light}, {hero.id} found {relic.phrase}.")
    world.say(f"The little thing was called {tale.title}, and it seemed to hold a Czechoslovakian thesis inside.")
    world.para()

    _do_peek(world, hero, relic, tale)
    _do_warn(world, guardian, hero, relic, tale)
    world.para()
    _do_guard(world, hero, relic, tale)

    world.say(
        f"At the end, the thesis egg stayed whole, and {hero.id} learned that kindness can protect curiosity."
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS:
        for t in TALES:
            setting, tale, relic = SETTINGS[s], TALES[t], RELICS["thesis_egg"]
            if reasonableness_gate(setting, tale, relic):
                out.append((s, t))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about Curiosity, Kindness, and a Czechoslovakian thesis egg.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
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
    tale = args.tale or rng.choice(list(TALES))
    if (setting, tale) not in valid_combos():
        raise StoryError("No valid combination matches the given options.")
    name, hero_type = None, None
    if args.hero_type:
        hero_type = args.hero_type
    else:
        name, hero_type = rng.choice(HEROES)
    if args.name:
        name = args.name
    if name is None:
        name = rng.choice([h for h, t in HEROES if t == hero_type])
    return StoryParams(setting=setting, tale=tale, hero_name=name, hero_type=hero_type)


def generate(params: StoryParams) -> StorySample:
    setting, tale, relic = select_combo(params.setting, params.tale)
    world = tell(setting, tale, params.hero_name, params.hero_type)
    hero = world.facts["hero"]
    guardian = world.facts["guardian"]
    story = world.render()
    prompts = [
        f"Write a short fable about {params.hero_name}, Curiosity, Kindness, and {relic.phrase}.",
        f"Tell a child-friendly story in which {params.hero_name} finds something egg-dim in {setting.place}.",
        f"Write a gentle fable where a Czechoslovakian thesis egg is protected by kindness instead of broken by curiosity.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero_name} find in {setting.place}?",
            answer=f"{params.hero_name} found {relic.phrase}, a fragile Czechoslovakian thesis egg.",
        ),
        QAItem(
            question=f"What did {params.hero_name} want to do at first?",
            answer=f"{params.hero_name} wanted to open the thesis egg and peek inside, because curiosity was strong.",
        ),
        QAItem(
            question=f"How was the thesis egg kept safe?",
            answer=f"{params.hero_name} used kindness, wrapped it gently, and waited for the scholar instead of tapping it open.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more, look closer, or ask questions.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is caring about another person or thing and choosing gentle, helpful actions.",
        ),
        QAItem(
            question="Why should a fragile egg be handled carefully?",
            answer="A fragile egg can crack easily, so careful hands help keep it whole.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
tale(T) :- tale_fact(T).
relic(R) :- relic_fact(R).

valid(S,T) :- setting(S), tale(T), afford(S,guard), fragile(thesis_egg), tale_has(T,thesis).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
        for a in sorted(SETTINGS[s].afford):
            lines.append(asp.fact("afford", s, a))
    for t in TALES:
        lines.append(asp.fact("tale_fact", t))
        lines.append(asp.fact("tale_has", t, "thesis"))
    lines.append(asp.fact("relic_fact", "thesis_egg"))
    lines.append(asp.fact("fragile", "thesis_egg"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(sorted(asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s, t in valid_combos():
            p = StoryParams(setting=s, tale=t, hero_name="Lina", hero_type="girl", seed=base_seed)
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
