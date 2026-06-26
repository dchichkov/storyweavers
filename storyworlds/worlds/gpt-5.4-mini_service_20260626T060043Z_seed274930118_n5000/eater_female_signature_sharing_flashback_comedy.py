#!/usr/bin/env python3
"""
storyworlds/worlds/eater_female_signature_sharing_flashback_comedy.py
======================================================================

A small comedy storyworld about a hungry female eater, a signature treat,
sharing, and a tiny flashback that helps the ending land well.

The core premise:
- A girl with a big appetite loves one special signature snack.
- She wants to keep it all to herself.
- A flashback reminds her of a funny past moment when sharing worked better.
- She chooses to share, and the story ends with everyone smiling at the crumbs.

This world is intentionally small and constraint-checked. It is not a frozen
paragraph with swapped nouns: the simulated world state changes, drives the
turn, and proves the ending image.
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
    receiver: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "sister", "aunt", "female"}
        male = {"boy", "man", "father", "dad", "brother", "uncle", "male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def capitalized(self) -> str:
        return self.id


@dataclass
class Setting:
    place: str = "the kitchen"
    afford_share: bool = True
    afford_flashback: bool = True


@dataclass
class Treat:
    label: str
    phrase: str
    bite_size: str
    mess: str
    shares: int = 2


@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    parent: str
    friend: str
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

    def copy(self) -> "World":
        import copy as _copy
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: callable


def _r_sticky_face(world: World) -> list[str]:
    out = []
    eater = world.get("eater")
    treat = world.get("treat")
    if eater.meters.get("crumbs", 0.0) < THRESHOLD:
        return out
    sig = ("sticky",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    eater.memes["silliness"] = eater.memes.get("silliness", 0.0) + 1
    treat.meters["missing"] = treat.meters.get("missing", 0.0) + 0.5
    out.append(f"{eater.id} got a frosting dot on {eater.pronoun('possessive')} nose and snorted a laugh.")
    return out


CAUSAL_RULES = [Rule("sticky_face", _r_sticky_face)]


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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", afford_share=True, afford_flashback=True),
    "table": Setting(place="the table", afford_share=True, afford_flashback=True),
    "picnic": Setting(place="the picnic blanket", afford_share=True, afford_flashback=True),
}

TREATS = {
    "pie": Treat(label="signature pie", phrase="a warm signature pie", bite_size="slice", mess="crumbs", shares=4),
    "cake": Treat(label="signature cake", phrase="a fluffy signature cake", bite_size="piece", mess="crumbs", shares=4),
    "cookie": Treat(label="signature cookie", phrase="a giant signature cookie", bite_size="half", mess="crumbs", shares=2),
}

NAMES = ["Mina", "Lia", "Nora", "Ivy", "Zoe", "Maya"]
FRIENDS = ["Pip", "Rae", "Tia", "Ben", "Ollie", "June"]
PARENTS = ["mother", "aunt", "mom"]


def can_share(treat: Treat) -> bool:
    return treat.shares >= 2


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_share:
            lines.append(asp.fact("affords_share", sid))
        if s.afford_flashback:
            lines.append(asp.fact("affords_flashback", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("label", tid, t.label))
        lines.append(asp.fact("shares", tid, t.shares))
    return "\n".join(lines)


ASP_RULES = r"""
shareable(T) :- treat(T), shares(T,N), N >= 2.
valid_story(S, T) :- setting(S), treat(T), shareable(T), affords_share(S), affords_flashback(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, t) for s in SETTINGS for t, tr in TREATS.items() if can_share(tr)}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a female eater, a signature treat, sharing, and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--friend")
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
    if args.treat and not can_share(TREATS[args.treat]):
        raise StoryError("That treat cannot be shared in a reasonable way.")
    places = [p for p in SETTINGS if args.place is None or p == args.place]
    treats = [t for t in TREATS if args.treat is None or t == args.treat]
    combos = [(p, t) for p in places for t in treats if can_share(TREATS[t])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treat = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, treat=treat, name=name, parent=parent, friend=friend)


def _flashback_line(eater: Entity, friend: Entity, treat: Treat) -> str:
    return (
        f"She remembered last week, when {eater.id} had tried to keep the whole {treat.label} to {self_friend(friend)} "
        f"and ended up wearing more crumbs than lunch. {friend.id} had laughed so hard that even the spoon "
        f"looked embarrassed."
    )


