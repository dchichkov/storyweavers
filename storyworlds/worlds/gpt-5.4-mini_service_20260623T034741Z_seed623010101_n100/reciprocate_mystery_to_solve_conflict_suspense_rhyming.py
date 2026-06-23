#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/reciprocate_mystery_to_solve_conflict_suspense_rhyming.py
====================================================================================================

A small standalone storyworld for a rhyming mystery about a lost token, a
tense misunderstanding, and a kind reciprocal gesture that mends the trouble.

The seed prompt asks for:
- reciprocate
- Mystery to Solve
- Conflict
- Suspense
- Rhyming Story

This world models a child-facing "lost charm / found clue / mixed-up feelings /
kindly reciprocated help" domain. The story is generated from world state, not
from a frozen paragraph. Characters have physical meters and emotional memes,
and the prose follows the simulated beats.

Contract notes:
- Uses storyworlds/results.py eagerly for QAItem, StoryError, StorySample.
- Imports storyworlds/asp.py lazily in ASP helpers.
- Provides StoryParams, build_parser, resolve_params, generate, emit, main.
- Supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    knows: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    lost_item: str
    lost_phrase: str
    hiding_place: str
    clue: str
    clue_place: str
    solved_place: str
    rhymes_with: str
    tension_line: str
    reveal_line: str
    reciprocal_gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _py_rng_choice(rng: random.Random, items):
    return rng.choice(list(items))


def pronoun_pair(e: Entity) -> tuple[str, str, str]:
    return e.pronoun("subject"), e.pronoun("object"), e.pronoun("possessive")


def make_story_line(text: str) -> str:
    return text


def rhyme(end1: str, end2: str) -> str:
    return f"{end1} and {end2}"


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, helper_name: str,
         helper_gender: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender, role="hero",
        tags={"child", "curious"},
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_gender, role="friend",
        tags={"child", "helpful"},
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, role="helper",
        tags={"adult", "kind"},
    ))
    token = world.add(Entity(
        id="token", kind="thing", type="token", label=mystery.lost_item,
        phrase=mystery.lost_phrase, owner=hero.id, tags={"lost", "important"},
    ))
    clue = world.add(Entity(
        id="clue", kind="thing", type="clue", label=mystery.clue,
        phrase=mystery.clue, tags={"clue"},
    ))
    helper.knows.update({"finds", "reciprocates"})

    hero.memes.update({"worry": 0.0, "hope": 0.0, "relief": 0.0, "joy": 0.0})
    friend.memes.update({"worry": 0.0, "curiosity": 0.0, "trust": 0.0, "joy": 0.0})
    helper.memes.update({"calm": 0.0, "trust": 0.0, "kindness": 0.0, "joy": 0.0})
    token.meters.update({"lost": 0.0, "found": 0.0})
    clue.meters.update({"noticed": 0.0})

    world.say(
        f"At {setting.place}, under skies so bright, "
        f"{hero.id} wore {mystery.lost_phrase} with shining delight."
    )
    world.say(
        f"But then it was gone, and the room felt wrong; "
        f"{hero.id} looked around with a worried song."
    )

    world.para()
    hero.memes["worry"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f'{friend.id} said, "Do not fret, we will not roam, '
        f'we will search the soft {setting.mood} home."'
    )
    world.say(
        f"{mystery.tension_line} {friend.id} peeked by the stair, "
        f"while whispers of suspense floated in the air."
    )
    clue.meters["noticed"] += 1
    world.say(
        f"They spotted {mystery.clue} tucked near {mystery.clue_place}, "
        f"as if it had winked with a hiding face."
    )

    world.para()
    helper.memes["calm"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{helper.id} came gently, with a patient pace, "
        f"and asked them both to slow the chase."
    )
    world.say(
        f'"If you share what you know, we can solve this small doubt; '
        f'kind hands find answers by looking about."'
    )
    world.say(
        f"{mystery.reveal_line} {mystery.solved_place} was the clue, "
        f"and there sat the token, as good as new."
    )
    token.meters["found"] += 1
    hero.memes["hope"] += 1
    hero.memes["relief"] += 1
    friend.memes["joy"] += 1

    world.para()
    world.say(
        f"{hero.id} smiled wide and did not stay shy; "
        f"{hero.id} said, \"I will reciprocate and try.\""
    )
    world.say(
        f"So {hero.id} shared {mystery.reciprocal_gift} with {friend.id}, "
        f"and {friend.id} shared a grin that felt like a bend."
    )
    world.say(
        f"{helper.id} laughed softly, with warmth in the light, "
        f"and the lost little token was held all right."
    )
    hero.memes["joy"] += 1
    friend.memes["trust"] += 1
    helper.memes["joy"] += 1
    helper.memes["kindness"] += 1

    world.facts.update(
        setting=setting,
        mystery=mystery,
        hero=hero,
        friend=friend,
        helper=helper,
        token=token,
        clue=clue,
        solved=token.meters["found"] >= THRESHOLD,
        reciprocated=True,
    )
    return world


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="the cozy cottage",
        mood="sunlit",
        clues=["under the rug", "by the window", "near the chair"],
    ),
    "library": Setting(
        id="library",
        place="the little library",
        mood="quiet",
        clues=["behind a book cart", "beside the lamp", "under a table"],
    ),
    "garden": Setting(
        id="garden",
        place="the flower garden",
        mood="breezy",
        clues=["by the gate", "under a pot", "near the bench"],
    ),
}

