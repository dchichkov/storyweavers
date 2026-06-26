#!/usr/bin/env python3
"""
Folk-tale storyworld: additive blending with shortsleeves, dialogue, curiosity,
and teamwork.

A small village story about a child who wants to blend colors, a parent who
worries about a messy apron, and a shared fix that lets everyone work together.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "painted", "dirty", "mixed", "ready", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "curiosity", "trust", "tension", "teamwork", "defiance"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village paint shed"
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
    keyword: str
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


def add_meters(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def add_memes(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cottage": Setting(place="the little cottage kitchen", indoor=True, affords={"blend"}),
    "mill": Setting(place="the old mill room", indoor=True, affords={"blend"}),
}

ACTIVITIES = {
    "blend": Activity(
        id="blend",
        verb="blend the colors",
        gerund="blending colors",
        rush="reach for the bowls and stir too fast",
        mess="painted",
        soil="spattered with paint",
        zone={"torso", "arms", "hands"},
        keyword="blend",
        tags={"blend", "additive"},
    ),
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a clean shortsleeved shirt",
        type="shirt",
        region="torso",
    ),
    "smock": Prize(
        label="smock",
        phrase="a shortsleeved work smock",
        type="smock",
        region="torso",
    ),
    "apron": Prize(
        label="apron",
        phrase="a bright apron",
        type="apron",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="coverleeves",
        label="short sleeves rolled tight",
        covers={"arms"},
        guards={"painted"},
        prep="roll up the sleeves and tie on a light cover",
        tail="rolled up the sleeves and tied on a light cover",
    ),
    Gear(
        id="smock",
        label="an old smock",
        covers={"torso"},
        guards={"painted"},
        prep="put on an old smock first",
        tail="put on the old smock",
    ),
]

VILLAGE_NAMES = ["Mara", "Ivo", "Nia", "Toma", "Sera", "Pavel", "Lina", "Kato"]
PARENT_NAMES = ["Grandmother", "Grandfather", "Aunt", "Uncle"]
TRAITS = ["curious", "kind", "clever", "patient", "lively"]


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    apply: callable


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mixed", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            add_meters(item, "dirty", 1.0)
            add_meters(item, "painted", 1.0)
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got spattered with paint.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        add_meters(caretaker, "workload", 1.0)
        out.append(f"That would mean more washing for {caretaker.label}.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("trust", 0.0) >= THRESHOLD and actor.memes.get("curiosity", 0.0) >= THRESHOLD:
            sig = ("teamwork", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            add_memes(actor, "teamwork", 1.0)
            out.append(f"{actor.id} felt ready to work as a team.")
    return out


RULES = [
    Rule("soil", _r_soil),
    Rule("workload", _r_workload),
    Rule("teamwork", _r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {prize.label} is not at risk during {activity.gerund}, "
            f"so there is no honest problem to solve.)"
        )
    return (
        f"(No story: nothing in the gear catalog both covers the {prize.region} "
        f"and guards against {activity.mess}.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(VILLAGE_NAMES)


def activity_delight(activity: Activity) -> str:
    return "the colors swirled like ribbons in a festival bowl"


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} smelled of flour, ash, and old wood."


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in child.memes.get('traits', []) or ['curious'])} child "
        f"who loved asking how things became what they were."
    )


def want(world: World, child: Entity, activity: Activity) -> None:
    add_memes(child, "curiosity", 1.0)
    world.say(
        f"{child.id} wanted to {activity.verb}, because {activity_delight(activity)}."
    )


def warn(world: World, elder: Entity, child: Entity, activity: Activity, prize: Entity) -> bool:
    if not prize_at_risk(activity, prize):
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," '
        f"{elder.label} said."
    )
    return True


def answer(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f'"But what if we work together?" {child.id} asked. '
        f'"Then the colors can blend neatly," {elder.label} said.'
    )
    add_memes(child, "trust", 1.0)
    add_memes(elder, "trust", 1.0)


def prepare_gear(world: World, child: Entity, elder: Entity, gear: Gear) -> None:
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        owner=child.id,
        caretaker=elder.id,
    ))
    g.worn_by = child.id
    world.say(
        f"{elder.label} smiled and said, \"Let's {gear.prep}.\""
    )


def do_activity(world: World, child: Entity, activity: Activity) -> None:
    child.meters["mixed"] = child.meters.get("mixed", 0.0) + 1.0
    add_memes(child, "joy", 1.0)
    world.zone = set(activity.zone)
    propagate(world, narrate=False)
    world.say(
        f"{child.id} stirred gently, and the paints mixed into a bright new shade."
    )


def resolve(world: World, child: Entity, elder: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    add_memes(child, "teamwork", 1.0)
    add_memes(elder, "teamwork", 1.0)
    add_memes(child, "joy", 1.0)
    world.say(
        f"{child.id} and {elder.label} worked side by side, and {gear.tail}."
    )
    world.say(
        f"At last, the bowl held a fine blend, {prize.pronoun('possessive')} shirt stayed clean, "
        f"and the little room felt full of laughter."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, elder: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name, memes={"traits": [trait]}))
    caretaker = world.add(Entity(id=elder, kind="character", type="elder", label=elder))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=caretaker.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    prize.worn_by = child.id

    world.say(
        f"Long ago, in a little village, {child.id} wore {prize_cfg.phrase}."
    )
    world.say(setting_detail(setting))
    world.para()

    introduce(world, child)
    want(world, child, activity)
    warn(world, caretaker, child, activity, prize)
    answer(world, child, caretaker)
    prepare_gear(world, child, caretaker, GEAR[0])
    world.para()
    do_activity(world, child, activity)
    gear = GEAR[0]
    resolve(world, child, caretaker, prize, activity, gear)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        prize=prize,
        activity=activity,
        gear=gear,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, caretaker, activity, prize = f["child"], f["caretaker"], f["activity"], f["prize"]
    return [
        f'Write a short folk tale for a child who wants to {activity.verb} while wearing {prize.phrase}.',
        f'Create a gentle story with dialogue, curiosity, and teamwork about {child.id} and {caretaker.label} in {world.setting.place}.',
        f'Write a tale where a shortsleeved shirt stays clean because everyone chooses a careful way to {activity.verb}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, caretaker, activity, prize = f["child"], f["caretaker"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"What did {child.id} want to do in the village?",
            answer=f"{child.id} wanted to {activity.verb}, because the colors were calling to {child.id} like bright festival ribbons.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} worry about {prize.label}?",
            answer=f"{caretaker.label} worried because {prize.pronoun('possessive')} {prize.label} could get {activity.soil} if they were not careful.",
        ),
        QAItem(
            question=f"How did {child.id} and {caretaker.label} solve the problem?",
            answer=f"They chose to work together, used a light cover first, and kept the {prize.label} clean while the colors were mixed.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"The ending was happy: the blend came out fine, the {prize.label} stayed clean, and the room was full of laughter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does blend mean?",
            answer="To blend means to mix things together until they make one new result.",
        ),
        QAItem(
            question="What are short sleeves?",
            answer="Short sleeves are sleeves that end above the elbows, so they leave the arms more open.",
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because people can share jobs, solve problems together, and make hard tasks feel easier.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions and learn how things work.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
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
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def valid_names(gender: str, rng: random.Random) -> str:
    return rng.choice(VILLAGE_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    elder = args.elder or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.elder,
        params.trait,
    )
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale world: additive blending, shortsleeves, dialogue, curiosity, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=PARENT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams(place="cottage", activity="blend", prize="shirt", name="Mara", gender="girl", elder="Grandmother", trait="curious"),
    StoryParams(place="mill", activity="blend", prize="smock", name="Ivo", gender="boy", elder="Uncle", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:")
        for row in models:
            print(" ", row)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: blend at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
