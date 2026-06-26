#!/usr/bin/env python3
"""
A standalone storyworld for a small folk-tale domain about teamwork and conflict.

Seed impression:
- A village holds a seventieth feast.
- A proud cook has a steak meant for the celebration.
- The steak threatens to fall off the edge of a table or cliffside tray.
- The villagers must work together, but an argument about who leads the effort
  creates conflict before the group cooperates and saves the feast.

The world is intentionally small and constraint-checked: the story only
generates when the chosen setting, event, and item form a plausible folk tale
about a shared task, a risk, a disagreement, and a joint rescue.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"woman", "girl", "queen", "mother", "aunt"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"man", "boy", "king", "father", "uncle"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    key: str
    name: str
    setting_word: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Event:
    key: str
    verb: str
    gerund: str
    risk: str
    danger: str
    zone: set[str]
    need_teamwork: bool = True
    keyword: str = ""


@dataclass
class Prize:
    key: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Aid:
    key: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _ensure_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _ensure_mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _set_meter(ent: Entity, key: str, value: float) -> None:
    ent.meters[key] = value


def _set_mem(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for a in world.characters():
        if _ensure_mem(a, "insulted") < THRESHOLD or _ensure_mem(a, "stubborn") < THRESHOLD:
            continue
        sig = ("conflict", a.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _set_mem(a, "conflict", _ensure_mem(a, "conflict") + 1)
        out.append(f"{a.label} narrowed {a.pronoun('possessive')} eyes and would not back down.")
    return out


def _r_hold(world: World) -> list[str]:
    out: list[str] = []
    cook = world.get("cook")
    steak = world.get("steak")
    if _ensure_meter(steak, "slip") < THRESHOLD:
        return out
    if ("held", steak.id) in world.fired:
        return out
    world.fired.add(("held", steak.id))
    _set_meter(steak, "slip", 0.0)
    _set_mem(cook, "relief", _ensure_mem(cook, "relief") + 1)
    out.append("The cook caught the steak before it slid away.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = [a for a in world.characters() if _ensure_mem(a, "helping") >= THRESHOLD]
    if len(team) < 2:
        return out
    if ("teamwork",) in world.fired:
        return out
    world.fired.add(("teamwork",))
    for a in team:
        _set_mem(a, "joy", _ensure_mem(a, "joy") + 1)
        _set_mem(a, "conflict", 0.0)
    out.append("Together, they made one strong pair of hands out of many small ones.")
    return out


RULES = [_r_conflict, _r_hold, _r_teamwork]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            res = rule(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_loss(world: World) -> bool:
    sim = world.copy()
    steak = sim.get("steak")
    _set_meter(steak, "slip", 1.0)
    propagate(sim, narrate=False)
    return _ensure_meter(sim.get("steak"), "slip") >= THRESHOLD


def reasonableness_gate(place: Place, event: Event, prize: Prize) -> bool:
    if prize.region not in event.zone:
        return False
    if not place.affordances.intersection({event.key}):
        return False
    return True


def select_aid(event: Event, prize: Prize) -> Optional[Aid]:
    for aid in AID_REGISTRY:
        if event.key in aid.helps and prize.region in aid.covers:
            return aid
    return None


def introduce(world: World, hero: Entity, helper: Entity, prize: Entity, event: Event) -> None:
    world.say(
        f"Long ago, in {world.place.name}, there lived {hero.label} and {helper.label}, "
        f"who were both needed for the {event.keyword} feast."
    )
    world.say(
        f"At the heart of the feast was {prize.phrase}, a prize fit for the "
        f"{world.facts['ordinal']} celebration."
    )


def set_scene(world: World, event: Event, prize: Entity) -> None:
    world.say(
        f"The day was busy and bright, and everyone knew the {event.verb} had to be finished "
        f"before the supper bell."
    )
    world.say(
        f"But the {prize.label} sat near the edge, and one wrong bump could send it over."
    )


def start_conflict(world: World, hero: Entity, helper: Entity, event: Event) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    helper.memes["stubborn"] = helper.memes.get("stubborn", 0) + 1
    hero.memes["insulted"] = 1
    helper.memes["insulted"] = 1
    world.say(
        f"{hero.label} said {hero.pronoun('possessive')} way was best, and {helper.label} answered back."
    )
    world.say(
        f"Soon the two were in a little conflict, each one talking over the other about how to {event.verb}."
    )


def need_help(world: World, hero: Entity, helper: Entity, prize: Entity, aid: Aid) -> None:
    world.say(
        f"Then {helper.label} looked at the {prize.label} teetering near the edge and softened."
    )
    world.say(
        f"At last {hero.label} saw that the only safe way was to use {aid.label}."
    )


def resolve(world: World, hero: Entity, helper: Entity, prize: Entity, aid: Aid, event: Event) -> None:
    hero.memes["helping"] = 1
    helper.memes["helping"] = 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.label} and {helper.label} lifted the {prize.label} together, keeping it steady with {aid.label}."
    )
    world.say(
        f"They carried it back from the edge and finished the {event.gerund} in time."
    )
    world.say(
        f"When the feast began, the whole village shared the steak, and the old conflict was gone like smoke."
    )


def tell(world_place: Place, event: Event, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(world_place)
    hero = world.add(Entity(id="hero", kind="character", type="man", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=helper_name))
    cook = world.add(Entity(id="cook", kind="character", type="woman", label="the cook"))
    prize = world.add(Entity(id=prize_cfg.key, kind="thing", type=prize_cfg.key, label=prize_cfg.label, phrase=prize_cfg.phrase))

    world.facts["ordinal"] = "seventieth"
    world.facts["event"] = event
    world.facts["prize"] = prize
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["cook"] = cook

    introduce(world, hero, helper, prize, event)
    world.para()
    set_scene(world, event, prize)
    start_conflict(world, hero, helper, event)
    propagate(world, narrate=True)

    world.para()
    aid = select_aid(event, prize)
    if aid is None:
        raise StoryError("No reasonable aid exists for this event and prize.")
    world.facts["aid"] = aid
    need_help(world, hero, helper, prize, aid)
    resolve(world, hero, helper, prize, aid, event)
    return world


PLACE_REGISTRY = {
    "village": Place(key="village", name="the village green", setting_word="village", affordances={"carry"}),
    "hill": Place(key="hill", name="the hilltop table", setting_word="hill", affordances={"carry"}),
    "harbor": Place(key="harbor", name="the harbor pier", setting_word="harbor", affordances={"carry"}),
}

EVENT_REGISTRY = {
    "carry": Event(
        key="carry",
        verb="carry the feast",
        gerund="carrying the feast",
        risk="slip",
        danger="the edge",
        zone={"hands", "arms"},
        need_teamwork=True,
        keyword="teamwork",
    ),
    "balance": Event(
        key="balance",
        verb="balance the platter",
        gerund="balancing the platter",
        risk="slip",
        danger="the edge",
        zone={"hands", "arms"},
        need_teamwork=True,
        keyword="teamwork",
    ),
}

PRIZE_REGISTRY = {
    "steak": Prize(key="steak", label="steak", phrase="a thick roast steak", region="hands"),
}

AID_REGISTRY = [
    Aid(key="tray", label="a wide wooden tray", covers={"hands", "arms"}, helps={"carry", "balance"}, prep="use a wide wooden tray", tail="walked carefully with the tray"),
    Aid(key="rope", label="a length of rope", covers={"hands", "arms"}, helps={"carry"}, prep="tie the handles with a length of rope", tail="walked carefully with the rope"),
]

HERO_NAMES = ["Mara", "Niko", "Sera", "Tomas", "Iva", "Bram"]
HELPER_NAMES = ["Old Jo", "Lena", "Pek", "Anya", "Gus", "Mina"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACE_REGISTRY.values():
        for e in EVENT_REGISTRY.values():
            for pr in PRIZE_REGISTRY.values():
                if reasonableness_gate(p, e, pr):
                    out.append((p.key, e.key, pr.key))
    return out


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about teamwork, conflict, and a seventieth feast.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--event", choices=EVENT_REGISTRY)
    ap.add_argument("--prize", choices=PRIZE_REGISTRY)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.event is None or c[1] == args.event)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event, prize = rng.choice(combos)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(place=place, event=event, prize=prize, hero=hero, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about teamwork and conflict that includes the word "edge".',
        f"Tell a gentle village story where {f['hero'].label} and {f['helper'].label} disagree, then work together to save {f['prize'].label}.",
        f"Write a story for children about the seventieth feast, a steak near the edge, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    event = f["event"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who were the two villagers at the center of the story?",
            answer=f"The story was about {hero.label} and {helper.label}, who had to work together during the feast.",
        ),
        QAItem(
            question=f"What was in danger near the edge?",
            answer=f"The {prize.label} was in danger near the edge of the table, so it had to be held carefully.",
        ),
        QAItem(
            question=f"Why did {hero.label} and {helper.label} argue at first?",
            answer=f"They had a conflict because they both wanted to lead the {event.verb} in their own way.",
        ),
        QAItem(
            question=f"What helped them solve the problem?",
            answer=f"They used {aid.label} and worked together so the {prize.label} would not slip over the edge.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a disagreement or struggle between people who want different things.",
        ),
        QAItem(
            question="What does seventieth mean?",
            answer="Seventieth means the number 70th, like the seventieth celebration in a long line of celebrations.",
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACE_REGISTRY.values():
        lines.append(asp.fact("place", p.key))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", p.key, a))
    for e in EVENT_REGISTRY.values():
        lines.append(asp.fact("event", e.key))
        for z in sorted(e.zone):
            lines.append(asp.fact("zone", e.key, z))
        lines.append(asp.fact("needs_teamwork", e.key))
    for pr in PRIZE_REGISTRY.values():
        lines.append(asp.fact("prize", pr.key))
        lines.append(asp.fact("region", pr.key, pr.region))
    for aid in AID_REGISTRY:
        lines.append(asp.fact("aid", aid.key))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.key, c))
        for h in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.key, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,E,Pr) :- place(P), event(E), prize(Pr), affords(P,E), zone(E,R), region(Pr,R).
has_aid(E,Pr) :- aids(A), helps(A,E), covers(A,R), region(Pr,R).
good(P,E,Pr) :- valid(P,E,Pr), has_aid(E,Pr).
"""


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
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACE_REGISTRY[params.place],
        EVENT_REGISTRY[params.event],
        PRIZE_REGISTRY[params.prize],
        params.hero,
        params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="village", event="carry", prize="steak", hero="Mara", helper="Old Jo"),
    StoryParams(place="hill", event="balance", prize="steak", hero="Niko", helper="Anya"),
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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
