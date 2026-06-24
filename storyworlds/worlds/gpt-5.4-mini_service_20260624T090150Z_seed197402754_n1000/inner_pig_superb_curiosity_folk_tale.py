#!/usr/bin/env python3
"""
storyworlds/worlds/inner_pig_superb_curiosity_folk_tale.py
===========================================================

A small folk-tale storyworld about a superbly curious pig who wants to go
inside something just a little too mysterious.

Seed tale, imagined from the prompt words:
---
There was once a pig with superb curiosity. The pig lived in a little folk
village where every lane had a secret corner and every old thing had an inner
place to hide a surprise. One day the pig wanted to look inside a locked door,
but the elder worried the pig would get dusty and lost. So the elder offered a
lantern and a gentle rule: look together, then close the door kindly. The pig
agreed, and the little mystery turned into a safe discovery.

Design notes:
- The world is small and classical: one actor, one elder, one tempting inner
  place, and one safe compromise.
- Physical state matters through meters such as dust, lost, and light.
- Emotional state matters through memes such as curiosity, worry, trust, and joy.
- The story is driven by world state, not a frozen paragraph with swapped nouns.
- The prose is intentionally folk-tale in tone: plain, warm, concrete, and
  child-facing.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key in ["dust", "lost", "light", "safe"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "worry", "trust", "joy", "relief"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    soil: str
    zone: set[str]
    weather: str
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
        self.weather: str = ""
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))


SETTINGS = {
    "lane": Setting(place="the crooked lane", indoor=False, affords={"peek", "listen"}),
    "cottage": Setting(place="the little cottage", indoor=True, affords={"peek", "listen"}),
    "barn": Setting(place="the old barn", indoor=True, affords={"peek", "listen"}),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek inside the inner place",
        gerund="peeking into the inner place",
        rush="hurry to the door",
        mess="dusty",
        soil="dusty and tired",
        zone={"face", "paws"},
        weather="",
        keyword="inner",
        tags={"inner", "curiosity"},
    ),
    "listen": Activity(
        id="listen",
        verb="listen at the hidden door",
        gerund="listening at the hidden door",
        rush="tiptoe to the door",
        mess="lost",
        soil="muddled and lost",
        zone={"ears", "paws"},
        weather="",
        keyword="curiosity",
        tags={"curiosity", "inner"},
    ),
}

PRIZES = {
    "bells": Prize(
        label="bells",
        phrase="a string of bright bells",
        type="bells",
        region="paws",
        plural=True,
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a small blue cloak",
        type="cloak",
        region="body",
    ),
    "cap": Prize(
        label="cap",
        phrase="a round wool cap",
        type="cap",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="lantern",
        label="a lantern",
        covers={"face", "paws"},
        guards={"dusty", "lost"},
        prep="bring a lantern and go together",
        tail="went softly with the lantern held high",
    ),
    Gear(
        id="rope",
        label="a little rope",
        covers={"body"},
        guards={"lost"},
        prep="tie a little rope to the porch post",
        tail="kept the porch post close with the little rope",
    ),
    Gear(
        id="cloth",
        label="a clean cloth",
        covers={"paws", "body"},
        guards={"dusty"},
        prep="wrap a clean cloth around the pig's snout",
        tail="kept the dust from sneaking in",
    ),
]

PIG_NAMES = ["Pip", "Pudding", "Milo", "Mabel", "Bram", "Bessie", "Nell", "Toby"]
ELDER_NAMES = ["Gran", "Old Ben", "Aunt Rose", "Grandma Fern", "Uncle Cobb"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    elder: str
    seed: Optional[int] = None


def _valid(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or activity.keyword == "curiosity"


def _select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and (prize.region in gear.covers or "body" in gear.covers):
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if _valid(act, prize) and _select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not have a reasonable safe fix for "
        f"{prize.label} in this small folk tale.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about a superbly curious pig and a safe inner mystery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--elder")
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
        if not (_valid(act, prize) and _select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(PIG_NAMES),
        elder=args.elder or rng.choice(ELDER_NAMES),
    )


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    actor.meters["light"] += 0.25
    if narrate:
        world.say(f"{actor.id} stepped nearer with curious little paws.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters[activity.mess] >= THRESHOLD}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, pig_name: str, elder_name: str) -> World:
    world = World(setting)
    pig = world.add(Entity(id=pig_name, kind="character", type="pig", meters={"dust": 0.0, "lost": 0.0, "light": 0.0, "safe": 0.0}, memes={"curiosity": 0.0, "worry": 0.0, "trust": 0.0, "joy": 0.0, "relief": 0.0}))
    elder = world.add(Entity(id=elder_name, kind="character", type="elder", label=elder_name))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=pig.id, caretaker=elder.id, worn_by=pig.id))

    pig.memes["curiosity"] += 2
    pig.memes["trust"] += 1

    world.say(f"{pig.id} was a superbly curious little pig who lived by {setting.place}.")
    world.say(f"{pig.id} liked every nook, but most of all {pig.pronoun('possessive')} heart longed for inner mysteries.")
    world.say(f"One day {elder.id} gave {pig.id} {prize.phrase}, and the pig wore {prize.it()} with pride.")

    world.para()
    world.say(f"At {setting.place}, {pig.id} found a hidden door and wanted to {activity.verb}.")
    world.say(f"{elder.id} saw the shine in {pig.id}'s eyes and worried the pig would get {activity.soil}.")
    pred = predict_mess(world, pig, activity, prize.id)
    if pred["soiled"]:
        pig.memes["worry"] += 1
        world.say(f'"You may get {activity.soil}," {elder.id} said. "Let us be wise together."')
    _do_activity(world, pig, activity, narrate=True)
    prize.meters[activity.mess] += 1
    prize.meters["dust"] += 1
    pig.meters["dust"] += 1
    pig.memes["worry"] += 0.5

    world.para()
    gear = _select_gear(activity, prize_cfg)
    if gear is None:
        raise StoryError("No reasonable safe gear for this tale.")
    world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), worn_by=pig.id))
    if predict_mess(world, pig, activity, prize.id)["soiled"]:
        raise StoryError("The chosen compromise did not make the story safe enough.")
    pig.memes["trust"] += 1
    pig.memes["joy"] += 1
    pig.memes["relief"] += 1
    world.say(f"{elder.id} smiled and said, \"How about we {gear.prep}?\"")
    world.say(f"{pig.id} agreed at once.")
    world.say(f"They {gear.tail}, and together they opened the door just enough to peek.")
    world.say(f"Inside, the little secret was only a shadow and a shelf, but it felt wonderful because they had looked safely together.")
    world.say(f"{pig.id} went home with {prize.label} still fine and {pig.id}'s curious heart feeling even brighter.")

    world.facts.update(hero=pig, elder=elder, prize=prize, activity=activity, setting=setting, gear=gear, resolved=True)
    return world


SETTING_ORDER = ["cottage", "barn", "lane"]
ACTIVITY_ORDER = ["peek", "listen"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pig, elder, act, prize = f["hero"], f["elder"], f["activity"], f["prize"]
    return [
        f'Write a gentle folk tale for a small child about a pig named {pig.id} and the word "inner".',
        f"Tell a story where {pig.id}, a superbly curious pig, wants to {act.verb} but {elder.id} helps keep {prize.label} safe.",
        f'Write a short story with the words "inner", "pig", and "superb" that ends with a wise compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pig, elder, prize, act = f["hero"], f["elder"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {pig.id}, a superbly curious pig who wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {elder.id} worry about {pig.id} going inside?",
            answer=f"{elder.id} worried because {pig.id} might get {act.soil} while peeking into the inner place.",
        ),
        QAItem(
            question=f"What helped {pig.id} stay safe?",
            answer=f"A lantern and a careful walk together helped {pig.id} stay safe while the pig looked inside.",
        ),
        QAItem(
            question=f"What stayed fine by the end of the tale?",
            answer=f"{pig.id}'s {prize.label} stayed fine, and the pig came home with a happy heart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curious mean?",
            answer="Curious means wanting to know more and wanting to see what a thing is like.",
        ),
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives light, so people can see in dark places or on dark paths.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a simple old story that often has a gentle lesson and plain, memorable characters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), splashes(A, R), worn_on(P, R).
has_fix(A, P) :- prize_at_risk(A, P), gear(G), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
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
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.elder)
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
    StoryParams(place="cottage", activity="peek", prize="cap", name="Pip", elder="Gran"),
    StoryParams(place="barn", activity="listen", prize="bells", name="Pudding", elder="Old Ben"),
    StoryParams(place="lane", activity="peek", prize="cloak", name="Bram", elder="Aunt Rose"),
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for p in triples:
            print("  ", p)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
