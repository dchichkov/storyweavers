#!/usr/bin/env python3
"""A fairy-tale storyworld about willow mail and a dusty lamp in a post office.

Seed:
    Words: willow, dusty lamp
    Setting: post office
    Features: Surprise, Transformation
    Style: Fairy Tale

Source tale used for the simulation:
    In a village post office shaded by a willow tree, a child helper discovers
    one last piece of troubled mail waiting under a dusty lamp after closing
    time. The message cannot travel as it is, because its truest way of
    reaching home is still sleeping inside it. The child tends the lamp in the
    right gentle way, the lamp wakes, and the mail surprises the room by
    transforming into the exact living or shining shape its journey needs. By
    morning, a small thank-you proof on the counter shows that the waiting home
    truly received it.
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
    affords: frozenset[str]
    tags: frozenset[str]


@dataclass(frozen=True)
class MailPiece:
    id: str
    label: str
    material: str
    problem: str
    omen: str
    need: str
    transform_kind: str
    transform_sentence: str
    recipient: str
    journey_sentence: str
    ending_image: str
    tags: frozenset[str]


@dataclass(frozen=True)
class LampRite:
    id: str
    label: str
    grants: str
    action: str
    awakening: str
    prompt: str
    tags: frozenset[str]


@dataclass(frozen=True)
class Recipient:
    id: str
    label: str
    home: str
    accepts: frozenset[str]
    reveal: str
    arrival: str
    proof: str
    tags: frozenset[str]


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
    "willow_sorting_window": Nook(
        id="willow_sorting_window",
        label="the willow sorting window",
        scene="the narrow sorting shelf under the post office window where the willow leaves tapped the glass like polite green fingers",
        lamp_detail="A dusty lamp hung above the shelf, and every grain on its brass shade shone faintly as if moonlight had once slept there.",
        affords=frozenset({"willow_seed_notice", "willow_music_roll"}),
        tags=frozenset({"window", "sorting", "willow", "lamp"}),
    ),
    "registry_counter": Nook(
        id="registry_counter",
        label="the registry counter",
        scene="the old registry counter beside the red ledger and the string spool for special deliveries",
        lamp_detail="A dusty lamp stood on the counter with a pearly chimney, dim but watchful above the evening stamps.",
        affords=frozenset({"willow_seed_notice", "willow_button_parcel"}),
        tags=frozenset({"counter", "ledger", "special_delivery", "lamp"}),
    ),
    "parcel_bench": Nook(
        id="parcel_bench",
        label="the parcel bench",
        scene="the parcel bench near the outgoing sacks where brown paper and twine made tidy little hills",
        lamp_detail="A dusty lamp swung over the bench, and each slow sway sent a warm shimmer through the dust on its glass.",
        affords=frozenset({"willow_button_parcel", "willow_music_roll"}),
        tags=frozenset({"bench", "parcels", "twine", "lamp"}),
    ),
}


MAILPIECES = {
    "willow_seed_notice": MailPiece(
        id="willow_seed_notice",
        label="willow seed notice",
        material="pale paper tucked around a tiny seed with a green address seal",
        problem="the address seal had gone cloudy, so no one could tell which garden gate had been waiting for it",
        omen="When the paper was lifted, the seed inside gave one soft tap, as if spring itself were knocking from a very small room",
        need="clear_name",
        transform_kind="leaf_swallow",
        transform_sentence="the green seal blinked awake, unfolded into bright feathered leaves, and became a tiny swallow made of paper and spring light",
        recipient="glass_gardener",
        journey_sentence="The leaf swallow darted through the willow-shadowed yard and flew straight toward the glass gardener's gate without circling once.",
        ending_image="a pinch of fresh potting soil and one white blossom rested on the counter by dawn",
        tags=frozenset({"seed", "garden", "willow", "paper"}),
    ),
    "willow_button_parcel": MailPiece(
        id="willow_button_parcel",
        label="willow button parcel",
        material="soft bark paper tied with blue thread around a moon-bright brass button",
        problem="the thread had tightened in the cold, and the hidden delivery mark beneath it could not be read without tearing the wrapper",
        omen="The button inside gave a shy chiming click whenever the dusty lamp trembled on its hook",
        need="kind_warmth",
        transform_kind="golden_key_mouse",
        transform_sentence="the blue thread loosened in a single sigh, and the brass button shook itself into a tiny golden mouse carrying a key on its back",
        recipient="bridge_tailor",
        journey_sentence="The key-mouse scampered along the willow root path to the tailor's bridge satchel, balancing its bright burden as neatly as a prince with a crown.",
        ending_image="a velvet cuff with the missing button sewn back on was waiting beside the stamp pad in the morning",
        tags=frozenset({"parcel", "button", "tailor", "willow"}),
    ),
    "willow_music_roll": MailPiece(
        id="willow_music_roll",
        label="willow music roll",
        material="silver paper rolled around a thin reed whistle and tied with a willow-green ribbon",
        problem="its tune had curled inward and gone shy, so the right tower room could not hear itself being called",
        omen="Each time the clock above the boxes sighed, the reed whistle answered with a breath no louder than a sleeping cricket",
        need="brave_song",
        transform_kind="ribbon_boat",
        transform_sentence="the ribbon leapt free, stretched into a silver-blue boat no bigger than two hands, and the reed whistle stood in it like a singing mast",
        recipient="clockmaker_niece",
        journey_sentence="The ribbon boat sailed down a rain-filled gutter, turned at the willow drain, and glided to the clockmaker's stair with its thin brave tune shining ahead of it.",
        ending_image="a neatly wound silver music string hung from the lamp chain by sunrise",
        tags=frozenset({"music", "reed", "silver", "willow"}),
    ),
}


LAMP_RITES = {
    "wipe_glass_with_willow_cloth": LampRite(
        id="wipe_glass_with_willow_cloth",
        label="wipe the glass with willow cloth",
        grants="clear_name",
        action="breathed on the chimney and wiped it in patient circles with the willow-patterned polishing cloth kept under the stamps",
        awakening="The gray blur cleared to honey-gold, and the lamp opened a calm eye that could see through every muddle.",
        prompt="wiping the dusty lamp glass with a willow cloth until it shone clear",
        tags=frozenset({"glass", "clarity", "care"}),
    ),
    "warm_the_wick_with_blue_oil": LampRite(
        id="warm_the_wick_with_blue_oil",
        label="warm the wick with blue oil",
        grants="kind_warmth",
        action="trimmed the wick and gave it one blue drop of oil from the postmistress's little bottle",
        awakening="The flame lifted at once and tucked a pocket of kind warmth under the brass shade.",
        prompt="warming the dusty lamp wick with one blue drop of oil",
        tags=frozenset({"wick", "warmth", "care"}),
    ),
    "ring_the_brass_pull": LampRite(
        id="ring_the_brass_pull",
        label="ring the brass pull",
        grants="brave_song",
        action="drew the brass pull until the lamp answered with one silver note that quivered through the rafters",
        awakening="Dust slipped from the shade like old sleep, and the lamp began to hum with a brave little music of its own.",
        prompt="ringing the dusty lamp's brass pull to wake a brave note",
        tags=frozenset({"sound", "song", "care"}),
    ),
}


RECIPIENTS = {
    "glass_gardener": Recipient(
        id="glass_gardener",
        label="Madam Fern of the glass garden",
        home="the glass garden beyond the willow gate",
        accepts=frozenset({"leaf_swallow"}),
        reveal="Postmistress Iven said that only Madam Fern of the glass garden had been waiting for a seed notice sealed in green.",
        arrival="Madam Fern opened her gate just as the leaf swallow reached her, and she caught the little bird on both hands before setting the seed in a warm tray of soil.",
        proof="a pinch of fresh potting soil and one white blossom rested on the counter by dawn",
        tags=frozenset({"garden", "seed", "glasshouse"}),
    ),
    "bridge_tailor": Recipient(
        id="bridge_tailor",
        label="Master Rowan at the willow bridge",
        home="the tailor's satchel under the willow bridge",
        accepts=frozenset({"golden_key_mouse"}),
        reveal="Postmistress Iven knew the hidden mark belonged to Master Rowan, the tailor who kept a bridge satchel ready for urgent mending.",
        arrival="Master Rowan laughed softly when the key-mouse bowed at his satchel clasp, and he slipped the mended cuff inside before the bridge fog touched the cloth.",
        proof="a velvet cuff with the missing button sewn back on was waiting beside the stamp pad in the morning",
        tags=frozenset({"tailor", "bridge", "button"}),
    ),
    "clockmaker_niece": Recipient(
        id="clockmaker_niece",
        label="Lina in the clockmaker's tower",
        home="the clockmaker's tower room above the square",
        accepts=frozenset({"ribbon_boat"}),
        reveal="Postmistress Iven remembered that Lina in the clockmaker's tower was waiting for the tune that told her when to wind the moon clock.",
        arrival="Lina leaned from the tower stair just as the ribbon boat sang below, and she lifted the reed whistle free before the silver hull melted into rain.",
        proof="a neatly wound silver music string hung from the lamp chain by sunrise",
        tags=frozenset({"clock", "tower", "music"}),
    ),
}


HEROES = {
    "ada": HeroSeed(id="ada", name="Ada", gender="girl", trait="soft-footed"),
    "ben": HeroSeed(id="ben", name="Ben", gender="boy", trait="steady"),
    "clara": HeroSeed(id="clara", name="Clara", gender="girl", trait="bright-eyed"),
    "tomas": HeroSeed(id="tomas", name="Tomas", gender="boy", trait="careful"),
}


NEED_EXPLANATIONS = {
    "clear_name": "clear golden sight so the true name could appear",
    "kind_warmth": "gentle warmth so the wrapper would open without being hurt",
    "brave_song": "a brave singing note so the shy tune would dare to travel",
}


RITE_TITLES = {
    "wipe_glass_with_willow_cloth": "Wiping the lamp glass",
    "warm_the_wick_with_blue_oil": "Warming the lamp wick",
    "ring_the_brass_pull": "Ringing the brass pull",
}


TRANSFORM_LABELS = {
    "leaf_swallow": "leaf swallow message",
    "golden_key_mouse": "golden key-mouse parcel",
    "ribbon_boat": "ribbon boat message",
}


def possessive(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


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
    rite = LAMP_RITES[params.rite]
    recipient = RECIPIENTS[mail.recipient]

    hero = world.add(Entity(id="hero", kind="child", label=hero_seed.name, location="post_office"))
    hero.meters["resolve"] = 0.3
    hero.meters["wonder"] = 0.2
    hero.memes["kindness"] = 1.0
    hero.memes["concern"] = 1.0
    hero.note = hero_seed.trait

    postmistress = world.add(Entity(id="postmistress", kind="postmistress", label="Postmistress Iven", location="post_office"))
    postmistress.memes["wisdom"] = 1.0
    postmistress.memes["patience"] = 1.0
    postmistress.note = "keeper of the willow keys"

    lamp = world.add(Entity(id="lamp", kind="object", label="dusty lamp", location=nook.id))
    lamp.meters["dust"] = 1.0
    lamp.meters["glow"] = 0.0
    lamp.meters["warmth"] = 0.0
    lamp.memes["memory"] = 1.0
    lamp.states.add("sleeping")

    willow = world.add(Entity(id="willow", kind="tree", label="willow", location="outside_window"))
    willow.meters["sway"] = 0.4
    willow.memes["watchfulness"] = 1.0
    willow.states.add("waiting")

    mail_ent = world.add(Entity(id="mail", kind="mail", label=mail.label, location=nook.id))
    mail_ent.meters["hidden"] = 1.0
    mail_ent.meters["delivered"] = 0.0
    mail_ent.meters["changed"] = 0.0
    mail_ent.memes["homesick"] = 1.0
    mail_ent.states.add("stuck")
    mail_ent.note = mail.material

    recipient_ent = world.add(Entity(id="recipient", kind="destination", label=recipient.label, location=recipient.home))
    recipient_ent.meters["waiting"] = 1.0
    recipient_ent.states.add("waiting")

    world.facts["nook"] = nook.id
    world.facts["mailpiece"] = mail.id
    world.facts["rite"] = rite.id
    world.facts["recipient"] = recipient.id
    return world


def introduce(world: World) -> None:
    hero = HEROES[world.params.hero]
    nook = NOOKS[world.params.nook]
    mail = MAILPIECES[world.params.mailpiece]

    world.say(
        f"At the close of a pearl-blue evening, {hero.name}, a {hero.trait} child, was helping finish the last chores at {nook.scene}."
    )
    world.say(nook.lamp_detail)
    world.say(
        f"Outside, the willow brushed the pane, and under the lamp lay a {mail.label} made of {mail.material}."
    )
    world.say(
        f"It should have been the easiest errand of the night, but {mail.problem}. {mail.omen}."
    )
    world.record("premise_introduced")


def raise_tension(world: World) -> None:
    hero = HEROES[world.params.hero]
    mail = MAILPIECES[world.params.mailpiece]
    hero_ent = world.get("hero")

    world.break_para()
    world.say(
        f"{hero.name} turned the {mail.label} over in {possessive(hero.gender)} hands and felt sorry for the message trapped inside it."
    )
    world.say(
        '"Do not pry or tear," said Postmistress Iven. "The dusty lamp only helps the honest and the patient, and it must be asked in the proper way."'
    )
    world.say(
        "That made the room feel suddenly important, because somewhere past the willow gate someone was still waiting for the thing this post office had promised to bring."
    )
    hero_ent.meters["resolve"] = 0.7
    hero_ent.memes["hope"] = 0.5
    world.record("trouble_understood")


def wake_lamp(world: World) -> None:
    hero = HEROES[world.params.hero]
    rite = LAMP_RITES[world.params.rite]
    hero_ent = world.get("hero")
    lamp = world.get("lamp")

    world.break_para()
    world.say(f"So {hero.name} {rite.action}.")
    world.say(rite.awakening)
    world.say("Even the willow stilled its whispering, as if the tree itself wanted to hear what would happen next.")
    hero_ent.meters["wonder"] = 0.8
    hero_ent.memes["courage"] = 1.0
    lamp.meters["dust"] = 0.0
    lamp.meters["glow"] = 1.0
    lamp.meters["warmth"] = 1.0
    lamp.states.discard("sleeping")
    lamp.states.add("awake")
    lamp.label = "awakened lamp"
    world.record("lamp_awakened")


def transform_mail(world: World) -> None:
    hero = HEROES[world.params.hero]
    mail = MAILPIECES[world.params.mailpiece]
    recipient = RECIPIENTS[mail.recipient]
    hero_ent = world.get("hero")
    mail_ent = world.get("mail")
    willow = world.get("willow")

    world.say(f"Then the {mail.label} answered the light: {mail.transform_sentence}.")
    world.say(
        f"The surprise made {hero.name} laugh aloud, and even Postmistress Iven looked as pleased as if the moon had posted her a secret of its own."
    )
    world.say(recipient.reveal)
    hero_ent.meters["wonder"] = 1.0
    hero_ent.memes["concern"] = 0.1
    hero_ent.memes["delight"] = 1.0
    mail_ent.meters["hidden"] = 0.0
    mail_ent.meters["changed"] = 1.0
    mail_ent.label = TRANSFORM_LABELS[mail.transform_kind]
    mail_ent.states.discard("stuck")
    mail_ent.states.add(mail.transform_kind)
    willow.meters["sway"] = 1.0
    willow.states.add("approving")
    world.facts["transformation"] = mail.transform_kind
    world.record("transformation_happened")


def complete_delivery(world: World) -> None:
    hero = HEROES[world.params.hero]
    mail = MAILPIECES[world.params.mailpiece]
    recipient = RECIPIENTS[mail.recipient]
    hero_ent = world.get("hero")
    mail_ent = world.get("mail")
    recipient_ent = world.get("recipient")

    world.break_para()
    world.say(mail.journey_sentence)
    world.say(recipient.arrival)
    world.say(
        f"When {hero.name} came back to the counter, the post office no longer felt sleepy at all. The lamp burned clear and faithful above the room, and {recipient.proof}."
    )
    hero_ent.meters["resolve"] = 1.0
    hero_ent.meters["wonder"] = 1.0
    hero_ent.memes["relief"] = 1.0
    mail_ent.meters["delivered"] = 1.0
    mail_ent.location = recipient.home
    recipient_ent.meters["waiting"] = 0.0
    recipient_ent.states.discard("waiting")
    recipient_ent.states.add("reached")
    world.record("delivery_completed")


def tell(world: World) -> str:
    introduce(world)
    raise_tension(world)
    wake_lamp(world)
    transform_mail(world)
    complete_delivery(world)
    return world.render()


def generation_prompts(params: StoryParams) -> list[str]:
    hero = HEROES[params.hero]
    nook = NOOKS[params.nook]
    mail = MAILPIECES[params.mailpiece]
    rite = LAMP_RITES[params.rite]
    recipient = RECIPIENTS[mail.recipient]
    return [
        "Write a fairy tale set in a post office that includes a willow and a dusty lamp.",
        f"Write a surprise transformation story in which {hero.name} discovers a troubled {mail.label} at {nook.label}.",
        f"Write a gentle fairy tale where {rite.prompt} lets the message reach {recipient.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = HEROES[world.params.hero]
    mail = MAILPIECES[world.params.mailpiece]
    rite = LAMP_RITES[world.params.rite]
    recipient = RECIPIENTS[mail.recipient]
    return [
        QAItem(
            question=f"Why could {hero.name} not send the {mail.label} at once?",
            answer=(
                f"{hero.name} could not send it at once because {mail.problem}. The message needed the dusty lamp to wake the hidden way it was meant to travel."
            ),
        ),
        QAItem(
            question="How did the child wake the dusty lamp?",
            answer=(
                f"The lamp woke when {hero.name} {rite.action}. That careful rite gave the lamp exactly the kind of help this trapped message needed."
            ),
        ),
        QAItem(
            question="What was the surprise transformation?",
            answer=(
                f"The surprise transformation happened when {mail.transform_sentence}. Its new shape matched the road to {recipient.label}, so the delivery could finally continue."
            ),
        ),
        QAItem(
            question="How does the ending prove that the problem was solved?",
            answer=(
                f"The ending proves it because {recipient.proof}. That thank-you sign could only appear after the transformed mail reached the waiting home."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    nook = NOOKS[world.params.nook]
    mail = MAILPIECES[world.params.mailpiece]
    rite = LAMP_RITES[world.params.rite]
    recipient = RECIPIENTS[mail.recipient]
    return [
        QAItem(
            question="What does a post office do in a fairy tale like this?",
            answer=(
                "A post office gathers letters and parcels, keeps them safe, and helps them find the homes that are waiting for them. In a fairy tale, it can also become the place where a stubborn message learns the right shape for its journey."
            ),
        ),
        QAItem(
            question="Why is the dusty lamp important in this world?",
            answer=(
                "The dusty lamp gives more than plain light, because it reveals what honest mail is trying to become. Without its help, the hidden route stays asleep and the story cannot turn."
            ),
        ),
        QAItem(
            question="Why was that rite the correct one?",
            answer=(
                f"It was the correct rite because the {mail.label} needed {NEED_EXPLANATIONS[mail.need]}. {RITE_TITLES[rite.id]} matched the trouble gently instead of forcing the message before it was ready."
            ),
        ),
        QAItem(
            question=f"Why does {nook.label} matter at the beginning?",
            answer=(
                f"{sentence_case(nook.label)} gives the child a small, concrete place to notice the trouble under the lamp. Its setting beside the willow and the evening work of the post office makes the later change feel earned."
            ),
        ),
        QAItem(
            question=f"What kind of place is {recipient.home}?",
            answer=(
                f"It is the true home this transformed message has been trying to reach all along. The ending feels complete because the journey finishes in a place that fits the message exactly."
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
        for transform_kind in recipient.accepts:
            rows.append(asp.fact("accepts", recipient.id, transform_kind))
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
    attempts = 0
    while len(samples) < args.n and attempts < args.n * 50:
        params = resolve_params(args, random.Random(base_seed + attempts), index=attempts)
        sample = generate(params)
        attempts += 1
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
                params = sample.params
                header = (
                    "### "
                    f"nook={params.nook} mailpiece={params.mailpiece} "
                    f"rite={params.rite} hero={params.hero}"
                )
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
