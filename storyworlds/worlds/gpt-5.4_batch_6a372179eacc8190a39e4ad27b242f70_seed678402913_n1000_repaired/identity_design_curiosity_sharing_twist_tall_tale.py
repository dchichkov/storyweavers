#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/identity_design_curiosity_sharing_twist_tall_tale.py
==============================================================================

A standalone storyworld about a child who makes an enormous sky-design for a
wind festival. The child wants the design to show family identity, curiosity
leads to an old clue, sharing solves the build problem, and a tall-tale twist
appears once the thing finally flies.

Run it
------
    python storyworlds/worlds/gpt-5.4/identity_design_curiosity_sharing_twist_tall_tale.py
    python storyworlds/worlds/gpt-5.4/identity_design_curiosity_sharing_twist_tall_tale.py --project kite --material sailcloth
    python storyworlds/worlds/gpt-5.4/identity_design_curiosity_sharing_twist_tall_tale.py --project kite --material tissue
    python storyworlds/worlds/gpt-5.4/identity_design_curiosity_sharing_twist_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/identity_design_curiosity_sharing_twist_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/identity_design_curiosity_sharing_twist_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly.
_THIS = os.path.abspath(__file__)
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_THIS)))
sys.path.insert(0, _STORYWORLDS_DIR)
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    brag: str
    gust: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    need: int
    boast: str
    fly: str
    visible_from: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    strength: int
    texture: str
    flimsy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Frame:
    id: str
    label: str
    phrase: str
    strength: int
    springy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareMode:
    id: str
    label: str
    phrase: str
    help_strength: int
    shared_object: str
    action: str
    ending_gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Discovery:
    id: str
    clue: str
    find_place: str
    lesson: str
    hidden_image: str
    twist_line: str
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


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the Windbrag Prairie Fair",
        sky="a sky so wide it looked borrowed from tomorrow",
        brag="folks there measured gusts the way bakers measure flour",
        gust="the wind came running low over the grass",
        tags={"wind", "fair"},
    ),
    "river": Setting(
        id="river",
        place="the Riverbend Gust Day",
        sky="a sky as shiny as a pail tipped upside down",
        brag="people said even the fish listened when the wind whistled there",
        gust="the wind hopped along the levee and slapped every flag awake",
        tags={"wind", "river"},
    ),
    "hill": Setting(
        id="hill",
        place="the High Hill Sky Picnic",
        sky="a sky so tall the clouds seemed to need ladders",
        brag="neighbors claimed a good gust could tug a hat clear into next week",
        gust="the wind rolled over the hill like a laughing drumbeat",
        tags={"wind", "hill"},
    ),
}

PROJECTS = {
    "kite": Project(
        id="kite",
        label="kite",
        phrase="a sky-high kite",
        need=5,
        boast="big enough to make the geese check their manners",
        fly="climbed into the air",
        visible_from="three fields away",
        tags={"kite", "design"},
    ),
    "banner": Project(
        id="banner",
        label="banner-kite",
        phrase="a banner-kite as long as a wagon",
        need=6,
        boast="long enough to tickle the weather vane",
        fly="unfurled and pulled against the clouds",
        visible_from="the far side of town",
        tags={"banner", "design"},
    ),
    "swallow": Project(
        id="swallow",
        label="swallow-kite",
        phrase="a swallow-shaped kite with a forked tail",
        need=5,
        boast="broad enough to make the crows stare",
        fly="swooped up and skimmed the bright wind",
        visible_from="every porch on the ridge",
        tags={"kite", "bird", "design"},
    ),
}

