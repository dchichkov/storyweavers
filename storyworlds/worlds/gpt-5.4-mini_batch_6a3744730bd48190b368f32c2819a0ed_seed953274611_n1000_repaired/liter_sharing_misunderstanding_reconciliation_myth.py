#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/liter_sharing_misunderstanding_reconciliation_myth.py
=====================================================================================

A tiny mythic storyworld about sharing a single liter of something precious,
a misunderstanding over how it should be divided, and a reconciliation that
restores harmony.

The world is deliberately small and classical:
- a sacred vessel holds exactly one liter of a gifted substance
- two figures care about fairness, but one act is misunderstood
- an elder or mediator helps them repair the hurt and share wisely

The story must always include the word "liter" and read with a myth-like tone.
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
MEME_HIGH = 1.0
LITER = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goddess", "priestess"}
        male = {"boy", "father", "man", "god", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    vessel: str
    gift: str
    blessing: str
    style_note: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SharingPattern:
    id: str
    action: str
    share_text: str
    fair_text: str
    tag: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Misunderstanding:
    id: str
    cause: str
    speech: str
    hurt_text: str
    tag: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Reconciliation:
    id: str
    helper_text: str
    repair_text: str
    ending_text: str
    tag: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bearer").memes["hurt"] >= THRESHOLD and world.get("other").memes["kindness"] >= THRESHOLD:
        sig = ("soften",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("bearer").memes["softened"] += 1
            world.get("other").memes["softened"] += 1
            out.append("__soften__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("soften", _r_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_sharing(sharing: SharingPattern) -> bool:
    return sharing.id in SHARING and "liter" in sharing.share_text


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for share_id, share in SHARING.items():
            for mis_id, mis in MISUNDERSTANDINGS.items():
                for rec_id, rec in RECONCILIATIONS.items():
                    if "liter" in share.share_text and mis.cause and rec.helper_text:
                        combos.append((setting_id, share_id, mis_id))
    return combos


def honest_warning(world: World, bearer: Entity, other: Entity, mis: Misunderstanding) -> bool:
    bearer.memes["hope"] += 1
    if bearer.meters["shared"] < LITER:
        return False
    world.say(
        f'{bearer.id} lifted the vessel and offered a full liter to {other.id}. '
        f'But {other.id} heard {mis.speech} and thought the gift was being withheld.'
    )
    return True


def misunderstanding_beats(world: World, bearer: Entity, other: Entity, mis: Misunderstanding, setting: Setting) -> None:
    bearer.memes["hurt"] += 1
    other.memes["hurt"] += 1
    world.say(
        f'{other.id} frowned and said, "{mis.speech}" '
        f'{mis.cause} sounded like a riddle under the moon.'
    )
    world.say(
        f'Their voices rose among the stones of {setting.place}, and the holy hush grew heavy.'
    )


def mediator_arrives(world: World, mediator: Entity, bearer: Entity, other: Entity, rec: Reconciliation, setting: Setting) -> None:
    mediator.memes["wisdom"] += 1
    world.say(
        f'{mediator.id} came like a lantern-bearer at dawn. "{rec.helper_text}" '
        f'{mediator.pronoun().capitalize()} said, seeing the hurt between them.'
    )


def repair(world: World, bearer: Entity, other: Entity, rec: Reconciliation, setting: Setting) -> None:
    bearer.memes["hurt"] = 0
    other.memes["hurt"] = 0
    bearer.memes["peace"] += 1
    other.memes["peace"] += 1
    world.get("vessel").meters["empty"] = 1
    world.say(rec.repair_text)
    world.say(
        f'Then the two of them shared the liter again, this time with open hands, '
        f'and the old quarrel fell away like ash from an altar.'
    )
    world.say(rec.ending_text)


def tell(setting: Setting, sharing: SharingPattern, misunderstanding: Misunderstanding,
         reconciliation: Reconciliation, bearer_name: str, other_name: str,
         mediator_name: str) -> World:
    world = World()
    bearer = world.add(Entity(id=bearer_name, kind="character", type="boy", role="bearer"))
    other = world.add(Entity(id=other_name, kind="character", type="girl", role="other"))
    mediator = world.add(Entity(id=mediator_name, kind="character", type="priestess", role="mediator"))
    vessel = world.add(Entity(id="vessel", kind="thing", type="vessel", label=setting.vessel))
    bearer.meters["shared"] = 1.0
    bearer.memes["kindness"] = 1.0
    other.memes["kindness"] = 1.0

    world.say(
        f'In the age when rivers remembered names, {bearer.id} and {other.id} met beside {setting.place}. '
        f'The sky was {setting.sky}, and the gods had left them a single liter of {setting.gift}.'
    )
    world.say(
        f'{sharing.share_text} {setting.style_note}.'
    )

    world.para()
    if honest_warning(world, bearer, other, misunderstanding):
        misunderstanding_beats(world, bearer, other, misunderstanding, setting)
        world.para()
        mediator_arrives(world, mediator, bearer, other, reconciliation, setting)
        repair(world, bearer, other, reconciliation, setting)
    else:
        world.say(
            f'Yet the measure was plain, and no shadow rose between them; they shared the liter in peace.'
        )

    world.facts.update(
        setting=setting,
        sharing=sharing,
        misunderstanding=misunderstanding,
        reconciliation=reconciliation,
        bearer=bearer,
        other=other,
        mediator=mediator,
        vessel=vessel,
        outcome="reconciled",
    )
    return world


SETTINGS = {
    "spring": Setting(
        id="spring",
        place="the spring at the hill's foot",
        sky="blue and watchful",
        vessel="stone bowl",
        gift="sweet water",
        blessing="a blessing for thirsty travelers",
        style_note="The old path glimmered, as if the hills themselves were listening",
    ),
    "temple": Setting(
        id="temple",
        place="the temple courtyard",
        sky="golden and still",
        vessel="bronze cup",
        gift="milk",
        blessing="a blessing for the temple lamps",
        style_note="The carved lions watched in silence while the wind brushed the flags",
    ),
    "grove": Setting(
        id="grove",
        place="the cypress grove",
        sky="silver with evening",
        vessel="clay jar",
        gift="honey",
        blessing="a blessing for the sleeping trees",
        style_note="The roots beneath their feet felt old as songs",
    ),
}

SHARING = {
    "pour_once": SharingPattern(
        id="pour_once",
        action="shared it",
        share_text="They agreed to pour the liter into the vessel and split it fairly.",
        fair_text="Both would receive the same measure, and neither would go thirsty.",
    ),
    "measure_carefully": SharingPattern(
        id="measure_carefully",
        action="measured it",
        share_text="They measured the liter with a reed and marked each cup with care.",
        fair_text="Fairness could be seen in the marks, clear as moonlit lines.",
    ),
    "offer_first": SharingPattern(
        id="offer_first",
        action="offered it first",
        share_text="One offered the liter first, trusting the other to take only what was meant.",
        fair_text="A first gift can be a bridge when hearts are gentle.",
    ),
}

MISUNDERSTANDINGS = {
    "too_little": Misunderstanding(
        id="too_little",
        cause="because the other thought the first pour meant refusal",
        speech="You gave me too little",
        hurt_text="The words stung, for the giver had meant kindness, not stinginess.",
    ),
    "taking_all": Misunderstanding(
        id="taking_all",
        cause="because the other feared the whole liter would be kept away",
        speech="You meant to keep it all",
        hurt_text="The fear was quick, and it made a small share seem like a great wound.",
    ),
    "shadow_sign": Misunderstanding(
        id="shadow_sign",
        cause="because a shadow on the bowl looked like an omen",
        speech="The gods are angry",
        hurt_text="The shadow made a harmless moment seem dark and dangerous.",
    ),
}

RECONCILIATIONS = {
    "elder_words": Reconciliation(
        id="elder_words",
        helper_text="A fair share is still a real gift, even when it comes in two hands",
        repair_text="The mediator lifted the bowl and showed them the marks, one for each heart.",
        ending_text="The sky seemed gentler, and the birds returned to the branches above them.",
    ),
    "shared_drink": Reconciliation(
        id="shared_drink",
        helper_text="Drink together, and let the measure be a vow of peace",
        repair_text="She guided their hands so they drank in turn from the same vessel, without hurry.",
        ending_text="By the end, the liter had become a treaty, and the treaty had become a song.",
    ),
    "promise_oath": Reconciliation(
        id="promise_oath",
        helper_text="Speak the truth again, and let the misunderstanding fall away",
        repair_text="They spoke their hurts aloud, and the speaking itself made room for mercy.",
        ending_text="After that, the hill remembered them not as rivals, but as companions.",
    ),
}

NAMES = ["Ari", "Mira", "Taro", "Lena", "Sorin", "Iria", "Niko", "Dara"]


@dataclass
class StoryParams:
    setting: str
    sharing: str
    misunderstanding: str
    reconciliation: str
    bearer: str
    other: str
    mediator: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def valid_setting_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about sharing one liter, misunderstanding, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sharing", choices=SHARING)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--bearer")
    ap.add_argument("--other")
    ap.add_argument("--mediator")
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
    combos = [
        (sid, shid, mid, rid)
        for sid in SETTINGS
        for shid in SHARING
        for mid in MISUNDERSTANDINGS
        for rid in RECONCILIATIONS
        if "liter" in SHARING[shid].share_text
    ]
    if args.setting and args.sharing and args.misunderstanding and args.reconciliation:
        if (args.setting, args.sharing, args.misunderstanding, args.reconciliation) not in combos:
            raise StoryError("That mythic combination cannot be made into a fair sharing story.")
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.sharing is None or c[1] == args.sharing)
        and (args.misunderstanding is None or c[2] == args.misunderstanding)
        and (args.reconciliation is None or c[3] == args.reconciliation)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sharing, misunderstanding, reconciliation = rng.choice(sorted(filtered))
    return StoryParams(
        setting=setting,
        sharing=sharing,
        misunderstanding=misunderstanding,
        reconciliation=reconciliation,
        bearer=args.bearer or rng.choice(NAMES),
        other=args.other or rng.choice([n for n in NAMES if n != (args.bearer or "")]),
        mediator=args.mediator or rng.choice([n for n in NAMES if n not in {args.bearer or "", args.other or ""}]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a child that uses the word "liter" and shows sharing, misunderstanding, and reconciliation.',
        f"Tell a gentle myth about {f['bearer'].id} and {f['other'].id} sharing one liter at {f['setting'].place}, then making peace again.",
        f'Write a short myth where a sacred liter of {f["setting"].gift} is shared fairly after a hurt feeling is repaired.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Setting = f["setting"]
    sh: SharingPattern = f["sharing"]
    mis: Misunderstanding = f["misunderstanding"]
    rec: Reconciliation = f["reconciliation"]
    bearer: Entity = f["bearer"]
    other: Entity = f["other"]
    mediator: Entity = f["mediator"]
    answers = [
        QAItem(
            question="What was being shared?",
            answer=f"They were sharing one liter of {s.gift}. In the myth, that small measure mattered because it was precious and meant to be divided fairly.",
        ),
        QAItem(
            question="What went wrong?",
            answer=f"{other.id} misunderstood the sharing and spoke as if the gift were being withheld. {mis.speech} sounded like a complaint, so the moment turned sharp even though the first act was meant kindly.",
        ),
        QAItem(
            question="How was the misunderstanding fixed?",
            answer=f"{mediator.id} helped them look again at the share and speak truthfully. That turned the hurt into reconciliation, and both could receive the liter with peace.",
        ),
        QAItem(
            question="Why does the ending feel calm?",
            answer=f"Because the hearts of {bearer.id} and {other.id} were softened before the story ended. Once they shared the liter again, the place felt blessed instead of divided.",
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a liter?",
            answer="A liter is a way to measure liquid. It is a little more than a quart, and people use it when they want to know how much water, milk, or honey there is.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use or have something. When people share kindly, each person gets a fair turn or a fair amount.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what another person meant. It can make people upset until they talk and understand each other again.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after hurt feelings or a fight. It is when people come back together and the bad feeling is repaired.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    sharing = SHARING[params.sharing]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    reconciliation = RECONCILIATIONS[params.reconciliation]
    world = World()
    bearer = world.add(Entity(id=params.bearer, kind="character", type="boy", role="bearer"))
    other = world.add(Entity(id=params.other, kind="character", type="girl", role="other"))
    mediator = world.add(Entity(id=params.mediator, kind="character", type="priestess", role="mediator"))
    world.add(Entity(id="vessel", kind="thing", type="vessel", label=setting.vessel))
    bearer.meters["shared"] = 1.0
    other.meters["shared"] = 0.0
    bearer.memes["kindness"] = 1.0
    other.memes["kindness"] = 1.0

    world.say(
        f"In the old days, when the hills still listened, {bearer.id} and {other.id} met at {setting.place}. "
        f"The sky was {setting.sky}, and a blessing waited in {setting.vessel}: one liter of {setting.gift}."
    )
    world.say(f"{sharing.share_text} The myth began with a fair intent, and {setting.blessing.lower()}.")

    world.para()
    world.say(
        f"But then the light shifted. {other.id} heard the moment through the wrong ear and spoke too quickly: "
        f'"{misunderstanding.speech}." {misunderstanding.hurt_text}'
    )
    bearer.memes["hurt"] += 1
    other.memes["hurt"] += 1
    world.say(
        f"The two stood apart, each sure the other had meant harm, and the shared liter seemed to weigh like a stone."
    )

    world.para()
    world.say(f"Then {mediator.id} came to them as a calm voice between thunder and rain.")
    world.say(f'"{reconciliation.helper_text}," {mediator.id} said.')
    world.say(reconciliation.repair_text)
    repair(world, bearer, other, reconciliation, setting)

    world.facts.update(
        setting=setting,
        sharing=sharing,
        misunderstanding=misunderstanding,
        reconciliation=reconciliation,
        bearer=bearer,
        other=other,
        mediator=mediator,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.sharing not in SHARING:
        raise StoryError("Unknown sharing pattern.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if params.reconciliation not in RECONCILIATIONS:
        raise StoryError("Unknown reconciliation.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
sharing_ok(S) :- sharing(S).
liter_present :- gift(liter).
misunderstanding(M) :- misunderstanding(M).
reconciliation(R) :- reconciliation(R).
valid(S, Sh, M) :- setting(S), sharing(Sh), misunderstanding(M), liter_present.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for shid in SHARING:
        lines.append(asp.fact("sharing", shid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for rid in RECONCILIATIONS:
        lines.append(asp.fact("reconciliation", rid))
    lines.append(asp.fact("gift", "liter"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {err}")
    return rc


CURATED = [
    StoryParams(
        setting="spring",
        sharing="pour_once",
        misunderstanding="too_little",
        reconciliation="elder_words",
        bearer="Ari",
        other="Mira",
        mediator="Iria",
    ),
    StoryParams(
        setting="temple",
        sharing="measure_carefully",
        misunderstanding="taking_all",
        reconciliation="shared_drink",
        bearer="Taro",
        other="Lena",
        mediator="Dara",
    ),
    StoryParams(
        setting="grove",
        sharing="offer_first",
        misunderstanding="shadow_sign",
        reconciliation="promise_oath",
        bearer="Sorin",
        other="Niko",
        mediator="Mira",
    ),
]


def explain_rejection() -> str:
    return "(No story: this mythic arrangement cannot be made into a fair sharing tale.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
