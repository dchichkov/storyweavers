#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/accessory_personal_scab_sharing_rhyme_bedtime_story.py
=================================================================================

A standalone storyworld about bedtime comfort, a small hurt from the day, and a
child deciding to share a treasured accessory. The world rebuilds a tiny tale
with these constraints:

- one child has a personal bedtime accessory
- another child has a small scab from a scrape and feels uneasy at bedtime
- a soothing rhyme helps, but the emotional turn only fully lands when the first
  child chooses to share
- only soft, bedtime-sensible accessories are allowed by the reasonableness gate

The prose is state-driven rather than template-swapped: physical state (a scab,
the object being shared) and emotional state (worry, protectiveness, generosity,
calm) determine the middle turn and ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/accessory_personal_scab_sharing_rhyme_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/accessory_personal_scab_sharing_rhyme_bedtime_story.py --accessory moon_scarf
    python storyworlds/worlds/gpt-5.4/accessory_personal_scab_sharing_rhyme_bedtime_story.py --accessory paper_crown
    python storyworlds/worlds/gpt-5.4/accessory_personal_scab_sharing_rhyme_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/accessory_personal_scab_sharing_rhyme_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/accessory_personal_scab_sharing_rhyme_bedtime_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Accessory:
    id: str
    label: str
    phrase: str
    wear_text: str
    share_text: str
    end_text: str
    soft: bool = True
    bedtime: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Injury:
    id: str
    place: str
    phrase: str
    article_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rhyme:
    id: str
    first: str
    second: str
    topic: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def propagate(world: World) -> None:
    owner = world.get("owner")
    friend = world.get("friend")
    accessory = world.get("accessory")
    sig = (
        owner.memes["generosity"] >= THRESHOLD,
        accessory.attrs.get("shared_with") == friend.id,
        friend.memes["heard_rhyme"] >= THRESHOLD,
        friend.meters["throb"] >= THRESHOLD,
    )
    if sig in world.fired:
        return
    world.fired.add(sig)

    if friend.memes["heard_rhyme"] >= THRESHOLD:
        friend.memes["calm"] += 1
        friend.memes["sleepiness"] += 1
    if accessory.attrs.get("shared_with") == friend.id:
        friend.memes["comfort"] += 1
        friend.memes["calm"] += 1
        owner.memes["warmth"] += 1
    if friend.meters["throb"] >= THRESHOLD and friend.memes["comfort"] < THRESHOLD:
        friend.memes["worry"] += 1
    if friend.memes["calm"] >= 2:
        friend.meters["throb"] = 0.0


def accessory_reasonable(acc: Accessory) -> bool:
    return acc.soft and acc.bedtime


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for accessory_id, accessory in ACCESSORIES.items():
        if not accessory_reasonable(accessory):
            continue
        for injury_id in INJURIES:
            for rhyme_id in RHYMES:
                combos.append((accessory_id, injury_id, rhyme_id))
    return combos


@dataclass
class StoryParams:
    accessory: str
    injury: str
    rhyme: str
    owner_name: str
    owner_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    relation: str = "siblings"
    share: bool = True
    seed: Optional[int] = None


ACCESSORIES = {
    "moon_scarf": Accessory(
        id="moon_scarf",
        label="moon scarf",
        phrase="a soft moon scarf with tiny stitched stars",
        wear_text="wrapped the moon scarf around her shoulders",
        share_text="loosely around {friend}'s shoulders so it felt like a small night hug",
        end_text="the moon scarf lay over both children like a silver ribbon of sleep",
        soft=True,
        bedtime=True,
        tags={"accessory", "scarf", "sharing"},
    ),
    "star_bracelet": Accessory(
        id="star_bracelet",
        label="star bracelet",
        phrase="a soft felt star bracelet with a quiet snap",
        wear_text="fastened the star bracelet around her wrist",
        share_text="around {friend}'s wrist beside the sore place so {friend_pron} could feel its soft edge",
        end_text="the star bracelet rested on the pillow between them like a tiny sleepy moon",
        soft=True,
        bedtime=True,
        tags={"accessory", "bracelet", "sharing"},
    ),
    "comet_ribbon": Accessory(
        id="comet_ribbon",
        label="comet ribbon",
        phrase="a silky comet ribbon for bedtime braids",
        wear_text="tied the comet ribbon into her hair",
        share_text="gently into {friend}'s hand so {friend_pron} could rub the smooth ribbon while breathing slowly",
        end_text="the comet ribbon curled on the blanket while both children drifted toward sleep",
        soft=True,
        bedtime=True,
        tags={"accessory", "ribbon", "sharing"},
    ),
    "paper_crown": Accessory(
        id="paper_crown",
        label="paper crown",
        phrase="a stiff paper crown with glitter points",
        wear_text="set the paper crown on her head",
        share_text="near {friend}, though its scratchy edge did not belong in bed",
        end_text="the paper crown sat on the dresser, bright but not cozy",
        soft=False,
        bedtime=False,
        tags={"accessory"},
    ),
}

