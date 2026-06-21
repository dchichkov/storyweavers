#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/beggar_cliff_lookout_friendship_transformation_quest_pirate.py
==========================================================================================

A standalone storyworld for a small pirate-tale domain:

A young would-be pirate climbs to a cliff lookout on a quest. There the child
meets a beggar who seems bent, tired, and forgotten. The child must pause the
quest long enough to help. When the help truly fits the beggar's need, the
beggar's body and spirit change: the hunched stranger becomes a steady friend
and guide, and together they finish the lookout quest.

This world models:

* Friendship: kindness changes the relationship between hero and beggar.
* Transformation: relief and hope let the beggar stand tall again.
* Quest: the mission at the cliff lookout only succeeds once the helper and the
  beggar can work together.

The domain is intentionally tight: each quest needs a certain kind of ability,
each beggar-need blocks that ability, and only a matching aid makes a
reasonable story. Invalid combinations are rejected with a clear explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/beggar_cliff_lookout_friendship_transformation_quest_pirate.py
    python storyworlds/worlds/gpt-5.4/beggar_cliff_lookout_friendship_transformation_quest_pirate.py --quest light_beacon --need cold --aid cloak
    python storyworlds/worlds/gpt-5.4/beggar_cliff_lookout_friendship_transformation_quest_pirate.py --quest raise_flag --need blister --aid bandage
    python storyworlds/worlds/gpt-5.4/beggar_cliff_lookout_friendship_transformation_quest_pirate.py --all
    python storyworlds/worlds/gpt-5.4/beggar_cliff_lookout_friendship_transformation_quest_pirate.py --qa --json
    python storyworlds/worlds/gpt-5.4/beggar_cliff_lookout_friendship_transformation_quest_pirate.py --verify
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

# Make the shared result containers importable when this script is run directly.
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
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    opener: str
    blocked_skill: str
    finish: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    request: str
    state_line: str
    relief_line: str
    blocked_skill: str
    before_pose: str
    after_pose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    use_line: str
    fixes_need: str
    gift_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


def need_matches_quest(quest: Quest, need: Need) -> bool:
    return quest.blocked_skill == need.blocked_skill


def aid_matches_need(aid: Aid, need: Need) -> bool:
    return aid.fixes_need == need.id


def valid_combo(quest: Quest, need: Need, aid: Aid) -> bool:
    return need_matches_quest(quest, need) and aid_matches_need(aid, need)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for quest_id, quest in QUESTS.items():
        for need_id, need in NEEDS.items():
            for aid_id, aid in AIDS.items():
                if valid_combo(quest, need, aid):
                    combos.append((quest_id, need_id, aid_id))
    return combos


def explain_rejection(quest: Quest, need: Need, aid: Aid) -> str:
    if not need_matches_quest(quest, need):
        return (
            f"(No story: {quest.title.lower()} needs someone who can {quest.blocked_skill}, "
            f"but a beggar slowed by {need.label} is blocked in a different way. "
            f"Pick the need that truly stands in the way of that quest.)"
        )
    if not aid_matches_need(aid, need):
        return (
            f"(No story: {aid.label} would not honestly fix {need.label}. "
            f"The help in this world must match the beggar's real need.)"
        )
    return "(No story: this combination does not make a reasonable quest.)"


