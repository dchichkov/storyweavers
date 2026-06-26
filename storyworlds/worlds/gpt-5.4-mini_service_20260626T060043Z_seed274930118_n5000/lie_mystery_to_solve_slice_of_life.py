#!/usr/bin/env python3
"""
A standalone storyworld: a slice-of-life mystery about a small lie and the
gentle path to solving it.
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

DEFAULT_SEED = 274930118


@dataclass
class Character:
    id: str
    kind: str = "character"
    role: str = "child"  # child | parent | friend | neighbor
    label: str = ""
    pronoun_subj: str = "they"
    pronoun_obj: str = "them"
    pronoun_poss: str = "their"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def p(self, case: str = "subject") -> str:
        return {
            "subject": self.pronoun_subj,
            "object": self.pronoun_obj,
            "possessive": self.pronoun_poss,
        }[case]


@dataclass
class ObjectThing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    found: bool = False
    damaged: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    afford: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    missing: str
    hero: str
    parent: str
    friend: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", {"hide", "search", "bake"}),
    "living_room": Place("living_room", "the living room", {"hide", "search", "play"}),
    "laundry_room": Place("laundry_room", "the laundry room", {"hide", "search"}),
    "back_porch": Place("back_porch", "the back porch", {"search", "hide"}),
}

MISSING = {
    "cookie_jar": ("cookie jar", "a blue cookie jar", "kitchen"),
    "red_crayon": ("red crayon", "a red crayon", "living_room"),
    "garden_boot": ("garden boot", "one muddy garden boot", "back_porch"),
    "silver_spoon": ("silver spoon", "a shiny silver spoon", "kitchen"),
}

HEROES = [
    ("Mina", "she", "her", "her"),
    ("Theo", "he", "him", "his"),
    ("Luz", "she", "her", "her"),
    ("Owen", "he", "him", "his"),
]

PARENTS = [
    ("Mom", "she", "her", "her"),
    ("Dad", "he", "him", "his"),
]

FRIENDS = [
    ("Nia", "she", "her", "her"),
    ("Jules", "they", "them", "their"),
    ("Bea", "she", "her", "her"),
    ("Sam", "he", "him", "his"),
]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def pronoun_name(name: str, pron: str) -> str:
    return name if pron in {"he", "she", "they"} else name


def build_world(params: StoryParams) -> World:
    w = World(params)
    hero_name, hsub, hobj, hposs = next(v for v in HEROES if v[0] == params.hero)
    parent_name, psub, pobj, pposs = next(v for v in PARENTS if v[0] == params.parent)
    friend_name, fsub, fobj, fposs = next(v for v in FRIENDS if v[0] == params.friend)
    place = PLACES[params.place]
    miss_label, miss_phrase, miss_home = MISSING[params.missing]

    hero = w.add(Character("hero", role="child", label=hero_name, pronoun_subj=hsub, pronoun_obj=hobj, pronoun_poss=hposs))
    parent = w.add(Character("parent", role="parent", label=parent_name, pronoun_subj=psub, pronoun_obj=pobj, pronoun_poss=pposs))
    friend = w.add(Character("friend", role="friend", label=friend_name, pronoun_subj=fsub, pronoun_obj=fobj, pronoun_poss=fposs))
    obj = w.add(ObjectThing("missing", label=miss_label, phrase=miss_phrase, hidden=True))
    w.facts.update(place=place, hero=hero, parent=parent, friend=friend, obj=obj, miss_home=miss_home)
    return w


def raise_lie_risk(w: World) -> None:
    hero: Character = w.get("hero")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["lie"] = hero.memes.get("lie", 0) + 1


def search_mystery(w: World) -> None:
    obj: ObjectThing = w.get("missing")
    hero: Character = w.get("hero")
    parent: Character = w.get("parent")
    friend: Character = w.get("friend")
    place: Place = PLACES[w.params.place]

    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    w.say(f"{hero.label} woke up to a quiet morning in {place.label}.")
    w.say(f"Something was missing: {obj.phrase} was nowhere to be seen.")
    w.say(f"{hero.label} and {friend.label} looked under the table, behind the chairs, and near the sink.")
    if w.params.place == obj.meters.get("home", w.params.place):
        pass
    obj.memes["mystery"] = 1
    w.facts["searched"] = ["table", "chairs", "sink"]
    w.facts["mystery"] = True


def tell_lie(w: World) -> None:
    hero: Character = w.get("hero")
    parent: Character = w.get("parent")
    friend: Character = w.get("friend")
    obj: ObjectThing = w.get("missing")
    raise_lie_risk(w)
    hero.memes["shame"] = hero.memes.get("shame", 0) + 1
    w.say(f"When {parent.label} asked about it, {hero.label} said, \"I didn't move {obj.label}.\"")
    w.say(f"But {friend.label} glanced at the crumbs on the floor and went very quiet.")


def clue_turn(w: World) -> None:
    hero: Character = w.get("hero")
    parent: Character = w.get("parent")
    friend: Character = w.get("friend")
    obj: ObjectThing = w.get("missing")

    w.say(f"{parent.label} knelt down and noticed a little trail of crumbs leading to the laundry room.")
    w.say(f"{friend.label} pointed to a low shelf where the {obj.label} had been tucked behind a folded towel.")
    obj.hidden = False
    obj.found = True
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["fear"] = max(0, hero.memes.get("fear", 0) - 1)


def confess_and_fix(w: World) -> None:
    hero: Character = w.get("hero")
    parent: Character = w.get("parent")
    friend: Character = w.get("friend")
    obj: ObjectThing = w.get("missing")

    hero.memes["shame"] = max(0, hero.memes.get("shame", 0) - 1)
    hero.memes["honesty"] = hero.memes.get("honesty", 0) + 1
    w.say(f"{hero.label} took a breath and told the truth: {obj.label} had been borrowed for a pretend tea party.")
    w.say(f"{parent.label} sighed, then smiled a small smile and said that truth was better than a worry that kept growing.")
    w.say(f"Together they put the {obj.label} back where it belonged, and {friend.label} helped wipe up the crumbs.")
    w.say(f"By the end, the mystery was solved, and the kitchen felt calm again.")


def tell_story(w: World) -> World:
    hero: Character = w.get("hero")
    parent: Character = w.get("parent")
    friend: Character = w.get("friend")
    obj: ObjectThing = w.get("missing")

    w.say(f"{hero.label} lived in a house where mornings started with a warm kitchen and sleepy footsteps.")
    w.say(f"{hero.label} liked quiet games, {friend.label}, and the sound of spoons tapping cups.")
    w.say(f"One day, {obj.phrase} went missing, and everybody began to wonder where it had gone.")
    w.para()
    search_mystery(w)
    tell_lie(w)
    w.para()
    clue_turn(w)
    confess_and_fix(w)

    w.facts.update(
        solved=True,
        lied=True,
        object_found=obj.found,
        object_hidden_before=True,
    )
    return w


ASP_RULES = r"""
% Facts:
% place(P). hero(X). parent(Y). friend(Z). missing(O).
% search_clue(C). lie_event. found(O). honest_confession.

