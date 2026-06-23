#!/usr/bin/env python3
"""
storyworlds/worlds/harrow_gyp_sentry_surprise_nursery_rhyme.py
==============================================================

A tiny nursery-rhyme story world about a garden, a surprise, and three named
things: Harrow, Gyp, and Sentry.

The seed tale behind this world is a small child-friendly rhyme: a little crew
prepares a nursery garden, loses something small, then finds a surprising gift
hidden where nobody expected it. The simulation below turns that premise into
typed entities with physical meters and emotional memes, a simple causal engine,
a reasonableness gate, and a story-driven renderer.

The required words are part of the world vocabulary:
- harrow
- gyp
- sentry

The style aims for nursery rhyme: short beats, repeated sounds, concrete images,
and a surprise ending that changes the world state.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    plural: bool = False
    owner: str = ""
    caretaker: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    spoil: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    tags: set[str] = field(default_factory=set)


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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id]

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["work"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.label in {"apron", "boots"}:
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] += 1
            actor.memes["oops"] += 1
            out.append(f"{actor.id}'s {item.label} got dusty and dull.")
    return out


def _r_surprise(world: World) -> list[str]:
    if world.facts.get("surprise_seen"):
        return []
    if world.facts.get("surprise_ready") and world.facts.get("surprise_found"):
        world.facts["surprise_seen"] = True
        giver = world.get(world.facts["giver"])
        child_fact = world.facts["child"]
        child = child_fact if isinstance(child_fact, Entity) else world.get(child_fact)
        giver.memes["glee"] += 1
        child.memes["glee"] += 1
        return ["__surprise__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("mess", "physical", _r_mess),
    Rule("surprise", "social", _r_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if s != "__surprise__")
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.id in {"apron", "boots"}


def select_surprise(activity: Activity, prize: Prize) -> Optional[Surprise]:
    for s in SURPRISES.values():
        if prize.region in s.tags and activity.id in s.tags:
            return s
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if not prize_at_risk(act, prize):
                    continue
                for sur_id, sur in SURPRISES.items():
                    if prize.region in sur.tags and act_id in sur.tags:
                        combos.append((place, act_id, prize_id, sur_id))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    activity: str = ""
    prize: str = ""
    surprise: str = ""
    child: str = "Mabel"
    child_gender: str = "girl"
    helper: str = "Ned"
    helper_gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


SETTINGS = {
    "nursery": Setting(place="the nursery garden", indoor=False, affords={"harrow", "gyp"}),
    "greenhouse": Setting(place="the little greenhouse", indoor=True, affords={"gyp"}),
    "yard": Setting(place="the yard by the shed", indoor=False, affords={"harrow", "gyp"}),
}

ACTIVITIES = {
    "harrow": Activity(
        id="harrow",
        verb="rake the rows",
        gerund="raking the rows",
        rush="run to rake",
        mess="dust",
        spoil="dusty",
        zone={"hands", "shoes"},
        tags={"harrow", "garden"},
    ),
    "gyp": Activity(
        id="gyp",
        verb="mix the pots",
        gerund="mixing the pots",
        rush="hurry to stir",
        mess="mud",
        spoil="muddy",
        zone={"hands", "apron"},
        tags={"gyp", "garden"},
    ),
}

PRIZES = {
    "apron": Prize("apron", "a striped apron", "striped apron", "torso", tags={"apron"}),
    "boots": Prize("boots", "little boots", "little boots", "feet", plural=True, tags={"boots"}),
    "cap": Prize("cap", "a paper cap", "paper cap", "head", tags={"cap"}),
}

SURPRISES = {
    "seedcake": Surprise(
        "seedcake",
        "seed cake",
        "a seed cake",
        "a seed cake tucked in the potting bench",
        tags={"torso", "harrow", "gyp"},
    ),
    "starbell": Surprise(
        "starbell",
        "star bell",
        "a little star bell",
        "a little star bell tied to the sentry post",
        tags={"feet", "harrow", "gyp"},
    ),
}

GIRL_NAMES = ["Mabel", "Nell", "Poppy", "Lucy", "May", "Ruby"]
BOY_NAMES = ["Ned", "Ben", "Toby", "Jack", "Owen", "Will"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story about {f["child"].id} and {f["helper"].id} in {f["place"]} that uses the words harrow, gyp, and sentry, and includes a surprise.',
        f"Tell a short rhyming garden story where {f['child'].id} wants to {f['activity'].verb}, but a hidden surprise near the sentry post changes the day.",
        f"Write a child-friendly rhyme about a small garden task, a dusty mishap, and a surprise treasure at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    act = f["activity"]
    prize = f["prize"]
    sur = f["surprise"]
    return [
        QAItem(
            question=f"Who is the story about in the nursery garden?",
            answer=f"It is about {child.id} and {helper.id}, who were busy in {world.setting.place}. The little rhyme follows them as they work and then find a surprise.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the harrow?",
            answer=f"{child.id} wanted to {act.verb}. That made the day feel busy and bouncy, but it also meant dust could drift onto nearby things.",
        ),
        QAItem(
            question=f"What got a little dusty when the work began?",
            answer=f"{prize.phrase} got a little dusty. The work was close enough to the prize to make the story turn from tidy to messy for a moment.",
        ),
    ] + (
        [
            QAItem(
                question=f"Why was the ending a surprise?",
                answer=f"The surprise was {sur.reveal}. It was hidden in a place the children did not expect, so the story ended with a happy gasp.",
            ),
            QAItem(
                question=f"How did {child.id} feel when the surprise was found?",
                answer=f"{child.id} felt glad and bright-eyed. The surprise changed the day from ordinary garden work into a little celebration.",
            ),
        ]
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | set(world.facts["surprise"].tags)
    out: list[QAItem] = []
    if "harrow" in tags:
        out.append(QAItem(
            question="What is a harrow?",
            answer="A harrow is a garden tool used to rake and smooth soil so rows can look neat.",
        ))
    if "gyp" in tags:
        out.append(QAItem(
            question="What is gyp in this story?",
            answer="Here, gyp is a playful garden task about mixing pots and soil. It makes the little garden feel busy and lively.",
        ))
    if "sentry" in tags:
        out.append(QAItem(
            question="What is a sentry?",
            answer="A sentry is a guard who keeps watch. In a nursery rhyme story, it can mean a little post or watcher standing by the garden path.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, prize: Prize, surprise: Surprise, child_name: str, child_gender: str, helper_name: str, helper_gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label="harrow"))
    hidden = world.add(Entity(id="hidden", kind="thing", type="thing", label=surprise.label))

    prize_ent = world.add(Entity(id="prize", kind="thing", type="thing", label=prize.label, plural=prize.plural))
    prize_ent.owner = helper.id
    tool.owner = helper.id
    hidden.owner = helper.id

    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["parent"] = parent
    world.facts["activity"] = activity
    world.facts["prize"] = prize
    world.facts["surprise"] = surprise
    world.facts["place"] = setting

    world.facts["surprise_ready"] = True
    world.facts["surprise_found"] = False
    world.facts["surprise_seen"] = False
    world.facts["giver"] = helper.id

    child.memes["curious"] += 1
    helper.memes["steady"] += 1

    world.say(
        f"In {setting.place}, under a bright little sky, {child.id} and {helper.id} were as busy as bees. "
        f"{child.id} took the harrow and began to {activity.verb}."
    )
    world.say(
        f"{helper.id} sang a hum and a rhyme, while {prize.phrase} sat by the path, neat and shy."
    )

    world.para()
    world.say(
        f"But the work went swish and swash, and dust did hop. {child.id}'s hands grew gray, and the {prize.label} got a little dusty."
    )
    child.meters["work"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then came a tap on the sentry post, a tiny tinkly sound. {helper.id} reached under a flower pot and found something round."
    )
    world.facts["surprise_found"] = True
    selected = select_surprise(activity, prize)
    if selected:
        hidden.label = selected.label
        world.facts["surprise"] = selected
    propagate(world, narrate=True)
    if world.facts.get("surprise_seen"):
        world.say(
            f"With a twinkle and a chuckle, the surprise came into view: {selected.reveal if selected else surprise.reveal}."
        )
        world.say(
            f"{child.id} clapped, and {helper.id} laughed; the nursery garden felt warm and new."
        )

    world.facts["tool"] = tool
    world.facts["hidden"] = hidden
    return world


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.owner:
            parts.append(f"owner={e.owner}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", activity="harrow", prize="apron", surprise="seedcake", child="Mabel", child_gender="girl", helper="Ned", helper_gender="boy", parent="mother"),
    StoryParams(place="yard", activity="gyp", prize="boots", surprise="starbell", child="Nell", child_gender="girl", helper="Toby", helper_gender="boy", parent="father"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.id} does not reasonably reach {prize.label} in this small garden world.)"


def valid_story_combo(place: str, activity: str, prize: str, surprise: str) -> bool:
    if place not in SETTINGS or activity not in ACTIVITIES or prize not in PRIZES or surprise not in SURPRISES:
        return False
    act = ACTIVITIES[activity]
    pr = PRIZES[prize]
    sur = SURPRISES[surprise]
    return prize_at_risk(act, pr) and pr.region in sur.tags and activity in sur.tags


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
valid(Place,A,P,S) :- setting(Place), activity(A), prize(P), surprise(S),
                      prize_at_risk(A,P), sur_zone(S,R), worn_on(P,R), sur_act(S,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        for t in sorted(s.tags):
            if t in {"harrow", "gyp"}:
                lines.append(asp.fact("sur_act", sid, t))
            else:
                lines.append(asp.fact("sur_zone", sid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme story world with harrow, gyp, and sentry.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.surprise is None or c[3] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize, surprise = rng.choice(list(combos))
    child_gender = "girl" if rng.random() < 0.5 else "boy"
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        surprise=surprise,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.activity not in ACTIVITIES or params.prize not in PRIZES or params.surprise not in SURPRISES:
        raise StoryError("(Invalid params.)")
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        SURPRISES[params.surprise],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
        params.parent,
    )
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        base = generate(CURATED[0])
        ok = True
        try:
            _ = base.story
        except Exception:
            ok = False
        if not ok:
            print("Smoke test failed.")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params.seed = base_seed + i
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
