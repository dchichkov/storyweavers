#!/usr/bin/env python3
"""
A small storyworld: two friends, a windy afternoon, and a quick little fix.

Premise:
- A child wants to play with something that depends on air moving fast.
- A friend notices a small problem before the fun can begin.
- The child thinks hard, then accepts help.
- The ending shows the changed state: the play happens smoothly, and the friendship grows.

Narrative instruments:
- Inner monologue: the hero quietly thinks through the problem.
- Friendship: the friend helps with a practical, kind fix.
- Rhyme: short rhyming lines appear at key beats.
- Slice of life: the events stay ordinary, concrete, and homey.

The simulated world models:
- physical meters: wind_strength, string_twist, height, steadiness, mess
- emotional memes: joy, worry, pride, care, closeness
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    with_friend: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    kind: str  # park, rooftop, field, beach
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    inner_monologue: str
    fast_need: str
    risk: str
    wind_gain: float
    mess_gain: float
    tags: set[str] = field(default_factory=set)
    keyword: str = "air"


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    needs_air: bool
    likes_fast_air: bool
    can_tangle: bool
    can_rattle: bool
    use_line: str
    rescue_line: str


@dataclass
class Helper:
    id: str
    label: str
    action: str
    fix: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "park": Setting(place="the park", kind="park", affords={"kite", "paperplane"}),
    "field": Setting(place="the field", kind="field", affords={"kite", "paperplane"}),
    "beach": Setting(place="the beach", kind="beach", affords={"kite"}),
    "rooftop": Setting(place="the rooftop", kind="rooftop", affords={"kite"}),
}

ACTIVITIES = {
    "kite": Activity(
        id="kite",
        verb="fly a kite",
        gerund="flying a kite",
        inner_monologue="If the air is fast and steady, the kite will listen.",
        fast_need="fast air",
        risk="the string may tangle",
        wind_gain=1.0,
        mess_gain=0.0,
        tags={"air", "fast"},
        keyword="air",
    ),
    "paperplane": Activity(
        id="paperplane",
        verb="race paper planes",
        gerund="racing paper planes",
        inner_monologue="A little fast air could carry the planes farther.",
        fast_need="a quick breeze",
        risk="the folds may flop",
        wind_gain=0.7,
        mess_gain=0.0,
        tags={"air", "fast"},
        keyword="air",
    ),
}

TOYS = {
    "kite": Toy(
        id="kite",
        label="kite",
        phrase="a bright paper kite with a long tail",
        needs_air=True,
        likes_fast_air=True,
        can_tangle=True,
        can_rattle=False,
        use_line="The kite pulled up at once and bobbed in the air.",
        rescue_line="A smoother string path kept it from knotting.",
    ),
    "paperplane": Toy(
        id="paperplane",
        label="paper planes",
        phrase="folded paper planes with blue stripes",
        needs_air=True,
        likes_fast_air=True,
        can_tangle=False,
        can_rattle=True,
        use_line="The paper planes skimmed ahead on the breeze.",
        rescue_line="A careful fold helped the nose stay straight.",
    ),
}

HELPERS = {
    "friend_tug": Helper(
        id="friend_tug",
        label="Mina",
        action="held the string a little higher",
        fix="That lifted the line away from the snaggy grass.",
        rhyme="High in the air, light as a sparrow, the string could slip straight and narrow.",
        tags={"friendship"},
    ),
    "friend_fold": Helper(
        id="friend_fold",
        label="Owen",
        action="smoothed the paper fold",
        fix="That made the plane stay neat when the breeze rushed by.",
        rhyme="Fold it tight, fold it neat, and the little plane will beat the street.",
        tags={"friendship"},
    ),
}

NAMES = {
    "girl": ["Lila", "Maya", "Nora", "Zoe", "Mia"],
    "boy": ["Finn", "Theo", "Eli", "Noah", "Ben"],
}
FRIEND_NAMES = ["Mina", "Owen", "Tess", "June", "Ira"]
TRAITS = ["thoughtful", "shy", "cheerful", "curious", "gentle", "quick"]


@dataclass
class StoryParams:
    place: str
    activity: str
    toy: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
% A toy is workable when the place affords the activity and the activity likes air.
workable(Place, Activity, Toy) :- affords(Place, Activity), toy(Toy), needs_air(Toy), air_activity(Activity).

% A friendly fix is available when helper and activity match and the toy actually needs it.
fixable(Place, Activity, Toy, Helper) :- workable(Place, Activity, Toy), helper(Helper), helper_for(Helper, Activity, Toy).

% Valid story choices require a workable toy and a fixable helper.
valid_story(Place, Activity, Toy, Friend) :- work_ok(Place, Activity, Toy), friend_ok(Friend).
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
        lines.append(asp.fact("air_activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if t.needs_air:
            lines.append(asp.fact("needs_air", tid))
        if t.likes_fast_air:
            lines.append(asp.fact("likes_fast_air", tid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("helper_tag", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _reasonableness(activity: Activity, toy: Toy) -> bool:
    return activity.id in {"kite", "paperplane"} and toy.needs_air and toy.likes_fast_air


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for toy_id, toy in TOYS.items():
                if _reasonableness(act, toy):
                    out.append((place, act_id, toy_id))
    return out


def explain_rejection(activity: Activity, toy: Toy) -> str:
    return (
        f"(No story: {activity.gerund} and {toy.label} do not make a sensible air-and-fast scene.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.toy:
        act, toy = ACTIVITIES[args.activity], TOYS[args.toy]
        if not _reasonableness(act, toy):
            raise StoryError(explain_rejection(act, toy))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.toy is None or c[2] == args.toy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, toy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, toy=toy, name=name, gender=gender, friend=friend, trait=trait)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about air, fast play, friendship, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait")
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


def _intro(world: World, hero: Entity, friend: Entity, activity: Activity, toy: Entity) -> None:
    world.say(f"{hero.id} was a {hero.pronoun('possessive')} little {hero.type} who liked quiet afternoons at {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {activity.verb} with {toy.label}, because the {activity.keyword} in the air felt full of promise.")
    world.say(f"Inside {hero.id}'s head, a tiny thought went by: {activity.inner_monologue}")


def _conflict(world: World, hero: Entity, friend: Entity, activity: Activity, toy: Entity) -> None:
    toy_ent = world.get("toy")
    toy_ent.meters["string_twist"] = 1.0 if toy.can_tangle else 0.0
    hero.memes["worry"] += 1.0
    world.say(f"But the {activity.fast_need} was not smooth yet, and {activity.risk}.")
    world.say(f"{hero.id} looked at the {toy.label} and thought, 'If I rush, this may go wrong.'")
    world.say(f"Then {friend.id} came close and smiled, as if she had noticed the same small problem.")


def _helper_choice(activity: Activity, toy: Toy) -> Helper:
    if toy.can_tangle:
        return HELPERS["friend_tug"]
    return HELPERS["friend_fold"]


def _resolve(world: World, hero: Entity, friend: Entity, activity: Activity, toy: Entity, helper: Helper) -> None:
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["joy"] += 1.0
    hero.memes["pride"] += 1.0
    friend.memes["care"] += 1.0
    friend.memes["closeness"] += 1.0
    toy.meters["steady"] = 1.0
    toy.meters["height"] = 1.0
    world.say(f"{friend.id} {helper.action}, and {helper.fix}")
    world.say(f"\"{helper.rhyme}\" {friend.id} said, and the words sounded like a little song.")
    world.say(f"{hero.id} nodded, and in a soft inner voice thought, 'Oh. That is actually better.'")
    world.say(f"Together they tried again, and {toy.label} found the fast air at just the right angle.")
    world.say(f"{toy.label.capitalize()} went up cleanly, and the afternoon felt easy and bright.")


def tell(setting: Setting, activity: Activity, toy_cfg: Toy, hero_name: str, gender: str, friend_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, memes={"worry": 0.0, "joy": 0.0, "pride": 0.0, "closeness": 0.0}))
    friend = world.add(Entity(id=friend_name, kind="character", type="child", memes={"care": 0.0, "closeness": 0.0}))
    toy = world.add(Entity(id="toy", type=toy_cfg.label, label=toy_cfg.label, phrase=toy_cfg.phrase, meters={"string_twist": 0.0, "height": 0.0, "steady": 0.0}))
    world.facts = {"hero": hero, "friend": friend, "toy": toy_cfg, "activity": activity, "setting": setting, "trait": trait}

    _intro(world, hero, friend, activity, toy)
    world.say("")
    world.say(f"The breeze was quick, but not yet cooperative.")
    _conflict(world, hero, friend, activity, toy_cfg)
    world.say("")
    helper = _helper_choice(activity, toy_cfg)
    _resolve(world, hero, friend, activity, toy, helper)
    world.facts["helper"] = helper
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child who wants to {f["activity"].verb} with {f["toy"].label} in the air.',
        f'Write a gentle friendship story where {f["hero"].id} notices a problem, thinks quietly, and gets help from {f["friend"].id}.',
        f'Include a small rhyme and an inner monologue, and end with {f["toy"].label} working better in the fast air.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    activity: Activity = f["activity"]
    toy: Toy = f["toy"]
    helper: Helper = f["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb} with the {toy.label}.",
        ),
        QAItem(
            question=f"Who helped when the plan needed a small fix?",
            answer=f"{friend.id} helped by {helper.action}, which made the toy work better in the fast air.",
        ),
        QAItem(
            question=f"What did {hero.id} think quietly before trying again?",
            answer=activity.inner_monologue,
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {toy.label} moving cleanly through the air and both friends feeling happy together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is air?",
            answer="Air is the invisible stuff all around us that we breathe and that can move as wind.",
        ),
        QAItem(
            question="What does it mean when wind is fast?",
            answer="Fast wind means the air is moving quickly, which can help a kite or paper plane travel farther.",
        ),
        QAItem(
            question="Why can a friend make a small problem feel easier?",
            answer="A friend can help by noticing what is wrong, sharing a good idea, and staying kind while you try again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], TOYS[params.toy], params.name, params.gender, params.friend, params.trait)
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


def valid_asp_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_asp_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def valid_story_pairs() -> list[tuple[str, str]]:
    return [(p, a) for p, a, _ in valid_combos()]


CURATED = [
    StoryParams(place="park", activity="kite", toy="kite", name="Lila", gender="girl", friend="Mina", trait="thoughtful"),
    StoryParams(place="field", activity="paperplane", toy="paperplane", name="Finn", gender="boy", friend="Owen", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_asp_combos())} compatible stories")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
