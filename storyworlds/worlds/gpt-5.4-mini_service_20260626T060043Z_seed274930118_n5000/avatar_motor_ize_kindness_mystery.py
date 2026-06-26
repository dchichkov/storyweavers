#!/usr/bin/env python3
"""
storyworlds/worlds/avatar_motor_ize_kindness_mystery.py
=======================================================

A small mystery-flavored story world about an avatar that wants to be
motor-ized, with kindness as the turning point.

The seed idea is simple:
- A child loves a homemade avatar.
- The avatar needs to move on its own.
- Something about the build feels strange and uncertain.
- A kind helper spots the problem and offers the safe fix.
- The ending proves the change in motion and feeling.

This script follows the shared Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- one simulated world driving prose
- prompts, story Q&A, and world Q&A
- inline ASP rules plus a Python reasonableness gate
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters or {})
        self.memes = dict(self.memes or {})

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
    place: str = "the workshop"
    indoor: bool = True
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
    weather: str = ""
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("jolted", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if not item.protective and item.region in world.zone and not world.covered(actor, item.region):
                sig = ("bump", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["scratched"] = item.meters.get("scratched", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got scratched.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("scratched", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That made {carer.label} worry.")
    return out


CAUSAL_RULES = [
    ("bump", _r_bump),
    ("worry", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("scratched", 0.0) >= THRESHOLD),
        "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("The setting does not support that activity.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "careful")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved making things move.")


def loves_avatar(world: World, hero: Entity, avatar: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {avatar.label} and watched it as if it kept a secret.")


def mystery_setup(world: World, avatar: Entity) -> None:
    world.say("But the little avatar kept stopping with a faint click, and that felt like a mystery.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, even if nobody knew yet what was wrong.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"If we rush it, your {prize.label} might get scratched," {parent.label} said softly. '
        f'"Let’s solve the mystery first."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["impulse"] = hero.memes.get("impulse", 0.0) + 1
    world.say(f"{hero.id} frowned and tried to {activity.rush}.")


def kind_help(world: World, helper: Entity, hero: Entity, prize: Entity, gear_def: Gear) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(
        f"{helper.id} knelt beside the table and pointed to the answer: "
        f'"We can use {gear_def.label} so it stays safe."'
    )


def accept(world: World, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear, helper: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded, and together they {gear_def.tail}. "
        f"After that, the {prize.label} could {activity.verb} without getting scratched, "
        f"and the mystery was solved by a kind hand instead of a loud fuss."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "gentle"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    helper = world.add(Entity(id="Helper", kind="character", type="woman", label="the kind helper"))

    avatar = world.add(Entity(
        id="avatar",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_avatar(world, hero, avatar)
    mystery_setup(world, avatar)
    world.para()
    wants(world, hero, activity)
    warn(world, parent, hero, activity, avatar)
    defies(world, hero, activity)
    kind_help(world, helper, hero, avatar, GEAR[0])
    world.para()
    gear_def = compromise(world, parent, hero, activity, avatar)
    if gear_def is None:
        gear_def = GEAR[0]
    accept(world, hero, activity, avatar, gear_def, helper)
    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper,
        prize=avatar,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=True,
    )
    return world


SETTINGS = {
    "workshop": Setting(place="the workshop", indoor=True, affords={"motorize"}),
    "studio": Setting(place="the little studio", indoor=True, affords={"motorize"}),
}

ACTIVITIES = {
    "motorize": Activity(
        id="motorize",
        verb="motor-ize the avatar",
        gerund="motor-izing the avatar",
        rush="jiggle the wires until it ran too hard",
        mess="jolted",
        soil="scratched and shaky",
        zone={"torso", "legs"},
        weather="",
        keyword="avatar",
        tags={"avatar", "motor-ize", "kindness", "mystery"},
    ),
}

PRIZES = {
    "avatar": Prize(
        label="avatar",
        phrase="a handmade avatar with a painted face",
        type="avatar",
        region="torso",
    )
}

GEAR = [
    Gear(
        id="pads",
        label="soft foam pads",
        covers={"torso"},
        guards={"jolted"},
        prep="place soft foam pads around the moving parts",
        tail="slid the soft foam pads into place",
    )
]

NAMES = ["Mina", "June", "Ivy", "Noah", "Eli", "Luna"]
TRAITS = ["curious", "gentle", "patient", "careful", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, act = f["hero"], f["prize_cfg"], f["activity"]
    return [
        'Write a short mystery story for a young child about an avatar that needs to move.',
        f"Tell a gentle mystery where {hero.id} wants to {act.verb} and a kind helper keeps {prize.label} safe.",
        'Write a story that includes kindness, a clue, and a happy ending with an avatar that can move.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, helper, prize, act = f["hero"], f["parent"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the parent worry about the {prize.label}?",
            answer=f"The parent worried that if they rushed, the {prize.label} could get {act.soil}.",
        ),
        QAItem(
            question=f"Who helped solve the mystery kindly?",
            answer=f"{helper.label} helped by suggesting {GEAR[0].label}.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The {prize.label} could {act.verb} safely, and the mystery was solved with kindness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avatar?",
            answer="An avatar is a picture, figure, or character that stands in for a person in a story or game.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, caring, and being gentle with someone else.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to understand or solve.",
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="workshop", prize="avatar", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="studio", prize="avatar", name="Noah", gender="boy", parent="father", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: the setting and prize do not make a meaningful mystery here. "
        f"The avatar must actually be at risk from {activity.gerund}, and there must be a safe helper gear.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,P) :- affords(Place,motorize), prize_at_risk(motorize,P), has_fix(motorize,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    ap = argparse.ArgumentParser(description="Mystery story world: avatar, motor-ize, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
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
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{parent.label} found a safe answer: {gear_def.label}.")
    return gear_def


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES["motorize"], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, prize in triples:
            print(f"  {place:10} {prize}")
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
            header = f"### {p.name}: {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
