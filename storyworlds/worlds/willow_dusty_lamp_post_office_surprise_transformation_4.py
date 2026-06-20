#!/usr/bin/env python3
"""
Fairy-tale storyworld about willow mail and a dusty lamp in a post office.

Seed:
    Words: willow, dusty lamp
    Setting: post office
    Features: Surprise, Transformation
    Style: Fairy Tale

Internal source tale:
    In an old post office, a child helper stays after dusk to mind the last
    piece of willow mail resting beside a dusty lamp. The mail has a physical
    problem that makes delivery impossible: an address is hidden, a wax seal is
    sleeping, or a route crease is curled shut. The child refuses to guess and
    instead chooses the lamp-tending act that fits the mail's true need. The
    lamp wakes in a surprising way, the mail transforms into a shape that shows
    its path, and dawn reveals a final image that proves the promise of the
    post office has been kept.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

STORYWORLDS = Path(__file__).resolve().parents[1]
if str(STORYWORLDS) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Nook:
    key: str
    phrase: str
    lamp_phrase: str
    dawn_view: str
    supports_mail: tuple[str, ...]
    supports_ritual: tuple[str, ...]
    hush: str


@dataclass(frozen=True)
class MailPiece:
    key: str
    phrase: str
    material: str
    trouble: str
    need: str
    clue: str
    transformed_form: str
    transformation: str
    route: str
    recipient: str
    ending_image: str
    lesson: str


@dataclass(frozen=True)
class Ritual:
    key: str
    phrase: str
    grants: str
    action: str
    awakening: str
    reason: str


@dataclass
class StoryParams:
    nook: str
    mailpiece: str
    ritual: str
    hero: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    location: str
    tags: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@dataclass
class World:
    params: StoryParams
    nook: Nook
    mailpiece: MailPiece
    ritual: Ritual
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)

    def add_entity(self, key: str, entity: Entity) -> None:
        self.entities[key] = entity

    def event(self, kind: str, **data: str) -> None:
        row = {"kind": kind}
        row.update(data)
        self.history.append(row)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(
            "  params: "
            f"nook={self.params.nook} mailpiece={self.params.mailpiece} "
            f"ritual={self.params.ritual} hero={self.params.hero} gender={self.params.gender} seed={self.params.seed}"
        )
        lines.append("  facts:")
        for key, value in sorted(self.facts.items()):
            lines.append(f"    {key}={value}")
        lines.append("  entities:")
        for key, entity in self.entities.items():
            lines.append(f"    {key}: {entity.name} ({entity.kind}) at {entity.location}")
            if entity.tags:
                lines.append(f"      tags={entity.tags}")
            if entity.meters:
                lines.append(f"      meters={entity.meters}")
            if entity.memes:
                lines.append(f"      memes={entity.memes}")
        lines.append("  history:")
        for row in self.history:
            detail = ", ".join(f"{k}={v}" for k, v in row.items() if k != "kind")
            lines.append(f"    {row['kind']}: {detail}")
        return "\n".join(lines)


NOOKS: dict[str, Nook] = {
    "willow_window": Nook(
        key="willow_window",
        phrase="the willow-carved service window in the old post office",
        lamp_phrase="a dusty lamp with a glass chimney etched with little willow leaves and a short silver chain",
        dawn_view="the willow-carved sill facing Willow Row",
        supports_mail=("willow_invitation", "willow_postcard"),
        supports_ritual=("polish_chimney", "ring_chain"),
        hush="the stamp drawers were shut and even the hanging scale seemed to listen",
    ),
    "sorting_table": Nook(
        key="sorting_table",
        phrase="the sorting table beside the parcel cubbies in the old post office",
        lamp_phrase="a dusty lamp with a brass key in its side and a bowl round as a nest",
        dawn_view="the side-door boards beside the cart lane",
        supports_mail=("willow_invitation", "willow_parcel"),
        supports_ritual=("polish_chimney", "wind_key"),
        hush="only the paper twine and the wall clock still dared to move",
    ),
    "pigeon_gallery": Nook(
        key="pigeon_gallery",
        phrase="the high pigeonhole gallery above the counter of the old post office",
        lamp_phrase="a dusty lamp hanging on a fine chain with a tiny brass key above the empty mail slots",
        dawn_view="the upper rail facing Reed Landing",
        supports_mail=("willow_postcard", "willow_parcel"),
        supports_ritual=("wind_key", "ring_chain"),
        hush="the wooden slots held their breath as if one more message might change the night",
    ),
}


MAILPIECES: dict[str, MailPiece] = {
    "willow_invitation": MailPiece(
        key="willow_invitation",
        phrase="a willow invitation",
        material="leaf-green paper tied with silver thread",
        trouble="its address had faded beneath a powdery veil and no bag could claim it",
        need="clear_beam",
        clue="When the child tilted it, a faint scent of willow bark rose from the paper as if the true road were hiding just under the dust",
        transformed_form="a lantern-letter",
        transformation="golden writing climbed across the page, and the flat invitation lifted into a lantern-letter whose glowing seams spelled out Willow Row",
        route="the dawn satchel for Willow Row",
        recipient="the baker's daughter on Willow Row",
        ending_image="the lantern-letter shining through the satchel cloth like a tiny moonlit leaf",
        lesson="careful light finds a truer road than hurried guessing ever can",
    ),
    "willow_parcel": MailPiece(
        key="willow_parcel",
        phrase="a willow parcel",
        material="thin willow bark wrapped with blue twine and sleeping wax",
        trouble="its wax seal had gone stiff as winter sap, so the label inside could not wake",
        need="gentle_heat",
        clue="A soft tap sounded from the wrapper now and then, as if the parcel remembered spring but could not reach it",
        transformed_form="a cradle-basket parcel",
        transformation="the bark wrapper softened, opened, and folded itself into a cradle-basket parcel with a bright silver tag swinging from one handle",
        route="the creek cart beside the side door",
        recipient="the bridge gardener beyond the creek",
        ending_image="the cradle-basket parcel rocking softly in the straw of the creek cart while its silver tag flashed in the dawn",
        lesson="patient warmth opens what rough hands would only hurt",
    ),
    "willow_postcard": MailPiece(
        key="willow_postcard",
        phrase="a willow postcard",
        material="a flat green card bordered with pressed willow leaves",
        trouble="its route crease was curled shut so tightly that every pigeonhole sent it back",
        need="moving_shadow",
        clue="Each time the lamp trembled, the leaf border threw a wing-shaped shadow across the counter and then hid it again",
        transformed_form="a swallow-card",
        transformation="the stiff card arched into a swallow-card, and dark ink feathers drew Reed Landing along its wings as it settled back to the table",
        route="the reed pouch hanging over the river rack",
        recipient="the ferry child at Reed Landing",
        ending_image="the swallow-card resting on the reed pouch with its ink wings spread toward the river",
        lesson="sometimes a path appears only when still things are allowed to move",
    ),
}


RITUALS: dict[str, Ritual] = {
    "polish_chimney": Ritual(
        key="polish_chimney",
        phrase="polishing the lamp chimney with a sorting cloth",
        grants="clear_beam",
        action="lifted the soft sorting cloth and polished the dusty lamp until the chimney shone as clear as pond ice",
        awakening="The dusty lamp answered with a straight honey-colored beam that reached every hidden corner of the paper.",
        reason="Only a clear beam can wake writing that dust has buried.",
    ),
    "wind_key": Ritual(
        key="wind_key",
        phrase="winding the lamp's brass key three patient turns",
        grants="gentle_heat",
        action="set two fingers on the brass key and wound it three patient turns until the little wick stood taller",
        awakening="The dusty lamp glowed from within like a warm acorn, and its small circle of heat spread kindly across the table.",
        reason="Gentle heat is better than force when a sleeping seal must soften without tearing.",
    ),
    "ring_chain": Ritual(
        key="ring_chain",
        phrase="ringing the hanging chain in three slow silver notes",
        grants="moving_shadow",
        action="touched the hanging chain and rang it in three slow silver notes until the lamp began to sway",
        awakening="The dusty lamp swung from side to side and sent living willow shadows over the waiting mail.",
        reason="Moving shadow can reveal a folded path that flat light keeps hidden.",
    ),
}


HEROES: dict[str, tuple[str, ...]] = {
    "girl": ("Mira", "Tansy", "Etta", "Lina", "Wren"),
    "boy": ("Rowan", "Milo", "Theo", "Ivo", "Nico"),
}


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def need_phrase(key: str) -> str:
    mapping = {
        "clear_beam": "a clear beam",
        "gentle_heat": "gentle heat",
        "moving_shadow": "moving shadow",
    }
    return mapping.get(key, key.replace("_", " "))


def sentence_count(text: str) -> int:
    return sum(text.count(mark) for mark in ".!?")


def reasonableness_gate(params: StoryParams) -> None:
    if params.nook not in NOOKS:
        raise StoryError(f"No story: unknown nook {params.nook!r}.")
    if params.mailpiece not in MAILPIECES:
        raise StoryError(f"No story: unknown mailpiece {params.mailpiece!r}.")
    if params.ritual not in RITUALS:
        raise StoryError(f"No story: unknown ritual {params.ritual!r}.")
    if params.gender not in HEROES:
        raise StoryError(f"No story: unknown gender {params.gender!r}.")

    nook = NOOKS[params.nook]
    mailpiece = MAILPIECES[params.mailpiece]
    ritual = RITUALS[params.ritual]

    if params.mailpiece not in nook.supports_mail:
        raise StoryError(f"No story: {mailpiece.phrase} does not belong at {nook.phrase}.")
    if params.ritual not in nook.supports_ritual:
        raise StoryError(f"No story: {ritual.phrase} cannot be done with {nook.lamp_phrase}.")
    if ritual.grants != mailpiece.need:
        raise StoryError(
            "No story: "
            f"{mailpiece.phrase} needs {need_phrase(mailpiece.need)}, but {ritual.phrase} does not provide it."
        )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for nook in NOOKS.values():
        for mailpiece in MAILPIECES.values():
            if mailpiece.key not in nook.supports_mail:
                continue
            for ritual in RITUALS.values():
                if ritual.key not in nook.supports_ritual:
                    continue
                if ritual.grants != mailpiece.need:
                    continue
                combos.append((nook.key, mailpiece.key, ritual.key))
    return combos


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    nook = NOOKS[params.nook]
    mailpiece = MAILPIECES[params.mailpiece]
    ritual = RITUALS[params.ritual]
    world = World(params=params, nook=nook, mailpiece=mailpiece, ritual=ritual)

    world.add_entity(
        "post_office",
        Entity(
            name="Old Post Office",
            kind="place",
            location="village square",
            tags={"setting": "post office", "mood": "hushed"},
            meters={"hush": 0.82, "wonder": 0.18, "dawn": 0.05},
            memes={"promise": 1.0, "order": 0.8},
        ),
    )
    world.add_entity(
        "hero",
        Entity(
            name=params.hero,
            kind="child helper",
            location=params.nook,
            tags={"role": "helper", "duty": "last mail"},
            meters={"courage": 0.46, "patience": 0.64},
            memes={"care": 0.86, "worry": 0.54},
        ),
    )
    world.add_entity(
        "lamp",
        Entity(
            name="Dusty Lamp",
            kind="object",
            location=params.nook,
            tags={"state": "sleeping"},
            meters={"dust": 1.0, "glow": 0.15, "warmth": 0.1, "sway": 0.0},
            memes={"memory": 0.42, "wonder": 0.1},
        ),
    )
    world.add_entity(
        "mailpiece",
        Entity(
            name=mailpiece.phrase,
            kind="mail",
            location=params.nook,
            tags={"route_state": "uncertain", "shape": "ordinary"},
            meters={"route_clarity": 0.08, "sealedness": 0.82, "transformation": 0.0},
            memes={"belonging": 0.4, "waiting": 0.55},
        ),
    )
    world.add_entity(
        "recipient",
        Entity(
            name=mailpiece.recipient,
            kind="recipient",
            location=mailpiece.route,
            tags={"status": "waiting"},
            meters={"distance": 1.0},
            memes={"expectation": 0.66},
        ),
    )
    world.add_entity(
        "route_spot",
        Entity(
            name=mailpiece.route,
            kind="route",
            location=nook.dawn_view,
            tags={"state": "empty"},
            meters={"readiness": 0.2},
            memes={"direction": 0.5},
        ),
    )
    return world


def _premise(world: World) -> None:
    hero = world.entities["hero"]
    mail = world.entities["mailpiece"]
    post_office = world.entities["post_office"]
    world.facts["setting"] = world.nook.phrase
    world.facts["problem"] = world.mailpiece.trouble
    world.facts["recipient"] = world.mailpiece.recipient
    world.facts["route"] = world.mailpiece.route
    world.facts["lesson"] = world.mailpiece.lesson
    hero.add_meme("wonder", 0.12)
    mail.add_meme("hope", 0.18)
    post_office.add_meme("keeping_faith", 0.25)
    world.event(
        "premise",
        nook=world.nook.key,
        mailpiece=world.mailpiece.key,
        lamp_state=world.entities["lamp"].tags["state"],
    )


def _tension(world: World) -> None:
    hero = world.entities["hero"]
    mail = world.entities["mailpiece"]
    post_office = world.entities["post_office"]
    hero.add_meme("worry", 0.28)
    hero.add_meter("courage", 0.08)
    post_office.add_meter("hush", 0.05)
    mail.add_meter("route_clarity", 0.0)
    world.facts["risk"] = (
        f"If {world.params.hero} guessed, {world.mailpiece.phrase} might travel away from {world.mailpiece.recipient}."
    )
    world.facts["clue"] = world.mailpiece.clue
    world.event(
        "tension",
        trouble=world.mailpiece.trouble,
        clue=world.mailpiece.clue,
        risk=world.facts["risk"],
    )


def _turn(world: World) -> None:
    hero = world.entities["hero"]
    lamp = world.entities["lamp"]
    mail = world.entities["mailpiece"]
    post_office = world.entities["post_office"]

    lamp.set_tag("state", "awakened")
    lamp.add_meter("dust", -0.78)
    lamp.add_meter("glow", 0.9)
    lamp.add_meme("wonder", 1.0)
    hero.add_meme("wonder", 0.96)
    hero.add_meter("patience", 0.18)
    mail.add_meter("route_clarity", 0.94)
    mail.add_meter("transformation", 1.0)
    mail.add_meme("belonging", 0.9)
    mail.set_tag("shape", world.mailpiece.transformed_form)
    post_office.add_meter("wonder", 0.74)

    if world.ritual.grants == "gentle_heat":
        lamp.add_meter("warmth", 0.84)
        mail.add_meter("sealedness", -0.72)
    elif world.ritual.grants == "moving_shadow":
        lamp.add_meter("sway", 0.9)
        mail.add_meter("sealedness", -0.36)
    else:
        lamp.add_meter("warmth", 0.28)
        mail.add_meter("sealedness", -0.14)

    world.facts["awakening"] = world.ritual.awakening
    world.facts["transformation"] = world.mailpiece.transformation
    world.facts["transformed_form"] = world.mailpiece.transformed_form
    world.event(
        "turn",
        ritual=world.ritual.key,
        grants=world.ritual.grants,
        lamp_state=lamp.tags["state"],
        transformed_form=world.mailpiece.transformed_form,
    )


def _resolution(world: World) -> None:
    hero = world.entities["hero"]
    post_office = world.entities["post_office"]
    mail = world.entities["mailpiece"]
    recipient = world.entities["recipient"]
    route_spot = world.entities["route_spot"]

    hero.add_meme("relief", 1.0)
    hero.add_meme("duty_kept", 0.8)
    post_office.add_meter("dawn", 0.95)
    post_office.add_meme("promise", 0.4)
    mail.set_tag("route_state", "ready")
    recipient.set_tag("status", "nearly_reached")
    recipient.add_meter("distance", -0.96)
    route_spot.set_tag("state", "holding_mail")
    route_spot.add_meter("readiness", 0.78)
    world.facts["ending_image"] = world.mailpiece.ending_image
    world.event(
        "resolution",
        route=world.mailpiece.route,
        recipient=world.mailpiece.recipient,
        ending_image=world.mailpiece.ending_image,
    )


def tell(world: World) -> World:
    _premise(world)
    _tension(world)
    _turn(world)
    _resolution(world)

    hero_name = world.params.hero
    subject, _, _ = pronouns(world.params.gender)
    lamp = world.entities["lamp"]
    hero = world.entities["hero"]
    mail = world.entities["mailpiece"]

    if lamp.meters["glow"] > 0.9:
        beam_line = "The light no longer looked sleepy; it looked like a promise keeping watch."
    else:
        beam_line = "The light gathered itself softly, but it had not yet shown its whole heart."

    if hero.meters["patience"] >= 0.8:
        turn_manner = "with the patient care of a child who means to do one small thing exactly right"
    else:
        turn_manner = "with careful fingers"

    if mail.meters["route_clarity"] >= 0.9:
        ending_proof = "No one had to guess anymore, because the changed mail now showed its own road."
    else:
        ending_proof = "The road was less hidden than before, though the night still guarded part of it."

    opening = (
        f"In the old post office, after the last boots had gone down the lane, {hero_name} stayed beside {world.nook.phrase}. "
        f"There under {world.nook.lamp_phrase} rested {world.mailpiece.phrase}, made of {world.mailpiece.material}, and {world.nook.hush}."
    )
    tension = (
        f"When {hero_name} lifted the mail, the trouble showed itself at once: {world.mailpiece.trouble}. "
        f"{sentence_case(world.mailpiece.clue)}. {hero_name} would not guess at the road, for {subject} knew that a wrong guess would keep {world.mailpiece.recipient} waiting."
    )
    turn = (
        f"So {hero_name} chose {world.ritual.phrase} {turn_manner}. {hero_name} {world.ritual.action}. "
        f"{world.ritual.awakening} {beam_line} Then the surprise came: {world.mailpiece.transformation}."
    )
    ending = (
        f"{hero_name} set the transformed mail onto {world.mailpiece.route} for {world.mailpiece.recipient}. "
        f"When dawn entered through the high panes and touched {world.nook.dawn_view}, everyone could see {world.mailpiece.ending_image}. "
        f"{ending_proof} {hero_name} remembered that {world.mailpiece.lesson}."
    )

    world.paragraphs = [opening, tension, turn, ending]
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a fairy-tale story set in a post office that includes the words "willow" and "dusty lamp".',
        f"Tell a surprise-transformation tale where {world.params.hero} finds {world.mailpiece.phrase} at {world.nook.phrase}.",
        f"Show how {world.ritual.phrase} changes the mail into {world.mailpiece.transformed_form} and reveals its true route.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why did the child stay with the last piece of mail?",
            answer=(
                f"{world.params.hero} stayed because {world.mailpiece.phrase} still could not be delivered in its ordinary state. "
                f"The child cared about the post office's promise and would not let the last willow message go astray."
            ),
        ),
        QAItem(
            question="What problem made the mail hard to send?",
            answer=(
                f"The problem was that {world.mailpiece.trouble}. "
                f"That meant the route could not be trusted until the hidden sign was physically revealed."
            ),
        ),
        QAItem(
            question="How did the dusty lamp help the child?",
            answer=(
                f"The dusty lamp helped after {world.params.hero} chose {world.ritual.phrase}. "
                f"{world.ritual.awakening} Because that change matched the mail's need, the lamp turned confusion into guidance."
            ),
        ),
        QAItem(
            question="What was the surprise transformation?",
            answer=(
                f"The mail transformed into {world.mailpiece.transformed_form}. "
                f"{sentence_case(world.mailpiece.transformation)}."
            ),
        ),
        QAItem(
            question="How does the ending image prove the story changed?",
            answer=(
                f"The ending image is {world.mailpiece.ending_image}. "
                f"That picture proves the mail is no longer lost, because it is resting on the right route for {world.mailpiece.recipient}."
            ),
        ),
        QAItem(
            question="Why was the chosen ritual the right one?",
            answer=(
                f"It was the right ritual because {world.ritual.reason.lower()} "
                f"{world.mailpiece.phrase.capitalize()} needed {need_phrase(world.mailpiece.need)}, and that is exactly what the child gave it."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    qas = [
        QAItem(
            question="Why is it better to match a method to a problem than to guess?",
            answer=(
                "A matched method changes the object in the way it truly needs. Guessing may feel faster, but it sends effort in the wrong direction and can break trust."
            ),
        ),
        QAItem(
            question="Why do fairy tales often end with a strong physical image?",
            answer=(
                "A strong image lets the reader see that the world has truly changed. It is a child-facing proof, not just a statement that everything turned out well."
            ),
        ),
        QAItem(
            question="Why does a post office make a good setting for a promise-keeping story?",
            answer=(
                "A post office is built around carrying messages to the right hands. That makes every missed route feel important and every true delivery feel like a promise fulfilled."
            ),
        ),
    ]
    if world.mailpiece.need == "clear_beam":
        qas.append(
            QAItem(
                question="Why can clear light matter so much on paper?",
                answer=(
                    "Clear light can lift faint marks out of dust and shadow. In a story like this one, seeing clearly is the first step toward sending faithfully."
                ),
            )
        )
    elif world.mailpiece.need == "gentle_heat":
        qas.append(
            QAItem(
                question="Why is gentle warmth safer than force for a sealed parcel?",
                answer=(
                    "Gentle warmth softens what has tightened without tearing the object apart. Force might open it faster, but it can also damage the very thing the story is trying to protect."
                ),
            )
        )
    else:
        qas.append(
            QAItem(
                question="Why can moving shadow reveal something still light cannot?",
                answer=(
                    "Movement makes edges and folds announce themselves. A changing shadow can show a hidden pattern that lies quiet under ordinary light."
                ),
            )
        )
    return qas


def generate(params: StoryParams) -> StorySample:
    world = tell(build_world(params))
    story = "\n\n".join(world.paragraphs)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate willow dusty-lamp post-office fairy-tale storyworld samples."
    )
    parser.add_argument("--nook", choices=sorted(NOOKS))
    parser.add_argument("--mailpiece", choices=sorted(MAILPIECES))
    parser.add_argument("--ritual", choices=sorted(RITUALS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES))
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


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for nook, mailpiece, ritual in valid_combos():
        if args.nook and args.nook != nook:
            continue
        if args.mailpiece and args.mailpiece != mailpiece:
            continue
        if args.ritual and args.ritual != ritual:
            continue
        combos.append((nook, mailpiece, ritual))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = matching_combos(args)
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    if not combos:
        candidate = StoryParams(
            nook=args.nook or sorted(NOOKS)[0],
            mailpiece=args.mailpiece or sorted(MAILPIECES)[0],
            ritual=args.ritual or sorted(RITUALS)[0],
            hero=hero,
            gender=gender,
            seed=getattr(rng, "story_seed", None),
        )
        try:
            reasonableness_gate(candidate)
        except StoryError as exc:
            raise StoryError(str(exc)) from exc
        raise StoryError("No story: those filters do not leave any reasonable fairy-tale variants.")
    nook, mailpiece, ritual = rng.choice(combos)
    return StoryParams(
        nook=nook,
        mailpiece=mailpiece,
        ritual=ritual,
        hero=hero,
        gender=gender,
        seed=getattr(rng, "story_seed", None),
    )


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if args.qa:
        print()
        print("== (1) Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, start=1):
            print(f"{index}. {prompt}")
        print()
        print("== (2) Story-grounded QA ==")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print()
        print("== (3) World-knowledge QA ==")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


ASP_RULES = r"""
combo(N,M,R) :-
    nook(N),
    mailpiece(M),
    ritual(R),
    supports_mail(N,M),
    supports_ritual(N,R),
    need(M,G),
    grants(R,G).

