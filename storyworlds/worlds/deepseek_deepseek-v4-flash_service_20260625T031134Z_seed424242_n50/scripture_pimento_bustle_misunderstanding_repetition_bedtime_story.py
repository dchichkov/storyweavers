#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/scripture_pimento_bustle_misunderstanding_repetition_bedtime_story.py
=============================================================================================================

A standalone *story world* sketch about a small child who misunderstands a grown-up's
scripture reading and repeats a pimento-related request, creating a gentle bedtime bustle.

Initial story (used to build a world model):
---
Once upon a time, a little girl named Ella listened while her grandmother read from
the big family scripture book. The word "pimento" appeared in the story about a
special feast. Ella thought pimento was a magical fruit that made people happy.

Grandma put the scripture away and said, "Time for bed, little one."
But Ella wanted pimento. She asked again and again: "Please, Grandma, can I have
some pimento?"

Grandma smiled. "There is no pimento here, dear. It is just a word in the old book."

Ella did not understand. She kept repeating her question. The bedtime bustle grew
as Grandma searched the kitchen, then the pantry, then the garden. No pimento.

Finally, Grandma sat on Ella's bed and explained: "Pimento is a tiny red thing
that goes in olives. It is not a magical fruit. But you know what else is tiny
and red? A strawberry!"

Ella's eyes went wide. "Strawberry is pimento?" she asked.

"Almost," said Grandma, and she kissed Ella's forehead. They shared a strawberry
together, and Ella fell asleep dreaming of tiny red wonders.