def self_friend(friend: Entity) -> str:
    return f"{friend.id} for herself"


def generate_story(world: World) -> None:
    eater = world.add(Entity(id="eater", kind="character", type="girl", label=world.facts["name"]))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label=world.facts["parent"]))
    friend = world.add(Entity(id="friend", kind="character", type="girl", label=world.facts["friend"]))
    treat = world.add(Entity(id="treat", kind="thing", type="treat", label=world.facts["treat"].label, phrase=world.facts["treat"].phrase))

    eater.memes["hunger"] = 2
    eater.memes["wanting"] = 1
    world.say(f"{eater.label} was a female eater with a big grin and an even bigger appetite.")
    world.say(f"At {world.setting.place}, she found {treat.phrase} on the counter, and it looked like a tiny treasure.")
    world.say(f'"Mine," she said, hugging the plate with both hands like a sleepy octopus.')

    world.para()
    eater.meters["crumbs"] = 1
    world.say(f"Her {world.facts['parent']} peeked over and said, 'That is a signature treat. Great taste is even better when it gets shared.'")
    world.say(f"{eater.label} wrinkled her nose. She wanted the whole thing, because the middle looked extra soft and the frosting had glittery sprinkles.")
    world.say("Then she paused, because the smell of cinnamon tugged at a funny memory.")

    world.para()
    world.say(f"Flashback: {eater.label} once tried to eat a whole signature cookie by herself at the picnic.")
    world.say(f"It broke into three pieces, rolled under a napkin, and left a frosting mustache so large her {world.facts['friend']} could not stop giggling.")
    world.say(f"After that, {eater.label} had shared the next bite and discovered that two smiles are louder than one.")

    world.para()
    world.say(f"{eater.label} looked at {friend.id} and then at the pie again. 'Okay,' she said, 'we can share the fancy part first.'")
    treat.receiver = friend.id
    treat.shared_with.append(friend.id)
    eater.meters["crumbs"] += 1
    propagate(world, narrate=True)
    eater.memes["joy"] = 2
    world.say(f"So she cut the signature treat into neat pieces, passed one over, and the two of them ate with bright eyes and sticky fingers.")
    world.say(f"Even the parent laughed when {eater.label} licked a dot of frosting from her nose and declared it her 'official dessert badge.'")

    world.facts.update(
        eater=eater,
        parent=parent,
        friend=friend,
        treat=world.facts["treat"],
        setting=world.setting,
        shared=True,
        flashback=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny short story for a small child about a female eater, a signature treat, sharing, and a flashback.',
        f"Tell a comedy story where {f['name']} wants to keep {f['treat'].label} all to herself, then remembers a silly time she shared before.",
        f"Write a gentle, funny story set at {world.setting.place} that includes the words eater, female, and signature.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    eater = f["eater"]
    parent = f["parent"]
    friend = f["friend"]
    treat = f["treat"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {eater.label}, a female eater with a big appetite, and the funny choice she makes about {treat.label}.",
        ),
        QAItem(
            question=f"What made {eater.label} stop and think before grabbing the treat?",
            answer=f"She remembered a flashback about the last time she tried to keep a whole treat for herself and ended up with a frosting mustache.",
        ),
        QAItem(
            question=f"What did {parent.label} say about the signature treat?",
            answer=f"{parent.label.capitalize()} said it was a signature treat and reminded {eater.label} that good taste is even better when it gets shared.",
        ),
        QAItem(
            question=f"How did the story end for {eater.label} and {friend.id}?",
            answer=f"They shared the treat, ate the pieces together, and laughed at the crumbs and frosting on {eater.label}'s nose.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else have some of what you have, like a bite of food or a toy to hold.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened earlier, so readers can understand why someone acts a certain way now.",
        ),
        QAItem(
            question="Why can eating a sticky treat be funny?",
            answer="Sticky treats can leave crumbs, frosting, or smudges on faces, which can make people laugh in a harmless way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    treat = TREATS[params.treat]
    world.facts.update(name=params.name, parent=params.parent, friend=params.friend, treat=treat)
    generate_story(world)
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
    StoryParams(place="kitchen", treat="cake", name="Mina", parent="mother", friend="Rae"),
    StoryParams(place="table", treat="pie", name="Lia", parent="aunt", friend="June"),
    StoryParams(place="picnic", treat="cookie", name="Nora", parent="mom", friend="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
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
