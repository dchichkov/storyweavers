#!/usr/bin/env python3
"""
storyworlds/worlds/reindeer_delicious_minimize_twist_cautionary_folk_tale.py
============================================================================

A small folk-tale storyworld about a careful winter gift: a child and a reindeer
share something delicious, learn to minimize waste, and meet a twist that turns
a cautionary moment into a kinder ending.

The domain is intentionally tiny and state-driven. Physical meters track hunger,
warmth, crumbs, and frost. Emotional memes track delight, caution, worry, trust,
and relief. The simulated world decides whether the gift is shared wisely or
spilled by a twist in the path.

Seed image:
---
A child meets a reindeer by the lane and offers a delicious oat cake. The
reindeer is eager, but a patch of ice and a greedy handful can make the treat
vanish too fast. A wiser choice minimizes waste, and the tale ends with the
reindeer licking a clean bowl under the lantern glow.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    deliciousness: int
    crumbly: bool = False
    messy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    phrase: str
    risk: str
    prevents: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    minimizes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    treat: str
    twist: str
    aid: str
    child: str
    child_type: str
    reindeer: str
    reindeer_type: str
    seed: Optional[int] = None


SETTINGS = {
    "lantern_lane": Setting(place="the lantern lane", indoor=False, affordances={"share"}),
    "barn_door": Setting(place="the barn door", indoor=False, affordances={"share"}),
    "snow_kitchen": Setting(place="the snowy kitchen", indoor=True, affordances={"share"}),
}

TREATS = {
    "oat_cake": Treat(id="oat_cake", label="oat cake", phrase="a delicious oat cake", deliciousness=3, crumbly=True, messy=True, tags={"delicious", "cake"}),
    "honey_apple": Treat(id="honey_apple", label="honey apple", phrase="a delicious honey apple", deliciousness=2, crumbly=False, messy=True, tags={"delicious", "apple"}),
    "berry_bun": Treat(id="berry_bun", label="berry bun", phrase="a warm berry bun", deliciousness=2, crumbly=True, messy=True, tags={"delicious", "bun"}),
}

TWISTS = {
    "ice_patch": Twist(id="ice_patch", label="ice patch", phrase="a slick patch of ice", risk="slip", prevents={"rushing"}, tags={"twist", "ice"}),
    "snow_drift": Twist(id="snow_drift", label="snow drift", phrase="a deep snow drift", risk="slow", prevents={"running"}, tags={"twist", "snow"}),
    "wind_gust": Twist(id="wind_gust", label="wind gust", phrase="a sudden gust of wind", risk="spill", prevents={"holding_loose"}, tags={"twist", "wind"}),
}

AIDS = {
    "small_bowl": Aid(id="small_bowl", label="small bowl", phrase="a small bowl", minimizes={"spill", "crumbs"}, tags={"minimize", "bowl"}),
    "napkin": Aid(id="napkin", label="napkin", phrase="a folded napkin", minimizes={"crumbs"}, tags={"minimize", "napkin"}),
    "steady_hand": Aid(id="steady_hand", label="steady hand", phrase="a steady hand", minimizes={"spill"}, tags={"minimize", "hand"}),
}

GIRL_NAMES = ["Mira", "Elsa", "Nina", "Tove", "Ada", "Lina"]
BOY_NAMES = ["Ivo", "Oren", "Bram", "Pekka", "Sven", "Niko"]
REINDEER_NAMES = ["Runa", "Hearth", "Moss", "Snow", "Pine"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "share" not in setting.affordances:
            continue
        for treat_id, treat in TREATS.items():
            for twist_id, twist in TWISTS.items():
                for aid_id, aid in AIDS.items():
                    if treat.messy and ({"spill", "crumbs"} & aid.minimizes):
                        combos.append((place, treat_id, twist_id, aid_id))
    return combos


def _is_valid_combo(place: str, treat: str, twist: str, aid: str) -> bool:
    return (place, treat, twist, aid) in valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about reindeer, delicious treats, and minimizing waste.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--reindeer")
    ap.add_argument("--reindeer-type", choices=["reindeer"])
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
              and (args.treat is None or c[1] == args.treat)
              and (args.twist is None or c[2] == args.twist)
              and (args.aid is None or c[3] == args.aid)]
    if not combos:
        raise StoryError("No valid story matches the chosen filters.")
    place, treat, twist, aid = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    reindeer = args.reindeer or rng.choice(REINDEER_NAMES)
    return StoryParams(
        place=place,
        treat=treat,
        twist=twist,
        aid=aid,
        child=child,
        child_type=child_type,
        reindeer=reindeer,
        reindeer_type="reindeer",
    )


def propagate(world: World) -> None:
    child = world.get("child")
    reindeer = world.get("reindeer")
    treat = world.get("treat")
    aid = world.get("aid")
    if child.meters["sharing"] >= THRESHOLD and aid.label == "small bowl":
        if "spill" not in world.fired:
            world.fired.add(("minimize",))
            treat.meters["spilled"] = max(0.0, treat.meters.get("spilled", 0.0) - 1.0)
            child.memes["relief"] += 1
            reindeer.memes["delight"] += 1


def tell(params: StoryParams) -> World:
    if not _is_valid_combo(params.place, params.treat, params.twist, params.aid):
        raise StoryError("Invalid story combination.")
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child, meters={"kindness": 0.0, "sharing": 0.0}, memes={"caution": 0.0, "delight": 0.0, "relief": 0.0}, attrs={"name": params.child}))
    reindeer = world.add(Entity(id="reindeer", kind="character", type="reindeer", label=params.reindeer, meters={"hunger": 0.0, "warmth": 1.0}, memes={"trust": 0.0, "delight": 0.0, "worry": 0.0}, attrs={"name": params.reindeer}, tags={"reindeer"}))
    treat = world.add(Entity(id="treat", type="treat", label=TREATS[params.treat].label, meters={"crumbs": 0.0, "spilled": 0.0}, memes={"delight": 0.0}, attrs={"phrase": TREATS[params.treat].phrase}))
    twist = world.add(Entity(id="twist", type="twist", label=TWISTS[params.twist].label, attrs={"phrase": TWISTS[params.twist].phrase, "risk": TWISTS[params.twist].risk}, tags={"twist"}))
    aid = world.add(Entity(id="aid", type="aid", label=AIDS[params.aid].label, attrs={"phrase": AIDS[params.aid].phrase}, tags={"minimize"}))
    world.facts.update(child=child, reindeer=reindeer, treat=treat, twist=twist, aid=aid, params=params)

    world.say(f"On a winter morning, {child.label} met {reindeer.label} by {world.setting.place}.")
    world.say(f"{child.label.capitalize()} held up {treat.attrs['phrase']}, and the reindeer sniffed it as if it were a treasure from the king's table.")

    world.para()
    world.say(f"Then the twist came: {twist.attrs['phrase']} hid along the path, and the {twist.label} made the trail tricky.")
    child.memes["caution"] += 1
    world.say(f"{child.label.capitalize()} remembered that a wise hand should {AIDS[params.aid].phrase.split()[-2]} {treat.label} and minimize waste.")

    if params.twist == "ice_patch":
        world.say(f"The ice patch made quick steps risky, so {child.label} slowed down and kept the bowl steady.")
    elif params.twist == "snow_drift":
        world.say(f"The snow drift rose high, so {child.label} took smaller steps and held the treat close.")
    else:
        world.say(f"The wind gust tugged at the smell of the treat, so {child.label} cupped it with both hands.")

    child.meters["sharing"] += 1
    reindeer.meters["hunger"] += 1
    reindeer.memes["trust"] += 1
    treat.memes["delight"] += 1
    if params.aid == "small_bowl":
        world.say(f"{child.label.capitalize()} set the delicious treat in {aid.attrs['phrase']}, and not a crumb slipped away.")
    elif params.aid == "napkin":
        world.say(f"{child.label.capitalize()} wrapped the treat in {aid.attrs['phrase']}, which kept most of the crumbs together.")
        treat.meters["crumbs"] += 1
    else:
        world.say(f"{child.label.capitalize()} used {aid.attrs['phrase']} to carry the treat, and the holding stayed steady.")
    propagate(world)

    world.para()
    if params.aid == "small_bowl":
        world.say(f"In the end, the reindeer licked the clean bowl, and {child.label} smiled at how little was wasted.")
    else:
        world.say(f"In the end, the reindeer still ate well, and {child.label} gathered the few crumbs left on the snow for a sparrow.")
    world.say(f"The folk tale ended with a warm lantern glow, a kind heart, and a clever way to minimize the loss of something delicious.")
    return world


def story_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short folk tale about {p.child} and a reindeer sharing something delicious by {world.setting.place}, with a twist that teaches how to minimize waste.",
        f"Tell a gentle cautionary story where {p.child} offers {TREATS[p.treat].phrase} to a reindeer and chooses a careful way to carry it through {TWISTS[p.twist].phrase}.",
        f"Write a small winter story that includes a reindeer, the word delicious, and the idea of minimize, ending with a wise, tidy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    reindeer = world.facts["reindeer"]
    treat = world.facts["treat"]
    twist = world.facts["twist"]
    aid = world.facts["aid"]
    return [
        QAItem(question=f"Who shared a treat with the reindeer at {world.setting.place}?", answer=f"{child.label} shared {treat.attrs['phrase']} with {reindeer.label}. They met by {world.setting.place}, and the story follows how they kept it from going to waste."),
        QAItem(question=f"What twist made the path tricky?", answer=f"The twist was {twist.attrs['phrase']}. It made the lane slippery or hard to cross, so {child.label} had to be careful."),
        QAItem(question=f"How did {child.label} minimize waste?", answer=f"{child.label} used {aid.label_word if hasattr(aid, 'label_word') else aid.label} to carry the treat carefully. That kept most of the delicious food together and left very little behind."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a reindeer?", answer="A reindeer is a deer that lives in cold places. It has strong legs for walking in snow and often helps folk-tale travelers in winter."),
        QAItem(question="What does delicious mean?", answer="Delicious means very tasty. People say food is delicious when they really enjoy eating it."),
        QAItem(question="What does minimize mean?", answer="Minimize means make something as small as possible. If you minimize waste, you try not to leave much behind."),
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs} tags={sorted(e.tags)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="lantern_lane", treat="oat_cake", twist="ice_patch", aid="small_bowl", child="Mira", child_type="girl", reindeer="Runa", reindeer_type="reindeer"),
    StoryParams(place="barn_door", treat="honey_apple", twist="wind_gust", aid="napkin", child="Bram", child_type="boy", reindeer="Hearth", reindeer_type="reindeer"),
    StoryParams(place="snow_kitchen", treat="berry_bun", twist="snow_drift", aid="steady_hand", child="Nina", child_type="girl", reindeer="Pine", reindeer_type="reindeer"),
]


ASP_RULES = r"""
valid(P,T,W,A) :- place(P), treat(T), twist(W), aid(A), treat_messy(T), aid_min(A, spill).
valid(P,T,W,A) :- place(P), treat(T), twist(W), aid(A), treat_messy(T), aid_min(A, crumbs).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t, obj in TREATS.items():
        lines.append(asp.fact("treat", t))
        if obj.messy:
            lines.append(asp.fact("treat_messy", t))
    for w in TWISTS:
        lines.append(asp.fact("twist", w))
    for a, obj in AIDS.items():
        lines.append(asp.fact("aid", a))
        for m in sorted(obj.minimizes):
            lines.append(asp.fact("aid_min", a, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH")
        print("only python:", sorted(py - asp_set))
        print("only asp:", sorted(asp_set - py))
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story:
        return 1
    print(f"OK: {len(py)} combos; story generation works.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(args.n)] if not args.all else [generate(p) for p in CURATED]
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