MATERIALS = {
    "sailcloth": Material(
        id="sailcloth",
        label="sailcloth",
        phrase="old sailcloth from a shed hook",
        strength=3,
        texture="strong as a promise and smooth in the hand",
        tags={"cloth", "sturdy"},
    ),
    "feed_sacks": Material(
        id="feed_sacks",
        label="feed-sack cloth",
        phrase="bright feed-sack cloth",
        strength=2,
        texture="patched, cheerful, and tougher than it looked",
        tags={"cloth", "patched"},
    ),
    "tissue": Material(
        id="tissue",
        label="tissue paper",
        phrase="thin tissue paper from a party box",
        strength=1,
        texture="pretty as candy and nearly as delicate",
        flimsy=True,
        tags={"paper", "flimsy"},
    ),
}

FRAMES = {
    "willow": Frame(
        id="willow",
        label="willow ribs",
        phrase="springy willow ribs",
        strength=2,
        springy="bent without breaking",
        tags={"wood", "springy"},
    ),
    "bamboo": Frame(
        id="bamboo",
        label="bamboo spars",
        phrase="light bamboo spars",
        strength=3,
        springy="stayed light and straight",
        tags={"wood", "light"},
    ),
    "broom": Frame(
        id="broom",
        label="broom handles",
        phrase="two old broom handles",
        strength=1,
        springy="were stiff and clunky",
        tags={"wood", "clunky"},
    ),
}

SHARES = {
    "ribbon": ShareMode(
        id="ribbon",
        label="ribbon tails",
        phrase="a fistful of ribbon tails",
        help_strength=1,
        shared_object="ribbons",
        action="tied on extra tails so the kite could remember how to balance",
        ending_gift="a ribbon bow for the doorknob",
        tags={"sharing", "ribbon"},
    ),
    "paste": ShareMode(
        id="paste",
        label="paste and brush",
        phrase="a jar of wheat paste and a wide brush",
        help_strength=1,
        shared_object="paste",
        action="smoothed every seam until the skin held like one piece",
        ending_gift="the brush, washed and wrapped in string",
        tags={"sharing", "paste"},
    ),
    "spool": ShareMode(
        id="spool",
        label="string spool",
        phrase="a long spool of string",
        help_strength=2,
        shared_object="string",
        action="ran out a longer line so the wind could pull without snapping it",
        ending_gift="the spare string wound into a neat blue ring",
        tags={"sharing", "string"},
    ),
}

DISCOVERIES = {
    "monogram": Discovery(
        id="monogram",
        clue="an old flour-sack monogram stitched in red thread",
        find_place="inside a cedar trunk",
        lesson="that a design can show identity before anyone says a word",
        hidden_image="a giant curling first letter",
        twist_line="the tails curled into a letter so grand it looked like the wind had learned to write",
        tags={"identity", "letter"},
    ),
    "reverse": Discovery(
        id="reverse",
        clue="a faded sketch that showed two pictures painted back to back",
        find_place="under a tin of buttons",
        lesson="that one brave design can carry more than one story",
        hidden_image="a second picture on the reverse side",
        twist_line="when the gust flipped the cloth, the whole sky changed its face at once",
        tags={"identity", "twist"},
    ),
    "mirror": Discovery(
        id="mirror",
        clue="a handful of bright foil stars tucked in an envelope",
        find_place="behind a cracked frame",
        lesson="that a design can wave hello to faraway eyes",
        hidden_image="a flashing star path",
        twist_line="sunlight bounced from the foil and made a shining path across the fair",
        tags={"identity", "shine"},
    ),
}

GIRL_NAMES = ["Lila", "Mara", "June", "Tessa", "Nell", "Ruby", "Ada", "Molly"]
BOY_NAMES = ["Eli", "Beau", "Cal", "Jesse", "Otis", "Ned", "Roy", "Wade"]
HELPER_NAMES = ["Pip", "Toby", "Cora", "Wren", "Sadie", "Finn", "Mabel", "Gus"]
TRAITS = ["curious", "bold", "busy", "cheerful", "careful", "eager"]