def tell(quest: Quest, need: Need, aid: Aid, hero_name: str, hero_gender: str, trait: str) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[trait, "brave"],
            label=hero_name,
            phrase=hero_name,
            tags={"pirate", "friendship"},
        )
    )
    beggar = world.add(
        Entity(
            id="Rowan",
            kind="character",
            type="man",
            role="beggar",
            label="the beggar",
            phrase="a ragged old beggar",
            tags={"beggar", "friendship"},
        )
    )
    lookout = world.add(
        Entity(
            id="lookout",
            kind="thing",
            type="place",
            label="the cliff lookout",
            phrase="the cliff lookout above the sea",
            tags={"lookout", "cliff"},
        )
    )

    hero.memes["quest"] = 1
    hero.memes["kindness"] = 1
    beggar.meters[need.id] = 1
    beggar.memes["lonely"] = 1
    beggar.meters["bent"] = 1
    world.facts["transformed"] = False
    world.facts["befriended"] = False
    world.facts["quest_done"] = False

    world.say(
        f"{hero_name} liked to pretend {hero.pronoun()} was captain of a small pirate crew, "
        f"even when {hero.pronoun()} climbed alone. One bright morning, {hero.pronoun()} scrambled "
        f"up to the cliff lookout above the roaring blue water with a quest in mind: {quest.goal}."
    )
    world.say(quest.opener)
    world.say(
        f"The wind tugged at {hero.pronoun('possessive')} shirt, gulls wheeled overhead, "
        f"and the whole sea looked wide enough for a hundred stories."
    )

    world.para()
    world.say(
        f"But curled beside the old stone wall sat {beggar.phrase}. {need.before_pose} "
        f"{need.state_line}"
    )
    world.say(
        f'"Please," he said, "{need.request}"'
    )
    hero.memes["hurry"] = 1
    world.say(
        f"{hero_name} almost rushed past. The quest felt important, and the tide below was already turning."
    )
    world.say(
        f"Then {hero.pronoun()} noticed how the old man's eyes kept slipping from the sea to {hero.pronoun('possessive')} face, "
        f"as if he had not expected anyone to stop."
    )

    world.para()
    world.say(
        f"{hero_name}'s pirate heart gave a stronger tug than hurry. {aid.gift_line}"
    )
    world.say(aid.use_line)
    beggar.meters[need.id] = 0.0
    beggar.memes["hope"] += 1
    beggar.memes["trust"] += 1
    hero.memes["trust"] += 1
    hero.memes["friendship"] += 1
    beggar.memes["friendship"] += 1
    world.facts["befriended"] = True
    world.say(need.relief_line)
    beggar.meters["bent"] = 0.0
    beggar.meters["steady"] += 1
    beggar.memes["dignity"] += 1
    world.facts["transformed"] = True
    world.say(
        f"{need.after_pose} In that moment, he did not look like a lonely beggar anymore. "
        f"He looked like a weather-wise sailor who had simply been waiting for one kind friend."
    )
    world.say(
        '"Rowan," he said, touching his chest. "That is my name. I used to keep watch here before my luck went thin."'
    )

    world.para()
    world.say(
        f"Because {hero_name} had helped first, Rowan could help back. He knew exactly how to {quest.blocked_skill}, "
        f"and he showed {hero.pronoun('object')} what to do."
    )
    hero.meters["working"] += 1
    beggar.meters["working"] += 1
    lookout.meters["quest_ready"] += 1
    world.say(quest.finish)
    hero.memes["joy"] += 1
    beggar.memes["joy"] += 1
    world.facts["quest_done"] = True

    world.para()
    world.say(
        f"When the work was done, {hero_name} and Rowan stood shoulder to shoulder at the cliff edge, "
        f"watching the sea answer them."
    )
    world.say(
        f"{quest.ending_image} {hero_name} had come looking for a pirate victory, "
        f"but found something better: a friend."
    )

    world.facts.update(
        hero=hero,
        beggar=beggar,
        lookout=lookout,
        quest=quest,
        need=need,
        aid=aid,
    )
    return world


@dataclass
class StoryParams:
    quest: str
    need: str
    aid: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


