#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/ken_loo_sharing_problem_solving_cautionary_myth.py
====================================================================================================

A small myth-style storyworld about sharing, problem solving, and a cautionary
turn. Ken and Loo meet a village need, choose how to share a scarce treasure,
and learn a careful lesson from the world itself.

The seed prompt asks for the words "ken" and "loo" and for a mythic style.
This world keeps the stories short, concrete, and state-driven: a village has a
problem, the pair tries a choice, a warning matters, and the ending image
proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    carries: str = ""
    shares: bool = False
    helpful: bool = False
    cautious: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    problem: str
    image: str
    needs: str
    holds: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    kind: str
    can_share: bool = True
    can_split: bool = False
    fragile: bool = False
    region: str = "hands"


@dataclass
class Fix:
    id: str
    label: str
    plan: str
    ending: str
    handles: set[str] = field(default_factory=set)
    kind: str = "help"


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def people(self) -> list[Entity]:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    treasure: str
    problem: str
    fix: str
    seed: Optional[int] = None


PLACES = {
    "well": Place(id="well", label="the old well", problem="dry", image="dusty stones and a dark bottom", needs="water", holds={"water", "rope"}),
    "grove": Place(id="grove", label="the fig grove", problem="hungry", image="silver leaves and empty branches", needs="fruit", holds={"fruit", "shade"}),
    "village": Place(id="village", label="the village square", problem="noisy", image="a ring of stalls and a cracked fountain", needs="calm", holds={"bread", "water"}),
    "shore": Place(id="shore", label="the moonlit shore", problem="dark", image="waves and black stones under stars", needs="light", holds={"shells", "light"}),
}

TREASURES = {
    "waterjar": Treasure(id="waterjar", label="a clay water jar", phrase="a cool clay water jar", kind="water"),
    "breadbasket": Treasure(id="breadbasket", label="a basket of bread", phrase="a warm basket of bread", kind="bread", can_split=True),
    "lantern": Treasure(id="lantern", label="a bronze lantern", phrase="a bronze lantern with a bright wick", kind="light", fragile=True),
    "shells": Treasure(id="shells", label="a shell necklace", phrase="a necklace of shining shells", kind="shells", can_split=False),
}

FIXES = {
    "share": Fix(id="share", label="shared hands", plan="they split it fairly and passed it around", ending="shared it with open hands", handles={"water", "bread", "shells", "light"}),
    "trade": Fix(id="trade", label="trading gifts", plan="they traded one treasure for what the place needed", ending="traded for what the place needed", handles={"water", "bread", "shells", "light"}),
    "repair": Fix(id="repair", label="a careful repair", plan="they tied, mended, and set things right before anyone used them", ending="mended it and made it useful again", handles={"water", "bread", "shells", "light"}),
    "warn": Fix(id="warn", label="a warning", plan="they paused and listened to the old sign before choosing", ending="chose the safer way after the warning", handles={"water", "bread", "shells", "light"}),
}

NAMES = ["Ken", "Loo"]
TRAITS = ["steady", "kind", "curious", "brave", "gentle"]


class Rule:
    def __init__(self, name: str, fn):
        self.name = name
        self.fn = fn


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared"):
        return out
    treasure: Treasure = world.facts["treasure_cfg"]
    if not treasure.can_share and not treasure.can_split:
        return out
    if treasure.can_split:
        for p in world.people():
            p.memes["generosity"] += 1
        world.facts["shared"] = True
        out.append("They split the bread so both could eat.")
    return out


