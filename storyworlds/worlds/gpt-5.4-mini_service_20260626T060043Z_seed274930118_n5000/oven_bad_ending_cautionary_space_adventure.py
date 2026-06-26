#!/usr/bin/env python3
"""
Standalone storyworld: oven_bad_ending_cautionary_space_adventure

A small cautionary space-adventure domain about a curious child, a spaceship
galley oven, and a warning that should have been heeded.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    safe: bool = False
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
    place: str = "the starship kitchen"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    risk: str
    keyword: str = "oven"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    kind: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str
    safe_with: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.heat_level = 0.0
        self.power_level = 1.0
        self.oven_on = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.heat_level = self.heat_level
        c.power_level = self.power_level
        c.oven_on = self.oven_on
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_overheat(world: World) -> list[str]:
    out: list[str] = []
    if not world.oven_on:
        return out
    world.heat_level += 1.0
    if world.heat_level < 2.0:
        return out
    for e in world.entities.values():
        if e.kind != "thing" or not e.worn_by:
            continue
        if e.safe:
            continue
        sig = ("burn", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["burned"] = e.meters.get("burned", 0.0) + 1.0
        out.append(f"The heat reached {e.label}, and it began to scorch.")
    return out


def _r_alarm(world: World) -> list[str]:
    if world.heat_level < 2.0:
        return []
    sig = ("alarm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    return ["A sharp alarm began to wail through the ship."]


CAUSAL_RULES = [
    Rule("overheat", _r_overheat),
    Rule("alarm", _r_alarm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "burned": prize.meters.get("burned", 0.0) >= THRESHOLD,
        "alarm": sim.heat_level >= 2.0,
    }


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.kind in {"ship", "paper", "food", "cloth"} and activity.risk == prize.kind


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.kind in gear.safe_with:
            return gear
    return None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.oven_on = True
    world.power_level -= 0.1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1.0
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved every shiny button on the ship.")


def setup(world: World, hero: Entity, prize: Entity, activity: Activity, parent: Entity) -> None:
    world.say(
        f"{hero.id} loved {activity.gerund}; {activity.keyword} consoles and warm vents made the whole kitchen feel like an adventure."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} had bought {hero.pronoun('object')} {prize.phrase} for the trip."
    )
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} proudly, even in the ship's narrow hall.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["burned"]:
        return False
    world.facts["predicted_burned"] = True
    world.say(
        f'"Don\'t {activity.verb}," {parent.label} said. "The oven is too hot, and your {prize.label} could get {activity.soil}."'
    )
    return True


def ignores(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1.0
    world.say(f"{hero.id} frowned and decided the warning sounded boring.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


def tragedy(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    if prize.meters.get("burned", 0.0) >= THRESHOLD:
        world.say(
            f"The oven stayed on too long, and {hero.pronoun('possessive')} {prize.label} got {activity.soil}."
        )
        world.say(
            f"Before anyone could help, the alarm was still screaming, and the trip turned into a sad mess."
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, safe=True, owner=hero.id))
    gear.worn_by = hero.id
    if predict(world, hero, activity, prize.id)["burned"]:
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.label} pointed to {gear_def.label} and said, "{gear_def.prep} first, then you can watch the oven safely."'
    )
    return gear_def


def ending_bad(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{hero.id} did not listen. The {activity.keyword} glow grew brighter, the {prize.label} was ruined, and {parent.label} had to shut the oven down."
    )
    world.say(
        f"At the end, the ship was quiet, {hero.id} felt tiny, and the lesson was simple: some warnings are there to keep everyone safe."
    )


SETTING = Setting(place="the starship kitchen", indoors=True, affords={"oven"})
ACTIVITIES = {
    "oven": Activity(
        id="oven",
        verb="open the oven",
        gerund="watching the oven glow",
        rush="run closer to the oven",
        mess="heat",
        soil="black and ruined",
        risk="cloth",
        keyword="oven",
        tags={"oven", "heat", "ship"},
    )
}
PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a bright red captain's cape",
        type="cape",
        kind="cloth",
        plural=False,
    ),
    "banner": Prize(
        label="banner",
        phrase="a small mission banner",
        type="banner",
        kind="cloth",
        plural=False,
    ),
}
GEAR = [
    Gear(
        id="gloves",
        label="heat gloves",
        guards={"heat"},
        prep="put on the heat gloves",
        tail="slid on the heat gloves and stood back from the oven",
        safe_with={"cloth"},
    ),
    Gear(
        id="visor",
        label="a clear visor",
        guards={"heat"},
        prep="snap on the clear visor",
        tail="snapped on the clear visor and watched from a safe spot",
        safe_with={"cloth"},
    ),
]

GIRL_NAMES = ["Mina", "Lia", "Nora", "Tess"]
BOY_NAMES = ["Finn", "Oren", "Milo", "Jace"]
TRAITS = ["curious", "bold", "restless", "tiny"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"ship": SETTING}.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short cautionary space adventure for a child who wants to {act.verb} near an oven.',
        f"Tell a story where {hero.id} ignores {parent.label}'s warning and the {prize.phrase} gets ruined.",
        f'Write a tiny spaceship story that includes the word "{act.keyword}" and ends with a lesson about safety.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a curious little {hero.type}, and {parent.label} trying to keep the ship safe.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the oven?",
            answer=f"{hero.id} wanted to {act.verb}, even though the oven was too hot and dangerous.",
        ),
        QAItem(
            question=f"What got ruined in the end?",
            answer=f"{hero.pronoun('possessive').capitalize()} {prize.label} got {act.soil} in the hot oven mess.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id}?",
            answer=f"{parent.label} warned {hero.id} because the oven could make {prize.phrase} burn and turn the trip into trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an oven for?",
            answer="An oven is a hot box used for cooking food or heating things up.",
        ),
        QAItem(
            question="Why is a hot oven dangerous?",
            answer="A hot oven can burn skin or things that are too close to it, so people should be careful around it.",
        ),
        QAItem(
            question="What should you do when an adult gives a safety warning?",
            answer="You should listen carefully and follow the warning, because it is meant to keep everyone safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.safe:
            bits.append("safe=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  heat_level={world.heat_level}")
    lines.append(f"  oven_on={world.oven_on}")
    lines.append(f"  fired rules={sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), risk_of(A, cloth), kind_of(P, cloth).
compatible(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, heat), safe_with(G, cloth).
valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), compatible(_, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "ship"))
    lines.append(asp.fact("affords", "ship", "oven"))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, act.risk))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("kind_of", pid, prize.kind))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
        for s in sorted(gear.safe_with):
            lines.append(asp.fact("safe_with", gear.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gate")
    if a - b:
        print(" only in clingo:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary space adventure about an oven.")
    ap.add_argument("--place", choices=["ship"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("No valid combination matches the given options.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize_id = rng.choice(combos)
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize_id, name, gender, parent, trait)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prize = world.add(Entity(
        id="prize",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    act = ACTIVITIES[params.activity]

    world.say(f"{hero.id} was a little {params.trait} {params.gender} aboard the starship.")
    world.say(f"{hero.id} loved {act.gerund}, because the ship felt like a tiny glowing moon.")
    world.say(f"{parent.label} had given {hero.id} {prize.phrase} for the journey.")
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} with pride.")

    world.para()
    world.say("Inside the kitchen module, the oven hummed like a warm little engine.")
    world.say(f"{hero.id} wanted to {act.verb}, but {parent.label} raised a hand.")
    warn(world, parent, hero, act, prize)
    ignores(world, hero, act)
    world.oven_on = True
    propagate(world)

    world.para()
    ending_bad(world, hero, parent, act, prize)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=act, prize_cfg=PRIZES[params.prize])
    return world


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
    StoryParams(place="ship", activity="oven", prize="cape", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="ship", activity="oven", prize="banner", name="Finn", gender="boy", parent="father", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