QUESTS = {
    "find_cove": Quest(
        id="find_cove",
        title="Find the Hidden Cove",
        goal="to find the hidden cove where moon-shells washed ashore",
        opener="At the top of the lookout, an old brass marker pointed toward a narrow stair cut into the cliff.",
        blocked_skill="climb the steep stair",
        finish="Together they climbed the steep stair, followed the brass marker, and found the hidden cove shining below like a secret bowl of silver water.",
        ending_image="Far beneath them, the moon-shells flashed pale in the sand, and the waves curled in with a sleepy pirate hush.",
        tags={"cove", "cliff", "quest"},
    ),
    "raise_flag": Quest(
        id="raise_flag",
        title="Raise the Warning Flag",
        goal="to raise the red warning flag before the fishing boats came too close to the rocks",
        opener="Beside the lookout stood a leaning mast with a stiff rope waiting to be hauled.",
        blocked_skill="haul the heavy rope",
        finish="Together they hauled the heavy rope, hand over hand, until the red warning flag snapped open against the sky.",
        ending_image="Down on the water, the little fishing boats turned away from the rocks, and the red flag flapped like a brave pirate banner.",
        tags={"flag", "boats", "quest"},
    ),
    "light_beacon": Quest(
        id="light_beacon",
        title="Light the Blue Beacon",
        goal="to light the blue beacon lantern before the evening fog rolled in",
        opener="Near the edge of the lookout, a glass beacon waited on its iron post, dull and dark.",
        blocked_skill="light the beacon with steady hands",
        finish="Together they lit the blue beacon with steady hands, and its clean glow spread over the gray sea just as the first fingers of fog arrived.",
        ending_image="The blue light shone over the waves like a calm pirate star, and even the gulls seemed to circle more softly around it.",
        tags={"beacon", "fog", "quest"},
    ),
}

NEEDS = {
    "blister": Need(
        id="blister",
        label="a sore blistered foot",
        request="my foot is rubbed raw, and I cannot trust it on the cliff stair",
        state_line="He kept one boot half off and winced each time he tried to shift.",
        relief_line="The tightness in his face loosened, and he let out a long breath.",
        blocked_skill="climb the steep stair",
        before_pose="His shoulders were folded in on themselves.",
        after_pose="Rowan set his boot down carefully, straightened, and found his balance again.",
        tags={"foot", "bandage"},
    ),
    "hunger": Need(
        id="hunger",
        label="an empty hungry belly",
        request="I have not eaten since yesterday, and the rope is too heavy for me now",
        state_line="His hands trembled against his coat, and his voice sounded thin as string.",
        relief_line="Color returned to his cheeks, and his hands stopped shaking.",
        blocked_skill="haul the heavy rope",
        before_pose="His back was bent like a hooked branch.",
        after_pose="Rowan rolled his shoulders, planted his feet, and stood far straighter than before.",
        tags={"bread", "food"},
    ),
    "cold": Need(
        id="cold",
        label="a cold, shaking body",
        request="the sea wind has gone right through me, and I cannot hold a flame still",
        state_line="The wind worried his sleeves, and his fingers shook too hard to be useful.",
        relief_line="Warmth crept back into him, and the shivering began to fade.",
        blocked_skill="light the beacon with steady hands",
        before_pose="He huddled into himself under the stone wall.",
        after_pose="Rowan lifted his chin, rubbed life into his hands, and stood with the sea wind instead of hiding from it.",
        tags={"cloak", "warmth"},
    ),
}

AIDS = {
    "bandage": Aid(
        id="bandage",
        label="a clean bandage",
        phrase="a clean bandage from a little sailor's pouch",
        use_line="Very gently, the child wrapped the sore foot with a clean bandage and helped Rowan tie his boot more softly.",
        fixes_need="blister",
        gift_line="From a little sailor's pouch, the child pulled out a clean bandage and knelt beside him.",
        tags={"bandage", "care"},
    ),
    "bread": Aid(
        id="bread",
        label="a round of bread",
        phrase="a round of bread",
        use_line="The child shared a round of bread, and Rowan ate slowly at first, then with grateful bites that seemed to wake him back up.",
        fixes_need="hunger",
        gift_line="From a striped cloth bundle, the child drew out a warm round of bread and broke it in half.",
        tags={"bread", "food"},
    ),
    "cloak": Aid(
        id="cloak",
        label="a wool cloak",
        phrase="a wool cloak",
        use_line="The child settled a wool cloak around Rowan's shoulders and tucked the edges in against the fierce salt wind.",
        fixes_need="cold",
        gift_line="Without fuss, the child slipped off a wool cloak and laid it around his shoulders.",
        tags={"cloak", "warmth"},
    ),
    "coin": Aid(
        id="coin",
        label="a shiny coin",
        phrase="a shiny coin",
        use_line="The child pressed a shiny coin into Rowan's hand, but a coin could not warm him, feed him, or steady his foot.",
        fixes_need="none",
        gift_line="The child reached for a shiny coin first.",
        tags={"coin"},
    ),
}

