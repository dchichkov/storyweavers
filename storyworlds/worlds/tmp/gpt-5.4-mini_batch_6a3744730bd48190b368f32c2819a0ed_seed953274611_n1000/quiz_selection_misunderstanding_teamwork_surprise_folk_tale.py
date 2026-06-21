#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/quiz_selection_misunderstanding_teamwork_surprise_folk_tale.py
==============================================================================================

A tiny folk-tale storyworld about a village quiz, a selection, a misunderstanding,
teamwork, and a surprise ending.

This world is self-contained and follows the shared Storyweavers contract:
- typed entities with physical meters and emotional memes
- a state-driven story renderer
- a Python reasonableness gate plus inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
- standard CLI flags including --verify and --show-asp
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman", "queen", "maiden"}
        male = {"boy", "father", "man", "king", "herdsman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quiz:
    id: str
    topic: str
    question: str
    hint: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Selection:
    id: str
    name: str
    confusion: str
    truth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    reveal: str
    gift: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["misunderstanding"] < THRESHOLD:
            continue
        sig = ("misunderstanding", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__misunderstanding__")
    return out


def _r_teamwork(world: World) -> list[str]:
    if world.facts.get("helped") and not world.facts.get("teamwork_narrated"):
        world.facts["teamwork_narrated"] = True
        for e in world.characters():
            e.memes["trust"] += 1
        return ["__teamwork__"]
    return []


def _r_surprise(world: World) -> list[str]:
    if world.facts.get("surprise_ready") and not world.facts.get("surprise_seen"):
        world.facts["surprise_seen"] = True
        return ["__surprise__"]
    return []


CAUSAL_RULES = [Rule("misunderstanding", "social", _r_misunderstanding),
                Rule("teamwork", "social", _r_teamwork),
                Rule("surprise", "social", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def story_reasonable(setting: Setting, quiz: Quiz, selection: Selection, surprise: Surprise) -> bool:
    return bool(setting.place and quiz.topic and selection.truth and surprise.gift)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUIZZES:
            for selid in SELECTIONS:
                if "quiz" in QUIZZES[qid].tags and "selection" in SELECTIONS[selid].tags:
                    combos.append((sid, qid, selid))
    return combos


@dataclass
class StoryParams:
    setting: str
    quiz: str
    selection: str
    surprise: str
    hero: str
    helper: str
    elder: str
    hero_gender: str
    helper_gender: str
    elder_gender: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, helper: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f"Once in {setting.place}, {hero.id} and {helper.id} went with {elder.id} "
        f"to the little square where {setting.detail}."
    )
    world.say(
        f"{hero.id} loved folk tales, and {helper.id} loved clever plans, while {elder.id} "
        f"kept the old songs safe."
    )


def announce_quiz(world: World, quiz: Quiz) -> None:
    world.say(
        f"That day there was a quiz about {quiz.topic}. The town promised a {quiz.reward} "
        f"to the child who answered best."
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, selection: Selection) -> None:
    hero.meters["misunderstanding"] += 1
    helper.memes["concern"] += 1
    world.say(
        f"{hero.id} heard about the selection and thought it meant choosing berries "
        f"for supper, not choosing a quiz helper."
    )
    world.say(
        f"{helper.id} blinked. {helper.pronoun().capitalize()} saw the confusion at once "
        f"and knew a gentle explanation was needed."
    )


def teamwork(world: World, hero: Entity, helper: Entity, elder: Entity, quiz: Quiz, selection: Selection) -> None:
    world.facts["helped"] = True
    hero.meters["misunderstanding"] = 0.0
    hero.memes["hope"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"Then {helper.id} took {hero.pronoun('possessive')} hand and said, "
        f'"Let us solve it together. We can listen to the clue, and {elder.id} can '
        f"tell us what the selection truly means.""
    )
    world.say(
        f"{elder.id} smiled and explained that the selection was not for berries at all. "
        f"It was the village way of choosing who would stand beside the quiz table."
    )
    world.say(
        f"So the three of them practiced the quiz side by side, and the confusion began to melt."
    )


def surprise_end(world: World, surprise: Surprise, hero: Entity, helper: Entity, elder: Entity, quiz: Quiz) -> None:
    world.facts["surprise_ready"] = True
    world.say(
        f"When the answers were done, the crowd gave a hush -- and then came the surprise."
    )
    world.say(
        f"The winner was not a single child. The elders had chosen the whole little trio, "
        f"because their teamwork had been the cleverest answer of all."
    )
    world.say(
        f"They were handed {surprise.gift}, and {surprise.reveal}."
    )
    world.say(
        f"{hero.id} laughed, {helper.id} clapped, and {elder.id} nodded like a tree in the wind."
    )


def tell(setting: Setting, quiz: Quiz, selection: Selection, surprise: Surprise,
         hero_name: str = "Mara", hero_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy",
         elder_name: str = "Aunt Rowan", elder_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))

    introduce(world, hero, helper, elder, setting)
    announce_quiz(world, quiz)
    world.para()
    misunderstanding(world, hero, helper, selection)
    propagate(world, narrate=False)
    world.para()
    teamwork(world, hero, helper, elder, quiz, selection)
    propagate(world, narrate=False)
    world.para()
    surprise_end(world, surprise, hero, helper, elder, quiz)

    world.facts.update(
        hero=hero, helper=helper, elder=elder, setting=setting, quiz=quiz,
        selection=selection, surprise=surprise, outcome="surprise"
    )
    return world


SETTINGS = {
    "village_green": Setting(
        id="village_green",
        place="the village green",
        detail="the children gathered around a plum tree and a bright quilt",
        tags={"folk", "village"},
    ),
    "river_fair": Setting(
        id="river_fair",
        place="the river fair",
        detail="the river sang under the bridge and ribbons fluttered from the stalls",
        tags={"folk", "river"},
    ),
    "apple_lane": Setting(
        id="apple_lane",
        place="Apple Lane",
        detail="the old market stall waited beside a cart of apples",
        tags={"folk", "market"},
    ),
}

QUIZZES = {
    "birds": Quiz(
        id="birds",
        topic="birds and their songs",
        question="Which bird sings at dawn?",
        hint="Listen for the first sweet note in the morning.",
        reward="silver ribbon",
        tags={"quiz", "song"},
    ),
    "stars": Quiz(
        id="stars",
        topic="stars and moonlight",
        question="Which star guides night travelers?",
        hint="Look for the bright one that seems to point the way.",
        reward="moon cake",
        tags={"quiz", "night"},
    ),
    "seasons": Quiz(
        id="seasons",
        topic="the turning seasons",
        question="Which season brings apples and red leaves?",
        hint="It comes after summer and before winter.",
        reward="golden apple",
        tags={"quiz", "nature"},
    ),
}

SELECTIONS = {
    "draw_shell": Selection(
        id="draw_shell",
        name="shell selection",
        confusion="thought the selection was a basket of shells",
        truth="the choosing of one helper for the quiz table",
        tags={"selection"},
    ),
    "choose_song": Selection(
        id="choose_song",
        name="song selection",
        confusion="thought the selection meant picking a song to sing",
        truth="the choosing of a team to answer the quiz together",
        tags={"selection"},
    ),
    "pick_branch": Selection(
        id="pick_branch",
        name="branch selection",
        confusion="thought the selection meant finding a branch for kindling",
        truth="the choosing of a child to stand with the elder",
        tags={"selection"},
    ),
}

SURPRISES = {
    "whole_team": Surprise(
        id="whole_team",
        reveal="the village had decided that helping one another was the real prize",
        gift="three sweet buns wrapped in cloth",
        tags={"surprise", "teamwork"},
    ),
    "secret_song": Surprise(
        id="secret_song",
        reveal="the elder had hidden a new folk song for them to sing on the way home",
        gift="a little carved flute",
        tags={"surprise", "song"},
    ),
}

GIRL_NAMES = ["Mara", "Nia", "Anya", "Lina", "Tara"]
BOY_NAMES = ["Pip", "Bram", "Oren", "Joss", "Tobin"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a quiz, a selection, and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quiz", choices=QUIZZES)
    ap.add_argument("--selection", choices=SELECTIONS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk-tale story that includes the words quiz and selection, set in {f['setting'].place}.",
        f"Tell a small village story where a misunderstanding about a selection leads to teamwork and a surprise.",
        f"Write a child-friendly tale in which friends solve a quiz together and are rewarded with an unexpected surprise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, elder = f["hero"], f["helper"], f["elder"]
    quiz, sel, surprise = f["quiz"], f["selection"], f["surprise"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, {helper.id}, and {elder.id}. They are the little group who moves the story forward together."),
        ("What was the quiz about?",
         f"The quiz was about {quiz.topic}. It gave the village a reason to gather, listen, and test what they knew."),
        ("What did the misunderstanding change?",
         f"{hero.id} thought the selection meant something ordinary, not the village choice of a helper. That wrong idea caused confusion until {helper.id} and {elder.id} cleared it up."),
        ("How did they fix the misunderstanding?",
         f"They worked together. {helper.id} spoke kindly, {elder.id} explained the truth, and the three of them practiced side by side until the confusion faded."),
        ("What was the surprise at the end?",
         f"The surprise was that the whole little trio was chosen, not just one child. The village wanted to reward their teamwork, so the ending felt joyful and bright."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["quiz"].tags) | set(f["selection"].tags) | set(f["surprise"].tags) | {"quiz", "selection"}
    know = {
        "quiz": [("What is a quiz?",
                  "A quiz is a set of questions people try to answer. It can be a game, a lesson, or a village contest.")],
        "selection": [("What does selection mean?",
                      "Selection means choosing one thing or one person from several choices.")],
        "teamwork": [("What is teamwork?",
                     "Teamwork is when people help one another and do something together.")],
        "surprise": [("What is a surprise?",
                     "A surprise is something you do not expect. It can make people gasp, smile, or laugh.")],
    }
    out = []
    for tag in ["quiz", "selection", "teamwork", "surprise"]:
        if tag in tags:
            out.extend(know[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen quiz, selection, and surprise do not make a coherent folk-tale selection-and-teamwork scene.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUIZZES.items():
        lines.append(asp.fact("quiz", qid))
        for tag in sorted(q.tags):
            lines.append(asp.fact("tagged", qid, tag))
    for sid, s in SELECTIONS.items():
        lines.append(asp.fact("selection", sid))
        for tag in sorted(s.tags):
            lines.append(asp.fact("tagged", sid, tag))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        for tag in sorted(s.tags):
            lines.append(asp.fact("tagged", sid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,Sel,Sur) :- setting(S), quiz(Q), selection(Sel), surprise(Sur).
needs_teamwork(Q) :- quiz(Q).
has_selection(Sel) :- selection(Sel).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        assert sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.quiz and args.selection and args.surprise:
        if (args.setting, args.quiz, args.selection, args.surprise) not in [(s, q, sel, sur) for s, q, sel in combos for sur in SURPRISES]:
            pass
    subset = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.quiz is None or c[1] == args.quiz)
              and (args.selection is None or c[2] == args.selection)]
    if not subset:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quiz, selection = rng.choice(sorted(subset))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != hero])
    elder = args.elder or ("Aunt Rowan" if elder_gender == "woman" else "Uncle Reed")
    return StoryParams(setting=setting, quiz=quiz, selection=selection, surprise=surprise,
                       hero=hero, helper=helper, elder=elder,
                       hero_gender=hero_gender, helper_gender=helper_gender, elder_gender=elder_gender)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quiz = QUIZZES[params.quiz]
    selection = SELECTIONS[params.selection]
    surprise = SURPRISES[params.surprise]
    world = tell(setting, quiz, selection, surprise, params.hero, params.hero_gender,
                 params.helper, params.helper_gender, params.elder, params.elder_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid in QUIZZES:
            for selid in SELECTIONS:
                combos.append((sid, qid, selid))
    return combos


CURATED = [
    StoryParams(setting="village_green", quiz="birds", selection="draw_shell", surprise="whole_team",
                hero="Mara", hero_gender="girl", helper="Pip", helper_gender="boy",
                elder="Aunt Rowan", elder_gender="woman"),
    StoryParams(setting="river_fair", quiz="stars", selection="choose_song", surprise="secret_song",
                hero="Nia", hero_gender="girl", helper="Tobin", helper_gender="boy",
                elder="Uncle Reed", elder_gender="man"),
    StoryParams(setting="apple_lane", quiz="seasons", selection="pick_branch", surprise="whole_team",
                hero="Oren", hero_gender="boy", helper="Lina", helper_gender="girl",
                elder="Aunt Rowan", elder_gender="woman"),
]


def build_random_names(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible quiz/selection settings:\n")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
