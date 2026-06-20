#!/usr/bin/env python3
"""A fairy-tale storyworld about willow mail and a dusty lamp in a post office.

Seed:
    Words: willow, dusty lamp
    Setting: post office
    Features: Surprise, Transformation
    Style: Fairy Tale

Source tale used for the simulation:
    In an old village post office, a child helper finds one last piece of
    willow mail resting under a dusty lamp. The mail cannot be sent by ordinary
    sorting, because something about it is hidden, sleeping, or folded shut.
    The postmistress knows that the dusty lamp wakes truthful mail, but only
    when it is tended in the right way. Once the child performs the proper
    ritual, the lamp brightens, the mail transforms in a surprising form, and
    the story ends with a concrete image proving that the lost message found its
    true home.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass(frozen=True)
class Alcove:
    id: str
    label: str
    scene: str
    affords: set[str]
    lamp_detail: str
    tags: set[str]


@dataclass(frozen=True)
class MailPiece:
    id: str
    label: str
    material: str
    problem: str
    need: str
    transform_kind: str
    recipient: str
    hidden_sign: str
    transform_sentence: str
    tags: set[str]


@dataclass(frozen=True)
class Ritual:
    id: str
    label: str
    grants: str
    action: str
    awakening: str
    prompt: str
    tags: set[str]


@dataclass(frozen=True)
class Recipient:
    id: str
    label: str
    home: str
    accepts: set[str]
    reveal: str
    delivery: str
    proof: str
    tags: set[str]


@dataclass(frozen=True)
class HeroSeed:
    id: str
    name: str
    gender: str
    trait: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: Optional[str] = None
    meters: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    states: set[str] = field(default_factory=set)
    note: str = ""


class World:
    def __init__(self, params: "StoryParams"):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.events: list[str] = []
        self.facts: dict[str, str] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def break_para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event: str) -> None:
        self.events.append(event)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = [
            f"params: alcove={self.params.alcove} mailpiece={self.params.mailpiece} ritual={self.params.ritual} hero={self.params.hero}",
            f"facts: {self.facts}",
            "events:",
        ]
        if self.events:
            for event in self.events:
                lines.append(f"  - {event}")
        else:
            lines.append("  - none")
        lines.append("entities:")
        for ent in self.entities.values():
            bits = [f"  {ent.id} | {ent.kind} | {ent.label}"]
            if ent.location:
                bits.append(f"location={ent.location}")
            if ent.states:
                bits.append(f"states={sorted(ent.states)}")
            if ent.note:
                bits.append(f"note={ent.note}")
            lines.append(" | ".join(bits))
            if ent.meters:
                lines.append(f"    meters={dict(ent.meters)}")
            if ent.memes:
                lines.append(f"    memes={dict(ent.memes)}")
        return "\n".join(lines)


@dataclass(frozen=True)
class StoryParams:
    alcove: str
    mailpiece: str
    ritual: str
    hero: str
    seed: Optional[int] = None


ALCOVES = {
    "moon_counter": Alcove(
        "moon_counter",
        "the moon-painted counter",
        "the moon-painted counter at the back of the post office",
        {"willow_letter", "willow_postcard"},
        "Above it hung a dusty lamp with a little crescent cut into its brass shade.",
        {"counter", "lamp", "letters"},
    ),
    "parcel_window": Alcove(
        "parcel_window",
        "the parcel window",
        "the parcel window where twine, wax, and stamps slept in neat rows",
        {"willow_letter", "willow_parcel"},
        "A dusty lamp drooped there on a crooked chain, as if it had nodded off while counting parcels.",
        {"window", "parcel", "lamp"},
    ),
    "pigeon_shelf": Alcove(
        "pigeon_shelf",
        "the pigeonhole shelf",
        "the tall pigeonhole shelf where unsent notes waited in little wooden squares",
        {"willow_letter", "willow_postcard"},
        "A dusty lamp watched from the top shelf, gray with powder and old stories.",
        {"shelf", "sorting", "lamp"},
    ),
}


MAILPIECES = {
    "willow_letter": MailPiece(
        "willow_letter",
        "willow letter",
        "leaf-green paper tied with pale thread",
        "its address was hidden under a veil of pearly dust",
        "clear_glass",
        "address_bloom",
        "willow_cottage",
        "The paper carried a faint smell of rain and willow bark",
        "green-gold letters climbed across the page like tiny vines, and a true address bloomed where none had shown before",
        {"letter", "willow", "address", "transformation"},
    ),
    "willow_parcel": MailPiece(
        "willow_parcel",
        "willow parcel",
        "thin willow bark wrapped with blue twine",
        "its wax seal slept so deeply that no ordinary thumb could wake it",
        "warm_wick",
        "brass_key",
        "bridge_postbox",
        "The parcel gave one soft thump, as if something inside remembered a journey",
        "the wax seal curled, shimmered, and became a tiny brass key hanging in a ribbon of warm smoke",
        {"parcel", "willow", "seal", "transformation"},
    ),
    "willow_postcard": MailPiece(
        "willow_postcard",
        "willow postcard",
        "a silver-edged card pressed with a real willow leaf",
        "its message had folded itself inward until the card looked almost blank",
        "bell_chime",
        "paper_swallow",
        "reed_boathouse",
        "When tilted, the card flashed like a fish scale and then went plain again",
        "the card folded itself into a paper swallow with silver wings and a pointed little beak",
        {"postcard", "willow", "bird", "transformation"},
    ),
}


RITUALS = {
    "polish_glass": Ritual(
        "polish_glass",
        "polish the lamp glass",
        "clear_glass",
        "breathed on the chimney and polished the glass with a soft sorting cloth",
        "The dust slid away in silky rings, and the lamp opened one clear gold eye.",
        "polishing the lamp glass until it shone",
        {"care", "glass", "light"},
    ),
    "trim_wick": Ritual(
        "trim_wick",
        "trim the lamp wick",
        "warm_wick",
        "trimmed the wick and fed it one bright drop of oil from the postmistress's blue bottle",
        "The flame stood up straight and blue, and warm light gathered under the brass shade.",
        "trimming the wick and giving the lamp a drop of oil",
        {"care", "flame", "warmth"},
    ),
    "ring_chain": Ritual(
        "ring_chain",
        "ring the little lamp chain",
        "bell_chime",
        "tugged the little brass chain until the lamp answered with a silver chime",
        "The note ran through the pigeonholes like a tiny bellbird and made the dust tremble loose.",
        "ringing the lamp chain for one silver chime",
        {"care", "sound", "chime"},
    ),
}


RECIPIENTS = {
    "willow_cottage": Recipient(
        "willow_cottage",
        "the basket-maker in the willow cottage",
        "the willow cottage at the edge of town",
        {"address_bloom"},
        "The lost letter belonged to the basket-maker in the willow cottage at the edge of town.",
        "By the time the evening bell rang, the letter was resting in the basket-maker's hands beside a doorstep woven with willow reeds.",
        "a new willow basket sat on the post office counter in the morning with a plum tucked inside it for thanks",
        {"cottage", "willow", "home"},
    ),
    "bridge_postbox": Recipient(
        "bridge_postbox",
        "Grandmother Fen's blue postbox by the willow bridge",
        "the blue postbox under the willow bridge",
        {"brass_key"},
        "The tiny brass key belonged to Grandmother Fen's blue postbox under the willow bridge.",
        "The key clicked the blue postbox open, and the parcel slipped safely inside before the river mist could thicken.",
        "the blue postbox shone with its door open, and a thank-you sprig of willow was tied to the latch",
        {"bridge", "postbox", "willow"},
    ),
    "reed_boathouse": Recipient(
        "reed_boathouse",
        "the ferryman at the reed boathouse past Willow Bend",
        "the reed boathouse past Willow Bend",
        {"paper_swallow"},
        "The paper swallow knew the road to the ferryman at the reed boathouse past Willow Bend.",
        "It fluttered ahead through the dusk until the ferryman laughed, caught the postcard gently, and read the hidden message at last.",
        "the postcard was sleeping again on the ferryman's windowsill, while a silver feather lay on the post office ledger as a surprise",
        {"boathouse", "willow", "bird"},
    ),
}


HEROES = {
    "mira": HeroSeed("mira", "Mira", "girl", "patient"),
    "tobin": HeroSeed("tobin", "Tobin", "boy", "careful"),
    "nella": HeroSeed("nella", "Nella", "girl", "bright-eyed"),
    "eli": HeroSeed("eli", "Eli", "boy", "gentle"),
}


CURATED = [
    StoryParams("moon_counter", "willow_letter", "polish_glass", "mira", 701),
    StoryParams("parcel_window", "willow_parcel", "trim_wick", "tobin", 702),
    StoryParams("pigeon_shelf", "willow_postcard", "ring_chain", "nella", 703),
    StoryParams("moon_counter", "willow_postcard", "ring_chain", "eli", 704),
]


NEED_EXPLANATIONS = {
    "clear_glass": "clear, wakeful light before its hidden writing could be seen",
    "warm_wick": "a warm, steady flame before its sleeping seal would loosen",
    "bell_chime": "a bright silver chime before its folded message would open",
}


def pronoun_possessive(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def valid_combo(alcove_id: str, mail_id: str, ritual_id: str, hero_id: str) -> bool:
    if alcove_id not in ALCOVES or mail_id not in MAILPIECES or ritual_id not in RITUALS or hero_id not in HEROES:
        return False
    alcove = ALCOVES[alcove_id]
    mail = MAILPIECES[mail_id]
    ritual = RITUALS[ritual_id]
    recipient = RECIPIENTS[mail.recipient]
    return (
        mail.id in alcove.affords
        and ritual.grants == mail.need
        and mail.transform_kind in recipient.accepts
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for alcove_id in sorted(ALCOVES):
        for mail_id in sorted(MAILPIECES):
            for ritual_id in sorted(RITUALS):
                for hero_id in sorted(HEROES):
                    if valid_combo(alcove_id, mail_id, ritual_id, hero_id):
                        combos.append((alcove_id, mail_id, ritual_id, hero_id))
    return combos


def explain_rejection(alcove_id: str, mail_id: str, ritual_id: str, hero_id: str) -> str:
    if alcove_id not in ALCOVES:
        return f"Unknown post-office alcove {alcove_id!r}."
    if mail_id not in MAILPIECES:
        return f"Unknown willow mailpiece {mail_id!r}."
    if ritual_id not in RITUALS:
        return f"Unknown lamp ritual {ritual_id!r}."
    if hero_id not in HEROES:
        return f"Unknown hero {hero_id!r}."
    alcove = ALCOVES[alcove_id]
    mail = MAILPIECES[mail_id]
    ritual = RITUALS[ritual_id]
    recipient = RECIPIENTS[mail.recipient]
    if mail.id not in alcove.affords:
        return f"{alcove.label} does not plausibly hold the {mail.label}."
    if ritual.grants != mail.need:
        return f"{ritual.label} cannot solve this mail's trouble; the {mail.label} needs {mail.need}."
    if mail.transform_kind not in recipient.accepts:
        return f"{recipient.label} would not plausibly receive a {mail.transform_kind} ending."
    return "That fairy-tale post office story is outside the valid set."


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.alcove, params.mailpiece, params.ritual, params.hero):
        raise StoryError(explain_rejection(params.alcove, params.mailpiece, params.ritual, params.hero))

    world = World(params)
    hero_seed = HEROES[params.hero]
    alcove = ALCOVES[params.alcove]
    mail = MAILPIECES[params.mailpiece]
    ritual = RITUALS[params.ritual]
    recipient = RECIPIENTS[mail.recipient]

    hero = world.add(Entity("hero", "child", hero_seed.name, location="post_office"))
    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 1.0
    hero.note = hero_seed.trait

    keeper = world.add(Entity("keeper", "postmistress", "Mistress Alder", location="post_office"))
    keeper.memes["patience"] = 1.0
    keeper.memes["knowing"] = 1.0
    keeper.note = "keeper of the night lamp"

    lamp = world.add(Entity("lamp", "object", "dusty lamp", location=alcove.id))
    lamp.meters["dust"] = 1.0
    lamp.meters["glow"] = 0.0
    lamp.meters["awakened"] = 0.0
    lamp.memes["memory"] = 1.0
    lamp.states.add("sleeping")

    mail_ent = world.add(Entity("mail", "mail", mail.label, location=alcove.id))
    mail_ent.meters["hidden"] = 1.0
    mail_ent.meters["transformed"] = 0.0
    mail_ent.meters["delivered"] = 0.0
    mail_ent.memes["homesick"] = 1.0
    mail_ent.note = mail.material
    mail_ent.states.add("unsent")

    dest = world.add(Entity("recipient", "destination", recipient.label, location=recipient.home))
    dest.meters["ready"] = 1.0

    world.facts["alcove"] = alcove.id
    world.facts["mailpiece"] = mail.id
    world.facts["ritual"] = ritual.id
    world.facts["recipient"] = recipient.id
    return world


def introduce(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    alcove = ALCOVES[params.alcove]
    mail = MAILPIECES[params.mailpiece]
    hero = world.get("hero")
    keeper = world.get("keeper")

    world.say(
        f"At dusk, {hero_seed.name}, a {hero_seed.trait} child, was minding {alcove.scene} in the old village post office."
    )
    world.say(alcove.lamp_detail)
    world.say(
        f"Under the lamp lay a {mail.label} made of {mail.material}, and it was the very last piece of mail before the shutters were meant to close."
    )
    world.say(
        f"{mail.hidden_sign}. Mistress Alder always said that no fairy-tale post office should sleep while a lonely letter was still wondering where it belonged."
    )
    hero.meters["present"] = 1.0
    keeper.meters["present"] = 1.0
    world.record("scene_introduced")


def tension(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    hero = world.get("hero")

    world.break_para()
    world.say(f"{hero_seed.name} lifted the {mail.label} and saw that {mail.problem}.")
    world.say(
        f"A little thread of worry tugged at {pronoun_possessive(hero_seed.gender)} chest, because the postmark glimmered as if it remembered a home that the sorting table had forgotten."
    )
    world.say(
        '"There now," said Mistress Alder. "That dusty lamp tells the truth to gentle hands, but it wakes in only one right way."'
    )
    hero.meters["worry"] = 1.0
    hero.memes["hope"] += 0.5
    world.record("problem_recognized")


def awaken_and_transform(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    ritual = RITUALS[params.ritual]
    recipient = RECIPIENTS[mail.recipient]
    hero = world.get("hero")
    lamp = world.get("lamp")
    mail_ent = world.get("mail")

    world.break_para()
    world.say(f"So {hero_seed.name} {ritual.action}.")
    world.say(ritual.awakening)
    lamp.meters["dust"] = 0.0
    lamp.meters["glow"] = 1.0
    lamp.meters["awakened"] = 1.0
    lamp.states.discard("sleeping")
    lamp.states.add("awake")
    lamp.label = "bright lamp"

    world.say(
        f"At once the {mail.label} stirred under the clear light, and {mail.transform_sentence}."
    )
    world.say(
        f"It was such a sweet surprise that {hero_seed.name} laughed aloud, and even Mistress Alder's stern mouth turned into a moon-shaped smile."
    )
    mail_ent.meters["hidden"] = 0.0
    mail_ent.meters["transformed"] = 1.0
    mail_ent.states.discard("unsent")
    mail_ent.states.add(mail.transform_kind)
    mail_ent.label = {
        "address_bloom": "letter with a blooming address",
        "brass_key": "parcel with a brass key",
        "paper_swallow": "paper swallow postcard",
    }[mail.transform_kind]
    hero.memes["wonder"] += 1.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] += 1.0
    world.facts["transformation"] = mail.transform_kind
    world.record("lamp_awakened")
    world.record("mail_transformed")
    world.say(recipient.reveal)


def deliver(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    recipient = RECIPIENTS[mail.recipient]
    hero = world.get("hero")
    mail_ent = world.get("mail")
    dest = world.get("recipient")

    world.say(recipient.delivery)
    world.say(
        f"When {hero_seed.name} returned, the post office no longer looked sleepy. The lamp burned clear above the quiet counter, and {recipient.proof}."
    )
    hero.memes["relief"] += 1.0
    hero.memes["wonder"] += 0.5
    mail_ent.meters["delivered"] = 1.0
    mail_ent.location = recipient.home
    dest.states.add("reached")
    world.record("mail_delivered")


def tell(world: World) -> str:
    introduce(world)
    tension(world)
    awaken_and_transform(world)
    deliver(world)
    return world.render()


def generation_prompts(params: StoryParams) -> list[str]:
    hero = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    ritual = RITUALS[params.ritual]
    return [
        'Write a fairy tale set in a post office that includes a willow object and a dusty lamp.',
        f"Write a surprise transformation story where {hero.name} saves a {mail.label} by {ritual.prompt}.",
        "Write a fairy tale where careful tending, not force, helps lost mail find its true home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.params
    hero = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    ritual = RITUALS[params.ritual]
    recipient = RECIPIENTS[mail.recipient]
    return [
        QAItem(
            f"Why could {hero.name} not send the {mail.label} at first?",
            f"{hero.name} could not send it at first because {mail.problem}. The post office needed the lamp's help before the mail could show where it truly belonged.",
        ),
        QAItem(
            "How was the dusty lamp awakened?",
            f"The dusty lamp was awakened when {hero.name} {ritual.action}. That careful act gave the lamp exactly the kind of waking it needed.",
        ),
        QAItem(
            f"What changed when the lamp shone on the {mail.label}?",
            f"When the lamp shone on it, {mail.transform_sentence}. That surprise transformation revealed the path to {recipient.label}.",
        ),
        QAItem(
            "How did the ending prove that the problem was solved?",
            f"The ending proved it because {recipient.proof}. The bright lamp and the thankful token showed that the lost mail had reached its true home.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    params = world.params
    mail = MAILPIECES[params.mailpiece]
    ritual = RITUALS[params.ritual]
    recipient = RECIPIENTS[mail.recipient]
    items = [
        QAItem(
            "What is a post office for?",
            "A post office gathers letters and parcels, sorts them carefully, and helps each one travel to the right home. In a fairy tale, it can also be the place where lost messages are gently understood.",
        ),
        QAItem(
            "Why is a lamp useful in an old post office?",
            "A lamp helps people read small writing and notice quiet details after the sun goes down. In this world, the lamp also helps true addresses and messages show themselves.",
        ),
        QAItem(
            "Why might willow appear in a fairy tale?",
            "Willow often suggests softness, memory, and places near water or old roads. That makes it a good symbol for messages that are waiting to find their way home.",
        ),
        QAItem(
            "Why was that lamp ritual the right one?",
            f"It was the right one because the {mail.label} needed {NEED_EXPLANATIONS[mail.need]}. The ritual matched the mail gently instead of forcing the answer too quickly.",
        ),
        QAItem(
            f"What kind of place is {recipient.home}?",
            f"It is the place where this story's hidden message truly belonged. The transformation was believable because it pointed toward that home in a concrete, visible way.",
        ),
    ]
    tags = set().union(mail.tags, ritual.tags, recipient.tags, ALCOVES[params.alcove].tags)
    selected: list[QAItem] = []
    for item in items:
        if "willow" in item.answer.lower() and "willow" not in tags:
            continue
        selected.append(item)
    return selected[:4]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = tell(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(A,M,R,H) :-
    alcove(A),
    mailpiece(M),
    ritual(R),
    hero(H),
    affords(A,M),
    need(M,N),
    grants(R,N),
    recipient_for(M,Rec),
    transform(M,T),
    accepts(Rec,T).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for alcove in ALCOVES.values():
        facts.append(asp.fact("alcove", alcove.id))
        for mail_id in alcove.affords:
            facts.append(asp.fact("affords", alcove.id, mail_id))
    for mail in MAILPIECES.values():
        facts.append(asp.fact("mailpiece", mail.id))
        facts.append(asp.fact("need", mail.id, mail.need))
        facts.append(asp.fact("transform", mail.id, mail.transform_kind))
        facts.append(asp.fact("recipient_for", mail.id, mail.recipient))
    for ritual in RITUALS.values():
        facts.append(asp.fact("ritual", ritual.id))
        facts.append(asp.fact("grants", ritual.id, ritual.grants))
    for recipient in RECIPIENTS.values():
        facts.append(asp.fact("recipient", recipient.id))
        for transform in recipient.accepts:
            facts.append(asp.fact("accepts", recipient.id, transform))
    for hero in HEROES.values():
        facts.append(asp.fact("hero", hero.id))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_facts() + ASP_RULES):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(x) for x in atom))  # type: ignore[arg-type]
    return sorted(combos)


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("ASP/Python mismatch")
        print("Only Python:", sorted(py - lp))
        print("Only ASP:", sorted(lp - py))
        return 1
    for combo in sorted(py):
        generate(StoryParams(*combo, seed=17))
    print(f"OK: Python and ASP agree on {len(py)} valid willow-lamp post-office stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alcove", choices=sorted(ALCOVES))
    parser.add_argument("--mailpiece", choices=sorted(MAILPIECES))
    parser.add_argument("--ritual", choices=sorted(RITUALS))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.alcove is None or combo[0] == args.alcove)
        and (args.mailpiece is None or combo[1] == args.mailpiece)
        and (args.ritual is None or combo[2] == args.ritual)
        and (args.hero is None or combo[3] == args.hero)
    ]
    if not choices:
        alcove = args.alcove or sorted(ALCOVES)[0]
        mailpiece = args.mailpiece or sorted(MAILPIECES)[0]
        ritual = args.ritual or sorted(RITUALS)[0]
        hero = args.hero or sorted(HEROES)[0]
        raise StoryError(explain_rejection(alcove, mailpiece, ritual, hero))
    alcove, mailpiece, ritual, hero = rng.choice(choices)
    seed = (args.seed if args.seed is not None else 1000) + index
    return StoryParams(alcove, mailpiece, ritual, hero, seed)


def format_qa(title: str, items: list[QAItem]) -> list[str]:
    lines = [title]
    for item in items:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return lines


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("\n".join(format_qa("STORY QA", sample.story_qa)))
        print()
        print("\n".join(format_qa("WORLD KNOWLEDGE QA", sample.world_qa)))
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        base_seed = args.seed if args.seed is not None else 700
        return [
            generate(StoryParams(alcove, mailpiece, ritual, hero, base_seed + i))
            for i, (alcove, mailpiece, ritual, hero) in enumerate(valid_combos(), start=1)
        ]

    target = max(1, args.n)
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    i = 0
    while len(samples) < target and attempts < target * 40:
        seed = base_seed + i
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed), index=i)
        sample = generate(params)
        i += 1
        attempts += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Could not generate enough unique fairy-tale post-office stories with those constraints.")
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return 0

    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        print(str(exc))
        return 2

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples, start=1):
        header = ""
        if len(samples) > 1:
            header = (
                "=== willow_dusty_lamp_post_office_surprise_transformation "
                f"#{idx} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
