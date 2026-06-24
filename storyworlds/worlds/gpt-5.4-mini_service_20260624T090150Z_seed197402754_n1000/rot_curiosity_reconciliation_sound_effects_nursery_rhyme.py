#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about curiosity, a bad smell from rot, and a
warm reconciliation after a noisy mishap.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    part: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type
        if not self.phrase:
            self.phrase = self.label

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label


@dataclass
class Setting:
    place: str = "the orchard"
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
    sound: str
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    part: str
    plural: bool = False


@dataclass
class Helper:
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

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
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.facts = copy.deepcopy(self.facts)
        return c


ACTIVITIES = {
    "peeking": Activity(
        id="peeking",
        verb="peek in the jar",
        gerund="peeking in jars",
        rush="run to the shelf",
        mess="tippy",
        soil="tipped and toppled",
        zone={"table"},
        sound="clink-clink",
        keyword="peek",
    ),
    "stirring": Activity(
        id="stirring",
        verb="stir the pudding",
        gerund="stirring pudding",
        rush="dash to the bowl",
        mess="sticky",
        soil="sticky and smeared",
        zone={"mouth", "hands"},
        sound="plip-plop",
        keyword="stir",
    ),
    "sniffing": Activity(
        id="sniffing",
        verb="sniff the basket",
        gerund="sniffing baskets",
        rush="tiptoe to the basket",
        mess="musty",
        soil="musty and rotten-smelling",
        zone={"nose", "hands"},
        sound="sniff-snuff",
        keyword="sniff",
    ),
}

PRIZES = {
    "apple": Prize(
        label="apple",
        phrase="a bright red apple",
        type="apple",
        part="hands",
    ),
    "bread": Prize(
        label="bread",
        phrase="a soft loaf of bread",
        type="bread",
        part="hands",
    ),
    "sock": Prize(
        label="sock",
        phrase="a little blue sock",
        type="sock",
        part="hands",
    ),
}

HELPERS = [
    Helper(
        label="a clean cloth",
        prep="wipe the mess with a clean cloth",
        tail="wiped the jar and set it straight",
        guards={"sticky", "musty"},
        covers={"hands"},
    ),
    Helper(
        label="a little basket lid",
        prep="close the basket with a little lid",
        tail="closed the basket and kept the air inside",
        guards={"musty"},
        covers={"nose", "hands"},
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Rose", "Nina", "Tia", "Lily"]
BOY_NAMES = ["Ben", "Finn", "Toby", "Eli", "Max", "Noah"]
TRAITS = ["curious", "cheerful", "gentle", "bright", "busy"]


def normalize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_").lower()


def sound_line(sound: str) -> str:
    return f"{sound}!"


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.part in activity.zone


def select_helper(activity: Activity, prize: Prize) -> Optional[Helper]:
    for helper in HELPERS:
        if activity.mess in helper.guards and prize.part in helper.covers:
            return helper
    return None


def predict_mess(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": bool(prize.meters.get("dirty", 0) >= THRESHOLD),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    if narrate:
        world.say(sound_line(activity.sound))
    for item in world.entities.values():
        if item.worn_by == actor.id and item.part in activity.zone:
            sig = ("mess", item.id, activity.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            item.meters[activity.mess] = item.meters.get(activity.mess, 0) + 1
            if narrate:
                world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got {activity.soil}.")
            if item.caretaker:
                carer = world.get(item.caretaker)
                carer.memes["worry"] = carer.memes.get("worry", 0) + 1
                if narrate:
                    world.say(f"That made {carer.label} sigh, oh dear.")


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.meters.keys()), 'one')} child who loved to look and learn.")


def setup_story(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} loved to {activity.verb}, and {hero.pronoun('possessive')} {parent.label} had brought {hero.pronoun('object')} {prize.phrase}."
    )
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {prize.pronoun('object') if hasattr(prize, 'pronoun') else 'it'} all through the day.")