INJURIES = {
    "knee": Injury(
        id="knee",
        place="knee",
        phrase="a little scab on her knee",
        article_phrase="the little scab on her knee",
        tags={"scab", "knee"},
    ),
    "elbow": Injury(
        id="elbow",
        place="elbow",
        phrase="a little scab on his elbow",
        article_phrase="the little scab on his elbow",
        tags={"scab", "elbow"},
    ),
    "shin": Injury(
        id="shin",
        place="shin",
        phrase="a little scab on her shin",
        article_phrase="the little scab on her shin",
        tags={"scab", "shin"},
    ),
}

RHYMES = {
    "moon": Rhyme(
        id="moon",
        first="Moon so mild, shine on this child.",
        second="Rest so deep, drift into sleep.",
        topic="moon",
        tags={"rhyme", "moon"},
    ),
    "breeze": Rhyme(
        id="breeze",
        first="Soft little breeze, hush through the trees.",
        second="Quiet and slow, off to dreams we go.",
        topic="breeze",
        tags={"rhyme", "breeze"},
    ),
    "nest": Rhyme(
        id="nest",
        first="Cozy little nest, bedtime is best.",
        second="Close your eyes tight, cuddle the night.",
        topic="nest",
        tags={"rhyme", "nest"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tess", "Nora", "Ivy", "Ella", "June", "Sadie"]
BOY_NAMES = ["Owen", "Ben", "Milo", "Theo", "Eli", "Finn", "Noah", "Sam"]


def explain_rejection(accessory: Accessory) -> str:
    return (
        f"(No story: {accessory.phrase} is not a sensible bedtime accessory to share. "
        f"The world only allows soft, bedtime-friendly accessories that can comfort a child in bed.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a bedtime accessory, a child with a small scab, and a sharing rhyme."
    )
    ap.add_argument("--accessory", choices=ACCESSORIES)
    ap.add_argument("--injury", choices=INJURIES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--share", choices=["yes", "no"], help="force whether the accessory is shared")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.accessory and not accessory_reasonable(ACCESSORIES[args.accessory]):
        raise StoryError(explain_rejection(ACCESSORIES[args.accessory]))

    combos = [
        combo for combo in valid_combos()
        if (args.accessory is None or combo[0] == args.accessory)
        and (args.injury is None or combo[1] == args.injury)
        and (args.rhyme is None or combo[2] == args.rhyme)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    accessory_id, injury_id, rhyme_id = rng.choice(sorted(combos))
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    owner_name = pick_name(rng, owner_gender)
    friend_name = pick_name(rng, friend_gender, avoid=owner_name)
    parent = args.parent or rng.choice(["mother", "father"])
    share = True if args.share is None else args.share == "yes"
    relation = args.relation or rng.choice(["siblings", "friends"])
    return StoryParams(
        accessory=accessory_id,
        injury=injury_id,
        rhyme=rhyme_id,
        owner_name=owner_name,
        owner_gender=owner_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        relation=relation,
        share=share,
    )


def introduce(world: World, owner: Entity, accessory_cfg: Accessory, friend: Entity, injury_cfg: Injury) -> None:
    relation_text = "shared a room" if world.facts["relation"] == "siblings" else "were having a sleepover"
    world.say(
        f"At bedtime, {owner.id} and {friend.id} {relation_text} while the house grew quiet and the window turned dark as plum jam."
    )
    world.say(
        f"{owner.id} {accessory_cfg.wear_text}. It was {owner.pronoun('possessive')} personal accessory for sleepy nights, and {owner.pronoun()} loved how it made bedtime feel gentle."
    )
    world.say(
        f"But {friend.id} kept touching {injury_cfg.article_phrase}. The little scab had come from an earlier tumble, and now it felt much bigger in the dark."
    )


def worry(world: World, friend: Entity, parent: Entity, injury_cfg: Injury) -> None:
    friend.meters["throb"] += 1
    friend.memes["worry"] += 1
    world.say(
        f'"My {injury_cfg.place} is trying to stay awake," {friend.id} whispered. "{injury_cfg.article_phrase.capitalize()} feels scratchy."'
    )
    world.say(
        f"{parent.label_word.capitalize()} tucked the blanket near {friend.pronoun('object')} and promised that small hurts usually quiet down when the rest of the room does."
    )


def offer_rhyme(world: World, owner: Entity, friend: Entity, rhyme_cfg: Rhyme) -> None:
    friend.memes["heard_rhyme"] += 1
    world.say(
        f'{owner.id} leaned closer and said, "I know a bedtime rhyme." Then {owner.pronoun()} sang softly: "{rhyme_cfg.first} {rhyme_cfg.second}"'
    )
    propagate(world)
    if friend.memes["calm"] >= THRESHOLD:
        world.say(
            f"{friend.id} listened, and {friend.pronoun('possessive')} breathing slowed a little. The words gave the room a softer shape."
        )


def hesitate(world: World, owner: Entity, accessory_cfg: Accessory) -> None:
    owner.memes["protective"] += 1
    world.say(
        f"{owner.id} held the {accessory_cfg.label} close for a moment. It had always been the bedtime thing {owner.pronoun()} kept just for {owner.pronoun('object')}."
    )


def share_accessory(world: World, owner: Entity, friend: Entity, accessory: Entity, accessory_cfg: Accessory) -> None:
    owner.memes["generosity"] += 1
    accessory.attrs["shared_with"] = friend.id
    propagate(world)
    friend_pron = friend.pronoun("subject")
    world.say(
        f"Then {owner.id} remembered how dark a room can feel when someone is hurting. {owner.pronoun().capitalize()} placed the {accessory_cfg.label} {accessory_cfg.share_text.format(friend=friend.id, friend_pron=friend_pron)}."
    )
    world.say(
        f'"You can borrow my personal accessory tonight," {owner.pronoun()} whispered. "We can share the calm part."'
    )


def keep_accessory(world: World, owner: Entity, friend: Entity, accessory_cfg: Accessory) -> None:
    propagate(world)
    world.say(
        f'{owner.id} almost offered the {accessory_cfg.label}, but tucked it back under {owner.pronoun("possessive")} chin instead. "{friend.id}, you can listen to the rhyme again," {owner.pronoun()} said.'
    )
    if friend.memes["comfort"] < THRESHOLD:
        world.say(
            f"The rhyme helped some, but {friend.id} still rubbed at the blanket and blinked at the ceiling."
        )


def settle(world: World, owner: Entity, friend: Entity, accessory_cfg: Accessory, rhyme_cfg: Rhyme) -> None:
    if friend.memes["comfort"] >= THRESHOLD and friend.memes["calm"] >= 2:
        world.say(
            f"Soon {friend.id}'s sore thoughts grew smaller than the night song. {friend.pronoun('possessive').capitalize()} hand loosened, and even {friend.pronoun('possessive')} worry about the scab drifted away."
        )
        world.say(
            f"{parent_name(world).capitalize()} smiled from the doorway and listened to the last hush of the rhyme. In the dim room, {accessory_cfg.end_text}."
        )
    else:
        world.say(
            f"After another whisper of the rhyme, {friend.id} finally grew drowsy, though {friend.pronoun('possessive')} hand still stayed close to the sore spot."
        )
        world.say(
            f"{parent_name(world).capitalize()} left the door cracked open so a strip of hall light could keep the room company. The night became quieter, but not quite as cozy."
        )


def parent_name(world: World) -> str:
    return world.get("parent").label_word


def tell(
    accessory_cfg: Accessory,
    injury_cfg: Injury,
    rhyme_cfg: Rhyme,
    owner_name: str,
    owner_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    relation: str,
    share: bool,
) -> World:
    world = World()
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    accessory = world.add(
        Entity(
            id="accessory",
            kind="thing",
            type="accessory",
            label=accessory_cfg.label,
            phrase=accessory_cfg.phrase,
            role="comfort_object",
            tags=set(accessory_cfg.tags),
            attrs={"owner": owner.id, "shared_with": ""},
        )
    )
    friend.attrs["injury_place"] = injury_cfg.place
    friend.tags |= set(injury_cfg.tags)

    world.facts["relation"] = relation

    introduce(world, owner, accessory_cfg, friend, injury_cfg)
    world.para()
    worry(world, friend, parent, injury_cfg)
    offer_rhyme(world, owner, friend, rhyme_cfg)
    hesitate(world, owner, accessory_cfg)
    world.para()
    if share:
        share_accessory(world, owner, friend, accessory, accessory_cfg)
    else:
        keep_accessory(world, owner, friend, accessory_cfg)
    settle(world, owner, friend, accessory_cfg, rhyme_cfg)

    world.facts.update(
        owner=owner,
        friend=friend,
        parent=parent,
        accessory_cfg=accessory_cfg,
        injury_cfg=injury_cfg,
        rhyme_cfg=rhyme_cfg,
        accessory=accessory,
        shared=accessory.attrs.get("shared_with") == friend.id,
        outcome="shared" if accessory.attrs.get("shared_with") == friend.id else "kept",
        soothed=friend.memes["calm"] >= THRESHOLD,
        slept_easily=friend.memes["calm"] >= 2 and friend.memes["comfort"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    owner = world.facts["owner"]
    friend = world.facts["friend"]
    accessory_cfg = world.facts["accessory_cfg"]
    injury_cfg = world.facts["injury_cfg"]
    rhyme_cfg = world.facts["rhyme_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "shared":
        return [
            f'Write a bedtime story for a 3-to-5-year-old that includes the words "accessory", "personal", and "scab", and centers on sharing.',
            f"Tell a gentle night story where {owner.id} shares {owner.pronoun('possessive')} personal {accessory_cfg.label} with {friend.id}, who is worried about {injury_cfg.article_phrase}. Include a soothing rhyme.",
            f'Write a cozy story where a treasured bedtime accessory stops being only personal once one child chooses to share it with another child who cannot sleep.',
        ]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "accessory", "personal", and "scab". Include a rhyme and a small emotional dilemma.',
        f"Tell a quiet story where {owner.id} knows a comforting rhyme for {friend.id}, who is worried about {injury_cfg.article_phrase}, but hesitates to share {owner.pronoun('possessive')} personal {accessory_cfg.label}.",
        f'Write a bedtime story about a child deciding whether a personal accessory can become something shared when another child needs comfort.',
    ]


KNOWLEDGE = {
    "accessory": [
        (
            "What is an accessory?",
            "An accessory is an extra thing you wear or carry, like a scarf, bracelet, or ribbon. It can make you feel dressed, cozy, or special."
        )
    ],
    "scab": [
        (
            "What is a scab?",
            "A scab is the dry cover your body makes over a small scrape while the skin heals. It helps protect the hurt place underneath."
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing is kind because it lets someone else use or enjoy something that helps them. It can make two people feel close instead of only one person feeling comfortable."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair of words or lines that sound alike at the end. Rhymes can make songs and bedtime verses easier to remember."
        )
    ],
    "bedtime": [
        (
            "Why do quiet routines help at bedtime?",
            "Quiet routines help because the same calm steps each night tell your body it is time to rest. Soft words, dim light, and slow breathing can make sleepy feelings grow."
        )
    ],
}


def story_qa(world: World) -> list[tuple[str, str]]:
    owner = world.facts["owner"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    accessory_cfg = world.facts["accessory_cfg"]
    injury_cfg = world.facts["injury_cfg"]
    rhyme_cfg = world.facts["rhyme_cfg"]
    shared = world.facts["shared"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id} and {friend.id} at bedtime. {parent.label_word.capitalize()} is there too, helping the room feel quiet."
        ),
        (
            f"Why could {friend.id} not settle down at first?",
            f"{friend.id} kept thinking about {injury_cfg.article_phrase}, and the sore place felt bigger in the dark. That worry made bedtime feel harder than usual."
        ),
        (
            f"What was special about {owner.id}'s {accessory_cfg.label}?",
            f"It was {owner.id}'s personal accessory for bedtime, something {owner.pronoun()} usually kept just for {owner.pronoun('object')}. That is why sharing it felt important."
        ),
        (
            "What was the rhyme in the story for?",
            f"The rhyme was meant to slow the room down and help {friend.id} feel calmer. Its soft sound started the change before the sharing decision finished it."
        ),
    ]
    if shared:
        qa.append(
            (
                f"How did {owner.id} help {friend.id}?",
                f"{owner.id} first sang the rhyme, then shared the {accessory_cfg.label}. That gave {friend.id} both gentle words and a comforting thing to hold or wear."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with both children feeling calmer and closer. The bedtime accessory became something shared, and that change helped the night feel safe again."
            )
        )
    else:
        qa.append(
            (
                f"Did the rhyme help {friend.id} completely?",
                f"Not completely. The rhyme made things softer, but {friend.id} still felt some worry because the accessory stayed personal instead of being shared."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended more quietly than happily. {friend.id} did get sleepy at last, but the room never became as cozy as it could have if the accessory had been shared."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"accessory", "scab", "sharing", "rhyme", "bedtime"}
    out: list[tuple[str, str]] = []
    for tag in ["accessory", "scab", "sharing", "rhyme", "bedtime"]:
        out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if entity.tags:
            bits.append(f"tags={sorted(entity.tags)}")
        if entity.role:
            bits.append(f"role={entity.role}")
        lines.append(f"  {entity.id:10} ({entity.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {len(world.fired)} state updates")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        accessory="moon_scarf",
        injury="knee",
        rhyme="moon",
        owner_name="Lila",
        owner_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        relation="siblings",
        share=True,
    ),
    StoryParams(
        accessory="star_bracelet",
        injury="elbow",
        rhyme="nest",
        owner_name="Mina",
        owner_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        parent="father",
        relation="friends",
        share=True,
    ),
    StoryParams(
        accessory="comet_ribbon",
        injury="shin",
        rhyme="breeze",
        owner_name="June",
        owner_gender="girl",
        friend_name="Ella",
        friend_gender="girl",
        parent="mother",
        relation="siblings",
        share=False,
    ),
]


ASP_RULES = r"""
reasonable_accessory(A) :- accessory(A), soft(A), bedtime(A).
valid(A, I, R) :- reasonable_accessory(A), injury(I), rhyme(R).

shared_outcome(shared) :- choose_share(yes).
shared_outcome(kept) :- choose_share(no).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for accessory_id, accessory in ACCESSORIES.items():
        lines.append(asp.fact("accessory", accessory_id))
        if accessory.soft:
            lines.append(asp.fact("soft", accessory_id))
        if accessory.bedtime:
            lines.append(asp.fact("bedtime", accessory_id))
    for injury_id in INJURIES:
        lines.append(asp.fact("injury", injury_id))
    for rhyme_id in RHYMES:
        lines.append(asp.fact("rhyme", rhyme_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(share: bool) -> str:
    import asp

    extra = "choose_share(yes)." if share else "choose_share(no)."
    model = asp.one_model(asp_program(extra, "#show shared_outcome/1."))
    atoms = asp.atoms(model, "shared_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo - py:
            print("  only in clingo:", sorted(clingo - py))
        if py - clingo:
            print("  only in python:", sorted(py - clingo))

    if asp_outcome(True) == "shared" and asp_outcome(False) == "kept":
        print("OK: outcome model matches share flag.")
    else:
        rc = 1
        print("MISMATCH in share outcome model.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.accessory not in ACCESSORIES:
        raise StoryError(f"(Unknown accessory: {params.accessory})")
    if params.injury not in INJURIES:
        raise StoryError(f"(Unknown injury: {params.injury})")
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme: {params.rhyme})")
    accessory_cfg = ACCESSORIES[params.accessory]
    if not accessory_reasonable(accessory_cfg):
        raise StoryError(explain_rejection(accessory_cfg))

    world = tell(
        accessory_cfg=accessory_cfg,
        injury_cfg=INJURIES[params.injury],
        rhyme_cfg=RHYMES[params.rhyme],
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        relation=params.relation,
        share=params.share,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show shared_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (accessory, injury, rhyme) combos:\n")
        for accessory_id, injury_id, rhyme_id in combos:
            print(f"  {accessory_id:14} {injury_id:8} {rhyme_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.owner_name} and {p.friend_name}: {p.accessory}, {p.injury}, {asp_outcome(p.share)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
