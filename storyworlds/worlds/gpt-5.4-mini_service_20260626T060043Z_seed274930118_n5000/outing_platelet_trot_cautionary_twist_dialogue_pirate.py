#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/outing_platelet_trot_cautionary_twist_dialogue_pirate.py
=========================================================================================================

A small pirate-tale storyworld built from the seed words:
outing, platelet, trot.

Premise:
- A young pirate crew goes on a careful outing to a seaside cove.
- A tiny, round "platelet" charm is part of the ship's medicine kit.
- The captain wants a brisk trot along the docks, but the deck is slippery.

Narrative instruments:
- Cautionary: the captain warns about the slick boards and the fragile charm.
- Twist: the warning turns out to be about a hidden tide pool, not the charm.
- Dialogue: the story is carried by pirate talk and short spoken lines.

The world model tracks physical meters and emotional memes. The plot is driven by
a small simulated risk: if the crew trots too fast on slick planks, the platelet
charm can tumble into the sea. The safe turn is to slow down and use a rope line.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"slick": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "joy": 0.0, "alarm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cove"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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
        self.facts: dict = {}

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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "dock": Setting(place="the dock", affords={"outing", "trot"}),
    "cove": Setting(place="the cove", affords={"outing"}),
    "ship": Setting(place="the ship deck", affords={"outing", "trot"}),
}

ACTIVITIES = {
    "outing": Activity(
        id="outing",
        verb="go on the outing",
        gerund="going on the outing",
        rush="hurry across the deck",
        risk="slip into the tide",
        weather="windy",
        keyword="outing",
        tags={"outing", "pirate"},
    ),
    "trot": Activity(
        id="trot",
        verb="trot along the boards",
        gerund="trotting along the boards",
        rush="trot fast over the planks",
        risk="skid near the water",
        weather="windy",
        keyword="trot",
        tags={"trot", "pirate"},
    ),
}

PRIZES = {
    "platelet": Prize(
        label="platelet",
        phrase="a tiny red platelet charm",
        type="charm",
        region="hand",
        genders={"girl", "boy"},
    ),
    "map": Prize(
        label="map",
        phrase="a folded treasure map",
        type="map",
        region="hand",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="rope",
        label="a rope line",
        covers={"hand", "feet"},
        guards={"slip"},
        prep="tie a rope line to the rail first",
        tail="kept one hand on the rope line",
    ),
    Gear(
        id="boots",
        label="deck boots",
        covers={"feet"},
        guards={"slip"},
        prep="put on deck boots first",
        tail="stomped in the deck boots",
    ),
]

NAMES = ["Nell", "Pip", "Mara", "Jory", "Tess", "Finn"]
TRAITS = ["brave", "curious", "quick", "careful", "spry", "cheery"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    parent: str = "captain"
    seed: Optional[int] = None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "hand" and activity.id in {"outing", "trot"}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if not prize_at_risk(activity, prize):
        return None
    return GEAR[0]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(ACTIVITIES[act], prize) and select_gear(ACTIVITIES[act], prize):
                    combos.append((place, act, prize_id))
    return combos


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="pirate", label=name, memes={"worry": 0.0, "joy": 0.0, "alarm": 0.0}))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="the captain", memes={"worry": 0.0, "joy": 0.0, "alarm": 0.0}))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=captain.id, region=prize_cfg.region, plural=prize_cfg.plural))

    # Act 1
    world.say(f"{hero.id} was a {trait} little pirate who loved a bold outing by the sea.")
    world.say(f"{hero.pronoun('possessive').capitalize()} chest held {prize.phrase}, and {hero.id} wore it like a lucky prize.")
    world.para()

    # Act 2 - cautionary warning
    world.say(f"On the windy {setting.place}, {hero.id} wanted to {activity.verb}.")
    world.say(f'The captain pointed at the slick boards and said, "Mind the shine, matey. One wrong trot and {prize.label} could go overboard."')
    hero.memes["worry"] += 1
    hero.memes["alarm"] += 1
    world.say(f"{hero.id} tried to {activity.rush}, but the planks answered with a sly gleam.")
    world.para()

    # Twist: the real danger is hidden tide water, not the charm.
    world.say(f"Then a hidden tide pool flashed beside the dock, and the captain gave a second warning.")
    world.say(f'"That is the true trick, not the charm," {captain.pronoun("subject")} said. "The board near the water is the trouble."')
    gear = select_gear(activity, prize)
    if gear:
        rope = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers)))
        rope.worn_by = hero.id
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
        world.say(f'{hero.id} nodded and said, "Aye, {gear.prep}."')
        world.say(f"With the rope line ready, {hero.id} went {activity.gerund}, and the {prize.label} stayed safe in a pouch.")
        world.say(f"They {gear.tail}, and the hidden tide lapped at the wood without taking anything.")
        hero.memes["joy"] += 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short pirate tale for children that includes the word "{act.keyword}" and the word "{prize.label}".',
        f"Tell a cautionary pirate story where {hero.id} wants to {act.verb} but a captain warns about {prize.phrase}.",
        f"Write a dialogue-filled story about a seaside outing with a twist and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    prize = f["prize"]
    act = f["activity"]
    gear = f.get("gear")
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the outing?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the captain warn {hero.id} about the board?",
            answer=f"The captain warned {hero.id} because the dock was slick, and {prize.label} could have gone overboard during the trot.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The hidden tide pool was the real danger, not the platelet charm itself.",
        ),
        QAItem(
            question="How did the pirate crew stay safe?",
            answer=f"They used {gear.label} and kept one hand on the rope line while they moved carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a platelet?",
            answer="A platelet is a tiny blood cell that helps stop bleeding by making clots.",
        ),
        QAItem(
            question="What does cautionary mean in a story?",
            answer="Cautionary means the story gives a warning so someone can avoid danger.",
        ),
        QAItem(
            question="What is a trot?",
            answer="A trot is a quick, light way of moving faster than a walk but not as fast as a run.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} worn_by={e.worn_by} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="dock", activity="outing", prize="platelet", name="Nell", trait="careful"),
    StoryParams(place="ship", activity="trot", prize="platelet", name="Pip", trait="spry"),
    StoryParams(place="cove", activity="outing", prize="map", name="Mara", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with caution, twist, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
        raise StoryError("(No valid pirate outing matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.trait)
    hero = next(e for e in world.entities.values() if e.id == params.name)
    captain = world.get("Captain")
    prize = world.get("prize")
    gear = next((e for e in world.entities.values() if e.protective), None)
    world.facts = {"hero": hero, "captain": captain, "prize": prize, "activity": ACTIVITIES[params.activity], "prize_cfg": PRIZES[params.prize], "gear": gear}
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


ASP_RULES = r"""
place(dock).
place(cove).
place(ship).

activity(outing).
activity(trot).

prize(platelet).
prize(map).

affords(dock,outing).
affords(dock,trot).
affords(cove,outing).
affords(ship,outing).
affords(ship,trot).

worn_on(platelet,hand).
worn_on(map,hand).

splashes(outing,hand).
splashes(trot,hand).

gear(rope).
gear(boots).
guards(rope,slip).
guards(boots,slip).
covers(rope,hand).
covers(rope,feet).
covers(boots,feet).

prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,slip), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("splashes", aid, "hand"))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
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
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
