#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    companion: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    risk_region: str
    fragile: bool = False
    plural: bool = False


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    ending: str
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)
            self.trace.append(line)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        parts: list[str] = []
        cur: list[str] = []
        for line in self.lines:
            if line == "":
                if cur:
                    parts.append(" ".join(cur))
                    cur = []
            else:
                cur.append(line)
        if cur:
            parts.append(" ".join(cur))
        return "\n\n".join(parts)


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    remedy: str
    name: str
    companion: str
    seed: Optional[int] = None


SETTINGS = {
    "railway": Setting(
        place="the hill town trolley stop",
        detail="The trolley clanged along its bright rail, past the bakery and the bell tower.",
        affordances={"ride", "compare"},
    )
}

ACTIVITIES = {
    "ride": Activity(
        id="ride",
        verb="ride the trolley",
        gerund="riding the trolley",
        risk="a bump could jostle the prize",
        keyword="trolley",
        tags={"trolley"},
    ),
    "compare": Activity(
        id="compare",
        verb="compare the two routes",
        gerund="comparing the two routes",
        risk="a wrong guess could send the trolley the long way around",
        keyword="similarity",
        tags={"similarity"},
    ),
}

PRIZES = {
    "coil": Prize(
        id="coil",
        label="coil",
        phrase="a shiny copper coil in a wicker case",
        risk_region="hands",
        fragile=True,
    ),
    "pigeon": Prize(
        id="pigeon",
        label="parcel",
        phrase="a parcel of chalk-dust jars",
        risk_region="hands",
        fragile=True,
    ),
}

REMEDIES = {
    "gloves": Remedy(
        id="gloves",
        label="soft gloves",
        prep="put on soft gloves and steady the case",
        ending="wore soft gloves and kept the case snug",
        protects={"hands"},
    ),
    "strap": Remedy(
        id="strap",
        label="a strap",
        prep="buckle on a strap and hold the case close",
        ending="buckled on a strap and held the case close",
        protects={"hands"},
    ),
}

