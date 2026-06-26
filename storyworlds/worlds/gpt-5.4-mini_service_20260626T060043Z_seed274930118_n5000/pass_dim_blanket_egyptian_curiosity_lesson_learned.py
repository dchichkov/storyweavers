#!/usr/bin/env python3
"""
storyworlds/worlds/pass_dim_blanket_egyptian_curiosity_lesson_learned.py
=========================================================================

A pirate-tale story world about a curious child on a ship, a dim pass, a
blanket, and an Egyptian treasure lesson that ends in reconciliation.

The simulated premise:
- A young sailor is aboard a small pirate ship near a dim sea pass.
- The sailor is curious about an Egyptian-looking blanket wrapped around a map.
- The captain warns that the blanket protects a fragile chart from spray and sand.
- Curiosity leads the sailor to peek anyway, causing trouble.
- A lesson is learned, and the pair reconcile.

This file follows the Storyworld contract with a world model, reasonableness
gates, inline ASP rules, and CLI support for story, QA, trace, JSON, and verify.
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
    worn_by: Optional[str] = None
    wrapped_in: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "sand", "scratched", "dirty"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "lesson", "reconciliation", "joy", "regret"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate", "sailor", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dim pass"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_mess_blanket(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD and actor.meters["sand"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.wrapped_in != actor.id:
                continue
            if item.protective:
                continue
            sig = ("mess_blanket", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += actor.meters["wet"]
            item.meters["sand"] += actor.meters["sand"]
            item.meters["dirty"] += 1
            out.append(f"The {item.label} got damp and gritty.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        if actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["regret"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    _r_mess_blanket,
    _r_conflict,
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"damaged": prize.meters["dirty"] >= THRESHOLD or prize.meters["wet"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("The chosen place cannot host that pirate business.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"Little {hero.type} {hero.id} sailed like a tiny sparrow on a pirate ship, "
        f"always peeking at every rope, crate, and shadow."
    )


def loves_blanket(world: World, hero: Entity, blanket: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} loved the old Egyptian blanket because it was stitched with gold thread "
        f"and smelled like faraway sand."
    )
    blanket.wrapped_in = hero.id


def shows_place(world: World, hero: Entity) -> None:
    world.say(
        f"One dusk, the ship crept into {world.setting.place}, where the water was dark as ink "
        f"and the rocks stood like sleepy sharks."
    )


def wants_peek(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, even though everyone knew the pass was too dim "
        f"for careless hands."
    )


def warns(world: World, captain: Entity, hero: Entity, blanket: Entity, activity: Activity) -> bool:
    predicted = predict_damage(world, hero, activity, blanket.id)
    if not predicted["damaged"]:
        return False
    captain.memes["worry"] += 1
    world.say(
        f'"Steady now," {captain.id} said. "That blanket guards the Egyptian chart. '
        f"If you stir the spray in {world.setting.place}, it'll get ruined.""
    )
    world.facts["predicted_damage"] = True
    return True


def ignores(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But {hero.id}'s nose was too busy sniffing the mystery, and {hero.id} tried to "
        f"{activity.rush}."
    )


def trouble(world: World, captain: Entity, hero: Entity) -> None:
    hero.memes["worry"] += 1
    hero.memes["regret"] += 1
    world.say(
        f"The captain caught the sleeve just in time, and {hero.id} froze with a sheepish face."
    )


def lesson(world: World, captain: Entity, hero: Entity, blanket: Entity) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"Then {captain.id} unfolded the blanket and showed how the dry middle kept the chart safe. "
        f"{hero.id} learned that a curious pirate still had to protect what kept the crew on course."
    )


def reconcile(world: World, captain: Entity, hero: Entity, blanket: Entity) -> None:
    hero.memes["reconciliation"] += 1
    captain.memes["reconciliation"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} tucked the blanket back around the chart, and {captain.id} smiled. "
        f"They made up, shoulder to shoulder, while the ship glided on and the dim pass opened ahead."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Milo", hero_type: str = "boy",
         parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id="Captain", kind="character", type=parent_type, label="captain"))
    blanket = world.add(Entity(
        id="blanket",
        type="blanket",
        label="blanket",
        phrase="an Egyptian blanket with a sun stitch",
        owner=hero.id,
        caretaker=captain.id,
        wrapped_in=hero.id,
        region=prize_cfg.region,
    ))
    world.facts.update(hero=hero, captain=captain, blanket=blanket, activity=activity, prize_cfg=prize_cfg)

    intro(world, hero)
    loves_blanket(world, hero, blanket)
    shows_place(world, hero)

    world.para()
    wants_peek(world, hero, activity)
    warns(world, captain, hero, blanket, activity)
    ignores(world, hero, activity)
    trouble(world, captain, hero)

    world.para()
    lesson(world, captain, hero, blanket)
    reconcile(world, captain, hero, blanket)

    world.facts.update(resolved=True)
    return world


SETTING = Setting(place="the dim pass", affords={"peek", "spray"})
ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek inside the blanket",
        gerund="peeking inside the blanket",
        rush="reach under the blanket",
        mess="sand",
        soil="sandy and damp",
        zone={"torso"},
        keyword="blanket",
        tags={"blanket", "egyptian", "curiosity"},
    ),
    "spray": Activity(
        id="spray",
        verb="lean over the rail to watch the spray",
        gerund="watching the spray",
        rush="lean over the rail",
        mess="wet",
        soil="wet and salty",
        zone={"torso"},
        keyword="pass-dim",
        tags={"pass-dim", "curiosity"},
    ),
}
PRIZES = {
    "blanket": Prize(
        label="blanket",
        phrase="an Egyptian blanket",
        type="blanket",
        region="torso",
    )
}
GEAR = [
    Gear(
        id="wrap",
        label="a dry wrap",
        covers={"torso"},
        guards={"wet", "sand"},
        prep="wrap the chart in a dry wrap",
        tail="kept the chart tucked safe in a dry wrap",
    )
]
NAMES = ["Milo", "Nina", "Pip", "Tessa", "Jory"]
TRAITS = ["curious", "brave", "sly", "bright"]


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
    for place, setting in {"pass": SETTING}.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if is_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, captain, act = f["hero"], f["captain"], f["activity"]
    return [
        'Write a pirate tale for a child about curiosity, a dim pass, and a blanket.',
        f"Tell a short story where {hero.id} wants to {act.verb} but {captain.id} warns about an Egyptian blanket.",
        "Write a story that ends with a lesson learned and a reconciliation on a ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, act, blanket = f["hero"], f["captain"], f["activity"], f["blanket"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the dim pass?",
            answer=f"{hero.id} wanted to {act.verb}, because curiosity kept tugging at {hero.id} like a little fishhook.",
        ),
        QAItem(
            question=f"Why did {captain.id} worry about the Egyptian blanket?",
            answer=f"{captain.id} worried because the blanket protected the chart, and the spray and sand in the dim pass could make it dirty and damp.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The child learned to protect the blanket, and the captain and child made up in the end.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {captain.id}?",
            answer=f"They reached reconciliation, with {hero.id} helping tuck the blanket safely around the chart while the ship moved on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blanket for?",
            answer="A blanket helps keep someone warm, or it can wrap and protect something delicate.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is wanting to know more about something and to look closely at it.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is when someone understands a better way to act after making a mistake.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a disagreement so people feel friendly again.",
        ),
        QAItem(
            question="What makes a pass dim?",
            answer="A dim pass has little light, so it feels shadowy and hard to see through clearly.",
        ),
        QAItem(
            question="What does Egyptian mean here?",
            answer="Egyptian means the blanket has a style inspired by Egypt, like a faraway treasure from old stories.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.wrapped_in:
            bits.append(f"wrapped_in={e.wrapped_in}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
damages(A,P) :- at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid_story(Place,A,P) :- affords(Place,A), at_risk(A,P), not damages(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "pass"))
    lines.append(asp.fact("affords", "pass", "peek"))
    lines.append(asp.fact("affords", "pass", "spray"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not make the {prize.label} meaningfully at risk "
        f"on {prize.region}, or there is no fair protective fix. The pirate lesson needs a real danger.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale: curiosity, a dim pass, a blanket, and reconciliation.")
    ap.add_argument("--place", choices=["pass"])
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (is_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = valid_combos()
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        place="pass",
        activity=activity,
        prize=prize,
        name=name,
        gender=gender,
        parent="captain",
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [StoryParams(place="pass", activity="peek", prize="blanket", name="Milo", gender="boy", parent="captain", trait="curious")]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
