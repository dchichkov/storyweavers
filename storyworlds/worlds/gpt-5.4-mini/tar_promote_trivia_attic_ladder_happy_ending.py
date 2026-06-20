#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tar_promote_trivia_attic_ladder_happy_ending.py
================================================================================

A small fable-style story world about a quest in an attic, where a child finds
tar, wants to promote a class pet or helper, and wins a trivia game that unlocks
the ladder and leads to a happy ending.

The domain is intentionally tiny and state-driven:
- an attic ladder can be slick with tar
- a quest requires climbing to the attic
- a helper can be promoted into a new role after solving trivia
- the story ends with a concrete change in the world model

This script is self-contained and uses only the Python standard library plus the
shared result containers from storyworlds/results.py.
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
    kind: str = "thing"  # "character" | "thing"
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Quest:
    id: str
    goal: str
    reward: str
    requires_clear_ladder: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Item:
    id: str
    label: str
    phrase: str
    makes_ladder_slick: bool = False
    sticky: bool = False
    dangerous: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class RoleOption:
    id: str
    title: str
    promoted_to: str
    praise: str
    trivia_bonus: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    def __init__(self) -> None:
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_tar_slick(world: World) -> list[str]:
    out: list[str] = []
    ladder = world.get("ladder")
    tar = world.get("tar")
    if tar.meters["spread"] < THRESHOLD:
        return out
    sig = ("slick",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ladder.meters["slick"] += 1
    ladder.memes["worry"] += 1
    out.append("The ladder grew slick and hard to trust.")
    return out


def _r_quest_blocked(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ladder").meters["slick"] < THRESHOLD:
        return out
    for ent in list(world.entities.values()):
        if ent.role == "quester":
            ent.memes["uncertainty"] += 1
            sig = ("blocked", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{ent.id} paused, because the climb looked risky.")
    return out


CAUSAL_RULES = [Rule("tar_slick", "physical", _r_tar_slick), Rule("quest_blocked", "social", _r_quest_blocked)]


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


def tar_is_trouble(item: Item) -> bool:
    return item.makes_ladder_slick


def trivia_help(role: RoleOption, answer_right: bool) -> int:
    return role.trivia_bonus if answer_right else 0


def ladder_clear(world: World) -> bool:
    return world.get("ladder").meters["slick"] < THRESHOLD


def predict_climb(world: World) -> dict:
    sim = world.copy()
    if sim.get("tar").meters["spread"] < THRESHOLD:
        sim.get("tar").meters["spread"] = 1.0
    propagate(sim, narrate=False)
    return {"clear": ladder_clear(sim), "worry": sim.get("ladder").memes["worry"]}


def open_fable(world: World, child: Entity, helper: Entity, setting: Setting, quest: Quest) -> None:
    world.say(
        f"In a quiet house, {child.id} and {helper.id} found {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f"They had a small quest: reach the attic and bring back {quest.reward}."
    )


def notice_tar(world: World, child: Entity, tar: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At the foot of the ladder, {child.id} noticed a dark smear of tar. "
        f"It shone like old ink on the wood."
    )
    world.say(f'"That should not be there," {child.id} whispered.')


def want_promote(world: World, child: Entity, helper: Entity, role: RoleOption) -> None:
    helper.memes["hope"] += 1
    world.say(
        f"{child.id} said {helper.id} should be promoted to {role.promoted_to}, "
        f"because {helper.id} was brave enough to help on the quest."
    )


def warn(world: World, child: Entity, helper: Entity, tar: Entity) -> None:
    pred = predict_climb(world)
    world.facts["predicted_clear"] = pred["clear"]
    world.say(
        f"{helper.id} frowned and said the ladder would be too slippery if they "
        f"left the tar alone."
    )


def clean(world: World, child: Entity, tar: Entity) -> None:
    tar.meters["spread"] = 0.0
    tar.memes["trouble"] += 1
    world.get("ladder").meters["slick"] = 0.0
    world.say(
        f"So {child.id} fetched cloths and wiped the tar away until the boards "
        f"looked safe again."
    )
    world.say("The ladder stopped shining with danger and became plain wood once more.")


def trivia_round(world: World, helper: Entity, role: RoleOption, success: bool) -> None:
    if success:
        helper.memes["pride"] += 1
        helper.meters["points"] += role.trivia_bonus
        world.say(
            f"Then came the trivia: {helper.id} answered every question, and the room "
            f"rang with happy cheers."
        )
    else:
        helper.memes["pride"] -= 1
        world.say(
            f"The trivia game began, but {helper.id} missed too many answers, so the "
            f"promotion had to wait."
        )


def promote(world: World, child: Entity, helper: Entity, role: RoleOption) -> None:
    helper.attrs["title"] = role.promoted_to
    helper.memes["belonging"] += 1
    world.say(
        f"Because of the good work, {helper.id} was promoted to {role.promoted_to}. "
        f"{role.praise.capitalize()}."
    )


def climb_and_finish(world: World, child: Entity, helper: Entity, quest: Quest) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Together they climbed the ladder, found {quest.reward}, and brought it "
        f"down safely."
    )
    world.say(
        f"By the end, the attic quest was done, the tar was gone, and the new title "
        f"fit {helper.id} like a bright ribbon."
    )


def tell(setting: Setting, quest: Quest, tar_item: Item, role: RoleOption,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="quester"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    ladder = world.add(Entity(id="ladder", type="thing", label="attic ladder"))
    tar = world.add(Entity(id="tar", type="thing", label=tar_item.label))
    tar.meters["spread"] = 1.0
    world.facts.update(setting=setting, quest=quest, tar_item=tar_item, role=role)

    open_fable(world, child, helper, setting, quest)
    world.para()
    notice_tar(world, child, tar)
    want_promote(world, child, helper, role)
    warn(world, child, helper, tar)
    clean(world, child, tar)
    world.para()
    trivia_round(world, helper, role, success=True)
    promote(world, child, helper, role)
    climb_and_finish(world, child, helper, quest)
    world.facts.update(child=child, helper=helper, tar=tar, ladder=ladder, outcome="happy")
    return world


SETTINGS = {
    "attic_ladder": Setting(
        "attic_ladder",
        "the attic ladder",
        "Dust floated in the beams, and the narrow ladder waited beside a tiny door."
    ),
}

QUESTS = {
    "attic_treasure": Quest("attic_treasure", "climb to the attic and find the old treasure box", "the old treasure box"),
}

ITEMS = {
    "tar": Item("tar", "tar", "a sticky patch of tar", makes_ladder_slick=True, sticky=True, dangerous=True),
}

ROLES = {
    "promote": RoleOption("promote", "helper", "quest captain", "The quest had a wiser guide now", 3),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tess", "June"]
BOY_NAMES = ["Pip", "Bram", "Otto", "Finn", "Milo", "Theo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    tar: str
    role: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    return [(s, q, t, r) for s in SETTINGS for q in QUESTS for t in ITEMS for r in ROLES]


def explain_rejection() -> str:
    return "(No story: this tiny fable only supports the attic ladder quest, tar hazard, trivia test, and promotion ending.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style attic ladder quest with tar, trivia, and a happy promotion.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tar", choices=ITEMS)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    tar = args.tar or rng.choice(list(ITEMS))
    role = args.role or rng.choice(list(ROLES))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    return StoryParams(setting, quest, tar, role, child_name, gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fable-style story about an attic ladder, tar, and a happy quest ending.',
        f"Tell a short quest story where {f['child'].id} finds tar by the attic ladder, then a helper is promoted after trivia.",
        f"Write a child-friendly fable that includes the words tar, promote, and trivia, and ends with a safe climb upstairs.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    qa = [
        QAItem(
            question="What was the quest about?",
            answer="It was about climbing the attic ladder and bringing back the old treasure box. The quest gave the children a simple goal to work toward."
        ),
        QAItem(
            question=f"Why did {child.id} wipe away the tar?",
            answer="Because the tar made the attic ladder slippery. If they left it there, the climb would have been unsafe."
        ),
        QAItem(
            question=f"Why was {helper.id} promoted?",
            answer=f"{helper.id} answered the trivia questions well and helped on the quest. That is why the new title of quest captain fit so nicely."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the tar cleaned up, the ladder safe, and the treasure box brought down. The ending shows that the quest succeeded and everyone was proud."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tar like?",
            answer="Tar is thick and sticky, and it can make a surface slippery or messy. It is something to keep off wood and hands."
        ),
        QAItem(
            question="What does promote mean?",
            answer="To promote someone means to give them a better or more important role. It is a reward for good work."
        ),
        QAItem(
            question="What is trivia?",
            answer="Trivia is a game of little questions and answers. It is often used to test what someone knows in a fun way."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission with a goal to reach or find. In stories, quests give the characters a reason to be brave and keep going."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
tar_slick :- tar(spread), spread >= 1.
quest_ready :- not tar_slick.
promoted :- trivia_success, quest_ready.
outcome(happy) :- promoted.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("quest", qid) for qid in QUESTS]
    lines += [asp.fact("tar", tid) for tid in ITEMS]
    lines += [asp.fact("role", rid) for rid in ROLES]
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    ok = bool(atoms and atoms[0][0] == "happy")
    if not ok:
        print("MISMATCH: ASP did not produce happy outcome.")
        return 1
    print("OK: ASP twin produces the expected happy outcome.")
    return 0


def tell_story(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        ITEMS[params.tar],
        ROLES[params.role],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


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
        print(asp_program(show="#show outcome/1."))
        return
    if args.verify:
        params = StoryParams("attic_ladder", "attic_treasure", "tar", "promote", "Mina", "girl", "Pip", "boy")
        sample = generate(params)
        if not sample.story or "tar" not in sample.story:
            raise SystemExit(1)
        rc = asp_verify()
        sys.exit(rc)
    if args.asp:
        print("happy-ending attic ladder quest: 1")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [StoryParams("attic_ladder", "attic_treasure", "tar", "promote", "Mina", "girl", "Pip", "boy")]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