MYSTERIES = {
    "music_box_key": Mystery(
        id="music_box_key",
        lost_item="the tiny key",
        lost_phrase="the tiny key to the music box",
        hiding_place="the teacup shelf",
        clue="a silver glimmer",
        clue_place="the teacup shelf",
        solved_place="the teacup shelf",
        rhymes_with="glee",
        tension_line="A silver clue was tricky to see,",
        reveal_line="The glimmer led them where the boxes could be,",
        reciprocal_gift="a paper crown",
        tags={"mystery", "key", "music_box"},
    ),
    "red_scarf": Mystery(
        id="red_scarf",
        lost_item="the red scarf",
        lost_phrase="the red scarf with a soft fringe",
        hiding_place="the coat stand",
        clue="a flutter of thread",
        clue_place="the coat stand",
        solved_place="the coat stand",
        rhymes_with="glow",
        tension_line="A flutter of thread was easy to miss,",
        reveal_line="The thread pointed straight to the place of bliss,",
        reciprocal_gift="a sticker star",
        tags={"mystery", "scarf"},
    ),
    "blue_shell": Mystery(
        id="blue_shell",
        lost_item="the blue shell",
        lost_phrase="the blue shell on a string",
        hiding_place="the basket edge",
        clue="a blue shine",
        clue_place="the basket edge",
        solved_place="the basket edge",
        rhymes_with="tune",
        tension_line="A blue shine blinked like moonlight's wish,",
        reveal_line="The shine slipped onward, quick as a fish,",
        reciprocal_gift="a shell bead",
        tags={"mystery", "shell"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Owen", "Theo", "Ben"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            combos.append((s, m))
    return combos


def explain_rejection() -> str:
    return "(No story: the mystery pieces do not fit the little rhyming world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming mystery world where characters solve a loss, "
                    "face a conflict, and reciprocate kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, mystery = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    helper = args.helper or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        hero_name=hero,
        hero_gender=hero_gender,
        friend_name=friend,
        friend_gender=friend_gender,
        helper_name=helper,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming mystery story for a little child where {f["hero"].id} and {f["friend"].id} look for {f["mystery"].lost_phrase} and solve the puzzle together.',
        f'Create a gentle suspense story that includes the word "reciprocate" and ends with {f["hero"].id} sharing a kind return gift.',
        f'Write a small rhyming story about a missing treasure, a clue, and a calm helper who helps solve the mystery at {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, helper = f["hero"], f["friend"], f["helper"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What went missing in {setting.place}?",
            answer=f"{mystery.lost_phrase} went missing, and that made {hero.id} feel worried. The story follows the search until the missing thing is found again.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve the mystery?",
            answer=f"They looked for a clue, stayed together, and followed the hint to {mystery.solved_place}. That careful search solved the puzzle without rushing past the answer.",
        ),
        QAItem(
            question=f"What did {helper.id} do when the search got tense?",
            answer=f"{helper.id} came with a calm voice and helped them slow down. That steadiness made the suspense easier to handle and let the clue do its work.",
        ),
        QAItem(
            question=f"How did {hero.id} reciprocate after the mystery was solved?",
            answer=f"{hero.id} reciprocated by sharing {mystery.reciprocal_gift} with {friend.id}. That kind return showed thanks and turned the ending warm and friendly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign that helps you figure something out. Clues can be shiny, hidden, or surprising, and they point the way to an answer.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next. It can make a story feel exciting while the characters search for answers.",
        ),
        QAItem(
            question="What does reciprocate mean?",
            answer="To reciprocate means to return a kind act with another kind act. If someone helps you, you may reciprocate by helping, sharing, or saying thank you in a warm way.",
        ),
        QAItem(
            question=f"What kind of thing is {mystery.lost_item} in this world?",
            answer=f"{mystery.lost_item} is the important object everyone is trying to find. It is the heart of the mystery, so the clues all point back to it.",
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
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
solved :- found(token).
reciprocated :- joy(hero), joy(friend), kindness(helper).
conflict :- worry(hero), curiosity(friend), not found(token).
suspense :- not found(token), clue(clue).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    lines.append(asp.fact("reciprocal_word", "reciprocate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        asp_set = set((s, m) for s, m in asp_valid_combos())
        ok_gate = py == asp_set
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        ok_story = bool(sample.story)
    except Exception as exc:
        print(f"FAIL: smoke test crashed: {exc}")
        return 1
    if ok_gate and ok_story:
        print(f"OK: ASP gate matches Python and smoke generation succeeded ({len(py)} combos).")
        return 0
    print("FAIL: ASP/Python mismatch or smoke test failure.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES:
        raise StoryError("invalid StoryParams")
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = tell(
        setting=setting,
        mystery=mystery,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
    )
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
    StoryParams(setting="cottage", mystery="music_box_key", hero_name="Lily", hero_gender="girl",
                friend_name="Max", friend_gender="boy", helper_name="Maya", helper_gender="mother"),
    StoryParams(setting="library", mystery="red_scarf", hero_name="Nora", hero_gender="girl",
                friend_name="Ben", friend_gender="boy", helper_name="Theo", helper_gender="father"),
    StoryParams(setting="garden", mystery="blue_shell", hero_name="Leo", hero_gender="boy",
                friend_name="Ava", friend_gender="girl", helper_name="Ella", helper_gender="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for s, m in asp_valid_combos():
            print(s, m)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
