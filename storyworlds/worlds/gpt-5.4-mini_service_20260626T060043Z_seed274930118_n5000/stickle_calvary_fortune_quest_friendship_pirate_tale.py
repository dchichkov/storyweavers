#!/usr/bin/env python3
"""
storyworlds/worlds/stickle_calvary_fortune_quest_friendship_pirate_tale.py
============================================================================

A small pirate-tale story world about a brave little seeker, a real quest,
and the kind of friendship that matters more than any fortune.

Seed premise:
---
A tiny pirate named Stickle hears about a hidden fortune in the blue cove.
Stickle wants the treasure, but the map leads through rough water and a lonely
island where a friend can either help or be left behind. The story turns when
Stickle chooses friendship first, and the fortune becomes the thing they share
instead of the thing they chase alone.

World model:
---
    hero.courage rises when the quest begins
    hero.worry rises when the route looks hard
    friend.trust rises when help is offered and accepted
    fortune.value stays high, but its meaning changes after the turn
    if the hero abandons a friend, worry and loneliness rise
    if the hero shares the prize, friendship settles the end image

This file follows the Storyweavers contract:
- one standalone stdlib script
- lazy ASP helper import
- StoryParams, registries, parser, resolve_params, generate, emit, main
- physical meters and emotional memes in the simulated state
- story-driven prose with a stateful beginning, middle, turn, and ending

The required seed words are included in the world:
- stickle
- calvary
- fortune
- Quest
- Friendship
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"weight": 0.0, "distance": 0.0, "risk": 0.0, "value": 0.0}
        if not self.memes:
            self.memes = {"courage": 0.0, "worry": 0.0, "trust": 0.0, "joy": 0.0, "lonely": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    sea: str
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
    value_name: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class FriendGift:
    id: str
    label: str
    phrase: str
    helps: set[str]
    required_place: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


def safe_title(name: str) -> str:
    return name[:1].upper() + name[1:]


def _step(world: World, actor: Entity, meters: dict[str, float] | None = None, memes: dict[str, float] | None = None) -> None:
    if meters:
        for k, v in meters.items():
            actor.meters[k] = actor.meters.get(k, 0.0) + v
    if memes:
        for k, v in memes.items():
            actor.memes[k] = actor.memes.get(k, 0.0) + v


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("distance", 0.0) < THRESHOLD or actor.meters.get("risk", 0.0) < THRESHOLD:
            continue
        sig = ("strain", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"The salty route grew hard, and {actor.id} swallowed a worried breath.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    if hero.memes.get("trust", 0.0) < THRESHOLD or friend.memes.get("trust", 0.0) < THRESHOLD:
        return out
    sig = ("friendship", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    out.append("Their Friendship warmed the deck like lantern light.")
    return out


CAUSAL_RULES = [
    _r_strain,
    _r_friendship,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_route(world: World, hero: Entity, activity: Activity, prize: Prize) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    chest = sim.get(prize.label)
    return {
        "risk": chest.meters.get("risk", 0.0),
        "worry": sim.get(hero.id).memes.get("worry", 0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["distance"] = actor.meters.get("distance", 0.0) + 1
    actor.meters["risk"] = actor.meters.get("risk", 0.0) + 1
    actor.memes["courage"] = actor.memes.get("courage", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little pirate with a quick grin and a brave heart.")
    world.say(f"{hero.id} loved the sound of the sea and the promise of a Quest.")


def quest_begins(world: World, hero: Entity, activity: Activity, prize: Prize) -> None:
    world.say(
        f"One bright morning, {hero.id} spotted a torn map that pointed toward the blue cove."
    )
    world.say(
        f"It promised a {prize.value_name}, so {hero.id} wanted to {activity.verb} at once."
    )


def warning(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Prize) -> None:
    pred = predict_route(world, hero, activity, prize)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{friend.id} frowned and said, \"That path is rough, and the sea can steal a prize.\""
    )
    world.say(
        f"{hero.id} looked at the water, and the thought of the {prize.label} made {hero.id} hesitate."
    )
    world.facts["predicted_risk"] = pred["risk"]


def choose_friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0.0) + 1
    world.say(
        f"Then {hero.id} remembered Friendship is better than a lonely chest of gold."
    )
    world.say(
        f'{hero.id} said, "Come with me, {friend.id}. We can look together and keep each other safe."'
    )


def finish_quest(world: World, hero: Entity, friend: Entity, prize: Prize, gift: FriendGift) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(
        f"They used {gift.label} to follow the map, and soon the hidden cove opened wide before them."
    )
    world.say(
        f"There sat the {prize.label}, bright as sunrise, but {hero.id} did not grab it alone."
    )
    world.say(
        f"{hero.id} and {friend.id} split the fortune, laughed together, and sailed home side by side."
    )


SETTINGS = {
    "harbor": Setting(place="the harbor", sea="calm sea", affords={"quest"}),
    "cove": Setting(place="the blue cove", sea="bright sea", affords={"quest"}),
    "island": Setting(place="the lonely island", sea="windy sea", affords={"quest"}),
}

ACTIVITIES = {
    "quest": Activity(
        id="quest",
        verb="set out on the Quest for the fortune",
        gerund="searching for the fortune",
        rush="sail after the map",
        risk="rough water and hidden rocks",
        weather="breezy",
        keyword="Quest",
        tags={"quest", "fortune"},
    ),
    "gather": Activity(
        id="gather",
        verb="gather clues for the Quest",
        gerund="gathering clues",
        rush="hunt for signs",
        risk="fog and long turns",
        weather="foggy",
        keyword="Quest",
        tags={"quest"},
    ),
}

PRIZES = {
    "fortune": Prize(
        label="fortune",
        phrase="a chest of fortune",
        type="treasure",
        value_name="fortune",
        genders={"girl", "boy"},
    ),
    "map": Prize(
        label="map",
        phrase="a tattered map",
        type="paper",
        value_name="route",
        genders={"girl", "boy"},
    ),
}

GIFTS = [
    FriendGift(
        id="lantern",
        label="a lantern",
        phrase="a small lantern",
        helps={"quest"},
        required_place={"harbor", "cove", "island"},
    ),
    FriendGift(
        id="rope",
        label="a rope",
        phrase="a strong rope",
        helps={"quest"},
        required_place={"cove", "island"},
    ),
    FriendGift(
        id="snack",
        label="a snack sack",
        phrase="a little sack of snacks",
        helps={"quest"},
        required_place={"harbor", "cove", "island"},
    ),
]

NAMES = ["Stickle", "Pip", "Nori", "Milo", "Tessa", "Jory"]
FRIEND_NAMES = ["Calvary", "Lina", "Bram", "Sailor Jo", "Mina"]
TRAITS = ["bold", "quick", "cheerful", "curious"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                if act_id == "quest" and prize_id == "fortune":
                    combos.append((place, act_id, prize_id))
                if act_id == "gather" and prize_id == "map":
                    combos.append((place, act_id, prize_id))
    return combos


def choose_gift(setting: Setting, activity: Activity) -> Optional[FriendGift]:
    for gift in GIFTS:
        if activity.id in gift.helps and setting.place.split()[-1] or True:
            return gift
    return GIFTS[0]


def make_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type="boy", traits=[params.trait, "little"]))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl"))
    prize = world.add(Entity(id=params.prize, type="treasure", label=params.prize, phrase=PRIZES[params.prize].phrase))
    world.facts.update(hero=hero, friend=friend, prize=prize, activity=ACTIVITIES[params.activity], setting=world.setting)
    intro(world, hero)
    world.para()
    quest_begins(world, hero, ACTIVITIES[params.activity], PRIZES[params.prize])
    warning(world, hero, friend, ACTIVITIES[params.activity], PRIZES[params.prize])
    world.para()
    choose_friendship(world, hero, friend)
    gift = choose_gift(world.setting, ACTIVITIES[params.activity])
    if gift is None:
        raise StoryError("No friendly tool fits this quest.")
    _do_activity(world, hero, ACTIVITIES[params.activity], narrate=True)
    finish_quest(world, hero, friend, PRIZES[params.prize], gift)
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, act.keyword))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("value_name", pid, prize.value_name))
    for gift in GIFTS:
        lines.append(asp.fact("gift", gift.id))
        for act in sorted(gift.helps):
            lines.append(asp.fact("helps", gift.id, act))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Prize) :- affords(Place, Act), activity(Act), prize(Prize),
                            Act = quest, Prize = fortune.
valid(Place, Act, Prize) :- affords(Place, Act), activity(Act), prize(Prize),
                            Act = gather, Prize = map.
friendly_tool(Gift, Act) :- gift(Gift), helps(Gift, Act).
compatible_story(Place, Act, Prize, Gift) :- valid(Place, Act, Prize), friendly_tool(Gift, Act).
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
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world about a Quest and Friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
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
        if (args.activity, args.prize) not in {("quest", "fortune"), ("gather", "map")}:
            raise StoryError("That quest and prize do not fit this pirate tale.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, friend=friend, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child about {f["hero"].id}, a Quest, and Friendship.',
        f"Tell a gentle sea story where {f['hero'].id} chases a {f['prize'].label} but chooses friendship first.",
        f'Write a story that includes the words "stickle", "calvary", and "fortune" in a pirate adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    prize = world.facts["prize"]
    return [
        QAItem(
            question=f"Who went on the Quest for the fortune?",
            answer=f"{hero.id} went on the Quest, and {friend.id} went with {hero.id} as a true friend.",
        ),
        QAItem(
            question=f"What did {hero.id} learn mattered more than the {prize.label}?",
            answer="Friendship mattered more than the treasure, so the hero chose to share the journey instead of chasing the prize alone.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} end the story?",
            answer=f"They ended by sharing the fortune and sailing home together with happy hearts.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or search for something important, often with a goal to reach or a problem to solve.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who help, care, and trust each other.",
        ),
        QAItem(
            question="What is fortune in a pirate tale?",
            answer="Fortune usually means treasure, gold, or valuable things that a pirate might find on an adventure.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.kind:8}) meters={{{', '.join(f'{k}: {round(v, 2)}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {round(v, 2)}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", activity="quest", prize="fortune", name="Stickle", friend="Calvary", trait="bold"),
    StoryParams(place="cove", activity="quest", prize="fortune", name="Stickle", friend="Lina", trait="curious"),
    StoryParams(place="island", activity="gather", prize="map", name="Pip", friend="Calvary", trait="cheerful"),
]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    world.weather = "breezy"
    world = make_story(world, params)
    story_text = world.render()
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("#show valid/3.\n#show compatible_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/4."))
        tuples = sorted(set(asp.atoms(model, "compatible_story")))
        for t in tuples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} with {p.friend}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
