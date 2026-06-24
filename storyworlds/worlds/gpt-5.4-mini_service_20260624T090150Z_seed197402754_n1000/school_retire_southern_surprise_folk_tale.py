#!/usr/bin/env python3
"""
A small folk-tale storyworld about a southern school, a retiring teacher, and a surprise ending.

Premise:
- In a little southern town, a kind teacher is retiring from the school.
- The children want to honor them, but the school day is still going.
- A surprise plan grows from shared effort, a hidden gift, and a final reveal.

The simulation tracks:
- physical meters: time, distance, hiddenness, readiness, carried things
- emotional memes: surprise, warmth, worry, pride, gratitude

The generated story is meant to read like a short folk tale:
clear beginning, a small tension, a turn, and a warm ending image.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "teacher"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    region: str
    affords: set[str] = field(default_factory=set)
    mood: str = "quiet"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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
class Gift:
    id: str
    label: str
    phrase: str
    prep: str
    reveal: str
    secret: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    gift: str
    name: str
    gender: str
    role: str
    seed: Optional[int] = None


SETTINGS = {
    "schoolyard": Setting(place="the schoolyard", region="south", affords={"procession", "sing", "hide"}),
    "porch": Setting(place="the school porch", region="south", affords={"procession", "hide"}),
    "oak": Setting(place="the oak tree by the school", region="south", affords={"hide", "sing"}),
}

ACTIVITIES = {
    "procession": Activity(
        id="procession",
        verb="walk in a little procession",
        gerund="walking in a little procession",
        rush="hurry to the school gate",
        risk="leave the surprise too soon",
        zone={"field"},
        keyword="school",
        tags={"school", "surprise"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing a farewell song",
        gerund="singing a farewell song",
        rush="start the song too early",
        risk="spoil the surprise",
        zone={"yard"},
        keyword="southern",
        tags={"song", "surprise"},
    ),
    "hide": Activity(
        id="hide",
        verb="hide the gift under a cloth",
        gerund="hiding the gift under a cloth",
        rush="peek at the basket",
        risk="show the gift before the right hour",
        zone={"porch"},
        keyword="retire",
        tags={"gift", "surprise"},
    ),
}

PRIZES = {
    "clock": Prize(
        label="clock",
        phrase="a bright brass clock",
        type="clock",
        region="desk",
        genders={"girl", "boy"},
    ),
    "book": Prize(
        label="book",
        phrase="a storybook with a blue ribbon",
        type="book",
        region="hands",
    ),
    "shawl": Prize(
        label="shawl",
        phrase="a warm shawl stitched with stars",
        type="shawl",
        region="shoulders",
        genders={"girl"},
    ),
}

GIFTS = {
    "bells": Gift(
        id="bells",
        label="little silver bells",
        phrase="little silver bells tied with red thread",
        prep="hide the bells beneath a basket cloth",
        reveal="the bells peeped out when the cloth was lifted",
        secret="the bells stayed hidden behind a basket of apples",
    ),
    "quilt": Gift(
        id="quilt",
        label="a patchwork quilt",
        phrase="a patchwork quilt with bright squares",
        prep="fold the quilt into a plain bundle",
        reveal="the quilt opened like a flower when the bundle was untied",
        secret="the quilt rested in a sack of tea towels",
    ),
    "bread": Gift(
        id="bread",
        label="sweet bread",
        phrase="a round loaf of sweet bread",
        prep="cover the bread in a clean cloth",
        reveal="the sweet smell floated out when the cloth came off",
        secret="the bread hid inside a covered basket",
    ),
}

GIRL_NAMES = ["Mabel", "Lena", "Hazel", "Nora", "Ivy", "Sadie"]
BOY_NAMES = ["Ezra", "Eli", "Miles", "Otis", "Beau", "Cal"]
ROLES = ["teacher", "principal"]
TRAITS = ["kind", "gentle", "patient", "cheerful", "wise"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.region in {"hands", "shoulders"} and activity.id == "hide"


def select_gift(activity: Activity, prize: Prize) -> Optional[Gift]:
    if activity.id == "procession":
        return GIFTS["bells"]
    if activity.id == "sing":
        return GIFTS["quilt"]
    if activity.id == "hide":
        return GIFTS["bread"]
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if not prize_at_risk(act, prize):
                    continue
                for gift_id in GIFTS:
                    out.append((place, act_id, prize_id, gift_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not create a believable worry for "
        f"{prize.phrase}. Pick a prize that the plan could truly hide or protect.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item here; try {ok}.)"


def build_story(world: World, hero: Entity, elder: Entity, prize: Entity, gift: Gift, activity: Activity) -> None:
    world.say(f"In {world.setting.place}, in the southern light, {hero.id} was a {hero.memes.get('trait_name', 'kind')} {hero.type} who loved {hero.memes.get('role_word', 'the school')}.")
    world.say(f"The old {elder.type} had worked there for many years, and now {elder.pronoun('subject')} was ready to retire.")
    world.say(f"The children wanted to thank {elder.pronoun('object')} with {prize.phrase}, because a farewell should be sweet and bright.")
    world.para()

    world.say(f"At first, everyone moved slowly, because {gift.secret} and nobody wanted to spoil the day.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {activity.risk}, so the little plan had to be kept careful.")
    hero.memes["worry"] = hero.meme("worry") + 1
    world.facts["gift"] = gift
    world.facts["activity"] = activity
    world.facts["prize"] = prize
    world.facts["elder"] = elder
    world.facts["hero"] = hero
    world.facts["surprise"] = True
    world.facts["hidden"] = True
    world.para()

    world.say(f"Then the bell of the school day rang soft, and the children gathered close.")
    world.say(f"They lifted the cloth, and {gift.reveal}.")
    hero.memes["surprise"] = hero.meme("surprise") + 1
    elder.memes["surprise"] = elder.meme("surprise") + 2
    elder.memes["warmth"] = elder.meme("warmth") + 1
    world.say(f"The retiring {elder.type} smiled with shining eyes, because the surprise came from every small hand.")
    world.say(f"{hero.id} stood beside the old school steps, and the southern evening felt as gentle as a hymn.")
    world.say(f"So the school said farewell, the gift was shared, and the day ended with {elder.pronoun('possessive')} heart full of thanks.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short folk tale for a child about a southern school and a surprise for someone who will retire.',
        f"Tell a gentle story in which {f['hero'].id} helps the school prepare a surprise for a retiring {f['elder'].type}.",
        f'Write a simple story that includes the words "school", "retire", and "southern", and ends with a warm surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    prize = f["prize"]
    gift = f["gift"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who was the story about in the southern school tale?",
            answer=f"It was about {hero.id} and the retiring {elder.type}, with the school children helping to make a surprise.",
        ),
        QAItem(
            question=f"What were the children hiding for the surprise?",
            answer=f"They were hiding {gift.phrase} so the gift would stay secret until the right moment.",
        ),
        QAItem(
            question=f"Why did the school children need to be careful?",
            answer=f"They needed to be careful because they did not want to {act.risk}, and they wanted the farewell to stay a true surprise.",
        ),
        QAItem(
            question=f"What did the retiring {elder.type} receive?",
            answer=f"The retiring {elder.type} received {prize.phrase} and a warm farewell from the school.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a school?", answer="A school is a place where children learn, listen, and practice new things together."),
        QAItem(question="What does it mean to retire?", answer="To retire means to stop working after many years and rest from the job."),
        QAItem(question="What does southern mean?", answer="Southern means from the south, often a warm direction or a warm part of a country."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that someone learns or sees at just the right time."),
        QAItem(question="What is a folk tale?", answer="A folk tale is a story people tell and retell, often with simple lessons and memorable characters."),
    ]


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gift_for(A,G), covers(G,R), worn_on(P,R).
valid(Place,A,P,G) :- affords(Place,A), prize_at_risk(A,P), gift_for(A,G), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift_for", g.id, gid))
        lines.append(asp.fact("covers", gid, "desk" if g.id == "bells" else "shoulders" if g.id == "quilt" else "hands"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a southern school and a retirement surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=ROLES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gift is None or c[3] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize, gift = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    role = args.role or rng.choice(ROLES)
    return StoryParams(place=place, activity=activity, prize=prize, gift=gift, name=name, gender=gender, role=role)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={"trait_name": "kind", "role_word": "the school"}))
    elder = world.add(Entity(id="OldTeacher", kind="character", type=params.role, label="the old teacher", meters={}, memes={"warmth": 0.0}))
    prize = world.add(Entity(id="Prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    gift = GIFTS[params.gift]
    act = ACTIVITIES[params.activity]
    build_story(world, hero, elder, prize, gift, act)
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
    StoryParams(place="schoolyard", activity="hide", prize="book", gift="bells", name="Mabel", gender="girl", role="teacher"),
    StoryParams(place="porch", activity="procession", prize="shawl", gift="quilt", name="Ezra", gender="boy", role="teacher"),
    StoryParams(place="oak", activity="sing", prize="clock", gift="bread", name="Lena", gender="girl", role="principal"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
