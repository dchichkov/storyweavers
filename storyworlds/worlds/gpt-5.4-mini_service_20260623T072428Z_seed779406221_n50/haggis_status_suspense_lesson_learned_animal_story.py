#!/usr/bin/env python3
"""
storyworlds/worlds/haggis_status_suspense_lesson_learned_animal_story.py
=========================================================================

A small Animal Story-style world about haggis, status, suspense, and a lesson
learned. A young animal wants a little status boost, a tempting haggis becomes
the source of suspense, and the ending shows what changed in the world.

This script is standalone and uses only the stdlib plus the shared result
containers. It also includes a reasonableness gate and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "dog", "boar", "bear", "rabbit", "cat"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Creature:
    type: str
    name: str
    trait: str
    status_goal: str
    status_label: str


@dataclass
class Haggis:
    id: str
    label: str
    phrase: str
    smell: str
    tempting: bool = True


@dataclass
class Setting:
    place: str
    detail: str


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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("suspense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.entities.values():
            if other.kind == "character":
                other.memes["attention"] += 1
        out.append("__suspense__")
    return out


def _r_lose_status(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["mess"] < THRESHOLD:
            continue
        sig = ("lose_status", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["status"] = max(0.0, ent.memes["status"] - 1.0)
        out.append(f"{ent.id} felt less grand.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["lesson"] < THRESHOLD:
            continue
        sig = ("lesson", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["calm"] += 1
        out.append("__lesson__")
    return out


CAUSAL_RULES = [
    _r_suspense,
    _r_lose_status,
    _r_lesson,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def status_at_risk(goal: str, haggis: Haggis) -> bool:
    return goal == "status" and haggis.tempting


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for h in HAGGIS:
            if h.tempting:
                combos.append((place, h.id))
    return combos


def avoid_story_error(place: str, haggis: Haggis) -> str:
    return f"(No story: {haggis.label} would not create the right kind of suspense at {place}.)"


def predict(world: World, kid_id: str) -> dict:
    sim = world.copy()
    kid = sim.get(kid_id)
    kid.meters["mess"] += 1
    propagate(sim, narrate=False)
    return {
        "status_drop": kid.memes["status"] < 0.0,
        "mess": kid.meters["mess"],
    }


def raise_status(world: World, kid: Entity) -> None:
    kid.memes["status"] += 1
    world.say(f"{kid.id} tried to act grand and keep everyone looking at {kid.id}.")


def set_scene(world: World, kid: Entity, setting: Setting) -> None:
    world.say(f"At {setting.place}, {setting.detail}")
    world.say(f"{kid.id} was a little {kid.type} who liked being noticed.")


def tempt(world: World, kid: Entity, haggis: Haggis) -> None:
    kid.memes["worry"] += 1
    world.say(
        f"Then {kid.id} smelled {haggis.smell}. {kid.id} wanted {haggis.label} "
        f"because it looked like a fancy treat."
    )
    world.say(f"The air felt still, as if something important might happen next.")


def spill(world: World, kid: Entity, haggis: Haggis) -> None:
    kid.meters["mess"] += 1
    kid.memes["status"] += 0.5
    world.say(
        f"{kid.id} reached for {haggis.phrase}, and a little mess spread on "
        f"{kid.id}'s paws."
    )
    propagate(world, narrate=False)


def warn(world: World, parent: Entity, kid: Entity, haggis: Haggis) -> None:
    pred = predict(world, kid.id)
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'"Careful," {parent.id} said. "If you rush {haggis.label}, you will get '
        f"messy and lose your proud status.""
    )


def turn(world: World, kid: Entity, parent: Entity, haggis: Haggis) -> None:
    kid.memes["lesson"] += 1
    kid.memes["worry"] = 0
    world.say(
        f"{kid.id} paused, looked at {haggis.label}, and understood why {parent.id} "
        f"had warned {kid.pronoun('object')}."
    )
    world.say(
        f"Instead of grabbing it, {kid.id} asked for help and waited nicely."
    )


def ending(world: World, kid: Entity, haggis: Haggis, parent: Entity) -> None:
    kid.memes["status"] += 1
    world.say(
        f"In the end, {kid.id} was still a little {kid.type}, but now {kid.id} "
        f"knew that real status came from being patient and safe."
    )
    world.say(
        f"{parent.id} smiled, and the {haggis.label} stayed tidy for later."
    )


SETTINGS = {
    "barn": Setting(place="the barn", detail="the straw was warm, and the animals were quiet."),
    "kitchen": Setting(place="the kitchen", detail="the table was low, and a small plate waited nearby."),
    "garden": Setting(place="the garden", detail="the grass was soft, and the path was bright with morning light."),
}

HAGGIS = {
    "haggis": Haggis(
        id="haggis",
        label="haggis",
        phrase="the haggis on the plate",
        smell="a rich, smoky smell",
        tempting=True,
    ),
    "sharing_bowl": Haggis(
        id="sharing_bowl",
        label="a sharing bowl of haggis",
        phrase="the sharing bowl of haggis",
        smell="a warm, savory smell",
        tempting=True,
    ),
}

CREATURES = {
    "fox": Creature(type="fox", name="Finn", trait="curious", status_goal="status", status_label="looked grown-up"),
    "dog": Creature(type="dog", name="Dot", trait="proud", status_goal="status", status_label="looked important"),
    "rabbit": Creature(type="rabbit", name="Ruby", trait="careful", status_goal="status", status_label="looked wise"),
}

GROWNUPS = ["Mum", "Dad", "Auntie", "Uncle"]


@dataclass
class StoryParams:
    place: str
    creature: str
    haggis: str
    grownup: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "haggis": [
        ("What is haggis?", "Haggis is a savory food dish made from oats and seasonings, and in stories it can be a special treat."),
    ],
    "status": [
        ("What does status mean?", "Status means how important, respected, or impressive someone seems to others."),
    ],
    "suspense": [
        ("What is suspense in a story?", "Suspense is the feeling that something important or surprising might happen next."),
    ],
    "lesson": [
        ("What is a lesson learned?", "A lesson learned is a good idea someone understands after something happens."),
    ],
}
KNOWLEDGE_ORDER = ["haggis", "status", "suspense", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    h = f["haggis"]
    return [
        f'Write an Animal Story about a little {kid.type} who wants more status after seeing {h.label}.',
        f"Tell a suspenseful story where {kid.id} gets tempted by {h.phrase} and learns a lesson about acting safely.",
        f'Write a short story for children that includes the words "haggis" and "status" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    parent = f["parent"]
    h = f["haggis"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {kid.id}, a little {kid.type} who wanted more status.",
        ),
        QAItem(
            question=f"What made {kid.id} feel suspense?",
            answer=f"The smell and sight of {h.label} made {kid.id} wonder what would happen next.",
        ),
        QAItem(
            question=f"What did {parent.id} warn {kid.id} about?",
            answer=f"{parent.id} warned {kid.id} that rushing toward {h.label} would make {kid.id} messy and would not be a smart way to gain status.",
        ),
        QAItem(
            question=f"What lesson did {kid.id} learn?",
            answer=f"{kid.id} learned that real status comes from being patient, safe, and respectful, not from grabbing the treat first.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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


def tell(setting: Setting, creature: Creature, haggis: Haggis, grownup: str) -> World:
    world = World(setting)
    kid = world.add(Entity(id=creature.name, kind="character", type=creature.type))
    parent = world.add(Entity(id=grownup, kind="character", type="adult"))
    treat = world.add(Entity(id=haggis.id, label=haggis.label, phrase=haggis.phrase))
    kid.memes["status"] = 1.0
    set_scene(world, kid, setting)
    raise_status(world, kid)
    world.para()
    tempt(world, kid, haggis)
    warn(world, parent, kid, haggis)
    spill(world, kid, haggis)
    world.para()
    turn(world, kid, parent, haggis)
    ending(world, kid, haggis, parent)
    world.facts.update(kid=kid, parent=parent, haggis=haggis, treat=treat)
    return world


def explain_rejection(place: str, haggis: Haggis) -> str:
    return f"(No story: {haggis.label} at {place} would not create a strong enough suspenseful turn.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.haggis:
        if not status_at_risk("status", HAGGIS[args.haggis]):
            raise StoryError(explain_rejection(args.place, HAGGIS[args.haggis]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.haggis is None or c[1] == args.haggis)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, haggis = rng.choice(sorted(combos))
    creature = args.creature or rng.choice(sorted(CREATURES))
    grownup = args.grownup or rng.choice(GROWNUPS)
    return StoryParams(place=place, creature=creature, haggis=haggis, grownup=grownup)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CREATURES[params.creature], HAGGIS[params.haggis], params.grownup)
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
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


ASP_RULES = r"""
status_at_risk(P,H) :- haggis(H), tempting(H).
suspense(K) :- kid(K), status_at_risk(status, H), haggis(H).
lesson_learned(K) :- kid(K), learned(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for hid, h in HAGGIS.items():
        lines.append(asp.fact("haggis", hid))
        if h.tempting:
            lines.append(asp.fact("tempting", hid))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("kid", c.name))
        lines.append(asp.fact("creature_type", c.name, c.type))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show status_at_risk/2."))
    return sorted(set(asp.atoms(model, "status_at_risk")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), {( "status", h.id) for h in HAGGIS.values() if status_at_risk("status", h)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} facts).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story-style haggis/status suspense world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--haggis", choices=HAGGIS)
    ap.add_argument("--grownup", choices=GROWNUPS)
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


CURATED = [
    StoryParams(place="barn", creature="fox", haggis="haggis", grownup="Mum"),
    StoryParams(place="kitchen", creature="rabbit", haggis="sharing_bowl", grownup="Dad"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show status_at_risk/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show status_at_risk/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.creature}: haggis in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
