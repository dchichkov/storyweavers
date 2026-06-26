#!/usr/bin/env python3
"""
imperial_mount_groom_lesson_learned_pirate_tale.py
===================================================

A small storyworld about an imperial groom, a proud mount, and a pirate-style
lesson learned.

Premise:
- A careful groom tends an imperial mount that must look fine for a parade.
- A piratey gust of trouble threatens to leave the mount dusty, splashed, or
  frightened.
- The groom learns that a better plan, a gentler hand, and the right tack can
  keep the mount calm and ready.

This world is intentionally tiny and classical: one concrete problem, one turn,
and one satisfying resolution image proving that something changed.
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
# Core model
# ---------------------------------------------------------------------------

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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for k in ("dusty", "wet", "tired", "clean", "ready", "safe", "quiet", "sparkle"):
            self.meters.setdefault(k, 0.0)
        for k in ("pride", "worry", "joy", "love", "lesson", "calm", "fear", "stubborn"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "lady"}
        male = {"boy", "man", "father", "groom", "king", "captain", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the imperial stable"
    affords: set[str] = field(default_factory=set)
    imperial: bool = True


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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "stable": Setting(place="the imperial stable", affords={"gallop", "bathe", "groom"}),
    "harbor": Setting(place="the harbor", affords={"sail", "gallop"}),
    "courtyard": Setting(place="the palace courtyard", affords={"gallop", "march"}),
}

ACTIVITIES = {
    "gallop": Activity(
        id="gallop",
        verb="gallop past the banners",
        gerund="galloping past the banners",
        rush="charge out under the flags",
        mess="dusty",
        soil="dusty and flustered",
        zone={"legs", "mane"},
        keyword="gallop",
        tags={"dust", "mount"},
    ),
    "bathe": Activity(
        id="bathe",
        verb="bathe the mount",
        gerund="bathing the mount",
        rush="dash to the water barrels",
        mess="wet",
        soil="wet and shining",
        zone={"legs", "mane", "body"},
        keyword="wash",
        tags={"wet", "mount"},
    ),
    "groom": Activity(
        id="groom",
        verb="brush the mount",
        gerund="brushing the mount",
        rush="reach for the brushes",
        mess="dusty",
        soil="dusty but neat",
        zone={"mane", "body"},
        keyword="groom",
        tags={"dust", "groom"},
    ),
    "march": Activity(
        id="march",
        verb="march in the parade",
        gerund="marching in the parade",
        rush="clatter into line",
        mess="dusty",
        soil="dusty and proud",
        zone={"legs", "body"},
        keyword="parade",
        tags={"imperial", "banner"},
    ),
    "sail": Activity(
        id="sail",
        verb="sail by the harbor ships",
        gerund="sailing by the harbor ships",
        rush="run to the docks",
        mess="wet",
        soil="wet and salty",
        zone={"legs", "body"},
        keyword="sail",
        tags={"sea", "pirate"},
    ),
}

PRIZES = {
    "coat": Prize(
        label="coat",
        phrase="a crisp imperial coat",
        type="coat",
        region="body",
    ),
    "saddlecloth": Prize(
        label="saddlecloth",
        phrase="a bright saddlecloth",
        type="saddlecloth",
        region="body",
        plural=False,
    ),
    "mane-ribbon": Prize(
        label="mane ribbon",
        phrase="a shiny mane ribbon",
        type="ribbon",
        region="mane",
    ),
}

GEAR = [
    Gear(
        id="brush",
        label="a soft brush",
        covers={"mane"},
        guards={"dusty"},
        prep="put the soft brush to work first",
        tail="took the soft brush and smoothed the mane",
    ),
    Gear(
        id="cloak",
        label="a waxed cloak",
        covers={"body"},
        guards={"wet"},
        prep="tie on a waxed cloak before the rain-splash work",
        tail="slipped the waxed cloak on and stayed dry",
    ),
    Gear(
        id="cover",
        label="a clean cover cloth",
        covers={"body"},
        guards={"dusty", "wet"},
        prep="lay a clean cover cloth over the tack",
        tail="laid down the clean cover cloth and kept the coat neat",
    ),
]

GROOM_NAMES = ["Nico", "Tarin", "Jory", "Pell", "Mira", "Sela"]
MOUNT_NAMES = ["Brine", "Comet", "Aurora", "Hush", "Marble", "Storm"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    groom_name: str
    mount_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
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
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict_mess(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": bool(prize.meters[activity.mess] >= THRESHOLD),
        "lesson": hero.memes["lesson"],
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    actor.memes["lesson"] += 0.25
    if narrate:
        world.say(f"{actor.id} did the {activity.gerund}.")


def narrative_opening(world: World, groom: Entity, mount: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"In the imperial stable, {groom.id} cared for {mount.id}, a brave mount with a kind eye."
    )
    world.say(
        f"{groom.id} loved {activity.gerund}, and {mount.id} wore {prize.phrase} for the court parade."
    )


def scene_setup(world: World, groom: Entity, mount: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"On a bright day, {groom.id} and {mount.id} waited near {world.setting.place}."
    )
    world.say(
        f"{groom.id} wanted to {activity.verb}, but {groom.pronoun('possessive')} work would not be easy if the {prize.label} got messy."
    )


def warn(world: World, groom: Entity, mount: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, mount, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_mess"] = activity.soil
    world.say(
        f'"If you do that, {mount.id} will get {activity.soil}," {groom.pronoun("possessive")} groom said. '
        f'"Then the parade will look sloppy."'
    )
    return True


def defy(world: World, mount: Entity, activity: Activity) -> None:
    mount.memes["stubborn"] += 1
    mount.memes["fear"] += 0.5
    world.say(f"{mount.id} snorted and tried to {activity.rush}.")


def turn_to_gear(world: World, groom: Entity, mount: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    world.say(
        f"{groom.id} took a breath, then chose a steadier plan: {gear.prep}."
    )
    return gear


def resolve(world: World, groom: Entity, mount: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    groom.memes["lesson"] += 1
    mount.memes["calm"] += 1
    mount.memes["fear"] = 0.0
    world.say(
        f"{mount.id} settled down while {groom.id} {gear.tail}."
    )
    world.say(
        f"At last, {mount.id} was {activity.gerund}, {prize.phrase} stayed neat, and the imperial banners fluttered with pride."
    )
    world.say(
        f"{groom.id} learned that a good captain of the stable uses patience first, not noise."
    )


def tell_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)

    groom = world.add(Entity(id=params.groom_name, kind="character", type="groom"))
    mount = world.add(Entity(id=params.mount_name, kind="character", type="horse"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=mount.id,
            caretaker=groom.id,
            region=prize_cfg.region,
        )
    )

    mount.worn_by = mount.id
    prize.worn_by = mount.id

    narrative_opening(world, groom, mount, prize, activity)
    world.para()
    scene_setup(world, groom, mount, prize, activity)
    warn(world, groom, mount, activity, prize)
    defy(world, mount, activity)
    world.para()
    gear = turn_to_gear(world, groom, mount, activity, prize)
    if gear:
        resolve(world, groom, mount, prize, activity, gear)

    world.facts.update(
        groom=groom,
        mount=mount,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        conflict=True,
        resolved=gear is not None,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    groom = f["groom"]
    mount = f["mount"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short pirate-tale-style story for a child about an imperial groom named {groom.id}, a mount named {mount.id}, and a lesson learned.',
        f"Tell a gentle story where {groom.id} wants to {act.verb} but worries that {mount.id}'s {prize.label} will get messy, and a better plan is found.",
        f'Write a story that includes the words "imperial", "mount", and "groom" and ends with a clear lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    groom = f["groom"]
    mount = f["mount"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    answers = [
        QAItem(
            question=f"Who is the story about in the imperial stable?",
            answer=f"It is about {groom.id}, the groom, and {mount.id}, the mount. {groom.id} takes care of {mount.id} and watches over the {prize.label}.",
        ),
        QAItem(
            question=f"What did {groom.id} want {mount.id} to do?",
            answer=f"{groom.id} wanted {mount.id} to {act.verb}. That is why the {prize.label} might have gotten messy.",
        ),
        QAItem(
            question=f"Why did the groom worry about the {prize.label}?",
            answer=f"Because if {mount.id} did the {act.gerund}, the {prize.label} could become {act.soil}. The groom did not want the parade to look sloppy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {groom.id} choosing a better plan, using {gear.label}, and learning that patience and care work better than rushing.",
        ),
    ]
    if gear:
        answers.append(
            QAItem(
                question=f"What helped keep the {prize.label} neat?",
                answer=f"{gear.label} helped, because it matched the trouble and covered the part of the mount that could get dirty.",
            )
        )
    return answers


WORLD_KNOWLEDGE = {
    "imperial": [
        QAItem(
            question="What does imperial usually mean?",
            answer="Imperial means it belongs to an empire, a king, an empress, or their court.",
        )
    ],
    "mount": [
        QAItem(
            question="What is a mount?",
            answer="A mount is an animal, often a horse, that someone rides or leads for travel or ceremony.",
        )
    ],
    "groom": [
        QAItem(
            question="What does a groom do?",
            answer="A groom cares for a horse or other animal by feeding it, brushing it, and keeping it ready.",
        )
    ],
    "dust": [
        QAItem(
            question="What is dust?",
            answer="Dust is tiny dry bits of dirt that can settle on clothes, hair, and tack.",
        )
    ],
    "wet": [
        QAItem(
            question="What happens when something gets wet?",
            answer="When something gets wet, water soaks into it or covers it, and it may feel cold or heavy.",
        )
    ],
    "pirate": [
        QAItem(
            question="Who is a pirate?",
            answer="A pirate is a sea robber or sea adventurer from old stories, often with a ship and a daring way of speaking.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("imperial")
    tags.add("mount")
    tags.add("groom")
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in ("imperial", "mount", "groom", "dust", "wet", "pirate"):
        if tag in tags and tag in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="stable", activity="groom", prize="mane-ribbon", groom_name="Nico", mount_name="Brine"),
    StoryParams(place="stable", activity="bathe", prize="coat", groom_name="Tarin", mount_name="Storm"),
    StoryParams(place="courtyard", activity="march", prize="coat", groom_name="Jory", mount_name="Aurora"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Imperial mount-groom pirate tale with a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--groom-name")
    ap.add_argument("--mount-name")
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
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError("No reasonable story: that activity would not honestly threaten that prize, or there is no fitting fix.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        groom_name=args.groom_name or rng.choice(GROOM_NAMES),
        mount_name=args.mount_name or rng.choice(MOUNT_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:\n")
        for row in vals:
            print("  ", row)
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
            header = f"### {p.groom_name} and {p.mount_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
