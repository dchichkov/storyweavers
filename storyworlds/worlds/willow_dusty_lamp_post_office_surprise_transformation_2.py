#!/usr/bin/env python3
"""A fairy-tale storyworld about willow mail and a dusty lamp in a post office.

Seed:
    Words: willow, dusty lamp
    Setting: post office
    Features: Surprise, Transformation
    Style: Fairy Tale

Source tale used for the simulation:
    In a village post office beside a willow tree, a child helper finds one
    stubborn piece of willow mail resting under a dusty lamp. The mail cannot
    travel in its present form, because its true direction is hidden, sleeping,
    or folded tight. The postmaster knows the dusty lamp can change honest mail
    into the shape its journey requires, but only when it is tended with the
    proper little rite. The child performs that careful task, the lamp wakes,
    and the mail surprises everyone by transforming into a living guide, key,
    or ribbon path. By the end, a concrete thank-you image proves that the
    message reached the home that had been waiting for it.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Nook:
    id: str
    label: str
    scene: str
    lamp_detail: str
    affords: set[str]
    tags: set[str]


@dataclass(frozen=True)
class MailPiece:
    id: str
    label: str
    material: str
    problem: str
    hidden_sign: str
    need: str
    transform_kind: str
    transform_sentence: str
    recipient: str
    arrival_method: str
    tags: set[str]


@dataclass(frozen=True)
class LampRite:
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        lines = [
            (
                "params: "
                f"nook={self.params.nook} mailpiece={self.params.mailpiece} "
                f"rite={self.params.rite} hero={self.params.hero}"
            ),
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
    nook: str
    mailpiece: str
    rite: str
    hero: str
    seed: Optional[int] = None


NOOKS = {
    "willow_window": Nook(
        id="willow_window",
        label="the willow window",
        scene="the little sorting desk under the post office window where willow branches brushed the glass",
        lamp_detail="Above the desk hung a dusty lamp whose brass shade was painted with tiny green leaves.",
        affords={"willow_invitation", "willow_telegram"},
        tags={"window", "willow", "sorting", "lamp"},
    ),
    "stamp_cubby": Nook(
        id="stamp_cubby",
        label="the stamp cubby",
        scene="the stamp cubby where ink pads, sealing wax, and old twine slept in tidy drawers",
        lamp_detail="A dusty lamp leaned over the cubby, dim as a dozing cricket in a brass shell.",
        affords={"willow_invitation", "willow_parcel"},
        tags={"stamps", "cubby", "lamp", "drawers"},
    ),
    "parcel_scale": Nook(
        id="parcel_scale",
        label="the parcel scale",
        scene="the brass parcel scale beside the outgoing sacks and the red registry ledger",
        lamp_detail="A dusty lamp swung above the scale, and each slow sway sent a pale shimmer through the dust on its chimney.",
        affords={"willow_parcel", "willow_telegram"},
        tags={"scale", "sacks", "ledger", "lamp"},
    ),
}


MAILPIECES = {
    "willow_invitation": MailPiece(
        id="willow_invitation",
        label="willow invitation",
        material="cream card sewn with a willow-green thread",
        problem="the place-name on it had faded until even the finest clerk could not read where it belonged",
        hidden_sign="When the card was tilted, a pale green glimmer ran under the paper as if a hidden road wanted to wake up",
        need="clear_route",
        transform_kind="route_ribbon",
        transform_sentence="a narrow ribbon of green-gold light slipped out of the folded card and laid itself over the floorboards like a polite little road",
        recipient="orchard_glasshouse",
        arrival_method="The shining ribbon wound out past the willow tree and led the way to the orchard glasshouse without a single wrong turn.",
        tags={"invitation", "route", "willow", "card"},
    ),
    "willow_parcel": MailPiece(
        id="willow_parcel",
        label="willow parcel",
        material="thin willow bark wrapped around a seed box with blue twine",
        problem="its sleepy clasp would not open, so nobody could see the true delivery mark hidden beneath it",
        hidden_sign="The parcel gave one small warm knock against the child's palms, as if something inside remembered spring",
        need="warm_clasp",
        transform_kind="pollen_key",
        transform_sentence="the blue twine loosened itself, and a tiny gold key dusted with sweet pollen rose from the knot on a curl of light",
        recipient="bridge_tailor",
        arrival_method="The gold key skipped ahead to the blue satchel by the willow bridge and opened the little hidden lock sewn under the flap.",
        tags={"parcel", "key", "willow", "seed"},
    ),
    "willow_telegram": MailPiece(
        id="willow_telegram",
        label="willow telegram",
        material="silver paper folded around a pressed willow leaf",
        problem="its message had curled inward and gone still, as if the words were too shy to travel in a straight line",
        hidden_sign="A fine tremble crossed the folded leaf whenever the post office clock sighed the half hour",
        need="singing_path",
        transform_kind="paper_lark",
        transform_sentence="the silver fold lifted, feathered itself with moon-bright edges, and became a paper lark that hopped once before spreading its neat wings",
        recipient="ferry_lantern",
        arrival_method="The paper lark fluttered out through the willow-shadowed yard and flew straight to the ferry lantern by the river steps.",
        tags={"telegram", "bird", "willow", "silver"},
    ),
}


LAMP_RITES = {
    "polish_chimney": LampRite(
        id="polish_chimney",
        label="polish the lamp chimney",
        grants="clear_route",
        action="breathed on the lamp chimney and polished it in slow circles with the softest sorting cloth",
        awakening="The dusty glass cleared from gray to honey, and the lamp opened one steady eye of gold.",
        prompt="polishing the dusty lamp chimney until it shone clear",
        tags={"care", "glass", "light"},
    ),
    "feed_blue_oil": LampRite(
        id="feed_blue_oil",
        label="feed the lamp blue oil",
        grants="warm_clasp",
        action="trimmed the wick and fed it one blue bead of oil from the postmaster's tiny bottle",
        awakening="The lamp flame stood taller at once, and a snug warm glow tucked itself under the brass shade.",
        prompt="trimming the wick and giving the dusty lamp a bead of blue oil",
        tags={"care", "flame", "warmth"},
    ),
    "ring_leaf_chain": LampRite(
        id="ring_leaf_chain",
        label="ring the leaf-shaped chain",
        grants="singing_path",
        action="tugged the leaf-shaped chain until the lamp answered with one silver note",
        awakening="The chime ran through the rafters like a small birdcall, and the dust around the lamp trembled free.",
        prompt="ringing the dusty lamp's leaf-shaped chain for one silver note",
        tags={"care", "sound", "chime"},
    ),
}


RECIPIENTS = {
    "orchard_glasshouse": Recipient(
        id="orchard_glasshouse",
        label="Madam Plum in the orchard glasshouse",
        home="the orchard glasshouse beyond the willow lane",
        accepts={"route_ribbon"},
        reveal="Mistress Wren smiled and said that only Madam Plum in the orchard glasshouse was waiting for a wedding invitation tied with willow thread.",
        delivery=(
            "Madam Plum followed the ribbon to her gate, clapped her hands, and found the invitation lying neatly on a tray of pears as if it had always known the way."
        ),
        proof="a jar of pear jam stood on the post office counter at dawn with the green thread tied around its lid",
        tags={"orchard", "glasshouse", "invitation", "willow"},
    ),
    "bridge_tailor": Recipient(
        id="bridge_tailor",
        label="Master Reed at the willow bridge",
        home="the tailor's blue satchel by the willow bridge",
        accepts={"pollen_key"},
        reveal="Mistress Wren knew the hidden mark belonged to Master Reed, the tailor who kept a blue satchel under the willow bridge for urgent mending.",
        delivery=(
            "The little key opened the satchel's secret clasp, and the parcel slipped inside before the bridge mist could dampen its bark wrapping."
        ),
        proof="a bright brass button waited on the ledger in the morning, tied there with a thread the color of young willow bark",
        tags={"bridge", "tailor", "parcel", "willow"},
    ),
    "ferry_lantern": Recipient(
        id="ferry_lantern",
        label="Old Sella at the ferry lantern",
        home="the ferry lantern beside the river steps",
        accepts={"paper_lark"},
        reveal="Mistress Wren said the shy telegram belonged to Old Sella, who watched the ferry lantern and listened better to birds than to bells.",
        delivery=(
            "Old Sella lifted her lantern, and the paper lark settled on the rail so she could unfold the silver message with both careful hands."
        ),
        proof="a silver feather lay across the stamp book next morning, and the willow outside the window seemed to bow to it",
        tags={"ferry", "lantern", "telegram", "willow"},
    ),
}


HEROES = {
    "elsie": HeroSeed(id="elsie", name="Elsie", gender="girl", trait="gentle"),
    "joel": HeroSeed(id="joel", name="Joel", gender="boy", trait="steady"),
    "mae": HeroSeed(id="mae", name="Mae", gender="girl", trait="bright-eyed"),
    "ned": HeroSeed(id="ned", name="Ned", gender="boy", trait="careful"),
}


NEED_EXPLANATIONS = {
    "clear_route": "clear golden light so its hidden road could be seen",
    "warm_clasp": "a warm, patient glow so its clasp would loosen without being forced",
    "singing_path": "a bright singing note so its folded message would dare to travel",
}


RITE_PHRASES = {
    "polish_chimney": "Polishing the lamp chimney",
    "feed_blue_oil": "Feeding the lamp blue oil",
    "ring_leaf_chain": "Ringing the leaf-shaped chain",
}


TRANSFORM_LABELS = {
    "route_ribbon": "glowing route ribbon",
    "pollen_key": "pollen-bright key",
    "paper_lark": "paper lark telegram",
}


def possessive(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def sentence_case(phrase: str) -> str:
    return phrase[:1].upper() + phrase[1:] if phrase else phrase


def valid_combo(nook_id: str, mail_id: str, rite_id: str, hero_id: str) -> bool:
    if nook_id not in NOOKS or mail_id not in MAILPIECES or rite_id not in LAMP_RITES or hero_id not in HEROES:
        return False
    nook = NOOKS[nook_id]
    mail = MAILPIECES[mail_id]
    rite = LAMP_RITES[rite_id]
    recipient = RECIPIENTS[mail.recipient]
    return mail.id in nook.affords and rite.grants == mail.need and mail.transform_kind in recipient.accepts


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for nook_id in sorted(NOOKS):
        for mail_id in sorted(MAILPIECES):
            for rite_id in sorted(LAMP_RITES):
                for hero_id in sorted(HEROES):
                    if valid_combo(nook_id, mail_id, rite_id, hero_id):
                        combos.append((nook_id, mail_id, rite_id, hero_id))
    return combos


def explain_rejection(nook_id: str, mail_id: str, rite_id: str, hero_id: str) -> str:
    if nook_id not in NOOKS:
        return f"Unknown post-office nook {nook_id!r}."
    if mail_id not in MAILPIECES:
        return f"Unknown willow mailpiece {mail_id!r}."
    if rite_id not in LAMP_RITES:
        return f"Unknown lamp rite {rite_id!r}."
    if hero_id not in HEROES:
        return f"Unknown hero {hero_id!r}."
    nook = NOOKS[nook_id]
    mail = MAILPIECES[mail_id]
    rite = LAMP_RITES[rite_id]
    recipient = RECIPIENTS[mail.recipient]
    if mail.id not in nook.affords:
        return f"{nook.label} does not plausibly hold the {mail.label}."
    if rite.grants != mail.need:
        return f"{rite.label} cannot solve this trouble; the {mail.label} needs {mail.need}."
    if mail.transform_kind not in recipient.accepts:
        return f"{recipient.label} would not plausibly receive a {mail.transform_kind} ending."
    return "That fairy-tale post office story falls outside the valid world."


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.nook, params.mailpiece, params.rite, params.hero):
        raise StoryError(explain_rejection(params.nook, params.mailpiece, params.rite, params.hero))

    world = World(params)
    hero_seed = HEROES[params.hero]
    nook = NOOKS[params.nook]
    mail = MAILPIECES[params.mailpiece]
    recipient = RECIPIENTS[mail.recipient]

    hero = world.add(Entity(id="hero", kind="child", label=hero_seed.name, location="post_office"))
    hero.meters["steadiness"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 1.0
    hero.note = hero_seed.trait

    postmaster = world.add(Entity(id="postmaster", kind="postmaster", label="Mistress Wren", location="post_office"))
    postmaster.memes["wisdom"] = 1.0
    postmaster.memes["patience"] = 1.0
    postmaster.note = "keeper of the closing bell"

    lamp = world.add(Entity(id="lamp", kind="object", label="dusty lamp", location=nook.id))
    lamp.meters["dust"] = 1.0
    lamp.meters["glow"] = 0.0
    lamp.meters["warmth"] = 0.0
    lamp.memes["memory"] = 1.0
    lamp.states.add("sleeping")

    willow = world.add(Entity(id="willow", kind="tree", label="willow tree", location="outside_window"))
    willow.meters["sway"] = 0.5
    willow.memes["watchfulness"] = 1.0
    willow.states.add("waiting")

    mail_ent = world.add(Entity(id="mail", kind="mail", label=mail.label, location=nook.id))
    mail_ent.meters["hidden"] = 1.0
    mail_ent.meters["transformed"] = 0.0
    mail_ent.meters["delivered"] = 0.0
    mail_ent.memes["homesick"] = 1.0
    mail_ent.note = mail.material
    mail_ent.states.add("stuck")

    home = world.add(Entity(id="recipient", kind="destination", label=recipient.label, location=recipient.home))
    home.meters["ready"] = 1.0
    home.states.add("waiting")

    world.facts["nook"] = nook.id
    world.facts["mailpiece"] = mail.id
    world.facts["rite"] = params.rite
    world.facts["recipient"] = recipient.id
    return world


def introduce(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    nook = NOOKS[params.nook]
    mail = MAILPIECES[params.mailpiece]

    world.say(
        f"One blue evening, {hero_seed.name}, a {hero_seed.trait} child, was helping close {nook.scene} in the village post office."
    )
    world.say(nook.lamp_detail)
    world.say(
        f"Outside, the old willow tree whispered against the pane, while beneath the lamp lay a {mail.label} made of {mail.material}."
    )
    world.say(
        f"It was the very last errand before the bell, yet {mail.problem}. {mail.hidden_sign}."
    )
    world.record("scene_introduced")


def tension(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    hero = world.get("hero")

    world.break_para()
    world.say(
        f"{hero_seed.name} turned the {mail.label} over in {possessive(hero_seed.gender)} hands and felt a small fretful tug of pity for it."
    )
    world.say(
        '"Do not force it," said Mistress Wren. "Honest mail only listens when the dusty lamp is wakened in the right little way."'
    )
    world.say(
        f"That meant the post office could not sleep yet, because somewhere beyond the willow lane a waiting heart still had no message."
    )
    hero.meters["resolve"] = 1.0
    hero.memes["hope"] = 0.5
    world.record("problem_seen")


def awaken(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    rite = LAMP_RITES[params.rite]
    lamp = world.get("lamp")
    hero = world.get("hero")

    world.break_para()
    world.say(f"So {hero_seed.name} {rite.action}.")
    world.say(rite.awakening)
    world.say(
        f"The post office seemed to hold its breath, and even the willow branches paused at the window to watch."
    )
    lamp.meters["dust"] = 0.0
    lamp.meters["glow"] = 1.0
    lamp.meters["warmth"] = 1.0
    lamp.states.discard("sleeping")
    lamp.states.add("awake")
    lamp.label = "bright lamp"
    hero.memes["courage"] += 1.0
    world.record("lamp_awakened")


def transform(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    recipient = RECIPIENTS[mail.recipient]
    hero = world.get("hero")
    mail_ent = world.get("mail")
    willow = world.get("willow")

    world.say(
        f"Then the {mail.label} answered the light: {mail.transform_sentence}."
    )
    world.say(
        f"The surprise was so lovely that {hero_seed.name} laughed aloud, and Mistress Wren's face softened like a folded note opening."
    )
    world.say(recipient.reveal)
    mail_ent.meters["hidden"] = 0.0
    mail_ent.meters["transformed"] = 1.0
    mail_ent.label = TRANSFORM_LABELS[mail.transform_kind]
    mail_ent.states.discard("stuck")
    mail_ent.states.add(mail.transform_kind)
    hero.memes["wonder"] += 1.2
    hero.memes["worry"] = 0.0
    willow.meters["sway"] = 1.0
    willow.states.add("approving")
    world.facts["transformation"] = mail.transform_kind
    world.record("mail_transformed")


def deliver(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    recipient = RECIPIENTS[mail.recipient]
    hero = world.get("hero")
    mail_ent = world.get("mail")
    home = world.get("recipient")

    world.break_para()
    world.say(mail.arrival_method)
    world.say(recipient.delivery)
    world.say(
        f"When {hero_seed.name} came back, the post office no longer felt sleepy at all. The bright lamp kept a faithful glow above the counter, and {recipient.proof}."
    )
    hero.memes["relief"] += 1.0
    hero.memes["wonder"] += 0.4
    mail_ent.meters["delivered"] = 1.0
    mail_ent.location = recipient.home
    home.states.discard("waiting")
    home.states.add("reached")
    world.record("mail_delivered")


def tell(world: World) -> str:
    introduce(world)
    tension(world)
    awaken(world)
    transform(world)
    deliver(world)
    return world.render()


def generation_prompts(params: StoryParams) -> list[str]:
    hero = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    rite = LAMP_RITES[params.rite]
    recipient = RECIPIENTS[mail.recipient]
    return [
        "Write a fairy tale set in a post office that includes a willow and a dusty lamp.",
        f"Write a surprise transformation story where {hero.name} helps a {mail.label} reach {recipient.label}.",
        f"Write a gentle fairy tale where {rite.prompt} changes a lost message into the right shape for its journey.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.params
    hero = HEROES[params.hero]
    mail = MAILPIECES[params.mailpiece]
    rite = LAMP_RITES[params.rite]
    recipient = RECIPIENTS[mail.recipient]
    return [
        QAItem(
            question=f"Why could {hero.name} not send the {mail.label} right away?",
            answer=(
                f"{hero.name} could not send it right away because {mail.problem}. The dusty lamp had to wake the mail's true direction before anyone could finish the delivery."
            ),
        ),
        QAItem(
            question="How was the dusty lamp awakened?",
            answer=(
                f"The dusty lamp awakened when {hero.name} {rite.action}. That careful rite gave the lamp exactly the kind of help it needed."
            ),
        ),
        QAItem(
            question=f"What was the surprise transformation in the story?",
            answer=(
                f"The surprise transformation happened when {mail.transform_sentence}. That new form finally showed the path to {recipient.label}."
            ),
        ),
        QAItem(
            question="How did the ending prove the problem was solved?",
            answer=(
                f"The ending proved it because {recipient.proof}. The thank-you object on the counter showed that the message had reached its waiting home."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    params = world.params
    mail = MAILPIECES[params.mailpiece]
    rite = LAMP_RITES[params.rite]
    recipient = RECIPIENTS[mail.recipient]
    nook = NOOKS[params.nook]
    return [
        QAItem(
            question="What does a post office do in a story like this?",
            answer=(
                "A post office gathers letters and parcels, sorts them carefully, and sends them toward the homes that are waiting for them. In a fairy tale, it can also become a place where lost messages are gently understood."
            ),
        ),
        QAItem(
            question="Why is a dusty lamp important here?",
            answer=(
                "The dusty lamp gives more than ordinary light, because it helps hidden marks, shy words, and sleepy routes show themselves. Its light matters because the mail cannot become truthful until the lamp wakes."
            ),
        ),
        QAItem(
            question="Why was that lamp rite the correct one?",
            answer=(
                f"It was correct because the {mail.label} needed {NEED_EXPLANATIONS[mail.need]}. {RITE_PHRASES[rite.id]} matched the trouble in a gentle way instead of forcing the answer."
            ),
        ),
        QAItem(
            question=f"What kind of place is {recipient.home}?",
            answer=(
                f"It is the home that truly belongs to this story's message, not just another stop on the road. The ending feels complete because the transformed mail reaches a place that fits its secret exactly."
            ),
        ),
        QAItem(
            question=f"Why does {nook.label} matter in the beginning?",
            answer=(
                f"{sentence_case(nook.label)} shapes the mood of the story by placing the mail beside the lamp and the evening work of the post office. It gives the child a small, concrete place where the trouble can first be noticed."
            ),
        ),
    ]


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
valid(N,M,R,H) :-
    nook(N),
    mailpiece(M),
    rite(R),
    hero(H),
    affords(N,M),
    need(M,Need),
    grants(R,Need),
    recipient_for(M,Rec),
    transform(M,T),
    accepts(Rec,T).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for nook in NOOKS.values():
        rows.append(asp.fact("nook", nook.id))
        for mail_id in nook.affords:
            rows.append(asp.fact("affords", nook.id, mail_id))
    for mail in MAILPIECES.values():
        rows.append(asp.fact("mailpiece", mail.id))
        rows.append(asp.fact("need", mail.id, mail.need))
        rows.append(asp.fact("transform", mail.id, mail.transform_kind))
        rows.append(asp.fact("recipient_for", mail.id, mail.recipient))
    for rite in LAMP_RITES.values():
        rows.append(asp.fact("rite", rite.id))
        rows.append(asp.fact("grants", rite.id, rite.grants))
    for recipient in RECIPIENTS.values():
        rows.append(asp.fact("recipient", recipient.id))
        for transform in recipient.accepts:
            rows.append(asp.fact("accepts", recipient.id, transform))
    for hero in HEROES.values():
        rows.append(asp.fact("hero", hero.id))
    return "\n".join(rows) + "\n"


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    models = asp.solve(asp_program("#show valid/4."))
    combos: set[tuple[str, str, str, str]] = set()
    for model in models:
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(value) for value in atom))  # type: ignore[arg-type]
    return sorted(combos)


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("ASP/Python mismatch")
        print("Only Python:", sorted(python_set - asp_set))
        print("Only ASP:", sorted(asp_set - python_set))
        return 1
    for combo in sorted(python_set):
        generate(StoryParams(*combo, seed=17))
    print(f"OK: Python and ASP agree on {len(python_set)} valid willow-lamp post-office stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nook", choices=sorted(NOOKS))
    parser.add_argument("--mailpiece", choices=sorted(MAILPIECES))
    parser.add_argument("--rite", choices=sorted(LAMP_RITES))
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


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.nook is None or combo[0] == args.nook)
        and (args.mailpiece is None or combo[1] == args.mailpiece)
        and (args.rite is None or combo[2] == args.rite)
        and (args.hero is None or combo[3] == args.hero)
    ]
    if not choices:
        nook = args.nook or sorted(NOOKS)[0]
        mailpiece = args.mailpiece or sorted(MAILPIECES)[0]
        rite = args.rite or sorted(LAMP_RITES)[0]
        hero = args.hero or sorted(HEROES)[0]
        raise StoryError(explain_rejection(nook, mailpiece, rite, hero))
    nook, mailpiece, rite, hero = rng.choice(sorted(choices))
    seed = (args.seed if args.seed is not None else 1000) + index
    return StoryParams(nook=nook, mailpiece=mailpiece, rite=rite, hero=hero, seed=seed)


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
            generate(StoryParams(*combo, seed=base_seed + idx))
            for idx, combo in enumerate(valid_combos(), start=1)
        ]

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < args.n * 50:
        params = resolve_params(args, random.Random(base_seed + i), index=i)
        sample = generate(params)
        i += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < args.n:
        raise StoryError("Could not generate enough unique stories with this constraint set.")
    return samples


def main() -> int:
    args = build_parser().parse_args()

    try:
        if args.show_asp:
            print(asp_program("#show valid/4."))
            return 0
        if args.verify:
            return asp_verify()
        if args.asp:
            for combo in asp_valid_combos():
                print("\t".join(combo))
            return 0

        samples = samples_from_args(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = f"### nook={p.nook} mailpiece={p.mailpiece} rite={p.rite} hero={p.hero}"
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
