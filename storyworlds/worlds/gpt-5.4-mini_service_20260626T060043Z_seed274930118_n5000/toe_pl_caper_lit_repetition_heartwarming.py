#!/usr/bin/env python3
"""
storyworlds/worlds/toe_pl_caper_lit_repetition_heartwarming.py
==============================================================

A tiny heartwarming storyworld about a child's little caper to get the toe-pls
lit in time, with repetition used as a gentle narrative instrument.

Seed-image sketch:
---
A child wants to surprise someone they love with a row of toe-pls lit on the
porch. The first try goes wrong because the matches are missing and the dusk
feels too dark. The child keeps trying again and again, counting the toe-pls
one by one, until a helper brings a safe lantern and the whole porch glows.

The world is built around:
- a small, physical lightable object called a toe-pl
- a little caper to gather what is needed
- repetition in the narration and the state changes
- a heartwarming ending image where the lights stay lit and the surprise lands
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoor: bool
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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _light(world: World, actor: Entity, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if actor.memes.get("ready", 0.0) < THRESHOLD:
        return out
    if actor.meters.get("matches", 0.0) < THRESHOLD and actor.meters.get("lamp", 0.0) < THRESHOLD:
        return out
    for toe in world.entities.values():
        if toe.type != "toe-pl":
            continue
        if toe.meters.get("lit", 0.0) >= THRESHOLD:
            continue
        sig = ("light", toe.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        toe.meters["lit"] += 1
        out.append(f"One by one, the {toe.label} was lit.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _glow(world: World) -> list[str]:
    if sum(1 for e in world.entities.values() if e.type == "toe-pl" and e.meters.get("lit", 0.0) >= THRESHOLD) < 1:
        return []
    if ("glow",) in world.fired:
        return []
    world.fired.add(("glow",))
    world.entities["home"].meters["warmth"] = 1
    return ["The porch grew warm and golden."]


def _mend_mood(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return []
    sig = ("mend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    helper.memes["love"] = helper.memes.get("love", 0.0) + 1
    return ["The worry slipped away when the light stayed on."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_light, _glow, _mend_mood):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def act_at_risk(act: Activity, prize: Prize) -> bool:
    return prize.region in act.zone


def select_gear(act: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if act.mess in g.guards and prize.region in g.covers:
            return g
    return None


def predict(world: World, actor: Entity, act: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["ready"] = 1
    sim.get(actor.id).meters["matches"] = 1
    sim.get(actor.id).meters["lamp"] = 1
    _do_activity(sim, sim.get(actor.id), act, narrate=False)
    prize = sim.get(prize_id)
    return {"lit": prize.meters.get("lit", 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    if act.id not in world.setting.affords:
        return
    actor.memes["ready"] = actor.memes.get("ready", 0.0) + 1
    world.zone = set(act.zone)
    if act.id == "caper":
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        world.say(f"{actor.id} began the little caper with careful toes and a brave heart.")
    propagate(world, narrate=narrate)


SETTINGS = {
    "porch": Setting(place="the porch", outdoor=True, affords={"caper"}),
    "kitchen": Setting(place="the kitchen", outdoor=False, affords={"caper"}),
    "garden": Setting(place="the garden path", outdoor=True, affords={"caper"}),
}

ACTIVITIES = {
    "caper": Activity(
        id="caper",
        verb="light the toe-pls for the surprise",
        gerund="lighting the toe-pls",
        rush="hurry to find the last match",
        mess="smudged",
        soil="smudged and dim",
        zone={"hands"},
        keyword="caper",
        tags={"caper", "lit", "toe-pl"},
    )
}

PRIZES = {
    "toe_pl": Prize(
        label="toe-pls",
        phrase="a row of little toe-pls",
        type="toe-pl",
        region="hands",
        plural=True,
    )
}

GEAR = [
    Gear(
        id="lantern",
        label="a safe lantern",
        covers={"hands"},
        guards={"smudged"},
        prep="bring the safe lantern",
        tail="brought the safe lantern to the porch",
    ),
    Gear(
        id="tray",
        label="a bright tray",
        covers={"hands"},
        guards={"smudged"},
        prep="carry a bright tray instead",
        tail="carried a bright tray out",
    ),
]

CHILD_NAMES = ["Mina", "Jules", "Toby", "Lena", "Arlo", "Nia"]
HELPER_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if act_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming toe-pl caper with repetition and a lit ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, helper=helper)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, child_name: str, helper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="child", label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=helper_name))
    toe_names = ["first", "second", "third"]
    for i, nm in enumerate(toe_names, 1):
        world.add(Entity(id=f"toe{i}", type="toe-pl", label="toe-pl", plural=True, meters={"lit": 0}))
    world.add(Entity(id="home", type="home", label="home", meters={"warmth": 0}))
    child.memes["worry"] = 1
    world.say(f"{child_name} loved the toe-pls because they were little and bright.")
    world.say(f"{child_name} counted them the same sweet way every time: one toe-pl, two toe-pls, three toe-pls.")
    world.para()
    world.say(f"That evening, {child_name} wanted to {activity.verb} on {setting.place}.")
    world.say(f"But the {prize_cfg.label} were still dark, and the caper was not ready yet.")
    world.para()
    world.say(f"{child_name} went on the caper to {activity.rush}, again and again, because little lights like little patience.")
    _do_activity(world, child, activity, narrate=True)
    world.say(f"{helper_name} saw the trouble and smiled.")
    gear = select_gear(activity, prize_cfg)
    if gear:
        world.say(f'"How about I {gear.prep}?" {helper_name} asked.')
        child.meters["lamp"] = 1
        child.meters["matches"] = 1
        world.add(Entity(id="lantern", type="gear", label=gear.label, protective=True, meters={"lit": 0}))
        world.say(f"Together they {gear.tail}.")
    child.meters["ready"] = 1
    _do_activity(world, child, activity, narrate=True)
    if sum(1 for e in world.entities.values() if e.type == "toe-pl" and e.meters.get("lit", 0.0) >= THRESHOLD) < 3:
        for toe in [e for e in world.entities.values() if e.type == "toe-pl"]:
            toe.meters["lit"] = 1
            world.say(f"The next toe-pl was lit too, just like the last one.")
    propagate(world, narrate=True)
    world.say(f"In the end, the toe-pls stayed lit, and the porch looked like a tiny warm welcome.")
    world.facts.update(child=child, helper=helper, activity=activity, prize=prize_cfg, setting=setting, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming short story for a young child about a little caper to get the toe-pls lit.',
        f"Tell a gentle story where {f['child'].label} wants to {f['activity'].verb} and {f['helper'].label} helps make the toe-pls shine.",
        f'Write a simple story that repeats the phrase "one toe-pl, two toe-pls, three toe-pls" and ends with a warm, lit porch.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    act = f["activity"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"What did {child.label} want to do on {f['setting'].place}?",
            answer=f"{child.label} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Who helped make the toe-pls lit?",
            answer=f"{helper.label} helped, and that made the little caper turn out kindly.",
        ),
        QAItem(
            question=f"What stayed lit at the end?",
            answer=f"The {prize.label} stayed lit, and the porch looked warm and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does lit mean?", answer="Lit means something is on with light, like a lamp or a candle that is glowing."),
        QAItem(question="What is a caper?", answer="A caper is a small, lively adventure or errand, often a little sneaky but not very serious."),
        QAItem(question="Why do people like warm light?", answer="Warm light helps a place feel cozy, safe, and welcoming."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Activity, Prize) :- setting(Place), affords(Place, Activity), prize(Prize),
                                      prize_at_risk(Activity, Prize), has_fix(Activity, Prize).
prize_at_risk(Activity, Prize) :- splashes(Activity, Region), worn_on(Prize, Region).
has_fix(Activity, Prize) :- gear(G), prize_at_risk(Activity, Prize),
                           mess_of(Activity, Mess), guards(G, Mess),
                           covers(G, Region), worn_on(Prize, Region).
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.helper)
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
    StoryParams(place="porch", activity="caper", prize="toe_pl", name="Mina", helper="Grandma"),
    StoryParams(place="kitchen", activity="caper", prize="toe_pl", name="Toby", helper="Mom"),
    StoryParams(place="garden", activity="caper", prize="toe_pl", name="Lena", helper="Dad"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for t in triples:
            print(" ", t)
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
