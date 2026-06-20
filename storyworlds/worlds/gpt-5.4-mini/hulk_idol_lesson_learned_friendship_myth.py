#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hulk_idol_lesson_learned_friendship_myth.py
===========================================================================

A tiny, standalone storyworld in a mythic style.

Premise
-------
A child hears an old myth about a great hulk-like guardian idol in a village square.
The child and a friend are tempted to copy the mighty pose, but the idol's lesson
is about strength used gently, friendship, and learning to help rather than boast.

This world is intentionally small and classical:
- a child protagonist,
- a friend,
- a revered idol,
- a public place with a fragile offering,
- a mythic warning,
- a turn where friendship changes the choice,
- a lesson learned ending image.

The words "hulk" and "idol" are included in the generated prose.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    tags: set[str] = field(default_factory=set)

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
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    light: str
    wind: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Relic:
    id: str
    label: str
    title: str
    strength: int
    lesson: str
    gentle: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Temptation:
    id: str
    act: str
    boast: str
    risk: str
    charge: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Help:
    id: str
    act: str
    result: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_scorn(world: World) -> list[str]:
    out: list[str] = []
    idol = world.get("idol")
    if idol.meters["shaken"] < THRESHOLD:
        return out
    sig = ("scorn", idol.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["shame"] += 1
    world.get("offering").meters["spilled"] += 1
    out.append("__idol_quiver__")
    return out


CAUSAL_RULES = [Rule("scorn", "social", _r_scorn)]


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


def mythic_opening(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    child.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"In the old days, when the wind still sang over {setting.place}, {child.id} "
        f"and {friend.id} heard a tale of a mighty hulk who guarded the people with quiet hands."
    )
    world.say(
        f"At the center of the square stood an idol of the guardian, green with moss, "
        f"its face solemn beneath {setting.light} and its stone feet firm in the dust."
    )


def desire_to_impress(world: World, child: Entity, friend: Entity, temptation: Temptation) -> None:
    child.memes["pride"] += 1
    world.say(
        f'{child.id} lifted {child.pronoun("possessive")} chin. "{temptation.boast}" '
        f'{child.id} said, hoping to seem as mighty as the hulk from the tale.'
    )
    world.say(f"But {friend.id} frowned. The offering bowl and the little flowers were near the idol.")


def warning(world: World, friend: Entity, child: Entity, temptation: Temptation, relic: Relic) -> None:
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} touched {friend.pronoun("possessive")} heart and spoke softly. '
        f'"{temptation.risk}. {relic.lesson}"'
    )


def defy(world: World, child: Entity, temptation: Temptation, relic: Relic) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'Yet {child.id} stepped closer and tried to {temptation.act}. '
        f"The stone floor echoed like a drum, and the flowers trembled beside the idol."
    )
    world.get("idol").meters["shaken"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With one boastful motion, {child.id} made the idol's base tremble and the offering jar wobbled."
    )


def friendship_turn(world: World, child: Entity, friend: Entity, relic: Relic) -> None:
    child.memes["regret"] += 1
    friend.memes["loyalty"] += 1
    world.say(
        f"{friend.id} did not laugh. Instead {friend.id} held out a steady hand and said, "
        f'"A friend is not one who copies a hulk. A friend is one who helps lift what is falling."'
    )
    world.say(
        f"{child.id} looked at the shaky offering bowl and saw that the real strength was gentleness."
    )


def repair(world: World, child: Entity, friend: Entity, help_cfg: Help) -> None:
    child.memes["understanding"] += 1
    friend.memes["joy"] += 1
    world.get("idol").meters["shaken"] = 0.0
    world.get("offering").meters["spilled"] = 0.0
    world.say(
        f"Together they chose a better way: {help_cfg.act}, and the little flowers were set right again."
    )
    world.say(
        f"The idol stood calm once more, and its shadow seemed to nod at the two friends."
    )
    world.say(
        f"{child.id} bowed low and learned the lesson at last: strength is best when it protects, not when it boasts."
    )


def tell(setting: Setting, relic: Relic, temptation: Temptation, help_cfg: Help,
         child_name: str = "Lina", child_gender: str = "girl",
         friend_name: str = "Taro", friend_gender: str = "boy") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    idol = world.add(Entity(id="idol", label="idol", kind="thing", type="idol"))
    offering = world.add(Entity(id="offering", label="offering bowl", kind="thing", type="offering"))
    child.memes["curiosity"] += 1
    friend.memes["care"] += 1

    mythic_opening(world, child, friend, setting)
    world.para()
    desire_to_impress(world, child, friend, temptation)
    warning(world, friend, child, temptation, relic)
    world.para()
    defy(world, child, temptation, relic)
    world.say(
        f"The old people said the idol had once watched over the village like a hulk of living stone."
    )
    world.para()
    friendship_turn(world, child, friend, relic)
    repair(world, child, friend, help_cfg)

    world.facts.update(
        child=child,
        friend=friend,
        idol=idol,
        offering=offering,
        setting=setting,
        relic=relic,
        temptation=temptation,
        help_cfg=help_cfg,
        lesson_learned=child.memes["understanding"] >= THRESHOLD,
        friendship=f"{child.id} and {friend.id}",
    )
    return world