def _r_warn(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("warned") or not world.facts.get("risk"):
        return out
    place: Place = world.facts["place_cfg"]
    treasure: Treasure = world.facts["treasure_cfg"]
    if treasure.fragile or place.problem == "dark":
        world.facts["warned"] = True
        for p in world.people():
            p.memes["caution"] += 1
        out.append("The old stones seemed to warn them to be careful.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("fixed"):
        return out
    if world.facts.get("chosen_fix") == "share":
        world.facts["fixed"] = True
        out.append("The village felt calmer after they shared.")
    elif world.facts.get("chosen_fix") == "trade":
        world.facts["fixed"] = True
        out.append("The place gained what it needed.")
    elif world.facts.get("chosen_fix") == "repair":
        world.facts["fixed"] = True
        out.append("What was broken became useful again.")
    elif world.facts.get("chosen_fix") == "warn":
        world.facts["fixed"] = True
        out.append("They chose the safer path.")
    return out


CAUSAL_RULES = [Rule("share", _r_share), Rule("warn", _r_warn), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    said: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.fn(world)
            if lines:
                changed = True
                said.extend(lines)
    if narrate:
        for s in said:
            world.say(s)
    return said


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for tre_id, tre in TREASURES.items():
            for fix_id, fix in FIXES.items():
                if tre.kind in fix.handles:
                    combos.append((place_id, tre_id, place.problem, fix_id))
    return combos


def explain_rejection() -> str:
    return "(No story: that choice does not fit a reasonable sharing problem.)"


def build_world(place: Place, treasure: Treasure, fix: Fix) -> World:
    w = World()
    ken = w.add(Entity(id="Ken", kind="character", type="boy", label="Ken", role="sharer"))
    loo = w.add(Entity(id="Loo", kind="character", type="girl", label="Loo", role="helper"))
    old = w.add(Entity(id="OldStone", kind="thing", type="thing", label="the old stone sign"))
    item = w.add(Entity(id=treasure.id, kind="thing", type="thing", label=treasure.label, phrase=treasure.phrase, carries=treasure.kind))
    w.facts.update(
        ken=ken,
        loo=loo,
        place_cfg=place,
        treasure_cfg=treasure,
        fix_cfg=fix,
        old_sign=old,
        treasure_ent=item,
        risk=treasure.fragile or place.problem in {"dry", "dark"},
        chosen_fix=fix.id,
        shared=False,
        warned=False,
        fixed=False,
    )
    return w


def tell(place: Place, treasure: Treasure, fix: Fix, trait: str) -> World:
    w = build_world(place, treasure, fix)
    ken: Entity = w.facts["ken"]
    loo: Entity = w.facts["loo"]
    ken.memes["desire"] += 1
    loo.memes["care"] += 1
    ken.memes["joy"] += 1
    loo.memes["joy"] += 1

    w.say(f"Long ago, Ken and Loo came to {place.label}. {place.image.capitalize()}.")
    w.say(f"They found {treasure.phrase} and knew the place needed {place.needs}.")
    w.para()
    if place.problem == "dry":
        w.say("Ken wanted to keep the jar for himself, but Loo noticed the cracked earth by the well.")
    elif place.problem == "hungry":
        w.say("Ken wanted to guard the bread, but Loo heard children stirring near the road.")
    elif place.problem == "noisy":
        w.say("Ken wanted to carry the lantern away, but Loo saw the square growing restless.")
    else:
        w.say("Ken wanted the shells, but Loo saw how dark the shore had become.")

    w.say(f"Loo said, 'Let us {fix.plan}.'")
    propagate(w, narrate=False)

    if fix.id == "warn":
        w.say("The old sign leaned in the wind, and Ken listened.")
        w.say(f"They {fix.ending}.")
    elif fix.id == "share":
        if treasure.can_split:
            w.say("Ken broke the bread in two, and Loo handed a piece to each waiting hand.")
        else:
            w.say("They shared it by turn, each giving the other a fair chance to hold it.")
        w.say(f"In the end, they {fix.ending}.")
    elif fix.id == "trade":
        w.say("They carried the treasure to the person who needed it most.")
        w.say(f"In the end, they {fix.ending}.")
    else:
        w.say("They mended the treasure before anyone used it.")
        w.say(f"In the end, they {fix.ending}.")

    if treasure.kind == "water":
        final = "the well held water again"
    elif treasure.kind == "bread":
        final = "the village had bread enough to share"
    elif treasure.kind == "light":
        final = "the lantern shone above the path"
    else:
        final = "the shore gleamed with shells, but only after they were shared"

    w.para()
    w.say(f"At the end, {final}, and Ken and Loo stood together in the quiet light.")
    w.facts["trait"] = trait
    return w


def generation_prompts(world: World) -> list[str]:
    p: Place = world.facts["place_cfg"]
    t: Treasure = world.facts["treasure_cfg"]
    f: Fix = world.facts["fix_cfg"]
    return [
        f'Write a short myth for children about Ken and Loo at {p.label}, with "{t.label}" and a careful sharing choice.',
        f"Tell a mythic story where Ken and Loo face {p.problem} at {p.label} and solve it by {f.label}.",
        f'Write a gentle cautionary myth that uses the words "Ken" and "Loo" and ends with a clear change in the village.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Place = world.facts["place_cfg"]
    t: Treasure = world.facts["treasure_cfg"]
    f: Fix = world.facts["fix_cfg"]
    ken: Entity = world.facts["ken"]
    loo: Entity = world.facts["loo"]
    qa = [
        QAItem(
            question=f"What problem did Ken and Loo find at {p.label}?",
            answer=f"They found a {p.problem} place that needed {p.needs}. That made the treasure matter, because they had to decide how to use it wisely.",
        ),
        QAItem(
            question=f"What did Ken and Loo do with {t.label}?",
            answer=f"They worked out a way to use {t.label} for the good of the place. {f.plan.capitalize()}.",
        ),
        QAItem(
            question=f"How did Loo help Ken solve the problem?",
            answer=f"Loo noticed what the place needed and suggested a careful plan. That helped Ken stop thinking only about keeping the treasure and start thinking about the village.",
        ),
    ]
    if world.facts.get("warned"):
        qa.append(QAItem(
            question="What made them stop and be careful?",
            answer="The old stone sign and the feel of the place made them pause. They chose the safer way because they listened before acting.",
        ))
    if world.facts.get("fixed"):
        qa.append(QAItem(
            question=f"What changed by the end at {p.label}?",
            answer=f"The place was no longer stuck in its old trouble. The ending image showed that Ken and Loo's choice had made a real difference.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: Place = world.facts["place_cfg"]
    t: Treasure = world.facts["treasure_cfg"]
    out = [
        QAItem(question="What does it mean to share something?", answer="To share means to let more than one person use or enjoy the same thing. It is a kind way to make sure nobody is left out."),
        QAItem(question="What is a myth?", answer="A myth is an old story that uses big, memorable events to explain a lesson or a special feeling about the world."),
        QAItem(question=f"Why can a {t.kind} treasure need careful use?", answer="Some treasures are useful but limited, so people need to choose wisely. Careful use keeps the treasure from causing a new problem."),
        QAItem(question=f"What does {p.label_word if hasattr(p, 'label_word') else p.label} suggest in a story?", answer="A village place like that can feel important because it affects everyone. In stories, the setting often shows what the characters must solve."),
    ]
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: { {k: v for k, v in world.facts.items() if k in {'risk','shared','warned','fixed','chosen_fix'}} }")
    return "\n".join(lines)


ASP_RULES = r"""
place(pw).
treasure(tt).
fix(fx).

share_ok(tt) :- treasure(tt), can_share(tt).
trade_ok(tt) :- treasure(tt).
repair_ok(tt) :- treasure(tt).
warn_ok(tt) :- treasure(tt).

valid(Place, Treasure, Fix) :- place(Place), treasure(Treasure), fix(Fix), ok(Fix, Treasure).
ok(share, Treasure) :- can_share(Treasure).
ok(trade, Treasure) :- treasure(Treasure).
ok(repair, Treasure) :- treasure(Treasure).
ok(warn, Treasure) :- treasure(Treasure).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("problem", pid, p.problem))
        lines.append(asp.fact("needs", pid, p.needs))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.can_share:
            lines.append(asp.fact("can_share", tid))
        if t.can_split:
            lines.append(asp.fact("can_split", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
        lines.append(asp.fact("kind", tid, t.kind))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    ok = True
    if py != ax:
        ok = False
        print("MISMATCH in valid_combos()")
        print(" only python:", sorted(py - ax))
        print(" only asp:", sorted(ax - py))
    sample = resolve_params(build_parser().parse_args([]), random.Random(7))
    try:
        sample_story = generate(sample)
        _ = sample_story.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: ASP parity and smoke story generation passed ({len(py)} combos).")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic sharing storyworld for Ken and Loo.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--fix", choices=FIXES)
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
              and (args.treasure is None or c[1] == args.treasure)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treasure, _problem, fix = rng.choice(sorted(combos))
    return StoryParams(place=place, treasure=treasure, problem=PLACES[place].problem, fix=fix)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.treasure not in TREASURES or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    treasure = TREASURES[params.treasure]
    fix = FIXES[params.fix]
    if treasure.kind not in fix.handles:
        raise StoryError("That fix does not match that treasure.")
    world = tell(place, treasure, fix, trait="steady")
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
    StoryParams(place="well", treasure="waterjar", problem="dry", fix="share"),
    StoryParams(place="grove", treasure="breadbasket", problem="hungry", fix="trade"),
    StoryParams(place="village", treasure="lantern", problem="noisy", fix="warn"),
    StoryParams(place="shore", treasure="shells", problem="dark", fix="repair"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
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