NAMES = ["Ada", "Mina", "Tess", "Iris", "Lena", "Ruth", "Jules", "Nell"]
COMPANIONS = ["the conductor", "the station keeper", "the old porter", "the bell ringer"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for p in PRIZES:
                out.append((s, a, p))
    return out


def reasonableness_gate(setting: Setting, activity: Activity, prize: Prize, remedy: Remedy) -> bool:
    return "ride" in setting.affordances and prize.fragile and "hands" in remedy.protects


ASP_RULES = r"""
setting_valid(S) :- setting(S).
activity_valid(A) :- activity(A).
prize_valid(P) :- prize(P).
remedy_valid(R) :- remedy(R).

compatible(S,A,P) :- setting_valid(S), activity_valid(A), prize_valid(P), affords(S,A), fragile(P).
story_ok(S,A,P,R) :- compatible(S,A,P), remedy_valid(R), protects(R,hands).
#show compatible/3.
#show story_ok/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for part in sorted(r.protects):
            lines.append(asp.fact("protects", rid, part))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale trolley storyworld with similarity and a physicist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    if args.remedy and args.remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")
    if args.setting and args.activity and args.prize and args.remedy:
        s, a, p, r = SETTINGS[args.setting], ACTIVITIES[args.activity], PRIZES[args.prize], REMEDIES[args.remedy]
        if not reasonableness_gate(s, a, p, r):
            raise StoryError("That combination is not a believable trolley tale.")
    combos = [c for c in combos if (not args.setting or c[0] == args.setting)
              and (not args.activity or c[1] == args.activity)
              and (not args.prize or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, activity, prize = rng.choice(combos)
    remedy = args.remedy or rng.choice(list(REMEDIES))
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(setting=setting, activity=activity, prize=prize, remedy=remedy, name=name, companion=companion)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    remedy = REMEDIES[params.remedy]
    w = World(setting)
    hero = w.add(Entity(id=params.name, kind="character", type="woman", label=params.name))
    comp = w.add(Entity(id="companion", kind="character", type="person", label=params.companion))
    w.add(Entity(id="prize", kind="thing", type="thing", label=prize.label, phrase=prize.phrase, owner=hero.id))
    w.facts.update(hero=hero, companion=comp, prize=prize, remedy=remedy, activity=activity, setting=setting)

    w.say(f"At the hill town trolley stop, {hero.id} the physicist came striding along like a weather vane with a secret.")
    w.say(f"{hero.id} carried {prize.phrase}, and {hero.pronoun().capitalize()} kept saying, \"Easy now, easy now; a grand mind needs a gentle hand.\"")
    w.say(f"{hero.id} loved {activity.gerund}, and {comp.label} wagged a finger. \"If the road is rough, the case may rattle like a kettle,\" {comp.pronoun()} said.")
    w.para()
    w.say(f"The conductor called, \"Two routes look mighty alike today: one short, one long. Their rails are as similar as twins in a mirror!\"")
    w.say(f"{hero.id} squinted at the map and grinned. \"Similarity is my fiddle-string,\" {hero.id} said. \"I can tell what matches by the tiniest tick and tattle.\"")
    w.say(f"But the trolley gave a great ding and leaned toward the wrong bend, and the case gave one nervous clack.")
    w.say(f"\"By my chalk and my clockwork shoes,\" said {comp.label}, \"choose quick, or that fragile prize will jostle and moo like a cow in a canoe.\"")
    w.para()
    w.say(f"{hero.id} laughed, then answered in rhyme, \"If routes are near and rails align, I read the clues in a silver line. If left and right look much the same, I test the sound, I test the frame.\"")
    w.say(f"Then {hero.id} used {remedy.label}: {remedy.prep}.")
    w.say(f"The trolley stayed true, the prize stayed snug, and the wheels sang on like fiddle bows over a barn dance rug.")
    w.say(f"At the last stop, {hero.id} was still {activity.gerund}, {remedy.ending}, and the little case shone safe as a moon in a pail.")
    w.say(f"\"That physicist can rhyme a line and tame a trolley at the same time,\" said {comp.label}. \"Well I’ll be!\"")
    w.facts["resolved"] = True
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        'Write a tall-tale story for a young child that includes the words "similarity" and "trolley".',
        f"Tell a funny story about a physicist named {f['hero'].id} who must use similarity to guide a trolley safely while carrying {f['prize'].phrase}.",
        f"Write a story with dialogue and rhyme where {f['hero'].id} and {f['companion'].label} solve a trolley problem without breaking the prize.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    hero: Entity = f["hero"]
    comp: Entity = f["companion"]
    prize: Prize = f["prize"]
    activity: Activity = f["activity"]
    remedy: Remedy = f["remedy"]
    return [
        QAItem(
            question=f"Who was the physicist in the story?",
            answer=f"The physicist was {hero.id}, who rode the trolley and kept the shiny case safe.",
        ),
        QAItem(
            question=f"What two things did {hero.id} compare to make the right choice?",
            answer="They compared the two trolley routes, looking for how similar they were before choosing the safer way.",
        ),
        QAItem(
            question=f"Why did the trolley worry {comp.label}?",
            answer=f"It worried {comp.label} because a rough turn could jostle {prize.phrase} and make it bang around in the trolley.",
        ),
        QAItem(
            question=f"How did {hero.id} protect the prize?",
            answer=f"{hero.id} used {remedy.label} and kept the case snug, so the prize stayed safe while the trolley rolled on.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is similarity?",
            answer="Similarity means two things are alike in some way, like twins wearing the same kind of hat.",
        ),
        QAItem(
            question="What is a trolley?",
            answer="A trolley is a wheeled car that rides along rails or a track and carries people from one place to another.",
        ),
        QAItem(
            question="What does a physicist study?",
            answer="A physicist studies how the world moves and behaves, like motion, light, sound, and force.",
        ),
    ]


def dump_trace(w: World) -> str:
    return "\n".join(["--- trace ---"] + w.trace)


CURATED = [
    StoryParams(setting="railway", activity="compare", prize="coil", remedy="gloves", name="Ada", companion="the conductor"),
    StoryParams(setting="railway", activity="ride", prize="coil", remedy="strap", name="Mina", companion="the bell ringer"),
]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    w = tell(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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
        print(asp_program("#show story_ok/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        models = asp.one_model(asp_program("#show compatible/3."))
        print(sorted(set(asp.atoms(models, "compatible"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
