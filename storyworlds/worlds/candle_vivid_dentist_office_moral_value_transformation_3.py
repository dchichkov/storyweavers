#!/usr/bin/env python3
"""Mythic dentist-office storyworld about a vivid candle, misunderstanding, and moral transformation.

Seed:
    Words: candle, vivid
    Setting: dentist office
    Features: Moral Value, Transformation, Misunderstanding
    Style: Myth

Internal source tale:
    In a hill-town dentist office, a vivid candle burns beside the chair so
    frightened children remember that small lights tell the truth more plainly
    than large fears do. A child mistakes an ordinary sign of treatment for a
    mythic warning and believes the office is judging a hidden fault. The
    healer does not argue with the fear by force. Instead, the child must make
    a moral choice that fits the danger: telling the truth, accepting careful
    help, or holding still with patience. Once that virtue is chosen, the room
    reveals its simple cause, the misunderstanding dissolves, and the candle
    wax changes into a small token that proves fear has been transformed into
    wisdom.
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

STORYWORLDS = Path(__file__).resolve().parents[1]
if str(STORYWORLDS) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Chamber:
    key: str
    label: str
    opening_line: str
    candle_line: str
    departure_line: str
    supports_signs: tuple[str, ...]


@dataclass(frozen=True)
class Sign:
    key: str
    label: str
    vision: str
    mistaken_belief: str
    real_cause: str
    needed_virtue: str
    reveal_action: str
    token_shape: str
    ending_image: str
    object_involved: str


@dataclass(frozen=True)
class Virtue:
    key: str
    label: str
    grants: str
    choice_line: str
    teaching: str
    effect_line: str
    moral: str


@dataclass(frozen=True)
class HeroSeed:
    key: str
    name: str
    gender: str
    trait: str


@dataclass(frozen=True)
class StoryParams:
    chamber: str
    sign: str
    virtue: str
    hero: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    owner: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    states: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Event:
    kind: str
    text: str
    actor: str
    target: str = ""


@dataclass
class DentistMythWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | float] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        line = text.strip()
        if line:
            self.paragraphs[-1].append(line)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, text: str, actor: str, target: str = "") -> None:
        self.history.append(Event(kind=kind, text=text, actor=actor, target=target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(
            "  params: "
            f"chamber={self.params.chamber} sign={self.params.sign} "
            f"virtue={self.params.virtue} hero={self.params.hero} seed={self.params.seed}"
        )
        lines.append("  facts:")
        for key, value in sorted(self.facts.items()):
            lines.append(f"    {key}={value}")
        lines.append("  entities:")
        for entity in self.entities.values():
            lines.append(f"    {entity.id}: {entity.label} ({entity.kind}) at {entity.location}")
            if entity.owner:
                lines.append(f"      owner={entity.owner}")
            if entity.attrs:
                lines.append(f"      attrs={dict(sorted(entity.attrs.items()))}")
            if entity.states:
                lines.append(f"      states={sorted(entity.states)}")
            if entity.meters:
                lines.append(f"      meters={dict(sorted(entity.meters.items()))}")
            if entity.memes:
                lines.append(f"      memes={dict(sorted(entity.memes.items()))}")
        lines.append("  history:")
        for event in self.history:
            lines.append(
                f"    {event.kind}: actor={event.actor} target={event.target or '-'} text={event.text}"
            )
        return "\n".join(lines)

    def copy(self) -> "DentistMythWorld":
        return copy.deepcopy(self)


CHAMBERS: dict[str, Chamber] = {
    "pearl_chair": Chamber(
        key="pearl_chair",
        label="the pearl chair",
        opening_line=(
            "Long ago, in a dentist office built against a windy hill, the pearl chair stood beneath a painted arch of dawn."
        ),
        candle_line=(
            "On a brass shelf beside it burned a vivid candle, and the flame was so even that the silver tools looked tamed by its light."
        ),
        departure_line="stepped down from the chair with a looser jaw and a quieter heartbeat",
        supports_signs=("falcon_crown",),
    ),
    "rinsing_font": Chamber(
        key="rinsing_font",
        label="the rinsing font",
        opening_line=(
            "Long ago, in a dentist office lined with blue tiles, the rinsing font waited below a row of tiny white cups."
        ),
        candle_line=(
            "A vivid candle rested by the basin, and its gold light drifted over the water like a patient ribbon."
        ),
        departure_line="set the cup aside and walked from the basin without flinching",
        supports_signs=("rose_tide",),
    ),
    "picture_apse": Chamber(
        key="picture_apse",
        label="the picture apse",
        opening_line=(
            "Long ago, in a dentist office where tooth pictures shone on the wall like moon maps, a narrow stool faced the bright screen."
        ),
        candle_line=(
            "At the foot of the screen stood a vivid candle in a white saucer, keeping one small moon of flame for the whole room."
        ),
        departure_line="slid from the stool and found that both shoulders had remembered how to rest",
        supports_signs=("moon_gate",),
    ),
}


SIGNS: dict[str, Sign] = {
    "falcon_crown": Sign(
        key="falcon_crown",
        label="the falcon crown",
        vision=(
            "the vivid candle flashed along the mouth mirror until a hooked falcon seemed to peck at a shining crown above the aching tooth"
        ),
        mistaken_belief=(
            "a tooth-king's bird had come because the child had hidden a sticky fig sweet in one cheek on the walk to the office"
        ),
        real_cause=(
            "a thread of fig paste clung beside the sore tooth, and the angled mirror stem crossed the candlelight into one sharp beak of silver"
        ),
        needed_virtue="honesty",
        reveal_action=(
            "Healer Samira lifted the fig thread away with a tiny hook and tipped the mirror a little, so the fierce bird broke apart into plain silver and light."
        ),
        token_shape="wax feather",
        ending_image=(
            "The wax feather lay beside the polished mirror, and nothing bright in the room looked like punishment anymore."
        ),
        object_involved="mouth mirror",
    ),
    "rose_tide": Sign(
        key="rose_tide",
        label="the rose tide",
        vision=(
            "the rinsing water blushed vivid rose, as if a dawn river had suddenly flowed into the basin"
        ),
        mistaken_belief=(
            "the office had wounded the little moon inside the tooth and the basin was catching its sorrow"
        ),
        real_cause=(
            "berry syrup from breakfast still stained the tongue, so the first rinse borrowed that color for only a moment"
        ),
        needed_virtue="trust",
        reveal_action=(
            "Healer Samira steadied the cup, counted the rinses aloud, and showed that the red color faded as soon as clear water had room to speak."
        ),
        token_shape="wax petal",
        ending_image=(
            "The basin held clear water at last, and the wax petal shone beside it like a promise that had chosen calm."
        ),
        object_involved="rinse cup",
    ),
    "moon_gate": Sign(
        key="moon_gate",
        label="the broken moon gate",
        vision=(
            "the tooth picture rose up like a split white gate, huge enough to make the whole jaw seem under siege by the moon"
        ),
        mistaken_belief=(
            "a stone giant was pushing through from inside the mouth because the child had trembled too much to be worthy of the healer's help"
        ),
        real_cause=(
            "the first picture blurred when the child twisted, and the strange shape was only a baby tooth loosening in its proper season"
        ),
        needed_virtue="patience",
        reveal_action=(
            "Healer Samira took a second picture while the child stayed still as a carved swallow, and the broken gate settled into one small tooth ready for an ordinary leaving."
        ),
        token_shape="wax moon bead",
        ending_image=(
            "The wax moon bead rested beneath the quiet screen, and the once-terrible gate had become a gentle doorway for growing."
        ),
        object_involved="tooth picture",
    ),
}


VIRTUES: dict[str, Virtue] = {
    "speak_truth": Virtue(
        key="speak_truth",
        label="speak the plain truth",
        grants="honesty",
        choice_line=(
            "opened a brave mouth and confessed that a sticky fig sweet had been hidden on the way to the office"
        ),
        teaching=(
            '"When truth enters first," Healer Samira said, "fear loses the costume it borrowed from shadows."'
        ),
        effect_line=(
            "Because the truth was spoken, the healer could clean what hurt instead of chasing a larger and darker guess."
        ),
        moral="truth makes frightening signs smaller because it gives them their real name",
    ),
    "accept_guidance": Virtue(
        key="accept_guidance",
        label="accept gentle guidance",
        grants="trust",
        choice_line=(
            "let Healer Samira steady the cup and count the rinses slowly instead of jerking away from the basin"
        ),
        teaching=(
            '"Not every red sign is a wound," Healer Samira said. "Trust is the bridge that lets clear water appear."'
        ),
        effect_line=(
            "Because help was accepted instead of fought, the basin could become a lesson instead of remaining a fright."
        ),
        moral="trust can turn panic into understanding because help reveals what fear miscolors",
    ),
    "hold_still": Virtue(
        key="hold_still",
        label="hold still with patience",
        grants="patience",
        choice_line=(
            "pressed both feet to the stool rung and held still long enough for a true picture to be made"
        ),
        teaching=(
            '"A shaking body can draw a shaking omen," Healer Samira said. "Patience is also courage, because it lets the real shape arrive."'
        ),
        effect_line=(
            "In that small stillness, the room stopped inventing giants and began telling the truth in its own quiet voice."
        ),
        moral="patience can be brave because a calm moment allows frightened eyes to see what is really there",
    ),
}


HEROES: dict[str, HeroSeed] = {
    "amira": HeroSeed(key="amira", name="Amira", gender="girl", trait="watchful"),
    "elin": HeroSeed(key="elin", name="Elin", gender="girl", trait="thoughtful"),
    "joel": HeroSeed(key="joel", name="Joel", gender="boy", trait="earnest"),
    "soren": HeroSeed(key="soren", name="Soren", gender="boy", trait="dreamy"),
}


def article(text: str) -> str:
    return "an" if text[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def pronouns(hero_key: str) -> tuple[str, str, str]:
    hero = HEROES[hero_key]
    if hero.gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def token_article(token_shape: str) -> str:
    return "an" if token_shape[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def reasonableness_gate(params: StoryParams) -> None:
    if params.chamber not in CHAMBERS:
        raise StoryError(f"No story: unknown chamber {params.chamber!r}.")
    if params.sign not in SIGNS:
        raise StoryError(f"No story: unknown sign {params.sign!r}.")
    if params.virtue not in VIRTUES:
        raise StoryError(f"No story: unknown virtue {params.virtue!r}.")
    if params.hero not in HEROES:
        raise StoryError(f"No story: unknown hero {params.hero!r}.")

    chamber = CHAMBERS[params.chamber]
    sign = SIGNS[params.sign]
    virtue = VIRTUES[params.virtue]

    if params.sign not in chamber.supports_signs:
        raise StoryError(f"No story: {chamber.label} does not plausibly produce {sign.label}.")
    if virtue.grants != sign.needed_virtue:
        raise StoryError(
            "No story: "
            f"{virtue.label} cannot resolve {sign.label} because that misunderstanding needs {sign.needed_virtue}."
        )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for chamber_key, chamber in CHAMBERS.items():
        for sign_key, sign in SIGNS.items():
            if sign_key not in chamber.supports_signs:
                continue
            for virtue_key, virtue in VIRTUES.items():
                if virtue.grants != sign.needed_virtue:
                    continue
                combos.append((chamber_key, sign_key, virtue_key))
    return combos


def build_world(params: StoryParams) -> DentistMythWorld:
    reasonableness_gate(params)
    chamber = CHAMBERS[params.chamber]
    sign = SIGNS[params.sign]
    hero_seed = HEROES[params.hero]
    world = DentistMythWorld(params=params)

    world.add(
        Entity(
            id="office",
            kind="place",
            label="the hill-town dentist office",
            location=params.chamber,
            attrs={"setting": "dentist office", "style": "myth"},
            states={"open"},
            meters={"hush": 0.7, "clarity": 0.3},
            memes={"care": 1.0, "wonder": 0.6},
        )
    )
    world.add(
        Entity(
            id="hero",
            kind="child",
            label=hero_seed.name,
            location=params.chamber,
            attrs={"trait": hero_seed.trait, "gender": hero_seed.gender},
            meters={"fear": 0.2, "calm": 0.5, "tooth_pain": 0.7},
            memes={"wonder": 0.8, "misunderstanding": 0.0, "wisdom": 0.0},
        )
    )
    world.add(
        Entity(
            id="healer",
            kind="dentist",
            label="Healer Samira",
            location=params.chamber,
            meters={"steadiness": 1.0},
            memes={"patience": 1.0, "guidance": 1.0},
        )
    )
    world.add(
        Entity(
            id="candle",
            kind="object",
            label="the vivid candle",
            location=params.chamber,
            states={"burning"},
            meters={"glow": 1.0, "wax": 1.0, "transformation": 0.0},
            memes={"guidance": 1.0, "memory": 0.7},
        )
    )
    world.add(
        Entity(
            id="sign",
            kind="misreading",
            label=sign.label,
            location=params.chamber,
            attrs={"object_involved": sign.object_involved, "real_cause": sign.real_cause},
            states={"misread"},
            meters={"threat": 1.0, "clarity": 0.0},
            memes={"fear": 1.0},
        )
    )
    world.add(
        Entity(
            id="tooth",
            kind="body_part",
            label="the aching tooth",
            location="mouth",
            owner="hero",
            states={"sore"},
            meters={"ache": 1.0, "ease": 0.0},
            memes={"attention": 0.5},
        )
    )
    world.add(
        Entity(
            id="token",
            kind="object",
            label="the waiting wax",
            location=params.chamber,
            states={"unformed"},
            meters={"formed": 0.0},
            memes={"meaning": 0.1},
        )
    )

    world.facts.update(
        setting="dentist office",
        style="myth",
        chamber_label=chamber.label,
        sign_label=sign.label,
        needed_virtue=sign.needed_virtue,
        token_shape=sign.token_shape,
        real_cause=sign.real_cause,
        moral=VIRTUES[params.virtue].moral,
        resolved=False,
    )
    return world


def opening(world: DentistMythWorld) -> None:
    chamber = CHAMBERS[world.params.chamber]
    hero = world.get("hero")
    office = world.get("office")
    office.meters["clarity"] = 0.4
    world.record(
        "opening",
        f"{chamber.opening_line} {hero.label}, {article(hero.attrs['trait'])} {hero.attrs['trait']} child with one aching tooth, climbed up to {chamber.label}.",
        "hero",
        "tooth",
    )
    world.record(
        "candle",
        f"{chamber.candle_line} People in that town said a candle belonged in every dentist office, because children listened better to a small brave flame than to a room full of bright metal.",
        "candle",
        "office",
    )


def misunderstanding(world: DentistMythWorld) -> None:
    sign = SIGNS[world.params.sign]
    hero = world.get("hero")
    office = world.get("office")
    hero.meters["fear"] = 1.0
    hero.meters["calm"] = 0.0
    hero.memes["misunderstanding"] = 1.0
    office.meters["clarity"] = 0.1
    world.para()
    world.record(
        "misreading",
        f"Then {sign.vision}. {hero.label} believed {sign.mistaken_belief}.",
        "sign",
        "hero",
    )
    world.record(
        "fear",
        "Fear hurried through the room faster than the healer's hands, so even the ordinary instruments seemed to lean toward legend.",
        "hero",
        "office",
    )


def guidance(world: DentistMythWorld) -> None:
    virtue = VIRTUES[world.params.virtue]
    world.record(
        "guidance",
        f"{virtue.teaching} Her voice did not chase the fear away by force. It gave the child one good path to walk.",
        "healer",
        "hero",
    )


def moral_choice(world: DentistMythWorld) -> None:
    hero = world.get("hero")
    virtue = VIRTUES[world.params.virtue]
    hero.meters[virtue.grants] = 1.0
    hero.meters["fear"] = 0.3
    hero.meters["calm"] = 0.8
    hero.memes["courage"] = hero.memes.get("courage", 0.0) + 0.8
    hero.memes["misunderstanding"] = 0.6
    world.para()
    world.record(
        "choice",
        f"So {hero.label} {virtue.choice_line}. {virtue.effect_line}",
        "hero",
        "healer",
    )


def reveal_and_transformation(world: DentistMythWorld) -> None:
    sign = SIGNS[world.params.sign]
    hero = world.get("hero")
    sign_entity = world.get("sign")
    candle = world.get("candle")
    tooth = world.get("tooth")
    token = world.get("token")
    office = world.get("office")
    _, _, object_pronoun = pronouns(world.params.hero)

    hero.meters["fear"] = 0.0
    hero.meters["calm"] = 1.0
    hero.memes["misunderstanding"] = 0.0
    hero.memes["wisdom"] = 1.1

    sign_entity.states.discard("misread")
    sign_entity.states.add("understood")
    sign_entity.meters["threat"] = 0.0
    sign_entity.meters["clarity"] = 1.0
    sign_entity.memes["fear"] = 0.0

    candle.meters["wax"] = 0.4
    candle.meters["transformation"] = 1.0
    candle.memes["memory"] = 1.0

    token.label = sign.token_shape
    token.states.discard("unformed")
    token.states.add("formed")
    token.meters["formed"] = 1.0
    token.memes["meaning"] = 1.0

    tooth.states.discard("sore")
    tooth.states.add("eased")
    tooth.meters["ache"] = 0.2
    tooth.meters["ease"] = 0.9

    office.meters["clarity"] = 1.0
    office.meters["hush"] = 0.9

    world.record(
        "reveal",
        f"Then the true cause stood in the open: {sign.real_cause}. {sign.reveal_action}",
        "healer",
        "sign",
    )
    world.record(
        "transformation",
        f"At the candle's edge, the wax softened and settled into {token_article(sign.token_shape)} {sign.token_shape}. {hero.label} saw that the room had never meant to punish {object_pronoun}. It had been waiting for the right virtue to make the picture plain.",
        "candle",
        "token",
    )
    world.facts["resolved"] = True


def ending(world: DentistMythWorld) -> None:
    chamber = CHAMBERS[world.params.chamber]
    sign = SIGNS[world.params.sign]
    virtue = VIRTUES[world.params.virtue]
    hero = world.get("hero")
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 0.6
    world.para()
    world.record(
        "ending",
        f"When the visit was done, {hero.label} {chamber.departure_line}. {sign.ending_image} From that day on, {hero.label} remembered that {virtue.moral}.",
        "hero",
        "token",
    )


def tell(params: StoryParams) -> DentistMythWorld:
    world = build_world(params)
    opening(world)
    misunderstanding(world)
    guidance(world)
    moral_choice(world)
    reveal_and_transformation(world)
    ending(world)
    return world


def generation_prompts(world: DentistMythWorld) -> list[str]:
    hero = HEROES[world.params.hero]
    sign = SIGNS[world.params.sign]
    virtue = VIRTUES[world.params.virtue]
    return [
        'Write a myth set in a dentist office that clearly includes the words "candle" and "vivid."',
        f"Center the story on {hero.name}, who misunderstands {sign.label} before learning to {virtue.label}.",
        "Make the ending concrete: the real cause must be revealed, the candle wax must transform into a token, and the final image must show that fear has changed into wisdom.",
    ]


def story_grounded_qa(world: DentistMythWorld) -> list[QAItem]:
    hero = HEROES[world.params.hero]
    sign = SIGNS[world.params.sign]
    virtue = VIRTUES[world.params.virtue]
    return [
        QAItem(
            question=f"What misunderstanding frightened {hero.name} in the dentist office?",
            answer=(
                f"{hero.name} was frightened because {sign.vision}. "
                f"To the child, that sign looked like {sign.label} and seemed to prove that {sign.mistaken_belief}."
            ),
        ),
        QAItem(
            question="What was the sign really made of?",
            answer=(
                f"It was really made of ordinary things in the room, because {sign.real_cause}. "
                f"{sign.reveal_action}"
            ),
        ),
        QAItem(
            question=f"How did {hero.name} help the misunderstanding clear?",
            answer=(
                f"{hero.name} helped by choosing to {virtue.label}. "
                f"That moral act gave the healer exactly what the moment needed, so the fear could shrink back into a true and ordinary cause."
            ),
        ),
        QAItem(
            question="How did the candle show a transformation?",
            answer=(
                f"The vivid candle showed it physically when the wax became {token_article(sign.token_shape)} {sign.token_shape}. "
                "That new token proved the room had changed from a place of dread into a place of understood care."
            ),
        ),
        QAItem(
            question="Why does the ending image matter?",
            answer=(
                f"The ending image matters because {sign.ending_image[0].lower() + sign.ending_image[1:]} "
                f"It gives the child a concrete picture of the lesson that {virtue.moral}."
            ),
        ),
    ]


def world_knowledge_qa(world: DentistMythWorld) -> list[QAItem]:
    need = world.facts["needed_virtue"]
    specific = {
        "honesty": QAItem(
            question="Why can honesty help in a dentist story?",
            answer=(
                "Honesty gives the healer the true cause of the trouble instead of making her guess around it. "
                "In a child-facing myth, that truth also makes a scary sign smaller because the fear loses its hidden fuel."
            ),
        ),
        "trust": QAItem(
            question="Why does trust matter when a child feels afraid at the dentist?",
            answer=(
                "Trust lets the child accept careful help instead of fighting every movement around the sore place. "
                "That cooperation often reveals the difference between an actual injury and a harmless color or reflection."
            ),
        ),
        "patience": QAItem(
            question="Why can patience change what a child sees?",
            answer=(
                "Patience creates the still moment needed for a clear picture, steady rinse, or careful look. "
                "When the body stops shaking, the world often stops looking like a monster and starts looking like itself again."
            ),
        ),
    }[str(need)]
    return [
        QAItem(
            question="Why can a dentist office feel mythic to a child?",
            answer=(
                "A dentist office is full of mirrors, lights, water, and bright tools that can seem strange when a child is already worried. "
                "Those ordinary objects can gather into a larger story inside the mind before the child knows what each one really does."
            ),
        ),
        QAItem(
            question="Why is a physical ending image important in a myth for children?",
            answer=(
                "A physical ending image proves that the change truly happened in the world of the story. "
                "Instead of hearing only a lesson, the child reader sees a new object or scene that carries the lesson."
            ),
        ),
        QAItem(
            question="Why should a moral choice come before the reveal?",
            answer=(
                "When the moral choice comes first, the turn feels earned instead of accidental. "
                "The child's action becomes part of the cause that allows truth to appear."
            ),
        ),
        specific,
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate mythic dentist-office storyworld samples.")
    parser.add_argument("--chamber", choices=sorted(CHAMBERS))
    parser.add_argument("--sign", choices=sorted(SIGNS))
    parser.add_argument("--virtue", choices=sorted(VIRTUES))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for chamber_key, sign_key, virtue_key in valid_combos():
        if args.chamber and args.chamber != chamber_key:
            continue
        if args.sign and args.sign != sign_key:
            continue
        if args.virtue and args.virtue != virtue_key:
            continue
        combos.append((chamber_key, sign_key, virtue_key))
    return combos


def _default_hero(args: argparse.Namespace, rng: random.Random) -> str:
    return args.hero or rng.choice(sorted(HEROES))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = _matching_combos(args)
    if not combos:
        candidate = StoryParams(
            chamber=args.chamber or "pearl_chair",
            sign=args.sign or "falcon_crown",
            virtue=args.virtue or "speak_truth",
            hero=args.hero or "amira",
            seed=getattr(rng, "story_seed", None),
        )
        reasonableness_gate(candidate)
    chamber_key, sign_key, virtue_key = rng.choice(combos)
    return StoryParams(
        chamber=chamber_key,
        sign=sign_key,
        virtue=virtue_key,
        hero=_default_hero(args, rng),
        seed=getattr(rng, "story_seed", None),
    )


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        print("")
        print("== (1) Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("")
        print("== (2) Story-grounded QA ==")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("")
        print("== (3) World-knowledge QA ==")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


ASP_RULES = r"""
combo(C,S,V) :-
    chamber(C),
    sign(S),
    virtue(V),
    supports_sign(C,S),
    needs(S,G),
    grants(V,G).

