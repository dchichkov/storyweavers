#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/energetic_surprise_bad_ending_twist_tall_tale.py
==================================================================================

A standalone storyworld for a tall-tale style surprise with a twist and a bad
ending. The tiny domain is a windy hill, a homemade kite, and an energetic child
who wants one last grand flight.

The story engine is state-driven: the kite has physical meters like `pull`,
`lift`, `strain`, and `lost`, and the people have emotional memes like `pride`,
`alarm`, and `sadness`. The ending is not always happy; the default arc here is a
surprising twist that leaves the kite gone for good.

Base seed prompt
-----------------
Write a story that includes the following words and narrative instruments.
Words: energetic
Features: Surprise, Bad Ending, Twist
Style: Tall Tale
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    gust: int
    allows: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risk: str
    strength: int
    lift: int
    tail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    object: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, Any] = {}

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
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label,
            traits=list(v.traits), role=v.role, attrs=dict(v.attrs),
            meters=defaultdict(float, v.meters), memes=defaultdict(float, v.memes)
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "hill": Setting(id="hill", place="the windy hill", sky="big and blue", gust=3, allows={"kite"}),
    "field": Setting(id="field", place="the wide field", sky="open and blustery", gust=2, allows={"kite"}),
    "dock": Setting(id="dock", place="the old dock", sky="salt-stung and windy", gust=4, allows={"kite"}),
}

OBJECTS = {
    "kite": ObjectCfg(
        id="kite",
        label="kite",
        phrase="a striped kite with a long tail",
        risk="the string",
        strength=2,
        lift=3,
        tail="the kite winked once, then danced away into the sky",
        tags={"kite", "wind"},
    ),
    "banner": ObjectCfg(
        id="banner",
        label="banner",
        phrase="a bright banner on a pole",
        risk="the pole",
        strength=4,
        lift=1,
        tail="the banner snapped and flapped like a flag in a storm",
        tags={"banner", "wind"},
    ),
}

