#!/usr/bin/env python3
"""
Story world: motel_bad_ending_friendship_transformation_slice_of

A small slice-of-life storyworld about a roadside motel, a brief friendship,
and a transformation that leaves a sad ending image behind.

Premise used to shape the world:
- A child and caregiver stop at a motel for one night.
- The child feels lonely, then meets another child in the hallway/lobby.
- They share a small game and transform an ordinary motel item into something
  special together.
- Morning comes too fast. The friend is gone, leaving the hero changed but sad.

The story model tracks both physical state (meters) and emotional state (memes).
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
# World data
# ---------------------------------------------------------------------------

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_plural(self) -> bool:
        return self.plural


@dataclass
class Setting:
    place: str = "the motel"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    emotion: str
    keyword: str
    turns: set[str] = field(default_factory=set)  # what can transform into what
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    value: str
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    caregiver: str
    seed: Optional[int] = None


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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "motel": Setting(place="the roadside motel", affordances={"quiet_play", "paper_game", "lobby_visit"}),
}

ACTIVITIES = {
    "quiet_play": Activity(
        id="quiet_play",
        verb="play quietly in the hall",
        gerund="playing quietly in the hall",
        mess="stillness",
        emotion="lonely to hopeful",
        keyword="hall",
        turns={"lonely": "hopeful"},
        tags={"motel", "friendship"},
    ),
    "paper_game": Activity(
        id="paper_game",
        verb="make a paper map",
        gerund="making a paper map",
        mess="paper scraps",
        emotion="lonely to proud",
        keyword="map",
        turns={"ordinary": "special"},
        tags={"motel", "transformation"},
    ),
    "lobby_visit": Activity(
        id="lobby_visit",
        verb="sit by the lobby window",
        gerund="sitting by the lobby window",
        mess="waiting",
        emotion="lonely to thoughtful",
        keyword="window",
        turns={"lonely": "thoughtful"},
        tags={"motel", "slice_of_life"},
    ),
}

PRIZES = {
    "keytag": Prize(
        label="key tag",
        phrase="a plain plastic key tag from the front desk",
        type="keytag",
        value="important",
    ),
    "postcard": Prize(
        label="postcard",
        phrase="a free postcard with the motel's neon sign on it",
        type="postcard",
        value="small",
    ),
    "map": Prize(
        label="road map",
        phrase="a folded road map from the glove box",
        type="map",
        value="useful",
    ),
}

NAMES = {
    "girl": ["Maya", "Nina", "Ella", "June", "Tara"],
    "boy": ["Theo", "Owen", "Ben", "Milo", "Noah"],
}
CAREGIVERS = ["mother", "father", "aunt", "uncle"]

TRAITS = ["quiet", "shy", "careful", "curious", "soft-spoken"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for act_id in setting.affordances:
            for prize_id in PRIZES:
                combos.append((setting_id, act_id, prize_id))
    return combos


def invalid_reason(act: Activity, prize: Prize) -> str:
    return f"(No story: {act.verb} doesn't reasonably transform a {prize.label} in this motel slice.)"


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES[gender])


def transform_label(activity: Activity, prize: Prize) -> str:
    if activity.id == "paper_game" and prize.type == "map":
        return "a treasure map"
    if activity.id == "paper_game" and prize.type == "keytag":
        return "a lucky tag"
    if activity.id == "quiet_play" and prize.type == "postcard":
        return "a keepsake postcard"
    return prize.phrase


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, caregiver: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"loneliness": 1.0, "curiosity": 1.0}))
    adult = world.add(Entity(id="Caregiver", kind="character", type=caregiver, label=f"their {caregiver}", meters={}, memes={}))
    friend = world.add(Entity(id="Friend", kind="character", type="boy", label="the other child", meters={}, memes={"shyness": 1.0}))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=adult.id,
    ))

    transformed_label = transform_label(activity, prize_cfg)

    # Setup
    world.say(
        f"{child.id} and {adult.label} stopped at {setting.place} after a long drive."
    )
    world.say(
        f"The room was clean but small, with thin curtains, a humming light, and a bed that made the night feel far away."
    )
    world.say(
        f"{child.id} held on to {prize.phrase} and wished the evening felt less empty."
    )

    # Middle turn: friendship begins
    world.para()
    world.say(
        f"In the hall, {child.id} met {friend.label}. {friend.id} was sitting near a vending machine with a bent paper straw and a half-smile."
    )
    world.say(
        f"They started with a quiet game: {activity.gerund}, using {prize.label} as if it were something more interesting than it looked."
    )
    child.memes["loneliness"] = 0.4
    child.memes["curiosity"] = 2.0
    child.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0

    # Transformation
    world.para()
    world.say(
        f"{friend.id} folded the edges just right, and soon the plain thing changed shape in {child.id}'s hands."
    )
    world.say(
        f"By the time they were done, {prize.label} had become {transformed_label}, and both children were smiling at the same little trick."
    )
    child.memes["pride"] = 1.0
    child.memes["joy"] = 1.0
    prize.meters["transformed"] = 1.0

    # Bad ending
    world.para()
    world.say(
        f"At breakfast, {child.id} ran to the window to look for {friend.id}, but the room across the hall was already empty."
    )
    world.say(
        f"The bed was still smooth, the curtains still still, and only {transformed_label} stayed behind on the dresser."
    )
    child.memes["loss"] = 1.0
    child.memes["loneliness"] = 1.2
    child.memes["friendship"] = 0.5
    child.memes["transformed"] = 1.0

    world.facts.update(
        child=child,
        adult=adult,
        friend=friend,
        prize=prize,
        transformed_label=transformed_label,
        setting=setting,
        activity=activity,
        prize_cfg=prize_cfg,
        bad_ending=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short slice-of-life story for a young child set at a motel, with a brief friendship and a small transformation, using the word "motel".',
        f"Tell a gentle but sad story where {child.id} meets a new friend at the motel and {activity.verb}, changing {prize.phrase} into something special.",
        f"Write a simple story about a motel hallway, a new friend, and an ordinary thing that becomes different by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    adult = f["adult"]
    prize = f["prize"]
    activity = f["activity"]
    transformed = f["transformed_label"]
    return [
        QAItem(
            question=f"Where did {child.id} stop with {adult.label}?",
            answer=f"{child.id} stopped at the roadside motel with {adult.label}.",
        ),
        QAItem(
            question=f"Who did {child.id} meet in the hall?",
            answer=f"{child.id} met {friend.id}, the other child in the hallway.",
        ),
        QAItem(
            question=f"What did {they(child)} use to begin their game?",
            answer=f"They used {prize.label} while {activity.gerund}, and that made the quiet night feel less empty.",
        ),
        QAItem(
            question=f"What did {prize.label} become?",
            answer=f"It became {transformed}, which was the little transformation they made together.",
        ),
        QAItem(
            question=f"Why did the ending feel bad?",
            answer=f"It felt bad because {friend.id} was gone in the morning, so the friendship had to end too soon.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a motel?",
            answer="A motel is a place where travelers can sleep for a night, often beside a road or highway.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form, look, or feeling.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, play together, and enjoy being together.",
        ),
    ]


def they(ent: Entity) -> str:
    return ent.pronoun("subject")


# ---------------------------------------------------------------------------
# Serialization / CLI
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    parts = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Motel slice-of-life storyworld with friendship and transformation.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid motel story matches the given options.)")
    setting, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender, rng)
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, caregiver=caregiver)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.caregiver)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(motel).
affords(motel, quiet_play).
affords(motel, paper_game).
affords(motel, lobby_visit).

activity(quiet_play).
activity(paper_game).
activity(lobby_visit).

prize(keytag).
prize(postcard).
prize(map).

can_story(S, A, P) :- setting(S), affords(S, A), activity(A), prize(P).

#show can_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    for sid, setting in SETTINGS.items():
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - ac))
    print("asp-only:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="motel", activity="paper_game", prize="map", name="Maya", gender="girl", caregiver="mother"),
    StoryParams(setting="motel", activity="quiet_play", prize="keytag", name="Theo", gender="boy", caregiver="father"),
    StoryParams(setting="motel", activity="lobby_visit", prize="postcard", name="Nina", gender="girl", caregiver="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.activity} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
