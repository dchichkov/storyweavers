#!/usr/bin/env python3
"""
storyworlds/worlds/tale_shawl_craft_workshop_surprise_repetition_quest.py
========================================================================

A small slice-of-life storyworld set in a craft workshop, built around a tale,
a shawl, a surprise, repetition, and a gentle quest.

Seed image:
A child visits a busy craft workshop to help make a shawl for a family story
night. The child keeps repeating a stitch pattern while looking for the right
button, ribbon, or yarn charm. A surprise changes the plan: the shawl needs one
last finishing touch, and the child goes on a tiny quest through the workshop to
find it. The ending proves what changed by showing the finished shawl and the
happy smallness of an ordinary day.

Design notes:
- The domain is slice-of-life, concrete, and child-facing.
- Physical meters and emotional memes drive the state and narration.
- The story includes premise, tension, turn, and resolution.
- Invalid selections fail closed with StoryError.
- Inline ASP rules mirror the Python reasonableness gate.
"""

from __future__ import annotations

import argparse
import copy
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
    maker: Optional[str] = None
    location: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Workshop:
    name: str = "the craft workshop"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "Workshop":
        c = Workshop(self.name)
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Setting:
    place: str = "the craft workshop"


@dataclass
class StoryObject:
    id: str
    label: str
    phrase: str
    kind: str = "object"
    location: str = "table"
    makes_good_end: bool = False


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    location: str
    surprise: bool = False
    available: bool = True


@dataclass
class StoryParams:
    setting: str
    tale: str
    shawl: str
    surprise: str
    repetition: str
    quest: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "craft_workshop": Setting(place="the craft workshop"),
}

TALES = {
    "winter_story": StoryObject(
        id="winter_story",
        label="tale",
        phrase="a tiny tale for family story night",
        location="story basket",
    ),
    "rain_story": StoryObject(
        id="rain_story",
        label="tale",
        phrase="a little rain tale for a cozy evening",
        location="story shelf",
    ),
    "bird_story": StoryObject(
        id="bird_story",
        label="tale",
        phrase="a bright bird tale with a soft ending",
        location="story basket",
    ),
}

SHAWLS = {
    "blue_shawl": StoryObject(
        id="blue_shawl",
        label="shawl",
        phrase="a soft blue shawl with a wide edge",
        location="spool table",
    ),
    "red_shawl": StoryObject(
        id="red_shawl",
        label="shawl",
        phrase="a warm red shawl with neat fringe",
        location="work rack",
    ),
    "green_shawl": StoryObject(
        id="green_shawl",
        label="shawl",
        phrase="a green shawl that felt smooth in the hand",
        location="folding chair",
    ),
}

SURPRISES = {
    "missing_button": "the shawl needed one last button",
    "loose_thread": "a loose thread kept peeking out",
    "tiny_smudge": "a tiny smudge needed hiding",
}

REPETITIONS = {
    "three_knots": "three careful knots, three careful knots",
    "two_stitches": "two slow stitches, two slow stitches",
    "soft_fold": "fold, smooth, fold, smooth",
}

QUESTS = {
    "find_button": QuestItem(
        id="find_button",
        label="button box",
        phrase="the button box",
        location="the shelf under the window",
    ),
    "find_ribbon": QuestItem(
        id="find_ribbon",
        label="ribbon tin",
        phrase="the ribbon tin",
        location="the drawer beside the table",
    ),
    "find_pin": QuestItem(
        id="find_pin",
        label="pin jar",
        phrase="the pin jar",
        location="the little cart by the door",
    ),
}

NAMES = ["Maya", "Leo", "Nina", "Eli", "Ava", "Ben", "Iris", "Noah"]
HELPERS = ["grandmother", "mother", "father", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for tale in TALES:
        for shawl in SHAWLS:
            for surprise in SURPRISES:
                for quest in QUESTS:
                    combos.append((tale, shawl, surprise, quest))
    return combos


def reasonableness_gate(params: StoryParams) -> bool:
    return params.tale in TALES and params.shawl in SHAWLS and params.surprise in SURPRISES and params.quest in QUESTS


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen tale, shawl, surprise, or quest is not part of this workshop.)"


