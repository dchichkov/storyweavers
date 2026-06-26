#!/usr/bin/env python3
"""
storyworlds/worlds/hole_chimp_gots_surprise_comedy.py
======================================================

A small comedy storyworld about a chimp, a hole, and a surprise.

Premise:
- A curious chimp named Niko loves snacks and shiny things.
- In the play yard, Niko finds a hole in the ground.
- The hole hides a surprise: a dropped tin cup full of bananas.

Tension:
- Niko wants to poke into the hole immediately.
- The keeper worries the hole is unsafe and that Niko will get stuck or make a bigger mess.

Turn:
- The keeper laughs, fetches a stick and a small rope, and turns the discovery into a game.
- Niko learns how to lift the surprise out without falling in.

Resolution:
- Everyone gets the bananas, the hole gets marked for repair, and the chimp's delight becomes the joke that ends the story.
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
        if self.type == "chimp":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "keeper":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the play yard"
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
class Tool:
    id: str
    label: str
    prep: str
    use: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.zone = set(self.zone)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Niko"
    keeper_name: str = "Mara"
    setting: str = "play_yard"
    surprise: str = "bananas"
    mood: str = "cheerful"


SETTINGS = {
    "play_yard": Setting(place="the play yard", affords={"dig", "discover"}),
    "sandbox": Setting(place="the sandbox corner", affords={"dig", "discover"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig",
        verb="dig around the hole",
        gerund="digging around the hole",
        rush="poke the hole with both hands",
        mess="dusty",
        soil="dusty and crooked",
        zone={"hands", "knees"},
        keyword="hole",
        tags={"hole"},
    ),
    "discover": Activity(
        id="discover",
        verb="peek into the hole",
        gerund="peeking into the hole",
        rush="lean right over the hole",
        mess="dusty",
        soil="dusty",
        zone={"hands", "head"},
        keyword="surprise",
        tags={"hole", "surprise"},
    ),
}

PRIZES = {
    "bananas": Prize(label="bananas", phrase="a little bunch of bananas", type="bananas", region="hands", plural=True),
    "cup": Prize(label="tin cup", phrase="a small tin cup", type="cup", region="hands"),
}

TOOLS = [
    Tool(id="stick", label="a long stick", prep="fetch a long stick", use="hook", guards={"dusty"}, covers={"hands"}),
    Tool(id="rope", label="a short rope", prep="grab a short rope", use="lift", guards={"dusty"}, covers={"hands"}),
]


def reason_ok(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


ASP_RULES = r"""
#show valid/2.
#show valid_story/3.
valid(A,P) :- activity(A), prize(P), prize_at_risk(A,P), has_tool(A,P).
valid_story(S,A,P) :- valid(A,P), setting(S).
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_tool(A,P) :- tool(T), guards(T,M), mess_of(A,M), covers(T,R), worn_on(P,R).
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
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for m in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, m))
        for r in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((a, p) for a in ACTIVITIES for p in PRIZES if reason_ok(ACTIVITIES[a], PRIZES[p]))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about a chimp, a hole, and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--keeper")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or rng.choice(list(PRIZES))
    if not reason_ok(ACTIVITIES[activity], PRIZES[prize]):
        raise StoryError("No valid story: the chimp's move and the surprise don't fit this hole safely.")
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(["Niko", "Pip", "Boko", "Milo"]),
        keeper_name=args.keeper or rng.choice(["Mara", "Jules", "Sana"]),
        setting=setting,
        surprise=prize,
        mood="cheerful",
    )


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} began {activity.gerund}.")


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"mess": actor.meters.get(activity.mess, 0.0), "stuck": prize.meters.get("stuck", 0.0)}


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type="chimp"))
    keeper = world.add(Entity(id=params.keeper_name, kind="character", type="keeper"))
    hole = world.add(Entity(id="hole", type="hole", label="a deep little hole"))
    surprise = world.add(Entity(id=params.surprise, type=params.surprise, label=params.surprise, phrase="the surprise"))
    world.facts.update(hero=hero, keeper=keeper, hole=hole, surprise=surprise)

    world.say(f"{hero.id} was a curious chimp who loved shiny things and snack time.")
    world.say(f"One day, {hero.id} found {hole.label} near {world.setting.place}.")
    world.say(f"Inside the hole, there was a surprise: {surprise.phrase}.")

    world.para()
    act = ACTIVITIES["discover"]
    world.say(f"{hero.id} wanted to {act.verb}, because {hero.pronoun()} thought the hole might hide treasure.")
    pred = predict(world, hero, act, surprise.id)
    if pred["mess"] >= 0:
        world.say(f"{keeper.id} laughed and said, \"Careful now, little chimp. That hole looks like trouble with a grin.\"")
    _do_activity(world, hero, act)

    world.say(f"{hero.id} leaned too close and shouted, \"I gots it!\"")
    world.say(f"That made {keeper.id} snort-laugh, because {hero.id} said it like a proud pirate.")

    world.para()
    tool = TOOLS[0]
    world.say(f"Then {keeper.id} {tool.prep} and showed {hero.id} how to {tool.use} the surprise out.")
    world.say(f"{hero.id} used the stick like a tiny hero, and the {surprise.label} came up without anyone falling in.")

    world.say(f"In the end, {hero.id} ate the bananas, {keeper.id} patched the hole, and everyone laughed at the very serious chimp voice that said, \"I gots a surprise!\"")

    world.facts.update(activity=act, setting=world.setting, prize=surprise, tool=tool, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short comedy about a chimp who finds a hole and a surprise inside.",
        f"Tell a funny story where {hero.id} says 'gots' after discovering something in a hole.",
        "Make the ending playful, with the chimp and keeper solving the hole problem kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, keeper, prize, act = f["hero"], f["keeper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} find near the play yard?",
            answer=f"{hero.id} found a hole, and inside it there was a surprise: {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did {keeper.id} laugh when {hero.id} said \"I gots it!\"?",
            answer=f"{keeper.id} laughed because {hero.id} sounded proud and funny, and the surprise still needed careful lifting out of the hole.",
        ),
        QAItem(
            question=f"How did they get the surprise out without trouble?",
            answer=f"{keeper.id} fetched a long stick, and {hero.id} used it to hook the surprise out instead of falling into the hole.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hole?",
            answer="A hole is an empty opening in the ground or in something else.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that makes people stop and look.",
        ),
        QAItem(
            question="Why can chimps be funny in stories?",
            answer="Chimps can be funny in stories because they are curious, active, and often make silly choices that lead to comic trouble.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(name="Niko", keeper_name="Mara", setting="play_yard", surprise="bananas"),
    StoryParams(name="Pip", keeper_name="Sana", setting="sandbox", surprise="cup"),
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
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 50):
            try:
                params = resolve_params(args, random.Random((args.seed or 0) + i))
            except StoryError as e:
                print(e)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
            if len(samples) >= args.n:
                break

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
