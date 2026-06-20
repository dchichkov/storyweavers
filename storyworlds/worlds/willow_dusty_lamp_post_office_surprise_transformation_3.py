#!/usr/bin/env python3
"""
Fairy-tale storyworld about willow mail and a dusty lamp in a post office.

Seed:
    Words: willow, dusty lamp
    Setting: post office
    Features: Surprise, Transformation
    Style: Fairy Tale

Internal source tale:
    In an old post office, a child helper finds one last piece of willow mail
    beneath a dusty lamp after the evening queue is gone. The mail cannot be
    sent yet because its true road is hidden: one letter has no visible
    address, one parcel sleeps inside a stubborn seal, and one postcard is
    folded too tightly to show its route. The child chooses the right lamp
    tending ritual for that kind of mail. When the ritual matches the need, the
    dusty lamp wakes, the mail transforms in a surprising physical way, and the
    ending image proves that the message has found its proper path.
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
    supports_mail: tuple[str, ...]
    supports_ritual: tuple[str, ...]
    hush: str


@dataclass(frozen=True)
class MailPiece:
    key: str
    phrase: str
    material: str
    problem: str
    need: str
    hidden_mark: str
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
            f"ritual={self.params.ritual} hero={self.params.hero} gender={self.params.gender}"
        )
        fact_text = ", ".join(f"{k}={v}" for k, v in sorted(self.facts.items()))
        lines.append(f"  facts: {fact_text}")
        lines.append("  entities:")
        for key, entity in self.entities.items():
            tags = ", ".join(f"{k}={v}" for k, v in sorted(entity.tags.items()))
            lines.append(f"    {key}: {entity.name} ({entity.kind}) at {entity.location}")
            if tags:
                lines.append(f"      tags={{{tags}}}")
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
    "moon_counter": Nook(
        "moon_counter",
        "the moon-painted counter in the old post office",
        "a dusty lamp with a round glass chimney and a brass moon on its shade",
        ("willow_letter", "willow_postcard"),
        ("wipe_glass", "pull_chain"),
        "the room had gone so quiet that even paper corners seemed to listen",
    ),
    "parcel_alcove": Nook(
        "parcel_alcove",
        "the parcel alcove beside the brass scale in the old post office",
        "a dusty lamp with a sleepy wick and a copper belly",
        ("willow_letter", "willow_parcel"),
        ("wipe_glass", "trim_wick"),
        "only the tick of the wall clock and the rustle of twine still moved",
    ),
    "pigeon_shelf": Nook(
        "pigeon_shelf",
        "the tall pigeonhole shelf of the old post office",
        "a dusty lamp hanging from a little chain above the empty slots",
        ("willow_letter", "willow_postcard"),
        ("wipe_glass", "pull_chain"),
        "the last stamps slept in their tray while the wooden slots held their breath",
    ),
}


MAILPIECES: dict[str, MailPiece] = {
    "willow_letter": MailPiece(
        "willow_letter",
        "a willow letter",
        "leaf-green paper tied with pale thread",
        "its address had vanished under a silver veil of dust",
        "clean_light",
        "the paper smelled faintly of rain and willow bark",
        "a vine-bright letter",
        "green-gold letters climbed across the page like tiny vines until a true address bloomed at the center",
        "the Willow Bridge dawn satchel",
        "Grandmother Fen at the willow gate",
        "the vine-bright address glowing through the canvas of the Willow Bridge satchel",
        "kind light reveals a hidden road better than guessing does",
    ),
    "willow_parcel": MailPiece(
        "willow_parcel",
        "a willow parcel",
        "thin willow bark wrapped with blue twine",
        "its wax seal slept so deeply that no ordinary thumb could wake it",
        "warm_wick",
        "a soft tapping came from inside, as if something small remembered spring",
        "a cradle-open parcel",
        "the bark wrapper softened and unfurled into a tiny willow cradle around a silver key and a proper delivery label",
        "the river-road morning cart",
        "the bridge keeper at the toll house",
        "the cradle-open parcel rocking gently on the river-road cart with its silver key shining in the straw",
        "patient warmth can open what force would only bruise",
    ),
    "willow_postcard": MailPiece(
        "willow_postcard",
        "a willow postcard",
        "flat green card with a border of pressed leaves",
        "its route line was folded so tightly that no one could tell which bag should carry it",
        "swing_shadow",
        "the leaf border cast a wing-shaped shadow whenever the lamp trembled",
        "a paper-swallow postcard",
        "the postcard lifted into a paper swallow shape, and dark ink feathers wrote the reed-dock route along its wings",
        "the reed-dock brass hook",
        "the boat child at the reed dock",
        "the paper-swallow postcard resting on the brass hook above the reed-dock pouch with its ink feathers spread",
        "moving shadows can show a pattern that flat eyes miss",
    ),
}


RITUALS: dict[str, Ritual] = {
    "wipe_glass": Ritual(
        "wipe_glass",
        "wiping the lamp glass",
        "clean_light",
        "lifted a linen sorting cloth and wiped the dusty lamp until the chimney shone clear",
        "The dusty lamp breathed out a honey-colored beam that could no longer hide behind powder.",
        "Only clear light can read what dust is hiding on paper.",
    ),
    "trim_wick": Ritual(
        "trim_wick",
        "trimming the wick",
        "warm_wick",
        "trimmed the sleepy wick with tiny brass scissors and fed it one patient spark",
        "The dusty lamp stood up in a warm amber flame, as neat and awake as a little watchman.",
        "A sleeping seal wakes to gentle warmth, not to pulling fingers.",
    ),
    "pull_chain": Ritual(
        "pull_chain",
        "pulling the chain three gentle times",
        "swing_shadow",
        "pulled the lamp chain three gentle times until the shade rocked over the counter like a slow firefly",
        "The dusty lamp swung from side to side and painted moving willow shadows over the waiting mail.",
        "A folded path can show itself when shadow begins to move.",
    ),
}


HEROES: dict[str, tuple[str, ...]] = {
    "girl": ("Mira", "Tansy", "Lina", "Etta", "Wren"),
    "boy": ("Rowan", "Theo", "Milo", "Ivo", "Nico"),
}


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def need_words(key: str) -> str:
    mapping = {
        "clean_light": "clear light",
        "warm_wick": "gentle warmth",
        "swing_shadow": "moving shadow",
    }
    return mapping.get(key, key.replace("_", " "))


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
            f"{ritual.phrase} cannot solve the problem because {mailpiece.phrase} needs {mailpiece.need.replace('_', ' ')}."
        )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for nook_key, nook in NOOKS.items():
        for mail_key, mailpiece in MAILPIECES.items():
            for ritual_key, ritual in RITUALS.items():
                if mail_key not in nook.supports_mail:
                    continue
                if ritual_key not in nook.supports_ritual:
                    continue
                if ritual.grants != mailpiece.need:
                    continue
                combos.append((nook_key, mail_key, ritual_key))
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
            "Old Post Office",
            "place",
            "village square",
            tags={"mood": "hushed", "setting": "post office"},
            meters={"quiet": 0.8, "lamplight": 0.2},
            memes={"order": 1.0},
        ),
    )
    world.add_entity(
        "hero",
        Entity(
            params.hero,
            "child",
            params.nook,
            tags={"role": "helper"},
            meters={"steadiness": 0.5},
            memes={"responsibility": 0.8, "worry": 0.7},
        ),
    )
    world.add_entity(
        "lamp",
        Entity(
            "Dusty Lamp",
            "object",
            params.nook,
            tags={"state": "sleeping"},
            meters={"dust": 1.0, "glow": 0.2},
            memes={"memory": 0.6},
        ),
    )
    world.add_entity(
        "mailpiece",
        Entity(
            mailpiece.phrase,
            "mail",
            params.nook,
            tags={"route_state": "uncertain"},
            meters={"route_clarity": 0.1, "transformation": 0.0},
            memes={"belonging": 0.4, "wonder": 0.2},
        ),
    )
    world.add_entity(
        "recipient",
        Entity(
            mailpiece.recipient,
            "recipient",
            mailpiece.route,
            tags={"status": "waiting"},
            meters={"distance": 1.0},
            memes={"expectation": 0.6},
        ),
    )
    return world


def _premise(world: World) -> None:
    hero = world.entities["hero"]
    mail = world.entities["mailpiece"]
    world.facts["setting"] = world.nook.phrase
    world.facts["problem"] = world.mailpiece.problem
    world.facts["need"] = world.mailpiece.need
    world.facts["hidden_mark"] = world.mailpiece.hidden_mark
    hero.add_meme("care", 0.5)
    mail.add_meme("waiting", 0.5)
    world.event("premise", place=world.nook.key, mail=world.mailpiece.key, hush=world.nook.hush)


def _tension(world: World) -> None:
    hero = world.entities["hero"]
    lamp = world.entities["lamp"]
    mail = world.entities["mailpiece"]
    hero.add_meme("worry", 0.4)
    hero.add_meter("steadiness", -0.1)
    lamp.add_meme("memory", 0.3)
    mail.add_meter("route_clarity", 0.0)
    world.facts["risk"] = "If the child guessed, the last piece of willow mail would travel the wrong road."
    world.event("tension", hidden_mark=world.mailpiece.hidden_mark, risk=world.facts["risk"])


def _turn(world: World) -> None:
    hero = world.entities["hero"]
    lamp = world.entities["lamp"]
    mail = world.entities["mailpiece"]
    recipient = world.entities["recipient"]
    post_office = world.entities["post_office"]

    lamp.set_tag("state", "awake")
    lamp.add_meter("glow", 0.9)
    lamp.add_meter("dust", -0.8)
    lamp.add_meme("revelation", 1.0)
    mail.add_meter("route_clarity", 1.0)
    mail.add_meter("transformation", 1.0)
    mail.add_meme("wonder", 1.2)
    mail.add_meme("belonging", 1.0)
    hero.add_meme("wonder", 1.1)
    hero.add_meter("steadiness", 0.5)
    post_office.add_meter("lamplight", 0.8)
    recipient.add_meme("expectation", 0.4)
    world.facts["transformed_form"] = world.mailpiece.transformed_form
    world.facts["route"] = world.mailpiece.route
    world.facts["awakening"] = world.ritual.awakening
    world.event(
        "turn",
        ritual=world.ritual.key,
        grants=world.ritual.grants,
        transformed_form=world.mailpiece.transformed_form,
    )


def _resolution(world: World) -> None:
    hero = world.entities["hero"]
    mail = world.entities["mailpiece"]
    recipient = world.entities["recipient"]
    hero.add_meme("relief", 1.2)
    hero.add_meme("responsibility", 0.5)
    mail.set_tag("route_state", "ready")
    recipient.set_tag("status", "reached")
    recipient.add_meter("distance", -1.0)
    world.facts["ending_image"] = world.mailpiece.ending_image
    world.facts["lesson"] = world.mailpiece.lesson
    world.event(
        "resolution",
        route=world.mailpiece.route,
        recipient=world.mailpiece.recipient,
        lesson=world.mailpiece.lesson,
    )


def tell(world: World) -> World:
    _premise(world)
    _tension(world)
    _turn(world)
    _resolution(world)

    subject, _, _ = pronouns(world.params.gender)
    hero = world.params.hero

    opening = (
        f"At dusk, when the last footsteps had faded from the old post office, {hero} remained by {world.nook.phrase}. "
        f"There under {world.nook.lamp_phrase} lay {world.mailpiece.phrase}, made of {world.mailpiece.material}, and {world.nook.hush}."
    )
    problem = (
        f"{hero} picked it up and saw at once that it could not be sent in its present state: {world.mailpiece.problem}. "
        f"{sentence_case(world.mailpiece.hidden_mark)}, and {subject} knew that if {subject} guessed at the road, "
        f"the last willow mail would wander away from {world.mailpiece.recipient}."
    )
    turn = (
        f"So {hero} chose {world.ritual.phrase}. {hero} {world.ritual.action}. "
        f"{world.ritual.awakening} Then the surprise arrived all at once: {world.mailpiece.transformation}."
    )
    ending = (
        f"{hero} placed the transformed mail onto {world.mailpiece.route} for {world.mailpiece.recipient}. "
        f"When the post office opened again at dawn, everyone could see {world.mailpiece.ending_image}. "
        f"{hero} understood that {world.mailpiece.lesson}."
    )

    world.paragraphs = [opening, problem, turn, ending]
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a fairy-tale story set in a post office that includes the words "willow" and "dusty lamp".',
        f"Tell a surprise-transformation story in which {world.params.hero} finds {world.mailpiece.phrase} at {world.nook.phrase}.",
        f"Show how {world.ritual.phrase} reveals the true road for willow mail in the old post office.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What problem did the child find in the post office?",
            f"{world.params.hero} found that {world.mailpiece.phrase} could not be mailed because {world.mailpiece.problem}. "
            f"That mattered because the child might have sent it down the wrong road if the hidden sign stayed concealed.",
        ),
        QAItem(
            "How did the dusty lamp help?",
            f"The dusty lamp helped after {world.params.hero} performed the ritual of {world.ritual.phrase}. "
            f"{world.ritual.awakening} That new light matched the mail's need and made the true route appear.",
        ),
        QAItem(
            "What changed during the surprise transformation?",
            f"The mail changed into {world.mailpiece.transformed_form}. "
            f"{world.mailpiece.transformation.capitalize()}, so the child could finally see where it belonged.",
        ),
        QAItem(
            "Where did the transformed mail go?",
            f"It went onto {world.mailpiece.route} for {world.mailpiece.recipient}. "
            f"The ending image proves the route was correct because {world.mailpiece.ending_image}.",
        ),
        QAItem(
            "Why was the chosen ritual the right one?",
            f"The ritual was right because {world.ritual.reason.lower()} "
            f"{world.mailpiece.phrase.capitalize()} needed {need_words(world.mailpiece.need)}, and that is exactly what the ritual provided.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    qas = [
        QAItem(
            "Why can dust matter in a post office story?",
            "Dust can hide writing, seals, and tiny route marks on real objects. In a storyworld like this one, clearing dust changes what the child is able to know and do.",
        ),
        QAItem(
            "Why should a child match the method to the problem?",
            "A good method fits the object instead of forcing it. When the action matches the problem, the object can change safely and the story's turn feels earned.",
        ),
        QAItem(
            "Why is the ending image important in a fairy tale?",
            "The ending image gives a physical proof that the change truly happened. It lets the child reader see the new state instead of hearing only a vague promise.",
        ),
    ]
    if world.mailpiece.need == "clean_light":
        qas.append(
            QAItem(
                "Why does clear light help a hidden address?",
                "Clear light lets faint marks rise from the paper instead of staying buried under dust. In this world, the address becomes visible only when the lamp can shine without powder in the way.",
            )
        )
    elif world.mailpiece.need == "warm_wick":
        qas.append(
            QAItem(
                "Why does warmth help a sleeping seal?",
                "Gentle warmth softens wax and wakes what has been closed too long. That is safer than tugging hard at a parcel that needs to open in one piece.",
            )
        )
    else:
        qas.append(
            QAItem(
                "Why do moving shadows help a folded route?",
                "A moving shadow can reveal edges and patterns that stay flat in still light. In this tale, the shifting lamp makes the postcard's hidden road show itself like wings.",
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
    parser = argparse.ArgumentParser(description="Generate willow post-office fairy-tale storyworld samples.")
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


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
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


def _default_gender(args: argparse.Namespace, rng: random.Random) -> str:
    return args.gender or rng.choice(sorted(HEROES))


def _default_hero(args: argparse.Namespace, gender: str, rng: random.Random) -> str:
    return args.hero or rng.choice(HEROES[gender])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = _matching_combos(args)
    if not combos:
        fallback_gender = args.gender or "girl"
        fallback_hero = args.hero or HEROES[fallback_gender][0]
        candidate = StoryParams(
            args.nook or "moon_counter",
            args.mailpiece or "willow_letter",
            args.ritual or "wipe_glass",
            fallback_hero,
            fallback_gender,
            getattr(rng, "story_seed", None),
        )
        reasonableness_gate(candidate)
    gender = _default_gender(args, rng)
    hero = _default_hero(args, gender, rng)
    nook, mailpiece, ritual = rng.choice(combos)
    return StoryParams(nook, mailpiece, ritual, hero, gender, getattr(rng, "story_seed", None))


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
combo(N,M,R) :-
    nook(N),
    mailpiece(M),
    ritual(R),
    supports_mail(N,M),
    supports_ritual(N,R),
    need(M,G),
    grants(R,G).

ok :- chosen(N,M,R), combo(N,M,R).

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

    for index, combo in enumerate(sorted(python_combos)):
        params = StoryParams(combo[0], combo[1], combo[2], "Mira", "girl", index)
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected Python-valid combo: {combo}")
        sample = generate(params)
        if "post office" not in sample.story or "dusty lamp" not in sample.story or "willow" not in sample.story:
            raise StoryError(f"Generated story dropped seed essentials for combo: {combo}")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated QA set is too thin for combo: {combo}")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story is missing a full beginning-turn-ending shape for combo: {combo}")
    return f"OK: clingo gate matches Python gate and exercised {len(python_combos)} story variants."


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 5000
    for index, combo in enumerate(valid_combos()):
        story_seed = base_seed + index
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        gender = _default_gender(args, rng)
        hero = _default_hero(args, gender, rng)
        params = StoryParams(combo[0], combo[1], combo[2], hero, gender, story_seed)
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
                header = f"### {sample.params.nook} / {sample.params.mailpiece} / {sample.params.ritual}"
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