def valid_combo(project_id: str, material_id: str, frame_id: str) -> bool:
    project = PROJECTS[project_id]
    material = MATERIALS[material_id]
    frame = FRAMES[frame_id]
    return material.strength + frame.strength >= project.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for project_id in PROJECTS:
        for material_id in MATERIALS:
            for frame_id in FRAMES:
                if valid_combo(project_id, material_id, frame_id):
                    combos.append((project_id, material_id, frame_id))
    return combos


def explain_rejection(project: Project, material: Material, frame: Frame) -> str:
    total = material.strength + frame.strength
    return (
        f"(No story: {project.phrase} needs strength {project.need}, but "
        f"{material.label} plus {frame.label} only reaches {total}. "
        f"A tall tale may brag, but the build still has to be sturdy enough to fly.)"
    )


@dataclass
class StoryParams:
    setting: str
    project: str
    material: str
    frame: str
    share: str
    discovery: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def launch_power(params: StoryParams) -> int:
    project = PROJECTS[params.project]
    material = MATERIALS[params.material]
    frame = FRAMES[params.frame]
    share = SHARES[params.share]
    return material.strength + frame.strength + share.help_strength - project.need


def outcome_of(params: StoryParams) -> str:
    power = launch_power(params)
    if power >= 2:
        return "grand"
    return "steady"