def story_intro(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(f"On a bright day at {world.setting.place}, {hero.id} and {parent.label} went together.")
    world.say(f"{hero.id} saw {prize.phrase} and wanted to {activity.verb}.")


def warning(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["rot_warning"] = True
    world.say(
        f"\"Oh no, dear, that could get your {prize.label} {activity.soil},\" said {parent.label}."
    )
    world.say(f"{hero.id} listened, but curiosity still went {sound_line('tap-tap')}.")
    return True


def defy_and_return(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(f"{hero.id} tripped along and tried to {activity.rush}, {sound_line('tip-tap')}.")


def reconciliation(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Helper]:
    helper = select_helper(activity, prize)
    if helper is None:
        return None
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f"But first they chose {helper.label}, which could keep the trouble away.")
        return helper
    return None


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, helper: Helper) -> None:
    world.say(f"{parent.label} smiled a smile that was soft and slow.")
    world.say(f"\"Let us {helper.prep}, then you may {activity.verb},\" said {parent.label}.")
    world.say(f"{hero.id} nodded, and the two made peace in a merry little row.")
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0) + 1
    world.say(
        f"They {helper.tail}, and soon {hero.id} was {activity.gerund}, while {prize.label} stayed clean and neat."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, parent_label: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if hero_name in GIRL_NAMES else "boy"))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label=parent_label))
    prize = world.add(Entity(
        id=prize_cfg.type,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        part=prize_cfg.part,
    ))
    introduce(world, hero)
    world.para()
    story_intro(world, hero, parent, prize, activity)
    setup_story(world, hero, parent, prize, activity)
    warning(world, parent, hero, activity, prize)
    defy_and_return(world, hero, activity)
    world.para()
    helper = reconciliation(world, parent, hero, activity, prize)
    if helper:
        accept(world, parent, hero, activity, prize, helper)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, helper=helper, setting=setting)
    return world


SETTINGS = {
    "orchard": Setting(place="the orchard", affords={"peeking", "sniffing"}),
    "kitchen": Setting(place="the kitchen", affords={"stirring", "sniffing"}),
    "pantry": Setting(place="the pantry", affords={"sniffing", "peeking"}),
}

CURATED = [
    ("orchard", "sniffing", "apple", "Mia"),
    ("kitchen", "stirring", "bread", "Ben"),
    ("pantry", "sniffing", "sock", "Luna"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about curiosity, rot, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, setting in SETTINGS.items():
        for a in setting.affords:
            act = ACTIVITIES[a]
            for pr in PRIZES:
                if prize_at_risk(act, PRIZES[pr]) and select_helper(act, PRIZES[pr]):
                    out.append((p, a, pr))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme-like story about a curious child named {f["hero"].id} at {f["setting"].place}.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} but a parent worries about {f['prize'].phrase}.",
        f"Write a story with soft sound effects and a happy reconciliation after a mishap with rot.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because {prize.label} could get {activity.soil}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {parent.label}?",
            answer=f"They chose a kind compromise, and the two made peace again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rot?",
            answer="Rot is what happens when food or other things go bad and start to smell unpleasant.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are little words like clink, plop, or tap that help you hear the action in your mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.part:
            bits.append(f"part={e.part}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), helper(H), guards(H,M), mess_of(A,M), covers(H,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    out = []
    for pid, s in SETTINGS.items():
        out.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            out.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        out.append(asp.fact("activity", aid))
        out.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            out.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        out.append(asp.fact("prize", pid))
        out.append(asp.fact("worn_on", pid, p.part))
    for h in HELPERS:
        out.append(asp.fact("helper", normalize_name(h.label)))
        for g in sorted(h.guards):
            out.append(asp.fact("guards", normalize_name(h.label), g))
        for c in sorted(h.covers):
            out.append(asp.fact("covers", normalize_name(h.label), c))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, "the parent")
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
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place, activity, prize in CURATED:
            params = StoryParams(place=place, activity=activity, prize=prize, name="Mia")
            samples.append(generate(params))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
