#!/usr/bin/env python3
"""A mythic dentist-office storyworld about a vivid candle, misunderstanding, and moral change.

Seed:
    Words: candle, vivid
    Setting: dentist office
    Features: Moral Value, Transformation, Misunderstanding
    Style: Myth

Internal source tale:
    In an old dentist office, a vivid candle is kept so frightened children can
    remember that small lights tell the truth better than large fears do. A
    child sees an ordinary dental sign twisted into a mythic omen and
    misunderstands it as punishment or danger. Doctor Ilya does not break the
    fear by force. Instead, the child must choose the right moral act, and that
    choice lets the office reveal its real cause. When the misunderstanding
    clears, the candle wax changes into a gentle token that shows fear has been
    transformed into wisdom.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Chamber:
    id: str
    label: str
    setting_line: str
    candle_line: str
    exit_line: str
    affords: set[str]


@dataclass(frozen=True)
class Omen:
    id: str
    label: str
    vision: str
    mistaken_belief: str
    hidden_cause: str
    need: str
    reveal_line: str
    transform_line: str
    final_image: str


@dataclass(frozen=True)
class Virtue:
    id: str
    label: str
    grants: str
    action: str
    teaching: str
    help_line: str
    moral: str


@dataclass(frozen=True)
class HeroSeed:
    id: str
    name: str
    gender: str
    trait: str


@dataclass(frozen=True)
class StoryParams:
    chamber: str
    omen: str
    virtue: str
    hero: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    location: str = ""
    owner: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    states: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class DentistOfficeWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | float] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, ent_id: str) -> Entity:
        return self.entities[ent_id]

    def say(self, text: str) -> None:
        text = text.strip()
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "DentistOfficeWorld":
        return copy.deepcopy(self)


CHAMBERS: dict[str, Chamber] = {
    "mirror_altar": Chamber(
        id="mirror_altar",
        label="the mirror chair",
        setting_line=(
            "Long ago, in a dentist office above the bread market, the mirror chair stood under a window of pale morning glass."
        ),
        candle_line=(
            "By its arm rested a vivid candle in a brass cup, and its small flame shone so steadily that even the steel tools looked polite beside it."
        ),
        exit_line="stepped down from the chair with a lighter jaw and a steadier heart",
        affords={"serpent_glint"},
    ),
    "rinsing_font": Chamber(
        id="rinsing_font",
        label="the rinse basin",
        setting_line=(
            "Long ago, in a dentist office tiled in mint and pearl, the rinse basin waited beneath a shelf of little cups."
        ),
        candle_line=(
            "A vivid candle burned near the basin, and its gold light kept laying soft ribbons over the water."
        ),
        exit_line="set the cup down and walked back from the basin without hurrying",
        affords={"rose_tide"},
    ),
    "picture_niche": Chamber(
        id="picture_niche",
        label="the picture screen",
        setting_line=(
            "Long ago, in a dentist office where tooth pictures were shown like weather maps, a narrow stool faced the bright screen."
        ),
        candle_line=(
            "At the foot of the screen, a vivid candle made a white pool on its saucer, as if the room kept one quiet moon of its own."
        ),
        exit_line="slid from the stool and stood with both shoulders loose again",
        affords={"gate_mountain"},
    ),
}


OMENS: dict[str, Omen] = {
    "serpent_glint": Omen(
        id="serpent_glint",
        label="the serpent of light",
        vision=(
            "the vivid candle stretched across the mouth mirror until a shining serpent seemed to coil above the chair"
        ),
        mistaken_belief=(
            "a tooth serpent had woken because the child had hidden the truth about a sticky date sweet"
        ),
        hidden_cause=(
            "a thin strand of date filling clung beside the sore tooth, and the mirror stem crossed the candlelight into one long curling line"
        ),
        need="honesty",
        reveal_line=(
            "Doctor Ilya lifted the sticky strand away with a tiny hook and turned the mirror just a finger-width, so the fierce serpent broke into plain silver and light."
        ),
        transform_line=(
            "At the candle's rim, a curl of wax softened and settled into a little white coil, more like a sleeping ribbon than a snake."
        ),
        final_image=(
            "The wax coil rested by the polished mirror, and no light in the room looked angry any longer."
        ),
    ),
    "rose_tide": Omen(
        id="rose_tide",
        label="the rose tide",
        vision=(
            "the rinse bowl flashed vivid rose, as if a bright spring had suddenly turned to blood"
        ),
        mistaken_belief=(
            "the office had wounded the little moon inside the tooth and the basin was catching its sorrow"
        ),
        hidden_cause=(
            "mulberry ice still stained the child's tongue and the first rinse, so the water borrowed that color for only a moment"
        ),
        need="trust",
        reveal_line=(
            "Doctor Ilya poured fresh mint water, counted the rinses aloud, and showed how the red glow faded as soon as the stain washed clean away."
        ),
        transform_line=(
            "One bead of wax cooled on the tray into a pale petal, bright and calm as a flower that had chosen not to close."
        ),
        final_image=(
            "The basin held clear water at last, and the wax petal shone beside it like a quiet promise."
        ),
    ),
    "gate_mountain": Omen(
        id="gate_mountain",
        label="the mountain gate",
        vision=(
            "the tooth picture rose up like a split white mountain gate, huge enough to make the whole jaw seem under siege"
        ),
        mistaken_belief=(
            "a stone giant was breaking through from inside the mouth"
        ),
        hidden_cause=(
            "the first picture had blurred when the child twisted, and the strange shape was only a baby tooth loosening in its proper season"
        ),
        need="stillness",
        reveal_line=(
            "Doctor Ilya took a second picture while the child sat still as a carved sparrow, and the broken mountain settled into one small tooth ready for its ordinary journey."
        ),
        transform_line=(
            "Wax along the saucer stretched into a tiny arch boat carrying a white tooth-seed in the middle."
        ),
        final_image=(
            "The wax arch stood by the quiet screen, and the once-terrible mountain had become a gentle leaving."
        ),
    ),
}


VIRTUES: dict[str, Virtue] = {
    "tell_truth": Virtue(
        id="tell_truth",
        label="tell the plain truth",
        grants="honesty",
        action="opened a brave mouth and admitted that a sticky date sweet had been tucked in one cheek on the walk to the office",
        teaching=(
            '"Hidden crumbs grow larger in the mind than they do in the tooth," Doctor Ilya said. "When truth comes first, fear loses its costume."'
        ),
        help_line=(
            "With the truth spoken aloud, Doctor Ilya could clean carefully instead of guessing at the pain."
        ),
        moral="truth makes frightening signs smaller because it gives them their real name",
    ),
    "accept_help": Virtue(
        id="accept_help",
        label="accept gentle help",
        grants="trust",
        action="let Doctor Ilya steady the cup and count the rinses slowly instead of pulling away from the basin",
        teaching=(
            '"Not every red sign is a wound," Doctor Ilya said. "Sometimes trust is the bridge that lets clear water appear."'
        ),
        help_line=(
            "Because the child accepted help instead of fighting it, the rinse became a lesson and not a fright."
        ),
        moral="trust can turn panic into understanding because help reveals what fear miscolors",
    ),
    "sit_still": Virtue(
        id="sit_still",
        label="sit still with courage",
        grants="stillness",
        action="pressed both feet to the stool rung and stayed still long enough for a true picture to be made",
        teaching=(
            '"A shaking body can draw a shaking omen," Doctor Ilya said. "Stillness is also courage, because it lets the real shape arrive."'
        ),
        help_line=(
            "In that brief stillness, the room stopped inventing monsters and started telling the truth."
        ),
        moral="stillness can be brave because patience allows a frightened mind to see what is really there",
    ),
}


HEROES: dict[str, HeroSeed] = {
    "aria": HeroSeed(id="aria", name="Aria", gender="girl", trait="careful"),
    "lev": HeroSeed(id="lev", name="Lev", gender="boy", trait="earnest"),
    "nila": HeroSeed(id="nila", name="Nila", gender="girl", trait="bright-eyed"),
    "tomas": HeroSeed(id="tomas", name="Tomas", gender="boy", trait="dreamy"),
}


NEED_EXPLANATIONS = {
    "honesty": "the child needed truth before the serpent-shaped fear could be named and reduced",
    "trust": "the child needed to accept careful help before the red water could return to its ordinary color",
    "stillness": "the child needed one calm moment before the false mountain could become a true picture",
}


TOKEN_LABELS = {
    "serpent_glint": "wax coil",
    "rose_tide": "wax petal",
    "gate_mountain": "wax arch",
}


def pronoun_subject(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def pronoun_possessive(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.chamber not in CHAMBERS:
        return False, f"unknown chamber: {params.chamber}"
    if params.omen not in OMENS:
        return False, f"unknown omen: {params.omen}"
    if params.virtue not in VIRTUES:
        return False, f"unknown virtue: {params.virtue}"
    if params.hero not in HEROES:
        return False, f"unknown hero: {params.hero}"
    chamber = CHAMBERS[params.chamber]
    omen = OMENS[params.omen]
    virtue = VIRTUES[params.virtue]
    if omen.id not in chamber.affords:
        return False, f"{chamber.label} does not plausibly produce {omen.label}"
    if virtue.grants != omen.need:
        return False, f"{virtue.label} cannot resolve {omen.label}; it needs {omen.need}"
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for chamber in CHAMBERS:
        for omen in OMENS:
            for virtue in VIRTUES:
                for hero in HEROES:
                    params = StoryParams(chamber=chamber, omen=omen, virtue=virtue, hero=hero)
                    if valid_params(params)[0]:
                        combos.append(params)
    return combos


def make_world(params: StoryParams) -> DentistOfficeWorld:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    chamber = CHAMBERS[params.chamber]
    omen = OMENS[params.omen]
    hero_seed = HEROES[params.hero]
    world = DentistOfficeWorld(params)

    world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_seed.gender,
            label=hero_seed.name,
            location=chamber.id,
        )
    )
    world.add(
        Entity(
            id="dentist",
            kind="character",
            type="man",
            label="Doctor Ilya",
            location=chamber.id,
        )
    )
    world.add(
        Entity(
            id="candle",
            kind="object",
            type="candle",
            label="the vivid candle",
            location=chamber.id,
        )
    )
    world.add(
        Entity(
            id="omen",
            kind="sign",
            type="omen",
            label=omen.label,
            location=chamber.id,
        )
    )
    world.add(
        Entity(
            id="tooth",
            kind="body_part",
            type="tooth",
            label="the sore tooth",
            location="mouth",
            owner="hero",
        )
    )
    world.add(
        Entity(
            id="token",
            kind="object",
            type="token",
            label="the waiting wax",
            location=chamber.id,
        )
    )

    hero = world.get("hero")
    dentist = world.get("dentist")
    candle = world.get("candle")
    omen_ent = world.get("omen")
    tooth = world.get("tooth")
    token = world.get("token")

    hero.attrs["trait"] = hero_seed.trait
    hero.meters["fear"] = 0.0
    hero.meters["calm"] = 0.4
    hero.meters["honesty"] = 0.0
    hero.meters["trust"] = 0.0
    hero.meters["stillness"] = 0.0
    hero.memes["wonder"] = 0.7
    hero.memes["misunderstanding"] = 0.0
    hero.memes["wisdom"] = 0.0

    dentist.memes["patience"] = 1.0
    dentist.memes["guidance"] = 1.0

    candle.states.add("burning")
    candle.meters["glow"] = 1.0
    candle.meters["wax"] = 1.0
    candle.meters["transformed"] = 0.0
    candle.memes["guidance"] = 1.0

    omen_ent.states.add("misread")
    omen_ent.meters["menace"] = 1.0
    omen_ent.meters["understood"] = 0.0
    omen_ent.attrs["hidden_cause"] = omen.hidden_cause

    tooth.states.add("troubled")
    tooth.meters["trouble"] = 1.0
    tooth.meters["ease"] = 0.0

    token.meters["formed"] = 0.0

    world.facts.update(
        chamber_label=chamber.label,
        omen_label=omen.label,
        hidden_cause=omen.hidden_cause,
        need=omen.need,
        moral=VIRTUES[params.virtue].moral,
        resolved=False,
        token_label=TOKEN_LABELS[omen.id],
    )
    return world


def opening(world: DentistOfficeWorld) -> None:
    chamber = CHAMBERS[world.params.chamber]
    hero = world.get("hero")
    world.record(
        "opening",
        f"{chamber.setting_line} {hero.label}, {article(hero.attrs['trait'])} {hero.attrs['trait']} child, came there with one aching tooth and many questions.",
        "hero",
        "tooth",
    )
    world.record(
        "candle",
        f"{chamber.candle_line} People in that town said each child carried a tiny tooth-moon inside the mouth, and the dentist office kept one candle lit so those little moons would not feel alone.",
        "candle",
        "hero",
    )


def omen_appears(world: DentistOfficeWorld) -> None:
    omen = OMENS[world.params.omen]
    hero = HEROES[world.params.hero]
    hero_ent = world.get("hero")
    hero_ent.meters["fear"] = 1.0
    hero_ent.meters["calm"] = 0.0
    hero_ent.memes["misunderstanding"] = 1.0
    world.para()
    world.record(
        "omen",
        f"Then {omen.vision}. {hero.name} thought {omen.mistaken_belief}.",
        "omen",
        "hero",
    )
    world.record(
        "fear",
        f"Fear hurried through {pronoun_possessive(hero.gender)} chest so quickly that even the bright room seemed to lean the wrong way.",
        "hero",
        "omen",
    )


def moral_teaching(world: DentistOfficeWorld) -> None:
    virtue = VIRTUES[world.params.virtue]
    world.record(
        "teaching",
        f"{virtue.teaching} The words were gentle, but they stood firm in the room like a rail a child could hold.",
        "dentist",
        "hero",
    )


def choose_virtue(world: DentistOfficeWorld) -> None:
    virtue = VIRTUES[world.params.virtue]
    hero = world.get("hero")
    hero.meters[virtue.grants] = 1.0
    hero.meters["fear"] = 0.2
    hero.meters["calm"] = 0.9
    hero.memes["courage"] += 1.0
    world.para()
    world.record(
        "choice",
        f"So {hero.label} {virtue.action}. {virtue.help_line}",
        "hero",
        "dentist",
    )


def reveal_truth(world: DentistOfficeWorld) -> None:
    omen = OMENS[world.params.omen]
    hero = world.get("hero")
    candle = world.get("candle")
    omen_ent = world.get("omen")
    tooth = world.get("tooth")
    token = world.get("token")

    hero.meters["fear"] = 0.0
    hero.meters["calm"] = 1.0
    hero.memes["misunderstanding"] = 0.0
    hero.memes["wisdom"] += 0.8

    candle.meters["wax"] = 0.4
    candle.meters["transformed"] = 1.0

    omen_ent.states.discard("misread")
    omen_ent.states.add("understood")
    omen_ent.meters["menace"] = 0.0
    omen_ent.meters["understood"] = 1.0

    tooth.states.discard("troubled")
    tooth.states.add("eased")
    tooth.meters["trouble"] = 0.0
    tooth.meters["ease"] = 1.0

    token.label = world.facts["token_label"]
    token.meters["formed"] = 1.0
    token.states.add("formed")

    world.record(
        "reveal",
        f"Then the true cause stood in the open: {omen.hidden_cause}. {omen.reveal_line}",
        "dentist",
        "omen",
    )
    world.record(
        "transform",
        f"{omen.transform_line} {hero.label} saw that the room had never been trying to frighten {pronoun_object(world.params.hero)}. It had only been waiting for goodness to make the picture plain.",
        "candle",
        "token",
    )
    world.facts["resolved"] = True


def pronoun_object(hero_id: str) -> str:
    return "her" if HEROES[hero_id].gender == "girl" else "him"


def ending(world: DentistOfficeWorld) -> None:
    chamber = CHAMBERS[world.params.chamber]
    omen = OMENS[world.params.omen]
    virtue = VIRTUES[world.params.virtue]
    hero_seed = HEROES[world.params.hero]
    hero = world.get("hero")
    hero.memes["wisdom"] += 0.7
    world.para()
    world.record(
        "ending",
        f"When the visit was done, {hero.label} {chamber.exit_line}. {omen.final_image} From that day on, {hero_seed.name} remembered that {virtue.moral}.",
        "hero",
        "token",
    )


def tell(params: StoryParams) -> DentistOfficeWorld:
    world = make_world(params)
    opening(world)
    omen_appears(world)
    moral_teaching(world)
    choose_virtue(world)
    reveal_truth(world)
    ending(world)
    return world


def generation_prompts(world: DentistOfficeWorld) -> list[str]:
    hero = HEROES[world.params.hero]
    omen = OMENS[world.params.omen]
    virtue = VIRTUES[world.params.virtue]
    return [
        'Write a myth set in a dentist office that clearly includes the words "candle" and "vivid."',
        f"Center the story on {hero.name}, who misunderstands {omen.label} before learning to {virtue.label}.",
        "Make the ending concrete: the misunderstanding must clear, the tooth problem must be explained, and the candle wax must transform into a small token of wisdom.",
    ]


def story_grounded_qa(world: DentistOfficeWorld) -> list[QAItem]:
    hero = HEROES[world.params.hero]
    omen = OMENS[world.params.omen]
    virtue = VIRTUES[world.params.virtue]
    return [
        QAItem(
            question=f"What frightened {hero.name} in the dentist office?",
            answer=(
                f"{hero.name} was frightened because {omen.vision}. "
                f"To the child, that vivid sign looked like {omen.label} and seemed to prove that {omen.mistaken_belief}."
            ),
        ),
        QAItem(
            question="What was the omen really made of?",
            answer=(
                f"It was really made of ordinary things in the room, because {omen.hidden_cause}. "
                f"{omen.reveal_line}"
            ),
        ),
        QAItem(
            question=f"How did {hero.name} help solve the problem?",
            answer=(
                f"{hero.name} helped by choosing to {virtue.label}. "
                "That moral act gave Doctor Ilya the cooperation this omen needed, so the misunderstanding could not keep growing."
            ),
        ),
        QAItem(
            question="How did the ending prove that something had transformed?",
            answer=(
                f"The ending proved it with a physical change, because the candle wax became {article(world.facts['token_label'])} {world.facts['token_label']}. "
                "The new token showed that fear had not merely ended; it had changed into a memory of wisdom."
            ),
        ),
    ]


def world_knowledge_qa(world: DentistOfficeWorld) -> list[QAItem]:
    omen = OMENS[world.params.omen]
    virtue = VIRTUES[world.params.virtue]
    return [
        QAItem(
            question="Why can a dentist office feel mysterious to a child?",
            answer=(
                "A dentist office has mirrors, lights, cups, and tools that can look strange when a child is already worried. "
                "Fear can turn ordinary care into a bigger story before the child knows what each object is for."
            ),
        ),
        QAItem(
            question="Why do misunderstandings often grow quickly when someone is afraid?",
            answer=(
                "Fear pushes the mind to choose a dangerous explanation before a careful one. "
                "That is why a gentle guide and a clear next step can matter so much."
            ),
        ),
        QAItem(
            question=f"Why was it important to {virtue.label} in this story?",
            answer=(
                f"It was important because {NEED_EXPLANATIONS[omen.need]}. "
                "The right moral value fit the real problem instead of fighting an imaginary one."
            ),
        ),
        QAItem(
            question="Why is a transformed object a good ending image in a myth?",
            answer=(
                "A transformed object lets children see an inner lesson become something visible and memorable. "
                "It keeps the story's change in the room after the fear itself has gone."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(C, O, V, H) :-
    chamber(C),
    omen(O),
    virtue(V),
    hero(H),
    affords(C, O),
    needs(O, N),
    grants(V, N).

ok :- chosen(C, O, V, H), valid(C, O, V, H).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for chamber_key, chamber in CHAMBERS.items():
        rows.append(fact("chamber", chamber_key))
        for omen in chamber.affords:
            rows.append(fact("affords", chamber_key, omen))
    for omen_key, omen in OMENS.items():
        rows.append(fact("omen", omen_key))
        rows.append(fact("needs", omen_key, omen.need))
    for virtue_key, virtue in VIRTUES.items():
        rows.append(fact("virtue", virtue_key))
        rows.append(fact("grants", virtue_key, virtue.grants))
    for hero_key in HEROES:
        rows.append(fact("hero", hero_key))
    if params is not None:
        rows.append(fact("chosen", params.chamber, params.omen, params.virtue, params.hero))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from asp import atoms, one_model

    combos: set[tuple[str, str, str, str]] = set()
    for combo in atoms(one_model(asp_program()), "valid"):
        combos.add(tuple(str(part) for part in combo))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_combos = {(p.chamber, p.omen, p.virtue, p.hero) for p in all_params()}
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(
            f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}"
        )

    for params in all_params():
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        story = sample.story
        world = sample.world
        if world is None:
            raise StoryError(f"world missing for params={params}")
        if "candle" not in story or "vivid" not in story or "dentist office" not in story:
            raise StoryError(f"seed language missing from story for params={params}")
        if len(sample.prompts) < 3 or len(sample.story_qa) < 4 or len(sample.world_qa) < 4:
            raise StoryError(f"QA or prompts too thin for params={params}")
        if not world.facts.get("resolved"):
            raise StoryError(f"misunderstanding did not resolve for params={params}")
        if world.get("token").meters["formed"] < 1.0:
            raise StoryError(f"candle wax did not transform for params={params}")
        if world.get("tooth").meters["ease"] < 1.0:
            raise StoryError(f"tooth trouble was not eased for params={params}")
        if "{}" in story or "  " in story:
            raise StoryError(f"story leaked scaffold text for params={params}")
    return (
        f"OK: Python and ASP agree on {len(python_combos)} valid mythic dentist-office stories, "
        "and every story resolves the misunderstanding through a fitting moral choice."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chamber", choices=sorted(CHAMBERS))
    parser.add_argument("--omen", choices=sorted(OMENS))
    parser.add_argument("--virtue", choices=sorted(VIRTUES))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    choices = [
        combo
        for combo in all_params()
        if (args.chamber is None or combo.chamber == args.chamber)
        and (args.omen is None or combo.omen == args.omen)
        and (args.virtue is None or combo.virtue == args.virtue)
        and (args.hero is None or combo.hero == args.hero)
    ]
    if not choices:
        chamber = args.chamber or sorted(CHAMBERS)[0]
        omen = args.omen or sorted(OMENS)[0]
        virtue = args.virtue or sorted(VIRTUES)[0]
        hero = args.hero or sorted(HEROES)[0]
        params = StoryParams(chamber=chamber, omen=omen, virtue=virtue, hero=hero, seed=args.seed)
        ok, reason = valid_params(params)
        raise StoryError(reason if not ok else "no valid stories for that selection")
    chosen = rng.choice(choices)
    return StoryParams(
        chamber=chosen.chamber,
        omen=chosen.omen,
        virtue=chosen.virtue,
        hero=chosen.hero,
        seed=args.seed,
    )


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for index, params in enumerate(all_params()):
            yield generate(
                StoryParams(
                    chamber=params.chamber,
                    omen=params.omen,
                    virtue=params.virtue,
                    hero=params.hero,
                    seed=args.seed + index,
                )
            )
        return

    explicit = any(
        getattr(args, key) is not None
        for key in ("chamber", "omen", "virtue", "hero")
    )
    if explicit:
        rng = random.Random(args.seed)
        for index in range(max(1, args.n)):
            params = resolve_params(args, rng)
            yield generate(
                StoryParams(
                    chamber=params.chamber,
                    omen=params.omen,
                    virtue=params.virtue,
                    hero=params.hero,
                    seed=args.seed + index,
                )
            )
        return

    combos = all_params()
    rng = random.Random(args.seed)
    rng.shuffle(combos)
    for index in range(max(1, args.n)):
        params = combos[index % len(combos)]
        yield generate(
            StoryParams(
                chamber=params.chamber,
                omen=params.omen,
                virtue=params.virtue,
                hero=params.hero,
                seed=args.seed + index,
            )
        )


def trace_lines(world: DentistOfficeWorld) -> list[str]:
    hero = world.get("hero")
    tooth = world.get("tooth")
    omen = world.get("omen")
    token = world.get("token")
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  hero_fear={fear:.1f} hero_calm={calm:.1f} hero_wisdom={wisdom:.1f}".format(
            fear=hero.meters["fear"],
            calm=hero.meters["calm"],
            wisdom=hero.memes["wisdom"],
        )
    )
    lines.append(
        "  tooth_trouble={trouble:.1f} tooth_ease={ease:.1f} omen_understood={understood:.1f} token_formed={formed:.1f}".format(
            trouble=tooth.meters["trouble"],
            ease=tooth.meters["ease"],
            understood=omen.meters["understood"],
            formed=token.meters["formed"],
        )
    )
    return lines


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        payload = sample.to_dict()
        if header:
            payload = {"header": header, **payload}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace:
        print()
        print("\n".join(trace_lines(sample.world)))
    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\nWorld QA:")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = list(iter_samples(args))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = None
            if args.all:
                p = sample.params
                header = (
                    f"### chamber={p.chamber} omen={p.omen} virtue={p.virtue} hero={p.hero}"
                )
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, args, header=header)
            if index < len(samples) - 1:
                print("\n---\n")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