ok :- chosen(N,M,R), combo(N,M,R).
:- chosen(N,M,R), not combo(N,M,R).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    rows: list[str] = []
    for nook in NOOKS.values():
        rows.append(asp.fact("nook", nook.key))
        for mailpiece in nook.supports_mail:
            rows.append(asp.fact("supports_mail", nook.key, mailpiece))
        for ritual in nook.supports_ritual:
            rows.append(asp.fact("supports_ritual", nook.key, ritual))
    for mailpiece in MAILPIECES.values():
        rows.append(asp.fact("mailpiece", mailpiece.key))
        rows.append(asp.fact("need", mailpiece.key, mailpiece.need))
    for ritual in RITUALS.values():
        rows.append(asp.fact("ritual", ritual.key))
        rows.append(asp.fact("grants", ritual.key, ritual.grants))
    if params is not None:
        rows.append(asp.fact("chosen", params.nook, params.mailpiece, params.ritual))
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

    for index, combo in enumerate(sorted(python_combos), start=1):
        params = StoryParams(
            nook=combo[0],
            mailpiece=combo[1],
            ritual=combo[2],
            hero="Mira",
            gender="girl",
            seed=index,
        )
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected Python-valid combo: {combo}")
        sample = generate(params)
        lowered = sample.story.lower()
        if "willow" not in lowered or "dusty lamp" not in lowered or "post office" not in lowered:
            raise StoryError(f"Generated story dropped seed essentials for combo: {combo}")
        if len(sample.story.split("\n\n")) != 4:
            raise StoryError(f"Generated story is missing a four-part tale shape for combo: {combo}")
        if len(sample.prompts) < 3 or len(sample.story_qa) < 6 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated prompts or QA are too thin for combo: {combo}")
        if any(sentence_count(item.answer) < 2 for item in sample.story_qa):
            raise StoryError(f"A story-grounded QA answer is too fragmentary for combo: {combo}")
        if sample.world is None:
            raise StoryError(f"Generated sample is missing its world model for combo: {combo}")
        if len(sample.world.history) != 4:
            raise StoryError(f"World history does not have premise/tension/turn/resolution for combo: {combo}")
        if sample.world.entities["lamp"].tags.get("state") != "awakened":
            raise StoryError(f"Lamp failed to awaken for combo: {combo}")
        if sample.world.entities["mailpiece"].tags.get("route_state") != "ready":
            raise StoryError(f"Mail failed to reach a ready route for combo: {combo}")
    return f"OK: clingo gate matches Python gate and exercised {len(python_combos)} story variants."


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_combos(args)
        if not combos:
            raise StoryError("No story: those filters do not leave any reasonable fairy-tale variants.")
        base_seed = args.seed if args.seed is not None else 4000
        samples: list[StorySample] = []
        for index, combo in enumerate(combos):
            story_seed = base_seed + index
            rng = random.Random(story_seed)
            rng.story_seed = story_seed
            gender = args.gender or rng.choice(sorted(HEROES))
            hero = args.hero or rng.choice(HEROES[gender])
            params = StoryParams(
                nook=combo[0],
                mailpiece=combo[1],
                ritual=combo[2],
                hero=hero,
                gender=gender,
                seed=story_seed,
            )
            samples.append(generate(params))
        return samples

    target = max(1, args.n)
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    while len(samples) < target and attempts < target * 40:
        story_seed = base_seed + attempts
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        attempts += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Could not generate enough unique willow dusty-lamp post-office stories with those constraints.")
    return samples


def emit_json(samples: list[StorySample]) -> None:
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

        samples = samples_from_args(args)
        if args.json:
            emit_json(samples)
            return 0
        for index, sample in enumerate(samples, start=1):
            header = None
            if args.all:
                header = f"### {sample.params.nook} / {sample.params.mailpiece} / {sample.params.ritual}"
            elif len(samples) > 1:
                header = f"### variant {index}"
            emit(sample, args, header)
            if index != len(samples):
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