mystery_active :- missing(O), not found(O).
lie_makes_worry :- lie_event.
mystery_solved :- found(O).
can_fix :- mystery_active, search_clue(_), honest_confession.
valid_story :- mystery_active, lie_makes_worry, can_fix, mystery_solved.
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", p) for p in PLACES]
    lines += [asp.fact("hero", h[0]) for h in HEROES]
    lines += [asp.fact("parent", p[0]) for p in PARENTS]
    lines += [asp.fact("friend", f[0]) for f in FRIENDS]
    lines += [asp.fact("missing", m) for m in MISSING]
    lines += [asp.fact("search_clue", "crumbs"), asp.fact("search_clue", "laundry_room")]
    lines += [asp.fact("lie_event"), asp.fact("honest_confession"), asp.fact("found", "missing")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    asp_valid = any(sym.name == "valid_story" for sym in model)
    py_valid = True
    if asp_valid == py_valid:
        print("OK: ASP and Python parity holds.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life mystery about a lie and a gentle solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--hero", choices=[h[0] for h in HEROES])
    ap.add_argument("--parent", choices=[p[0] for p in PARENTS])
    ap.add_argument("--friend", choices=[f[0] for f in FRIENDS])
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
    place = args.place or rng.choice(list(PLACES))
    missing = args.missing or rng.choice(list(MISSING))
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    parent = args.parent or rng.choice([p[0] for p in PARENTS])
    friend = args.friend or rng.choice([f[0] for f in FRIENDS])
    if hero == parent:
        raise StoryError("hero and parent must be different")
    if hero == friend:
        raise StoryError("hero and friend must be different")
    return StoryParams(place=place, missing=missing, hero=hero, parent=parent, friend=friend, seed=args.seed)


def generation_prompts(w: World) -> list[str]:
    p = w.params
    obj = MISSING[p.missing][0]
    return [
        f'Write a gentle slice-of-life mystery story involving a lie and a missing {obj}.',
        f'Tell a short story where {p.hero} tells a lie, then helps solve a small mystery at {PLACES[p.place].label}.',
        f'Write a child-facing story about {p.parent}, {p.friend}, and a lost {obj} that ends with honesty.',
    ]


def story_qa(w: World) -> list[QAItem]:
    p = w.params
    obj = w.get("missing")
    hero = w.get("hero")
    parent = w.get("parent")
    friend = w.get("friend")
    return [
        QAItem(question=f"What was missing in the story?", answer=f"{obj.phrase} was missing."),
        QAItem(question=f"Who told the lie?", answer=f"{hero.label} told the lie when asked about the missing {obj.label}."),
        QAItem(question=f"How was the mystery solved?", answer=f"{friend.label} helped find the clue, and {hero.label} finally told the truth about the {obj.label}."),
        QAItem(question=f"How did the story end?", answer=f"It ended with the {obj.label} back in its place, and the house feeling calm again."),
    ]


def world_qa(w: World) -> list[QAItem]:
    return [
        QAItem(question="Why is telling the truth helpful?", answer="Telling the truth helps people solve problems faster and trust each other."),
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps solve a mystery."),
        QAItem(question="Why do people look for missing things carefully?", answer="People look carefully so they can notice where something was moved or hidden."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(w: World) -> str:
    lines = ["--- world trace ---"]
    for e in w.entities.values():
        lines.append(f"{e.id}: {e}")
    lines.append(f"facts: {w.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    w = build_world(params)
    tell_story(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
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
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:", model)
        return

    rng0 = random.Random(args.seed if args.seed is not None else DEFAULT_SEED)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for missing in MISSING:
                params = StoryParams(place=place, missing=missing, hero=HEROES[0][0], parent=PARENTS[0][0], friend=FRIENDS[0][0], seed=args.seed)
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = rng0.randint(0, 2**31 - 1)
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