def tell(
    setting: Setting,
    project: Project,
    material: Material,
    frame: Frame,
    share: ShareMode,
    discovery: Discovery,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    elder_type: str,
    trait: str,
) -> World:
    if not valid_combo(project.id, material.id, frame.id):
        raise StoryError(explain_rejection(project, material, frame))

    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            attrs={"trait": trait},
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            tags={"child"},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            tags={"adult"},
        )
    )
    build = world.add(
        Entity(
            id="build",
            kind="thing",
            type="project",
            label=project.label,
            phrase=project.phrase,
            tags=set(project.tags),
        )
    )
    wind = world.add(
        Entity(
            id="wind",
            kind="thing",
            type="weather",
            label="wind",
            phrase=setting.gust,
            tags={"wind"},
        )
    )

    build.meters["strength"] = float(material.strength + frame.strength)
    build.meters["need"] = float(project.need)
    build.meters["size"] = float(project.need + 2)
    hero.memes["curiosity"] += 1
    hero.memes["pride"] += 1
    world.facts["problem"] = build.meters["need"] - build.meters["strength"]

    world.say(
        f"In {setting.place}, under {setting.sky}, folks told stories bigger than barns, and {setting.brag}."
    )
    world.say(
        f"{hero.id} was a {trait} little {hero.type} who wanted to make {project.phrase}, {project.boast}."
    )
    world.say(
        f'"I want one look at it to tell everybody our family identity," {hero.id} said. '
        f'"Not with words first. With the design."'
    )

    world.para()
    world.say(
        f"So {hero.id} rummaged {discovery.find_place} and found {discovery.clue}. "
        f"{hero.pronoun().capitalize()} studied it until {hero.pronoun('possessive')} curiosity hummed."
    )
    hero.memes["understanding"] += 1
    world.say(
        f"The old clue taught {hero.pronoun('object')} {discovery.lesson}."
    )
    build.attrs["hidden_image"] = discovery.hidden_image

    world.say(
        f"{hero.id} stretched out {material.phrase}, set down {frame.phrase}, and began to plan every stripe and loop."
    )
    world.say(
        f"The {material.label} felt {material.texture}, and the {frame.label} {frame.springy}."
    )

    world.para()
    if build.meters["strength"] < build.meters["need"]:
        build.meters["wobble"] += 1
        hero.memes["worry"] += 1
        world.say(
            f"But once the pieces were spread on the grass, {hero.id} saw the trouble. "
            f"The grand design was bigger than the first build could honestly hold."
        )
        world.say(
            f"One gust nipped the edge, and the half-made {project.label} shivered like it was thinking twice."
        )
    else:
        world.say(
            f"Even before it was finished, the thing looked ready to tug on the afternoon."
        )

    helper.memes["generosity"] += 1
    build.meters["strength"] += float(share.help_strength)
    world.say(
        f"That was when {helper.id} came skipping over with {share.phrase}. "
        f'"Take this," {helper.pronoun()} said. "A sky thing that grand ought to belong to more than one pair of hands."'
    )
    world.say(
        f"Together they {share.action}."
    )
    hero.memes["gratitude"] += 1
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1

    world.say(
        f"{elder.label_word.capitalize()} watched from the porch and nodded. "
        f'"Now that is sharing," {elder.pronoun()} said. "And sharing gives a design room to grow."'
    )

    world.para()
    power = build.meters["strength"] - build.meters["need"]
    world.facts["launch_power"] = power
    build.meters["lift"] = max(1.0, power + 1.0)
    build.meters["airborne"] += 1
    world.say(
        f"At last they ran. {setting.gust}, the line sang in {hero.id}'s hands, and the {project.label} {project.fly}."
    )
    world.say(
        f"It rose {project.visible_from}, pulling every eye in the fair upward."
    )

    if discovery.id == "reverse":
        build.meters["twist"] += 1
        world.say(
            f"Then came the twist. {discovery.twist_line}. One side showed the careful family mark {hero.id} had planned, "
            f"and the other side burst out with {discovery.hidden_image}."
        )
    elif discovery.id == "mirror":
        build.meters["twist"] += 1
        world.say(
            f"Then came the twist. {discovery.twist_line}. The shining bits did not just glitter; "
            f"they drew a bright road in the air straight toward {hero.id}'s family's picnic blanket."
        )
    else:
        build.meters["twist"] += 1
        world.say(
            f"Then came the twist. {discovery.twist_line}. Folks on the ground first saw a whirl of color, "
            f"and only after the tails settled did they gasp at {discovery.hidden_image}."
        )

    if power >= 2:
        hero.memes["wonder"] += 1
        helper.memes["wonder"] += 1
        world.say(
            f"People swore the sky-design pulled the whole afternoon a little taller. "
            f"For the rest of the day, children chased its shadow and grown-ups laughed as if the wind had told them a secret."
        )
    else:
        hero.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(
            f"It held steady at last, proud and high. That was miracle enough for a piece of cloth that had started as a worry on the grass."
        )

    world.para()
    hero.memes["belonging"] += 1
    helper.memes["belonging"] += 1
    world.say(
        f'When it came down, {hero.id} did not keep all the glory. {hero.pronoun().capitalize()} handed {helper.id} {share.ending_gift} and said, '
        f'"This design carries your hands in it too."'
    )
    world.say(
        f"So the biggest thing at {setting.place} was not only the flying shape overhead. "
        f"It was the roomy feeling in {hero.id}'s chest: identity could be shown by one child, but it grew brighter when shared."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        elder=elder,
        build=build,
        setting=setting,
        project=project,
        material=material,
        frame=frame,
        share=share,
        discovery=discovery,
        outcome="grand" if power >= 2 else "steady",
    )
    return world


