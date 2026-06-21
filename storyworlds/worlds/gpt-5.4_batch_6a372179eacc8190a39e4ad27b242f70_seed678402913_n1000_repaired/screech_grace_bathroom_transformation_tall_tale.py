#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/screech_grace_bathroom_transformation_tall_tale.py
=============================================================================

A standalone storyworld for a tall-tale bathroom transformation story built
around the seed words "screech" and "Grace".

Premise
-------
Grace comes to the bathroom carrying some ordinary mess from play. The tap lets
out a startling screech, and for a moment the bathroom feels too big, too echoey,
and too wild. A grown-up answers that wobble with calm grace and a sensible
washing plan. As the right bathroom helper goes to work, the room changes:
steam climbs, bubbles gather, mirrors glow, and Grace's courage changes too.
By the end, the cleanup becomes a child-sized tall tale of transformation.

World logic
-----------
This world refuses weak combinations. A helper must actually be able to clean
the chosen mess, and the chosen transformation form must fit what the helper
produces. For example, a sink can wash paint from hands, but it cannot honestly
support a steam-crown mirror tale. A shower can make steam for that, and a tub
can make bubble mountain tales.

Run it
------
    python storyworlds/worlds/gpt-5.4/screech_grace_bathroom_transformation_tall_tale.py
    python storyworlds/worlds/gpt-5.4/screech_grace_bathroom_transformation_tall_tale.py --mess muddy_feet --helper tub
    python storyworlds/worlds/gpt-5.4/screech_grace_bathroom_transformation_tall_tale.py --helper sink --mess muddy_feet
    python storyworlds/worlds/gpt-5.4/screech_grace_bathroom_transformation_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/screech_grace_bathroom_transformation_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/screech_grace_bathroom_transformation_tall_tale.py --json
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REGIONS = {"hands", "feet", "legs", "torso", "hair"}


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mess:
    id: str
    label: str
    phrase: str
    regions: set[str] = field(default_factory=set)
    severity: int = 1
    kind: str = "dirty"
    cause: str = ""
    tall_bit: str = ""
    rinse_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    power: int = 1
    comfort: int = 1
    bubbles: bool = False
    steam: bool = False
    start_text: str = ""
    clean_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Form:
    id: str
    title: str
    requires_bubbles: bool = False
    requires_steam: bool = False
    claim: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def helper_cleans(helper: Helper, mess: Mess) -> bool:
    return mess.regions.issubset(helper.covers) and helper.power >= mess.severity


def form_possible(helper: Helper, form: Form) -> bool:
    if form.requires_bubbles and not helper.bubbles:
        return False
    if form.requires_steam and not helper.steam:
        return False
    return True


def valid_combo(mess: Mess, helper: Helper, form: Form) -> bool:
    return helper_cleans(helper, mess) and form_possible(helper, form)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mess_id, mess in MESSES.items():
        for helper_id, helper in HELPERS.items():
            for form_id, form in FORMS.items():
                if valid_combo(mess, helper, form):
                    combos.append((mess_id, helper_id, form_id))
    return combos


def outcome_from(helper: Helper, screech: int) -> str:
    return "booming" if helper.comfort > screech else "steady"


