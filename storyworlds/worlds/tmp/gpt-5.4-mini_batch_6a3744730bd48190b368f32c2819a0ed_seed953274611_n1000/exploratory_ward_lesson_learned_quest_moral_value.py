#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exploratory_ward_lesson_learned_quest_moral_value.py
===================================================================================

A small bedtime-story storyworld about an exploratory ward who goes on a quest,
learns a lesson, and ends with a clear moral value. The domain is kept tiny and
state-driven: a child explores a little setting, gets warned by a ward, makes a
choice, and comes home wiser.

The story includes the seed words "exploratory" and "ward" and is designed to
read like a warm bedtime tale.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
COURAGE_INIT = 4.0
WISDOM_INIT = 0.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    dark_spot: str
    quest_goal: str
    quiet_detail: str


@dataclass
class Quest:
    id: str
    verb: str
    title: str
    object: str
    reward: str
    risk: str
    keyword: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ward:
    id: str
    label: str
    guidance: str
    comfort: str
    promise: str
    wisdom_gain: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Moral:
    id: str
    statement: str
    lesson: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_wisdom(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ward = world.get("ward")
    if child.memes["learned"] >= THRESHOLD and ("wisdom", "ward") not in world.fired:
        world.fired.add(("wisdom", "ward"))
        ward.memes["warmth"] += 1
        out.append("__wisdom__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CAUSAL_RULES = [Rule("wisdom", _r_wisdom)]


def reasonables(quest: Quest, setting: Setting) -> bool:
    return quest.zone in {"path", "garden", "attic"} and setting.id in SETTINGS


def can_complete(quest: Quest, delay: int) -> bool:
    return quest.difficulty + delay <= 3


@dataclass
class StoryParams:
    setting: str
    quest: str
    ward: str
    child_name: str
    child_gender: str
    parent_name: str
    delay: int = 0
    seed: Optional[int] = None


def tell(setting: Setting, quest: Quest, ward_cfg: Ward, moral: Moral,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Mama", delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="explorer", traits=["curious"]))
    ward = world.add(Entity(id="ward", kind="character", type="woman",
                            label=ward_cfg.label, role="ward", traits=["gentle"]))
    parent = world.add(Entity(id=parent_name, kind="character", type="woman",
                              label="the parent", role="parent"))
    child.memes["courage"] = COURAGE_INIT
    child.memes["learned"] = WISDOM_INIT
    ward.memes["care"] = 1.0

    world.say(
        f"At bedtime, {child.id} was an exploratory little explorer who lived by "
        f"the quiet {setting.place}. {setting.quiet_detail}"
    )
    world.say(
        f"{child.id} loved a small quest: to {quest.verb} and bring home {quest.reward}. "
        f"{quest.title} sounded brave, but the dark {setting.dark_spot} made the path feel big."
    )
    world.para()
    world.say(
        f"Then {ward_cfg.label} stepped close and said, \"{ward_cfg.guidance} {ward_cfg.comfort}\""
    )
    child.memes["courage"] += 1
    child.memes["doubt"] += 1
    world.say(
        f"{child.id} looked at {ward_cfg.promise}. {ward_cfg.label} was a ward at the door, "
        f"watching kindly, like a moonbeam keeping the room safe."
    )

    world.para()
    if can_complete(quest, delay):
        child.meters["quest_progress"] += 1
        world.say(
            f"So {child.id} took the quest carefully, tiptoed along the {setting.place}, "
            f"and listened when {ward_cfg.label} pointed out the safest way."
        )
        child.meters["reward"] += 1
        child.memes["learned"] += 1
        propagate(world, narrate=False)
        world.say(
            f"In the end, {child.id} found {quest.reward} near the {quest.object}, "
            f"and the little prize felt brighter because it had been earned gently."
        )
        world.say(
            f"{child.id} brought it home, and {ward_cfg.label} smiled at how calm the quest had become."
        )
    else:
        child.meters["stumble"] += 1
        child.memes["fear"] += 1
        world.say(
            f"{child.id} hurried too fast, and the quest grew wobbly. The path near the "
            f"{setting.dark_spot} looked too tricky for such a late hour."
        )
        world.say(
            f"{ward_cfg.label} held up a hand, led {child.id} back, and said that a brave heart "
            f"still needs a wise step."
        )
        child.memes["learned"] += 1
        propagate(world, narrate=False)
        world.say(
            f"So the quest waited for another night, and the little explorer came home safe."
        )

    world.para()
    world.say(
        f"Before sleep, {parent.label_word} tucked {child.id} in and repeated the lesson: "
        f"{moral.statement} {moral.lesson}"
    )
    world.say(
        f"{child.id} nodded, warm under the blanket, and kept the good lesson like a tiny lantern in {child.pronoun('possessive')} heart."
    )

    world.facts.update(
        child=child, ward=ward, parent=parent, setting=setting, quest=quest,
        moral=moral, delay=delay, completed=bool(child.meters["reward"] >= THRESHOLD),
        learned=bool(child.memes["learned"] >= THRESHOLD),
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="garden gate",
        dark_spot="hedge tunnel",
        quest_goal="the silver pebble",
        quiet_detail="The flowers nodded in the moonlight, and the path smelled sweet."
    ),
    "attic": Setting(
        id="attic",
        place="attic stair",
        dark_spot="dusty corner",
        quest_goal="the old star map",
        quiet_detail="The house was hush-soft, and the beams above made sleepy stripes."
    ),
    "lantern_room": Setting(
        id="lantern_room",
        place="lantern room",
        dark_spot="back shelf",
        quest_goal="the tiny bell",
        quiet_detail="A lantern glowed nearby, and the shadows were small and round."
    ),
}

QUESTS = {
    "pebble": Quest(
        id="pebble",
        verb="find the silver pebble",
        title="A Little Moon Quest",
        object="mossy step",
        reward="the silver pebble",
        risk="a long, dark path",
        keyword="quest",
        zone="garden",
        tags={"quest", "garden"},
    ),
    "map": Quest(
        id="map",
        verb="bring back the old star map",
        title="An Attic Quest",
        object="old trunk",
        reward="the old star map",
        risk="a tall, dusty shelf",
        keyword="exploratory",
        zone="attic",
        tags={"quest", "attic", "exploratory"},
    ),
    "bell": Quest(
        id="bell",
        verb="find the tiny bell",
        title="A Lantern Quest",
        object="back shelf",
        reward="the tiny bell",
        risk="a sleepy corner",
        keyword="ward",
        zone="lantern_room",
        tags={"quest", "ward"},
    ),
}

WARDS = {
    "mama": Ward(
        id="mama",
        label="Mama",
        guidance="Let's go slowly and keep our feet near the light.",
        comfort="I will stay beside you.",
        promise="the soft hand on the rail",
        wisdom_gain=1,
        tags={"ward", "lesson"},
    ),
    "grandma": Ward(
        id="grandma",
        label="Grandma",
        guidance="Brave explorers use careful steps.",
        comfort="A safe path is still a real adventure.",
        promise="the little candle by the door",
        wisdom_gain=1,
        tags={"ward", "lesson"},
    ),
}

MORALS = {
    "care": Moral(
        id="care",
        statement="The best quest is the one that keeps everyone safe.",
        lesson="That is the moral value of the story, and it made the night feel gentle.",
        tags={"moral", "lesson"},
    ),
    "kindness": Moral(
        id="kindness",
        statement="A kind helper is worth more than a hurried victory.",
        lesson="The lesson learned was that patience can shine brighter than rushing.",
        tags={"moral", "lesson"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for wid, ward in WARDS.items():
                if reasonables(quest, setting):
                    combos.append((sid, qid, wid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: exploratory ward, quest, lesson, moral.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ward", choices=WARDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2, 3])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.ward is None or c[2] == args.ward)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, ward = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting, quest=quest, ward=ward, child_name=name,
        child_gender=gender, parent_name=parent, delay=delay
    )


def story_for(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q, w, s = f["quest"], f["ward"], f["setting"]
    return [
        f'Write a bedtime story for a young child that includes the words "exploratory" and "ward".',
        f"Tell a gentle quest story where {f['child'].id} is exploratory, listens to {w.label}, and learns a bedtime lesson.",
        f"Write a soft moral tale in which a child and a ward turn a small quest in the {s.place} into a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ward, setting, quest, moral = f["child"], f["ward"], f["setting"], f["quest"], f["moral"]
    out = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id}, an exploratory child, and {ward.label}, the ward who helps keep the night calm."
        ),
        QAItem(
            question=f"What was the quest?",
            answer=f"The quest was to {quest.verb} in the {setting.place}. It was a little adventure, but it stayed gentle because {ward.label} guided the way."
        ),
    ]
    if f["completed"]:
        out.append(QAItem(
            question="How did the quest end?",
            answer=f"{child.id} completed the quest and came home with {quest.reward}. The ending proves that careful steps can still lead to happy treasure."
        ))
    else:
        out.append(QAItem(
            question="How did the quest end?",
            answer=f"The quest ended with {child.id} turning back safely. That made the lesson clearer: some adventures are best saved for another night."
        ))
    out.append(QAItem(
        question="What lesson was learned?",
        answer=f"{moral.statement} {moral.lesson}"
    ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["ward"].tags) | set(world.facts["moral"].tags)
    out: list[QAItem] = []
    if "quest" in tags:
        out.append(QAItem(
            question="What is a quest?",
            answer="A quest is a small mission or adventure where someone tries to find something or do something important."
        ))
    if "ward" in tags:
        out.append(QAItem(
            question="What is a ward in a bedtime story?",
            answer="A ward is a gentle helper or guardian who watches over someone and helps them stay safe."
        ))
    if "lesson" in tags:
        out.append(QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important after an experience, so you can do better next time."
        ))
    if "moral" in tags:
        out.append(QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to act, like kindness, patience, or safety."
        ))
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        parts.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    parts.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(parts)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
valid(S,Q,W) :- setting(S), quest(Q), ward(W).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for wid in WARDS:
        lines.append(asp.fact("ward", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def tell_from_params(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    quest = QUESTS.get(params.quest)
    ward = WARDS.get(params.ward)
    if setting is None:
        raise StoryError(f"Unknown setting: {params.setting}")
    if quest is None:
        raise StoryError(f"Unknown quest: {params.quest}")
    if ward is None:
        raise StoryError(f"Unknown ward: {params.ward}")
    moral = MORALS["care"] if params.quest != "bell" else MORALS["kindness"]
    return tell(setting, quest, ward, moral, params.child_name, params.child_gender, params.parent_name, params.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell_from_params(params)
    return StorySample(
        params=params,
        story=story_for(world),
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
    StoryParams(setting="garden", quest="pebble", ward="mama", child_name="Mina", child_gender="girl", parent_name="mother", delay=0),
    StoryParams(setting="attic", quest="map", ward="grandma", child_name="Owen", child_gender="boy", parent_name="father", delay=1),
    StoryParams(setting="lantern_room", quest="bell", ward="mama", child_name="Luna", child_gender="girl", parent_name="mother", delay=0),
]


def build_sample_from_random(args: argparse.Namespace, rng: random.Random) -> StorySample:
    return generate(resolve_params(args, rng))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
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
            header = f"### {p.child_name} in the {p.setting} ({p.quest}, {p.ward})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
