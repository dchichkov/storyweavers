#!/usr/bin/env python3
"""
storyworlds/worlds/relief_pillar_rhyme_friendship_flashback_tall_tale.py
========================================================================

A tiny tall-tale storyworld about a leaning pillar, a flash of flashback,
and a rhyming friendship that brings relief.

The seed words here are "relief" and "pillar", and the narrative instruments
are Rhyme, Friendship, and Flashback.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    wind_prone: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    effect: str
    weather: str
    tag: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    elder_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "town_square": Setting("the town square"),
    "river_dock": Setting("the river dock"),
    "fairground": Setting("the fairground"),
}

ACTIVITIES = {
    "wind": Activity(
        id="wind",
        verb="haul the big banner",
        effect="leaning",
        weather="windy",
        tag="wind",
    ),
    "storm": Activity(
        id="storm",
        verb="protect the lantern",
        effect="shaking",
        weather="stormy",
        tag="storm",
    ),
    "parade": Activity(
        id="parade",
        verb="raise the bright flag",
        effect="trembling",
        weather="sunny",
        tag="parade",
    ),
}

PRIZES = {
    "banner": Prize("banner", "banner", "a long banner with gold stitching", "upper"),
    "lantern": Prize("lantern", "lantern", "a glass lantern with a brass hook", "upper"),
    "flag": Prize("flag", "flag", "a painted flag with a red edge", "upper"),
}

GEAR = [
    Gear("rope", "a long rope", "tie the pillar with a long rope", "walked over to the rope", {"wind", "storm"}),
    Gear("brace", "a wooden brace", "set a wooden brace against the pillar", "went to fetch the brace", {"wind", "storm"}),
    Gear("peg", "iron pegs", "drive iron pegs into the ground", "ran for the iron pegs", {"wind"}),
]

GIRL_NAMES = ["Ruby", "Mabel", "Nell", "Ivy", "Lena", "June"]
BOY_NAMES = ["Otis", "Hank", "Jeb", "Clay", "Bo", "Wade"]


def _story_pronoun(gender: str) -> tuple[str, str, str]:
    return ("she", "her", "her") if gender == "girl" else ("he", "him", "his")


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


THRESHOLD = 1.0


def _r_relief(world: World) -> list[str]:
    out = []
    pillar = world.entities.get("pillar")
    if pillar and pillar.meters.get("stable", 0) >= THRESHOLD and not world.fired.__contains__(("relief",)):
        world.fired.add(("relief",))
        world.get("hero").memes["relief"] = 1
        out.append("A sweet wave of relief rolled across the square.")
    return out


RULES = [Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_damage(world: World, act: Activity) -> bool:
    sim = world.entities["pillar"].meters.get("stable", 0)
    return sim < 1.0 and act.tag in {"wind", "storm"}


def select_gear(act: Activity) -> Optional[Gear]:
    for gear in GEAR:
        if act.tag in gear.guards:
            return gear
    return None


def tell(setting: Setting, activity: Activity, prize: Prize, name: str, gender: str,
         friend_name: str, friend_gender: str, elder_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity("hero", kind="character", type=gender, label=name))
    friend = world.add(Entity("friend", kind="character", type=friend_gender, label=friend_name))
    elder = world.add(Entity("elder", kind="character", type="elder", label=elder_name))
    pillar = world.add(Entity("pillar", type="pillar", label="pillar", phrase="a tall town pillar"))
    prize_ent = world.add(Entity("prize", type=prize.id, label=prize.label, phrase=prize.phrase, owner="pillar"))
    world.facts.update(hero=hero, friend=friend, elder=elder, pillar=pillar, prize=prize_ent,
                       activity=activity, setting=setting, gear=None)

    subj, obj, pos = _story_pronoun(gender)
    fsubj, fobj, fpos = _story_pronoun(friend_gender)

    world.say(
        f"In {setting.place}, there stood a pillar tall enough to tickle the belly of a thundercloud."
    )
    world.say(
        f"{name} and {friend_name} were best friends, the sort who could split a biscuit and a burden with one grin."
    )
    world.say(
        f"They loved how the breeze swayed {prize.phrase}, and {name} wished to {activity.verb} before the day was done."
    )
    world.para()
    world.say(
        f"Then the wind came nosing round the square, and the pillar began to list like a sleepy giant."
    )
    world.say(
        f"{name} held {pos} breath, because if the pillar leaned much farther, the {prize.label} might come tumbling down."
    )
    world.say(
        f"{friend_name} pointed and said, \"This calls for a little courage and a lot of elbow grease.\""
    )
    if predict_damage(world, activity):
        world.say(
            f"{name} wanted to charge ahead, but {elder_name} raised a hand and said, "
            f"\"Hold up, young spark. I once heard a rhyme that could steady a barn cat in a gale.\""
        )
        world.say(
            f"That sentence opened a door in {name}'s memory, and a flashback popped up bright as a firefly."
        )
        world.say(
            f"In the flashback, {name} was small as a corn kernel, listening to {elder_name} chant, "
            f"\"Lean, then keep it keen; sing together, make it lean no more seen.\""
        )
        world.say(
            f"{friend_name} laughed at the rhyme, but {name} grinned, because friendship is a bridge that grows when voices cross it."
        )
        gear = select_gear(activity)
        if gear is None:
            raise StoryError("No reasonable gear exists for this tall-tale moment.")
        world.facts["gear"] = gear
        world.say(
            f"So they {gear.prep}, and then they stood shoulder to shoulder by the pillar."
        )
        world.say(
            f"They sang the old rhyme, clapped in time, and pushed with the kind of teamwork that makes crows blink twice."
        )
        pillar.meters["stable"] = 1.0
        prize_ent.meters["safe"] = 1.0
        propagate(world, narrate=True)
        world.say(
            f"At last the pillar held steady, the {prize.label} shone up high again, and a warm relief settled into every heart in the square."
        )
        world.say(
            f"{name} and {friend_name} laughed so hard that even the wind seemed to bow and go find another place to wander."
        )
    else:
        world.say(
            f"The pillar only wobbled a little, so {name} and {friend_name} gave it a careful pat and called the day a lucky one."
        )
        pillar.meters["stable"] = 1.0
        prize_ent.meters["safe"] = 1.0
        propagate(world, narrate=True)
        world.say(
            f"With the pillar straight again, the whole town felt relief as soft as fresh bread."
        )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        f"Write a tall tale for a child about {hero.label}, a pillar, and a burst of relief.",
        f"Tell a friendship story where {hero.label} wants to {activity.verb} near {prize.label} and a rhyme helps.",
        f"Write a story with a flashback that reminds {hero.label} how to steady a leaning pillar.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, elder = f["hero"], f["friend"], f["elder"]
    activity = f["activity"]
    prize = f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label} and {friend.label}, who were best friends in the town square.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do?",
            answer=f"{hero.label} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What object worried everyone when the wind blew?",
            answer=f"The tall pillar worried everyone because it began to lean and might have dropped the {prize.label}.",
        ),
        QAItem(
            question=f"Why did the rhyme matter?",
            answer=f"The rhyme mattered because it helped {hero.label} and {friend.label} work together and steady the pillar.",
        ),
        QAItem(
            question=f"What did the flashback show?",
            answer=f"The flashback showed {elder.label} teaching a rhyme about keeping a pillar from leaning.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the gear help?",
                answer=f"They used {gear.label} to hold the pillar steady while they sang and pushed together.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the pillar standing straight, the {prize.label} safe, and everybody feeling relief.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pillar?",
            answer="A pillar is a tall upright support that can hold up parts of a building, a sign, or a decoration.",
        ),
        QAItem(
            question="What is relief?",
            answer="Relief is the happy feeling you get when a worry goes away and things are safe again.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little pattern of words that sound alike at the end, and it can make a saying easy to remember.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a story moment that jumps back to something that happened before.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people who help, trust, and enjoy one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a pillar, rhyme, friendship, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
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
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or rng.choice(list(PRIZES))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    elder_name = args.elder_name or rng.choice(["Gran", "Old Tom", "Aunt Rose", "Mr. Bell"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender,
                       friend_name=friend_name, friend_gender=friend_gender, elder_name=elder_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.friend_name, params.friend_gender, params.elder_name)
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
affected(P) :- prize(P), pillar(pillar).
needs_rhyme(H,F) :- hero(H), friend(F).
flashback_needed(H) :- hero(H), elder(elder).
relief :- pillar_stable(pillar).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    lines.append(asp.fact("pillar", "pillar"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("friend", "friend"))
    lines.append(asp.fact("elder", "elder"))
    lines.append(asp.fact("pillar_stable", "pillar"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show relief/0."))
    got = bool(asp.atoms(model, "relief"))
    want = True
    if got == want:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH: ASP and Python gates disagree.")
    return 1


def valid_combo(place: str, activity: str, prize: str) -> bool:
    return place in SETTINGS and activity in ACTIVITIES and prize in PRIZES


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show relief/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show relief/0."))
        print("relief" if asp.atoms(model, "relief") else "no relief")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        combos = [
            StoryParams("town_square", "wind", "banner", "Ruby", "girl", "Otis", "boy", "Gran"),
            StoryParams("river_dock", "storm", "lantern", "Hank", "boy", "Mabel", "girl", "Old Tom"),
            StoryParams("fairground", "parade", "flag", "June", "girl", "Bo", "boy", "Aunt Rose"),
        ]
        samples = [generate(p) for p in combos]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