Causal state updates:
---
    child hears word in scripture     -> child.pimento_belief += 1
    child repeats request             -> child.repetition_count += 1
                                          bustle_level += 1
    adult searches                    -> bustle_level += 1
                                          adult.search_count += 1
    misunderstanding resolved         -> child.understanding += 1 
                                          bustle_level = 0
                                          adult.workload -= 1 (when resolved)
    shared snack                      -> child.joy += 1
                                          adult.joy += 1
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

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mama"}
        male = {"boy", "man", "grandfather", "papa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, scripture: str, snack: str) -> None:
        self.scripture = scripture
        self.snack = snack
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.bustle_level: float = 0.0
        self.misunderstanding_word: str = "pimento"
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> World:
        clone = World(self.scripture, self.snack)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.bustle_level = self.bustle_level
        clone.misunderstanding_word = self.misunderstanding_word
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_bustle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("searching", 0.0) >= THRESHOLD:
            sig = ("bustle", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                world.bustle_level += 1
                if world.bustle_level >= 2:
                    out.append("The bedtime bustle grew and grew.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("asking", 0.0) >= THRESHOLD:
            sig = ("repeat", actor.id, int(actor.memes["asking"]))
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["repetition_count"] = actor.memes.get("repetition_count", 0.0) + 1
                out.append(f'The question came again, soft and hopeful.')
    return out


def _r_resolve(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("understanding", 0.0) >= THRESHOLD and world.bustle_level > 0:
            sig = ("resolve", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                world.bustle_level = 0.0
                out.append("The bustle quieted into a warm hush.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bustle", tag="physical", apply=_r_bustle),
    Rule(name="repetition", tag="social", apply=_r_repetition),
    Rule(name="resolve", tag="social", apply=_r_resolve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_snack(misunderstood: str) -> str:
    alternatives = {
        "pimento": "strawberry",
        "manna": "honey",
        "myrrh": "apple",
        "olive": "grape",
    }
    return alternatives.get(misunderstood, "strawberry")


# ---------------------------------------------------------------------------
# Verbs / Scenes
# ---------------------------------------------------------------------------
def scripture_reading(world: World, child: Entity, adult: Entity) -> None:
    word = world.misunderstanding_word
    child.memes["pimento_belief"] += 1
    world.say(
        f"{child.id} listened while {adult.label_word} read from the big family "
        f"scripture book. The word '{word}' appeared in the story about a special feast."
    )
    world.say(
        f"{child.pronoun().capitalize()} thought '{word}' was a magical fruit "
        f"that made people happy."
    )


def bedtime_call(world: World, child: Entity, adult: Entity) -> None:
    world.say(
        f'{adult.label_word.capitalize()} put the scripture away and said, '
        f'"Time for bed, little one."'
    )


def first_request(world: World, child: Entity, adult: Entity) -> None:
    word = world.misunderstanding_word
    child.memes["asking"] += 1
    world.say(
        f'But {child.id} wanted {word}. {child.pronoun().capitalize()} looked up '
        f'with bright eyes and said, "Please, {adult.label_word}, can I have some {word}?"'
    )


def explain_no_pimento(world: World, child: Entity, adult: Entity) -> None:
    word = world.misunderstanding_word
    adult.memes["searching"] += 1
    world.say(
        f'{adult.label_word.capitalize()} smiled gently. "There is no {word} here, dear. '
        f'It is just a word in the old book."'
    )


def repeat_request(world: World, child: Entity, adult: Entity) -> None:
    word = world.misunderstanding_word
    child.memes["asking"] += 0.5
    propagate(world, narrate=True)
    world.say(
        f'{child.id} did not understand. {child.pronoun().capitalize()} kept repeating, '
        f'"But I want the {word}!"'
    )


def search_bustle(world: World, child: Entity, adult: Entity) -> None:
    adult.memes["searching"] += 1
    world.bustle_level += 1
    propagate(world, narrate=True)
    world.say(
        f'{adult.label_word.capitalize()} looked in the kitchen, then the pantry, '
        f'then the garden. No {world.misunderstanding_word} anywhere.'
    )


def resolve_misunderstanding(world: World, child: Entity, adult: Entity) -> None:
    word = world.misunderstanding_word
    snack = world.snack
    child.memes["understanding"] += 1
    adult.memes["workload"] = max(0.0, adult.memes.get("workload", 0.0) - 1)
    propagate(world, narrate=True)
    world.say(
        f'Finally, {adult.label_word} sat on {child.id}\'s bed and explained: '
        f'"{word.capitalize()} is a tiny red thing that goes in olives. It is not '
        f'a magical fruit. But you know what else is tiny and red? A {snack}!"'
    )


def shared_snack(world: World, child: Entity, adult: Entity) -> None:
    snack = world.snack
    child.memes["joy"] += 1
    adult.memes["joy"] += 1
    child.memes["asking"] = 0.0
    world.say(
        f'{child.id}\'s eyes went wide. "{snack.capitalize()} is {world.misunderstanding_word}?" '
        f'{child.pronoun()} asked.'
    )
    world.say(
        f'"Almost," said {adult.label_word}, and {adult.pronoun()} kissed '
        f'{child.pronoun("possessive")} forehead. They shared a {snack} together, '
        f'and {child.id} fell asleep dreaming of tiny red wonders.'
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(scripture: str, child_name: str, child_type: str, adult_type: str,
         misunderstanding_word: str = "pimento") -> World:
    snack = select_snack(misunderstanding_word)
    world = World(scripture, snack)
    world.misunderstanding_word = misunderstanding_word

    child = world.add(Entity(
        id=child_name, kind="character", type=child_type,
        traits=["little", "curious", "repeating"],
    ))
    adult = world.add(Entity(
        id="Adult", kind="character", type=adult_type, label="the grown-up",
    ))

    # Act 1: Scripture and misunderstanding
    scripture_reading(world, child, adult)
    bedtime_call(world, child, adult)
    world.para()

    # Act 2: Repetition and bustle
    first_request(world, child, adult)
    explain_no_pimento(world, child, adult)
    world.para()
    repeat_request(world, child, adult)
    search_bustle(world, child, adult)
    world.para()

    # Act 3: Resolution
    resolve_misunderstanding(world, child, adult)
    shared_snack(world, child, adult)

    world.facts.update(
        child=child,
        adult=adult,
        scripture=scripture,
        snack=snack,
        misunderstanding_word=misunderstanding_word,
        bustle_level=world.bustle_level,
        repetition_count=child.memes.get("repetition_count", 0.0),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SCRIPTURES = {
    "feast": "the big family scripture book about a special feast",
    "garden": "the old scripture book about the garden of good things",
    "journey": "the worn scripture book about a long journey",
    "harvest": "the leather scripture book about the harvest time",
}

CHILD_NAMES = ["Ella", "Milo", "Nina", "Oscar", "Iris", "Theo", "Luna", "Finn"]
CHILD_TYPES = ["girl", "boy"]
ADULT_TYPES = ["grandmother", "grandfather", "mama", "papa"]
MISUNDERSTOOD_WORDS = ["pimento", "manna", "myrrh", "olive"]

REPETITION_PHRASES = [
    "asked again and again",
    "kept asking, soft and steady",
    "repeated the question like a song",
    "said it once more, hoping",
]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    scripture: str
    child_name: str
    child_type: str
    adult_type: str
    misunderstanding_word: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pimento": [
        ("What is a pimento?",
         "A pimento is a small, sweet red pepper. People sometimes put it inside "
         "olives or use it in cooking."),
    ],
    "manna": [
        ("What is manna?",
         "In old stories, manna was special food that appeared on the ground "
         "so traveling people could eat."),
    ],
    "myrrh": [
        ("What is myrrh?",
         "Myrrh is a sweet-smelling resin from a tree, used long ago as perfume "
         "or medicine."),
    ],
    "olive": [
        ("What is an olive?",
         "An olive is a small fruit that grows on olive trees. It can be green "
         "or black and is often eaten or pressed for oil."),
    ],
    "scripture": [
        ("What is a scripture book?",
         "A scripture book is a special book with old stories and teachings "
         "that a family or community reads together."),
    ],
    "misunderstanding": [
        ("What does it mean to misunderstand something?",
         "It means you hear or see something, but you think it means something "
         "different from what it really means."),
    ],
    "repetition": [
        ("Why do little children ask the same question many times?",
         "Little children ask the same question many times because they are "
         "trying to understand, or because they really want something."),
    ],
}
KNOWLEDGE_ORDER = ["pimento", "manna", "myrrh", "olive", "scripture", "misunderstanding", "repetition"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    word = f["misunderstanding_word"]
    return [
        f'Write a gentle bedtime story about a child who hears the word "{word}" '
        f'in a scripture reading and misunderstands what it means.',
        f'Tell a story about repetition and bedtime bustle, where a {f["child"].type} '
        f'named {f["child"].id} keeps asking {f["adult"].label_word} for {word}.',
        f'Create a cozy bedtime tale where a misunderstanding about "{word}" leads '
        f'to a search and a sweet resolution with a snack.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult = f["child"], f["adult"]
    word = f["misunderstanding_word"]
    snack = f["snack"]
    sub, obj, pos = (child.pronoun("subject"), child.pronoun("object"),
                     child.pronoun("possessive"))
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"What word did {child.id} hear while {adult.label_word} was "
                f"reading the scripture?"
            ),
            answer=(
                f"{child.id} heard the word '{word}' while {adult.label_word} "
                f"read from the scripture about a special feast. "
                f"{sub.capitalize()} thought it was a magical fruit."
            ),
        ),
        QAItem(
            question=(
                f"Did {adult.label_word} have {word} in the kitchen or pantry?"
            ),
            answer=(
                f"No, {adult.label_word} looked in the kitchen, the pantry, and "
                f"the garden, but there was no {word} anywhere. "
                f"It was just a word from the old book."
            ),
        ),
        QAItem(
            question=(
                f"How did {child.id} feel when {adult.label_word} said it was "
                f"time for bed?"
            ),
            answer=(
                f"{child.id} was still curious about {word}, so {sub} kept asking "
                f"about it instead of going to sleep. "
                f"The bedtime bustle grew as the questions continued."
            ),
        ),
    ]
    if world.bustle_level <= THRESHOLD:
        qa.append(QAItem(
            question=(
                f"What did {adult.label_word} explain about {word} in the end?"
            ),
            answer=(
                f"{adult.label_word.capitalize()} explained that {word} is really "
                f"a tiny red thing that goes in olives, not a magical fruit. "
                f"Then {adult.pronoun()} showed {obj} that a {snack} is also "
                f"tiny and red."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What did {child.id} and {adult.label_word} share together "
                f"before bedtime?"
            ),
            answer=(
                f"They shared a {snack} together after the misunderstanding was "
                f"resolved. {child.id} fell asleep dreaming of tiny red wonders."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    word = f["misunderstanding_word"]
    tags = {word, "scripture", "misunderstanding", "repetition"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  bustle_level={world.bustle_level:.1f}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scripture="feast",
        child_name="Ella",
        child_type="girl",
        adult_type="grandmother",
        misunderstanding_word="pimento",
    ),
    StoryParams(
        scripture="garden",
        child_name="Milo",
        child_type="boy",
        adult_type="grandfather",
        misunderstanding_word="manna",
    ),
    StoryParams(
        scripture="journey",
        child_name="Nina",
        child_type="girl",
        adult_type="mama",
        misunderstanding_word="myrrh",
    ),
    StoryParams(
        scripture="harvest",
        child_name="Oscar",
        child_type="boy",
        adult_type="papa",
        misunderstanding_word="olive",
    ),
]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A misunderstanding story is valid when scripture and word pair exists.
word_in_scripture(S, W) :- scripture_word(S, W).
valid_story(S, W, C, A) :- scripture_word(S, W), child_type(C), adult_type(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCRIPTURES:
        lines.append(asp.fact("scripture", sid))
    for w in MISUNDERSTOOD_WORDS:
        lines.append(asp.fact("word", w))
        for sid in SCRIPTURES:
            lines.append(asp.fact("scripture_word", sid, w))
    for c in CHILD_TYPES:
        lines.append(asp.fact("child_type", c))
    for a in ADULT_TYPES:
        lines.append(asp.fact("adult_type", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    stories = asp_valid_stories()
    print(f"OK: clingo found {len(stories)} valid story combinations.")
    return 0


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child misunderstands a scripture word and repeats a request.")
    ap.add_argument("--scripture", choices=SCRIPTURES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
    ap.add_argument("--misunderstanding-word", choices=MISUNDERSTOOD_WORDS)
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
    scripture = args.scripture or rng.choice(list(SCRIPTURES.keys()))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    misunderstanding_word = args.misunderstanding_word or rng.choice(MISUNDERSTOOD_WORDS)
    return StoryParams(
        scripture=scripture,
        child_name=child_name,
        child_type=child_type,
        adult_type=adult_type,
        misunderstanding_word=misunderstanding_word,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        scripture=SCRIPTURES[params.scripture],
        child_name=params.child_name,
        child_type=params.child_type,
        adult_type=params.adult_type,
        misunderstanding_word=params.misunderstanding_word,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combinations:\n")
        for s, w, c, a in stories:
            print(f"  scripture={s}, word={w}, child={c}, adult={a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.child_name}: scripture about {p.scripture} (word: {p.misunderstanding_word})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
