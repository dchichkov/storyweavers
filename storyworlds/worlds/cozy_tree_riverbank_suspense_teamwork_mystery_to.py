#!/usr/bin/env python3
"""
storyworlds/worlds/cozy_tree_riverbank_suspense_teamwork_mystery_to.py
========================================================================

Myth-flavored riverbank suspense world for the seed:

    Words: cozy tree
    Setting: riverbank
    Features: Suspense, Teamwork, Mystery to Solve
    Style: Myth

Internal source tale
--------------------
At a cozy tree on a riverbank, children care for a small evening token that
helps the village trust the water at dusk. One evening the token is gone, the
mist thickens, and two children must solve a gentle mystery before moonrise.
They cannot simply grab in the dark. One must steady the search while the other
reads a real clue, and together they find the harmless cause, restore the token,
and end with a visible change in the riverbank world.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
RIVER_NAME = "the Moonthread River"


@dataclass(frozen=True)
class RiverTree:
    key: str
    phrase: str
    cozy_detail: str
    duty_place: str
    ending_image: str
    zones: tuple[str, ...]
    methods: tuple[str, ...]


@dataclass(frozen=True)
class Mystery:
    key: str
    token_label: str
    token_phrase: str
    vanish_spot: str
    stakes: str
    omen: str
    hideout: str
    culprit: str
    culprit_kind: str
    motive: str
    reveal: str
    restore_line: str
    ending_image: str
    clues: tuple[str, ...]
    methods: tuple[str, ...]
    lesson: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Clue:
    key: str
    kind: str
    label: str
    mark: str
    trail: str
    location: str
    points_to: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Method:
    key: str
    label: str
    phrase: str
    action_text: str
    teamwork_line: str
    gentle_reason: str
    reads: tuple[str, ...]
    reaches: tuple[str, ...]
    tags: tuple[str, ...] = ()


@dataclass
class StoryParams:
    tree: str
    mystery: str
    clue: str
    method: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    trait: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    role: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Rule:
    name: str
    apply: callable


@dataclass
class World:
    params: StoryParams
    tree_cfg: RiverTree
    mystery_cfg: Mystery
    clue_cfg: Clue
    method_cfg: Method
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple[str, ...]] = field(default_factory=set)
    history: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  tree={self.tree_cfg.key}")
        rows.append(f"  mystery={self.mystery_cfg.key}")
        rows.append(f"  clue={self.clue_cfg.key}")
        rows.append(f"  method={self.method_cfg.key}")
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            rows.append(
                f"  {ent.name:<10} <{ent.kind:<8}> role={ent.role or '-':<8} "
                f"location={ent.location:<12} meters={meters} memes={memes}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append(f"  fired={sorted(self.fired)}")
        rows.append(f"  history={self.history}")
        return "\n".join(rows)


TREES: dict[str, RiverTree] = {
    "willow_nook": RiverTree(
        key="willow_nook",
        phrase="the cozy willow tree at the riverbank",
        cozy_detail="its roots made a round little room above the mud, and woven reeds hung there like sleepy curtains",
        duty_place="the low willow branch above the ferry stones",
        ending_image="The willow leaves ticked together like quiet green bells above the gentle water.",
        zones=("roots", "reeds", "branch_hook"),
        methods=("lantern_watch", "reed_chain"),
    ),
    "alder_hollow": RiverTree(
        key="alder_hollow",
        phrase="the cozy alder tree on the riverbank",
        cozy_detail="a warm hollow opened in its trunk, and dry moss turned the inside into a tiny room for evening offerings",
        duty_place="the alder hollow facing the slow water",
        ending_image="The alder hollow glowed softly, and the dark river looked as calm as folded silk.",
        zones=("hollow", "branch_hook"),
        methods=("lantern_watch", "echo_call"),
    ),
    "fig_ferry": RiverTree(
        key="fig_ferry",
        phrase="the cozy fig tree by the riverbank ferry path",
        cozy_detail="its mossy roots curved into low seats, and a lantern hook leaned over the shallows like a kind arm",
        duty_place="the fig tree's mossy crook beside the stepping stones",
        ending_image="The fig leaves held moonlight on their edges, and the stepping stones shone in a neat bright chain.",
        zones=("roots", "reeds", "hollow", "branch_hook", "stones"),
        methods=("lantern_watch", "reed_chain", "echo_call"),
    ),
}


MYSTERIES: dict[str, Mystery] = {
    "moon_bell": Mystery(
        key="moon_bell",
        token_label="the moon bell",
        token_phrase="the little bronze moon bell",
        vanish_spot="the low branch where the evening bell should hang",
        stakes="Without the moon bell, the ferry children could not hear the usual sign that the dusk current was gentle.",
        omen="When the children arrived, the branch was still, the bell-cord was gone, and a thin ribbon of mist crept over the bank.",
        hideout="reeds",
        culprit="an otter pup",
        culprit_kind="animal",
        motive="borrowed the bright cord to line a river-game nest",
        reveal="The reeds parted, and there sat an otter pup beside the moon bell, batting the shining cord between two wet paws.",
        restore_line="The children thanked the playful little thief, untangled the cord, and hung the bell where the river could hear it again.",
        ending_image="The bell rang once, and the mist loosened as if the river had let out a careful breath.",
        clues=("otter_tracks", "silver_thread"),
        methods=("reed_chain", "lantern_watch"),
        lesson="Safe mysteries open when friends share the brave part and the careful part.",
        tags=("bell", "otter", "tracks", "river"),
    ),
    "ferry_ribbon": Mystery(
        key="ferry_ribbon",
        token_label="the ferry ribbon",
        token_phrase="the blue ferry ribbon",
        vanish_spot="the bark peg above the stepping stones",
        stakes="Without the ferry ribbon, the late berry pickers would not see which stones were safest at moonrise.",
        omen="The bark peg was bare, and the water below looked darker than usual, as if it were keeping a secret.",
        hideout="branch_hook",
        culprit="the river wind",
        culprit_kind="wind",
        motive="looped the ribbon around a branch where the breeze kept trying to sing through it",
        reveal="High on the branch hook, the ribbon fluttered in slow circles, wrapped around the bark like a blue fish tail.",
        restore_line="One child listened for the flutter while the other held the lantern steady, and together they eased the ribbon free without tearing it.",
        ending_image="The ribbon floated over the safe stones again, and the water stopped pretending to be deeper than it was.",
        clues=("snagged_fiber", "branch_whisper"),
        methods=("lantern_watch", "echo_call"),
        lesson="A hard mystery can soften when one friend sees and the other listens.",
        tags=("ribbon", "wind", "echo", "river"),
    ),
    "shell_cup": Mystery(
        key="shell_cup",
        token_label="the shell cup",
        token_phrase="the white shell cup",
        vanish_spot="the warm hollow where evening thanks were usually poured",
        stakes="Without the shell cup, the moonrise thanks could not be offered at the tree before the first star appeared.",
        omen="The hollow stood empty, and even the frogs sounded far away for one long breath.",
        hideout="hollow",
        culprit="a shy turtle",
        culprit_kind="animal",
        motive="nudged the cup above the eggs to make a little roof of shade",
        reveal="Inside the hollow, the shell cup leaned over a small nest of turtle eggs, pale as marbles in the moss.",
        restore_line="The children moved the cup only after they had seen what it was protecting, and they tucked a broad leaf over the eggs before returning it.",
        ending_image="The shell cup shone in the hollow again, and the moon laid a silver road across the riverbank water.",
        clues=("moss_dust", "shell_echo"),
        methods=("lantern_watch", "echo_call"),
        lesson="Kind teamwork looks carefully before it reaches.",
        tags=("shell", "turtle", "echo", "moon"),
    ),
}


CLUES: dict[str, Clue] = {
    "otter_tracks": Clue(
        key="otter_tracks",
        kind="tracks",
        label="otter tracks",
        mark="comma-shaped otter tracks stitched across the wet mud",
        trail="They slipped toward the reeds, then vanished where the stalks grew thick.",
        location="roots",
        points_to="reeds",
        tags=("tracks", "mud"),
    ),
    "silver_thread": Clue(
        key="silver_thread",
        kind="thread",
        label="a silver bell-cord thread",
        mark="one silver thread caught on a bent reed",
        trail="It trembled every time the river breathed against the bank.",
        location="reeds",
        points_to="reeds",
        tags=("cord", "reed"),
    ),
    "snagged_fiber": Clue(
        key="snagged_fiber",
        kind="fiber",
        label="a snag of blue ribbon fiber",
        mark="a tiny fringe of blue ribbon fiber clinging to rough bark",
        trail="The little threads pointed up instead of down, as if the mystery had climbed.",
        location="branch_hook",
        points_to="branch_hook",
        tags=("fiber", "bark"),
    ),
    "branch_whisper": Clue(
        key="branch_whisper",
        kind="echo",
        label="a whisper in the branch",
        mark="a thin flutter-whisper answering from one branch whenever the breeze returned",
        trail="The sound came from above the lantern hook, then circled back once more.",
        location="branch_hook",
        points_to="branch_hook",
        tags=("sound", "wind"),
    ),
    "moss_dust": Clue(
        key="moss_dust",
        kind="moss",
        label="fresh moss dust",
        mark="a crescent of fresh moss dust on the lip of the hollow",
        trail="It looked as though something had nudged gently inward instead of being stolen away.",
        location="hollow",
        points_to="hollow",
        tags=("moss", "hollow"),
    ),
    "shell_echo": Clue(
        key="shell_echo",
        kind="echo",
        label="a shell-echo",
        mark="a tiny shell-echo returning from the back of the hollow",
        trail="The sound doubled itself, as if a smooth white curve were catching it.",
        location="hollow",
        points_to="hollow",
        tags=("sound", "shell"),
    ),
}


METHODS: dict[str, Method] = {
    "lantern_watch": Method(
        key="lantern_watch",
        label="a honey lantern",
        phrase="hold up a honey lantern and study the clue slowly",
        action_text=(
            "{partner} held the honey lantern still while {hero} bent close enough to read the small sign without touching the dark water. "
            "The light stayed calm, and the clue stopped looking like a fright and started looking like an answer."
        ),
        teamwork_line=(
            '"No grabbing in the dark," said {partner}. "I will hold the light. You read what the river left for us."'
        ),
        gentle_reason="The lantern gives the mystery shape without turning a careful search into a wild one.",
        reads=("thread", "fiber", "moss"),
        reaches=("branch_hook", "hollow", "roots"),
        tags=("lantern", "careful"),
    ),
    "reed_chain": Method(
        key="reed_chain",
        label="a linked reed pole",
        phrase="brace the bank and reach with a linked reed pole",
        action_text=(
            "{hero} planted {hero_possessive} feet between two roots while {partner} passed over the linked reed pole. "
            "One child kept the bank steady, and the other guided the light reach into the reeds."
        ),
        teamwork_line=(
            '"If one of us leans and one of us steadies, the bank will not trick us," said {hero}.'
        ),
        gentle_reason="It lets the children reach into wet places together instead of slipping after the clue alone.",
        reads=("tracks", "thread", "stones"),
        reaches=("reeds", "stones", "roots"),
        tags=("reach", "teamwork"),
    ),
    "echo_call": Method(
        key="echo_call",
        label="a shell call cup",
        phrase="cup a shell to the air and listen for the answer",
        action_text=(
            "{partner} lifted the little shell cup to the air while {hero} stood beneath the branch and counted each answering whisper. "
            "Together they followed the sound until it settled in one true place."
        ),
        teamwork_line=(
            '"I will listen above, and you listen below," said {partner}. "The sound will choose the place if we are patient."'
        ),
        gentle_reason="Listening first keeps the children from reaching into the wrong hollow or tearing at the wrong branch.",
        reads=("echo", "fiber"),
        reaches=("hollow", "branch_hook"),
        tags=("listening", "echo"),
    ),
}


HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Lina", "Mara", "Nila", "Tessa", "Suri"),
    "boy": ("Ivo", "Kiran", "Leo", "Milo", "Tarin"),
}

PARTNER_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Ada", "Bria", "Esme", "Jori", "Pia"),
    "boy": ("Darin", "Nico", "Oren", "Pavel", "Rami"),
}

TRAITS = ("careful", "steady", "brave", "patient", "thoughtful")

KNOWLEDGE: dict[str, tuple[tuple[str, str], ...]] = {
    "riverbank": (
        (
            "What is a riverbank?",
            "A riverbank is the edge of the land beside a river. Mud, reeds, roots, and stones often gather there.",
        ),
    ),
    "teamwork": (
        (
            "Why does teamwork help in a mystery?",
            "Teamwork lets one person do one job while another person does a different job. That way they can solve a problem more safely and more clearly.",
        ),
    ),
    "myth": (
        (
            "What makes a story feel like a myth?",
            "A myth often gives ordinary places a sacred or wondrous meaning. It can make a river, tree, or moon feel important to how people live.",
        ),
    ),
    "tracks": (
        (
            "Why are tracks helpful clues?",
            "Tracks show where a creature has moved. They help a careful searcher follow a path without guessing wildly.",
        ),
    ),
    "echo": (
        (
            "What is an echo?",
            "An echo is a sound that bounces back after hitting a surface. It can help people tell where a sound is coming from.",
        ),
    ),
    "reeds": (
        (
            "Why do reeds grow well by a river?",
            "Reeds like wet ground and shallow water. Their stems often grow thick along quiet river edges.",
        ),
    ),
    "lantern": (
        (
            "Why is a lantern useful in a careful search?",
            "A lantern adds steady light. Steady light helps people see small details without rushing.",
        ),
    ),
}
KNOWLEDGE_ORDER = ("riverbank", "myth", "teamwork", "tracks", "echo", "reeds", "lantern")


def _lower_initial(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def valid_combo(tree_key: str, mystery_key: str, clue_key: str, method_key: str) -> bool:
    if tree_key not in TREES or mystery_key not in MYSTERIES or clue_key not in CLUES or method_key not in METHODS:
        return False
    tree = TREES[tree_key]
    mystery = MYSTERIES[mystery_key]
    clue = CLUES[clue_key]
    method = METHODS[method_key]
    return (
        mystery.hideout in tree.zones
        and clue.location in tree.zones
        and clue.key in mystery.clues
        and method.key in tree.methods
        and method.key in mystery.methods
        and clue.kind in method.reads
        and mystery.hideout in method.reaches
        and clue.points_to == mystery.hideout
    )


def explain_rejection(tree_key: str, mystery_key: str, clue_key: str, method_key: str) -> str:
    if tree_key not in TREES:
        return f"No story: unknown tree {tree_key!r}."
    if mystery_key not in MYSTERIES:
        return f"No story: unknown mystery {mystery_key!r}."
    if clue_key not in CLUES:
        return f"No story: unknown clue {clue_key!r}."
    if method_key not in METHODS:
        return f"No story: unknown method {method_key!r}."

    tree = TREES[tree_key]
    mystery = MYSTERIES[mystery_key]
    clue = CLUES[clue_key]
    method = METHODS[method_key]

    if mystery.hideout not in tree.zones:
        return (
            f"No story: {tree.phrase} does not contain the right hiding place for {mystery.token_label}. "
            f"It cannot host a mystery hidden in {mystery.hideout}."
        )
    if clue.location not in tree.zones:
        return (
            f"No story: {clue.label} does not belong at {tree.phrase}. "
            f"The clue needs a {clue.location} zone there."
        )
    if clue.key not in mystery.clues:
        return (
            f"No story: {clue.label} does not honestly point to {mystery.token_label}. "
            f"Choose one of: {', '.join(mystery.clues)}."
        )
    if method.key not in tree.methods:
        return (
            f"No story: {tree.phrase} does not support the method {method.key!r}. "
            f"Try one of: {', '.join(tree.methods)}."
        )
    if method.key not in mystery.methods:
        return (
            f"No story: {method.label} does not sensibly solve the mystery of {mystery.token_label}. "
            f"Use one of: {', '.join(mystery.methods)}."
        )
    if clue.kind not in method.reads:
        return (
            f"No story: {method.label} cannot read {clue.label}. "
            f"It only reads: {', '.join(method.reads)}."
        )
    if mystery.hideout not in method.reaches:
        return (
            f"No story: {method.label} cannot safely reach {mystery.hideout}. "
            f"It only reaches: {', '.join(method.reaches)}."
        )
    if clue.points_to != mystery.hideout:
        return (
            f"No story: {clue.label} points to {clue.points_to}, not to the mystery hideout {mystery.hideout}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for tree_key in sorted(TREES):
        for mystery_key in sorted(MYSTERIES):
            for clue_key in sorted(CLUES):
                for method_key in sorted(METHODS):
                    if valid_combo(tree_key, mystery_key, clue_key, method_key):
                        combos.append((tree_key, mystery_key, clue_key, method_key))
    return combos


def _pick_name(pool: dict[str, tuple[str, ...]], gender: str, rng: random.Random, avoid: str = "") -> str:
    options = [name for name in pool[gender] if name != avoid]
    return rng.choice(options)


def build_world(params: StoryParams) -> World:
    tree_cfg = TREES[params.tree]
    mystery_cfg = MYSTERIES[params.mystery]
    clue_cfg = CLUES[params.clue]
    method_cfg = METHODS[params.method]
    world = World(params=params, tree_cfg=tree_cfg, mystery_cfg=mystery_cfg, clue_cfg=clue_cfg, method_cfg=method_cfg)

    hero = world.add(
        Entity(
            name=params.hero,
            kind=params.hero_gender,
            label=params.hero,
            role="hero",
            location="riverbank",
            meters=defaultdict(float, {"balance": 1.0, "reach": 0.8}),
            memes=defaultdict(float, {"wonder": 1.0, "worry": 0.0, "trust": 0.7, "courage": 0.7}),
        )
    )
    partner = world.add(
        Entity(
            name=params.partner,
            kind=params.partner_gender,
            label=params.partner,
            role="partner",
            location="riverbank",
            meters=defaultdict(float, {"balance": 1.0, "light": 0.8}),
            memes=defaultdict(float, {"wonder": 0.8, "worry": 0.0, "trust": 0.8, "care": 0.9}),
        )
    )
    world.add(
        Entity(
            name="tree",
            kind="tree",
            label=tree_cfg.phrase,
            role="shelter",
            location="riverbank",
            meters=defaultdict(float, {"shelter": 1.3, "lantern_glow": 0.6}),
            memes=defaultdict(float, {"cozy": 1.4, "old_magic": 1.0}),
        )
    )
    world.add(
        Entity(
            name="river",
            kind="river",
            label=RIVER_NAME,
            role="river",
            location="riverbank",
            meters=defaultdict(float, {"mist": 0.2, "current": 0.5, "quiet": 0.7}),
            memes=defaultdict(float, {"mystery": 0.8}),
        )
    )
    world.add(
        Entity(
            name="token",
            kind="token",
            label=mystery_cfg.token_label,
            role="token",
            location=mystery_cfg.vanish_spot,
            meters=defaultdict(float, {"present": 1.0, "missing": 0.0, "found": 0.0, "restored": 0.0}),
            memes=defaultdict(float, {"importance": 1.2}),
        )
    )
    world.add(
        Entity(
            name="clue",
            kind="clue",
            label=clue_cfg.label,
            role="clue",
            location=clue_cfg.location,
            meters=defaultdict(float, {"visible": 0.0, "understood": 0.0}),
            memes=defaultdict(float, {"hint": 1.0}),
        )
    )
    world.add(
        Entity(
            name="method",
            kind="method",
            label=method_cfg.label,
            role="method",
            location="riverbank",
            meters=defaultdict(float, {"used": 0.0}),
            memes=defaultdict(float, {"teamwork": 1.0}),
        )
    )
    world.add(
        Entity(
            name="culprit",
            kind=mystery_cfg.culprit_kind,
            label=mystery_cfg.culprit,
            role="carrier",
            location=mystery_cfg.hideout,
            meters=defaultdict(float, {"present": 1.0}),
            memes=defaultdict(float, {"harmless": 1.0}),
        )
    )

    world.facts.update(
        {
            "setting": "riverbank",
            "style": "myth",
            "features": ["suspense", "teamwork", "mystery_to_solve"],
            "resolved": False,
            "token_found_in": None,
            "lesson": mystery_cfg.lesson,
            "seed_word": "cozy tree",
            "seed": params.seed,
        }
    )
    hero.memes["trait"] = 1.0
    partner.memes["teamwork"] = 0.0
    hero.memes["teamwork"] = 0.0
    return world


def _hero(world: World) -> Entity:
    return world.get(world.params.hero)


def _partner(world: World) -> Entity:
    return world.get(world.params.partner)


def _tree(world: World) -> Entity:
    return world.get("tree")


def _river(world: World) -> Entity:
    return world.get("river")


def _token(world: World) -> Entity:
    return world.get("token")


def _clue(world: World) -> Entity:
    return world.get("clue")


def _method(world: World) -> Entity:
    return world.get("method")


def _mark(world: World, *parts: str) -> bool:
    if parts in world.fired:
        return False
    world.fired.add(parts)
    return True


def _r_missing_alarm(world: World) -> bool:
    token = _token(world)
    hero = _hero(world)
    partner = _partner(world)
    river = _river(world)
    if token.meters["missing"] < THRESHOLD:
        return False
    if not _mark(world, "missing_alarm"):
        return False
    hero.memes["worry"] += 1.0
    partner.memes["worry"] += 0.8
    river.meters["mist"] += 0.6
    river.meters["quiet"] = max(0.2, river.meters["quiet"] - 0.3)
    world.history.append("token_missing_raised_alarm")
    return True


def _r_team_focus(world: World) -> bool:
    hero = _hero(world)
    partner = _partner(world)
    if hero.memes["teamwork"] < THRESHOLD or partner.memes["teamwork"] < THRESHOLD:
        return False
    if not _mark(world, "team_focus"):
        return False
    hero.memes["trust"] += 0.4
    partner.memes["trust"] += 0.4
    hero.memes["worry"] = max(0.2, hero.memes["worry"] - 0.3)
    partner.memes["worry"] = max(0.2, partner.memes["worry"] - 0.2)
    world.history.append("teamwork_steady")
    return True


def _r_read_clue(world: World) -> bool:
    clue = _clue(world)
    method = _method(world)
    if clue.meters["visible"] < THRESHOLD or method.meters["used"] < THRESHOLD:
        return False
    if world.clue_cfg.kind not in world.method_cfg.reads:
        return False
    if _hero(world).memes["teamwork"] < THRESHOLD or _partner(world).memes["teamwork"] < THRESHOLD:
        return False
    if not _mark(world, "read_clue", world.clue_cfg.key, world.method_cfg.key):
        return False
    clue.meters["understood"] += 1.0
    _hero(world).memes["courage"] += 0.3
    _partner(world).memes["care"] += 0.2
    world.history.append("clue_understood")
    return True


def _r_recover_token(world: World) -> bool:
    token = _token(world)
    clue = _clue(world)
    if clue.meters["understood"] < THRESHOLD:
        return False
    if world.mystery_cfg.hideout not in world.method_cfg.reaches:
        return False
    if not _mark(world, "recover_token", world.mystery_cfg.key):
        return False
    token.meters["found"] += 1.0
    token.meters["missing"] = 0.0
    token.location = world.mystery_cfg.hideout
    world.facts["token_found_in"] = world.mystery_cfg.hideout
    world.history.append("token_found")
    return True


def _r_restore_calm(world: World) -> bool:
    token = _token(world)
    river = _river(world)
    if token.meters["found"] < THRESHOLD:
        return False
    if not _mark(world, "restore_calm", world.mystery_cfg.key):
        return False
    token.meters["restored"] += 1.0
    token.meters["present"] = 1.0
    token.location = world.mystery_cfg.vanish_spot
    river.meters["mist"] = max(0.0, river.meters["mist"] - 0.6)
    river.meters["quiet"] += 0.5
    _hero(world).memes["worry"] = max(0.0, _hero(world).memes["worry"] - 0.8)
    _partner(world).memes["worry"] = max(0.0, _partner(world).memes["worry"] - 0.7)
    _hero(world).memes["wonder"] += 0.3
    _partner(world).memes["wonder"] += 0.3
    world.facts["resolved"] = True
    world.history.append("token_restored")
    return True


CAUSAL_RULES = (
    Rule("missing_alarm", _r_missing_alarm),
    Rule("team_focus", _r_team_focus),
    Rule("read_clue", _r_read_clue),
    Rule("recover_token", _r_recover_token),
    Rule("restore_calm", _r_restore_calm),
)


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def _introduce(world: World) -> None:
    hero = _hero(world)
    partner = _partner(world)
    world.say(
        f"People on the banks of {RIVER_NAME} said the water listened at dusk, especially beneath {world.tree_cfg.phrase}. "
        f"That cozy tree was where {hero.label} and {partner.label} brought the evening token for the river."
    )
    world.say(
        f"On that night, the children came to {world.tree_cfg.phrase}, where {world.tree_cfg.cozy_detail}. "
        f"{hero.label} was known for being {world.params.trait}, and {partner.label} never hurried a careful task."
    )


def _raise_suspense(world: World) -> None:
    token = _token(world)
    token.meters["present"] = 0.0
    token.meters["missing"] = 1.0
    token.location = world.mystery_cfg.hideout
    propagate(world)

    world.para()
    world.say(
        f"They were meant to hang {world.mystery_cfg.token_phrase} at {world.mystery_cfg.vanish_spot}, but {_lower_initial(world.mystery_cfg.omen)}"
    )
    world.say(world.mystery_cfg.stakes)
    world.say(
        f"{_hero(world).label} felt the mystery grow larger in the dim light, and even {RIVER_NAME} seemed to pause against the riverbank stones."
    )


def _hesitate(world: World) -> None:
    hero = _hero(world)
    world.para()
    world.say(
        f"{hero.label} almost reached into the dark at once, but the wet bank looked slippery and the old stories warned against snatching at shadows. "
        f"So {hero.pronoun('subject')} stopped before turning a small mystery into a foolish one."
    )


def _team_plan(world: World) -> None:
    hero = _hero(world)
    partner = _partner(world)
    hero.memes["teamwork"] += 1.0
    partner.memes["teamwork"] += 1.0
    propagate(world)

    line = world.method_cfg.teamwork_line.format(hero=hero.label, partner=partner.label)
    world.say(line)
    world.say(
        f"They chose to {world.method_cfg.phrase}. {world.method_cfg.gentle_reason}"
    )


def _find_clue(world: World) -> None:
    clue = _clue(world)
    clue.meters["visible"] += 1.0
    world.para()
    world.say(
        f"Near the {world.clue_cfg.location.replace('_', ' ')}, they found {world.clue_cfg.mark}. "
        f"{world.clue_cfg.trail}"
    )


def _use_method(world: World) -> None:
    hero = _hero(world)
    partner = _partner(world)
    method = _method(world)
    method.meters["used"] += 1.0
    world.say(
        world.method_cfg.action_text.format(
            hero=hero.label,
            partner=partner.label,
            hero_possessive=hero.pronoun("possessive"),
        )
    )
    propagate(world)


def _reveal(world: World) -> None:
    if not world.facts["resolved"]:
        raise StoryError(
            f"No story: the chosen clue and method did not resolve the mystery of {world.mystery_cfg.token_label}."
        )
    world.say(world.mystery_cfg.reveal)
    world.say(
        f"It had happened because {world.mystery_cfg.culprit} {world.mystery_cfg.motive}."
    )


def _restore(world: World) -> None:
    world.say(world.mystery_cfg.restore_line)
    world.say(
        f"{_hero(world).label} and {_partner(world).label} smiled at each other, because the answer had needed both steady hands and steady minds."
    )


def _close(world: World) -> None:
    world.para()
    world.say(
        f"When the children finished, they remembered that {_lower_initial(world.mystery_cfg.lesson)}"
    )
    world.say(world.mystery_cfg.ending_image)
    world.say(world.tree_cfg.ending_image)


def tell(params: StoryParams) -> World:
    if not valid_combo(params.tree, params.mystery, params.clue, params.method):
        raise StoryError(explain_rejection(params.tree, params.mystery, params.clue, params.method))
    world = build_world(params)
    _introduce(world)
    _raise_suspense(world)
    _hesitate(world)
    _team_plan(world)
    _find_clue(world)
    _use_method(world)
    _reveal(world)
    _restore(world)
    _close(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a myth-like story for children that includes the words "cozy tree" and takes place on a riverbank.',
        f"Tell a suspenseful riverbank mystery where {world.params.hero} and {world.params.partner} solve the disappearance of {world.mystery_cfg.token_phrase} through teamwork.",
        f"Write a gentle myth about {world.tree_cfg.phrase}, a missing evening token, a real clue, and a calm solution before moonrise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = _hero(world)
    partner = _partner(world)
    mystery = world.mystery_cfg
    clue = world.clue_cfg
    method = world.method_cfg
    qa = [
        (
            "Where did the story happen?",
            f"The story happened at {world.tree_cfg.phrase} beside {RIVER_NAME}. That riverbank setting is where the children cared for the evening token.",
        ),
        (
            "What mystery did the children have to solve?",
            f"They had to solve why {mystery.token_label} was missing from {mystery.vanish_spot}. The missing token mattered because {mystery.stakes.lower()}",
        ),
        (
            "What clue helped them?",
            f"The clue was {clue.label}. It mattered because {clue.trail.lower()} It pointed them toward the {mystery.hideout.replace('_', ' ')}.",
        ),
        (
            "How did teamwork help solve the mystery?",
            f"{hero.label} and {partner.label} worked together by using {method.label}. One child handled one part of the search while the other handled the second part, so the mystery became clear without anyone grabbing blindly in the dark.",
        ),
        (
            "What was the real reason the token was missing?",
            f"The token was missing because {mystery.culprit} {mystery.motive}. The problem looked spooky at first, but the cause was gentle and real.",
        ),
    ]
    if world.facts["resolved"]:
        qa.append(
            (
                "How did the story end?",
                f"The children restored {mystery.token_label} to {mystery.vanish_spot}. {mystery.ending_image}",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"riverbank", "myth", "teamwork"}
    tags |= set(world.mystery_cfg.tags)
    tags |= set(world.clue_cfg.tags)
    tags |= set(world.method_cfg.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines += [f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the world and story ==")
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


CURATED = [
    StoryParams("willow_nook", "moon_bell", "otter_tracks", "reed_chain", "Lina", "girl", "Rami", "boy", "steady"),
    StoryParams("willow_nook", "ferry_ribbon", "snagged_fiber", "lantern_watch", "Ivo", "boy", "Ada", "girl", "careful"),
    StoryParams("alder_hollow", "shell_cup", "shell_echo", "echo_call", "Mara", "girl", "Oren", "boy", "patient"),
    StoryParams("fig_ferry", "moon_bell", "silver_thread", "lantern_watch", "Leo", "boy", "Esme", "girl", "thoughtful"),
]


ASP_RULES = r"""
hosts_tree(T,M,C) :- zone(T,H), hideout(M,H), clue_location(C,L), zone(T,L).
fits_clue(M,C)    :- mystery_clue(M,C).
fits_method(M,Me) :- mystery_method(M,Me).
tree_method_ok(T,Me) :- tree_method(T,Me).
reads_clue(Me,C)  :- clue_kind(C,K), reads(Me,K).
reaches_hide(Me,M) :- hideout(M,H), reaches(Me,H).
honest_pointer(M,C) :- clue_points(C,H), hideout(M,H).
valid(T,M,C,Me) :- tree(T), mystery(M), clue(C), method(Me),
                   hosts_tree(T,M,C), fits_clue(M,C), fits_method(M,Me),
                   tree_method_ok(T,Me), reads_clue(Me,C), reaches_hide(Me,M),
                   honest_pointer(M,C).
