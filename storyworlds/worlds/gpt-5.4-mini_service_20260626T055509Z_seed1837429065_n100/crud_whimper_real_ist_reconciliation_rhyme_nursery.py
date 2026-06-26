#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a tiny quarrel, a bit of crud, a
whimper, and a real-ist who notices what is true and helps with reconciliation.

The domain is intentionally simple:
- two friends
- one small mess
- a hurt feeling
- a rhyme that helps them make up
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    mess: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": "the nursery",
    "garden": "the little garden",
    "kitchen": "the sunny kitchen",
}

HEROES = {
    "Pip": ("boy", "Pip"),
    "Dot": ("girl", "Dot"),
    "Milo": ("boy", "Milo"),
    "Nina": ("girl", "Nina"),
}

FRIENDS = {
    "Bea": ("girl", "Bea"),
    "Toby": ("boy", "Toby"),
    "Luna": ("girl", "Luna"),
    "Finn": ("boy", "Finn"),
}

MESSES = {
    "crumbs": {
        "label": "crumbs",
        "phrase": "tiny biscuit crumbs",
        "meter": "crumby",
        "cause": "nibbled biscuits too fast",
        "cleaning": "swept the crumbs into a neat little heap",
        "rhyme": "Crumbs be small, but they can crawl.",
    },
    "paint": {
        "label": "paint",
        "phrase": "bright paint spots",
        "meter": "painty",
        "cause": "tapped the paint pot with a curious paw",
        "cleaning": "wiped the paint away with a soft cloth",
        "rhyme": "Paint may splash, but feelings can dash.",
    },
    "mud": {
        "label": "mud",
        "phrase": "muddy toe marks",
        "meter": "muddy",
        "cause": "stomped after a rainy hop",
        "cleaning": "rinsed the muddy toe marks clean",
        "rhyme": "Mud can stick, but kindness is quick.",
    },
}

CURATED = [
    StoryParams(setting="nursery", hero="Pip", friend="Bea", mess="crumbs"),
    StoryParams(setting="garden", hero="Dot", friend="Toby", mess="mud"),
    StoryParams(setting="kitchen", hero="Milo", friend="Luna", mess="paint"),
]