ok :- chosen(C,S,V), combo(C,S,V).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    rows: list[str] = []
    for chamber in CHAMBERS.values():
        rows.append(asp.fact("chamber", chamber.key))
        for sign_key in chamber.supports_signs:
            rows.append(asp.fact("supports_sign", chamber.key, sign_key))
    for sign in SIGNS.values():
        rows.append(asp.fact("sign", sign.key))
        rows.append(asp.fact("needs", sign.key, sign.needed_virtue))
    for virtue in VIRTUES.values():
        rows.append(asp.fact("virtue", virtue.key))
        rows.append(asp.fact("grants", virtue.key, virtue.grants))
    if params is not None:
        rows.append(asp.fact("chosen", params.chamber, params.sign, params.virtue))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    import asp

    combos: set[tuple[str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update(asp.atoms(model, "combo"))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    import asp

    return bool(asp.atoms(asp.one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    for index, combo in enumerate(sorted(python_combos)):
        params = StoryParams(
            chamber=combo[0],
            sign=combo[1],
            virtue=combo[2],
            hero="amira",
            seed=index,
        )
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected Python-valid combo: {combo}")
        sample = generate(params)
        if "dentist office" not in sample.story or "candle" not in sample.story or "vivid" not in sample.story:
            raise StoryError(f"Generated story dropped seed essentials for combo: {combo}")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated QA set is too thin for combo: {combo}")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story is missing a full beginning-turn-ending shape for combo: {combo}")
        if not sample.world or not sample.world.facts.get("resolved"):
            raise StoryError(f"Generated world never resolved for combo: {combo}")
        if sample.world.get("token").label == "the waiting wax":
            raise StoryError(f"Candle transformation did not complete for combo: {combo}")
    return f"OK: clingo gate matches Python gate and exercised {len(python_combos)} story variants."


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else 8000
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos()):
        story_seed = base_seed + index
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        params = StoryParams(
            chamber=combo[0],
            sign=combo[1],
            virtue=combo[2],
            hero=_default_hero(args, rng),
            seed=story_seed,
        )
        samples.append(generate(params))
    return samples


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    seen: set[str] = set()
    samples: list[StorySample] = []
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 30:
        story_seed = base_seed + attempts
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        attempts += 1
    return samples


def _emit_json(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
        return
    print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
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

        samples = _samples_for_all(args) if args.all else _samples_for_n(args)
        if args.json:
            _emit_json(samples)
            return 0
        for index, sample in enumerate(samples):
            header = None
            if args.all:
                header = f"### {sample.params.chamber} / {sample.params.sign} / {sample.params.virtue}"
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, args, header)
            if index != len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