GIRL_NAMES = ["Lily", "Mara", "Nora", "Ava", "Ella", "Ruby", "Tessa", "Mina"]
BOY_NAMES = ["Tom", "Finn", "Leo", "Jack", "Noah", "Eli", "Sam", "Theo"]
TRAITS = ["kind", "quick", "curious", "bold", "bright", "cheerful"]


CURATED = [
    StoryParams(
        quest="find_cove",
        need="blister",
        aid="bandage",
        name="Mara",
        gender="girl",
        trait="kind",
    ),
    StoryParams(
        quest="raise_flag",
        need="hunger",
        aid="bread",
        name="Finn",
        gender="boy",
        trait="bold",
    ),
    StoryParams(
        quest="light_beacon",
        need="cold",
        aid="cloak",
        name="Ruby",
        gender="girl",
        trait="curious",
    ),
]


KNOWLEDGE = {
    "beggar": [
        (
            "What is a beggar?",
            "A beggar is a very poor person who asks others for help. A kind person can still be brave and worthy, even when they have very little."
        )
    ],
    "lookout": [
        (
            "What is a lookout?",
            "A lookout is a high place where someone watches the sea or the land. From a lookout, you can spot danger or help guide boats."
        )
    ],
    "flag": [
        (
            "Why would a warning flag matter near rocks?",
            "A warning flag can tell boats to keep away from danger. Seeing it early can help sailors choose a safer path."
        )
    ],
    "beacon": [
        (
            "What is a beacon?",
            "A beacon is a signal light. People use it to help others find their way or to warn them in fog or darkness."
        )
    ],
    "bread": [
        (
            "Why does food help a hungry person work again?",
            "Food gives the body energy. After eating, a hungry person can feel stronger and steadier."
        )
    ],
    "cloak": [
        (
            "What does a cloak do?",
            "A cloak is a warm outer covering. It helps block wind and keep body heat from escaping."
        )
    ],
    "bandage": [
        (
            "What is a bandage for?",
            "A bandage helps protect a sore or hurt place. It can make walking or healing easier."
        )
    ],
    "friendship": [
        (
            "How can helping someone start a friendship?",
            "Helping shows care and respect. When two people care for each other, trust can grow into friendship."
        )
    ],
}
KNOWLEDGE_ORDER = ["beggar", "lookout", "flag", "beacon", "bread", "cloak", "bandage", "friendship"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    quest = world.facts["quest"]
    need = world.facts["need"]
    aid = world.facts["aid"]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old set at a cliff lookout that includes the word "beggar".',
        f"Tell a gentle quest story where a young pirate named {hero.id} meets a beggar slowed by {need.label}, helps with {aid.label}, and discovers a new friend.",
        f"Write a story about friendship and transformation in which kindness comes before treasure, and the quest is to {quest.goal}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    beggar = world.facts["beggar"]
    quest = world.facts["quest"]
    need = world.facts["need"]
    aid = world.facts["aid"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child playing at being a pirate, and Rowan, the beggar at the cliff lookout. Their meeting turns into a friendship."
        ),
        (
            f"What quest did {hero.id} go to the lookout to do?",
            f"{hero.id} climbed to the lookout to {quest.goal}. The quest mattered because the cliff lookout watched over the sea."
        ),
        (
            "Why could Rowan not help right away?",
            f"He was slowed by {need.label}. That problem kept him from being able to {quest.blocked_skill}."
        ),
        (
            f"How did {hero.id} help Rowan?",
            f"{hero.id} helped him with {aid.label}. That matched Rowan's real trouble, so it changed more than his body: it gave him hope and dignity again."
        ),
    ]
    if world.facts.get("transformed"):
        qa.append(
            (
                "How did Rowan change after he was helped?",
                f"At first Rowan looked bent and lonely, but after the help he stood taller and spoke like an old sailor again. The kindness let him become more like his true self."
            )
        )
    if world.facts.get("quest_done"):
        qa.append(
            (
                "Did the quest succeed, and why?",
                f"Yes. The quest succeeded because {hero.id} stopped to help first, and then Rowan was able to {quest.blocked_skill}. Their friendship became the reason the quest could be finished."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {hero.id} and Rowan standing together at the cliff edge after the work was done. The sea answered their signal, and {hero.id} had found both a pirate victory and a friend."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"beggar", "lookout", "friendship"}
    quest = world.facts["quest"]
    aid = world.facts["aid"]
    if "flag" in quest.tags:
        tags.add("flag")
    if "beacon" in quest.tags:
        tags.add("beacon")
    if "bread" in aid.tags:
        tags.add("bread")
    if "cloak" in aid.tags:
        tags.add("cloak")
    if "bandage" in aid.tags:
        tags.add("bandage")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: transformed={world.facts.get('transformed')} befriended={world.facts.get('befriended')} quest_done={world.facts.get('quest_done')}")
    return "\n".join(lines)


ASP_RULES = r"""
% quest / need compatibility
valid_need(Q, N) :- quest(Q), need(N), quest_skill(Q, S), need_skill(N, S).

% aid / need compatibility
valid_aid(N, A) :- need(N), aid(A), fixes(A, N).

% full story compatibility
valid(Q, N, A) :- valid_need(Q, N), valid_aid(N, A).

outcome(success) :- chosen_quest(Q), chosen_need(N), chosen_aid(A), valid(Q, N, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest", quest_id))
        lines.append(asp.fact("quest_skill", quest_id, quest.blocked_skill))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        lines.append(asp.fact("need_skill", need_id, need.blocked_skill))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        if aid.fixes_need in NEEDS:
            lines.append(asp.fact("fixes", aid_id, aid.fixes_need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_quest", params.quest),
            asp.fact("chosen_need", params.need),
            asp.fact("chosen_aid", params.aid),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    for params in CURATED:
        py_ok = "success" if (params.quest, params.need, params.aid) in python_set else "invalid"
        asp_ok = asp_outcome(params)
        if py_ok != asp_ok:
            rc = 1
            print(f"MISMATCH in outcome for {params}: python={py_ok} asp={asp_ok}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: pirate tale at a cliff lookout with a beggar, friendship, transformation, and a quest."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.need and args.aid:
        quest = QUESTS[args.quest]
        need = NEEDS[args.need]
        aid = AIDS[args.aid]
        if not valid_combo(quest, need, aid):
            raise StoryError(explain_rejection(quest, need, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.need is None or combo[1] == args.need)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        if args.quest and args.need and args.aid:
            raise StoryError(explain_rejection(QUESTS[args.quest], NEEDS[args.need], AIDS[args.aid]))
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, need_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        quest=quest_id,
        need=need_id,
        aid=aid_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.need not in NEEDS or params.aid not in AIDS:
        raise StoryError("(Invalid params: unknown quest, need, or aid key.)")
    quest = QUESTS[params.quest]
    need = NEEDS[params.need]
    aid = AIDS[params.aid]
    if not valid_combo(quest, need, aid):
        raise StoryError(explain_rejection(quest, need, aid))

    world = tell(
        quest=quest,
        need=need,
        aid=aid,
        hero_name=params.name,
        hero_gender=params.gender,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, need, aid) combos:\n")
        for quest_id, need_id, aid_id in combos:
            print(f"  {quest_id:12} {need_id:8} {aid_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} with {p.need} helped by {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
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