class StoryWorld:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.world = World(setting=SETTINGS[params.setting])
        hero_kind, hero_label = HEROES[params.hero]
        friend_kind, friend_label = FRIENDS[params.friend]
        self.hero = self.world.add(Entity(id=params.hero, kind="character", type=hero_kind, label=hero_label))
        self.friend = self.world.add(Entity(id=params.friend, kind="character", type=friend_kind, label=friend_label))
        self.mess = MESSES[params.mess]
        self.secret = self.world.add(Entity(
            id="secret",
            kind="thing",
            type="thing",
            label="a little story",
            phrase="a small real-ist truth",
        ))
        self.word = self.world.add(Entity(
            id="rhyme",
            kind="thing",
            type="thing",
            label="a rhyme",
            phrase="a simple rhyme",
        ))
        self.world.facts.update(
            setting=params.setting,
            hero=self.hero,
            friend=self.friend,
            mess=params.mess,
            mess_info=self.mess,
            rhyme=self.word,
            secret=self.secret,
        )

    def tell(self) -> World:
        w = self.world
        h = self.hero
        f = self.friend
        m = self.mess

        h.memes["curious"] = 1
        f.memes["busy"] = 1
        w.say(f"Little {h.label} and little {f.label} lived in {w.setting}.")
        w.say(f"They liked to skip and sing, for nursery days were merry and thin with misty light.")
        w.say(f"But one day {h.label} {m['cause']}, and the room got {m['label']}.")

        w.para()
        h.memes["worry"] = 1
        f.memes["hurt"] = 1
        w.say(f"{f.label} looked at the mess and gave a tiny whimper.")
        w.say(f"{h.label} felt very still. The air went quiet as a mouse.")

        w.para()
        h.memes["realist"] = 1
        w.say(f"{h.label} was a real-ist and spoke the true small truth: '{m['label']} is here, and it will not vanish by itself.'")
        w.say(f"Then {h.label} found a rhyme: '{m['rhyme']}'")
        w.say(f"The rhyme made the room feel softer, like wool in winter.")

        f.memes["calmer"] = 1
        h.memes["care"] = 1
        w.para()
        w.say(f"{f.label} took a breath and nodded.")
        w.say(f"Together they {m['cleaning']}, and the floor shone again.")
        w.say(f"{h.label} said sorry, {f.label} said it's all right, and the two friends made up at the end of the night.")

        h.memes["reconciled"] = 1
        f.memes["reconciled"] = 1
        w.facts["resolved"] = True
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about crud, whimper, and reconciliation.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--mess", choices=sorted(MESSES))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    friend = args.friend or rng.choice(list(FRIENDS))
    mess = args.mess or rng.choice(list(MESSES))
    if hero == friend:
        raise StoryError("hero and friend must be different children.")
    return StoryParams(setting=setting, hero=hero, friend=friend, mess=mess)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story about {f["hero"].label} and {f["friend"].label} in {world.setting} with {f["mess"]}.',
        f"Tell a gentle story where a real-ist child notices {f['mess']} and uses a rhyme to help with reconciliation.",
        f'Write a short child-facing tale that includes the words "crud", "whimper", and "real-ist".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = f["hero"].label
    fr = f["friend"].label
    mess = f["mess_info"]["label"]
    return [
        QAItem(
            question=f"Who was the real-ist in the story?",
            answer=f"{h} was the real-ist, because {h} noticed the truth about the {mess} and spoke it clearly.",
        ),
        QAItem(
            question=f"Why did {fr} whimper?",
            answer=f"{fr} whimpered because the room was messy and the little trouble made {fr} feel hurt for a moment.",
        ),
        QAItem(
            question="What helped the friends make up?",
            answer=f"A simple rhyme helped them calm down, clean the mess, and find reconciliation together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is crud?",
            answer="Crud is a word for yucky little dirt or mess that does not belong on the floor or on things.",
        ),
        QAItem(
            question="What does whimper mean?",
            answer="To whimper is to make a small, soft cry when you feel sad, shy, or hurt.",
        ),
        QAItem(
            question="What does real-ist mean here?",
            answer="A real-ist is someone who notices what is true and says it plainly, even when it is a little uncomfortable.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a hurt feeling or a quarrel, so friends can be kind again.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little song or line where words sound alike at the end, which can make speech feel playful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).
mess(M) :- mess_name(M).
reconciliation(H,F) :- hero(H), friend(F), H != F, shared_rhyme(H,F), honest_truth(H), apology(H,F).
rhyme_help(M) :- mess(M), soothing_rhyme(M).
valid_story(S,H,F,M) :- setting(S), hero(H), friend(F), mess(M), H != F, reconciliation(H,F), rhyme_help(M).
#show valid_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HEROES:
        lines.append(asp.fact("hero_name", h))
    for f in FRIENDS:
        lines.append(asp.fact("friend_name", f))
    for m in MESSES:
        lines.append(asp.fact("mess_name", m))
        lines.append(asp.fact("soothing_rhyme", m))
    lines.append(asp.fact("shared_rhyme", "any", "any"))
    lines.append(asp.fact("honest_truth", "any"))
    lines.append(asp.fact("apology", "any", "any"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid_story/4.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for s in SETTINGS:
        for h in HEROES:
            for f in FRIENDS:
                for m in MESSES:
                    if h != f:
                        py_set.add((s, h, f, m))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        sample = generate(resolve_params(argparse.Namespace(setting=None, hero=None, friend=None, mess=None), random.Random(7)))
        if not sample.story or "reconciliation" not in sample.story.lower():
            raise StoryError("verification story did not exercise reconciliation.")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = StoryWorld(params).tell()
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


def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} compatible stories:")
        for row in atoms:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = valid_params(args, random.Random(seed))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