SETTINGS = {
    "village_square": Setting("village_square", "the village square", "moonlight", "soft night wind"),
    "temple_courtyard": Setting("temple_courtyard", "the temple courtyard", "sunrise", "warm dawn wind"),
    "harbor_plaza": Setting("harbor_plaza", "the harbor plaza", "sea light", "salt wind"),
}

RELICS = {
    "idol": Relic("idol", "idol", "lesson of the stone guardian", 5, "A proud hand can break what a careful hand can keep."),
    "statue": Relic("statue", "statue", "lesson of the watchful ancestor", 4, "Might is noble only when it keeps peace."),
}

TEMPTATIONS = {
    "boast": Temptation("boast", "beat the drum and strike the idol's base", "I can be as mighty as that old hulk!", "The idol is not for testing your strength.", "The wise do not prove themselves by making a ruin.", {"hulk", "idol"}),
    "climb": Temptation("climb", "climb upon the idol's pedestal", "Watch me stand like the hulk of the legends!", "Do not climb sacred stones.", "Friendship means knowing when to step down.", {"hulk", "idol"}),
}

HELPS = {
    "steady": Help("steady", "lift the fallen flowers and straighten the offering bowl", "the offering was set right", {"friendship"}),
    "sweep": Help("sweep", "sweep the petals back into a neat circle at the idol's feet", "the circle was whole again", {"friendship"}),
}

NAMES = [("Lina", "girl"), ("Mira", "girl"), ("Taro", "boy"), ("Kian", "boy"), ("Nori", "nonbinary")]
FRIEND_NAMES = [("Taro", "boy"), ("Kian", "boy"), ("Mina", "girl"), ("Sora", "girl"), ("Pax", "nonbinary")]


@dataclass
@dataclass
class StoryParams:
    setting: str
    relic: str
    temptation: str
    help_cfg: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for r in RELICS:
            for t in TEMPTATIONS:
                for h in HELPS:
                    combos.append((s, r, t, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about hulk, idol, lesson learned, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--help-cfg", dest="help_cfg", choices=HELPS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy", "nonbinary"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy", "nonbinary"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    temptation = args.temptation or rng.choice(list(TEMPTATIONS))
    help_cfg = args.help_cfg or rng.choice(list(HELPS))
    child_name, child_gender = (args.child_name, args.child_gender) if args.child_name and args.child_gender else rng.choice(NAMES)
    friend_name, friend_gender = (args.friend_name, args.friend_gender) if args.friend_name and args.friend_gender else rng.choice(FRIEND_NAMES)
    if child_name == friend_name:
        friend_name, friend_gender = "Pax", "nonbinary"
    return StoryParams(setting, relic, temptation, help_cfg, child_name, child_gender, friend_name, friend_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-style story for a young child that includes the words "hulk" and "idol" and ends with a lesson learned about friendship.',
        f"Tell a small village myth where {f['child'].id} and {f['friend'].id} face the tempting strength of the idol and choose a kinder path.",
        f'Write a gentle legend about an idol, a hulk-like boast, and a friendship lesson that ends with the offering put right again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    relic = f["relic"]
    temptation = f["temptation"]
    help_cfg = f["help_cfg"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {child.id} and {friend.id}, two friends who stood before an idol in the village. The story followed how they learned what true strength should look like."
        ),
        QAItem(
            question=f"What did {child.id} first want to do?",
            answer=f"{child.id} first wanted to {temptation.act}. {child.id} wanted to seem mighty like the hulk from the old tale, but that choice put the idol and the offering at risk."
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"{friend.id} reminded {child.id} about {relic.lesson.lower()} and helped by {help_cfg.act}. That turned the moment from boasting into friendship, and the idol's place was set right again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an idol in a myth?",
            answer="An idol is a respected statue or image that people honor. In myths, an idol can stand for a lesson, a memory, or a sacred promise."
        ),
        QAItem(
            question="What is a hulk in this story?",
            answer="A hulk here means something huge and powerful, like a giant guardian. The story uses that idea to show why strength should be calm and careful."
        ),
        QAItem(
            question="What does friendship mean in this world?",
            answer="Friendship means helping someone choose well, even when the choice is hard. A true friend protects, listens, and helps repair mistakes."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    out = ["--- world ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        out.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("village_square", "idol", "boast", "steady", "Lina", "girl", "Taro", "boy"),
    StoryParams("temple_courtyard", "statue", "climb", "sweep", "Mira", "girl", "Kian", "boy"),
]


def explain_rejection() -> str:
    return "(No story: this mythic world expects an idol, a tempting boast, and a friendship repair.)"


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for t in TEMPTATIONS:
        lines.append(asp.fact("temptation", t))
    for h in HELPS:
        lines.append(asp.fact("help_cfg", h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,T,H) :- setting(S), relic(R), temptation(T), help_cfg(H).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid_combos")
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, relic=None, temptation=None, help_cfg=None,
                                                            child_name=None, child_gender=None, friend_name=None, friend_gender=None),
                                        random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced story text.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], RELICS[params.relic], TEMPTATIONS[params.temptation], HELPS[params.help_cfg],
                 params.child_name, params.child_gender, params.friend_name, params.friend_gender)
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(" ".join(map(str, row)) for row in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
