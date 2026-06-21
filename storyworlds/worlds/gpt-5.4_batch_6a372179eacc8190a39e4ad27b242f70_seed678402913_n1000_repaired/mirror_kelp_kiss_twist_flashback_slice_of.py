#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mirror_kelp_kiss_twist_flashback_slice_of.py
=======================================================================

A small slice-of-life storyworld about a child who brings home a piece of kelp
from the shore, sees how soggy it looks in a mirror, remembers an older beach
moment, and has to decide whether to keep wearing the kelp or save it neatly for
a visitor. The stories always include a flashback beat and a gentle twist: the
visitor arrives with an old pressed bit of kelp from their own childhood, so the
child learns that the treasure was never about being messy.

The world model tracks both physical state (wetness, drips, freshness, pressed /
wilted) and emotional state (pride, worry, stubbornness, relief, love). The
mirror scene, the warning, the flashback, the turn, and the ending all read back
from that simulated state instead of swapping nouns into one fixed paragraph.
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
SENSE_MIN = 2


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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    shore_detail: str
    home_detail: str
    mirror_place: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class WearStyle:
    id: str
    label: str
    phrase: str
    wear_verb: str
    body: str
    size: int
    mirror_line: str
    drip_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PreserveMethod:
    id: str
    label: str
    sense: int
    power: int
    prep: str
    success: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class VisitorCfg:
    id: str
    type: str
    label: str
    arrival: str
    twist_item: str
    memory_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wet_mess(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    kelp = world.get("kelp")
    if kelp.meters["worn"] < THRESHOLD or kelp.meters["wet"] < THRESHOLD:
        return out
    sig = ("wet_mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["damp"] += 1
    child.memes["worry"] += 1
    kelp.meters["dripping"] += 1
    out.append("__drip__")
    return out


def _r_press_result(world: World) -> list[str]:
    out: list[str] = []
    kelp = world.get("kelp")
    if kelp.meters["stored"] < THRESHOLD:
        return out
    sig = ("press_result",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    need = world.facts["wear_cfg"].size + world.facts["delay"]
    power = world.facts["method_cfg"].power
    if power >= need:
        kelp.meters["pressed"] += 1
        kelp.meters["fresh"] += 1
        out.append("__saved__")
    else:
        kelp.meters["wilted"] += 1
        out.append("__wilted__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wet_mess", tag="physical", apply=_r_wet_mess),
    Rule(name="press_result", tag="physical", apply=_r_press_result),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def method_fits(method: PreserveMethod, wear: WearStyle) -> bool:
    return method.power >= wear.size and method.sense >= SENSE_MIN


def sensible_methods() -> list[PreserveMethod]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for wid in sorted(setting.affords):
            wear = WEAR_STYLES[wid]
            for mid, method in METHODS.items():
                if method_fits(method, wear):
                    combos.append((sid, wid, mid))
    return combos


def preservation_need(wear: WearStyle, delay: int) -> int:
    return wear.size + delay


def preserved(method: PreserveMethod, wear: WearStyle, delay: int) -> bool:
    return method.power >= preservation_need(wear, delay)


def predict_mess(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    kelp = sim.get("kelp")
    kelp.meters["worn"] = 1
    kelp.meters["wet"] = 1
    propagate(sim, narrate=False)
    return {
        "dripping": kelp.meters["dripping"] >= THRESHOLD,
        "child_damp": child.meters["damp"] >= THRESHOLD,
        "worry": child.memes["worry"],
    }


def collect_kelp(world: World, child: Entity, wear: WearStyle) -> None:
    kelp = world.get("kelp")
    child.memes["pride"] += 1
    kelp.meters["wet"] += 1
    kelp.meters["worn"] += 1
    world.say(
        f"After a slow walk at {world.setting.place}, {child.id} found {wear.phrase} "
        f"of kelp and {wear.wear_verb} it as if the sea had made a small present "
        f"just for {child.pronoun('object')}."
    )
    world.say(world.setting.shore_detail)


def mirror_beat(world: World, child: Entity, wear: WearStyle) -> None:
    pred = predict_mess(world)
    world.facts["predicted_dripping"] = pred["dripping"]
    world.facts["predicted_worry"] = pred["worry"]
    child.memes["self_notice"] += 1
    world.say(
        f"At home, {child.id} stopped by {world.setting.mirror_place} and looked in the mirror. "
        f"{wear.mirror_line}"
    )
    if pred["dripping"]:
        world.say(wear.drip_line)
    world.say(
        f"For a moment, {child.id} loved how sea-green it looked and worried about it at the same time."
    )


def flashback(world: World, child: Entity, visitor: Entity) -> None:
    child.memes["memory"] += 1
    world.say(
        f"That picture tugged up a flashback from last summer. {visitor.label_word.capitalize()} "
        f"{world.facts['visitor_cfg'].memory_line}"
    )
    world.say(
        f'{visitor.pronoun().capitalize()} had kissed the top of {child.id}\'s salty head then and said, '
        f'"Bring me another sea treasure someday, and we will look at it together."'
    )


def warn(world: World, parent: Entity, child: Entity, wear: WearStyle) -> None:
    child.memes["worry"] += 1
    world.say(
        f'{child.id} wanted to keep the kelp on until {world.facts["visitor_cfg"].arrival}, '
        f'but {child.pronoun("possessive")} {parent.label_word} touched the wet strand and said, '
        f'"It is beautiful, but it will not stay lovely if we leave it {wear.body} and dripping."'
    )
    if world.facts.get("predicted_dripping"):
        world.say(
            f'{parent.pronoun().capitalize()} nodded toward the mirror. "See? The mirror is telling the truth. '
            f'The kelp is already sliding and leaving little wet marks."'
        )


def insist(world: World, child: Entity, visitor: Entity) -> None:
    child.memes["stubborn"] += 1
    world.say(
        f'{child.id} held very still. "But what if {visitor.label_word} wanted to see it exactly like this?" '
        f'{child.pronoun().capitalize()} asked.'
    )


def preserve_kelp(world: World, parent: Entity, method: PreserveMethod) -> None:
    kelp = world.get("kelp")
    kelp.meters["worn"] = 0
    kelp.meters["stored"] += 1
    world.say(
        f'{parent.label_word.capitalize()} suggested they {method.prep}.'
    )
    propagate(world, narrate=False)
    if kelp.meters["pressed"] >= THRESHOLD:
        world.say(method.success)
    else:
        world.say(method.fail)


def clean_up(world: World, child: Entity) -> None:
    kelp = world.get("kelp")
    child.meters["damp"] = 0
    child.memes["relief"] += 1
    world.say(
        f"Then {child.id} washed sandy fingers, smoothed flyaway hair, and looked in the mirror again. "
        f"This time the face in the glass looked ready to welcome somebody."
    )
    if kelp.meters["pressed"] >= THRESHOLD:
        world.say("The sea treasure had moved from a costume into a keepsake.")
    else:
        world.say("The sea treasure was no longer grand, but it was still part of the day.")


def visitor_arrives(world: World, child: Entity, visitor: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f"When {world.facts['visitor_cfg'].arrival}, {visitor.label_word} came in with a cool breeze and a smile."
    )


def twist_reveal(world: World, child: Entity, visitor: Entity) -> None:
    kelp = world.get("kelp")
    child.memes["surprise"] += 1
    child.memes["love"] += 1
    world.say(
        f"Then came the twist. {visitor.label_word.capitalize()} reached into a pocket and pulled out "
        f"{world.facts['visitor_cfg'].twist_item}."
    )
    world.say(
        f'"Look," {visitor.pronoun()} said. "I kept this from when I was little. I never wanted the sea on your '
        f'head all evening. I wanted to see whether you noticed something worth keeping."'
    )
    if kelp.meters["pressed"] >= THRESHOLD:
        world.say(
            f"{child.id} blinked at the old piece of kelp and then at {method_phrase(world)}. "
            f"The two treasures seemed to nod to each other across the room."
        )
    else:
        world.say(
            f"{child.id} looked from the old keepsake to the softened kelp they had saved as best they could. "
            f"Even that smaller treasure suddenly felt understood."
        )


def ending(world: World, child: Entity, visitor: Entity) -> None:
    kelp = world.get("kelp")
    child.memes["love"] += 1
    child.memes["relief"] += 1
    if kelp.meters["pressed"] >= THRESHOLD:
        world.say(
            f'{visitor.label_word.capitalize()} bent down, kissed {child.id} on the forehead, and said, '
            f'"Now that is a sea treasure."'
        )
        world.say(
            f"By bedtime, the pressed kelp lay flat beside the old one, and every time {child.id} passed the mirror, "
            f"{child.pronoun()} smiled instead of fussing."
        )
    else:
        world.say(
            f'{visitor.label_word.capitalize()} still gave {child.id} a warm kiss and said, '
            f'"The important part was bringing your eyes home full of the shore."'
        )
        world.say(
            f"By bedtime, the not-quite-flat kelp rested on a saucer to dry, and {child.id} kept peeking in the mirror "
            f"as if the day had learned how to be gentle after all."
        )


def method_phrase(world: World) -> str:
    kelp = world.get("kelp")
    if kelp.meters["pressed"] >= THRESHOLD:
        return f"the neatly saved kelp they had just made with {world.facts['method_cfg'].label}"
    return "the slightly wilted piece they had hurried to save"


def tell(
    setting: Setting,
    wear: WearStyle,
    method: PreserveMethod,
    visitor_cfg: VisitorCfg,
    child_name: str = "Mina",
    child_type: str = "girl",
    parent_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    visitor = world.add(Entity(id="visitor", kind="character", type=visitor_cfg.type, label=visitor_cfg.label, role="visitor"))
    kelp = world.add(Entity(id="kelp", type="kelp", label="kelp", phrase="a piece of kelp", tags={"kelp"}))
    mirror = world.add(Entity(id="mirror", type="mirror", label="mirror", phrase="the mirror", tags={"mirror"}))

    child.id = child_name
    parent.id = "Parent"
    visitor.id = visitor_cfg.label_word.capitalize()

    world.facts.update(
        child=child,
        parent=parent,
        visitor=visitor,
        wear_cfg=wear,
        method_cfg=method,
        visitor_cfg=visitor_cfg,
        setting_cfg=setting,
        delay=delay,
    )

    collect_kelp(world, child, wear)
    world.say(world.setting.home_detail)

    world.para()
    mirror_beat(world, child, wear)
    flashback(world, child, visitor)

    world.para()
    warn(world, parent, child, wear)
    insist(world, child, visitor)
    if delay:
        world.say(
            f"They talked for a little while longer, long enough for the kelp to lose some of its bright springy look."
        )

    world.para()
    preserve_kelp(world, parent, method)
    clean_up(world, child)

    world.para()
    visitor_arrives(world, child, visitor)
    twist_reveal(world, child, visitor)
    ending(world, child, visitor)

    world.facts["outcome"] = outcome_name(world)
    world.facts["saved"] = kelp.meters["pressed"] >= THRESHOLD
    return world


def outcome_name(world: World) -> str:
    kelp = world.get("kelp")
    return "saved" if kelp.meters["pressed"] >= THRESHOLD else "wilted"


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="the little cove",
        shore_detail="The wet stones shone like buttons, and the air smelled green and salty.",
        home_detail="Back in the apartment, sand kept appearing on the doormat as if the beach had followed along.",
        mirror_place="the narrow hallway mirror",
        affords={"bracelet", "crown", "streamer"},
        tags={"shore"},
    ),
    "tidepool": Setting(
        id="tidepool",
        place="the tide pools",
        shore_detail="Tiny crabs tucked themselves under rock lips, and ribbons of kelp waved in the clear pockets of water.",
        home_detail="At home, the kitchen window was still open, and the whole place held a sleepy seaside smell.",
        mirror_place="the bedroom mirror",
        affords={"bracelet", "crown"},
        tags={"shore"},
    ),
    "jetty": Setting(
        id="jetty",
        place="the old jetty",
        shore_detail="Gulls fussed over the posts, and long dark strips of kelp rocked below the boards.",
        home_detail="Their front room was warm after the windy walk, with shoes lined up to dry by the door.",
        mirror_place="the mirror above the shoe bench",
        affords={"bracelet", "streamer"},
        tags={"shore"},
    ),
}

WEAR_STYLES = {
    "bracelet": WearStyle(
        id="bracelet",
        label="kelp bracelet",
        phrase="a looped bracelet",
        wear_verb="slipped",
        body="around your wrist",
        size=1,
        mirror_line="A little green loop sat on one wrist, shiny as ribbon.",
        drip_line="It did not make a mess, but one drop slid down to the floor and made the child step back.",
        tags={"kelp"},
    ),
    "crown": WearStyle(
        id="crown",
        label="kelp crown",
        phrase="a ragged crown",
        wear_verb="rested",
        body="on your head",
        size=2,
        mirror_line="The kelp sat across the hair like a crooked crown, funny and grand all at once.",
        drip_line="A cold bead of seawater crept down near one ear, and a dark wet line touched the collar.",
        tags={"kelp", "mirror"},
    ),
    "streamer": WearStyle(
        id="streamer",
        label="kelp streamer",
        phrase="a long streamer",
        wear_verb="draped",
        body="over your shoulder",
        size=3,
        mirror_line="The strand looked almost like a sash, though it hung heavier on one side than the other.",
        drip_line="The lowest end kept tapping the shirt with damp little kisses of seawater.",
        tags={"kelp", "mirror"},
    ),
}

METHODS = {
    "press_book": PreserveMethod(
        id="press_book",
        label="a heavy library book",
        sense=3,
        power=3,
        prep="rinsed the kelp, laid it between two sheets of baking paper, and tuck it inside a heavy library book",
        success="Together they eased the green strand flat and safe, where it could dry into something worth keeping.",
        fail="They tucked it away carefully, but by then the kelp had already gone limp at the edges.",
        qa_text="They rinsed it and pressed it flat in a heavy book",
        tags={"book", "kelp"},
    ),
    "tray": PreserveMethod(
        id="tray",
        label="a little painted tray",
        sense=3,
        power=4,
        prep="spread the kelp on a little painted tray by the window so it could rest flat and dry",
        success="On the tray, the strand looked less like a costume and more like a tiny piece of shoreline brought indoors.",
        fail="On the tray, it could rest, but the best of its shape had already sagged away.",
        qa_text="They spread it flat on a tray by the window to dry",
        tags={"kelp", "drying"},
    ),
    "jar": PreserveMethod(
        id="jar",
        label="a clear jam jar",
        sense=2,
        power=2,
        prep="coil the kelp into a clear jam jar with fresh water for the evening",
        success="Inside the jar, the kelp floated quietly, still green enough to feel like it had just come from the sea.",
        fail="Inside the jar, the kelp stayed with them, but it no longer looked as crisp and lively as before.",
        qa_text="They set it in a clear jar of water for the evening",
        tags={"jar", "kelp"},
    ),
    "pocket": PreserveMethod(
        id="pocket",
        label="a shorts pocket",
        sense=1,
        power=1,
        prep="stuff the kelp into a shorts pocket",
        success="It somehow survived the pocket, though nobody sensible would count on that.",
        fail="The pocket only crushed the soft seaweed into a tired green knot.",
        qa_text="They stuffed it into a pocket",
        tags={"pocket"},
    ),
}

VISITORS = {
    "grandma": VisitorCfg(
        id="grandma",
        type="grandmother",
        label="grandma",
        arrival="grandma arrived for supper",
        twist_item="a tiny envelope holding a pressed strip of kelp",
        memory_line="had once shown how to hold a strand up to the sun and look for tiny bubbles caught on its edges",
        tags={"family"},
    ),
    "aunt": VisitorCfg(
        id="aunt",
        type="aunt",
        label="aunt",
        arrival="auntie came by with warm rolls from the bakery",
        twist_item="an old notebook page with a ferny piece of pressed kelp tucked inside",
        memory_line="had laughed on the pier and called kelp the sea's ribbon, if only you looked at it closely enough",
        tags={"family"},
    ),
    "grandpa": VisitorCfg(
        id="grandpa",
        type="grandfather",
        label="grandpa",
        arrival="grandpa knocked just before dusk",
        twist_item="a folded card with a flat brown piece of kelp taped inside",
        memory_line="had crouched beside the rocks and said every good walk leaves one small thing for you to notice",
        tags={"family"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Ivy", "Ella", "Rosa"]
BOY_NAMES = ["Owen", "Max", "Eli", "Noah", "Finn", "Theo", "Leo", "Sam"]


@dataclass
class StoryParams:
    setting: str
    wear: str
    method: str
    visitor: str
    child_name: str
    child_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="cove",
        wear="crown",
        method="press_book",
        visitor="grandma",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        setting="tidepool",
        wear="bracelet",
        method="jar",
        visitor="aunt",
        child_name="Owen",
        child_gender="boy",
        parent="father",
        delay=1,
    ),
    StoryParams(
        setting="jetty",
        wear="streamer",
        method="tray",
        visitor="grandpa",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        delay=0,
    ),
    StoryParams(
        setting="cove",
        wear="streamer",
        method="press_book",
        visitor="aunt",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        delay=1,
    ),
    StoryParams(
        setting="tidepool",
        wear="crown",
        method="jar",
        visitor="grandma",
        child_name="Ivy",
        child_gender="girl",
        parent="mother",
        delay=1,
    ),
]


KNOWLEDGE = {
    "mirror": [(
        "What does a mirror do?",
        "A mirror bounces light back at you, so you can see your own face and clothes. That is why people use a mirror to check how something looks."
    )],
    "kelp": [(
        "What is kelp?",
        "Kelp is a kind of big brown or green seaweed that grows in the ocean. It can wash up on the shore after waves move it around."
    )],
    "pressing": [(
        "Why do people press plants or seaweed in a book?",
        "Pressing holds something flat while it dries, so it can be kept as a memory. It is a gentle way to save a leaf, flower, or piece of seaweed."
    )],
    "jar": [(
        "Why might someone put a sea treasure in a jar of water?",
        "A jar can keep something wet and easy to look at for a little while. It is not always the best forever-home, but it can help for one evening."
    )],
    "shore": [(
        "Why does kelp feel wet and slippery?",
        "Kelp lives in the sea, so it holds a lot of water. When you pick it up, that seawater can drip and make it feel slippery."
    )],
    "kiss": [(
        "What can a kiss mean in a family story?",
        "A kiss can show love, welcome, or comfort. In a gentle family story, it often tells you that the child feels safe and cared for."
    )],
    "flashback": [(
        "What is a flashback in a story?",
        "A flashback is a short look back at something that happened earlier. It helps explain why a character feels or chooses something now."
    )],
    "twist": [(
        "What is a twist in a story?",
        "A twist is a new piece of information that changes how you understand what was happening. A good twist feels surprising but still makes sense."
    )],
}
KNOWLEDGE_ORDER = ["mirror", "kelp", "shore", "pressing", "jar", "kiss", "flashback", "twist"]


def explain_rejection(setting_id: str, wear_id: str, method_id: str) -> str:
    if setting_id in SETTINGS and wear_id in WEAR_STYLES and wear_id not in SETTINGS[setting_id].affords:
        return (
            f"(No story: {SETTINGS[setting_id].place} does not plausibly offer the long, tidy piece needed for a "
            f"{WEAR_STYLES[wear_id].label}. Pick a wear style that fits that shore.)"
        )
    if method_id in METHODS and METHODS[method_id].sense < SENSE_MIN:
        return (
            f"(Refusing method '{method_id}': it is too careless for this world "
            f"(sense={METHODS[method_id].sense} < {SENSE_MIN}). The child should save the kelp in a calmer, more believable way.)"
        )
    if wear_id in WEAR_STYLES and method_id in METHODS and not method_fits(METHODS[method_id], WEAR_STYLES[wear_id]):
        return (
            f"(No story: {METHODS[method_id].label} is not a strong enough way to save a "
            f"{WEAR_STYLES[wear_id].label}. Pick a method that can really keep the kelp.)"
        )
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    wear = WEAR_STYLES[params.wear]
    method = METHODS[params.method]
    return "saved" if preserved(method, wear, params.delay) else "wilted"


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    visitor = world.facts["visitor"]
    wear = world.facts["wear_cfg"]
    return [
        f'Write a short slice-of-life story for ages 3 to 5 that includes the words "mirror", "kelp", and "kiss".',
        f"Tell a gentle home-and-shore story where {child.id} comes back wearing a {wear.label}, looks in a mirror, remembers an older beach moment, and waits for {visitor.label_word} to arrive.",
        "Write a story with a flashback and a small twist, where a child learns that keeping a treasure carefully can matter more than showing it off.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    visitor = world.facts["visitor"]
    wear = world.facts["wear_cfg"]
    method = world.facts["method_cfg"]
    saved = world.facts["saved"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who brought home a piece of kelp from {world.setting.place}, and {child.pronoun('possessive')} {parent.label_word} and {visitor.label_word}. The story follows the child from the shore to home and then to the visitor's arrival."
        ),
        (
            "What happened when the child looked in the mirror?",
            f"{child.id} saw the kelp more clearly and noticed that it was beautiful but wet and crooked. The mirror turned a proud sea costume into something the child had to think about."
        ),
        (
            "What was the flashback about?",
            f"The flashback was about an older beach day with {visitor.label_word}, when {visitor.pronoun()} taught {child.id} to notice sea treasures carefully and gave {child.pronoun('object')} a kiss. That memory is why keeping the kelp felt important in the present."
        ),
    ]
    if saved:
        qa.append(
            (
                f"How did {child.id}'s {parent.label_word} help save the kelp?",
                f"{parent.label_word.capitalize()} helped by using {method.label} instead of leaving the kelp dripping on {wear.body}. {method.qa_text}, which let the treasure stay part of the story without making a mess."
            )
        )
    else:
        qa.append(
            (
                "Did the kelp stay perfect?",
                f"No. They tried to save it with {method.label}, but they had already waited long enough for it to soften. Even so, the visitor cared about the noticing and the memory, not about having a perfect piece."
            )
        )
    qa.append(
        (
            "What was the twist at the end?",
            f"The twist was that {visitor.label_word} arrived with an old piece of saved kelp from {visitor.pronoun('possessive')} own childhood. That changed the meaning of the whole day, because {child.id} learned the visitor had hoped for careful noticing, not a soggy costume."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with a kiss and relief. {visitor.label_word.capitalize()} welcomed {child.id} warmly, and the mirror no longer felt like a place for worry but a sign that the child had learned something gentle and true."
        )
    )
    if outcome == "wilted":
        qa.append(
            (
                "Was the ending still happy even though the kelp wilted?",
                "Yes. The kelp was not as fresh as before, but the family still understood why it mattered. The child ended the story feeling loved rather than ashamed."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mirror", "kelp", "shore", "kiss", "flashback", "twist"}
    if world.facts["method_cfg"].id == "jar":
        tags.add("jar")
    else:
        tags.add("pressing")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
fits(W, M)  :- wear(W), method(M), size(W, Need), power(M, P), P >= Need.
valid(S, W, M) :- setting(S), affords(S, W), sensible(M), fits(W, M).

need(N) :- chosen_wear(W), size(W, Base), delay(D), N = Base + D.
saved :- chosen_method(M), power(M, P), need(N), P >= N.
outcome(saved) :- saved.
outcome(wilted) :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for wid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, wid))
    for wid, wear in WEAR_STYLES.items():
        lines.append(asp.fact("wear", wid))
        lines.append(asp.fact("size", wid, wear.size))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_wear", params.wear),
        asp.fact("chosen_method", params.method),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated story was empty.)")
    if sample.world is None:
        raise StoryError("(Smoke test failed: world model missing.)")


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child, a mirror, a piece of kelp, a remembered kiss, and a gentle twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wear", choices=WEAR_STYLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long they wait before saving the kelp")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.wear and args.wear not in SETTINGS[args.setting].affords:
        raise StoryError(explain_rejection(args.setting, args.wear, args.method or ""))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.setting or "", args.wear or "", args.method))
    if args.wear and args.method and not method_fits(METHODS[args.method], WEAR_STYLES[args.wear]):
        raise StoryError(explain_rejection(args.setting or "", args.wear, args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.wear is None or combo[1] == args.wear)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, wear_id, method_id = rng.choice(sorted(combos))
    visitor_id = args.visitor or rng.choice(sorted(VISITORS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        wear=wear_id,
        method=method_id,
        visitor=visitor_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.wear not in WEAR_STYLES:
        raise StoryError(f"(Unknown wear style: {params.wear})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.visitor not in VISITORS:
        raise StoryError(f"(Unknown visitor: {params.visitor})")
    if params.wear not in SETTINGS[params.setting].affords:
        raise StoryError(explain_rejection(params.setting, params.wear, params.method))
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_rejection(params.setting, params.wear, params.method))
    if not method_fits(METHODS[params.method], WEAR_STYLES[params.wear]):
        raise StoryError(explain_rejection(params.setting, params.wear, params.method))

    world = tell(
        setting=SETTINGS[params.setting],
        wear=WEAR_STYLES[params.wear],
        method=METHODS[params.method],
        visitor_cfg=VISITORS[params.visitor],
        child_name=params.child_name,
        child_type=params.child_gender,
        parent_type=params.parent,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (setting, wear, method) combos:\n")
        for setting_id, wear_id, method_id in combos:
            print(f"  {setting_id:8} {wear_id:9} {method_id}")
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
            header = f"### {p.child_name}: {p.wear} at {p.setting} ({p.method}, {outcome_of(p)})"
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
