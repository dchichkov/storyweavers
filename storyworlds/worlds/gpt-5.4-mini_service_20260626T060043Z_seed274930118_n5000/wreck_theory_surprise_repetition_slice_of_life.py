#!/usr/bin/env python3
"""
storyworlds/worlds/wreck_theory_surprise_repetition_slice_of_life.py
=====================================================================

A small slice-of-life story world about a child, a careful theory, a repeated
habit, and a surprising little wreck.

Seed-inspired premise:
- A child keeps testing a gentle theory about how to keep a favorite thing safe.
- Repetition makes the theory feel true.
- A surprise knocks it off course.
- The ending should show a quieter, sturdier routine.

The world is intentionally tiny and domestic: a table, a few objects, one helper,
and one small mishap that changes the day's plan.
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
    kind: str = "thing"           # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    repeat_line: str
    surprise_line: str
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.surprise: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.surprise = self.surprise
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wreck(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("shake", 0.0) < THRESHOLD and actor.meters.get("mess", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            if item.protective := False:  # pragma: no cover - deliberate assignment-free placeholder avoided
                pass
        for item in world.entities.values():
            if item.owner != actor.id:
                continue
            if item.region not in world.zone:
                continue
            if item.meters.get("safe", 0.0) >= THRESHOLD:
                continue
            sig = ("wreck", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wrecked"] = 1.0
            item.memes["sad"] = item.memes.get("sad", 0.0) + 1.0
            out.append(f"The careful little setup got wrecked.")
    return out


def _r_workaround(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("wrecked", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("fix", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["calm"] = carer.memes.get("calm", 0.0) + 1.0
        out.append(f"That meant a small cleanup for {carer.label}.")
    return out


CAUSAL_RULES = [Rule("wreck", _r_wreck), Rule("cleanup", _r_workaround)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                lines.extend(out)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen table", indoor=True, affords={"stack", "lineup"}),
    "hall": Setting(place="the hallway bench", indoor=True, affords={"stack", "lineup"}),
    "porch": Setting(place="the porch step", indoor=False, affords={"stack", "lineup"}),
}

ACTIVITIES = {
    "stack": Activity(
        id="stack",
        verb="stack the little pieces",
        gerund="stacking the little pieces",
        repeat_line="Again and again, the tower looked just right.",
        surprise_line="Then a surprise breeze made everything wobble.",
        mess="shake",
        soil="wobbly and broken",
        zone={"table"},
        keyword="stack",
        tags={"repeat", "surprise"},
    ),
    "lineup": Activity(
        id="lineup",
        verb="line up the toys",
        gerund="lining up the toys",
        repeat_line="Each careful row made the table feel neat.",
        surprise_line="Then one fast bump sent the front toy sliding.",
        mess="bump",
        soil="scattered",
        zone={"table"},
        keyword="lineup",
        tags={"repeat", "surprise"},
    ),
}

PRIZES = {
    "tower": Prize(label="tower", phrase="a tiny block tower", type="tower", region="table"),
    "train": Prize(label="train", phrase="a little toy train", type="train", region="table"),
    "cups": Prize(label="cups", phrase="three small cups", type="cups", region="table", plural=True),
}

FIXES = [
    Fix(
        id="tray",
        label="a tray",
        prep="move everything onto a tray first",
        tail="moved the little pieces onto a tray",
        protects={"shake", "bump"},
        covers={"table"},
    ),
    Fix(
        id="mat",
        label="a rubber mat",
        prep="put down a rubber mat first",
        tail="set the toys on a rubber mat",
        protects={"shake", "bump"},
        covers={"table"},
    ),
]

GIRL_NAMES = ["Maya", "Nina", "Lena", "Ivy", "Ruth", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Eli", "Noah", "Leo"]
TRAITS = ["careful", "patient", "curious", "quiet", "cheerful"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if activity.mess in fx.protects and prize.region in fx.covers:
            return fx
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: repetition, surprise, and a tiny wreck."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr) or select_fix(act, pr) is None:
            raise StoryError("No reasonable story: that setup would not get wrecked in a way a small fix can address.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("No reasonable story: that prize does not fit the chosen child in this world.")

    combos = [
        (place, act_id, prize_id)
        for place, setting in SETTINGS.items()
        for act_id in setting.affords
        for prize_id, prize in PRIZES.items()
        if (args.place is None or place == args.place)
        and (args.activity is None or act_id == args.activity)
        and (args.prize is None or prize_id == args.prize)
        and prize_at_risk(ACTIVITIES[act_id], prize)
        and select_fix(ACTIVITIES[act_id], prize) is not None
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["focus"] = actor.memes.get("focus", 0.0) + 1.0
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id, caretaker=helper.id, region=prize_cfg.region, plural=prize_cfg.plural))
    world.facts.update(child=child, helper=helper, prize=prize, activity=activity, setting=setting)

    world.say(f"{child.id} was a little {trait} {gender} who liked the quiet order of {setting.place}.")
    world.say(f"{child.id} had a theory: if the pieces were placed just so, nothing would get wrecked.")
    world.say(f"{child.id} kept testing that theory by {activity.gerund}.")
    world.say(activity.repeat_line)

    world.para()
    world.say(f"One day at {setting.place}, {child.id} and {helper.label} sat down again.")
    world.say(f"{child.id} wanted to {activity.verb}, and {helper.label} let the routine begin.")
    world.say(activity.surprise_line)
    world.surprise = activity.surprise_line
    child.meters[activity.mess] = child.meters.get(activity.mess, 0.0) + 1.0
    _do_activity(world, child, activity, narrate=True)

    world.para()
    if prize.meters.get("wrecked", 0.0) >= THRESHOLD:
        world.say(f"{child.id} stared at the {prize.label} and went quiet for a moment.")
        world.say(f"{helper.label.capitalize()} did not scold. {helper.label.capitalize()} just said it was all right to try a smaller fix.")
        fx = select_fix(activity, prize)
        if fx:
            helper_obj = world.add(Entity(id=fx.id, type="thing", label=fx.label, owner=child.id, caretaker=helper.id))
            helper_obj.meters["safe"] = 1.0
            world.say(f"They chose {fx.label} and decided to {fx.prep}.")
            world.say(f"That way, {child.id} could keep playing without another wreck.")
            world.say(f"They {fx.tail}, and the next careful try stayed neat.")
            child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
            child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
            helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1.0
    else:
        world.say(f"Nothing got wrecked after all, and the room stayed cozy.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, act, prize = f["child"], f["helper"], f["activity"], f["prize"]
    return [
        f'Write a gentle slice-of-life story for a young child about a "{act.keyword}" theory, a surprise, and a small fix.',
        f"Tell a story where {child.id} keeps {act.gerund} and then learns what happens when a tiny surprise ruins {prize.phrase}.",
        f"Write a short story with the words 'theory', 'surprise', and 'repetition' about {child.id} and {helper.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, act, prize = f["child"], f["helper"], f["activity"], f["prize"]
    trait = next((t for t in child.traits if t != "little"), "careful")
    return [
        QAItem(
            question=f"What was {child.id}'s theory about the repeated {act.keyword} routine?",
            answer=f"{child.id}'s theory was that if the pieces were placed carefully again and again, the little setup would stay safe and not get wrecked.",
        ),
        QAItem(
            question=f"What surprised {child.id} during the story?",
            answer=f"A surprise {act.surprise_line.lower()} It changed the tidy routine and made the setup go wrong.",
        ),
        QAItem(
            question=f"What did {helper.label} do after the {prize.label} got wrecked?",
            answer=f"{helper.label.capitalize()} stayed calm, helped choose a smaller fix, and showed {child.id} how to keep playing without another wreck.",
        ),
        QAItem(
            question=f"How did {child.id} act in the story?",
            answer=f"{child.id} was a little {trait} {child.pronoun('subject')} kept trying the same careful routine and learned from the surprise instead of giving up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a theory?", answer="A theory is a guess about how something works, usually made by watching what happens over and over."),
        QAItem(question="What is repetition?", answer="Repetition means doing something again and again."),
        QAItem(question="What is a surprise?", answer="A surprise is something you do not expect to happen."),
        QAItem(question="What does wrecked mean?", answer="If something is wrecked, it is broken or messed up so it does not work or look right anymore."),
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="kitchen", activity="stack", prize="tower", name="Nina", gender="girl", helper="mother", trait="careful"),
    StoryParams(place="hall", activity="lineup", prize="train", name="Owen", gender="boy", helper="father", trait="patient"),
    StoryParams(place="kitchen", activity="stack", prize="cups", name="Maya", gender="girl", helper="father", trait="curious"),
]


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), splashes(A, R), worn_on(P, R).
has_fix(A, P) :- prize_at_risk(A, P), activity(A), prize(P), mess_of(A, M), fix(F), protects(F, M), covers(F, R), worn_on(P, R).
valid_story(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.protects):
            lines.append(asp.fact("protects", fx.id, m))
        for r in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(
        (place, act_id, prize_id)
        for place, setting in SETTINGS.items()
        for act_id in setting.affords
        for prize_id, prize in PRIZES.items()
        if prize_at_risk(ACTIVITIES[act_id], prize) and select_fix(ACTIVITIES[act_id], prize) is not None
    )
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_and_generate(args: argparse.Namespace, seed: int) -> StorySample:
    rng = random.Random(seed)
    params = resolve_params(args, rng)
    params.seed = seed
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.helper, params.trait)
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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:")
        for place, act, prize in stories:
            print(f"  {place:8} {act:8} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                sample = resolve_and_generate(args, base_seed + i)
            except StoryError as err:
                print(err)
                return
            i += 1
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