ASP_RULES = r"""
valid(Tale, Shawl, Surprise, Quest) :- tale(Tale), shawl(Shawl), surprise(Surprise), quest(Quest).

chosen(T, S, U, Q) :- valid(T, S, U, Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in TALES:
        lines.append(asp.fact("tale", t))
    for s in SHAWLS:
        lines.append(asp.fact("shawl", s))
    for u in SURPRISES:
        lines.append(asp.fact("surprise", u))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class Rule:
    name: str
    apply: callable


def _r_repeat(world: Workshop) -> list[str]:
    out = []
    if world.facts.get("repeating") and not world.facts.get("repeat_narrated"):
        world.facts["repeat_narrated"] = True
        out.append("The workshop hummed with the same careful motion again and again.")
    return out


def propagate(world: Workshop, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in [Rule("repeat", _r_repeat)]:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, tale: StoryObject, shawl: StoryObject, surprise: str,
         repetition: str, quest: QuestItem, name: str, helper: str) -> Workshop:
    w = Workshop(setting.place)
    child = w.add(Entity(id=name, kind="character", type="child", label=name))
    adult = w.add(Entity(id=helper, kind="character", type="adult", label=helper))
    tale_e = w.add(Entity(id=tale.id, type="tale", label="tale", phrase=tale.phrase, location=tale.location))
    shawl_e = w.add(Entity(id=shawl.id, type="shawl", label="shawl", phrase=shawl.phrase, location=shawl.location))
    quest_e = w.add(Entity(id=quest.id, type="quest_item", label=quest.label, phrase=quest.phrase, location=quest.location))

    for e in (child, adult, tale_e, shawl_e, quest_e):
        e.meters.setdefault("care", 0.0)
        e.meters.setdefault("finished", 0.0)
        e.meters.setdefault("found", 0.0)
        e.memes.setdefault("joy", 0.0)
        e.memes.setdefault("curiosity", 0.0)
        e.memes.setdefault("surprise", 0.0)
        e.memes.setdefault("relief", 0.0)

    child.memes["curiosity"] = 1.0
    child.memes["joy"] = 1.0
    adult.memes["calm"] = 1.0
    w.facts["repeating"] = True

    w.say(f"{name} came into {setting.place} to help with {tale.phrase}.")
    w.say(f"On the table waited {shawl.phrase}, and {helper} smiled at the steady work ahead.")
    w.para()
    w.say(f"{name} kept saying {repetition} while the stitches grew longer and neater.")
    w.say(f"The same quiet rhythm made the shawl feel almost finished.")
    w.para()
    w.say(f"Then came a surprise: {SURPRISES[surprise]}.")
    child.memes["surprise"] += 1.0
    w.facts["surprise"] = surprise
    w.facts["quest"] = quest
    if surprise == "missing_button":
        w.say(f"{name} and {helper} looked for {quest.phrase}.")
    elif surprise == "loose_thread":
        w.say(f"{name} and {helper} went on a little quest for {quest.phrase}.")
    else:
        w.say(f"{name} and {helper} began a small quest toward {quest.phrase}.")
    quest_e.meters["found"] = 0.0
    quest_e.attrs["located"] = False
    propagate(w, narrate=False)
    w.para()
    w.say(f"At last, {name} found {quest.phrase} at {quest.location}.")
    quest_e.meters["found"] = 1.0
    child.meters["care"] += 1.0
    adult.meters["care"] += 1.0
    child.memes["relief"] += 1.0
    adult.memes["relief"] += 1.0
    tale_e.meters["finished"] = 1.0
    shawl_e.meters["finished"] = 1.0
    w.say(f"{helper} helped fasten it, and the {shawl.label} finally looked ready for the tale.")
    w.say(f"{name} held up the {shawl.label} beside the finished {tale.label}, happy with the small, tidy ending.")
    w.facts.update(child=child, adult=adult, tale=tale_e, shawl=shawl_e, quest_item=quest_e, setting=setting)
    return w


def generation_prompts(world: Workshop) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story set in {f["setting"].place} about a child helping with a tale and a shawl.',
        f"Tell a gentle workshop story where {f['child'].id} repeats a stitch pattern, then goes on a quest for {f['quest_item'].phrase}.",
        f'Write a child-friendly story that includes the words "tale" and "shawl" and ends with a small surprise in {f["setting"].place}.',
    ]


def story_qa(world: Workshop) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    tale = f["tale"]
    shawl = f["shawl"]
    quest = f["quest_item"]
    return [
        QAItem(
            question=f"Who is the story about in the craft workshop?",
            answer=f"It is about {child.id}, who came to help with a tale and a shawl in {f['setting'].place}.",
        ),
        QAItem(
            question=f"What did {child.id} keep repeating while working?",
            answer=f"{child.id} kept repeating {REPETITIONS[f['repeat_key']]}, and that careful rhythm helped the shawl grow more finished.",
        ),
        QAItem(
            question=f"What surprise changed the plan?",
            answer=f"The surprise was that {SURPRISES[f['surprise']]}. That made {child.id} and {adult.id} pause and look for one more piece.",
        ),
        QAItem(
            question=f"What quest did {child.id} go on?",
            answer=f"{child.id} went on a tiny quest for {quest.phrase}, and found it at {quest.location}.",
        ),
        QAItem(
            question=f"What did the finished shawl show at the end?",
            answer=f"The finished shawl showed that {child.id} and {adult.id} had solved the surprise and made the tale ready for story night.",
        ),
    ]


def world_knowledge_qa(world: Workshop) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shawl?",
            answer="A shawl is a soft piece of clothing or wrapping that you wear over your shoulders for warmth or style.",
        ),
        QAItem(
            question="What is a tale?",
            answer="A tale is a story that someone tells or reads.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, even if the search is small and happens in one room.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying the same thing again, like a stitch pattern that comes back over and over.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that changes what happens next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: Workshop) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.location:
            bits.append(f"location={e.location}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_params() -> list[StoryParams]:
    out = []
    for t, s, u, q in valid_combos():
        out.append(StoryParams(
            setting="craft_workshop",
            tale=t,
            shawl=s,
            surprise=u,
            repetition=random.choice(list(REPETITIONS)),
            quest=q,
            name="Maya",
            helper="grandmother",
        ))
    return out


CURATED = [
    StoryParams("craft_workshop", "winter_story", "blue_shawl", "missing_button", "three_knots", "find_button", "Maya", "grandmother"),
    StoryParams("craft_workshop", "rain_story", "red_shawl", "loose_thread", "two_stitches", "find_ribbon", "Leo", "aunt"),
    StoryParams("craft_workshop", "bird_story", "green_shawl", "tiny_smudge", "soft_fold", "find_pin", "Nina", "mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life craft workshop storyworld with a tale, shawl, surprise, repetition, and quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--shawl", choices=SHAWLS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--repetition", choices=REPETITIONS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
              if (args.tale is None or c[0] == args.tale)
              and (args.shawl is None or c[1] == args.shawl)
              and (args.surprise is None or c[2] == args.surprise)
              and (args.quest is None or c[3] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tale, shawl, surprise, quest = rng.choice(sorted(combos))
    return StoryParams(
        setting=args.setting or "craft_workshop",
        tale=tale,
        shawl=shawl,
        surprise=surprise,
        repetition=args.repetition or rng.choice(list(REPETITIONS)),
        quest=quest,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_gate(params):
        raise StoryError(explain_rejection(params))
    world = tell(
        SETTINGS[params.setting],
        TALES[params.tale],
        SHAWLS[params.shawl],
        params.surprise,
        params.repetition,
        QUESTS[params.quest],
        params.name,
        params.helper,
    )
    world.facts["repeat_key"] = params.repetition
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        import asp
        python_set = set(valid_combos())
        clingo_set = set(asp_valid_combos())
        if python_set != clingo_set:
            print("MISMATCH between Python and ASP valid combos.")
            print("Python only:", sorted(python_set - clingo_set))
            print("ASP only:", sorted(clingo_set - python_set))
            sys.exit(1)
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
        sample = generate(resolve_params(args, random.Random(args.seed or 0)))
        print("OK: generated story sample exercises the world model.")
        _ = sample.story
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
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
