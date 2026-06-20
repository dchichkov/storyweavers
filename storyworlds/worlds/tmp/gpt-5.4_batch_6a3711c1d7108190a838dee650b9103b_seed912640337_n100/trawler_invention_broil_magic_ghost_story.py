#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trawler_invention_broil_magic_ghost_story.py
=======================================================================

A standalone story world for a gentle spooky tale about an old trawler, a magic
invention, and the dangerous temptation of the "broil" setting.

The domain:
-----------
A child visits a weathered harbor trawler with an inventive grandparent at dusk.
They are testing a small magic galley invention that should glow, hum, or warm
supper kindly when the right charm is tucked inside. If the dial is twisted to
broil, the invention overheats, and the trawler fills with ghostly steam and
fog. A friendly harbor ghost is startled awake. A sensible grown-up response can
calm the scare and mend the night; a weak response leaves everyone safe but
shaken on the dock until dawn.

Run it:
-------
    python storyworlds/worlds/gpt-5.4/trawler_invention_broil_magic_ghost_story.py
    python storyworlds/worlds/gpt-5.4/trawler_invention_broil_magic_ghost_story.py --heat broil
    python storyworlds/worlds/gpt-5.4/trawler_invention_broil_magic_ghost_story.py --invention moon_stove --charm brass_key
    python storyworlds/worlds/gpt-5.4/trawler_invention_broil_magic_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/trawler_invention_broil_magic_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/trawler_invention_broil_magic_ghost_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or any other working directory.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother"}
        male = {"boy", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Invention:
    id: str
    label: str
    phrase: str
    promise: str
    glow: str
    delicate: int
    good_heat: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    matches: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Heat:
    id: str
    label: str
    intensity: int
    spooky: bool
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
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


def _r_steam_spook(world: World) -> list[str]:
    out: list[str] = []
    inv = world.get("invention")
    ghost = world.get("ghost")
    child = world.get("child")
    boat = world.get("trawler")
    if inv.meters["overheat"] >= THRESHOLD:
        sig = ("steam_spook",)
        if sig not in world.fired:
            world.fired.add(sig)
            inv.meters["steam"] += 1
            ghost.memes["startled"] += 1
            boat.meters["fog"] += 1
            child.memes["fear"] += 1
            out.append("__spook__")
    return out


def _r_ghost_wail(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    boat = world.get("trawler")
    child = world.get("child")
    guardian = world.get("guardian")
    if ghost.memes["startled"] >= THRESHOLD:
        sig = ("ghost_wail",)
        if sig not in world.fired:
            world.fired.add(sig)
            boat.meters["drift_risk"] += 1
            child.memes["fear"] += 1
            guardian.memes["urgency"] += 1
            out.append("__wail__")
    return out


CAUSAL_RULES = [
    Rule("steam_spook", "physical", _r_steam_spook),
    Rule("ghost_wail", "social", _r_ghost_wail),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


INVENTIONS = {
    "moon_stove": Invention(
        "moon_stove",
        "moon stove",
        "a brass moon stove no bigger than a bread box",
        "warm fish pie and paint the galley with a pearly glow",
        "a soft round light, like a tiny moon trapped in a kettle",
        delicate=2,
        good_heat="warm",
        tags={"invention", "moon_stove"},
    ),
    "bell_boiler": Invention(
        "bell_boiler",
        "bell boiler",
        "a bell boiler with silver pipes and a shy little chimney",
        "heat cocoa while making the cabin ring with bright bell notes",
        "little silver chimes that trembled in the air",
        delicate=1,
        good_heat="glow",
        tags={"invention", "bell_boiler"},
    ),
    "gull_kettle": Invention(
        "gull_kettle",
        "gull kettle",
        "a gull kettle with a blue lid shaped like folded wings",
        "steam clam broth and call one clean lantern-bright cry over the harbor",
        "a ribbon of blue steam that curled like a feather",
        delicate=2,
        good_heat="warm",
        tags={"invention", "gull_kettle"},
    ),
}

CHARMS = {
    "moon_salt": Charm(
        "moon_salt",
        "moon salt",
        "a pinch of moon salt",
        matches={"moon_stove"},
        tags={"moon_salt", "magic"},
    ),
    "brass_key": Charm(
        "brass_key",
        "brass key",
        "a tiny brass key on a blue string",
        matches={"bell_boiler"},
        tags={"brass_key", "magic"},
    ),
    "gull_feather": Charm(
        "gull_feather",
        "gull feather",
        "a white gull feather wrapped in thread",
        matches={"gull_kettle"},
        tags={"gull_feather", "magic"},
    ),
}

HEATS = {
    "glow": Heat(
        "glow",
        "glow",
        0,
        False,
        'The dial clicked to glow, the gentlest mark on the little invention.',
        tags={"gentle_heat"},
    ),
    "warm": Heat(
        "warm",
        "warm",
        1,
        False,
        'The dial slid to warm, and the metal began to hum like a sleepy cat.',
        tags={"gentle_heat"},
    ),
    "broil": Heat(
        "broil",
        "broil",
        2,
        True,
        'The dial jumped to broil, the hottest word on the plate, and the metal answered at once.',
        tags={"broil"},
    ),
}

RESPONSES = {
    "cool_and_lower": Response(
        "cool_and_lower",
        3,
        4,
        "snatched up the seawater ladle, cooled the sides of the invention, and turned the dial down from broil to the proper gentle mark",
        "splashed a little seawater at the invention and reached for the dial, but the fog had already swollen thicker than soup",
        "cooled the invention with seawater and turned the dial down",
        tags={"seawater", "safe_fix"},
    ),
    "open_hatch_song": Response(
        "open_hatch_song",
        3,
        3,
        "threw open the hatch, let the hot breath roll out, and sang the harbor's old mooring song until the ghost's shiver eased",
        "opened the hatch and sang the mooring song, but the hot steam kept piling up inside the cabin",
        "opened the hatch and sang the mooring song to calm the ghost",
        tags={"song", "safe_fix"},
    ),
    "hide_in_net": Response(
        "hide_in_net",
        1,
        0,
        "ducked behind the net bins and waited",
        "hid behind the net bins while the fog grew thicker",
        "hid behind the net bins",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nell", "Tessa", "Ivy", "June", "Willa", "Cora"]
BOY_NAMES = ["Finn", "Theo", "Arlo", "Bram", "Nico", "Evan", "Milo", "Jude"]
TRAITS = ["careful", "curious", "bold", "thoughtful", "restless", "gentle"]


def charm_fits(invention: Invention, charm: Charm) -> bool:
    return invention.id in charm.matches


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for inv_id, inv in INVENTIONS.items():
        for ch_id, ch in CHARMS.items():
            if not charm_fits(inv, ch):
                continue
            for resp in sensible_responses():
                combos.append((inv_id, ch_id, resp.id))
    return combos


def spook_severity(invention: Invention, heat: Heat, delay: int) -> int:
    if not heat.spooky:
        return 0
    return invention.delicate + heat.intensity + delay


def is_mended(invention: Invention, heat: Heat, response: Response, delay: int) -> bool:
    if not heat.spooky:
        return True
    return response.power >= spook_severity(invention, heat, delay)


def outcome_of(params: "StoryParams") -> str:
    if not HEATS[params.heat].spooky:
        return "calm"
    return "mended" if is_mended(INVENTIONS[params.invention], HEATS[params.heat], RESPONSES[params.response], params.delay) else "adrift"


def explain_charm(invention: Invention, charm: Charm) -> str:
    wanted = ", ".join(sorted(ch.label for ch in CHARMS.values() if invention.id in ch.matches))
    return (
        f"(No story: {charm.label} does not wake {invention.label} the right way. "
        f"{invention.label.capitalize()} needs {wanted} so the magic has a sensible source.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def predict_spook(world: World, heat_id: str) -> dict:
    sim = world.copy()
    _set_heat(sim, HEATS[heat_id], narrate=False)
    ghost = sim.get("ghost")
    boat = sim.get("trawler")
    return {
        "ghost_startled": ghost.memes["startled"] >= THRESHOLD,
        "fog": boat.meters["fog"],
        "drift_risk": boat.meters["drift_risk"],
    }


def _set_heat(world: World, heat: Heat, narrate: bool = True) -> None:
    inv = world.get("invention")
    inv.attrs["heat"] = heat.id
    if heat.spooky:
        inv.meters["overheat"] += 1
        inv.meters["sizzle"] += 1
        propagate(world, narrate=narrate)
    else:
        inv.meters["working"] += 1
        inv.memes["content"] += 1
        world.get("ghost").memes["curious"] += 1


def harbor_setup(world: World, child: Entity, guardian: Entity, invention: Invention, charm: Charm) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"At dusk, {child.id} followed {child.pronoun('possessive')} {guardian.label_word} down the creaking pier to the old trawler, "
        f"where the gull ropes tapped the mast like small knuckles."
    )
    world.say(
        f"The trawler smelled of salt, iron, and supper. In the galley sat {invention.phrase}, "
        f"one of {guardian.label_word}'s newest inventions, and beside it lay {charm.phrase}."
    )
    world.say(
        f'"Tonight," {guardian.label_word} whispered, "we will see if it can {invention.promise}."'
    )


def tell_harbor_ghost(world: World, child: Entity, guardian: Entity) -> None:
    world.say(
        f"{child.id} had heard the harbor story before: a kind deckhand ghost still watched the trawler and liked quiet work better than noisy foolishness."
    )
    world.say(
        f'"If we are gentle," said {guardian.label_word}, "the old ghost only peeks and smiles."'
    )


def prepare_magic(world: World, child: Entity, guardian: Entity, invention: Invention, charm: Charm) -> None:
    world.get("invention").attrs["charm"] = charm.id
    child.memes["care"] += 1
    world.say(
        f"{child.id} tucked {charm.phrase} into the little chamber under the lid, and the metal gave one pleased silver shiver."
    )
    if invention.good_heat == "glow":
        advice = "glow"
    else:
        advice = "warm"
    world.say(
        f'"Now remember," said {guardian.label_word}, touching the dial, "this one likes {advice}. Never broil it on a damp night."'
    )


def choose_heat(world: World, child: Entity, heat: Heat) -> None:
    if heat.spooky:
        child.memes["impulse"] += 1
    else:
        child.memes["care"] += 1
    world.say(heat.line)


def gentle_success(world: World, child: Entity, guardian: Entity, invention: Invention, heat: Heat) -> None:
    inv = world.get("invention")
    ghost = world.get("ghost")
    child.memes["joy"] += 1
    child.memes["fear"] = 0.0
    ghost.memes["friendly"] += 1
    inv.meters["working"] += 1
    world.say(
        f"Instead of shrieking, the invention answered with {invention.glow}. The cabin light went tender and blue, and even the spoons stopped rattling."
    )
    world.say(
        "A pale shape lifted from the corner by the hanging nets. It was only a sailor's ghost, thin as mist and smiling under a cap of light."
    )
    world.say(
        f'"Good evening," {child.id} whispered. The ghost tipped his cap, and the trawler rocked as softly as a cradle.'
    )
    world.say(
        f"Soon the little meal was ready, the ropes were quiet, and {child.id} knew that magic behaved best when treated kindly."
    )


def ghost_broil(world: World, child: Entity, invention: Invention) -> None:
    inv = world.get("invention")
    ghost = world.get("ghost")
    boat = world.get("trawler")
    world.say(
        f"At once the {invention.label} hissed too hard. Hot steam burst from its seams, the cabin window whitened, and the old trawler seemed to suck in one long startled breath."
    )
    if ghost.memes["startled"] >= THRESHOLD:
        world.say(
            "Out of that steam rose a sailor-shaped ghost with lamp-bright eyes. He was not mean, but he was terribly alarmed, and his wail made the anchor chain shiver."
        )
    if boat.meters["fog"] >= THRESHOLD:
        world.say(
            f"{child.id}'s heart thumped. The fog inside the cabin curled like white fingers around the table legs."
        )
    inv.memes["trouble"] += 1


def mend_night(world: World, child: Entity, guardian: Entity, invention: Invention, response: Response) -> None:
    ghost = world.get("ghost")
    boat = world.get("trawler")
    inv = world.get("invention")
    inv.meters["overheat"] = 0.0
    inv.meters["steam"] = 0.0
    boat.meters["fog"] = 0.0
    boat.meters["drift_risk"] = 0.0
    ghost.memes["startled"] = 0.0
    ghost.memes["friendly"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} moved fast and calm. {guardian.pronoun().capitalize()} {response.text}."
    )
    world.say(
        "The angry steam thinned. The ghost's bright eyes softened, and instead of wailing he floated close enough to pat the air over the little stove, as if checking that it had settled."
    )
    world.say(
        f'"There now," said {guardian.label_word}. "{invention.label.capitalize()} wants kindness, not broil."'
    )
    world.say(
        f"The ghost tipped his cap to {child.id}, then drifted to the bow and glowed there like a lantern while the supper finished warming the proper way."
    )


def adrift_night(world: World, child: Entity, guardian: Entity, response: Response) -> None:
    boat = world.get("trawler")
    child.memes["fear"] += 1
    child.memes["sadness"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} {response.fail}."
    )
    world.say(
        "The steam only rolled thicker. The ghost gave one booming cry, and the cabin door banged open on its own."
    )
    world.say(
        f"There was no time to fuss over the invention. {guardian.label_word.capitalize()} scooped up the tool box, took {child.id}'s hand, and hurried back along the pier while the trawler sat wrapped in its own white cloud."
    )
    boat.meters["fog"] += 1
    world.say(
        "They waited on the dock under a harbor lamp until the sky slowly turned silver. When dawn came, the ghost had grown quiet again, and the trawler bobbed in the pale water as if nothing had happened."
    )
    world.say(
        f"{child.id} leaned against {guardian.label_word} and understood that some magic must be handled gently, or else even a friendly ghost can be frightened."
    )


def tell(
    invention: Invention,
    charm: Charm,
    heat: Heat,
    response: Response,
    child_name: str = "Lina",
    child_gender: str = "girl",
    guardian_type: str = "grandfather",
    trait: str = "curious",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, role="guardian", label="the guardian"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost", label="the harbor ghost"))
    trawler = world.add(Entity(id="trawler", type="trawler", label="the old trawler"))
    inv = world.add(Entity(id="invention", type="invention", label=invention.label))
    child.memes["trust"] += 1
    guardian.memes["care"] += 1

    harbor_setup(world, child, guardian, invention, charm)
    tell_harbor_ghost(world, child, guardian)

    world.para()
    prepare_magic(world, child, guardian, invention, charm)
    prediction = predict_spook(world, heat.id)
    world.facts["predicted_spook"] = prediction
    if heat.spooky:
        world.say(
            f"{child.id} glanced at the hottest word on the plate anyway. Broil looked bold and shiny, almost daring a small hand to try it."
        )
    else:
        world.say(
            f"{child.id} remembered the warning and kept one finger very still above the dial."
        )

    world.para()
    choose_heat(world, child, heat)

    if not heat.spooky:
        gentle_success(world, child, guardian, invention, heat)
    else:
        if delay:
            inv.meters["head_start"] += delay
        ghost_broil(world, child, invention)
        world.para()
        if is_mended(invention, heat, response, delay):
            mend_night(world, child, guardian, invention, response)
        else:
            adrift_night(world, child, guardian, response)

    outcome = outcome_of(
        StoryParams(
            invention=invention.id,
            charm=charm.id,
            heat=heat.id,
            response=response.id,
            name=child_name,
            gender=child_gender,
            guardian=guardian_type,
            trait=trait,
            delay=delay,
            seed=None,
        )
    )
    world.facts.update(
        child=child,
        guardian=guardian,
        ghost=ghost,
        trawler=trawler,
        invention_cfg=invention,
        charm_cfg=charm,
        heat_cfg=heat,
        response=response,
        outcome=outcome,
        severity=spook_severity(invention, heat, delay),
        delay=delay,
        ghost_seen=(ghost.memes["friendly"] >= THRESHOLD or heat.spooky),
    )
    return world


@dataclass
class StoryParams:
    invention: str
    charm: str
    heat: str
    response: str
    name: str
    gender: str
    guardian: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "trawler": [(
        "What is a trawler?",
        "A trawler is a fishing boat that works out on the water and carries nets, ropes, and gear. Old trawlers can creak and groan in ways that sound spooky at night."
    )],
    "invention": [(
        "What is an invention?",
        "An invention is something a person makes to do a new job in a clever way. Some inventions are machines, and some stories imagine magical ones."
    )],
    "broil": [(
        "What does broil mean?",
        "Broil means to use very high heat. High heat can be useful for some cooking, but it is not safe for every tool or every job."
    )],
    "magic": [(
        "What is magic in a story?",
        "Magic in a story is a special power that makes unusual things happen, like a kettle glowing blue or a ghost stepping out of steam. Story magic still works best when characters are careful and kind."
    )],
    "ghost": [(
        "What is a ghost story?",
        "A ghost story is a tale with spooky feelings, shadows, or spirits. In a gentle ghost story, the ghost can be eerie without being cruel."
    )],
    "seawater": [(
        "Why can cooling something help when it gets too hot?",
        "Cooling can help bring hot metal back down so it stops hissing and steaming so hard. A grown-up should decide the safe way to cool it."
    )],
    "song": [(
        "Why might a song calm someone down?",
        "A soft familiar song can make a scared person feel steadier. In stories, it can calm a frightened ghost too."
    )],
}
KNOWLEDGE_ORDER = ["trawler", "invention", "broil", "magic", "ghost", "seawater", "song"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    invention = f["invention_cfg"]
    heat = f["heat_cfg"]
    outcome = f["outcome"]
    if outcome == "calm":
        return [
            'Write a gentle ghost story for a 3-to-5-year-old that includes the words "trawler", "invention", and "broil", but ends safely.',
            f"Tell a harbor ghost story where {child.id} helps test {invention.phrase} on an old trawler and remembers not to twist the dial to broil.",
            "Write a magical nighttime story in which a friendly ghost appears only after a child treats a strange machine gently.",
        ]
    if outcome == "mended":
        return [
            'Write a spooky-but-safe ghost story for a 3-to-5-year-old that includes the words "trawler", "invention", and "broil".',
            f"Tell a story where {child.id} chooses broil on a magic invention aboard a trawler, wakes a harbor ghost, and a calm grown-up fixes the trouble.",
            "Write a magical harbor story with a scary middle turn and a warm ending image that proves everyone learned to be gentle with magic.",
        ]
    return [
        'Write a ghost story for a 3-to-5-year-old that includes the words "trawler", "invention", and "broil", with a spooky but safe ending.',
        f"Tell a cautionary harbor story where {child.id} uses broil on a magic invention, the ghostly fog grows too thick, and the child must leave the trawler until dawn.",
        "Write a gentle scary story where nobody is hurt, but a frightened ghost shows why some magical tools must not be pushed too hard.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    invention = f["invention_cfg"]
    charm = f["charm_cfg"]
    heat = f["heat_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    guardian_word = guardian.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {guardian_word}, and the harbor ghost on an old trawler. They meet while testing a strange magic invention at dusk."
        ),
        (
            f"What invention were they testing?",
            f"They were testing {invention.phrase}. It was supposed to {invention.promise} when {charm.phrase} was tucked inside."
        ),
        (
            f"Why did {guardian_word} warn {child.id} about broil?",
            f"{guardian_word.capitalize()} warned that broil was too strong for the little invention on a damp night. The machine worked best with gentle heat, and too much heat could startle the ghost and fill the cabin with steam."
        ),
    ]
    if outcome == "calm":
        qa.append((
            "What happened when they used the gentle setting?",
            f"The invention glowed kindly instead of hissing, and the ghost appeared in a calm friendly way. The ending shows that careful magic made the trawler feel safe and cozy."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a small meal warming quietly, the ghost smiling, and the trawler rocking softly in the dark water. That peaceful picture proves nothing scary had taken over."
        ))
    elif outcome == "mended":
        qa.append((
            "What happened when the dial was turned to broil?",
            f"The invention overheated and burst into hot steam, and the harbor ghost rose out of it with a frightened wail. The steam and fog made the cabin feel spooky because the magic had been pushed too hard."
        ))
        qa.append((
            f"How did {guardian_word} fix the problem?",
            f"{guardian_word.capitalize()} {response.qa_text}. That calm fix lowered the danger and helped the ghost stop feeling alarmed."
        ))
        qa.append((
            "What changed by the end of the story?",
            f"At first the trawler felt crowded with steam and fear, but by the end the ghost was calm and glowing at the bow like a lantern. The child learned that magic inventions want gentle hands, not broil."
        ))
    else:
        qa.append((
            f"Could {guardian_word} stop the spooky fog right away?",
            f"No. {guardian_word.capitalize()} tried, but the fog kept swelling through the trawler cabin. They had to leave the boat and wait safely on the dock until dawn."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely but sadly, with {child.id} and {guardian_word} under a harbor lamp while the trawler sat inside its own white cloud. Dawn finally quieted the ghost and showed why the broil setting had been too much."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"trawler", "invention", "magic", "ghost"}
    if f["heat_cfg"].id == "broil":
        tags.add("broil")
    if "seawater" in f["response"].tags:
        tags.add("seawater")
    if "song" in f["response"].tags:
        tags.add("song")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon_stove", "moon_salt", "warm", "cool_and_lower", "Lina", "girl", "grandfather", "careful", 0),
    StoryParams("bell_boiler", "brass_key", "broil", "open_hatch_song", "Finn", "boy", "grandmother", "curious", 0),
    StoryParams("gull_kettle", "gull_feather", "broil", "cool_and_lower", "Mara", "girl", "grandfather", "bold", 1),
    StoryParams("moon_stove", "moon_salt", "broil", "open_hatch_song", "Theo", "boy", "grandmother", "restless", 2),
]


ASP_RULES = r"""
fits(I, C) :- invention(I), charm(C), matches(C, I).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(I, C, R) :- invention(I), charm(C), response(R), fits(I, C), sensible(R).

spooky_heat :- chosen_heat(H), spooky(H).
severity(D + HI + DE) :- chosen_invention(I), delicate(I, D), chosen_heat(H), intensity(H, HI), delay(DE), spooky(H).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(calm) :- chosen_heat(H), not spooky(H).
outcome(mended) :- spooky_heat, contained.
outcome(adrift) :- spooky_heat, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for iid, inv in INVENTIONS.items():
        lines.append(asp.fact("invention", iid))
        lines.append(asp.fact("delicate", iid, inv.delicate))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for mid in sorted(charm.matches):
            lines.append(asp.fact("matches", cid, mid))
    for hid, heat in HEATS.items():
        lines.append(asp.fact("heat", hid))
        lines.append(asp.fact("intensity", hid, heat.intensity))
        if heat.spooky:
            lines.append(asp.fact("spooky", hid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_invention", params.invention),
        asp.fact("chosen_heat", params.heat),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a trawler, a magic invention, and the risky broil setting."
    )
    ap.add_argument("--invention", choices=INVENTIONS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--heat", choices=HEATS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--guardian", choices=["grandmother", "grandfather"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the spooky steam gets before the fix matters")
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
    if args.invention and args.charm:
        inv, charm = INVENTIONS[args.invention], CHARMS[args.charm]
        if not charm_fits(inv, charm):
            raise StoryError(explain_charm(inv, charm))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.invention is None or c[0] == args.invention)
        and (args.charm is None or c[1] == args.charm)
        and (args.response is None or c[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    invention_id, charm_id, response_id = rng.choice(sorted(combos))
    heat = args.heat or rng.choice(sorted(HEATS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else (rng.randint(0, 2) if heat == "broil" else 0)
    return StoryParams(invention_id, charm_id, heat, response_id, name, gender, guardian, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        INVENTIONS[params.invention],
        CHARMS[params.charm],
        HEATS[params.heat],
        RESPONSES[params.response],
        child_name=params.name,
        child_gender=params.gender,
        guardian_type=params.guardian,
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (invention, charm, response) combos:\n")
        for invention, charm, response in combos:
            print(f"  {invention:12} {charm:12} {response}")
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
            header = f"### {p.name}: {p.invention} on {p.heat} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
