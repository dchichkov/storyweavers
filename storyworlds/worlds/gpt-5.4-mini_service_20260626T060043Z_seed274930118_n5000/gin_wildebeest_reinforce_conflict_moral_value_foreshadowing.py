#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child, a zoo path, a wobbly rail, and
a careful fix. The seed words are woven into the prose: gin, wildebeest,
reinforce.

The world model keeps track of:
- physical meters: wobble, steadiness, helpfulness, worry, joy
- emotional memes: patience, conflict, pride, relief, care

Narrative shape:
1) A quiet zoo visit and a little foreshadowing
2) A conflict about getting too close to the wildebeest
3) A moral turn: the family reinforces the rail and chooses the safe way
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
# Typed entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------

SETTINGS = {
    "zoo_path": Setting(place="the zoo path", affords={"watch_wildebeest", "reinforce_rail"}),
    "shade_bench": Setting(place="the shaded bench", affords={"watch_wildebeest", "reinforce_rail"}),
}

ACTIVITIES = {
    "watch_wildebeest": Activity(
        id="watch_wildebeest",
        verb="watch the wildebeest",
        gerund="watching the wildebeest",
        rush="hurry closer to the rail",
        risk="too-close",
        keyword="wildebeest",
        tags={"wildebeest", "animal", "zoo"},
    ),
    "reinforce_rail": Activity(
        id="reinforce_rail",
        verb="reinforce the rail",
        gerund="reinforcing the rail",
        rush="grab the loose slat",
        risk="wobbly",
        keyword="reinforce",
        tags={"reinforce", "fix", "safety"},
    ),
}

GEAR = [
    Gear(
        id="brace",
        label="a wooden brace",
        prep="fetch a wooden brace and fit it under the rail",
        tail="carefully wedged the brace into place",
        guards={"wobbly"},
    ),
    Gear(
        id="rope",
        label="a strong rope tie",
        prep="loop a strong rope tie around the post",
        tail="tied the rope snugly around the post",
        guards={"wobbly"},
    ),
]

