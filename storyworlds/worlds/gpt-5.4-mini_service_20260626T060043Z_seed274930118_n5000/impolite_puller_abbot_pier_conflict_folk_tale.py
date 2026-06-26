#!/usr/bin/env python3
"""
A small folk-tale storyworld about a pier, an impolite puller, and an abbot.

Premise:
A young puller at the pier keeps yanking ropes and crates without asking.
A kind abbot notices the trouble before a bigger conflict breaks out.
The tale turns when the abbot offers a calmer way to help, and the puller learns to
work with care instead of rudeness.

This world models physical meters and emotional memes, uses a reasonableness gate,
and includes an inline ASP twin for parity checks.
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
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("strain", "torn", "safe", "order"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "conflict", "pride", "rudeness", "worry", "calm", "gratitude"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"man", "boy", "abbot", "father"}
        female = {"woman", "girl", "mother", "nun", "sister"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the pier"
    affords: set[str] = field(default_factory=lambda: {"pulling", "lifting", "helping"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    strain: str
    keyword: str = "pull"
    tags: set[str] = field(default_factory=set)


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
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _is_at_risk(activity: Activity, prize: Entity) -> bool:
    return prize.region == "hands" and "hands" in activity.tags or prize.region in {"hands", "torso"}


def _select_gear(activity: Activity, prize: Entity) -> Optional[Gear]:
    for g in GEAR:
        if prize.region in g.covers and activity.risk in g.guards:
            return g
    return None


def _apply_pull(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["strain"] += 1
    actor.memes["pride"] += 1
    actor.memes["rudeness"] += 1
    if narrate:
        world.say(f"{actor.id} tugged hard at the ropes, and the pier boards creaked under the pull.")


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["strain"] < THRESHOLD:
            continue
        if actor.memes["rudeness"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        out.append(f"{actor.id}'s sharp pulling stirred up a conflict.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _apply_pull(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["torn"] >= THRESHOLD, "conflict": sim.get(actor.id).memes["conflict"]}


def tell() -> World:
    setting = Setting()
    world = World(setting)

    hero = world.add(Entity(id="Ned", kind="character", type="puller"))
    abbot = world.add(Entity(id="Abbot", kind="character", type="abbot"))
    rope = world.add(Entity(
        id="rope", type="rope", label="rope",
        owner="Ned", caretaker="Abbot", region="hands",
        phrase="a frayed rope"
    ))

    world.say("At the old pier, there lived a young puller named Ned, and he was often impolite when the work grew slow.")
    world.say("Near the water stood an abbot who watched the gulls and the tide, and he hoped the boy would learn gentler ways.")
    world.say("Ned liked to pull crates, ropes, and nets so fast that the harbor hands had no chance to speak.")

    world.para()
    world.say("One gray morning, Ned saw a heavy mooring rope and wanted it moved at once.")
    world.say("He grabbed it with both hands and yanked, though the old wood was slippery and the line was bound tight.")
    _apply_pull(world, hero, ACTIVITY, narrate=False)
    world.say("The rope snapped against the post, and the noise rang out across the pier.")
    _propagate(world, narrate=True)
    hero.memes["worry"] += 1
    abbot.memes["worry"] += 1

    world.para()
    world.say("The abbot came closer and said that a rough pull could hurt hands and crack the mast ring.")
    pred = predict_mess(world, hero, ACTIVITY, rope.id)
    world.facts["predicted_conflict"] = pred["conflict"]
    if pred["conflict"] >= THRESHOLD:
        world.say('"If you keep tugging like that," he said, "you will make a bigger quarrel than the tide itself."')
    world.say("Ned frowned, because he still wanted to be useful, but he did not want to be laughed at for his rudeness.")

    world.para()
    gear = _select_gear(ACTIVITY, rope)
    if gear is None:
        raise StoryError("No fair compromise exists for this pier conflict.")
    world.say(f'The abbot pointed to {gear.label} and said, "{gear.prep}."')
    gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    gear_ent.worn_by = hero.id
    hero.memes["calm"] += 1
    hero.memes["conflict"] = 0.0
    hero.memes["gratitude"] += 1
    world.say(f'Ned tried the kinder way. {gear.tail}.')
    world.say("This time he pulled together with the abbot, slow and steady, and the rope came loose without a fight.")
    world.say("Ned bowed his head and thanked the abbot for teaching him that help can be strong without being rude.")
    world.say("By sunset, the pier was quiet again, and Ned was known not as the impolite puller, but as a careful helper.")

    world.facts.update(hero=hero, abbot=abbot, rope=rope, gear=gear, activity=ACTIVITY, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pier": Setting(place="the pier", affords={"pulling", "lifting", "helping"}),
}

ACTIVITIES = {
    "pulling": Activity(
        id="pulling",
        verb="pull the rope",
        gerund="pulling ropes",
        rush="tug at the line",
        risk="torn",
        strain="strain",
        keyword="pull",
        tags={"rope", "hands", "tension"},
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="a pair of stout gloves",
        covers={"hands"},
        guards={"torn", "strain"},
        prep="put on a pair of stout gloves first",
        tail="walked back to the post with the gloves on",
    ),
]

CURATED = [
    # Single safe canonical tale
]


@dataclass
class StoryParams:
    place: str = "pier"
    activity: str = "pulling"
    hero_name: str = "Ned"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "rope": [("What is a rope?", "A rope is a strong cord made by twisting fibers together, and people use it for pulling or tying things.")],
    "hands": [("Why do hands get sore when you pull too hard?", "Hands can get sore because hard pulling puts a lot of strain on the muscles and skin.")],
    "tension": [("What is tension?", "Tension is a tight pulling force that makes something feel stretched and ready to snap.")],
    "gloves": [("What do gloves do?", "Gloves cover your hands and help protect them from rough work or cold weather.")],
    "pier": [("What is a pier?", "A pier is a long wooden platform that stretches out over water, where boats can come close to shore.")],
}
KNOWLEDGE_ORDER = ["pier", "rope", "hands", "tension", "gloves"]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short folk tale set on a pier about an impolite puller, an abbot, and a rope.',
        'Tell a child-friendly story where a puller makes a conflict by yanking too hard, then learns a calmer way from an abbot.',
        'Write a simple folk tale that includes a pier, a stubborn pull, and a peaceful ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    abbot: Entity = f["abbot"]
    qa = [
        QAItem(
            question="Who was the impolite puller in the story?",
            answer=f"The impolite puller was {hero.id}, the young worker on the pier who tugged too roughly at the rope.",
        ),
        QAItem(
            question="Who helped calm the conflict at the pier?",
            answer=f"The abbot helped calm the conflict by warning Ned and showing him a gentler way to work.",
        ),
        QAItem(
            question="What happened after Ned chose the kinder way?",
            answer="The rope came loose without a fight, and the pier grew quiet again because everyone worked together.",
        ),
        QAItem(
            question="Why did the abbot worry about Ned's pulling?",
            answer="He worried because hard pulling could hurt hands, snap the line, and turn a small problem into a bigger conflict.",
        ),
        QAItem(
            question="How did Ned feel at the end?",
            answer="Ned felt thankful and calmer, and he learned that helpful work does not need to be rude.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("pier")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if s:
            bits.append(f"memes={s}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), must_use_hands(A), worn_on(P,hands).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), covers(G,hands), guards(G,torn), fits(G,A,P).
valid_story(P,A) :- setting(P), activity(A), prize_at_risk(A,rope), has_fix(A,rope).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "pier"), asp.fact("activity", "pulling"), asp.fact("must_use_hands", "pulling"), asp.fact("prize", "rope"), asp.fact("worn_on", "rope", "hands"), asp.fact("gear", "gloves"), asp.fact("covers", "gloves", "hands"), asp.fact("guards", "gloves", "torn")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("pier", "pulling")} if _select_gear(ACTIVITIES["pulling"], Entity(id="rope", region="hands")) else set()
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(cl)} story).")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "pier":
        raise StoryError("This storyworld only supports the pier setting.")
    return StoryParams(place="pier", activity="pulling", hero_name=args.name or "Ned", seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell()
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld: an impolite puller, an abbot, and a conflict at the pier.")
    ap.add_argument("--place", choices=["pier"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams())]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