"""


def asp_facts() -> str:
    from storyworlds import asp

    lines: list[str] = []
    for tree_key, tree in TREES.items():
        lines.append(asp.fact("tree", tree_key))
        for zone in tree.zones:
            lines.append(asp.fact("zone", tree_key, zone))
        for method in tree.methods:
            lines.append(asp.fact("tree_method", tree_key, method))
    for mystery_key, mystery in MYSTERIES.items():
        lines += [
            asp.fact("mystery", mystery_key),
            asp.fact("hideout", mystery_key, mystery.hideout),
        ]
        for clue in mystery.clues:
            lines.append(asp.fact("mystery_clue", mystery_key, clue))
        for method in mystery.methods:
            lines.append(asp.fact("mystery_method", mystery_key, method))
    for clue_key, clue in CLUES.items():
        lines += [
            asp.fact("clue", clue_key),
            asp.fact("clue_kind", clue_key, clue.kind),
            asp.fact("clue_location", clue_key, clue.location),
            asp.fact("clue_points", clue_key, clue.points_to),
        ]
    for method_key, method in METHODS.items():
        lines.append(asp.fact("method", method_key))
        for kind in method.reads:
            lines.append(asp.fact("reads", method_key, kind))
        for reach in method.reaches:
            lines.append(asp.fact("reaches", method_key, reach))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _verify_story(sample: StorySample) -> None:
    if "cozy tree" not in sample.story.lower():
        raise StoryError("Verification failed: story does not include the required seed words 'cozy tree'.")
    if "riverbank" not in sample.story.lower():
        raise StoryError("Verification failed: story does not clearly stay on the riverbank.")
    if sample.story.count("\n\n") < 3:
        raise StoryError("Verification failed: story is missing a strong beginning, turn, or ending paragraph.")
    if not sample.story_qa or not sample.world_qa:
        raise StoryError("Verification failed: QA output is empty.")
    if sample.world is None or not sample.world.facts.get("resolved"):
        raise StoryError("Verification failed: world did not resolve its mystery.")


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("MISMATCH between Python gate and ASP gate:")
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        return 1

    for index, combo in enumerate(sorted(python_set)):
        tree_key, mystery_key, clue_key, method_key = combo
        params = StoryParams(
            tree=tree_key,
            mystery=mystery_key,
            clue=clue_key,
            method=method_key,
            hero="Lina" if index % 2 == 0 else "Ivo",
            hero_gender="girl" if index % 2 == 0 else "boy",
            partner="Rami" if index % 2 == 0 else "Ada",
            partner_gender="boy" if index % 2 == 0 else "girl",
            trait=TRAITS[index % len(TRAITS)],
            seed=index,
        )
        sample = generate(params)
        _verify_story(sample)

    print(f"OK: clingo gate matches valid_combos() and {len(python_set)} stories verify cleanly.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Story world: cozy tree riverbank suspense teamwork mystery.")
    parser.add_argument("--tree", choices=TREES)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--clue", choices=CLUES)
    parser.add_argument("--method", choices=METHODS)
    parser.add_argument("--hero")
    parser.add_argument("--hero-gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--partner")
    parser.add_argument("--partner-gender", choices=sorted(PARTNER_NAMES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tree and args.mystery and args.clue and args.method:
        if not valid_combo(args.tree, args.mystery, args.clue, args.method):
            raise StoryError(explain_rejection(args.tree, args.mystery, args.clue, args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.tree is None or combo[0] == args.tree)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.clue is None or combo[2] == args.clue)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid cozy-tree riverbank mystery matches the given options.)")

    tree_key, mystery_key, clue_key, method_key = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(sorted(HERO_NAMES))
    partner_gender = args.partner_gender or rng.choice(sorted(PARTNER_NAMES))
    hero = args.hero or _pick_name(HERO_NAMES, hero_gender, rng)
    partner = args.partner or _pick_name(PARTNER_NAMES, partner_gender, rng, avoid=hero)
    return StoryParams(
        tree=tree_key,
        mystery=mystery_key,
        clue=clue_key,
        method=method_key,
        hero=hero,
        hero_gender=hero_gender,
        partner=partner,
        partner_gender=partner_gender,
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tree, mystery, clue, method) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{item:14}" for item in row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        tries = 0
        while len(samples) < args.n and tries < max(50, args.n * 60):
            seed = base_seed + tries
            tries += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
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

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = (
                f"### {sample.params.hero} & {sample.params.partner}: "
                f"{sample.params.mystery} at {sample.params.tree}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
