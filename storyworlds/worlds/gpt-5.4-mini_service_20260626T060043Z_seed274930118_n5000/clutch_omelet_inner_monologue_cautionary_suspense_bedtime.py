#!/usr/bin/env python3
"""
storyworlds/worlds/clutch_omelet_inner_monologue_cautionary_suspense_bedtime.py
===============================================================================

A small bedtime-style storyworld about a child, a clutch of eggs, and the
suspense of making an omelet without making a mess.

Premise:
- A child wants a warm omelet before sleep.
- The eggs are carried in a clutch.
- The stove is hot, the pan is slippery, and the child worries about cracking
  the shells too hard or dropping the pan.

Narrative instruments:
- Inner Monologue: the child thinks through each step before acting.
- Cautionary: a caregiver warns about hot metal, shell bits, and spills.
- Suspense: the story pauses on a near-mistake, then resolves with careful help.

The world model tracks:
- physical meters: heat, spill, crack, clean, finished
- emotional memes: worry, courage, relief, pride

This script follows the storyworld contract and includes an inline ASP twin
for the reasonableness gate.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def ensure(self, key: str) -> None:
        if key not in self.meters:
            self.meters[key] = 0.0
        if key not in self.memes:
            self.memes[key] = 0.0


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    bedtime: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    caution: str
    risk: str
    keyword: str
    mess: str = "spill"
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    type: str
    carried: bool = True
    plural: bool = False
    contents: str = "eggs"


@dataclass
class Tool:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


def _default_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _default_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def predict_spill(world: World, actor: Entity, act: Activity, vessel_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), act, narrate=False)
    vessel = sim.entities[vessel_id]
    return {
        "spilled": _default_meter(vessel, "spill") >= THRESHOLD,
        "heat": sum(_default_meter(e, "heat") for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    if act.id not in world.setting.affords:
        raise StoryError(f"(No story: this place does not support {act.id}.)")
    actor.ensure("spill")
    actor.ensure("courage")
    actor.meters["spill"] = actor.meters.get("spill", 0.0) + 1.0
    actor.memes["courage"] = actor.memes.get("courage", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} carefully began to {act.verb}.")
    if actor.meters["spill"] >= THRESHOLD:
        world.trace.append("activity_started")


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _default_meter(actor, "spill") < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind == "thing" and item.carried_by == actor.id and item.label in {"clutch", "bowl"}:
                sig = ("spill", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["spill"] = item.meters.get("spill", 0.0) + 1.0
                out.append(f"A little spill touched the {item.label}.")
    return out


def _r_heat_warning(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _default_meter(actor, "spill") < THRESHOLD:
            continue
        if _default_meme(actor, "worry") < THRESHOLD:
            continue
        sig = ("warn", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("A warning came gently, like a whisper before sleep.")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_heat_warning,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def inner_thought(hero: Entity, act: Activity) -> str:
    return (
        f"{hero.pronoun().capitalize()} thought, "
        f'"Take it slow. Crack the eggs one by one. Don\'t let the shell bits fall in."'
    )


def setup_world(setting: Setting, activity: Activity, vessel_cfg: Vessel, hero_name: str,
                hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Caregiver", kind="character", type=parent_type, label="the caregiver"))
    clutch = world.add(Entity(
        id="clutch", kind="thing", type="clutch", label="clutch",
        phrase="a little clutch of eggs", owner=hero.id, carried_by=hero.id, plural=True,
    ))
    pan = world.add(Entity(
        id="pan", kind="thing", type="pan", label="pan",
        phrase="a small pan", owner=hero.id
    ))
    vessel = world.add(Entity(
        id=vessel_cfg.id, kind="thing", type=vessel_cfg.type, label=vessel_cfg.label,
        phrase=vessel_cfg.phrase, owner=hero.id, carried_by=hero.id, plural=vessel_cfg.plural,
    ))
    hero.memes["worry"] = 1.0
    hero.memes["hope"] = 1.0
    world.facts.update(hero=hero, parent=parent, clutch=clutch, pan=pan, vessel=vessel,
                       activity=activity, setting=setting)
    return world


def tell(world: World, activity: Activity) -> World:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    vessel = world.facts["vessel"]

    world.say(f"At {world.setting.place}, {hero.id} held the {world.facts['clutch'].label} close.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {activity.verb} before bedtime.")
    world.say(inner_thought(hero, activity))
    world.say(f"But the night felt very still, and the {activity.keyword} on the stove looked hot enough to hiss.")

    world.para()
    world.say(f'"Easy now," said {parent.label}. "{activity.caution}."')
    world.say(f"{hero.id} listened and kept both hands steady.")
    _do_activity(world, hero, activity, narrate=False)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(f"{hero.id} wondered if the egg would crack cleanly or fall apart.")
    world.say("For a tiny moment, the spoon wobbled.")

    propagate(world, narrate=True)

    world.para()
    if hero.meters.get("spill", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} paused, breathed out, and tried again more carefully.")
    world.say(f"At last, the omelet turned soft and golden in the pan.")
    world.say(f"{hero.id} smiled, because the {vessel.label} stayed safe and the kitchen stayed tidy.")
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"make_omelet"}, bedtime=True),
    "cottage_kitchen": Setting(place="the little cottage kitchen", affords={"make_omelet"}, bedtime=True),
    "camp_kitchen": Setting(place="the camp kitchen", affords={"make_omelet"}, bedtime=True),
}

ACTIVITIES = {
    "make_omelet": Activity(
        id="make_omelet",
        verb="make an omelet",
        gerund="making an omelet",
        caution="Keep your fingers away from the hot pan",
        risk="the eggs might spill or the shell bits might sneak into the bowl",
        keyword="omelet",
        mess="spill",
        tags={"eggs", "pan", "hot", "sleep"},
    ),
}

VESSELS = {
    "clutch": Vessel(
        id="clutch",
        label="clutch",
        phrase="a little clutch of eggs",
        type="clutch",
        carried=True,
        plural=True,
        contents="eggs",
    ),
}

TOOLS = [
    Tool(
        id="wooden_spoon",
        label="a wooden spoon",
        guards={"spill"},
        covers={"hand"},
        prep="use a wooden spoon for the first stir",
        tail="used the wooden spoon for the first stir",
    ),
    Tool(
        id="small_lid",
        label="a small lid",
        guards={"spill", "splash"},
        covers={"pan"},
        prep="cover the pan with a small lid",
        tail="covered the pan with the small lid",
    ),
]


GIRL_NAMES = ["Mina", "Lily", "Tara", "Nora", "Ivy", "Luna"]
BOY_NAMES = ["Ben", "Theo", "Owen", "Finn", "Milo", "Eli"]
TRAITS = ["careful", "sleepy", "brave", "gentle", "curious", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, activity) for place, s in SETTINGS.items() for activity in s.affords]


def reasonableness_gate(place: str, activity: str) -> None:
    if (place, activity) not in valid_combos():
        raise StoryError("(No story: this place and activity do not fit together.)")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a bedtime story about {hero.id} and a clutch of eggs that becomes an omelet.',
        f"Tell a suspenseful but gentle story where {hero.id} thinks carefully before making an omelet.",
        f'Write a child-friendly story with an inner monologue, a caution, and a cozy ending around the word "omelet".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    activity = f["activity"]
    vessel = f["vessel"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {place} before bedtime?",
            answer=f"{hero.id} wanted to {activity.verb}. The idea felt cozy, but it needed careful hands."
        ),
        QAItem(
            question=f"What did {parent.label} warn {hero.id} about?",
            answer=f"{parent.label.capitalize()} warned {hero.id} to keep fingers away from the hot pan and to move slowly."
        ),
        QAItem(
            question=f"What did {hero.id} carry that started the cooking?",
            answer=f"{hero.id} carried a {vessel.label} with eggs inside it. That was the start of the omelet."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end after the suspenseful moment?",
            answer=f"It ended with a soft, golden omelet, a tidy kitchen, and {hero.id} feeling proud and relieved."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an omelet?",
            answer="An omelet is a cooked egg dish that is usually soft and folded in a pan."
        ),
        QAItem(
            question="Why should children be careful around a hot pan?",
            answer="A hot pan can burn skin, so it is safer to keep fingers away and move slowly."
        ),
        QAItem(
            question="What is a clutch?",
            answer="A clutch is a small group held together, like a clutch of eggs or a clutch of chicks."
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing" and e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="make_omelet", name="Mina", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="cottage_kitchen", activity="make_omelet", name="Theo", gender="boy", parent="father", trait="patient"),
    StoryParams(place="camp_kitchen", activity="make_omelet", name="Lily", gender="girl", parent="mother", trait="sleepy"),
]


ASP_RULES = r"""
place_ok(P) :- setting(P).
activity_ok(A) :- activity(A).
valid_story(P, A) :- setting(P), affords(P, A).

#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime-style story world: a clutch of eggs, a cautious child, and an omelet."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "make_omelet"
    reasonableness_gate(place, activity)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    vessel = VESSELS["clutch"]
    world = setup_world(setting, activity, vessel, params.name, params.gender, params.parent)
    tell(world, activity)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible story combos:\n")
        for place, activity in valid_combos():
            print(f"  {place:18} {activity}")
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