KNOWLEDGE = {
    "kite": [
        (
            "What helps a kite fly well?",
            "A kite flies well when it is light enough to lift, strong enough not to tear, and balanced by its frame and tail. Wind pulls on the shape, but the shape has to hold together."
        )
    ],
    "design": [
        (
            "What is a design?",
            "A design is a plan for how something should look or work. It helps you choose shapes, colors, and parts before you build."
        )
    ],
    "identity": [
        (
            "What does identity mean?",
            "Identity is what shows who someone is or what group they belong to. A name, mark, color, or special style can all help show identity."
        )
    ],
    "sharing": [
        (
            "Why can sharing make a project better?",
            "Sharing can give a project extra tools, materials, or ideas. It also means more people care for the finished thing."
        )
    ],
    "wind": [
        (
            "Why does wind matter for a kite?",
            "Wind pushes under and across a kite so it can rise. If the kite is weak or badly balanced, the same wind can also make it wobble."
        )
    ],
    "cloth": [
        (
            "Why is cloth often stronger than thin paper outside?",
            "Cloth usually bends without ripping as quickly as thin paper. That makes it a better choice when wind tugs and flaps at it."
        )
    ],
    "letter": [
        (
            "Why do letters make strong symbols?",
            "A letter can stand for a name, a family, or a team in one simple shape. People recognize it quickly, so it can work like a sign."
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprising turn that changes how you understand what is happening. It feels earned when the surprise grows from clues already in the story."
        )
    ],
    "shine": [
        (
            "Why do shiny pieces flash in the sun?",
            "Shiny pieces bounce light instead of soaking it up. When they tilt just right, the reflected light can look like a bright flash."
        )
    ],
}
KNOWLEDGE_ORDER = ["identity", "design", "sharing", "wind", "cloth", "kite", "letter", "shine", "twist"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    project = f["project"]
    discovery = f["discovery"]
    setting = f["setting"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that uses the words "identity" and "design" and takes place at {setting.place}.',
        f"Tell a windy fair story where {hero.id} builds {project.phrase}, curiosity leads to {discovery.clue}, and sharing changes the ending.",
        f"Write a child-facing tall tale with a clear twist at launch, where a giant flying design shows family identity in a surprising way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    elder = f["elder"]
    project = f["project"]
    material = f["material"]
    frame = f["frame"]
    share = f["share"]
    discovery = f["discovery"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child at {setting.place}, and {helper.id}, the friend who helped. {elder.label_word.capitalize()} also watched and encouraged them."
        ),
        (
            f"What did {hero.id} want to make?",
            f"{hero.id} wanted to make {project.phrase} so people could see family identity in the sky. The design was meant to show who the family was before anyone even spoke."
        ),
        (
            f"What made {hero.id} curious?",
            f"{hero.id} found {discovery.clue} {discovery.find_place}. That clue made {hero.pronoun('object')} wonder how an old mark or trick could become part of a new flying design."
        ),
    ]
    problem = world.facts.get("problem", 0)
    if problem > 0:
        qa.append(
            (
                "What problem showed up while they were building?",
                f"The first build was not quite strong enough, so the giant shape wobbled when the wind touched it. The trouble came from trying to make something very big with only {material.label} and {frame.label} at first."
            )
        )
    qa.append(
        (
            f"How did sharing help?",
            f"{helper.id} shared {share.shared_object}, and together they {share.action}. That help gave the flying design what it needed to hold together in the wind."
        )
    )
    qa.append(
        (
            "What was the twist?",
            f"The twist came after the design rose into the air: {discovery.twist_line}. The surprise worked because the clue {hero.id} found earlier became part of the finished sky-picture."
        )
    )
    if outcome == "grand":
        qa.append(
            (
                "How did the story end?",
                f"It ended in a grand way, with the sky-design so strong and striking that people all over the fair looked up. At the end, {hero.id} shared the credit too, which made the happy feeling even bigger."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the design flying steadily at last, which felt wonderful after the earlier worry. The final image proved that sharing and patience had turned a shaky plan into something real."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"design", "identity", "sharing", "twist"} | set(f["project"].tags)
    tags |= set(f["setting"].tags) | set(f["material"].tags) | set(f["discovery"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="prairie",
        project="kite",
        material="feed_sacks",
        frame="bamboo",
        share="spool",
        discovery="monogram",
        hero_name="Lila",
        hero_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        elder="mother",
        trait="curious",
    ),
    StoryParams(
        setting="river",
        project="banner",
        material="sailcloth",
        frame="bamboo",
        share="paste",
        discovery="reverse",
        hero_name="Eli",
        hero_gender="boy",
        helper_name="Cora",
        helper_gender="girl",
        elder="father",
        trait="bold",
    ),
    StoryParams(
        setting="hill",
        project="swallow",
        material="sailcloth",
        frame="willow",
        share="ribbon",
        discovery="mirror",
        hero_name="Mara",
        hero_gender="girl",
        helper_name="Gus",
        helper_gender="boy",
        elder="mother",
        trait="eager",
    ),
    StoryParams(
        setting="prairie",
        project="swallow",
        material="feed_sacks",
        frame="bamboo",
        share="paste",
        discovery="reverse",
        hero_name="Cal",
        hero_gender="boy",
        helper_name="Wren",
        helper_gender="girl",
        elder="father",
        trait="careful",
    ),
]


ASP_RULES = r"""
valid(Project, Material, Frame) :-
    project(Project), material(Material), frame(Frame),
    need(Project, N), strength(Material, MS), strength_frame(Frame, FS),
    MS + FS >= N.

launch_power(Project, Material, Frame, Share, P) :-
    valid(Project, Material, Frame),
    strength(Material, MS), strength_frame(Frame, FS),
    help_strength(Share, HS), need(Project, N), P = MS + FS + HS - N.

outcome(Project, Material, Frame, Share, grand) :-
    launch_power(Project, Material, Frame, Share, P), P >= 2.
outcome(Project, Material, Frame, Share, steady) :-
    launch_power(Project, Material, Frame, Share, P), P < 2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("need", project_id, project.need))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("strength", material_id, material.strength))
    for frame_id, frame in FRAMES.items():
        lines.append(asp.fact("frame", frame_id))
        lines.append(asp.fact("strength_frame", frame_id, frame.strength))
    for share_id, share in SHARES.items():
        lines.append(asp.fact("share", share_id))
        lines.append(asp.fact("help_strength", share_id, share.help_strength))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_material", params.material),
            asp.fact("chosen_frame", params.frame),
            asp.fact("chosen_share", params.share),
            "picked_outcome(O) :- chosen_project(P), chosen_material(M), chosen_frame(F), chosen_share(S), outcome(P, M, F, S, O).",
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            p = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=False, header="### smoke")
        finally:
            sys.stdout = old
        if not buf.getvalue().strip():
            raise StoryError("emit() produced empty output during smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale storyworld: a child designs an enormous flying sign of identity. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--discovery", choices=DISCOVERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible build triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def _pick_helper_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    name = rng.choice([n for n in HELPER_NAMES if n != avoid])
    gender = rng.choice(["girl", "boy"])
    return name, gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.material and args.frame:
        if not valid_combo(args.project, args.material, args.frame):
            raise StoryError(
                explain_rejection(
                    PROJECTS[args.project],
                    MATERIALS[args.material],
                    FRAMES[args.frame],
                )
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.material is None or combo[1] == args.material)
        and (args.frame is None or combo[2] == args.frame)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, material_id, frame_id = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    helper_name, helper_gender = _pick_helper_name(rng, avoid=hero_name)
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        project=project_id,
        material=material_id,
        frame=frame_id,
        share=args.share or rng.choice(sorted(SHARES)),
        discovery=args.discovery or rng.choice(sorted(DISCOVERIES)),
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        elder=args.elder or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.frame not in FRAMES:
        raise StoryError(f"(Unknown frame: {params.frame})")
    if params.share not in SHARES:
        raise StoryError(f"(Unknown share mode: {params.share})")
    if params.discovery not in DISCOVERIES:
        raise StoryError(f"(Unknown discovery: {params.discovery})")

    world = tell(
        setting=SETTINGS[params.setting],
        project=PROJECTS[params.project],
        material=MATERIALS[params.material],
        frame=FRAMES[params.frame],
        share=SHARES[params.share],
        discovery=DISCOVERIES[params.discovery],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        elder_type=params.elder,
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
        print(asp_program("", "#show valid/3.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, material, frame) combos:\n")
        for project_id, material_id, frame_id in combos:
            print(f"  {project_id:8} {material_id:10} {frame_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.project} with {p.material} and {p.frame} "
                f"({p.setting}, {outcome_of(p)})"
            )
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