CHILD_NAMES = ["Milo", "Nell", "Bess", "Ira", "Wren", "Otis", "June", "Arlo"]
HELPER_NAMES = ["Grandpa", "Aunt May", "Uncle Joe", "Mama", "Papa", "Big Sis"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            if oid in setting.allows:
                combos.append((sid, oid))
    return combos


def reasonableness_gate(setting: Setting, obj: ObjectCfg) -> bool:
    return obj.id in setting.allows


ASP_RULES = r"""
valid(S,O) :- setting(S), object(O), allows(S,O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for oid in setting.allows:
            lines.append(asp.fact("allows", sid, oid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale windy-kite storyworld with a surprise twist and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.object is None or c[1] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice([n for n in CHILD_NAMES if n != args.helper])
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    return StoryParams(setting=setting, object=obj, child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender)


def _make_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.object not in OBJECTS:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object]
    if not reasonableness_gate(setting, obj):
        raise StoryError("That object does not belong in that setting for this story.")
    w = World(setting)
    child = w.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child",
                         traits=["energetic"], attrs={"name": params.child}))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper",
                          traits=["old"], attrs={"name": params.helper}))
    toy = w.add(Entity(id="toy", kind="thing", type=obj.id, label=obj.label, attrs={"cfg": obj}))
    child.memes["energy"] = 2.0
    helper.memes["worry"] = 1.0
    return w


def _gust(world: World) -> None:
    world.get("toy").meters["lift"] += 1
    world.get("toy").meters["strain"] += 1
    world.get("toy").meters["lift"] += world.setting.gust


def tell_story(world: World) -> None:
    c = next(e for e in world.entities.values() if e.role == "child")
    h = next(e for e in world.entities.values() if e.role == "helper")
    toy = world.get("toy")
    cfg: ObjectCfg = toy.attrs["cfg"]

    world.say(
        f"On a day as big as a barn roof and twice as bright, {c.id} was so energetic "
        f"that {c.pronoun()} could have raced a wagon and still had breath left to sing."
    )
    world.say(
        f"{h.id} brought out {cfg.phrase} and said the kite ought to try the wind on {world.setting.place}."
    )

    world.para()
    world.say(
        f"{c.id} ran up the hill, laughing like thunder over a cornfield, and the string pulled tight."
    )
    _gust(world)
    world.say(
        f"Then came the surprise: a sneaky gust from nowhere at all snatched the air, yanked the string, and gave the whole thing a twist."
    )

    if toy.meters["lift"] >= cfg.lift:
        toy.meters["lost"] += 1
        c.memes["alarm"] += 1
        h.memes["alarm"] += 1
        world.say(
            f"The kite jumped higher than a fence post, higher than a chimney, higher than common sense, and the string snapped with a crack like a snapped branch."
        )
        world.say(
            f"{cfg.tail.capitalize()}. {c.id} shouted after it, but the wind was already carrying it over the far side of the hill."
        )
        world.para()
        world.say(
            f"{h.id} wrapped {h.pronoun('possessive')} arm around {c.id} and looked after the empty sky. "
            f'"That is a tall-tale twist if I ever saw one," {h.pronoun()} said, "and it ended with the kite gone for good."'
        )
        world.say(
            f"{c.id} nodded, hiccuping at the edge of tears, because the hill was still windy and the kite was already only a speck."
        )
    else:
        toy.meters["safe"] += 1
        world.say(
            f"But the wind was gentler than it looked, and the kite bobbed in place like a sleepy gull."
        )
        world.say(
            f"That was the end of the matter, and the day stayed simple."
        )

    world.facts.update(child=c, helper=h, toy=toy, cfg=cfg, ending="bad" if toy.meters["lost"] >= THRESHOLD else "safe")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall-tale story that uses the word 'energetic' and ends with a surprising twist about {f['cfg'].label}.",
        f"Tell a child-friendly tall tale where {f['child'].id} is energetic, a sudden gust changes everything, and the ending is bad because the toy is lost.",
        f"Write a windy adventure with a surprise and a twist, where a kite rises too high and never comes back.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    h = world.facts["helper"]
    toy: Entity = world.facts["toy"]
    cfg: ObjectCfg = world.facts["cfg"]
    qa = [
        QAItem(
            question=f"Why did {c.id} go up the hill?",
            answer=f"{c.id} wanted to fly the {cfg.label} in the wind. {c.pronoun().capitalize()} was so energetic that the hill seemed like the biggest possible place to race the breeze.",
        ),
        QAItem(
            question="What was the surprise in the story?",
            answer="A gust came out of nowhere and changed the flight at the exact moment everyone thought the kite was doing well. That surprise turned the playful scene into a twist.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly, because the {cfg.label} snapped free and was carried away. The children could still stand on the hill, but the toy was gone for good.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a gust of wind do?",
            answer="A gust is a sudden strong push of air. It can shove light things, tug on strings, and make kites or hats dart around.",
        ),
        QAItem(
            question="What is a kite?",
            answer="A kite is a light toy that flies in the wind on a string. It can rise high when the breeze is strong enough.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={dict((k, v) for k, v in e.meters.items() if v)} memes={dict((k, v) for k, v in e.memes.items() if v)}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1
    except Exception:
        return 1


CURATED = [
    StoryParams(setting="hill", object="kite", child="Milo", child_gender="boy", helper="Grandpa", helper_gender="boy"),
    StoryParams(setting="field", object="kite", child="June", child_gender="girl", helper="Aunt May", helper_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        try:
            sample = generate(CURATED[0])
            emit(sample)
        except Exception as exc:
            print(exc)
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        for s, o in asp_valid_combos():
            print(s, o)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            try:
                p = resolve_params(args, random.Random((args.seed or 0) + i))
                s = generate(p)
            except StoryError:
                print("No valid story could be made.")
                return
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
