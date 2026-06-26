#!/usr/bin/env python3
"""
A small tall-tale storyworld about a misunderstanding that sends a child on a
quest, with a flashback that explains the mistake. The tale is designed to
produce one clear turn: something fiery gets distorted by rumor, the hero feels
ashamed, then finds the true fact and returns with pride.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Locale:
    place: str = "the old crossroads"
    has_lookout: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    truth: str
    distorted: str
    fiery: bool = False


@dataclass
class Quest:
    id: str
    verb: str
    destination: str
    reason: str
    reward: str
    involves_fire: bool = False


@dataclass
class Flashback:
    id: str
    trigger: str
    memory: str
    truth_reveal: str


class World:
    def __init__(self, locale: Locale) -> None:
        self.locale = locale
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.locale)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

LOCALES = {
    "crossroads": Locale(place="the old crossroads", has_lookout=True),
    "ridge": Locale(place="the windy ridge", has_lookout=True),
    "harbor": Locale(place="the lantern harbor", has_lookout=False),
}

CLUES = {
    "torch": Clue(
        id="torch",
        label="torch",
        phrase="a bright torch",
        truth="The torch was only a signal flame, not a wild fire.",
        distorted="a fiery monster had come to town",
        fiery=True,
    ),
    "banner": Clue(
        id="banner",
        label="banner",
        phrase="a red banner",
        truth="The banner was only red cloth in the sunset.",
        distorted="the sky itself was on fire",
        fiery=True,
    ),
    "kite": Clue(
        id="kite",
        label="kite",
        phrase="a high kite",
        truth="The kite was snagged in a tree, not trapped by a giant claw.",
        distorted="a sky-beast was clutching the clouds",
        fiery=False,
    ),
}

QUESTS = {
    "find": Quest(
        id="find",
        verb="go find the truth",
        destination="the lookout",
        reason="to learn what the strange sight really was",
        reward="a clear answer",
    ),
    "deliver": Quest(
        id="deliver",
        verb="carry the message",
        destination="the far hill",
        reason="to warn the neighbors without causing alarm",
        reward="a grateful smile",
        involves_fire=True,
    ),
    "ask": Quest(
        id="ask",
        verb="ask the keeper",
        destination="the lantern house",
        reason="to hear the story from someone who saw it first",
        reward="the real story",
    ),
}

FLASHBACKS = {
    "signal": Flashback(
        id="signal",
        trigger="the tall flame",
        memory="The hero once watched a signal fire blink on and off for help.",
        truth_reveal="That memory showed the flame was a message, not a monster.",
    ),
    "sunset": Flashback(
        id="sunset",
        trigger="the red glow",
        memory="The hero once saw the whole ridge turn red at sunset.",
        truth_reveal="That memory showed the red glow was light, not danger.",
    ),
    "kite_day": Flashback(
        id="kite_day",
        trigger="the snagged kite",
        memory="The hero once chased a kite and found it only needed a long stick.",
        truth_reveal="That memory showed the shape in the sky had a simple cause.",
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Ruby", "June", "Pearl", "Ada"]
BOY_NAMES = ["Boone", "Otis", "Jasper", "Theo", "Mack", "Eli"]


@dataclass
class StoryParams:
    locale: str
    clue: str
    quest: str
    flashback: str
    name: str
    gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is fiery if it can be mistaken for fire.
fiery(C) :- clue(C), fires_like(C).

% A misunderstanding exists when the distorted version is not the truth.
misunderstanding(C) :- clue(C), distorted(C, D), truth(C, T), D != T.

% A quest is reasonable if there is a misunderstanding and the quest can
% realistically resolve it by going to a place that can reveal the truth.
reasonable(L, C, Q, F) :- locale(L), clue(C), quest(Q), flashback(F),
                          misunderstanding(C), can_reveal(F, C), can_answer(Q, C).

#show reasonable/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid in LOCALES:
        lines.append(asp.fact("locale", lid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("distorted", cid, c.distorted))
        lines.append(asp.fact("truth", cid, c.truth))
        if c.fiery:
            lines.append(asp.fact("fires_like", cid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("can_answer", qid, "torch" if qid != "ask" else "kite"))
    for fid, f in FLASHBACKS.items():
        lines.append(asp.fact("flashback", fid))
        if f.id == "signal":
            lines.append(asp.fact("can_reveal", fid, "torch"))
        if f.id == "sunset":
            lines.append(asp.fact("can_reveal", fid, "banner"))
        if f.id == "kite_day":
            lines.append(asp.fact("can_reveal", fid, "kite"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for loc in LOCALES:
        for clue in CLUES:
            for quest in QUESTS:
                for fb in FLASHBACKS:
                    if clue == "torch" and quest in {"find", "deliver"} and fb == "signal":
                        combos.append((loc, clue, quest, fb))
                    if clue == "banner" and quest in {"deliver", "ask"} and fb == "sunset":
                        combos.append((loc, clue, quest, fb))
                    if clue == "kite" and quest in {"find", "ask"} and fb == "kite_day":
                        combos.append((loc, clue, quest, fb))
    return combos


def explain_rejection(clue: Clue, quest: Quest, fb: Flashback) -> str:
    return (
        f"(No story: the clue '{clue.label}' and the quest '{quest.id}' do not fit "
        f"the same tall-tale misunderstanding, so the flashback '{fb.id}' would not "
        f"genuinely clear things up.)"
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def tell(locale: Locale, clue: Clue, quest: Quest, fb: Flashback, name: str, gender: str) -> World:
    world = World(locale)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    keeper = world.add(Entity(id="Keeper", kind="character", type="keeper", label="the keeper"))
    clue_ent = world.add(Entity(id="Clue", type="thing", label=clue.label, phrase=clue.phrase))

    world.facts.update(hero=hero, keeper=keeper, clue=clue, quest=quest, flashback=fb, locale=locale)

    hero.memes["curiosity"] = 1
    world.say(
        f"{hero.id} lived near {locale.place}, where the wind could whip a whisper into a roar."
    )
    world.say(
        f"One evening, {hero.pronoun('subject')} saw {clue.phrase} and heard a rumor that "
        f"made it sound like {clue.distorted}."
    )
    hero.memes["fear"] = 1
    hero.memes["shame"] = 1
    world.say(
        f"{hero.id} felt ashamed for nearly believing it, because {clue.truth.lower()}"
    )

    world.para()
    hero.memes["questing"] = 1
    world.say(
        f"So {hero.id} set out on a {quest.verb} at {quest.destination}, {quest.reason}."
    )
    world.say(
        f"The path was long and tall as a ladder to the clouds, but {hero.id} kept going with a brave heart."
    )

    world.para()
    hero.memes["doubt"] = 1
    world.say(
        f"At the edge of the road, {fb.memory}"
    )
    world.say(
        f"That flashback changed everything: {fb.truth_reveal}"
    )
    hero.memes["shame"] = 0
    hero.memes["pride"] = 1

    world.para()
    world.say(
        f"{hero.id} hurried back and told {keeper.pronoun('object')} the truth, and the rumor shrank down to its proper size."
    )
    world.say(
        f"By dawn, the whole place looked friendly again, and {hero.id} stood tall, no longer ashamed, with {quest.reward} in {hero.pronoun('possessive')} pocket."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall-tale story about {f['hero'].id} who mistakes {f['clue'].label} for {f['clue'].distorted}.",
        f"Tell a story with a misunderstanding, a quest, and a flashback that clears up a fiery rumor.",
        f"Write a child-facing tale where a small traveler feels ashamed, goes on a quest, and learns the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    clue: Clue = f["clue"]  # type: ignore[assignment]
    quest: Quest = f["quest"]  # type: ignore[assignment]
    fb: Flashback = f["flashback"]  # type: ignore[assignment]
    locale: Locale = f["locale"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} think {clue.label} meant at first?",
            answer=f"{hero.id} first thought it meant {clue.distorted}. That was the misunderstanding.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel ashamed before starting the quest?",
            answer=f"{hero.id} felt ashamed because the first thought was wrong, and the truth was that {clue.truth.lower()}",
        ),
        QAItem(
            question=f"What did {hero.id} do to fix the misunderstanding at {locale.place}?",
            answer=f"{hero.id} went on a quest to {quest.verb}, then used the flashback about {fb.trigger} to understand the truth.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=fb.truth_reveal,
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} ended the story standing tall and proud, no longer ashamed, after learning the truth and telling it back.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "fiery": [
        QAItem(
            question="What does fiery mean?",
            answer="Fiery means full of fire, heat, or a strong flame-like feeling.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what is really happening.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find something, learn something, or help someone.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story steps back to an earlier memory that helps explain the present.",
        )
    ],
    "ashamed": [
        QAItem(
            question="What does ashamed mean?",
            answer="Ashamed means feeling sorry or embarrassed about something you did or thought.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        item
        for key in ["fiery", "misunderstanding", "quest", "flashback", "ashamed"]
        for item in WORLD_KNOWLEDGE[key]
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params, parser, generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale world: misunderstanding, quest, flashback.")
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_named_combos() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_named_combos()
              if (args.locale is None or c[0] == args.locale)
              and (args.clue is None or c[1] == args.clue)
              and (args.quest is None or c[2] == args.quest)
              and (args.flashback is None or c[3] == args.flashback)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    locale, clue, quest, fb = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("invalid gender")
    return StoryParams(locale=locale, clue=clue, quest=quest, flashback=fb, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCALES[params.locale], CLUES[params.clue], QUESTS[params.quest], FLASHBACKS[params.flashback], params.name, params.gender)
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


CURATED = [
    StoryParams("crossroads", "torch", "find", "signal", "Mira", "girl"),
    StoryParams("ridge", "banner", "deliver", "sunset", "Boone", "boy"),
    StoryParams("harbor", "kite", "ask", "kite_day", "Ruby", "girl"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} / {p.quest} / {p.flashback}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
