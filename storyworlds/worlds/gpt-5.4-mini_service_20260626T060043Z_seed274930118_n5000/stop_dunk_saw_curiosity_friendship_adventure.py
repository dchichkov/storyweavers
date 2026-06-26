#!/usr/bin/env python3
"""
A standalone storyworld for a small adventure about Curiosity, Friendship,
and a risky dunk that must be stopped before things go wrong.

Premise:
- A curious child sees something interesting at a little water place.
- The child wants to dunk a treasured item to find out what happens.
- A friend notices the danger and helps stop the choice.
- They choose a safer adventure instead, ending with curiosity satisfied and
  friendship stronger.

This world is intentionally small, state-driven, and constraint-checked.
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
# World model
# ---------------------------------------------------------------------------
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("wet", 0.0)
        self.meters.setdefault("broken", 0.0)
        self.meters.setdefault("dirty", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("friendship", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("relief", 0.0)
        self.memes.setdefault("joy", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class SafeChoice:
    id: str
    label: str
    verb: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

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
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "stream": Setting(place="the stream", affords={"dunk", "splash"}),
    "pond": Setting(place="the pond", affords={"dunk", "splash"}),
    "shore": Setting(place="the shore", affords={"dunk", "splash"}),
}

ACTIVITIES = {
    "dunk": Activity(
        id="dunk",
        verb="dunk the curious trinket in the water",
        gerund="dunking the curious trinket",
        rush="rush to dunk the curious trinket",
        mess="wet",
        soil="soaked",
        zone={"hands"},
        keyword="dunk",
        tags={"water", "wet", "dunk"},
    ),
    "splash": Activity(
        id="splash",
        verb="splash in the water",
        gerund="splashing in the water",
        rush="run to splash in the water",
        mess="wet",
        soil="wet",
        zone={"hands", "feet"},
        keyword="splash",
        tags={"water", "wet"},
    ),
}

PRIZES = {
    "book": Prize(
        label="book",
        phrase="a small paper map book",
        type="book",
        region="hands",
    ),
    "sketchpad": Prize(
        label="sketchpad",
        phrase="a neat sketchpad",
        type="sketchpad",
        region="hands",
    ),
    "lantern": Prize(
        label="lantern",
        phrase="a little lantern with a bright glass",
        type="lantern",
        region="hands",
    ),
}

SAFE_CHOICES = {
    "look": SafeChoice(
        id="look",
        label="look more closely from the bank",
        verb="look more closely",
        ending="stood on the bank and studied the water together",
    ),
    "bridge": SafeChoice(
        id="bridge",
        label="cross the little bridge first",
        verb="cross the little bridge",
        ending="walked to the bridge and watched the stream from above",
    ),
    "stones": SafeChoice(
        id="stones",
        label="skip pebbles instead",
        verb="skip pebbles",
        ending="skipped pebbles and laughed at the rings on the water",
    ),
}

GIRL_NAMES = ["Ava", "Mina", "Luna", "Ivy", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Noah", "Finn", "Eli", "Theo"]
TRAITS = ["curious", "brave", "gentle", "quick", "bright", "bold"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk if the activity splashes the region it is held in.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% A compatible fix must be safe for the same risk region and the mess kind.
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).

has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    # gear catalog
    lines.append(asp.fact("gear", "towel"))
    lines.append(asp.fact("guards", "towel", "wet"))
    lines.append(asp.fact("covers", "towel", "hands"))
    lines.append(asp.fact("gear", "boots"))
    lines.append(asp.fact("guards", "boots", "wet"))
    lines.append(asp.fact("covers", "boots", "feet"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place, act_id, prize_id))
    return combos


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
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def predict_dunk(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"wet": prize.meters["wet"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    if narrate:
        world.say(f"{actor.id} did {activity.gerund}.")


def _rule_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet.")
    return out


def _rule_worry(world: World) -> list[str]:
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    prize = world.facts.get("prize")
    if not hero or not friend or not prize:
        return []
    if friend.memes["worry"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        return [f"{friend.id} worried about the {prize.label}."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_soak, _rule_worry):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    friend = world.add(Entity(id="Friend", kind="character", type="girl", meters={}, memes={}))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=friend.id, region=prize_cfg.region
    ))
    prize.worn_by = hero.id

    world.facts.update(hero=hero, friend=friend, prize=prize, activity=activity, setting=setting)

    world.say(f"{hero.id} was a {trait} little {gender} who loved adventure and new paths.")
    world.say(f"{hero.id} also had a strong case of curiosity, and {hero.pronoun('possessive')} eyes liked to wander.")
    world.say(f"One day, {hero.id} and {friend.id} went to {setting.place}.")
    world.para()

    world.say(f"{hero.id} saw the water sparkle, and that sight made {hero.pronoun('possessive')} curiosity grow.")
    world.say(f"{hero.id} wanted to {activity.verb}, even though {hero.pronoun('possessive')} {prize.label} was in hand.")
    pred = predict_dunk(world, hero, activity, prize.id)
    if pred["wet"]:
        friend.memes["worry"] += 1
        world.say(f"{friend.id} saw the trouble right away and said, \"Stop! Your {prize.label} will get soaked.\"")
        world.say(f"{hero.id} paused, because {friend.id}'s voice was full of friendship, not bossiness.")
    else:
        world.say(f"{friend.id} smiled, but the plan still felt too wild for the day.")

    world.para()
    safe = SAFE_CHOICES["look"] if activity.id == "dunk" else SAFE_CHOICES["stones"]
    friend.memes["friendship"] += 1
    hero.memes["friendship"] += 1
    hero.memes["curiosity"] += 1
    friend.memes["relief"] += 1

    world.say(f"Together they chose to {safe.label}.")
    world.say(f"They {safe.ending}.")
    world.say(f"{hero.id} learned what the water looked like without risking the {prize.label}, and {friend.id} stayed glad.")
    world.say(f"By the end, curiosity was answered, friendship felt stronger, and the little adventure still felt exciting.")
    world.facts["safe"] = safe
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, prize = f["hero"], f["friend"], f["activity"], f["prize"]
    return [
        f"Write a child-friendly adventure story where {hero.id} wants to {act.verb} and {friend.id} stops the choice in time.",
        f"Tell a short story with the words curiosity and friendship, set at {f['setting'].place}, with a risky {act.id}.",
        f"Write a gentle adventure where a child sees the water, hears a warning to stop, and chooses a safer way to explore.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act, safe = f["hero"], f["friend"], f["prize"], f["activity"], f["safe"]
    return [
        QAItem(
            question=f"Why did {friend.id} tell {hero.id} to stop at the water?",
            answer=f"{friend.id} stopped {hero.id} because {hero.id} wanted to {act.verb}, and that would have made the {prize.label} get soaked.",
        ),
        QAItem(
            question=f"What did {hero.id} choose to do instead of {act.verb}?",
            answer=f"{hero.id} and {friend.id} chose to {safe.label}, so they could keep the day safe and still enjoy the adventure.",
        ),
        QAItem(
            question=f"How did the story end for the {prize.label}?",
            answer=f"The {prize.label} stayed safe and dry because {hero.id} stopped before the dunk and chose a safer path.",
        ),
        QAItem(
            question=f"How did curiosity and friendship matter in the story?",
            answer=f"Curiosity pushed {hero.id} toward the water, and friendship helped {friend.id} stop the risky choice in a kind way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes someone want to know more, look closer, or ask questions.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other and help one another.",
        ),
    ]
    if world.facts["activity"].id == "dunk":
        out.append(
            QAItem(
                question="Why can water be risky for paper things?",
                answer="Water can soak paper, make it soft, and ruin things like maps, books, and drawings.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"{e.id}: ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and interface
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: curiosity, friendship, and a stopped dunk.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr):
            raise StoryError("No story: that prize would not be at risk in that activity.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in PRIZES[prize].genders:
        raise StoryError("Chosen prize does not fit the requested gender.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.trait)
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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("stream", "dunk", "book", "Mina", "girl", "curious"),
            StoryParams("pond", "dunk", "sketchpad", "Leo", "boy", "brave"),
            StoryParams("shore", "splash", "lantern", "Ivy", "girl", "bright"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