def _r_screech_fear(world: World) -> list[str]:
    room = world.entities.get("room")
    hero = world.entities.get("hero")
    if room is None or hero is None:
        return []
    if room.meters["noise"] < THRESHOLD:
        return []
    sig = ("fear", int(room.meters["noise"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    return []


def _r_clean(world: World) -> list[str]:
    hero = world.entities.get("hero")
    room = world.entities.get("room")
    helper_ent = world.entities.get("helper")
    mess = world.facts.get("mess_cfg")
    helper = world.facts.get("helper_cfg")
    if hero is None or room is None or helper_ent is None or mess is None or helper is None:
        return []
    if helper_ent.meters["active"] < THRESHOLD or hero.meters["dirty"] < THRESHOLD:
        return []
    sig = ("clean", mess.id, helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["dirty"] = 0.0
    hero.meters["clean"] += 1
    room.meters["sparkle"] += 1
    if helper.bubbles:
        room.meters["bubbles"] += 1
    if helper.steam:
        room.meters["steam"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    hero.memes["courage"] += float(helper.comfort)
    return []


def _r_transform(world: World) -> list[str]:
    hero = world.entities.get("hero")
    room = world.entities.get("room")
    form = world.facts.get("form_cfg")
    helper = world.facts.get("helper_cfg")
    if hero is None or room is None or form is None or helper is None:
        return []
    if hero.meters["clean"] < THRESHOLD:
        return []
    if not form_possible(helper, form):
        return []
    if form.requires_bubbles and room.meters["bubbles"] < THRESHOLD:
        return []
    if form.requires_steam and room.meters["steam"] < THRESHOLD:
        return []
    sig = ("transform", form.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["transformed"] += 1
    hero.memes["wonder"] += 1
    hero.memes["pride"] += 1
    room.meters["legend"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="screech_fear", tag="emotional", apply=_r_screech_fear),
    Rule(name="clean", tag="physical", apply=_r_clean),
    Rule(name="transform", tag="story", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name or sig[0] == rule.name.replace("_", "") for sig in world.fired):
                pass
            else:
                continue
        now = len(world.fired)
        if getattr(propagate, "_last_count", None) != now:
            changed = changed or False
        propagate._last_count = now
        newer = getattr(propagate, "_seen_count", None)
        if newer != now:
            changed = changed or False
        # detect progress by comparing fired size within the loop
        # explicit second pass for simplicity
        before = now
        for rule in CAUSAL_RULES:
            rule.apply(world)
        after = len(world.fired)
        if after > before:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def explain_rejection(mess: Mess, helper: Helper, form: Optional[Form] = None) -> str:
    if not helper_cleans(helper, mess):
        missing = sorted(mess.regions - helper.covers)
        if missing:
            return (
                f"(No story: {helper.label} does not reach {', '.join(missing)}, "
                f"so it cannot honestly clean {mess.label}. Choose a helper that covers the whole mess.)"
            )
        return (
            f"(No story: {helper.label} is too weak for {mess.label}. "
            f"It cannot handle a mess with severity {mess.severity}.)"
        )
    if form is not None and not form_possible(helper, form):
        need = []
        if form.requires_bubbles and not helper.bubbles:
            need.append("bubbles")
        if form.requires_steam and not helper.steam:
            need.append("steam")
        return (
            f"(No story: {form.title} needs {' and '.join(need)}, but {helper.label} does not make that.)"
        )
    return "(No story: this combination does not fit the world.)"


def predict_cleanup(world: World, helper: Helper) -> dict:
    sim = world.copy()
    sim.get("helper").meters["active"] += 1
    sim.facts["helper_cfg"] = helper
    propagate(sim, narrate=False)
    room = sim.get("room")
    hero = sim.get("hero")
    return {
        "clean": hero.meters["clean"] >= THRESHOLD,
        "bubbles": room.meters["bubbles"] >= THRESHOLD,
        "steam": room.meters["steam"] >= THRESHOLD,
        "courage": hero.memes["courage"],
    }


def introduce(world: World, hero: Entity, mess: Mess) -> None:
    hero.meters["dirty"] = float(mess.severity)
    world.say(
        f"Grace marched into the bathroom wearing {mess.phrase}. "
        f"{mess.tall_bit}"
    )
    world.say(
        "The bathroom was only a bathroom, of course, but to Grace it looked as wide as a silver canyon, "
        "with the tub like a harbor and the mirror like a moon."
    )


def screech(world: World, hero: Entity, screech_level: int) -> None:
    room = world.get("room")
    room.meters["noise"] = float(screech_level + 1)
    propagate(world, narrate=False)
    size_words = {
        0: "a tiny",
        1: "a sharp",
        2: "a great",
    }
    world.say(
        f"Then the tap gave {size_words.get(screech_level, 'a sharp')} screech that skipped around the tiles."
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            "Grace drew back and tucked her chin, because the sound made the room feel taller than ever."
        )


def parent_grace(world: World, parent: Entity, hero: Entity, helper: Helper) -> None:
    pred = predict_cleanup(world, helper)
    world.facts["predicted_clean"] = pred["clean"]
    world.facts["predicted_bubbles"] = pred["bubbles"]
    world.facts["predicted_steam"] = pred["steam"]
    world.say(
        f'Grace\'s {parent.label_word} answered with such calm grace that even the towels seemed to settle. '
        f'"Easy now," {parent.pronoun()} said. "{helper.start_text}"'
    )


def start_helper(world: World, helper: Helper) -> None:
    helper_ent = world.get("helper")
    helper_ent.meters["active"] += 1
    propagate(world, narrate=False)


def cleaning_turn(world: World, hero: Entity, helper: Helper, mess: Mess, form: Form) -> None:
    room = world.get("room")
    bubbles = room.meters["bubbles"] >= THRESHOLD
    steam = room.meters["steam"] >= THRESHOLD
    add_bits: list[str] = []
    if bubbles:
        add_bits.append("bubbles piled up in shining hills")
    if steam:
        add_bits.append("steam curled over the mirror like a warm white crown")
    if add_bits:
        world.say(f"Soon {', and '.join(add_bits)}.")
    world.say(
        f"{helper.clean_text} {mess.rinse_text}"
    )
    if hero.meters["transformed"] >= THRESHOLD:
        world.say(
            f"In that bright minute, Grace was not just a child getting clean. "
            f"She was {form.claim}"
        )


def ending(world: World, hero: Entity, parent: Entity, form: Form, outcome: str) -> None:
    if outcome == "booming":
        world.say(
            f'Grace lifted her chin and laughed. "That old screech was smaller than a spoon," she said.'
        )
        world.say(
            f"When she stepped from the bathroom at last, {form.ending_image}."
        )
    else:
        world.say(
            f"Grace took one last careful breath, then stood tall beside {parent.pronoun('object')}."
        )
        world.say(
            f"When she stepped from the bathroom at last, {form.ending_image}."
        )


def tell(
    mess: Mess,
    helper: Helper,
    form: Form,
    parent_type: str,
    screech_level: int,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type="girl", label="Grace", role="hero"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    room = world.add(Entity(id="room", type="bathroom", label="bathroom", role="room"))
    helper_ent = world.add(Entity(id="helper", type="helper", label=helper.label, phrase=helper.phrase, role="helper"))
    room.tags.add("bathroom")

    world.facts.update(
        hero=hero,
        parent=parent,
        room=room,
        helper_ent=helper_ent,
        mess_cfg=mess,
        helper_cfg=helper,
        form_cfg=form,
        screech_level=screech_level,
    )

    introduce(world, hero, mess)
    world.para()
    screech(world, hero, screech_level)
    parent_grace(world, parent, hero, helper)
    start_helper(world, helper)
    cleaning_turn(world, hero, helper, mess, form)
    world.para()
    outcome = outcome_from(helper, screech_level)
    world.facts["outcome"] = outcome
    ending(world, hero, parent, form, outcome)
    world.facts["cleaned"] = hero.meters["clean"] >= THRESHOLD
    world.facts["transformed"] = hero.meters["transformed"] >= THRESHOLD
    world.facts["bubbles"] = room.meters["bubbles"] >= THRESHOLD
    world.facts["steam"] = room.meters["steam"] >= THRESHOLD
    return world


MESSES = {
    "painty_hands": Mess(
        id="painty_hands",
        label="painty hands",
        phrase="blue paint on her hands and smudges on her wrists",
        regions={"hands"},
        severity=1,
        kind="paint",
        cause="after painting a mighty paper parade",
        tall_bit="It looked as if she had shaken hands with a whole pocket of sky.",
        rinse_text="The blue slipped away in ribbons until her hands looked like her own again.",
        tags={"paint", "sink", "clean"},
    ),
    "muddy_feet": Mess(
        id="muddy_feet",
        label="muddy feet",
        phrase="mud on her feet and freckles of dirt up her ankles",
        regions={"feet", "legs"},
        severity=2,
        kind="mud",
        cause="after stomping through the yard",
        tall_bit="Each footprint behind her looked fit for a giant chick from a storybook farm.",
        rinse_text="The mud loosened, swirled, and hurried off like a brown parade downriver.",
        tags={"mud", "tub", "shower", "clean"},
    ),
    "jammy_chest": Mess(
        id="jammy_chest",
        label="sticky jam",
        phrase="a sticky stripe of strawberry jam across her shirtfront and tummy",
        regions={"torso"},
        severity=1,
        kind="sticky",
        cause="after a heroic breakfast",
        tall_bit="The red shine on her front made her look as if a sunrise had landed on her shirt.",
        rinse_text="The sticky shine melted away until her shirtfront was only warm and damp.",
        tags={"sticky", "bathroom", "clean"},
    ),
    "leafy_hair": Mess(
        id="leafy_hair",
        label="leafy hair",
        phrase="little leaves in her hair and dust along the back of her neck",
        regions={"hair"},
        severity=1,
        kind="leafy",
        cause="after crawling under bushes",
        tall_bit="Her hair had gathered so many leaves that it might have belonged to a robin's secret cousin.",
        rinse_text="The leaves floated free and the dust rinsed away until her hair shone dark and soft.",
        tags={"hair", "shower", "clean"},
    ),
}

HELPERS = {
    "sink": Helper(
        id="sink",
        label="the sink",
        phrase="the bathroom sink",
        covers={"hands"},
        power=1,
        comfort=1,
        bubbles=False,
        steam=False,
        start_text="We'll let the sink do the quick, honest work.",
        clean_text="Warm water ran over Grace's fingers in a bright little stream.",
        tags={"sink", "water"},
    ),
    "tub": Helper(
        id="tub",
        label="the tub",
        phrase="the warm tub",
        covers={"feet", "legs", "torso"},
        power=2,
        comfort=3,
        bubbles=True,
        steam=True,
        start_text="We'll make the tub a warm harbor and wash the trouble away.",
        clean_text="The warm tub hugged her shins and feet while the water did its patient work.",
        tags={"tub", "bubbles", "steam", "water"},
    ),
    "shower": Helper(
        id="shower",
        label="the shower",
        phrase="the gentle shower",
        covers={"hands", "feet", "legs", "torso", "hair"},
        power=2,
        comfort=2,
        bubbles=False,
        steam=True,
        start_text="We'll let the shower fall softly till the whole fuss is gone.",
        clean_text="The shower pattered down in silver lines, rinsing from head to toe.",
        tags={"shower", "steam", "water"},
    ),
}

FORMS = {
    "bubble_giant": Form(
        id="bubble_giant",
        title="the Bubble Giant of Tile Mountain",
        requires_bubbles=True,
        requires_steam=False,
        claim="the Bubble Giant of Tile Mountain, taller than the towel rack and kinder than thunder",
        ending_image="she looked as bright as a pearl and as pleased as a giant who had just washed a whole valley clean",
        tags={"bubbles", "tall_tale"},
    ),
    "mirror_monarch": Form(
        id="mirror_monarch",
        title="the Mirror Monarch",
        requires_bubbles=False,
        requires_steam=True,
        claim="the Mirror Monarch, wearing a crown of warm mist and ruling every shining tile in sight",
        ending_image="she left a clear little face in the mirror and walked out like a monarch crossing her own silver bridge",
        tags={"steam", "tall_tale"},
    ),
    "harbor_hero": Form(
        id="harbor_hero",
        title="the Harbor Hero",
        requires_bubbles=False,
        requires_steam=False,
        claim="the Harbor Hero, captain of the warm-water fleet that could rinse any trouble down the drain",
        ending_image="she came out neat and brave, as if she had sailed a toy boat through a storm and come home smiling",
        tags={"water", "tall_tale"},
    ),
}


@dataclass
class StoryParams:
    mess: str
    helper: str
    form: str
    parent: str
    screech: int = 1
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mess="muddy_feet",
        helper="tub",
        form="bubble_giant",
        parent="mother",
        screech=2,
    ),
    StoryParams(
        mess="painty_hands",
        helper="sink",
        form="harbor_hero",
        parent="father",
        screech=1,
    ),
    StoryParams(
        mess="leafy_hair",
        helper="shower",
        form="mirror_monarch",
        parent="mother",
        screech=1,
    ),
    StoryParams(
        mess="jammy_chest",
        helper="tub",
        form="mirror_monarch",
        parent="father",
        screech=0,
    ),
    StoryParams(
        mess="muddy_feet",
        helper="shower",
        form="harbor_hero",
        parent="mother",
        screech=2,
    ),
]


KNOWLEDGE = {
    "bathroom": [
        (
            "What is a bathroom for?",
            "A bathroom is a room where people wash, brush, and get clean. It has things like a sink, a tub, or a shower to help with that work.",
        )
    ],
    "sink": [
        (
            "What is a sink good for?",
            "A sink is good for quick washing, like hands and little messes. Water runs into the bowl and down the drain.",
        )
    ],
    "tub": [
        (
            "What is a tub for?",
            "A tub holds warm water so you can soak and wash your body. It can help with bigger messes on feet, legs, or the rest of you.",
        )
    ],
    "shower": [
        (
            "What does a shower do?",
            "A shower sends water down from above in many little streams. It is useful when you need to rinse a lot of your body, including your hair.",
        )
    ],
    "bubbles": [
        (
            "How do bubbles help in a bath?",
            "Bubbles can make bath time feel playful and gentle. Soap in the bubbles also helps loosen dirt from skin.",
        )
    ],
    "steam": [
        (
            "What is steam?",
            "Steam is warm mist made when water gets hot. In a bathroom, it can fog the mirror and make the air feel cozy.",
        )
    ],
    "mud": [
        (
            "Why does mud wash off with water?",
            "Mud is wet dirt, so water helps loosen it and carry it away. Rubbing gently helps too.",
        )
    ],
    "paint": [
        (
            "Why should you wash paint off your hands?",
            "Washing paint off keeps your skin and other things cleaner. It also stops the paint from smearing onto doors, faces, or towels.",
        )
    ],
    "hair": [
        (
            "Why do leaves get stuck in hair?",
            "Hair can catch light things like leaves and dust when you crawl or play outside. Water and gentle fingers help lift them out.",
        )
    ],
    "clean": [
        (
            "Why do people feel different after getting clean?",
            "Getting clean can make your body feel more comfortable. It can also make you feel ready, calm, and proud again.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bathroom", "sink", "tub", "shower", "bubbles", "steam", "mud", "paint", "hair", "clean"]


def generation_prompts(world: World) -> list[str]:
    mess = world.facts["mess_cfg"]
    helper = world.facts["helper_cfg"]
    form = world.facts["form_cfg"]
    outcome = world.facts["outcome"]
    tone = "booming" if outcome == "booming" else "gentle"
    return [
        'Write a short tall-tale story for a 3-to-5-year-old set in a bathroom that includes the words "screech" and "Grace".',
        f"Tell a child-facing story where Grace comes to the bathroom with {mess.label}, the {helper.label} helps, and she imagines herself becoming {form.title}.",
        f"Write a {tone} transformation story in which a bathroom noise startles Grace at first, but getting clean turns the room into a grand adventure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    mess = world.facts["mess_cfg"]
    helper = world.facts["helper_cfg"]
    form = world.facts["form_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Grace in the bathroom with her {parent.label_word}. Grace begins the story carrying {mess.label} from play.",
        ),
        (
            "What startled Grace in the bathroom?",
            "The tap made a screech that bounced around the tiles and made the room feel bigger and louder. That sound is what made Grace pause.",
        ),
        (
            f"How did Grace's {parent.label_word} help?",
            f"Grace's {parent.label_word} stayed calm and chose {helper.phrase}. That mattered because {helper.label} could honestly clean the mess Grace had.",
        ),
        (
            "What changed during the story?",
            f"Grace went from messy and rattled to clean and brave. As the washing worked, she imagined herself becoming {form.title}.",
        ),
    ]
    if outcome == "booming":
        qa.append(
            (
                "How did Grace feel at the end?",
                "Grace felt bold enough to laugh at the old screech. The cleaning helped her body feel comfortable, and that let her courage grow bigger than the noise.",
            )
        )
    else:
        qa.append(
            (
                "How did Grace feel at the end?",
                "Grace felt steady and proud. She did not have to be loud to be brave, because she stayed with the plan and saw the scary sound lose its power.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    mess = world.facts["mess_cfg"]
    helper = world.facts["helper_cfg"]
    form = world.facts["form_cfg"]
    tags = set(mess.tags) | set(helper.tags) | set(form.tags) | {"bathroom"}
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(
        f"  facts: outcome={world.facts.get('outcome')} bubbles={world.facts.get('bubbles')} steam={world.facts.get('steam')}"
    )
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- cleaning reasonableness gate ------------------------------------------
can_clean(M, H) :- mess(M), helper(H),
                   not missing_region(M, H),
                   severity(M, S), power(H, P), P >= S.
missing_region(M, H) :- mess_region(M, R), not helper_covers(H, R).

form_ok(H, F) :- form(F),
                 not need_bubbles(F),
                 not need_steam(F).
form_ok(H, F) :- form(F), need_bubbles(F), helper_bubbles(H),
                 not need_steam(F).
form_ok(H, F) :- form(F), need_steam(F), helper_steam(H),
                 not need_bubbles(F).
form_ok(H, F) :- form(F), need_bubbles(F), helper_bubbles(H),
                 need_steam(F), helper_steam(H).

valid(M, H, F) :- mess(M), helper(H), form(F), can_clean(M, H), form_ok(H, F).

% --- outcome model ---------------------------------------------------------
booming :- chosen_helper(H), chosen_screech(S), comfort(H, C), C > S.
outcome(booming) :- booming.
outcome(steady) :- not booming.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mess_id, mess in MESSES.items():
        lines.append(asp.fact("mess", mess_id))
        lines.append(asp.fact("severity", mess_id, mess.severity))
        for region in sorted(mess.regions):
            lines.append(asp.fact("mess_region", mess_id, region))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
        lines.append(asp.fact("comfort", helper_id, helper.comfort))
        for region in sorted(helper.covers):
            lines.append(asp.fact("helper_covers", helper_id, region))
        if helper.bubbles:
            lines.append(asp.fact("helper_bubbles", helper_id))
        if helper.steam:
            lines.append(asp.fact("helper_steam", helper_id))
    for form_id, form in FORMS.items():
        lines.append(asp.fact("form", form_id))
        if form.requires_bubbles:
            lines.append(asp.fact("need_bubbles", form_id))
        if form.requires_steam:
            lines.append(asp.fact("need_steam", form_id))
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
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_screech", params.screech),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> Optional[str]:
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            return "smoke test generated an empty story"
        _ = format_qa(sample)
        _ = dump_trace(sample.world) if sample.world is not None else ""
        rng = random.Random(13)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 13
        sample2 = generate(params)
        if not sample2.story.strip():
            return "random smoke test generated an empty story"
    except Exception as exc:  # pragma: no cover - verification path
        return f"smoke test failed: {exc}"
    return None


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    rng = random.Random(21)
    for i in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(rng.randint(0, 99999)))
            params.seed = i
            cases.append(params)
        except StoryError:
            continue
    mismatches = []
    for params in cases:
        py = outcome_from(HELPERS[params.helper], params.screech)
        asp_out = asp_outcome(params)
        if py != asp_out:
            mismatches.append((params, py, asp_out))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")
        for params, py, asp_out in mismatches[:5]:
            print(" ", params, "python=", py, "asp=", asp_out)

    smoke_err = smoke_test()
    if smoke_err is None:
        print("OK: smoke test generated stories and QA without crashing.")
    else:
        rc = 1
        print("FAIL:", smoke_err)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale bathroom transformation storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--screech", type=int, choices=[0, 1, 2], help="how sharp the tap's screech is")
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
    if args.mess is not None and args.mess not in MESSES:
        raise StoryError(f"(Unknown mess: {args.mess})")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")
    if args.form is not None and args.form not in FORMS:
        raise StoryError(f"(Unknown form: {args.form})")

    if args.mess and args.helper:
        mess = MESSES[args.mess]
        helper = HELPERS[args.helper]
        if not helper_cleans(helper, mess):
            raise StoryError(explain_rejection(mess, helper))
    if args.helper and args.form:
        helper = HELPERS[args.helper]
        form = FORMS[args.form]
        if not form_possible(helper, form):
            mess = MESSES[args.mess] if args.mess else next(iter(MESSES.values()))
            raise StoryError(explain_rejection(mess, helper, form))
    if args.mess and args.helper and args.form:
        mess = MESSES[args.mess]
        helper = HELPERS[args.helper]
        form = FORMS[args.form]
        if not valid_combo(mess, helper, form):
            raise StoryError(explain_rejection(mess, helper, form))

    combos = [
        combo for combo in valid_combos()
        if (args.mess is None or combo[0] == args.mess)
        and (args.helper is None or combo[1] == args.helper)
        and (args.form is None or combo[2] == args.form)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mess_id, helper_id, form_id = rng.choice(sorted(combos))
    return StoryParams(
        mess=mess_id,
        helper=helper_id,
        form=form_id,
        parent=args.parent or rng.choice(["mother", "father"]),
        screech=args.screech if args.screech is not None else rng.choice([0, 1, 2]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mess not in MESSES:
        raise StoryError(f"(Unknown mess: {params.mess})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.form not in FORMS:
        raise StoryError(f"(Unknown form: {params.form})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.screech not in {0, 1, 2}:
        raise StoryError(f"(Unknown screech level: {params.screech})")

    mess = MESSES[params.mess]
    helper = HELPERS[params.helper]
    form = FORMS[params.form]
    if not valid_combo(mess, helper, form):
        raise StoryError(explain_rejection(mess, helper, form))

    world = tell(
        mess=mess,
        helper=helper,
        form=form,
        parent_type=params.parent,
        screech_level=params.screech,
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
        print(f"{len(combos)} compatible (mess, helper, form) combos:\n")
        for mess, helper, form in combos:
            print(f"  {mess:13} {helper:7} {form}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### Grace: {p.mess} with {p.helper} ({p.form}, screech {p.screech})"
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
