#!/usr/bin/env python3
"""
storyworlds/worlds/fellow_ship_paw_rosemary_happy_ending_humor.py
===============================================================

A standalone story world in a tiny pirate-tale style domain with a happy ending
and a light humorous turn.

Premise:
- A small crew of friends on a little ship wants to sail for rosemary.
- A playful paw-rat problem threatens the herb crate.
- The crew uses a clever, gentle trick and ends with rosemary saved and
  everyone laughing.

This world keeps the classical storyworld contract:
- typed entities with meters and memes
- state-driven narration
- validation of reasonable combinations
- inline ASP twin with facts
- QA and trace support
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
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
class Mischief:
    id: str
    label: str
    phrase: str
    humor: str
    harmless_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CrewAid:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_paw_smudge(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters.get("paw", 0.0) < THRESHOLD:
            continue
        sig = ("paw_smudge", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["amused"] = ent.memes.get("amused", 0.0) + 1
        out.append(f"{ent.id} snickered at the paw-print trouble.")
    return out


def _r_spill_rosemary(world: World) -> list[str]:
    out: list[str] = []
    crate = world.entities.get("rosemary")
    if not crate:
        return out
    if crate.meters.get("jostled", 0.0) < THRESHOLD:
        return out
    sig = ("spill", crate.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crate.meters["scattered"] = crate.meters.get("scattered", 0.0) + 1
    out.append("The rosemary leaves scattered like tiny green confetti.")
    return out


def _r_cheerful_fix(world: World) -> list[str]:
    out: list[str] = []
    herb = world.entities.get("rosemary")
    aid = world.entities.get("net")
    if not herb or not aid:
        return out
    if herb.meters.get("scattered", 0.0) < THRESHOLD or aid.meters.get("used", 0.0) < THRESHOLD:
        return out
    sig = ("fix", herb.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    herb.meters["gathered"] = 1.0
    for kid in world.characters():
        kid.memes["joy"] = kid.memes.get("joy", 0.0) + 1
    out.append("The crew gathered the rosemary back into the crate.")
    return out


CAUSAL_RULES = [
    Rule("paw_smudge", "humor", _r_paw_smudge),
    Rule("spill_rosemary", "physical", _r_spill_rosemary),
    Rule("cheerful_fix", "resolution", _r_cheerful_fix),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(setting: Setting, activity: Activity, prize: Prize, mischief: Mischief, aid: CrewAid) -> bool:
    return prize.region in activity.zone and "herb" in prize.tags and "paw" in mischief.tags and "net" in aid.tags


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for p in PRIZES:
                for m in MISCHIEF:
                    for c in AIDS:
                        if reasonable_combo(SETTINGS[s], ACTIVITIES[a], PRIZES[p], MISCHIEF[m], AIDS[c]):
                            combos.append((s, a, p, m, c))
    return combos


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    mischief: str
    aid: str
    crew_one: str
    crew_two: str
    crew_one_type: str
    crew_two_type: str
    captain_type: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    mischief = MISCHIEF[params.mischief]
    aid = AIDS[params.aid]
    world = World(setting)

    c1 = world.add(Entity(id=params.crew_one, kind="character", type=params.crew_one_type, label=params.crew_one))
    c2 = world.add(Entity(id=params.crew_two, kind="character", type=params.crew_two_type, label=params.crew_two))
    cap = world.add(Entity(id="Captain", kind="character", type=params.captain_type, label="the captain"))
    herb = world.add(Entity(id="rosemary", type="thing", label="rosemary", owner=cap.id, attrs={"kind": "herb"}))
    paw = world.add(Entity(id="paw", type="thing", label=mischief.label, attrs={"kind": "paw"}))
    net = world.add(Entity(id="net", type="thing", label=aid.label, attrs={"kind": "net"}))

    for e in (c1, c2, cap, herb, paw, net):
        e.meters.setdefault("paw", 0.0)
        e.meters.setdefault("jostled", 0.0)
        e.meters.setdefault("scattered", 0.0)
        e.meters.setdefault("gathered", 0.0)
        e.meters.setdefault("used", 0.0)
        e.memes.setdefault("joy", 0.0)
        e.memes.setdefault("worry", 0.0)
        e.memes.setdefault("amused", 0.0)

    return world


def tell(world: World, params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    mischief = MISCHIEF[params.mischief]
    aid = AIDS[params.aid]

    crew1 = world.get(params.crew_one)
    crew2 = world.get(params.crew_two)
    captain = world.get("Captain")
    herb = world.get("rosemary")
    paw = world.get("paw")
    net = world.get("net")

    crew1.memes["joy"] += 1
    crew2.memes["joy"] += 1

    world.say(
        f"On the little fellow-ship, {crew1.id} and {crew2.id} bobbed along the harbor "
        f"while {captain.label_word} watched the deck and the pot of rosemary."
    )
    world.say(
        f"They loved to {activity.verb}, and the {setting.place} smelled of salt, rope, "
        f"and rosemary."
    )

    world.para()
    world.say(
        f"Then {mischief.humor} made trouble: a {mischief.label} sneaked onto the deck, "
        f"and a puff of paws sent the crate sliding."
    )
    crew1.meters["paw"] += 1
    crew2.meters["paw"] += 1
    herb.meters["jostled"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{crew2.id} laughed and said, '{mischief.humor}'"
        f" {mischief.phrase} was no match for a clever {aid.label}."
    )
    net.meters["used"] += 1
    herb.meters["gathered"] += 1
    world.say(
        f"{captain.label_word.capitalize()} used {aid.phrase} to scoop the rosemary back safe."
    )
    propagate(world, narrate=True)

    world.para()
    if herb.meters.get("gathered", 0.0) >= THRESHOLD:
        crew1.memes["joy"] += 1
        crew2.memes["joy"] += 1
        captain.memes["joy"] = captain.memes.get("joy", 0.0) + 1
        world.say(
            f"At last, the crew tucked the rosemary away, and the whole fellow-ship "
            f"laughed when the paw tried to act like a mighty pirate."
        )
        world.say(
            f"The little pot stayed green, the deck stayed tidy, and the ship sailed on "
            f"with a happy ending."
        )
    else:
        raise StoryError("The rosemary was not safely gathered.")
    world.facts.update(
        crew_one=crew1,
        crew_two=crew2,
        captain=captain,
        herb=herb,
        paw=paw,
        net=net,
        setting=setting,
        activity=activity,
        prize=prize,
        mischief=mischief,
        aid=aid,
        resolved=True,
    )
    return world


SETTINGS = {
    "dock": Setting(place="the dock", indoors=False, affords={"sail"}),
    "deck": Setting(place="the deck", indoors=False, affords={"sail"}),
    "harbor": Setting(place="the harbor", indoors=False, affords={"sail"}),
}

ACTIVITIES = {
    "sail": Activity(
        id="sail",
        verb="sing and sail",
        gerund="singing and sailing",
        rush="hurry to the ropes",
        mess="spray",
        zone={"deck"},
        keyword="fellow-ship",
        tags={"ship"},
    ),
}

PRIZES = {
    "rosemary": Prize(
        id="rosemary",
        label="rosemary",
        phrase="a pot of rosemary",
        region="deck",
        tags={"herb"},
    ),
}

MISCHIEF = {
    "paw": Mischief(
        id="paw",
        label="paw",
        phrase="those paw prints",
        humor="The paw was so proud it nearly saluted itself.",
        harmless_fix="pat the floor dry",
        tags={"paw", "humor"},
    ),
}

AIDS = {
    "net": CrewAid(
        id="net",
        label="net",
        phrase="a little fishing net",
        use="scoop",
        tags={"net"},
    ),
}

CREW_NAMES = ["Mina", "Jules", "Pip", "Nell", "Otto", "Rae", "Toby", "Wren"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate-style story for a child that includes "fellow-ship" and "rosemary".',
        f"Tell a funny little ship story where {f['crew_one'].id} and {f['crew_two'].id} keep the rosemary safe from a paw on the deck.",
        f"Write a happy-ending story about a crew, a paw, and rosemary, with a joke and a clever rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1, c2, cap, herb, paw, aid = f["crew_one"], f["crew_two"], f["captain"], f["herb"], f["paw"], f["aid"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {c1.id}, {c2.id}, and {cap.label_word} on a little ship, all trying to keep the rosemary safe.",
        ),
        QAItem(
            question=f"What trouble did the paw cause?",
            answer=f"The paw knocked the rosemary crate around and made the crew laugh and worry at the same time.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used {aid.label} to gather the rosemary back safely and keep the deck tidy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: the rosemary stayed green, the crew laughed, and the little fellow-ship sailed on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rosemary?",
            answer="Rosemary is a fragrant herb used in cooking. It smells nice and has narrow green leaves.",
        ),
        QAItem(
            question="What is a paw?",
            answer="A paw is an animal foot, like a cat's paw or a dog's paw.",
        ),
        QAItem(
            question="What is a net for?",
            answer="A net can scoop or catch things so they do not tumble away.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


ASP_RULES = r"""
crew(C) :- character(C), crew_member(C).
trouble(paw) :- mischief(paw).
safe_fix(net) :- aid(net).
valid(setting, activity, prize, mischief, aid) :- setting(S), activity(A), prize(P), mischief(M), aid(I), prize_at_risk(P,A), paw_trouble(M), net_fix(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_at_risk", pid, "sail"))
    for mid in MISCHIEF:
        lines.append(asp.fact("mischief", mid))
        lines.append(asp.fact("paw_trouble", mid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("net_fix", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos_python() -> list[tuple[str, str, str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos_python()) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate-ish story world with rosemary and a paw.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--mischief", choices=MISCHIEF)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.mischief is None or c[3] == args.mischief)
              and (args.aid is None or c[4] == args.aid)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, activity, prize, mischief, aid = rng.choice(sorted(combos))
    crew_one = rng.choice(CREW_NAMES)
    crew_two = rng.choice([n for n in CREW_NAMES if n != crew_one])
    return StoryParams(
        setting=setting,
        activity=activity,
        prize=prize,
        mischief=mischief,
        aid=aid,
        crew_one=crew_one,
        crew_two=crew_two,
        crew_one_type="girl",
        crew_two_type="boy",
        captain_type="woman",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
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
    StoryParams("deck", "sail", "rosemary", "paw", "net", "Mina", "Jules", "girl", "boy", "woman"),
    StoryParams("harbor", "sail", "rosemary", "paw", "net", "Pip", "Wren", "boy", "girl", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