NAMES = ["Gin", "Mina", "Toby", "Ella", "Nico", "Ruby"]
PARENT_TYPES = ["mother", "father"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def needs_reinforcement(activity: Activity) -> bool:
    return activity.id == "watch_wildebeest"


def choose_gear(activity: Activity) -> Optional[Gear]:
    if activity.id != "watch_wildebeest":
        return None
    return GEAR[0]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            if needs_reinforcement(act) and choose_gear(act):
                combos.append((place, act_id, choose_gear(act).id))
    return combos


def explain_rejection() -> str:
    return "No story: this world only makes sense when the wildebeest visit creates a wobbly rail that can be reinforced."


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(zoo_path).
setting(shade_bench).

affords(zoo_path, watch_wildebeest).
affords(zoo_path, reinforce_rail).
affords(shade_bench, watch_wildebeest).
affords(shade_bench, reinforce_rail).

activity(watch_wildebeest).
activity(reinforce_rail).

gear(brace).
gear(rope).
guards(brace, wobbly).
guards(rope, wobbly).

needs_fix(A) :- activity(A), A = watch_wildebeest.
has_fix(A) :- needs_fix(A), gear(G), guards(G, wobbly).

valid(Place, A) :- affords(Place, A), needs_fix(A), has_fix(A).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for guard in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, guard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, a) for p, a, _ in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def build_story(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    rail = world.add(Entity(
        id="rail",
        type="thing",
        label="rail",
        phrase="the little wooden rail",
        meters={"wobble": 1.0, "steadiness": 0.2},
        memes={"worry": 1.0},
        caretaker=parent.id,
    ))

    act = ACTIVITIES[params.activity]
    gear = choose_gear(act)

    # Act 1: quiet life and foreshadowing
    world.say(
        f"{hero.id} and {parent.pronoun('possessive')} {parent.type} went to {world.setting.place} in the late morning."
    )
    world.say(
        f"They had come to watch the wildebeest, and the nearest rail gave a tiny creak that made {parent.pronoun()} glance over."
    )
    world.say(
        f"{hero.id} thought the wildebeest looked funny in the tall grass, with their shaggy heads and busy legs."
    )

    # Act 2: conflict
    world.para()
    hero.memes["want_close"] = 1.0
    hero.memes["conflict"] = 1.0
    world.say(
        f"When one young wildebeest trotted closer, {hero.id} wanted to {act.verb} right away."
    )
    world.say(
        f"{hero.id} started to {act.rush}, but {parent.pronoun('possessive')} {parent.type} held up a hand and said the rail was still {act.risk}."
    )
    world.say(
        f'"Wait," {parent.pronoun()} said, "we need to {act.verb} safely, and that means we should {act.id.replace("_", " ")} the right way first."'
    )
    world.say(
        f"{hero.id} frowned and crossed {hero.pronoun('possessive')} arms, because waiting felt longer than the zoo path itself."
    )

    # Act 3: moral turn and repair
    world.para()
    if gear is None:
        raise StoryError(explain_rejection())
    world.say(
        f"Then {parent.pronoun('possessive')} {parent.type} said, "
        f'"Let’s {gear.prep}; a stronger rail helps everyone."'
    )
    rail.meters["wobble"] = 0.0
    rail.meters["steadiness"] = 1.0
    rail.memes["worry"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.memes["patience"] = 1.0
    hero.memes["care"] = 1.0
    world.say(
        f"{hero.id} helped by holding the brace while {parent.pronoun('possessive')} {parent.type} {gear.tail}."
    )
    world.say(
        f"After that, the rail felt steady, and {hero.id} could {act.verb} without leaning too far."
    )
    world.say(
        f"The wildebeest kept grazing in the sun, and {hero.id} smiled at the calm, safe view."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        rail=rail,
        gear=gear,
        activity=act,
        setting=world.setting,
    )
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
    act = f["activity"]
    return [
        f'Write a slice-of-life story for a young child about {hero.id}, a zoo visit, and a rail that needs to be reinforced.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} near the wildebeest, but a parent chooses safety first.",
        f'Write a short child-facing story that includes the words "gin", "wildebeest", and "reinforce" in a natural way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    act = f["activity"]
    rail = f["rail"]
    gear = f["gear"]

    return [
        QAItem(
            question=f"Why did {parent.id} stop {hero.id} from getting too close to the wildebeest?",
            answer=f"{parent.id} stopped {hero.id} because the rail was wobbly, and the wildebeest were close enough that safety mattered.",
        ),
        QAItem(
            question=f"What did {hero.id} and {parent.id} do to make the rail safer?",
            answer=f"They used {gear.label} to reinforce the rail, which made it steadier.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after helping with the repair?",
            answer=f"{hero.id} felt calmer and prouder after helping reinforce the rail and waiting safely.",
        ),
        QAItem(
            question=f"What small clue foreshadowed the problem at the zoo?",
            answer=f"The rail gave a tiny creak before the conflict, which hinted that it needed reinforcement.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the rail was steady, the conflict was gone, and {hero.id} could watch the wildebeest safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wildebeest?",
            answer="A wildebeest is a large wild animal that lives in herds and likes to graze on grass.",
        ),
        QAItem(
            question="What does it mean to reinforce something?",
            answer="To reinforce something means to make it stronger or steadier so it can hold up better.",
        ),
        QAItem(
            question="What is a rail for?",
            answer="A rail helps keep people in a safe place by giving them something steady to stand behind or hold onto.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about a zoo visit and a reinforced rail.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    combos = valid_combos()
    combos = [c for c in combos
              if args.place is None or c[0] == args.place
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError(explain_rejection())
    place, activity, _ = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or ("girl" if name in {"Gin", "Ella", "Ruby"} else "boy")
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(f"{len(combos)} valid combos:")
        for p, a in combos:
            print(f"  {p}  {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(place="zoo_path", activity="watch_wildebeest", name="Gin", gender="girl", parent="mother")),
            generate(StoryParams(place="shade_bench", activity="watch_wildebeest", name="Mina", gender="girl", parent="father")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
