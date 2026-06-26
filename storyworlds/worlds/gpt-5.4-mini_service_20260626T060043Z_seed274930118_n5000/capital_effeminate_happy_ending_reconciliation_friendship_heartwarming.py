#!/usr/bin/env python3
"""
A small heartwarming storyworld about a child in a capital city who is teased
for being effeminate, then finds reconciliation through friendship.

Premise:
- A child loves a soft, graceful activity or style that others call "too
  effeminate."
- A friend or sibling worries that the child will be left out or mocked in a
  busy capital setting.
- The child faces a gentle conflict: stay quiet and hide the preference, or
  keep being themselves.

Turn:
- A kind companion notices the hurt and offers support.
- The child and companion make a small, concrete choice that keeps the child's
  style visible while making room for belonging.

Resolution:
- The child is accepted, friendship strengthens, and the ending image proves
  that the capital feels warmer because of the reconciliation.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    atmosphere: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    joy: str
    at_risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    style: str
    gender_ok: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Compromise:
    id: str
    label: str
    prep: str
    tail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    friend = world.get(world.facts["friend"].id)
    if child.memes.get("hurt", 0) >= THRESHOLD and friend.memes.get("support", 0) >= THRESHOLD:
        sig = ("soften", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["hurt"] = 0
            child.memes["joy"] = child.memes.get("joy", 0) + 1
            child.memes["belonging"] = child.memes.get("belonging", 0) + 1
            out.append("The hurt eased a little.")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soften,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def tell(setting: Setting, activity: Activity, prize: Prize, compromise: Compromise,
         child_name: str, child_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    outfit = world.add(Entity(
        id="outfit", type=prize.type, label=prize.label, phrase=prize.phrase,
        owner=child.id, worn_by=child.id
    ))
    helper = world.add(Entity(
        id=compromise.id, type="thing", label=compromise.label
    ))

    world.facts.update(child=child, friend=friend, outfit=outfit, helper=helper,
                       setting=setting, activity=activity, prize=prize, compromise=compromise)

    world.say(
        f"{child.id} lived near the capital, where the streets were busy and bright, "
        f"and {child.pronoun('possessive')} favorite thing was {activity.gerund}."
    )
    world.say(
        f"{child.id} loved {activity.gerund} because it felt gentle and graceful, "
        f"even if other children called it {prize.style}."
    )
    world.say(
        f"One afternoon, at {setting.place}, {child.id} wore {prize.phrase} and hoped no one would stare."
    )

    world.para()
    world.say(
        f"Then {child.id} wanted to {activity.verb}, but that could leave {child.pronoun('object')} "
        f"feeling singled out in the crowded capital."
    )
    child.memes["hurt"] = 1
    child.memes["fear"] = 1
    world.say(
        f"A small teasing voice floated by, and {child.id}'s smile faded."
    )

    world.para()
    friend.memes["support"] = 1
    friend.memes["love"] = 1
    world.say(
        f"{friend.id} came over, stood close, and said, "
        f'"You do not have to hide the way you like to move."'
    )
    world.say(
        f"Together they chose to {compromise.prep}, so {child.id} could still be themself "
        f"without being pushed aside."
    )

    child.memes["courage"] = 1
    world.say(
        f"{child.id} took a breath, lifted {child.pronoun('possessive')} chin, and went on to {activity.verb}."
    )
    world.say(
        f"People looked, then smiled, because the choice was kind and honest."
    )

    world.para()
    propagate(world)
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["friendship"] = child.memes.get("friendship", 0) + 1
    world.say(
        f"In the end, {child.id} and {friend.id} walked home through the capital together, "
        f"laughing softly as {child.pronoun('possessive')} {prize.label} stayed neat."
    )
    world.say(
        f"The day ended with reconciliation, friendship, and a warm little feeling that lasted."
    )

    return world


SETTINGS = {
    "square": Setting(place="the capital square", atmosphere="busy", affords={"dance", "sing"}),
    "garden": Setting(place="the quiet garden by the museum", atmosphere="gentle", affords={"dance", "sing"}),
    "bridge": Setting(place="the river bridge near the capital gate", atmosphere="windy", affords={"dance", "sing"}),
}

ACTIVITIES = {
    "dance": Activity(
        id="dance",
        verb="dance",
        gerund="dancing",
        rush="spin across the stones",
        joy="the graceful steps felt like music",
        at_risk="teasing",
        tags={"dance", "grace", "kindness"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing",
        gerund="singing",
        rush="start a bright song",
        joy="the melody felt like sunlight",
        at_risk="teasing",
        tags={"song", "kindness"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a soft blue ribbon",
        type="accessory",
        style="effeminate",
        gender_ok={"girl", "boy"},
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a silky scarf",
        type="accessory",
        style="effeminate",
        gender_ok={"girl", "boy"},
    ),
}

COMPROMISES = {
    "lantern_walk": Compromise(
        id="lantern_walk",
        label="a lantern walk together",
        prep="light a small lantern and dance where the light looked welcoming",
        tail="walked home with the lantern glowing between them",
        tags={"friendship", "reconciliation"},
    ),
    "music_corner": Compromise(
        id="music_corner",
        label="a music corner by the fountain",
        prep="move to a quieter corner and sing where the echo sounded kind",
        tail="stayed beside the fountain while the song turned the whole square warmer",
        tags={"friendship", "reconciliation"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Maya", "Nora", "Ari"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Milo", "Jude"]
TRAITS = ["gentle", "careful", "brave", "soft-spoken", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    compromise: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for activity in setting.affords:
            for prize in PRIZES:
                for compromise in COMPROMISES:
                    combos.append((place, activity, prize, compromise))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f'Write a heartwarming story about a child in the capital who loves {activity.gerund} and is teased for being {prize.style}.',
        f"Tell a gentle story where {child.id} faces teasing, then finds friendship and reconciliation.",
        f"Write a short story that ends happily with a child being accepted exactly as they are.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    activity = f["activity"]
    prize = f["prize"]
    compromise = f["compromise"]
    return [
        QAItem(
            question=f"Why did {child.id} feel hurt in the capital?",
            answer=f"{child.id} felt hurt because some children mocked {child.pronoun('possessive')} {prize.label} style and made {child.pronoun('object')} worry about being left out.",
        ),
        QAItem(
            question=f"Who helped {child.id} feel better?",
            answer=f"{friend.id} helped by standing close, speaking kindly, and choosing a way for {child.id} to keep {activity.gerund}.",
        ),
        QAItem(
            question=f"What compromise did they choose?",
            answer=f"They chose {compromise.label}, which let {child.id} keep being graceful without hiding {child.pronoun('possessive')} self.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily with {child.id} and {friend.id} walking home together after reconciliation and friendship had grown stronger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a capital city?",
            answer="A capital city is the main city of a country or region, where important buildings and people are often found.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after hurt feelings or disagreement.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a warm connection between people who care about each other and help each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming capital city reconciliation storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--compromise", choices=COMPROMISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    combos = valid_combos()
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.compromise is None or c[3] == args.compromise)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize, compromise = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    friend_gender = "girl" if friend_name in GIRL_NAMES else "boy"
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        compromise=compromise,
        child_name=child_name,
        child_type=gender,
        friend_name=friend_name,
        friend_type=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        COMPROMISES[params.compromise],
        params.child_name,
        params.child_type,
        params.friend_name,
        params.friend_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place,Activity,Prize,Compromise) :- setting(Place), activity(Activity), prize(Prize), compromise(Compromise).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for c in COMPROMISES:
        lines.append(asp.fact("compromise", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


CURATED = [
    StoryParams("square", "dance", "ribbon", "lantern_walk", "Mina", "girl", "Theo", "boy", "gentle"),
    StoryParams("garden", "sing", "scarf", "music_corner", "Eli", "boy", "Ari", "girl", "thoughtful"),
]


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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
