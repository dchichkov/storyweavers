#!/usr/bin/env python3
"""
storyworlds/worlds/burden_cry_derrick_conflict_space_adventure.py
==================================================================

A small space-adventure story world about a heavy burden, a crying moment,
and a useful derrick that helps turn Conflict into a safe plan.

Seed tale idea:
---
On a little moon base, a child engineer wants to move a heavy burden crate
across the docking bay with a derrick. The crate is too important to drop,
and the crane arm is a little rusty, so the captain worries. The child cries
for a moment, but then they work together, reset the derrick, and lift the
burden safely into the cargo hold.

World model:
---
- physical meters: weight, strain, damage, dust, lift, safety
- emotional memes: joy, worry, conflict, relief, pride, cry, trust

The story is generated from simulated state, not from a frozen template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    details: str


@dataclass
class Burden:
    label: str
    phrase: str
    weight: int
    place: str


@dataclass
class Derrick:
    label: str
    phrase: str
    safe_limit: int
    fix_phrase: str
    finish_phrase: str


@dataclass
class StoryParams:
    place: str
    burden: str
    derrick: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "moon_base": Setting(
        place="the moon base docking bay",
        details="The silver walls hummed softly, and the cargo lights blinked like little stars.",
    ),
    "asteroid_port": Setting(
        place="the asteroid port",
        details="Tiny rock dust floated by the windows, and the loading rails shone under bright lamps.",
    ),
    "orbit_station": Setting(
        place="the orbit station cargo ring",
        details="The station curved overhead, and the cargo floor felt steady under careful boots.",
    ),
}

BURDENS = {
    "toolbox": Burden(
        label="toolbox",
        phrase="a heavy red toolbox",
        weight=6,
        place="the cargo shelf",
    ),
    "seed_crate": Burden(
        label="crate",
        phrase="a sealed supply crate",
        weight=8,
        place="the loading pad",
    ),
    "water_tank": Burden(
        label="tank",
        phrase="a big water tank",
        weight=10,
        place="the docking floor",
    ),
    "spare_panel": Burden(
        label="panel",
        phrase="a wide spare panel",
        weight=7,
        place="the service cart",
    ),
}

DERRICKS = {
    "cargo_derrick": Derrick(
        label="derrick",
        phrase="the tall cargo derrick",
        safe_limit=7,
        fix_phrase="tighten the joint and set the safety latch",
        finish_phrase="the derrick swung once, then lifted cleanly",
    ),
    "little_derrick": Derrick(
        label="derrick",
        phrase="the little maintenance derrick",
        safe_limit=5,
        fix_phrase="lock the wheels and balance the hook",
        finish_phrase="the derrick hummed and raised the load inch by inch",
    ),
    "dock_derrick": Derrick(
        label="derrick",
        phrase="the dock derrick with bright yellow arms",
        safe_limit=8,
        fix_phrase="reset the cable guide and steady the base",
        finish_phrase="the derrick steadied, and the burden rose like a slow kite",
    ),
}

NAMES = ["Derrick", "Mina", "Aria", "Kai", "Nova", "Leif", "Iris", "Timo"]
HELPERS = ["captain", "mechanic", "pilot", "crew chief"]
ROLES = ["engineer", "cadet", "helper", "navigator"]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = _copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _get(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _set(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _gain(entity: Entity, key: str, value: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + value


def _emote(entity: Entity, key: str, value: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def predict_load(world: World, burden: Burden, derrick: Derrick) -> dict:
    sim = world.copy()
    burden_ent = sim.get("burden")
    derrick_ent = sim.get("derrick")
    _gain(burden_ent, "weight", burden.weight)
    if burden.weight > derrick.safe_limit:
        _gain(derrick_ent, "strain", 2.0)
        _gain(burden_ent, "risk", 1.0)
    return {
        "too_heavy": burden.weight > derrick.safe_limit,
        "strain": _get(derrick_ent, "strain"),
    }


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.role, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    burden = BURDENS[params.burden]
    derrick = DERRICKS[params.derrick]

    world.add(
        Entity(
            id="burden",
            type=burden.label,
            label=burden.label,
            phrase=burden.phrase,
            caretaker=helper.id,
            meters={"weight": float(burden.weight), "dust": 0.0, "risk": 0.0},
        )
    )
    world.add(
        Entity(
            id="derrick",
            type="machine",
            label="derrick",
            phrase=derrick.phrase,
            meters={"strain": 0.0, "lift": 0.0, "damage": 0.0, "safety": 1.0},
            memes={"trust": 0.0},
        )
    )
    world.facts.update(hero=hero, helper=helper, burden=burden, derrick=derrick)
    return world


def introduce(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    burden = world.facts["burden"]
    derrick = world.facts["derrick"]
    world.say(
        f"In {world.setting.place}, {hero.label} loved solving hard jobs with {helper.label_word if hasattr(helper, 'label_word') else helper.label}."
    )
    world.say(
        f"{hero.label} had one big job that day: move {burden.phrase} with {derrick.phrase}."
    )


def helper_label(helper: Entity) -> str:
    return helper.label if helper.label else f"the {helper.type}"


def act_turn(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    burden = world.facts["burden"]
    derrick = world.facts["derrick"]

    _emote(hero, "joy", 1.0)
    world.say(
        f"{hero.label} wanted to lift the burden right away, because the cargo bay felt like a tiny mission."
    )
    if burden.weight > derrick.safe_limit:
        _emote(helper, "worry", 1.0)
        _emote(hero, "cry", 1.0)
        _emote(hero, "conflict", 1.0)
        world.say(
            f"But {helper_label(helper)} frowned. {burden.phrase.capitalize()} was heavier than {derrick.phrase} should carry in one go."
        )
        world.say(
            f"{hero.label} felt a lump in {hero.pronoun('possessive')} throat and started to cry."
        )
        world.say(
            f"For a moment, the whole dock felt full of Conflict."
        )
    else:
        world.say(
            f"{derrick.phrase} looked ready, and {hero.label} grinned at the safe number on the panel."
        )


def repair_and_lift(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    burden = world.facts["burden"]
    derrick = world.facts["derrick"]

    if burden.weight > derrick.safe_limit:
        world.say(
            f"Then {helper_label(helper)} showed {hero.label} how to {derrick.fix_phrase}."
        )
        _gain(world.get("derrick"), "strain", 0.0)
        _gain(world.get("derrick"), "lift", 1.0)
        _emote(hero, "relief", 1.0)
        _emote(hero, "trust", 1.0)
        _set(world.get("hero"), "cry", 0.0)
        _set(world.get("hero"), "conflict", 0.0)
        world.say(
            f"{hero.label} wiped the tears away, nodded, and helped {helper_label(helper)} do the fix."
        )
        world.say(
            f"At last, {derrick.finish_phrase}, and {burden.phrase} floated up into the cargo hold."
        )
    else:
        _gain(world.get("derrick"), "lift", 1.0)
        _emote(hero, "pride", 1.0)
        world.say(
            f"{derrick.finish_phrase}, and {burden.phrase} went exactly where it needed to go."
        )

    world.say(
        f"By the end, {hero.label} was smiling again, and the moon base was quiet and safe."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    act_turn(world)
    world.para()
    repair_and_lift(world)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for burden_id, burden in BURDENS.items():
            for derrick_id, derrick in DERRICKS.items():
                if burden.weight >= derrick.safe_limit:
                    combos.append((place, burden_id, derrick_id))
    return combos


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, b, d in valid_combos():
        for role in ["engineer", "cadet", "helper"]:
            combos.append((place, b, d, role))
    return combos


def choose_name(rng: random.Random) -> str:
    return rng.choice(NAMES)


def choose_helper(rng: random.Random) -> str:
    return rng.choice(HELPERS)


def choose_role(rng: random.Random) -> str:
    return rng.choice(ROLES)


def choose_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.burden is None or c[1] == args.burden)
        and (args.derrick is None or c[2] == args.derrick)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, burden, derrick = choose_combo(args, rng)
    return StoryParams(
        place=place,
        burden=burden,
        derrick=derrick,
        name=args.name or choose_name(rng),
        role=args.role or choose_role(rng),
        helper=args.helper or choose_helper(rng),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    burden = f["burden"]
    derrick = f["derrick"]
    return [
        f'Write a short space adventure about {hero.label} and a heavy {burden.label} at {world.setting.place}.',
        f"Tell a child-friendly story where a {hero.type} named {hero.label} faces Conflict while using {derrick.phrase}.",
        f'Write a simple story that includes the words "burden", "cry", and "derrick" in a moon-base rescue scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    burden = f["burden"]
    derrick = f["derrick"]
    qa = [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {hero.label}, who worked with {helper.label_word if hasattr(helper, 'label_word') else helper.label} to move a heavy burden safely.",
        ),
        QAItem(
            question=f"What made {hero.label} cry for a moment?",
            answer=f"{burden.phrase.capitalize()} was too heavy for {derrick.phrase} to lift the first time, so {hero.label} got upset and cried.",
        ),
        QAItem(
            question=f"How did they fix the problem with the derrick?",
            answer=f"They tightened and steadied {derrick.phrase} so it could lift the burden safely instead of straining in the dock.",
        ),
    ]
    if _get(world.get("hero"), "conflict") == 0.0:
        qa.append(
            QAItem(
                question=f"What changed after the helper spoke to {hero.label}?",
                answer=f"The Conflict settled down, the tears stopped, and {hero.label} helped finish the job with a calmer heart.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a burden?",
            answer="A burden is something heavy or difficult to carry, so people often need help moving it safely.",
        ),
        QAItem(
            question="What is a derrick?",
            answer="A derrick is a lifting machine with a strong arm, used to raise heavy things like crates or panels.",
        ),
        QAItem(
            question="Why do people cry?",
            answer="People cry when they feel sad, hurt, scared, or overwhelmed, and tears can help show that they need comfort.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for b, burden in BURDENS.items():
        lines.append(asp.fact("burden", b))
        lines.append(asp.fact("weight", b, burden.weight))
    for d, derrick in DERRICKS.items():
        lines.append(asp.fact("derrick", d))
        lines.append(asp.fact("limit", d, derrick.safe_limit))
    return "\n".join(lines)


ASP_RULES = r"""
too_heavy(B,D) :- burden(B), derrick(D), weight(B,W), limit(D,L), W >= L.
valid_story(P,B,D) :- place(P), burden(B), derrick(D), too_heavy(B,D).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about burden, cry, derrick, and Conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--derrick", choices=DERRICKS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    StoryParams(place="moon_base", burden="water_tank", derrick="cargo_derrick", name="Derrick", role="engineer", helper="captain"),
    StoryParams(place="asteroid_port", burden="toolbox", derrick="little_derrick", name="Nova", role="cadet", helper="mechanic"),
    StoryParams(place="orbit_station", burden="spare_panel", derrick="dock_derrick", name="Mina", role="helper", helper="crew chief"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.burden} with {p.derrick} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
